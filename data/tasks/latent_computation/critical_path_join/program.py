# shared code: code_3c5a72292cae

import re


def _rows(ans):
    if isinstance(ans, (list, tuple)):
        return [str(t).strip() for t in ans if str(t).strip()]
    return [t.strip() for t in re.split(r"[;\n]+", str(ans or "")) if t.strip()]


def read_stubs(ans, names):
    want = [str(n).strip().lower() for n in names]
    out = {}
    for chunk in _rows(ans):
        t = str(chunk).lower()
        head = None
        for n in want:
            i = t.find(n)
            if i >= 0 and (head is None or i < head[0]):
                head = (i, n)
        if head is None or head[1] in out:
            continue
        nm = head[1]
        m = re.search(r"takes\s*(\d+)", t)
        if not m:
            m = re.search(r"(\d+)\s*wk", t)
        if not m:
            continue
        if "after" not in t:
            continue
        tail = t[t.find("after") + len("after"):]
        preds = [n for n in want if n != nm and n in tail]
        if not preds and not re.search(r"(nothing|none|no prereq|n/a)", tail):
            continue
        out[nm] = (int(m.group(1)), sorted(preds))
    if len(out) != len(want):
        return None
    if not any(pr for _d, pr in out.values()):
        return None
    return out


def read_names(ans, names):
    want = [str(n).strip().lower() for n in names]
    s = " ".join(_rows(ans)).lower()
    if re.search(r"\b(none|no bars|nothing)\b", s):
        return set()
    return set(n for n in want if re.search(r"(?<![a-z])%s(?![a-z])" % re.escape(n), s))


def read_starts(ans, names):
    want = [str(n).strip().lower() for n in names]
    out = {}
    for chunk in _rows(ans):
        t = str(chunk).lower()
        head = None
        for n in want:
            i = t.find(n)
            if i >= 0 and (head is None or i < head[0]):
                head = (i, n)
        nums = re.findall(r"\d+", t)
        if head and nums and head[1] not in out:
            out[head[1]] = int(nums[-1])
    return out


def cpm(tasks):
    es, ef, order, seen = {}, {}, [], set()

    def visit(n, stack=()):
        if n in seen or n in stack:
            return
        seen.add(n)
        for p in tasks[n][1]:
            if p in tasks:
                visit(p, stack + (n,))
        order.append(n)
    for n in tasks:
        visit(n)
    for n in order:
        d, preds = tasks[n]
        es[n] = max([ef[p] for p in preds if p in ef], default=0)
        ef[n] = es[n] + d
    mk = max(ef.values()) if ef else 0
    ls, lf = {}, {}
    for n in reversed(order):
        succ = [m for m in tasks if n in tasks[m][1]]
        lf[n] = min([ls[m] for m in succ if m in ls], default=mk)
        ls[n] = lf[n] - tasks[n][0]
    return {"es": es, "ef": ef, "makespan": mk,
            "critical": sorted(n for n in tasks if ls[n] == es[n]),
            "float": {n: ls[n] - es[n] for n in tasks}}


def check_critical_path(stubs_ans, red_ans, starts_ans, finish_ans, names):
    """Compare red bars, start weeks and finish week with the critical path from the stubs."""
    names = [str(n).strip().lower() for n in names]
    tasks = read_stubs(stubs_ans, names)
    if tasks is None:
        return {"unreadable": True, "law": 0.0, "share": 0.0, "schedule": 0.0,
                "makespan_ok": 0.0, "red": None, "critical": None}
    solution = cpm(tasks)
    red = read_names(red_ans, names)
    starts = read_starts(starts_ans, names)
    finish_numbers = re.findall(r"\d+", str(finish_ans if finish_ans is not None else ""))
    critical = set(solution["critical"])
    share = sum(1.0 for n in names if (n in red) == (n in critical)) / len(names)
    start_share = sum(1.0 for n in names if starts.get(n) == solution["es"][n] + 1) / len(names)
    return {"unreadable": False,
            "law": 1.0 if red == critical else 0.0,
            "share": round(share, 4),
            "schedule": round(start_share, 4),
            "makespan_ok": 1.0 if (finish_numbers and int(finish_numbers[0]) == solution["makespan"]) else 0.0,
            "red": sorted(red), "critical": sorted(critical), "float": solution["float"],
            "makespan": solution["makespan"]}

# end of code_3c5a72292cae

# shared code: code_350038490c80

import re


def _rows(ans):
    if isinstance(ans, (list, tuple)):
        return [str(t).strip() for t in ans if str(t).strip()]
    return [t.strip() for t in re.split(r"[;\n]+", str(ans or "")) if t.strip()]


def read_stubs(ans, names):
    want = [str(n).strip().lower() for n in names]
    out = {}
    for chunk in _rows(ans):
        t = str(chunk).lower()
        head = None
        for n in want:
            i = t.find(n)
            if i >= 0 and (head is None or i < head[0]):
                head = (i, n)
        if head is None or head[1] in out:
            continue
        nm = head[1]
        m = re.search(r"takes\s*(\d+)", t)
        if not m:
            m = re.search(r"(\d+)\s*wk", t)
        if not m:
            continue
        if "after" not in t:
            continue
        tail = t[t.find("after") + len("after"):]
        preds = [n for n in want if n != nm and n in tail]
        if not preds and not re.search(r"(nothing|none|no prereq|n/a)", tail):
            continue
        out[nm] = (int(m.group(1)), sorted(preds))
    if len(out) != len(want):
        return None
    if not any(pr for _d, pr in out.values()):
        return None
    return out


def netbad(ans, names):
    return {"bad": read_stubs(ans, [str(n).strip().lower() for n in names]) is None}


def first_usable_stubs(names, *reads):
    """The first reading whose stubs give a usable task network, else the last reading."""
    want = [str(n).strip().lower() for n in names]
    last = None
    for i, reading in enumerate(reads):
        if isinstance(reading, dict) or reading is None:
            continue
        last = reading
        if read_stubs(reading, want) is not None:
            return {"value": reading, "exhausted": False, "used": "reading %d of %d" % (i + 1, len(reads))}
    if last is None:
        return {"value": None, "exhausted": True, "used": "no reading came back"}
    return {"value": last, "exhausted": False, "used": "last reading (no usable network in any)"}

# end of code_350038490c80

# shared code: code_c81b14441e02

import difflib
import re


def join(answers):
    if not isinstance(answers, (list, tuple)):
        return ""
    return " ".join(str(a) for a in answers if a)


def _c(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def line_coverage(text, lines):
    """Share of expected lines found in the read text, allowing near matches."""
    s = _c(text)
    lines = list(lines or [])
    if not lines:
        return 0.0
    found = 0
    for line in lines:
        t = _c(line)
        if not t:
            found += 1
            continue
        if t in s:
            found += 1
            continue
        best, n = 0.0, len(t)
        step = max(1, n // 8)
        for i in range(0, max(1, len(s) - n + 1), step):
            best = max(best, difflib.SequenceMatcher(a=t, b=s[i:i + n + 3]).ratio())
        found += 1 if best >= 0.82 else 0
    return round(found / float(len(lines)), 4)

# end of code_c81b14441e02

# code: bands_code

def row_bands(n):
    """Split the image into n equal horizontal bands as boxes, top to bottom."""
    n = max(1, int(n))
    return [[int(round(1000.0 * i / n)), 0, int(round(1000.0 * (i + 1) / n)), 1000]
            for i in range(n)]

# end of bands_code
