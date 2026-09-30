#!/usr/bin/env python3
"""Plot the output of batchConnectivity.py — the connectivity bars, as figures.

Two views, both horizontal stacked bars of the distinct-entity distribution
(Complete = identified in every occurrence, Partial = in some, Missing = none),
as a percentage of each bar's entities:

  --institution TARGET   one institution, ALL its connectors      (one figure)
  --connector NAME       one connector, ALL institutions, ranked  (one figure)
  --all-institutions     a --institution figure for every target
  --all-connectors       a --connector figure for every connector

TARGET matches the CSV's Target column (e.g. sjyq.oozvia, member:4374) or a
case-insensitive substring of Target_Name. NAME matches a connector code
(creators_orcid, funders_id, …) or a substring of its label. When the CSV holds
more than one era, pass --era; otherwise the only era present is used.

Requires matplotlib (like prepBoxes.py); the batch CSV is produced by
batchConnectivity.py.

Usage:
  python3 batchConnectivity.py --registry datacite --file clients.txt --csv conn.csv
  python3 plotConnectivity.py conn.csv --institution sjyq.oozvia
  python3 plotConnectivity.py conn.csv --connector creators_orcid
  python3 plotConnectivity.py conn.csv --all-connectors --out figures/
"""
import argparse
import csv
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# connectivity bar semantics — Complete / Partial / Missing
C_COMPLETE, C_PARTIAL, C_MISSING = '#1a8a2a', '#f2c200', '#d6337f'
SURF, INK, INK2, MUTE, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#8a897f', '#e8e6df'

LABELS = {
    'creators_orcid': 'Creators — ORCID',
    'creator_affiliations': 'Creators — affiliation present',
    'creator_affiliations_ror': 'Creator affiliations — ROR',
    'contributors_orcid': 'Contributors — ORCID',
    'contributor_affiliations': 'Contributors — affiliation present',
    'contributor_affiliations_ror': 'Contributor affiliations — ROR',
    'funders_id': 'Funders — identifier',
    'publishers_ror': 'Publisher — ROR',
    'rights_id': 'Rights — identifier',
}


def load(path):
    rows = [r for r in csv.DictReader(open(path, encoding='utf-8')) if r.get('Connector') and r['Connector'] != 'Average']
    for r in rows:
        for k in ('Entities', 'Complete', 'Partial', 'Missing'):
            r[k] = int(r[k] or 0)
    return rows


def pick_era(rows, era):
    eras = sorted({r['Era'] for r in rows})
    if era:
        if era not in eras:
            raise SystemExit(f'era "{era}" not in the CSV (has: {", ".join(eras)})')
        return era
    if len(eras) > 1:
        raise SystemExit(f'the CSV holds several eras ({", ".join(eras)}) — pass --era')
    return eras[0]


def style():
    plt.rcParams.update({'font.family': 'Helvetica', 'text.color': INK, 'axes.edgecolor': MUTE,
                         'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
                         'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF})


def stacked(ax, labels, comp, part, miss):
    """Draw the Complete/Partial/Missing stack (percent) with best at the bottom."""
    y = np.arange(len(labels))
    ax.barh(y, comp, color=C_COMPLETE, label='Complete')
    ax.barh(y, part, left=comp, color=C_PARTIAL, label='Partial')
    ax.barh(y, miss, left=comp + part, color=C_MISSING, label='Missing')
    ax.set_yticks(y, labels, fontsize=8.5)
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 10))
    ax.set_xlabel('Entities (%)')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='x', color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def as_pct(rows):
    """(complete%, partial%, missing%) arrays from entity counts; skip zero-entity rows upstream."""
    comp = np.array([100 * r['Complete'] / r['Entities'] for r in rows])
    part = np.array([100 * r['Partial'] / r['Entities'] for r in rows])
    miss = np.array([100 * r['Missing'] / r['Entities'] for r in rows])
    return comp, part, miss


def fig_institution(rows, target, era, out_dir, stamp):
    era = pick_era(rows, era)
    tl = target.lower()
    sub = [r for r in rows if r['Era'] == era and r['Entities'] > 0
           and (r['Target'] == target or tl in r['Target_Name'].lower() or tl in r['Target'].lower())]
    if not sub:
        print(f'  no connectors with entities for "{target}" ({era}) — skipped'); return None
    name = sub[0]['Target_Name']; tok = sub[0]['Target']
    # order connectors by the catalog order, most-complete first for readability
    order = list(LABELS)
    sub.sort(key=lambda r: order.index(r['Connector']) if r['Connector'] in order else 99, reverse=True)
    labels = [LABELS.get(r['Connector'], r['Connector']) for r in sub]
    comp, part, miss = as_pct(sub)
    fig, ax = plt.subplots(figsize=(11, max(2.2, 0.5 * len(sub) + 1.2)))
    stacked(ax, labels, comp, part, miss)
    era_note = '' if era == 'all' else f' · {era}'
    ax.set_title(f'{name} ({tok}) — connectivity{era_note}', loc='left', fontsize=13, pad=12)
    ax.legend(loc='lower right', fontsize=8, framealpha=.9)
    fig.tight_layout()
    out = out_dir / f'connectivity_{safe(tok)}{"" if era == "all" else "_" + era}__{stamp}.png'
    fig.savefig(out, dpi=200); plt.close(fig); print('  written', out); return out


def fig_connector(rows, connector, era, out_dir, stamp):
    era = pick_era(rows, era)
    code = resolve_connector(rows, connector)
    sub = [r for r in rows if r['Era'] == era and r['Connector'] == code and r['Entities'] > 0]
    if not sub:
        print(f'  no institutions with entities for connector "{connector}" ({era}) — skipped'); return None
    sub.sort(key=lambda r: r['Complete'] / r['Entities'], reverse=True)   # most complete at the bottom (y=0)
    labels = [r['Target_Name'] for r in sub]
    comp, part, miss = as_pct(sub)
    fig, ax = plt.subplots(figsize=(12, max(3, 0.32 * len(sub) + 1.5)))
    stacked(ax, labels, comp, part, miss)
    era_note = '' if era == 'all' else f' · {era}'
    ax.set_title(f'All targets — {LABELS.get(code, code)}{era_note}', loc='left', fontsize=13, pad=12)
    ax.legend(loc='lower right', fontsize=8, framealpha=.9)
    fig.tight_layout()
    out = out_dir / f'connectivity_{code}{"" if era == "all" else "_" + era}__{stamp}.png'
    fig.savefig(out, dpi=200); plt.close(fig); print('  written', out); return out


def resolve_connector(rows, connector):
    codes = list(dict.fromkeys(r['Connector'] for r in rows))
    if connector in codes:
        return connector
    cl = connector.lower()
    hits = [c for c in codes if cl in c.lower() or cl in LABELS.get(c, '').lower()]
    if len(hits) == 1:
        return hits[0]
    raise SystemExit(f'connector "{connector}" is ambiguous or not found (have: {", ".join(codes)})')


def safe(s):
    return re.sub(r'[^0-9A-Za-z._-]', '_', s)


def main():
    from datetime import date
    ap = argparse.ArgumentParser(description='Plot batchConnectivity.py output as stacked Complete/Partial/Missing bars.')
    ap.add_argument('csv', help='batchConnectivity CSV')
    ap.add_argument('--institution', default='', help='one target: all its connectors in one figure')
    ap.add_argument('--connector', default='', help='one connector: all institutions in one figure')
    ap.add_argument('--all-institutions', action='store_true', help='a per-institution figure for every target')
    ap.add_argument('--all-connectors', action='store_true', help='a per-connector figure for every connector')
    ap.add_argument('--era', default='', help='which era to plot (needed only when the CSV holds several)')
    ap.add_argument('--out', default='', help='output directory (default: next to the CSV)')
    args = ap.parse_args()

    rows = load(args.csv)
    if not rows:
        raise SystemExit('no connector rows in that CSV')
    out_dir = Path(args.out) if args.out else Path(args.csv).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    style()

    if not (args.institution or args.connector or args.all_institutions or args.all_connectors):
        ap.error('choose --institution, --connector, --all-institutions, or --all-connectors')

    if args.institution:
        print('Institution view:'); fig_institution(rows, args.institution, args.era, out_dir, stamp)
    if args.connector:
        print('Connector view:'); fig_connector(rows, args.connector, args.era, out_dir, stamp)
    if args.all_institutions:
        print('All institutions:')
        for tok in dict.fromkeys(r['Target'] for r in rows):
            fig_institution(rows, tok, args.era, out_dir, stamp)
    if args.all_connectors:
        print('All connectors:')
        for code in dict.fromkeys(r['Connector'] for r in rows):
            fig_connector(rows, code, args.era, out_dir, stamp)


if __name__ == '__main__':
    main()
