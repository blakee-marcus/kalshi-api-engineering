# GOOD: reconnect resets to untrusted
def on_reconnect():
    book.trusted = False
    request_fresh_snapshot()
