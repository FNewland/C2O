# Sous-système de contrôle thermique (TCS) d'EOSAT-1 {#eosat-1-thermal-control-subsystem-tcs}

**Référence du document :** EOSAT1-UM-TCS-004
**Édition :** 2.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Vue d'ensemble {#1-overview}

Le sous-système de contrôle thermique (TCS) maintient tous les composants du satellite dans leurs
plages de température admissibles pendant toute la mission. EOSAT-1 recourt à un contrôle thermique
passif (revêtements de surface, cellules solaires fixées sur la structure, radiateur nadir isolé pour l'imageur
et emplacement de chaque équipement), complété par trois réchauffeurs régulés par thermostat : batterie (8 W), OBC
(4 W) et lit catalytique du propulseur (12 W). La température de chaque équipement suit la puissance qu'il
dissipe ; le satellite se refroidit donc en mode survie et lors d'un délestage. Le refroidisseur du plan focal
(FPA) est géré dans le cadre du sous-système charge utile.

## 2. Contrôle thermique passif {#2-passive-thermal-control}

### 2.1 Isolation (pas de MLI externe) {#21-multi-layer-insulation-mli}

EOSAT-1 ne porte aucune couverture MLI sur ses faces externes : les cellules fixées sur la structure couvrent
l'essentiel de l'extérieur, et un 6U est trop petit pour qu'une plateforme sous MLI rejette ~25–40 W. L'isolation
sert à l'intérieur :

- l'imageur et son radiateur nadir (-Z) forment un îlot thermique sur des fixations peu conductrices
  (titane / G10), de sorte que l'électronique de la plateforme et les 15 W du refroidisseur du FPA n'élèvent pas
  le puits thermique du refroidisseur ;
- la batterie est montée sur entretoises, à l'écart de la structure, sur la paroi froide +Y (voir §2.2).

### 2.2 Radiateurs {#22-radiators}

La plateforme n'a pas de panneaux radiateurs séparés : elle rejette sa chaleur par ses six faces
(0,28 m², émissivité ~0,87 — verre de protection des cellules et peinture blanche). Deux faces ont un rôle
thermique propre :

| Face        | Surface   | Rôle                                                                 |
|-------------|-----------|----------------------------------------------------------------------|
| -Z (nadir)  | 0,023 m² | Radiateur de l'imageur : peinture blanche Z-93, isolé de la plateforme avec l'imageur |
| +Y          | 0,037 m² | Paroi de la batterie : l'angle bêta d'EOSAT-1 vaut de -21 à -31 ° toute l'année, le Soleil est donc toujours du côté -Y et la face +Y n'est jamais éclairée |

### 2.3 Revêtements de surface {#23-surface-coatings}

| Surface                           | Absorptivité solaire | Émissivité IR |
|-----------------------------------|-------------------|--------------|
| Cellules triple jonction, verre de protection | 0,91 | 0,85         |
| Peinture blanche (Z-93), zones sans cellules et radiateur -Z | 0,17 | 0,92  |
| Ouverture / déflecteur de l'imageur (noir) | 0,90     | 0,88         |

Tant que les panneaux fournissent de la puissance, environ un cinquième de la lumière solaire reçue par les cellules
repart sous forme d'électricité et non de chaleur.

## 3. Contrôle thermique actif {#3-active-thermal-control}

### 3.1 Circuit de réchauffeur de batterie {#31-battery-heater-circuit}

Le réchauffeur de batterie est le seul élément de contrôle thermique actif d'EOSAT-1. Tous les autres
composants (OBC, structure, transpondeur) s'appuient sur une gestion thermique passive, assurée par
l'orientation du satellite, la dissipation thermique interne et la conception MLI/radiateurs.

| Circuit     | Emplacement      | Seuil d'allumage | Seuil d'extinction | Puissance |
|-------------|------------------|-------------|--------------|--------|
| Batterie    | Bloc batterie    | 5 °C        | 10 °C        | 8 W    |

Le réchauffeur de batterie se commande par la commande `HEATER_CONTROL` (S8,S1) avec les paramètres
`circuit=battery` et `on` (booléen). La régulation autonome du réchauffeur est mise en œuvre dans la logique
FDIR : elle active le réchauffeur si la température de la batterie descend sous 5 °C et prend le pas sur les
commandes sol si les températures approchent des limites rouges.

**Remarque :** EOSAT-1 comporte également un réchauffeur d'OBC et un réchauffeur de propulseur. Le réchauffeur d'OBC
(`HEATER_OBC`, S8 fonction 41 ; état `htr_obc` 0x040B ; 4 W sur la ligne PDM 6 ; thermostat ON -10 °C /
OFF -5 °C) est un réchauffeur de survie : la dissipation propre de l'OBC le maintient bien au-dessus de -10 °C en
exploitation nominale et en mode survie, et le réchauffeur intervient lors d'un délestage prolongé ou d'une survie en
saison froide. Il dispose d'environ 7 K d'autorité (4 W sur le support de 0,6 W/K de la pile électronique). Le réchauffeur du lit catalytique du propulseur (`HEATER_THRUSTER`, S8 fonction 42 ;
état 0x041B ; 12 W sur la ligne `prop`) préchauffe le propulseur avant une manœuvre.

### 3.2 Orientation au service du contrôle thermique passif {#32-orientation-for-passive-thermal-control}

EOSAT-1 utilise l'orientation du satellite comme stratégie de contrôle thermique passif. L'attitude
AOCS peut être ajustée de façon à présenter différentes faces au Soleil, ce qui permet aux opérateurs
d'agir sur l'environnement thermique :

| Stratégie                   | Effet                                           |
|-----------------------------|-------------------------------------------------|
| Pointage nadir (nominal)    | Environnement thermique équilibré, opérations standard |
| Pointage solaire (+Y vers le Soleil) | Maximise l'échauffement solaire sur +Y, réchauffe la batterie |
| Préparation à l'éclipse (rotation thermique) | Répartit la chaleur entre les faces avant l'éclipse |

Ce contrôle thermique par l'orientation est particulièrement important pendant la LEOP et dans les scénarios
de contingence où la puissance des réchauffeurs actifs doit être économisée. En mode survie, le mode AOCS COARSE_SUN
oriente le satellite vers le Soleil, ce qui assure un réchauffement passif.

### 3.3 Modes de défaillance des réchauffeurs {#33-heater-failure-modes}

| Mode de défaillance | Détection                       | Impact                          |
|-----------------|-------------------------------------|---------------------------------|
| Réchauffeur stuck_on | Température de la batterie qui monte au-delà du seuil ; `htr_battery` reste à 1 | Consommation excessive, surchauffe possible de la batterie |
| Réchauffeur open_circuit | Température de la batterie qui descend sous le seuil ; `htr_battery` = 1 mais aucune réaction de la température | Risque de gel de la batterie en éclipse |

Si un réchauffeur bloqué en marche est détecté, le sol devrait commander `HEATER_CONTROL` (circuit=battery,
on=false) et surveiller. Si le réchauffeur reste allumé, la sortie PDM qui alimente le circuit du réchauffeur
peut être mise hors tension par commande, à titre de mesure d'isolation.

### 3.4 Refroidisseur du FPA {#34-fpa-cooler}

Le refroidisseur du plan focal est un cryoréfrigérateur miniature à cycle de Stirling qui maintient le
détecteur de l'imageur à sa température de fonctionnement d'environ -15 °C. Le refroidisseur
consomme jusqu'à 15 W et nécessite une mise en froid de 30 minutes à partir de la température ambiante.

| Paramètre         | Valeur                       |
|-------------------|------------------------------|
| Type de refroidisseur | Cryoréfrigérateur à cycle de Stirling |
| Température cible du FPA | -15 °C (nominale)     |
| Durée de mise en froid | ~30 min depuis l'ambiante |
| Consommation      | 15 W                         |
| Commande          | Autonome selon le mode de la charge utile |

Le refroidisseur est activé automatiquement lorsque la charge utile passe en mode STANDBY, IMAGING ou
CALIBRATION, et désactivé lorsque la charge utile est mise sur OFF.

## 4. Zones de température {#4-temperature-zones}

| Zone           | Plage nominale   | Limites jaunes   | Limites rouges   |
|----------------|------------------|------------------|------------------|
| Batterie       | 5–25 °C          | 2–40 °C          | 0–45 °C          |
| OBC            | 10–35 °C         | -10–60 °C        | -20–70 °C        |
| Détecteur FPA  | -18 à -12 °C     | -22 à 14 °C      | -25,5 à 17,5 °C  |
| Panneaux de structure | -20 à 40 °C | —                | —                |
| Ailes déployées | -55 à 65 °C    | —                | —                |
| Structure      | -20 à 35 °C      | —                | —                |

Plages orbitales typiques (bêta -30 ° ; la plateforme suit la puissance qu'elle dissipe) :

| Cas                                    | Structure      | OBC            | Batterie       |
|----------------------------------------|----------------|----------------|----------------|
| Nominal, charge utile en STANDBY (refroidisseur en marche) | +15 à +29 °C | +22 à +33 °C | +16 à +22 °C |
| Nominal, refroidisseur arrêté          | +2 à +16 °C  | +8 à +20 °C  | +5 à +10 °C (réchauffeur en cycle) |
| Mode survie (pointage solaire)         | -7 à +7 °C   | -1 à +10 °C  | +5 à +10 °C (réchauffeur en cycle) |
| Délestage prolongé, lignes de réchauffeur sur OFF | -15 à -2 °C | -9 à +2 °C | -11 à -3 °C |

## 5. Paramètres de télémesure {#5-telemetry-parameters}

| ID param. | Nom            | Unité  | Description                          |
|----------|-----------------|--------|--------------------------------------|
| 0x0400   | temp_panel_px   | °C     | Température du panneau +X            |
| 0x0401   | temp_panel_mx   | °C     | Température du panneau -X            |
| 0x0402   | temp_panel_py   | °C     | Température du panneau +Y            |
| 0x0403   | temp_panel_my   | °C     | Température du panneau -Y            |
| 0x0404   | temp_panel_pz   | °C     | Température du panneau +Z (zénith)   |
| 0x0405   | temp_panel_mz   | °C     | Température du panneau -Z (nadir)    |
| 0x0406   | temp_obc        | °C     | Température du module OBC            |
| 0x0407   | temp_battery    | °C     | Température du bloc batterie         |
| 0x0408   | temp_fpa        | °C     | Température du plan focal            |
| 0x0409   | temp_thruster   | °C     | Température de la vanne du propulseur |
| 0x040A   | htr_battery     | booléen | État du réchauffeur de batterie (marche/arrêt) |
| 0x040B   | htr_obc         | booléen | État du réchauffeur de l'OBC (marche/arrêt) |
| 0x040C   | cooler_fpa      | booléen | État du refroidisseur du FPA (marche/arrêt) |

## 6. Définition des limites {#6-limit-definitions}

| Paramètre       | Jaune bas  | Jaune haut  | Rouge bas | Rouge haut |
|-----------------|------------|-------------|---------|----------|
| temp_obc (°C)   | -10        | 60          | -20     | 70       |
| temp_battery (°C)| 2         | 40          | 0       | 45       |
| temp_fpa (°C)   | -22.0      | 14.0        | -25.5   | 17.5     |

Les limites froides de l'OBC suivent le matériel : les OBC de CubeSat sont qualifiés jusqu'à -25 à -40 °C, la
limite rouge à -20 °C garde donc 5 K de marge sur la classe -25 °C, et la limite jaune à -10 °C est aussi le seuil
d'allumage du réchauffeur de l'OBC.

Les bandes du FPA sont **dérivées**, et non choisies : `subsystems/tcs.yaml: fpa_envelope`
est la source unique, et le logiciel sol en calcule tout le reste. Le nœud FPA a deux états de repos légitimes — régulé
n'importe où dans l'enveloppe de consigne commandable de **-20…0 °C**
(`PAYLOAD_COOLER_SETPOINT`, S8 fonction 36), et non refroidi à environ **+11,5 °C**
(crête mesurée à +12,4). La bande englobe les deux, plus 3 sigma de bruit de régulation
(0,5 K), avec une marge de 1,5 K pour le jaune et de 5,0 K pour le rouge. L'ancien
tableau -18/+8, -20/+12 était antérieur à la consigne commandable et transformait une commande légale à
-20 °C en alarme rouge permanente.

**Être assez froid pour prendre des images n'est pas une limite.** C'est le rôle de l'indicateur `fpa_ready`
(0x0610) et des événements `FPA_THERMAL_READY` / `FPA_THERMAL_NOT_READY`
(0x040A / 0x040B) : la boucle stabilisée autour de la consigne *active* (-1 K / +5 K)
**et** le détecteur à **-3.0 °C** ou en dessous. Un étuvage de décontamination
(+50 °C) dépassera la limite rouge haute — délibérément. Vous avez alors sorti le
détecteur de son enveloppe de fonctionnement, et la console doit le signaler.

## 7. Commandes {#7-commands}

| Commande          | Service  | Paramètres              | Description                        |
|-------------------|----------|-------------------------|------------------------------------|
| HEATER_CONTROL    | S8,S1    | circuit, on             | Activer/désactiver un circuit de réchauffeur |
| HK_REQUEST        | S3,S27   | sid=4                   | Demander le paquet de servitude TCS |
| GET_PARAM         | S20,S3   | param_id (0x0400–040C)  | Lire un paramètre TCS individuel   |
| SET_PARAM         | S20,S1   | param_id, value         | Modifier un paramètre de configuration TCS |

## 8. Couplage entre la température des panneaux et l'éclairement solaire {#8-panel-temperature-coupling-to-solar-illumination}

Les cinq panneaux solaires fixés sur la structure (toutes les faces sauf -Z) constituent l'interface thermique principale entre le
satellite et l'environnement spatial. Les températures des panneaux sont fortement couplées à l'éclairement
solaire :

| Condition            | Réaction du panneau                                  |
|----------------------|------------------------------------------------------|
| Éclairé (direct)     | Un panneau de structure monte à +30…+35 °C ; une aile à environ +55…+65 °C |
| Éclairé (oblique)    | Échauffement réduit ; lumière absorbée proportionnelle à cos(angle solaire) |
| Éclipse (à l'ombre)  | Les ailes se refroidissent jusqu'à environ -50 °C, jusqu'à ~2 °C/min ; les panneaux de structure suivent la structure |
| Albédo / IR terrestres | Échauffement continu de la face nadir (-Z) et des côtés qui voient la Terre |

Le mécanisme de couplage thermique agit dans les deux sens :

1. **Échauffement solaire** : le flux solaire direct chauffe le panneau éclairé, qui conduit la chaleur
   vers la structure du satellite et les composants adjacents.
2. **Refroidissement radiatif** : les panneaux à l'ombre rayonnent de la chaleur vers l'espace profond, en prélevant de la chaleur
   à l'intérieur du satellite.

Ce couplage compte pour la gestion thermique, car les températures des panneaux solaires
influent directement sur la température du compartiment de la batterie (adjacent aux panneaux +Y/-Y) et
sur celle du module OBC. Les opérateurs devraient surveiller les températures des panneaux pendant les manœuvres
d'attitude afin d'anticiper les transitoires thermiques.

## 9. Remarques d'exploitation {#9-operational-notes}

1. L'entrée en éclipse provoque une chute rapide de la température des panneaux exposés. Les ailes déployables,
   légères, se refroidissent le plus vite, jusqu'à ~2 °C/min.
2. L'activation du réchauffeur de batterie pendant l'éclipse est essentielle pour maintenir la température des éléments au-dessus de
   la limite minimale de qualification de 0 °C.
3. Le refroidisseur du FPA ne devrait pas être activé avant que l'électronique de la charge utile n'ait achevé
   son autotest de mise sous tension (environ 10 secondes après la commande STANDBY).
4. Les températures des panneaux (0x0400–0x0405) sont fournies à titre indicatif et ne déclenchent aucune action FDIR.
   Elles servent à la corrélation du modèle thermique pendant la recette en orbite et à la prédiction
   des températures des composants internes à partir de la répartition de l'éclairement solaire.
5. En mode SAFE, le refroidisseur du FPA est mis hors tension et l'AOCS pointe +X vers le Soleil. Les deux
   réchauffeurs restent sous thermostat ; l'OBC se maintient au chaud avec ses propres 3 W. Lors d'un délestage
   prolongé (seuls l'OBC et le récepteur alimentés, ~7,5 W), tout le satellite se refroidit de
   15–25 K et, en saison froide, l'OBC se dirige vers le seuil d'allumage de son réchauffeur à -10 °C : garder
   les lignes de réchauffeur 5 et 6 alimentées sous thermostat chaque fois que le bilan de puissance le permet.
6. L'orientation du satellite influe directement sur l'environnement thermique. Pendant les opérations de
   contingence, le directeur de vol devrait se coordonner avec les opérateurs Puissance/thermique et AOCS
   pour choisir une attitude qui concilie production de puissance et contraintes thermiques.

## 10. Marges de conception thermique {#10-thermal-design-margins}

La conception thermique assure une marge d'au moins 5 °C par rapport aux limites de qualification dans les cas
chaud et froid les plus défavorables (fin de vie, durée d'éclipse la plus défavorable, flux solaire maximal/minimal).
La vérification des marges s'appuie sur le modèle mathématique thermique corrélé pendant la
phase de recette en orbite.

---

*Fin du document — EOSAT1-UM-TCS-004*
