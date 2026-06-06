from odoo import models, fields, api
from .utils import get_vol, qty_to_pieces, pieces_to_qty


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_studio_pieces_1 = fields.Float(
        string='Pieces',
        compute='_compute_pieces',
        store=True,
        readonly=False,
        digits=(16, 2),
    )

    @api.depends('quantity', 'product_id')
    def _compute_pieces(self):
        """
        Converts quantity (CBM) to pieces automatically.
        Skipped when the user manually edits pieces to avoid overwriting.
        """
        for rec in self:
            # Skip recompute if triggered by pieces -> quantity flow
            if rec.env.context.get('vpp_qty_from_pieces'):
                continue

            vol = get_vol(rec.product_id.name)
            if vol <= 0:
                rec.x_studio_pieces_1 = 0.0
                continue

            expected = qty_to_pieces(rec.quantity, vol)

            # Only write if value changed to prevent unnecessary DB updates
            if rec.x_studio_pieces_1 != expected:
                rec.x_studio_pieces_1 = expected

    @api.onchange('x_studio_pieces_1')
    def _onchange_pieces(self):
        """
        Updates quantity (CBM) when user manually changes pieces.
        Only fires in UI, not on save, so no loop is possible.
        """
        for rec in self:
            if not rec.x_studio_pieces_1:
                continue

            vol = get_vol(rec.product_id.name)
            if vol <= 0:
                continue

            expected_pieces = qty_to_pieces(rec.quantity, vol)

            # Only update quantity if user changed pieces manually
            # (i.e. pieces value differs from what quantity would compute)
            if abs(rec.x_studio_pieces_1 - expected_pieces) > 0.01:
                rec.quantity = pieces_to_qty(rec.x_studio_pieces_1, vol)

    def write(self, vals):
        """
        Standard write override.
        No special logic needed here — compute handles quantity -> pieces,
        and onchange handles pieces -> quantity in the UI.
        """
        return super().write(vals)