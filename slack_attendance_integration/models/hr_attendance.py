# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrAttendance(models.Model):
    """Extend hr.attendance to add break tracking and net working hours"""
    _inherit = 'hr.attendance'

    break_ids = fields.One2many(
        'attendance.break',
        'attendance_id',
        string='Breaks'
    )
    total_break_duration = fields.Float(
        string='Total Break Time (Hours)',
        compute='_compute_break_duration',
        store=True
    )
    net_worked_hours = fields.Float(
        string='Net Working Hours',
        compute='_compute_net_worked_hours',
        store=True
    )
    slack_created = fields.Boolean(
        string='Created via Slack',
        default=False,
        help='Indicates if this attendance was created via Slack'
    )

    @api.depends('break_ids.duration', 'break_ids.is_counted')
    def _compute_break_duration(self):
        """Calculate total break duration - only is_counted=True breaks"""
        for record in self:
            # ✅ Only count breaks where is_counted = True
            counted_breaks = record.break_ids.filtered(lambda b: b.is_counted)
            record.total_break_duration = sum(counted_breaks.mapped('duration'))

    @api.depends('worked_hours', 'total_break_duration')
    def _compute_net_worked_hours(self):
        """Calculate net working hours (total - counted breaks)"""
        for record in self:
            record.net_worked_hours = record.worked_hours - record.total_break_duration

    def get_active_break(self):
        """Get the active (not ended) break for this attendance"""
        self.ensure_one()
        return self.break_ids.filtered(lambda b: not b.break_end)

    def format_worked_hours(self):
        """Format worked hours as 'Xh Ym'"""
        self.ensure_one()
        hours = int(self.net_worked_hours)
        minutes = int((self.net_worked_hours - hours) * 60)
        return f"{hours}h {minutes:02d}m"
