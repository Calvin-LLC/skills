from app.pricing import COUPONS, apply_coupon, sale_price


def line_total(sku, price, qty, coupon=None):
    unit = sale_price(sku, price)
    if coupon:
        unit = apply_coupon(unit, coupon)
        unit = unit * (1 - COUPONS.get(coupon, 0))
    return round(unit * qty, 2)


def cart_total(lines, coupon=None):
    return round(sum(line_total(sku, price, qty, coupon) for sku, price, qty in lines), 2)
