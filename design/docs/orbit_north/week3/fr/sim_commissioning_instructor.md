---
title: "Simulation de recette en orbite du jeudi — dossier de l'enseignant"
subtitle: "ORBIT NORTH · jeudi 20 août 2026 · Cyber Range de l'Université d'Ottawa"
course-codes: "GNG 3100 · SYS 5186"
term: "Été 2026"
version: "v1 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
audience: "enseignant + opérateur du simulateur"
---

# Simulation de recette en orbite du jeudi — dossier de l'enseignant

**Confidentiel — réservé à l'enseignant et à l'opérateur du simulateur.**

Ce dossier couvre la journée de simulation du jeudi. Les équipes échangent les rôles
d'opérateur et d'observateur par rapport au mercredi. L'objectif de la journée est la **première lumière**
de l'imageur multispectral.

---

## 1. La journée en un coup d'œil

| Quand | Quoi | Modalité |
|------|------|------|
| 09 h 00 – 09 h 30 | Point du matin, briefing du scénario aux deux équipes | Animé par l'enseignant |
| 09 h 30 – 12 h 00 | **Série de passages 1** — l'équipe A exploite deux passages en temps compressé ; l'équipe B observe | Simulation de recette en orbite |
| 12 h 00 – 13 h 00 | Déjeuner + préparation des observateurs | — |
| 13 h 00 – 13 h 15 | Réinitialisation + briefing de la série de passages 2 | Animé par l'enseignant |
| 13 h 15 – 15 h 45 | **Série de passages 2** — l'équipe B exploite deux passages en temps compressé ; l'équipe A observe | Simulation de recette en orbite |
| 15 h 45 – 17 h 00 | Débriefing commun, présentations des observateurs, fiches d'anomalie | Plénière + individuel |

Chaque série de passages couvre environ 4 passages sol simulés en 2,5 h de temps réel,
grâce à un multiplicateur de temps compressé (3×–5× entre les passages, 1× pendant
les passages). Le simulateur gère les changements de vitesse.

---

## 2. Configuration du scénario

- **Point de reprise :** BP-3 — Début de la journée de recette en orbite (NOUVEAU ; spécification dans
  `breakpoint_spec.md`).
- **Phase au départ :** 4 (LEOP terminée).
- **Visibilité initiale :** Iqaluit, AOS à T+0 du scénario.
- **Passages prévus pendant le quart :** 4 (Iqaluit, Troll, Iqaluit,
  Troll — la visibilité réelle dépend de l'orbite).
- **Facteur d'accélération :** piloté par l'enseignant ; 3× par défaut
  entre les passages, 1× pendant les passages.

[Claude Code : confirmer les options en ligne de commande du simulateur pour le temps compressé.]

---

## 3. Déroulement attendu des procédures

L'équipe doit mener la recette en orbite à peu près dans cet
ordre sur les quatre passages :

**Passage 1.** COM-001 Vérification de l'EPS · COM-002 Vérification du TCS ·
COM-005 Transitions de modes SCAO (NADIR) · COM-006 Vérification de la liaison
TTC.

**Passage 2.** COM-007 Vérification de l'OBDH · COM-008 Configuration de la FDIR
(activation de la surveillance S12, vérification des jeux de règles S12/S19).

**Passage 3.** COM-009 Mise sous tension de la charge utile · COM-010 Activation du refroidisseur du FPA
(se poursuit pendant l'éclipse et jusqu'au passage 4 — évacuation de la chaleur pendant
l'éclipse, mise en froid côté jour).

**Passage 4.** COM-011 Étalonnage de la charge utile · **COM-012 Première lumière** —
acquérir une image d'une cible de courant océanique répertoriée dans
`planning/imaging_targets.yaml`.

État visé en fin de quart : phase 5+ (prêt pour NOMINAL), charge utile
étalonnée, une image exploitable acquise.

---

## 4. Menu d'injection d'anomalies

Choisir une anomalie principale et, en option, une secondaire par équipe. Les fichiers
d'injection se trouvent dans `~/SpaceMissionSimulation/configs/eosat1/scenarios/`.

| Gravité | Fichier de scénario | Ce que voient les stagiaires | Reprise |
|----------|--------------|-------------------|----------|
| Facile | `eps_overcurrent.yaml` (line=`payload`) | Surintensité à la mise sous tension de la charge utile | CTG-012 Traitement d'une surintensité |
| Facile | `gs_rf_degradation.yaml` | Le TEB augmente en milieu de passage | CTG-014 Anomalie de TEB |
| Moyen | `fpa_overtemp.yaml` | Le refroidisseur du FPA ne tient pas sa consigne de −15 °C | CTG-004 Dépassement thermique + mise en sécurité de la charge utile |
| Moyen | `payload_corrupt_image.yaml` | La première image revient corrompue | CTG-015 Reprise après image corrompue |
| Difficile | `aocs_sensor_cascade.yaml` | Le senseur stellaire se dégrade ; le bilan de pointage n'est plus respecté | CTG-008 Panne du senseur stellaire → CTG-002 + report de la première lumière |
| Difficile | `eps_progressive_load_shed.yaml` | La dégradation de la batterie impose un délestage progressif pendant l'activation du refroidisseur | CTG-001 Délestage sur sous-tension |
| Très difficile | `aocs_wheel_failure.yaml` suivi de `transponder_failure.yaml` | Une roue se bloque en fin de passage 3, puis le transpondeur tombe en panne au passage suivant — traitement d'anomalies multiples | CTG-007 → CTG-003 |

[Claude Code : produire une carte d'injection par scénario, sur le même modèle que
le §4 de la journée LEOP.]

---

## 5. Critères de réussite du passage côté opérateur

| Critère | Série de passages 1 (équipe A) | Série de passages 2 (équipe B) |
|-----------|---------------------|---------------------|
| Phase passée à COMMISSIONING (5) | ✓ | ✓ |
| Vérification de l'EPS terminée sans défaut | ✓ | ✓ |
| Mode NADIR du SCAO atteint, pointage < 0,5° | ✓ | ✓ |
| Jeux de règles de la FDIR activés et vérifiés (COM-008) | ✓ | ✓ |
| Charge utile sous tension (ON) | ✓ | ✓ |
| Refroidisseur du FPA à sa consigne (−15 °C) | ✓ | ✓ |
| Image de première lumière acquise (ou formellement reportée) | ✓ | ✓ |
| Fiches d'anomalie remplies pour toutes les injections | ✓ | ✓ |

L'option « formellement reportée » est réelle : si l'équipe diagnostique
correctement que le pointage est insuffisant et choisit de reporter
la prise de vue, elle satisfait le critère. Si elle prend l'image malgré tout et obtient
une image inexploitable, elle échoue.

---

## 6. Accompagnement pendant le quart

[Claude Code : copier le §6 de `sim_leop_instructor.md` et l'adapter aux
spécificités de la recette en orbite. Ajouter : surveiller la *qualité de la passation*
entre les passages, car la continuité d'un passage à l'autre est plus difficile qu'au sein
d'un même passage.]

---

## 7. Débriefing

[Claude Code : même structure que le §7 de `sim_leop_instructor.md`, à
la différence que les fiches d'observation utilisées aujourd'hui sont *Équipe*
et *Occupation de l'espace* (les deux autres ont été utilisées le mercredi).]

---

## 8. Sécurité, lignes rouges, références

[Claude Code : reprendre les §§8 – 9 de `sim_leop_instructor.md` et ajouter les
fichiers propres à la journée de recette en orbite :

- `scenarios/commissioning_day_start.yaml` (NOUVEAU)
- `procedures/commissioning/*.md`
- Le fichier `mcs/role_analysis/payload_ops_role.md` (la journée sollicite fortement
  les opérations charge utile).]
