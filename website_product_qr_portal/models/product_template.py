# -*- coding: utf-8 -*-

import base64
import logging
from io import BytesIO

from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    _logger.warning(
        "website_product_qr_portal: 'qrcode' library not found. "
        "Install it with: pip install qrcode[pil]"
    )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qr_code_image = fields.Binary(
        string='QR Code',
        attachment=True,
        readonly=True,
        help='QR Code containing a link to full product details page.'
    )

    def _make_qr_image(self, url):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
        
    # def action_generate_qr_code(self):
    #     if not QR_AVAILABLE:
    #         raise UserError(_(
    #             "The 'qrcode' Python library is not installed.\n"
    #             "Please run:  pip install qrcode[pil]"
    #         ))
    
    #     self.ensure_one()
    
    #     # 🔥 ADD THIS CHECK
    #     if self.qr_code_image:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': _('Already Generated'),
    #                 'message': _('QR Code is already generated for "%s".') % self.name,
    #                 'sticky': False,
    #                 'type': 'warning',
    #             },
    #         }
    
    #     try:
    #         base_url = self.env['ir.config_parameter'].sudo().get_param(
    #             'web.base.url', ''
    #         ).rstrip('/')
    #         url = "{}/product/qr/{}".format(base_url, self.id)
    
    #         self.sudo().write({
    #             'qr_code_image': self._make_qr_image(url)
    #         })
    
    #         _logger.info("QR generated for '%s' -> %s", self.name, url)
    
    #     except Exception as exc:
    #         raise UserError(_("QR generation failed: %s") % str(exc))
    
    #     # ✅ success → reload
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'reload',
    #     }

    def action_generate_qr_code(self):
        if not QR_AVAILABLE:
            raise UserError(_(
                "The 'qrcode' Python library is not installed.\n"
                "Please run: pip install qrcode[pil]"
            ))
    
        self.ensure_one()
    
        if self.qr_code_image:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Already Generated'),
                    'message': _('QR Code is already generated for "%s".') % self.name,
                    'sticky': False,
                    'type': 'warning',
                },
            }
    
        try:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url', ''
            ).rstrip('/')
    
            # Website Product URL
            if not self.website_url:
                raise UserError(_("Website URL is not available for this product."))
    
            product_url = base_url + self.website_url
    
            self.sudo().write({
                'qr_code_image': self._make_qr_image(product_url)
            })
    
            _logger.info(
                "QR generated for '%s' -> %s",
                self.name,
                product_url
            )
    
        except Exception as exc:
            raise UserError(_("QR generation failed: %s") % str(exc))
    
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # def action_generate_qr_code(self):
    #     """
    #     Generate QR Code directly — no barcode dependency.
    #     QR encodes a URL to product detail page (shows all variants & barcodes).
    #     """
    #     if not QR_AVAILABLE:
    #         raise UserError(_(
    #             "The 'qrcode' Python library is not installed.\n"
    #             "Please run:  pip install qrcode[pil]"
    #         ))

    #     self.ensure_one()

    #     try:
    #         base_url = self.env['ir.config_parameter'].sudo().get_param(
    #             'web.base.url', ''
    #         ).rstrip('/')
    #         url = "{}/product/qr/{}".format(base_url, self.id)
    #         self.sudo().write({'qr_code_image': self._make_qr_image(url)})
    #         _logger.info("QR generated for '%s' -> %s", self.name, url)
    #     except Exception as exc:
    #         raise UserError(_("QR generation failed: %s") % str(exc))

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'reload',
    #         'params': {
    #             'title': _('QR Code Generated'),
    #             'message': _('QR Code generated for "%s".') % self.name,
    #             'sticky': False,
    #             'type': 'success',
    #         },
    #     }


