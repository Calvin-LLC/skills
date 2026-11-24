# Shop

A small shop backend. `app/pricing.py` holds sale and coupon rules, `app/cart.py` adds up a cart, and `web/` is the checkout page.

Run `python -c "from app.cart import cart_total; print(cart_total([('mug', 10.0, 2)], 'WELCOME10'))"` to price a cart.
