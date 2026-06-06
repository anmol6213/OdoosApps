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
