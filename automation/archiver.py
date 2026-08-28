#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Déplace les entrées anciennes d'index.html vers archive.html.

Pourquoi pas un data.json externe : `fetch()` est bloqué sur `file://` par la
politique d'origine, et la page cesserait de s'ouvrir par simple double-clic —
sa principale qualité. La manœuvre correcte est donc de scinder en deux pages
autonomes, bâties sur le même gabarit.

Garde-fou propre à l'archivage : une entrée encore référencée n'est jamais
déplacée. Elle peut l'être par un lien « nuance / prolonge / contredit » venant
d'une entrée conservée, ou par un renvoi `src` de l'onglet Traitements —
archiver la cible laisserait un renvoi mort, que `validate.py` rejetterait.

Par défaut le script SIMULE. Rien n'est écrit sans `--appliquer`.

Usage :  python3 automation/archiver.py [--mois 24] [--appliquer]
"""
import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
INDEX = RACINE / "index.html"
ARCHIVE = RACINE / "archive.html"
MARQUE = "<!-- LIEN_ARCHIVE -->"


def bornes(src, nom):
    m = re.search(rf"const\s+{re.escape(nom)}\s*=\s*\[", src)
    depart, profondeur = m.end() - 1, 0
    for i in range(depart, len(src)):
        if src[i] == "[":
            profondeur += 1
        elif src[i] == "]":
            profondeur -= 1
            if profondeur == 0:
                return depart, i + 1
    raise ValueError(nom)


def lire(src, nom):
    a, b = bornes(src, nom)
    return json.loads(src[a:b])


def ecrire(src, nom, valeur):
    a, b = bornes(src, nom)
    if not valeur:
        return src[:a] + "[]" + src[b:]
    lignes = ",\n".join("\n".join("  " + l for l in json.dumps(e, ensure_ascii=False, indent=2).split("\n"))
                        for e in valeur)
    return src[:a] + "[\n" + lignes + "\n]" + src[b:]


def seuil_iso(mois):
    a = date.today()
    total = a.year * 12 + (a.month - 1) - mois
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def references(src, conservees):
    """URL qu'on ne peut pas archiver sans casser un renvoi."""
    bloquees = {}
    for e in conservees:
        for l in e.get("liens", []):
            bloquees.setdefault(l["url"], []).append(f"lien depuis « {e['titre'][:52]}… »")
    for nom in ("SYNTHESE_TROUBLES", "PHARMA_REF", "PHARMA_HORS_AMM"):
        m = re.search(rf"const {nom} = \[(.*?)\n\];", src, re.S)
        if m:
            for u in set(re.findall(r'src:\s*"([^"]+)"', m.group(1))):
                bloquees.setdefault(u, []).append(f"renvoi de {nom}")
    return bloquees


def gabarit_archive(src_index, entrees):
    """L'archive est le même fichier, avec les données de veille remplacées."""
    s = src_index
    s = s.replace("<title>Veille &amp; Formation — Pédopsychiatrie, TCD &amp; TCC</title>",
                  "<title>Archive — Veille pédopsychiatrie, TCD &amp; TCC</title>")
    s = s.replace('<p class="eyebrow">Espace clinique personnel</p>',
                  '<p class="eyebrow">Archive · espace clinique personnel</p>')
    s = ecrire(s, "VEILLE_DATA", entrees)
    # L'archive ne duplique aucun référentiel : un essai en cours n'y a pas sa
    # place, et recopier les traitements ou les ressources créerait une seconde
    # version qui divergerait en silence. Leurs renvois pointeraient d'ailleurs
    # vers des entrées restées dans index.html.
    for vide in ("ESSAIS_A_SUIVRE", "SYNTHESE_TROUBLES", "PHARMA_REF",
                 "PHARMA_HORS_AMM", "RESSOURCES", "RESSOURCES_TCC"):
        s = ecrire(s, vide, [])
    # Les onglets correspondants sont masqués en CSS plutôt que retirés du DOM :
    # le JS continue de fonctionner sans traitement particulier.
    s = s.replace("</style>",
                  "  /* Archive : seuls la veille et le glossaire ont un sens ici. */\n"
                  "  #tab-formation, #tab-formation-tcc, #tab-traitements, #tab-essais "
                  "{ display: none; }\n</style>", 1)
    bandeau = ('<div class="warn-banner">Ces entrées sont <strong>archivées</strong> : '
               'leur publication remonte à plus de deux ans et elles ont pu être dépassées '
               'depuis. La veille courante est dans '
               '<a href="index.html">index.html</a>.</div>')
    s = s.replace('<p class="panel-stats" id="veille-stats"></p>',
                  '<p class="panel-stats" id="veille-stats"></p>\n  ' + bandeau, 1)
    return s


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mois", type=int, default=24, help="ancienneté à partir de laquelle archiver")
    p.add_argument("--appliquer", action="store_true", help="écrire réellement les fichiers")
    a = p.parse_args()

    src = INDEX.read_text(encoding="utf-8")
    veille = lire(src, "VEILLE_DATA")
    seuil = seuil_iso(a.mois)
    candidats = [e for e in veille if e["datePublication"][:7] < seuil]
    conservees = [e for e in veille if e["datePublication"][:7] >= seuil]

    print(f"index.html : {len(veille)} entrées, {len(src) // 1024} Ko")
    print(f"Seuil : publication antérieure à {seuil} ({a.mois} mois)")
    print(f"Candidates : {len(candidats)}\n")
    if not candidats:
        print("Rien à archiver. Les seuils de bascule sont 600 Ko ou 300 entrées.")
        return 0

    bloquees = references(src, conservees)
    a_archiver = [e for e in candidats if e["url"] not in bloquees]
    retenues = [e for e in candidats if e["url"] in bloquees]
    for e in retenues:
        print(f"  ⛔ conservée — {e['titre'][:64]}")
        for r in bloquees[e["url"]]:
            print(f"       {r}")
    for e in a_archiver:
        print(f"  → archivée  [{e['datePublication']}] {e['titre'][:66]}")

    if not a_archiver:
        print("\nToutes les candidates sont référencées ailleurs : rien à déplacer.")
        return 0

    if not a.appliquer:
        print(f"\nSIMULATION — {len(a_archiver)} entrée(s) seraient déplacées. "
              f"Relancer avec --appliquer pour écrire.")
        return 0

    deja = lire(ARCHIVE.read_text(encoding="utf-8"), "VEILLE_DATA") if ARCHIVE.exists() else []
    connues = {e["url"] for e in deja}
    fusion = deja + [e for e in a_archiver if e["url"] not in connues]
    fusion.sort(key=lambda e: e["datePublication"], reverse=True)
    ARCHIVE.write_text(gabarit_archive(src, fusion), encoding="utf-8")

    restantes = conservees + retenues
    restantes.sort(key=lambda e: e["dateAjout"], reverse=True)
    neuf = ecrire(src, "VEILLE_DATA", restantes)
    lien = (f'{MARQUE}<p class="panel-stats"><a href="archive.html">'
            f'{len(fusion)} entrées de plus de {a.mois} mois sont archivées →</a></p>')
    if MARQUE in neuf:
        neuf = re.sub(re.escape(MARQUE) + r'<p class="panel-stats">.*?</p>', lien, neuf, count=1)
    else:
        neuf = neuf.replace('<p class="panel-stats" id="veille-stats"></p>',
                            '<p class="panel-stats" id="veille-stats"></p>\n  ' + lien, 1)
    shutil.copy(INDEX, RACINE / "veille-pedopsy-tcd.backup.html")
    INDEX.write_text(neuf, encoding="utf-8")
    print(f"\nindex.html : {len(restantes)} entrées · archive.html : {len(fusion)} entrées")
    print("Vérifier les deux fichiers :")
    print("  python3 automation/validate.py && python3 automation/validate.py archive.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
