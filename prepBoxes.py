#!/usr/bin/env python3
"""Box plots of Crossref Participation Report averages by content type, one figure per era.

Companion to crossrefParticipation.py: reads its --all harvest CSV (which carries an
Average column — the mean of the fourteen checks per member x era x content type) and
draws one box-plot figure per era, x = content type, one point per member. Quartiles
and the upper-whisker endpoint are labeled; the exact numbers behind the boxes are the
Tukey values (whiskers at the extreme data inside the 1.5xIQR fences).

Only content types with at least --min-n members in EVERY era are drawn, in the same
order and colors across the figures, so the eras compare directly.

Style follows the MGC house distribution figures (RADS/Universities usViolins.py):
warm off-white surface, per-group colored boxes, labeled medians, percent axis.

Requires matplotlib + numpy (unlike the harvester, which is stdlib only).

Usage:
  python3 crossrefParticipation.py --all --csv allMembers.csv
  python3 prepBoxes.py allMembers.csv
  python3 prepBoxes.py allMembers.csv --out figures/ --min-n 250

Output: crossrefParticipation_boxes_{all,current,backfile}__YYYY-MM-DD.png next to the
input CSV (or in --out).
"""
import argparse
import csv
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

PALETTE = ['#2a78d6', '#eb6834', '#1baf7a', '#a352cc', '#d6a12a',
           '#d64545', '#2ab5c9', '#7a8a2a', '#c94d8f', '#6b6f78', '#4f63c9', '#9a7b4f']
SURF, INK, INK2, MUTE = '#fcfcfb', '#0b0b0b', '#52514e', '#8a897f'


def main():
    ap = argparse.ArgumentParser(description='Box plots of Participation Report averages by content type, per era.')
    ap.add_argument('csv', help='crossrefParticipation harvest CSV (needs the Average column)')
    ap.add_argument('--out', default='', help='output directory (default: next to the input CSV)')
    ap.add_argument('--min-n', type=int, default=100,
                    help='draw a content type only if this many members carry it in every era (default 100)')
    args = ap.parse_args()

    y = date.today().year
    eras = [('all', 'all time'), ('current', f'current ({y - 2}–{y})'), ('backfile', f'backfile (≤{y - 3})')]
    out_dir = Path(args.out) if args.out else Path(args.csv).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()

    rows = [r for r in csv.DictReader(open(args.csv, encoding='utf-8')) if r.get('Average')]
    if not rows:
        raise SystemExit('no rows with an Average column — harvest with crossrefParticipation.py first')
    data = {}
    for r in rows:
        data.setdefault(r['Era'], {}).setdefault(r['Content_Type'], []).append(float(r['Average']))
    types = sorted(
        (t for t in data.get('all', {}) if all(len(data.get(e, {}).get(t, [])) >= args.min_n for e, _ in eras)),
        key=lambda t: -len(data['all'][t]))
    if not types:
        raise SystemExit(f'no content type reaches {args.min_n} members in every era — lower --min-n')
    print('content types:', ', '.join(types))
    colors = {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(types)}

    plt.rcParams.update({'font.family': 'Helvetica', 'text.color': INK, 'axes.edgecolor': MUTE,
                         'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
                         'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF})

    for era, era_label in eras:
        vals = [data[era][t] for t in types]
        fig, ax = plt.subplots(figsize=(12.5, 5.5))
        pos = np.arange(len(types), dtype=float)
        bp = ax.boxplot(vals, positions=pos, widths=0.6, patch_artist=True,
                        showfliers=True, whis=1.5,
                        flierprops=dict(marker='o', markersize=2.5, alpha=0.35, markeredgecolor='none'))
        for i, t in enumerate(types):
            c = colors[t]
            bp['boxes'][i].set_facecolor(c); bp['boxes'][i].set_alpha(0.45)
            bp['boxes'][i].set_edgecolor(c); bp['boxes'][i].set_linewidth(1.2)
            bp['medians'][i].set_color(c); bp['medians'][i].set_linewidth(2)
            bp['fliers'][i].set_markerfacecolor(c)
            for part in ('whiskers', 'caps'):
                for artist in bp[part][2 * i:2 * i + 2]:
                    artist.set_color(c); artist.set_linewidth(1.1)
            q1, med, q3 = np.percentile(vals[i], [25, 50, 75])
            v = np.asarray(vals[i])
            hi = v[v <= q3 + 1.5 * (q3 - q1)].max()   # upper whisker endpoint (Tukey)
            ax.annotate(f'{med:.2f}', (pos[i], med), xytext=(0, 9), textcoords='offset points',
                        ha='center', fontsize=8, color=INK2)
            # quartile + whisker labels, skipped where they would collide (degenerate boxes, the axis)
            if hi - q3 > 0.02 and hi > 0.03:
                ax.annotate(f'{hi:.2f}', (pos[i], hi), xytext=(0, 4), textcoords='offset points',
                            ha='center', fontsize=7, color=MUTE)
            if q3 - med > 0.02:
                ax.annotate(f'{q3:.2f}', (pos[i], q3), xytext=(0, 4), textcoords='offset points',
                            ha='center', fontsize=7, color=MUTE)
            if med - q1 > 0.02 and q1 > 0.03:
                ax.annotate(f'{q1:.2f}', (pos[i], q1), xytext=(0, -11), textcoords='offset points',
                            ha='center', fontsize=7, color=MUTE)
        ax.set_xticks(pos, [f'{t}\n(n={len(data[era][t]):,})' for t in types], fontsize=8.5)
        ax.set_ylim(0, 1)
        ax.set_yticks(np.arange(0, 1.01, 0.25))
        ax.set_yticklabels([f'{int(v * 100)}%' for v in np.arange(0, 1.01, 0.25)])
        ax.set_ylabel('Participation Report average (14 checks)')
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', color='#e8e6df', lw=0.8)
        ax.set_axisbelow(True)
        ax.set_title(f'Crossref Participation Report average by content type — {era_label} '
                     f'(one point per member, quartiles labeled)', loc='left', fontsize=13, pad=12)
        fig.tight_layout()
        out = out_dir / f'crossrefParticipation_boxes_{era}__{stamp}.png'
        fig.savefig(out, dpi=200)
        plt.close(fig)
        print('written', out)


if __name__ == '__main__':
    main()
