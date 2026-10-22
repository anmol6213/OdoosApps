# CBM Converter

CBM Converter is an Odoo 19 module designed to convert cubic meter (CBM) quantities into piece counts for construction and material-related products.

It is especially useful for businesses that manage products by dimensions and need automatic conversion between volume and piece count during sales, invoicing, and stock operations.

## Overview

This module automatically calculates the number of pieces from a CBM value based on product dimensions found in the product name, such as:

- 600x200x225
- 1200x300x50
- 500x250x100

It supports both directions:

- CBM → Pieces
- Pieces → CBM

This helps simplify workflows where inventory and accounting data are managed in different units.

## Features

- Auto-calculates piece quantity from CBM value
- Works on sale orders, invoices, and stock documents
- Supports products with dimensions embedded in the product name
- Uses ceiling rounding for accurate piece counting
- Supports bidirectional conversion logic
- Prevents conversion loops using smart onchange logic
- Suitable for construction material and inventory workflows
- Integrated with Odoo accounting, sales, and stock models

## Use Case

In construction and material businesses, products are often described using dimensions but sold or tracked as volume or count. This module helps bridge that gap by converting values automatically and accurately.

Example:
- Product name: 600x200x225
- Quantity entered: 1.5 CBM
- System calculates the equivalent piece count automatically

## Installation

1. Clone the repository:

```bash
git clone https://github.com/anmol6213/OdoosApps.git
