# -*- coding: utf-8 -*-

import json
import logging
import ssl
import urllib.request
from datetime import datetime
from pytz import timezone as pytz_timezone

from odoo import http, fields
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class SlackAttendanceController(http.Controller):
    """Slack Slash Command Controller for Attendance"""
    
    IST = pytz_timezone('Asia/Kolkata')

    def _utc_to_ist(self, utc_time):
        return utc_time.astimezone(self.IST)

    def _send_webhook(self, url, message):
        """Send webhook - SSL verification disabled for Odoo.sh compatibility"""
        try:
            data = json.dumps({"text": message}).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            # ✅ KEY FIX: Disable SSL verification (Odoo.sh compatible)
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            
            urllib.request.urlopen(req, timeout=2, context=ssl_ctx)
            _logger.info("✅ Webhook sent successfully")
            
        except Exception as e:
            _logger.warning(f"Webhook failed: {e}")

    def _get_config(self):
        """Get grace & min break minutes from config"""
        request.env.cr.execute("""
            SELECT login_grace_minutes, min_break_minutes
            FROM slack_config WHERE active = true LIMIT 1
        """)
        row = request.env.cr.fetchone()
        return (row[0] or 0, row[1] or 0) if row else (0, 0)

    def _handle_login(self, employee):
        from datetime import timedelta
        Attendance = request.env['hr.attendance'].sudo()
        existing = Attendance.search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], limit=1)
        
        if existing:
            return f"*{employee.name}*\nAlready logged in since {self._utc_to_ist(existing.check_in).strftime('%I:%M %p')}"
        
        now_utc = fields.Datetime.now()

        # ✅ Grace minutes: actual check_in time = now - grace_minutes
        grace_minutes, _ = self._get_config()
        check_in_utc = now_utc - timedelta(minutes=grace_minutes)

        Attendance.create({
            'employee_id': employee.id,
            'check_in': check_in_utc,
            'slack_created': True
        })

        # Display the adjusted time to user
        display_time = self._utc_to_ist(check_in_utc)
        return f"*{employee.name}*\nLogged in at {display_time.strftime('%I:%M %p')}"

    def _handle_break(self, employee):
        Attendance = request.env['hr.attendance'].sudo()
        attendance = Attendance.search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], limit=1)
        
        if not attendance:
            return f"*{employee.name}*\nPlease login first"
        if attendance.get_active_break():
            return f"*{employee.name}*\nAlready on break"
        
        request.env['attendance.break'].sudo().create({
            'employee_id': employee.id,
            'attendance_id': attendance.id,
            'break_start': fields.Datetime.now()
        })
        return f"*{employee.name}*\nBreak started"
    
    def _handle_resume(self, employee):
        from datetime import timedelta
        Attendance = request.env['hr.attendance'].sudo()
        attendance = Attendance.search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], limit=1)
        
        if not attendance:
            return f"*{employee.name}*\nPlease login first"
        
        active_break = attendance.get_active_break()
        if not active_break:
            return f"*{employee.name}*\nNot on break"
        
        now_utc = fields.Datetime.now()
        break_duration_minutes = (now_utc - active_break.break_start).total_seconds() / 60

        _, min_break = self._get_config()

        if break_duration_minutes < min_break:
            # ✅ Save record but mark as excluded (not counted in working hours)
            active_break.write({
                'break_end': now_utc,
                'is_counted': False   # Not counted in working hours
            })
            return f"*{employee.name}*\nResumed (break under {min_break} min — not counted)"
        else:
            # ✅ Save record and count it
            active_break.write({
                'break_end': now_utc,
                'is_counted': True
            })
            return f"*{employee.name}*\nBreak ended, resumed work"

    def _handle_logout(self, employee):
        Attendance = request.env['hr.attendance'].sudo()
        attendance = Attendance.search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], limit=1)
        
        if not attendance:
            return f"*{employee.name}*\nNot logged in"
        if attendance.get_active_break():
            return f"*{employee.name}*\nResume from break first"
        
        now_utc = fields.Datetime.now()
        attendance.write({'check_out': now_utc})
        return f"*{employee.name}*\nLogged out at {self._utc_to_ist(now_utc).strftime('%I:%M %p')}"

    @http.route('/slack/attendance', type='http', auth='public', methods=['POST'], csrf=False, save_session=False)
    def slack_attendance_webhook(self, **kwargs):
        
        cmd = kwargs.get("command", "").replace("/", "")
        user_id = kwargs.get("user_id")
        
        _logger.info(f"📥 /{cmd} from {user_id}")
        
        try:
            request.env.cr.execute("""
                SELECT e.id, e.name, c.webhook_url
                FROM hr_employee e, slack_config c
                WHERE e.slack_user_id = %s AND c.active = true
                LIMIT 1
            """, (user_id,))
            
            row = request.env.cr.fetchone()
            if not row:
                return Response('', status=200)
            
            emp_id, emp_name, webhook = row
            emp = request.env['hr.employee'].sudo().browse(emp_id)
            
            handlers = {
                'login': self._handle_login,
                'break': self._handle_break,
                'resume': self._handle_resume,
                'logout': self._handle_logout
            }
            
            if cmd in handlers:
                msg = handlers[cmd](emp)
                request.env.cr.commit()
                if webhook:
                    self._send_webhook(webhook, msg)
        
        except Exception as e:
            _logger.error(f"Error: {e}")
        
        return Response('', status=200)
