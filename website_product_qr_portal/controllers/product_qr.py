# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class ProductQRController(http.Controller):

    @http.route('/product/qr/<int:product_id>', type='http', auth='public', website=True)
    def product_qr_page(self, product_id, **kwargs):
        """
        Public page shown when customer scans product QR code.
        Displays: Product Name, Barcode, Category, Sales Price, Internal Reference.
        No login required — fully public.
        """
        product = request.env['product.template'].sudo().browse(product_id)

        if not product.exists() or not product.active:
            return request.render('website_product_qr_portal.page_product_not_found', {})

        return request.render('website_product_qr_portal.page_product_qr_detail', {
            'product': product,
        })
