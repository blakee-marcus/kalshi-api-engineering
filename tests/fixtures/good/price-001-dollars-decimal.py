# GOOD: parse fixed-point price as Decimal, no division
from decimal import Decimal
price_dollars = "0.5600"
price = Decimal(price_dollars)  # => Decimal('0.5600')
