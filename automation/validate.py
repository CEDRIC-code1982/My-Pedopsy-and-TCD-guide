#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation d'index.html avant commit.

Vérifie que les deux blocs de données sont intacts et cohérents :
structure JSON, champs obligatoires, énumérations, vocabulaire contrôlé
des sousThemes, absence de doublons, et syntaxe du bloc <script>.

Usage :  python3 automation/validate.py [chemin/index.html]
Sortie :  0 = tout est bon, 1 = au moins une erreur (le commit est bloqué).
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "automation"))
from vocabulaire import ALIAS, VOCABULAIRE  # noqa: E402

CHAMPS = ["titre", "url", "datePublication", "dateAjout", "theme", "sousThemes",
          "typeSource", "niveauPreuve", "consensus", "source", "synthese", "pertinence"]
THEMES = {"Pédopsychiatrie", "TCD", "TCD-Adolescents (DBT-A)", "TCC", "Transversal"}
TYPES = {"Méta-analyse", "RCT", "Étude observationnelle", "Recommandation officielle",
         "Revue narrative", "Article de presse spécialisée"}
NIVEAUX = {"Élevé", "Modéré", "Faible", "Avis d'expert"}
CONSENSUS = {"Consensus établi", "Émergent", "Controversé"}
SOURCES = {"PubMed", "HAS", "Cochrane", "NICE", "SFPEADA", "AACAP", "Autre"}

CHAMPS_RES = ["titre", "url", "type", "langue", "cout", "note"]
TYPES_RES = {"Livre", "Site", "Vidéo", "Formation", "Article"}
LANGUES = {"FR", "EN", "FR/EN"}
COUTS = {"Gratuit", "Payant"}

MARQUEURS = ["/* VEILLE_DATA_START */", "/* VEILLE_DATA_END */",
             "/* FORMATION_RESSOURCES_START */", "/* FORMATION_RESSOURCES_END */"]

erreurs = []


def err(msg):
    erreurs.append(msg)


def bornes_tableau(src, declaration):
    """Renvoie (début, fin) du littéral tableau qui suit `declaration`."""
    depart = src.index(declaration) + len(declaration) - 1
    profondeur = 0
    for i in range(depart, len(src)):
        if src[i] == "[":
            profondeur += 1
        elif src[i] == "]":
            profondeur -= 1
            if profondeur == 0:
                return depart, i + 1
    raise ValueError(f"fin de tableau introuvable pour {declaration!r}")


def norme(txt):
    return re.sub(r"\s+", " ", str(txt).strip().lower()).rstrip("/")


def valide_veille(entrees):
    vus_url, vus_titre = {}, {}
    for n, e in enumerate(entrees, 1):
        ref = f"veille #{n} ({str(e.get('titre', '?'))[:45]}…)"
        manquants = [c for c in CHAMPS if c not in e]
        superflus = [c for c in e if c not in CHAMPS]
        if manquants:
            err(f"{ref} : champs manquants {manquants}")
        if superflus:
            err(f"{ref} : champs inattendus {superflus}")
        if e.get("theme") not in THEMES:
            err(f"{ref} : theme invalide {e.get('theme')!r}")
        if e.get("typeSource") not in TYPES:
            err(f"{ref} : typeSource invalide {e.get('typeSource')!r}")
        if e.get("niveauPreuve") not in NIVEAUX:
            err(f"{ref} : niveauPreuve invalide {e.get('niveauPreuve')!r}")
        if e.get("consensus") not in CONSENSUS:
            err(f"{ref} : consensus invalide {e.get('consensus')!r}")
        if e.get("source") not in SOURCES:
            err(f"{ref} : source invalide {e.get('source')!r}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e.get("datePublication", ""))):
            err(f"{ref} : datePublication mal formée {e.get('datePublication')!r}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", str(e.get("dateAjout", ""))):
            err(f"{ref} : dateAjout doit être AAAA-MM-JJTHH:MM, reçu {e.get('dateAjout')!r}")
        if not str(e.get("url", "")).startswith("https://"):
            err(f"{ref} : url non https {e.get('url')!r}")
        st = e.get("sousThemes")
        if not isinstance(st, list) or not st:
            err(f"{ref} : sousThemes doit être une liste non vide")
        else:
            for t in st:
                if t in ALIAS:
                    cible = ALIAS[t]
                    err(f"{ref} : sousTheme obsolète {t!r} → utiliser "
                        f"{cible!r}" if cible else f"{ref} : sousTheme {t!r} à supprimer")
                elif t not in VOCABULAIRE:
                    err(f"{ref} : sousTheme hors vocabulaire {t!r} "
                        f"(ajouter à automation/vocabulaire.py si légitime)")
            if len(set(st)) != len(st):
                err(f"{ref} : sousThemes contient des doublons")
        for cle, registre in (("url", vus_url), ("titre", vus_titre)):
            v = norme(e.get(cle, ""))
            if v in registre:
                err(f"{ref} : {cle} en double avec l'entrée #{registre[v]}")
            else:
                registre[v] = n


def valide_ressources(ressources):
    vus = {}
    for n, r in enumerate(ressources, 1):
        ref = f"ressource #{n} ({str(r.get('titre', '?'))[:45]}…)"
        manquants = [c for c in CHAMPS_RES if c not in r]
        superflus = [c for c in r if c not in CHAMPS_RES]
        if manquants:
            err(f"{ref} : champs manquants {manquants}")
        if superflus:
            err(f"{ref} : champs inattendus {superflus}")
        if r.get("type") not in TYPES_RES:
            err(f"{ref} : type invalide {r.get('type')!r}")
        if r.get("langue") not in LANGUES:
            err(f"{ref} : langue invalide {r.get('langue')!r}")
        if r.get("cout") not in COUTS:
            err(f"{ref} : cout invalide {r.get('cout')!r}")
        v = norme(r.get("url", ""))
        if v in vus:
            err(f"{ref} : url en double avec la ressource #{vus[v]}")
        else:
            vus[v] = n


def valide_js(src):
    if shutil.which("node") is None:
        print("  ⚠️  node absent : contrôle de syntaxe JS ignoré")
        return
    i = src.index("<script>") + len("<script>")
    j = src.rindex("</script>")
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as f:
        f.write(src[i:j])
        tmp = f.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    Path(tmp).unlink(missing_ok=True)
    if r.returncode != 0:
        err(f"bloc <script> invalide :\n{r.stderr.strip()}")


def main():
    cible = Path(sys.argv[1]) if len(sys.argv) > 1 else RACINE / "index.html"
    src = cible.read_text(encoding="utf-8")

    for m in MARQUEURS:
        if src.count(m) != 1:
            err(f"marqueur {m} présent {src.count(m)} fois (attendu : 1)")
    if erreurs:
        rapport(cible)
        return 1

    try:
        vs, ve = bornes_tableau(src, "const VEILLE_DATA = [")
        veille = json.loads(src[vs:ve])
    except (ValueError, json.JSONDecodeError) as exc:
        err(f"VEILLE_DATA illisible : {exc}")
        rapport(cible)
        return 1
    try:
        rs, re_ = bornes_tableau(src, "const RESSOURCES = [")
        ressources = json.loads(src[rs:re_])
    except (ValueError, json.JSONDecodeError) as exc:
        err(f"RESSOURCES illisible : {exc}")
        rapport(cible)
        return 1

    if not (src.index(MARQUEURS[0]) < vs < ve < src.index(MARQUEURS[1])):
        err("VEILLE_DATA déborde de ses marqueurs")
    if not (src.index(MARQUEURS[2]) < rs < re_ < src.index(MARQUEURS[3])):
        err("RESSOURCES déborde de ses marqueurs")

    valide_veille(veille)
    valide_ressources(ressources)
    valide_js(src)

    rapport(cible, len(veille), len(ressources))
    return 1 if erreurs else 0


def rapport(cible, n_veille=None, n_res=None):
    print(f"Validation de {cible.name}")
    if n_veille is not None:
        print(f"  {n_veille} entrées de veille · {n_res} ressources · "
              f"{len(VOCABULAIRE)} tags au vocabulaire")
    if erreurs:
        print(f"\n❌ {len(erreurs)} erreur(s) :")
        for e in erreurs:
            print(f"  · {e}")
    else:
        print("  ✅ tout est conforme")


if __name__ == "__main__":
    sys.exit(main())
