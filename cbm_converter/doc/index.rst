CBM Converter
=============

Auto-convert CBM (cubic meter) quantity to Pieces for construction materials —
directly inside Sale Orders, Invoices, Deliveries and Return Pickings, with no
separate app or manual calculation required.

.. contents::
   :local:
   :depth: 1


Features
--------

Automatic Volume Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The product's dimensions are read straight from its name — e.g. a product
named ``Tile 600x200x225`` is parsed as 600 mm x 200 mm x 225 mm, and the
per-piece volume (in m³) is derived from that automatically. No separate
dimension fields need to be maintained.

CBM → Pieces
~~~~~~~~~~~~

Whenever the CBM quantity changes, the **Pieces** field recomputes
automatically::

    Pieces = ceil(Quantity / Volume per piece)   if Quantity > 5
    Pieces = round(Quantity / Volume per piece, 2)   otherwise

Ceiling rounding is used for larger quantities so that a partial piece is
never under-counted.

Pieces → CBM
~~~~~~~~~~~~

Pieces can also be edited directly (in the UI). When a user changes the
**Pieces** value by hand, the quantity is recalculated the other way::

    Quantity = Pieces x Volume per piece

This bidirectional flow works without creating an update loop — the module
uses a context flag / value comparison to detect whether the change was
triggered by quantity or by pieces before recomputing.

Works Across Documents
~~~~~~~~~~~~~~~~~~~~~~

The **Pcs** column is available on:

+---------------------------+------------------------------------------------+
| Document                  | Model                                           |
+===========================+==================================================+
| Sale Order Lines          | ``sale.order.line``                             |
+---------------------------+------------------------------------------------+
| Invoice Lines             | ``account.move.line``                           |
+---------------------------+------------------------------------------------+
| Delivery / Stock Moves    | ``stock.move``                                  |
+---------------------------+------------------------------------------------+
| Return Picking Lines      | ``stock.return.picking.line``                   |
+---------------------------+------------------------------------------------+


Installation
------------

Requirements
~~~~~~~~~~~~

* Odoo 19.0
* Standard Odoo apps: ``account``, ``sale_management``, ``stock``
  (installed automatically as dependencies)

Steps
~~~~~

1. Copy the ``cbm_converter`` folder into your Odoo addons path.
2. Restart the Odoo server (or update the apps list).
3. In Odoo, go to **Apps** → search for *CBM Converter* → click **Install**.
4. Open any Sale Order, Invoice, Delivery, or Return Picking — the **Pcs**
   column appears next to the Quantity column (toggle via the optional
   columns menu if hidden).


Product Naming Convention
--------------------------

For the volume to be detected, the product name must contain three
dimension numbers (in millimetres), each greater than 50, in any order
within the name — separated by ``x``, spaces, or both. For example:

* ``Tile 600x200x225``
* ``Block 400 x 200 x 100 Grey``

If fewer than three valid dimensions are found, the volume is treated as
zero and **Pieces** is left at ``0.0`` (no conversion is attempted).


Fields Added
------------

+-------------------------+---------------------------------------------------------+
| Field                   | Description                                              |
+=========================+===========================================================+
| ``x_studio_pieces_1``   | Computed **Pieces** field, editable, kept in sync with   |
|                         | the document's Quantity field via the CBM <-> Pieces      |
|                         | conversion logic                                          |
+-------------------------+---------------------------------------------------------+


Changelog
---------

19.0.1.0.0
~~~~~~~~~~

* Initial release
* Auto-calculates Pieces from CBM quantity on Sale Orders, Invoices and
  Deliveries
* Support for Return Picking lines
* Ceiling rounding for accurate piece counts on larger quantities
* Bidirectional conversion: Pieces -> CBM and CBM -> Pieces
* Floating point rounding fix on the CBM -> Pieces calculation


Support
-------

* GitHub: https://github.com/anmol6213
* Contact: anmol621314@gmail.com
