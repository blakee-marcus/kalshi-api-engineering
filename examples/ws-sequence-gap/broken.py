book = {"trusted": True, "levels": {}}

def on_seq_gap(gap):
    # BUG: logs the gap but keeps trading on a broken book
    print(f"gap {gap}")
    continue_trading()
