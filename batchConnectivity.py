#!/usr/bin/env python3
"""Measure identifier connectivity for many repositories at once — DataCite or Crossref.

The desktop, batch companion to the two web Connectivity tools
(metadataConnectivity.html / crossrefConnectivity.html): for a list of targets it
samples records, normalizes them to one shape, and reports the SAME connectivity
model the bars use — for every connector, the occurrence share (identified
occurrences / all occurrences) AND the distinct-entity view (complete / partial /
missing, with quick wins). One tidy CSV, one row per target x connector.

Connectors (a connector is skipped when its registry has no such field):
  creators_orcid              authors/creators that carry an ORCID
  creator_affiliations_ror    their affiliations that carry a ROR
  contributors_orcid          contributors (DataCite) / editors, translators,
                              chairs (Crossref) that carry an ORCID
  contributor_affiliations_ror  their affiliations that carry a ROR
  funders_id                  funders that carry any funder identifier (ROR /
                              Funder Registry / Crossref Funder ID)
  publishers_ror              the publisher's ROR                (DataCite only)
  rights_id                   rights that carry an identifier/URI (DataCite only)
An extra "Average" row per target is the mean of that target's connector shares.

"Connectivity" differs from completeness: the denominator is the number of
entities that COULD carry an identifier (people, organizations), not the number
of records — so it stays informative even when a record-level score is already
100%. Quick wins are entities identified in SOME occurrences but not all: their
identifier is already known, so it can be copied across without a lookup.

Requires python3 (standard library only — no jq; connectivity is counted here).

Usage:
  python3 batchConnectivity.py --registry datacite --client sjyq.oozvia
  python3 batchConnectivity.py --registry datacite --file clients.txt --max 200
  python3 batchConnectivity.py --registry crossref --member 4374 --member 340
  python3 batchConnectivity.py --registry crossref --issn 1932-6203 --era current
  python3 batchConnectivity.py --registry crossref --file members.txt --type journal-article

Targets: --client (DataCite client id) / --member / --issn / --ror, each
repeatable, plus --file (one id per line; # comments and trailing text ignored).
The registry is inferred from the flags when unambiguous; pass --registry to be
sure (required for --file and --ror). Crossref eras use the Participation Report
definition (current = the current calendar year or the two previous); --era is a
Crossref-only filter (use --query for date filters on DataCite).

Output: batchConnectivity__YYYY-MM-DDThh.csv (override with --csv). Rows are
flushed as produced; rerunning with the same --csv RESUMES (finished target x
filter combinations are skipped).
"""

import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

DATACITE_API = 'https://api.datacite.org'
CROSSREF_API = 'https://api.crossref.org'
MAILTO = 'ted@metadatagamechangers.com'   # Crossref polite pool
UA = f'recuration-watch batchConnectivity (https://github.com/Metadata-Game-Changers/recuration-watch; mailto:{MAILTO})'

# connector -> (source family, identifier kind); families present per registry differ
CONNECTORS = ['creators_orcid', 'creator_affiliations_ror',
              'contributors_orcid', 'contributor_affiliations_ror',
              'funders_id', 'publishers_ror', 'rights_id']

rnd = lambda x: '' if x is None else int(x * 10000 + 0.5) / 10000


def api_get(url, retries=3, backoff=4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            if attempt == retries - 1:
                raise RuntimeError(f'request failed after {retries} tries: {url} ({e})')
            time.sleep(backoff * (attempt + 1))


# ─────────────────────────── identifier detection ───────────────────────────
def _is_orcid(scheme, value):
    return str(scheme or '').upper() == 'ORCID' or 'orcid.org' in str(value or '').lower()


def _is_ror(scheme, value):
    return str(scheme or '').upper() == 'ROR' or 'ror.org' in str(value or '').lower()


def _person_name(p):
    return (p.get('name')
            or ' '.join(x for x in [p.get('givenName'), p.get('familyName')] if x).strip()
            or None)


# ─────────────────────────── DataCite normalization ─────────────────────────
def _dc_person(p):
    if not isinstance(p, dict):
        return None
    orcid = any(_is_orcid(n.get('nameIdentifierScheme'), n.get('nameIdentifier'))
                for n in (p.get('nameIdentifiers') or []) if isinstance(n, dict))
    affs = []
    for a in (p.get('affiliation') or []):
        if isinstance(a, str) and a.strip():
            affs.append({'name': a.strip(), 'ror': False})
        elif isinstance(a, dict) and a.get('name'):
            affs.append({'name': a['name'],
                         'ror': _is_ror(a.get('affiliationIdentifierScheme'), a.get('affiliationIdentifier'))})
    name = _person_name(p)
    return {'name': name, 'orcid': orcid, 'affiliations': affs} if name else None


def normalize_datacite(rec):
    a = rec.get('attributes') or {}
    creators = [x for x in (_dc_person(p) for p in (a.get('creators') or [])) if x]
    contributors = [x for x in (_dc_person(p) for p in (a.get('contributors') or [])) if x]
    funders = [{'name': f.get('funderName'), 'id': bool(f.get('funderIdentifier'))}
               for f in (a.get('fundingReferences') or []) if isinstance(f, dict) and f.get('funderName')]
    pub = a.get('publisher')
    if isinstance(pub, dict) and pub.get('name'):
        publisher = {'name': pub['name'],
                     'ror': _is_ror(pub.get('publisherIdentifierScheme'), pub.get('publisherIdentifier'))}
    elif isinstance(pub, str) and pub.strip():
        publisher = {'name': pub.strip(), 'ror': False}
    else:
        publisher = None
    rights = [{'name': r.get('rights') or r.get('rightsUri') or r.get('rightsIdentifier'),
               'id': bool(r.get('rightsIdentifier') or r.get('rightsUri'))}
              for r in (a.get('rightsList') or []) if isinstance(r, dict)
              and (r.get('rights') or r.get('rightsUri') or r.get('rightsIdentifier'))]
    return {'creators': creators, 'contributors': contributors,
            'funders': funders, 'publisher': publisher, 'rights': rights}


def dc_client_qs(client_id):
    return '' if client_id == 'datacite.all' else f'client-id={urllib.parse.quote(client_id)}&'


def fetch_datacite(client_id, cap, random_sample, resource_type, query):
    filt = ''
    if resource_type:
        filt += f'&resource-type-id={urllib.parse.quote(resource_type)}'
    if query:
        filt += f'&query={urllib.parse.quote(query)}'
    page_size = min(1000, cap)
    records, seen, matching, eff_random = [], set(), None, random_sample
    peek = api_get(f'{DATACITE_API}/dois?{dc_client_qs(client_id)}page%5Bsize%5D=1&disable-facets=true{filt}')
    total = (peek.get('meta') or {}).get('total')
    if isinstance(total, int):
        matching = total
        if total <= cap:
            eff_random = False
        if total == 0:
            return [], 0
    page, requests = 1, 0
    while len(records) < cap:
        requests += 1
        base = f'{DATACITE_API}/dois?{dc_client_qs(client_id)}page%5Bsize%5D={page_size}&affiliation=true&publisher=true{filt}'
        url = f'{base}&random=true&disable-facets=true' if eff_random else f'{base}&page%5Bnumber%5D={page}'
        d = api_get(url)
        batch = d.get('data') or []
        added = 0
        for r in batch:
            if r.get('id') and r['id'] not in seen:
                seen.add(r['id']); records.append(r); added += 1
        t = (d.get('meta') or {}).get('total')
        if isinstance(t, int):
            matching = t
        if eff_random:
            if len(records) >= cap or (matching is not None and len(records) >= matching) or added == 0 or requests >= 30:
                break
        else:
            if not batch or page >= (d.get('meta') or {}).get('totalPages', page) or page >= 10:
                break
            page += 1
    return [normalize_datacite(r) for r in records[:cap]], matching


def datacite_name(client_id):
    if client_id == 'datacite.all':
        return 'All of DataCite'
    try:
        d = api_get(f'{DATACITE_API}/clients/{urllib.parse.quote(client_id)}')
        return (d.get('data') or {}).get('attributes', {}).get('name') or client_id
    except Exception:
        return client_id


# ─────────────────────────── Crossref normalization ─────────────────────────
def _cr_person(p):
    if not isinstance(p, dict):
        return None
    name = p.get('name') or ' '.join(x for x in [p.get('given'), p.get('family')] if x).strip() or None
    if not name:
        return None
    affs = []
    for a in (p.get('affiliation') or []):
        if isinstance(a, dict) and a.get('name'):
            affs.append({'name': a['name'],
                         'ror': any(_is_ror(i.get('id-type'), i.get('id'))
                                    for i in (a.get('id') or []) if isinstance(i, dict))})
    return {'name': name, 'orcid': bool(p.get('ORCID')), 'affiliations': affs}


def normalize_crossref(w):
    creators = [x for x in (_cr_person(p) for p in (w.get('author') or [])) if x]
    contributors = []
    for key in ('editor', 'translator', 'chair'):
        contributors += [x for x in (_cr_person(p) for p in (w.get(key) or [])) if x]
    funders = [{'name': f.get('name'),
                'id': bool(f.get('DOI') or (f.get('id') or []))}
               for f in (w.get('funder') or []) if isinstance(f, dict) and f.get('name')]
    return {'creators': creators, 'contributors': contributors,
            'funders': funders, 'publisher': None, 'rights': []}


def era_filter(era):
    y = datetime.now().year
    if era == 'current':
        return f'from-pub-date:{y - 2}-01-01'
    if era == 'backfile':
        return f'until-pub-date:{y - 3}-12-31'
    return ''


CR_SELECT = 'DOI,author,editor,translator,chair,funder'


def fetch_crossref(token, cap, type_id, era, query):
    """token is issn:… / member:… / ror-id:… — a Crossref /works filter clause."""
    filters = ','.join(f for f in [token, f'type:{type_id}' if type_id else '', era_filter(era)] if f)
    common = (f'{CROSSREF_API}/works?filter={urllib.parse.quote(filters)}'
              f'&select={urllib.parse.quote(CR_SELECT)}&mailto={urllib.parse.quote(MAILTO)}')
    if query:
        common += f'&query={urllib.parse.quote(query)}'
    peek = api_get(f'{common}&rows=0')
    total = (peek.get('message') or {}).get('total-results') or 0
    if not total:
        return [], 0
    works, seen, requests = [], set(), 0
    if total <= cap:
        cursor = '*'
        while len(works) < total and requests < 12:
            requests += 1
            d = (api_get(f'{common}&rows=1000&cursor={urllib.parse.quote(cursor)}').get('message') or {})
            batch = d.get('items') or []
            for w in batch:
                if w.get('DOI') and w['DOI'] not in seen:
                    seen.add(w['DOI']); works.append(w)
            cursor = d.get('next-cursor') or ''
            if not batch or not cursor:
                break
    else:
        while len(works) < cap and requests < 30:
            requests += 1
            batch = (api_get(f'{common}&sample={min(100, cap)}').get('message') or {}).get('items') or []
            added = 0
            for w in batch:
                if w.get('DOI') and w['DOI'] not in seen:
                    seen.add(w['DOI']); works.append(w); added += 1
            if added == 0:
                break
    return [normalize_crossref(w) for w in works[:cap]], total


def crossref_name(token):
    m = re.match(r'member:(\d+)', token)
    if m:
        d = (api_get(f'{CROSSREF_API}/members/{m.group(1)}?mailto={urllib.parse.quote(MAILTO)}').get('message') or {})
        return d.get('primary-name') or token
    m = re.match(r'issn:(.+)', token)
    if m:
        try:
            d = (api_get(f'{CROSSREF_API}/journals/{urllib.parse.quote(m.group(1))}?mailto={urllib.parse.quote(MAILTO)}').get('message') or {})
            return d.get('title') or token
        except Exception:
            return token
    return token


# ─────────────────────────── connectivity engine ────────────────────────────
def _occurrences(records, connector):
    """Yield (entity_name, identified_bool) for every occurrence a connector counts."""
    for r in records:
        if connector == 'creators_orcid':
            for p in r['creators']:
                yield p['name'], p['orcid']
        elif connector == 'creator_affiliations_ror':
            for p in r['creators']:
                for a in p['affiliations']:
                    yield a['name'], a['ror']
        elif connector == 'contributors_orcid':
            for p in r['contributors']:
                yield p['name'], p['orcid']
        elif connector == 'contributor_affiliations_ror':
            for p in r['contributors']:
                for a in p['affiliations']:
                    yield a['name'], a['ror']
        elif connector == 'funders_id':
            for f in r['funders']:
                yield f['name'], f['id']
        elif connector == 'publishers_ror':
            if r['publisher']:
                yield r['publisher']['name'], r['publisher']['ror']
        elif connector == 'rights_id':
            for x in r['rights']:
                yield x['name'], x['id']


def connectivity(records, connector):
    """The web bars' exact model: occurrence share plus the distinct-entity view."""
    ent = {}                       # name -> [occ, identified]
    occ = idocc = 0
    for name, ident in _occurrences(records, connector):
        if not name:
            continue
        occ += 1
        idocc += 1 if ident else 0
        e = ent.setdefault(name, [0, 0])
        e[0] += 1
        e[1] += 1 if ident else 0
    if occ == 0:
        return None
    complete = sum(1 for o, i in ent.values() if i >= o)
    missing = sum(1 for o, i in ent.values() if i == 0)
    partial = len(ent) - complete - missing
    return {'occurrences': occ, 'identified': idocc, 'pct': idocc / occ,
            'entities': len(ent), 'complete': complete, 'partial': partial,
            'missing': missing, 'quick_wins': partial}


# ─────────────────────────────────── main ───────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description='Batch identifier connectivity for DataCite or Crossref repositories.')
    ap.add_argument('--registry', choices=['datacite', 'crossref'], default='',
                    help='which registry (inferred from the flags when unambiguous; required for --file / --ror)')
    ap.add_argument('--client', action='append', default=[], help='DataCite client id (repeatable); "datacite.all" for all of DataCite')
    ap.add_argument('--member', action='append', default=[], help='Crossref member id (repeatable)')
    ap.add_argument('--issn', action='append', default=[], help='Crossref journal ISSN (repeatable)')
    ap.add_argument('--ror', action='append', default=[], help='organization ROR id (repeatable; needs --registry)')
    ap.add_argument('--file', default='', help='text file of ids, one per line (# comments allowed)')
    ap.add_argument('--type', default='', help='content type filter (Crossref work type / DataCite resource-type-id)')
    ap.add_argument('--era', action='append', default=[], choices=['all', 'current', 'backfile'],
                    help='Crossref era (repeatable; default all). Ignored for DataCite — use --query.')
    ap.add_argument('--query', default='', help='free-text/query filter')
    ap.add_argument('--max', type=int, default=200, help='records sampled per target (default 200)')
    ap.add_argument('--sequential', dest='random', action='store_false', help='most-recent records instead of a random sample')
    ap.add_argument('--csv', default='', help='output CSV (default batchConnectivity__<stamp>.csv)')
    args = ap.parse_args()

    # infer registry
    reg = args.registry
    if not reg:
        if args.client and not (args.member or args.issn):
            reg = 'datacite'
        elif (args.member or args.issn) and not args.client:
            reg = 'crossref'
        else:
            ap.error('could not infer --registry — pass --registry datacite|crossref')

    # build the target list (a token per target: Crossref filter clause, or a DataCite client id)
    def file_ids():
        if not args.file:
            return []
        out = []
        for line in Path(args.file).read_text(encoding='utf-8').splitlines():
            line = line.split('#')[0].strip()
            if line:
                out.append(line.split()[0])
        return out

    targets = []   # (token, kind) where kind labels it for display; token is API-ready
    if reg == 'datacite':
        ids = list(args.client) + [i for i in file_ids()]
        if args.ror:
            ap.error('--ror is a Crossref target; for DataCite use --client')
        for c in dict.fromkeys(ids):
            targets.append(c)
        eras = ['all']   # DataCite has no PReP era; one pass
    else:
        toks = [f'member:{m}' for m in args.member] + [f'issn:{s}' for s in args.issn] + [f'ror-id:{r}' for r in args.ror]
        for raw in file_ids():
            if raw.isdigit():
                toks.append(f'member:{raw}')
            elif re.fullmatch(r'\d{4}-\d{3}[\dxX]', raw):
                toks.append(f'issn:{raw}')
            elif re.fullmatch(r'(ror-id:)?[0-9a-z]{9}', raw):
                toks.append(f"ror-id:{raw.split(':')[-1]}")
            else:
                toks.append(f'member:{raw}')
        targets = list(dict.fromkeys(toks))
        eras = args.era or ['all']
    if not targets:
        ap.error('nothing to measure — give a target (--client / --member / --issn / --ror / --file)')

    active = [c for c in CONNECTORS if reg == 'datacite' or c not in ('publishers_ror', 'rights_id')]
    headers = ['Registry', 'Target', 'Target_Name', 'Type', 'Era', 'Query', 'Sample_N', 'Matching',
               'Connector', 'Occurrences', 'Identified', 'Occurrence_Pct',
               'Entities', 'Complete', 'Partial', 'Missing', 'Quick_Wins', 'Run_Date']

    stamp = datetime.now().strftime('%Y-%m-%dT%H')
    out = Path(args.csv) if args.csv else Path(f'batchConnectivity__{stamp}.csv')
    done, mode = set(), 'w'
    if out.exists() and out.stat().st_size:
        with open(out, newline='', encoding='utf-8') as fh:
            r = csv.reader(fh)
            if next(r, None) != headers:
                sys.exit(f'{out} exists with a different column layout — move it aside or pass a fresh --csv')
            for row in r:
                if row:
                    done.add((row[0], row[1], row[3], row[4], row[5]))   # Registry,Target,Type,Era,Query
        mode = 'a'
        print(f'Resuming into {out}: {len(done)} target × filter combinations already present', flush=True)
    fh = open(out, mode, newline='', encoding='utf-8')
    w = csv.writer(fh)
    if mode == 'w':
        w.writerow(headers); fh.flush()

    run_date = datetime.now().strftime('%Y-%m-%d')
    written = 0
    for i, token in enumerate(targets, 1):
        name = None
        for era in eras:
            key = (reg, token, args.type, era, args.query)
            if key in done:
                print(f'{datetime.now():%H:%M:%S} [{i}/{len(targets)}] {token} · {era}: already in CSV — skipped', flush=True)
                continue
            try:
                if reg == 'datacite':
                    recs, matching = fetch_datacite(token, args.max, args.random, args.type, args.query)
                    if name is None:
                        name = datacite_name(token)
                else:
                    recs, matching = fetch_crossref(token, args.max, args.type, era, args.query)
                    if name is None:
                        name = crossref_name(token)
            except Exception as e:
                print(f'{datetime.now():%H:%M:%S} [{i}/{len(targets)}] {token} · {era}: FAILED — {e}', flush=True)
                continue
            if not recs:
                print(f'{datetime.now():%H:%M:%S} [{i}/{len(targets)}] {token} · {era}: no matching records — skipped', flush=True)
                continue
            stats = {c: connectivity(recs, c) for c in active}
            shares = [s['pct'] for s in stats.values() if s]
            avg = sum(shares) / len(shares) if shares else None
            base = [reg, token, name or token, args.type, era, args.query, len(recs), matching if matching is not None else '']
            for c in active:
                s = stats[c]
                if s:
                    w.writerow(base + [c, s['occurrences'], s['identified'], rnd(s['pct']),
                                       s['entities'], s['complete'], s['partial'], s['missing'], s['quick_wins']])
                else:
                    w.writerow(base + [c, 0, 0, '', 0, 0, 0, 0, 0])   # connector present but no occurrences
            w.writerow(base + ['Average', '', '', rnd(avg), '', '', '', '', ''])
            fh.flush()
            written += 1
            pct = lambda v: f'{v:.0%}' if v is not None else '—'
            print(f"{datetime.now():%H:%M:%S} [{i}/{len(targets)}] {token} · {era}: {len(recs)} of {matching:,} · "
                  f"avg {pct(avg)} · ORCID {pct(stats['creators_orcid']['pct'] if stats['creators_orcid'] else None)}", flush=True)

    fh.close()
    if not written and not done:
        sys.exit('no rows produced')
    print(f'Wrote {out} ({written} new target × era block{"" if written == 1 else "s"}'
          + (f', {len(done)} carried over' if done else '') + ')', flush=True)


if __name__ == '__main__':
    main()
