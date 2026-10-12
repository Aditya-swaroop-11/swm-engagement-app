from config import SPLIT


def inr(n: int) -> str:
    """Indian digit grouping: 145200 -> 1,45,200"""
    s = str(int(n)); neg = s.startswith("-"); s = s.lstrip("-")
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + s


def split_compensation(monthly_total: int):
    """Returns [(name, monthly, yearly), ...] plus totals.
    Components are rounded to whole rupees; the last one absorbs any rounding
    difference so the three always add up exactly to the total."""
    monthly_total = int(monthly_total)
    rows, used = [], 0
    for i, (name, pct) in enumerate(SPLIT):
        m = monthly_total - used if i == len(SPLIT) - 1 else round(monthly_total * pct / 100)
        used += m
        rows.append((name, m, m * 12))
    return rows, monthly_total, monthly_total * 12
