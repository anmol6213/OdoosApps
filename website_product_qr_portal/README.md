# Generate Product QR Code — Odoo 19

## Features
- Generate QR Code for any product that has a barcode set
- QR Code encodes the product barcode (customers scan → get barcode info)
- Validation error if barcode is missing — no silent failures
- Success notification after QR generation
- Works on Odoo 19 Community and Enterprise

## Installation

### 1. Install Python dependency
Run this on your Odoo server:
```bash
pip install qrcode[pil]
```

### 2. Copy module to addons
```bash
cp -r website_product_qr_portal /path/to/your/odoo/custom_addons/
```

### 3. Update Apps List
In Odoo: Settings → Activate Developer Mode → Apps → Update Apps List

### 4. Install the module
Search for "Generate Product QR Code" and click Install.

## Usage
1. Open any Product (Inventory > Products > select a product)
2. Make sure the **Barcode** field is filled
3. Click the **Generate QR Code** button
4. The QR Code image appears in the QR Code field
5. Share/print the QR code — customers scan it to get the barcode

## Error Handling
| Situation | What happens |
|-----------|-------------|
| Barcode not set | UserError popup: "Please set the Barcode..." |
| qrcode library missing | UserError popup with pip install instructions |
| Any unexpected error | UserError with full error message — nothing crashes silently |

## Technical Notes
- Field: `qr_code_image` (Binary, stored as attachment)
- Model: `product.template` (inherits)
- Odoo version: 19.0
- Python libs: `qrcode[pil]`, `Pillow`
