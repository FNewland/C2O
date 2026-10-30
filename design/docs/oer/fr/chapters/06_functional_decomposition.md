# Chapitre 6 — Décomposition fonctionnelle et allocation

> **Lectures préalables conseillées.** NASA *Systems Engineering Handbook* §4.3 (*Logical Decomposition*) ; ECSS-E-ST-10C Rev.1 §5.3 ; INCOSE *Systems Engineering Handbook*, 5e éd., §2.3.5. Ce chapitre suppose qu'un ensemble d'exigences validé existe (chapitre 5) et s'appuie sur le cycle en V du chapitre 1.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez en mesure de :

1. expliquer le rôle de la décomposition fonctionnelle comme passerelle entre les exigences et la conception ;
2. décomposer les objectifs de la mission en un arbre fonctionnel hiérarchique (trois niveaux ou plus) ;
3. classer les fonctions par type (observer, communiquer, naviguer, pointer, alimenter, protéger, stocker, traiter, soutenir) ;
4. allouer les fonctions aux domaines des sous-systèmes, y compris l'allocation multiple pour les responsabilités partagées ;
5. dériver des exigences de l'analyse fonctionnelle ;
6. identifier et combler les lacunes de couverture (fonctions terminales sans exigence associée) ;
7. construire et valider l'architecture fonctionnelle d'un petit satellite, dans un outil de conception concourante ou dans un tableur.

---

## 6.1 Qu'est-ce que la décomposition fonctionnelle ?

*[Source : NASA SEH sect. 4.3 — Process 3: Logical Decomposition]*

La décomposition fonctionnelle répond à une seule question : **« Que doit FAIRE le système pour satisfaire les exigences ? »**

Elle établit une passerelle entre les exigences (CE QUE le système doit accomplir) et la conception physique (COMMENT il sera réalisé). Les fonctions décrivent les *actions* que le système doit exécuter, sans préciser le matériel ni le logiciel qui les exécuteront. Dans le cycle en V du chapitre 1 (figure 1.1), c'est l'étape située entre les exigences système et l'architecture : les exigences du chapitre 5 sont ici décomposées en fonctions, et ces fonctions sont allouées aux sous-systèmes dont les frontières et les interfaces sont définies au chapitre 8.

### 6.1.1 Le flux de décomposition

La figure 6.1 montre les trois couches et le sens du flux. Les objectifs et les exigences énoncent ce qui est nécessaire ; l'analyse fonctionnelle énonce ce que le système doit faire ; l'architecture physique énonce ce qui le fera.

<svg viewBox="0 0 800 360" xmlns="http://www.w3.org/2000/svg" style="max-width:700px; font-family: sans-serif; font-size: 12px;">
  <!-- Boxes -->
  <rect x="250" y="10" width="300" height="40" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="400" y="35" text-anchor="middle" fill="#1e40af" font-weight="bold">Objectifs et exigences</text>
  <!-- Arrow -->
  <line x1="400" y1="50" x2="400" y2="80" stroke="#64748b" stroke-width="2" marker-end="url(#arrowhead6)"/>
  <rect x="250" y="80" width="300" height="40" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="400" y="105" text-anchor="middle" fill="#92400e" font-weight="bold">Analyse fonctionnelle (QUOI)</text>
  <line x1="400" y1="120" x2="400" y2="150" stroke="#64748b" stroke-width="2" marker-end="url(#arrowhead6)"/>
  <rect x="250" y="150" width="300" height="40" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="400" y="175" text-anchor="middle" fill="#166534" font-weight="bold">Architecture physique (COMMENT)</text>
  <!-- Side annotations -->
  <text x="570" y="70" fill="#64748b" font-size="11">Fait le lien</text>
  <!-- Function tree below -->
  <rect x="100" y="230" width="180" height="30" rx="4" fill="#fef3c7" stroke="#d97706"/>
  <text x="190" y="250" text-anchor="middle" fill="#92400e" font-size="11">F-001 : Acquérir des images</text>
  <!-- Children -->
  <line x1="190" y1="260" x2="100" y2="290" stroke="#d97706"/>
  <line x1="190" y1="260" x2="280" y2="290" stroke="#d97706"/>
  <line x1="190" y1="260" x2="460" y2="290" stroke="#d97706"/>
  <rect x="20" y="290" width="160" height="26" rx="4" fill="#fff7ed" stroke="#d97706"/>
  <text x="100" y="308" text-anchor="middle" fill="#92400e" font-size="10">F-002 : Pointer la cible</text>
  <rect x="200" y="290" width="160" height="26" rx="4" fill="#fff7ed" stroke="#d97706"/>
  <text x="280" y="308" text-anchor="middle" fill="#92400e" font-size="10">F-003 : Capter l'image</text>
  <rect x="380" y="290" width="160" height="26" rx="4" fill="#fff7ed" stroke="#d97706"/>
  <text x="460" y="308" text-anchor="middle" fill="#92400e" font-size="10">F-004 : Stocker à bord</text>
  <!-- Universal functions -->
  <rect x="580" y="230" width="180" height="30" rx="4" fill="#e0e7ff" stroke="#4f46e5"/>
  <text x="670" y="250" text-anchor="middle" fill="#3730a3" font-size="11">Fonctions universelles</text>
  <text x="670" y="280" text-anchor="middle" fill="#3730a3" font-size="10">F-010 : Produire l'énergie</text>
  <text x="670" y="296" text-anchor="middle" fill="#3730a3" font-size="10">F-020 : Maintenir l'env. thermique</text>
  <text x="670" y="312" text-anchor="middle" fill="#3730a3" font-size="10">F-030 : Résister au lancement</text>
  <text x="670" y="328" text-anchor="middle" fill="#3730a3" font-size="10">F-040 : TTC avec le sol</text>
  <text x="670" y="344" text-anchor="middle" fill="#3730a3" font-size="10">F-050 : Retrait en fin de vie</text>
  <defs><marker id="arrowhead6" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/></marker></defs>
</svg>

**Figure 6.1** — Le flux de décomposition, des objectifs et exigences à l'architecture physique (COMMENT) en passant par l'analyse fonctionnelle (QUOI). En bas : le sommet d'un arbre fonctionnel d'observation de la Terre et les cinq fonctions universelles que tout engin spatial assure.

### 6.1.2 Types de fonctions

Toute fonction d'un engin spatial relève de l'une des catégories suivantes :

| Type | Verbe | Description | Exemple |
|------|------|-------------|---------|
| **Observer** | Détecter/mesurer | Acquérir des données sur l'environnement | Acquérir des images multispectrales, recevoir des signaux AIS |
| **Communiquer** | Transférer | Acheminer l'information entre les éléments | Transmettre au sol les données scientifiques, envoyer des télécommandes vers le bord |
| **Naviguer** | Déterminer/contrôler la position | Connaître ou modifier l'orbite | Effectuer une manœuvre de maintien d'orbite |
| **Pointer** | Orienter | Contrôler l'attitude de l'engin spatial | Pointage nadir pendant la prise de vue, poursuite d'une cible |
| **Alimenter** | Produire/stocker/distribuer | Fournir l'énergie électrique | Production de puissance solaire, gestion de la charge de la batterie |
| **Protéger** | Maintenir l'environnement | Maintenir les composants dans leurs limites | Contrôle thermique, blindage contre les rayonnements |
| **Stocker** | Enregistrer | Mettre les données en mémoire tampon pour un usage ultérieur | Enregistrement des données à bord sur mémoire de masse à l'état solide |
| **Traiter** | Transformer | Convertir les données d'une forme à une autre | Compression d'images à bord, mise en trames de niveau L0 |
| **Soutenir** | Assurer la structure | Intégrité mécanique | Résister aux charges du lancement, déployer les mécanismes |

### 6.1.3 Fonctions universelles

Quel que soit le type de mission, **tout engin spatial** doit assurer les cinq fonctions suivantes :

1. **produire l'énergie électrique** (solaire, RTG, batterie) ;
2. **maintenir l'environnement thermique** (contrôle thermique passif/actif) ;
3. **résister à l'environnement du lancement** (charges structurales, vibrations, chocs) ;
4. **communiquer avec le sol pour la TTC** (télémesure, poursuite, télécommande) ;
5. **assurer le retrait de service de l'engin spatial en fin de vie** (désorbitation, orbite cimetière, passivation).

Parce qu'elles sont universelles, ces cinq fonctions devraient figurer dans tout arbre fonctionnel avant le début de toute analyse propre à la mission ; un outil de conception concourante les génère généralement de façon automatique pour chaque mission.

---

## 6.2 Arbres fonctionnels propres à chaque type de mission

Des types de mission différents produisent des arbres de fonctions principales fondamentalement différents. Les fonctions universelles restent les mêmes ; c'est la branche propre à la mission qui fait la différence.

### 6.2.1 Observation de la Terre (optique/SAR)

```
F-001 : Acquérir des images de la zone cible
  ├── F-002 : Pointer l'instrument vers la cible
  ├── F-003 : Acquérir les données image (exposer le détecteur / impulsion SAR)
  ├── F-004 : Stocker à bord les données acquises
  └── F-005 : Transmettre les données à la station sol
```

**Exemple réel — Planet SuperDove :** F-001 se décompose en acquisition push-broom sur 8 bandes, correction radiométrique à bord, compression sans perte et liaison descendante en bande X. Chaque sous-fonction est tracée vers des exigences précises de SuperDove (distance d'échantillonnage au sol (GSD) de 3,7 m, 8 bandes spectrales, liaison descendante à 200 Mbit/s).

### 6.2.2 Relais de télécommunications (stockage et retransmission ou transparent)

```
F-001 : Relayer les communications entre utilisateurs
  ├── F-002 : Recevoir le signal montant du terminal utilisateur
  ├── F-003 : Traiter et acheminer les données (stockage et retransmission ou transparent)
  └── F-004 : Émettre le signal descendant vers le terminal destinataire ou la passerelle
```

**Exemple réel — Astrocast (IoT) :** F-001 se décompose en réception en bande L (depuis les objets connectés), dédoublonnage des messages à bord et stockage-retransmission, puis liaison descendante UHF/bande S vers les stations passerelles. Chaque message fait au plus 160 octets.

*[Source : Astrocast, « Astrocast Network Overview », astrocast.com]*

### 6.2.3 Récepteur AIS/IoT (passif)

```
F-001 : Recevoir et traiter les signaux d'intérêt
  ├── F-002 : Recevoir les signaux AIS/IoT (passif — aucune émission montante)
  ├── F-003 : Décoder et valider les messages
  ├── F-004 : Stocker à bord les données traitées
  └── F-005 : Transmettre au sol pour diffusion
```

### 6.2.4 Fonctions du segment sol

Les missions qui comportent des traitements au sol ont besoin de fonctions relevant du domaine sol :

```
F-G01 : Recevoir les données satellite à la station sol
F-G02 : Traiter les données en chaîne (produits L0 → L1 → L2)
F-G03 : Archiver et diffuser les produits de données aux utilisateurs
F-G04 : Exploiter le centre de contrôle de mission (planification, commande, surveillance)
```

Les fonctions sol sont allouées aux domaines sol (station sol, traitement sol, capteur sol) exactement de la même manière que les fonctions spatiales sont allouées aux sous-systèmes ; l'architecture du segment sol qui les accueille est développée au chapitre 17.

---

## 6.3 Allocation aux sous-systèmes

Chaque fonction doit être **allouée** à un ou plusieurs domaines de sous-systèmes responsables. Cette allocation définit les frontières du système et, point essentiel, fait apparaître des **interfaces** partout où une fonction est partagée. Ces interfaces sont les entrées de la matrice N² construite au chapitre 8, §8.3.

### 6.3.1 Règles d'allocation

| Fonction | Allocation typique | Allocation multiple ? |
|----------|-------------------|-------------------|
| Acquérir des images | Charge utile | Non (responsable unique) |
| Pointer la cible | SCAO (système de contrôle d'attitude et d'orbite) | Non |
| Stocker les données | OBC/gestion des données | Non |
| Transmettre les données au sol | Télécom + SCAO | **Oui** — télécom pour la chaîne RF, SCAO pour le pointage de l'antenne |
| Produire l'énergie | EPS | Non |
| Maintenir l'environnement thermique | Thermique | Non |
| Relayer les communications | Charge utile + télécom | **Oui** — la frontière dépend de l'architecture |
| Résister au lancement | Structure | Non |
| Retrait de service en fin de vie | Propulsion (ou opérations) | Non (ou multiple en cas de voile de traînée) |

### 6.3.2 Allocation multiple et identification des interfaces

Lorsqu'une fonction est allouée à plusieurs sous-systèmes, elle crée une **interface** qui doit être gérée explicitement.

**Exemple — « Transmettre les données à la station sol » :**

| Sous-système responsable | Contribution | Interface créée |
|-----------------------|-------------|-------------------|
| Télécom (liaison) | Transpondeur, antenne, modulation, chaîne RF | Télécom ↔ SCAO (pointage de l'antenne) |
| SCAO | Pointage de l'antenne vers la station sol pendant le passage | Télécom ↔ gestion des données (routage des paquets) |
| Gestion des données | Mise en paquets, priorisation, mise en trames CCSDS | Gestion des données ↔ SCAO (programmation des passages) |

Dans un tableau des fonctions, l'allocation multiple s'enregistre simplement en indiquant, en regard de la fonction, chacun des domaines qui y contribuent ; toute la rigueur consiste ensuite à désigner un **responsable** unique et à traiter les autres comme des **contributeurs**.

**Matière à réflexion.** Pour chaque fonction à allocation multiple d'une conception, où faut-il tracer la frontière du système ? Qui est « responsable » de la fonction, et qui n'est que « contributeur » ? La réponse détermine qui rédige l'exigence d'interface — et qui doit rendre des comptes lorsque l'interface fait défaut à l'intégration.

### 6.3.3 Exigences dérivées des fonctions

Chaque fonction allouée engendre des **exigences dérivées** — des exigences que les parties prenantes n'ont pas formulées explicitement, mais qui sont nécessaires au fonctionnement de la fonction :

| Fonction | Exigence dérivée | Logique de dérivation |
|----------|-------------------|------------------|
| « Pointer l'instrument vers la cible » | « Le SCAO doit assurer une précision de pointage ≤ 0,1° pendant la prise de vue » | À partir de l'exigence de GSD et de la géométrie optique |
| « Stocker les données à bord » | « L'OBDH doit fournir une mémoire de masse à l'état solide ≥ 32 Go » | À partir du débit × période orbitale × marge pour passages manqués |
| « Transmettre au sol pendant la fenêtre de visibilité quotidienne » | « L'émetteur doit assurer un débit effectif ≥ 50 Mbit/s » | À partir du volume de données quotidien / durée totale de contact |
| « Produire l'énergie dans tous les modes » | « Le générateur solaire doit produire ≥ 15 W en EOL » | À partir de la demande de puissance la plus défavorable en phase éclairée + recharge |

*[Source : NASA SEH sect. 4.3.3 — exigences dérivées de l'allocation fonctionnelle]*

---

## 6.4 Critères de performance et analyse de couverture

Chaque fonction terminale (fonction sans sous-fonction) doit être assortie de **critères de performance** — des seuils quantitatifs qui définissent « à quel niveau » la fonction doit être assurée :

| Fonction | Critères de performance |
|----------|---------------------|
| Acquérir des images | GSD ≤ 10 m ; RSB ≥ 100:1 ; ≥ 4 bandes spectrales |
| Pointer la cible | Précision ≤ 0,1° ; stabilité ≤ 0,01°/s ; vitesse de basculement ≥ 1°/s |
| Transmettre les données au sol | Marge de liaison ≥ 3 dB ; volume quotidien transmis ≥ 5 Go |
| Produire l'énergie | Marge positive dans tous les modes ; DoD de la batterie ≤ 30 % |
| Maintenir l'environnement thermique | Tous les composants dans leur plage de fonctionnement avec une marge ≥ 5 °C |

Les critères de performance constituent la base quantitative des exigences au niveau des sous-systèmes.

### 6.4.1 Analyse de couverture

**Chaque fonction terminale** doit être tracée vers au moins une exigence. Sinon, il existe une **lacune de couverture** — la fonction est définie mais ne dispose d'aucune voie de vérification.

Une vérification de couverture classe chaque fonction terminale dans l'un des trois états suivants :

- **Couverte :** la fonction est associée à au moins une exigence ;
- **Lacune :** aucune exigence n'est associée — une lacune de couverture a été détectée ;
- **Conflit :** la fonction entre en conflit avec une exigence existante.

Un outil de conception concourante affiche généralement ces états sous forme de pastilles sur l'arbre fonctionnel ; dans un tableur, un simple décompte des identifiants d'exigences associés à chaque fonction terminale produit le même résultat.

### 6.4.2 Exemple de mission réelle : la lacune de couverture de CAPSTONE

La mission CAPSTONE de la NASA (2022, Advanced Space) a connu une lacune de couverture pendant son développement : la fonction « maintenir l'attitude pendant les manœuvres de correction de trajectoire » ne comportait initialement aucune exigence formelle de pointage pendant les poussées. Cette lacune, relevée lors de la revue fonctionnelle, a conduit à dériver l'exigence SSR-AOCS-007 : « Le SCAO doit maintenir une précision de pointage ≤ 2° pendant toutes les manœuvres propulsives. »

*[Source : Advanced Space, « CAPSTONE Mission Overview », 2022]*

---

## 6.5 Exemple résolu : arbre fonctionnel d'un CubeSat 3U d'observation de la Terre

> **Arbre fonctionnel d'un CubeSat 3U de surveillance agricole (EOSat-3U)**
>
> ```
> F-001 : Acquérir des images multispectrales
>   ├── F-002 : Pointer le télescope vers la zone cible (SCAO)
>   ├── F-003 : Exposer le détecteur et acquérir les trames d'image (charge utile)
>   ├── F-004 : Compresser et stocker les données image (OBC)
>   └── F-005 : Transmettre les données stockées à la station sol (télécommunications + SCAO)
>
> F-010 : Produire l'énergie électrique (EPS)
>   ├── F-011 : Convertir l'énergie solaire en énergie électrique (générateur solaire)
>   ├── F-012 : Stocker l'énergie pour l'éclipse (batterie)
>   └── F-013 : Réguler et distribuer la puissance (carte EPS)
>
> F-020 : Maintenir l'environnement thermique (thermique)
>   ├── F-021 : Évacuer la chaleur dissipée par l'électronique (radiateur)
>   └── F-022 : Maintenir la température de la batterie pendant l'éclipse (réchauffeur)
>
> F-030 : Résister à l'environnement de lancement (structure)
> F-040 : Communiquer avec le sol pour la TT&C (télécommunications)
> F-050 : Retirer le satellite du service en fin de vie (propulsion/opérations)
> ```
>
> **Exigences dérivées de F-002 (pointer le télescope vers la cible) :**
> - SSR-AOCS-001 : « Le SCAO doit atteindre une précision de pointage ≤ 0,5° en mode prise de vue » ;
> - SSR-AOCS-002 : « Le SCAO doit atteindre une stabilité de pointage ≤ 0,01°/s pendant la prise de vue ».
>
> **Allocation multiple de F-005 (transmettre les données au sol) :**
> - sous-système télécom : responsable de la chaîne RF (transpondeur, antenne, modulation) ;
> - sous-système SCAO : assure le pointage de l'antenne vers la station sol ;
> - interface : le SCAO doit recevoir de l'OBC les déclencheurs du programme de passages pour lancer le basculement vers le pointage de la station sol.

Retour sur UniSat-1, le démonstrateur magnétométrique 1U du chapitre 1, §1.7 : son arbre comporte les mêmes cinq fonctions universelles, mais la branche mission se réduit à « F-001 : mesurer le vecteur du champ géomagnétique », avec des sous-fonctions pour échantillonner le magnétomètre MEMS, horodater et stocker les échantillons, puis les transmettre au sol en UHF. Il n'y a aucune fonction « pointer » — c'est pourquoi, au chapitre 10, UniSat-1 n'a besoin d'aucun contrôle d'attitude actif.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Décomposition fonctionnelle | Relie les exigences (QUOI) à la conception (COMMENT) en identifiant les actions du système |
| Types de fonctions | Observer, communiquer, naviguer, pointer, alimenter, protéger, stocker, traiter, soutenir |
| Fonctions universelles | Puissance, thermique, résistance au lancement, TTC, retrait de service — tout engin spatial a besoin des cinq |
| Arbres propres à la mission | OT : acquérir/pointer/stocker/transmettre ; télécom : recevoir/router/émettre ; AIS : recevoir/décoder/stocker |
| Allocation | Chaque fonction est affectée à un ou plusieurs domaines de sous-systèmes ; l'allocation multiple crée des interfaces |
| Exigences dérivées | Les fonctions engendrent de nouvelles exigences non formulées par les parties prenantes |
| Analyse de couverture | Chaque fonction terminale doit être tracée vers au moins une exigence — aucune lacune admise |

## Exercices

1. **Arbre à trois niveaux.** Pour un CubeSat 3U d'observation de la Terre dont l'objectif de mission est de cartographier l'état sanitaire des cultures sur une région agricole de latitude moyenne, construisez un arbre fonctionnel comportant au moins trois niveaux de décomposition et au moins douze fonctions terminales. Incluez les cinq fonctions universelles. Classez chaque fonction terminale par type à l'aide du tableau du §6.1.2.

2. **Exigences dérivées.** Pour chaque fonction terminale de votre arbre de l'exercice 1, rédigez une exigence dérivée assortie d'un seuil mesurable et d'une logique de dérivation tenant en une ligne, dans le style du §6.3.3. Indiquez lesquels de vos seuils vous pouvez justifier dès maintenant par la physique et lesquels doivent attendre un calcul de dimensionnement de sous-système (chapitres 9 à 12).

3. **Tableau de traçabilité.** Construisez un tableau de traçabilité fonctions-exigences comportant au moins huit entrées. Supprimez ensuite délibérément deux exigences et montrez comment une vérification de couverture signalerait les lacunes qui en résultent.

4. **Frontière d'une allocation multiple.** La fonction « transmettre au sol les données stockées » est allouée aux télécoms, au SCAO et à la gestion des données. Proposez un responsable et des contributeurs, nommez les trois interfaces créées et rédigez une exigence d'interface (sous la forme « doit » du chapitre 5) pour l'interface qui vous semble la plus susceptible de poser un problème à l'intégration. Justifiez votre choix.

5. **Contraste entre types de mission.** Rédigez la branche propre à la mission de l'arbre fonctionnel (a) d'un relais IoT à stockage et retransmission et (b) d'un récepteur AIS passif. Quelles fonctions apparaissent dans l'un mais pas dans l'autre, et quel matériel cette différence supprime-t-elle de la mission AIS ?

6. **UniSat-1.** En revenant à UniSat-1 (chapitre 1, §1.7), rédigez son arbre fonctionnel complet. Identifiez la fonction universelle qui est assurée sans sous-système dédié, et expliquez comment l'absence de fonction « pointer » se répercute sur l'architecture du contrôle d'attitude (en anticipant le chapitre 10).

7. **Cas de lacune de couverture.** Le cas CAPSTONE du §6.4.2 montre une fonction dépourvue d'exigence. Donnez deux autres exemples de fonctions d'un petit satellite d'observation de la Terre que l'on laisse facilement sans exigence et, pour chacune, rédigez l'exigence qui comble la lacune.

## Références

1. NASA, *Systems Engineering Handbook* (NASA/SP-2016-6105 Rev 2), 2016, §4.3 (Process 3: Logical Decomposition). https://www.nasa.gov/reference/systems-engineering-handbook/
2. ECSS, *ECSS-E-ST-10C Rev.1: System Engineering General Requirements*, 2017, §5.3. https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/
3. INCOSE, *Systems Engineering Handbook*, 5e éd., 2023, §2.3.5.3. https://www.incose.org/products-and-publications/se-handbook
4. Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, chap. 2. https://www.space.com/smad
5. Blanchard & Fabrycky, *Systems Engineering and Analysis*, 5e éd., 2010, chap. 3. https://www.pearson.com/en-us/subject-catalog/p/systems-engineering-and-analysis/P200000003502
6. Advanced Space, *CAPSTONE Mission Overview*, 2022. https://advancedspace.com/capstone/
7. Astrocast, *Astrocast Network Overview*. https://www.astrocast.com
