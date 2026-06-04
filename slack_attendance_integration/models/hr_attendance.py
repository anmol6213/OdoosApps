# -*- coding: utf-8 -*-
from odoo import models, fields, api
from pytz import timezone, utc
from datetime import datetime

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
        string='Total Working Hours',
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
        for record in self:
            counted_breaks = record.break_ids.filtered(lambda b: b.is_counted)
            record.total_break_duration = sum(counted_breaks.mapped('duration'))

    @api.depends('check_in', 'check_out', 'total_break_duration')
    def _compute_worked_hours(self):
        """worked_hours = gross - breaks"""
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                delta = attendance.check_out - attendance.check_in
                gross = delta.total_seconds() / 3600.0
                attendance.worked_hours = gross - attendance.total_break_duration
            else:
                attendance.worked_hours = False

    @api.depends('check_in', 'check_out')
    def _compute_net_worked_hours(self):
        """Total Working Hours = gross"""
        for record in self:
            if record.check_in and record.check_out:
                delta = record.check_out - record.check_in
                record.net_worked_hours = delta.total_seconds() / 3600.0
            else:
                record.net_worked_hours = 0.0

    def _get_expected_hours_from_calendar(self):
        self.ensure_one()
        calendar = self.employee_id.resource_calendar_id
        if not calendar:
            return 8.0
        tz = timezone(calendar.tz)
        check_in_local = utc.localize(self.check_in).astimezone(tz)
        date = check_in_local.date()
        day_start = tz.localize(datetime.combine(date, datetime.min.time()))
        day_end = tz.localize(datetime.combine(date, datetime.max.time()))
        work_intervals = calendar._work_intervals_batch(
            day_start, day_end,
            resources=self.employee_id.resource_id
        )
        return sum(
            (stop - start).total_seconds() / 3600
            for start, stop, _ in work_intervals[self.employee_id.resource_id.id]
        )

    def _update_overtime(self, attendance_domain=None):
        """Override: overtime = worked_hours - expected (breaks वजा)"""
        super()._update_overtime(attendance_domain)
        for attendance in self.filtered('check_out'):
            if not attendance.linked_overtime_ids:
                continue
            expected = attendance._get_expected_hours_from_calendar()
            correct_ot = max(0, attendance.worked_hours - expected)
            ot = attendance.linked_overtime_ids[0]
            ot.write({
                'duration': round(correct_ot, 3),
                'time_stop': attendance.check_out
            })

    def get_active_break(self):
        self.ensure_one()
        return self.break_ids.filtered(lambda b: not b.break_end)

    def format_worked_hours(self):
        self.ensure_one()
        hours = int(self.worked_hours)
        minutes = int((self.worked_hours - hours) * 60)
        return f"{hours}h {minutes:02d}m"



# # -*- coding: utf-8 -*-
# from odoo import models, fields, api

# class HrAttendance(models.Model):
#     """Extend hr.attendance to add break tracking and net working hours"""
#     _inherit = 'hr.attendance'

#     break_ids = fields.One2many(
#         'attendance.break',
#         'attendance_id',
#         string='Breaks'
#     )
#     total_break_duration = fields.Float(
#         string='Total Break Time (Hours)',
#         compute='_compute_break_duration',
#         store=True
#     )
#     net_worked_hours = fields.Float(
#         string='Net Working Hours',
#         compute='_compute_net_worked_hours',
#         store=True
#     )
#     slack_created = fields.Boolean(
#         string='Created via Slack',
#         default=False,
#         help='Indicates if this attendance was created via Slack'
#     )

#     @api.depends('break_ids.duration', 'break_ids.is_counted')
#     def _compute_break_duration(self):
#         """Calculate total break duration - only is_counted=True breaks"""
#         for record in self:
#             # ✅ Only count breaks where is_counted = True
#             counted_breaks = record.break_ids.filtered(lambda b: b.is_counted)
#             record.total_break_duration = sum(counted_breaks.mapped('duration'))

#     @api.depends('worked_hours', 'total_break_duration')
#     def _compute_net_worked_hours(self):
#         """Calculate net working hours (total - counted breaks)"""
#         for record in self:
#             record.net_worked_hours = record.worked_hours - record.total_break_duration

#     def get_active_break(self):
#         """Get the active (not ended) break for this attendance"""
#         self.ensure_one()
#         return self.break_ids.filtered(lambda b: not b.break_end)

#     def format_worked_hours(self):
#         """Format worked hours as 'Xh Ym'"""
#         self.ensure_one()
#         hours = int(self.net_worked_hours)
#         minutes = int((self.net_worked_hours - hours) * 60)
#         return f"{hours}h {minutes:02d}m"
