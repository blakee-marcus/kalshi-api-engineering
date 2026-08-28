# BAD: reduce_only with good_till_canceled (margin API rejects)
order = {"ticker": "PF_X", "reduce_only": True, "time_in_force": "good_till_canceled"}
