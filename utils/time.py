from datetime import datetime, timedelta, timezone


def parse_when(value: str) -> datetime:
    amount = int(value[:-1]); unit = value[-1].lower()
    delta = {'m': timedelta(minutes=amount), 'h': timedelta(hours=amount), 'd': timedelta(days=amount)}.get(unit)
    if delta is None:
        raise ValueError('Use a relative time like 30m, 2h, or 7d.')
    return datetime.now(timezone.utc) + delta
