# -*- coding: utf-8 -*-
import json
import logging
import ssl
import urllib.request
from datetime import date, datetime

import certifi

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

CLAUDE_URL  = "https://api.anthropic.com/v1/messages"
GEMINI_URL  = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


class SlackConfig(models.Model):
    _inherit = 'slack.config'

    ai_enabled = fields.Boolean(
        string='Enable AI Summaries',
        default=False,
        help='Use AI to generate personalised daily summary messages',
    )
    ai_provider = fields.Selection([
        ('gemini', 'Google Gemini (Free)'),
        ('claude', 'Anthropic Claude (Paid)'),
    ], string='AI Provider', default='gemini')

    ai_api_key = fields.Char(
        string='AI API Key',
        help='Gemini: get free key at aistudio.google.com | Claude: console.anthropic.com',
        groups='base.group_system',
    )


class HrAttendanceAI(models.Model):
    _inherit = 'hr.attendance'

    ai_summary_text = fields.Text(
        string='AI Summary',
        readonly=True,
    )

    # ── Call Gemini (FREE) ─────────────────────────────────────────
    def _call_gemini(self, api_key: str, prompt: str) -> str:
        url  = f"{GEMINI_URL}?key={api_key}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 300, "temperature": 0.8}
        }).encode('utf-8')
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method='POST',
        )
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text'].strip()

    # ── Call Claude (PAID) ─────────────────────────────────────────
    def _call_claude(self, api_key: str, prompt: str) -> str:
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        }).encode('utf-8')
        req = urllib.request.Request(
            CLAUDE_URL, data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method='POST',
        )
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result['content'][0]['text'].strip()

    # ── Build prompt ───────────────────────────────────────────────
    def _build_prompt(self):
        self.ensure_one()
        config = self.env['slack.config'].sudo().search([('active','=',True)], limit=1)
        target = config.min_working_hours if config else 8.0
        hours   = int(self.net_worked_hours)
        minutes = int((self.net_worked_hours - hours) * 60)
        breaks  = int(self.total_break_duration * 60)
        gap     = round(self.net_worked_hours - target, 2)
        ci  = self.check_in.strftime('%I:%M %p')  if self.check_in  else 'N/A'
        co  = self.check_out.strftime('%I:%M %p') if self.check_out else 'N/A'
        streak = self._get_work_streak()

        return f"""
You are a friendly HR assistant sending a daily Slack attendance summary.

Employee: {self.employee_id.name}
Date: {date.today().strftime('%A, %d %B %Y')}
Check-in: {ci} | Check-out: {co}
Net working hours: {hours}h {minutes}m
Break time: {breaks} minutes
Daily target: {target}h
vs target: {'+' if gap>=0 else ''}{gap}h
Streak (consecutive days on target): {streak}

Write a SHORT (3-4 lines), warm, personalised Slack message in markdown (*bold*).
- Mention one specific number to make it personal
- If streak > 1, mention it
- End with one motivational line
- Max 2 emoji
- Reply with ONLY the message, nothing else
""".strip()

    # ── Main: generate summary ─────────────────────────────────────
    def generate_ai_summary(self) -> str:
        self.ensure_one()
        config = self.env['slack.config'].sudo().search([('active','=',True)], limit=1)

        if not config or not config.ai_enabled or not config.ai_api_key:
            return self._build_plain_summary()

        prompt = self._build_prompt()
        try:
            if config.ai_provider == 'gemini':
                summary = self._call_gemini(config.ai_api_key, prompt)
            else:
                summary = self._call_claude(config.ai_api_key, prompt)
        except Exception as e:
            _logger.warning(f"AI summary failed for {self.employee_id.name}: {e}")
            summary = self._build_plain_summary()

        self.sudo().write({'ai_summary_text': summary})
        return summary

    def _build_plain_summary(self) -> str:
        config = self.env['slack.config'].sudo().search([('active','=',True)], limit=1)
        target = config.min_working_hours if config else 8.0
        worked = self.format_worked_hours()
        breaks = int(self.total_break_duration * 60)
        ci  = self.check_in.strftime('%I:%M %p')  if self.check_in  else 'N/A'
        co  = self.check_out.strftime('%I:%M %p') if self.check_out else 'N/A'
        status = "Great work today!" if self.net_worked_hours >= target else f"Below expected {target}h"
        return (
            f"*Daily Attendance Summary*\n\n"
            f"Check-in: {ci}\nCheck-out: {co}\n"
            f"Working time: {worked}\nBreak time: {breaks}m\n\n{status}"
        )

    def _get_work_streak(self) -> int:
        config = self.env['slack.config'].sudo().search([('active','=',True)], limit=1)
        target = config.min_working_hours if config else 8.0
        today  = date.today()
        streak = 0
        for offset in range(60):
            day = today - datetime.timedelta(days=offset) if hasattr(datetime, 'timedelta') else __import__('datetime').date.today() - __import__('datetime').timedelta(days=offset)
            day_start = datetime.combine(day, datetime.min.time())
            day_end   = datetime.combine(day, datetime.max.time())
            rec = self.env['hr.attendance'].sudo().search([
                ('employee_id','=', self.employee_id.id),
                ('check_in','>=', day_start),
                ('check_in','<=', day_end),
                ('check_out','!=', False),
            ], limit=1)
            if rec and rec.net_worked_hours >= target:
                streak += 1
            else:
                break
        return streak

    @api.model
    def action_send_ai_daily_summary(self):
        config = self.env['slack.config'].sudo().search([('active','=',True)], limit=1)
        if not config or not config.send_daily_summary:
            return
        today     = date.today()
        day_start = datetime.combine(today, datetime.min.time())
        day_end   = datetime.combine(today, datetime.max.time())
        attendances = self.sudo().search([
            ('check_in','>=', day_start),
            ('check_in','<=', day_end),
        ])
        for att in attendances:
            emp = att.employee_id
            if not emp.slack_user_id:
                continue
            if att.check_out:
                message = att.generate_ai_summary()
            else:
                ci = att.check_in.strftime('%I:%M %p')
                message = (
                    f"*Attendance Alert*\n\n"
                    f"Hey {emp.name}, you checked in at {ci} "
                    f"but haven't logged out yet. Don't forget to /logout!"
                )
            try:
                payload = json.dumps({
                    "channel": emp.slack_user_id,
                    "text": message,
                }).encode('utf-8')
                req = urllib.request.Request(
                    "https://slack.com/api/chat.postMessage",
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {config.bot_token}",
                        "Content-Type": "application/json",
                    },
                    method='POST',
                )
                ssl_ctx = ssl.create_default_context(cafile=certifi.where())
                with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
                    result = json.loads(resp.read().decode('utf-8'))
                    if not result.get('ok'):
                        _logger.warning(f"Slack DM failed for {emp.name}: {result}")
            except Exception as e:
                _logger.error(f"Error sending summary to {emp.name}: {e}")
