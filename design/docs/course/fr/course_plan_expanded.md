---
title: "Cours de conception de missions SpaceCDF"
subtitle: "Conception collaborative de missions spatiales : du problème au CubeSat prêt pour le vol — programme de 40 heures"
course-codes: "SpaceCDF · 40 heures"
term: "Été 2026"
version: "v2 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
footer-en: "SpaceCDF · 40-Hour Course Plan · 2026"
footer-fr: "SpaceCDF · Plan du cours · 2026"
running: "SpaceCDF — Plan du cours de 40 heures"
---

# Plan du cours

## Intitulé du cours

**Conception collaborative de missions spatiales : du problème au
CubeSat prêt pour le vol.** Un stage intensif de 40 heures en
conception concourante de missions spatiales, dispensé avec SpaceCDF,
centre de conception concourante assisté par l'IA.

## Public

Ingénieurs, scientifiques et chefs de projet participant à des études
en centre de conception concourante (CDF). **Aucune expérience
préalable de la conception d'engins spatiaux n'est requise**, mais une
formation d'ingénieur opérationnelle est supposée (mécanique,
électromagnétisme, notions de programmation).

## Organisation

Le programme de 40 heures se déroule sur **cinq jours × huit heures**
ou **dix demi-journées**. La promotion travaille en **équipes
pluridisciplinaires de 4–5 personnes**, chaque étudiant occupant un
poste du CDF (p. ex. puissance, AOCS, communications, charge utile).
Deux ouvrages de référence accompagnent le cours :

- **Le Guide de l'animateur** — référence pédagogique complète,
  détaillant chaque séance, avec corrigés et schémas.
- **Le Cahier d'exercices de l'apprenant** — contenus condensés et
  fiches d'exercices pour les travaux sur l'outil SpaceCDF.

> **Lectures attendues avant le jour 1.** *NASA CubeSat 101* (≈ 90 min)
> — [https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf).
> *NASA Systems Engineering Handbook*, §1 – §3 (≈ 90 min) —
> [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).

---

## Ce que la promotion va construire

D'ici la fin de la semaine, chaque équipe livrera :

1. **Une conception préliminaire complète de mission CubeSat** —
   concept, référentiel d'exigences, toutes les décisions majeures
   relatives aux sous-systèmes, matrice d'interfaces, plan de V&V,
   estimation des coûts et registre des risques.
2. **Un ensemble de documents alignés sur les normes ECSS**, exporté
   automatiquement par SpaceCDF : MRD (document d'exigences de
   mission), TS (spécification technique), VP (plan de vérification).
3. **Une présentation de revue de conception de type PDR** montrant le
   bouclage des bilans, les options étudiées et le chemin vers la
   conception détaillée.

![Phases du cycle de vie et jalons de revue — NASA et ECSS](../assets/figures/fig_lifecycle.png)

*Figure 2.1 — Le cycle de vie dans lequel s'inscrit le cours. Le
programme de 40 heures couvre la pré-phase A jusqu'à la fin de la
phase B (PDR).*

![Cycle en V — la décomposition rejoint l'intégration](../assets/figures/fig_system_v.png)

*Figure 2.2 — Cycle en V. La décomposition (à gauche) guide la
réalisation ; l'intégration et la vérification (à droite) bouclent la
boucle. Les tirets horizontaux représentent la traçabilité qu'exigent
à la fois l'ECSS et la NASA.*

![Les 17 processus techniques communs du NASA SEH](../assets/figures/fig_seh_processes.png)

*Figure 2.3 — Les 17 processus du NASA SEH, répartis entre conception
du système (en haut), réalisation du produit (au milieu) et management
technique (en bas). Chaque séance du cours indique le ou les processus
dont elle relève.*

---

## Registre des normes de référence

| Norme | Titre | Place dans le cours |
|----------|-------|----------------------|
| NASA SP-2016-6105 Rev 2 | *Systems Engineering Handbook* | Toutes les séances ; texte de base pour les processus d'ingénierie système |
| NPR 7123.1D | *NASA Systems Engineering Processes & Requirements* | Séances 1.1, 2.1, 4.1, 5.1 |
| NPR 7120.5F | *NASA Space Flight Program & Project Management* | Séances 1.1, 4.4, 5.1 |
| ECSS-E-ST-10C Rev. 1 | Ingénierie spatiale — exigences générales | Toutes les séances |
| ECSS-E-ST-10-02C Rev. 1 | Vérification | Séances 4.1, 4.2 |
| ECSS-E-ST-10-24C | Gestion des interfaces | Séance 2.3 |
| ECSS-M-ST-10C Rev. 1 | Planification et management de projet | Séances 1.1, 4.4 |
| ECSS-M-ST-80C | Gestion des risques | Séance 4.3 |
| ECSS-Q-ST-30-02C | AMDE / AMDEC (FMEA / FMECA) | Séance 4.3 |
| ECSS-E-ST-32C | Structures | Séance 3.2 |
| ECSS-E-ST-31C | Contrôle thermique | Séance 3.3 |
| ECSS-E-ST-50-05C | Radiofréquences et modulation | Séance 3.4 |
| ECSS-U-AS-10C Rev. 2 | Atténuation des débris spatiaux | Séance 5.2 |
| Cal Poly CDS Rev 14 | *CubeSat Design Specification* | Séances 3.2, 5.3 |
| CCSDS PUS | Norme d'utilisation des paquets (*Packet Utilization Standard*) | Séance 4.1, semaine 3 |
| Règlement des radiocommunications de l'UIT | Attribution des fréquences et licences | Séance 5.2 |
| ISDE CPC-2-6-02 | Licences de spectre des stations spatiales (Canada) | Séance 5.2 |
| LSTS | Loi sur les systèmes de télédétection spatiale (Canada) | Séance 5.2 |

> **Référence normative.** Les normes ECSS sont librement accessibles sur
> [https://ecss.nl/](https://ecss.nl/). Normes de la NASA : [https://standards.nasa.gov](https://standards.nasa.gov).

---

## Carte des modules — séances, § du NASA SEH, § ECSS, écrans de SpaceCDF

| Jour | Séance | § NASA SEH | § ECSS | Onglet SpaceCDF | Livrable |
|-----|---------|-----------|--------|--------------|-------------|
| 1 | 1.1 Introduction et cycle de vie | §1 – §3 | E-ST-10C §4 | Step 1 | Matrice d'adaptation |
| 1 | 1.2 Besoin de mission et parties prenantes | §4 | E-ST-10C §5.2 | Step 1 | Matrice des parties prenantes, objectifs |
| 1 | 1.3 Analyse de compromis de mission | §6.5 (processus 17) | E-ST-10C §5.3 | Step 2 | Matrice d'étude de compromis |
| 1 | 1.4 Concept d'opérations | Annexe S | E-ST-10C §5.4 | Onglet ConOps | Plan du ConOps |
| 2 | 2.1 Ingénierie des exigences | §4.2 | E-ST-10C §5.5 | Onglet Exigences (Requirements) | Référentiel d'exigences |
| 2 | 2.2 Fonctions et décomposition | §4.3 | E-ST-10C §5.6 | Onglet Fonctions (Functions) | Référentiel fonctionnel |
| 2 | 2.3 Gestion des interfaces | §6.3 | E-ST-10-24C | Onglet Interfaces | Matrice N² |
| 2 | 2.4 Architecture et schémas fonctionnels | §4.4 | E-ST-10C §5.7 | Dashboard | Schéma fonctionnel |
| 3 | 3.1 Puissance et EPS | §4.4 | E-ST-20C | Onglet EPS | Dimensionnement solaire/batterie |
| 3 | 3.2 Structure et mécanismes | §4.4 | E-ST-32C | Onglet Structure | Bilan de masse |
| 3 | 3.3 Thermique | §4.4 | E-ST-31C | Onglet Thermal | Bilan thermique |
| 3 | 3.4 Communications | §4.4 | E-ST-50-05C | Onglet Link Budget | Bilan de liaison |
| 4 | 4.1 Choix des équipements | §6.5 | E-ST-10C §5.8 | Onglet Équipements (Equipment) | Nomenclature (BOM) |
| 4 | 4.2 Planification de la V&V | §6.4 | E-ST-10-02C | V&V Matrix | Matrice de vérification |
| 4 | 4.3 Gestion des risques | §6.6 | M-ST-80C | Onglet Risk | Registre des risques |
| 4 | 4.4 Coûts et planning | §6.7 | M-ST-10C | Onglet Cost | Estimation des coûts |
| 5 | 5.1 Préparation des revues de jalon | §7 | M-ST-10C §6 | Gate Review | Dossier de PDR |
| 5 | 5.2 Réglementation et licences | — | (national) | Regulatory | Dossier de déclarations réglementaires |
| 5 | 5.3 Intégration au lanceur | §6.5 | E-ST-10C §5.10 | Launch ICD | Liste de vérification de l'ICD |
| 5 | 5.4 Optimisation et revue finale | §6.5 | E-ST-10C §5.11 | Optimizer | Conception finale |

---

## Diagramme de Gantt du cours — variantes intensive de 40 heures et sur 3 semaines

Le même contenu peut être dispensé soit en stage intensif de 5 jours
et 40 heures (une séance par créneau), soit en version étalée sur
3 semaines (voir le programme sur 3 semaines). L'enchaînement des
séances ne change pas.

| | Lun. | Mar. | Mer. | Jeu. | Ven. |
|---|------|------|------|------|------|
| **Matin** | 1.1 + 1.2 | 2.1 + 2.2 | 3.1 + 3.2 | 4.1 + 4.2 | 5.1 + 5.2 |
| **Après-midi** | 1.3 + 1.4 | 2.3 + 2.4 | 3.3 + 3.4 | 4.3 + 4.4 | 5.3 + 5.4 |

---

## Jour 1 — Définition de la mission et concept (8 h)

### Séance 1.1 — Introduction à la conception des missions spatiales (2 h)

- Qu'est-ce qu'un centre de conception concourante (CDF) ? Historique
  (Concurrent Design Facility de l'ESA, Team-X du JPL, COMPASS du
  centre Glenn de la NASA).
- Le cycle en V (NASA SEH, chap. 2 – 3) — voir la figure 2.2.
- Les 17 processus d'ingénierie système (NPR 7123.1) — voir la
  figure 2.3.
- Phases du cycle de vie NASA / ECSS et jalons de revue — voir la
  figure 2.1.
- Rôle de chaque poste du CDF et sens de la « responsabilité » dans
  un CDF.
- **Exercice :** mettre en correspondance les 17 processus et les
  onglets de l'outil SpaceCDF.
- **Fiche d'exercices :** fiche 1.1 (carte des processus).

### Séance 1.2 — Besoin de mission et analyse des parties prenantes (2 h)

- Processus 1 du NASA SEH : définition des attentes des parties
  prenantes.
- Rédaction de l'énoncé du problème (NASA SEH, §4.1).
- Identification des parties prenantes et recueil des besoins.
  Dialogue avec les communautés autochtones et prise en compte de la
  DNUDPA (UNDRIP) dans le contexte canadien.
- Définition des objectifs assortis de critères de réussite
  mesurables.
- Hiérarchie MoE / MoP / TPM.
- **Exercice :** définir le besoin de mission pour un problème type
  (avec l'étape 1 de SpaceCDF).
- **Fiche d'exercices :** matrice des parties prenantes, hiérarchie
  des objectifs.

### Séance 1.3 — Analyse de compromis de mission (2 h)

- Processus 17 du NASA SEH : analyse de décision.
- Solutions spatiales et non spatiales — *quand ne pas construire de
  satellite*.
- Méthodologie des études de compromis : critères, pondérations,
  notation ; AHP et sensibilité de la somme pondérée.
- Services de données existants (Copernicus / Sentinel, Planet,
  Spire, Radarsat).
- **Exercice :** mener le compromis de mission dans SpaceCDF
  (étape 2).
- **Fiche d'exercices :** matrice d'étude de compromis avec notation.

### Séance 1.4 — Concept d'opérations (2 h)

- Annexe S du NASA SEH : structure du ConOps.
- Architecture de la mission : segments spatial, sol et utilisateur.
- Phases de la mission (LEOP → recette en orbite → nominale → retrait
  de service) — voir la figure 2.4.
- Modes opérationnels et fonctionnement par intermittence.
- Conception de la chaîne de flux de données.
- Options d'architecture du segment sol.
- **Exercice :** construire le ConOps dans SpaceCDF.
- **Fiche d'exercices :** plan du ConOps selon l'annexe S.

![Chronologie du ConOps — du LEOP au retrait de service](../assets/figures/fig_conops_timeline.png)

*Figure 2.4 — Chronologie représentative d'une mission LEO. Dès le
jour 1, le cours conçoit la mission au regard de cette chronologie.*

> **Lectures attendues avant le jour 2.** SMAD4, chap. 4 – §6
> (définition de la mission) ; annexe C du NASA SEH (*How to write a
> good requirement*) — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).

---

## Jour 2 — Exigences, fonctions et interfaces (8 h)

### Séance 2.1 — Ingénierie des exigences (2 h)

- Processus 2 du NASA SEH : définition des exigences techniques.
- Exigences SMART (spécifiques · mesurables · atteignables ·
  pertinentes · traçables).
- *Le QUOI, pas le COMMENT* — exigences et choix de conception. Le
  défaut classique : inscrire la réalisation dans les exigences.
- Hiérarchie des exigences : mission → système → sous-système.
- Annexe C du NASA SEH — *How to write a good requirement*.
- **Exercice :** générer les exigences à partir des objectifs dans
  SpaceCDF.
- **Fiche d'exercices :** liste de vérification de la qualité des
  exigences.

### Séance 2.2 — Fonctions et décomposition (2 h)

- Processus 3 du NASA SEH : décomposition logique.
- Analyse fonctionnelle et décomposition physique.
- Arbres fonctionnels ; matrice d'allocation des fonctions ; matrice
  des modes.
- **Exercice :** décomposer la fonction de plus haut niveau de la
  mission dans SpaceCDF.
- **Fiche d'exercices :** matrice d'allocation des fonctions.

### Séance 2.3 — Gestion des interfaces (2 h)

- NASA SEH, §6.3 (processus 12) — gestion des interfaces.
- ECSS-E-ST-10-24C — documents d'exigences d'interface.
- La matrice N² et la classification des types d'interfaces
  (mécanique, électrique, thermique, données, RF, optique).

![Matrice d'interfaces N² d'un CubeSat 6U](../assets/figures/fig_n2_matrix.png)

*Figure 2.5 — Matrice d'interfaces N² d'un CubeSat 6U. Les cellules
sont colorées selon le type d'interface : « D » = données,
« E » = électrique, « M » = mécanique, « T » = thermique, « R » = RF,
« O » = optique.*

- **Exercice :** compléter la matrice N² de la mission de l'équipe
  dans SpaceCDF.
- **Fiche d'exercices :** projet d'exigences d'interface pour deux
  paires.

### Séance 2.4 — Architecture et schémas fonctionnels (2 h)

- Registres de décisions d'architecture.
- Conventions des schémas fonctionnels ; flux de signaux et flux de
  puissance.
- Architecture de puissance ; architecture des données ; couplage
  thermique.
- **Exercice :** construire les schémas fonctionnels des
  sous-systèmes dans SpaceCDF.
- **Fiche d'exercices :** journal des décisions d'architecture
  (3 entrées).

> **Lectures attendues avant le jour 3.** SMAD4, chap. 9 (choix de
> l'orbite), chap. 11 (puissance), chap. 12 (thermique), chap. 13
> (structures). Toutes les sections citées sont disponibles dans
> Brightspace.

---

## Jour 3 — Boucle de conception des sous-systèmes (8 h)

### Séance 3.1 — Puissance et EPS (2 h)

- Structure du bilan de puissance : bus / servitude / charge utile /
  communications / thermique / marge.
- Dimensionnement du générateur solaire (fixé sur la structure ou
  déployable) en fin de vie.
- Dimensionnement de la batterie — compromis entre DoD et durée de vie
  en cycles.
- Architecture de l'EPS : MPPT, PCDU, bus unique ou double bus.

![Profil de puissance sur une orbite — production et charges empilées](../assets/figures/fig_power_modes.png)

*Figure 2.6 — Production (en haut) et charges empilées (en bas) sur
une orbite. L'éclipse dimensionne la batterie ; les impulsions des
communications et de la charge utile dimensionnent la puissance crête
de la PCDU.*

- **Exercice :** dimensionner le générateur solaire et la batterie
  dans SpaceCDF.
- **Fiche d'exercices :** feuille de dimensionnement de l'EPS, cas le
  plus défavorable en fin de vie.

### Séance 3.2 — Structure et mécanismes (2 h)

- Cal Poly CDS Rev 14 — enveloppe structurale du CubeSat.
- Charges au lancement : quasi statiques, vibrations sinusoïdales,
  vibrations aléatoires, chocs.
- Convergence du bilan de masse selon la politique de marges ECSS.

![Bilan de masse — répartition et politique de marges ECSS](../assets/figures/fig_mass_budget.png)

*Figure 2.7 — Répartition de la masse et échéancier des marges ECSS.
La marge composée (maturité des équipements × marge système de 20 %)
démarre à +44 % en phase A et se resserre jusqu'à +5 % en phase D.*

- **Exercice :** dimensionner la structure dans SpaceCDF.
- **Fiche d'exercices :** bilan de masse avec colonne de marge.

### Séance 3.3 — Thermique (2 h)

- Analyse au premier ordre de l'équilibre radiatif.
- Enveloppe cas chaud / cas froid.
- Angle β et éclipse — voir la figure 2.8.
- Contrôle thermique passif ou actif ; MLI ; réchauffeurs ; caloducs.

![Enveloppe de l'angle β et analyse de la fraction d'éclipse](../assets/figures/fig_beta_eclipse.png)

*Figure 2.8 — Plage de l'angle β en fonction du jour de l'année (à
gauche) et courbes analytiques de la fraction d'éclipse (à droite)
pour une orbite de type ISS et une SSO à 600 km.*

- **Exercice :** analyse de l'enveloppe thermique dans SpaceCDF.
- **Fiche d'exercices :** bilan thermique avec rapport cyclique des
  réchauffeurs.

### Séance 3.4 — Communications (2 h)

- Notions de base du bilan de liaison : PIRE, affaiblissement en
  espace libre (FSPL), G/T, C/N₀ et Eb/N₀.
- Choix de la bande de fréquences — UHF / S / X / Ka.
- Modulation et codage : QPSK + LDPC (famille DVB-S2) pour le sol.
- Bilan Doppler et de dérive Doppler pour un passage polaire.
- Diagrammes de rayonnement des antennes et pointage.

![Bilan de liaison descendante en bande S — cascade](../assets/figures/fig_link_budget.png)

*Figure 2.9 — Bilan de liaison en cascade type. Le C/N₀ requis et la
marge de liaison figurent toujours en bas à droite.*

- **Exercice :** boucler le bilan de liaison dans SpaceCDF.
- **Fiche d'exercices :** calculateur de bilan de liaison avec marge.

> **Lectures attendues avant le jour 4.** SMAD4, chap. 17 (V&V) ; ECSS-E-ST-10-02C ; NASA NPR 8715.3 (sécurité des systèmes —
> introduction seulement).

---

## Jour 4 — Équipements, V&V, risques, coûts (8 h)

### Séance 4.1 — Choix des équipements (2 h)

- Catalogue ou conception spécifique.
- Décisions de passage de jalon fondées sur le TRL.

![Échelle des niveaux de maturité technologique](../assets/figures/fig_trl.png)

*Figure 2.10 — Échelle des TRL. La plupart des décisions relatives à
la plateforme d'un CubeSat se situent aux TRL 7 – 9 ; les instruments
nouveaux, aux TRL 4 – 6, exigent une planification explicite de la
réduction des risques.*

- **Exercice :** terminer le choix des équipements dans SpaceCDF.
- **Fiche d'exercices :** liste de vérification de la compatibilité
  des équipements.

### Séance 4.2 — Planification de la vérification et de la validation (2 h)

- Processus 7 – 8 du NASA SEH.
- ECSS-E-ST-10-02C — méthodes de vérification (A · T · R · I).
- Structure de la matrice de vérification.
- Niveaux d'essai — unité → sous-système → système → recette →
  qualification.
- Essais d'environnement — vibrations, vide thermique, CEM.
- **Exercice :** examiner la matrice de conformité dans SpaceCDF.
- **Fiche d'exercices :** matrice V&V pour 10 exigences clés.

### Séance 4.3 — Gestion des risques (2 h)

- ECSS-M-ST-80C — processus de gestion des risques.
- Identification, évaluation (matrice 5×5) et réduction des risques.
- Méthodologie AMDEC (FMECA) (ECSS-Q-ST-30-02C).
- Analyse des points de défaillance unique.
- Indicateurs de performance technique (TPM).

![Matrice des risques 5×5 avec exemples résolus](../assets/figures/fig_risk_matrix.png)

*Figure 2.11 — La matrice des risques en pratique. Chaque point
représenté est un risque réel d'une mission représentative ; sa
position dans la matrice détermine la priorité de réduction.*

- **Exercice :** examiner les scores de risque et la fiabilité dans
  SpaceCDF.
- **Fiche d'exercices :** registre des risques pour les 5 principaux
  risques.

### Séance 4.4 — Coûts et planning (2 h)

- Estimation des coûts : paramétrique (SSCM, COMPACT), par analogie,
  ascendante.
- Structure du WBS (NPR 7120.5).
- Facteurs de coût et fractions de coût d'un CubeSat.
- Estimation du planning et chemin critique ; effets de courbe
  d'apprentissage pour les constellations.
- **Exercice :** examiner la ventilation des coûts et lancer
  l'optimiseur.
- **Fiche d'exercices :** estimation des coûts par élément du WBS.

> **Lectures attendues avant le jour 5.** ECSS-M-ST-10C, §6 (jalons
> de revue) — [https://ecss.nl/](https://ecss.nl/). Règlement des
> radiocommunications de l'UIT, article 21 — [https://www.itu.int/pub/R-REG-RR](https://www.itu.int/pub/R-REG-RR).

---

## Jour 5 — Revue de conception et réglementation (8 h)

### Séance 5.1 — Préparation des revues de jalon (2 h)

- ECSS-M-ST-10C — structure des jalons de revue.
- Critères de sortie des revues MCR / SRR / PDR / CDR.
- Structure de la présentation en revue de conception : dossier type
  de 6 diapositives.
- Gestion des actions.
- **Exercice :** mener la revue de jalon dans SpaceCDF ; solder les
  actions.
- **Fiche d'exercices :** plan de la présentation de la PDR.

### Séance 5.2 — Réglementation et licences (2 h)

- Licences de fréquences — UIT, IARU, autorité nationale.
- Procédure de notification à l'UIT (API → coordination →
  notification).
- LSTS canadienne pour la télédétection.
- Contrôle des exportations : ITAR / EAR / CGP canadien.
- Convention sur l'immatriculation de l'ONU (CUPEEA).
- Réglementation sur les débris spatiaux (règles des 25 ans / 5 ans).
- **Exercice :** générer les dossiers réglementaires dans SpaceCDF.
- **Fiche d'exercices :** arbre de décision pour les licences.

### Séance 5.3 — Intégration au lanceur (2 h)

- Panorama des fournisseurs de lancement et des tarifs.
- Normes de déployeurs (ISIPOD, EXOpod, CSD).
- Exigences de l'ICD lanceur (mécaniques, électriques,
  d'environnement).
- Interrupteurs de séparation et inhibitions.
- Dérivation de la spécification des essais d'environnement.
- **Exercice :** choisir un fournisseur de lancement, examiner les
  exigences de l'ICD.
- **Fiche d'exercices :** liste de vérification de la conformité à
  l'ICD lanceur.

### Séance 5.4 — Optimisation de la conception et revue finale (2 h)

- Optimisation multiobjectif (notions de Pareto).
- Analyse de sensibilité (criblage de Morris).
- Itération et convergence de la conception.
- Présentation de la revue de conception finale.
- Recueil du retour d'expérience.
- **Exercice :** lancer l'optimiseur, examiner le front de Pareto,
  choisir la conception finale.
- **Exercice final :** chaque équipe présente la conception complète
  de sa mission.

---

## Évaluation

- **Jours 1 – 4 :** fiches d'exercices remplies en classe (formative).
- **Jour 5 :** présentation en équipe de la conception complète de la
  mission (sommative).
- **Après le cours :** accès maintenu à l'outil SpaceCDF et au Guide
  de l'animateur pour l'autoformation.

### Matrice des acquis d'apprentissage selon Bloom

| Acquis | Niveau de Bloom | Où il est acquis |
|---------|-------------|--------------|
| Restituer les 17 processus du SEH et la séquence des jalons | Mémoriser | Séances 1.1, 5.1 |
| Expliquer le cycle en V et ses limites | Comprendre | Séances 1.1, 4.2 |
| Appliquer les critères SMART pour dériver des exigences | Appliquer | Séance 2.1 |
| Appliquer la matrice N² à un CubeSat réel | Appliquer | Séance 2.3 |
| Analyser un bilan de liaison et identifier la perte dominante | Analyser | Séance 3.4 |
| Analyser un registre des risques et identifier les points de défaillance unique | Analyser | Séance 4.3 |
| Évaluer des options de compromis et défendre une recommandation | Évaluer | Séances 1.3, 5.4 |
| Créer une conception préliminaire complète de CubeSat | Créer | Revue finale du jour 5 |

### Registre des équipements et logiciels

| Outil | Rôle | Place dans le cours |
|------|---------|-----------------|
| SpaceCDF (web) | Conception concourante et revue | Tous les jours |
| Brightspace | Diffusion des lectures, remise des travaux | Tous les jours |
| Python 3.11+ (notebooks) | Exercices analytiques facultatifs | Jours 3, 4 |
| Outils de tracé libres (matplotlib, plotly) | Visualisations | Jours 3, 4 |
| Suite bureautique | Diapositives de la PDR | Jours 1, 5 |

### Bilan des connaissances préalables (autoévaluation)

| Thème | Niveau requis | Où se remettre à niveau |
|-------|----------------|------------------|
| Mécanique newtonienne | 1re année d'ingénierie | Hibbeler / Meriam |
| Algèbre vectorielle et matricielle | 2e année d'ingénierie | Strang |
| Électromagnétisme de base | 1re année de physique | Griffiths, chap. 1 – 3 |
| Statistiques et probabilités | 2e année d'ingénierie | Montgomery & Runger |
| Bases de la programmation | Aisance dans un langage quelconque | — |

### Matrice RACI de l'enseignement

| Activité | Enseignant | Co-enseignant | Assistant / animateur | Promotion |
|----------|------------|---------------|------------------|--------|
| Cours magistraux | R | A | C | I |
| Animation des séances CDF | A | R | R | C |
| Assistance sur l'outil | I | I | R | A |
| Relecture des fiches d'exercices | C | R | A | I |
| Revue de jalon | R | A | C | C |
| Jury de la revue finale | R | R | C | I |

R = réalise (*Responsible*), A = approuve (*Accountable*), C = consulté, I = informé.

---

## Approfondissements par poste (annexes)

Le Guide de l'animateur contient des annexes complètes pour chaque
poste (ingénieur système, analyste de mission, charge utile,
puissance, AOCS, thermique, structures, propulsion, communications,
OBDH, logiciel, opérations, segment sol). La liste résumée des postes
et de leurs responsabilités figure ci-dessous ; les annexes complètes
se trouvent dans le Guide de l'animateur.

| Poste | Responsable de (paramètres) | Pilote (séances) |
|----------|-------------------|-------------------|
| Ingénieur système | Marge de masse, marge de puissance, coût du système, TRL, score de santé | Toutes |
| Analyste de mission | Orbite, trace au sol, durée de contact, éclipse, β | 1.4, 3.1 – 3.3 |
| Ingénieur charge utile | Ouverture, GSD, débit, champ de vue | 1.2, 3.4 |
| Ingénieur puissance | Surface du générateur solaire, capacité de la batterie, topologie de l'EPS | 3.1 |
| Ingénieur SCAO | Bilan de pointage, capacité des roues de réaction, choix des capteurs | 3.2, 4.3 |
| Ingénieur thermique | Cas chaud/froid, surface des radiateurs, rapport cyclique des réchauffeurs | 3.3 |
| Ingénieur structures | Bouclage du bilan de masse, déployeurs, mécanismes | 3.2 |
| Ingénieur propulsion | Bilan de Δv, dimensionnement des propulseurs, masse d'ergols | (si nécessaire) |
| Ingénieur télécommunications | Bilan de liaison, diagramme d'antenne, modulation | 3.4 |
| OBDH / logiciel | OBC, architecture du logiciel de vol, FDIR, liste de télémesure | 4.1 |
| Opérations | Plan de passage, ConOps, arbre des anomalies | 1.4, 5.1 |
| Segment sol | Stations sol, MCS, MPS, archive | 1.4, 5.1 |
| Coûts / planning | WBS, CER, chemin critique | 4.4 |

---

## Liste de références (liens actifs)

- **NASA SEH (SP-2016-6105 Rev 2)** — *Systems Engineering Handbook*. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
- **NPR 7123.1D** — [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/)
- **NPR 7120.5F** — [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/)
- **NASA CubeSat 101** — [https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf)
- **Normes ECSS (toutes)** — [https://ecss.nl/](https://ecss.nl/)
- **Cal Poly CDS Rev 14** — [https://www.cubesat.org/cds-announcement](https://www.cubesat.org/cds-announcement)
- **CCSDS PUS** — [https://public.ccsds.org/Pubs/660x0g3.pdf](https://public.ccsds.org/Pubs/660x0g3.pdf)
- **Règlement des radiocommunications de l'UIT** — [https://www.itu.int/pub/R-REG-RR](https://www.itu.int/pub/R-REG-RR)
- **ISDE CPC-2-6-02** — [https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en](https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en)
- **Loi sur les systèmes de télédétection spatiale** — [https://laws-lois.justice.gc.ca/eng/acts/R-5.4/](https://laws-lois.justice.gc.ca/eng/acts/R-5.4/)
- **Lignes directrices de l'IADC sur les débris** — [https://www.iadc-home.org/](https://www.iadc-home.org/)
- **Convention sur l'immatriculation (CUPEEA, ONU)** — [https://www.unoosa.org/](https://www.unoosa.org/)
- **Wertz, Everett & Puschell** — *Space Mission Engineering : The New SMAD* (2011).
- **Larson & Wertz** — *Space Mission Analysis and Design*, 4e éd.
- **Sutton & Biblarz** — *Rocket Propulsion Elements*, 9e éd.
- **Markley & Crassidis** — *Fundamentals of Spacecraft Attitude Determination and Control*.
- **Pratt, Bostian & Allnutt** — *Satellite Communications*, 3e éd.
- **Fortescue, Stark & Swinerd** — *Spacecraft Systems Engineering*, 4e éd.
