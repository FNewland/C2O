# Chapitre 5 — Ingénierie des exigences

> **Lectures préalables conseillées.** NASA *Systems Engineering Handbook*, annexe C — *How to Write a Good Requirement* ; ECSS-E-ST-10C §5.5 ; ECSS-E-ST-10-06C §5. Ce chapitre suppose qu'un besoin de mission, une analyse des parties prenantes et un concept d'opérations existent déjà (chapitre 4), et s'appuie sur le cycle en V du chapitre 1.

## Objectifs d'apprentissage

À l'issue de ce chapitre, vous serez capable de :

1. Expliquer comment les exigences descendent la branche gauche du cycle en V tandis que la vérification remonte la branche droite
2. Rédiger des exigences qui satisfont les critères SMART et expriment le QUOI, et non le COMMENT
3. Classer les exigences par type : fonctionnelles, de performance, d'interface, de contrainte et d'environnement
4. Construire une hiérarchie d'exigences à trois niveaux (mission, système, sous-système) avec une traçabilité bidirectionnelle
5. Affecter des méthodes de vérification (ATIR(D)) aux exigences et justifier chaque choix
6. Produire, valider et gérer un ensemble d'exigences pour un petit engin spatial, que ce soit dans un outil de conception concourante ou dans un tableur

---

## 5.1 Les exigences dans le cycle en V

Rappelons le cycle en V du chapitre 1 (figure 1.1). La branche gauche décompose les besoins des parties prenantes en exigences de mission, de système et de sous-système, à des niveaux de détail croissants ; la branche droite intègre et vérifie aux niveaux correspondants, de sorte que chaque ligne horizontale du V forme une paire — une exigence et la campagne d'essais ou d'analyses qui la confirme. La correspondance avec les phases (tableau 1.1) et l'exemple SuperDove (§1.2.6) ont montré comment une constellation commerciale met en œuvre cette correspondance dans la pratique. Ce chapitre traite du *sommet de la branche gauche* : comment rédiger les exigences à partir desquelles le reste de la conception sera décomposé, comment les organiser en une hiérarchie traçable et comment affecter à chacune la méthode de vérification qui fermera ensuite sa ligne du V.

*[Source : NASA SEH, fig. 3-1 ; ECSS-E-ST-10C Rev.1, fig. 5-1 ; INCOSE SEH, 5e éd., fig. 2.7]*

---

## 5.2 Qu'est-ce qu'une exigence ?

*[Source : NASA SEH, sect. 4.2 ; ECSS-E-ST-10-06C, sect. 5.2]*

Une exigence est un **énoncé formel et vérifiable de ce que le système doit faire ou du niveau de performance qu'il doit atteindre**. Elle s'exprime par un énoncé en « doit » (*shall*) assorti d'un seuil mesurable.

### 5.2.1 La convention « shall » (« doit »)

Les exigences emploient un langage d'une précision contractuelle :

| Mot-clé | Signification | Force contractuelle |
|---------|---------|-------------------|
| **« Doit »** (*shall*) | Exigence obligatoire — doit être satisfaite | Contraignante |
| **« Devrait »** (*should*) | Objectif ou recommandation — souhaité mais non obligatoire | Consultative |
| **Futur de l'indicatif** (*will*) | Énoncé d'un fait ou d'une intention — pas une exigence | Informative |

**Exemple :**
> « Le système **doit** atteindre une distance d'échantillonnage au sol de 10 m ou mieux au nadir depuis l'orbite opérationnelle. »

Cette exigence est vérifiable : la GSD peut être calculée à partir de la géométrie optique et vérifiée sur des images d'étalonnage.

### 5.2.2 Types d'exigences

| Type | Définition | Exemple |
|------|-----------|---------|
| **Fonctionnelle** | Ce que le système doit *faire* (une capacité) | « Le système doit acquérir une imagerie multispectrale de la zone cible » |
| **De performance** | À quel *niveau* il doit le faire (quantifié) | « Le système doit atteindre une GSD ≤ 10 m au nadir » |
| **D'interface** | Accords aux frontières entre éléments | « L'EPS doit fournir à tous les sous-systèmes un bus régulé de 5,0 V ± 0,25 V » |
| **De contrainte** | Limites externes non négociables | « La masse totale du système ne doit pas dépasser 6,0 kg » |
| **D'environnement** | Conditions de survie | « Le système doit résister à des charges au lancement de 9 g en axial et de 4 g en latéral » |

*[Source : NASA SEH, annexe C, tableau C-1 ; ECSS-E-ST-10-06C, sect. 5.2.2]*

### 5.2.3 Exigences et choix de conception

| Exigence (QUOI) | Choix de conception (COMMENT) |
|--------------------|---------------------|
| « Le système doit atteindre une GSD ≤ 10 m » | « Utiliser un télescope de 150 mm d'ouverture » |
| « Le système doit résister aux charges au lancement » | « Utiliser une structure en aluminium 7075-T6 » |
| « Le système doit offrir une marge de liaison ≥ 3 dB » | « Utiliser la bande S avec un émetteur de 2 W » |
| « Le système doit être désorbité dans les 5 ans suivant la fin de vie » | « Intégrer un système de propulsion à gaz froid » |
| « Le système doit fonctionner pendant ≥ 3 ans » | « Utiliser des composants tolérants aux rayonnements » |

**Principe clé :** les exigences restreignent l'espace des solutions sans spécifier la solution. Cela préserve la liberté de conception nécessaire aux études de compromis du chapitre 4 et aux décisions d'architecture du chapitre 8.

---

## 5.3 Le cadre SMART

Si l'annexe C de la NASA fournit une liste de contrôle qualité détaillée, l'acronyme SMART sert de filtre qualité rapide :

| Lettre | Signification | Question de contrôle |
|--------|---------|---------------|
| **S** | Spécifique | Traite-t-elle exactement un seul point ? Est-elle dépourvue d'ambiguïté ? |
| **M** | Mesurable | Comporte-t-elle un seuil numérique assorti d'unités ? Peut-elle être vérifiée ? |
| **A** | Atteignable | Est-elle techniquement réalisable avec une technologie actuelle ou à court terme ? |
| **R** | Pertinente (*Relevant*) | Se rattache-t-elle à un besoin des parties prenantes ou à un objectif de niveau supérieur ? |
| **T** | Traçable | Pouvez-vous identifier son parent (son origine) et ses enfants (la manière dont elle sera vérifiée) ? |

### 5.3.1 Annexe C du NASA SEH : liste de contrôle qualité complète

*[Source : NASA SEH, annexe C — « How to Write a Good Requirement »]*

La liste de contrôle complète de la NASA ajoute des critères au-delà de SMART :

1. **Une seule exigence par énoncé** — pas d'exigences composées avec « et »
2. **Forme positive** — énoncer ce que le système DOIT FAIRE, et non ce qu'il ne doit PAS faire
3. **Voix active** — « Le système doit… » et non « Il est exigé que… »
4. **Pas de mise en œuvre** — éviter de nommer un matériel, un logiciel ou une méthode spécifiques
5. **Vérifiable** — doit pouvoir être démontrée par analyse, essai, inspection, revue de conception ou démonstration
6. **Pas de TBD** — chaque seuil doit avoir une valeur (même si elle change ensuite)
7. **Cohérente** — aucune contradiction avec les autres exigences de l'ensemble
8. **Bornée** — tolérance ou plage précisée lorsque c'est pertinent

### 5.3.2 Contre-modèles fréquents

| Contre-modèle | Problème | Meilleure version |
|-------------|---------|----------------|
| « L'engin spatial doit fonctionner à 500 km d'altitude » | Prescrit l'orbite (choix de conception) | « Le système doit assurer une couverture mondiale avec une revisite ≤ 5 jours entre ±60° de latitude » |
| « L'engin spatial doit utiliser des cellules solaires GaAs à triple jonction » | Prescrit la technologie | « L'EPS doit produire ≥ 15 W en fin de vie avec une surface de générateur ≤ 0,5 m² » |
| « Le système doit utiliser le protocole AX.25 » | Prescrit la mise en œuvre | « Le système TTC doit assurer une réception fiable des télécommandes avec un TEB ≤ $10^{-6}$ » |
| « L'engin spatial doit être un CubeSat 3U » | Prescrit le format | « Le système doit avoir une masse totale ≤ 6 kg et tenir dans l'enveloppe d'un déployeur 3U standard » |

**Exception :** les exigences d'interface SONT spécifiques, car elles définissent des frontières contractuelles :
> « L'EPS doit fournir à tous les sous-systèmes une tension de bus régulée de 28 V ± 2 V. »

C'est acceptable, car la tension du bus est un accord d'interface négocié, et non un choix de conception unilatéral.

---

## 5.4 Hiérarchie des exigences et traçabilité

Les exigences existent à plusieurs niveaux, chacun décomposé à partir du niveau supérieur. Chaque exigence doit être traçable dans les deux sens. La figure 5.1 présente la hiérarchie pour une mission de surveillance agricole.

### 5.4.1 Structure de la hiérarchie

![Arborescence des exigences : besoin de la partie prenante, exigence de mission MR-001, trois exigences système, trois exigences de sous-système et, en dessous, le niveau composant.](../assets/figures/fig_requirement_hierarchy.png)

**Figure 5.1** — Hiérarchie des exigences d'une mission d'observation de la Terre pour la surveillance agricole : un besoin de partie prenante donne lieu à une exigence de mission (MR-001), qui se décompose en exigences système pour la charge utile, le SCAO et la liaison, chacune donnant lieu à une exigence de sous-système ; le niveau composant situé en dessous (en tirets) est celui où les exigences de sous-système sont allouées aux différentes pièces. Chaque exigence est traçable vers le haut jusqu'à son parent et vers le bas jusqu'à ses enfants (§5.4.3).

### 5.4.2 Définition des niveaux

| Niveau | Périmètre | Rédigées par | Vérifiées par |
|-------|-------|-----------|-------------|
| **Mission** | Ce que la mission accomplit (dérivé des MoE) | Ingénieur système et parties prenantes | Validation opérationnelle |
| **Système** | Ce que le système doit faire (dérivé des MoP) | Ingénieur système | Intégration et essais au niveau système |
| **Sous-système** | Ce que chaque sous-système doit fournir | Ingénieurs sous-systèmes | Qualification et recette des sous-systèmes |
| **Composant** | Ce que chaque composant doit respecter | Ingénieurs composants | Essais de recette des composants |

### 5.4.3 Règles de traçabilité

Chaque exigence doit être traçable dans trois directions :

1. **Vers le haut :** vers son exigence ou son objectif parent (POURQUOI existe-t-elle ?)
2. **Vers le bas :** vers les exigences filles ou les paramètres de conception (COMMENT est-elle décomposée ?)
3. **Horizontalement :** vers une méthode de vérification (COMMENT sera-t-elle confirmée ?)

Cette traçabilité selon trois axes est consignée dans la **matrice de traçabilité des exigences (RTM)**.

L'ingénierie des exigences ne comporte pas d'équations à proprement parler, mais une relation régit la complétude de la traçabilité — le même indicateur que celui introduit sous le nom de $T_c$ au chapitre 1, §1.2.4 :

$$\text{Couverture} = \frac{N_{\text{verified requirements}}}{N_{\text{total requirements}}} \times 100\%$$

Cible : couverture de 100 % — chaque exigence doit se voir affecter au moins une méthode de vérification et un lien de traçabilité vers son parent.

*[Source : NASA SEH, sect. 6.2 (processus 11 : gestion des exigences) ; ECSS-E-ST-10C, sect. 5.2]*

### 5.4.4 Scinder les exigences composées

Une exigence composée qui traite plusieurs points doit être scindée pour permettre une vérification indépendante :

| Composée (médiocre) | Scindée (correcte) |
|-----------------|-----------------|
| « Le système doit fournir une GSD de 10 m avec une revisite de 5 jours et une latence de 24 h » | MR-001 : « GSD ≤ 10 m » **+** MR-002 : « Revisite ≤ 5 jours » **+** MR-003 : « Latence ≤ 24 h » |
| « L'EPS doit assurer une marge de puissance positive dans tous les modes, y compris en éclipse » | SR-PWR-001 : « Marge positive dans les modes éclairés » **+** SR-PWR-002 : « Marge positive en éclipse » **+** SR-PWR-003 : « DoD de la batterie ≤ 30 % dans l'éclipse la plus défavorable » |

**Justification :** chaque exigence scindée peut être vérifiée indépendamment. Si la GSD est conforme mais que la revisite ne l'est pas, l'équipe sait exactement quoi corriger, sans ambiguïté.

---

## 5.5 Méthodes de vérification — ATIR(D)

*[Source : ECSS-E-ST-10-02C Rev.1, sect. 5.3 ; NASA SEH, sect. 5.3]*

Chaque exigence doit se voir affecter une méthode de vérification. L'ECSS-E-ST-10-02C définit quatre méthodes — analyse, essai, inspection et revue de conception — et la pratique de la NASA y ajoute la démonstration ; ce manuel abrège l'ensemble en ATIR(D). Le chapitre 14 décrit la planification et la mise en œuvre de chaque méthode.

| Méthode | Code | Ce qu'elle prouve | Quand l'utiliser |
|--------|------|---------------|-----------|
| **Analyse** | A | Exigence satisfaite par modèle mathématique, simulation ou similarité | Phase B–C ; lorsque les essais sont irréalisables ou d'un coût prohibitif |
| **Essai** | T | Exigence satisfaite par mesure physique | Phase C–D ; lorsque la preuve exige du matériel dans un environnement maîtrisé |
| **Inspection** | I | Exigence confirmée par examen visuel ou physique | Caractéristiques physiques (dimensions, étiquettes, marquages, masse) |
| **Revue de conception** | R | Exigence confirmée par l'examen de plans, de schémas ou de documents | Caractéristiques de conception établies à partir des dossiers (p. ex. emploi de pièces approuvées, présence d'une redondance) |
| **Démonstration** | D | Exigence confirmée par un exercice opérationnel | Exigences fonctionnelles prouvées par l'exécution de procédures |

### 5.5.1 Guide de choix de la méthode de vérification

| Type d'exigence | Méthode habituelle | Justification |
|-----------------|---------------|-----------|
| Masse ≤ X kg | **I** (pesée) | Mesure physique directe |
| Pointage ≤ Y° | **A** (simulation) + **T** (TVAC/HITL) | D'abord l'analyse, confirmée par l'essai |
| Marge de liaison ≥ 3 dB | **A** (analyse du bilan de liaison) | Un essai complet exigerait le satellite en orbite |
| Tenue aux charges au lancement | **T** (essai de vibrations) | L'intégrité structurale doit être prouvée physiquement |
| Latence des données ≤ 24 h | **D** (exercice d'exploitation de bout en bout) | La chaîne est procédurale — il faut démontrer qu'elle fonctionne |
| Plage de températures de fonctionnement | **T** (essai de vide thermique) | L'environnement thermique doit être simulé |
| Logique FDIR du logiciel | **D** (essai par injection de pannes) | Démontrer une réponse autonome correcte |
| Présence d'une voie d'alimentation redondante | **R** (revue des schémas) | Établie à partir du dossier de conception |

### 5.5.2 Vérification par phase de projet

| Phase | Activités de vérification |
|-------|------------------------|
| **B** | Vérification par analyse (modèles, simulations, bilans, études de compromis) |
| **C** | Vérification de la conception (analyse détaillée, essais sur maquette, qualification) |
| **D** | Essais de recette (matériel de vol), intégration du système, essais d'environnement |
| **E** | Validation en orbite (recette en orbite, étalonnage, vérification opérationnelle) |

---

## 5.6 Exemples résolus

### 5.6.1 Dériver les exigences du CubeSat 3U d'OT

> **Exemple résolu — Dériver les exigences d'un CubeSat 3U d'OT**
>
> **Besoin des parties prenantes :** « Surveiller l'état des cultures dans les Prairies canadiennes avec des mises à jour hebdomadaires. »
>
> **Étape 1 — Exigence de mission :**
> MR-001 : « Le système doit fournir une imagerie permettant le calcul du NDVI avec une GSD ≤ 10 m et une revisite ≤ 7 jours sur la zone 49–54° N, 100–115° O. »
>
> **Étape 2 — Exigences système (décomposées) :**
> - SR-PL-001 : « La charge utile doit acquérir des images au moins dans les bandes ROUGE (630–690 nm) et PIR (760–900 nm). »
> - SR-AOCS-001 : « Le SCAO doit assurer une précision de pointage ≤ 0,5° (3σ) pendant la prise de vue. »
> - SR-LINK-001 : « Le système de télécommunications doit transmettre au sol ≥ 2 Go par jour vers une station sol canadienne. »
> - SR-PWR-001 : « L'EPS doit assurer une marge de puissance positive dans tous les modes opérationnels. »
>
> **Étape 3 — Exigences des sous-systèmes (dérivées) :**
> - SSR-PL-001a : « L'ouverture du télescope doit être ≥ 80 mm. » [Dérivée de la GSD et de l'altitude]
> - SSR-AOCS-001a : « Le senseur stellaire doit fournir une connaissance d'attitude ≤ 30 secondes d'arc. » [Dérivée du bilan de pointage]
> - SSR-LINK-001a : « L'émetteur en bande X doit fournir une puissance RF de sortie ≥ 2 W. » [Dérivée du bilan de liaison]
>
> **Étape 4 — Affectation des méthodes de vérification :**
>
> | Exigence | Méthode | Phase | Justification |
> |-------------|--------|-------|-----------|
> | MR-001 (GSD + revisite) | A + D | B + E | Analyse pendant la conception ; démonstration depuis l'orbite |
> | SR-PL-001 (bandes spectrales) | T | D | Étalonnage spectral en laboratoire |
> | SR-AOCS-001 (pointage) | A + T | B + D | Simulation, puis essai avec matériel dans la boucle |
> | SR-LINK-001 (liaison descendante) | A | B | Analyse du bilan de liaison |
> | SSR-PL-001a (ouverture) | I | D | Mesure physique |

### 5.6.2 Retour sur UniSat-1

> **Exemple résolu — Dériver les exigences d'un démonstrateur technologique 1U**
>
> **Besoin des parties prenantes :** « Démontrer la faisabilité d'un magnétomètre à base de MEMS pour la surveillance de la météorologie de l'espace en LEO. »
>
> **Étape 1 — Exigences de mission :**
>
> | ID | Exigence | Type | Justification |
> |----|------------|------|-----------|
> | MR-001 | « Le système doit mesurer le vecteur champ magnétique local avec une résolution ≤ 10 nT à une fréquence d'échantillonnage de 1 Hz pendant au moins 6 mois. » | Performance | Retour scientifique minimal pour la validation de la technologie |
> | MR-002 | « La masse totale du système ne doit pas dépasser 1,33 kg. » | Contrainte | CDS Rev 14, masse maximale d'un 1U |
> | MR-003 | « Le système doit transmettre au sol au moins 1 Mo de données magnétométriques par jour. » | Performance | Suffisant pour une analyse statistique des performances du capteur |
> | MR-004 | « Le système doit fonctionner pendant au moins 6 mois en LEO. » | Performance | Durée de mission minimale pour couvrir les variations saisonnières |
>
> **Étape 2 — Exigences système (décomposées) :**
> - SR-PWR-001 : « L'EPS doit fournir à tous les sous-systèmes une puissance moyenne sur l'orbite ≥ 2 W. »
> - SR-PWR-002 : « La batterie doit offrir une capacité ≥ 10 Wh. »
> - SR-LINK-001 : « Le système de télécommunications doit offrir un débit de liaison descendante ≥ 9600 bit/s. »
> - SR-LINK-002 : « Le système de télécommunications doit atteindre une marge de liaison ≥ 3 dB à une élévation minimale de 10°. »
> - SR-OBC-001 : « L'OBC doit consommer une puissance moyenne ≤ 0,5 W. »
> - SR-STR-001 : « La structure doit être conforme à la CDS Rev 14, enveloppe 1U (100 × 100 × 113,5 mm). »
>
> **Étape 3 — Exigences des sous-systèmes (dérivées) :**
> - SSR-PWR-001a : « Les cellules solaires fixées sur la structure doivent produire ≥ 2 W de puissance moyenne sur l'orbite, compte tenu de l'éclipse et de la géométrie. » [Dérivée du bilan de puissance]
> - SSR-LINK-001a : « L'émetteur UHF doit fournir une puissance RF de sortie ≥ 0,5 W à 437 MHz. » [Dérivée du bilan de liaison]
>
> **Étape 4 — Affectation des méthodes de vérification :**
>
> | Exigence | Méthode | Phase | Justification |
> |-------------|--------|-------|-----------|
> | MR-001 (performances du magnétomètre) | T + D | D + E | Étalonnage au sol, puis démonstration en orbite |
> | MR-002 (masse ≤ 1,33 kg) | I | D | Pesée du modèle de vol |
> | SR-PWR-001 (puissance moyenne sur l'orbite) | A | B | Analyse du bilan de puissance |
> | SR-LINK-001 (liaison descendante à 9600 bit/s) | A + D | B + E | Analyse du bilan de liaison ; démonstration depuis l'orbite |
> | SR-STR-001 (conformité à la CDS) | I | D | Mesure physique à l'aide du gabarit CDS |
>
> **Différence clé avec le 3U :** l'ensemble d'exigences du 1U est bien plus réduit (env. 15–20 exigences contre env. 40–60 pour une mission 3U d'observation de la Terre). Il n'y a ni exigence de pointage, ni exigence d'imagerie, ni exigence de propulsion. La campagne de vérification en est nettement plus simple et moins coûteuse.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Cycle en V | La branche gauche décompose les exigences ; la branche droite intègre et vérifie aux niveaux correspondants (figure 1.1) |
| Énoncés en « doit » | Énoncés formels, vérifiables, portant sur un seul point |
| Le QUOI, pas le COMMENT | Les exigences préservent la liberté de conception ; les choix de conception viennent plus tard, dans les études de compromis |
| SMART | Spécifique, Mesurable, Atteignable, Pertinente (*Relevant*), Traçable |
| Types d'exigences | Fonctionnelle, de performance, d'interface, de contrainte, d'environnement |
| Hiérarchie | Mission → système → sous-système, avec une traçabilité bidirectionnelle (vers le haut, vers le bas, horizontale) |
| Scission | Un seul point par exigence pour permettre une vérification indépendante |
| ATIR(D) | Analyse, essai (*Test*), inspection, revue de conception (*Review of design*) (+ démonstration) — affectées à chaque exigence pour chaque phase |

---

## Exercices

1. **Le QUOI, pas le COMMENT.** Chacun des énoncés suivants prescrit une mise en œuvre. Réécrivez chacun sous forme d'exigence qui préserve la liberté de conception, et indiquez à quel besoin des parties prenantes ou à quelle exigence de niveau supérieur il devrait se rattacher. (a) « L'engin spatial doit utiliser une antenne UHF déployable en ruban métallique. » (b) « La charge utile doit être montée sur la face +Z. » (c) « L'OBC doit fonctionner sous FreeRTOS. » (d) « L'engin spatial doit emporter quatre roues de réaction. »

2. **Scinder des exigences composées.** Scindez chacune des exigences suivantes en exigences portant sur un seul point, avec leurs identifiants, et expliquez pour l'une d'elles quelle ambiguïté surgirait si la forme composée échouait à la vérification. (a) « Le segment sol doit recevoir, traiter et diffuser les images dans les 6 h suivant l'acquisition avec une disponibilité de 99 %. » (b) « Le sous-système de contrôle thermique doit maintenir la batterie entre 0 °C et 40 °C et le détecteur de la charge utile en dessous de −10 °C pendant la prise de vue. »

3. **Classification.** Classez chacune des exigences suivantes comme fonctionnelle, de performance, d'interface, de contrainte ou d'environnement, et justifiez votre classement : (a) « L'engin spatial doit résister à une dose ionisante totale de 10 krad(Si). » (b) « L'engin spatial doit transmettre la télémesure de servitude. » (c) « La charge utile doit fournir les données d'image à l'OBC par SpaceWire à 100 Mbit/s. » (d) « L'engin spatial doit être livré pour le lancement au plus tard 24 mois après la signature du contrat. » (e) « Le SCAO doit se stabiliser à moins de 0,1° de l'attitude commandée dans les 60 s suivant un basculement de 30°. » (f) « La masse totale de l'engin spatial ne doit pas dépasser 4,0 kg. »

4. **Affectation des méthodes de vérification.** Pour un CubeSat 3U d'OT doté d'un imageur multispectral de 90 mm d'ouverture et d'une liaison descendante en bande S, rédigez cinq exigences — une de niveau mission, deux de niveau système et deux de niveau sous-système — et affectez à chacune une méthode de vérification (A, T, I, R ou D) et une phase cible (B, C, D ou E). Justifiez chaque choix en une phrase, selon le format de l'étape 4 du §5.6.1.

5. **Une hiérarchie à partir d'un nouveau besoin.** Une autorité côtière exprime le besoin suivant : « Connaître, à une heure près, la position de tout navire de plus de 300 tonnes situé à moins de 200 milles marins des côtes. » Dérivez une exigence de mission, au moins trois exigences système (couvrant la charge utile, les télécommunications et la puissance) et au moins deux exigences de sous-système, avec leurs identifiants et des liens explicites vers leurs parents. Lesquelles de vos exigences sont de performance et lesquelles sont fonctionnelles ?

6. **Audit SMART.** Chacune des exigences suivantes enfreint au moins un critère SMART ou un point de la liste de contrôle de la NASA du §5.3.1. Identifiez le défaut et réécrivez l'exigence. (a) « L'engin spatial doit avoir de bonnes performances de pointage. » (b) « La marge de liaison doit être de TBD dB. » (c) « L'engin spatial ne doit pas tomber en panne. » (d) « Il est exigé que le mode de prise de vue soit activé. » (e) « Le système doit fournir une GSD de 5 m et 10 bandes et une revisite quotidienne. »

7. **Indicateur de couverture.** Un ensemble d'exigences en compte 52. 44 se sont vu affecter une méthode de vérification ; 49 ont un lien de traçabilité vers leur parent ; 41 ont les deux. Calculez la couverture telle que définie au §5.4.3 et indiquez si l'ensemble atteint la cible. Quelles exigences l'ingénieur système devrait-il examiner en premier, et pourquoi ?

8. **Dériver une exigence de sous-système à partir d'une exigence de mission.** Retour sur UniSat-1 : l'exigence de mission MR-003 impose au moins 1 Mo de données magnétométriques par jour, et SR-LINK-001 fournit 9600 bit/s. (a) Calculez la durée de contact quotidienne totale minimale nécessaire, en supposant que la liaison est utilisée avec une efficacité de 100 %. (b) Recommencez en supposant une efficacité protocolaire de 60 % et que seule la moitié de chaque passage est exploitable à une élévation ≥ 10°. (c) Rédigez l'exigence dérivée qui en résulte pour le segment sol (nombre minimal de minutes de contact par jour), avec son lien vers le parent et sa méthode de vérification.

9. **Exigences d'interface.** Expliquez pourquoi « L'EPS doit fournir à tous les sous-systèmes une tension de bus régulée de 28 V ± 2 V » est une exigence acceptable, bien qu'elle fixe une valeur qui ressemble à un choix de conception. Rédigez deux autres exigences d'interface pour le CubeSat 3U d'OT — une interface de données entre la charge utile et l'OBC, et une interface mécanique entre l'engin spatial et son déployeur — et identifiez les postes du tableau 1.4 qui doivent s'accorder sur chacune.

10. **Dimensionner l'ensemble d'exigences.** Les exemples résolus suggèrent env. 15–20 exigences pour un démonstrateur 1U et env. 40–60 pour une mission 3U d'OT. Pour chacune des modifications suivantes d'UniSat-1, indiquez quelles nouvelles exigences (type et niveau) seraient nécessaires et estimez leur nombre : (a) ajout d'un magnétocoupleur 1 axe pour passer d'un amortissement passif à un amortissement actif des vitesses angulaires ; (b) ajout d'un second magnétomètre redondant ; (c) allongement de la durée de vie nominale de 6 mois à 2 ans.

---

## Références

1. NASA, *Systems Engineering Handbook* (NASA/SP-2016-6105 Rev 2), 2016, chap. 4.2 et annexe C. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
2. ECSS, *ECSS-E-ST-10-06C : Technical Requirements Specification*, 2009, sect. 5. [https://ecss.nl/standard/ecss-e-st-10-06c-technical-requirements-specification/](https://ecss.nl/standard/ecss-e-st-10-06c-technical-requirements-specification/)
3. ECSS, *ECSS-E-ST-10C Rev.1 : Space Engineering — System Engineering General Requirements*, 2017, sect. 5.2. [https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/](https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/)
4. ECSS, *ECSS-E-ST-10-02C Rev.1 : Space Engineering — Verification*, 2018, sect. 5.3. [https://ecss.nl/standard/ecss-e-st-10-02c-rev-1-verification-1-february-2018/](https://ecss.nl/standard/ecss-e-st-10-02c-rev-1-verification-1-february-2018/)
5. Wertz, J.R., Everett, D.F. et Puschell, J.J., *Space Mission Engineering : The New SMAD*, Microcosm Press, 2011, chap. 3–4. [https://www.microcosminc.com/](https://www.microcosminc.com/)
6. INCOSE, *Systems Engineering Handbook*, 5e éd., 2023, chap. 2.3.5. [https://www.incose.org/products-and-publications/se-handbook](https://www.incose.org/products-and-publications/se-handbook)
