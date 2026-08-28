# BAD: reconnect reuses old snapshot as trusted
def on_reconnect():
    book.trusted = True  # stale snapshot reused as trusted
