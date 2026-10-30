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
| 13 h 00 – 15 h 00 | Tour de rôle sur le MCS : briefing de 15 min, puis chaque étudiant passe par les sept consoles (7 × 15 min) | Tour des postes effectué |
| 15 h 00 – 16 h 30 | Exercice d'équipe de plan de passage sur le MPS | Plan de passage rédigé par l'équipe |
| 16 h 30 – 17 h 00 | Débriefing et briefing du jour 2 ; **rappel des lectures attendues** | Prêts pour le jour 2 |

**Cadre :** Cyber Range de l'Université d'Ottawa, salle des consoles. Le simulateur exécute le
point de reprise **Nominal après recette en orbite** (BP-1 dans la spécification des points
d'arrêt) — le satellite est en bonne santé et en opérations de routine, de sorte que l'équipe
peut se concentrer sur les outils plutôt que sur la reprise.

---

## 1. Briefing — ce que nous exploitons

EOSAT-1 est un CubeSat 6U (12,0 kg à sec, 12,40 kg avec ergols) destiné à
la surveillance des courants océaniques le long des côtes canadiennes. Son
imageur multispectral à balayage de type « pushbroom » à quatre bandes (443,
560, 665 et 865 nm) offre une fauchée de 273 km avec une distance
d'échantillonnage au sol de 33,4 m. Il évolue sur une orbite héliosynchrone
de 513 km inclinée à 97,39°, avec le nœud ascendant à 10 h 00 heure locale ;
chaque orbite de 94,5 minutes comporte donc environ 34 minutes d'éclipse.
L'énergie provient de cellules fixées sur la structure et de deux ailes
déployables, et alimente une batterie de 100 Wh. L'attitude est contrôlée par
quatre roues de réaction, avec deux senseurs stellaires, six capteurs solaires
grossiers, un magnétomètre et trois gyros, et un module de monergol vert de 1U
(66,9 m/s) assure l'évitement de débris, la compensation de la traînée et la
poussée de retrait de service en fin de vie.

Le segment sol compte cinq stations polaires en bande S — Iqaluit, Troll,
Svalbard, Inuvik et O'Higgins — avec un masque de 5° : environ 51 passages par
jour, d'une durée moyenne de 7,5 minutes, avec un écart médian de 33 minutes.
La télémesure suit une échelle à trois échelons : BEACON 1 kbit/s, LOW
16 kbit/s pour les opérations de routine, HIGH 128 kbit/s pour les vidages
d'images au-dessus de 10° d'élévation.

Le briefing complet se trouve dans le manuel du cours, partie 2, §5.7. Les
valeurs de référence figurent dans `configs/eosat1/mission.yaml` et
`orbit.yaml`.

### 1.1 Les quatre éléments du segment sol

Le manuel du cours, partie 2, §8.2, passe en revue les quatre éléments tels
qu'ils apparaissent dans la salle : les **stations sol** (cinq sites polaires en
bande S avec un masque de 5° — Iqaluit 63,7° N, Inuvik 68,3° N, Svalbard
78,2° N, Troll 72,0° S et O'Higgins 63,3° S ; `ttc.active_gs`, 0x0523, indique
la station active), la **bande de base** (le flux de santé RF et bande de
base : Eb/N0 et synchronisation trame), le **MCS** (port 9090) et la
**dynamique du vol** (le planning des contacts du planificateur sur le port 9091
et `tools/pass_gap_analysis.py`). La liste des stations et leurs coordonnées
figurent dans `orbit.yaml`.

### 1.2 Géométrie des passages — le cas polaire en bande S

Le manuel du cours, partie 2, §8.2.1, avec la figure 8.1 (une orbite avec les
cônes de visibilité des cinq stations, segments éclairés et en éclipse ombrés),
sert de texte à la séance. Le message à faire passer : les stations sont à
haute latitude, là où convergent les traces au sol d'une orbite héliosynchrone
polaire, de sorte que la plupart des orbites amènent le satellite au-dessus de
l'une d'elles. Sur 48 h, cela donne 103 passages, un écart médian de 33 minutes
et un écart maximal de 79 minutes. Les passages durent de 3 à 9,4 minutes ; le
maximum au zénith avec le masque de 5° est de 9,3 minutes à 513 km.

### 1.3 Structure d'une procédure

Parcourir `procedures/leop/first_acquisition.md` à l'aide de l'*Aide-mémoire
des procédures*, « Lire un fichier de procédure », et du manuel du cours, partie 2,
§7.4. Mettre en évidence l'en-tête et son état d'entrée, la liste de contrôle
Prerequisites, les étapes construites à partir des étiquettes **TC**,
**Action**, **Verify** et **Note**, la rubrique Off-Nominal Handling, ainsi
que Exit state et Post-Conditions, qui forment le critère de sortie. La
responsabilité n'est pas une colonne du fichier : ce sont les
`required_positions` de `procedure_index.yaml`. Les étudiants lisent les
procédures ; ils ne les rédigent pas.

### 1.4 Introduction aux services PUS (allégée)

Utiliser la liste des sept services de la *Référence MCS et MPS pour les
étudiants*, §3 (S1, S3, S5, S8, S9, S11 et S17, une ligne chacun).
L'introduction complète se trouve dans le manuel du cours, partie 2, §7.6, et
la source est `mcs/pus_services.yaml`. Les étudiants commandent par le MCS ; la
connaissance du PUS ne sert que de contexte.

---

## 2. Synthèse de la mission EOSAT-1 (lecture attendue avant le jour 1)

> **À lire avant le jour 1.** Temps de lecture estimé : 25 minutes.

La lecture attendue est le manuel du cours, partie 2, §5.7 (*Ce que nous
exploitons — EOSAT-1 en 600 mots*), complété par les §§ 5.2 à 5.5 pour le
concept d'opérations : l'arc de la mission, ce qu'un opérateur doit savoir
faire, les postes de la salle de contrôle, et l'organisation des passages et
des quarts. Sur l'orbite : une orbite héliosynchrone conserve l'heure solaire
locale de chaque passage, de sorte que les images d'une cible sont prises sous
un éclairage comparable ; celle d'EOSAT-1 est à 513 km avec le nœud ascendant
à 10 h 00, elle comporte donc une éclipse à chaque orbite. La décroissance
naturelle depuis 513 km prend 5,0 ans à activité solaire moyenne et 14,2 ans
au minimum solaire, ce qui ne respecte pas la règle de retrait de service de
5 ans : la mission se termine donc par une poussée de 34,3 m/s qui abaisse le
périgée à 390 km (NOM-014), après quoi la rentrée prend 1,5 an (4,2 ans au
minimum solaire). Le choix des
bandes (443, 560, 665 et 865 nm, pour le carbone organique dissous et la
chlorophylle de surface) est expliqué au §5.7. Figures : la figure 8.1 pour
l'orbite et la visibilité des stations, et le §5.6 pour l'aménagement de la
salle de contrôle.

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

> **À FAIRE (auteur) :** Rédiger l'exercice MPS d'une page et demie pour
> cette séance à partir de `planning/activity_types.yaml`,
> `planning/imaging_targets.yaml` et `planning/ground_stations.yaml` :
> ouvrir le planning des stations sur 24 h, choisir trois cibles de courants
> océaniques, placer une activité de prise de vue par cible dans une fenêtre
> exploitable, lancer la vérification des conflits (temps de basculement,
> puissance, thermique), résoudre et exporter le plan, puis l'ouvrir dans la
> page Procedures du MCS. Le manuel du cours, partie 2, §8.5, en donne une
> version en dix étapes qui peut servir de base.

---

## 4. Tour de rôle sur le MCS

Un briefing de 15 minutes, puis sept ateliers de 15 minutes, un par console
configurée dans `mcs/positions.yaml` : exactement le créneau 13 h 00 – 15 h 00.
Chaque étudiant passe par les sept au cours de l'après-midi. À chaque atelier,
la personne en poste lit à voix haute la carte d'analyse du rôle, puis réalise
une tâche propre au poste en suivant la télémesure en direct et la consigne sur
la carte correspondante du cahier d'exercices (WB-5.1). Le responsable de
mission et le segment sol sont des rôles de salle, et non des consoles ; la
vérification du segment sol fait partie de l'atelier TT&C.

| Poste | Source de l'analyse du rôle | Tâche de 15 min |
|----------|---------------------|-------------|
| Directeur de vol | `mcs/role_analysis/flight_director_role.md` | Conduire un tour de table GO/NO-GO sur le tableau de bord en direct (*go for* `CONNECTION_TEST`) |
| Puissance et thermique | `mcs/role_analysis/eps_tcs_role.md` | Prédire le SoC de la batterie à la sortie de la prochaine éclipse ; nommer le réchauffeur au rapport cyclique le plus élevé |
| Dynamique du vol | `mcs/role_analysis/aocs_role.md` | Comparer `aocs.att_error` au bilan du mode NOMINAL ; calculer l'AOS, le TCA et le LOS du prochain passage d'Iqaluit |
| TT&C | `mcs/role_analysis/ttc_role.md` | Parcourir l'échelle de débits de LOW à HIGH à l'AOS ; confirmer la station qui assure le passage |
| Opérations charge utile | `mcs/role_analysis/payload_ops_role.md` | Programmer une séance de prise de vue via le MPS ; confirmer `payload.fpa_ready` = 1 |
| FDIR / systèmes | `mcs/role_analysis/fdir_systems_role.md` | Parcourir le panneau FDIR et expliquer une règle |
| Propulsion | `mcs/role_analysis/propulsion_role.md` | Lire le masque des verrouillages d'armement (`prop.arm_inhibit_mask`, 0x0B15) et nommer celui qui bloque l'armement, sans envoyer de commande |

Les cartes d'atelier sont les cartes WB-5.1 du cahier d'exercices, une par
console, chacune avec sa tâche et les relevés à consigner. L'analyse du rôle
indiquée dans le tableau est la fiche que la personne en poste lit à voix haute.

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
