"""Run with python -m unittest discover -s tests after installing requirements."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

@unittest.skipUnless(importlib.util.find_spec('flask'), 'Flask must be installed for API tests')
class ApiTests(unittest.TestCase):
    def setUp(self):
        from backend import create_app
        self.directory=tempfile.TemporaryDirectory()
        Path(self.directory.name,'snapshot.json').write_text(json.dumps({'forecasts':[],'actuals':[],'provenance':{}}))
        self.client=create_app({'TESTING':True,'DATA_DIR':self.directory.name}).test_client()
    def tearDown(self):
        self.directory.cleanup()
    def test_validation(self):
        for cutoff in ['25:00','9:00','09:99','bad']:
            self.assertEqual(self.client.get('/api/analysis?cutoff='+cutoff).status_code,400)
    def test_json_csv_and_health(self):
        self.assertEqual(self.client.get('/api/health').status_code,200)
        response=self.client.get('/api/analysis')
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json['days']),31)
        csv=self.client.get('/api/export').text
        self.assertEqual(len(csv.splitlines()),745)
    def test_missing_snapshot(self):
        Path(self.directory.name,'snapshot.json').unlink()
        self.assertEqual(self.client.get('/api/analysis').status_code,503)
        self.assertEqual(self.client.get('/api/export').status_code,503)
