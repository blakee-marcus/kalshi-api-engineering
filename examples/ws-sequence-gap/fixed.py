book = {"trusted": False, "levels": {}}

def on_seq_gap(gap):
    # FIX: invalidate trust and demand a fresh snapshot before any decision
    book["trusted"] = False
    resnapshot()
