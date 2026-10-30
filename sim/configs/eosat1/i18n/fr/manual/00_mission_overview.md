# Vue d'ensemble de la mission EOSAT-1

**Référence du document :** EOSAT1-UM-MIS-001
**Édition :** 2.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Objet

Le présent document donne une vue d'ensemble de haut niveau de la mission EOSAT-1 (Earth Observation Satellite 1) :
objectifs de la mission, configuration du satellite, paramètres orbitaux, segment sol et
phases de la mission. Il constitue le point d'entrée de la collection des manuels utilisateur du satellite EOSAT-1.

## 2. Objectifs de la mission

EOSAT-1 est un CubeSat 6U d'imagerie multispectrale en orbite basse, conçu pour la surveillance
des courants océaniques et l'observation des zones côtières. Les objectifs principaux de la mission sont les suivants :

- surveiller les courants océaniques par imagerie multispectrale systématique des signatures de couleur
  de la surface de la mer, en exploitant les bandes de couleur de l'océan (bleu 443 nm, vert 560 nm, rouge 665 nm, proche infrarouge (NIR) 865 nm) ;
- acquérir des images multispectrales de moyenne résolution des zones côtières et des régions océaniques avec un
  temps de revisite d'environ 5 jours ;
- démontrer la gestion bord autonome des données et la compression d'image adaptée à la scène ;
- servir de support à des exercices de planification de mission au sol, de programmation par passage et de récupération des données ;
- fournir des données d'imagerie pour l'estimation de la vitesse des courants océaniques, la détection des remontées d'eau froide (upwelling) et la
  cartographie de la concentration en chlorophylle.

## 3. Paramètres orbitaux

| Paramètre              | Valeur                       |
|------------------------|------------------------------|
| Type d'orbite          | Héliosynchrone (SSO)         |
| Altitude               | ~513 km en moyenne (503–530 km) |
| Inclinaison            | 98°                          |
| LTAN                   | Aube-crépuscule (~06:00/18:00 heure locale) |
| Période orbitale       | ~94,5 min                    |
| Durée d'éclipse        | ~34–36 min (variation saisonnière) |
| Cycle de répétition    | ~5 jours                     |
| Vitesse de la trace au sol | ~7,07 km/s               |

L'altitude moyenne d'environ 513 km maintient une distance d'échantillonnage au sol (GSD) de quelques dizaines de mètres,
tout en conservant une orbite héliosynchrone à 98° d'inclinaison. L'orbite SSO aube-crépuscule offre
des conditions d'éclairement favorables à l'imageur multispectral et maximise l'exposition des panneaux
solaires, ce qui réduit la profondeur de décharge de la batterie pendant les éclipses.

## 4. Vue d'ensemble de la plateforme

EOSAT-1 est un CubeSat 6U à plateforme stabilisée trois axes, doté des principaux sous-systèmes suivants :

| Sous-système                       | Abréviation  | Description                                      |
|------------------------------------|--------------|--------------------------------------------------|
| Sous-système d'alimentation électrique | EPS      | Bus régulé 28 V, 5 panneaux GaAs fixés sur la structure + 2 ailes déployables, batterie Li-ion, PDM en redondance froide |
| Système de contrôle d'attitude et d'orbite (SCAO) | AOCS | 4 roues de réaction, 1 magnétomètre (sans redondance), 2 senseurs stellaires, 6 têtes CSS, gyromètres |
| Gestion bord des données           | OBDH         | OBC en redondance froide (A/B), double bus CAN, mémoire de masse, traitement TC/TM |
| Sous-système de contrôle thermique | TCS          | Passif (MLI/radiateurs), réchauffeurs de batterie (actifs), contrôle thermique passif par l'orientation |
| Télémesure, poursuite et télécommande | TTC       | Transpondeur bande S en redondance froide, émetteur de balise UHF, canal de commande PDM dédié, antenne déployée par fil thermofusible |
| Charge utile                       | PLD          | Imageur multispectral (4 bandes de couleur de l'océan), monté au nadir |

### 4.1 Repère satellite

Le repère satellite est défini comme suit :

- **+X** : le long de la trace (vecteur vitesse en pointage nadir nominal) ;
- **+Y** : transverse à la trace (vers le panneau solaire tribord) ;
- **+Z** : nadir (vers la Terre en attitude nominale) ; le senseur stellaire nadir et la charge utile y sont montés ;
- **-Z** : zénith ; le senseur stellaire zénith et l'antenne GPS y sont montés.

Chacune des six faces de la structure (+X, -X, +Y, -Y, +Z, -Z) porte une tête de senseur solaire grossier ; cinq
d'entre elles (toutes sauf -Z) portent un panneau solaire fixé sur la structure. Des ailes solaires déployables sur les faces +Y et -Y
(0,120 m² de cellules chacune) portent la surface de captation solaire totale de 0,198 m² (repliées) à
0,438 m² (déployées).

### 4.2 Bilan de masse et de puissance

| Paramètre        | Valeur         |
|------------------|----------------|
| Masse sèche      | ~12 kg (6U)   |
| Puissance produite max. | ~89 W (phase éclairée, ailes déployées et orientées vers le Soleil, début de vie) |
| Puissance consommée moy. | ~29 W (NOMINAL, moyenne sur l'orbite) |
| Capacité de la batterie | 100 Wh, 3 Ah (8S1P), 21,5–29,2 V |
| Puissance de l'OBC | 6 W          |

### 4.3 Architecture de redondance

EOSAT-1 utilise la redondance froide pour les sous-systèmes critiques :

| Composant       | Redondance    | Basculement                                   |
|-----------------|---------------|-----------------------------------------------|
| OBC             | A/B (froide)  | Commande sol ou FDIR après 3 réinitialisations par le chien de garde |
| Transpondeur    | Principal/redondant (froide) | Commande sol ou FDIR après perte de liaison |
| PDM             | Voie A/B (froide) | Commande sol                              |
| Magnétomètre    | Aucune (unité unique) | Sa perte met fin à l'amortissement B-dot et à la désaturation magnétique |
| Senseur stellaire | Zénith/nadir | Sélection automatique selon la disponibilité du champ de vue (FOV) |

## 5. Segment sol

### 5.1 Stations sol

| Station    | Emplacement                 | Élévation min. | Rôle principal     |
|------------|-----------------------------|---------------|--------------------|
| Iqaluit    | 63,747 N, 68,518 O          | 5°            | TT&C + vidage des données |
| Troll      | 72,012 S, 2,535 E           | 5°            | TT&C + vidage des données |

EOSAT-1 s'appuie sur un segment sol à deux stations assurant une couverture polaire dans les deux hémisphères :

- **Iqaluit** (Nunavut, Canada) : station de l'hémisphère Nord, à 63,747° de latitude nord.
  Elle assure la TT&C principale et la transmission au sol des données scientifiques lors des passages nord. Sa latitude élevée
  permet plusieurs contacts par jour avec l'orbite polaire héliosynchrone.
- **Troll** (Terre de la Reine-Maud, Antarctique) : station de l'hémisphère Sud, à 72,012° de latitude sud.
  Elle assure une couverture complémentaire de TT&C et de vidage des données lors des passages sud, ce qui réduit
  l'intervalle maximal entre deux contacts sol.

Toutes les stations sol communiquent en bande S (liaison montante à 2025 MHz / liaison descendante à 2200 MHz). La durée
type d'un contact varie de 5 à 12 minutes selon la géométrie du passage et l'élévation
maximale. Le réseau de deux stations offre environ 4 à 8 contacts par jour, avec
un intervalle maximal d'environ 4 à 6 heures entre deux contacts.

### 5.2 Système de contrôle de mission

Le système de contrôle de mission (MCS) assure :

- la surveillance de la télémesure en temps réel et le contrôle de limites depuis 6 postes opérateur ;
- la génération, la validation et l'envoi des télécommandes avec le générateur de commandes PUS ;
- le soutien à la dynamique du vol (restitution d'orbite par le GPS de bord) ;
- la planification de mission par passage et la programmation de la charge utile avec suivi des bilans de puissance et de données ;
- le journal des alarmes, avec suivi des événements S5 et des violations de surveillance S12 ;
- la relecture de la TM enregistrée et l'analyse des tendances à l'échelle de l'orbite ;
- le processus de coordination GO/NO-GO pour les opérations critiques ;
- la frise chronologique des fenêtres de visibilité, avec affichage de la visibilité par station.

### 5.3 Postes opérateur

Le MCS prend en charge 6 postes opérateur avec contrôle d'accès par rôle :

| Poste             | Abréviation  | Responsabilité                              |
|-------------------|--------------|---------------------------------------------|
| Directeur de vol  | FD           | Autorité générale sur la mission, tours de table GO/NO-GO |
| Puissance/thermique | PT         | Surveillance et commande de l'EPS et du TCS |
| Opérateur AOCS    | AOCS         | Détermination et contrôle d'attitude         |
| Opérateur TTC     | TTC          | Gestion de la liaison de communication       |
| Opérateur OBDH    | OBDH         | Santé de l'OBC, gestion des données, gestion du logiciel |
| Opérateur charge utile | PLD     | Opérations de prise de vue et gestion des données |

## 6. Phases de la mission

| Phase                | Durée          | Description                                          |
|----------------------|----------------|------------------------------------------------------|
| Séparation           | T+0 à T+30min  | Séparation du lanceur, minuterie de 30 min, mise sous tension des lignes non commutables |
| LEOP                 | 0–3 jours      | Phase de lancement et de début d'orbite : premier contact, opérations sous chargeur d'amorçage, amortissement des vitesses angulaires |
| Recette en orbite    | 3–30 jours     | Vérification des sous-systèmes, étalonnage du SCAO, activation de la charge utile |
| Opérations nominales | 30 jours–EOM   | Prise de vue de routine des océans, transmission des données au sol, surveillance de l'orbite |
| Opérations prolongées | EOM+          | Opérations réduites en cas de prolongation de la mission |
| Retrait de service   | Phase finale   | Passivation et désorbitation contrôlée               |

### 6.0 La phase de mission bord — et ce qu'elle conditionne

Le satellite porte la phase de mission comme un état actif, dans `eps.spacecraft_phase`
(0x0129) :

| Valeur | Nom | Signification |
|---|---|---|
| 0 | PRE_SEPARATION   | Tout est éteint, aucun sous-système n'est cadencé |
| 1 | SEPARATION_TIMER | Attente réglementaire de 30 minutes en cours, tout est encore éteint |
| 2 | INITIAL_POWER_ON | Minuterie échue, lignes non commutables (OBC + RX) activées |
| 3 | BOOTLOADER_OPS   | OBC sous chargeur d'amorçage, HK balise uniquement |
| 4 | LEOP             | Logiciel applicatif démarré, vérification séquentielle |
| 5 | COMMISSIONING    | Vérification de tous les sous-systèmes en cours |
| 6 | NOMINAL          | Déclaré opérationnel |

La phase **n'est pas une simple étiquette**. Elle constitue un verrouillage sur six mécanismes, et un
opérateur qui ne la fait pas avancer constatera que le satellite refuse silencieusement de
fonctionner :

1. **Cadencement des sous-systèmes** — rien ne s'exécute aux phases 0–1.
2. **Acceptation des télécommandes** — à la phase ≤ 3, l'OBC est sous chargeur d'amorçage et
   seul le sous-ensemble de commandes du chargeur d'amorçage est accepté (S17.1, S9.1, HK balise S3,
   S20.1/3, et S8.1 fonctions 19/20, 52–57, 61, 66/67, 69, 120). Tout le reste
   est refusé à l'acceptation avec le code d'échec 0x0006. S9.1 (`SET_TIME`) franchit
   cette condition, mais échoue à l'exécution tant que `OBC_BOOT_APP` n'a pas été exécutée.
3. **Le mode satellite dérivé** — `sc_mode`, et sa copie en télémesure
   `sat.mode` (0x0001), est forcé à SAFE à toute phase inférieure à 6, quel que soit
   l'état de santé du satellite. L'en-tête de la console ne peut afficher NOMINAL tant que NOMINAL n'a
   pas été déclaré.
4. **Armement de la FDIR avancée** — le modèle de propagation de défaillance et de reprise est
   désarmé en dessous de la phase 6, car pendant la LEOP les roues de réaction sont
   légitimement hors tension et les règles en cascade déclareraient une double défaillance de roue
   dès le premier cycle.
5. **Règles FDIR historiques conditionnées par la phase** — les deux règles de
   `subsystems/fdir.yaml` qui portent un `min_phase` (`aocs.wheels_enabled` et
   `aocs.att_error`) ne s'arment qu'à la phase 6. Les autres, toutes dédiées à la protection du matériel,
   restent armées dans toutes les phases.
6. **Le verrouillage de la propulsion** — `subsystems/prop.yaml` déclare
   `min_phase: 6`, de sorte qu'**aucune poussée ne peut être armée** tant que NOMINAL n'est pas déclaré.

L'automate d'états avance **seul de 1 → 2 → 3 → 4** (minuterie de séparation, mise sous tension
de l'OBC, démarrage de l'application) et revient à 3 lors d'un redémarrage de l'OBC. Il ne règle jamais 5
ni 6 : **COMMISSIONING et NOMINAL sont des déclarations sol**, faites au moyen de la
télécommande `SYS_SET_MISSION_PHASE` (S8.1, func_id 120, criticité
`critical`) :

```
SYS_SET_MISSION_PHASE(phase = 3..6, flags)
    flags bit 0 = FORCE (permit a backwards transition)
```

* La phase 5 est déclarée à la fin de **LEOP-007** (Mise sous tension séquentielle), étape 8.
* La phase 6 est déclarée à la fin de **COM-013** (Recette complète du SCAO),
  étape 14, après la liste de vérification préalable à la transition de `09_leop.md` §9.1.

Garde-fous, chacun avec son propre code d'échec pour que la console nomme la cause du refus :

| Code | Refus |
|---|---|
| 0x0C01 | Phase cible hors de 0–6 |
| 0x0C02 | Les phases 0–2 sont des états antérieurs à la séparation et ne peuvent jamais être commandées depuis le sol, forcées ou non — commander la phase 0 ou 1 arrêterait le cadencement qui porte la liaison montante |
| 0x0C03 | Impossible d'entrer dans une phase applicative (≥ 4) tant que l'OBC est sous chargeur d'amorçage ; envoyer `OBC_BOOT_APP` (fonction 55), l'automate d'états avance alors de lui-même |
| 0x0C04 | Transition arrière sans l'indicateur FORCE |

**Les transitions arrière sont permises, mais uniquement de façon délibérée.** Une mission réelle
ne revient pas à la légère de NOMINAL à LEOP ; une tentative sans indicateur est donc
rejetée avec un motif qui nomme l'indicateur. Un opérateur qui annule une déclaration
prématurée renvoie la commande avec `flags = 1`, et le journal d'événements enregistre la transition
comme FORCED. Un refus pur et simple laisserait une déclaration prématurée sans
remède.

Chaque changement accepté déclenche l'événement S5 `MISSION_PHASE_CHANGED` (0x0055),
qui porte la phase de départ et la phase d'arrivée.

### 6.1 Séquence de séparation

La séquence de séparation du lanceur suit un automate à 7 phases :

| Phase             | Durée      | Description                                       |
|-------------------|------------|---------------------------------------------------|
| PRE_SEPARATION    | —          | Attente du signal de séparation du lanceur        |
| SEP_DETECTED      | Instantané | Ouverture des interrupteurs de séparation, démarrage de la minuterie |
| POWER_STABILIZE   | ~30 s      | Initialisation de l'EPS, les lignes non commutables alimentent OBC+RX |
| TIMER_WAIT        | ~30 min    | Attente réglementaire : aucune émission pendant 30 minutes |
| ANTENNA_DEPLOY    | ~60 s      | Déploiement de l'antenne par fil thermofusible    |
| BEACON_START      | ~10 s      | Début des émissions de balise (SID 11, palier SAFE à 1 kbit/s) |
| NOMINAL           | —          | Transition vers les opérations LEOP               |

Pendant l'attente de 30 minutes de la minuterie, seuls l'OBC (par la ligne PDM non commutable) et le récepteur
(par le canal de commande PDM dédié) sont alimentés. Aucune émission RF n'a lieu.

### 6.2 Concept de la LEOP

Pendant la LEOP, le satellite fonctionne d'abord en mode BOOTLOADER, avec un jeu de commandes
restreint et une télémesure limitée à la balise (SID 11). La séquence LEOP se déroule comme suit :

1. **Premier contact** : le sol acquiert le signal RF du paquet de balise. Vérifier la santé du satellite
   à partir des paramètres HK de la balise.
2. **Démarrage de l'application** : le sol commande la transition du BOOTLOADER vers le logiciel applicatif.
   Vérifier la réussite du démarrage grâce à la télémesure de servitude complète.
3. **Amortissement des vitesses angulaires** : l'AOCS fonctionne en mode DETUMBLE à l'aide des magnétocoupleurs. Surveiller la convergence des vitesses angulaires
   en dessous de 0.5 deg/s.
4. **Acquisition du Soleil** : l'AOCS passe en mode COARSE_SUN (3), en utilisant les CSS et les magnétocoupleurs
   pour le pointage solaire.
5. **Mise sous tension séquentielle** : activer les sous-systèmes un par un, en vérifiant leur santé à chaque étape.
6. **Recette du SCAO** : effectuer la recette des capteurs et actionneurs d'attitude dans l'ordre (voir
   `09_leop.md` pour la procédure détaillée).
7. **Transition vers le nominal** : une fois tous les points de contrôle GO/NO-GO franchis, commander la transition vers le
   mode AOCS NOMINAL (4) et commencer les opérations nominales.

### 6.3 Concept des opérations nominales

En opérations nominales, le satellite maintient une attitude de pointage nadir (mode AOCS NOMINAL, 4)
pour la surveillance des courants océaniques. Les cibles de prise de vue sont planifiées en fonction des régions d'intérêt
des courants océaniques et programmées passage par passage, en tenant compte des bilans de puissance et de données.
La charge utile est activée environ 60 secondes avant la fenêtre de prise de vue, puis ramenée
en STANDBY. Les données d'image enregistrées sont transmises au sol lors des passages au-dessus des stations
d'Iqaluit et de Troll.

Les opérations quotidiennes types comprennent :

- 4 à 8 contacts sol avec les stations d'Iqaluit et de Troll ;
- 2 à 6 opportunités de prise de vue au-dessus des régions océaniques ciblées ;
- l'enregistrement continu de la télémesure de servitude, pour relecture pendant les contacts ;
- la surveillance des bilans de puissance et de données pour la planification de l'orbite suivante.

## 7. Documents associés

| Document                          | Référence              |
|-----------------------------------|------------------------|
| Manuel d'opérations de l'EPS      | `01_eps.md`            |
| Manuel d'opérations de l'AOCS     | `02_aocs.md`           |
| Manuel d'opérations du TCS        | `03_tcs.md`            |
| Manuel d'opérations de l'OBDH     | `04_obdh.md`           |
| Manuel d'opérations de la TTC     | `05_ttc.md`            |
| Manuel d'opérations de la charge utile | `06_payload.md`   |
| Opérations orbitales              | `07_orbit_ops.md`      |
| Référence FDIR                    | `08_fdir.md`           |
| Guide des opérations LEOP         | `09_leop.md`           |
| Référence des commandes et de la télémesure | `09_command_reference.md` |

---

*Fin du document — EOSAT1-UM-MIS-001*
