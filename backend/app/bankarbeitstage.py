"""German bank holiday and business day calculation utility.

Supports:
- German public holidays (federal + per-Bundesland)
- Bank business day calculations (excluding weekends + holidays)
- "N-th last bank business day" logic (e.g. drittletzter Bankarbeitstag)
- Offset from deadlines (e.g. "SV-Nachweis = SV-Zahlung minus 2 Bankarbeitstage")
- "Next business day" shift for weekends/holidays
"""

from datetime import date, timedelta
from typing import Optional

# ─────────────────────────────────────────
# German Public Holidays
# ─────────────────────────────────────────

def _ostersonntag(year: int) -> date:
    """Compute Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def feiertage_deutschland(year: int, bundesland: Optional[str] = None) -> set:
    """Return set of public holidays for a given year and optional Bundesland.

    If bundesland is None, only federal holidays are returned.
    """
    ostern = _ostersonntag(year)

    # Federal holidays (all Bundesländer)
    holidays = {
        date(year, 1, 1),       # Neujahr
        ostern - timedelta(days=2),   # Karfreitag
        ostern + timedelta(days=1),   # Ostermontag
        date(year, 5, 1),       # Tag der Arbeit
        ostern + timedelta(days=39),  # Christi Himmelfahrt
        ostern + timedelta(days=50),  # Pfingstmontag
        date(year, 10, 3),      # Tag der Deutschen Einheit
        date(year, 12, 25),     # 1. Weihnachtsfeiertag
        date(year, 12, 26),     # 2. Weihnachtsfeiertag
    }

    if not bundesland:
        return holidays

    bl = bundesland.upper().strip()

    # Heilige Drei Könige (6.1.) – BW, BY, ST
    if bl in ("BW", "BY", "ST"):
        holidays.add(date(year, 1, 6))

    # Frauentag (8.3.) – BE, MV
    if bl in ("BE", "MV"):
        holidays.add(date(year, 3, 8))

    # Fronleichnam – BW, BY, HE, NW, RP, SL
    if bl in ("BW", "BY", "HE", "NW", "RP", "SL"):
        holidays.add(ostern + timedelta(days=60))

    # Mariä Himmelfahrt (15.8.) – BY (partially), SL
    if bl in ("BY", "SL"):
        holidays.add(date(year, 8, 15))

    # Weltkindertag (20.9.) – TH
    if bl in ("TH",):
        holidays.add(date(year, 9, 20))

    # Reformationstag (31.10.) – BB, HB, HH, MV, NI, SN, SH, ST, TH
    if bl in ("BB", "HB", "HH", "MV", "NI", "SN", "SH", "ST", "TH"):
        holidays.add(date(year, 10, 31))

    # Allerheiligen (1.11.) – BW, BY, NW, RP, SL
    if bl in ("BW", "BY", "NW", "RP", "SL"):
        holidays.add(date(year, 11, 1))

    # Buß- und Bettag – SN (Wednesday before Totensonntag = last Sun before Advent)
    if bl in ("SN",):
        # Totensonntag = last Sunday before 1st Advent
        # 1st Advent = 4th Sunday before 25.12.
        weihnachten = date(year, 12, 25)
        # 4th Sunday before Christmas
        first_advent = weihnachten - timedelta(days=(weihnachten.weekday() + 22) % 7 + 1)
        totensonntag = first_advent - timedelta(days=7)
        buss_bettag = totensonntag - timedelta(days=4)  # Wednesday before
        holidays.add(buss_bettag)

    return holidays


# ─────────────────────────────────────────
# Business Day Helpers
# ─────────────────────────────────────────

def ist_bankarbeitstag(d: date, bundesland: Optional[str] = None) -> bool:
    """Check if a date is a bank business day (not weekend, not holiday)."""
    if d.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    return d not in feiertage_deutschland(d.year, bundesland)


def naechster_bankarbeitstag(d: date, bundesland: Optional[str] = None) -> date:
    """Return d if it is a business day, else the next business day."""
    while not ist_bankarbeitstag(d, bundesland):
        d += timedelta(days=1)
    return d


def vorheriger_bankarbeitstag(d: date, bundesland: Optional[str] = None) -> date:
    """Return d if it is a business day, else the previous business day."""
    while not ist_bankarbeitstag(d, bundesland):
        d -= timedelta(days=1)
    return d


def bankarbeitstag_offset(d: date, offset: int, bundesland: Optional[str] = None) -> date:
    """Move by `offset` bank business days from d. Positive = forward, negative = backward."""
    step = 1 if offset > 0 else -1
    remaining = abs(offset)
    current = d
    while remaining > 0:
        current += timedelta(days=step)
        if ist_bankarbeitstag(current, bundesland):
            remaining -= 1
    return current


def n_ter_letzter_bankarbeitstag(year: int, month: int, n: int,
                                  bundesland: Optional[str] = None) -> date:
    """Return the n-th last bank business day of a month.

    n=1 → last business day
    n=3 → third-to-last business day (drittletzter Bankarbeitstag)
    """
    # Start from last day of month
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    count = 0
    current = last_day
    while count < n:
        if ist_bankarbeitstag(current, bundesland):
            count += 1
            if count == n:
                return current
        current -= timedelta(days=1)
    return current


def naechster_werktag_wenn_wochenende_feiertag(d: date, bundesland: Optional[str] = None) -> date:
    """Shift to next working day if d falls on weekend/holiday (LSt rule)."""
    return naechster_bankarbeitstag(d, bundesland)


# ─────────────────────────────────────────
# Deadline Calculation
# ─────────────────────────────────────────

def berechne_frist(
    jahr: int,
    monat: int,
    regeltyp: str,
    regel_config: dict,
    bundesland: Optional[str] = None,
) -> Optional[date]:
    """Calculate a deadline date from rule type and config.

    regeltyp values:
        - "fixes_datum": config = {"tag": 15, "monat_offset": 0}
        - "relativ_monatsende": config = {"tage_nach_monatsende": 10}
        - "relativ_bankarbeitstage": config = {"n_ter_letzter": 3}
        - "relativ_andere_frist": handled externally (needs reference date)
        - "ereignisbasiert": returns None (trigger-based)
    """
    if regeltyp == "fixes_datum":
        tag = regel_config.get("tag", 1)
        monat_offset = regel_config.get("monat_offset", 0)
        target_monat = monat + monat_offset
        target_jahr = jahr
        while target_monat > 12:
            target_monat -= 12
            target_jahr += 1
        while target_monat < 1:
            target_monat += 12
            target_jahr -= 1
        # Clamp day to valid range
        import calendar
        max_day = calendar.monthrange(target_jahr, target_monat)[1]
        tag = min(tag, max_day)
        d = date(target_jahr, target_monat, tag)
        # Apply weekend/holiday shift if configured
        if regel_config.get("verschiebung_naechster_werktag", False):
            d = naechster_werktag_wenn_wochenende_feiertag(d, bundesland)
        return d

    elif regeltyp == "relativ_monatsende":
        tage = regel_config.get("tage_nach_monatsende", 0)
        if monat == 12:
            monatsende = date(jahr + 1, 1, 1) - timedelta(days=1)
        else:
            monatsende = date(jahr, monat + 1, 1) - timedelta(days=1)
        return monatsende + timedelta(days=tage)

    elif regeltyp == "relativ_bankarbeitstage":
        n = regel_config.get("n_ter_letzter", 1)
        return n_ter_letzter_bankarbeitstag(jahr, monat, n, bundesland)

    elif regeltyp == "ereignisbasiert":
        return None  # event-triggered, no fixed date

    return None


def berechne_frist_relativ(
    referenz_datum: date,
    offset_bankarbeitstage: int,
    bundesland: Optional[str] = None,
) -> date:
    """Calculate a deadline relative to another deadline by bank business days."""
    return bankarbeitstag_offset(referenz_datum, offset_bankarbeitstage, bundesland)
