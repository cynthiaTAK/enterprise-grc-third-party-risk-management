"""Synthetic third-party GRC risk assessment and reporting (stdlib only)."""
import argparse
import csv
import html
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path):
    with Path(path).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def score_vendor(vendor):
    """Illustrative 5x5 inherent risk matrix; not CVSS or a regulatory score."""
    likelihood = int(vendor['inherent_likelihood'])
    impact = int(vendor['inherent_impact'])
    if not (1 <= likelihood <= 5 and 1 <= impact <= 5):
        raise ValueError('Likelihood and impact must be between 1 and 5')
    score = likelihood * impact
    tier = 'Critical' if score >= 20 else 'High' if score >= 12 else 'Medium' if score >= 6 else 'Low'
    return {'score': score, 'tier': tier}


def analyze(vendors, findings, as_of):
    vendor_ids = {v['vendor_id'] for v in vendors}
    if len(vendor_ids) != len(vendors):
        raise ValueError('Duplicate vendor ID')
    if any(f['vendor_id'] not in vendor_ids for f in findings):
        raise ValueError('Finding references unknown vendor')
    enriched = [{**v, **score_vendor(v)} for v in vendors]
    open_findings = [f for f in findings if f['status'].strip().lower() != 'closed']
    overdue = [f for f in open_findings if date.fromisoformat(f['due_date']) < as_of]
    outstanding_baa = [v for v in vendors if v['phi_access'] == 'Yes' and v['baa_status'] != 'Signed']
    missing_soc2 = [v for v in vendors if v['soc2_status'] in ('Missing', 'Expired')]
    return {
        'as_of': as_of.isoformat(),
        'summary': {
            'vendors_assessed': len(vendors),
            'high_or_critical_inherent_risk': sum(v['tier'] in ('High', 'Critical') for v in enriched),
            'open_findings': len(open_findings),
            'overdue_findings': len(overdue),
            'phi_vendors_without_signed_baa': len(outstanding_baa),
            'missing_or_expired_soc2': len(missing_soc2),
        },
        'risk_tiers': dict(Counter(v['tier'] for v in enriched)),
        'vendors': enriched,
        'overdue_findings': overdue,
        'findings': findings,
    }


def dashboard_html(result):
    summary = result['summary']
    cards = ''.join(f'<section class="card"><strong>{html.escape(key.replace("_", " ").title())}</strong><div class="number">{value}</div></section>' for key, value in summary.items())
    rows = ''.join('<tr>' + ''.join(f'<td>{html.escape(str(v[k]))}</td>' for k in ('vendor_name', 'service', 'phi_access', 'score', 'tier', 'baa_status', 'soc2_status')) + '</tr>' for v in result['vendors'])
    finding_rows = ''.join('<tr>' + ''.join(f'<td>{html.escape(str(f[k]))}</td>' for k in ('finding_id','vendor_id','description','severity','status','due_date','owner')) + '</tr>' for f in result['findings'])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Enterprise GRC Dashboard</title><style>body{{font:16px system-ui;background:#f4f7fb;color:#1b2940;max-width:1100px;margin:40px auto;padding:0 20px}}h1{{margin-bottom:0}}.muted{{color:#52617a}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:25px 0}}.card{{background:white;padding:20px;border-radius:12px;box-shadow:0 2px 8px #dae2ed}}.number{{font-size:32px;font-weight:700;margin-top:12px}}table{{border-collapse:collapse;width:100%;background:white;margin-bottom:32px}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #dce3ed}}th{{background:#e4ebf5}}.scroll{{overflow-x:auto}}footer{{margin:30px 0;color:#52617a}}</style></head><body><h1>Enterprise GRC & Third-Party Risk</h1><p class="muted">Demonstration dashboard | As of {html.escape(result['as_of'])} | Synthetic vendors and findings</p><div class="grid">{cards}</div><h2>Vendor risk register</h2><div class="scroll"><table><thead><tr><th>Vendor</th><th>Service</th><th>PHI access</th><th>Risk score</th><th>Tier</th><th>BAA</th><th>SOC 2</th></tr></thead><tbody>{rows}</tbody></table></div><h2>Remediation tracker</h2><div class="scroll"><table><thead><tr><th>Finding</th><th>Vendor ID</th><th>Description</th><th>Severity</th><th>Status</th><th>Due date</th><th>Owner</th></tr></thead><tbody>{finding_rows}</tbody></table></div><footer>Illustrative scoring only. Do not use for real compliance decisions without review and validation.</footer></body></html>'''


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic GRC risk reports')
    parser.add_argument('--as-of', type=date.fromisoformat, default=date.today(), help='YYYY-MM-DD')
    parser.add_argument('--output', type=Path, default=ROOT / 'reports')
    args = parser.parse_args()
    result = analyze(read_csv(ROOT/'data/vendors.csv'), read_csv(ROOT/'data/findings.csv'), args.as_of)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'risk_report.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    (args.output/'dashboard.html').write_text(dashboard_html(result), encoding='utf-8')
    print(f"Created {args.output/'risk_report.json'} and {args.output/'dashboard.html'}")


if __name__ == '__main__':
    main()
