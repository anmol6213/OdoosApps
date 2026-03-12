# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SlackConfig(models.Model):
    """Configuration for Slack integration credentials and settings"""
    _name = 'slack.config'
    _description = 'Slack Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Configuration Name',
        required=True,
        default='Slack Attendance Config'
    )
    signing_secret = fields.Char(
        string='Slack Signing Secret',
        required=True,
        help='Used to verify requests from Slack'
    )
    bot_token = fields.Char(
        string='Slack Bot Token',
        required=True,
        help='Bot User OAuth Token (starts with xoxb-)'
    )
    webhook_url = fields.Char(
        string='Incoming Webhook URL',
        required=True,
        help='Webhook URL for posting messages (starts with https://hooks.slack.com/services/...)'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    min_working_hours = fields.Float(
        string='Minimum Working Hours',
        default=8.0,
        help='Minimum expected working hours per day'
    )
    send_daily_summary = fields.Boolean(
        string='Send Daily Summary',
        default=True,
        help='Send attendance summary at end of day'
    )
    summary_time = fields.Float(
        string='Summary Time (Hours)',
        default=18.0,
        help='Time to send daily summary (24-hour format, e.g., 18.0 for 6:00 PM)'
    )

    # ✅ NEW FIELD 1: Login Grace Minutes
    login_grace_minutes = fields.Integer(
        string='Login Grace Minutes',
        default=5,
        help='Subtract these minutes from actual login time. E.g. if set to 5, login at 10:00 shows as 9:55'
    )

    # ✅ NEW FIELD 2: Minimum Break Minutes
    min_break_minutes = fields.Integer(
        string='Minimum Break Minutes',
        default=5,
        help='Break will only be counted if duration is more than these minutes. E.g. if set to 5, breaks under 5 min are ignored'
    )

    @api.constrains('signing_secret', 'bot_token', 'webhook_url')
    def _check_credentials(self):
        """Validate that credentials are not empty"""
        for record in self:
            if not record.signing_secret or not record.bot_token or not record.webhook_url:
                raise ValidationError('Slack credentials cannot be empty!')

    @api.constrains('login_grace_minutes', 'min_break_minutes')
    def _check_minutes(self):
        for record in self:
            if record.login_grace_minutes < 0:
                raise ValidationError('Login Grace Minutes cannot be negative!')
            if record.min_break_minutes < 0:
                raise ValidationError('Minimum Break Minutes cannot be negative!')

    @api.model
    def get_active_config(self):
        """Get the active Slack configuration"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            raise ValidationError('No active Slack configuration found. Please configure Slack settings first.')
        return config

    @api.model
    def action_send_daily_summary(self):
        """Send daily attendance summary to employees via Slack"""
        import requests
        from datetime import date, datetime
        
        config = self.get_active_config()
        
        if not config.send_daily_summary:
            return
        
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        Attendance = self.env['hr.attendance'].sudo()
        attendances = Attendance.search([
            ('check_in', '>=', today_start),
            ('check_in', '<=', today_end),
        ])
        
        for attendance in attendances:
            employee = attendance.employee_id
            
            if not employee.slack_user_id:
                continue
            
            if attendance.check_out:
                worked_time = attendance.format_worked_hours()
                break_time = int(attendance.total_break_duration * 60)
                
                message = (
                    f"📊 *Daily Attendance Summary*\n\n"
                    f"Check-in: {attendance.check_in.strftime('%I:%M %p')}\n"
                    f"Check-out: {attendance.check_out.strftime('%I:%M %p')}\n"
                    f"Working time: {worked_time}\n"
                    f"Break time: {break_time}m\n"
                )
                
                if attendance.net_worked_hours < config.min_working_hours:
                    message += f"\n⚠️ Below expected {config.min_working_hours}h"
                else:
                    message += "\n✅ Great work today!"
            else:
                message = (
                    f"⚠️ *Attendance Alert*\n\n"
                    f"You checked in at {attendance.check_in.strftime('%I:%M %p')} "
                    f"but haven't checked out yet."
                )
            
            try:
                url = "https://slack.com/api/chat.postMessage"
                headers = {
                    "Authorization": f"Bearer {config.bot_token}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "channel": employee.slack_user_id,
                    "text": message
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if not response.json().get('ok'):
                    _logger.warning(f"Failed to send summary to {employee.name}: {response.text}")
            except Exception as e:
                _logger.error(f"Error sending Slack summary to {employee.name}: {str(e)}")
