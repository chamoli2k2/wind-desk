import unittest
from backend.services.analysis import analyse, metrics


def snapshot(forecasts=None, actuals=None):
    return {'forecasts':forecasts or [],'actuals':actuals or [],'provenance':{}}


def f(value, published='2026-01-01T08:00:00Z', target='2026-01-02T00:00:00Z'):
    return {'startTime':target,'publishTime':published,'generation':value}


class AnalysisTests(unittest.TestCase):
    def test_no_lookahead_inclusive_cutoff_and_unsorted_revisions(self):
        s=snapshot([f(900,'2026-01-01T09:01:00Z'), f(200,'2026-01-01T09:00:00Z'),f(100)])
        row=analyse(s,'09:00')['days'][0]['rows'][0]
        self.assertEqual(row['forecast'],200)
        self.assertEqual(row['ageHours'],0)

    def test_actuals_require_two_half_hours(self):
        a=[{'startTime':'2026-01-02T00:00:00Z','generation':80}]
        self.assertIsNone(analyse(snapshot([f(200)],a),'09:00')['days'][0]['rows'][0]['actual'])
        a.append({'startTime':'2026-01-02T00:30:00Z','generation':120})
        d=analyse(snapshot([f(200)],a),'09:00')['days'][0]
        self.assertEqual(d['rows'][0]['actual'],100)
        self.assertEqual(d['metrics']['bias'],100)
        self.assertEqual(d['metrics']['n'],1)

    def test_month_boundary_and_empty_coverage(self):
        d=analyse(snapshot(),'09:00')
        self.assertEqual(d['days'][-1]['deliveryDate'],'2026-02-01')
        self.assertEqual(sum(len(x['rows']) for x in d['days']),744)
        self.assertEqual(d['metrics']['n'],0)
        self.assertIsNone(d['metrics']['mae'])

    def test_metrics_known_values_and_zero_actual(self):
        m=metrics([{'forecast':200,'actual':100},{'forecast':50,'actual':100}])
        self.assertEqual(m['mae'],75)
        self.assertEqual(m['bias'],25)
        self.assertAlmostEqual(m['rmse'],(6250)**.5)
        self.assertEqual(m['wape'],75)
        self.assertEqual(m['shortfall'],100)
        self.assertIsNone(metrics([{'forecast':1,'actual':0}])['wape'])

    def test_each_target_uses_own_latest_available_forecast(self):
        s=snapshot([f(10),f(30,target='2026-01-02T01:00:00Z'),f(100,'2026-01-01T10:00:00Z')])
        d=analyse(s,'09:00')['days'][0]
        self.assertEqual([r['forecast'] for r in d['rows'][:2]],[10,30])
        self.assertEqual(d['forecastHours'],2)

if __name__=='__main__':
    unittest.main()
