---
title: "SpaceCDF — Cahier d'exercices du cours"
subtitle: "Fiches et exercices du stage intensif de 40 heures en centre de conception concourante"
version: "v6 — 2026-05-10"
language: fr
---


# Note aux apprenants et apprenantes

Ce cahier d'exercices accompagne le *Manuel du cours SpaceCDF*. Il est conçu pour
que vous l'utilisiez seul ou en équipe d'étude, à votre rythme : aucun
animateur ni enseignant n'est nécessaire. Chaque chapitre comporte des
fiches d'exercices, des calculs à effectuer et des réflexions à rédiger.
Des indices vous renvoient au chapitre du manuel qui présente la théorie
correspondante.

Lorsque le cahier fait référence à l'outil SpaceCDF, vous devez disposer
d'une installation fonctionnelle (voir le *Guide d'installation de SpaceCDF*).
L'outil s'exécute entièrement sur votre propre ordinateur ; les consignes
de navigation sont rédigées pour que vous puissiez effectuer les étapes sans encadrement.

Les espaces marqués d'un trait fin au crayon sont destinés à vos propres notes.
Ce volume ne contient aucune grille d'évaluation.

# Déclaration — IA générative (AIG)

Ce cahier d'exercices a été produit avec l'aide de l'IA générative dans le cadre
du flux de travail du centre de conception concourante SpaceCDF. Le contenu des
fiches, les énoncés de calcul, les fiches d'équations et les figures intégrées
sont générés par la chaîne d'outils SpaceCDF (Python · matplotlib · python-docx),
guidée par les références ECSS, NASA SEH et SMAD-4. Le cadrage éditorial et les
commentaires pédagogiques restent la propriété de l'équipe pédagogique SpaceCDF.

*L'attribution suit le cadre AIG (*Assisted by Generative AI*) —
Peters (2023), Logos IA-EN, CC BY-NC-SA 4.0 —
https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/*

Tout livrable de cours que vous produisez à partir de ce cahier — ou
tout document exporté par SpaceCDF — doit porter le badge AIG et une
courte note décrivant l'usage qui a été fait de l'IA générative. Vous pouvez
refuser d'utiliser l'IA lorsqu'elle est autorisée ; ce qui n'est pas acceptable,
c'est de l'utiliser sans le dire.

---

# Fiche 1.1 : Introduction à la conception de missions spatiales

| | |
|---|---|
| **Nom :** | __________________________________________ |
| **Date :** | __________________________________________ |
| **Équipe :** | __________________________________________ |
| **Séance :** | 1.1 -- Introduction à la conception de missions spatiales |

---

## Partie A : Les 17 processus d'ingénierie système -- correspondance avec SpaceCDF

Pour chaque processus d'ingénierie système de la NASA (NPR 7123.1D), identifiez la fonctionnalité de SpaceCDF qui le met en œuvre. Indiquez le nom de l'onglet, du bouton ou du panneau. Si le processus exige un jugement humain que l'outil ne peut pas automatiser, inscrivez « Manuel » dans la dernière colonne.

*Indice : commencez par le Guide de la barre d'outils : niveau par niveau, il indique quoi faire et dans quel onglet. Parcourez ensuite les onglets de niveau (0 Mission, 1 Segment, 2 Système / élément, 3 Sous-système, V&V) et les onglets d'activité (Blocs, Exigences, Fonctions, Interfaces, Décider, Analyses…). De nombreux processus correspondent à plus d'une fonctionnalité ; les liens « Où dans SpaceCDF » sous cette partie, dans le journal de bord, ouvrent les principaux.*

| # | Processus d'ingénierie système | Fonctionnalité(s) de SpaceCDF | Manuel ? |
|---|-----------|---------------------|---------|
| 1 | Définition des attentes des parties prenantes | __________________________________________ | ______ |
| 2 | Définition des exigences techniques | __________________________________________ | ______ |
| 3 | Décomposition logique | __________________________________________ | ______ |
| 4 | Définition de la solution de conception | __________________________________________ | ______ |
| 5 | Réalisation du produit | __________________________________________ | ______ |
| 6 | Intégration du produit | __________________________________________ | ______ |
| 7 | Vérification du produit | __________________________________________ | ______ |
| 8 | Validation du produit | __________________________________________ | ______ |
| 9 | Transfert du produit | __________________________________________ | ______ |
| 10 | Planification technique | __________________________________________ | ______ |
| 11 | Gestion des exigences | __________________________________________ | ______ |
| 12 | Gestion des interfaces | __________________________________________ | ______ |
| 13 | Gestion des risques techniques | __________________________________________ | ______ |
| 14 | Gestion de configuration | __________________________________________ | ______ |
| 15 | Gestion des données techniques | __________________________________________ | ______ |
| 16 | Évaluation technique | __________________________________________ | ______ |
| 17 | Analyse de décision | __________________________________________ | ______ |

**Réflexion :** quels processus l'outil prend-il bien en charge ? Lesquels exigent fondamentalement un jugement humain et ne peuvent pas être entièrement automatisés ? Rédigez votre réponse ci-dessous :

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

## Partie B : Identification des phases du cycle de vie

Pour chacune des activités ci-dessous, indiquez à quelle phase du cycle de vie NASA (de pré-A à F) elle appartient et quel jalon de revue marque la fin de cette phase :

| Activité | Phase NASA | Jalon de revue |
|----------|-----------|-------------|
| « Nous devons surveiller l'épaisseur de la glace de mer dans l'Arctique canadien » | __________ | __________ |
| Rédiger des exigences système en « doit », avec leurs méthodes de vérification | __________ | __________ |
| Choisir un fournisseur précis de roues de réaction après avoir évalué 3 options | __________ | __________ |
| Réaliser les essais de qualification en vide thermique sur le modèle de vol | __________ | __________ |
| Exploiter le satellite et produire des produits de données quotidiens | __________ | __________ |
| Retirer le satellite du service et procéder à sa passivation | __________ | __________ |
| Étude de compromis préliminaire sur l'orbite comparant SSO, orbite de l'ISS et orbite polaire | __________ | __________ |
| Analyse détaillée par éléments finis de la structure primaire | __________ | __________ |

*Indice : reportez-vous au tableau des phases du cycle de vie de la séance 1.1, section 4.3. Demandez-vous quel niveau de détail de conception cette activité exige.*

---

## Partie C : Analyse des interactions entre postes du CDF

Pour chacun des conflits de conception ci-dessous, identifiez les postes d'ingénierie qui doivent interagir pour le résoudre. Décrivez ensuite brièvement comment vous aborderiez sa résolution.

**Conflit 1 :** la charge utile demande 50 W, mais le générateur solaire ne peut fournir que 30 W.

Postes concernés : _______________________________________________

Démarche de résolution : _______________________________________________

_______________________________________________

**Conflit 2 :** les vibrations des roues de réaction dépassent l'exigence de stabilité de pointage de la charge utile.

Postes concernés : _______________________________________________

Démarche de résolution : _______________________________________________

_______________________________________________

**Conflit 3 :** l'orbite retenue (700 km) impose une désorbitation propulsive pour respecter les règles relatives aux débris, mais il ne reste aucune marge dans le bilan de masse pour un système propulsif.

Postes concernés : _______________________________________________

Démarche de résolution : _______________________________________________

_______________________________________________

**Conflit 4 :** le diagramme de rayonnement de l'antenne de liaison descendante en bande X interfère avec le récepteur optique sensible de la charge utile.

Postes concernés : _______________________________________________

Démarche de résolution : _______________________________________________

_______________________________________________

---

## Partie D : Exploration de l'outil SpaceCDF

Parcourez l'outil SpaceCDF et répondez à chaque question :

1. Ouvrez la liste de maturité de la barre d'état (« Maturité du niveau 0 : n/m »). Quelles vérifications énumère-t-elle pour votre niveau, et lesquelles ne sont pas encore satisfaites ?

   _______________________________________________

   _______________________________________________

   _______________________________________________

2. Dans V&V › Jalons de revue, quels sont les critères de sortie de la MDR ? Lesquels sont obligatoires, et lesquels l'outil évalue-t-il automatiquement plutôt que de vous les laisser (manuels) ?

   _______________________________________________

   _______________________________________________

   _______________________________________________

3. Quels postes d'ingénierie une équipe peut-elle choisir sous Taille de l’équipe (postes), à la dernière étape de Définition de la mission ?

   _______________________________________________

   _______________________________________________

4. Par quelles étapes SpaceCDF vous guide-t-il, de gauche à droite (les étapes de Définition de la mission, puis les onglets de niveau) ?

   _______________________________________________

5. Ouvrez le Guide (barre d'outils) à votre niveau : quels objectifs d'apprentissage et conseils énumère-t-il ? Dans V&V › Jalons de revue, quels critères relèvent de votre poste ?

   _______________________________________________

   _______________________________________________

   _______________________________________________

---

## Partie E : Esquisse du cycle en V

Dans l'espace ci-dessous, esquissez de mémoire le cycle en V. Nommez chaque niveau sur la branche gauche (décomposition) et sur la branche droite (intégration). Tracez les flèches de traçabilité horizontale et nommez-les.

*Utilisez cet espace pour votre esquisse :*

|   |
|---|
|   |
|   |
|   |
|   |
|   |
|   |
|   |
|   |
|   |
|   |
|   |
|   |
|   |
|   |
|   |

---

## Notes et réflexions

Notez ci-dessous les points clés, les questions que vous souhaitez approfondir et les liens avec votre concept de mission :

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Fiche 1.2 : Écosystème spatial canadien et environnement réglementaire

| | |
|---|---|
| **Nom :** | __________________________________________ |
| **Date :** | __________________________________________ |
| **Équipe :** | __________________________________________ |
| **Séance :** | 1.2 -- Écosystème spatial canadien et environnement réglementaire |

---

## Partie A : Cartographie de l'industrie spatiale canadienne

Pour le concept de mission de votre équipe, identifiez des partenaires industriels canadiens potentiels à chaque niveau. S'il n'existe aucun fournisseur canadien pour une capacité donnée, indiquez de quel pays vous vous approvisionneriez et pourquoi.

| Niveau | Capacité requise | Candidat(s) canadien(s) | Solution internationale | Justification |
|------|-------------------|----------------------|--------------------------|--------------|
| Niveau 1 (maître d'œuvre/intégration) | _____________________ | _____________________ | _____________________ | _____________________ |
| Niveau 2 (sous-système) | _____________________ | _____________________ | _____________________ | _____________________ |
| Niveau 2 (sous-système) | _____________________ | _____________________ | _____________________ | _____________________ |
| Niveau 3 (composant/service) | _____________________ | _____________________ | _____________________ | _____________________ |
| Niveau 4 (R-D/université) | _____________________ | _____________________ | _____________________ | _____________________ |

**Question :** quel(s) programme(s) de financement de l'Agence spatiale canadienne (ASC) pourrai(en)t soutenir votre mission ? Pourquoi ?

_______________________________________________

_______________________________________________

_______________________________________________

---

## Partie B : Évaluation de la conformité à la LSTS

Répondez aux questions suivantes pour le concept de mission de votre équipe :

1. Votre mission comporte-t-elle une forme de télédétection de la Terre (imagerie, SAR, radiométrie, etc.) ?

   _______________________________________________

2. Si oui, le satellite sera-t-il exploité depuis le Canada ?

   _______________________________________________

3. Quelles conditions de la Loi sur les systèmes de télédétection spatiale (LSTS ; RSSSA en anglais) pourraient s'appliquer ? (Cochez toutes celles qui s'appliquent.)

   | Condition | S'applique ? | Notes |
   |-----------|----------|-------|
   | Accès prioritaire du gouvernement du Canada | __________ | _____________________ |
   | Dispositions d'interruption de service (*shutter control*) | __________ | _____________________ |
   | Plan de disposition et de traitement des données | __________ | _____________________ |
   | Plan de retrait de service du système | __________ | _____________________ |
   | Protection des données brutes | __________ | _____________________ |
   | Accords d'interopérabilité (accès étranger) | __________ | _____________________ |

4. Si votre mission ne comporte PAS de télédétection, quelles autres exigences réglementaires s'appliquent ? (p. ex. attribution de licences de spectre, contrôle des exportations)

   _______________________________________________

   _______________________________________________

---

## Partie C : Plan d'attribution des licences de spectre

Identifiez les bandes de fréquences que votre mission utilisera et la démarche d'obtention de licence pour chacune :

| Liaison | Bande | Fréquence (GHz) | Débit | Usage (TT&C / charge utile / ISL) | Démarche de licence |
|------|------|-----------------|-----------|---------------------------|---------------|
| Liaison montante | __________ | __________ | __________ | __________ | __________ |
| Liaison descendante (TT&C) | __________ | __________ | __________ | __________ | __________ |
| Liaison descendante (charge utile) | __________ | __________ | __________ | __________ | __________ |
| Autre | __________ | __________ | __________ | __________ | __________ |

*Indice : pour un CubeSat typique, la TT&C utilise la bande S (2,0--2,3 GHz) et les données de charge utile la bande X (8,025--8,4 GHz). La démarche de licence est la même pour chacune : demande auprès d'Innovation, Sciences et Développement économique Canada (ISDE) -> examen technique par ISDE -> notification à l'UIT (publication anticipée, API) -> coordination UIT -> délivrance de la licence par ISDE.*

**Question :** à quel stade de votre projet devez-vous engager la démarche de licence de spectre ? Pourquoi ?

_______________________________________________

_______________________________________________

_______________________________________________

---

## Partie D : Classification au titre du contrôle des exportations

Énumérez les 3 composants les plus critiques de votre concept de mission préliminaire. Pour chacun, identifiez la classification probable au titre du contrôle des exportations :

| Composant | Pays d'origine | Classification probable | Licence requise ? |
|-----------|------------------|-----------------------|-------------------|
| _____________________ | __________ | ECCN : __________ / USML Cat. : __________ | __________ |
| _____________________ | __________ | ECCN : __________ / USML Cat. : __________ | __________ |
| _____________________ | __________ | ECCN : __________ / USML Cat. : __________ | __________ |

*Indice : la plupart des composants spatiaux sur étagère (COTS) de fabricants américains relèvent des EAR (ECCN 9A515 pour les pièces d'engins spatiaux). Les articles de qualité militaire ou spécialement conçus peuvent relever des ITAR (USML catégorie XV). Les composants d'origine canadienne sont soumis à la Loi sur les licences d'exportation et d'importation (LLEI) s'ils figurent sur la Liste des marchandises et technologies d'exportation contrôlée.*

**Question :** si votre mission comprend un senseur stellaire d'origine américaine et que vous prévoyez un lancement sur un PSLV indien, quels problèmes de contrôle des exportations se posent ?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

## Partie E : Calendrier réglementaire

À partir de votre concept de mission, estimez quand chaque activité réglementaire doit commencer et combien de temps elle prendra. Reportez les activités sur le calendrier ci-dessous :

| Activité réglementaire | Phase de début | Durée | Chemin critique ? |
|--------------------|-------------|----------|---------------|
| Demande de licence au titre de la LSTS | __________ | __________ | __________ |
| Demande de spectre auprès d'ISDE | __________ | __________ | __________ |
| Coordination UIT | __________ | __________ | __________ |
| Licence(s) d'exportation | __________ | __________ | __________ |
| Accord d'interface avec le fournisseur de lancement | __________ | __________ | __________ |

**Question :** quelle activité réglementaire a le plus de chances de se trouver sur le chemin critique de votre mission ? Pourquoi ?

_______________________________________________

_______________________________________________

_______________________________________________

---

## Notes et réflexions

Notez ci-dessous les points clés, les questions réglementaires que vous devez approfondir et leurs conséquences sur la conception de votre mission :

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Fiche 1.3 : Normes internationales pour les systèmes spatiaux

| | |
|---|---|
| **Nom :** | __________________________________________ |
| **Date :** | __________________________________________ |
| **Équipe :** | __________________________________________ |
| **Séance :** | 1.3 -- Normes internationales pour les systèmes spatiaux |

---

## Partie A : Matrice d'applicabilité des normes

Pour le concept de mission de votre équipe, déterminez quelles normes ECSS et NASA s'appliquent. Pour chaque norme, décidez si elle est entièrement applicable, partiellement applicable (avec adaptation) ou non applicable. Justifiez votre décision.

| Norme | Branche | Applicabilité | Notes d'adaptation / justification |
|----------|--------|--------------|-------------------------------|
| ECSS-M-ST-10C (gestion de projet) | M | __________ | _____________________________________ |
| ECSS-M-ST-40C (gestion de configuration) | M | __________ | _____________________________________ |
| ECSS-M-ST-80C (gestion des risques) | M | __________ | _____________________________________ |
| ECSS-E-ST-10C (ingénierie système) | E | __________ | _____________________________________ |
| ECSS-E-ST-20C (électricité et électronique) | E | __________ | _____________________________________ |
| ECSS-E-ST-32C (structures) | E | __________ | _____________________________________ |
| ECSS-E-ST-40C (logiciel) | E | __________ | _____________________________________ |
| ECSS-E-ST-50C (communications) | E | __________ | _____________________________________ |
| ECSS-Q-ST-10C (assurance produit) | Q | __________ | _____________________________________ |
| ECSS-U-AS-10C (atténuation des débris) | U | __________ | _____________________________________ |
| ISO 24113 (atténuation des débris) | -- | __________ | _____________________________________ |
| NPR 7123.1D (processus d'ingénierie système) | -- | __________ | _____________________________________ |

*Indice : une mission CubeSat universitaire invoquerait typiquement ECSS-E-ST-10C avec une adaptation poussée, ECSS-U-AS-10C intégralement, et pourrait déroger à ECSS-Q-ST-10C (assurance produit) pour des raisons de coût. Une mission financée par l'ASC exigerait généralement une conformité ECSS plus complète.*

**Question :** quel est l'ensemble minimal de normes que votre mission DOIT respecter, quelle que soit sa classe ?

_______________________________________________

_______________________________________________

_______________________________________________

---

## Partie B : Liste de vérification de conformité à la CDS rév. 14

Si votre mission utilise un format CubeSat, remplissez cette liste de vérification de conformité. Sinon, passez à la partie C.

| Exigence de la CDS | Valeur de votre conception | Conforme ? | Notes |
|----------------|------------------|-----------|-------|
| Dimensions de l'unité (100 x 100 x 113,5 mm par U) | __________ | __________ | __________ |
| Masse par U ($\leq$ 2,0 kg) | __________ | __________ | __________ |
| Masse totale (pour votre format) | __________ | __________ | __________ |
| Matériau des rails (Al anodisé dur) | __________ | __________ | __________ |
| Centre de gravité à moins de 2 cm du centre géométrique | __________ | __________ | __________ |
| Aucune saillie hors de l'enveloppe pendant le lancement | __________ | __________ | __________ |
| Silence RF pendant 30 min après le déploiement | __________ | __________ | __________ |
| Interrupteurs de déploiement sur tous les éléments déployables | __________ | __________ | __________ |
| Inhibitions de la propulsion (3 indépendantes, le cas échéant) | __________ | __________ | __________ |

*Indice : l'onglet Satellite (niveau 2) affiche le format que SpaceCDF déduit et la limite de masse du tableau 1 de la CDS 14.1, comparée à la masse de conception plus la marge. Vérifiez les rails, les dimensions, la goupille RBF et les interrupteurs de déploiement dans la CDS elle-même (lien dans le journal de bord).*

---

## Partie C : Conformité en matière d'atténuation des débris

Effectuez l'évaluation suivante de l'atténuation des débris pour l'orbite de votre mission :

1. **Altitude d'orbite prévue :** __________ km

2. **Durée de vie orbitale naturelle estimée** (sans propulsion) :

   *Utilisez la règle empirique $\tau_{years} \approx \frac{h - 200}{30} \times \frac{m/A}{50}$ où $h$ est l'altitude (km), $m$ la masse (kg) et $A$ la section efficace (m$^2$)*

   $h$ = __________ km, $m$ = __________ kg, $A$ = __________ m$^2$

   $m/A$ = __________ kg/m$^2$

   $\tau$ = __________ ans (approximation)

3. **Évaluation de la conformité :**

   | Exigence | Limite | Votre mission | Conforme ? |
   |-------------|-------|-------------|-----------|
   | Durée de vie post-mission IADC | $\leq$ 25 ans | __________ | __________ |
   | Durée de vie post-mission FCC (2024+) | $\leq$ 5 ans | __________ | __________ |
   | Fiabilité du retrait de service ISO 24113 | $\geq$ 90 % | __________ | __________ |

4. **Si la mission n'est pas conforme à la règle FCC des 5 ans, quelles options s'offrent à vous ?**

   _______________________________________________

   _______________________________________________

   _______________________________________________

5. **Plan de passivation** (énumérez toutes les sources d'énergie stockée et la manière dont vous les épuiserez en fin de vie) :

   | Source d'énergie | Méthode de passivation |
   |-------------|-------------------|
   | Batterie | __________________________________________ |
   | Réservoirs sous pression (le cas échéant) | __________________________________________ |
   | Roues de réaction | __________________________________________ |
   | Émetteur RF | __________________________________________ |
   | Autre : __________ | __________________________________________ |

---

## Partie D : Marges de dimensionnement structural

Si vous disposez d'informations préliminaires sur la conception structurale de votre mission, calculez la marge de sécurité :

*Utilisez la formule $MoS = \frac{\sigma_{allowable}}{FoS \times \sigma_{applied}} - 1$*

**Exemple résolu :** pour l'Al 7075-T6 ($\sigma_{yield}$ = 503 MPa), contrainte appliquée = 200 MPa, FoS (limite d'élasticité) = 1,25 :

$MoS = \frac{503}{1.25 \times 200} - 1 = \frac{503}{250} - 1 = 1.012$

La marge est positive (conforme).

**Votre calcul :**

Matériau : __________ , $\sigma_{allowable}$ = __________ MPa

$\sigma_{applied}$ = __________ MPa, FoS = __________

$MoS$ = __________ (détaillez le calcul ci-dessous)

_______________________________________________

_______________________________________________

---

## Partie E : Vérifications de conformité dans SpaceCDF

SpaceCDF n'a pas de panneau de conformité unique : chaque vérification se trouve là où se fait cette partie de la conception. Trouvez-les et répondez :

1. Quel est l'état de votre mission en matière d'atténuation des débris ? (Décider › Étude de compromis d'orbite, colonnes Durée de vie, 25 ans et FCC 5 ans ; Exporter › Conformité désorbitation et débris)

   _______________________________________________

2. Quelle altitude orbitale faudrait-il pour respecter la règle FCC des 5 ans SANS propulsion ? (Comparez la durée de vie naturelle des candidates dans Décider › Étude de compromis d'orbite.)

   _______________________________________________

3. Quelles normes SpaceCDF cite-t-il pour votre conception ? (Exporter › Matrice de conformité ECSS ; des écrans comme Interfaces et Schémas nomment la norme qu'ils suivent)

   _______________________________________________

   _______________________________________________

4. Votre conception actuelle présente-t-elle des signalements de conformité (avertissements ou erreurs) ? (Analyses › Conflits)

   _______________________________________________

   _______________________________________________

---

## Notes et réflexions

Notez les points clés concernant l'applicabilité des normes, les difficultés de conformité et les conséquences sur la conception de votre mission :

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Fiche 1.4 : Besoins de mission, études de compromis et concept d'opérations

| | |
|---|---|
| **Nom :** | __________________________________________ |
| **Date :** | __________________________________________ |
| **Équipe :** | __________________________________________ |
| **Séance :** | 1.4 -- Besoins de mission, études de compromis et ConOps |

---

## Partie A : Matrice d'analyse des parties prenantes

Identifiez au moins 4 parties prenantes de la mission de votre équipe. Pour chacune, relevez ses besoins, ses contraintes, sa priorité et son niveau d'influence.

| # | Partie prenante | Rôle | Besoins clés | Contraintes imposées | Priorité (P/S/T) | Influence (É/M/F) |
|---|-------------|------|-----------|--------------------|--------------------|-------------------|
| 1 | ____________ | ____________ | ________________________ | ________________________ | ______ | ______ |
| 2 | ____________ | ____________ | ________________________ | ________________________ | ______ | ______ |
| 3 | ____________ | ____________ | ________________________ | ________________________ | ______ | ______ |
| 4 | ____________ | ____________ | ________________________ | ________________________ | ______ | ______ |
| 5 | ____________ | ____________ | ________________________ | ________________________ | ______ | ______ |
| 6 | ____________ | ____________ | ________________________ | ________________________ | ______ | ______ |

*P = primaire (doit être satisfaite), S = secondaire (devrait être satisfaite), T = tertiaire (souhaitable)*
*É = influence élevée, M = moyenne, F = faible*

**Question :** quelle partie prenante a le plus d'influence sur votre mission ? Certaines parties prenantes ont-elles des besoins contradictoires ? Si oui, comment pourriez-vous résoudre ce conflit ?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

## Partie B : Énoncé du problème

Rédigez l'énoncé du problème de la mission de votre équipe. Il doit répondre aux quatre questions suivantes : quel est le problème ? Qui est concerné ? Quel est l'impact ? Quelles contraintes existent ?

**Énoncé du problème :**

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

**Liste de vérification pour l'évaluation par les pairs** (à échanger avec une autre équipe) :

| Critère | Validé ? | Commentaires |
|-----------|-------|---------|
| Décrit-il CE QUI est nécessaire, et non COMMENT y parvenir ? | ______ | _________________________________ |
| Identifie-t-il le manque de capacité ? | ______ | _________________________________ |
| Nomme-t-il précisément les parties prenantes concernées ? | ______ | _________________________________ |
| Quantifie-t-il l'impact d'une absence de solution ? | ______ | _________________________________ |
| Énonce-t-il les contraintes (budget, calendrier, réglementation) ? | ______ | _________________________________ |
| Est-il exempt de formulation de solution ? (Aucun type de satellite, orbite ou composant précis n'est nommé) | ______ | _________________________________ |

---

## Partie C : Objectifs de mission

Rédigez 2 à 3 objectifs de mission. Évaluez chacun d'eux au regard de la liste de critères de qualité.

**Objectif 1 :** _______________________________________________

_______________________________________________

| Critère de qualité | Oui/Non | Notes |
|-------------------|--------|-------|
| Énonce-t-il le QUOI, et non le COMMENT ? | ______ | _________________________________ |
| Comporte-t-il un critère mesurable avec un nombre et une unité ? | ______ | _________________________________ |
| Est-il réalisable avec la technologie actuelle (TRL $\geq$ 4) ? | ______ | _________________________________ |
| Est-il pertinent au regard de l'énoncé du problème ? | ______ | _________________________________ |
| Est-il traçable jusqu'à un besoin précis d'une partie prenante ? | ______ | _________________________________ |
| Est-il classé comme primaire ou secondaire ? | ______ | _________________________________ |

**Objectif 2 :** _______________________________________________

_______________________________________________

| Critère de qualité | Oui/Non | Notes |
|-------------------|--------|-------|
| Énonce-t-il le QUOI, et non le COMMENT ? | ______ | _________________________________ |
| Comporte-t-il un critère mesurable avec un nombre et une unité ? | ______ | _________________________________ |
| Est-il réalisable avec la technologie actuelle (TRL $\geq$ 4) ? | ______ | _________________________________ |
| Est-il pertinent au regard de l'énoncé du problème ? | ______ | _________________________________ |
| Est-il traçable jusqu'à un besoin précis d'une partie prenante ? | ______ | _________________________________ |
| Est-il classé comme primaire ou secondaire ? | ______ | _________________________________ |

**Objectif 3 (facultatif) :** _______________________________________________

_______________________________________________

---

## Partie D : Traçabilité MoE / MoP / TPM

Pour votre objectif primaire, retracez la hiérarchie des mesures :

**Objectif :** _______________________________________________

**MoE** (mesure d'efficacité -- efficacité opérationnelle du point de vue de l'utilisateur) :

_______________________________________________

_______________________________________________

**MoP** (mesure de performance -- performances techniques du système) :

_______________________________________________

_______________________________________________

**TPM** (indicateur de performance technique -- paramètre de conception suivi pendant le développement) :

_______________________________________________

_______________________________________________

*Indice : si votre objectif est « Fournir des images multispectrales avec une distance d'échantillonnage au sol (GSD) de 10 m… », alors :*
- *la MoE pourrait être « % de la zone cible couverte par des images exploitables (< 30 % de nébulosité) en 5 jours »*
- *la MoP pourrait être « GSD $\leq$ 10 m au nadir, RSB $\geq$ 100 dans toutes les bandes »*
- *le TPM pourrait être « estimation courante du diamètre d'ouverture (cible : 15 cm), masse de l'imageur (cible : 1,5 kg) »*

---

## Partie E : Étude de compromis -- solution spatiale ou non spatiale

Réalisez une étude de compromis pour déterminer si un satellite dédié est la bonne solution au besoin de votre mission.

**Énoncé de la décision :** _______________________________________________

**Solutions envisagées :**

| # | Solution | Description |
|---|------------|-------------|
| 1 | __________________________ | ________________________________________________ |
| 2 | __________________________ | ________________________________________________ |
| 3 | __________________________ | ________________________________________________ |
| 4 | Ne rien faire / statu quo | ________________________________________________ |

**Critères et pondérations** (leur somme doit valoir 1,0) :

*Utilisez la comparaison par paires ou l'attribution directe. Montrez ci-dessous comment vous avez obtenu les pondérations.*

| Critère | Pondération | Sens (plus élevé / plus faible = meilleur) |
|-----------|--------|-----------------------------------|
| __________________________ | ______ | __________ |
| __________________________ | ______ | __________ |
| __________________________ | ______ | __________ |
| __________________________ | ______ | __________ |
| __________________________ | ______ | __________ |
| **Total** | **1,00** | |

*Obtention des pondérations (tableau de comparaison par paires ou notes) :*

_______________________________________________

_______________________________________________

_______________________________________________

**Matrice de notation** (normalisée de 0 à 1) :

| Solution | Critère 1 | Critère 2 | Critère 3 | Critère 4 | Critère 5 | **Total pondéré** |
|------------|:-----------:|:-----------:|:-----------:|:-----------:|:-----------:|:-----------------:|
| 1 : ____________ | ______ | ______ | ______ | ______ | ______ | ______ |
| 2 : ____________ | ______ | ______ | ______ | ______ | ______ | ______ |
| 3 : ____________ | ______ | ______ | ______ | ______ | ______ | ______ |
| 4 : Ne rien faire | ______ | ______ | ______ | ______ | ______ | ______ |

*Rappel : total pondéré = $\sum w_c \times s(a,c)$*

**Résultat :** la solution qui obtient le meilleur score est : _______________________________________________

**Énoncé de la décision** (1 paragraphe -- présentez les 2 meilleures solutions et expliquez pourquoi l'une a été préférée à l'autre) :

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

**Contrôle de sensibilité :** si vous augmentez de 20 % la pondération de votre deuxième critère le plus important (puis renormalisez), le classement change-t-il ?

_______________________________________________

_______________________________________________

---

## Partie F : Plan du concept d'opérations

Documentez votre ConOps préliminaire en suivant la structure de l'annexe S du NASA SEH :

**1. Architecture de la mission :**

Segment spatial : _______________________________________________

Segment sol : _______________________________________________

Segment utilisateur : _______________________________________________

**2. Bilan de puissance moyenne sur l'orbite :**

*Calculez avec : $P_{avg} = \sum P_{mode,i} \times DC_i$*

| Mode | Puissance (W) | Rapport cyclique (fraction de l'orbite) | P x DC (W) |
|------|-----------|-------------------------------|-----------|
| Veille / servitude | __________ | __________ | __________ |
| Science / prise de vue | __________ | __________ | __________ |
| Liaison descendante | __________ | __________ | __________ |
| Éclipse | __________ | __________ | __________ |
| | | **Puissance moyenne sur l'orbite :** | **__________ W** |

Besoin du générateur solaire : $P_{SA}$ = __________ W

*Détaillez votre calcul :*

_______________________________________________

_______________________________________________

**3. Bilan de données :**

Volume de données produit par jour : __________ Go/jour

Capacité de liaison descendante par passage : __________ Go/passage

Passages par jour : __________

Capacité quotidienne de liaison descendante : __________ Go/jour

Équilibre (liaison descendante $\geq$ production) ? __________

---

## Partie G : Saisie dans l'outil SpaceCDF

Dans SpaceCDF, saisissez votre besoin de mission dans Définition de la mission (étapes 1 Problème, 2 Parties prenantes, 3 Solutions de rechange, 4 Architecture). Répondez ensuite aux questions suivantes :

1. À l'étape 1 (Problème), quel type de mission avez-vous choisi, et comment modifie-t-il les solutions de rechange proposées à l'étape 3 ?

   _______________________________________________

2. À l'étape 3 (Solutions de rechange), SpaceCDF analyse les solutions de rechange. Son classement correspond-il au résultat de l'étude de compromis manuelle de la partie E ?

   _______________________________________________

   _______________________________________________

3. Dans l'onglet Blocs, aux niveaux 0 et 1, combien de segments et de systèmes votre architecture comporte-t-elle ?

   _______________________________________________

4. Dans Décider › Étude de compromis d'orbite (niveau 0), évaluez les options d'orbite (au moins 3 candidates). Quelle orbite arrive en tête, et pourquoi ?

   _______________________________________________

---

## Notes et réflexions

Notez les décisions clés prises aujourd'hui, les questions en suspens et ce que vous souhaitez approfondir :

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Fiche 2.1 : Le cycle en V et l'ingénierie des exigences

| | |
|---|---|
| **Nom :** | _______________________________________ |
| **Date :** | _______________________________________ |
| **Équipe / mission :** | _______________________________________ |
| **Rôle / poste :** | _______________________________________ |

**Onglet SpaceCDF :** Exigences (Requirements)

---

## Rappel des équations clés

> **Couverture de traçabilité :**
> $$\text{Couverture} = \frac{N_{\text{verified requirements}}}{N_{\text{total requirements}}} \times 100\%$$
> Cible : 100 % -- chaque exigence doit avoir une traçabilité vers son exigence mère, une méthode de vérification et un sous-système responsable.

> **Qualité des exigences (SMART) :**
> **S**pécifique -- **M**esurable -- **A**tteignable -- **R**attachée au besoin (pertinente) -- **T**raçable

> **Méthodes de vérification (ATIR(D)) :**
> **A**nalyse -- **T**est (essai) -- **I**nspection -- **R**evue de conception -- (**D**émonstration, que l'ECSS compte dans l'essai et que la NASA présente à part)

---

## Partie A : Correspondance avec le cycle en V

Pour votre mission, identifiez un élément à chaque niveau du cycle en V :

| Niveau du V | Branche gauche (décomposition) | Branche droite (vérification) |
|---------|---------------------------|---------------------------|
| **Besoin des parties prenantes** | | |
| **Exigence de mission** | | |
| **Exigence système** | | |
| **Exigence sous-système** | | |

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Partie B : Évaluation de la qualité des exigences

Évaluez chaque exigence à l'aide de la liste SMART et des critères de l'annexe C de la NASA. Indiquez Conforme (C) ou Non conforme (N). Réécrivez toute exigence non conforme.

| # | Exigence | S | M | A | R | T | QUOI ou COMMENT ? | Réécriture (si nécessaire) |
|---|------------|---|---|---|---|---|-------------|---------------------|
| 1 | « Le satellite doit fonctionner à 500 km d'altitude » | | | | | | | |
| 2 | « Le système doit atteindre une GSD <= 10 m au nadir » | | | | | | | |
| 3 | « L'EPS doit utiliser des cellules GaAs à triple jonction » | | | | | | | |
| 4 | « Le système doit avoir une durée de vie nominale d'au moins 3 ans » | | | | | | | |
| 5 | « La structure doit être en aluminium 7075 » | | | | | | | |

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Partie C : Hiérarchie et traçabilité des exigences

Pour votre mission, rédigez une exigence à chaque niveau. Tracez la chaîne de traçabilité.

**Objectif des parties prenantes (origine de la traçabilité) :** _________________________________________

_____________________________________________________________________

**Exigence de mission (MR-___) :** ______________________________________________

_____________________________________________________________________

**Exigence système (SR-___), dérivée de la MR ci-dessus :** __________________________

_____________________________________________________________________

**Exigence sous-système (SSR-___), dérivée de la SR ci-dessus :** _____________________

_____________________________________________________________________

**Diagramme de traçabilité** (tracez des flèches montrant les relations mère-fille) :

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Partie D : Décomposition des exigences composées

Décomposez cette exigence composée en énoncés vérifiables individuellement :

> « Le système doit fournir des images multispectrales d'une GSD de 10 m avec une revisite de 5 jours, une latence des données de 24 heures et une marge de puissance positive dans tous les modes opérationnels, y compris en éclipse. »

| # | Exigence décomposée (un seul objet chacune) | Type (F/P/I/C/E) | Vérification (A/T/I/D) | Phase |
|---|--------------------------------------|-------------------|------------------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

_____________________________________________________________________

_____________________________________________________________________

---

## Partie E : Génération des exigences dans SpaceCDF

1. À la création de l'étude, SpaceCDF a rédigé une exigence de mission par objectif (onglet Exigences, niveau 0). Combien y en a-t-il, et combien de Modèles suggérés l'onglet propose-t-il ? ____

2. Comptez les exigences à chaque niveau (V&V › Exigences donne les totaux) :
   - Mission : ____     Système : ____     Sous-système : ____

3. Classez 5 exigences par type :

| ID exig. | Texte de l'exigence (abrégé) | Type (fonctionnelle / performance / interface / contrainte / environnement) |
|--------|-------------------------------|-------------------------------------------------------------------------|
| | | |
| | | |
| | | |
| | | |
| | | |

4. Trouvez une exigence qui énonce le COMMENT (mise en œuvre) et non le QUOI. Recopiez-la avec votre correction :

   - **Originale :** _______________________________________________
   - **Corrigée :** _______________________________________________

5. Passez au moins 5 exigences à l'état Approuvée et rejetez-en au moins 1 (supprimez-la ou réécrivez-la). Consignez vos décisions :

| ID exig. | Action (accepter/modifier/rejeter) | Justification |
|--------|----------------------------|-----------|
| | | |
| | | |
| | | |
| | | |
| | | |
| | | |

6. Pour 5 exigences clés, choisissez la méthode de vérification dans l'onglet Exigences et indiquez la phase :

| ID exig. | Méthode de vérification (A/T/I/D) | Phase (B/C/D/E) | Justification de la méthode |
|--------|-------------------------------|-----------------|---------------------|
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |

---

## Notes et réflexions

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

# Fiche 2.2 : Décomposition fonctionnelle et allocation

| | |
|---|---|
| **Nom :** | _______________________________________ |
| **Date :** | _______________________________________ |
| **Équipe / mission :** | _______________________________________ |
| **Rôle / poste :** | _______________________________________ |

**Onglet SpaceCDF :** Fonctions (Functions)

---

## Rappel des équations clés

> **Types de fonctions :** observer, communiquer, naviguer, pointer, alimenter, protéger, stocker, traiter, soutenir
>
> **Fonctions universelles (tout engin spatial) :**
> 1. Produire l'énergie électrique
> 2. Maintenir l'environnement thermique
> 3. Survivre à l'environnement de lancement
> 4. Communiquer avec le sol (TTC)
> 5. Assurer le retrait de service en fin de vie
>
> **Règle de couverture :** chaque fonction terminale doit être tracée vers au moins une exigence. Aucune lacune.
>
> **Règle d'allocation :** les fonctions allouées à plusieurs sous-systèmes créent des interfaces qui doivent être gérées explicitement.

---

## Partie A : Arbre fonctionnel de la mission

Tracez l'arbre fonctionnel complet de votre mission. Utilisez au moins 3 niveaux de décomposition. Incluez à la fois les fonctions propres à la mission et les fonctions universelles.

**Fonctions propres à la mission :**

```
F-001: _______________________________________________
  +-- F-002: _______________________________________________
      +-- F-002a: ___________________________________________
      +-- F-002b: ___________________________________________
  +-- F-003: _______________________________________________
      +-- F-003a: ___________________________________________
  +-- F-004: _______________________________________________
  +-- F-005: _______________________________________________
```

**Fonctions universelles :**

```
F-010 : Produire l'énergie électrique
  +-- F-011 : _______________________________________________
  +-- F-012 : _______________________________________________
F-020 : Maintenir l'environnement thermique
  +-- F-021 : _______________________________________________
F-030 : Résister à l'environnement de lancement
F-040 : Communiquer avec le sol (TTC)
F-050 : Retirer le satellite du service en fin de vie
```

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Partie B : Traçabilité des fonctions vers les exigences

Pour chaque fonction terminale, rédigez une exigence dérivée assortie d'un seuil mesurable :

| ID de la fonction | Nom de la fonction | Allouée à (sous-système) | Exigence dérivée | Type |
|-------------|--------------|-------------------------|-------------------|------|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

_____________________________________________________________________

_____________________________________________________________________

---

## Partie C : Analyse des allocations multiples

Identifiez au moins une fonction allouée à plus d'un sous-système :

**Fonction :** _______________________________________________

**Sous-système A (principal) :** _______________________________________________

**Sous-système B (contributeur) :** _______________________________________________

**Interface créée entre A et B :** _______________________________________________

_____________________________________________________________________

**Qui est « propriétaire » de cette fonction ?** _______________________________________________

**Quelles exigences d'interface sont nécessaires ?** _______________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Partie D : Critères de performance

Pour 4 fonctions clés, définissez des critères de performance quantitatifs :

| Fonction | Critère de performance | Valeur | Unité | Source |
|----------|----------------------|-------|------|--------|
| | | | | |
| | | | | |
| | | | | |
| | | | | |

---

## Partie E : Vérification de la couverture dans SpaceCDF

Après avoir saisi les fonctions dans SpaceCDF :

1. Combien de fonctions votre arbre compte-t-il au total ? ____

2. Combien de fonctions terminales ? ____

3. Combien de fonctions sont encore non allouées (étiquette « non allouée »), et quelles fonctions terminales ne sont reliées à aucune exigence (onglet Traçabilité) ? ____

4. Énumérez les fonctions non couvertes et dérivez-en des exigences :

| ID de la fonction | Nom de la fonction | Exigence dérivée |
|-------------|--------------|-------------------|
| | | |
| | | |
| | | |

5. L'outil a-t-il généré des fonctions qui ne conviennent PAS à votre mission ? Énumérez-les et expliquez pourquoi vous les avez supprimées :

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Notes et réflexions

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

# Fiche 2.3 : Choix de l'orbite et architecture de la mission

| | |
|---|---|
| **Nom :** | _______________________________________ |
| **Date :** | _______________________________________ |
| **Équipe / mission :** | _______________________________________ |
| **Rôle / poste :** | _______________________________________ |

**Onglets SpaceCDF :** Blocs (niveaux 0–1), Décider › Étude de compromis d'orbite, Analyses › Boucle de conception

---

## Rappel des équations clés

> **Période orbitale :** $T = 2\pi \sqrt{a^3/\mu}$    où $a = R_E + h$, $\mu = 3.986 \times 10^{14}$ m$^3$/s$^2$, $R_E = 6371$ km
>
> **Vitesse orbitale :** $v = \sqrt{\mu/a}$
>
> **Fraction d'éclipse :** $f_{\text{ecl}} = \frac{1}{\pi} \arccos\left(\frac{\sqrt{a^2 - R_E^2}}{a}\right)$
>
> **Inclinaison héliosynchrone :** $\cos(i) = -\frac{2\dot{\Omega} a^{7/2}}{3 R_E^2 J_2 \sqrt{\mu}}$    où $J_2 = 1.0826 \times 10^{-3}$
>
> **$\Delta V$ de Hohmann :** $\Delta V_1 = \sqrt{\mu/r_1}\left(\sqrt{2r_2/(r_1+r_2)} - 1\right)$
>
> **Largeur de fauchée :** $W = 2h\tan(\theta)$

---

## Partie A : Calculs de mécanique spatiale

**Orbite retenue :** altitude $h$ = _____ km,   inclinaison $i$ = _____°,   type : __________

Détaillez tous les calculs :

**1. Demi-grand axe :**

$a = R_E + h = 6371 + $ _____ $= $ _____ km $= $ _____ m

_____________________________________________________________________

**2. Période orbitale :**

$T = 2\pi\sqrt{a^3/\mu} = 2\pi\sqrt{$ _____ $^3 /\ 3.986 \times 10^{14}} = $ _____ s $= $ _____ min

_____________________________________________________________________

_____________________________________________________________________

**3. Vitesse orbitale :**

$v = \sqrt{\mu/a} = \sqrt{3.986 \times 10^{14} /\ }$ _____ $= $ _____ m/s

_____________________________________________________________________

**4. Fraction d'éclipse (maximale) :**

$f = \frac{1}{\pi}\arccos\left(\frac{\sqrt{a^2 - R_E^2}}{a}\right) = \frac{1}{\pi}\arccos\left(\frac{\sqrt{\ }}{\ }\right) = $ _____

_____________________________________________________________________

_____________________________________________________________________

**5. Durées d'ensoleillement et d'éclipse par orbite :**

$t_{\text{sun}} = T \times (1 - f) = $ _____ $\times$ _____ $= $ _____ min

$t_{\text{ecl}} = T \times f = $ _____ $\times$ _____ $= $ _____ min

**6. Inclinaison héliosynchrone** (le cas échéant) :

$\cos(i) = $ _____ $\Rightarrow i = $ _____°

Correspond-elle à l'inclinaison retenue ? O / N

_____________________________________________________________________

---

## Partie B : Matrice de compromis d'orbite

Relevez dans Décider › Étude de compromis d'orbite (niveau 0) les 3 meilleures orbites candidates :

| Rang | Type d'orbite | Alt. (km) | Inc. (°) | GSD (m) | Revisite (j) | Durée de vie naturelle (ans) | FCC 5 ans ? | Score |
|------|-----------|---------|---------|---------|-------------|----------------------|-----------|-------|
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |

**Orbite retenue :** ___________ **Justification :** ___________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Partie C : Conformité en matière de débris

Pour l'orbite retenue :

| Paramètre | Valeur |
|-----------|-------|
| Durée de vie orbitale naturelle | _____ ans |
| Conforme à la règle FCC des 5 ans ? | O / N |
| Conforme à la règle IADC des 25 ans ? | O / N |
| Propulsion nécessaire pour la désorbitation ? | O / N |
| Si oui, $\Delta V$ de désorbitation estimé | _____ m/s |
| Méthode de désorbitation (si nécessaire) | _____________________________________ |

**Détaillez le calcul du $\Delta V$ si une propulsion est nécessaire :**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Partie D : Analyse des répercussions en aval

Comment le choix de l'orbite influe-t-il sur chaque sous-système ? Complétez les répercussions :

| Sous-système | Paramètre orbital déterminant | Répercussion sur votre conception |
|-----------|-----------------------------|-----------------------|
| Charge utile (GSD) | Altitude = _____ km | GSD = _____ m |
| EPS (éclipse) | Fraction d'éclipse = _____ | Durée d'éclipse = _____ min |
| Télécom (liaison) | Distance oblique à 10° d'élévation = _____ km | Augmentation de l'affaiblissement en espace libre = _____ dB |
| Thermique | Alternance éclipse/ensoleillement | Préoccupation cas chaud / cas froid : ______ |
| SCAO | Vitesse angulaire orbitale = _____ °/min | Vitesse de suivi du nadir nécessaire |
| Propulsion | Durée de vie = _____ ans | Propulsion nécessaire ? O / N |
| Rayonnement | Estimation de la TID = _____ krad/an | Classe d'électronique : ____________ |

---

## Partie E : Discussion

Qu'arriverait-il à votre mission si vous releviez l'orbite de **100 km** ?

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

Qu'arriverait-il si vous l'abaissiez de **100 km** ?

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Notes et réflexions

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

# Fiche 2.4 : Architecture de la mission -- segments, interfaces et bilans

| | |
|---|---|
| **Nom :** | _______________________________________ |
| **Date :** | _______________________________________ |
| **Équipe / mission :** | _______________________________________ |
| **Rôle / poste :** | _______________________________________ |

**Onglets SpaceCDF :** Blocs, Interfaces, Bilans, Modes, V&V › Bilans consolidés

---

## Rappel des équations clés

> **Marge de masse :** $\text{Marge}_\% = \frac{M_{\text{alloc}} - M_{\text{MEV}}}{M_{\text{alloc}}} \times 100\%$
>    Vert : > 20 % | Orange : 10--20 % | Rouge : < 10 %
>
> **MEV :** $M_{\text{MEV}} = M_{\text{CBE}} + \text{marge équipement} + \text{marge système}$
>
> **Puissance moyenne sur l'orbite :** $P_{\text{avg}} = \sum (P_{\text{mode}} \times f_{\text{duty}})$
>
> **Puissance du générateur solaire :** $P_{\text{SA}} = P_{\text{peak}} + \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{t_{\text{sun}} \times \eta_{\text{charge}}}$
>
> **Marges ECSS en phase A :** équipement 20 % + système 20 % = env. 44 % en cumulé

---

## Partie A : Bilan de masse

Complétez à partir de votre conception SpaceCDF (ou par estimation si l'outil n'a pas encore été utilisé). Bilans › Masse affiche la valeur nominale (meilleure estimation actuelle) et la marge de maturité de chaque élément, puis la marge système de 25 % ; comparez-les à la marge d'équipement de 20 % utilisée ici :

| Sous-système | Masse CBE (kg) | % de la masse sèche | Marge équip. (20 %) | MEV (kg) |
|-----------|--------------|----------|---------------------|---------|
| Charge utile | | | | |
| EPS | | | | |
| SCAO | | | | |
| Télécom (TTC) | | | | |
| OBC | | | | |
| Thermique | | | | |
| Structure | | | | |
| Harnais | | | | |
| Propulsion | | | | |
| **Total sec (CBE)** | | 100 % | | |
| **Marge système (20 %)** | | | | |
| **MEV sèche** | | | | |
| Ergols | | | | |
| **Masse humide** | | | | |
| **Allocation lanceur** | | | | |
| **Marge de masse** | | | | |
| **Marge de masse (%)** | | | V / O / R | |

**Détaillez le calcul de la marge :**

_____________________________________________________________________

_____________________________________________________________________

---

## Partie B : Bilan de puissance par mode

Modes › Puissance par mode donne la puissance de chaque unité dans les modes de l'outil (LEOP, mise en service, nominal, prise de vue, liaison descendante, survie, survie extrême) ; utilisez le mode nominal pour la veille. L'éclipse est un cas, pas un mode : Modes › Énergie par orbite montre comment chaque mode traverse l'éclipse.

| Sous-système | Survie (W) | Veille (W) | Prise de vue (W) | Liaison desc. (W) | Éclipse (W) |
|-----------|---------|---------|-------------|-------------|-------------|
| OBC | | | | | |
| SCAO | | | | | |
| Charge utile | | | | | |
| Télécom (TX) | | | | | |
| Thermique | | | | | |
| **Total** | | | | | |
| **Rapport cyclique (%)** | | | | | |

**Calcul de la puissance moyenne sur l'orbite (détaillez) :**

$P_{\text{avg}} = $ _____ $\times$ _____ $+$ _____ $\times$ _____ $+$ _____ $\times$ _____ $+$ _____ $\times$ _____ $= $ _____ W

_____________________________________________________________________

**Puissance requise du générateur solaire :**

$P_{\text{recharge}} = \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{t_{\text{sun}} \times \eta_{\text{charge}}} = \frac{\ \ \ \ \times \ \ \ \ }{\ \ \ \ \times 0.9} = $ _____ W

$P_{\text{SA,EOL}} = P_{\text{peak}} + P_{\text{recharge}} = $ _____ $+$ _____ $= $ _____ W

$P_{\text{SA,BOL}} = P_{\text{SA,EOL}} / (1 - 0.025)^n = $ _____ $/ $ _____ $= $ _____ W

_____________________________________________________________________

---

## Partie C : Identification des interfaces

Énumérez les 5 interfaces les plus critiques de votre conception :

| # | Sous-système A | Sous-système B | Types d'interface (M/E/T/D/R/O) | Préoccupation principale |
|---|-------------|-------------|-------------------------------|-------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Rédigez 2 exigences d'interface formelles** pour votre paire la plus critique :

Interface : ____________ <-> ____________

**IR-001 :** _______________________________________________

_____________________________________________________________________

**IR-002 :** _______________________________________________

_____________________________________________________________________

Méthode de vérification pour IR-001 : _____   IR-002 : _____

---

## Partie D : Résolution de conflit

Dans Analyses › Conflits (ou d'après un bloc orange de l'onglet Satellite), identifiez un conflit :

**Description du conflit :** _______________________________________________

_____________________________________________________________________

**Gravité :** critique / majeure / mineure

**Options de résolution envisagées :**

| # | Option | Avantages | Inconvénients |
|---|--------|------|------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

**Résolution retenue :** _______________________________________________

**Justification :** _______________________________________________

---

## Partie E : Contrôle de l'état des bilans

Dans l'onglet Bilans (Masse, Puissance, Données, Coût) et dans V&V › Bilans consolidés, relevez chaque bilan :

| Bilan | Valeur | Marge | État (V/O/R) |
|--------|-------|--------|----------------|
| Masse | _____ kg (humide) vs _____ kg (allocation) | _____ % | |
| Puissance (mode le plus défavorable) | _____ W vs _____ W (générateur solaire) | _____ % | |
| Liaison | marge de _____ dB | >= 3 dB ? | |
| Coût | _____ M€ vs _____ (plafond) | _____ % | |
| Pointage | _____° vs _____° (exigence) | _____ % | |

**Quel bilan est le plus tendu ?** _______________________________________________

**Quelle modification de conception unique l'améliorerait ?** ____________________________

_____________________________________________________________________

---

## Notes et réflexions

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

# Fiche 3.1 : Conception du sous-système d'alimentation électrique et du contrôle thermique

| | |
|---|---|
| **Nom :** | _______________________________________ |
| **Date :** | _______________________________________ |
| **Équipe / mission :** | _______________________________________ |
| **Rôle / poste :** | _______________________________________ |

**Onglets SpaceCDF :** Analyses › Boucle de conception (dimensionnement électrique), Modes › Énergie par orbite, Analyses › Physique (réseau thermique), Bilans › Puissance

---

## Aide-mémoire : notions de puissance et de thermique

### Qu'est-ce qu'un générateur solaire ?

Un générateur solaire convertit la lumière du Soleil en énergie électrique au moyen de cellules photovoltaïques. Dans l'espace, le flux solaire (appelé constante solaire) vaut $S = 1361$ W/m$^2$ à 1 UA du Soleil -- environ 40 % de plus qu'à la surface de la Terre, car aucune atmosphère n'absorbe une partie du spectre.

**Types de cellules solaires et rendement (AM0, spectre spatial) :**

| Technologie de cellule | Rendement typique | Taux de dégradation | Coût relatif | Notes |
|----------------|-------------------|------------------|--------------|-------|
| Silicium (Si) | 16--18 % | ~3,5 %/an | Faible | Technologie ancienne ; rarement utilisée dans les nouvelles missions |
| Arséniure de gallium (GaAs) à simple jonction | 22--24 % | ~2,5 %/an | Moyen | Bonne tenue au rayonnement |
| GaAs à triple jonction (InGaP/GaAs/Ge) | 28--30 % | ~2,5 %/an | Élevé | Standard actuel des CubeSat |
| Multijonction (4J, 5J) | 32--35 % | ~2 %/an | Très élevé | Émergente ; utilisée sur les missions phares |

Pour la conception d'un CubeSat, supposez des **cellules GaAs à triple jonction d'un rendement de 29,5 %** ($\eta = 0.295$). Les cellules sont montées sur des panneaux avec un **taux de remplissage** $f_{\text{pack}} = 0.80$--$0.85$ : 80 à 85 % de la surface du panneau est réellement couverte de cellules actives (le reste correspond aux interstices, au câblage et à la marge structurale).

**Dégradation :** les cellules solaires perdent du rendement au fil du temps sous l'effet des dommages dus au rayonnement (bombardement de protons et d'électrons dans les ceintures de Van Allen). Avec un taux de $\delta = 2.5\%$ par an, le rendement restant après $n$ années vaut $(1 - 0.025)^n$. Une mission de 3 ans perd ainsi environ 7,3 % de sa puissance en début de vie (BOL), et une mission de 5 ans environ 11,9 %.

### Générateurs solaires fixés sur la structure ou déployables

| Configuration | Avantages | Inconvénients | Puissance typique |
|--------------|-----------|---------------|---------------|
| **Fixé sur la structure** | Aucune pièce mobile, aucun risque de déploiement, aucune pénalité de volume replié | Surface limitée (seules les faces éclairées), puissance variable selon l'attitude | 1U : ~2 W, 3U : ~7 W, 6U : ~12 W |
| **Simple déployable** | Surface accrue, complexité modérée | Un mécanisme, masque partiellement le champ de vue | 1U : ~4 W, 3U : ~15 W, 6U : ~30 W |
| **Double déployable** | Surface maximale pour le format | Deux mécanismes, volume replié plus important, risque de déploiement | 3U : ~25 W, 6U : ~48 W |

**Règle empirique :** si votre besoin total en puissance (recharge de la batterie comprise) dépasse ce que des panneaux fixés sur la structure peuvent fournir, il vous faut des panneaux déployables. Comparez votre $P_{\text{SA,BOL}}$ aux valeurs de puissance de référence ci-dessus.

### Fonctionnement des batteries dans l'espace

Les batteries stockent l'énergie électrique qui alimente le satellite pendant l'éclipse (lorsqu'il se trouve dans l'ombre de la Terre et ne reçoit aucune lumière solaire). En LEO, les éclipses se produisent à chaque orbite -- typiquement 30 à 36 minutes sur une période orbitale d'environ 95 minutes.

**Paramètres clés d'une batterie :**

- **Profondeur de décharge (DOD) :** fraction de la capacité totale de la batterie utilisée à chaque cycle. Une DOD plus faible allonge considérablement la durée de vie en cycles, mais exige une batterie plus grosse (plus lourde).
- **Durée de vie en cycles :** nombre de cycles de charge/décharge avant que la capacité de la batterie ne tombe sous 80 % de sa valeur initiale.
- **Énergie massique :** énergie stockée par unité de masse (Wh/kg). Pour des éléments Li-ion 18650 de qualité spatiale : 150 à 200 Wh/kg.

| DOD | Durée de vie typique en cycles (Li-ion 18650) | Durée de mission adaptée |
|-----|----------------------------------|--------------------------|
| 80 % | ~500 cycles | Missions courtes (< 1 mois) |
| 50 % | ~2000 cycles | Missions moyennes (< 6 mois) |
| 30 % | ~10 000 cycles | Missions LEO pluriannuelles |
| 20 % | ~30 000 cycles | LEO longue durée (> 5 ans) |

**Recommandation de conception :** pour une mission LEO pluriannuelle (15 orbites/jour), retenez DOD = 30 %. Pour une démonstration technologique de 6 mois, une DOD de 50 % est acceptable.

### Que fait l'EPS ?

Le sous-système d'alimentation électrique (EPS) est le fournisseur d'énergie du satellite. Une carte EPS typique de CubeSat (p. ex. GomSpace P31u) comprend :

- **MPPT (recherche du point de puissance maximale) :** convertisseur continu-continu qui ajuste en permanence la tension de fonctionnement du générateur solaire pour en extraire la puissance maximale. Rendement : 90 à 95 %.
- **Contrôleur de charge de la batterie :** gère la charge de la batterie avec des limites de tension et de courant afin de préserver sa durée de vie.
- **Rails de tension régulée :** fournissent des tensions fixes (typiquement 3,3 V, 5 V et la tension non régulée de la batterie) à tous les sous-systèmes.
- **Sorties commutées :** permettent à l'OBC d'allumer et d'éteindre les sous-systèmes pour la gestion de la puissance et le mode survie.
- **Protection contre les surintensités :** protège contre les courts-circuits dans n'importe quel sous-système.

### Notions de base du contrôle thermique

Dans l'espace, il n'y a pas d'air permettant la convection. Les transferts de chaleur se font uniquement par **rayonnement** et par **conduction**. Un engin spatial atteint l'équilibre thermique lorsque la chaleur absorbée (flux solaire, albédo terrestre, rayonnement infrarouge terrestre, chaleur dissipée par l'électronique interne) est égale à la chaleur rayonnée (vers l'espace profond, à ~3 K).

**Marges thermiques (convention pédagogique du manuel, tableau 3.1.11 ; le TVAC de protovol se fait à la prévision $\pm$10 °C selon le GSFC-STD-7000B) :** fonctionnement $\pm$5 °C, recette $\pm$10 °C, qualification $\pm$15 °C. Si la température prévue d'un composant se situe à moins de 5 °C de sa limite de fonctionnement, vous devez ajouter un moyen de contrôle thermique (réchauffeur, modification du revêtement ou radiateur).

---

## Rappel des équations clés

> **Puissance du générateur solaire en fin de vie :** $P_{\text{SA,EOL}} = P_{\text{peak}} + \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{t_{\text{sun}} \times \eta_{\text{charge}}}$
>
> **Puissance du générateur solaire en début de vie :** $P_{\text{SA,BOL}} = \frac{P_{\text{SA,EOL}}}{(1 - \delta)^n}$    ($\delta = 0.025$/an pour le GaAs)
>
> **Surface du générateur solaire :** $A = \frac{P_{\text{BOL}}}{\eta_{\text{cell}} \times S \times \cos\theta \times f_{\text{pack}}}$    ($\eta = 0.295$, $S = 1361$ W/m$^2$, $f_{\text{pack}} = 0.85$)
>
> **Capacité de la batterie :** $C = \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{DOD \times \eta_{\text{discharge}}}$    ($DOD = 0.30$, $\eta = 0.95$)
>
> **Équilibre thermique :** $T = \left(\frac{Q_{\text{abs}} + Q_{\text{int}}}{\varepsilon \sigma A_{\text{rad}}}\right)^{1/4}$    ($\sigma = 5.67 \times 10^{-8}$ W/m$^2$/K$^4$)
>
> **Marges thermiques (convention du manuel) :** fonctionnement +/-5 °C, recette +/-10 °C, qualification +/-15 °C

---

## Exemple résolu : puissance et thermique d'UniSat-1 (1U)

### Dimensionnement du générateur solaire (fixé sur la structure)

UniSat-1 utilise des cellules solaires fixées sur 5 faces (la 6e face est l'interface de déploiement). Orbite de l'ISS : 400 km d'altitude, période de 92,4 min, 56 min d'ensoleillement, 36 min d'éclipse.

**Données :** $P_{\text{peak,sunlight}} = 1.2$ W, $P_{\text{eclipse}} = 0.5$ W (OBC seul), durée de mission = 6 mois.

**Étape 1 -- Surface éclairée effective (attitude magnétique passive, ~1,5 face en moyenne) :**

$A_{\text{eff}} = 1.5 \times (0.10 \times 0.10) = 0.015$ m$^2$

**Étape 2 -- Puissance du générateur solaire en début de vie :**

$P_{\text{SA,BOL}} = \eta \times S \times A_{\text{eff}} \times f_{\text{pack}} = 0.295 \times 1361 \times 0.015 \times 0.80 = 4.82$ W (crête en éclairement)

**Étape 3 -- Puissance moyenne disponible sur l'orbite :**

$P_{\text{avg}} = P_{\text{SA,BOL}} \times \frac{t_{\text{sun}}}{T_{\text{orbit}}} \times \eta_{\text{EPS}} = 4.82 \times \frac{56}{92.4} \times 0.85 = 2.48$ W

**Étape 4 -- Après 6 mois de dégradation :**

$(1 - 0.025)^{0.5} = 0.987$, donc $P_{\text{avg,EOL}} = 2.48 \times 0.987 = 2.45$ W

**Étape 5 -- Besoin en puissance :** $P_{\text{avg,demand}} = 0.68$ W. Marge = $2.45 - 0.68 = 1.77$ W (72 %). **Confortable.**

### Dimensionnement de la batterie

**Données :** $P_{\text{ecl}} = 0.5$ W, $t_{\text{ecl}} = 36$ min $= 0.60$ h, $DOD = 0.50$ (acceptable pour une mission de 6 mois), $\eta = 0.95$.

$C_{\text{bat}} = \frac{0.5 \times 0.60}{0.50 \times 0.95} = \frac{0.30}{0.475} = 0.63$ Wh

Spécifiez au minimum **10 Wh** (batterie standard GomSpace NanoPower P31u). DOD réelle par éclipse = 0,63/10 = 6,3 %. Nombre de cycles : 6 mois à 15 orbites/jour = 2740 éclipses. Avec une DOD réelle de 6,3 %, la durée de vie de la batterie n'est pas un problème. **Conforme.**

### Vérification thermique (contrôle passif uniquement)

UniSat-1 n'utilise ni réchauffeur ni isolant multicouche (MLI). À 400 km, le fort rayonnement infrarouge terrestre (~240 W/m$^2$) assure un plancher chaud. Avec une électronique COTS spécifiée de −20 à +60 °C et une orbite à 400 km, l'environnement thermique reste compris entre environ −10 et +45 °C pour un 1U à surfaces en aluminium anodisé. Un calcul simplifié d'équilibre en cas froid donne une température d'équilibre très basse, mais l'inertie thermique d'un CubeSat de 1 kg limite le refroidissement réel pendant les éclipses de 36 minutes. **Aucun réchauffeur n'est nécessaire pour une mission de 6 mois à 400 km.**

---

## Partie A : Dimensionnement du générateur solaire

Détaillez tous les calculs étape par étape.

**1. Besoin en puissance crête en ensoleillement :** $P_{\text{peak}} = $ _____ W (mode : _____________)

**2. Besoin en puissance en éclipse :** $P_{\text{ecl}} = $ _____ W

**3. Durées d'éclipse et d'ensoleillement (d'après la fiche 2.3) :**

$t_{\text{ecl}} = $ _____ min     $t_{\text{sun}} = $ _____ min

**4. Puissance de recharge :**

$P_{\text{recharge}} = \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{t_{\text{sun}} \times \eta_{\text{charge}}} = \frac{\ \ \ \ \ \times \ \ \ \ \ }{\ \ \ \ \ \times 0.9} = $ _____ W

_____________________________________________________________________

**5. Puissance du générateur solaire requise en fin de vie :**

$P_{\text{SA,EOL}} = P_{\text{peak}} + P_{\text{recharge}} = $ _____ $+$ _____ $= $ _____ W

**6. Facteur de dégradation en fin de vie** (durée de mission = _____ ans, $\delta = 0.025$/an) :

$(1 - 0.025)^{\ \ \ } = $ _____

**7. Puissance du générateur solaire requise en début de vie :**

$P_{\text{SA,BOL}} = \frac{P_{\text{SA,EOL}}}{(1-\delta)^n} = \frac{\ \ \ \ \ }{\ \ \ \ \ } = $ _____ W

_____________________________________________________________________

**8. Surface du générateur solaire :**

$A = \frac{P_{\text{BOL}}}{0.295 \times 1361 \times \cos(\ \ \ ) \times 0.85} = \frac{\ \ \ \ \ }{\ \ \ \ \ } = $ _____ m$^2$

_____________________________________________________________________

**9. Type de générateur solaire nécessaire** (comparez aux valeurs de référence des CubeSat) :

- [ ] Fixé sur la structure uniquement (1U : ~2 W, 3U : ~7 W, 6U : ~12 W)
- [ ] Simple déployable (1U : ~4 W, 3U : ~15 W, 6U : ~30 W)
- [ ] Double déployable (3U : ~25 W, 6U : ~48 W)

**10. Masse du générateur solaire :**

$m_{\text{SA}} = A \times \sigma = $ _____ $\times$ _____ $= $ _____ kg

(fixé sur la structure : $\sigma = 2.5$ kg/m$^2$ ; déployable : $\sigma = 1.5$ kg/m$^2$)

---

## Partie B : Dimensionnement de la batterie

Détaillez tous les calculs :

**1. Énergie consommée en éclipse :**

$E = P_{\text{ecl}} \times \frac{t_{\text{ecl}}}{60} = $ _____ $\times$ _____ $= $ _____ Wh

**2. Capacité de batterie requise :**

$C = \frac{E}{DOD \times \eta} = \frac{\ \ \ \ \ }{0.30 \times 0.95} = \frac{\ \ \ \ \ }{0.285} = $ _____ Wh

**3. Avec une marge de 20 % :** $C_{\text{spec}} = $ _____ $\times 1.2 = $ _____ Wh

_____________________________________________________________________

**4. Masse de la batterie :**

$m_{\text{bat}} = \frac{C_{\text{spec}}}{E_{\text{specific}}} = \frac{\ \ \ \ \ }{150} = $ _____ kg

**5. Vérification de la durée de vie en cycles :**

Nombre d'éclipses pendant la mission = _____ orbites/jour $\times$ 365 $\times$ _____ ans $= $ _____ cycles

Avec une DOD de 30 %, une batterie Li-ion tient ~10 000 cycles. Est-ce suffisant ? O / N

_____________________________________________________________________

---

## Partie C : Analyse thermique

**1. Identifiez le cas chaud et le cas froid pour votre orbite :**

| Paramètre | Cas chaud | Cas froid |
|-----------|----------|-----------|
| Éclairement solaire | | |
| Mode opérationnel | | |
| Dissipation interne | | |
| État du revêtement | BOL / EOL | BOL / EOL |
| Préoccupation principale | | |

**2. Relevez les prédictions thermiques dans Analyses › Physique (masse / AOCS / thermique), réseau thermique :**

| Composant | Min. prévu (°C) | Max. prévu (°C) | Min. de fonctionnement (°C) | Max. de fonctionnement (°C) |
|-----------|---------------------|---------------------|---------------------|---------------------|
| Charge utile / capteur | | | | |
| Batterie | | | | |
| OBC | | | | |
| Transpondeur | | | | |

**3. Vérification des marges (>= 5 °C exigés) :**

| Composant | Marge chaude = Max_op - Max_pred | Marge froide = Min_pred - Min_op | Conforme ? |
|-----------|-------------------------------|--------------------------------|-------|
| | | | |
| | | | |
| | | | |
| | | | |

**4. Si une marge n'est pas respectée, quelle mesure de contrôle thermique prendriez-vous ?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Partie D : Vérification avec SpaceCDF

Comparez vos calculs manuels aux valeurs de SpaceCDF :

| Paramètre | Calcul manuel | Valeur SpaceCDF | Écart |
|-----------|-----------------|---------------|------------|
| Puissance requise du générateur solaire (BOL) | _____ W | _____ W | _____ W |
| Capacité de la batterie | _____ Wh | _____ Wh | _____ Wh |
| Puissance moyenne sur l'orbite | _____ W | _____ W | _____ W |
| Durée d'éclipse | _____ min | _____ min | _____ min |

En cas d'écarts importants, expliquez-en la raison :

_____________________________________________________________________

_____________________________________________________________________

---

## Justification des décisions

Expliquez POURQUOI vous avez choisi chaque élément de votre conception électrique et thermique. Tenez compte des solutions que vous avez écartées et des compromis en jeu.

**Choix de la configuration du générateur solaire et justification :**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Justification du dimensionnement de la batterie (pourquoi cette DOD ? pourquoi cette marge de capacité ?) :**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Approche de contrôle thermique (passif uniquement ? réchauffeurs ? revêtements ?) :**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Notes et réflexions

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

# Fiche 3.2 : Système de contrôle d'attitude et d'orbite (SCAO)

| | |
|---|---|
| **Nom :** | _______________________________________ |
| **Date :** | _______________________________________ |
| **Équipe / mission :** | _______________________________________ |
| **Rôle / poste :** | _______________________________________ |

**Onglets SpaceCDF :** Analyses › Physique (section SCAO), Décider › Compromis d'architecture (AOCS), Bilans › Masse

---

## Aide-mémoire : notions de SCAO

### Qu'est-ce que le SCAO ?

Le système de contrôle d'attitude et d'orbite (SCAO ; AOCS sur la console) remplit deux fonctions distinctes :

- **Détermination d'attitude (AD) :** établir dans quelle direction pointe l'engin spatial, à l'aide de capteurs.
- **Contrôle d'attitude (AC) :** modifier ou maintenir l'orientation de l'engin spatial, à l'aide d'actionneurs.

Ce sont deux problèmes distincts. Vous pouvez connaître parfaitement votre orientation (excellents capteurs) tout en oscillant si vos actionneurs sont trop faibles. Ou bien disposer d'actionneurs puissants mais mal connaître la direction dans laquelle vous pointez.

### Capteurs : comment savoir où l'on pointe ?

| Capteur | Grandeur mesurée | Précision | Masse | Puissance | Coût | Cas d'emploi |
|--------|-----------------|----------|------|-------|------|----------------|
| **Magnétomètre** | Direction du champ magnétique terrestre | ~2--5° | ~5 g | ~0,1 W | ~1 k€ | Détermination grossière ; toujours actif pour connaître le champ B |
| **Senseur solaire grossier** | Direction du Soleil (1--2 axes) | ~2--5° | ~5 g | ~0,01 W | ~0,5 k€ | Mode survie ; acquisition initiale |
| **Senseur solaire fin** | Direction du Soleil (2 axes, haute précision) | ~0,1--0,5° | ~10 g | ~0,05 W | ~2 k€ | Missions à pointage solaire ; secours du senseur stellaire |
| **Senseur stellaire** | Attitude complète sur 3 axes à partir de configurations d'étoiles | ~0,001--0,01° (3--30″) | 50--350 g | ~0,5--1,5 W | ~20--35 k€ | Pointage de précision pour l'imagerie, les télécommunications, la science |
| **Gyroscope MEMS** | Vitesse angulaire (vitesse de rotation) | Dérive : ~1--10°/h | ~20 g | ~0,3 W | ~3 k€ | Comble les lacunes pendant l'éblouissement du senseur stellaire ; commande des basculements |
| **Senseur terrestre** | Direction du nadir (verticale locale) | ~0,1--0,5° | ~50 g | ~0,5 W | ~5 k€ | Missions à pointage nadir (moins courant sur les CubeSat) |

**Idée essentielle :** les senseurs stellaires sont de loin les capteurs les plus précis. Ils photographient le ciel, comparent la configuration d'étoiles observée à un catalogue embarqué et calculent l'orientation de l'engin spatial à quelques secondes d'arc près. Ils sont cependant éblouis lorsque le Soleil, la Lune ou le limbe terrestre entre dans leur champ de vue ; les senseurs solaires ou les gyroscopes prennent alors le relais.

### Actionneurs : comment commander notre orientation ?

| Actionneur | Principe de fonctionnement | Couple | Précision | Masse | Puissance | Cas d'emploi |
|----------|-------------|--------|-----------|------|-------|----------------|
| **Aimant permanent** | Aligne l'engin spatial sur le champ B terrestre, comme une aiguille de boussole | ~$10^{-5}$ N m (rappel) | ~10--15° | ~20 g | 0 W | Stabilisation passive pour les missions sans besoin de pointage |
| **Barreaux d'hystérésis** | Dissipent l'énergie de rotation par hystérésis magnétique ; amortissent le culbutage | S. O. (amortissement uniquement) | S. O. | ~10 g chacun | 0 W | Toujours associés à un aimant permanent pour la stabilisation passive |
| **Magnétocoupleurs (MTQ)** | Bobines électromagnétiques qui interagissent avec le champ magnétique terrestre pour produire un couple | ~$10^{-6}$--$10^{-4}$ N m | ~2--5° (en actionneur principal) ; S. O. (en désaturation) | ~10--30 g chacun | 0,1--0,2 W | **Commande principale** pour les missions peu exigeantes en précision ; **désaturation** des roues de réaction pour tous les systèmes à roues |
| **Roues de réaction (RW)** | Volants d'inertie en rotation qui échangent du moment cinétique avec l'engin spatial | ~$10^{-4}$--$10^{-2}$ N m | ~0,001--0,01° | 30--120 g chacune | 0,3--1,5 W | Pointage de précision -- toute mission exigeant une précision < 2° |
| **Propulseurs** | Éjectent de la masse (gaz froid, ions) pour produire un couple par une force excentrée | Variable | ~0,1--1° | Selon le système | Élevée | Grands basculements ; ajustement d'orbite ; lorsque les MTQ sont insuffisants (espace lointain) |

**Magnétocoupleurs -- deux rôles essentiels :**

1. **En actionneurs principaux** (missions n'exigeant qu'un pointage de 2--5°) : les MTQ assurent à eux seuls un contrôle sur 3 axes, mais uniquement en LEO, où le champ magnétique terrestre est intense. Ils ne peuvent pas produire de couple parallèle au vecteur champ local ; leur capacité de commande varie donc le long de l'orbite.

2. **En actionneurs de désaturation** (toutes les missions à roues de réaction) : les roues de réaction absorbent les couples perturbateurs en accélérant. Avec le temps, elles accumulent du moment cinétique et atteignent la saturation (vitesse de rotation maximale). Les MTQ « déchargent » ce moment stocké en produisant un couple opposé grâce au champ magnétique terrestre. Cette opération a lieu environ une fois par orbite. Comme le couple magnétique disponible est faible et s'annule le long de la direction du champ local, un déchargement complet prend typiquement **plusieurs dizaines de minutes (de l'ordre de 20--50 min)**, et non quelques minutes -- prévoyez une inhibition des prises de vue pendant toute sa durée.

**Roues de réaction -- pourquoi 4 roues ?** Trois roues (une par axe) assurent le contrôle minimal sur 3 axes. Une 4e roue sur un axe oblique apporte la tolérance à une panne simple : si l'une des roues tombe en panne, les trois restantes assurent toujours un contrôle complet sur 3 axes.

### Tableau de décision pour l'architecture du SCAO

Utilisez ce tableau pour choisir votre architecture en fonction de votre exigence de pointage :

| Exigence de pointage | Architecture | Capteurs | Actionneurs | Masse | Puissance | Coût |
|---------------------|-------------|---------|-----------|------|-------|------|
| > 5° (pas de besoin de pointage) | Magnétique passive | Magnétomètre | Aimant permanent + barreaux d'hystérésis | ~50 g | 0 W | ~2 k€ |
| 2--5° | À magnétocoupleurs | Senseurs solaires grossiers + magnétomètre | MTQ 3 axes | ~100 g | 0,2 W | ~8 k€ |
| 0,1--2° | À roues de réaction | Senseurs solaires fins + magnétomètre | 3--4 RW + 3 MTQ (désaturation) | ~500 g | 2--4 W | ~35 k€ |
| < 0,1° | Pointage fin | Senseur stellaire + senseurs solaires fins | 4 RW + 3 MTQ | ~800 g | 3--5 W | ~55 k€ |
| < 0,01° | Pointage très fin | Senseur stellaire + gyroscope MEMS + senseurs solaires | 4 RW + 3 MTQ | ~1200 g | 4--6 W | ~80 k€ |

**Mode d'emploi du tableau :** repérez l'exigence de pointage de votre mission (dans votre fiche d'exigences). Lisez la ligne pour trouver l'architecture, les capteurs et les actionneurs nécessaires. Si votre mission est une caméra d'observation de la Terre exigeant un pointage de 0,05°, il vous faut un pointage fin (senseur stellaire + 4 RW + 3 MTQ). Si votre mission est un relais IoT (Internet des objets) n'exigeant qu'un pointage de 5°, les magnétocoupleurs seuls suffisent.

---

## Rappel des équations clés

> **Couple de gradient de gravité :** $T_{gg} = \frac{3\mu}{2a^3}|I_z - I_x|\sin(2\theta)$
>
> **Couple aérodynamique :** $T_{\text{aero}} = \frac{1}{2}\rho v^2 C_D A \cdot d_{cp-cm}$
>
> **Couple de pression de radiation solaire :** $T_{\text{SRP}} = \frac{S}{c} A_s (1+q) \cdot d_{sp-cm}$
>
> **Couple magnétique :** $T_{\text{mag}} = M \times B$
>
> **Stockage de moment cinétique :** $H = T_{\text{dist}} \times t_{\text{desat}}/2$
>
> **Erreur de pointage (RSS) :** $\theta_{\text{total}} = \sqrt{\sum \theta_i^2}$
>
> **Couple des MTQ :** $T_{\text{MTQ}} = m_{\text{dipole}} \times B \times \sin(\alpha)$

---

## Exemple résolu : SCAO d'UniSat-1 (1U)

### Choix de l'architecture

UniSat-1 emporte une charge utile magnétométrique MEMS qui n'exige pas de pointage précis. En réalité, un état de rotation lente ou de culbutage fournit des mesures du champ magnétique dans plusieurs directions, ce qui améliore la qualité des données.

**Architecture : stabilisation magnétique passive** (aimant permanent + barreaux d'hystérésis). Aucun bilan d'erreurs de pointage n'est nécessaire, puisqu'il n'y a pas d'exigence de pointage.

| Paramètre | Valeur |
|-----------|-------|
| Précision de pointage | ~10--15° (par rapport au champ magnétique local) |
| Masse | ~30--50 g |
| Puissance | 0 W |
| Coût | ~1--2 k€ |

### Couples perturbateurs à 400 km

Même si UniSat-1 n'a pas de SCAO actif, la connaissance de l'environnement perturbateur confirme que l'aimant passif fournit un couple de rappel suffisant.

**Gradient de gravité** (le 1U est presque cubique, donc $I_z \approx I_x$, ce qui rend ce couple très faible) :

$T_{gg} \approx \frac{3 \times 3.986 \times 10^{14}}{2 \times (6.771 \times 10^6)^3} \times |I_z - I_x| \approx 1 \times 10^{-8}$ N m

**Aérodynamique** ($\rho$ à 400 km $\approx 4 \times 10^{-12}$ kg/m$^3$, $v \approx 7670$ m/s) :

$T_{\text{aero}} = 0.5 \times 4 \times 10^{-12} \times 7670^2 \times 2.2 \times 0.01 \times 0.01 \approx 3 \times 10^{-8}$ N m

**Couple de rappel de l'aimant permanent :** $\sim 1 \times 10^{-5}$ N m -- trois ordres de grandeur au-dessus de l'ensemble des perturbations. **Le satellite reste aligné sur le champ.**

---

## Partie A : Choix de l'architecture du SCAO

**Exigence de pointage de votre mission :** _____° (3 sigma)

**Architecture du SCAO retenue** (cochez-en une) :

- [ ] Magnétique passive (> 5°)
- [ ] Magnétocoupleurs seuls (2--5°)
- [ ] Roues de réaction + MTQ (0,1--2°)
- [ ] Pointage fin : RW + senseur stellaire + MTQ (< 0,1°)
- [ ] Très fin : RW + senseur stellaire + gyroscope + MTQ (< 0,01°)

**Justification du choix :**

_____________________________________________________________________

_____________________________________________________________________

**Masse estimée du SCAO :** _____ kg     **Puissance estimée du SCAO :** _____ W

---

## Partie B : Calcul des couples perturbateurs

Calculez au moins 2 couples perturbateurs pour votre engin spatial et votre orbite. Détaillez tous les calculs.

**Propriétés de l'engin spatial :**

| Paramètre | Valeur | Unité |
|-----------|-------|------|
| Masse | | kg |
| Format | | U |
| $I_z$ (plus grand moment d'inertie) | | kg m$^2$ |
| $I_x$ (plus petit moment d'inertie) | | kg m$^2$ |
| Section efficace (plus grande face) | | m$^2$ |
| $d_{cp-cm}$ (estimation du décalage centre de pression -- centre de masse) | | m |
| Altitude de l'orbite | | km |

**1. Couple de gradient de gravité :**

$T_{gg} = \frac{3 \times 3.986 \times 10^{14}}{2 \times (\ \ \ \ )^3} \times |I_z - I_x| = $

_____________________________________________________________________

_____________________________________________________________________

$T_{gg} = $ _____ N m

**2. Couple aérodynamique** ($\rho$ à _____ km $\approx$ _____ kg/m$^3$) :

$T_{\text{aero}} = \frac{1}{2} \times$ _____ $\times$ _____ $^2 \times 2.2 \times$ _____ $\times$ _____ $= $

_____________________________________________________________________

$T_{\text{aero}} = $ _____ N m

**3. (Facultatif) Couple de pression de radiation solaire :**

_____________________________________________________________________

_____________________________________________________________________

$T_{\text{SRP}} = $ _____ N m

**4. (Facultatif) Couple dû au dipôle magnétique résiduel** ($M \approx$ _____ A m$^2$, $B \approx 3 \times 10^{-5}$ T) :

$T_{\text{mag}} = $ _____ $\times$ _____ $= $ _____ N m

**Synthèse :**

| Source | Couple (N m) |
|--------|-------------|
| Gradient de gravité | |
| Aérodynamique | |
| Pression de radiation solaire | |
| Dipôle magnétique | |
| **Total (RSS ou somme)** | |

**Quelle perturbation domine ?** _______________________________________________

---

## Partie C : Dimensionnement des roues de réaction

*Sautez cette partie si votre mission utilise une architecture magnétique passive ou à magnétocoupleurs seuls.*

**1. Exigence de couple** ($\geq 2\times$ la perturbation totale) :

$T_{\text{RW,req}} = 2 \times$ _____ $= $ _____ N m $= $ _____ mN m

**2. Stockage de moment cinétique** (intervalle de désaturation = 1 orbite = _____ s) :

$H = T_{\text{dist}} \times \frac{t_{\text{desat}}}{2} = $ _____ $\times \frac{\ \ \ \ }{2} = $ _____ mN m s

**3. Roue de réaction retenue :**

| Paramètre | Exigé | Produit retenu |
|-----------|----------|-----------------|
| Couple | _____ mN m | _____ mN m |
| Moment cinétique | _____ mN m s | _____ mN m s |
| Masse | -- | _____ g |
| Puissance | -- | _____ W |
| Quantité | 4 (3+1 en redondance) | |

---

## Partie D : Bilan d'erreurs de pointage

*Sautez cette partie si votre mission utilise une stabilisation magnétique passive (pas d'exigence de pointage).*

Complétez le bilan d'erreurs de pointage par sommation quadratique (RSS) :

| Source d'erreur | Valeur (°) | Valeur$^2$ |
|-------------|------------|-----------|
| Précision des capteurs | | |
| Résolution des actionneurs | | |
| Connaissance de l'alignement | | |
| Distorsion thermique | | |
| Microvibrations (RW) | | |
| Connaissance de l'orbite | | |
| Erreur de datation | | |
| **Somme des carrés** | | |
| **Total RSS** = $\sqrt{\text{somme}}$ | **= _____°** | |

**Exigence :** _____°

**Marge :** _____° (_____ %)

**Le bilan de pointage est-il bouclé ?** O / N

**Quelle source d'erreur domine ?** _______________________________________________

**Quelle action améliorerait le plus le bilan ?** _________________________________

_____________________________________________________________________

---

## Partie E : Vérification avec SpaceCDF

Comparez vos calculs manuels à la section SCAO d'Analyses › Physique (masse / AOCS / thermique) :

| Paramètre | Calcul manuel | SpaceCDF | Concordance ? |
|-----------|-----------------|----------|--------|
| Erreur de pointage RSS | _____° | _____° | |
| Contributeur dominant | ____________ | ____________ | |
| Marge par rapport à l'exigence | _____ % | _____ % | |

En cas d'écarts, expliquez-les :

_____________________________________________________________________

_____________________________________________________________________

---

## Justification des décisions

Expliquez POURQUOI vous avez choisi votre architecture de SCAO. Tenez compte des solutions envisagées et de ce qui a déterminé votre décision.

**Pourquoi cette architecture plutôt qu'une plus simple ?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Pourquoi cette architecture plutôt qu'une plus performante ?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Quel est le principal risque de votre conception du SCAO ?**

_____________________________________________________________________

_____________________________________________________________________

---

## Notes et réflexions

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

# Fiche 3.3 : Conception des télécommunications et bilan de liaison

| | |
|---|---|
| **Nom :** | _______________________________________ |
| **Date :** | _______________________________________ |
| **Équipe / mission :** | _______________________________________ |
| **Rôle / poste :** | _______________________________________ |

**Onglets SpaceCDF :** Analyses › Boucle de conception (liaison et données), Analyses › Segment sol, Décider › Compromis d'architecture (TTC), Catalogue des équipements (Communications), TM/TC › Échelle de débits

---

## Aide-mémoire : notions de télécommunications

### Qu'est-ce qu'un bilan de liaison ?

Un bilan de liaison est l'état comptable de votre liaison de communication. Il additionne tous les gains (puissance d'émission, gain d'antenne) et soustrait toutes les pertes (distance, atmosphère, erreur de pointage) pour déterminer si le signal qui arrive au récepteur est assez fort pour être décodé. Tout est calculé en **décibels (dB)**, de sorte que les multiplications et les divisions deviennent des additions et des soustractions.

**Rappel sur les décibels :**

| Conversion | Formule | Valeurs courantes |
|-----------|---------|---------------|
| Watts en dBW | $P_{\text{dBW}} = 10\log_{10}(P_W)$ | 2 W = +3,0 dBW ; 1 W = 0 dBW ; 0,5 W = −3,0 dBW |
| Kelvins en dBK | $T_{\text{dBK}} = 10\log_{10}(T_K)$ | 150 K = 21,8 dBK ; 600 K = 27,8 dBK |
| Rapport en dB | $G_{\text{dB}} = 10\log_{10}(G)$ | x2 = +3 dB ; x10 = +10 dB ; x100 = +20 dB |

### Signification de chaque terme du bilan de liaison

| Terme | Définition | Analogie |
|------|-----------|---------|
| **Puissance d'émission ($P_{TX}$)** | Puissance électrique fournie à l'amplificateur de l'émetteur | La force avec laquelle vous criez |
| **Gain de l'antenne d'émission ($G_{TX}$)** | Capacité de l'antenne à concentrer le signal en un faisceau (au lieu de rayonner également dans toutes les directions) | Utiliser un mégaphone plutôt que crier dans toutes les directions |
| **Pertes de ligne à l'émission ($L_{TX}$)** | Puissance perdue dans les câbles et les filtres entre l'amplificateur et l'antenne | Le son absorbé par les parois du mégaphone |
| **PIRE** | Puissance isotrope rayonnée équivalente = $P_{TX} + G_{TX} - L_{TX}$. La « puissance totale du signal qui quitte le satellite » | Le volume sonore total entendu à distance |
| **Affaiblissement en espace libre (FSPL)** | Le signal s'affaiblit en se répartissant sur une sphère de plus en plus grande. Dépend de la distance et de la fréquence | La voix qui faiblit à mesure que vous vous éloignez |
| **Affaiblissement atmosphérique** | Signal absorbé ou diffusé par l'atmosphère terrestre (pluie, oxygène, vapeur d'eau) | Le brouillard qui étouffe le son |
| **Perte de dépointage** | Perte de signal due au fait que le faisceau de l'antenne n'est pas parfaitement orienté | Le mégaphone légèrement décalé par rapport à la cible |
| **Perte de polarisation** | Perte lorsque les polarisations des antennes d'émission et de réception ne correspondent pas | Tenir le mégaphone de côté quand l'auditeur l'attend à la verticale |
| **Gain de l'antenne de réception ($G_{RX}$)** | Capacité de l'antenne de la station sol à capter le signal. Plus la parabole est grande, plus le gain est élevé | L'auditeur qui utilise un grand cornet acoustique |
| **Température de bruit du système ($T_{sys}$)** | Bruit combiné de l'antenne, du ciel et de l'électronique de réception. Plus elle est basse, mieux c'est | Le bruit de fond dans la pièce |
| **G/T** | Facteur de qualité du récepteur = $G_{RX} - T_{sys}$ (en dB). Traduit la « qualité » de la station sol | Taille du cornet acoustique moins le bruit de la pièce |
| **$C/N_0$** | Rapport porteuse sur densité de bruit -- la puissance du signal reçu rapportée au bruit | Le rapport signal sur bruit avant décodage |
| **$E_b/N_0$** | Énergie par bit sur densité de bruit -- la mesure fondamentale de la qualité de la liaison. On l'obtient en divisant $C/N_0$ par le débit | La quantité d'énergie disponible par bit d'information |
| **Marge de liaison** | Excédent de $E_b/N_0$ par rapport au minimum requis. Doit être >= 3 dB | Le coefficient de sécurité de votre communication |

### Comparaison des bandes de fréquences

| Paramètre | UHF (amateur) | Bande S | Bande X | Bande Ka |
|-----------|--------------|--------|--------|---------|
| **Fréquence** | 435--438 MHz | 2200--2290 MHz | 8025--8400 MHz | 25,5--27,0 GHz |
| **Largeur de bande disponible** | 20 kHz | 5 MHz | 375 MHz | 1,5 GHz |
| **Débit maximal** | < 20 kbit/s | 0,1--10 Mbit/s | 10--400 Mbit/s | 100--2000 Mbit/s |
| **Affaiblissement en espace libre à 500 km (nadir)** | 139 dB | 153 dB | 165 dB | 175 dB |
| **Affaiblissement en espace libre à 1300 km (10° d'élévation)** | 148 dB | 162 dB | 173 dB | 183 dB |
| **Affaiblissement atmosphérique** | ~0,1 dB | ~0,5 dB | ~1,0 dB | ~3--10 dB (pluie !) |
| **Antenne bord typique** | Monopôle (0 dBi) | Patch (6 dBi) | Cornet / réseau de patchs (10--15 dBi) | Petite parabole / réseau (20+ dBi) |
| **Antenne sol** | Yagi (10--13 dBi) | Parabole de 3 m (35 dBi) | Parabole de 3 m (45 dBi) | Parabole de 1 m (45 dBi) |
| **Type de licence** | Coordination IARU (gratuite) | ISDE/FCC (30--45 k\$) | ISDE/FCC + UIT (plus coûteux) | Notification UIT complexe |
| **Délai d'obtention de la licence** | ~6 mois | 6--12 mois | 12+ mois | 12--18 mois |
| **Disponibilité des équipements** | Nombreux COTS | Nombreux COTS | Offre COTS croissante | Émergente |
| **Idéal pour** | TT&C, télémesure, missions simples | Débit moyen, observation de la Terre standard | Haut débit, observation de la Terre / SAR | Très haut débit |

**Comment choisir :** partez de votre exigence de débit. Si vous avez besoin de moins de 20 kbit/s et que vos données sont non commerciales, la bande UHF amateur est gratuite et simple. Jusqu'à 10 Mbit/s, la bande S est la bête de somme des CubeSat. Pour une imagerie à haute résolution produisant des Go par jour, il vous faut la bande X ou la bande Ka.

### Types d'antennes

| Type d'antenne | Gain | Ouverture du faisceau | Besoin de pointage | Masse | Bande typique | Cas d'emploi |
|-------------|------|-----------|---------------|------|-------------|----------|
| **Monopôle/dipôle** | ~0 dBi | Omnidirectionnelle | Aucun | 5--20 g | UHF | TT&C, télémesure simple |
| **Patch (simple)** | ~5--8 dBi | ~70--90° | Faible (~10°) | 10--50 g | Bande S | Liaison descendante standard d'un CubeSat |
| **Réseau de patchs (2x2)** | ~12 dBi | ~30--40° | Moyen (~5°) | 30--100 g | Bandes S/X | Liaison descendante à débit plus élevé |
| **Cornet** | ~10--15 dBi | ~20--30° | Moyen (~5°) | 50--200 g | Bande X | Liaison descendante à haut débit |
| **Réflecteur parabolique** | ~20--35 dBi | ~2--10° | Strict (< 1°) | 200--500 g | Bandes X/Ka | Très haut débit, transmission directe vers la Terre (DTE) |
| **Antenne réseau à commande de phase** | ~15--25 dBi | Orientation électronique | Électronique (rapide) | 100--300 g | Bandes S/X/Ka | Faisceau agile, cibles multiples |

**Compromis :** les antennes à gain élevé fournissent des signaux plus forts (ce qui permet des débits plus élevés ou une puissance d'émission plus faible), mais leurs faisceaux sont plus étroits, ce qui impose au satellite un pointage plus précis. Une antenne omnidirectionnelle fonctionne quelle que soit l'orientation du satellite, mais n'offre qu'un gain très faible.

### Modulation et codage

Le schéma de modulation et le code de correction d'erreurs directe (FEC) déterminent le $E_b/N_0$ minimal requis pour un taux d'erreur binaire (TEB) cible :

| Modulation + codage | $E_b/N_0$ requis (TEB $10^{-6}$) | Efficacité spectrale | Idéal pour |
|--------------------|-----------------------------------|--------------------|----------|
| BPSK non codée | 10,5 dB | 1,0 bit/s/Hz | Télécommande ancienne génération |
| QPSK non codée | 10,5 dB | 2,0 bit/s/Hz | Télémesure simple |
| QPSK + convolutif (r=1/2) | 5,0 dB | 1,0 bit/s/Hz | TM CCSDS standard |
| QPSK + LDPC (r=1/2) | 2,0 dB | 1,0 bit/s/Hz | Liaison descendante à haute efficacité |
| QPSK + LDPC (r=3/4) | 4,0 dB | 1,5 bit/s/Hz | Équilibré (standard CubeSat) |
| 8PSK + LDPC (r=3/4) | 6,5 dB | 2,25 bit/s/Hz | Liaison descendante à haut débit |

**Recommandation de conception :** pour la plupart des missions CubeSat, **QPSK + LDPC (r=3/4)** avec $E_b/N_0 = 4.0$ dB est le choix standard ; il offre un bon équilibre entre gain de codage et simplicité de mise en œuvre.

---

## Rappel des équations clés

> **PIRE :** $\text{PIRE} = P_{TX} + G_{TX} - L_{TX}$   (dBW)
>
> **Affaiblissement en espace libre :** $\text{FSPL} = 20\log_{10}\left(\frac{4\pi d f}{c}\right)$   (dB)
>
> **G/T :** $G/T = G_{RX} - 10\log_{10}(T_{sys})$   (dB/K)
>
> **C/N$_0$ :** $C/N_0 = \text{PIRE} - \text{FSPL} - L_{\text{losses}} + G/T + 228.6$   (dBHz)
>
> **$E_b/N_0$ :** $E_b/N_0 = C/N_0 - 10\log_{10}(R_b)$   (dB)
>
> **Marge de liaison :** $\text{Marge} = E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}} \geq 3$ dB
>
> **Gain d'antenne :** $G = \eta_a(\pi D/\lambda)^2$
>
> **Conversion en dB :** $P_{\text{dBW}} = 10\log_{10}(P_W)$ ;   2 W = +3,0 dBW ; 1 W = 0 dBW

---

## Exemple résolu : bilan de liaison UHF d'UniSat-1 (1U)

UniSat-1 utilise la bande UHF amateur à 437 MHz, avec une liaison descendante à 9600 bit/s vers une station sol amateur.

### Bilan de liaison étape par étape

**Scénario :** orbite à 400 km, 437 MHz, 9600 bit/s, élévation minimale de 10° (distance oblique ~1150 km), station sol équipée d'une antenne Yagi croisée de 13 dBi (RHCP).

| Ligne | Paramètre | Calcul | Valeur | Unité |
|------|-----------|-------------|-------|------|
| 1 | Puissance d'émission | 0,5 W = $10\log_{10}(0.5)$ | −3,0 | dBW |
| 2 | Gain de l'antenne d'émission | Monopôle | 0,0 | dBi |
| 3 | Pertes de ligne à l'émission | Câble court | −0,5 | dB |
| 4 | **PIRE** | $-3.0 + 0.0 - 0.5$ | **−3,5** | dBW |
| 5 | Affaiblissement en espace libre | $21.98 + 20\log_{10}(1.15 \times 10^6) + 20\log_{10}(437 \times 10^6) - 169.54$ | −146,5 | dB |
| 6 | Affaiblissement atmosphérique | Minime en UHF | −0,3 | dB |
| 7 | Perte de dépointage | Antenne omnidirectionnelle, minime | −0,5 | dB |
| 8 | Perte de polarisation | RHCP vers RHCP (Yagi croisée) | −0,5 | dB |
| 9 | Gain de l'antenne de réception | Yagi croisée de 13 dBi | +13,0 | dBi |
| 10 | Température de bruit du système | 600 K (amateur + LNA) = $10\log_{10}(600)$ | 27,8 | dBK |
| 11 | **G/T** | $13.0 - 27.8$ | **−14,8** | dB/K |
| 12 | Constante de Boltzmann | | +228,6 | dBW/K/Hz |
| 13 | **C/N$_0$** | $-3.5 - 146.5 - 0.3 - 0.5 - 0.5 + (-14.8) + 228.6$ | **+62,5** | dBHz |
| 14 | Débit | 9600 bit/s = $10\log_{10}(9600)$ | 39,8 | dB(bit/s) |
| 15 | **$E_b/N_0$ disponible** | $62.5 - 39.8$ | **+22,7** | dB |
| 16 | $E_b/N_0$ requis | GMSK + code convolutif r=1/2 (K=7) | 5,0 | dB |
| 17 | Perte d'implémentation | | 2,0 | dB |
| 18 | **MARGE DE LIAISON** | $22.7 - 5.0 - 2.0$ | **+15,7** | dB |

**Résultat :** la liaison est bouclée avec une marge de 15,7 dB (> 3 dB). **Conforme.**

### Détail du calcul de l'affaiblissement en espace libre

$\text{FSPL} = 21.98 + 20\log_{10}(1.15 \times 10^6) + 20\log_{10}(437 \times 10^6) - 169.54$

$20\log_{10}(1.15 \times 10^6) = 20 \times 6.0607 = 121.2$ dB

$20\log_{10}(437 \times 10^6) = 20 \times 8.640 = 172.8$ dB

$\text{FSPL} = 21.98 + 121.2 + 172.8 - 169.54 = 146.5$ dB

Vérification avec la formule unique, distance oblique en mètres ($1.15 \times 10^6$ m) et fréquence en Hz ($437 \times 10^6$ Hz) :

$20\log_{10}\!\left(4\pi \times 1.15 \times 10^6 \times 437 \times 10^6 / 3 \times 10^8\right) = 146.5$ dB

Et avec la forme pratique (distance en km, fréquence en MHz) :

$\text{FSPL} = 32.44 + 20\log_{10}(1150) + 20\log_{10}(437) = 32.44 + 61.2 + 52.8 = 146.5$ dB

Les trois formes concordent. **Erreur fréquente :** utiliser 41,44 au lieu de 32,44 dans la forme km/MHz ajoute 9 dB parasites à chaque bilan de liaison. Si votre affaiblissement en espace libre paraît trop élevé d'environ 9 dB, vérifiez d'abord cette constante.

### Débit utile

Avec un débit utile de 4800 bit/s (débit canal de 9600 bit/s avec une FEC r=1/2), un passage de 7 minutes fournit :

$V_{\text{pass}} = 4800 \times 420 \times 0.85 = 1.71$ Mbit $= 214$ ko par passage

Avec 4 passages par jour : ~0,86 Mo/jour. Le magnétomètre produit ~1,13 Mo/jour -- c'est limite. Une deuxième station sol ou une priorisation des données pourrait être nécessaire.

---

## Partie A : Choix de la bande de fréquences

**Exigence de débit de la mission :** _____ Mbit/s

**Type de licence retenu :** amateur / expérimentale / commerciale

**Bande retenue :** _____________    **Fréquence centrale :** _____ MHz

**Justification du choix de la bande :**

_____________________________________________________________________

_____________________________________________________________________

**Licences / notifications requises :** _______________________________________________

**Coût estimé des licences :** _____    **Délai :** _____ mois

---

## Partie B : Bilan de liaison complet

Remplissez TOUTES les lignes. Détaillez le calcul de la PIRE, de l'affaiblissement en espace libre, du G/T, du C/N$_0$ et de la marge.

| Ligne | Paramètre | Formule / source | Valeur | Unité |
|------|-----------|-----------------|-------|------|
| 1 | Puissance d'émission | _____ W = | | dBW |
| 2 | Gain de l'antenne d'émission | | | dBi |
| 3 | Pertes de ligne à l'émission | | | dB |
| 4 | **PIRE** = lignes 1 + 2 + 3 | | **______** | dBW |
| 5 | Affaiblissement en espace libre | $20\log_{10}(4\pi \times$ ___ $\times$ ___ $/c)$ | | dB |
| 6 | Affaiblissement atmosphérique | | | dB |
| 7 | Perte de dépointage | | | dB |
| 8 | Perte de polarisation | | | dB |
| 9 | Gain de l'antenne de réception | | | dBi |
| 10 | Température de bruit du système | _____ K = | | dBK |
| 11 | **G/T** = ligne 9 - 10 | | **______** | dB/K |
| 12 | Constante de Boltzmann | | +228,6 | dBW/K/Hz |
| 13 | **C/N$_0$** = 4 + 5 + 6 + 7 + 8 + 11 + 12 | | **______** | dBHz |
| 14 | Débit | _____ bit/s = $10\log_{10}($___$)$ | | dB(bit/s) |
| 15 | **$E_b/N_0$ disponible** = 13 - 14 | | **______** | dB |
| 16 | $E_b/N_0$ requis (mod. + codage : ________) | | | dB |
| 17 | Perte d'implémentation | | | dB |
| 18 | **MARGE DE LIAISON** = 15 - 16 - 17 | | **______** | dB |

**Détaillez le calcul de l'affaiblissement en espace libre :**

$\text{FSPL} = 20\log_{10}(4\pi) + 20\log_{10}(d) + 20\log_{10}(f) - 20\log_{10}(c)$

$= 21.98 + 20\log_{10}($ _____ $) + 20\log_{10}($ _____ $) - 169.54 = $ _____ dB

_____________________________________________________________________

_____________________________________________________________________

**La liaison est-elle bouclée ($\geq$ 3 dB) ?** O / N

**Si la marge est excessive, débit maximal atteignable avec une marge de 3 dB :**

$R_{b,\text{max}} = 10^{(E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}} - 3)/10} \times R_b = $ _____ Mbit/s

_____________________________________________________________________

---

## Partie C : Bilan de données

**Volume de données produit par jour :**

$V_{\text{gen}} = R_{\text{payload}} \times t_{\text{imaging}} \times N_{\text{orbits}} \times f_{\text{compression}}$

$= $ _____ Mbit/s $\times$ _____ s $\times$ _____ $\times$ _____ $= $ _____ Mo/jour $= $ _____ Go/jour

**Capacité quotidienne de liaison descendante :**

$V_{\text{DL}} = R_{\text{DL}} \times t_{\text{contact}} \times N_{\text{passes}} \times \eta_{\text{protocol}}$

$= $ _____ Mbit/s $\times$ _____ s $\times$ _____ $\times$ _____ $= $ _____ Mo/jour $= $ _____ Go/jour

**Le bilan de données est-il bouclé ?** ($V_{\text{DL}} \geq V_{\text{gen}}$) : O / N

Si ce n'est pas le cas, quel est votre plan de réduction du risque ?

_____________________________________________________________________

_____________________________________________________________________

---

## Partie D : Comparaison avec SpaceCDF

Ouvrez Analyses › Boucle de conception (liaison et données) et Analyses › Segment sol, puis comparez :

| Paramètre | Calcul manuel | SpaceCDF | Écart |
|-----------|-----------------|----------|------------|
| PIRE (dBW) | | | |
| Affaiblissement en espace libre (dB) | | | |
| C/N$_0$ (dBHz) | | | |
| Marge de liaison (dB) | | | |

En cas d'écarts, expliquez-les :

_____________________________________________________________________

_____________________________________________________________________

---

## Partie E : Choix de la modulation et du codage

**Modulation retenue :** _______________________________________________

**Code FEC retenu :** _______________________________________________

**$E_b/N_0$ requis pour un TEB de $10^{-6}$ :** _____ dB

**Efficacité spectrale :** _____ bit/s/Hz

**Justification :**

_____________________________________________________________________

_____________________________________________________________________

---

## Justification des décisions

Expliquez POURQUOI vous avez choisi votre architecture de télécommunications. Traitez chaque décision explicitement.

**Pourquoi cette bande de fréquences plutôt qu'une autre ?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Pourquoi ce type d'antenne ? Quel pointage exige-t-il du SCAO ?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Pourquoi ce schéma de modulation et de codage ? Quel compromis avez-vous fait entre débit et robustesse de la liaison ?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Notes et réflexions

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

# Fiche 3.4 : Structure, propulsion et choix des équipements

| | |
|---|---|
| **Nom :** | _______________________________________ |
| **Date :** | _______________________________________ |
| **Équipe / mission :** | _______________________________________ |
| **Rôle / poste :** | _______________________________________ |

**Onglets SpaceCDF :** Catalogue des équipements (Blocs, niveau 3), Satellite, Bilans, Décider › Matrice de Pugh

---

## Aide-mémoire : notions de structure et de propulsion

### Dimensions clés de la CubeSat Design Specification (CDS rév. 14)

La CDS définit les formats standard des CubeSat. Tous les CubeSat doivent respecter ces dimensions pour tenir dans les déployeurs standard (p. ex. ISIPOD, NRCSD, Exolaunch). L'unité « U » représente un cube de 10 x 10 x 11,35 cm.

| Format | Dimensions (mm) | Masse max. (kg) | Volume interne (cm$^3$) | Rails | Usage typique |
|------------|-----------------|---------------|------------------------|-------|-------------|
| **1U** | 100 x 100 x 113,5 | 2,0 | ~1000 | 4 | Démonstration technologique, capteurs simples |
| **1,5U** | 100 x 100 x 170,2 | 3,0 | ~1500 | 4 | 1U étendu, avec plus de volume |
| **2U** | 100 x 100 x 227,0 | 4,0 | ~2000 | 4 | IoT, AIS, charges utiles simples |
| **3U** | 100 x 100 x 340,5 | 6,0 | ~3000 | 4 | Observation de la Terre standard, télécommunications, science |
| **6U** | 100 x 226,3 x 340,5 | 12,0 | ~6000 | 4 | Observation de la Terre haute performance, SAR, télécommunications |
| **12U** | 226,3 x 226,3 x 340,5 | 24,0 | ~12 000 | 8 | Charges utiles avancées, propulsion |
| **16U** | 226,3 x 226,3 x 454,0 | 32,0 | ~16 000 | 8 | Missions de classe microsatellite |

**Exigences clés de la CDS (tous formats) :**

| Exigence | Spécification | Pourquoi c'est important |
|------------|---------------|---------------|
| Matériau des rails | Al 7075-T6 ou 6061-T6 anodisé dur | Évite le soudage à froid dans le vide ; assure le cheminement des efforts structuraux |
| Section des rails | Contact minimal de 8,5 x 8,5 mm | Transmet les charges de lancement par les rails du déployeur |
| Interrupteurs de déploiement | Au moins 1 (sur une entretoise de rail) | Garantit que le satellite reste hors tension jusqu'au déploiement |
| Goupille RBF (*Remove Before Flight*, à retirer avant le vol) | Obligatoire | Déconnecte physiquement les batteries pendant les manipulations au sol |
| Aucune saillie hors de l'enveloppe des rails (configuration repliée) | Obligatoire | Évite le coincement dans le déployeur |
| Décalage du centre de gravité par rapport au centre géométrique | <= 2 cm | Évite un culbutage incontrôlé au déploiement ; équilibre dans le déployeur |
| Fréquence propre fondamentale | > 40 Hz (premier mode) | Évite la résonance avec les modes du lanceur |

### Charges structurales et marges

Pendant le lancement, l'engin spatial subit :

- **une accélération quasi statique :** 6--9 g en axial (le long de l'axe de la fusée), 2--4 g en latéral. Imaginez votre CubeSat de 5 kg comme s'il pesait 45 kg ;
- **des vibrations aléatoires :** secousses à large bande entre 20 et 2000 Hz. Critiques pour les soudures des cartes électroniques et les connecteurs ;
- **des chocs :** impulsions brèves à g élevé (500--2000 g) lors des événements de séparation. Critiques pour les composants fragiles.

**Marge de sécurité (MoS) :** rapport entre ce que la structure peut supporter et ce qu'elle doit supporter, moins 1. Elle doit être >= 0. Si la MoS est négative, la structure cède sous la charge de dimensionnement.

**Propriétés du matériau (Al 7075-T6) :** limite d'élasticité $\sigma_y = 503$ MPa, résistance à la rupture $\sigma_u = 572$ MPa. Facteur de sécurité : 1,25 (limite d'élasticité), 1,5 (rupture).

### Arbre de décision pour la propulsion

Tous les CubeSat n'ont pas besoin de propulsion. Utilisez cet arbre de décision :

```
START (départ) : ma mission a-t-elle besoin de propulsion ?
  |
  +-- Altitude de l'orbite < 500 km ?
  |     YES --> La traînée atmosphérique naturelle désorbite en moins de 5 ans (conforme FCC)
  |             Ai-je besoin d'un maintien d'orbite pour prolonger la durée de vie ?
  |               NO  --> NO PROPULSION NEEDED (pas de propulsion nécessaire)
  |               YES --> Compensation de traînée nécessaire (5-15 m/s par an)
  |
  +-- Altitude de l'orbite 500-700 km ?
  |     Durée de vie naturelle de 5 à 25+ ans
  |     Règle FCC des 5 ans : probablement NON-COMPLIANT (non conforme) sans désorbitation active
  |     --> PROPULSION LIKELY REQUIRED (propulsion probablement requise) pour la désorbitation (50-150 m/s)
  |
  +-- Altitude de l'orbite > 700 km ?
  |     Durée de vie naturelle de plusieurs décennies à plusieurs siècles
  |     Recommandation IADC des 25 ans : NON-COMPLIANT (non conforme)
  |     --> PROPULSION REQUIRED (propulsion requise) pour la désorbitation (Delta-V élevé)
  |
  +-- Mise en phase d'une constellation nécessaire ?
  |     YES --> Ajouter 10-50 m/s pour l'ajustement de plan orbital / de phase
  |
  +-- Évitement de collision nécessaire ?
        YES --> Ajouter une réserve de 1-5 m/s par manœuvre
```

**Règle clé :** en dessous de ~500 km, vous n'avez presque certainement pas besoin de propulsion. Au-dessus de ~600 km, vous en avez presque certainement besoin. Entre 500 et 600 km, tout dépend de votre coefficient balistique et de la durée de votre mission.

### Comparaison des technologies de propulsion

| Type | Principe | $I_{sp}$ (s) | Poussée | Masse d'ergols (100 m/s, satellite de 5 kg) | Masse sèche du système | Masse totale du système | Durée d'allumage | Coût |
|------|-------------|-------------|--------|--------------------------------------|-----------------|-------------------|-----------|------|
| **Gaz froid** | Gaz sous pression éjecté par une tuyère | 40--80 | 10--100 mN | 0,87 kg | 0,3 kg | **1,17 kg** | Minutes | ~15 k€ |
| **Résistojet** | Gaz chauffé avant éjection | 80--150 | 10--50 mN | 0,34 kg | 0,3 kg | **0,64 kg** | Minutes | ~25 k€ |
| **Électronébulisation (FEEP)** | Métal liquide ionisé et accéléré par un champ électrique | 500--1500 | 0,01--1 mN | 0,04 kg | 0,9 kg | **0,94 kg** | Mois | ~50 k€ |
| **Effet Hall** | Xénon ionisé et accéléré par des champs magnétique et électrique | 800--1500 | 1--10 mN | 0,05 kg | 1,5 kg | **1,55 kg** | Semaines | ~80 k€ |
| **Monergol vert** | Décomposition catalytique d'un ergol non toxique | 200--250 | 0,1--1 N | 0,21 kg | 1,0 kg | **1,21 kg** | Secondes | ~60 k€ |

**Le compromis fondamental :**

- **$I_{sp}$ élevée (propulsion électrique) :** consomme très peu d'ergols mais offre une poussée très faible ; les manœuvres prennent donc des semaines ou des mois. Le matériel propulsif est en outre plus lourd et plus coûteux.
- **$I_{sp}$ faible (chimique / gaz froid) :** consomme beaucoup plus d'ergols mais fournit une poussée élevée pour des manœuvres rapides. Le matériel est plus simple, plus léger et moins coûteux.

Choisissez en fonction des questions suivantes : de quel $\Delta V$ avez-vous besoin ? En combien de temps la manœuvre doit-elle être réalisée ? Quelle masse, quel volume et quel coût pouvez-vous vous permettre ?

---

## Rappel des équations clés

> **Marge de sécurité structurale :** $\text{MoS} = \frac{\sigma_{\text{allow}}}{\sigma_{\text{design}} \times \text{FoS}} - 1 \geq 0$
>    FoS : limite d'élasticité 1,25, rupture 1,5 (métaux)
>
> **Équation de Tsiolkovski :** $\Delta V = I_{sp} \cdot g_0 \cdot \ln(m_0/m_f)$
>
> **Masse d'ergols :** $m_{\text{prop}} = m_{\text{dry}} \times \left(e^{\Delta V/(I_{sp} \cdot g_0)} - 1\right)$
>    $g_0 = 9.80665$ m/s$^2$
>
> **Stockage de données :** $S = V_{\text{daily}} \times N_{\text{days}} \times f_{\text{safety}}$
>
> **Fréquence propre fondamentale :** $f_1 > 40$ Hz (exigence du déployeur)

---

## Exemple résolu : structure et propulsion d'UniSat-1 (1U)

### Conformité à la CDS

| Paramètre | Spécification 1U | Conception d'UniSat-1 | Conforme ? |
|-----------|-----------------|-----------------|-----------|
| Dimensions | 100 x 100 x 113,5 mm | 100 x 100 x 113,5 mm (structure 1U ISIS) | O |
| Masse maximale | 2,0 kg (CDS) / 1,33 kg (NanoRacks) | 1,0 kg (objectif) | O |
| Matériau des rails | Al 7075-T6 anodisé dur | Structure standard ISIS | O |
| Interrupteurs de déploiement | Au moins 1 | 2 (standard ISIS) | O |
| Goupille RBF | Obligatoire | Incluse | O |
| Décalage du centre de gravité | <= 2 cm | < 1 cm (aménagement symétrique) | O |
| Saillies (configuration repliée) | Aucune hors de l'enveloppe des rails | Antenne UHF repliée le long d'un rail | O |

### Décision relative à la propulsion

**Altitude de l'orbite :** 400 km. **Durée de vie naturelle :** ~8--14 mois (coefficient balistique $BC = m/(C_D A) = 1.0/(2.2 \times 0.01) = 45.5$ kg/m$^2$).

La règle FCC des 5 ans est respectée sans propulsion. Aucun maintien d'orbite n'est nécessaire (mission de 6 mois). Aucun phasage de constellation. **Décision : pas de propulsion.**

### Marge structurale (charge axiale)

**Données :** masse = 1,0 kg, charge axiale = 9 g, 4 rails.

$F_{\text{axial}} = \frac{1.0 \times 9 \times 9.81}{4} = \frac{88.3}{4} = 22.1$ N par rail

$\sigma = \frac{22.1}{8.5 \times 10^{-3} \times 8.5 \times 10^{-3}} = \frac{22.1}{7.225 \times 10^{-5}} = 0.31$ MPa

$\text{MoS}_y = \frac{503}{0.31 \times 1.25} - 1 = \frac{503}{0.3875} - 1 = 1297 \gg 0$ **Conforme** (avec une très large marge)

**Idée essentielle :** la contrainte axiale quasi statique n'est jamais le cas dimensionnant pour les CubeSat. Les vrais risques structuraux sont : (a) la fatigue des soudures des cartes électroniques sous vibrations aléatoires, (b) la fiabilité des mécanismes de déploiement, (c) la rigidité (fréquence propre fondamentale > 40 Hz).

### Liste des équipements

| # | Catégorie | Composant | Masse (g) | Puissance (W) | Coût (k€) |
|---|----------|-----------|----------|----------|-------------|
| 1 | Structure | Structure 1U ISIS | 200 | -- | 4,0 |
| 2 | EPS + batterie | GomSpace P31us | 200 | 0,3 | 12,0 |
| 3 | Cellules solaires | GaAs fixées sur la structure (5 faces) | 50 | -- | 8,0 |
| 4 | OBC | MSP430/Cortex-M sur mesure | 30 | 0,3 | 3,0 |
| 5 | Télécom | NanoCom AX100 (UHF) | 60 | 0,5 | 8,0 |
| 6 | Antenne | Monopôle UHF (déployable) | 20 | -- | 2,0 |
| 7 | Charge utile | Carte magnétomètre MEMS | 50 | 0,2 | 5,0 |
| 8 | SCAO | Aimant permanent + barreaux d'hystérésis | 30 | 0 | 1,0 |
| 9 | Harnais | Câbles internes, connecteurs | 50 | -- | 1,0 |
| | **TOTAL** | | **690** | **~1,3 (crête)** | **~44** |

Marge de masse : 1330 - 690 = 640 g (48 %). Avec 20 % de marge équipement + 20 % de marge système (MEV) : 1330 - 994 = 336 g (25 %). **Vert.**

---

## Partie A : Vérification de la conformité à la CDS

| Exigence de la CDS | Valeur de votre conception | Spécification | Conforme ? |
|----------------|-------------------|---------------|-----------|
| Format : _____ U | Dimensions : _____ mm | _____ mm | O / N |
| Masse maximale | _____ kg (humide) | _____ kg | O / N |
| Matériau des rails | | Al anodisé dur | O / N |
| Interrupteurs de déploiement | _____ (quantité) | Au moins 1 | O / N |
| Goupille RBF prévue | O / N | Obligatoire | O / N |
| Aucune saillie hors des rails (configuration repliée) | O / N | Obligatoire | O / N |
| Centre de gravité à moins de 2 cm du centre géométrique | Décalage estimé : _____ cm | <= 2 cm | O / N |
| Fréquence propre fondamentale | Estimée : _____ Hz | > 40 Hz | O / N |

**Points de non-conformité et actions correctives :**

_____________________________________________________________________

_____________________________________________________________________

---

## Partie B : Calcul de la marge structurale

**Charge de lancement axiale :** _____ g    **Charge de lancement latérale :** _____ g

**Charge par rail** (4 rails, répartition égale) :

$F_{\text{axial}} = \frac{m \times a_{\text{axial}} \times g_0}{4} = \frac{\ \ \ \ \times \ \ \ \ \times 9.81}{4} = $ _____ N

**Contrainte dans le rail** (section 8,5 x 8,5 mm = $7.225 \times 10^{-5}$ m$^2$) :

$\sigma = \frac{F}{A} = \frac{\ \ \ \ }{7.225 \times 10^{-5}} = $ _____ MPa

**Marge de sécurité (limite d'élasticité, Al 7075-T6, $\sigma_y = 503$ MPa) :**

$\text{MoS} = \frac{503}{\ \ \ \ \times 1.25} - 1 = $ _____

**Conforme ?** O / N

_____________________________________________________________________

---

## Partie C : Décision relative à la propulsion

**Votre mission a-t-elle besoin de propulsion ?**

| Question | Réponse |
|----------|--------|
| Altitude de l'orbite | _____ km |
| Durée de vie orbitale naturelle | _____ ans |
| Conforme à la règle FCC des 5 ans sans propulsion ? | O / N |
| Maintien d'orbite nécessaire ? | O / N |
| Phasage de constellation nécessaire ? | O / N |
| Désorbitation active nécessaire ? | O / N |

**Décision :**   propulsion / pas de propulsion

---

**Si vous retenez une propulsion, remplissez cette partie. Détaillez tous les calculs.**

**$\Delta V$ total requis :**

| Manœuvre | $\Delta V$ (m/s) |
|-----------|-----------------|
| Maintien d'orbite (_____ ans) | |
| Désorbitation | |
| Marge pour l'évitement de collision | |
| **Total** | |

**Type de propulsion retenu :** _______________    $I_{sp} = $ _____ s

**Masse d'ergols (Tsiolkovski) :**

$m_{\text{prop}} = m_{\text{dry}} \times \left(e^{\Delta V/(I_{sp} \times g_0)} - 1\right)$

$= $ _____ $\times \left(e^{\ \ \ /(\ \ \ \times 9.81)} - 1\right) = $ _____ $\times \left(e^{\ \ \ } - 1\right) = $ _____ $\times$ _____ $= $ _____ kg

_____________________________________________________________________

_____________________________________________________________________

**Masse sèche du système (propulseur + réservoir + alimentation) :** _____ kg

**Masse totale du système propulsif :** _____ kg (ergols + masse sèche)

**Fraction de la masse totale du satellite :** _____ %

---

## Partie D : Journal de choix des équipements

À l'aide du Catalogue des équipements (onglet Blocs dans un sous-système, niveau 3), choisissez les composants de chaque catégorie :

| Catégorie | Composant retenu | Fabricant | Masse (kg) | Puissance (W) | Coût (k€) | Qté | Masse totale |
|----------|-------------------|-------------|-----------|-----------|-------------|-----|-----------|
| Carte EPS | | | | | | 1 | |
| Batterie | | | | | | 1 | |
| Panneaux solaires | | | | | | | |
| OBC | | | | | | 1 | |
| Roue de réaction | | | | | | x | |
| Magnétocoupleur | | | | | | x | |
| Senseur stellaire | | | | | | | |
| Senseur solaire | | | | | | x | |
| Transpondeur | | | | | | 1 | |
| Antenne | | | | | | | |
| Charge utile | | | | | | 1 | |
| Structure | | | | | | 1 | |
| Harnais | | | | | | 1 | |
| Propulsion | | | | | | | |
| **TOTAL** | | | **_____** | | **_____** | | |

**Estimation paramétrique (séance 2.4) :** _____ kg

**Total fondé sur les équipements :** _____ kg

**Écart :** _____ kg ( _____ %)

**Des incompatibilités ont-elles été détectées ?** (bande RF, tension ou interface incompatibles)

_____________________________________________________________________

_____________________________________________________________________

---

## Partie E : Étude de compromis sur un composant

**Sous-système étudié :** _____________    **Options comparées :** 3

| Critère | Pondération | Option A : _________ | Note | Option B : _________ | Note | Option C : _________ | Note |
|-----------|--------|---------------------|-------|---------------------|-------|---------------------|-------|
| Masse | 0,20 | | | | | | |
| Puissance | 0,15 | | | | | | |
| Coût | 0,20 | | | | | | |
| TRL | 0,15 | | | | | | |
| Héritage en vol | 0,15 | | | | | | |
| Performances | 0,15 | | | | | | |
| **Total pondéré** | **1,00** | | **_____** | | **_____** | | **_____** |

**Option retenue :** _____________    **Note :** _____

**Justification (au-delà des chiffres) :**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Partie F : Contrôle final de l'état des bilans

Après le choix des équipements, consignez l'état final des bilans :

| Bilan | Valeur | Marge | État |
|--------|-------|--------|--------|
| Masse (humide vs allocation) | _____ / _____ kg | _____ % | V / O / R |
| Puissance (mode le plus défavorable vs générateur solaire) | _____ / _____ W | _____ % | V / O / R |
| Marge de liaison | _____ dB | >= 3 dB ? | V / O / R |
| Coût vs plafond | _____ / _____ M€ | _____ % | V / O / R |
| Pointage (RSS vs exigence) | _____ / _____° | _____ % | V / O / R |
| Données (liaison descendante vs production) | _____ / _____ Go/jour | _____ % | V / O / R |

**Un bilan n'est-il pas bouclé ?** _______________________________________________

**Correction proposée :** _______________________________________________

_____________________________________________________________________

---

## Justification des décisions

Expliquez POURQUOI vous avez pris chacune des décisions clés relatives à la structure et à la propulsion.

**Justification du choix du format (pourquoi cette taille, et pas plus grande ou plus petite ?) :**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Justification de la décision relative à la propulsion (sans propulsion : pourquoi pas ? avec propulsion : pourquoi ce type ?) :**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Justification du choix des équipements (quels compromis entre composants ont été les plus difficiles ? quelles concessions avez-vous faites ?) :**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Notes et réflexions

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

# Fiche 4.1 : Choix des équipements et nomenclature

**Nom :** ___________________________  **Date :** ___________  **Équipe :** ___________

**Nom de la mission :** ___________________________  **Format :** ______U

---

## Partie A : Décisions faire, acheter ou réutiliser

Pour chaque sous-système, documentez la décision d'approvisionnement et sa justification :

| Sous-système | Décision (acheter/réutiliser/faire) | Justification | Délai d'approvisionnement |
|-----------|--------------------------|-----------|-----------|
| Structure | | | |
| EPS (générateur solaire) | | | |
| EPS (batterie) | | | |
| EPS (distribution) | | | |
| OBC | | | |
| SCAO (capteurs) | | | |
| SCAO (actionneurs) | | | |
| TTC (émetteur-récepteur) | | | |
| TTC (antenne) | | | |
| Thermique | | | |
| Charge utile | | | |
| Propulsion (le cas échéant) | | | |

---

## Partie B : Nomenclature (BOM)

Complétez la nomenclature à partir de V&V › Nomenclature (vos choix dans le Catalogue des équipements ; la référence et l'ECCN ne figurent pas dans SpaceCDF) :

| ID de l'article | Composant | Fabricant | Référence | Qté | Masse (g) | Puissance (W) | Coût (k€) | TRL | ECCN |
|---------|-----------|-------------|-------------|-----|----------|-----------|-------------|-----|------|
| STR-001 | | | | | | | | | |
| EPS-001 | | | | | | | | | |
| EPS-002 | | | | | | | | | |
| EPS-003 | | | | | | | | | |
| OBC-001 | | | | | | | | | |
| AOCS-001 | | | | | | | | | |
| AOCS-002 | | | | | | | | | |
| AOCS-003 | | | | | | | | | |
| TTC-001 | | | | | | | | | |
| TTC-002 | | | | | | | | | |
| THM-001 | | | | | | | | | |
| PLD-001 | | | | | | | | | |
| HRN-001 | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |

---

## Partie C : Suivi des bilans

Une fois tous les choix effectués, relevez les valeurs des bilans en temps réel dans l'onglet Bilans et les totaux de V&V › Nomenclature :

| Bilan | Total de la nomenclature | Estimation paramétrique | Allocation | Marge | Marge (%) |
|--------|-----------|--------------------|-----------:|-------:|---------:|
| Masse sèche | _____ g | _____ g | _____ g | _____ g | _____ % |
| Puissance crête | _____ W | _____ W | _____ W | _____ W | _____ % |
| Coût total | _____ k€ | _____ k€ | _____ k€ | _____ k€ | _____ % |
| Volume | _____ % de ___U | | 100 % | _____ % | |

Tout tient-il dans les allocations ? O / N

Sinon, que modifieriez-vous ? _______________________________________________

_______________________________________________

---

## Partie D : Évaluation au titre du contrôle des exportations

Énumérez les composants susceptibles d'exiger une licence d'exportation :

| Composant | ECCN / catégorie USML | Contrôlé ? | Licence requise ? | Action nécessaire |
|-----------|---------------------|-------------|-------------------|--------------|
| | | O / N | O / N | |
| | | O / N | O / N | |
| | | O / N | O / N | |
| | | O / N | O / N | |

Y a-t-il des articles soumis aux ITAR ? O / N

Si oui, quel accord TAA (*Technical Assistance Agreement*) ou quelle licence DSP-5 faut-il ?

_______________________________________________

---

## Partie E : Vérification de la compatibilité des interfaces

Pour chaque composant retenu, vérifiez la compatibilité des interfaces :

| Composant | Tension du bus OK ? | Protocole de données OK ? | Bande RF compatible ? | Connecteur OK ? | Notes |
|-----------|:-:|:-:|:-:|:-:|-------|
| | O / N | O / N | O / N / S.O. | O / N | |
| | O / N | O / N | O / N / S.O. | O / N | |
| | O / N | O / N | O / N / S.O. | O / N | |
| | O / N | O / N | O / N / S.O. | O / N | |
| | O / N | O / N | O / N / S.O. | O / N | |
| | O / N | O / N | O / N / S.O. | O / N | |

---

## Partie F : Résolution d'une incompatibilité d'interface

Décrivez une incompatibilité d'interface constatée lors du choix des équipements et la manière dont vous l'avez résolue :

**Problème :** _______________________________________________

_______________________________________________

**Composants concernés :** _______________________________________________

**Cause première :** _______________________________________________

**Résolution retenue :** _______________________________________________

**Incidence sur les bilans :** _______________________________________________

---

## Notes et réflexions

Quelle a été la décision de choix d'équipement la plus difficile ? Pourquoi ?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Fiche 4.2 : Planification de la vérification et de la validation

**Nom :** ___________________________  **Date :** ___________  **Équipe :** ___________

**Nom de la mission :** ___________________________

---

## Partie A : Attribution des méthodes ATIR(D)

Pour 10 exigences clés de votre Matrice V&V (V&V Matrix) dans SpaceCDF, attribuez la méthode de vérification et justifiez-la :

| # | ID exig. | Texte de l'exigence (abrégé) | Méthode (A/T/I/R/D) | Phase (B/C/D) | Niveau (équip./sous-syst./syst.) | Justification |
|---|--------|-------------------------------|:-:|:-:|:-:|--------------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |
| 7 | | | | | | |
| 8 | | | | | | |
| 9 | | | | | | |
| 10 | | | | | | |

**Décompte :** analyse : ___ / essai (test) : ___ / inspection : ___ / revue de conception : ___ / démonstration : ___

---

## Partie B : Exigences à double méthode

Identifiez 3 exigences qui nécessitent À LA FOIS une analyse (confiance précoce) ET un essai (preuve finale) :

| ID de l'exigence | Texte de l'exigence | Analyse (phase B) | Essai (phase C/D) | Pourquoi les deux ? |
|---------------|-----------------|-------------------|------------------|-----------------|
| | | | | |
| | | | | |
| | | | | |

---

## Partie C : Séquence d'essais d'environnement

Pour le lanceur retenu, spécifiez la séquence complète d'essais protovol :

**Lanceur :** _______________  **Référence du manuel utilisateur (PUG) :** _______________

| Étape | Essai | Spécification | Durée | Critères de réussite |
|:----:|------|--------------|----------|--------------|
| 1 | Essai fonctionnel initial | Référence complète des performances | _____ h | Tous les paramètres nominaux |
| 2 | Vibrations sinusoïdales | _____ g, _____ - _____ Hz | _____ min/axe x 3 | Aucun décalage de résonance > 5 % |
| 3 | Vibrations aléatoires | _____ gRMS global | _____ min/axe x 3 | Aucun dommage structural |
| 4 | Essai fonctionnel après vibrations | Identique à l'étape 1 | _____ h | Comparaison avec la référence |
| 5 | Vide thermique -- chaud | + _____ °C (max. prévu + 10 °C) | _____ cycles | Fonctionnel à l'extrême chaud |
| 6 | Vide thermique -- froid | - _____ °C (min. prévu - 10 °C) | _____ cycles | Fonctionnel à l'extrême froid |
| 7 | Essai fonctionnel après TVAC | Identique à l'étape 1 | _____ h | Comparaison avec la référence |
| 8 | Essai de CEM | Requis ? O / N | _____ jour | Aucune interférence |
| 9 | Mesure de la masse | Balance étalonnée (+/- 0,01 kg) | 30 min | M <= _____ kg |
| 10 | Vérification de l'insertion dans le déployeur | Déployeur _____ | 2 h | S'insère ; coulisse librement |

**Durée totale estimée de la campagne d'essais :** _____ semaines

---

## Partie D : Profil de l'essai de vibrations

Relevez le profil de DSP des vibrations aléatoires dans le manuel utilisateur (PUG) de votre lanceur :

| Fréquence (Hz) | Niveau de DSP (g^2/Hz) | Pente |
|:-:|:-:|:-:|
| 20 | | Début |
| 20 - _____ | | + _____ dB/oct |
| _____ - _____ | | Plat |
| _____ - 2000 | | - _____ dB/oct |
| 2000 | | Fin |

**gRMS global (calculé) :** _____ gRMS

**Détaillez votre calcul :**

_______________________________________________

_______________________________________________

_______________________________________________

---

## Partie E : Profil d'un cycle TVAC

Esquissez ou décrivez un cycle TVAC :

**Extrême chaud :** + _____ °C    **Extrême froid :** - _____ °C

**Vitesse de rampe :** _____ °C/min    **Durée de palier aux extrêmes :** _____ h

**Essai fonctionnel à chaque extrême ?** O / N    **Durée de l'essai fonctionnel :** _____ h

**Calculez la durée d'un cycle :**

t_cycle = _______________________________________________

= _____ heures

**Campagne TVAC totale :** _____ cycles x _____ h + _____ h de mise en place = _____ h = _____ jours

---

## Partie F : Identification des dérogations

Certaines exigences ne peuvent-elles pas être vérifiées par la méthode standard ? Documentez les dérogations potentielles :

| ID exig. | Méthode standard | Solution de remplacement proposée | Justification | Risque |
|--------|:-:|:-:|--------------|------|
| | | | | |
| | | | | |

---

## Notes et réflexions

Quel essai d'environnement jugez-vous le plus critique pour votre mission ? Pourquoi ?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Fiche 4.3 : Risques, interfaces et AMDEC

**Nom :** ___________________________  **Date :** ___________  **Équipe :** ___________

**Nom de la mission :** ___________________________

---

## Partie A : Registre des risques

Identifiez au moins 5 risques techniques pour la conception de votre mission. Attribuez à chacun un score sur la matrice 5 x 5.

**Rappel du calcul :** L x C = score (L = vraisemblance, *likelihood* ; C = conséquence). Faible (1-4), moyen (5-9), élevé (10-15), critique (16-25).

| # | Description du risque | L (1-5) | C (1-5) | Score | Catégorie (F/M/É/C) | Stratégie de réduction | Responsable (poste) | Score après réduction |
|:-:|-----------------|:-:|:-:|:-:|:-:|-------------------|:-:|:-:|
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | |
| 6 | | | | | | | | |
| 7 | | | | | | | | |

**Combien de risques sont élevés ou critiques (avant réduction) ?** _____

**Combien restent élevés ou critiques après réduction ?** _____

---

## Partie B : Report sur la matrice des risques 5 x 5

Reportez vos risques sur la matrice ci-dessous. Inscrivez le numéro du risque dans la case appropriée.

```
             Conséquence ->
             1       2       3       4       5
  P   5 |       |       |       |       |       |
  r   4 |       |       |       |       |       |
  o   3 |       |       |       |       |       |
  b   2 |       |       |       |       |       |
  a   1 |       |       |       |       |       |
```

---

## Partie C : Matrice d'interfaces N-carré (N^2)

Remplissez la matrice d'interfaces des sous-systèmes de votre mission. Utilisez les abréviations suivantes :
- **P** = puissance (électrique)
- **D** = données (I2C, SPI, UART, CAN, RS-422)
- **R** = RF (coaxial)
- **M** = mécanique (fixation, alignement)
- **T** = thermique (conductif/radiatif)

|  | EPS | OBC | SCAO | TTC | Charge utile | Structure |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **EPS** | --- | | | | | |
| **OBC** | | --- | | | | |
| **SCAO** | | | --- | | | |
| **TTC** | | | | --- | | |
| **Charge utile** | | | | | --- | |
| **Structure** | | | | | | --- |

**Nombre total d'interfaces identifiées :** _____

**Conflits d'interface détectés :** (décrivez-en au moins 2)

1. Conflit : _______________________________________________

   Résolution : _______________________________________________

2. Conflit : _______________________________________________

   Résolution : _______________________________________________

---

## Partie D : Tableau d'AMDEC (FMECA)

Remplissez le tableau pour 4 composants critiques :

| Composant | Fonction | Mode de défaillance | Cause | Effet local | Effet système | Gravité (1-5) | Méthode de détection | Disposition compensatoire |
|-----------|----------|-------------|-------|-------------|---------------|:-:|:-:|:-:|
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |

---

## Partie E : Analyse des points de défaillance unique

Énumérez tous les points de défaillance unique (SPF) de votre conception :

| # | Composant | Mode de défaillance | Effet sur la mission | SPF ? | Acceptable ? | Réduction (si non acceptable) |
|:-:|-----------|-------------|-------------------|:-:|:-:|:-:|
| 1 | | | | O/N | O/N | |
| 2 | | | | O/N | O/N | |
| 3 | | | | O/N | O/N | |
| 4 | | | | O/N | O/N | |
| 5 | | | | O/N | O/N | |

**Nombre total de SPF identifiés :** _____    **Acceptés :** _____    **Réduits :** _____

---

## Partie F : Calcul de fiabilité

Calculez la fiabilité série de la chaîne critique de votre mission (composants qui doivent tous fonctionner pour que la mission réussisse) :

| Composant | Fiabilité individuelle (R_i) | Durée de mission considérée |
|-----------|:--:|:-:|
| | | |
| | | |
| | | |
| | | |
| | | |

**R_series = R_1 x R_2 x ... x R_n = _____________________________**

**R_series = ___________**

Si vous ajoutiez de la redondance sur un composant (p. ex. double mécanisme de déploiement), refaites le calcul :

**R_redundant = 1 - (1 - R)^2 = 1 - (1 - _____)^2 = _____**

**Nouvelle R_series (avec redondance) = _____**

**Amélioration : de _____ à _____ (+ _____ points de pourcentage)**

---

## Partie G : Discussion sur les risques

Quel est l'élément le plus risqué de votre conception ? Que faudrait-il (coût, masse, délais) pour ramener ce risque à un niveau acceptable ?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

## Notes et réflexions

Quel point de défaillance unique vous inquiète le plus ? L'accepteriez-vous, ou sa réduction est-elle indispensable ?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Fiche 4.4 : Estimation des coûts et revue de conception

**Nom :** ___________________________  **Date :** ___________  **Équipe :** ___________

**Nom de la mission :** ___________________________

---

## Partie A : Estimation du coût de la mission (WBS)

Complétez à la fois avec des estimations paramétriques (Bilans › Coût et Analyses › Boucle de conception, coût par poste) et des estimations ascendantes (devis fournisseurs de la nomenclature) :

| N° WBS | Élément | Paramétrique (k€) | Ascendante (k€) | Écart | Notes |
|:-----:|---------|------------------:|------------------:|:----------:|-------|
| 1.0 | Gestion de programme | | | | |
| 2.0 | Ingénierie système | | | | |
| 3.0 | Assurance de mission | | | | |
| 4.0 | Charge utile | | | | |
| 5.0 | Matériel de la plateforme | | | | |
|  | 5.1 Structure et mécanismes | | | | |
|  | 5.2 EPS | | | | |
|  | 5.3 SCAO | | | | |
|  | 5.4 TTC | | | | |
|  | 5.5 OBC et gestion des données | | | | |
|  | 5.6 Thermique | | | | |
|  | 5.7 Propulsion | | | | |
|  | 5.8 Harnais | | | | |
| 6.0 | Intégration et essais | | | | |
| 7.0 | Logiciel (FSW + GSW) | | | | |
| 8.0 | Services de lancement | | | | |
| 9.0 | Segment sol | | | | |
| 10.0 | Exploitation (_____ ans) | | | | |
| | **TOTAL** | **_____** | **_____** | | |

---

## Partie B : Niveaux de confiance

**Estimation P50 (votre meilleure estimation) :** _____ k€

**Estimation P70 (P50 x 1,2) :** _____ k€

**Estimation P80 (P50 x 1,3) :** _____ k€

Expliquez votre raisonnement sur le multiplicateur (1,3 est-il approprié, ou devrait-il être plus élevé pour votre mission ?) :

_______________________________________________

_______________________________________________

_______________________________________________

---

## Partie C : Coût d'une constellation (le cas échéant)

**Nombre de satellites :** _____    **Taux d'apprentissage :** _____ %

**b = ln(learning_rate) / ln(2) = ln(_____) / ln(2) = _____**

| Unité n° | Coût unitaire (k€) = C_1 x N^b | Cumul (k€) |
|:------:|-----------------------------:|------------------:|
| 1 | | |
| 2 | | |
| 4 | | |
| 8 | | |
| _____ (total) | | |

Détaillez votre calcul du coût total de la constellation :

Matériel : _____ unités x _____ k€ en moyenne = _____ k€

Rechanges (____ %) : _____ unités x _____ k€ = _____ k€

Lancement : _____ satellites x _____ k€ = _____ k€

Segment sol : _____ k€

Exploitation (_____ ans) : _____ k€

PM/SE/MA (gestion de projet, ingénierie système, assurance de mission) : _____ k€

**Coût total de la constellation : _____ k€ = _____ M€**

**Coût P80 de la constellation (x 1,3) : _____ M€**

---

## Partie D : Facteurs de coût

**Les 3 principaux facteurs de coût de votre mission (d'après Bilans › Coût et le tableau des coûts de la boucle de conception) :**

| Rang | Élément de coût | Coût (k€) | % du total | Pourquoi est-il coûteux ? |
|:----:|-------------|------------:|-----------:|---------------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

**Que modifieriez-vous pour réduire le coût total de 20 % ?**

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

## Partie E : État de préparation à la revue de conception

Dans V&V › Jalons de revue, évaluez votre état de préparation à la SRR ou à la PDR :

| # | Critère de jalon | État (réussi/échoué/manuel) | Emplacement des preuves | En cas d'échec : action nécessaire |
|:-:|---------------|:------------------------:|:-:|:-:|
| 1 | Besoin de mission justifié | | | |
| 2 | Exigences complètes et traçables | | | |
| 3 | Tous les bilans bouclés avec marge | | | |
| 4 | Équipements choisis (nomenclature complète) | | | |
| 5 | Interfaces définies, conflits résolus | | | |
| 6 | Démarche de V&V définie | | | |
| 7 | Risques identifiés avec mesures de réduction | | | |
| 8 | Estimation des coûts avec WBS | | | |
| 9 | ConOps défini | | | |
| 10 | Conformité en matière de durabilité | | | |

**Critères obligatoires satisfaits :** _____ / _____

**État de préparation global :** PRÊT / NON PRÊT

**Actions à mener pour être prêt :**

1. _______________________________________________

2. _______________________________________________

3. _______________________________________________

---

## Partie F : Préparation de la présentation

Établissez le plan de votre présentation de revue de conception de 12 minutes :

| Section | Durée | Message clé | Preuves / données à montrer |
|---------|:--------:|------------|---------------------|
| 1. Besoin de mission | 2 min | | |
| 2. Pourquoi l'espace ? | 2 min | | |
| 3. Conception du système | 3 min | | |
| 4. Équipements et V&V | 2 min | | |
| 5. Risques et coûts | 2 min | | |
| 6. Exploitation et retour d'expérience | 1 min | | |

---

## Notes et réflexions

Quel est l'élément le plus incertain de votre estimation des coûts ? Comment réduiriez-vous cette incertitude ?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Fiche 5.1 : Segment sol et architecture des opérations

**Nom :** ___________________________  **Date :** ___________  **Équipe :** ___________

**Nom de la mission :** ___________________________  **Orbite :** _____ km, inclinaison de _____°

---

## Partie A : Analyse des contacts avec la station sol

**Calculez la durée de contact et le volume de données par passage pour votre mission.**

### Paramètres d'entrée

| Paramètre | Valeur | Source |
|-----------|-------|--------|
| Altitude orbitale (h) | _____ km | Choix d'orbite dans SpaceCDF |
| Angle d'élévation minimal (epsilon) | _____° | Spécification de la station sol (typiquement 5-10) |
| Débit de la liaison descendante (R) | _____ Mbit/s | Bilan de liaison SpaceCDF |
| Efficacité protocolaire (eta) | _____ (typiquement 0,85-0,95) | Estimation du surdébit CCSDS |
| Latitude de la station sol | _____° | Station retenue |
| Rayon terrestre (R_E) | 6371 km | Constante |

### Calculs

**Distance oblique maximale :**

rho = R_E x (sqrt((h/R_E + 1)^2 - cos^2(epsilon)) - sin(epsilon))

rho = 6371 x (sqrt((_____/6371 + 1)^2 - cos^2(_____)) - sin(_____))

rho = _____ km

**Durée moyenne d'un passage (approximative) :**

T_avg ~ _____ minutes (d'après STK/SpaceCDF ou par estimation : ~6 min pour une SSO à 500 km)

**Volume de données par passage :**

V_data = R x T x eta = _____ Mbit/s x _____ s x _____ = _____ Mbit = _____ Mo

---

## Partie B : Bouclage du bilan de données

| Paramètre | Valeur | Unité |
|-----------|------:|------|
| Données produites par jour (charge utile) | | Mo/jour |
| Données produites par jour (servitude) | | Mo/jour |
| **Production quotidienne totale** | | **Mo/jour** |
| | | |
| Passages par jour (station 1 : _____________) | | passages |
| Données par passage (station 1) | | Mo |
| Sous-total liaison descendante (station 1) | | Mo/jour |
| | | |
| Passages par jour (station 2 : _____________) | | passages |
| Données par passage (station 2) | | Mo |
| Sous-total liaison descendante (station 2) | | Mo/jour |
| | | |
| **Capacité quotidienne totale de liaison descendante** | | **Mo/jour** |
| | | |
| **Marge du bilan de données** | | **Mo/jour** |
| **Marge en pourcentage** | | **%** |

**Le bilan de données est-il bouclé ?** O / N

Sinon, quelles modifications permettraient de le boucler ? (cochez toutes celles qui s'appliquent)

- [ ] Ajouter une autre station sol à : _______________
- [ ] Porter le débit à : _____ Mbit/s (nécessite : _______________)
- [ ] Réduire la production de données de la charge utile à : _____ Mo/jour (incidence : _______________)
- [ ] Ajouter une compression à bord (taux : _____:1)
- [ ] Utiliser le réseau SatNOGS pour des passages supplémentaires
- [ ] Autre : _______________________________________________

---

## Partie C : Conception du réseau de stations sol

| Station n° | Lieu | Latitude | Antenne | Bande | Débit | Passages/jour | Rôle |
|:-:|---------|:--------:|---------|:----:|:---------:|:----------:|------|
| 1 | | | | | | | TTC principale |
| 2 | | | | | | | Liaison descendante charge utile |
| 3 | | | | | | | Secours/SatNOGS |

**Estimation du coût total du segment sol :** _____ k€

| Élément de coût | Coût annuel (k€) | Notes |
|-------------|-------------------:|-------|
| Location / propriété des antennes | | |
| Licence du logiciel MCS | | |
| Connectivité réseau | | |
| Personnel d'exploitation (_____ ETP) | | |
| **Total annuel** | | |
| **Durée de vie de la mission (_____ ans)** | | |

---

## Partie D : Chronologie de la LEOP

Construisez la chronologie de la LEOP pour les 72 premières heures après la séparation :

| Heure (UTC) | Temps SIM | Activité | Critère de réussite | État |
|-----------|----------|---------|-------------------|:------:|
| T+0 | Séparation | Libération des interrupteurs de déploiement | | [ ] |
| T+30 min | Expiration de la minuterie | Commande du déploiement de l'antenne | | [ ] |
| T+_____ | | Acquisition de la balise | Verrouillage de la porteuse | [ ] |
| T+_____ | | Première télémesure de servitude (HK) | Données décodées | [ ] |
| T+_____ | | Première télécommande envoyée | ACK reçu | [ ] |
| T+_____ | | Déploiement du générateur solaire (s'il est distinct) | Production de puissance confirmée | [ ] |
| T+_____ | | Initialisation du SCAO | Détermination d'attitude active | [ ] |
| T+_____ | | Étalonnage du SCAO | Pointage < _____° | [ ] |
| T+_____ | | Validation du duplex intégral | Liaisons montante et descendante au débit opérationnel | [ ] |
| T+_____ | | Évaluation de l'état de santé terminée | Tous les sous-systèmes nominaux | [ ] |

---

## Partie E : Chronologie des opérations de la mission (diagramme de Gantt)

Esquissez la chronologie des opérations, du lancement à la fin de vie :

```
Phase :      LEOP  Recette     Début expl.  Opérations nominales       EOL
Semaine : 1  2  3  4  5  6  7  8  9  ... 26 ... 52 ... 104 ... 156
          |  |  |  |  |  |  |  |  |       |      |       |       |
Effectifs : ______________________________________________
          24/7     16/7        8/5         8/5 ou automatisé   8/5

Jalons clés :
  L+___ : première lumière
  L+___ : fin de la recette en orbite
  L+___ : manœuvre de maintien d'orbite (le cas échéant)
  L+___ : fin de la mission nominale
  L+___ : mission prolongée (le cas échéant)
  L+___ : passivation et désorbitation
```

---

## Notes et réflexions

Quel est l'aspect le plus difficile de la conception de votre segment sol ? Que feriez-vous différemment avec un budget plus important ?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Fiche 5.2 : Concepts d'opérations de mission

**Nom :** ___________________________  **Date :** ___________  **Équipe :** ___________

**Nom de la mission :** ___________________________

---

## Partie A : Modes opérationnels

Définissez tous les modes opérationnels de votre engin spatial. Saisissez-les dans l'onglet Modes (Machine de modes ; puissance par mode sous Puissance par mode).

| Mode | Description | Puissance (W) | Débit | Condition d'entrée | Condition de sortie |
|------|------------|:---------:|:---------:|----------------|---------------|
| Survie | | | | | |
| Amortissement | | | | | |
| Attente | | | | | |
| Science | | | | | |
| Liaison descendante | | | | | |
| Éclipse | | | | | |
| Manœuvre | | | | | |
| | | | | | |

**Vérifiez :** le bilan de puissance est-il bouclé dans chaque mode ?

| Mode | Puissance consommée (W) | Puissance disponible (W) | Marge (W) | Bouclé ? |
|------|:---------------------:|:-------------------:|:----------:|:-------:|
| Survie | | | | O / N |
| Amortissement | | | | O / N |
| Attente | | | | O / N |
| Science | | | | O / N |
| Liaison descendante | | | | O / N |
| Éclipse (batterie seule) | | | | O / N |

---

## Partie B : Règles FDIR

Définissez au moins 5 règles FDIR pour votre engin spatial :

| # | Description du défaut | Méthode de détection | Seuil | Niveau FDIR (0-4) | Réponse autonome | Procédure de reprise |
|:-:|------------------|-----------------|-----------|:-:|:-:|:-:|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |

**Le mode survie peut-il maintenir l'engin spatial indéfiniment (puissance + thermique) ?** O / N

Sinon, quelle est la durée maximale en mode survie ? _____ heures

**Chaque action FDIR autonome peut-elle faire l'objet d'un forçage depuis le sol ?** O / N

Sinon, lesquelles ne le peuvent pas ? _______________________________________________

---

## Partie C : Procédure nominale

Rédigez une procédure nominale pour votre mission (observation scientifique ou transmission de données au sol) :

**ID de la procédure :** _____________  **Titre :** _______________________________________________

**Préconditions :**

_______________________________________________

_______________________________________________

| Étape | Action | Résultat attendu | En cas d'échec |
|:----:|--------|----------------|----------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |

**Postconditions :**

_______________________________________________

---

## Partie D : Procédure de contingence

Rédigez une procédure de contingence (p. ex. reprise après passage en mode survie, rétablissement après perte de communication) :

**ID de la procédure :** _____________  **Titre :** _______________________________________________

**Condition de déclenchement :**

_______________________________________________

**Niveau de gravité :** vert / jaune / orange / rouge

| Étape | Action | Résultat attendu | En cas d'échec | Délai d'attente |
|:----:|--------|----------------|----------------|:-------:|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |

**Escalade :** si cette procédure échoue, faites remonter à : _______________________________________________

**Postconditions :**

_______________________________________________

---

## Partie E : Effectifs d'exploitation

Estimez les effectifs nécessaires pour chaque phase de la mission :

| Phase | Durée | Quarts/jour | Personnes/quart | Total ETP | Coût annuel (k€) |
|-------|----------|:----------:|:-----------:|:---------:|---------:|
| LEOP | _____ jours | 3 (24/7) | | | |
| Recette en orbite | _____ semaines | 2 (16/7) | | | |
| Premières opérations | _____ mois | 1 (8/5) | | | |
| Opérations nominales | _____ ans | 1 (8/5) ou automatisé | | | |
| Fin de vie | _____ semaines | 1 (8/5) | | | |
| **Total** | | | | | |

---

## Partie F : Scénario d'anomalie

Scénario hypothétique : votre satellite passe en mode survie pendant un week-end. Le prochain contact sol a lieu lundi matin (dans 40 heures). Déroulez votre réponse :

1. **Que fait l'engin spatial en mode survie ?**

   _______________________________________________

   _______________________________________________

2. **Survivra-t-il 40 heures ? (Vérifiez la puissance et la thermique.)**

   _______________________________________________

   _______________________________________________

3. **Quelle télémesure examinerez-vous en premier lundi ?**

   _______________________________________________

   _______________________________________________

4. **Quel est votre plan de reprise ?**

   _______________________________________________

   _______________________________________________

---

## Notes et réflexions

Quel degré d'autonomie votre engin spatial doit-il avoir ? Où se situe la frontière entre la prise de décision à bord et le contrôle depuis le sol ?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Fiche 5.3 : Journée de simulation de mission

**Nom :** ___________________________  **Date :** ___________  **Équipe :** ___________

**Nom de la mission :** ___________________________

**Votre rôle :** ___________________________  (FD / SC / GSO / PO / FD-nav / Logger)

---

## Journal des événements de la simulation

Consignez TOUS les événements, décisions et actions en temps réel pendant la simulation :

| # | Temps SIM | Heure réelle | Événement / observation | Action menée | Résultat | Consigné par |
|:-:|----------|:---------:|--------------------:|-------------|--------|:---------:|
| 1 | T+0 | | Séparation | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |
| 7 | | | | | | |
| 8 | | | | | | |
| 9 | | | | | | |
| 10 | | | | | | |
| 11 | | | | | | |
| 12 | | | | | | |
| 13 | | | | | | |
| 14 | | | | | | |
| 15 | | | | | | |
| 16 | | | | | | |
| 17 | | | | | | |
| 18 | | | | | | |
| 19 | | | | | | |
| 20 | | | | | | |

---

## Liste de vérification de la LEOP

Cochez chaque jalon de la LEOP dès qu'il est atteint pendant la simulation :

| # | Jalon | Heure d'atteinte | État | Notes |
|:-:|-----------|:-------------:|:------:|-------|
| 1 | Séparation confirmée | | [ ] | |
| 2 | Minuterie de 30 min expirée | | [ ] | |
| 3 | Antenne déployée | | [ ] | |
| 4 | Balise acquise | | [ ] | |
| 5 | Première télémesure de servitude (HK) décodée | | [ ] | |
| 6 | Première télécommande acquittée (ACK) | | [ ] | |
| 7 | Générateur solaire déployé (si distinct) | | [ ] | |
| 8 | Amortissement (detumbling) du SCAO terminé | | [ ] | |
| 9 | Étalonnage du SCAO terminé | | [ ] | |
| 10 | Duplex intégral validé | | [ ] | |
| 11 | Tous les sous-systèmes nominaux | | [ ] | |

---

## Fiche de traitement d'anomalie 1

Remplissez cette fiche pour chaque anomalie injectée pendant la simulation.

| Champ | Saisie |
|-------|-------|
| **ID de l'anomalie** | ANO-SIM-001 |
| **Temps SIM** | |
| **Heure réelle** | |
| **Gravité** | vert / jaune / orange / rouge |
| **Sous-système concerné** | |

**Observation** (valeurs de télémesure exactes et symptômes) :

_______________________________________________

_______________________________________________

_______________________________________________

**Évaluation initiale** (que s'est-il passé selon vous ?) :

_______________________________________________

_______________________________________________

_______________________________________________

**Diagnostic** (cause première après investigation) :

_______________________________________________

_______________________________________________

_______________________________________________

**Actions menées** (télécommandes envoyées, procédures exécutées) :

| Étape | Heure | Action | Résultat attendu | Résultat obtenu |
|:----:|:----:|--------|----------------|:-------------:|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Résultat final** (état du système après traitement) :

_______________________________________________

_______________________________________________

**Suivi nécessaire :**

_______________________________________________

**Procédure utilisée :** _______________  **A-t-elle fonctionné telle que rédigée ?** O / N / en partie

Sinon, quelles modifications sont nécessaires ? _______________________________________________

---

## Fiche de traitement d'anomalie 2

| Champ | Saisie |
|-------|-------|
| **ID de l'anomalie** | ANO-SIM-002 |
| **Temps SIM** | |
| **Heure réelle** | |
| **Gravité** | vert / jaune / orange / rouge |
| **Sous-système concerné** | |

**Observation** (valeurs de télémesure exactes et symptômes) :

_______________________________________________

_______________________________________________

_______________________________________________

**Évaluation initiale** (que s'est-il passé selon vous ?) :

_______________________________________________

_______________________________________________

_______________________________________________

**Diagnostic** (cause première après investigation) :

_______________________________________________

_______________________________________________

_______________________________________________

**Actions menées** (télécommandes envoyées, procédures exécutées) :

| Étape | Heure | Action | Résultat attendu | Résultat obtenu |
|:----:|:----:|--------|----------------|:-------------:|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Résultat final** (état du système après traitement) :

_______________________________________________

_______________________________________________

**Suivi nécessaire :**

_______________________________________________

**Procédure utilisée :** _______________  **A-t-elle fonctionné telle que rédigée ?** O / N / en partie

Sinon, quelles modifications sont nécessaires ? _______________________________________________

---

## Fiche de traitement d'anomalie 3

| Champ | Saisie |
|-------|-------|
| **ID de l'anomalie** | ANO-SIM-003 |
| **Temps SIM** | |
| **Heure réelle** | |
| **Gravité** | vert / jaune / orange / rouge |
| **Sous-système concerné** | |

**Observation** (valeurs de télémesure exactes et symptômes) :

_______________________________________________

_______________________________________________

_______________________________________________

**Évaluation initiale :**

_______________________________________________

_______________________________________________

**Diagnostic :**

_______________________________________________

_______________________________________________

**Actions menées :**

| Étape | Heure | Action | Résultat attendu | Résultat obtenu |
|:----:|:----:|--------|----------------|:-------------:|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |

**Résultat final :**

_______________________________________________

**Procédure utilisée :** _______________  **A-t-elle fonctionné telle que rédigée ?** O / N / en partie

---

## État de la recette en orbite

À l'issue de la phase de recette en orbite de la simulation, consignez l'état de vérification de chaque sous-système :

| Sous-système | Vérification terminée ? | Performances vs spécification | Problèmes constatés |
|-----------|:-:|:-:|:-:|
| EPS | [ ] | Nominal / dégradé / défaillant | |
| OBC | [ ] | Nominal / dégradé / défaillant | |
| SCAO | [ ] | Nominal / dégradé / défaillant | |
| TTC | [ ] | Nominal / dégradé / défaillant | |
| Thermique | [ ] | Nominal / dégradé / défaillant | |
| Charge utile | [ ] | Nominal / dégradé / défaillant | |
| Propulsion | [ ] | Nominal / dégradé / défaillant / S.O. | |

---

## Synthèse des opérations nominales

À l'issue de la phase d'opérations nominales, consignez :

| Indicateur | Prévu | Réel (simulé) | Écart |
|--------|--------:|-------------------:|---------:|
| Observations scientifiques réalisées | | | |
| Données transmises au sol (Mo) | | | |
| Anomalies rencontrées | | | |
| Contacts sol établis | | | |
| Passages en mode survie | | | |

---

## Débriefing de la simulation

### Qu'est-ce qui a bien fonctionné ?

_______________________________________________

_______________________________________________

_______________________________________________

### Qu'est-ce qui pourrait être amélioré ?

_______________________________________________

_______________________________________________

_______________________________________________

### Faiblesses de conception révélées par la simulation :

_______________________________________________

_______________________________________________

_______________________________________________

### Modifications de procédures nécessaires :

_______________________________________________

_______________________________________________

_______________________________________________

### Lacunes FDIR identifiées :

_______________________________________________

_______________________________________________

---

## Notes et réflexions

Quel a été le moment le plus stressant de la simulation ? Que vous a-t-il appris sur les opérations ?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Fiche 5.4 : Revue finale et présentations

**Nom :** ___________________________  **Date :** ___________  **Équipe :** ___________

**Nom de la mission :** ___________________________

---

## Partie A : Synthèse de la conception finale

Relevez l'état final de votre conception dans V&V › Bilans consolidés, l'onglet Bilans et Analyses › Conflits :

| Paramètre | Valeur | Unité | Marge | Marge (%) | État (V/O/R) |
|-----------|------:|------|-------:|---------:|:-:|
| Masse sèche | | kg | | | |
| Masse humide (si propulsion) | | kg | | | |
| Puissance du générateur solaire (EOL) | | W | | | |
| Capacité de la batterie | | Wh | | | |
| Marge de liaison (cas le plus défavorable) | | dB | | | |
| Précision de pointage | | ° | | | |
| Équilibre des données | | Mo/jour | | | |
| Coût total (P50) | | k€ | | | |
| Coût total (P80) | | k€ | | | |
| Score de conformité en matière de débris | | /100 | | | |
| Durée de vie de la mission | | ans | | | |

**Tous les bilans sont-ils bouclés ?** O / N    **Sinon, lesquels ne le sont pas ?** _______________________________________________

**Nombre de conflits non résolus :** _____

---

## Partie B : Liste de vérification de la documentation

Cochez chaque document généré depuis Exporter (barre d'outils) :

| Document | Généré ? | Complet ? | Notes |
|----------|:----------:|:---------:|-------|
| MRD (document des exigences de mission) | [ ] | [ ] | |
| Spécification technique | [ ] | [ ] | |
| Plan de vérification | [ ] | [ ] | |
| Document ConOps | [ ] | [ ] | |
| SEMP (plan de management de l'ingénierie système) | [ ] | [ ] | |
| IRD (document des exigences d'interface) | [ ] | [ ] | |
| Plan de gestion des risques | [ ] | [ ] | |
| Plan d'essais | [ ] | [ ] | |
| Nomenclature | [ ] | [ ] | |
| Modèle de notification UIT | [ ] | [ ] | |
| Dossier LSTS (RSSSA) | [ ] | [ ] | |
| Évaluation au titre du contrôle des exportations | [ ] | [ ] | |
| Rapport de fin de vie | [ ] | [ ] | |
| Immatriculation auprès du CUPEEA (COPUOS) | [ ] | [ ] | |

**Nombre total de documents générés :** _____ / 14

---

## Partie C : Plan de la présentation

Préparez votre présentation de revue de conception finale de 12 minutes :

| Section | Durée | Points clés à aborder | Preuves / données à montrer |
|---------|:----:|--------------------|-----------------------|
| 1. Besoin de mission | 2 min | | |
| 2. Pourquoi l'espace ? | 2 min | | |
| 3. Conception du système | 3 min | | |
| 4. Équipements et V&V | 2 min | | |
| 5. Risques et coûts | 2 min | | |
| 6. Exploitation et retour d'expérience | 1 min | | |

**Présentateur(s) ou présentatrice(s) :** _______________________________________________

**Diapositives de secours préparées sur :** _______________________________________________

---

## Partie D : Évaluation par les pairs

*Remplissez cette partie pendant que vous évaluez la présentation d'une autre équipe.*

**Équipe évaluée :** ___________________________

**Évaluateurs :** ___________________________

| # | Critère | Note (0-2) | Commentaires / questions |
|:-:|-----------|:----------:|---------------------|
| 1 | Besoin de mission clairement justifié | | |
| 2 | Exigences complètes et traçables | | |
| 3 | Tous les bilans bouclés avec marge | | |
| 4 | Équipements choisis au moyen de compromis justifiés | | |
| 5 | Interfaces définies, conflits résolus | | |
| 6 | Démarche de V&V définie | | |
| 7 | Risques identifiés avec mesures de réduction | | |
| 8 | Estimation des coûts avec WBS et P80 | | |
| 9 | ConOps et segment sol conçus | | |
| 10 | Conformité en matière de durabilité | | |
| | **TOTAL** | **/ 20** | |

**Qualité de la présentation :**

| Critère | Note (1-5) | Commentaires |
|-----------|:----------:|---------|
| Clarté de la communication | | |
| Recours aux preuves (des données, pas des affirmations) | | |
| Capacité à répondre aux questions | | |
| Gestion du temps | | |

**Recommandation du comité :** GO / NO GO / GO AVEC ACTIONS

**Actions pour l'équipe qui présente :**

| # | Action | Responsable | Échéance |
|:-:|--------|:-----------:|:--------:|
| 1 | | | |
| 2 | | | |
| 3 | | | |

**Point fort principal de la conception de cette équipe :**

_______________________________________________

**Principal axe d'amélioration :**

_______________________________________________

---

## Partie E : Retour d'expérience

1. **Quelle a été la décision de conception la plus difficile pour votre équipe ?**

   _______________________________________________

   _______________________________________________

   _______________________________________________

2. **Que feriez-vous différemment si vous recommenciez le cours ?**

   _______________________________________________

   _______________________________________________

   _______________________________________________

3. **De quoi la conception a-t-elle besoin maintenant (activités de phase B) ?**

   _______________________________________________

   _______________________________________________

   _______________________________________________

4. **Quelle fonctionnalité de SpaceCDF vous a été la plus utile ?**

   _______________________________________________

   _______________________________________________

5. **Quelle fonctionnalité vous a manqué ?**

   _______________________________________________

   _______________________________________________

6. **Quelle notion de ce cours appliquerez-vous dans votre travail futur ?**

   _______________________________________________

   _______________________________________________

   _______________________________________________

---

## Partie F : Grille d'autoévaluation

Évaluez vos propres apprentissages au cours des trois semaines du cours. Soyez honnête -- cette grille sert à votre propre réflexion et n'est pas notée.

| Compétence | Début de la semaine 1 (1-5) | Maintenant (1-5) | Preuves de progression |
|-----------|:------------------:|:---------:|-------------------|
| Définir une mission spatiale en partant du problème, et non de la solution | | | |
| Rédiger des exigences vérifiables et traçables (format SMART) | | | |
| Mener une étude de compromis structurée avec des critères pondérés | | | |
| Dimensionner des sous-systèmes à l'aide de modèles paramétriques et de bilans d'ingénierie | | | |
| Choisir des équipements COTS et vérifier la compatibilité des interfaces | | | |
| Construire une matrice de vérification avec les méthodes ATIR(D) | | | |
| Évaluer les risques à l'aide d'une matrice 5 x 5 et définir des mesures de réduction | | | |
| Estimer le coût d'une mission par des méthodes paramétriques et ascendantes | | | |
| Concevoir un segment sol et calculer un bilan de données | | | |
| Définir des modes opérationnels, des règles FDIR et des procédures | | | |
| Traiter des anomalies selon une démarche systématique | | | |
| Présenter une conception à un comité de revue, preuves à l'appui | | | |

**Échelle :** 1 = aucune connaissance, 2 = notions de base, 3 = capable d'appliquer avec un accompagnement, 4 = capable d'appliquer en autonomie, 5 = capable d'enseigner à d'autres

**Autoévaluation globale :**

Au début de ce cours, j'aurais décrit mes compétences en ingénierie système comme suit :

_______________________________________________

Aujourd'hui, je les décrirais comme suit :

_______________________________________________

**Ce dont je suis le plus fier ou la plus fière dans ce cours :**

_______________________________________________

_______________________________________________

---

## Notes et réflexions

Dernières réflexions sur le cours, sur le processus de conception et sur la suite :

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

# Revue finale et présentations

*Déplacé de la conclusion de la partie 2 du manuel vers le cahier d'exercices, afin de figurer avec les fiches dont il dépend.*


> **Lectures attendues avant cette séance.** SMAD4, chap. 22 (optimisation) ; Wertz et al., SME, chap. 9.



**Prérequis :** toutes les séances précédentes (conception complète jusqu'à la simulation)
**Références :** ECSS-M-ST-10C Rev.1, section 6 (revues) ; NPR 7123.1D, annexe G ; NASA SEH Rev 2, section 3.7 ; ECSS-E-ST-10C, section 4 (dossier technique)

---

## Objectifs d'apprentissage

À la fin de cette séance, les personnes participantes seront en mesure de :
1. préparer un dossier complet de documentation de conception en vue de la revue ;
2. mener une présentation de revue de conception fondée sur des arguments étayés par des preuves ;
3. évaluer la conception d'une équipe de pairs au regard des critères de jalon ;
4. formuler des retours techniques constructifs à l'aide d'une grille d'évaluation structurée ;
5. dégager un retour d'expérience et formuler les prochaines étapes de la phase B.

---

## 1. Revue de la documentation de conception
Avant de présenter, chaque équipe doit vérifier que sa documentation de conception est complète et cohérente en interne.

### Liste de vérification de la documentation

| Document | Source dans SpaceCDF | Point de contrôle |
|----------|-------------------|-------------|
| Document des exigences de mission (MRD) | Exporter -> Ingénierie système | Toutes les exigences sont-elles intégrées au référentiel ? |
| Spécification technique (TS) | Exporter -> Revues de conception (dossier SRR / PDR) | Tous les bilans sont-ils repris ? |
| Concept d'opérations (ConOps) | Exporter -> Ingénierie système | Toutes les phases sont-elles définies ? |
| Plan de vérification (VP) | Onglet Matrice V&V | Toutes les exigences ont-elles une méthode ? |
| Nomenclature (BOM) | Exporter -> Ingénierie système ; V&V › Nomenclature | Tous les équipements sont-ils listés avec leur TRL ? |
| Registre des risques | Fiche 4.3 | Tous les risques sont-ils notés et réduits ? |
| Matrice d'interfaces (N^2) | Fiche 4.3 | Interfaces identifiées ? Conflits résolus ? |
| Estimation des coûts | Fiche 4.4 | WBS complet ? P80 calculé ? |
| Concept d'opérations | Onglets Modes et FDIR | Modes, FDIR et procédures définis ? |
| Évaluation de la durabilité | Carte Durabilité (Sustainability Card) | Score de conformité en matière de débris ? |

### Contrôles de cohérence interne

Avant de présenter, vérifiez :

| Contrôle | Comment vérifier | Erreur fréquente |
|-------|-------------|-------------|
| Le bilan de masse est bouclé | Bilans › Masse : marge > 0 % | Équipements ajoutés sans mise à jour du bilan |
| Le bilan de puissance est bouclé | Modes › Énergie par orbite : chaque mode est tenable | Puissance en mode éclipse non vérifiée |
| Le bilan de liaison est bouclé | Analyses › Segment sol : marge >= 3 dB | Affaiblissement dû à la pluie non pris en compte |
| Le bilan de données est bouclé | Modes › Chaîne de données : liaison descendante quotidienne >= production quotidienne | Nombre de passages par jour surestimé |
| Le coût respecte le plafond | Bilans › Coût : total <= budget alloué | Coût de lancement ou d'exploitation oublié |
| Les exigences sont traçables | Chaque exigence est rattachée à un objectif | Exigences orphelines (sans objectif parent) |
| La V&V est complète | Chaque exigence a une méthode attribuée | Entrées « TBD » (à déterminer) restantes |
| Aucun conflit non résolu | Analyses › Conflits : aucun ouvert | Incompatibilités d'interface non traitées |

### Génération des documents dans SpaceCDF

Ouvrez **Exporter** dans la barre d'outils et générez tous les documents :
1. Documents ECSS : MRD, TS, VP, ConOps, SEMP, IRD
2. Données de conception : BOM, données du modèle paramétrique
3. Dossiers réglementaires : API UIT, LSTS (RSSSA), évaluation au titre du contrôle des exportations, CUPEEA (COPUOS), rapport de fin de vie (EOL)
4. Présentation : données de la diapositive de synthèse (remplies automatiquement)

---

## 2. Structure de la présentation
Chaque équipe présente une revue de conception de 12 minutes, suivie de 5 minutes de questions-réponses avec le comité d'évaluation par les pairs.

*[Source : ECSS-M-ST-10C Rev.1, section 6 ; NPR 7123.1D, annexe G (processus de revue)]*

### Plan de la présentation
| Section | Durée | Contenu | Preuves |
|---------|----------|---------|----------|
| **1. Besoin de mission** | 2 min | Énoncé du problème ; parties prenantes ; objectifs avec MoP | Étape Besoin de mission |
| **2. Pourquoi l'espace ?** | 2 min | Résultats de l'étude de compromis ; pourquoi la solution spatiale l'emporte sur les autres | Résultats du compromis de mission |
| **3. Conception du système** | 3 min | Architecture ; orbite ; paramètres clés ; état des bilans | Onglet Bilans, V&V › Bilans consolidés |
| **4. Équipements et vérification** | 2 min | Équipements clés ; synthèse de la nomenclature ; démarche de V&V ; plan d'essais | Nomenclature, matrice V&V |
| **5. Risques et coûts** | 2 min | 5 principaux risques ; estimation des coûts (P50/P80) ; calendrier | Registre des risques, onglet Coûts |
| **6. Exploitation et retour d'expérience** | 1 min | Synthèse du ConOps ; FDIR ; ce que vous changeriez | ConOps, débriefing de la simulation |

### Bonnes pratiques de présentation

**Conception des diapositives :**
- un seul message clé par diapositive ;
- des données, pas de prose (bilans, tableaux de compromis, pas de paragraphes) ;
- des diapositives de secours avec les analyses détaillées pour les questions-réponses.

**Prise de parole :**
- Commencez par les conclusions : « Notre bilan de masse est bouclé avec une marge de 22 % »
- Étayez chaque affirmation : « L'analyse du bilan de liaison montre une marge de 4,2 dB dans le cas le plus défavorable »
- Reconnaissez honnêtement les risques : « Le déploiement de l'antenne est notre risque le plus élevé, avec un score de 12 (L3 x C4) »
- Face à une question à laquelle vous ne savez pas répondre : « Bonne question -- nous la prenons comme action »

**Écueils fréquents à éviter :**
- lire les diapositives mot pour mot ;
- dissimuler les problèmes connus (les comités de revue les trouvent toujours) ;
- présenter une analyse sans en énoncer les hypothèses ;
- s'attarder sur la description de la mission et survoler les résultats techniques.

---

## 3. Processus d'évaluation par les pairs
Chaque équipe joue le rôle de comité de revue pour une autre équipe. Ce dispositif reproduit le processus réel de revue de conception, dans lequel un comité indépendant évalue le projet.

### Rôles au sein du comité de revue

| Rôle | Responsabilité | Questions clés à poser |
|------|---------------|---------------------|
| **Président** | Conduit la revue ; veille à ce que tous les critères soient couverts | « Vérifions méthodiquement chaque critère de jalon » |
| **Évaluateur système** | Évalue l'architecture d'ensemble et les bilans | « Tous les bilans sont-ils bouclés ? Quelle est la marge minimale ? » |
| **Évaluateur technique** | Évalue les décisions de conception des sous-systèmes | « Pourquoi avez-vous choisi ce composant plutôt que les autres solutions ? » |
| **Évaluateur risques** | Évalue la gestion des risques et la V&V | « Quel est votre risque le plus élevé ? La mesure de réduction est-elle adaptée ? » |
| **Évaluateur opérations** | Évalue le ConOps, le segment sol et les aspects réglementaires | « Que se passe-t-il si vous perdez le contact pendant 48 heures ? » |

### Évaluation au regard des critères de jalon

Le comité de revue évalue l'équipe qui présente au regard des critères de jalon de niveau PDR :

| # | Critère | Note (0-2) | Notes |
|---|-----------|------------|-------|
| 1 | Besoin de mission clairement justifié | 0 = absent, 1 = partiel, 2 = solide | Le problème est-il réel ? L'espace est-il la bonne réponse ? |
| 2 | Exigences complètes et traçables | 0/1/2 | Toutes les exigences sont-elles rattachées à des objectifs ? Vérifiables ? |
| 3 | Tous les bilans bouclés avec une marge suffisante | 0/1/2 | Masse, puissance, liaison, données, pointage -- tous positifs ? |
| 4 | Équipements choisis au moyen de compromis justifiés | 0/1/2 | Nomenclature complète ? TRL suffisant ? Études de compromis documentées ? |
| 5 | Interfaces définies et conflits résolus | 0/1/2 | Matrice N^2 ? Aucun conflit non résolu ? |
| 6 | Démarche de V&V définie pour toutes les exigences | 0/1/2 | Méthodes attribuées ? Plan d'essais esquissé ? |
| 7 | Risques identifiés avec mesures de réduction | 0/1/2 | Registre des risques avec scores ? Principaux risques réduits ? |
| 8 | Estimation des coûts avec WBS et P80 | 0/1/2 | Paramétrique et ascendante ? Courbe d'apprentissage appliquée ? |
| 9 | ConOps et segment sol conçus | 0/1/2 | Modes définis ? Architecture FDIR ? Stations sol ? |
| 10 | Conformité en matière de durabilité | 0/1/2 | Conformité en matière de débris ? Règle des 5 ans de la FCC ? Plan de passivation ? |

### Banque de questions pour le comité de revue

Questions types que le comité de revue peut poser :

- « Pourquoi l'espace est-il la bonne réponse ? Quelles autres solutions ont été envisagées ? »
- « Quelle est votre marge de masse ? Qu'est-ce qui la détermine ? Et si la charge utile pesait 20 % de plus que prévu ? »
- « Présentez-moi votre bilan de liaison dans le cas le plus défavorable. Quelle est la marge minimale ? »
- « Quels sont vos 3 principaux risques ? Quel est le risque résiduel après réduction ? »
- « Montrez-moi votre bilan de données. Est-il bouclé avec une seule station sol ? »
- « Que se passe-t-il lors d'un passage en mode survie en éclipse ? Le bilan thermique tient-il ? »
- « Quel composant a le TRL le plus bas ? Quel est votre plan de qualification ? »
- « Avez-vous engagé la démarche de licence de spectre ? Qu'y a-t-il sur le chemin critique ? »
- « Quelle est votre liste de points de défaillance unique ? Lesquels avez-vous acceptés ? »
- « Si vous disposiez de 6 mois et de 20 % de budget supplémentaires, que changeriez-vous ? »

---

## 4. Présentations des équipes
### Consignes

**Déroulement des présentations :** 12 minutes de présentation + 5 minutes de questions-réponses par équipe.

Pour 4 équipes, prévoyez 17 min x 4 = 68 min. Adaptez le minutage au nombre réel d'équipes. S'il y a moins de 4 équipes, accordez 15 min de présentation + 8 min de questions-réponses.

**Pour l'équipe qui présente :**
1. Présentez le plan en 6 sections ci-dessus.
2. Utilisez SpaceCDF en direct pour des démonstrations lorsque c'est utile (montrez l'onglet Bilans et V&V › Bilans consolidés).
3. Répondez aux questions du comité preuves à l'appui.

**Pour le comité de revue :**
1. Remplissez le formulaire d'évaluation des critères de jalon de la fiche 5.4.
2. Posez au moins 3 questions de fond.
3. Formulez une recommandation GO / NO GO / GO AVEC ACTIONS.
4. Documentez les actions avec une personne responsable et une échéance.

**Après chaque présentation :**
- la présidence annonce la recommandation du comité ;
- les actions sont consignées ;
- brefs applaudissements et passage à l'équipe suivante.

---

## 5. Clôture du cours et retour d'expérience
### Réflexion individuelle
Chaque personne participante remplit la grille d'autoévaluation de la fiche 5.4, en réfléchissant à ses apprentissages au cours des trois semaines.

### Retour d'expérience de l'équipe
Chaque équipe discute des points suivants et en rend compte :

1. **Décision de conception la plus difficile :** quel compromis a été le plus difficile à trancher ? Pourquoi ?
2. **Plus grande surprise :** quel aspect de la conception de mission s'est le plus éloigné de vos attentes ?
3. **Retours sur l'outil :** quelle fonctionnalité de SpaceCDF a été la plus utile ? Qu'est-ce qui manquait ?
4. **Enseignement sur le processus :** en quoi la conception concourante a-t-elle changé votre approche de l'ingénierie ?
5. **Si c'était à refaire :** que feriez-vous différemment en semaine 1 ?

### Points clés à retenir du cours
| Semaine | Thème | Leçon essentielle |
|------|-------|------------|
| **Semaine 1** | Exigences et architecture | Partez du problème, pas de la solution. Les exigences définissent le QUOI, pas le COMMENT. |
| **Semaine 2** | Conception des sous-systèmes et bilans | Les bilans d'ingénierie sont le langage de l'ingénierie système. Tout se négocie contre tout. |
| **Semaine 3** | Intégration, vérification et opérations | Bien construire le produit (vérification) et construire le bon produit (validation) comptent autant que sa conception. Les opérations révèlent ce que l'analyse ne peut pas montrer. |

### Le cycle en V de l'ingénierie système -- parcouru

```
Point de départ :                          Point d'arrivée :

  Besoin de mission                          Mission validée
     |                                              ^
     v                                              |
  Exigences                                 Exigences vérifiées
     |                                              ^
     v                                              |
  Conception système                        Système intégré (simulation)
     |                                              ^
     v                                              |
  Conception sous-système                   V&V sous-système planifiées
     |                                              ^
     v                                              |
  Équipements choisis  ------>  Équipements vérifiés (BOM + conformité)

  Semaines 1-2 (branche gauche)    Semaine 3 (branche droite)
```

*Vous avez parcouru l'intégralité du cycle en V : du besoin de mission à une conception vérifiée et validée.*

### Prochaines étapes pour les personnes participantes

- **L'accès à SpaceCDF** est maintenu après le cours
- **Appliquez la méthode** à vos propres missions ou projets
- **Utilisez l'outil** pour des études de type CDF avec votre équipe
- **Reportez-vous au manuel du cours** pour les plans de séance et les annexes
- **Faites part de vos retours** pour améliorer le cours au profit des prochaines promotions

### Évaluation du cours

Distribuez le formulaire d'évaluation du cours. Questions clés :
- Quelle séance a été la plus utile ? La moins utile ?
- Quels contenus faudrait-il ajouter ? Supprimer ?
- Quelle a été l'efficacité de la journée de simulation ?
- Recommanderiez-vous ce cours à des collègues ?
- Quelle est la chose que vous ferez différemment dans votre pratique de l'ingénierie à la suite de ce cours ?

---

## Références citées

| # | Référence | URL |
|---|-----------|-----|
| 1 | ECSS-M-ST-10C Rev.1 (*Project Planning and Implementation*) | https://ecss.nl/standard/ecss-m-st-10c-rev-1-project-planning-and-implementation/ |
| 2 | NPR 7123.1D, annexe G (*Review Process*) | https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7123&s=1D |
| 3 | NASA SEH Rev 2, section 3.7 (*Technical Reviews*) | https://www.nasa.gov/reference/systems-engineering-handbook/ |
| 4 | ECSS-E-ST-10C (*System Engineering*) | https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/ |

---

## Synthèse de la séance

| Thème | Point clé |
|-------|-------------|
| Documentation | Dossier complet : MRD, TS, ConOps, VP, nomenclature, registre des risques, coûts, aspects réglementaires |
| Cohérence | Tous les bilans doivent être bouclés ; aucun conflit non résolu ; exigences entièrement traçables |
| Présentation | 6 sections : besoin, justification, conception, V&V, risques + coûts, exploitation + retour d'expérience |
| Évaluation par les pairs | Un comité indépendant évalue au regard des critères de jalon ; GO/NO GO/GO avec actions |
| Bonnes pratiques | Commencer par les conclusions, montrer les preuves, reconnaître les risques, répondre directement |
| Cycle en V | Le cours parcourt l'intégralité du V : besoins -> exigences -> conception -> V&V -> validation |
| Retour d'expérience | Documenter ce qui a fonctionné, ce qui a échoué et ce qu'il faut changer -- c'est le véritable résultat |

