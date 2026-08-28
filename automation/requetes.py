# -*- coding: utf-8 -*-
"""Équations PubMed canoniques de la veille.

Pourquoi les figer ici : tant que les requêtes étaient réinventées à chaque
run, le même travail ressortait plusieurs fois et des pans entiers de la
littérature n'étaient jamais interrogés. Une équation versionnée se corrige,
se compare d'un run à l'autre et rend le corpus reproductible.

⚠️ Le filtre de date est ajouté par `recherche.py` sur le champ **EDAT**
(date d'entrée dans PubMed) et non PDAT (date de publication) : c'est l'entrée
dans la base qui dit ce qui est nouveau pour nous. Un article publié en
janvier mais indexé en août est une nouveauté ; l'inverse n'existe pas.

Aucune restriction de langue, volontairement : la veille se veut mondiale.
"""

PSY = ('(psychiatr*[tiab] OR "mental health"[tiab] OR depress*[tiab] OR anxiety[tiab] '
       'OR bipolar[tiab] OR mania[tiab] OR manic[tiab] OR psychosis[tiab] OR psychotic[tiab] '
       'OR schizophren*[tiab] OR ADHD[tiab] OR autis*[tiab] OR suicid*[tiab] '
       'OR "self-harm"[tiab] OR irritability[tiab] OR aggress*[tiab] OR borderline[tiab])')

ENFANT = ('(child*[tiab] OR adolescen*[tiab] OR paediatric[tiab] OR pediatric[tiab] '
          'OR youth[tiab] OR teen*[tiab] OR "young people"[tiab])')

AXES = [
    {
        "nom": "tcd",
        "description": "TCD / DBT, toutes populations et tous formats",
        "theme": "TCD",
        "requete": '("dialectical behavior therapy"[tiab] OR "dialectical behaviour therapy"[tiab] '
                   'OR "dialectical behavioral therapy"[tiab] OR "DBT skills"[tiab] '
                   'OR "radically open dialectical"[tiab])',
    },
    {
        "nom": "tcd-ado",
        "description": "TCD chez l'enfant et l'adolescent (DBT-A)",
        "theme": "TCD-Adolescents (DBT-A)",
        "requete": '("dialectical behavior therapy"[tiab] OR "dialectical behaviour therapy"[tiab] '
                   'OR "dialectical behavioral therapy"[tiab] OR "DBT-A"[tiab]) AND ' + ENFANT,
    },
    {
        "nom": "borderline-jeune",
        "description": "Trouble borderline et dysrégulation émotionnelle du jeune",
        "theme": "TCD",
        "requete": '("borderline personality"[tiab] OR "emotion dysregulation"[ti] '
                   'OR "emotional dysregulation"[ti]) AND ' + ENFANT
                   + ' AND (treatment*[tiab] OR therap*[tiab] OR intervention*[tiab] '
                     'OR trial[tiab] OR diagnos*[tiab] OR prognos*[tiab])',
    },
    {
        "nom": "autoagression",
        "description": "Automutilation, suicidalité et interventions de crise",
        "theme": "Pédopsychiatrie",
        "requete": '("self-harm"[tiab] OR "self harm"[tiab] OR "self-injury"[tiab] '
                   'OR "suicidal ideation"[tiab] OR "suicide attempt*"[tiab] OR NSSI[tiab]) AND '
                   + ENFANT + ' AND (trial[tiab] OR intervention*[tiab] OR meta-analysis[pt] '
                   'OR systematic review[pt] OR randomized controlled trial[pt])',
    },
    {
        "nom": "pharmaco-tdah",
        "description": "Traitements médicamenteux du TDAH",
        "theme": "Pédopsychiatrie",
        "requete": '(ADHD[tiab] OR "attention deficit"[tiab]) AND (methylphenidate[tiab] '
                   'OR amphetamine*[tiab] OR lisdexamfetamine[tiab] OR atomoxetine[tiab] '
                   'OR guanfacine[tiab] OR clonidine[tiab] OR viloxazine[tiab] '
                   'OR centanafadine[tiab] OR stimulant*[tiab]) AND ' + ENFANT,
    },
    {
        "nom": "pharmaco-humeur",
        "description": "Thymorégulateurs et antipsychotiques (lithium inclus)",
        "theme": "Pédopsychiatrie",
        "requete": '(lithium[tiab] OR valproate[tiab] OR lamotrigine[tiab] OR "mood stabili*"[tiab] '
                   'OR antipsychotic*[tiab] OR risperidone[tiab] OR aripiprazole[tiab] '
                   'OR olanzapine[tiab] OR quetiapine[tiab] OR lurasidone[tiab] '
                   'OR cariprazine[tiab] OR clozapine[tiab]) AND ' + ENFANT + ' AND ' + PSY,
    },
    {
        "nom": "pharmaco-depression",
        "description": "Antidépresseurs, kétamine et dépression résistante",
        "theme": "Pédopsychiatrie",
        "requete": '(antidepressant*[tiab] OR SSRI*[tiab] OR fluoxetine[tiab] OR sertraline[tiab] '
                   'OR escitalopram[tiab] OR ketamine[tiab] OR esketamine[tiab] '
                   'OR "treatment-resistant depression"[tiab]) AND ' + ENFANT + ' AND ' + PSY,
    },
    {
        "nom": "neurodev",
        "description": "TSA et troubles du neurodéveloppement",
        "theme": "Pédopsychiatrie",
        "requete": '("autism spectrum"[tiab] OR "autistic"[tiab] OR "neurodevelopmental disorder*"[tiab]) '
                   'AND ' + ENFANT + ' AND (randomized controlled trial[pt] OR meta-analysis[pt] '
                   'OR systematic review[pt] OR guideline[pt])',
    },
    {
        "nom": "tcc-enfant",
        "description": "TCC et psychothérapies de l'enfant et de l'adolescent",
        "theme": "TCC",
        "requete": '("cognitive behavio*therapy"[tiab] OR "cognitive-behavio*"[tiab] OR CBT[tiab]) '
                   'AND ' + ENFANT + ' AND (meta-analysis[pt] OR systematic review[pt] '
                   'OR randomized controlled trial[pt])',
    },
    {
        "nom": "recommandations",
        "description": "Recommandations, consensus et documents de cadrage",
        "theme": "Pédopsychiatrie",
        "requete": '(guideline[pt] OR practice guideline[pt] OR "clinical practice guideline"[ti] '
                   'OR "consensus statement"[ti] OR "position statement"[ti] OR "expert consensus"[ti]) '
                   'AND ' + ENFANT + ' AND (psychiatr*[tiab] OR "mental health"[tiab] '
                   'OR depress*[tiab] OR anxiety[tiab] OR ADHD[tiab] OR autism[tiab] '
                   'OR suicid*[tiab] OR self-harm[tiab])',
    },
    {
        # Ajouté après un contrôle de rappel : le consensus Delphi sur la
        # catatonie pédiatrique n'était capté par AUCUN axe. Toute la
        # psychiatrie aiguë et de liaison était un angle mort.
        "nom": "urgences-liaison",
        "description": "Psychiatrie aiguë et de liaison : catatonie, agitation, crise",
        "theme": "Pédopsychiatrie",
        "requete": '(catatoni*[tiab] OR "psychiatric emergency"[tiab] OR "acute agitation"[tiab] '
                   'OR "consultation-liaison"[tiab] OR "autoimmune encephalitis"[tiab] '
                   'OR "emergency department"[tiab] OR "inpatient psychiatric"[tiab] '
                   'OR restraint*[tiab] OR seclusion[tiab]) AND ' + ENFANT + ' AND ' + PSY,
    },
    {
        "nom": "experimental",
        "description": "Travaux de phase précoce, pilotes et translationnels",
        "theme": "Pédopsychiatrie",
        "requete": '("pilot study"[tiab] OR "proof of concept"[tiab] OR feasibility[ti] '
                   'OR "phase 1"[tiab] OR "phase 2"[tiab] OR "first-in-human"[tiab] '
                   'OR biomarker*[ti]) AND ' + ENFANT + ' AND (psychiatr*[ti] '
                   'OR depress*[ti] OR anxiety[ti] OR ADHD[ti] OR autis*[ti] '
                   'OR suicid*[ti] OR "self-harm"[ti] OR bipolar[ti] OR psychosis[ti])',
    },
]

PAR_NOM = {a["nom"]: a for a in AXES}
