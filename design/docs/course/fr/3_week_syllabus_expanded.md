---
title: "Conception et opérations de missions spatiales"
subtitle: "Programme intensif de 3 semaines — plan de cours"
course-codes: "Cours SpaceCDF"
term: "Été 2026"
version: "v2 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
footer-en: "SpaceCDF · 3-Week Intensive Syllabus · 2026"
footer-fr: "SpaceCDF · Programme intensif de 3 semaines · 2026"
running: "SpaceCDF — Programme intensif de 3 semaines"
---

# Programme intensif de 3 semaines

## Public et prérequis

Ce programme s'adresse aux **professionnels de l'industrie, aux
étudiants des cycles supérieurs et aux étudiants de fin de premier
cycle** ayant une formation d'ingénieur et l'envie de prendre des
décisions rapidement et devant les autres. Nous supposons acquises des
bases de mécanique, d'électromagnétisme et de programmation — mais
**aucune expérience préalable des engins spatiaux**. La promotion
compte **de 20 à 30 participants**, répartis en **équipes
pluridisciplinaires de 4 à 5 personnes**.

Le cours se déroule du lundi au vendredi, de 9 h 00 à 16 h 00, en
présentiel à l'Université d'Ottawa. L'outil qui structure le cours est
**SpaceCDF, centre de conception concourante assisté par l'IA**.

> **Lectures attendues avant le jour 1.** *NASA CubeSat 101* (≈ 90 min) —
> [https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf).
> *NASA Systems Engineering Handbook*, §2 (≈ 60 min) —
> [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).

---

## Comment les trois semaines s'articulent

![Cycle de vie de la mission et jalons de revue — de la pré-phase A à la phase F, jalons NASA et ECSS](../assets/figures/fig_lifecycle.png)

*Figure 1.1 — Le cycle de vie que vit la promotion. La semaine 1 vous
ancre dans la pré-phase A ; la semaine 2 parcourt la partie du V
correspondant aux phases A/B ; la semaine 3 vous installe aux postes
d'opérateur pendant la recette en orbite.*

Le cours suit le **cycle en V** — décomposition à gauche, intégration
et vérification à droite — et fait correspondre chaque journée à une
phase reconnaissable du cycle de vie.

![Cycle en V avec les points de contact quotidiens de la promotion](../assets/figures/fig_system_v.png)

*Figure 1.2 — Cycle en V et points de contact du cours. Le travail sur
les besoins de la mission a lieu le jour 1 ; les spécifications des
sous-systèmes convergent les jours 2–3 ; l'intégration et la V&V
occupent le jour 4 ; la revue de jalon a lieu le jour 5.*

---

## Semaine 1 — Paysage spatial canadien et environnement réglementaire

Cette semaine ancre la promotion dans le système où vivent les
missions : l'**écosystème spatial canadien**, le **paysage
réglementaire** et les cadres d'ingénierie système qu'utilisent
réellement les professionnels. Les cours magistraux sont
volontairement courts : il s'agit de poser le contexte du travail
mené avec l'outil, qui commence en semaine 2.

![Le secteur spatial canadien — acteurs et flux de financement](../assets/figures/fig_canadian_sector.png)

*Figure 1.3 — Carte du secteur spatial canadien. La place que les
étudiants se voient occuper dans ce tableau est la question centrale
du jour 1.*

### Emploi du temps quotidien

| Jour | Thème | Activités |
|-----|-------|-----------|
| **Lun.** | **L'écosystème spatial canadien** | Mandat et programmes de l'Agence spatiale canadienne. Cartographie de l'industrie : MDA, Telesat, GHGSat, Kepler, NorthStar, laboratoires universitaires. Financement de l'ASC (PDTS, FAST, CSEP). Rôle du Canada dans Artemis, le Lunar Gateway et Radarsat. Intervenant extérieur (ASC ou industrie). |
| **Mar.** | **Cadre réglementaire** | Licences de spectre d'ISDE au titre de la CPC-2-6-02. LSTS (Loi sur les systèmes de télédétection spatiale). Programme des marchandises contrôlées et contrôle des exportations. Notification à l'UIT par l'intermédiaire d'ISDE. Travaux pratiques : remplir une demande de licence de spectre auprès d'ISDE pour une mission type. |
| **Mer.** | **Normes internationales et conformité** | Cadre des normes ECSS et adaptation. Vue d'ensemble des 17 processus du NASA SEH (voir la figure 2.3 du plan de cours). Cal Poly CDS Rev 14. Atténuation des débris spatiaux (25 ans selon l'IADC, 5 ans selon la FCC). Convention sur l'immatriculation de l'ONU. Travaux pratiques : remplir une matrice d'adaptation. |
| **Jeu.** | **Besoins et opportunités de mission** | Identification des besoins de mission dans le contexte canadien (surveillance de l'Arctique, surveillance maritime, agriculture, gestion des ressources, connectivité). Analyse des parties prenantes. Dialogue avec les communautés autochtones et DNUDPA (UNDRIP). Atelier de rédaction de l'énoncé du problème. |
| **Ven.** | **Compromis spatial / non spatial et concept** | Méthodologie des études de compromis (critères, pondérations, notation). Services existants (Radarsat, Sentinel, Planet) face à de nouvelles missions. Économie des constellations et analyses de rentabilité. Constitution des équipes, choix d'un besoin de mission et première analyse de compromis dans SpaceCDF. |

### Liste de vérification réglementaire canadienne (livrable du mardi)

| Autorité | Démarche | Élément déclencheur | Délai approximatif |
|-----------|--------|---------|----------------------|
| ISDE (gestion du spectre) | Licence radio — CPC-2-6-02 | Toute émission RF à destination ou en provenance du satellite | 6 – 12 mois |
| ISDE (LSTS) | Licence LSTS | Charge utile d'observation de la Terre au-delà du seuil de résolution | 12 – 18 mois |
| UIT (par l'intermédiaire d'ISDE) | API → coordination → notification | Nouvelle assignation de fréquence | 2 – 5 ans |
| Affaires mondiales Canada | Licence d'exportation (ECL / CGP) | Transfert transfrontalier de matériel, de données ou de technologie | 4 – 12 semaines |
| UNOOSA (par l'intermédiaire d'Affaires mondiales) | Immatriculation de l'objet spatial | Mise en orbite | Au lancement |
| ISDE (objet spatial) | Plan d'atténuation des débris | Lancement — IADC 25 ans / FCC 5 ans | Au lancement |

> **Référence normative.** ECSS-E-ST-10C Rev. 1 — *System engineering
> general requirements* — [https://ecss.nl/standards/active-standards/ecss-e-st-10c-rev-1-system-engineering-general-requirements/](https://ecss.nl/standards/active-standards/ecss-e-st-10c-rev-1-system-engineering-general-requirements/).
> NASA SEH (SP-2016-6105 Rev 2) — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).

### Archétypes de mission utilisés dans les études de compromis de la semaine 1

| Archétype | Orbite | Charge utile | Communications | Usage type |
|-----------|-------|---------|-------|-------------|
| Observation de la couleur de l'océan | SSO de 450 – 700 km, ≈ 98° | Imageur multispectral | Bande S | GES, climat, pêcheries |
| Observation de la Terre SAR | SSO de 500 – 700 km | SAR en bande C/X/Ka | Bande X | Maritime, glaces, défense |
| AIS | LEO de 400 – 600 km | Récepteur RF | UHF/VHF | Trafic maritime |
| IoT / relais de données | LEO de 500 – 1100 km | Radio à stockage et retransmission | UHF/Ka | Connectivité, IoT |
| Climat – GES | SSO de 500 km | Spectromètre (ponctuel) | Bande S | Méthane, CO₂ |
| PNT en LEO | MEO/LEO de 500 – 1200 km | Complément GNSS | Bande L | PNT de secours |
| Constellation de communications | LEO de 500 – 1200 km | Antenne réseau à commande de phase | Bande Ka | Haut débit/IoT |

### Travail préparatoire du week-end (lectures à faire la veille)

> **Lectures attendues avant le mardi.** ECSS-M-ST-10C Rev. 1,
> §5 (cycle de vie du management de projet), ≈ 30 min —
> [https://ecss.nl/](https://ecss.nl/). *NASA CubeSat 101*, §3
> (types de missions).

> **Lectures attendues avant le mercredi.** Cal Poly *CubeSat Design
> Specification* Rev 14, §1 – §3 (≈ 45 min) —
> [https://www.cubesat.org/cds-announcement](https://www.cubesat.org/cds-announcement).

> **Lectures attendues avant le vendredi.** Guide de l'utilisateur de
> SpaceCDF, §1 – §3 (≈ 30 min). Apporter une idée de mission tenant
> sur une page le vendredi matin.

---

## Semaine 2 — Centre de conception concourante — concevoir une mission

La semaine 2 est le **stage intensif en CDF**. Chaque équipe
pluridisciplinaire converge vers une conception préliminaire complète
de mission en cinq jours ouvrés, avec l'appui des modules de SpaceCDF
consacrés au processus d'ingénierie système, au registre des risques
et aux études de compromis. La PDR a lieu à la fin de la semaine.

![Chronologie du ConOps — du LEOP à la recette en orbite, aux opérations nominales et au retrait de service](../assets/figures/fig_conops_timeline.png)

*Figure 1.4 — Chronologie représentative d'une mission LEO. La
semaine 2 construit la conception qui suivra cette chronologie en
vol.*

### Emploi du temps quotidien

| Jour | Thème | Activités |
|-----|-------|-----------|
| **Lun.** | **Cycle en V et exigences** | Étude approfondie du cycle en V. Exigences SMART dérivées des objectifs. Décomposition fonctionnelle. Les équipes saisissent le besoin de mission, utilisent les assistants d'orbite et de classe, et établissent le référentiel d'exigences dans SpaceCDF. |
| **Mar.** | **Conception des sous-systèmes : puissance, SCAO, thermique** | Compromis sur le choix de l'orbite. Dimensionnement du générateur solaire et de la batterie. Fonctionnement par intermittence. Choix du contrôle d'attitude. Analyse de l'environnement thermique. Les équipes exécutent la boucle de conception et examinent les bilans paramétriques. |
| **Mer.** | **Conception des sous-systèmes : communications, structure, propulsion** | Calcul du bilan de liaison. Choix de la bande de fréquences et conséquences en matière de licences, au moyen de la vérification réglementaire de SpaceCDF. Structure du CubeSat et choix du déployeur. Compromis sur la propulsion. Choix des équipements dans la bibliothèque de SpaceCDF. |
| **Jeu.** | **Intégration, vérification, coûts** | Examen de la matrice d'interfaces. Affectation de la matrice V&V. Planification des essais d'environnement. Estimation des coûts (paramétrique + COTS). Nomenclature. Études de compromis sur les décisions clés. |
| **Ven.** | **Revue de conception et optimisation** | Lancer l'optimiseur. Analyse de sensibilité. Revue de jalon (critères de la PDR). Résolution des conflits. Génération des documents ECSS (MRD, TS, VP). Dossiers réglementaires (UIT, LSTS le cas échéant). Chaque équipe présente sa conception préliminaire. |

### Premier aperçu des bilans que vous bouclerez

![Répartition de la masse et politique de marges ECSS par phase](../assets/figures/fig_mass_budget.png)

*Figure 1.5 — Bilan de masse et échéancier des marges ECSS. La marge
composée (maturité des équipements × marge système de 20 %) démarre à
+44 % au-dessus de la masse sèche en phase A et se resserre phase après
phase jusqu'à +5 % en phase D.*

![Profil de puissance sur une orbite — production, éclipse, charges empilées](../assets/figures/fig_power_modes.png)

*Figure 1.6 — Profil de production et de consommation de puissance sur
une orbite. C'est l'éclipse qui consomme, inexorablement, la marge de
conception.*

![Bilan de liaison en cascade — liaison descendante en bande S, distance oblique de 1500 km](../assets/figures/fig_link_budget.png)

*Figure 1.7 — Le bilan de liaison en cascade est la manière standard de
présenter une liaison bouclée. Le C/N₀ requis et la marge de liaison
figurent en bas à droite dans toute revue de bilan de liaison.*

### Modèle de registre des risques (mercredi + jeudi)

| ID | Intitulé | P (1–5) | I (1–5) | Score | Responsable | Réduction | État |
|----|-------|--------:|--------:|------:|-------|------------|--------|
| R1 | Défaillance d'une roue de réaction à mi-vie | 4 | 3 | 12 | AOCS | Pyramide redondante de 4 roues ; stratégie de désaturation en vol | Ouvert |
| R2 | Dégradation de la batterie > 20 % | 2 | 4 | 8 | EPS | Modèle de durée de vie en cycles ; point de conception à DoD ≤ 30 % | Ouvert |
| R3 | Éblouissement du senseur stellaire lors du passage à l'équateur | 3 | 2 | 6 | AOCS | Senseur stellaire à deux têtes ; conception du baffle ; loi de pointage | Ouvert |
| R4 | Coupure de la liaison sol au LOS | 3 | 3 | 9 | TT&C | Stations sol redondantes (Iqaluit + Troll) ; recul de puissance du SSPA | Ouvert |
| R5 | Glissement du planning du programme | 4 | 4 | 16 | PM | Marge sur le chemin critique ; approvisionnement anticipé des articles à long délai | Ouvert |
| R6 | SEU d'origine cosmique sur l'OBC | 5 | 1 | 5 | OBDH | Chien de garde + EDAC + programmation N-versions ; contrôle quotidien de la TM | Ouvert |

![Matrice des risques 5×5 avec exemple résolu](../assets/figures/fig_risk_matrix.png)

*Figure 1.8 — La matrice des risques 5×5 de l'ECSS-M-ST-80C. Code
couleur par niveau : 1–2 vert, 3–4 vert clair, 5–9 jaune, 10–15
orange, 16–25 rouge. R5 (planning) se situe dans la bande orange ;
R6 (SEU) est jaune, mais mérite l'attention en raison de la dimension
conséquence.*

> **Lectures attendues avant le mardi de la semaine 2.** SMAD4, chap. 9
> (choix de l'orbite) et chap. 10 (analyse de mission) — disponibles
> localement dans Brightspace. ECSS-E-ST-32C (structures), §4 — [https://ecss.nl/](https://ecss.nl/).

---

## Semaine 3 — Opérations et simulation de mission

La semaine 3 installe la promotion aux postes du contrôle de mission.
Deux jours de formation aux opérations sont suivis de deux jours de
simulation en direct sur le simulateur SpaceCDF / EOSAT-1, au Cyber
Range de l'uOttawa. Voir les documents dédiés à la semaine 3 pour le
programme d'opérations, les procédures et les dossiers de simulation.

| Jour | Thème | Activités |
|-----|-------|-----------|
| **Lun.** | **Élaboration du concept d'opérations** | Architecture du segment sol. Prise en main du MCS (aperçu de COSMOS / OpenMCT / Yamcs). Procédures d'opérations : nominales, de contingence, FDIR. Planification et ordonnancement des passages. Définition des TC/TM à partir de l'export du logiciel de vol de SpaceCDF. |
| **Mar.** | **Formation aux opérations de mission** | Postes de console et responsabilités. Discipline de boucle vocale. Procédures de traitement des anomalies. Répétitions à blanc des scénarios LEOP, nominal et de contingence. Entraînement à l'envoi de télécommandes et à la surveillance de la télémesure. |
| **Mer.** | **Simulation de mission, jour 1** | Journée complète de LEOP et de recette en orbite simulés. Les équipes exploitent à la console la mission qu'elles ont conçue. Déploiement, premier contact, amortissement des vitesses angulaires, vérifications initiales. Injection d'anomalies en temps réel. Débriefing après la simulation et retour d'expérience. |
| **Jeu.** | **Simulation de mission, jour 2** | Journée complète d'opérations nominales et de contingence simulées. Mode d'acquisition des données scientifiques. Liaison descendante lors des passages au-dessus des stations sol. Anomalies injectées : passage en mode survie, anomalie de puissance, dégradation des communications. Opérations de constellation (pour les équipes ayant conçu plusieurs satellites). Débriefing après la simulation. |
| **Ven.** | **Clôture et présentations** | Revue finale de la documentation de conception. Chaque équipe présente sa mission complète : besoin, conception, concept d'opérations, retour d'expérience. Évaluation par les pairs et questions-réponses. Certificat. Évaluation du cours. Discussion : prochaines étapes, possibilités de collaboration, parcours vers l'ASC et l'industrie. |

---

## Évaluation

| Composante | Pondération | Description |
|-----------|-------:|-------------|
| Fiches d'exercices (quotidiennes) | 20 % | Remplies pendant les séances, retours formatifs |
| Revue de conception (vendredi de la semaine 2) | 30 % | Présentation en équipe de la conception préliminaire |
| Performance en simulation (semaine 3) | 20 % | Opérations à la console, traitement des anomalies |
| Présentation finale (vendredi de la semaine 3) | 30 % | Conception complète de la mission, concept d'opérations, retour d'expérience |

### Grille d'autoévaluation des compétences

Utilisez-la en **semaine 0**, puis à nouveau à la fin de la
**semaine 3**. Notez chaque ligne de 1 (aucune exposition) à 5
(capable de diriger une équipe dans ce domaine).

| Compétence | Sem. 0 | Sem. 3 | Δ |
|------------|:----:|:----:|:-:|
| Décrire le secteur spatial canadien et la place qu'on y occupe | | | |
| Identifier et appliquer les obligations réglementaires canadiennes | | | |
| Décomposer les objectifs de la mission en exigences SMART | | | |
| Concevoir une mission au sein d'un CDF (quel que soit le rôle disciplinaire) | | | |
| Tenir un registre des risques et un référentiel de planification | | | |
| Lire et rédiger un fichier de procédure (ECSS-E-ST-70-32C) | | | |
| Exploiter une console du MCS dans le respect de la discipline de boucle vocale | | | |
| Animer une critique structurée entre pairs | | | |
| Transformer le retour d'expérience en actions d'amélioration | | | |

---

## Acquis du cours

À la fin du programme, chaque participant aura :

- mené une conception complète de mission CubeSat, de l'énoncé du
  problème jusqu'à la PDR, au sein d'un centre de conception
  concourante ;
- occupé chacun des six postes du MCS pendant au moins un passage
  au-dessus d'une station sol sur un simulateur en direct ;
- tenu un registre des risques et un référentiel de planification
  pendant toute la semaine de conception ;
- rédigé, exécuté et critiqué au moins une procédure d'opérations ;
- constitué un réseau de pairs dans le monde universitaire, dans
  l'industrie et à l'Agence spatiale canadienne.

---

## Liste de références

Liste à jour, avec liens, des normes, manuels et outils cités dans le
plan de cours.

- **NASA SEH (SP-2016-6105 Rev 2)** — *Systems Engineering Handbook*. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
- **NPR 7123.1D** — *NASA Systems Engineering Processes and Requirements*. [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/)
- **NPR 7120.5F** — *NASA Space Flight Program and Project Management Requirements*. [https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_)
- **NASA CubeSat 101** — *Basic Concepts and Processes for First-Time CubeSat Developers*. [https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf)
- **ECSS-E-ST-10C Rev. 1** — *System engineering general requirements*. [https://ecss.nl/standards/active-standards/ecss-e-st-10c-rev-1-system-engineering-general-requirements/](https://ecss.nl/standards/active-standards/ecss-e-st-10c-rev-1-system-engineering-general-requirements/)
- **ECSS-E-ST-10-02C Rev. 1** — *Verification*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-E-ST-10-24C** — *Interface management*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-M-ST-10C Rev. 1** — *Project planning*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-M-ST-80C** — *Risk management*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-Q-ST-30-02C** — *FMEA / FMECA*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-E-ST-70C** — *Ground systems and operations*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-E-ST-70-32C** — *Test and operations procedures*. [https://ecss.nl/](https://ecss.nl/)
- **Cal Poly CDS Rev 14** — *CubeSat Design Specification*. [https://www.cubesat.org/cds-announcement](https://www.cubesat.org/cds-announcement)
- **CCSDS PUS** — *Packet Utilization Standard*. [https://public.ccsds.org/Pubs/660x0g3.pdf](https://public.ccsds.org/Pubs/660x0g3.pdf)
- **Règlement des radiocommunications de l'UIT-R** — [https://www.itu.int/pub/R-REG-RR](https://www.itu.int/pub/R-REG-RR)
- **ISDE CPC-2-6-02** — *Licensing of space stations*. [https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en](https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en)
- **Loi sur les systèmes de télédétection spatiale** — [https://laws-lois.justice.gc.ca/eng/acts/R-5.4/](https://laws-lois.justice.gc.ca/eng/acts/R-5.4/)
- **Ligne directrice de l'IADC sur l'atténuation des débris (règle des 25 ans)** — [https://www.iadc-home.org/](https://www.iadc-home.org/)
- **Convention sur l'immatriculation (CUPEEA, ONU)** — [https://www.unoosa.org/](https://www.unoosa.org/)
- **Wertz, Everett & Puschell** — *Space Mission Engineering : The New SMAD* (2011).
- **Larson & Wertz** — *Space Mission Analysis and Design*, 4e éd.
- **Sutton & Biblarz** — *Rocket Propulsion Elements*, 9e éd.
- **Markley & Crassidis** — *Fundamentals of Spacecraft Attitude Determination and Control*.
- **Pratt, Bostian & Allnutt** — *Satellite Communications*, 3e éd.
