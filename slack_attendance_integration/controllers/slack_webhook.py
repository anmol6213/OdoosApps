# -*- coding: utf-8 -*-

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime

import certifi
import ssl
import urllib.request
from pytz import timezone as pytz_timezone

from odoo import http, fields
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class SlackAttendanceController(http.Controller):
    """Slack Slash Command Controller for Attendance"""

    IST = pytz_timezone('Asia/Kolkata')

    # ─────────────────────────────────────────────
    #  SECURITY HELPERS
    # ─────────────────────────────────────────────

    def _verify_slack_signature(self, raw_body: bytes, timestamp: str, signature: str) -> bool:
        """
        Verify the request really came from Slack using HMAC-SHA256.
        Docs: https://api.slack.com/authentication/verifying-requests-from-slack
        """
        try:
            # Replay-attack protection: reject requests older than 5 minutes
            if abs(time.time() - int(timestamp)) > 300:
                _logger.warning("Slack signature expired — possible replay attack")
                return False

            config = request.env['slack.config'].sudo().search(
                [('active', '=', True)], limit=1
            )
            if not config:
                _logger.error("No active Slack config for signature verification")
                return False

            base_string = f"v0:{timestamp}:{raw_body.decode('utf-8')}"
            expected = (
                'v0='
                + hmac.new(
                    config.signing_secret.encode('utf-8'),
                    base_string.encode('utf-8'),
                    hashlib.sha256,
                ).hexdigest()
            )

            # compare_digest prevents timing attacks
            is_valid = hmac.compare_digest(expected, signature)
            if not is_valid:
                _logger.warning("Invalid Slack signature — request rejected")
            return is_valid

        except Exception as e:
            _logger.error(f"Signature verification error: {e}")
            return False

    # ─────────────────────────────────────────────
    #  WEBHOOK / SSL HELPER
    # ─────────────────────────────────────────────

    def _send_webhook(self, url: str, message: str):
        """
        Send message to Slack via Incoming Webhook.
        Uses certifi CA bundle — no CERT_NONE security risk.
        """
        try:
            data = json.dumps({"text": message}).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
            urllib.request.urlopen(req, timeout=5, context=ssl_ctx)
            _logger.info("Webhook sent successfully")
        except Exception as e:
            _logger.warning(f"Webhook failed: {e}")

    # ─────────────────────────────────────────────
    #  TIMEZONE HELPER
    # ─────────────────────────────────────────────

    def _get_employee_tz(self, employee):
        """Employee tz → company tz → IST fallback. No more hardcoded timezone."""
        tz_name = (
            employee.tz
            or employee.company_id.partner_id.tz
            or 'Asia/Kolkata'
        )
        try:
            return pytz_timezone(tz_name)
        except Exception:
            return self.IST

    def _utc_to_local(self, utc_time, employee):
        return utc_time.astimezone(self._get_employee_tz(employee))

    # ─────────────────────────────────────────────
    #  CONFIG HELPER  (ORM — no raw SQL)
    # ─────────────────────────────────────────────

    def _get_config_values(self):
        """Return (grace_minutes, min_break_minutes) via ORM."""
        config = request.env['slack.config'].sudo().search(
            [('active', '=', True)], limit=1
        )
        if config:
            return config.login_grace_minutes or 0, config.min_break_minutes or 0
        return 0, 0

    # ─────────────────────────────────────────────
    #  COMMAND HANDLERS
    # ─────────────────────────────────────────────

    def _handle_login(self, employee):
        from datetime import timedelta
        Attendance = request.env['hr.attendance'].sudo()
        existing = Attendance.search(
            [('employee_id', '=', employee.id), ('check_out', '=', False)], limit=1
        )
        if existing:
            t = self._utc_to_local(existing.check_in, employee)
            return f"*{employee.name}*\nAlready logged in since {t.strftime('%I:%M %p')}"

        now_utc = fields.Datetime.now()
        grace, _ = self._get_config_values()
        check_in_utc = now_utc - timedelta(minutes=grace)
        Attendance.create({'employee_id': employee.id, 'check_in': check_in_utc, 'slack_created': True})
        t = self._utc_to_local(check_in_utc, employee)
        return f"*{employee.name}*\nLogged in at {t.strftime('%I:%M %p')}"

    def _handle_break(self, employee):
        Attendance = request.env['hr.attendance'].sudo()
        att = Attendance.search(
            [('employee_id', '=', employee.id), ('check_out', '=', False)], limit=1
        )
        if not att:
            return f"*{employee.name}*\nPlease login first"
        if att.get_active_break():
            return f"*{employee.name}*\nAlready on break"
        request.env['attendance.break'].sudo().create({
            'employee_id': employee.id,
            'attendance_id': att.id,
            'break_start': fields.Datetime.now(),
        })
        return f"*{employee.name}*\nBreak started"

    def _handle_resume(self, employee):
        Attendance = request.env['hr.attendance'].sudo()
        att = Attendance.search(
            [('employee_id', '=', employee.id), ('check_out', '=', False)], limit=1
        )
        if not att:
            return f"*{employee.name}*\nPlease login first"
        active_break = att.get_active_break()
        if not active_break:
            return f"*{employee.name}*\nNot on break"

        now_utc = fields.Datetime.now()
        duration_min = (now_utc - active_break.break_start).total_seconds() / 60
        _, min_break = self._get_config_values()

        if duration_min < min_break:
            active_break.write({'break_end': now_utc, 'is_counted': False})
            return f"*{employee.name}*\nResumed (break under {min_break} min — not counted)"
        active_break.write({'break_end': now_utc, 'is_counted': True})
        return f"*{employee.name}*\nBreak ended, resumed work"

    def _handle_logout(self, employee):
        Attendance = request.env['hr.attendance'].sudo()
        att = Attendance.search(
            [('employee_id', '=', employee.id), ('check_out', '=', False)], limit=1
        )
        if not att:
            return f"*{employee.name}*\nNot logged in"
        if att.get_active_break():
            return f"*{employee.name}*\nResume from break first"
        now_utc = fields.Datetime.now()
        att.write({'check_out': now_utc})
        t = self._utc_to_local(now_utc, employee)
        return f"*{employee.name}*\nLogged out at {t.strftime('%I:%M %p')}"

    # ─────────────────────────────────────────────
    #  MAIN ROUTE  (with signature verification)
    # ─────────────────────────────────────────────

    @http.route(
        '/slack/attendance',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
        save_session=False,
    )
    def slack_attendance_webhook(self, **kwargs):

        # 1. Verify Slack signature
        http_req  = request.httprequest
        raw_body  = http_req.get_data()
        timestamp = http_req.headers.get('X-Slack-Request-Timestamp', '')
        signature = http_req.headers.get('X-Slack-Signature', '')

        if not self._verify_slack_signature(raw_body, timestamp, signature):
            _logger.warning("Rejected invalid Slack request")
            return Response('', status=200)   # Always 200 to avoid Slack retries

        # 2. Parse command
        cmd     = kwargs.get('command', '').replace('/', '')
        user_id = kwargs.get('user_id')
        _logger.info(f"/{cmd} from {user_id}")

        try:
            # 3. Look up employee via ORM
            employee = request.env['hr.employee'].sudo().search(
                [('slack_user_id', '=', user_id)], limit=1
            )
            if not employee:
                return Response('', status=200)

            config = request.env['slack.config'].sudo().search(
                [('active', '=', True)], limit=1
            )

            # 4. Dispatch to handler
            handlers = {
                'login':  self._handle_login,
                'break':  self._handle_break,
                'resume': self._handle_resume,
                'logout': self._handle_logout,
            }
            if cmd in handlers:
                msg = handlers[cmd](employee)
                request.env.cr.commit()
                if config and config.webhook_url:
                    self._send_webhook(config.webhook_url, msg)

        except Exception as e:
            _logger.error(f"Webhook handler error: {e}")

        return Response('', status=200)
