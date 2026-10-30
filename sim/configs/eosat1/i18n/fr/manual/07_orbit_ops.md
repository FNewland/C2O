# Opérations orbitales d'EOSAT-1

**Référence du document :** EOSAT1-UM-ORB-008
**Édition :** 2.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Vue d'ensemble

Le présent document décrit les caractéristiques orbitales d'EOSAT-1 et leurs conséquences
opérationnelles : cycles d'éclipse, géométrie des contacts avec les stations sol, planification des cibles
de prise de vue pour la surveillance des courants océaniques et programmation par passage.

## 2. Définition de l'orbite

| Paramètre              | Valeur                       |
|------------------------|------------------------------|
| Type d'orbite          | Héliosynchrone (SSO)         |
| Demi-grand axe         | 6873,7 km                    |
| Altitude               | ~513 km géodésique moyenne (503–530 km) |
| Inclinaison            | 98°                          |
| Excentricité           | ~0 (quasi circulaire)        |
| LTAN                   | 06:00 / 18:00 (aube-crépuscule) |
| Période orbitale       | ~94,5 min                    |
| Révolutions par jour   | 15,24                        |
| Vitesse de régression nodale | ~0,9856°/jour (= 1°/jour) |
| Vitesse de la trace au sol | ~7,07 km/s               |

### 2.1 Propriétés héliosynchrones

L'inclinaison de 98° provoque une précession du plan orbital vers l'est d'environ
0,9856°/jour, égale au mouvement moyen de la Terre autour du Soleil. Il en résulte que :

- l'heure solaire locale au nœud ascendant (LTAN) reste approximativement constante ;
- la configuration aube-crépuscule maximise l'éclairement solaire des panneaux fixés sur la structure ;
- les cibles océaniques sont observées dans des conditions d'éclairement homogènes d'une revisite à l'autre,
  ce qui est essentiel pour les mesures de couleur de l'océan.

### 2.2 Trace au sol

La trace au sol se répète environ tous les 5 jours. Le point subsatellite décrit une
sinusoïde entre les latitudes +/- 82° (complément de l'inclinaison). À l'équateur, deux traces
au sol successives sont distantes d'environ 2 630 km ; la maille de répétition à 5 jours est d'environ 525 km. À l'altitude moyenne d'environ 513 km,
l'imageur offre une distance d'échantillonnage au sol (GSD) d'environ 33 m et une fauchée d'environ 273 km
(toutes deux proportionnelles à l'altitude), bien adaptées à la détection des structures océaniques.

## 3. Cycle d'éclipse

### 3.1 Géométrie des éclipses

À l'altitude moyenne d'environ 513 km, le cône d'ombre de la Terre produit des éclipses lorsque le satellite traverse
la région antisolaire. Pour l'orbite SSO aube-crépuscule :

| Paramètre              | Valeur                       |
|------------------------|------------------------------|
| Durée d'éclipse max.   | ~36 min                      |
| Durée d'éclipse min.   | ~0 min (près de l'équinoxe)  |
| Saison d'éclipses      | Variation saisonnière        |
| Fraction d'orbite (max.) | ~38 % de la période orbitale |

### 3.2 Variation saisonnière

L'orbite aube-crépuscule minimise la durée des éclipses par rapport aux autres configurations SSO.
Des éclipses se produisent néanmoins du fait de la variation de l'angle bêta :

| Plage d'angle bêta | Durée d'éclipse | Remarques                    |
|------------------|------------------|------------------------------|
| |bêta| > 70°     | 0 min            | Plein soleil (pas d'éclipse) |
| |bêta| ~ 60°     | ~15 min          | Éclipse courte               |
| |bêta| ~ 30°     | ~30 min          | Éclipse moyenne              |
| |bêta| < 25°     | ~36 min          | Durée d'éclipse maximale     |

### 3.3 Conséquences opérationnelles des éclipses

Pendant l'éclipse :

1. **EPS** : la production du générateur solaire tombe à zéro. La batterie fournit toute la puissance du satellite.
   La profondeur de décharge dépend de la durée de l'éclipse et de la consommation.
2. **TCS** : refroidissement rapide des surfaces exposées. Les réchauffeurs de la batterie et de l'OBC peuvent s'activer.
3. **AOCS** : le senseur stellaire peut être ébloui par la Terre ou le Soleil lors des transitions d'éclipse.
   La propagation sur les seuls gyromètres est utilisée pendant 60 secondes au plus.
4. **Charge utile** : la prise de vue produit des images d'obscurité (utiles pour l'étalonnage du détecteur).

## 4. Géométrie des contacts avec les stations sol

### 4.1 Emplacement des stations

| Station    | Latitude   | Longitude  | Élév. min. | Contacts par jour (approx.) |
|------------|------------|------------|-----------|----------------------|
| Iqaluit    | 63,747 N   | 68,518 O   | 5°        | 2–4                  |
| Troll      | 72,012 S   | 2,535 E    | 5°        | 2–4                  |

Le réseau de deux stations assure une couverture bipolaire :

- **Iqaluit** (Nunavut, Canada) : couvre les passages dans l'hémisphère Nord. Elle bénéficie des fréquents
  survols des hautes latitudes par la trace au sol de l'orbite polaire.
- **Troll** (Terre de la Reine-Maud, Antarctique) : couvre les passages dans l'hémisphère Sud. Sa latitude de 72° S
  offre une excellente couverture du nœud descendant de l'orbite.

### 4.2 Profil de passage type

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

### 4.3 Durée de contact en fonction de l'élévation maximale

| Élévation max. | Durée approx.    | Qualité de la liaison |
|---------------|-------------------|------------------|
| 5–10°         | 3–5 min           | Marginale        |
| 10–30°        | 5–8 min           | Acceptable       |
| 30–60°        | 8–10 min          | Bonne            |
| 60–90°        | 10–12 min         | Excellente       |

Les passages à élévation maximale plus élevée offrent des contacts plus longs et de meilleures marges de liaison.
La ligne des 10° n'est pas ici une règle empirique — c'est la condition stricte du palier HIGH. Un passage
dont l'élévation maximale est inférieure à 10° ne peut jamais utiliser le palier de vidage à 128 kbit/s : il est donc
utilisable pour la commande et pour les données de servitude de routine au palier LOW (16 kbit/s), mais ne transporte aucune
image. Au-delà de 10°, seul l'arc situé au-dessus de 10° permet le palier HIGH : un passage à 30° passe environ
76 % de sa fenêtre au-dessus de ce seuil, un passage à 12° seulement 47 %. Le planificateur de mission calcule
cette fraction à partir de la géométrie du passage et réserve les vidages en conséquence, de sorte qu'un plan ne peut pas
supposer en silence un débit constant.

### 4.4 Visibilité et programmation

Le réseau de stations bipolaire offre une couverture complémentaire. Ensemble, les deux stations
assurent :

- **Nombre total de contacts par jour** : 4–8 ;
- **Temps de contact cumulé** : 30–60 min/jour ;
- **Intervalle maximal entre contacts** : ~4 heures (cas type), ~6 heures (pire cas).

La frise chronologique des fenêtres de visibilité du MCS affiche une barre horizontale de 24 heures montrant les passages
au-dessus d'Iqaluit (en bleu) et de Troll (en vert), annotés des heures d'AOS/LOS et de l'élévation maximale.

## 5. Restitution d'orbite

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

## 6. Maintien de l'orbite

EOSAT-1 embarque un module de propulsion 1U à monergol vert en mode blowdown (0,400 kg de LMP-103S, delta-V total d'environ 67 m/s ;
S8 fonctions 108–118) pour les manœuvres d'évitement de débris et une compensation limitée de la traînée. Ce n'est pas un système de désorbitation.

**Caractéristiques du déclin orbital :**

| Paramètre             | Valeur                       |
|-----------------------|------------------------------|
| Surface de traînée    | ~0,06 m² (6U, face 1U)       |
| Coefficient balistique | ~200 kg/m²                  |
| Vitesse de déclin attendue | 2–5 km/an               |
| Durée de vie de la mission | >7 ans (estimation à 450 km ; le déclin depuis l'altitude réelle d'environ 513 km est plus lent — nouvelle estimation en attente) |

**Conséquences opérationnelles :**

1. **Capacité de correction d'orbite limitée :** un propulseur unique permet de compenser la traînée dans la limite du
   budget de delta-V (`subsystems/prop.yaml`). Les changements de plan et la désorbitation propulsive sont hors périmètre.
2. **Surveillance de l'altitude :** le suivi continu de l'altitude par GPS est indispensable pour :
   - prévoir la fin de vie de la mission et la fenêtre de rentrée ;
   - prédire avec précision la trace au sol (essentiel pour la planification des cibles de prise de vue) ;
   - détecter au plus tôt un déclin anormal (signe possible d'une perturbation atmosphérique).
3. **Planification de mission :** toute la programmation de la charge utile, la disponibilité des fenêtres de prise de vue et la géométrie
   des fenêtres de visibilité reposent sur l'orbite naturelle en déclin progressif. Le planificateur utilise l'état
   orbital courant pour prédire la disponibilité des passages futurs.

**Télémesure de surveillance de l'orbite :**
- `sc_alt` (0x0212) : altitude orbitale issue du GPS (km) ;
- `sc_lat` (0x0210) : latitude du point subsatellite (°) ;
- `sc_lon` (0x0211) : longitude du point subsatellite (°).

## 7. Planification des cibles de prise de vue pour les courants océaniques

### 7.1 Régions océaniques cibles

La prise de vue d'EOSAT-1 est planifiée autour des régions de surveillance des courants océaniques :

| Région                      | Plage de latitudes | Structure ciblée               |
|-----------------------------|------------------|----------------------------------|
| Gulf Stream (bord ouest)    | 25–45 N          | Méandres du courant, tourbillons |
| Courant du Kuroshio         | 25–40 N          | Courant de bord ouest du Pacifique |
| Courant circumpolaire antarctique | 45–65 S    | Zones frontales, remontées d'eau froide |
| Courant de Benguela         | 15–35 S          | Remontées d'eau froide de bord est |
| Dérive nord-atlantique      | 45–60 N          | Circulation du gyre subpolaire   |

### 7.2 Calcul des opportunités de prise de vue

Les opportunités de prise de vue sont calculées par le planificateur de mission en fonction :

1. **de la géométrie orbitale** : point subsatellite à l'intérieur de la région cible ;
2. **de l'éclairement solaire** : la cible doit être éclairée (élévation solaire > 10 deg sur la cible) ;
3. **des contraintes satellite** : SoC de la batterie > 40 %, AOCS en NOMINAL (4), att_error < 0.5 deg ;
4. **du bilan de données** : mémoire de masse et capacité de transmission au sol suffisantes pour le volume de données de l'image ;
5. **du calendrier des contacts** : passage de transmission au sol disponible dans un délai raisonnable après l'acquisition.

## 8. Programmation par passage

Le planificateur de mission utilise une approche de programmation par passage, dans laquelle les activités sont affectées
à des passages orbitaux individuels :

### 8.1 Types de passages

| Type de passage | Activités                                             |
|---------------|---------------------------------------------------------|
| Passage de prise de vue | Activation de la charge utile, acquisition d'image, retour en veille |
| Passage de transmission | Vidage des données scientifiques, relecture de la TM enregistrée (Iqaluit ou Troll) |
| Passage combiné | Prise de vue suivie d'une transmission au sol (si la fenêtre de visibilité le permet) |
| Passage inactif | Données de servitude uniquement, charge de la batterie |

### 8.2 Contraintes de programmation

L'ordonnanceur doit satisfaire les contraintes suivantes :

| Contrainte          | Règle                                                  |
|---------------------|--------------------------------------------------------|
| Bilan de puissance  | Le SoC doit rester > 25 % en permanence (prédiction par orbite) |
| Volume de données   | La mémoire de masse ne doit pas dépasser 90 % de sa capacité |
| Thermique           | Rapport cyclique de la charge utile limité à 10 min par fenêtre de prise de vue |
| Conflits de contact | Aucune prise de vue pendant un passage de transmission en cours |
| Intervalle minimal  | Au moins 5 min entre la fin de la prise de vue et le début de la transmission |

### 8.3 Suivi des bilans de puissance et de données

Le planificateur suit deux bilans sur l'horizon de planification :

- **Bilan de puissance** : trajectoire prévue du SoC de la batterie, fondée sur le modèle de production solaire,
  les heures d'éclipse et le profil de charge prévu. Le planificateur ne programme pas de prise de vue si
  le SoC prévu descend sous 40 % à un moment quelconque.
- **Bilan de données** : volume de données cumulé issu des prises de vue, comparé à la capacité de transmission au sol.
  Les taux de compression adaptés à la scène sont estimés selon le type de cible (océan,
  côte, terre). La capacité de transmission au sol est calculée à partir de la durée des contacts et du mode de débit.

## 9. Télémesure utile

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
