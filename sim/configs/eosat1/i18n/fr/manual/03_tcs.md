# Sous-système de contrôle thermique (TCS) d'EOSAT-1

**Référence du document :** EOSAT1-UM-TCS-004
**Édition :** 2.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Vue d'ensemble

Le sous-système de contrôle thermique (TCS) maintient tous les composants du satellite dans leurs
plages de température admissibles pendant toute la mission. EOSAT-1 recourt principalement à un contrôle thermique
passif (MLI, radiateurs, revêtements de surface), complété par des réchauffeurs de batterie qui constituent le seul élément
actif de contrôle thermique. L'OBC et les autres composants s'appuient sur une gestion thermique passive,
assurée par l'orientation du satellite et la dissipation thermique interne. Le refroidisseur du plan focal (FPA)
est géré dans le cadre du sous-système charge utile.

## 2. Contrôle thermique passif

### 2.1 Isolant multicouche (MLI)

Des couvertures MLI recouvrent la majeure partie des surfaces externes du satellite et assurent l'isolation
thermique vis-à-vis de l'environnement spatial. Les principales zones couvertes sont :

- les panneaux latéraux du satellite (faces +/-X, +/-Y) ;
- le compartiment de la batterie ;
- le boîtier du module OBC ;
- la baie électronique de la charge utile.

### 2.2 Radiateurs

Des panneaux radiateurs dédiés sont montés sur les faces -Y et +Y pour évacuer la chaleur dissipée.
Le dimensionnement des radiateurs est optimisé pour une puissance dissipée nominale d'environ 29 W (moyenne sur l'orbite, voir 01_eps.md).

| Radiateur       | Emplacement | Surface | Capacité de rejet |
|-----------------|----------|----------|-----------------|
| Principal (-Y)  | Face -Y  | 0,25 m²  | ~50 W           |
| Secondaire (+Y) | Face +Y  | 0,15 m²  | ~30 W           |

### 2.3 Revêtements de surface

Les surfaces externes associent une peinture blanche (à forte émissivité) sur les radiateurs et du
Kapton noir sur les surfaces de structure internes, afin de favoriser le transfert de chaleur par rayonnement à l'intérieur
de la cavité du satellite.

## 3. Contrôle thermique actif

### 3.1 Circuit de réchauffeur de batterie

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
(`HEATER_OBC`, S8 fonction 41 ; état `htr_obc` 0x040B ; 4 W sur la ligne PDM 6 ; thermostat ON +5 °C /
OFF +10 °C) est une sécurité pour le cas froid : la dissipation interne, la MLI et le dimensionnement des radiateurs maintiennent
normalement l'OBC dans sa plage qualifiée. Le réchauffeur du lit catalytique du propulseur (`HEATER_THRUSTER`, S8 fonction 42 ;
état 0x041B ; 12 W sur la ligne `prop`) préchauffe le propulseur avant une manœuvre.

### 3.2 Orientation au service du contrôle thermique passif

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

### 3.3 Modes de défaillance des réchauffeurs

| Mode de défaillance | Détection                       | Impact                          |
|-----------------|-------------------------------------|---------------------------------|
| Réchauffeur stuck_on | Température de la batterie qui monte au-delà du seuil ; `htr_battery` reste à 1 | Consommation excessive, surchauffe possible de la batterie |
| Réchauffeur open_circuit | Température de la batterie qui descend sous le seuil ; `htr_battery` = 1 mais aucune réaction de la température | Risque de gel de la batterie en éclipse |

Si un réchauffeur bloqué en marche est détecté, le sol devrait commander `HEATER_CONTROL` (circuit=battery,
on=false) et surveiller. Si le réchauffeur reste allumé, la sortie PDM qui alimente le circuit du réchauffeur
peut être mise hors tension par commande, à titre de mesure d'isolation.

### 3.4 Refroidisseur du FPA

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

## 4. Zones de température

| Zone           | Plage nominale   | Limites jaunes   | Limites rouges   |
|----------------|------------------|------------------|------------------|
| Batterie       | 5–35 °C          | 2–40 °C          | 0–45 °C          |
| OBC            | 15–50 °C         | 5–60 °C          | 0–70 °C          |
| Détecteur FPA  | -18 à -12 °C     | -22 à 14 °C      | -25,5 à 17,5 °C  |
| Panneaux solaires | -80 à 80 °C   | —                | —                |
| Structure      | -20 à 50 °C      | —                | —                |

## 5. Paramètres de télémesure

| ID param. | Nom            | Unité  | Description                          |
|----------|-----------------|--------|--------------------------------------|
| 0x0400   | temp_panel_px   | °C     | Température du panneau +X            |
| 0x0401   | temp_panel_mx   | °C     | Température du panneau -X            |
| 0x0402   | temp_panel_py   | °C     | Température du panneau +Y            |
| 0x0403   | temp_panel_my   | °C     | Température du panneau -Y            |
| 0x0404   | temp_panel_pz   | °C     | Température du panneau +Z (nadir)    |
| 0x0405   | temp_panel_mz   | °C     | Température du panneau -Z (zénith)   |
| 0x0406   | temp_obc        | °C     | Température du module OBC            |
| 0x0407   | temp_battery    | °C     | Température du bloc batterie         |
| 0x0408   | temp_fpa        | °C     | Température du plan focal            |
| 0x0409   | temp_thruster   | °C     | Température de la vanne du propulseur |
| 0x040A   | htr_battery     | booléen | État du réchauffeur de batterie (marche/arrêt) |
| 0x040B   | htr_obc         | booléen | État du réchauffeur de l'OBC (marche/arrêt) |
| 0x040C   | cooler_fpa      | booléen | État du refroidisseur du FPA (marche/arrêt) |

## 6. Définition des limites

| Paramètre       | Jaune bas  | Jaune haut  | Rouge bas | Rouge haut |
|-----------------|------------|-------------|---------|----------|
| temp_obc (°C)   | 5          | 60          | 0       | 70       |
| temp_battery (°C)| 2         | 40          | 0       | 45       |
| temp_fpa (°C)   | -22.0      | 14.0        | -25.5   | 17.5     |

Ces bandes sont **dérivées**, et non choisies : `subsystems/tcs.yaml: fpa_envelope`
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

## 7. Commandes

| Commande          | Service  | Paramètres              | Description                        |
|-------------------|----------|-------------------------|------------------------------------|
| HEATER_CONTROL    | S8,S1    | circuit, on             | Activer/désactiver un circuit de réchauffeur |
| HK_REQUEST        | S3,S27   | sid=4                   | Demander le paquet de servitude TCS |
| GET_PARAM         | S20,S3   | param_id (0x0400–040C)  | Lire un paramètre TCS individuel   |
| SET_PARAM         | S20,S1   | param_id, value         | Modifier un paramètre de configuration TCS |

## 8. Couplage entre la température des panneaux et l'éclairement solaire

Les cinq panneaux solaires fixés sur la structure (toutes les faces sauf -Z) constituent l'interface thermique principale entre le
satellite et l'environnement spatial. Les températures des panneaux sont fortement couplées à l'éclairement
solaire :

| Condition            | Réaction du panneau                                  |
|----------------------|------------------------------------------------------|
| Éclairé (direct)     | La température du panneau monte vers +80 °C (régime établi) |
| Éclairé (oblique)    | Échauffement réduit ; température proportionnelle à cos(angle solaire) |
| Éclipse (à l'ombre)  | Refroidissement rapide vers -80 °C à ~5 °C/min       |
| Albédo terrestre seul | Léger échauffement de la face nadir (+Z)            |

Le mécanisme de couplage thermique agit dans les deux sens :

1. **Échauffement solaire** : le flux solaire direct chauffe le panneau éclairé, qui conduit la chaleur
   vers la structure du satellite et les composants adjacents.
2. **Refroidissement radiatif** : les panneaux à l'ombre rayonnent de la chaleur vers l'espace profond, en prélevant de la chaleur
   à l'intérieur du satellite.

Ce couplage compte pour la gestion thermique, car les températures des panneaux solaires
influent directement sur la température du compartiment de la batterie (adjacent aux panneaux +Y/-Y) et
sur celle du module OBC. Les opérateurs devraient surveiller les températures des panneaux pendant les manœuvres
d'attitude afin d'anticiper les transitoires thermiques.

## 9. Remarques d'exploitation

1. L'entrée en éclipse provoque une chute rapide de la température des panneaux exposés. Le gradient thermique
   peut atteindre 5 °C/min sur les surfaces directement exposées.
2. L'activation du réchauffeur de batterie pendant l'éclipse est essentielle pour maintenir la température des éléments au-dessus de
   la limite minimale de qualification de 0 °C.
3. Le refroidisseur du FPA ne devrait pas être activé avant que l'électronique de la charge utile n'ait achevé
   son autotest de mise sous tension (environ 10 secondes après la commande STANDBY).
4. Les températures des panneaux (0x0400–0x0405) sont fournies à titre indicatif et ne déclenchent aucune action FDIR.
   Elles servent à la corrélation du modèle thermique pendant la recette en orbite et à la prédiction
   des températures des composants internes à partir de la répartition de l'éclairement solaire.
5. En mode SAFE, seul le réchauffeur de batterie reste actif. Le refroidisseur du FPA est mis hors tension
   pour économiser l'énergie. L'OBC s'appuie sur le contrôle thermique passif (autoéchauffement par
   dissipation de puissance interne).
6. L'orientation du satellite influe directement sur l'environnement thermique. Pendant les opérations de
   contingence, le directeur de vol devrait se coordonner avec les opérateurs Puissance/thermique et AOCS
   pour choisir une attitude qui concilie production de puissance et contraintes thermiques.

## 10. Marges de conception thermique

La conception thermique assure une marge d'au moins 5 °C par rapport aux limites de qualification dans les cas
chaud et froid les plus défavorables (fin de vie, durée d'éclipse la plus défavorable, flux solaire maximal/minimal).
La vérification des marges s'appuie sur le modèle mathématique thermique corrélé pendant la
phase de recette en orbite.

---

*Fin du document — EOSAT1-UM-TCS-004*
