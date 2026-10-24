import csv
import io
import re
from flask import Blueprint, current_app, jsonify, request, Response
from backend.models.repository import Repository
from backend.services.analysis import analyse

api = Blueprint('api', __name__)


@api.get('/health')
def health():
    return jsonify(status='ok')


def result():
    cutoff = request.args.get('cutoff', '09:00')
    if not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', cutoff):
        raise ValueError('Cutoff must be HH:MM between 00:00 and 23:59.')
    return analyse(Repository(current_app.config['DATA_DIR']).load(), cutoff)


@api.get('/analysis')
def analysis():
    try:
        return jsonify(result())
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except FileNotFoundError:
        return jsonify(error='No snapshot found. Run python -m backend.ingest.'), 503


@api.get('/export')
def export():
    try:
        data = result()
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except FileNotFoundError:
        return jsonify(error='No snapshot found. Run python -m backend.ingest.'), 503
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['decision_date','decision_cutoff_utc','delivery_time_utc','forecast_mw','actual_mw','error_mw','published_utc'])
    for day in data['days']:
        for row in day['rows']:
            writer.writerow([day['decisionDate'],day['cutoff'],row['time'],row['forecast'],row['actual'],row['error'],row['publishTime']])
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=wind-january-2026.csv'})
