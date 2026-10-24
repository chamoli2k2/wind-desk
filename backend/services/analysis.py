"""As-of forecast selection and hourly error evaluation; all timestamps are UTC."""
from datetime import datetime, timedelta, timezone
from math import sqrt
from statistics import mean


def dt(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def iso(value):
    return value.isoformat().replace('+00:00', 'Z')


def metrics(rows):
    pairs = [r for r in rows if r['forecast'] is not None and r['actual'] is not None]
    if not pairs:
        return dict(n=0, mae=None, rmse=None, bias=None, wape=None, shortfall=None)
    errors = [r['forecast'] - r['actual'] for r in pairs]
    denominator = sum(abs(r['actual']) for r in pairs)
    return dict(n=len(pairs), mae=mean(map(abs, errors)), rmse=sqrt(mean(e*e for e in errors)),
                bias=mean(errors), wape=100*sum(map(abs, errors))/denominator if denominator else None,
                shortfall=sum(max(0, e) for e in errors))


def analyse(snapshot, cutoff):
    hours, minutes = map(int, cutoff.split(':'))
    forecasts = {}
    for f in snapshot['forecasts']:
        forecasts.setdefault(f['startTime'], []).append(f)
    actuals = {r['startTime']: r['generation'] for r in snapshot['actuals']}
    days = []
    for day in range(1, 32):
        decision = datetime(2026, 1, day, hours, minutes, tzinfo=timezone.utc)
        delivery = decision.replace(hour=0, minute=0) + timedelta(days=1)
        rows = []
        for h in range(24):
            target = delivery + timedelta(hours=h)
            # Select independently for each target. Never use a later publication.
            available = [f for f in forecasts.get(iso(target), []) if dt(f['publishTime']) <= decision]
            selected = max(available, key=lambda f: f['publishTime']) if available else None
            a, b = actuals.get(iso(target)), actuals.get(iso(target + timedelta(minutes=30)))
            # WINDFOR is hourly in this snapshot. Require BOTH half-hours, never fill gaps.
            actual = (a+b)/2 if a is not None and b is not None else None
            forecast = selected['generation'] if selected else None
            rows.append(dict(time=iso(target), hour=f'{h:02}:00', forecast=forecast, actual=actual,
                             error=forecast-actual if forecast is not None and actual is not None else None,
                             publishTime=selected['publishTime'] if selected else None,
                             ageHours=(decision-dt(selected['publishTime'])).total_seconds()/3600 if selected else None))
        days.append(dict(decisionDate=decision.date().isoformat(), deliveryDate=delivery.date().isoformat(),
                         cutoff=iso(decision), rows=rows, metrics=metrics(rows),
                         forecastHours=sum(r['forecast'] is not None for r in rows),
                         actualHours=sum(r['actual'] is not None for r in rows)))
    return dict(days=days, metrics=metrics([r for d in days for r in d['rows']]),
                provenance=snapshot['provenance'], expectedHours=744, cutoff=cutoff)
