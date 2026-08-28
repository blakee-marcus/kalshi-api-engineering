# GOOD: sequence gap invalidates trust
def on_seq_gap(gap):
    book.trust = UNTRUSTED
    resnapshot()
