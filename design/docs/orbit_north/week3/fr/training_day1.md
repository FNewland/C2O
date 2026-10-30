---
title: "Semaine 3 — journée de formation 1 : élaboration du concept d'opérations"
subtitle: "ORBIT NORTH · lundi 17 août 2026 · Cyber Range de l'Université d'Ottawa"
course-codes: "GNG 3100 · SYS 5186"
term: "Été 2026"
version: "v1 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
audience: "étudiantes et étudiants + enseignant"
expected-reading: "Synthèse de la mission EOSAT-1 (section 2 du présent document) avant le jour 1 ; la Référence MCS et MPS pour les étudiants (document séparé) avant le jour 2"
---

# Journée de formation 1 — élaboration du concept d'opérations

**La journée en un coup d'œil**

| Quand | Quoi | Production |
|------|------|--------|
| 09 h 00 – 10 h 30 | Briefing : éléments du segment sol ; rappel du ConOps ; présentation des outils | Questions-réponses consignées |
| 10 h 30 – 12 h 00 | Prise en main du système de planification de mission (MPS) | Premier plan exporté |
| 13 h 00 – 15 h 00 | Tour de rôle sur le MCS : chaque étudiant passe par six postes | Tour des postes effectué |
| 15 h 00 – 16 h 30 | Exercice d'équipe de plan de passage sur le MPS | Plan de passage rédigé par l'équipe |
| 16 h 30 – 17 h 00 | Débriefing et briefing du jour 2 ; **rappel des lectures attendues** | Prêts pour le jour 2 |

**Cadre :** Cyber Range de l'Université d'Ottawa, salle des consoles. Le simulateur exécute le
point de reprise **Nominal après recette en orbite** (BP-1 dans la spécification des points
d'arrêt) — le satellite est en bonne santé et en opérations de routine, de sorte que l'équipe
peut se concentrer sur les outils plutôt que sur la reprise.

---

## 1. Briefing — ce que nous exploitons

[Claude Code : développer jusqu'à environ 400 mots. Présenter la mission EOSAT-1 : CubeSat
6U, surveillance des courants océaniques par imageur multispectral (443,
560, 665, 865 nm), orbite héliosynchrone de 450 km à 98° d'inclinaison.
Stations sol d'Iqaluit et de Troll, toutes deux polaires en bande S. S'appuyer sur
`~/SpaceMissionSimulation/configs/eosat1/mission.yaml` et
`orbit.yaml` pour les valeurs de référence.]

### 1.1 Les quatre éléments du segment sol

[Claude Code : 200 mots. Reprendre la structure du *Mission Operations
Handbook* de la NASA : stations sol · bande de base · MCS · dynamique
du vol. Spécificités d'EOSAT-1 : Iqaluit (63,7° N), Troll (72° S),
bande S, élévation minimale de 5°.]

### 1.2 Géométrie des passages — le cas polaire en bande S

[Claude Code : 200 mots et un schéma. Montrer pourquoi une SSO polaire associée à des
stations sol polaires donne de nombreux passages courts par jour. Inclure un
schéma généré en Python (style de `outputs/sample_figures/uottawa_brand.py`)
montrant une orbite avec ses traces au sol, les cônes de visibilité d'Iqaluit et de Troll,
et les repères AOS/TCA/LOS.]

### 1.3 Structure d'une procédure

[Claude Code : 150 mots. Présenter une procédure du
simulateur (de préférence `procedures/leop/first_acquisition.md`, car
c'est la plus simple des procédures LEOP). Mettre en évidence : bloc des préconditions,
colonne des responsables, vérification, critères de sortie. Dire aux étudiants qu'ils
liront des procédures, sans les écrire.]

### 1.4 Introduction aux services PUS (allégée)

[Claude Code : 150 mots. Présenter uniquement les services 1, 3, 5, 8, 9, 11,
17 par leur nom et leur signification en une ligne. Source : `mcs/pus_services.yaml`.
Souligner que les étudiants utilisent l'interface du MCS ; la connaissance du PUS ne sert
qu'à donner du contexte.]

---

## 2. Synthèse de la mission EOSAT-1 (lecture attendue avant le jour 1)

> **À lire avant le jour 1.** Temps de lecture estimé : 25 minutes.

[Claude Code : produire une synthèse lisible de 600 – 900 mots couvrant :
plateforme du satellite (plateforme 6U, imageur multispectral, bande S), justification du
choix d'orbite (héliosynchrone à 450 km, pourquoi), objectif scientifique de la charge utile
(surveillance des courants océaniques, pourquoi ces 4 bandes), segment sol, synthèse du
concept d'opérations. Inclure des schémas : orbite + traces au sol + visibilité des stations
sol (figure Python) ; schéma fonctionnel du satellite avec code couleur des
six postes du MCS ; graphique de la cadence des passages.]

### Références clés

- Configuration de la mission EOSAT-1 : `configs/eosat1/mission.yaml`
- ECSS-E-ST-70-11C — *Space segment operability* —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/
- NASA *Space Flight Program and Project Management Requirements* (NPR 7120.5F) —
  https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_
- CCSDS *Mission Operations Services Concept* (CCSDS 520.0-G) —
  https://public.ccsds.org/Pubs/520x0g4.pdf

---

## 3. Prise en main du système de planification de mission

**Outil :** l'interface web du MPS (port 9091 par défaut — le `--port`
propre au planificateur ; le simulateur utilise le 8080 et le MCS le 9090).

[Claude Code : produire un exercice de 1,5 page. S'appuyer sur les configurations de planification
(`planning/activity_types.yaml`, `planning/imaging_targets.yaml`,
`planning/ground_stations.yaml`). Étapes :
  1. Ouvrir le MPS, afficher le planning des stations sol pour les 24 h à venir
  2. Choisir trois cibles de prise de vue de courants océaniques dans la configuration
  3. Placer une activité de prise de vue par cible dans la prochaine fenêtre
     exploitable disponible
  4. Lancer la vérification des conflits (durée de basculement de pointage, puissance, thermique)
  5. Résoudre les conflits, exporter le plan
  6. Ouvrir le plan obtenu dans le panneau de procédures du MCS.]

---

## 4. Tour de rôle sur le MCS

Six postes du MCS, six ateliers de 15 minutes. Chaque étudiant passe par les
six au cours de l'après-midi. À chaque atelier, la personne en poste lit à voix haute la
carte d'analyse du rôle, puis réalise une tâche propre au
poste en suivant la télémesure en direct.

| Poste | Source de l'analyse du rôle | Tâche de 15 min |
|----------|---------------------|-------------|
| Directeur de vol | `mcs/role_analysis/flight_director_role.md` | Conduire un tour de table GO/NO-GO sur le tableau de bord en direct |
| Puissance et thermique | `mcs/role_analysis/eps_tcs_role.md` | Identifier la prochaine éclipse et prédire le SoC de la batterie en sortie |
| Dynamique du vol (AOCS) | `mcs/role_analysis/aocs_role.md` | Calculer l'AOS, le TCA et le LOS du prochain passage d'Iqaluit |
| TT&C | `mcs/role_analysis/ttc_role.md` | Configurer le passage de la balise bas débit à la liaison descendante haut débit à l'AOS |
| Opérations charge utile | `mcs/role_analysis/payload_ops_role.md` | Programmer une séance de prise de vue via le MPS |
| FDIR / Systèmes | `mcs/role_analysis/fdir_systems_role.md` | Parcourir le panneau FDIR et expliquer une règle |

[Claude Code : convertir chaque ligne en carte d'atelier d'une page et
l'inclure dans le dossier des étudiants.]

---

## 5. Exercice d'équipe : plan de passage

L'équipe rédige un plan de passage de 60–90 min pour un prochain
passage d'Iqaluit. Le plan doit comporter :

- l'horaire du passage (AOS – TCA – LOS, avec marges) ;
- les procédures à exécuter (à partir de l'aide-mémoire des procédures sélectionnées) ;
- la fenêtre de prise de vue, l'ID de la cible, la fauchée au sol prévue ;
- la configuration de la liaison descendante (débit, codage) ;
- la contingence en cas d'anomalie : citer **deux** pannes plausibles et
  l'ID de la procédure à exécuter pour chacune.

Les plans sont lus à voix haute à 16 h 30 et critiqués par une autre équipe à l'aide de
la fiche d'évaluation par les pairs de l'axe Équipe.

---

## 6. Débriefing et lectures attendues pour le jour 2

> **Lectures attendues avant le jour 2.** Lisez la *Référence MCS et MPS pour les étudiants*
> (`student_tool_reference.md`) — sections 1 à 4.
> Temps de lecture estimé : 45 minutes. Apportez vos questions pour le jour 2 à 09 h 00.

Questions de débriefing :

1. Quel poste du MCS vous a semblé le plus naturel ? Pourquoi ?
2. Qu'est-ce qui vous a surpris dans le déroulement temporel d'un passage de station sol ?
3. Quel point aimeriez-vous voir mieux documenté avant le jour 2 ?

---

## 7. Outils, fichiers et références

### Outils utilisés

- Système de contrôle de mission (MCS) — application web, port 9090
- Système de planification de mission (MPS) — application web, port 9091 (son propre serveur)
- Boucle vocale — softphone du Cyber Range

### Fichiers du simulateur cités

- `configs/eosat1/mission.yaml`
- `configs/eosat1/orbit.yaml`
- `configs/eosat1/mcs/positions.yaml`
- `configs/eosat1/mcs/role_analysis/*.md`
- `configs/eosat1/planning/*.yaml`
- `configs/eosat1/procedures/procedure_index.yaml`

### Références ouvertes

- ECSS-E-ST-70C — *Ground systems and operations* —
  https://ecss.nl/standards/active-standards/ecss-e-st-70c-ground-systems-and-operations/
- ECSS-E-ST-70-11C — *Space segment operability* —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/
- Normes CCSDS — https://public.ccsds.org/Publications/default.aspx
- NASA *Space Flight Program and Project Management Requirements* (NPR 7120.5F) —
  https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_
