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
        quantity → pieces.
        SKIPPED when:
        - user just edited pieces manually (vpp_qty_from_pieces context)
        - pieces value already matches expected (avoids rewrite loop)
        """
        for rec in self:
            # Skip if this compute was triggered by pieces→qty flow
            if rec.env.context.get('vpp_qty_from_pieces'):
                continue
            vol = get_vol(rec.product_id.name)
            if vol <= 0:
                rec.x_studio_pieces_1 = 0.0
                continue
            expected = qty_to_pieces(rec.quantity, vol)
            # Only update if value actually changed - prevents unnecessary recompute
            if rec.x_studio_pieces_1 != expected:
                rec.x_studio_pieces_1 = expected

    @api.onchange("x_studio_pieces_1")
    def _onchange_pieces(self):
        for rec in self:
            if not rec.x_studio_pieces_1:
                continue
            vol = get_vol(rec.product_id.name)
            if vol <= 0:
                continue
            expected_pieces = qty_to_pieces(rec.quantity, vol)
            # फक्त user ने manually बदलले तरच quantity update कर
            if abs(rec.x_studio_pieces_1 - expected_pieces) > 0.01:
                rec.quantity = pieces_to_qty(rec.x_studio_pieces_1, vol)

    def write(self, vals):
        """
        If quantity is written directly (not from pieces flow),
        ensure compute runs normally.
        If pieces triggered this write, pass context through.
        """
        if 'quantity' in vals and not self.env.context.get('vpp_qty_from_pieces'):
            # Normal quantity write - compute will run and update pieces
            return super().write(vals)
        return super().write(vals)
