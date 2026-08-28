# BAD: sequence gap logged but book stays trusted
def on_seq_gap(gap):
    print(f"gap {gap}")  # no trust invalidation
    continue_trading()
