# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AttendanceBreak(models.Model):
    _name = 'attendance.break'
    _description = 'Attendance Break'
    _order = 'break_start desc'
    _rec_name = 'display_name'

    # =====================
    # FIELDS
    # =====================
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True
    )
    attendance_id = fields.Many2one(
        'hr.attendance',
        string='Attendance',
        required=True,
        ondelete='cascade',
        index=True
    )
    break_start = fields.Datetime(
        string='Break Start',
        required=True,
        default=fields.Datetime.now
    )
    break_end = fields.Datetime(
        string='Break End'
    )
    duration = fields.Float(
        string='Duration (Hours)',
        compute='_compute_duration',
        store=True
    )

    # ✅ NEW: is_counted field
    is_counted = fields.Boolean(
        string='Counted in Working Hours',
        default=True,
        help='If False, this break will NOT be deducted from working hours'
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    # =====================
    # COMPUTE METHODS
    # =====================
    @api.depends('break_start', 'break_end')
    def _compute_duration(self):
        for record in self:
            if record.break_start and record.break_end:
                delta = record.break_end - record.break_start
                record.duration = delta.total_seconds() / 3600.0
            else:
                record.duration = 0.0

    @api.depends('employee_id', 'break_start')
    def _compute_display_name(self):
        for record in self:
            if record.employee_id and record.break_start:
                record.display_name = (
                    f"{record.employee_id.name} - "
                    f"{record.break_start.strftime('%Y-%m-%d %H:%M')}"
                )
            elif record.employee_id:
                record.display_name = f"{record.employee_id.name} - Break"
            else:
                record.display_name = "Attendance Break"
