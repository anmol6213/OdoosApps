# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    """Extend hr.employee to add Slack user ID mapping"""
    _inherit = 'hr.employee'

    slack_user_id = fields.Char(
        string='Slack User ID',
        help='Slack User ID for attendance integration (e.g., U01234ABCDE)',
        index=True,
        copy=False
    )

    @api.constrains('slack_user_id')
    def _check_unique_slack_user_id(self):
        """Ensure Slack User ID is unique across employees"""
        for record in self:
            if record.slack_user_id:
                duplicate = self.search([
                    ('slack_user_id', '=', record.slack_user_id),
                    ('id', '!=', record.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        f'Slack User ID "{record.slack_user_id}" is already assigned to {duplicate.name}!'
                    )

    @api.model
    def find_by_slack_id(self, slack_user_id):
        """Find employee by Slack User ID"""
        employee = self.search([('slack_user_id', '=', slack_user_id)], limit=1)
        if not employee:
            raise ValidationError(
                f'No employee found with Slack User ID: {slack_user_id}. '
                'Please contact HR to link your Slack account.'
            )
        return employee