#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation d'index.html avant commit.

Vérifie que les quatre blocs de données sont intacts et cohérents :
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
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "automation"))
from vocabulaire import (ALIAS, CATEGORIES_GLOSSAIRE, CONSENSUS,  # noqa: E402
                         NIVEAUX, REGISTRES, RELATIONS, SOURCES, STATUTS_ESSAI,
                         THEMES, TYPES_SOURCE, VOCABULAIRE)

CHAMPS = ["titre", "url", "datePublication", "dateAjout", "theme", "sousThemes",
          "typeSource", "niveauPreuve", "consensus", "source", "synthese", "pertinence"]
# `liens` est facultatif : la plupart des entrées se suffisent à elles-mêmes.
CHAMPS_OPT = ["liens"]
# Les énumérations vivent dans automation/vocabulaire.py — un seul point d'évolution.

CHAMPS_RES = ["titre", "url", "type", "langue", "cout", "note"]
TYPES_RES = {"Livre", "Site", "Vidéo", "Formation", "Article"}
LANGUES = {"FR", "EN", "FR/EN"}
COUTS = {"Gratuit", "Payant"}

CHAMPS_GLOSS = ["terme", "libelle", "categorie", "auto", "variantes", "definition"]

CHAMPS_ESSAI = ["titre", "registre", "identifiant", "url", "pays", "theme",
                "statut", "finPrevue", "population", "comparaison",
                "criterePrincipal", "interet"]

MARQUEURS = ["/* VEILLE_DATA_START */", "/* VEILLE_DATA_END */",
             "/* FORMATION_RESSOURCES_START */", "/* FORMATION_RESSOURCES_END */",
             "/* GLOSSAIRE_START */", "/* GLOSSAIRE_END */",
             "/* ESSAIS_START */", "/* ESSAIS_END */"]

# Échéance en deçà de laquelle un essai « à suivre » est considéré périmé :
# un an avant le mois courant.
PERIME = f"{date.today().year - 1:04d}-{date.today().month:02d}"

erreurs = []


def err(msg):
    erreurs.append(msg)


def bornes_tableau(src, nom):
    """Renvoie (début, fin) du littéral tableau affecté à `nom`.

    L'espacement autour du `=` est libre : on repère la déclaration par
    expression régulière plutôt que par chaîne littérale, pour qu'un
    reformatage anodin ne fasse pas échouer la validation.
    """
    m = re.search(rf"const\s+{re.escape(nom)}\s*=\s*\[", src)
    if m is None:
        raise ValueError(f"déclaration de {nom} introuvable")
    depart = m.end() - 1
    profondeur = 0
    for i in range(depart, len(src)):
        if src[i] == "[":
            profondeur += 1
        elif src[i] == "]":
            profondeur -= 1
            if profondeur == 0:
                return depart, i + 1
    raise ValueError(f"fin de tableau introuvable pour {nom}")


def norme(txt):
    return re.sub(r"\s+", " ", str(txt).strip().lower()).rstrip("/")


def valide_veille(entrees):
    vus_url, vus_titre = {}, {}
    for n, e in enumerate(entrees, 1):
        ref = f"veille #{n} ({str(e.get('titre', '?'))[:45]}…)"
        manquants = [c for c in CHAMPS if c not in e]
        superflus = [c for c in e if c not in CHAMPS + CHAMPS_OPT]
        if manquants:
            err(f"{ref} : champs manquants {manquants}")
        if superflus:
            err(f"{ref} : champs inattendus {superflus}")
        if e.get("theme") not in THEMES:
            err(f"{ref} : theme invalide {e.get('theme')!r}")
        if e.get("typeSource") not in TYPES_SOURCE:
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


def valide_liens_corpus(entrees):
    """Relations entre entrées (« nuance », « prolonge », « contredit »).

    Une relation qui pointe vers une entrée absente est pire qu'une absence de
    relation : elle affiche un renvoi mort au milieu d'une synthèse. Le lien se
    pose sur l'entrée la plus récente ; le sens inverse est calculé à
    l'affichage, il ne doit donc pas être saisi deux fois.
    """
    urls = {e.get("url") for e in entrees}
    for n, e in enumerate(entrees, 1):
        liens = e.get("liens")
        if liens is None:
            continue
        ref = f"veille #{n} ({str(e.get('titre', '?'))[:40]}…)"
        if not isinstance(liens, list) or not liens:
            err(f"{ref} : liens doit être une liste non vide, ou être absent")
            continue
        cibles = []
        for l in liens:
            if not isinstance(l, dict) or set(l) != {"url", "relation", "note"}:
                err(f"{ref} : un lien doit avoir exactement url, relation et note")
                continue
            if l["relation"] not in RELATIONS:
                err(f"{ref} : relation invalide {l['relation']!r} "
                    f"(attendu : {', '.join(RELATIONS)})")
            if l["url"] == e.get("url"):
                err(f"{ref} : lien vers l'entrée elle-même")
            elif l["url"] not in urls:
                err(f"{ref} : lien vers une entrée absente du corpus — {l['url']}")
            if not str(l.get("note", "")).strip():
                err(f"{ref} : note de lien vide — dire ce que la relation apporte")
            cibles.append(l["url"])
        if len(set(cibles)) != len(cibles):
            err(f"{ref} : deux liens vers la même entrée")


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


def valide_glossaire(entrees):
    """Un terme = une définition, et une graphie = un seul terme.

    La seconde règle est ce qui empêche l'annotation automatique des synthèses
    de devenir ambiguë : si deux entrées revendiquaient la graphie « DBT »,
    le repérage en choisirait une au hasard.
    """
    vus_terme, vus_graphie = {}, {}
    for n, g in enumerate(entrees, 1):
        ref = f"glossaire #{n} ({str(g.get('terme', '?'))[:35]}…)"
        manquants = [c for c in CHAMPS_GLOSS if c not in g]
        superflus = [c for c in g if c not in CHAMPS_GLOSS]
        if manquants:
            err(f"{ref} : champs manquants {manquants}")
        if superflus:
            err(f"{ref} : champs inattendus {superflus}")
        if g.get("categorie") not in CATEGORIES_GLOSSAIRE:
            err(f"{ref} : categorie invalide {g.get('categorie')!r} "
                f"(ajouter à automation/vocabulaire.py si légitime)")
        if not isinstance(g.get("auto"), bool):
            err(f"{ref} : auto doit être un booléen, reçu {g.get('auto')!r}")
        if not isinstance(g.get("variantes"), list):
            err(f"{ref} : variantes doit être une liste (vide si aucune)")
        for cle in ("terme", "libelle", "definition"):
            if not str(g.get(cle, "")).strip():
                err(f"{ref} : {cle} vide")
        t = norme(g.get("terme", ""))
        if t in vus_terme:
            err(f"{ref} : terme en double avec l'entrée #{vus_terme[t]}")
        else:
            vus_terme[t] = n
        if g.get("auto"):
            for graphie in [g.get("terme", "")] + list(g.get("variantes") or []):
                if graphie in vus_graphie:
                    err(f"{ref} : graphie {graphie!r} déjà revendiquée par "
                        f"l'entrée #{vus_graphie[graphie]} — le repérage serait ambigu")
                else:
                    vus_graphie[graphie] = n


def valide_essais(entrees, urls_veille):
    """Essais enregistrés non publiés.

    Deux contrôles propres à ce bloc : l'échéance annoncée doit rester dans le
    futur proche (un essai dont les résultats étaient attendus il y a plus d'un
    an est soit publié, soit abandonné — dans les deux cas il n'a plus sa place
    ici), et l'essai ne doit pas déjà figurer dans la veille.
    """
    vus = {}
    for n, e in enumerate(entrees, 1):
        ref = f"essai #{n} ({str(e.get('identifiant', '?'))})"
        manquants = [c for c in CHAMPS_ESSAI if c not in e]
        superflus = [c for c in e if c not in CHAMPS_ESSAI]
        if manquants:
            err(f"{ref} : champs manquants {manquants}")
        if superflus:
            err(f"{ref} : champs inattendus {superflus}")
        if e.get("registre") not in REGISTRES:
            err(f"{ref} : registre invalide {e.get('registre')!r}")
        if e.get("statut") not in STATUTS_ESSAI:
            err(f"{ref} : statut invalide {e.get('statut')!r}")
        if e.get("theme") not in THEMES:
            err(f"{ref} : theme invalide {e.get('theme')!r}")
        if not re.fullmatch(r"\d{4}-\d{2}", str(e.get("finPrevue", ""))):
            err(f"{ref} : finPrevue doit être AAAA-MM, reçu {e.get('finPrevue')!r}")
        elif e["finPrevue"] < PERIME:
            err(f"{ref} : résultats attendus en {e['finPrevue']}, dépassé depuis plus "
                f"d'un an — publier l'entrée dans la veille ou la retirer")
        if not str(e.get("url", "")).startswith("https://"):
            err(f"{ref} : url non https {e.get('url')!r}")
        ident = str(e.get("identifiant", "")).strip()
        if ident in vus:
            err(f"{ref} : identifiant en double avec l'essai #{vus[ident]}")
        else:
            vus[ident] = n
        if norme(e.get("url", "")) in urls_veille:
            err(f"{ref} : cet essai figure déjà dans la veille — le retirer d'ici")


def valide_renvois(src, urls_veille):
    """Les onglets Traitements renvoient à la veille par l'URL (champ `src`).

    Rien n'empêchait jusqu'ici qu'une entrée soit reformulée ou archivée en
    laissant derrière elle un renvoi vers le vide : le lien tombait sans bruit.
    """
    for nom in ("SYNTHESE_TROUBLES", "PHARMA_REF", "PHARMA_HORS_AMM"):
        m = re.search(rf"const {nom} = \[(.*?)\n\];", src, re.S)
        if m is None:
            err(f"{nom} introuvable — les renvois des traitements ne peuvent être vérifiés")
            continue
        for u in re.findall(r'src:\s*"([^"]+)"', m.group(1)):
            if norme(u) not in urls_veille:
                err(f"{nom} : renvoi vers une entrée absente de la veille — {u}")


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
        vs, ve = bornes_tableau(src, "VEILLE_DATA")
        veille = json.loads(src[vs:ve])
    except (ValueError, json.JSONDecodeError) as exc:
        err(f"VEILLE_DATA illisible : {exc}")
        rapport(cible)
        return 1
    try:
        rs, re_ = bornes_tableau(src, "RESSOURCES")
        ressources = json.loads(src[rs:re_])
    except (ValueError, json.JSONDecodeError) as exc:
        err(f"RESSOURCES illisible : {exc}")
        rapport(cible)
        return 1
    try:
        gs, ge = bornes_tableau(src, "GLOSSAIRE")
        glossaire = json.loads(src[gs:ge])
    except (ValueError, json.JSONDecodeError) as exc:
        err(f"GLOSSAIRE illisible : {exc}")
        rapport(cible)
        return 1
    try:
        es, ee = bornes_tableau(src, "ESSAIS_A_SUIVRE")
        essais = json.loads(src[es:ee])
    except (ValueError, json.JSONDecodeError) as exc:
        err(f"ESSAIS_A_SUIVRE illisible : {exc}")
        rapport(cible)
        return 1

    if not (src.index(MARQUEURS[0]) < vs < ve < src.index(MARQUEURS[1])):
        err("VEILLE_DATA déborde de ses marqueurs")
    if not (src.index(MARQUEURS[2]) < rs < re_ < src.index(MARQUEURS[3])):
        err("RESSOURCES déborde de ses marqueurs")
    if not (src.index(MARQUEURS[4]) < gs < ge < src.index(MARQUEURS[5])):
        err("GLOSSAIRE déborde de ses marqueurs")
    if not (src.index(MARQUEURS[6]) < es < ee < src.index(MARQUEURS[7])):
        err("ESSAIS_A_SUIVRE déborde de ses marqueurs")

    valide_veille(veille)
    valide_liens_corpus(veille)
    valide_ressources(ressources)
    valide_glossaire(glossaire)
    urls_veille = {norme(e.get("url", "")) for e in veille}
    valide_essais(essais, urls_veille)
    valide_renvois(src, urls_veille)
    valide_js(src)

    rapport(cible, len(veille), len(ressources), len(glossaire), len(essais))
    return 1 if erreurs else 0


def rapport(cible, n_veille=None, n_res=None, n_gloss=None, n_essais=None):
    print(f"Validation de {cible.name}")
    if n_veille is not None:
        print(f"  {n_veille} entrées de veille · {n_res} ressources · {n_essais} essais "
              f"suivis · {n_gloss} termes au glossaire · {len(VOCABULAIRE)} tags")
    if erreurs:
        print(f"\n❌ {len(erreurs)} erreur(s) :")
        for e in erreurs:
            print(f"  · {e}")
    else:
        print("  ✅ tout est conforme")


if __name__ == "__main__":
    sys.exit(main())
