# Partie I — Fondements et conception

# Chapitre 1 — Conception concourante et cadre de l'ingénierie système

> **Lectures préalables conseillées.** NASA *Systems Engineering Handbook* (SP-2016-6105 Rev 2) §1–§3 — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/) ; NPR 7123.1D §3. Une formation d'ingénieur de premier cycle est supposée acquise ; aucune expérience préalable de la conception d'engins spatiaux n'est requise.

## Objectifs d'apprentissage

À l'issue de ce chapitre, vous serez capable de :

1. Décrire la finalité et la structure d'un centre de conception concourante (CDF) et l'opposer à la conception séquentielle
2. Expliquer le cycle en V et ses deux branches (décomposition et intégration)
3. Énumérer les 17 processus techniques communs définis dans la NPR 7123.1D et expliquer leur application récursive
4. Mettre en correspondance les phases du cycle de vie de la NASA (pré-A à F) avec les phases ECSS et identifier les principaux jalons de revue
5. Identifier le rôle de chaque poste d'ingénierie du CDF et les paramètres dont il est responsable

---

## 1.1 Qu'est-ce qu'un centre de conception concourante ?

### 1.1.1 Le problème de la conception séquentielle

Posons la question : comment conçoit-on traditionnellement un engin spatial ?

La conception traditionnelle d'un engin spatial suit une **approche séquentielle (en cascade)** : une discipline achève son travail, le documente, puis transmet la conception à la discipline suivante. Cette méthode a dominé l'industrie spatiale des années 1960 aux années 1990. Ses limites sont bien documentées :

- **Incohérences d'interface** découvertes tardivement lors de l'intégration, qui imposent une reconception coûteuse
- **Dépassements des bilans** de masse, de puissance et de coût qui ne sont détectés qu'aux revues formelles
- **Cycles d'itération longs** — des mois entre deux revues de conception, avec peu d'échanges entre disciplines
- **Cloisonnement des connaissances** — des justifications de conception essentielles enfermées dans les notes personnelles des ingénieurs
- **Coûts de reprise** — le coût de correction d'une erreur augmente d'environ un ordre de grandeur à chaque phase du cycle de vie (la « règle 1-10-100 »)

La réponse de l'industrie aérospatiale a été l'**ingénierie concourante (CE)**, également appelée développement intégré de produits (IPD) ou ingénierie concourante intégrée (ICE). L'idée centrale : réunir toutes les disciplines pour qu'elles travaillent simultanément sur un modèle paramétrique partagé, en résolvant les conflits en temps réel plutôt qu'en les découvrant en revue.

> **Pratique industrielle.** Les Phantom Works de Boeing ont mis en œuvre l'ingénierie concourante pour le démonstrateur X-32 du programme Joint Strike Fighter à la fin des années 1990, ramenant la durée d'une itération de conception de plusieurs semaines à quelques heures. La Team X du JPL réalise des évaluations rapides de missions depuis 1995 et mène des études de pré-phase A en une semaine seulement. Le CDF de l'ESA, créé en novembre 1998 à l'ESTEC (Noordwijk, Pays-Bas), est devenu le modèle le plus largement reproduit de conception concourante propre au spatial.

### 1.1.2 Le CDF de l'ESA — le modèle de référence

Le centre de conception concourante (*Concurrent Design Facility*) de l'ESA a été le pionnier de cette approche pour les missions spatiales et a été largement reproduit par les agences spatiales du monde entier (DLR, CNES, JAXA, ASC et plus de 60 universités).

| Paramètre | Valeur |
|-----------|-------|
| Création | Novembre 1998, ESTEC, Noordwijk, Pays-Bas |
| Taille de l'équipe | 15–25 spécialistes de domaine par étude |
| Format des séances de conception | Séances de conception ciblées de 3–4 heures, généralement 2 par semaine |
| Durée d'une étude | 3–6 semaines pour une évaluation complète de mission en phase 0/A |
| Outils | À l'origine, l'IDM sous Excel ; aujourd'hui, l'Open Concurrent Design Tool (OCDT) |
| Résultats | Évaluation complète de la faisabilité de la mission : masse, puissance, coût, risque, calendrier |
| Bilan d'activité | Plus de 200 études réalisées au 20e anniversaire (2018) |
| Économies | Études réalisées en env. 1/5 du temps et pour env. 1/3 du coût de l'approche traditionnelle |

[Source : documentation officielle du CDF de l'ESA ; Bandecchi et al., « The ESA/ESTEC Concurrent Design Facility », ESA Bulletin n° 107, 2001]

### 1.1.3 Principes clés de la conception concourante

**Modèle paramétrique partagé.** Toutes les disciplines lisent et écrivent dans un modèle de données commun. Lorsque l'ingénieur puissance modifie la surface du générateur solaire, l'ingénieur structures voit immédiatement l'effet sur la masse, et l'ingénieur thermique voit la modification du facteur de forme du radiateur. Cela élimine le problème du « document d'interface figé ».

**Responsabilité délimitée des paramètres.** Chaque poste d'ingénierie est « propriétaire » d'un ensemble défini de paramètres. Seul l'ingénieur puissance peut modifier les paramètres de l'EPS ; seul l'ingénieur SCAO peut modifier les paramètres de contrôle d'attitude. On évite ainsi les modifications contradictoires tout en conservant un accès concourant.

**Détection des conflits en temps réel.** Lorsque des modifications de paramètres créent des conflits (p. ex. bilan de masse dépassé, marge de liaison négative), le système les signale immédiatement. L'ingénieur système arbitre.

**Convergence de la conception par itération.** Une étude en CDF converge généralement en 3–5 itérations majeures, chaque séance de conception affinant la conception vers son bouclage. Le modèle paramétrique propage automatiquement les modifications, de sorte que l'équipe voit l'effet de chaque décision au niveau du système.

### 1.1.4 La conception concourante dans un logiciel

Le concept de CDF n'exige pas de salle physique. Un outil de conception concourante accessible par le Web peut mettre en œuvre les mêmes principes, de sorte qu'une équipe répartie partage un même modèle en direct. Les exemples numériques de ce manuel ont été produits avec un outil de ce type, SpaceCDF, décrit de manière neutre à l'annexe A ; la correspondance entre les principes du CDF et les fonctions logicielles est résumée ci-dessous.

| Principe | Mise en œuvre logicielle |
|-----------|------------------------|
| Modèle partagé | Synchronisation en temps réel ; tous les participants voient les mises à jour en direct |
| Responsabilité des paramètres | 16 postes d'ingénierie dotés de droits de modification délimités (§1.5) |
| Convergence de la conception | Agents de conception en arrière-plan qui propagent les relations paramétriques (dimensionnement et analyse) |
| Détection des conflits | Moteur de contraintes automatisé portant sur les liens entre paramètres |
| Génération de documents | Exports au format ECSS avec traçabilité complète |
| Jalons de revue | Évaluation automatisée des critères de jalon pour les MCR, SRR, SDR, PDR et CDR (§1.4) |

**Matière à réflexion.** La conception concourante accélère la convergence, mais la vitesse a un prix. Dans quels cas une équipe étroitement couplée pourrait-elle converger *trop* vite — vers une architecture que personne n'a remise en question, ou vers un bilan qui n'a bouclé que parce que chacun a ajusté ses chiffres en même temps ? L'exercice 1 vous demande de mettre ces risques en balance avec les avantages.

---

## 1.2 Le cycle en V

### 1.2.1 Origine et finalité

Le modèle en « V » est le cadre fondateur de l'ingénierie système. Il figure dans le NASA SEH, section 2.3 (figure 2.3-1), dans l'ECSS-E-ST-10C et dans l'ISO/IEC 15288. Ce n'est pas un calendrier de projet — c'est un **modèle logique** qui montre la relation entre la décomposition (découper le problème) et l'intégration (construire et vérifier la solution).

Le cycle en V répond à deux questions fondamentales :

1. **Branche gauche (descendante) :** comment décomposer le besoin de la mission en composants réalisables ?
2. **Branche droite (ascendante) :** comment vérifier que ce qui a été construit satisfait le besoin initial ?

L'idée essentielle est la **traçabilité horizontale** : chaque élément de la branche gauche a une activité de vérification ou de validation correspondante sur la branche droite, reliée au même niveau d'abstraction. La figure 1.1 présente le modèle ; les branches gauche et droite sont détaillées sous forme de tableaux aux §1.2.2 et §1.2.3.

![Cycle en V : décomposition à gauche, intégration et vérification à droite.](../assets/figures/fig_system_v.png)

**Figure 1.1** — Le cycle en V (d'après la figure 2.3-1 du NASA SEH). La branche gauche décompose le besoin de la mission en composants ; la branche droite intègre et vérifie aux niveaux correspondants ; les liens horizontaux représentent la traçabilité entre une exigence et l'activité qui la vérifie.

### 1.2.2 Branche gauche : décomposition descendante

La branche gauche du V répond à la question « comment découper le problème en éléments que l'on sait résoudre ? »

| Niveau | Activité | Question clé | Résultat |
|-------|----------|-------------|--------|
| 1. Besoin de mission | Définir le problème et le concept d'opérations | Quel problème résolvons-nous ? Pour qui ? | ConOps, énoncé du problème, MoE |
| 2. Exigences des parties prenantes | Recueillir les besoins de toutes les parties prenantes | Que doit accomplir le système ? (le QUOI, pas le COMMENT) | Référentiel des exigences des parties prenantes |
| 3. Architecture système | Définir les segments, les éléments et les interfaces | Comment le système est-il structuré ? | Architecture système, ICD |
| 4. Conception des sous-systèmes | Concevoir chaque sous-système pour satisfaire les exigences allouées | Comment chaque sous-système fonctionne-t-il ? | Spécifications des sous-systèmes |
| 5. Choix des composants | Choisir ou concevoir les composants du niveau le plus bas | Quel matériel ou logiciel répond à chaque besoin ? | Spécifications des composants, nomenclature (BoM) |

### 1.2.3 Branche droite : intégration ascendante

La branche droite répond à la question « comment vérifier que ce qui a été construit satisfait le besoin initial ? »

| Niveau | Activité | Question clé | Méthode de vérification |
|-------|----------|-------------|-------------------|
| 5. Vérification des composants | Soumettre chaque composant à des essais par rapport à sa spécification | Chaque pièce fonctionne-t-elle ? | Inspection, essai |
| 4. Vérification des sous-systèmes | Intégrer chaque sous-système et le soumettre à des essais | Les sous-systèmes satisfont-ils les exigences allouées ? | Essai, analyse |
| 3. Intégration et essais | Assembler le système et tester les interfaces | Les sous-systèmes fonctionnent-ils ensemble ? | Essai, démonstration |
| 2. Vérification du système | Vérifier le système par rapport aux exigences | Le système satisfait-il toutes les exigences ? | Essai, analyse, inspection, démonstration |
| 1. Validation de la mission | Valider par rapport au besoin initial | Résout-il le problème initial ? | Exploitation, recette par l'utilisateur |

### 1.2.4 Traçabilité horizontale

Les liens horizontaux de la figure 1.1 représentent la **traçabilité horizontale** — le principe selon lequel chaque élément de la branche gauche doit avoir une activité de vérification ou de validation correspondante sur la branche droite :

- Chaque **exigence** (à gauche) a une **méthode de vérification** (à droite) : analyse, essai, inspection ou revue de conception, plus la démonstration qu'ajoute la pratique de la NASA — abrégées ATIR(D) dans tout ce manuel (le chapitre 14 traite ces méthodes en détail)
- Chaque **décision de conception** (à gauche) a un **essai ou une analyse** (à droite) qui confirme qu'elle fonctionne
- Cette traçabilité est consignée dans la **matrice de vérification des exigences (RVM)**

> **Équation clé.** L'indicateur de complétude de la traçabilité est
>
> $$T_c = \frac{N_{\text{verified}}}{N_{\text{total requirements}}} \times 100\%$$
>
> Une cible de $T_c = 100\%$ est exigée à la CDR. À la PDR, une valeur $T_c \geq 90\%$ est courante.

**Idée essentielle :** le V n'est pas une chronologie — c'est une *table de correspondance*. La branche gauche pose la question « que faut-il faire ? » à des niveaux de détail croissants. La branche droite pose la question « l'avons-nous fait ? » aux niveaux correspondants. Chaque ligne horizontale forme une paire.

### 1.2.5 Correspondance des phases avec le V

Bien que le V ne soit pas un calendrier, chacun de ses niveaux est traité principalement au cours de certaines phases du cycle de vie (les phases elles-mêmes sont définies au §1.4). La correspondance est donnée dans le tableau 1.1.

**Tableau 1.1** — Correspondance entre les niveaux du cycle en V et les phases du cycle de vie de la NASA.

| Niveau du V | Branche gauche (décomposition) | Branche droite (vérification) | Phase NASA |
|---------|---------------------------|---------------------------|------------|
| Sommet | Besoins et objectifs des parties prenantes | Validation opérationnelle (la mission apporte-t-elle de la valeur ?) | Pré-A / E |
| Mission | Exigences de niveau mission | V&V de niveau mission (recette en orbite, vérification en orbite) | A / E |
| Système | Exigences de niveau système | Intégration et essais du système (de bout en bout) | B / D |
| Sous-système | Exigences des sous-systèmes | Essais de qualification et de recette des sous-systèmes | C / D |
| Base | Réalisation (conception détaillée, fabrication) | Recette des composants | C–D |

### 1.2.6 Exemple de mission réelle : Planet SuperDove

La constellation SuperDove de Planet (de 2020 à aujourd'hui) illustre le cycle en V dans la pratique commerciale :

| Niveau | Exigence (gauche) | Vérification (droite) |
|-------|-------------------|---------------------|
| Parties prenantes | « Couverture mondiale quotidienne à < 5 m pour l'analyse agricole » | Validation en orbite : cartes de couverture, retours des utilisateurs |
| Mission | « Revisite ≤ 1 jour entre ±60° de latitude » | Confirmée par simulation de la couverture de la constellation |
| Système | « GSD ≤ 3,7 m depuis une SSO à 475 km » | Essai d'imagerie de bout en bout depuis l'orbite |
| Sous-système | « Ouverture du télescope ≥ 90 mm, 8 bandes spectrales » | Étalonnage de l'instrument au sol et en orbite |

*[Source : Planet Labs, « Planet Imagery Product Specifications », 2023]*

### 1.2.7 Itération et moteur d'ingénierie système

Le V ne se parcourt pas en une seule passe. Une conception réelle itère — les exigences évoluent à mesure que des contraintes de conception apparaissent, et les paramètres de conception rétroagissent pour affiner les exigences. Cette boucle itérative est formalisée par le concept de **« moteur d'ingénierie système »** (*SE engine*, NASA SEH, section 2.1) : les 17 processus techniques communs appliqués de manière récursive à chaque niveau de l'arborescence produit. Ces processus font l'objet du §1.3.

[Source : NASA SEH, section 2.3, figure 2.3-1 ; INCOSE *Systems Engineering Handbook*, 4e édition, section 3.2]

---

## 1.3 Les 17 processus techniques communs

### 1.3.1 Vue d'ensemble

La NPR 7123.1D de la NASA définit 17 processus qui s'appliquent de manière récursive à chaque niveau de l'arborescence produit. Ils sont regroupés en trois catégories, désignées collectivement sous le nom de **« moteur d'ingénierie système »** (*SE engine*). Ces processus ne sont pas séquentiels — ils s'exécutent de façon concourante et itérative, ce que précisément un CDF facilite. La figure 1.2 présente les trois groupes sous forme de pyramide ; les sous-sections suivantes détaillent chaque processus sous forme de tableau.

![Les 17 processus techniques communs du NASA SEH, regroupés en conception du système, réalisation du produit et management technique.](../assets/figures/fig_seh_processes.png)

**Figure 1.2** — Les 17 processus techniques communs de la NPR 7123.1D, regroupés en conception du système (1–4), réalisation du produit (5–9) et management technique (10–17).

[Source : NPR 7123.1D, chapitre 3 ; NASA SEH, section 2.1, figure 2.1-1]

### 1.3.2 Processus de conception du système (1–4)

Ces processus transforment le problème en solution par décomposition. Ils correspondent à la branche gauche du cycle en V.

| N° | Processus | Activité principale | Résultat principal | Référence NASA SEH |
|---|---------|-------------|------------|-------------------|
| 1 | **Définition des attentes des parties prenantes** | Recueillir les besoins, définir le ConOps, établir les MoE | Référentiel des exigences des parties prenantes | Section 4.1 |
| 2 | **Définition des exigences techniques** | Rédiger les énoncés en « doit », définir les MoP et les TPM | Référentiel des exigences techniques | Section 4.2 |
| 3 | **Décomposition logique** | Analyse fonctionnelle, modélisation comportementale, exigences dérivées | Architecture fonctionnelle | Section 4.3 |
| 4 | **Définition de la solution de conception** | Études de compromis, choix entre solutions alternatives, élaboration de la conception de référence | Référentiel de la solution de conception | Section 4.4 |

### 1.3.3 Processus de réalisation du produit (5–9)

Ces processus construisent, vérifient et livrent la solution. Ils correspondent à la branche droite du cycle en V.

| N° | Processus | Activité principale | Résultat principal | Référence NASA SEH |
|---|---------|-------------|------------|-------------------|
| 5 | **Mise en œuvre du produit** | Fabriquer, acheter, coder ou réutiliser les produits du niveau le plus bas | Produits matériels et logiciels | Section 5.1 |
| 6 | **Intégration du produit** | Assembler selon le plan d'intégration, vérifier les interfaces | Système intégré | Section 5.2 |
| 7 | **Vérification du produit** | Confirmer que le produit satisfait les exigences techniques (ATIR(D)) | Preuves de vérification | Section 5.3 |
| 8 | **Validation du produit** | Confirmer que le produit répond aux attentes des parties prenantes | Preuves de validation | Section 5.4 |
| 9 | **Transition du produit** | Livrer, déployer, transférer à l'exploitation | Système opérationnel | Section 5.5 |

### 1.3.4 Processus de management technique (10–17)

Ces processus pilotent le travail d'ingénierie et s'appliquent tout au long du cycle de vie.

| N° | Processus | Activité principale | Document de référence |
|---|---------|-------------|-------------------|
| 10 | **Planification technique** | SEMP, plans subsidiaires, WBS | NPR 7123.1D, section 3.10 |
| 11 | **Gestion des exigences** | Mise en référentiel, traçabilité, maîtrise des modifications | NPR 7123.1D, section 3.11 |
| 12 | **Gestion des interfaces** | ICD, IRD, interfaces internes et externes | NPR 7123.1D, section 3.12 |
| 13 | **Gestion des risques techniques** | Identification, évaluation, réduction selon la NPR 8000.4 | NPR 8000.4B |
| 14 | **Gestion de configuration** | Référentiels, plan de gestion de configuration, CCB | NPR 7120.5F, chapitre 4 |
| 15 | **Gestion des données techniques** | Droits sur les données, conservation, diffusion | NPR 7123.1D, section 3.15 |
| 16 | **Évaluation technique** | TPM, revues, EVM, bilans de santé | NPR 7123.1D, section 3.16 |
| 17 | **Analyse de décision** | Choix structuré entre solutions alternatives (études de compromis) | NASA SEH, section 6.8 |

### 1.3.5 Récursivité dans l'arborescence produit

Une propriété essentielle des 17 processus est qu'ils s'appliquent de manière **récursive** à chaque niveau de l'arborescence produit, comme l'illustre la figure 1.3.

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 420" style="max-width:760px; font-family: sans-serif;">
  <defs>
    <marker id="recArrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6" fill="#1f4e79"/>
    </marker>
  </defs>
  <!-- Nested levels -->
  <rect x="20" y="20" width="720" height="380" rx="14" fill="none" stroke="#1f4e79" stroke-width="2"/>
  <text x="40" y="46" font-size="14" font-weight="bold" fill="#1f4e79">Niveau mission</text>
  <text x="40" y="64" font-size="11" fill="#444">exigences de mission · ConOps · validation</text>

  <rect x="60" y="80" width="640" height="300" rx="12" fill="none" stroke="#2e6da4" stroke-width="2"/>
  <text x="80" y="106" font-size="14" font-weight="bold" fill="#2e6da4">Niveau système</text>
  <text x="80" y="124" font-size="11" fill="#444">exigences système · architecture · vérification</text>

  <rect x="100" y="140" width="560" height="220" rx="10" fill="none" stroke="#4a8fcf" stroke-width="2"/>
  <text x="120" y="166" font-size="14" font-weight="bold" fill="#4a8fcf">Niveau sous-système</text>
  <text x="120" y="184" font-size="11" fill="#444">exigences des sous-systèmes · conception · essais</text>

  <rect x="140" y="200" width="480" height="140" rx="8" fill="none" stroke="#7fb3e6" stroke-width="2"/>
  <text x="160" y="226" font-size="14" font-weight="bold" fill="#4a8fcf">Niveau composant</text>
  <text x="160" y="244" font-size="11" fill="#444">spécifications des composants · approvisionnement · recette</text>

  <!-- Central recursive cycle -->
  <path d="M 430 300 a 40 40 0 1 1 -0.1 -0.1" fill="none" stroke="#1f4e79" stroke-width="3" marker-end="url(#recArrow)"/>
  <text x="430" y="304" text-anchor="middle" font-size="11" font-weight="bold" fill="#1f4e79">17 processus</text>
  <text x="430" y="318" text-anchor="middle" font-size="11" font-weight="bold" fill="#1f4e79">d'IS</text>

  <!-- Side annotation -->
  <text x="520" y="280" font-size="11" fill="#444">mêmes processus,</text>
  <text x="520" y="296" font-size="11" fill="#444">périmètre, détail</text>
  <text x="520" y="312" font-size="11" fill="#444">et durée propres à chaque niveau</text>
</svg>

**Figure 1.3** — Récursivité du moteur d'ingénierie système. Les 17 mêmes processus s'exécutent aux niveaux mission, système, sous-système et composant, chacun avec son propre référentiel d'exigences, sa conception et ses preuves de vérification.

À chaque niveau, les mêmes processus s'exécutent, mais avec un périmètre, un niveau de détail et une durée différents. Dans un environnement de CDF, plusieurs niveaux sont souvent traités de façon concourante — l'ingénieur système pilote les niveaux mission et système tandis que les ingénieurs sous-systèmes travaillent chacun dans leur domaine.

> **Pratique industrielle.** Sur le télescope spatial James Webb (JWST), la gestion des exigences (processus 11) a été appliquée simultanément à cinq niveaux de l'arborescence produit : l'observatoire, l'élément télescope optique (OTE), le module intégré des instruments scientifiques (ISIM), chacun des instruments (NIRSpec, MIRI, NIRCam, FGS) et les composants (détecteurs, mécanismes). Chaque niveau disposait de son propre référentiel d'exigences, de sa matrice de traçabilité et de son plan de vérification. Le nombre total d'exigences dépassait 10 000.

---

## 1.4 Phases du cycle de vie et jalons de revue

### 1.4.1 Phases du cycle de vie de la NASA

La NASA définit sept phases du cycle de vie pour les projets de vol spatial, régies par la NPR 7120.5F. Chaque phase a des objectifs, des activités et des critères de sortie propres, évalués lors de jalons de revue formels appelés points de décision clés (KDP). La figure 1.4 présente les phases et les jalons de revue qui les séparent ; le tableau 1.2 détaille chaque phase.

![Phases du cycle de vie, de la pré-phase A à la phase F, et jalons de revue qui les séparent.](../assets/figures/fig_lifecycle.png)

**Figure 1.4** — Cycle de vie d'un projet de vol spatial de la NASA (NPR 7120.5F) : phases pré-A à F et jalons de revue qui les séparent. Les études de conception concourante du type décrit dans ce manuel couvrent la pré-phase A jusqu'à la phase C.

[Source : NPR 7120.5F, chapitre 2 ; NASA SEH, chapitre 3]

### 1.4.2 Détail des phases

**Tableau 1.2** — Phases du cycle de vie de la NASA, revues de sortie et résultats principaux.

| Phase | Nom | Activité principale | Revue de sortie | Résultats principaux |
|-------|------|-----------------|-------------|-------------|
| **Pré-A** | Études de concept | Identifier le besoin, explorer la faisabilité, élaborer le ConOps | MCR | Concept de mission, ConOps préliminaire, évaluation de faisabilité |
| **A** | Développement du concept et des technologies | Élaborer les exigences, faire mûrir les technologies jusqu'à TRL 4+ | SRR/SDR | Référentiel d'exigences, plan de développement technologique |
| **B** | Conception préliminaire et achèvement des technologies | Conception préliminaire, bouclage des bilans préliminaires, TRL 6+ | PDR | Conception préliminaire, allocations des bilans, plans d'essais |
| **C** | Conception finale et fabrication | Conception détaillée, fabrication du matériel, TRL 8 | CDR | Plans détaillés, documentation tel que construit, matériel de vol |
| **D** | Assemblage, intégration et essais, lancement | AIT du système, essais d'environnement, lancement | TRR, QR, ORR, FRR | Système de vol éprouvé, aptitude au lancement |
| **E** | Exploitation et maintien | Exploiter la mission, produire les produits de données | PLAR | Données scientifiques, retour d'expérience opérationnel |
| **F** | Clôture | Mise hors service, passivation, retrait de service, retour d'expérience | DR | Confirmation du retrait de service, rapport final |

**Points de décision clés (KDP) :** il s'agit des décisions GO/NO-GO de l'autorité entre les phases, désignées par les lettres A à F. Ils se distinguent des revues techniques — les KDP sont des décisions de direction éclairées par les conclusions des revues techniques. Pour les projets dépassant 250 M$ (USD), le KDP-C exige une analyse de niveau de confiance conjoint (JCL) conformément à la NPR 7120.5F.

### 1.4.3 Phases du cycle de vie ECSS

Les normes ECSS définissent un cycle de vie similaire mais non identique. Les lettres des phases coïncident commodément, mais les critères d'entrée et de sortie ainsi que le contenu des revues diffèrent.

[Source : ECSS-M-ST-10C Rev.1, section 5.3]

| Phase ECSS | Nom | Équivalent NASA | Différence principale |
|-----------|------|----------------|----------------|
| 0 | Analyse de mission / identification des besoins | Pré-A | La phase 0 ECSS comprend une analyse de mission formelle |
| A | Faisabilité | A | La phase A ECSS est centrée sur la démonstration de la faisabilité |
| B | Définition préliminaire (B1/B2) | B | L'ECSS la scinde en B1 (système) et B2 (détaillée) |
| C | Définition détaillée | C | Périmètre similaire |
| D | Qualification et production | D | La phase D ECSS met l'accent sur les modèles de qualification |
| E | Exploitation | E | Périmètre similaire |
| F | Retrait de service | F | La phase F ECSS traite explicitement de la passivation |

### 1.4.4 Jalons de revue — ce que chacun vérifie

Le tableau 1.3 constitue la liste de référence des jalons de revue utilisée dans tout ce manuel. Le chapitre 16 donne les critères d'entrée et de sortie détaillés de chaque jalon et explique comment présenter une conception devant un comité de revue.

**Tableau 1.3** — Jalons de revue, question à laquelle chacun répond et preuves exigées.

| Revue | Nom complet | Transition de phase | Question clé | Preuves exigées |
|--------|-----------|------------------|-------------|-------------------|
| **MCR** | Revue du concept de mission | Pré-A → A | Le besoin de la mission est-il justifié ? L'espace est-il la bonne réponse ? | Énoncé du problème, analyse des parties prenantes, analyse des solutions alternatives, projet de ConOps |
| **SRR** | Revue des exigences système | A | Les exigences sont-elles complètes, cohérentes, traçables et vérifiables ? | Référentiel d'exigences, matrice de traçabilité, registre des risques, ConOps préliminaire |
| **SDR** | Revue de définition du système | A → B | L'architecture du système satisfait-elle les exigences ? | Architecture système, décomposition fonctionnelle, définitions des interfaces |
| **PDR** | Revue de définition préliminaire | B → C | La conception préliminaire satisfait-elle toutes les exigences ? | Description de la conception, état des bilans (masse/puissance/coût), plans de réduction des risques |
| **CDR** | Revue de définition critique | C → D | La conception est-elle complète et prête pour la fabrication ? | Plans détaillés, résultats d'analyses, plans d'essais, tous les bilans bouclés avec des marges positives |
| **TRR** | Revue d'aptitude aux essais | D | Le système est-il prêt pour les essais formels ? | Procédures d'essai, disponibilité des moyens d'essai, critères de recette |
| **QR** | Revue de qualification | D | Le programme de qualification a-t-il démontré que la conception satisfait ses exigences avec marge ? | Résultats des essais de qualification, clôture des non-conformités, dérogations, référentiel tel que qualifié |
| **FRR** | Revue d'aptitude au vol | D → E | Tout est-il prêt pour le lancement ? | Tous les essais réussis, dérogations documentées, procédures de lancement vérifiées |

> **Pratique industrielle.** RADARSAT-2 (MDA/ASC, lancé en 2007) est passé par tous les jalons de revue équivalents à ceux de la NASA au cours d'un développement de 6 ans. La CDR à elle seule a mobilisé plus de 400 points de revue et 50 relecteurs pendant 3 semaines. La mission a dépassé sa durée de vie nominale de 7 ans et a fonctionné pendant plus de 15 ans — preuve d'une vérification rigoureuse à chaque jalon.

---

## 1.5 Postes d'ingénierie du CDF

### 1.5.1 Vue d'ensemble des postes

Dans une étude en CDF, chaque poste d'ingénierie est responsable d'un ensemble de paramètres et des décisions de conception de son domaine. Le tableau 1.4 énumère les 16 postes utilisés dans tout ce manuel. La partie IV présente une fiche complète pour chaque poste — les décisions qui lui reviennent, les équations qu'il utilise et les écueils auxquels il doit prendre garde.

**Tableau 1.4** — Les 16 postes d'ingénierie du CDF, leurs responsabilités et les paramètres dont ils sont responsables.

| Poste | Responsabilité | Principaux paramètres détenus | Interfaces principales |
|----------|---------------|---------------------|-------------------|
| **Ingénieur système** | Architecture d'ensemble, bilans, marges, résolution des conflits | Marge de masse, marge de puissance, bilans au niveau système | Tous les postes |
| **Chef de projet** | Calendrier, autorité budgétaire, propriétaire des risques ; préside la séance de conception | Calendrier, plafond de coût, registre des risques, décisions aux jalons de revue | Ingénieur système, coûts, tous les postes |
| **Analyste de mission** | Conception de l'orbite, analyse de couverture, accès aux stations sol | Altitude, inclinaison, RAAN, fraction d'éclipse, durée de contact | Télécommunications, charge utile, sol |
| **Responsable charge utile** | Performances de l'instrument, débits de production de données | GSD, bandes spectrales, débit, champ de vue (FOV), RSB | Analyste de mission, puissance, SCAO, télécommunications |
| **Ingénieur puissance** | Générateurs solaires, batteries, architecture de l'EPS, fonctionnement par intermittence | Surface du générateur solaire, capacité de la batterie, tension du bus, DoD | Tous (la puissance est une contrainte universelle) |
| **Ingénieur SCAO** | Capteurs d'attitude, actionneurs, modes de pointage | Précision de pointage, vitesse de basculement, moment cinétique des roues, jeu de capteurs | Charge utile, structures, propulsion |
| **Ingénieur thermique** | Contrôle de température, radiateurs, réchauffeurs, revêtements | Températures max./min., surface des radiateurs, puissance des réchauffeurs, marge thermique | Structures, puissance, charge utile |
| **Ingénieur télécommunications** | Bilan de liaison, transpondeur, antenne, attribution de licences de spectre | Marge de liaison, débit, bande de fréquences, PIRE, G/T | Analyste de mission, charge utile, sol |
| **Ingénieur propulsion** | Bilan de Δv, choix des propulseurs, masse d'ergols | Isp, masse d'ergols, impulsion totale, vecteur de poussée | Analyste de mission, SCAO, structures |
| **Ingénieur structures** | Structure primaire, mécanismes, charges au lancement | Masse de la structure, fréquence propre, marge de sécurité | Tous (la masse est une contrainte universelle) |
| **Ingénieur coûts** | WBS, relations d'estimation de coût, planning | Coût total, coût par sous-système, coût de lancement, coût ajusté du risque | Ingénieur système, tous les sous-systèmes |
| **Ingénieur conformité** | Normes, licences de fréquences, contrôle des exportations | Applicabilité des normes, statut ITAR/EAR, état des notifications | Tous |
| **Représentant des utilisateurs** | Besoins des utilisateurs finaux, exigences sur les produits de données | Format des données, latence, accessibilité, couverture | Charge utile, télécommunications, sol |
| **Opérations de mission** | Concept des opérations sol, effectifs, automatisation | Planning des contacts, niveau d'automatisation, procédures d'anomalie | Télécommunications, sol, système |
| **Segment sol** | Stations sol, chaîne de traitement des données | Réseau de stations, latence de traitement, capacité d'archivage | Télécommunications, opérations de mission, représentant des utilisateurs |
| **Ingénieur logiciel** | Logiciel de vol, FDIR, interfaces TC/TM | Architecture du logiciel de vol, dictionnaire de commandes, règles FDIR | OBC, SCAO, télécommunications, charge utile |

### 1.5.2 Conflits d'interface

Les séances de conception en CDF les plus productives sont celles où des **conflits d'interface** sont identifiés et résolus. Schémas de conflit courants :

| Conflit | Postes concernés | Démarche de résolution |
|----------|--------------------|-------------------|
| Bilan de masse dépassé | Système, structures, tous les sous-systèmes | Réallouer les marges, réduire le périmètre de la charge utile, choisir des composants plus légers |
| Bilan de puissance dépassé | Système, puissance, charge utile, télécommunications | Ajuster les rapports cycliques, augmenter la surface du générateur solaire, réduire la puissance de la charge utile |
| Exigence de pointage vs capacité des actionneurs | Charge utile, SCAO, structures | Assouplir l'exigence de pointage, ajouter un miroir de pointage fin, améliorer l'isolation |
| Capacité de liaison descendante vs production de données | Télécommunications, charge utile, sol | Ajouter des stations sol, augmenter la puissance d'émission, réduire le débit, ajouter une compression |
| Contrainte de volume vs évacuation thermique | Structures, thermique, charge utile | Repenser l'emplacement des radiateurs, ajouter un radiateur déployable, réduire la dissipation thermique |

---

## 1.6 Conduire le cycle de vie dans une étude de conception concourante

Une étude de conception concourante ne remplace pas le cycle de vie du §1.4 ; elle en comprime la première partie. Une étude type de phase 0/A conduit la mission d'un besoin exprimé jusqu'à un concept convergé dont les bilans de masse, de puissance, de liaison et de coût sont bouclés — les preuves exigées à la MCR et à la SRR dans le tableau 1.3 —, et une étude de phase B bien menée prolonge le même modèle jusqu'aux preuves exigées à la PDR. Les chapitres suivants sont organisés dans l'ordre où une équipe de conception concourante rencontre le travail :

- **Les chapitres 2 et 3** posent le contexte réglementaire et normatif dans lequel chaque décision de conception doit s'inscrire.
- **Les chapitres 4 à 8** parcourent la branche gauche du V, du besoin de la mission (chapitre 4) aux exigences (chapitre 5), à la décomposition fonctionnelle (chapitre 6), au choix de l'orbite (chapitre 7) et à l'architecture de mission avec ses bilans techniques (chapitre 8).
- **Les chapitres 9 à 12** dimensionnent les sous-systèmes — puissance et thermique, contrôle d'attitude, télécommunications, ainsi que structures, propulsion et gestion des données.
- **Les chapitres 13 à 19** traitent du choix des équipements, de la vérification et de la validation, des risques et des interfaces, des coûts et des revues, ainsi que des segments sol et opérations qui complètent la branche droite du V.

Chaque chapitre indique lesquels des 17 processus il met en œuvre et à quel jalon de revue ses résultats contribuent.

---

## 1.7 Les exemples fil rouge

Deux engins spatiaux servent d'exemples fil rouge tout au long de ce manuel. L'exemple principal est un **CubeSat 3U d'observation de la Terre (OT)** — un imageur multispectral destiné au suivi agricole, dimensionné en détail à partir du chapitre 4. À ses côtés, nous utilisons un second engin, volontairement plus simple : **UniSat-1**, un démonstrateur technologique CubeSat 1U conçu par une équipe universitaire. Il s'agit de la conception d'engin spatial réaliste la plus simple qui soit.

**Mission :** démontrer un magnétomètre innovant à base de MEMS pour la surveillance de la météorologie de l'espace depuis l'orbite basse (LEO).

**Pourquoi un 1U ?** Le format 1U (100 × 100 × 113,5 mm, jusqu'à 1,33 kg) est le plus petit CubeSat standard et le point d'entrée de nombreuses missions universitaires et éducatives. Il impose une discipline de conception extrême — chaque gramme, chaque milliwatt et chaque centimètre cube comptent.

| Paramètre | Valeur |
|-----------|-------|
| Format | 1U (100 × 100 × 113,5 mm) |
| Masse maximale | 1,33 kg (CDS Rev 14) |
| Masse visée | 1,0 kg |
| Orbite | Circulaire à 400 km, 51,6° (lancement partagé ISS) |
| Durée de vie nominale | 6 mois |
| Charge utile | Magnétomètre MEMS (50 g, 0,2 W, < 1 kbit/s) |
| Télécommunications | UHF 437 MHz, 9600 bit/s |
| Puissance | Env. 2 W en moyenne sur l'orbite (cellules solaires fixées sur la structure) |
| SCAO | Magnétique passif (aimant permanent + barreaux d'hystérésis) |
| Propulsion | Aucune (désorbitation naturelle en env. 1 an) |
| Coût estimé | 50–200 k€ (indicatif, 2026) |
| Durée de développement | 6–12 mois |

UniSat-1 montre qu'une mission spatiale utile peut être réalisée avec seulement cinq sous-systèmes (EPS, OBC, télécommunications, structure, charge utile), sans contrôle d'attitude actif, sans propulsion et sans matériel thermique autre que des revêtements de surface. Au fil du manuel, chaque chapitre montrera comment les mêmes processus de conception s'appliquent à UniSat-1, mais avec des solutions radicalement plus simples à chaque étape. Les chapitres suivants y reviennent dans une section intitulée « Retour sur UniSat-1 ».

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| CDF | La conception concourante multidisciplinaire résout les conflits en temps réel ; c'est un modèle paramétrique partagé, avec une responsabilité délimitée des paramètres, qui le permet |
| Cycle en V | La branche gauche décompose (du besoin aux composants) ; la branche droite intègre (construire pour valider) ; la traçabilité horizontale les relie |
| 17 processus | Récursifs à chaque niveau du système ; regroupés en conception (1–4), réalisation (5–9) et management (10–17) |
| Phases du cycle de vie | De la pré-phase A à la phase F, avec des jalons KDP ; les phases ECSS s'alignent approximativement ; les études de conception concourante couvrent la pré-phase A jusqu'à la phase C |
| Jalons de revue | Chaque jalon répond à une question précise à l'aide de preuves exigées (tableau 1.3) ; les critères de jalon peuvent être évalués automatiquement lorsque les preuves sont numériques |
| Postes | Chacun est responsable d'un domaine de paramètres ; les conflits naissent aux interfaces ; l'ingénieur système arbitre |
| Exemples fil rouge | Un CubeSat 3U d'OT et UniSat-1, un démonstrateur 1U de magnétomètre, sont suivis dans chaque chapitre |

---

## Exercices

1. **Conception concourante ou séquentielle.** Citez trois avantages de la conception concourante par rapport à la conception séquentielle (en cascade), et trois risques qu'elle introduit (pensez, par exemple, à la pensée de groupe et à la convergence prématurée). Pour chaque risque, proposez une pratique qu'un ingénieur système pourrait adopter pour le réduire.

2. **Esquisser le V.** Dessinez le cycle en V de mémoire et nommez chacun de ses cinq niveaux sur les deux branches. Ajoutez les liens de traçabilité horizontale et indiquez, pour chaque niveau, une méthode de vérification appropriée (parmi ATIR(D)).

3. **Coût d'une modification tardive.** En vous appuyant sur la « règle 1-10-100 » du §1.1.1, une incohérence d'interface dont la correction coûterait 2 k€ en phase A est découverte lors des essais d'environnement en phase D. Estimez le coût de sa correction, en précisant vos hypothèses sur le nombre de changements de phase que l'erreur a franchis. Qu'en déduisez-vous sur la valeur d'une étude de conception concourante de phase A dont le coût représente environ 1/3 de celui d'une étude classique ?

4. **Le moteur d'ingénierie système et le logiciel.** Pour chacun des 17 processus techniques communs du §1.3, indiquez si un outil de conception concourante ou un tableur peut le prendre en charge *directement* (en calculant ou en vérifiant quelque chose), *indirectement* (en consignant le résultat d'un jugement humain) ou *pas du tout*. Quels processus exigent le plus de jugement humain, et pourquoi ?

5. **Automatiser un jalon.** La MCR exige les preuves énumérées dans le tableau 1.3. Classez chaque élément de preuve comme (a) un élément pouvant être évalué automatiquement à partir d'un modèle paramétrique (p. ex. un bilan qui boucle avec une marge positive) ou (b) un élément qui exige l'examen d'un ingénieur. Pour un élément de la catégorie (b), rédigez la question à laquelle un examinateur devrait répondre.

6. **Complétude de la traçabilité.** Un projet de CubeSat 3U d'OT compte 48 exigences, dont 41 ont une méthode de vérification attribuée et réalisée. Calculez la complétude de la traçabilité $T_c$. Le projet est-il prêt pour la PDR selon la règle empirique du §1.2.4 ? Combien d'exigences supplémentaires doivent être vérifiées avant la CDR ?

7. **Identification des phases.** Pour chacune des activités suivantes, indiquez la phase du cycle de vie de la NASA au cours de laquelle elle se déroule principalement et le jalon de revue auquel ses preuves contribuent : (a) un essai de vide thermique du modèle de vol ; (b) une étude de compromis entre une orbite héliosynchrone à 500 km et une autre à 600 km ; (c) la passivation de la batterie en fin de vie ; (d) le bouclage du bilan de masse avec une marge système de 15 % ; (e) la rédaction de la première version du ConOps ; (f) la diffusion des plans de fabrication détaillés.

8. **Interactions entre postes.** Pour un CubeSat 3U d'OT doté d'un imageur multispectral, d'une liaison descendante en bande S et d'un contrôle d'attitude trois axes, identifiez les trois paires de postes du tableau 1.4 qui, selon vous, interagiront le plus souvent, et expliquez le paramètre que se disputent les deux postes de chaque paire. Où prévoyez-vous le compromis le plus difficile, et pourquoi ?

9. **Les postes d'une petite équipe.** Retour sur UniSat-1, qui ne compte que cinq sous-systèmes et n'a ni contrôle d'attitude actif ni propulsion : lesquels des 16 postes restent nécessaires, lesquels peuvent être regroupés et lesquels sont inutiles ? Proposez une équipe de cinq personnes et répartissez les postes entre elles. Comment le processus de CDF change-t-il lorsque l'équipe est aussi réduite ?

10. **Un tableau du cycle en V pour UniSat-1.** Sur le modèle de l'exemple SuperDove du §1.2.6, rédigez pour UniSat-1 un tableau de quatre lignes (parties prenantes, mission, système, sous-système) donnant une exigence sur la branche gauche et l'activité de vérification correspondante sur la branche droite. Utilisez les paramètres du §1.7.

---

## Références

1. NASA, *Systems Engineering Handbook* (SP-2016-6105 Rev 2), 2016. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
2. NASA, *NPR 7123.1D — Systems Engineering Processes and Requirements*, 2020. [https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_)
3. NASA, *NPR 7120.5F — NASA Space Flight Program and Project Management Requirements*, 2021. [https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_)
4. ECSS, *ECSS-M-ST-10C Rev.1 — Space Project Management*, 2009. [https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/](https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/)
5. INCOSE, *Systems Engineering Handbook*, 4e édition, 2015. [https://www.incose.org/products-and-publications/se-handbook](https://www.incose.org/products-and-publications/se-handbook)
6. Bandecchi, M. et al., « The ESA/ESTEC Concurrent Design Facility », *ESA Bulletin* n° 107, 2001. [https://www.esa.int/esapub/bulletin/bullet107/bul107_2.pdf](https://www.esa.int/esapub/bulletin/bullet107/bul107_2.pdf)
7. ESA, « 20 Years of Concurrent Design at ESA », 2018. [https://www.esa.int/Enabling_Support/Space_Engineering_Technology/CDF/What_is_the_CDF](https://www.esa.int/Enabling_Support/Space_Engineering_Technology/CDF/What_is_the_CDF)
8. Wertz, J.R. et al., *Space Mission Engineering : The New SMAD* (SMAD4), Microcosm Press, 2011. [https://www.microcosminc.com/](https://www.microcosminc.com/)
9. Planet Labs, *Planet Imagery Product Specifications*, 2023.
