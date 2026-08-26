# Veille & Formation — Pédopsychiatrie, TCD & TCC

Tableau de bord personnel réunissant une **veille scientifique** (pédopsychiatrie,
thérapie comportementale dialectique, TCC) et un **parcours de formation** aux
compétences TCD et TCC, alimenté automatiquement par une routine Claude Code.

## Ouvrir le dashboard

Double-cliquer sur `index.html`. C'est tout : la page est **entièrement autonome**
— aucune dépendance, aucun serveur, aucune étape de build. Elle fonctionne hors
ligne (seules les polices Google sont distantes, avec repli système).

> ⚠️ **Ne pas extraire les données dans un JSON externe.** `fetch()` est bloqué
> sur `file://` par la politique d'origine : la page cesserait de s'ouvrir par
> simple double-clic. Voir « Croissance du fichier » plus bas.

## Contenu

| Onglet | Contenu |
|---|---|
| **Veille** | Entrées bibliographiques filtrables par thème, niveau de preuve et période, avec synthèse factuelle et portée pratique |
| **Formation TCD** | Les 4 modules de compétences, suivi de progression, bibliothèque de ressources |
| **Formation TCC** | Même principe pour les TCC |
| **Traitements** | Synthèse pharmacologique, dont le volet hors AMM |

La progression de formation est stockée dans le `localStorage` du navigateur —
elle est donc **locale à la machine et au navigateur**, et n'est pas versionnée.

Depuis l'onglet Veille, les boutons **Copier (MD)** et **CSV** exportent les
entrées *actuellement filtrées*, pour réutilisation en bibliographie.

La puce **Expérimental** isole la veille exploratoire : essais de phase précoce,
preuves de concept, études pilotes. Ces entrées ne portent volontairement aucune
implication de pratique — elles servent à voir venir une évolution avant qu'elle
n'arrive en consultation.

## Structure du dépôt

```
index.html                        le dashboard complet (HTML + CSS + JS + données)
automation/
  pedopsy-tcd.SKILL.md            la routine de veille (voir ci-dessous)
  vocabulaire.py                  listes contrôlées : tags, thèmes, sources, types
  validate.py                     validation d'index.html avant commit
.githooks/pre-commit              rejoue validate.py, bloque un commit invalide
```

Deux blocs de `index.html` seulement sont éditables par la routine, délimités par
des marqueurs : `VEILLE_DATA` (les entrées) et `RESSOURCES` (la bibliothèque de
formation). Tout le reste — HTML, CSS, JS, curriculum des modules — est stable.

## La routine de veille

`automation/pedopsy-tcd.SKILL.md` est la définition complète de la tâche
planifiée : sources à interroger, critères de sélection, format des entrées,
règles de rédaction, procédure de commit.

**Ce fichier est la source de vérité et vit dans le dépôt.**
`~/.claude/scheduled-tasks/pedopsy-tcd/SKILL.md` n'est qu'un lien symbolique
pointant vers lui. Si le lien est perdu (nouvelle machine, réinstallation) :

```bash
ln -sfn "$PWD/automation/pedopsy-tcd.SKILL.md" ~/.claude/scheduled-tasks/pedopsy-tcd/SKILL.md
```

## Validation

Après toute modification manuelle d'`index.html` :

```bash
python3 automation/validate.py
```

Le script contrôle les marqueurs, le reparse JSON des deux blocs, les champs et
énumérations, le format des dates, la conformité des `sousThemes` au vocabulaire
contrôlé, l'absence de doublons d'URL ou de titre, et la syntaxe du bloc
`<script>`. Un JSON cassé rend la page blanche : c'est la panne que ce garde-fou
existe pour empêcher.

Le hook `pre-commit` le rejoue automatiquement. Il est versionné dans
`.githooks/`, donc à réactiver après un clone frais :

```bash
git config core.hooksPath .githooks
```

## Champ `source` : aucun fourre-tout

`source` désigne **qui produit** la référence, pas qui héberge le lien : un
article indexé dans PubMed prend `PubMed` même si l'url est un DOI Elsevier.
Il n'existe volontairement **pas** de valeur « Autre » — un fourre-tout n'informe
de rien. La liste autorisée est `SOURCES` dans `automation/vocabulaire.py` ; une
source légitime absente s'y ajoute, dans le même commit que l'entrée.

## Faire évoluer le vocabulaire des tags

Les `sousThemes` suivent un vocabulaire contrôlé (`automation/vocabulaire.py`)
pour éviter la dérive taxonomique — sans lui, les libellés se dupliquent en
variantes (« Auto-mutilation » / « Automutilation ») et les tags cessent de
servir à naviguer. Pour ajouter un tag : l'inscrire dans `VOCABULAIRE`, ajouter
les anciens libellés qu'il remplace dans `ALIAS`, puis relancer `validate.py`.

## Croissance du fichier

`index.html` gagne environ 170 lignes par exécution de la routine. Quand il
dépassera ~600 Ko ou ~300 entrées, déplacer les entrées de plus de 24 mois vers
un `archive.html` autonome bâti sur le même gabarit, plutôt que de découper les
données en fichiers externes.

## Convention git

Commits directs sur `main`, messages en français. `veille-pedopsy-tcd.backup.html`
est une sauvegarde locale à usage unique, ignorée par git — l'historique du dépôt
reste la vraie sauvegarde.
