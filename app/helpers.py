"""Template helpers (dates, prices, quantities, initials)."""
import re
from datetime import date, datetime, timezone

BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def initials(name=""):
    parts = str(name or "").split()
    if not parts:
        return "?"
    return (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()


def _as_dt(value):
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    return None


def format_date(value):
    d = _as_dt(value)
    return f"{d.day} {BULAN[d.month - 1]} {d.year}" if d else ""


def time_ago(value):
    d = _as_dt(value)
    if not d:
        return ""
    s = max(0, (datetime.now(timezone.utc) - d).total_seconds())
    if s < 60:
        return "baru saja"
    if s < 3600:
        return f"{int(s // 60)} menit yang lalu"
    if s < 86400:
        return f"{int(s // 3600)} jam yang lalu"
    if s < 86400 * 7:
        return f"{int(s // 86400)} hari yang lalu"
    return format_date(d)


def _short(n):
    return f"{round(n / 1000)}rb" if n >= 1000 else str(n)


def price_range(lo, hi):
    if lo is None and hi is None:
        return "-"
    if hi is None or lo == hi:
        return f"Rp{_short(lo)}"
    return f"Rp{_short(lo)}–{_short(hi)}"


def compact_number(n):
    n = int(n or 0)
    return f"{n / 1000:.1f}".replace(".0", "") + "k" if n >= 1000 else str(n)


def format_qty(q):
    if q is None:
        return ""
    whole = int(q)
    frac = q - whole
    if frac < 0.04:
        return str(whole)
    for v, label in [(0.25, "1/4"), (0.33, "1/3"), (0.5, "1/2"), (0.67, "2/3"), (0.75, "3/4")]:
        if abs(frac - v) < 0.04:
            return f"{whole} {label}" if whole else label
    return str(round(q, 1))


def qty_attr(q):
    """Quantity as a plain string for data-qty attributes ('' = secukupnya)."""
    return "" if q is None else ("%g" % q)


def youtube_embed(url):
    if not url:
        return None
    m = re.search(r"(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([\w-]{11})", str(url))
    return f"https://www.youtube-nocookie.com/embed/{m.group(1)}" if m else None


TEMPLATE_HELPERS = dict(
    initials=initials, format_date=format_date, time_ago=time_ago, price_range=price_range,
    compact_number=compact_number, format_qty=format_qty, qty_attr=qty_attr, youtube_embed=youtube_embed,
)
