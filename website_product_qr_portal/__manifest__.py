# -*- coding: utf-8 -*-
{
    'name': 'QR Code & Stock Availability Checker',
    'version': '19.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Generate product QR codes and let customers check live stock availability on the product page',
    'description': """
QR Code & Stock Availability Checker
=====================================
* Generate a QR Code for any product directly from the product form.
* QR Code encodes a URL — customer scans it → public page with full product details opens.
* Product details shown: Name, Barcode, Category, Price, Internal Reference, Variants.
* No login required for customers to view product info.
* Adds a "Check Availability" widget on the eCommerce product page — customers
  can enter a quantity and instantly see if it's in stock before adding to cart.
    """,
    'author': 'Anmol Patil',
    'website': 'https://github.com/anmol6213',
    'support': 'anmol621314@gmail.com',
    'license': 'LGPL-3',
    'depends': ['product', 'website', 'website_sale'],
    'external_dependencies': {
        'python': ['qrcode', 'Pillow'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/product_qr_portal.xml',
        'views/website_sale_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_product_qr_portal/static/src/js/check_availability.js',
        ],
    },
    'images': ['static/description/qr_banner.gif'],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 0,
    'currency': 'EUR',
}
