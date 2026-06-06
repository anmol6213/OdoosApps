from odoo import models, fields, api
import math


def get_vol(product_name):
    name = product_name or ""
    parts = name.lower().replace("x", " ").split()
    dims = []
    for part in parts:
        if part.isdigit() and int(part) > 50:
            dims.append(int(part))
        if len(dims) == 3:
            break
    if len(dims) != 3:
        return 0.0
    return (dims[0] * dims[1] * dims[2]) / 1_000_000_000.0


# def qty_to_pieces(qty, vol):
#     if vol <= 0 or qty <= 0:
#         return 0.0
#     raw = qty / vol
#     return float(math.ceil(raw)) if qty > 5 else round(raw, 2)
def qty_to_pieces(qty, vol):
    if vol <= 0 or qty <= 0:
        return 0.0
    raw = qty / vol
    raw = round(raw, 4)  # floating point fix!
    return float(math.ceil(raw)) if qty > 5 else round(raw, 2)


def pieces_to_qty(pieces, vol):
    if vol <= 0 or pieces <= 0:
        return 0.0
    return pieces * vol


class StockReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    x_studio_pieces_1 = fields.Float(
        string='Pieces',
        compute='_compute_pieces',
        store=False,
        readonly=False,
        digits=(16, 2),
    )

    @api.depends('quantity', 'product_id')
    def _compute_pieces(self):
        for rec in self:
            vol = get_vol(rec.product_id.name)
            rec.x_studio_pieces_1 = qty_to_pieces(rec.quantity, vol) if vol > 0 else 0.0

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
                rec.quantity = pieces_to_qty(rec.x_studio_pieces_1, vol)
