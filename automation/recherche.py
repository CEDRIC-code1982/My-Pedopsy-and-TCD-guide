#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recherche PubMed reproductible, avec mémoire des travaux déjà examinés.

Le problème résolu : sans mémoire, chaque run réexamine les mêmes articles.
Le run du 28 août 2026 est retombé sur six travaux déjà dans le corpus avant
de trouver du neuf. Le journal retient aussi les articles ÉCARTÉS et pourquoi,
ce qui évite de rejuger deux fois la même chose.

Sous-commandes
  amorcer            initialise le journal depuis les entrées du corpus
  chercher           liste les travaux entrés dans PubMed depuis la dernière fois
  noter PMID STATUT  journalise une décision (retenu | ecarte), avec sa raison
  stats              état du journal

Exemples
  python3 automation/recherche.py chercher --depuis 2026/08/01
  python3 automation/recherche.py chercher --axe tcd --axe tcd-ado
  python3 automation/recherche.py noter 42275028 retenu "méta-analyse DBT-ST"
  python3 automation/recherche.py noter 42555471 ecarte "cas clinique isolé"
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "automation"))
from requetes import AXES, PAR_NOM                       # noqa: E402

JOURNAL = RACINE / "automation" / "journal-pubmed.json"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PAUSE = 0.4          # NCBI tolère 3 requêtes/seconde sans clé d'API
STATUTS = ("retenu", "ecarte")


# --------------------------------------------------------------------------- io
def charge():
    if JOURNAL.exists():
        return json.loads(JOURNAL.read_text(encoding="utf-8"))
    return {"pmids": {}, "derniere_recherche": None, "sans_pmid": []}


def sauve(j):
    JOURNAL.write_text(json.dumps(j, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                       encoding="utf-8")


def appel(endpoint, **params):
    params.setdefault("db", "pubmed")
    url = f"{EUTILS}/{endpoint}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        brut = r.read().decode("utf-8", "replace")
    time.sleep(PAUSE)
    return brut


def esearch(terme, retmax=200):
    d = json.loads(appel("esearch.fcgi", term=terme, retmax=retmax, retmode="json"))
    return d["esearchresult"].get("idlist", []), int(d["esearchresult"].get("count", 0))


def esummary(pmids):
    if not pmids:
        return {}
    out = {}
    for i in range(0, len(pmids), 150):
        lot = pmids[i:i + 150]
        d = json.loads(appel("esummary.fcgi", id=",".join(lot), retmode="json"))["result"]
        for u in d.get("uids", []):
            out[u] = d[u]
    return out


# ------------------------------------------------------------------- sous-commandes
def cmd_amorcer(args):
    """Le corpus existant devient la mémoire de départ : tout ce qui y figure
    est « retenu », et ne sera plus proposé comme nouveauté."""
    src = (RACINE / "index.html").read_text(encoding="utf-8")
    veille = json.loads(re.search(r'VEILLE_DATA\s*=\s*(\[.*?\])\s*;\s*\n/\* VEILLE_DATA_END',
                                  src, re.S).group(1))
    j = charge()
    directs, a_resoudre, sans = {}, [], []
    for e in veille:
        m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", e["url"])
        if m:
            directs[m.group(1)] = e
        elif e["url"].startswith("https://doi.org/"):
            a_resoudre.append(e)
        else:
            sans.append({"url": e["url"], "titre": e["titre"]})

    print(f"{len(veille)} entrées : {len(directs)} PMID directs, "
          f"{len(a_resoudre)} DOI à résoudre, {len(sans)} hors PubMed.")

    for pmid, e in directs.items():
        j["pmids"][pmid] = {"statut": "retenu", "raison": "présent dans le corpus",
                            "date": str(date.today()), "titre": e["titre"][:110]}

    echecs = []
    for n, e in enumerate(a_resoudre, 1):
        doi = e["url"][len("https://doi.org/"):]
        try:
            ids, _ = esearch(f"{doi}[AID]", retmax=2)
        except Exception as exc:
            echecs.append((doi, type(exc).__name__)); continue
        if ids:
            j["pmids"][ids[0]] = {"statut": "retenu", "raison": "présent dans le corpus",
                                  "date": str(date.today()), "titre": e["titre"][:110]}
        else:
            echecs.append((doi, "non indexé"))
        if n % 20 == 0:
            print(f"  … {n}/{len(a_resoudre)} DOI résolus")

    j["sans_pmid"] = sans + [{"url": "https://doi.org/" + d, "titre": r} for d, r in echecs]
    sauve(j)
    print(f"\nJournal amorcé : {len(j['pmids'])} PMID mémorisés, "
          f"{len(echecs)} DOI non résolus, {len(sans)} entrées hors PubMed.")
    for doi, raison in echecs:
        print(f"  · {raison} : {doi}")
    return 0


def cmd_chercher(args):
    j = charge()
    connus = set(j["pmids"])
    depuis = args.depuis or j.get("derniere_recherche") or "2025/01/01"
    axes = [PAR_NOM[n] for n in args.axe] if args.axe else AXES
    print(f"Recherche des travaux entrés dans PubMed depuis le {depuis} "
          f"({len(axes)} axe(s), {len(connus)} PMID déjà examinés)\n")

    nouveaux = {}
    for a in axes:
        terme = f'({a["requete"]}) AND ("{depuis}"[EDAT] : "3000"[EDAT])'
        try:
            ids, total = esearch(terme, retmax=args.max)
        except Exception as exc:
            print(f"  ⚠️  {a['nom']} : {type(exc).__name__}"); continue
        inedits = [i for i in ids if i not in connus]
        tronque = " (tronqué)" if total > args.max else ""
        print(f"  {a['nom']:22} {total:5} résultats{tronque} · {len(inedits):4} inédits")
        for i in inedits:
            nouveaux.setdefault(i, []).append(a["nom"])

    if not nouveaux:
        print("\nAucun travail inédit. Rien à examiner.")
        return 0

    print(f"\n{len(nouveaux)} travaux inédits :\n")
    infos = esummary(list(nouveaux))
    lignes = []
    for pmid, axes_ in nouveaux.items():
        r = infos.get(pmid, {})
        lignes.append((r.get("sortpubdate", r.get("pubdate", "")), pmid, r, axes_))
    for _, pmid, r, axes_ in sorted(lignes, reverse=True):
        print(f"{pmid} | {r.get('pubdate','')[:11]:11} | {r.get('source','')[:24]:24} "
              f"| {','.join(axes_)[:26]:26} | {r.get('title','')[:88]}")

    if not args.essai:
        j["derniere_recherche"] = str(date.today()).replace("-", "/")
        sauve(j)
        print(f"\nDate de dernière recherche mise à jour : {j['derniere_recherche']}")
    print("\nJournaliser chaque décision :  "
          "python3 automation/recherche.py noter <PMID> retenu|ecarte \"<raison>\"")
    return 0


def cmd_noter(args):
    if args.statut not in STATUTS:
        print(f"statut invalide : {args.statut} (attendu : {' | '.join(STATUTS)})")
        return 1
    j = charge()
    titre = ""
    try:
        titre = esummary([args.pmid]).get(args.pmid, {}).get("title", "")[:110]
    except Exception:
        pass
    j["pmids"][args.pmid] = {"statut": args.statut, "raison": args.raison,
                             "date": str(date.today()), "titre": titre}
    sauve(j)
    print(f"{args.pmid} → {args.statut} : {args.raison}")
    return 0


def cmd_stats(args):
    j = charge()
    from collections import Counter
    c = Counter(v["statut"] for v in j["pmids"].values())
    print(f"Journal : {len(j['pmids'])} PMID · "
          f"{c.get('retenu', 0)} retenus · {c.get('ecarte', 0)} écartés")
    print(f"Entrées hors PubMed : {len(j.get('sans_pmid', []))}")
    print(f"Dernière recherche : {j.get('derniere_recherche') or 'jamais'}")
    if args.ecartes:
        print("\nÉcartés :")
        for pmid, v in sorted(j["pmids"].items()):
            if v["statut"] == "ecarte":
                print(f"  {pmid} · {v['raison']}\n      {v.get('titre','')[:96]}")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("amorcer").set_defaults(f=cmd_amorcer)
    c = sub.add_parser("chercher")
    c.add_argument("--depuis", help="date EDAT de départ, format AAAA/MM/JJ")
    c.add_argument("--axe", action="append", choices=list(PAR_NOM), help="restreindre à un axe")
    c.add_argument("--max", type=int, default=200, help="résultats maximum par axe")
    c.add_argument("--essai", action="store_true", help="ne pas mémoriser la date de recherche")
    c.set_defaults(f=cmd_chercher)
    n = sub.add_parser("noter")
    n.add_argument("pmid")
    n.add_argument("statut", choices=STATUTS)
    n.add_argument("raison")
    n.set_defaults(f=cmd_noter)
    s = sub.add_parser("stats")
    s.add_argument("--ecartes", action="store_true", help="détailler les travaux écartés")
    s.set_defaults(f=cmd_stats)
    a = p.parse_args()
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
