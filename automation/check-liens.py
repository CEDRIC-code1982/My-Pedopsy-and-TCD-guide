#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrôle des liens d'index.html.

Une veille dont les liens tombent perd sa valeur sans prévenir. Ce script
teste chaque URL des quatre blocs de données et classe les réponses.

⚠️ Un 403 n'est PAS un lien mort : Elsevier, ScienceDirect, JAACAP et
plusieurs éditeurs refusent les requêtes automatisées. Seuls les 404 et 410
signalent une cible réellement disparue. Le script sépare donc « cassé »
(à corriger) de « bloqué » (normal, à ignorer).

Le réseau n'étant pas disponible partout, ce contrôle ne fait PAS partie du
hook pre-commit : le lancer périodiquement, à la main.

Usage :  python3 automation/check-liens.py [chemin/index.html] [--tout]
         --tout : affiche aussi les liens valides.
Sortie :  0 = aucun lien cassé, 1 = au moins un 404/410.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) veille-pedopsy-tcd/1.0"
DELAI = 20
BLOQUANT = {401, 403, 429, 418}   # refus d'automate, pas une cible disparue
MORT = {404, 410}


def urls_du_fichier(src):
    """(url, provenance) pour les quatre blocs de données."""
    out = []
    for var, etiquette in (("VEILLE_DATA", "veille"), ("RESSOURCES", "ressource"),
                           ("ESSAIS_A_SUIVRE", "essai")):
        m = re.search(rf"const {var}\s*=\s*(\[.*?\])\s*;\s*\n/\*", src, re.S)
        if m is None:
            print(f"⚠️  {var} introuvable")
            continue
        for e in json.loads(m.group(1)):
            out.append((e["url"], f"{etiquette} · {e['titre'][:58]}"))
    # renvois des onglets Traitements
    for nom in ("SYNTHESE_TROUBLES", "PHARMA_REF", "PHARMA_HORS_AMM"):
        m = re.search(rf"const {nom} = \[(.*?)\n\];", src, re.S)
        if m:
            for u in set(re.findall(r'src:\s*"([^"]+)"', m.group(1))):
                out.append((u, f"renvoi · {nom}"))
    return out


def teste(url):
    """Renvoie (etat, detail). HEAD d'abord, GET en repli : certains serveurs
    ne répondent qu'aux GET, et un 405 sur HEAD ne dit rien de la cible."""
    for methode in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=methode, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=DELAI) as r:
                final = r.geturl()
                # Un DOI redirige TOUJOURS vers l'éditeur : c'est son rôle, pas
                # un déménagement. Ne signaler que les redirections des autres
                # URL, où elles indiquent une page qui a bougé.
                if url.startswith("https://doi.org/") or final.rstrip("/") == url.rstrip("/"):
                    return "ok", r.status
                return "redirige", final
        except urllib.error.HTTPError as e:
            if e.code in MORT:
                return "casse", e.code
            if e.code in BLOQUANT:
                return "bloque", e.code
            if methode == "GET":
                return "erreur", e.code
        except Exception as e:                      # DNS, TLS, délai dépassé
            if methode == "GET":
                return "erreur", type(e).__name__
    return "erreur", "inconnu"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tout = "--tout" in sys.argv
    cible = Path(args[0]) if args else RACINE / "index.html"
    liens = urls_du_fichier(cible.read_text(encoding="utf-8"))
    print(f"Contrôle de {len(liens)} liens dans {cible.name}…\n")

    with ThreadPoolExecutor(max_workers=8) as pool:
        resultats = list(pool.map(lambda l: (l, *teste(l[0])), liens))

    groupes = {}
    for (url, prov), etat, detail in resultats:
        groupes.setdefault(etat, []).append((url, prov, detail))

    for etat, titre in (("casse", "❌ CASSÉS — cible disparue, à corriger"),
                        ("erreur", "⚠️  INJOIGNABLES — à revérifier"),
                        ("redirige", "↪️  REDIRIGÉS — cible atteinte, URL déplacée"),
                        ("bloque", "🔒 BLOQUÉS — refus d'automate, lien probablement valide"),
                        ("ok", "✅ VALIDES")):
        lot = groupes.get(etat, [])
        if not lot:
            continue
        if etat in ("ok", "bloque", "redirige") and not tout:
            print(f"{titre} : {len(lot)}")
            continue
        print(f"\n{titre} ({len(lot)})")
        for url, prov, detail in sorted(lot, key=lambda x: x[1]):
            # Sens explicite : l'URL du fichier d'abord, la cible ensuite.
            fleche = f"\n      → {detail}" if etat == "redirige" else ""
            code = "" if etat == "redirige" else f"[{detail}] "
            print(f"  {code}{url}{fleche}\n      {prov}")

    casses = len(groupes.get("casse", []))
    print(f"\n{casses} lien(s) cassé(s) sur {len(liens)}.")
    return 1 if casses else 0


if __name__ == "__main__":
    sys.exit(main())
