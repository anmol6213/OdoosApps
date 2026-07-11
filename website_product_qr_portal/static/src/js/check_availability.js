// This file handles the "Check Availability" button logic on the
// eCommerce product page (website_sale.product template).
// It fetches live stock/combination info via Odoo's public JSON-RPC
// endpoint and shows Available / Not Available to the visitor.

(function () {

    function getSelectedCombination() {
        var combination = [];
        document.querySelectorAll('select.js_variant_change').forEach(function (sel) {
            var val = parseInt(sel.value);
            if (val > 0) combination.push(val);
        });
        document.querySelectorAll('input.js_variant_change:checked').forEach(function (inp) {
            var val = parseInt(inp.value);
            if (val > 0) combination.push(val);
        });
        return combination;
    }

    // ✅ FIX: Multiple fallback methods for public users
    function getTemplateId() {
        // Method 1: h1 data attribute (admin/edit mode)
        var h1 = document.querySelector('h1[data-oe-model="product.template"]');
        if (h1) {
            var id = parseInt(h1.getAttribute('data-oe-id'));
            if (id > 0) return id;
        }

        // Method 2: URL se extract — /shop/product-name-5 → 5
        var urlMatch = window.location.pathname.match(/-(\d+)(?:\/|$)/);
        if (urlMatch) {
            var id = parseInt(urlMatch[1]);
            if (id > 0) return id;
        }

        // Method 3: form data attribute
        var form = document.querySelector('form[action*="/shop/cart/update"]');
        if (form) {
            var tid = form.dataset.product_template_id
                   || form.dataset.productTemplateId;
            if (tid) return parseInt(tid) || null;
        }

        return null;
    }

    function initAvailabilityChecker() {
        var btn = document.getElementById('avail_check_btn');
        if (!btn || btn._avail_init) return;
        btn._avail_init = true;

        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();

            var templateId = getTemplateId(); // ✅ replaces inline h1 check
            var resultDiv = document.getElementById('avail_result');

            if (!templateId) {
                resultDiv.innerHTML =
                    '<span style="color:#ef4444;">❌ Product not found</span>';
                return;
            }

            var combination = getSelectedCombination();
            console.log("templateId:", templateId, "combination:", combination);

            var qty = parseFloat(document.getElementById('avail_qty').value) || 1;
            resultDiv.innerHTML = '<span style="color:#888;">⏳ Checking...</span>';

            fetch('/website_sale/get_combination_info', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    id: 1,
                    method: 'call',
                    params: {
                        product_template_id: templateId,
                        product_id: null,
                        combination: combination,
                        add_qty: qty,
                        pricelist_id: false,
                        context: {website_sale_stock_get_quantity: true}
                    }
                })
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.result) {
                    resultDiv.innerHTML = '<span style="color:#ef4444;">❌ Not Available</span>';
                    return;
                }
                var r = data.result;
                var freeQty = r.free_qty;
                var isStorable = r.is_storable;

                console.log("resolved product_id:", r.product_id,
                            "free_qty:", freeQty,
                            "is_storable:", isStorable,
                            "requested qty:", qty);

                var qtyOk = (freeQty === null || freeQty === undefined || freeQty >= qty);
                if (!isStorable || qtyOk) {
                    resultDiv.innerHTML = '<span style="color:#22c55e;">✅ Available</span>';
                } else {
                    resultDiv.innerHTML = '<span style="color:#ef4444;">❌ Not Available</span>';
                }
            })
            .catch(function (err) {
                resultDiv.innerHTML = '<span style="color:#ef4444;">❌ Error: ' + err.message + '</span>';
            });
        });
    }

    document.addEventListener('DOMContentLoaded', initAvailabilityChecker);
    setTimeout(initAvailabilityChecker, 500);
    setTimeout(initAvailabilityChecker, 1500);
    setTimeout(initAvailabilityChecker, 3000);

})();
