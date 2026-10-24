"""Download Elexon-only data. Run explicitly; the web process never calls upstream."""
import hashlib
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from backend.services.analysis import dt, iso

BASE = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/'


def fetch(job):
    dataset, start, end = job
    params = {'publishDateTimeFrom':iso(start), 'publishDateTimeTo':iso(end)} if dataset == 'WINDFOR' else {'settlementDateFrom':start.date().isoformat(), 'settlementDateTo':start.date().isoformat()}
    url = BASE + dataset + '/stream?' + urlencode(params)
    for attempt in range(4):
        try:
            with urlopen(url, timeout=90) as response:
                body = response.read()
            records = json.loads(body)
            if not isinstance(records, list):
                raise ValueError('Expected a stream array')
            return dataset, records, {'url':url,'sha256':hashlib.sha256(body).hexdigest(),'rows':len(records)}
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def main():
    start = datetime(2025,12,30,tzinfo=timezone.utc)
    jobs = [('WINDFOR',start+timedelta(days=i),start+timedelta(days=i+1)) for i in range(33)]
    start = datetime(2026,1,2,tzinfo=timezone.utc)
    jobs += [('FUELHH',start+timedelta(days=i),start+timedelta(days=i+1)) for i in range(31)]
    forecasts, actuals, sources = {}, {}, []
    for dataset, records, source in ThreadPoolExecutor(max_workers=4).map(fetch, jobs):
        sources.append(source)
        for row in records:
            if dataset == 'FUELHH' and row.get('fuelType') != 'WIND':
                continue
            target = dt(row['startTime'])
            if not datetime(2026,1,2,tzinfo=timezone.utc) <= target < datetime(2026,2,2,tzinfo=timezone.utc):
                continue
            value = row['generation']
            if value is None:
                continue
            if not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0:
                raise ValueError('Invalid generation value')
            clean = {'startTime':iso(target),'generation':value}
            if dataset == 'WINDFOR':
                if target.minute != 0 or target.second != 0:
                    raise ValueError('Forecast resolution changed; review hourly alignment')
                clean['publishTime'] = iso(dt(row['publishTime']))
                key = (clean['startTime'],clean['publishTime'])
                if key in forecasts and forecasts[key] != clean:
                    raise ValueError('Conflicting forecast revision')
                forecasts[key] = clean
            else:
                if target.minute not in (0,30) or target.second != 0:
                    raise ValueError('Unexpected actual resolution')
                key = clean['startTime']
                # Conflicting duplicates fail loudly rather than silently changing the benchmark.
                if key in actuals and actuals[key] != clean:
                    raise ValueError('Conflicting actual revision')
                actuals[key] = clean
        print(dataset,source['rows'], flush=True)
    output = {'forecasts':list(forecasts.values()),'actuals':list(actuals.values()),'provenance':{
        'source':'Elexon Insights Solution','retrievedAt':iso(datetime.now(timezone.utc)),
        'forecastCount':len(forecasts),'actualCount':len(actuals),'sources':sources,
        'alignment':'Hourly WINDFOR compared with mean of both FUELHH WIND half-hours',
        'forecastLookbackStart':'2025-12-30T00:00:00Z'}}
    directory = Path(os.environ.get('DATA_DIR','data')); directory.mkdir(exist_ok=True,parents=True)
    temporary = directory / 'snapshot.tmp'
    temporary.write_text(json.dumps(output,separators=(',',':')))
    temporary.replace(directory / 'snapshot.json')
    print('Snapshot saved:',len(forecasts),'forecasts;',len(actuals),'actuals')

if __name__ == '__main__':
    main()
