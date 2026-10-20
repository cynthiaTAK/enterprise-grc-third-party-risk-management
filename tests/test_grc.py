import unittest
from datetime import date
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from grc import analyze, read_csv, score_vendor, ROOT, dashboard_html

class GRCTests(unittest.TestCase):
    def setUp(self):
        self.vendors = read_csv(ROOT/'data/vendors.csv')
        self.findings = read_csv(ROOT/'data/findings.csv')

    def test_risk_tier(self):
        self.assertEqual(score_vendor(self.vendors[0]), {'score': 20, 'tier': 'Critical'})

    def test_outstanding_baa(self):
        report = analyze(self.vendors, self.findings, date(2026,10,19))
        self.assertEqual(report['summary']['phi_vendors_without_signed_baa'], 1)

    def test_overdue(self):
        report = analyze(self.vendors, self.findings, date(2026,10,19))
        self.assertEqual(report['summary']['overdue_findings'], 1)

    def test_html_escapes(self):
        self.vendors[0]['vendor_name'] = '<script>alert(1)</script>'
        page = dashboard_html(analyze(self.vendors, self.findings, date(2026,10,19)))
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)

    def test_unknown_vendor_rejected(self):
        bad = [{**self.findings[0], 'vendor_id': 'UNKNOWN'}]
        with self.assertRaises(ValueError):
            analyze(self.vendors, bad, date(2026,10,19))

if __name__ == '__main__':
    unittest.main()
