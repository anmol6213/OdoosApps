from odoo import models, fields, api
from .utils import get_vol, qty_to_pieces, pieces_to_qty


class StockMoveLine(models.Model):
    _inherit = 'stock.move'

    x_studio_pieces_1 = fields.Float(
        string='Pieces',
        compute='_compute_pieces',
        store=True,
        readonly=False,
        digits=(16, 2),
    )

    @api.depends('quantity', 'product_id')
    def _compute_pieces(self):
        for rec in self:
            if rec.env.context.get('vpp_qty_from_pieces'):
                continue
            vol = get_vol(rec.product_id.name)
            if vol <= 0:
                rec.x_studio_pieces_1 = 0.0
                continue
            expected = qty_to_pieces(rec.quantity, vol)
            if rec.x_studio_pieces_1 != expected:
                rec.x_studio_pieces_1 = expected

    @api.onchange('x_studio_pieces_1')
    def _onchange_pieces(self):
        for rec in self:
            if not rec.x_studio_pieces_1:
                continue
            vol = get_vol(rec.product_id.name)
            if vol <= 0:
                continue
            expected_pieces = qty_to_pieces(rec.quantity, vol)
            if abs(rec.x_studio_pieces_1 - expected_pieces) > 0.01:
                rec.with_context(vpp_qty_from_pieces=True).quantity = \
                    pieces_to_qty(rec.x_studio_pieces_1, vol)
