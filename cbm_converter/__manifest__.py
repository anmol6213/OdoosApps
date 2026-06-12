# -*- coding: utf-8 -*-
{
    'name': 'CBM Converter',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Construction',
    'summary': 'Auto-convert CBM quantity to Pieces for construction materials',
    'description': """
CBM Converter
========================================
* Auto-calculates Pieces from CBM quantity
* Works on Sale Orders, Invoices, and Deliveries
* Supports all products with dimensions in name (e.g. 600x200x225)
* Ceiling rounding for accurate piece counts
* Bidirectional: Pieces → CBM and CBM → Pieces
* No loop — store=False with smart onchange logic
    """,
    'author': 'Anmol Patil',
    'website': 'https://github.com/anmol6213',
    'support': 'anmol621314@gmail.com',
    'license': 'LGPL-3',
    'depends': ['account', 'sale_management', 'stock'],
    'data': [
        'views/cbm_views.xml',
    ],
    'images': ['static/description/banner (2).png'],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 0,
    'currency': 'EUR',
}
