# Opérations orbitales d'EOSAT-1 {#eosat-1-orbit-operations}

**Référence du document :** EOSAT1-UM-ORB-008
**Édition :** 2.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Vue d'ensemble {#1-overview}

Le présent document décrit les caractéristiques orbitales d'EOSAT-1 et leurs conséquences
opérationnelles : cycles d'éclipse, géométrie des contacts avec les stations sol, planification des cibles
de prise de vue pour la surveillance des courants océaniques et programmation par passage.

## 2. Définition de l'orbite {#2-orbit-definition}

| Paramètre              | Valeur                       |
|------------------------|------------------------------|
| Type d'orbite          | Héliosynchrone (SSO)         |
| Demi-grand axe         | 6873,7 km                    |
| Altitude               | ~513 km géodésique moyenne (503–530 km) |
| Inclinaison            | 97,39°                       |
| Excentricité           | ~0 (quasi circulaire)        |
| LTAN                   | ~10:00 (nœud descendant ~22:00) |
| Période orbitale       | ~94,5 min                    |
| Révolutions par jour   | 15,24                        |
| Vitesse de régression nodale | ~0,9856°/jour (= 1°/jour) |
| Vitesse de la trace au sol | ~7,06 km/s               |

### 2.1 Propriétés héliosynchrones {#21-sun-synchronous-properties}

L'inclinaison de 97,39° provoque une précession du plan orbital vers l'est d'environ
0,9856°/jour, égale au mouvement moyen de la Terre autour du Soleil. C'est la valeur héliosynchrone
exacte pour le moyen mouvement du TLE, 15,24 tours par jour : la vitesse séculaire du nœud J2/J4 de SGP4
est égale à celle du Soleil à 97,39°, et le nœud dérive de moins de 0,1° (moins d'une demi-minute
de LTAN) sur les 2 ans de phase active. (L'ancienne valeur de 98,0° faisait précesser le
nœud d'environ 1,07°/jour et dériver le LTAN d'environ 2 h par an ; la valeur intermédiaire de 97,45°,
calculée à partir de l'altitude et non du moyen mouvement, le faisait dériver d'environ 0,4 h en 2 ans.)
Il en résulte que :

- l'heure solaire locale au nœud ascendant (LTAN) reste approximativement constante, à ~10:00 ;
- le passage ascendant éclairé franchit l'équateur en milieu de matinée : les cibles océaniques sont donc
  observées dans des conditions d'éclairement homogènes d'une revisite à l'autre, ce qui est essentiel pour
  les mesures de couleur de l'océan ;
- l'orbite n'est pas aube-crépuscule : le satellite subit une éclipse à chaque orbite (§3).

### 2.2 Trace au sol {#22-ground-track}

La trace au sol se répète environ tous les 5 jours. Le point subsatellite décrit une
sinusoïde entre les latitudes +/- 82,6° (supplément de l'inclinaison, 180 − 97,39). À l'équateur, deux traces
au sol successives sont distantes d'environ 2 630 km ; la maille de répétition à 5 jours est d'environ 525 km. À l'altitude moyenne d'environ 513 km,
l'imageur offre une distance d'échantillonnage au sol (GSD) d'environ 33 m et une fauchée d'environ 273 km
(toutes deux proportionnelles à l'altitude), bien adaptées à la détection des structures océaniques.

## 3. Cycle d'éclipse {#3-eclipse-cycle}

### 3.1 Géométrie des éclipses {#31-eclipse-geometry}

À l'altitude moyenne d'environ 513 km, le cône d'ombre de la Terre produit des éclipses lorsque le satellite traverse
la région antisolaire. Pour l'orbite au LTAN d'environ 10:00 :

| Paramètre              | Valeur                       |
|------------------------|------------------------------|
| Durée d'éclipse max.   | ~35,2 min (bêta d'environ −21°) |
| Durée d'éclipse min.   | ~33,2 min (bêta d'environ −31°) |
| Saison d'éclipses      | À chaque orbite, toute l'année |
| Fraction d'orbite (max.) | ~37 % de la période orbitale |

### 3.2 Variation saisonnière {#32-seasonal-variation}

Avec un LTAN maintenu à ~10:00, l'angle bêta reste entre −20,8° et −31,2° pendant la
première année (propagation SGP4 du TLE de `orbit.yaml`, `tools/power_budget.py`). EOSAT-1 subit donc
une éclipse à chaque orbite, pendant 33,2 à 35,2 min (fraction d'éclipse 0,351–0,372). Le tableau donne la durée d'éclipse en fonction de bêta à ~513 km (ombre
cylindrique, période de 94,5 min) ; les lignes au-delà de |bêta| ~ 31° ne concernent que des orbites hors nominal :

| Plage d'angle bêta | Durée d'éclipse | Remarques                    |
|------------------|------------------|------------------------------|
| |bêta| > 68°     | 0 min            | Plein soleil (pas d'éclipse) |
| |bêta| ~ 60°     | ~21 min          | Éclipse courte               |
| |bêta| ~ 30°     | ~34 min          | Plage d'EOSAT-1 (21–31°)     |
| |bêta| < 20°     | ~35–36 min       | Durée d'éclipse maximale     |

### 3.3 Conséquences opérationnelles des éclipses {#33-eclipse-operational-impact}

Pendant l'éclipse :

1. **EPS** : la production du générateur solaire tombe à zéro. La batterie fournit toute la puissance du satellite.
   La profondeur de décharge dépend de la durée de l'éclipse et de la consommation.
2. **TCS** : refroidissement rapide des surfaces exposées. Les réchauffeurs de la batterie et de l'OBC peuvent s'activer.
3. **AOCS** : le senseur stellaire peut être ébloui par la Terre ou le Soleil lors des transitions d'éclipse.
   La propagation sur les seuls gyromètres est utilisée pendant 60 secondes au plus.
4. **Charge utile** : la prise de vue produit des images d'obscurité (utiles pour l'étalonnage du détecteur).

## 4. Géométrie des contacts avec les stations sol {#4-ground-station-contact-geometry}

### 4.1 Emplacement des stations {#41-station-locations}

| Station    | Latitude   | Longitude  | Élév. min. | Contacts par jour (approx.) |
|------------|------------|------------|-----------|----------------------|
| Iqaluit    | 63,747 N   | 68,518 O   | 5°        | ~9                   |
| Troll      | 72,012 S   | 2,535 E    | 5°        | ~11                  |
| Svalbard   | 78,230 N   | 15,398 E   | 5°        | ~13                  |
| Inuvik     | 68,320 N   | 133,550 O  | 5°        | ~10,5                |
| O'Higgins  | 63,321 S   | 57,901 O   | 5°        | ~8                   |

Le réseau de cinq stations (liste de référence dans `orbit.yaml`) assure une couverture bipolaire :

- **Svalbard** (KSAT SvalSat, Norvège) : la station de plus haute latitude, avec le plus de passages et
  les élévations les plus hautes ; première priorité de transmission au sol du planificateur.
- **Inuvik** (Territoires du Nord-Ouest, Canada) et **Iqaluit** (Nunavut, Canada) : passages dans l'hémisphère
  Nord, aux longitudes ouest et est de l'Arctique canadien.
- **Troll** (Terre de la Reine-Maud, Antarctique) et **O'Higgins** (péninsule Antarctique) : passages dans l'hémisphère
  Sud. Avec sa latitude de 72° S, Troll offre le plus de contacts au sud.

Les cinq stations ont le même rôle, TT&C en bande S et vidage des données (manuel 05 §5).

### 4.2 Profil de passage type {#42-typical-pass-profile}

Un contact type avec une station sol suit le profil d'élévation suivant :

```
Élévation
(deg)
  80 |          ___
  60 |        /     \
  40 |      /         \
  20 |    /             \
   5 |--/                 \--
   0 +-------------------------> Temps
     AOS     TCA         LOS
```

| Phase | Abréviation  | Description                              |
|-------|--------------|------------------------------------------|
| AOS   | Acquisition  | Signal acquis à l'élévation minimale     |
| TCA   | Rapprochement maximal | Élévation maximale (distance oblique la plus courte) |
| LOS   | Perte        | Signal perdu sous l'élévation minimale   |

### 4.3 Durée de contact en fonction de l'élévation maximale {#43-contact-duration-vs-maximum-elevation}

| Élévation max. | Durée approx.    | Qualité de la liaison |
|---------------|-------------------|------------------|
| 5–10°         | jusqu'à ~6 min    | Marginale        |
| 10–30°        | ~6–9 min          | Acceptable       |
| 30–60°        | ~9 min            | Bonne            |
| 60–90°        | ~9,5 min          | Excellente       |

Ces durées valent pour l'orbite d'environ 513 km et le masque de 5° (géométrie sphérique, rotation de la Terre
négligée). Sur 48 h, le contact moyen dure 6,7 min à Iqaluit, 7,4 min à Inuvik, 7,5 min à
O'Higgins et 7,8 min à Svalbard et à Troll.

Les passages à élévation maximale plus élevée offrent des contacts plus longs et de meilleures marges de liaison.
La ligne des 10° n'est pas ici une règle empirique — c'est la condition stricte du palier HIGH. Un passage
dont l'élévation maximale est inférieure à 10° ne peut jamais utiliser le palier de vidage à 128 kbit/s : il est donc
utilisable pour la commande et pour les données de servitude de routine au palier LOW (16 kbit/s), mais ne transporte aucune
image. Au-delà de 10°, seul l'arc situé au-dessus de 10° permet le palier HIGH : un passage à 30° passe environ
77 % de sa fenêtre au-dessus de ce seuil, un passage à 12° seulement 47 %. Le planificateur de mission calcule
cette fraction à partir de la géométrie du passage et réserve les vidages en conséquence, de sorte qu'un plan ne peut pas
supposer en silence un débit constant.

### 4.4 Visibilité et programmation {#44-visibility-and-scheduling}

Le réseau de stations bipolaire offre une couverture complémentaire. Ensemble, les cinq stations
assurent :

- **Nombre total de contacts par jour** : ~51 ;
- **Temps de contact cumulé** : ~385 min/jour ;
- **Intervalle entre contacts** : ~33 min (médiane), ~79 min (pire cas).

(48 h à partir de l'époque du TLE, `tools/pass_gap_analysis.py`.) Avec Iqaluit et Troll seules, on
compterait environ 20 contacts par jour et un pire intervalle d'environ 2,5 heures.

La frise chronologique des fenêtres de visibilité du MCS affiche une barre horizontale de 24 heures avec les passages
de chaque station, annotés des heures d'AOS/LOS et de l'élévation maximale.

## 5. Restitution d'orbite {#5-orbit-determination}

La restitution d'orbite s'appuie sur :

- **le GPS de bord** : le récepteur GPS monté au zénith fournit en continu des mesures de position et de vitesse
  (latitude et longitude du point subsatellite, altitude). C'est la source principale de restitution
  d'orbite ;
- **les données de mesure de distance** : distances obliques mesurées fournies par le transpondeur bande S pendant les contacts,
  utilisées pour une vérification indépendante ;
- **les éléments à deux lignes (TLE)** : publiés par les réseaux de surveillance de l'espace, utilisés en secours.

Les paramètres de télémesure `range_km` (0x0509) et `contact_elevation` (0x050A) fournissent
en temps réel la distance et l'élévation pendant les contacts sol. La position issue du GPS est
disponible dans `sc_lat` (0x0210), `sc_lon` (0x0211) et `sc_alt` (0x0212).

L'OBC exécute le logiciel SCAO pour la restitution d'orbite. Le contrôle d'orbite se limite
aux poussées du module de propulsion, planifiées au sol (voir §6).

## 6. Maintien de l'orbite {#6-orbit-maintenance}

EOSAT-1 embarque un module de propulsion 1U à monergol vert en mode blowdown (0,400 kg de LMP-103S, delta-V total d'environ 67 m/s ;
S8 fonctions 108–118) pour les manœuvres d'évitement de débris, une compensation limitée de la traînée et la poussée
de retrait de service en fin de vie (décision Q3 modifiée, 2026-10-30).

**Caractéristiques du déclin orbital :**

| Paramètre             | Valeur                       |
|-----------------------|------------------------------|
| Surface de traînée    | ~0,07 m² (C_D = 2,2)         |
| Coefficient balistique | 77,9 kg/m² (`subsystems/prop.yaml`) |
| Décroissance naturelle | ~5 ans (activité solaire moyenne), ~14 ans (minimum solaire) depuis 513 km (`subsystems/prop.yaml`) |
| Élimination           | Poussée d'abaissement du périgée à 390 km, 34,3 m/s en six poussées rétrogrades (NOM-014) ; rentrée en ~1,5 an (moyenne) et ~4,2 ans (minimum solaire), dans la règle des 5 ans |

Le déclin d'orbite naturel seul ne respecte pas la règle des 5 ans au minimum solaire. Ces valeurs proviennent
de l'intégration de la décroissance due à la traînée avec l'atmosphère exponentielle CIRA-72 (activité moyenne) et
0,35 fois celle-ci (minimum solaire), la méthode et le facteur d'échelle du dimensionnement initial de la propulsion ;
l'ancien « 1,7–4,8 ans » avait été calculé à l'altitude abandonnée de 450 km. La poussée de retrait de service fait partie
du bilan de delta-V (64,1 m/s nécessaires pour 66,9 m/s disponibles) : au moins 38 m/s doivent donc rester
en réserve pour elle.

**Conséquences opérationnelles :**

1. **Capacité de correction d'orbite limitée :** un propulseur unique permet de compenser la traînée et d'effectuer la
   poussée de retrait de service dans la limite du budget de delta-V (`subsystems/prop.yaml`). Les changements de plan sont hors périmètre.
2. **Surveillance de l'altitude :** le suivi continu de l'altitude par GPS est indispensable pour :
   - planifier la poussée de retrait de service en fin de vie et prévoir la rentrée ;
   - prédire avec précision la trace au sol (essentiel pour la planification des cibles de prise de vue) ;
   - détecter au plus tôt un déclin anormal (signe possible d'une perturbation atmosphérique).
3. **Planification de mission :** toute la programmation de la charge utile, la disponibilité des fenêtres de prise de vue et la géométrie
   des fenêtres de visibilité reposent sur l'orbite naturelle en déclin progressif. Le planificateur utilise l'état
   orbital courant pour prédire la disponibilité des passages futurs.

**Télémesure de surveillance de l'orbite :**
- `sc_alt` (0x0212) : altitude orbitale issue du GPS (km) ;
- `sc_lat` (0x0210) : latitude du point subsatellite (°) ;
- `sc_lon` (0x0211) : longitude du point subsatellite (°).

## 7. Planification des cibles de prise de vue pour les courants océaniques {#7-imaging-target-planning-for-ocean-currents}

### 7.1 Régions océaniques cibles {#71-target-ocean-regions}

La prise de vue d'EOSAT-1 est planifiée autour des régions de surveillance des courants océaniques :

| Région                      | Plage de latitudes | Structure ciblée               |
|-----------------------------|------------------|----------------------------------|
| Gulf Stream (bord ouest)    | 25–45 N          | Méandres du courant, tourbillons |
| Courant du Kuroshio         | 25–40 N          | Courant de bord ouest du Pacifique |
| Courant circumpolaire antarctique | 45–65 S    | Zones frontales, remontées d'eau froide |
| Courant de Benguela         | 15–35 S          | Remontées d'eau froide de bord est |
| Dérive nord-atlantique      | 45–60 N          | Circulation du gyre subpolaire   |

### 7.2 Calcul des opportunités de prise de vue {#72-imaging-opportunity-computation}

Les opportunités de prise de vue sont calculées par le planificateur de mission en fonction :

1. **de la géométrie orbitale** : point subsatellite à l'intérieur de la région cible ;
2. **de l'éclairement solaire** : la cible doit être éclairée (élévation solaire > 10 deg sur la cible) ;
3. **des contraintes satellite** : SoC de la batterie > 40 %, AOCS en NOMINAL (4), att_error < 0.5 deg ;
4. **du bilan de données** : mémoire de masse et capacité de transmission au sol suffisantes pour le volume de données de l'image ;
5. **du calendrier des contacts** : passage de transmission au sol disponible dans un délai raisonnable après l'acquisition.

## 8. Programmation par passage {#8-pass-based-scheduling}

Le planificateur de mission utilise une approche de programmation par passage, dans laquelle les activités sont affectées
à des passages orbitaux individuels :

### 8.1 Types de passages {#81-pass-types}

| Type de passage | Activités                                             |
|---------------|---------------------------------------------------------|
| Passage de prise de vue | Activation de la charge utile, acquisition d'image, retour en veille |
| Passage de transmission | Vidage des données scientifiques, relecture de la TM enregistrée (l'une des cinq stations) |
| Passage combiné | Prise de vue suivie d'une transmission au sol (si la fenêtre de visibilité le permet) |
| Passage inactif | Données de servitude uniquement, charge de la batterie |

### 8.2 Contraintes de programmation {#82-scheduling-constraints}

L'ordonnanceur doit satisfaire les contraintes suivantes :

| Contrainte          | Règle                                                  |
|---------------------|--------------------------------------------------------|
| Bilan de puissance  | Le SoC doit rester > 25 % en permanence (prédiction par orbite) |
| Volume de données   | La mémoire de masse ne doit pas dépasser 90 % de sa capacité |
| Thermique           | Rapport cyclique de la charge utile limité à 10 min par fenêtre de prise de vue |
| Conflits de contact | Aucune prise de vue pendant un passage de transmission en cours |
| Intervalle minimal  | Au moins 5 min entre la fin de la prise de vue et le début de la transmission |

### 8.3 Suivi des bilans de puissance et de données {#83-power-and-data-budget-tracking}

Le planificateur suit deux bilans sur l'horizon de planification :

- **Bilan de puissance** : trajectoire prévue du SoC de la batterie, fondée sur le modèle de production solaire,
  les heures d'éclipse et le profil de charge prévu. Le planificateur ne programme pas de prise de vue si
  le SoC prévu descend sous 40 % à un moment quelconque.
- **Bilan de données** : volume de données cumulé issu des prises de vue, comparé à la capacité de transmission au sol.
  Les taux de compression adaptés à la scène sont estimés selon le type de cible (océan,
  côte, terre). La capacité de transmission au sol est calculée à partir de la durée des contacts et du mode de débit.

## 9. Télémesure utile {#9-relevant-telemetry}

| ID param. | Nom              | Unité | Description                          |
|----------|-------------------|------|--------------------------------------|
| 0x0210   | sc_lat            | deg  | Latitude du point subsatellite (GPS) |
| 0x0211   | sc_lon            | deg  | Longitude du point subsatellite (GPS) |
| 0x0212   | sc_alt            | km   | Altitude orbitale (GPS)              |
| 0x0509   | range_km          | km   | Distance oblique jusqu'à la station sol |
| 0x050A   | contact_elevation | deg  | Élévation de la station sol          |
| 0x0108   | eclipse_flag      | booléen | État d'éclipse                    |

---

*Fin du document — EOSAT1-UM-ORB-008*
