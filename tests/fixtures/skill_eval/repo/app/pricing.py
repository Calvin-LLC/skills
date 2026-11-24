SALE = {"mug": 0.20, "cap": 0.10}
COUPONS = {"WELCOME10": 0.10, "VIP25": 0.25}


def sale_price(sku, price):
    return round(price * (1 - SALE.get(sku, 0)), 2)


def apply_coupon(price, code):
    return round(price * (1 - COUPONS.get(code, 0)), 2)
