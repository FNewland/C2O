# Cours de conception de missions spatiales SpaceCDF -- programme de 40 heures

## Intitulé du cours
**Conception collaborative de missions spatiales : du problème au CubeSat prêt pour le vol**

## Public
Ingénieurs, scientifiques et chefs de projet participant à des études en
centre de conception concourante (CDF). Aucune expérience préalable de la
conception d'engins spatiaux n'est requise, mais une formation d'ingénieur
est supposée.

## Organisation
- **40 heures de cours** sur 5 jours (8 heures par jour) ou 10 demi-journées
- **Guide de l'animateur** : référence complète avec l'ensemble des contenus, des corrigés et des schémas
- **Cahier d'exercices de l'apprenant** : contenus condensés et fiches d'exercices pour les travaux sur l'outil

## Documents de référence
- NASA/SP-2016-6105 Rev 2 (*Systems Engineering Handbook*)
- NPR 7123.1D (processus d'ingénierie système de la NASA)
- ECSS-E-ST-10C Rev.1 (exigences générales d'ingénierie spatiale)
- ECSS-M-ST-10C Rev.1 (management de projet)
- ECSS-E-ST-10-02C Rev.1 (vérification)
- Wertz et al., *Space Mission Engineering : The New SMAD* (2011)
- Larson & Wertz, *Space Mission Analysis and Design* (SMAD4)
- Cal Poly *CubeSat Design Specification* Rev 14.1
- Règlement des radiocommunications de l'UIT
- ECSS-U-AS-10C Rev.2 (atténuation des débris spatiaux)

---

## Jour 1 : définition de la mission et concept (8 heures)

### Séance 1.1 : introduction à la conception des missions spatiales (2 h)
- Qu'est-ce qu'un centre de conception concourante ?
- Le cycle en V (NASA SEH, chap. 2-3)
- Les 17 processus d'ingénierie système (NPR 7123.1)
- Phases du cycle de vie NASA/ECSS et jalons de revue
- Rôle de chaque poste du CDF
- **Exercice** : mettre en correspondance les 17 processus et l'outil SpaceCDF

### Séance 1.2 : besoin de mission et analyse des parties prenantes (2 h)
- Processus 1 du NASA SEH : définition des attentes des parties prenantes
- Rédaction de l'énoncé du problème (NASA SEH, §4.1)
- Identification des parties prenantes et recueil des besoins
- Définition des objectifs assortis de critères de réussite mesurables
- Hiérarchie MoE, MoP, TPM
- **Exercice** : définir le besoin de mission pour un problème type (avec l'étape 1 de SpaceCDF)
- **Fiche d'exercices** : matrice des parties prenantes, hiérarchie des objectifs

### Séance 1.3 : analyse de compromis de mission (2 h)
- Processus 17 du NASA SEH : analyse de décision
- Solutions spatiales et non spatiales
- Méthodologie des études de compromis : critères, pondérations, notation
- Services de données existants (Copernicus, Planet, Spire)
- Quand NE PAS construire de satellite
- **Exercice** : mener le compromis de mission dans SpaceCDF (étape 2)
- **Fiche d'exercices** : matrice d'étude de compromis avec notation

### Séance 1.4 : concept d'opérations (2 h)
- Annexe S du NASA SEH : structure du ConOps
- Architecture de la mission : segments spatial, sol et utilisateur
- Phases de la mission (LEOP -> recette en orbite -> nominale -> retrait de service)
- Modes opérationnels et fonctionnement par intermittence
- Conception de la chaîne de flux de données
- Options d'architecture du segment sol
- **Exercice** : construire le ConOps dans SpaceCDF
- **Fiche d'exercices** : plan du ConOps selon l'annexe S

---

## Jour 2 : exigences, fonctions, orbite et architecture (8 heures)

### Séance 2.1 : ingénierie des exigences (2 h)
- Processus 2 du NASA SEH : définition des exigences techniques
- Exigences SMART (spécifiques, mesurables, atteignables, pertinentes, traçables)
- Le QUOI, pas le COMMENT : exigences et choix de conception
- Hiérarchie des exigences : mission -> système -> sous-système
- Annexe C du NASA SEH : comment rédiger une bonne exigence
- **Exercice** : générer les exigences à partir des objectifs dans SpaceCDF
- **Fiche d'exercices** : liste de vérification de la qualité des exigences (annexe C)

### Séance 2.2 : décomposition fonctionnelle (2 h)
- Processus 3 du NASA SEH : décomposition logique
- Arbres fonctionnels : objectif -> fonction -> sous-fonction
- Allocation aux sous-systèmes (définition des frontières du système)
- Exigences dérivées des fonctions
- Définition des critères de performance
- **Exercice** : construire l'arbre fonctionnel dans SpaceCDF
- **Fiche d'exercices** : matrice de traçabilité fonctions-exigences

### Séance 2.3 : choix de l'orbite et architecture de mission (2 h)
- Fondamentaux de mécanique spatiale (éléments képlériens, perturbations)
- Compromis LEO/SSO/MEO/GEO/HEO
- Couverture, revisite et géométrie de contact avec les stations sol
- Durée de vie orbitale et conformité en matière de débris (ECSS-U-AS-10C)
- Fraction d'éclipse et conséquences sur la puissance ; environnement radiatif selon l'orbite
- **Exercice** : mener le compromis d'orbite dans SpaceCDF
- **Fiche d'exercices** : matrice de compromis pour le choix de l'orbite

### Séance 2.4 : architecture de mission -- segments, interfaces et bilans (2 h)
- Décomposition de la mission en segments et schéma fonctionnel du système
- Processus 12 du NASA SEH : gestion des interfaces ; ECSS-E-ST-10-24C : exigences d'interface
- Méthodologie de la matrice d'interfaces N^2 ; types d'interfaces : mécanique, électrique, thermique, données, RF, optique
- Identification et résolution des conflits
- Méthodologie du bilan de masse (ECSS-E-HB-10-02A) et du bilan de puissance (ECSS-E-ST-20C)
- Politique de marges selon la phase du projet ; consolidation des bilans : composant -> sous-système -> système
- **Exercice** : examiner la matrice d'interfaces et les bilans paramétriques dans SpaceCDF
- **Fiche d'exercices** : spécification d'interface pour 2 paires de sous-systèmes ; modèle de bilan de masse avec politique de marges

---

## Jour 3 : conception des sous-systèmes (8 heures)

### Séance 3.1 : puissance et thermique (2 h)
- Architecture de l'EPS (générateur solaire, batterie, régulation)
- Bilan de puissance par mode opérationnel, avec fonctionnement par intermittence
- Dimensionnement du générateur solaire et de la batterie en fin de vie
- Contrôle thermique : passif ou actif, dimensionnement des radiateurs, réchauffeurs
- Analyse cas chaud / cas froid
- **Exercice** : examiner les résultats puissance et thermique dans SpaceCDF
- **Fiche d'exercices** : tableau du bilan de puissance par mode

### Séance 3.2 : SCAO et propulsion (2 h)
- Capteurs et actionneurs d'attitude : magnétocoupleurs, roues de réaction ou senseurs stellaires
- Bilan de pointage (arbre d'erreurs RSS) ; couples perturbateurs et gestion du moment cinétique
- Options de propulsion : gaz froid, électrique, chimique
- Répartition du bilan de delta-V
- **Exercice** : examiner les résultats SCAO et propulsion dans SpaceCDF
- **Fiche d'exercices** : bilan de pointage et bilan de delta-V

### Séance 3.3 : télécommunications (2 h)
- Méthodologie du bilan de liaison (ECSS-E-ST-50-05C)
- Choix de la bande de fréquences et licences
- Licences radioamateur, expérimentales et commerciales
- Volume de données de la charge utile et dimensionnement de la liaison descendante (bilan de liaison -> antenne -> puissance)
- **Exercice** : configurer les données de la charge utile et examiner le bilan de liaison
- **Fiche d'exercices** : feuille de calcul du bilan de liaison

### Séance 3.4 : structure et gestion bord des données (2 h)
- *CubeSat Design Specification* (CDS Rev 14.1)
- Conception structurale : charges au lancement, fréquence propre, marge de sécurité
- Architecture de l'OBC, stockage des données, logiciel de vol
- Norme de bus PC/104
- **Exercice** : choisir les équipements dans le navigateur de SpaceCDF
- **Fiche d'exercices** : étude de compromis pour le choix des composants

---

## Jour 4 : intégration et vérification (8 heures)

### Séance 4.1 : choix et intégration des équipements (2 h)
- Méthodologie de choix des composants (études de compromis)
- Compatibilité de la chaîne RF (concordance des bandes du transpondeur et de l'antenne)
- Compatibilité avec le bus de puissance (tension, lignes commutées)
- Vérification de l'encombrement et de la masse
- Conception du harnais et du câblage
- **Exercice** : terminer le choix des équipements dans SpaceCDF
- **Fiche d'exercices** : liste de vérification de la compatibilité des équipements

### Séance 4.2 : planification de la vérification et de la validation (2 h)
- Processus 7-8 du NASA SEH : vérification et validation
- ECSS-E-ST-10-02C : méthodes de vérification, ATIR(D) (analyse, essai, inspection, revue de conception, + démonstration)
- Structure de la matrice de vérification
- Niveaux d'essai : unité -> sous-système -> système -> recette -> qualification
- Essais d'environnement (vibrations, vide thermique, CEM)
- **Exercice** : examiner la matrice de conformité dans SpaceCDF
- **Fiche d'exercices** : matrice V&V pour 10 exigences clés

### Séance 4.3 : gestion des risques (2 h)
- ECSS-M-ST-80C : processus de gestion des risques
- Identification, évaluation (matrice 5×5) et réduction des risques
- Méthodologie AMDEC (FMECA) (ECSS-Q-ST-30-02C)
- Analyse des points de défaillance unique
- Indicateurs de performance technique (TPM)
- **Exercice** : examiner les scores de risque et la fiabilité dans SpaceCDF
- **Fiche d'exercices** : registre des risques pour les 5 principaux risques

### Séance 4.4 : coûts et planning (2 h)
- Estimation des coûts : paramétrique (SSCM, COMPACT), par analogie, ascendante
- Structure du WBS (NPR 7120.5)
- Facteurs de coût et fractions de coût d'un CubeSat
- Estimation du planning et chemin critique
- Effets de courbe d'apprentissage pour les constellations
- **Exercice** : examiner la ventilation des coûts et lancer l'optimiseur
- **Fiche d'exercices** : estimation des coûts par élément du WBS

---

## Jour 5 : revue de conception et réglementation (8 heures)

### Séance 5.1 : préparation des revues de jalon (2 h)
- ECSS-M-ST-10C : structure des jalons de revue
- Critères de sortie des revues MCR/SRR/PDR/CDR ; le jalon du jour 5 est une revue de type PDR
- Structure de la présentation en revue de conception
- Gestion des actions
- **Exercice** : mener la revue de jalon dans SpaceCDF, solder les actions
- **Fiche d'exercices** : plan de la présentation de la PDR

### Séance 5.2 : réglementation et licences (2 h)
- Licences de fréquences (UIT, IARU, nationales)
- Procédure de notification à l'UIT (API -> coordination -> notification)
- LSTS canadienne pour la télédétection
- Contrôle des exportations (ITAR/EAR/CGP)
- Convention sur l'immatriculation de l'ONU (CUPEEA)
- Réglementation sur les débris spatiaux (règles des 25 ans / 5 ans)
- **Exercice** : générer les dossiers réglementaires dans SpaceCDF
- **Fiche d'exercices** : arbre de décision pour les licences

### Séance 5.3 : intégration au lanceur (2 h)
- Fournisseurs de lancement et tarifs
- Normes de déployeurs (ISIPOD, EXOpod, CSD)
- Exigences de l'ICD lanceur (mécaniques, électriques, d'environnement)
- Interrupteurs de séparation et inhibitions
- Dérivation de la spécification des essais d'environnement
- **Exercice** : choisir un fournisseur de lancement, examiner les exigences de l'ICD
- **Fiche d'exercices** : liste de vérification de la conformité à l'ICD lanceur

### Séance 5.4 : optimisation de la conception et revue finale (2 h)
- Optimisation multiobjectif (notions de Pareto)
- Analyse de sensibilité (criblage de Morris)
- Itération et convergence de la conception
- Présentation de la revue de conception finale
- Retour d'expérience
- **Exercice** : lancer l'optimiseur, examiner le front de Pareto, choisir la conception finale
- **Exercice final** : chaque équipe présente la conception complète de sa mission

---

## Évaluation
- Jours 1-4 : fiches d'exercices remplies en classe (formative)
- Jour 5 : présentation en équipe de la conception complète de la mission (sommative)
- Après le cours : accès à l'outil SpaceCDF et au Guide de l'animateur

## Approfondissements par poste (annexes)

### Annexe A : ingénieur système
- Gestion des bilans, politique de marges, pilotage des études de compromis
- Résolution des conflits entre domaines
- Préparation des revues de jalon et évaluation des critères de sortie

### Annexe B : analyste de mission
- Mécanique spatiale, analyse de couverture, conception de constellations
- Choix des stations sol, analyse des durées de contact
- Conditions d'éclairement, analyse des éclipses

### Annexe C : ingénieur charge utile
- Dimensionnement des charges utiles optiques/RF/SAR
- Débits de la charge utile et besoins de stockage
- Étalonnage des instruments et vérification des performances

### Annexe D : ingénieur puissance
- Dimensionnement du générateur solaire (fixé sur la structure ou déployable)
- Dimensionnement de la batterie et durée de vie en cycles
- Architecture de l'EPS et distribution de puissance
- Analyse des modes de puissance avec fonctionnement par intermittence

### Annexe E : ingénieur SCAO
- Détermination d'attitude : senseurs solaires, senseurs stellaires, gyroscopes
- Contrôle d'attitude : magnétocoupleurs, roues de réaction
- Bilan de pointage (analyse d'erreurs RSS)
- Gestion et déchargement du moment cinétique

### Annexe F : ingénieur thermique
- Environnement thermique orbital (cas chaud, cas froid, éclipse)
- Contrôle thermique passif (revêtements, MLI, radiateurs)
- Contrôle thermique actif (réchauffeurs, caloducs)
- Politique de marges thermiques (ECSS-E-ST-31C)

### Annexe G : ingénieur télécommunications
- Fondamentaux du bilan de liaison
- Choix de la bande de fréquences et licences
- Types et dimensionnement des antennes
- Choix de la modulation et du codage
- Conception du réseau de stations sol

### Annexe H : ingénieur propulsion
- Bilan de delta-V (injection en orbite, maintien, désorbitation, évitement de collision)
- Types de systèmes propulsifs (gaz froid, électrique, chimique)
- Dimensionnement des réservoirs et gestion des ergols
- Choix et performances des propulseurs

### Annexe I : ingénieur structures
- Conformité à la *CubeSat Design Specification*
- Analyse des charges au lancement (quasi statiques, vibrations, chocs)
- Calcul de la marge de sécurité structurale
- Conception des mécanismes (déploiement, séparation)

### Annexe J : ingénieur coûts
- Modèles de coût paramétriques (SSCM, COMPACT, NICM)
- Élaboration du WBS et répartition des coûts
- Coût ajusté au risque (Monte-Carlo)
- Courbe d'apprentissage pour les productions en série

### Annexe K : ingénieur conformité / réglementation
- Applicabilité et adaptation des normes ECSS
- Arbre de décision pour les licences de fréquences
- Classification au titre du contrôle des exportations
- Évaluation de la conformité en matière de débris spatiaux
- Planification et déclaration de la fin de vie

### Annexe L : ingénieur segment sol
- Architecture des stations sol
- Conception du centre de contrôle de mission
- Chaîne de traitement des données
- Concept d'opérations et dotation en personnel

### Annexe M : ingénieur logiciel
- Architecture du logiciel de vol
- FDIR (détection, isolation et reprise des défaillances)
- Définition des télécommandes et de la télémesure
- Logiciel sol et outils d'exploitation

---

## Plan de production des documents

### Guide de l'animateur (~400 pages)
- Contenu complet des 20 séances
- Corrigés complets de tous les exercices
- Schémas et formules tout au long de l'ouvrage
- Citations des références par section
- Index détaillé

### Cahier d'exercices de l'apprenant (~150 pages)
- Contenu condensé par séance (notions clés + références)
- 20 fiches d'exercices (une par séance)
- Guides des exercices sur l'outil (instructions SpaceCDF pas à pas)
- Espace pour les notes et les points de discussion
- Annexe avec les formules clés et des tableaux de référence
