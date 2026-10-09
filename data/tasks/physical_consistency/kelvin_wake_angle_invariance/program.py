# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_wake
def wake_spans_match(keys, span):
    """Match if both the 6 and 20 knot boats read with the same wake spread."""
    speed_keys = [''.join(c for c in str(k) if c.isdigit())
          for k in (keys or {}).get('answers') or []]
    span_reads = [str(s).strip().lower()[:1] for s in (span or {}).get('answers') or []]
    got = {speed_keys[i]: span_reads[i] for i in range(min(len(speed_keys), len(span_reads)))}
    ok = sorted(got) == ['20', '6'] and all(v == 's' for v in got.values())
    return {'state': 'match' if ok else 'off', 'n': len(got),
            'verdict': '; '.join('%s kn=%s' % (k, got[k]) for k in sorted(got))
                       or 'nothing read'}

# end of code_wake

# shared code: code_crest
def crest_gaps_match(keys, gaps):
    """Match if the 20 knot wake reads with far crest gaps and the 6 knot one close."""
    speed_keys = [''.join(c for c in str(k) if c.isdigit())
          for k in (keys or {}).get('answers') or []]
    gap_reads = [str(g).strip().lower()[:1] for g in (gaps or {}).get('answers') or []]
    got = {speed_keys[i]: gap_reads[i] for i in range(min(len(speed_keys), len(gap_reads)))}
    ok = len(got) == 2 and got.get('20') == 'f' and got.get('6') == 'c'
    return {'state': 'match' if ok else 'off', 'n': len(got),
            'verdict': '; '.join('%s kn=%s' % (k, got[k]) for k in sorted(got))
                       or 'nothing read'}

# end of code_crest
