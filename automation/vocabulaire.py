# -*- coding: utf-8 -*-
"""Vocabulaire contrôlé des `sousThemes` de la veille.

VOCABULAIRE : les seuls libellés autorisés dans le champ `sousThemes`.
ALIAS       : anciens libellés (ou variantes) → libellé canonique.
              La valeur None signifie « tag sans valeur informative, à supprimer ».

Toute évolution du vocabulaire se fait ICI, puis `python3 automation/validate.py`.
"""

VOCABULAIRE = [
    # — Troubles et tableaux cliniques —
    "TDAH", "TSA", "Neurodéveloppement", "Dépression", "Dépression résistante",
    "Anxiété", "TOC", "TSPT", "Trouble bipolaire", "Trouble borderline",
    "Schizophrénie et psychoses", "Catatonie", "Troubles des conduites alimentaires",
    "Trouble des conduites", "Addictions", "Auto-mutilation", "Suicidalité",
    "Dysrégulation émotionnelle", "Sommeil", "Comorbidités",
    # — Pharmacologie —
    "Pharmacothérapie", "Psychostimulants", "Non-stimulants", "Antidépresseurs",
    "Antipsychotiques", "Thymorégulateurs", "Lithium", "Kétamine et eskétamine",
    "Nouvelles molécules", "Posologie", "Potentialisation", "Usage hors AMM",
    "Effets indésirables", "Pharmacovigilance", "Déprescription",
    "Suivi thérapeutique pharmacologique", "Pratiques de prescription",
    # — Psychothérapies —
    "Entraînement aux compétences TCD", "DBT-A", "Fidélité au modèle",
    "Formation des thérapeutes", "TCC", "STEPPS", "EMDR", "Thérapie familiale",
    "Implication parentale", "Interventions psychosociales", "Neuromodulation",
    "Remédiation cognitive", "Adaptation de l'intervention",
    # — Numérique et organisation des soins —
    "Interventions numériques", "Téléconsultation", "Usage des écrans",
    "Parcours de soins", "Accès aux soins", "Psychiatrie de transition",
    "Urgences et crise", "Hospitalisation", "Protection de l'enfance",
    "Implémentation", "Assiduité et engagement", "Politique de santé",
    # — Diagnostic, épidémiologie, méthodologie —
    "Épidémiologie", "Dépistage et repérage", "Prévention", "Intervention précoce",
    "Suivi à long terme", "Génétique", "Neuro-imagerie", "Fonctions exécutives",
    "Fonctionnement global", "Mortalité", "Genre", "Coût-efficacité",
    "Médecine de précision", "Qualité des preuves", "Évaluation écologique momentanée",
]

ALIAS = {
    # Troubles
    "Troubles anxieux": "Anxiété", "Anxiété sociale": "Anxiété", "TAG": "Anxiété",
    "Manie aiguë": "Trouble bipolaire", "Manie bipolaire": "Trouble bipolaire",
    "Trouble borderline (adulte)": "Trouble borderline",
    "Schizophrénie de l'adolescent": "Schizophrénie et psychoses",
    "Schizophrénie précoce": "Schizophrénie et psychoses",
    "Troubles alimentaires": "Troubles des conduites alimentaires",
    "Anorexie mentale": "Troubles des conduites alimentaires",
    "ARFID": "Troubles des conduites alimentaires",
    "Troubles externalisés": "Trouble des conduites",
    "Usage de substances": "Addictions",
    "Automutilation": "Auto-mutilation",
    "Automutilation non suicidaire": "Auto-mutilation",
    "Prévention du suicide": "Suicidalité", "Plan de sécurité": "Suicidalité",
    "Régulation émotionnelle": "Dysrégulation émotionnelle",
    "Compétences de régulation émotionnelle": "Dysrégulation émotionnelle",
    "Régulation de la colère": "Dysrégulation émotionnelle",
    "Irritabilité": "Dysrégulation émotionnelle",
    "TSAF": "Neurodéveloppement", "Déficience intellectuelle": "Neurodéveloppement",
    "Transdiagnostique": "Comorbidités", "Groupe transdiagnostique": "Comorbidités",
    "Résistance au traitement": "Dépression résistante",
    # Pharmacologie
    "Pharmacologie": "Pharmacothérapie", "Psychopharmacologie": "Pharmacothérapie",
    "Choix du traitement": "Pharmacothérapie",
    "Méthylphénidate": "Psychostimulants", "Atomoxétine": "Non-stimulants",
    "Fluoxétine": "Antidépresseurs", "Quétiapine": "Antipsychotiques",
    "Kétamine": "Kétamine et eskétamine", "Eskétamine": "Kétamine et eskétamine",
    "Posologies": "Posologie", "Pharmacocinétique": "Posologie",
    "Voie transdermique": "Posologie",
    "Pharmacothérapie hors AMM": "Usage hors AMM",
    "Statut réglementaire": "Usage hors AMM",
    "Surveillance des effets indésirables": "Effets indésirables",
    "Tolérance": "Effets indésirables", "Hyperprolactinémie": "Effets indésirables",
    "Surveillance métabolique": "Effets indésirables", "Croissance": "Effets indésirables",
    "Sevrage": "Déprescription", "Bon usage du médicament": "Déprescription",
    # Psychothérapies
    "Compétences TCD": "Entraînement aux compétences TCD",
    "Entraînement aux compétences": "Entraînement aux compétences TCD",
    "TCC centrée sur le trauma": "TCC", "Activation comportementale": "TCC",
    "Thérapie d'exposition": "TCC", "Thérapie métacognitive": "TCC",
    "Guidance parentale": "Implication parentale", "Parentalité": "Implication parentale",
    "Comparaison de thérapies": "Interventions psychosociales",
    "Efficacité comparée": "Interventions psychosociales",
    "TMS": "Neuromodulation", "Neurofeedback": "Neuromodulation",
    "Accessibilité des outils": "Adaptation de l'intervention",
    # Numérique et organisation
    "Thérapeutiques numériques": "Interventions numériques",
    "Santé numérique": "Interventions numériques",
    "TCC par internet": "Interventions numériques", "iCBT": "Interventions numériques",
    "Télésanté": "Téléconsultation",
    "Continuité des soins": "Parcours de soins", "Coordination des soins": "Parcours de soins",
    "Organisation des soins": "Parcours de soins",
    "Planification des besoins": "Accès aux soins",
    "Transition 15-25": "Psychiatrie de transition",
    "Urgences pédiatriques": "Urgences et crise", "Recours aux urgences": "Urgences et crise",
    "Recours aux services de crise": "Urgences et crise",
    "Hospitalisation résidentielle": "Hospitalisation", "Hôpital de jour": "Hospitalisation",
    "Implémentation clinique": "Implémentation", "Multi-cadres cliniques": "Implémentation",
    "Format de délivrance": "Implémentation", "Format court": "Implémentation",
    "Assiduité": "Assiduité et engagement", "Persistance": "Assiduité et engagement",
    "Faisabilité": "Assiduité et engagement",
    "Santé publique": "Politique de santé", "Recommandation européenne": "Politique de santé",
    # Diagnostic, épidémiologie, méthodologie
    "Prévention scolaire": "Prévention",
    "Dépistage scolaire": "Dépistage et repérage",
    "Repérage chez les filles": "Dépistage et repérage",
    "Diagnostic tardif": "Dépistage et repérage",
    "Intervention comportementale intensive précoce": "Intervention précoce",
    "ABA": "Intervention précoce", "Nourrisson": "Intervention précoce",
    "Trajectoires développementales": "Suivi à long terme",
    "Bien-être": "Fonctionnement global",
    "Aide à la décision partagée": "Médecine de précision",
    "Biais méthodologiques": "Qualité des preuves", "Niveau de preuve": "Qualité des preuves",
    "Méthodologie de revue": "Qualité des preuves", "Revue systématique": "Qualité des preuves",
    # Sans valeur informative (le champ `theme` porte déjà l'information)
    "Adolescents": None, "Enfant/Adolescent": None,
}

# ---------------------------------------------------------------------------
# Registres et organismes autorisés dans le champ `source`.
# Le champ désigne QUI PRODUIT la référence, pas qui héberge le lien : un
# article indexé dans PubMed prend "PubMed" même si l'url est un DOI Elsevier.
# Il n'existe volontairement PAS de valeur « Autre » — un fourre-tout n'informe
# de rien. Une source légitime absente de la liste s'ajoute ici, dans le même
# commit que l'entrée qui l'introduit.
# ---------------------------------------------------------------------------
SOURCES = [
    "PubMed", "Cochrane",                       # registres bibliographiques
    "HAS", "ANSM", "DREES", "Santé publique France", "SFPEADA",
    "Académie de médecine",                     # France
    "NICE", "AACAP", "ESCAP", "OMS",            # international
]

# ---------------------------------------------------------------------------
# Nature de la source. « Étude expérimentale » couvre la recherche en amont de
# la pratique : essais de phase précoce, preuves de concept, études pilotes,
# protocoles innovants, travaux translationnels à visée clinique. Elle est
# volontairement distincte de « RCT » : on la veille pour anticiper, pas pour
# prescrire. Le niveau de preuve associé est presque toujours Faible.
# ---------------------------------------------------------------------------
TYPES_SOURCE = [
    "Méta-analyse", "RCT", "Étude observationnelle", "Étude expérimentale",
    "Recommandation officielle", "Revue narrative", "Article de presse spécialisée",
]

# ---------------------------------------------------------------------------
# Relations entre entrées de veille (champ optionnel `liens`).
# Le lien se pose sur l'entrée la PLUS RÉCENTE, qui commente l'antérieure ;
# le sens inverse est calculé et affiché automatiquement (rétrolien).
# ---------------------------------------------------------------------------
RELATIONS = {
    "prolonge": "prolongé par",     # même question, résultats convergents ou suite
    "nuance": "nuancé par",         # tempère ou restreint la portée
    "contredit": "contredit par",   # résultat opposé
}

# ---------------------------------------------------------------------------
# Registres d'essais cliniques et statuts d'avancement, pour le bloc
# ESSAIS_A_SUIVRE. Un essai enregistré n'a pas de niveau de preuve : il n'en
# porte donc aucun. Dès qu'il est publié, il quitte ce bloc pour VEILLE_DATA.
# ---------------------------------------------------------------------------
REGISTRES = [
    "ClinicalTrials.gov", "ISRCTN", "EU CTR", "ANZCTR", "ChiCTR",
    "IRCT", "CTRI", "jRCT", "ICTRP (OMS)",
]

STATUTS_ESSAI = [
    "Recrutement à venir", "Recrutement en cours",
    "En cours, recrutement clos", "Terminé, résultats non publiés",
]

# ---------------------------------------------------------------------------
# Catégories du glossaire. Elles structurent l'onglet dédié : en ajouter une
# crée une section, donc ne le faire que pour un ensemble de termes cohérent.
# ---------------------------------------------------------------------------
CATEGORIES_GLOSSAIRE = [
    "Réglementation et institutions", "Troubles et diagnostics", "Psychothérapies",
    "Pharmacologie", "Méthodologie", "Statistiques", "Échelles et mesures",
]

THEMES = ["Pédopsychiatrie", "TCD", "TCD-Adolescents (DBT-A)", "TCC", "Transversal"]
NIVEAUX = ["Élevé", "Modéré", "Faible", "Avis d'expert"]
CONSENSUS = ["Consensus établi", "Émergent", "Controversé"]
