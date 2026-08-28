# BAD: fixed-point price divided by 100
price_dollars = "0.5600"
price = float(price_dollars) / 100  # => 0.0056 (100x too small)
