import json
import unittest
from pathlib import Path
from backend.services.analysis import analyse

class SnapshotTests(unittest.TestCase):
    def test_bundled_month_coverage_and_publication_cutoff(self):
        path=Path(__file__).resolve().parents[1]/'data'/'snapshot.json'
        data=analyse(json.loads(path.read_text()),'09:00')
        self.assertEqual(data['metrics']['n'],744)
        for day in data['days']:
            self.assertEqual(day['actualHours'],24)
            self.assertEqual(day['forecastHours'],24)
            for row in day['rows']:
                self.assertLessEqual(row['publishTime'],day['cutoff'])
                self.assertGreaterEqual(row['ageHours'],0)
