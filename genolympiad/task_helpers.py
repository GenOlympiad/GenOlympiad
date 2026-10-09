"""Helpers that several tasks share: reading listed answers, counting confirmed boxes, cutting boxed
containers into cells, and small checks on numbers and words."""
import difflib
import math
import re
import struct


def count_confirmed_cutouts(node):
    """Count the cut-outs whose answer starts with yes."""
    ans = (node or {}).get('answers') or []
    n = sum(1 for a in ans if str(a).strip().lower().startswith('y'))
    return {'n': n, 'asked': len(ans),
            'verdict': '%d of the %d cut-outs confirmed their unit -> counted %d'
                       % (n, len(ans), n)}


def split_listed_items(text):
    """Split a listed answer into items and the running-total lines it also wrote."""
    import re
    s = str(text if text is not None else '')
    s = s.replace('\r', '\n')
    items, dropped = [], []
    for raw in re.split(r'[;\n]+', s):
        t = ' '.join(str(raw).split()).strip()
        t = re.sub(r'^[\-\*•·]+\s*', '', t)
        t = re.sub(r'^\(?\d{1,3}[\.\)]\s+', '', t)
        t = t.strip(' .,:')
        if not t:
            continue
        low = t.lower()
        if re.fullmatch(r'[\d,\. ]+', low):
            dropped.append(t)
            continue
        if re.match(r'^(total|in total|altogether|so there|there (is|are)|that (is|makes)|'
                    r'count|counting|answer|sum|list|items?)\b', low):
            dropped.append(t)
            continue
        items.append(t)
    return items, dropped


def classify_short_answer(text):
    """Say whether an answer is blank, means none, or means zero."""
    import re
    t = ' '.join(str(text if text is not None else '').split()).strip(' .,:').lower()
    if not t:
        return 'blank'
    if re.fullmatch(r'(none|nothing|no|there (is|are) none|none here|none at all|0)', t):
        return 'empty'
    if re.fullmatch(r'zero|none touch(es)? it|no line', t):
        return 'zero'
    return ''


def unreadable_count_result(node):
    """A copy of a read that did not come back, marked unreadable, or None."""
    if isinstance(node, dict) and (node.get('refused') or node.get('unreadable')
                                  or node.get('no_read')):
        out = dict(node)
        out.update({'answers': [None], 'counts': [], 'items': [], 'n': None, 'text': '',
                    'seq': [], 'unreadable': True,
                    'verdict': 'the read itself did not come back; nothing was counted'})
        return out
    return None


def answers_per_box(node):
    """The answers of a read, one per box."""
    if isinstance(node, dict):
        a = node.get('answers')
        if a is None:
            a = [None]
        return list(a)
    if isinstance(node, (list, tuple)):
        return list(node)
    return [node]


def copy_record(node):
    """A copy of a read's record, or an empty one."""
    return dict(node) if isinstance(node, dict) else {}


def count_listed_items(node, empty_as='0'):
    """Count, per box, the items the judge VLM listed."""
    held = unreadable_count_result(node)
    if held is not None:
        return held
    out, counts, items_per_box, notes = [], [], [], []
    refused, why = False, []
    for raw in answers_per_box(node):
        tok = classify_short_answer(raw)
        if tok == 'blank':
            out.append('')
            counts.append(None)
            items_per_box.append([])
            notes.append('nothing came back for this box')
            continue
        if tok == 'empty':
            out.append(str(empty_as))
            counts.append(None if empty_as == 'none' else 0)
            items_per_box.append([])
            notes.append('the reader reported none of them here')
            continue
        if tok == 'zero':
            out.append('0')
            counts.append(0)
            items_per_box.append([])
            notes.append('the reader reported the thing is there but carries none')
            continue
        its, dropped = split_listed_items(raw)
        if not its and dropped:
            refused = True
            why.append('the reader answered with a tally (%r) instead of enumerating' % dropped[0][:40])
            out.append('')
            counts.append(None)
            items_per_box.append([])
            notes.append('a tally came back where items were asked for')
            continue
        n = len(its)
        out.append(str(n))
        counts.append(n)
        items_per_box.append(its)
        notes.append('%d item(s) enumerated%s'
                     % (n, (', %d running-total line(s) ignored' % len(dropped)) if dropped else ''))
    first = counts[0] if counts else None
    res = copy_record(node)
    res.update({'answers': out, 'counts': counts, 'items': items_per_box,
                'n': first, 'text': out[0] if out else '', 'seq': out,
                'refused': refused,
                'refusal': '; '.join(why) if refused else '',
                'verdict': 'counted in code from the enumerated items: ' + '; '.join(notes)})
    return res


def count_items_per_label(node, labels):
    """Count the listed items that carry each label."""
    import re
    held = unreadable_count_result(node)
    if held is not None:
        return held
    ls = [str(x) for x in labels]
    per = dict((l, 0) for l in ls)
    unlabelled, smuggled = [], []
    for raw in answers_per_box(node):
        if classify_short_answer(raw) in ('empty', 'blank'):
            continue
        its, _ = split_listed_items(raw)
        for t in its:
            low = t.lower()
            hit = [l for l in ls if re.search(r'(?<![a-z0-9])' + re.escape(l.lower()) + r'(?![a-z0-9])', low)]
            if len(hit) != 1:
                unlabelled.append(t)
                continue
            rest = re.sub(r'(?<![a-z0-9])' + re.escape(hit[0].lower()) + r'(?![a-z0-9])', ' ', low)
            if re.search(r'\d', rest):
                smuggled.append(t)
                continue
            per[hit[0]] += 1
    seq = [per[l] for l in ls]
    txt = ', '.join(str(v) for v in seq)
    res = copy_record(node)
    res.update({'answers': [txt], 'text': txt, 'seq': seq, 'n': None, 'per_slot': per,
            'unlabelled': unlabelled, 'smuggled': smuggled,
            'refused': bool(smuggled) and not any(seq),
            'refusal': ('the reader answered with per-slot tallies (%r) instead of enumerating'
                        % smuggled[:2]) if smuggled and not any(seq) else '',
            'verdict': 'grouped in code by each item\'s own label: ' + txt
                       + ('; %d item(s) carried no single label' % len(unlabelled) if unlabelled else '')
                       + ('; %d item(s) were per-slot tallies and were not counted' % len(smuggled)
                          if smuggled else '')})
    return res


def list_items_per_box(node):
    """The listed items of each box, passed on unjudged."""
    held = unreadable_count_result(node)
    if held is not None:
        return held
    out, per = [], []
    for raw in answers_per_box(node):
        tok = classify_short_answer(raw)
        if tok in ('empty', 'zero'):
            out.append('none')
            per.append([])
            continue
        if tok == 'blank':
            out.append('')
            per.append([])
            continue
        its, _ = split_listed_items(raw)
        out.append(', '.join(its))
        per.append(its)
    res = copy_record(node)
    res.update({'answers': out, 'items': per, 'text': out[0] if out else '',
                'n': len(per[0]) if per else None, 'seq': out, 'refused': False,
                'verdict': 'the enumerated items, passed on unjudged: ' + ' | '.join(out)})
    return res


def answer_or_text_per_box(node):
    """The answers of a read, one per box, falling back to its text."""
    if isinstance(node, dict):
        a = node.get('answers')
        if a is None:
            a = [node.get('text')] if node.get('text') is not None else [None]
        return list(a)
    if isinstance(node, (list, tuple)):
        return list(node)
    return [node]


def unreadable_mapped_result(node):
    """A copy of a read that did not come back, marked unreadable, or None."""
    if isinstance(node, dict) and (node.get('refused') or node.get('unreadable')
                                   or node.get('no_read')):
        out = dict(node)
        out.update({'answers': [None], 'text': '', 'seq': [], 'n': None, 'items': [],
                    'unreadable': True, 'refused': True,
                    'verdict': 'the read itself did not come back; nothing was judged'})
        return out
    return None


def is_shrug(text):
    """Whether an answer says the judge VLM could not tell."""
    import re
    t = ' '.join(str(text if text is not None else '').split()).strip(' .,:!').lower()
    if not t:
        return True
    return bool(re.search(
        r"(?:^|\b)(?:i )?(?:can(?:no|')t|cannot|unable to) (?:tell|say|read|make out|determine)\b"
        r"|\bnot (?:readable|legible|clear|visible|possible to)\b"
        r"|\b(?:unclear|illegible|unreadable|indeterminate|ambiguous)\b"
        r"|^(?:n/?a|unknown|no answer|don't know|dont know|not sure|unsure)$", t))


def split_enumerated_items(text):
    """Split an enumerated answer into items and the running-total lines it also wrote."""
    import re
    s = str(text if text is not None else '').replace('\r', '\n')
    items, dropped = [], []
    for raw in re.split(r'[;\n]+', s):
        t = ' '.join(str(raw).split()).strip()
        t = re.sub(r'^[\-\*•·]+\s*', '', t)
        t = re.sub(r'^\(?\d{1,3}[\.\)]\s+', '', t)
        t = t.strip(' .,:')
        if not t:
            continue
        low = t.lower()
        if re.fullmatch(r'[\d,\. ]+', low):
            dropped.append(t)
            continue
        if re.match(r'^(total|in total|altogether|so there|there (is|are)|that (is|makes)|'
                    r'count|counting|answer|sum|list|items?)\b', low):
            dropped.append(t)
            continue
        items.append(t)
    return items, dropped


def last_table_token(text, table):
    """The token of the table word that appears last in an answer."""
    import re
    s = ' '.join(str(text if text is not None else '').split()).strip().lower()
    if not s:
        return ''
    best, at = '', -1
    for row in table:
        words, token = row[0], row[1]
        for w in words:
            for m in re.finditer(r'(?<![a-z0-9])' + re.escape(str(w).lower()) + r'(?![a-z0-9])', s):
                if m.start() > at:
                    best, at = token, m.start()
    return best


UNLISTED = 'unlisted'


def map_answer_to_token(node, table, unknown=UNLISTED):
    """Map each box's answer to the token of the table word it names."""
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    out, why = [], []
    for raw in answer_or_text_per_box(node):
        tok = last_table_token(raw, table)
        out.append(tok if tok else str(unknown))
        why.append('%r -> %s' % (str(raw)[:40], tok or 'no listed word'))
    res = copy_record(node)
    res.update({'answers': out, 'text': out[0] if out else '', 'seq': out,
                'n': None, 'refused': False,
                'verdict': 'the reader named a form; the code mapped it: ' + '; '.join(why)})
    return res


def all_items_satisfy(node, table, all_token, some_token, none_token=None):
    """Whether every enumerated item maps to a satisfying token, per box."""
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    out, per, why = [], [], []
    for raw in answer_or_text_per_box(node):
        items, _dropped = split_enumerated_items(raw)
        flags = []
        for it in items:
            tok = last_table_token(it, table)
            if tok == '':
                continue
            flags.append(tok == 'T')
        per.append(flags)
        if not flags:
            out.append(UNLISTED if none_token is None else str(none_token))
            why.append('no listed item came back')
            continue
        ok = all(flags)
        out.append(str(all_token) if ok else str(some_token))
        why.append('%d item(s), %d of them satisfying -> %s'
                   % (len(flags), sum(1 for f in flags if f),
                      all_token if ok else some_token))
    res = copy_record(node)
    res.update({'answers': out, 'text': out[0] if out else '', 'seq': out,
                'per_item': per, 'n': len(per[0]) if per else None, 'refused': False,
                'verdict': 'each enumerated item was checked on its own and the AND taken in '
                           'code: ' + '; '.join(why)})
    return res


def any_item_satisfies(node, table, any_token, none_token, empty_token=None):
    """Whether any enumerated item maps to a satisfying token, per box."""
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    out, per, why = [], [], []
    for raw in answer_or_text_per_box(node):
        items, _ = split_enumerated_items(raw)
        flags = []
        for it in items:
            tok = last_table_token(it, table)
            if tok == '':
                continue
            flags.append(tok == 'T')
        per.append(flags)
        if not flags:
            out.append(UNLISTED if empty_token is None else str(empty_token))
            why.append('no listed item came back')
            continue
        hit = any(flags)
        out.append(str(any_token) if hit else str(none_token))
        why.append('%d item(s), %d of them satisfying -> %s'
                   % (len(flags), sum(1 for f in flags if f), any_token if hit else none_token))
    res = copy_record(node)
    res.update({'answers': out, 'text': out[0] if out else '', 'seq': out,
                'per_item': per, 'n': len(per[0]) if per else None, 'refused': False,
                'verdict': 'the OR over the enumerated items was taken in code: ' + '; '.join(why)})
    return res


def pick_smallest_or_largest_figure(node, which='min'):
    """The smallest or largest figure the judge VLM copied, per box."""
    import re
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    out, why = [], []
    for raw in answer_or_text_per_box(node):
        s = ' '.join(str(raw if raw is not None else '').split()).strip().lower()
        if re.fullmatch(r'blank|none|nothing|no needle|n/a|-', s.strip(' .,:')):
            out.append('blank')
            why.append('the reader reported no needle on this dial')
            continue
        nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', s)]
        if not nums:
            out.append('')
            why.append('%r carried no figure' % s[:40])
            continue
        v = min(nums) if which == 'min' else max(nums)
        out.append(('%g' % v))
        why.append('%s of %s -> %g' % (which, nums, v))
    res = copy_record(node)
    res.update({'answers': out, 'text': out[0] if out else '', 'seq': out,
                'n': None, 'refused': False,
                'verdict': 'the reader copied the printed figures; the code picked: '
                           + '; '.join(why)})
    return res


def select_item_numbers(node, table, want='T', joiner=', '):
    """The numbers of the enumerated items that map to the wanted token, per box."""
    import re
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    out, per = [], []
    for raw in answer_or_text_per_box(node):
        items, _ = split_enumerated_items(raw)
        keep = []
        for it in items:
            tok = last_table_token(it, table)
            if tok != want:
                continue
            m = re.search(r'\d+', it)
            if m:
                keep.append(m.group(0).lstrip('0') or '0')
        keep = sorted(set(keep), key=lambda s: (len(s), s))
        per.append(keep)
        out.append(joiner.join(keep))
    res = copy_record(node)
    res.update({'answers': out, 'text': out[0] if out else '', 'seq': out[0] if out else '',
                'picked': per, 'n': len(per[0]) if per else None, 'refused': False,
                'verdict': 'the labels the code selected off the enumeration: '
                           + ' | '.join(o or 'none' for o in out)})
    return res


def map_items_to_tokens(node, table, joiner=' '):
    """One token per enumerated item, in the order listed, per box."""
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    out, per = [], []
    for raw in answer_or_text_per_box(node):
        items, _ = split_enumerated_items(raw)
        toks = []
        for it in items:
            tok = last_table_token(it, table)
            if tok:
                toks.append(tok)
        per.append(toks)
        out.append(joiner.join(toks))
    res = copy_record(node)
    res.update({'answers': out, 'text': out[0] if out else '', 'seq': out,
                'per_item': per, 'n': len(per[0]) if per else None, 'refused': False,
                'verdict': 'one word per enumerated item, in the order enumerated: '
                           + ' | '.join(o or 'none' for o in out)})
    return res


def check_permitted_characters(node, allowed, ok_token, bad_token):
    """Whether a transcribed name uses only the permitted characters."""
    import re
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    out, why = [], []
    ok_set = set(str(allowed))
    for raw in answer_or_text_per_box(node):
        s = str(raw if raw is not None else '')
        lines = [x.strip() for x in s.replace('\r', '\n').split('\n') if x.strip()]
        s = lines[-1] if lines else ''
        s = re.sub(r'(?i)^\s*(?:the\s+)?(?:stored\s+|file\s+|archive\s+)?name(?:\s+is)?\s*:\s*'
                   r'|^\s*(?:answer|output|result|it\s+reads|reads)\s*:\s*', '', s)
        for q in ('"', "'", '`'):
            if len(s) >= 2 and s[0] == q and s[-1] == q:
                s = s[1:-1]
        s = s.strip()
        if not s or is_shrug(s):
            out.append(str(bad_token))
            why.append('%r is a shrug, not a transcription' % s[:40])
            continue
        bad = sorted(set(ch for ch in s if ch not in ok_set and not ch.isalnum()))
        clean = not bad
        out.append(str(ok_token) if clean else str(bad_token))
        why.append('%r -> %s%s' % (s[:40], 'clean' if clean else 'not clean',
                                   ('' if clean else ' (%s)' % ''.join(bad))))
    res = copy_record(node)
    res.update({'answers': out, 'text': out[0] if out else '', 'seq': out,
                'n': None, 'refused': False,
                'verdict': 'the transcription was checked against the permitted characters in '
                           'code: ' + '; '.join(why)})
    return res


def check_shadow_directions(node, table, apart_min, apart_max, two_token, other_token, none_token):
    """Whether the enumerated shadows point the wanted number of hours apart."""
    import re
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    out, per, why = [], [], []
    for raw in answer_or_text_per_box(node):
        s = str(raw if raw is not None else '')
        if last_table_token(s, table) == 'NONE' and not re.search(r'\d', s):
            out.append(str(none_token))
            per.append([])
            why.append('the reader reported no shadow at all')
            continue
        hours = []
        for it, _ in [(x, 0) for x in split_enumerated_items(s)[0]]:
            m = re.findall(r'\b(1[0-2]|[1-9])\b', it)
            if m:
                hours.append(int(m[-1]))
        per.append(hours)
        if len(hours) < 2:
            out.append(str(other_token))
            why.append('%d shadow(s) enumerated' % len(hours))
            continue
        gaps = []
        for i in range(len(hours)):
            for j in range(i + 1, len(hours)):
                d = abs(hours[i] - hours[j]) % 12
                gaps.append(min(d, 12 - d))
        widest = max(gaps) if gaps else 0
        ok = float(apart_min) <= widest <= float(apart_max)
        out.append(str(two_token) if ok else str(other_token))
        why.append('hours %s, widest separation %d on the dial -> %s'
                   % (hours, widest, two_token if ok else other_token))
    res = copy_record(node)
    res.update({'answers': out, 'text': out[0] if out else '', 'seq': out,
                'hours': per, 'n': len(per[0]) if per else None, 'refused': False,
                'verdict': 'shadows enumerated with their own directions; counted and separated '
                           'in code: ' + '; '.join(why)})
    return res


def count_enumerated_items(node, empty_as='0'):
    """Count, per box, the items the judge VLM enumerated."""
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    import re
    out, counts, per, why = [], [], [], []
    refused, refusal = False, []
    for raw in answer_or_text_per_box(node):
        s = ' '.join(str(raw if raw is not None else '').split()).strip(' .,:').lower()
        if not s:
            out.append('')
            counts.append(None)
            per.append([])
            why.append('nothing came back for this box')
            continue
        if re.fullmatch(r'(none|nothing|no|zero|0|none here|there (is|are) none)', s):
            out.append(str(empty_as))
            counts.append(0 if empty_as != 'none' else None)
            per.append([])
            why.append('the reader reported none of them here')
            continue
        if is_shrug(s):
            refused = True
            refusal.append('the reader shrugged (%r) instead of enumerating' % s[:40])
            out.append('')
            counts.append(None)
            per.append([])
            why.append('a shrug came back where items were asked for')
            continue
        items, dropped = split_enumerated_items(raw)
        if not items and dropped:
            refused = True
            refusal.append('the reader answered with a tally (%r) instead of enumerating'
                           % dropped[0][:40])
            out.append('')
            counts.append(None)
            per.append([])
            why.append('a tally came back where items were asked for')
            continue
        out.append(str(len(items)))
        counts.append(len(items))
        per.append(items)
        why.append('%d item(s) enumerated' % len(items))
    res = copy_record(node)
    res.update({'answers': out, 'counts': counts, 'items': per,
                'n': counts[0] if counts else None, 'text': out[0] if out else '', 'seq': out,
                'refused': refused, 'refusal': '; '.join(refusal),
                'verdict': 'counted in code from the enumerated items: ' + '; '.join(why)})
    return res


def compare_printed_figure(node, want, hit_token, miss_token, markers=None, marker_token=None,
                 unknown=UNLISTED):
    """Whether the figure copied off the picture equals the wanted value."""
    import re
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    out, why = [], []
    for raw in answer_or_text_per_box(node):
        s = ' '.join(str(raw if raw is not None else '').split()).strip(' .,:')
        tok = last_table_token(s, markers or [])
        if tok:
            out.append(str(marker_token if marker_token is not None else tok))
            why.append('%r matched an authored marker' % s[:40])
            continue
        nums = re.findall(r'-?\d+(?:\.\d+)?', s)
        if not nums:
            out.append(str(unknown))
            why.append('%r carried no figure' % s[:40])
            continue
        v = float(nums[0])
        ok = abs(v - float(want)) < 1e-9
        out.append(str(hit_token) if ok else str(miss_token))
        why.append('read %g, the leg is about %g -> %s'
                   % (v, float(want), hit_token if ok else miss_token))
    res = copy_record(node)
    res.update({'answers': out, 'text': out[0] if out else '', 'seq': out,
                'n': None, 'refused': False,
                'verdict': 'the reader copied a printed figure; the code compared it: '
                           + '; '.join(why)})
    return res


def compare_transcribed_marks(node, none_token, one_token, same_token, diff_token, blank_marker='',
                blank_token=None):
    """Whether the transcribed lines carry no mark, one mark, the same mark or different marks."""
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    out, per, why = [], [], []
    for raw in answer_or_text_per_box(node):
        s = ' '.join(str(raw if raw is not None else '').split()).strip()
        if is_shrug(s):
            out.append('')
            per.append([])
            why.append('the reader shrugged; nothing was transcribed to compare')
            continue
        items, _ = split_enumerated_items(s)
        marks = []
        blanks = 0
        for it in items:
            t = it.strip().strip('"').strip("'")
            if not t:
                continue
            if blank_marker and blank_marker.lower() in t.lower():
                blanks += 1
                marks.append('')
                continue
            if t.lower().startswith('no-such-line') or t.lower() == 'none':
                continue
            marks.append(''.join(ch for ch in t.lower() if ch.isalnum()))
        per.append(marks)
        if not marks:
            out.append(str(none_token))
            why.append('no line of that time came back')
        elif len(marks) == 1:
            out.append(str(one_token))
            why.append('one line only')
        elif blanks == len(marks):
            out.append(str(blank_token if blank_token is not None else none_token))
            why.append('%d lines, none of them carrying a mark' % len(marks))
        elif len(set(marks)) == 1:
            out.append(str(same_token))
            why.append('%d lines, all carrying %r' % (len(marks), marks[0]))
        else:
            out.append(str(diff_token))
            why.append('%d lines carrying %s' % (len(marks), marks))
    res = copy_record(node)
    res.update({'answers': out, 'text': out[0] if out else '', 'seq': out,
                'marks': per, 'n': len(per[0]) if per else None, 'refused': False,
                'verdict': 'the transcribed marks were compared in code: ' + '; '.join(why)})
    return res


def judge_read_back(node, table, default_token, empty_token=UNLISTED):
    """Classify what was read back off a surface: a table marker, readable words or nothing."""
    held = unreadable_mapped_result(node)
    if held is not None:
        return held
    out, why = [], []
    for raw in answer_or_text_per_box(node):
        s = ' '.join(str(raw if raw is not None else '').split()).strip(' .,:')
        tok = last_table_token(s, table)
        if tok:
            out.append(tok)
            why.append('%r matched an authored marker -> %s' % (s[:40], tok))
            continue
        if is_shrug(s):
            out.append(str(empty_token))
            why.append('%r is a shrug, not a read-back' % s[:40])
            continue
        if any(ch.isalnum() for ch in s):
            out.append(str(default_token))
            why.append('%r came back as readable words -> %s' % (s[:40], default_token))
            continue
        out.append(str(empty_token))
        why.append('nothing was transcribed')
    res = copy_record(node)
    res.update({'answers': out, 'text': out[0] if out else '', 'seq': out,
                'n': None, 'refused': False,
                'verdict': 'what came off the surface, judged in code: ' + '; '.join(why)})
    return res


def to_float(x):
    """The value as a float."""
    return float(x)


def squash_spaces(v):
    """The text with runs of white space made single."""
    return ' '.join(str('' if v is None else v).split()).strip()


def answer_head(v):
    """The start of an answer, lower case, without leading marks."""
    return squash_spaces(v).lower().lstrip('*_"\'.,:;-([ ')


def says_yes(v):
    """Whether an answer starts with yes."""
    return answer_head(v).startswith('yes')


def says_no(v):
    """Whether an answer starts with no, none or nothing."""
    h = answer_head(v)
    return h.startswith('no') or h.startswith('none') or h.startswith('nothing')


def sweep_holds_nothing_banned(sw, named, banned):
    """Whether any box of the sweep holds something the picture may not carry."""
    sw = sw or {}
    geom = list(sw.get('geometry') or [])
    try:
        n = int(sw.get('n_confirmed') or 0)
    except Exception:
        n = 0
    if not n:
        n = len(geom)
    try:
        allow = int(sw.get('allow') or 0)
    except Exception:
        allow = 0
    if n <= allow:
        return {'clean': 'yes', 'refused': False, 'boxes': n, 'hits': 0, 'unproven': 0,
                'verdict': 'the sweep put no rectangle on anything, so the premise holds'}
    va = list((named or {}).get('answers') or [])
    ba = list((banned or {}).get('answers') or [])
    hits, cleared, unproven, seen = [], 0, 0, []
    for i in range(n):
        v = squash_spaces(va[i]) if i < len(va) else ''
        b = squash_spaces(ba[i]) if i < len(ba) else ''
        got = bool(v) and not says_no(v)
        seen.append('%d=%s' % (i + 1, (v or '(no value came back)')[:70]))
        if says_yes(b) and got:
            hits.append(i + 1)
        elif says_no(b) or (v and not got):
            cleared += 1
        else:
            unproven += 1
    read_back = ' | '.join(seen)
    if len(hits) > allow:
        return {'clean': 'no', 'refused': False, 'boxes': n, 'hits': len(hits),
                'unproven': unproven, 'read_back': read_back,
                'verdict': 'rectangle %s was read back and confirmed to hold what the page is '
                           'not allowed to carry -- %s'
                           % (','.join(str(h) for h in hits), read_back)}
    if unproven:
        return {'clean': None, 'refused': True, 'boxes': n, 'hits': 0, 'unproven': unproven,
                'read_back': read_back,
                'verdict': '%d of %d rectangles could not be read back, so the accusation is '
                           'unproven -> abstain rather than zero the task -- %s'
                           % (unproven, n, read_back)}
    return {'clean': 'yes', 'refused': False, 'boxes': n, 'hits': 0, 'unproven': 0,
            'read_back': read_back,
            'verdict': 'every rectangle was read back and none of them holds what the page is '
                       'not allowed to carry -- %s' % read_back}


def sweep_banned_by_both_wordings(sw, named, banned, carrier):
    """Like sweep_holds_nothing_banned, but a box counts only when two wordings both say so."""
    sw = sw or {}
    geom = list(sw.get('geometry') or [])
    try:
        n = int(sw.get('n_confirmed') or 0)
    except Exception:
        n = 0
    if not n:
        n = len(geom)
    try:
        allow = int(sw.get('allow') or 0)
    except Exception:
        allow = 0
    if n <= allow:
        return {'clean': 'yes', 'refused': False, 'boxes': n, 'hits': 0, 'unproven': 0,
                'corroborated': 0, 'uncorroborated': 0,
                'verdict': 'the sweep put no rectangle on anything, so the premise holds'}
    va = list((named or {}).get('answers') or [])
    ba = list((banned or {}).get('answers') or [])
    ca = list((carrier or {}).get('answers') or [])
    hits, unsettled, cleared, unproven, seen, why = [], [], 0, 0, [], []
    denied = 0
    for i in range(n):
        v = squash_spaces(va[i]) if i < len(va) else ''
        b = squash_spaces(ba[i]) if i < len(ba) else ''
        c = squash_spaces(ca[i]) if i < len(ca) else ''
        got = bool(v) and not says_no(v)
        seen.append('%d=%s' % (i + 1, (v or '(no value came back)')[:70]))
        if says_yes(b) and got:
            if says_yes(c):
                hits.append(i + 1)
                why.append('%d: both wordings say the page is not allowed to carry this' % (i + 1))
            elif says_no(c):
                cleared += 1
                denied += 1
                why.append('%d: the second wording says this belongs on the page, so the first '
                           'read stands uncorroborated and does not convict' % (i + 1))
            else:
                unsettled.append(i + 1)
                why.append('%d: the second wording did not come back, so the accusation is '
                           'neither stood up nor knocked down' % (i + 1))
        elif says_no(b) or (v and not got):
            cleared += 1
        else:
            unproven += 1
    read_back = ' | '.join(seen)
    note = '; '.join(why)
    if len(hits) > allow:
        return {'clean': 'no', 'refused': False, 'boxes': n, 'hits': len(hits),
                'unproven': unproven, 'corroborated': len(hits), 'unsettled': len(unsettled),
                'denied': denied, 'read_back': read_back, 'corroboration': note,
                'verdict': 'rectangle %s was read back and TWO independently worded reads BOTH '
                           'confirm it holds what the page is not allowed to carry -- %s'
                           % (','.join(str(h) for h in hits), read_back)}
    if unproven or len(hits) + len(unsettled) > allow:
        return {'clean': None, 'refused': True, 'boxes': n, 'hits': 0,
                'unproven': unproven + len(unsettled), 'corroborated': len(hits),
                'unsettled': len(unsettled),
                'denied': denied, 'read_back': read_back, 'corroboration': note,
                'verdict': '%d of %d rectangles were left unproven -- either nothing came back, '
                           'or one wording accused it and the other never answered -- so the '
                           'task abstains rather than being zeroed -- %s'
                           % (unproven + len(unsettled), n, read_back)}
    return {'clean': 'yes', 'refused': False, 'boxes': n, 'hits': 0, 'unproven': 0,
            'corroborated': len(hits), 'unsettled': len(unsettled), 'denied': denied,
            'read_back': read_back, 'corroboration': note,
            'verdict': 'no rectangle was stood up by both wordings, so nothing on the page is '
                       'shown to be what it is not allowed to carry -- %s' % read_back}


def sweep_banned_unless_count_disagrees(sw, named, banned, carrier):
    """Like sweep_banned_by_both_wordings, but withheld when the sweep and its own count disagree."""
    r = sweep_banned_by_both_wordings(sw, named, banned, carrier)
    if r.get('clean') != 'no':
        return r
    sw = sw or {}
    info = sw.get('sweep') or {}
    cnt = info.get('count_check_final')
    if cnt is None:
        cnt = info.get('count_check')
    try:
        cnt = None if cnt is None else int(cnt)
    except Exception:
        cnt = None
    try:
        n = int(sw.get('n_confirmed') or 0)
    except Exception:
        n = 0
    slack = 2
    if cnt is None or n <= cnt + slack:
        return r
    out = dict(r)
    out['clean'] = None
    out['refused'] = True
    out['hits'] = 0
    out['count_check'] = cnt
    out['boxes_confirmed'] = n
    out['witness_split'] = True
    out['verdict'] = ('the sweep drew %d rectangles but its own independent count of the same '
                      'thing came back %d -- the two readings the gate is built on contradict '
                      'each other, so nothing here is verified and the task abstains rather '
                      'than being zeroed -- %s' % (n, cnt, r.get('read_back') or ''))
    return out


def normalise_text(s):
    """Lower case text with hyphens, stars and underscores turned into spaces."""
    return " ".join(str(s or "").lower().replace("-", " ").replace("*", "").replace("_", " ").split())


def find_whole_word(tok, hay, start=0):
    """The position of a whole word in a text, or -1."""
    m = re.compile(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(normalise_text(tok))).search(hay, start)
    return m.start() if m else -1


def pick_state(ans, table):
    """The one state whose key words appear in an answer."""
    a = normalise_text(ans)
    if not a:
        return {"state": None, "refused": True}
    hit = [s for s, keys in table.items() if any(normalise_text(k) in a for k in keys)]
    if len(hit) == 1:
        return {"state": hit[0], "refused": False}
    return {"state": None, "refused": True}


NUMBER_WORDS = {"zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,
            "nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,
            "sixteen":16}


NUMBER_WORD_PATTERN = (r"(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen"
       r"|fourteen|fifteen|sixteen)")


NUMBER_PATTERN = r"(?:\d{1,3}|" + NUMBER_WORD_PATTERN + r")"


UNIT_PATTERN = (r"(?:mm|cm|km|nm|um|micron|microns|millimet(?:re|er)s?|centimet(?:re|er)s?|"
         r"met(?:re|er)s?|kilomet(?:re|er)s?|inch|inches|ft|feet|foot|yard|yards|mile|miles|"
         r"kg|kgs|gram|grams|mg|lb|lbs|oz|ton|tons|tonne|tonnes|"
         r"ml|litre|litres|liter|liters|gallon|gallons|"
         r"sec|secs|second|seconds|min|mins|minute|minutes|hour|hours|hr|hrs|day|days|"
         r"deg|degree|degrees|percent|psi|bar|kpa|mpa|kn|newton|newtons|"
         r"volt|volts|amp|amps|watt|watts|kw|hz|rpm|px|pixel|pixels|pt|"
         r"mph|kph|am|pm|celsius|fahrenheit)")


CONCLUSION_MARK = (r"(?:therefore|thus|hence|in\s+total|in\s+all|all\s+in\s+all|in\s+summary|in\s+conclusion|"
         r"overall|altogether|to\s+summari[sz]e|so|that\s+makes|that\s+gives|which\s+makes|"
         r"which\s+gives|counting\s+these|the\s+answer\s+is|final\s+answer|"
         r"(?:i|we)\s+(?:have|count|counted|make\s+it)|in\s+short)")


CONCLUSION_CLAUSE = r"(?:^|[.:;]\s+|,\s+|\*\s+)" + CONCLUSION_MARK + r"\b[^.;:]{0,160}"


STRONG_COUNT_PATTERNS = [
    r"\\boxed\s*\{\s*(\d{1,3})\s*\}",
    r"(?:final\s+answer|the\s+answer|the\s+count|the\s+number|the\s+total|the\s+tally)"
    r"\s*(?:is|are|:|=)\s*\$?\s*(%s)\b" % NUMBER_PATTERN,
    r"\bthere\s+(?:are|is|were|was)\s+(?:only\s+|just\s+|exactly\s+|about\s+|a\s+total\s+of\s+|"
    r"in\s+total\s+)?(%s)\b" % NUMBER_PATTERN,
    r"(?:a\s+)?total\s+of\s+(%s)\b" % NUMBER_PATTERN,
    r"\b(%s)\s+in\s+total\b" % NUMBER_PATTERN,
    r"\bin\s+total\s*,?\s*(?:there\s+(?:are|is)\s+)?(%s)\b" % NUMBER_PATTERN,
    r"\baltogether\s*,?\s*(%s)\b" % NUMBER_PATTERN,
    r"\b(%s)\s+altogether\b" % NUMBER_PATTERN,
    r"\b(?:count|number|total|tally)\s*(?:is|:|=)\s*(%s)\b" % NUMBER_PATTERN,
    r"=\s*(%s)\s+[a-z]" % NUMBER_PATTERN,
    r"\b(?:i|we)\s+(?:can\s+|could\s+|am\s+able\s+to\s+|are\s+able\s+to\s+)?(?:\w+ly\s+)?"
    r"(?:see|count|counted|find|found|identify|identified|make\s+out|have)"
    r"\s+(?:only\s+|just\s+|exactly\s+|a\s+total\s+of\s+)?(%s)\b" % NUMBER_PATTERN,
]


WEAK_COUNT_PATTERNS = [
    r"\b(?:all|only|just|exactly|both)?\s*(%s)\s+of\s+(?:the|these|those|them|which|it)\b" % NUMBER_PATTERN,
    r"\b(?:all|both)\s+(%s)\s+[a-z]" % NUMBER_PATTERN,
    r"\b(%s)\s+(?:separate|distinct|individual)\b" % NUMBER_PATTERN,
    r"\b(%s)\s+(?:are|is)\s+(?:visible|present|shown|standing|open|in\s+view|fitted|hung|left|there)\b" % NUMBER_PATTERN,
    r"^\s*(%s)\s*[.!]?\s*$" % NUMBER_PATTERN,
    r"\bis\s+(%s)\s*[.!]?\s*$" % NUMBER_PATTERN,
    r"\b(?:reach|reaches|reached|pass|passes|passed|extend|extends|extended|cross|crosses|"
    r"crossed|clear|clears|cleared|cover|covers|covered|go|goes|went)\s+"
    r"(?:past|beyond|over|up\s+to)\s+(%s)\b" % NUMBER_PATTERN,
]


NUMBER_NEAR_MARK = r"\b(%s)\b" % NUMBER_PATTERN


NUMBER_BEFORE_PLURAL = r"\b(%s)\s+(?:[a-z]+\s+){0,3}[a-z]+s\b" % NUMBER_PATTERN


ZERO_COUNT_PATTERNS = [
    r"there\s+(?:are|is|were|was)\s+(?:now\s+|currently\s+|absolutely\s+)?(?:no|none|not\s+any|zero)\b",
    r"there\s+(?:aren'?t|isn'?t|are\s+not|is\s+not|were\s+not|weren'?t)\s+any\b",
    r"\bthere\s+(?:are|is)\s+none\b",
    r"\bnone\s+of\s+(?:the|these|those|them|which|it)\b",
    r"\bnone\s+(?:are|is|were|was|have|has|appear|appears|seem|seems)\b",
    r"\bnone\s+at\s+all\b",
    r"^\s*none\b",
    r"\bnot\s+a\s+single\b",
    r"\bneither\s+of\b",
    r"\b(?:i|we)\s+(?:can|could)\s+see\s+no\b",
    r"\b(?:i|we)\s+(?:cannot|can\s*not|do\s+not|don'?t|did\s+not|didn'?t)\s+see\s+any\b",
    r"\bthe\s+answer\s+(?:is|:)\s*(?:none|zero)\b",
    r"\bzero\b",
    r"\bno\s+[a-z][a-z ]{0,44}?\s+(?:are|is)\s+"
    r"(?:visible|present|shown|standing|open|fitted|hung|used|left|crossed|twisted|chocked|rolled)\b",
]


def parenthesis_spans(a):
    """The spans of the parenthesised parts of a text."""
    spans, stack = [], []
    for i, ch in enumerate(a):
        if ch == "(":
            stack.append(i)
        elif ch == ")" and stack:
            spans.append((stack.pop(), i))
    return spans


def inside_spans(spans, pos):
    """Whether a position falls inside any span."""
    return any(s <= pos <= e for s, e in spans)


def sentence_spans(a):
    """The spans of the sentences of a text."""
    out, start = [], 0
    for m in re.finditer(r"(?<!\d)[.!?;]\s+", a):
        out.append((start, m.start()))
        start = m.end()
    out.append((start, len(a)))
    return [(s, e) for s, e in out if e > s]


def conclusion_mark_spans(a):
    """The spans of the concluding clauses (therefore, in total, ...) of a text."""
    return [(m.start(), m.end()) for m in re.finditer(CONCLUSION_CLAUSE, a)]


def looks_enumerated(a):
    """Whether a text is a numbered or bulleted list."""
    n = len(re.findall(r"(?:^|[.:;]\s+)\d{1,2}\s*[.)]\s+[a-z*]", a))
    n += len(re.findall(r"(?:^|\s)\*\s+\*?\*?[a-z]", a))
    return n >= 2


def conclusion_spans(a):
    """The spans where a text states its conclusion."""
    ss = sentence_spans(a)
    sp = list(conclusion_mark_spans(a))
    if ss:
        sp.append(ss[0])
        if not looks_enumerated(a):
            sp.append(ss[-1])
    return sp


def number_word_value(tok):
    """The value of a number written in digits or words."""
    tok = tok.strip()
    return NUMBER_WORDS[tok] if tok in NUMBER_WORDS else int(tok)


def count_stated_in_answer(ans):
    """The count an answer states, preferring its concluding sentence."""
    a = normalise_text(ans)
    if not a:
        return {"state": None, "refused": True}
    parens = parenthesis_spans(a)

    def plausible_count_at(a_, p, end):
        if inside_spans(parens, p):
            return False
        if re.match(r"\s*" + UNIT_PATTERN + r"(?![a-z])", a_[end:end + 24]):
            return False
        if re.match(r"\.\d", a_[end:end + 2]):
            return False
        if p >= 1 and re.search(r"\d\.$", a_[max(0, p - 2):p]):
            return False
        if re.match(r"\s*[.)]\s+[a-z*]", a_[end:end + 4]) and (
                p == 0 or re.search(r"(?:^|[.:;*]\s+)$", a_[max(0, p - 3):p])):
            return False
        if re.search(r"\bnot\s+(?:a\s+)?(?:single\s+)?$", a_[max(0, p - 18):p]):
            return False
        return True

    def scan_patterns(pats, hay_spans=None):
        best = None
        for pat in pats:
            for m in re.finditer(pat, a):
                p, end = m.start(1), m.end(1)
                if hay_spans is not None and not inside_spans(hay_spans, p):
                    continue
                if not plausible_count_at(a, p, end):
                    continue
                if best is None or p >= best[0]:
                    best = (p, number_word_value(m.group(1)))
        return best

    marks = conclusion_mark_spans(a)
    cands = []

    if marks:
        got = scan_patterns(STRONG_COUNT_PATTERNS + WEAK_COUNT_PATTERNS, marks)
        if got is None:
            for s, e in marks:
                for m in re.finditer(NUMBER_NEAR_MARK, a[s:e]):
                    p, end = s + m.start(1), s + m.end(1)
                    if plausible_count_at(a, p, end):
                        got = (p, number_word_value(m.group(1))) if (got is None or p > got[0]) else got
                        break
        if got is not None:
            cands.append(got)

    got = scan_patterns(STRONG_COUNT_PATTERNS)
    if got is not None:
        cands.append(got)
    if cands:
        return {"state": max(cands, key=lambda x: x[0])[1], "refused": False}

    got = scan_patterns(WEAK_COUNT_PATTERNS)
    if got is not None:
        return {"state": got[1], "refused": False}


    concl = conclusion_spans(a)
    for pat in ZERO_COUNT_PATTERNS:
        for m in re.finditer(pat, a):
            if inside_spans(concl, m.start()) and not inside_spans(parens, m.start()):
                return {"state": 0, "refused": False, "zero_read": m.group(0).strip()}

    return {"state": None, "refused": True}


def count_bucket(ans, cap):
    """The stated count, with counts at or above the cap merged into one bucket."""
    c = count_stated_in_answer(ans)
    if c["refused"] or c["state"] is None:
        return {"state": None, "refused": True}
    n = int(c["state"])
    return {"state": ("%d_or_more" % cap if n >= cap else str(n)), "refused": False, "n": n}


def colour_sequence(ans, vocab):
    """The colour words of an answer in order, repeats merged."""
    a = normalise_text(ans)
    if not a:
        return {"state": None, "refused": True}
    hits = []
    for m in re.finditer(r"(?<![a-z])(%s)(?![a-z])" % "|".join(sorted(vocab, key=len, reverse=True)), a):
        w = m.group(1)
        if not hits or hits[-1] != w:
            hits.append(w)
    if not hits:
        return {"state": None, "refused": True}
    return {"state": ",".join(hits), "refused": False, "seq": hits}


def count_as_text(ans, want):
    """The stated count as text."""
    c = count_stated_in_answer(ans)
    if c["refused"] or c["state"] is None:
        return {"state": None, "refused": True}
    return {"state": str(int(c["state"])), "refused": False}


def as_list(n):
    """The answers or geometry of a read as a list."""
    if isinstance(n, dict):
        n = n.get("answers") or n.get("geometry") or []
    return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])


def first_pool_word(v, pool):
    """The first pool word found in a value."""
    s = normalise_text(v)
    for k in pool:
        if k in s:
            return k
    return None


def first_number(v):
    """The first number in a value."""
    m = re.search(r"-?\d+(?:\.\d+)?", str(v or "").replace(",", ""))
    return float(m.group(0)) if m else None


def first_integer(v):
    """The first whole number in a value."""
    m = re.search(r"\d+", str(v or ""))
    return int(m.group(0)) if m else None


def count_boxes(bx):
    """The number of confirmed boxes as text."""
    if not isinstance(bx, dict) or bx.get("refused") is True or bx.get("geometry") is None:
        return {"state": None, "refused": True}
    return {"state": str(len(bx.get("geometry") or [])), "refused": False}


def word_sequence(ans, vocab):
    """The vocabulary words of an answer in order."""
    a = normalise_text(ans)
    if not a:
        return []
    pat = r"(?<![a-z])(%s)(?![a-z])" % "|".join(sorted(vocab, key=len, reverse=True))
    return [m.group(1) for m in re.finditer(pat, a)]


def adjacent_alike(ans, vocab):
    """Whether two neighbouring words of an answer are the same."""
    hits = word_sequence(ans, vocab)
    if len(hits) < 2:
        return {"state": None, "refused": True}
    alike = any(hits[i] == hits[i + 1] for i in range(len(hits) - 1))
    return {"state": "two_alike" if alike else "no_two_alike", "refused": False,
            "verdict": "read %s" % ",".join(hits)}


def integer_sequence(ans):
    """The whole numbers of an answer in order."""
    return [int(t) for t in re.findall(r"\d+", str(ans or ""))]


def consecutive_from_one(ans):
    """Whether the numbers read run 1, 2, 3 and so on, with no gap or repeat."""
    seq = integer_sequence(ans)
    if not seq:
        return {"state": None, "refused": True}
    if len(seq) != len(set(seq)):
        return {"state": "has_repeats", "refused": False, "verdict": "read %r" % seq}
    if seq == list(range(1, len(seq) + 1)):
        return {"state": "consecutive_from_one", "refused": False, "verdict": "read %r" % seq}
    return {"state": "has_gaps", "refused": False, "verdict": "read %r" % seq}


def across_numbers_in_grid(grid_ans, list_ans):
    """Whether every number of the across list appears in the grid."""
    g, a = set(integer_sequence(grid_ans)), integer_sequence(list_ans)
    if not g or not a:
        return {"state": None, "refused": True}
    ok = all(x in g for x in a)
    return {"state": "every_across_number_in_grid" if ok else "an_across_number_missing_from_grid",
            "refused": False, "verdict": "grid %r / across %r" % (sorted(g), a)}


def dangerous_goods_spacing(bay, cls, sep):
    """Whether every pair of classes sits at least the table's distance apart."""
    rows = [(b, c) for b, c in zip([first_integer(x) for x in as_list(bay)],
                                   [first_integer(x) for x in as_list(cls)])
            if b is not None and c is not None]
    if len(rows) < 2:
        return {"state": None, "refused": True}
    bad = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            k = "%d-%d" % tuple(sorted((rows[i][1], rows[j][1])))
            need = sep.get(k)
            if need is None:
                continue
            gap = abs(rows[i][0] - rows[j][0])
            if gap < int(need):
                bad.append("class %d in bay %d and class %d in bay %d are %d apart, table wants %d"
                           % (rows[i][1], rows[i][0], rows[j][1], rows[j][0], gap, int(need)))
    return {"state": "a_pair_too_close" if bad else "all_pairs_clear", "refused": False,
            "verdict": "; ".join(bad) or "every pair on the table is clear"}


def runny_glaze_on_bottom_shelf(glz, lvl, runny):
    """Whether every running glaze sits on the bottom shelf."""
    rows = [(normalise_text(g), first_pool_word(l, ("bottom", "middle", "top")))
            for g, l in zip(as_list(glz), as_list(lvl))]
    rows = [(g, l) for g, l in rows if g and l]
    if not rows:
        return {"state": None, "refused": True}
    bad = ["%s on the %s shelf" % (g, l) for g, l in rows
           if any(r in g for r in runny) and l != "bottom"]
    return {"state": "runny_piece_over_another" if bad else "runny_pieces_clear", "refused": False,
            "verdict": "; ".join(bad) or "every running glaze is on the bottom shelf"}


def layers_crossed(lyr, run):
    """Whether the lower and upper layers run in different directions."""
    rows = [(first_pool_word(a, ("lower", "upper")), first_pool_word(b, ("short", "long")))
            for a, b in zip(as_list(lyr), as_list(run))]
    rows = [(a, b) for a, b in rows if a and b]
    lo = [b for a, b in rows if a == "lower"]
    up = [b for a, b in rows if a == "upper"]
    if not lo or not up:
        return {"state": None, "refused": True}
    m_lo = max(set(lo), key=lo.count)
    m_up = max(set(up), key=up.count)
    return {"state": "layers_crossed" if m_lo != m_up else "layers_same_way", "refused": False,
            "verdict": "lower layer runs %s, upper layer runs %s" % (m_lo, m_up)}


def meter_matching_sheet_noting_tolerance(a_bend, b_straight, c_sheet, tol=0.5):
    """Which meter reading matches the sheet, noting the tolerance."""
    fa, fb, fc = first_number(a_bend), first_number(b_straight), first_number(c_sheet)
    if fa is None or fb is None or fc is None:
        return {"state": None, "refused": True}
    ma, mb = abs(fa - fc) <= tol, abs(fb - fc) <= tol
    st = ("both_match" if (ma and mb) else "bend_meter_matches" if ma else
          "straight_run_meter_matches" if mb else "neither_matches")
    return {"state": st, "refused": False,
            "verdict": "bend meter %g, straight-run meter %g, sheet %g (tol %g)"
                       % (fa, fb, fc, tol)}


def ranks_strictly_increasing(seq, rank_table):
    """Whether the ranks of the words read go strictly up."""
    if not isinstance(rank_table, dict) or not rank_table:
        return {"state": None, "refused": True}
    toks = as_list(seq)
    if len(toks) == 1 and isinstance(toks[0], str):
        s = normalise_text(toks[0])
        pool = sorted(rank_table, key=len, reverse=True)
        pat = r"(?<![a-z0-9])(%s)(?![a-z0-9])" % "|".join(re.escape(normalise_text(k)) for k in pool)
        norm = {}
        for k in rank_table:
            norm.setdefault(normalise_text(k), rank_table[k])
        ranks = [norm[m.group(1)] for m in re.finditer(pat, s)]
    else:
        norm = {}
        for k in rank_table:
            norm.setdefault(normalise_text(k), rank_table[k])
        ranks = [norm[normalise_text(t)] for t in toks if normalise_text(t) in norm]
    if len(ranks) < 2:
        return {"state": None, "refused": True}
    down = [i for i in range(len(ranks) - 1) if ranks[i + 1] < ranks[i]]
    same = [i for i in range(len(ranks) - 1) if ranks[i + 1] == ranks[i]]
    st = ("a_step_goes_down" if down else "a_step_repeats" if same else "strictly_increasing")
    return {"state": st, "refused": False,
            "verdict": "ranks %r (down at %r, repeat at %r)" % (ranks, down, same)}


def sequences_reversed(sa, sb):
    """Whether two number sequences are reverses of each other."""
    A, B_ = integer_sequence(sa), integer_sequence(sb)
    if len(A) < 2 or len(B_) < 2:
        return {"state": None, "refused": True}
    if A == list(reversed(B_)):
        st = "sequences_are_reverses"
    elif A == B_:
        st = "sequences_are_identical"
    else:
        st = "sequences_neither"
    return {"state": st, "refused": False, "verdict": "left %r / right %r" % (A, B_)}


def number_within_band(ans, lo, hi):
    """Whether the number read lies within a band."""
    n = first_number(ans)
    if n is None:
        return {"state": None, "refused": True}
    return {"state": ("in_band" if float(lo) <= n <= float(hi) else "out_of_band"),
            "refused": False, "verdict": "read %g, band [%g, %g]" % (n, float(lo), float(hi))}


def three_poses_match(ans, want):
    """Whether the three poses read match the wanted heights."""
    got = word_sequence(ans, ["up", "level", "down"])
    if len(got) < 3:
        return {"state": None, "refused": True}
    got = got[:3]
    if len(set(got)) == 1:
        st = "all_three_the_same"
    elif got == [str(w) for w in want]:
        st = "three_poses_match_the_heights"
    else:
        st = "three_differ_but_do_not_match"
    return {"state": st, "refused": False, "verdict": "read %r, want %r" % (got, list(want))}


def first_number_in_range(node, lo=1, hi=64):
    """The first number in a read that lies in a range."""
    a = node.get('answers') if isinstance(node, dict) else node
    a = (list(a or []) or [None])[0]
    t = [int(x) for x in re.findall(r'\d+', str(a if a is not None else ''))]
    t = [v for v in t if lo <= v <= hi]
    return t[0] if t else None


def merge_board_size(across, down):
    """Combine the across and down counts into one size answer."""
    across_n, down_n = first_number_in_range(across), first_number_in_range(down)
    if across_n is None or down_n is None:
        return {'answers': [None]}
    return {'answers': ['%d across, %d down' % (across_n, down_n)]}


def join_box_reads(node, sep):
    """Join the non-empty answers of all boxes into one text."""
    ans = (node or {}).get('answers') or []
    keep = [str(a).strip() for a in ans if a is not None and str(a).strip()]
    txt = (sep or '\n').join(keep)
    return {'text': txt, 'answers': [txt], 'tokens': keep,
            'asked': len(ans), 'kept': len(keep), 'unreadable': not keep}


def meter_matching_sheet(a_bend, b_straight, c_sheet, tol=0.5):
    """Which meter reading matches the sheet."""
    fa, fb, fc = first_number(a_bend), first_number(b_straight), first_number(c_sheet)
    if fa is None or fb is None or fc is None:
        return {"state": None, "refused": True}
    ma, mb = abs(fa - fc) <= tol, abs(fb - fc) <= tol
    st = ("both_match" if (ma and mb) else "bend_meter_matches" if ma else
          "straight_run_meter_matches" if mb else "neither_matches")
    return {"state": st, "refused": False,
            "verdict": "bend meter %g, straight-run meter %g, sheet %g" % (fa, fb, fc)}


def image_width_height(image):
    """The width and height of an image or image file."""
    try:
        if hasattr(image, "size"):
            w, h = image.size
            return float(w), float(h)
    except Exception:
        pass
    try:
        fh = open(str(image), "rb")
        try:
            head = fh.read(4096)
        finally:
            fh.close()
    except Exception:
        return None
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        try:
            w, h = struct.unpack(">II", head[16:24])
            return float(w), float(h)
        except Exception:
            return None
    if head[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(head):
            if head[i] != 0xFF:
                break
            mk = head[i + 1]
            try:
                ln = struct.unpack(">H", head[i + 2:i + 4])[0]
            except Exception:
                return None
            if 0xC0 <= mk <= 0xCF and mk not in (0xC4, 0xC8, 0xCC):
                try:
                    h, w = struct.unpack(">HH", head[i + 5:i + 9])
                    return float(w), float(h)
                except Exception:
                    return None
            i += 2 + ln
    return None


def anchor_box(fb, i=0):
    """One box of a read, as [ymin, xmin, ymax, xmax]."""
    g = fb
    if isinstance(fb, dict):
        if fb.get("refused") or fb.get("unreadable"):
            return None
        g = fb.get("geometry")
    if not g:
        return None
    if isinstance(g[0], (int, float)):
        g = [g]
    if i >= len(g):
        return None
    b = [float(v) for v in g[i][:4]]
    y0, x0, y1, x1 = min(b[0], b[2]), min(b[1], b[3]), max(b[0], b[2]), max(b[1], b[3])
    return [y0, x0, y1, x1]


def clamp(v, lo, hi):
    """The value limited to a range."""
    return lo if v < lo else (hi if v > hi else v)


def pack_cells(cells_px, W, H, pad_frac):
    """Pixel cells as padded crop boxes and overlay rectangles."""
    M = float(max(W, H))
    boxes, rects = [], []
    for (x0, y0, x1, y1) in cells_px:
        w, h = max(1.0, x1 - x0), max(1.0, y1 - y0)
        g = float(pad_frac) * max(w, h)
        bx0, by0 = clamp(x0 - g, 0.0, W), clamp(y0 - g, 0.0, H)
        bx1, by1 = clamp(x1 + g, 0.0, W), clamp(y1 + g, 0.0, H)
        boxes.append([by0 * 1000.0 / H, bx0 * 1000.0 / W,
                      by1 * 1000.0 / H, bx1 * 1000.0 / W])
        rects.append([(x0 + x1) / 2.0 / M, (y0 + y1) / 2.0 / M, w / M, h / M])
    return boxes, rects


def frame_anchors(W, H):
    """The corners of the picture as overlay anchors."""
    M = float(max(W, H))
    return ([[0.0, 0.0], [W / M, 0.0], [W / M, H / M], [0.0, H / M]],
            [[0.0, 0.0], [W, 0.0], [W, H], [0.0, H]])


def plan_cell_grid(image, fb, rows=1, cols=1, sub=None, pad=0.06, inset=0.02, i=0,
            min_side_px=24.0, labels=None):
    """Cut a boxed container into a grid of cells to read one by one."""
    a = anchor_box(fb, i)
    if a is None:
        return {"no_plan": True, "refused": True,
                "reason": "the container was never boxed"}
    wh = image_width_height(image)
    if not wh:
        return {"no_plan": True, "refused": True,
                "reason": "the picture's size could not be read"}
    W, H = wh
    rows, cols = max(1, int(rows)), max(1, int(cols))
    ax0, ay0 = a[1] * W / 1000.0, a[0] * H / 1000.0
    ax1, ay1 = a[3] * W / 1000.0, a[2] * H / 1000.0
    if sub:
        t, l, b, r = [float(v) for v in sub[:4]]
        aw, ah = ax1 - ax0, ay1 - ay0
        ax0, ax1 = ax0 + l * aw, ax0 + r * aw
        ay0, ay1 = ay0 + t * ah, ay0 + b * ah
    aw, ah = ax1 - ax0, ay1 - ay0
    if aw < min_side_px or ah < min_side_px:
        return {"no_plan": True, "refused": True, "anchor": a,
                "reason": "the container box is too small to cut into cells"}
    cw, ch = aw / float(cols), ah / float(rows)
    if min(cw, ch) < 4.0:
        return {"no_plan": True, "refused": True, "anchor": a,
                "reason": "the cells would be smaller than a few pixels"}
    cells_px, keys = [], []
    ix, iy = float(inset) * cw, float(inset) * ch
    for r_ in range(rows):
        for c_ in range(cols):
            x0 = ax0 + c_ * cw + ix
            x1 = ax0 + (c_ + 1) * cw - ix
            y0 = ay0 + r_ * ch + iy
            y1 = ay0 + (r_ + 1) * ch - iy
            cells_px.append([x0, y0, x1, y1])
            keys.append([r_, c_])
    boxes, rects = pack_cells(cells_px, W, H, pad)
    ref, found_boxes = frame_anchors(W, H)
    out = {"no_plan": False, "reason": "", "rows": rows, "cols": cols, "n": rows * cols,
           "frame": [W, H], "anchor": a, "anchor_px": [ax0, ay0, ax1, ay1],
           "cells": {"geometry": boxes}, "boxes": boxes, "rects": rects, "keys": keys,
           "cells_px": cells_px, "ref_anchors": ref, "found_anchors": found_boxes,
           "cell_w_px": cw, "cell_h_px": ch}
    if labels:
        out["labels"] = [str(x) for x in labels][:rows * cols]
    return out


def plan_dial_sectors(image, fb, n, start_deg=-90.0, clockwise=True, r_in=0.55, r_out=0.95,
               span_frac=0.9, pad=0.06, i=0, min_side_px=40.0):
    """Cut a boxed dial into sectors to read one by one."""
    a = anchor_box(fb, i)
    if a is None:
        return {"no_plan": True, "refused": True, "reason": "the dial was never boxed"}
    wh = image_width_height(image)
    if not wh:
        return {"no_plan": True, "reason": "the picture's size could not be read"}
    W, H = wh
    n = max(1, int(n))
    ax0, ay0 = a[1] * W / 1000.0, a[0] * H / 1000.0
    ax1, ay1 = a[3] * W / 1000.0, a[2] * H / 1000.0
    if (ax1 - ax0) < min_side_px or (ay1 - ay0) < min_side_px:
        return {"no_plan": True, "refused": True, "anchor": a,
                "reason": "the dial box is too small to cut into sectors"}
    cx, cy = (ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0
    rx, ry = (ax1 - ax0) / 2.0, (ay1 - ay0) / 2.0
    step = 360.0 / float(n)
    sgn = 1.0 if clockwise else -1.0
    cells_px, angs = [], []
    half = 0.5 * step * float(span_frac)
    for k in range(n):
        mid = float(start_deg) + sgn * step * k
        pts = []
        for da in (-half, 0.0, half):
            th = math.radians(mid + da)
            for rr in (float(r_in), float(r_out)):
                pts.append((cx + rx * rr * math.cos(th), cy + ry * rr * math.sin(th)))
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        cells_px.append([clamp(min(xs), 0.0, W), clamp(min(ys), 0.0, H),
                         clamp(max(xs), 0.0, W), clamp(max(ys), 0.0, H)])
        angs.append(mid % 360.0)
    boxes, rects = pack_cells(cells_px, W, H, pad)
    ref, found_boxes = frame_anchors(W, H)
    return {"no_plan": False, "reason": "", "rows": 1, "cols": n, "n": n,
            "frame": [W, H], "anchor": a, "centre_px": [cx, cy], "radius_px": [rx, ry],
            "angles_deg": angs, "cells": {"geometry": boxes}, "boxes": boxes, "rects": rects,
            "keys": [[0, k] for k in range(n)], "cells_px": cells_px,
            "ref_anchors": ref, "found_anchors": found_boxes}


def cell_index(pl, r, c):
    """The flat index of a grid cell, or -1."""
    if not isinstance(pl, dict) or pl.get("no_plan"):
        return -1
    r, c = int(r), int(c)
    if r < 0 or c < 0 or r >= int(pl["rows"]) or c >= int(pl["cols"]):
        return -1
    return r * int(pl["cols"]) + c


def pick_cells(pl, idx, labels=None):
    """A plan restricted to the named cells."""
    if not isinstance(pl, dict) or pl.get("no_plan"):
        return {"no_plan": True, "refused": True,
                "reason": (pl or {}).get("reason", "no plan to pick from")}
    flat = []
    for k in (idx or []):
        if isinstance(k, (list, tuple)):
            flat.append(cell_index(pl, k[0], k[1]))
        else:
            flat.append(int(k))
    keep = [k for k in flat if 0 <= k < len(pl["boxes"])]
    out = {"no_plan": not keep, "refused": not keep,
           "reason": "" if keep else "none of the named cells exist",
           "rows": 1, "cols": len(keep), "n": len(keep),
           "frame": pl["frame"], "anchor": pl.get("anchor"),
           "cells": {"geometry": [pl["boxes"][k] for k in keep]},
           "boxes": [pl["boxes"][k] for k in keep],
           "rects": [pl["rects"][k] for k in keep],
           "cells_px": [pl["cells_px"][k] for k in keep],
           "keys": [pl["keys"][k] for k in keep] if pl.get("keys") else [],
           "index": keep, "n_dropped": len(flat) - len(keep),
           "ref_anchors": pl["ref_anchors"], "found_anchors": pl["found_anchors"]}
    if labels:
        out["labels"] = [str(x) for x in labels][:len(keep)]
    return out


def paint_cells(pl, verdicts, idx=None):
    """Split the cells of a plan into hits, misses and unsure ones for the overlay."""
    if not isinstance(pl, dict) or pl.get("no_plan"):
        return {"hit": [], "miss": [], "edge": [], "n_hit": 0, "n_miss": 0, "n_edge": 0,
                "no_plan": True}
    rects = pl["rects"]
    order = list(idx) if idx is not None else list(range(len(rects)))
    hit, miss, edge = [], [], []
    for j, k in enumerate(order):
        try:
            k = int(k)
        except Exception:
            continue
        if not (0 <= k < len(rects)):
            continue
        v = verdicts[j] if j < len(verdicts) else None
        (hit if v is True or v == 1 else (edge if v is None else miss)).append(rects[k])
    return {"hit": hit, "miss": miss, "edge": edge, "no_plan": False,
            "n_hit": len(hit), "n_miss": len(miss), "n_edge": len(edge),
            "ref_anchors": pl["ref_anchors"], "found_anchors": pl["found_anchors"]}


def anchor_point(fb):
    """The point of a point read."""
    g = fb
    if isinstance(fb, dict):
        if fb.get("refused") or fb.get("unreadable"):
            return None
        g = fb.get("geometry")
    if not g or len(g) < 2:
        return None
    return float(g[0]), float(g[1])


def anchor_line(fb):
    """The line of a line read."""
    g = fb
    if isinstance(fb, dict):
        if fb.get("refused") or fb.get("unreadable"):
            return None
        g = fb.get("geometry")
    if not g or len(g) < 4:
        return None
    return tuple(float(v) for v in g[:4])


def fraction_along_anchor(pl, y=None, x=None):
    """How far a coordinate lies across the anchor box, from 0 to 1."""
    if not isinstance(pl, dict) or pl.get("no_plan"):
        return None
    W, H = [float(v) for v in pl["frame"]]
    ax0, ay0, ax1, ay1 = [float(v) for v in pl["anchor_px"]]
    if y is not None:
        span = ay1 - ay0
        return None if span <= 0 else (float(y) * H / 1000.0 - ay0) / span
    if x is not None:
        span = ax1 - ax0
        return None if span <= 0 else (float(x) * W / 1000.0 - ax0) / span
    return None


def reference_line(pl, y0, x0, y1, x1):
    """A line in overlay coordinates."""
    if not isinstance(pl, dict) or pl.get("no_plan"):
        return []
    W, H = [float(v) for v in pl["frame"]]
    M = max(W, H)
    return [[[float(x0) * W / 1000.0 / M, float(y0) * H / 1000.0 / M],
             [float(x1) * W / 1000.0 / M, float(y1) * H / 1000.0 / M]]]


def paint_cells_by_fraction(pl, frac, idx=None):
    """paint_cells with every cell given the same verdict from a score."""
    try:
        f = float(frac)
    except Exception:
        f = 0.0
    v = True if f >= 1.0 else (None if f > 0.0 else False)
    n = len(pl.get("rects") or []) if isinstance(pl, dict) else 0
    return paint_cells(pl, [v] * n, idx)


def padded_answers(rd, n=None):
    """The answers of a read, padded or cut to n."""
    a = rd.get("answers") if isinstance(rd, dict) else rd
    a = list(a or [])
    if n is not None:
        n = int(n)
        a = (a + [None] * n)[:n]
    return a


def first_count_in_range(s, lo=1, hi=64):
    """The first whole number in a text that lies in a range."""
    import re as _re
    t = _re.findall(r"\d+", str(s if s is not None else ""))
    for x in t:
        v = int(x)
        if lo <= v <= hi:
            return v
    return None


def first_two_counts_in_range(s, lo=1, hi=64):
    """The first two whole numbers in a text that lie in a range."""
    import re as _re
    t = [int(x) for x in _re.findall(r"\d+", str(s if s is not None else ""))]
    t = [v for v in t if lo <= v <= hi]
    return (t[0], t[1]) if len(t) >= 2 else (None, None)


def plan_pinned_grid(image, anc, rows=1, cols=1, sub=None, pad=0.06, inset=0.02):
    """plan_cell_grid for a layout the prompt pins."""
    try:
        rows = int(rows)
        cols = int(cols)
    except (TypeError, ValueError):
        return {"no_plan": True, "refused": True,
                "reason": "the pinned layout was not a pair of whole numbers"}
    if rows < 1 or cols < 1:
        return {"no_plan": True, "refused": True, "reason": "the pinned layout is empty"}
    return plan_cell_grid(image, anc, rows=rows, cols=cols, sub=sub, pad=pad, inset=inset)


def plan_grid_from_read_count(image, anc, n_read, cols=1, lo=1, hi=64, sub=None, pad=0.06, inset=0.02,
                 transpose=False):
    """plan_cell_grid with the row count read from the picture."""
    n = first_count_in_range(padded_answers(n_read, 1)[0], lo, hi)
    if n is None:
        return {"no_plan": True, "refused": True,
                "reason": "the number of cells in the container could not be read"}
    if transpose:
        return plan_cell_grid(image, anc, rows=int(cols), cols=n, sub=sub, pad=pad, inset=inset)
    return plan_cell_grid(image, anc, rows=n, cols=int(cols), sub=sub, pad=pad, inset=inset)


def plan_line_from_read_count(image, anc, n_read, lo=1, hi=64, pad=0.06, inset=0.02, across=None):
    """Cut a container into a row or column of cells, their number read from the picture."""
    n = first_count_in_range(padded_answers(n_read, 1)[0], lo, hi)
    if n is None:
        return {"no_plan": True, "refused": True,
                "reason": "the number of items in the container could not be read"}
    a = anchor_box(anc)
    wh = image_width_height(image)
    if a is None or not wh:
        return plan_cell_grid(image, anc, rows=n, cols=1, pad=pad, inset=inset)
    W, H = wh
    w = (a[3] - a[1]) * W / 1000.0
    h = (a[2] - a[0]) * H / 1000.0
    wide = (w >= h) if across is None else bool(across)
    if wide:
        return plan_cell_grid(image, anc, rows=1, cols=n, pad=pad, inset=inset)
    return plan_cell_grid(image, anc, rows=n, cols=1, pad=pad, inset=inset)


def plan_single_container(image, anc, rows=1, cols=1, sub=None, pad=0.06, inset=0.02):
    """plan_cell_grid when the sweep confirmed exactly one container."""
    if isinstance(anc, dict) and (anc.get("refused") or anc.get("unreadable")):
        return {"no_plan": True, "refused": True,
                "reason": "the completeness sweep for the container refused"}
    g = anc.get("geometry") if isinstance(anc, dict) else anc
    g = list(g or [])
    if g and isinstance(g[0], (int, float)):
        g = [g]
    n = len(g)
    if n == 0:
        return {"no_plan": True, "refused": False, "n_confirmed": 0,
                "reason": "the completeness sweep certified that there is no such thing in the "
                          "picture"}
    if n > 1:
        return {"no_plan": True, "refused": True, "n_confirmed": n,
                "reason": ("the completeness sweep confirmed %d of these, so which one is meant "
                           "cannot be said" % n)}
    pl = plan_cell_grid(image, {"geometry": g}, rows=int(rows), cols=int(cols), sub=sub,
                 pad=pad, inset=inset)
    if isinstance(pl, dict):
        pl["n_confirmed"] = 1
    return pl


def cell_boxes(pl):
    """The cell boxes of a plan as a read."""
    if not isinstance(pl, dict) or pl.get("no_plan"):
        return {"geometry": [], "refused": True, "unreadable": True}
    return {"geometry": list(pl.get("boxes") or []), "refused": False, "unreadable": False,
            "confirmed": True}


def count_as_read(c):
    """A count as a read record."""
    v = (c or {}).get('n')
    return {'answers': [str(v)], 'text': str(v), 'n': v,
            'asked': (c or {}).get('asked'), 'unreadable': v is None}


def plan_board_strips(image, board_box, rows, cols):
    """Cut a boxed board into strips of cells to read and the overlay of its cells."""
    import struct

    def width_height(p):
        try:
            with open(str(p), 'rb') as f:
                head = f.read(2048)
        except Exception:
            return None
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            w, h = struct.unpack('>II', head[16:24])
            return float(w), float(h)
        if head[:2] == b'\xff\xd8':
            i = 2
            while i + 9 < len(head):
                if head[i] != 0xFF:
                    break
                mk = head[i + 1]
                ln = struct.unpack('>H', head[i + 2:i + 4])[0]
                if 0xC0 <= mk <= 0xCF and mk not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack('>HH', head[i + 5:i + 9])
                    return float(w), float(h)
                i += 2 + ln
        return None

    rows, cols = int(rows), int(cols)
    geometry = board_box.get('geometry') if isinstance(board_box, dict) else board_box
    if not geometry:
        return {'no_plan': True}
    y0, x0, y1, x1 = [float(v) for v in geometry[0][:4]]
    if x1 - x0 < 50 or y1 - y0 < 50:
        return {'no_plan': True}
    size = width_height(image)
    W, H = size if size else (1000.0, 1000.0)
    m = 1
    for k in range(2, 6):
        if cols % k == 0:
            m = k
    rects = [[(j + 0.5) / cols, (i + 0.5) / rows, 0.96 / cols, 0.96 / rows]
             for i in range(rows) for j in range(cols)]
    chunks = []
    for i in range(rows):
        ry0 = y0 + (y1 - y0) * i / float(rows)
        ry1 = y0 + (y1 - y0) * (i + 1) / float(rows)
        for j in range(0, cols, m):
            cx0 = x0 + (x1 - x0) * j / float(cols)
            cx1 = x0 + (x1 - x0) * (j + m) / float(cols)
            chunks.append([ry0, cx0, ry1, cx1])
    return {'no_plan': False, 'rects': rects, 'm': m, 'per_row': cols // m,
            'found_anchors': [[x0 * W / 1000.0, y0 * H / 1000.0],
                            [x1 * W / 1000.0, y0 * H / 1000.0],
                            [x1 * W / 1000.0, y1 * H / 1000.0],
                            [x0 * W / 1000.0, y1 * H / 1000.0]],
            'chunks': {'geometry': chunks},
            'board_box': {'geometry': [[y0, x0, y1, x1]]},
            'frame': [W, H]}


def strip_numbers(a, want):
    """The numbers of one strip of cells, blanks read as 0."""
    s = str(a or '').lower()
    for w in ('blank', 'empty', 'none', 'nothing', 'no number'):
        s = s.replace(w, ' 0 ')
    t = re.findall(r'\d+', s)
    if len(t) != want:
        return None
    return [int(x) for x in t]


def board_size_read(a):
    """The across and down size of the board as read."""
    t = re.findall(r'\d+', str(a or ''))
    return (int(t[0]), int(t[1])) if len(t) == 2 else (None, None)


def assemble_board_grid(strip_reads, size_read, plan, rows, cols):
    """Assemble the board grid from the strip reads, checking the board size."""
    rows, cols = int(rows), int(cols)
    if not isinstance(plan, dict) or plan.get('no_plan'):
        return {'no_read': True, 'reason': 'the board was never boxed', 'grid': None}
    m, per_row = int(plan['m']), int(plan['per_row'])
    size_answers = (size_read.get('answers') if isinstance(size_read, dict) else size_read) or []
    n_wide, n_tall = board_size_read(size_answers[0] if size_answers else None)
    if (n_wide is not None and n_wide != cols) or (n_tall is not None and n_tall != rows):
        return {'no_read': True, 'size_fail': True, 'grid': None,
                'n_wide': n_wide, 'n_tall': n_tall,
                'reason': ('the drawn board is %sx%s cells, not the %dx%d the prompt pins, so '
                           'the committed cells are not on the picture'
                           % (n_tall, n_wide, rows, cols))}
    ans = (strip_reads.get('answers') if isinstance(strip_reads, dict) else strip_reads) or []
    grid, n_missing = [], 0
    for i in range(rows):
        row = []
        for c in range(per_row):
            k = i * per_row + c
            piece = strip_numbers(ans[k], m) if k < len(ans) else None
            if piece is None:
                n_missing += 1
                piece = ['?'] * m
            row += piece
        grid.append(row)
    if n_missing >= rows * per_row:
        return {'no_read': True, 'reason': 'every strip of the board refused to read',
                'grid': None, 'n_missing': n_missing}
    n_read = sum(1 for r in grid for v in r if v != '?')
    return {'no_read': False, 'grid': grid, 'n_missing': n_missing,
            'n_cells_read': n_read, 'n_cells': rows * cols,
            'n_wide': n_wide, 'n_tall': n_tall}


def read_peg_stacks(peg_boxes, peg_confirms, disk_boxes, disk_confirms, disk_numbers, gt):
    """The pieces stacked on each peg, bottom to top, from the confirmed boxes."""
    import re

    def cx(b):
        return (float(b[1]) + float(b[3])) / 2.0

    def cy(b):
        return (float(b[0]) + float(b[2])) / 2.0

    def yes(a):
        return str(a).strip().lower().startswith('y')

    g = dict(gt or {})
    n_pegs = int(g.get('n_pegs') or 0)
    letters = ['A', 'B', 'C', 'D', 'E', 'F'][:max(n_pegs, 1)]

    pg = (peg_boxes or {}).get('geometry') or []
    pa = (peg_confirms or {}).get('answers') or []
    pegs = [pg[i] for i in range(min(len(pg), len(pa))) if yes(pa[i])]
    pegs.sort(key=cx)

    dg = (disk_boxes or {}).get('geometry') or []
    da = (disk_confirms or {}).get('answers') or []
    dv = (disk_numbers or {}).get('answers') or []
    disks = []
    for i in range(min(len(dg), len(da))):
        if not yes(da[i]):
            continue
        m = re.search(r'\d+', str(dv[i] if i < len(dv) else ''))
        disks.append({'box': dg[i], 'num': int(m.group()) if m else 0})

    res = {'n_pegs_confirmed': len(pegs), 'n_disks_confirmed': len(disks),
           'pegs_asked': len(pa), 'disks_asked': len(da), 'total': len(disks)}

    if len(pegs) != n_pegs:
        for n in letters:
            res[n] = 'peg-count-mismatch'
            res['h_' + n] = -1
        res['verdict'] = ('%d pegs confirmed but the picture was asked for %d, so the peg letters '
                          'cannot be assigned' % (len(pegs), n_pegs))
        return res

    cols = dict((n, []) for n in letters)
    for d in disks:
        x = cx(d['box'])
        j = min(range(len(pegs)), key=lambda k: abs(cx(pegs[k]) - x))
        cols[letters[j]].append(d)

    for n in letters:
        col = sorted(cols[n], key=lambda d: -cy(d['box']))
        nums = [str(d['num']) for d in col if d['num'] > 0]
        res[n] = ','.join(nums) if nums else 'none'
        res['h_' + n] = len(col)
    res['verdict'] = ('%d pegs and %d stacked pieces confirmed by the rings; left to right the '
                      'pegs carry %s'
                      % (len(pegs), len(disks),
                         ' | '.join('%s:%s' % (n, res[n]) for n in letters)))
    return res


def count_confirmed_disks(disk_boxes, disk_confirms, gt):
    """Count the boxes confirmed to hold exactly one whole piece."""
    def yes(a):
        return str(a).strip().lower().startswith('y')
    ans = (disk_confirms or {}).get('answers') or []
    geo = (disk_boxes or {}).get('geometry') or []
    n = sum(1 for i in range(min(len(geo), len(ans))) if yes(ans[i]))
    return {'n': n, 'asked': len(ans),
            'verdict': '%d of %d framed candidates were confirmed to hold exactly one whole piece'
                       % (n, len(ans))}


def labelled_pairs(labels, vals):
    """The label and value pairs read, in canonical form."""
    la = (labels or {}).get('answers') or []
    va = (vals or {}).get('answers') or []
    pairs = {}
    for a, b in zip(la, va):
        k = ''.join(c for c in str(a).lower() if c.isalnum())
        v = ''.join(c for c in str(b).lower() if c.isalnum())
        if k and v:
            pairs[k] = v
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d labelled entries: %s' % (len(pairs), canon or 'none')}


def count_key_matches(keys, vals, want):
    """Count the ringed items whose answer follows the pinned rule."""
    w = dict(p.split('=') for p in str(want).split('|') if p.count('=') == 1)
    ks = [str(a).strip().upper().replace(' ', '') for a in ((keys or {}).get('answers') or [])]
    vs = [str(a).strip().lower().replace('-', ' ') for a in ((vals or {}).get('answers') or [])]
    n = 0
    for k, s in zip(ks, vs):
        t = str(w.get(k, '')).strip().lower()
        n += 1 if (t and s and t in s) else 0
    return {'n': n, 'asked': len(vs), 'verdict': '%d of the %d ringed items answer the way the pinned rule requires' % (n, len(vs))}


def frac_of(x):
    """The score fraction of a result."""
    return x['frac']


NOISE_WORDS = {"THE", "IS", "IT", "A", "AN", "AND", "ANSWER", "WORD", "ONLY", "READS", "SAYS"}


def last_word(a):
    """The last word of an answer, ignoring filler words."""
    ts = [t for t in re.findall(r"[A-Za-z0-9]+", str(a if a is not None else "").upper())
          if t not in NOISE_WORDS]
    return ts[-1] if ts else ""


def last_number(a):
    """The last number of an answer."""
    ns = re.findall(r"-?\d+(?:\.\d+)?", str(a if a is not None else ""))
    return ns[-1] if ns else ""


def compose_reads(kinds, *reads):
    """Combine several reads into one line per item."""
    cols = []
    for k, r in zip(kinds, reads):
        if not isinstance(r, (list, tuple)) or not r:
            return None
        cols.append([(last_number(x) if k == "n" else last_word(x)) for x in r])
    if not cols:
        return None
    n = min(len(c) for c in cols)
    return [" ".join(c[i] for c in cols) for i in range(n)]


def alnum_lower(a):
    """The letters and digits of a value, lower case."""
    return re.sub(r"[^a-z0-9]", "", str(a).lower())


SLOT_PREFIX = re.compile(r"^(?:panel|slot|row|bay|peg|photo|picture|number|no)*\d{0,2}$")


def slot_matches(a, k):
    """Whether a read slot names the wanted key."""
    if a is None:
        return 0.0
    if isinstance(a, (list, tuple)):
        a = a[0] if a else None
    s, t = alnum_lower(a), alnum_lower(k)
    if not t:
        return 0.0
    if s == t:
        return 1.0
    if s.endswith(t) and SLOT_PREFIX.match(s[:len(s) - len(t)]):
        return 1.0
    return 0.0


def slot_scores(got, want):
    """The match of each read slot against the wanted keys."""
    if isinstance(got, dict) or not isinstance(got, (list, tuple)) or len(got) < len(want):
        return None
    return [slot_matches(got[i], w) for i, w in enumerate(want)]


def panel_slots_verdict(gots, wants):
    """Whether every panel slot names its wanted key, and the share that do."""
    slots = []
    for g, w in zip(gots, wants):
        if not w:
            continue
        s = slot_scores(g, w)
        if s is None:
            return {"law": 0.0, "share": 0.0, "unreadable": True, "bad": None}
        slots += s
    if not slots:
        return {"law": 0.0, "share": 0.0, "unreadable": True, "bad": None}
    ok = sum(slots)
    return {"law": 1.0 if ok == len(slots) else 0.0,
            "share": round(ok / float(len(slots)), 4), "unreadable": False,
            "bad": [i for i, v in enumerate(slots) if v == 0.0]}


def join_answers(answers):
    """The non-empty answers joined by spaces."""
    if not isinstance(answers, (list, tuple)):
        return ""
    return " ".join(str(a) for a in answers if a)


def line_coverage(txt, lines):
    """The share of the wanted lines found in a transcription."""
    s = alnum_lower(txt)
    lines = list(lines or [])
    if not lines:
        return 0.0
    ok = 0
    for ln in lines:
        t = alnum_lower(ln)
        if not t:
            ok += 1
            continue
        if t in s:
            ok += 1
            continue
        best, n = 0.0, len(t)
        step = max(1, n // 8)
        for i in range(0, max(1, len(s) - n + 1), step):
            best = max(best, difflib.SequenceMatcher(a=t, b=s[i:i + n + 3]).ratio())
        ok += 1 if best >= 0.82 else 0
    return round(ok / float(len(lines)), 4)


def clean_panel_token(tok):
    """A panel attribute without numbering, quotes or a final full stop."""
    t = str(tok).strip().strip('*"\'` ').strip()
    t = re.sub(r'^(?:panel\s*)?\d+\s*[.):\-]\s*(?=\S)', '', t, flags=re.I)
    return t.strip().strip('.').strip().casefold()


def panel_cells(got, k):
    """The first k attribute cells of a panel read."""
    if isinstance(got, dict):
        ans = got.get('answers') or []
        got = ans[0] if ans else None
    if isinstance(got, (list, tuple)):
        out = [clean_panel_token(v[0] if isinstance(v, (list, tuple)) and v else v) for v in got]
        return out[:k] if len(out) >= k else None
    if got is None:
        return None
    lines = [l for l in str(got).splitlines() if l.strip()]
    for line in list(reversed(lines)) + [str(got)]:
        toks = [t for t in (clean_panel_token(x) for x in line.split(',')) if t]
        if len(toks) >= k:
            return toks[:k]
    return None


def panel_cells_verdict(gots, tgts):
    """Whether every panel cell holds its wanted attribute, and the share that do."""
    pairs = []
    for got, tgt in zip(gots, tgts):
        if tgt is None:
            continue
        tgt = [str(x).strip().casefold() for x in tgt]
        pairs.append((panel_cells(got, len(tgt)), tgt))
    if not pairs or any(p[0] is None for p in pairs):
        return {"law": 0.0, "share": 0.0, "unreadable": True, "bad": None,
                "verdict": "a panel-attribute read never came back in full -> unreadable"}
    ok = tot = 0
    bad = []
    for gi, (got, tgt) in enumerate(pairs):
        for i, t in enumerate(tgt):
            tot += 1
            if got[i] == t:
                ok += 1
            else:
                bad.append([gi, i + 1, got[i], t])
    return {"law": 1.0 if ok == tot else 0.0, "share": round(ok / tot, 4),
            "unreadable": False, "bad": bad,
            "verdict": "%d/%d panel-cells obey the law -> law %.1f, panel-share %.4f"
                       % (ok, tot, 1.0 if ok == tot else 0.0, ok * 1.0 / tot)}


def count_confirmed_distinct_boxes(confirm_reads, boxes):
    """Count the confirmed boxes, counting overlapping boxes of one instance once."""
    ans = (confirm_reads or {}).get('answers') or []
    geo = (boxes or {}).get('geometry') or []
    def area(b):
        return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    def same_instance(a, b):
        iy = min(a[2], b[2]) - max(a[0], b[0])
        ix = min(a[3], b[3]) - max(a[1], b[1])
        if iy <= 0 or ix <= 0:
            return False
        m = min(area(a), area(b))
        return m > 0 and (iy * ix) > 0.5 * m
    kept = []
    yes_raw = 0
    for i, a in enumerate(ans):
        if not str(a).strip().lower().startswith('y'):
            continue
        yes_raw += 1
        if i >= len(geo):
            continue
        b = [float(v) for v in geo[i]]
        if any(same_instance(b, k) for k in kept):
            continue
        kept.append(b)
    return {'n': len(kept), 'asked': len(ans), 'yes_raw': yes_raw}


def count_confirmed_boxes(node):
    """Count the proposed boxes whose answer starts with yes."""
    ans = (node or {}).get('answers') or []
    n = sum(1 for a in ans if str(a).strip().lower().startswith('y'))
    return {'n': n, 'asked': len(ans),
            'verdict': '%d of the %d proposed boxes were individually confirmed '
                       '-> counted %d' % (n, len(ans), n)}


def marker_degree(a):
    """The degree number read off a node marker."""
    import re
    if a is None:
        return None
    s = str(a).strip().lower()
    if s.startswith('none') or 'no dot' in s or 'no solid' in s or 'not a dot' in s:
        return None
    m = re.findall(r'\d+', s)
    if not m:
        return None
    v = int(m[-1])
    return v if 0 <= v <= 12 else None


def node_degrees(node_boxes, degree_reads):
    """The degrees of the confirmed nodes and their odd and even counts."""
    geo = (node_boxes or {}).get('geometry') or []
    ans = (degree_reads or {}).get('answers') or []
    degs = []
    for i in range(len(geo)):
        v = marker_degree(ans[i] if i < len(ans) else None)
        if v is None:
            continue
        degs.append(int(v))
    if not degs:
        return {'degrees': [], 'n_markers': 0, 'n_odd': None, 'n_deg4plus': None,
                'min_deg': None, 'max_deg': None, 'handshake_even': None,
                'asked': len(geo), 'degenerate': True}
    return {'degrees': degs, 'n_markers': len(degs),
            'n_odd': sum(1 for d in degs if d % 2 == 1),
            'n_deg4plus': sum(1 for d in degs if d >= 4),
            'min_deg': min(degs), 'max_deg': max(degs),
            'handshake_even': (sum(degs) % 2 == 0),
            'asked': len(geo), 'degenerate': False}


def node_degrees_with_colour(node_boxes, degree_reads, colour_reads):
    """node_degrees plus whether the red nodes are exactly the odd ones."""
    geo = (node_boxes or {}).get('geometry') or []
    ans = (degree_reads or {}).get('answers') or []
    cols = (colour_reads or {}).get('answers') or []
    nodes = []
    for i in range(len(geo)):
        v = marker_degree(ans[i] if i < len(ans) else None)
        if v is None:
            continue
        c = str(cols[i]).strip().lower() if i < len(cols) and cols[i] is not None else ''
        nodes.append((int(v), c.startswith('red')))
    if not nodes:
        return {'degrees': [], 'n_markers': 0, 'n_odd': None, 'n_marked': 0,
                'marked_is_odd_set': False, 'n_deg4plus': None, 'min_deg': None,
                'max_deg': None, 'handshake_even': None, 'asked': len(geo),
                'degenerate': True}
    degs = [d for d, r in nodes]
    return {'degrees': degs, 'n_markers': len(degs),
            'n_odd': sum(1 for d in degs if d % 2 == 1),
            'n_marked': sum(1 for d, r in nodes if r),
            'marked_is_odd_set': all((bool(r) == (d % 2 == 1)) for d, r in nodes),
            'n_deg4plus': sum(1 for d in degs if d >= 4),
            'min_deg': min(degs), 'max_deg': max(degs),
            'handshake_even': (sum(degs) % 2 == 0),
            'asked': len(geo), 'degenerate': False}
