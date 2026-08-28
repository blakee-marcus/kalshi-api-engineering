# GOOD: Decimal for money math
from decimal import Decimal
def total(p, q):
    return Decimal(p) * Decimal(q)
