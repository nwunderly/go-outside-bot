import datetime

SECOND = 1
MINUTE = SECOND * 60
HOUR = MINUTE * 60
DAY = HOUR * 24
WEEK = DAY * 7


def approximate_timedelta(dt):
    if isinstance(dt, datetime.timedelta):
        dt = dt.total_seconds()
    s = lambda n: "s" if n != 1 else ""
    if dt >= WEEK:
        t = f"{int(_w := dt // WEEK)} week" + s(_w)
    elif dt >= DAY:
        t = f"{int(_d := dt // DAY)} day" + s(_d)
    elif dt >= HOUR:
        t = f"{int(_h := dt // HOUR)} hour" + s(_h)
    elif dt >= MINUTE:
        t = f"{int(_m := dt // MINUTE)} minute" + s(_m)
    else:
        t = f"{int(_s := dt // SECOND)} second" + s(_s)

    return t
