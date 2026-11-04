# GUIDE DES OPÉRATIONS — simulateur du satellite EOSAT-1

**Guide pratique pour les opérations de mission, le déroulement des scénarios et le traitement des anomalies**

---

## Table des matières

1. [Démarrage rapide](#quick-start)
2. [Démarrage du simulateur](#simulator-startup)
3. [Système de contrôle de mission (MCS)](#mission-control-system-mcs)
4. [Surveillance de la télémesure](#telemetry-monitoring)
5. [Commander le satellite](#commanding-the-spacecraft)
6. [Utilisation du planificateur de mission](#mission-planner-usage)
7. [Procédures de traitement des anomalies](#anomaly-response-procedures)
8. [Scénarios opérationnels courants](#common-operational-scenarios)
9. [Tendances et historique](#trends-and-history)
10. [Rapports](#reports)
11. [Consulter la configuration](#browsing-the-configuration)
12. [Dépannage](#troubleshooting)
13. [Scénarios de formation](#training-scenarios)

---

## Démarrage rapide

**Prérequis :**
- Python 3.11+ avec les dépendances installées
- Fichiers de configuration d'EOSAT-1 en place
- Navigateur web pour le MCS (Chrome ou Firefox recommandé)

**Démarrage en 30 secondes :**

```bash
# Terminal 1: Start Simulator
cd /sessions/beautiful-dazzling-edison/mnt/SpaceMissionSimulation
python -m smo_simulator --config configs/eosat1/ --port 5678

# Terminal 2: Start MCS
cd /sessions/beautiful-dazzling-edison/mnt/SpaceMissionSimulation
python -m smo_mcs --simulator-host localhost:5678 --mcs-port 8080

# Browser: Open MCS
Navigate to: http://localhost:8080/
Login with default credentials (if required)
```

**Premières actions (5 minutes) :**

1. Ouvrir la vue d'ensemble système du MCS → vérifier le quaternion d'attitude et la position orbitale
2. Demander un rapport HK (S3 sous-type 27) → confirmer que la télémesure arrive
3. Envoyer un écho NOOP (S17 sous-type 1) → vérifier la liaison de commande
4. Activer la HK périodique (S3 sous-type 5, SID=1) → lancer le flux de télémesure EPS

---

## Démarrage du simulateur

### Option 1 : mode standard (simulation en temps réel)

```bash
python -m smo_simulator \
  --config configs/eosat1/ \
  --port 5678 \
  --time-scale 1.0
```

**Paramètres :**
- `--config` : chemin de la configuration d'EOSAT-1
- `--port` : port TCP de connexion du MCS (5678 par défaut)
- `--time-scale` : 1.0 = temps réel, 2.0 = vitesse 2x, 0.5 = demi-vitesse
- `--scenario` : charger un scénario de panne (facultatif)

### Option 2 : simulation accélérée (essais)

```bash
python -m smo_simulator \
  --config configs/eosat1/ \
  --port 5678 \
  --time-scale 10.0
```

**Cas d'usage :** tester 24 heures d'opérations en 2,4 heures.

### Option 3 : avec un scénario de panne

```bash
python -m smo_simulator \
  --config configs/eosat1/ \
  --port 5678 \
  --scenario configs/eosat1/scenarios/battery_discharge.yaml
```

**Scénarios disponibles :** voir le répertoire `configs/eosat1/scenarios/`

### Option 4 : mode distribué (passerelle)

```bash
# Start Simulator (headless, on server)
python -m smo_simulator --config configs/eosat1/ --port 5678

# Start Gateway (relays to network)
python -m smo_gateway --simulator localhost:5678 --listen 0.0.0.0:6789

# Connect MCS (from laptop, different machine)
python -m smo_mcs --simulator-host gateway.corp.net:6789 --mcs-port 8080
```

---

## Système de contrôle de mission (MCS)

### Disposition du tableau de bord

**Panneau de vue d'ensemble système (en haut à gauche) :**
```
Spacecraft: EOSAT-1
Phase: Nominal Operations
Orbit: 97.39° sun-synchronous, ~513 km mean altitude, LTAN ~10:00

Attitude:
  Quaternion: (0.001, 0.707, -0.002, 0.707)
  Pointing: Nadir (Earth center)
  Error: 0.05°

Power:
  Battery SoC: 78%
  Load Shedding: Stage 0 (None)
  Power Margin: +250 W

Thermal:
  Hottest Zone: OBC (+32°C)
  FPA: -15°C (Operational)
```

**Graphe de télémesure (en haut à droite) :**
- Paramètres sélectionnables pour le suivi de tendance en temps réel
- Historique de 1 h par défaut
- Commandes de zoom et de défilement

**Panneau de commande (en bas à gauche) :**
- Sélecteur de sous-système (AOCS, EPS, TCS, TTC, OBDH, charge utile)
- Liste des fonctions de commande avec éditeurs de paramètres
- Journal de l'historique des commandes

**Panneau d'alertes (en bas à droite) :**
- Flux d'événements S5 en temps réel (code couleur selon la gravité)
- Filtre des événements par sous-système
- Suivi de l'acquittement des événements

### Principaux onglets de vues

1. **Vue d'ensemble système** — synthèse de l'état du satellite
2. **Bilan de puissance** — batterie, générateur solaire, délestage, marge de puissance
3. **Attitude et contrôle** — quaternion, vitesses angulaires, moment cinétique, état des roues
4. **Suivi thermique** — températures des zones, état des réchauffeurs et du refroidisseur
5. **Qualité de liaison** — verrouillage de la porteuse, marge de liaison, température du PA
6. **État de la charge utile** — température du FPA, stockage, catalogue d'images
7. **Alarmes FDIR** — violations S12, déclenchements de règles S19, cascades de défaillances et avancement des procédures de reprise
8. **Planning des contacts** — fenêtres de visibilité des stations sol
9. **Tendances** — historique des paramètres sur n'importe quelle fenêtre (voir ci-dessous)
10. **Journal des événements** — historique des événements S5 (interrogeable)

### Bandeau de connaissance de la situation

En haut de chaque onglet, et à lire avant toute autre chose :

| Champ | Ce qu'il vous indique |
|---|---|
| Temps avant AOS / LOS, avec le nom de la station | Si vous pouvez commander maintenant, et pendant combien de temps |
| Palier de débit actif ou commandé | Une liaison **rétrogradée par une condition** — vous avez demandé HIGH et le satellite est en LOW parce que l'antenne, le mode DOWNLINK ou le masque d'élévation l'imposent |
| Remplissage de la mémoire bord | Ce qu'il vous reste à descendre au sol |
| Nombre d'alarmes non acquittées | Ce que personne n'a encore regardé |
| Vitesse de simulation | Si ce que vous observez se déroule en temps réel |
| EN DIRECT / PÉRIMÉ | Si la console reçoit encore quoi que ce soit |

### Coloration selon les limites

Un paramètre passe au jaune ou au rouge selon **deux** sources **indépendantes** :

* **Les limites sol** (`configs/eosat1/mcs/limits.yaml`, 51 plages) — contrôlées par
  le MCS à chaque échantillon. C'est le jugement propre de la salle de contrôle, et il
  couvre des paramètres que le satellite ne surveille pas du tout.
* **Les moniteurs bord S12** (46 définitions) — le jugement du satellite.
  Ils peuvent déclencher des actions autonomes S19 ; les limites sol ne le peuvent pas.

Ce sont délibérément des ensembles différents. 29 paramètres à limites n'ont pas d'équivalent
S12 — courant du bus, courants par ligne, température du gyromètre, PDOP GPS — si bien
qu'avant le câblage des limites sol, ils ne donnaient aucun repère visuel, ni d'un côté ni de l'autre.
`docs/PARAMETER_MAP.md` indique quel paramètre relève de quel mécanisme.

### Postes de console

Chaque poste de console a un seul titulaire, et c'est le MCS qui décide qui il est. Le sélecteur de poste de l'en-tête ne fait que passer d'un poste à l'autre parmi ceux que vous occupez.

- **Qui vous êtes.** Sur Google Cloud, vous êtes votre compte C2O, vérifié par IAP. Dans une classe sur portable (`SMO_SEATS=local`), vous saisissez votre nom, affiché comme *non vérifié*. Avec `SMO_SEATS=off`, le réglage par défaut sur portable, les postes ne sont pas gérés : le sélecteur fonctionne comme avant et chaque commande est journalisée comme *non vérifiée*.
- **Prendre un poste.** Ouvrez **Poste** à côté du sélecteur de poste. *Prenez* un poste vacant. Un poste occupé propose *Demande* : son titulaire voit la demande et a 60 s pour *Céder* ou *Le garder*. Un poste dont le titulaire n'a envoyé aucun signal depuis 3 min est *inactif*. Après 5 min, il est *récupérable* et n'importe qui peut le prendre. *Libérer* rend un poste.
- **Plusieurs postes.** Une même personne peut occuper plusieurs postes, comme dans une petite équipe. Le sélecteur change alors le poste *actif* parmi eux. Les postes que vous n'occupez pas sont grisés, avec le nom de leur titulaire.
- **Commander.** Chaque télécommande, exécution de procédure, envoi S11, demande de vidage, réponse GO/NO-GO et jeton de boucle vocale part *au nom d'un poste que vous occupez*. Un poste que vous n'occupez pas, ou un poste inconnu, est refusé (« Vous n'occupez pas le poste … »). Une procédure s'exécute au nom du poste qui l'a chargée. Chacune de ses commandes exige l'autorité de ce poste, et seul ce poste ou la Direction de vol peut la démarrer, la suspendre, la faire avancer ou l'interrompre.
- **Le journal vous nomme.** L'historique des commandes et la main courante enregistrent le poste, la personne et l'écran.
- **Cet écran.** Chaque onglet du navigateur est un écran (« screen 1 », renommé sous *Cet écran*). *Affiche* choisit ce qu'il montre : votre poste actif ; une mosaïque de tous vos postes (une seule barre de navigation et une seule vue d'ensemble les couvrent, et les commandes partent toujours du poste actif) ; ou l'écran mural (tout le satellite, sans les pages de commande). L'instructeur peut aussi le régler.
- **Instructeur.** Le tableau des postes (*Ouvrir le tableau des postes*, `/seats`, et la vue *Équipe* de la console instructeur) a une colonne par poste, plus *Banc* (connectés, sans poste) et *Écran mural*. Un poste vacant affiche un point rouge et le mot *vacant*. L'instructeur peut :
  - glisser une personne sur un poste pour le lui affecter (depuis le banc, cela ajoute un poste ; depuis un autre poste, la personne est déplacée) ;
  - glisser une pastille d'écran sur un poste ou sur l'écran mural ;
  - *Libérer* une personne (un « membre malade ») ;
  - lancer une *Rotation des rôles* (chacun passe au poste suivant) ;
  - *Verrouiller le tableau* (plus de libre-service), ou verrouiller un seul poste ;
  - autoriser un *binôme* à un poste : un observateur en lecture seule ou un second opérateur aux commandes.

  Chaque mouvement est journalisé. *Exporter le journal des postes* le télécharge, avec les noms ; il reste au sol.
- **Ce que voit le simulateur.** Rien sur les personnes. La chronologie de la console instructeur reçoit du sol un résumé anonyme, par poste uniquement : postes occupés, alarmes acquittées, étapes de procédure, réponses GO/NO-GO, et qui a parlé sur quelle boucle.

---

## Surveillance de la télémesure

### Activer les données de servitude périodiques

Par défaut, la HK n'est **pas diffusée en continu**. L'activer pour obtenir une télémesure continue :

```
MCS Command: S3 subtype 5 (Enable HK)
Parameter: SID = 1 (EPS structure)
Response: S1.1 Acceptance report
Effect: EPS HK packets sent every 4 seconds
```

**Répéter l'opération pour les autres structures :**
- SID 2 : AOCS (attitude, roues, capteurs)
- SID 3 : TCS (zones thermiques)
- SID 4 : OBDH (CPU, mémoire, stockage)
- SID 5 : charge utile (FPA, imagerie, stockage)
- SID 6 : TTC (qualité de liaison, thermique du PA)

### Principaux paramètres à surveiller

**Critiques (à vérifier en premier) :**

| Paramètre | Plage | Seuil d'alerte | Sous-système |
|-----------|-------|-----------------|-----------|
| `eps.bat_soc` | 0-100 % | < 10 % (CRITICAL) | EPS |
| `eps.bus_voltage` | 24-34 V | < 27,7 V (CRITICAL, mode survie EPS) | EPS |
| `aocs.att_error` | 0-180° | > 1° (WARNING) | AOCS |
| `aocs.total_momentum` | 0-0.06 Nms | enveloppe > 70 % (`aocs.h_env_frac` 0x02BA, WARNING) | AOCS |
| `tcs.fpa_temp` | -20 à 0 °C | > -3 °C bloque la prise de vue ; > +14 °C (WARNING) | TCS |
| `ttc.link_margin` | 0-15 dB | < 3 dB (CRITICAL) | TTC |
| `ttc.pa_temp` | 20-80 °C | > 65 °C (SHUTDOWN) | TTC |

**Utiles (à surveiller périodiquement) :**

| Paramètre | Valeur type | Points de vigilance |
|-----------|---------|-----------|
| `eps.power_gen` | 0-89 W (moyenne orbitale env. 40 W) | Tendance à la dégradation |
| `eps.power_cons` | env. 28 W en moyenne orbitale | Pics anormaux |
| `aocs.rw_speed` (les 4) | biais ±1200 tr/min (limite 5500) | Déséquilibre, survitesse |
| `tcs.battery_temp` | -5 à +40 °C | > 45 °C (réchauffeur coupé) |
| `ttc.ber` | < 1e-6 | Tendance à la hausse |

### Graphes de télémesure

**État de charge (SoC) de la batterie sur 24 heures :**
```
Tracer le SoC batterie en fonction du temps
Observer : profil en dents de scie (décharge en éclipse, charge au Soleil)
Normal : le SoC varie entre 30 et 90% (n'atteint ni 0% ni 100%)
Anomalie : hausse ou baisse monotone (charge et décharge non équilibrées)
```

**Vitesse des roues de réaction (les 4 roues) :**
```
Tracer les vitesses des 4 RW en fonction du temps
Observer : les roues gardent des vitesses équilibrées (à ±100 RPM les unes des autres)
Normal : hausse progressive pendant un basculement, baisse rapide pendant une désaturation
Anomalie : une roue nettement plus rapide que les autres (déséquilibre) → vérifier la FDIR
```

**Marge de liaison au cours d'un passage :**
```
Tracer Eb/N0 (link_margin) en fonction du temps pendant la fenêtre AOS-LOS
Observer : hausse à l'approche de la station sol (signal plus fort)
           pic à l'élévation maximale, baisse quand la station s'éloigne
Attendu : marge > 6 dB pendant tout le passage
Anomalie : marge < 3 dB → une règle S19 déclenche une hausse de puissance du PA
```

---

## Commander le satellite

### Déroulement d'une commande

1. **Vérifier l'état du satellite** (bilan de santé)
2. **Contrôler les bilans de puissance et thermique** (s'assurer que l'exécution est sûre)
3. **Composer la commande** (renseigner les paramètres)
4. **Soumettre la commande** (cliquer sur ENVOYER ou utiliser la ligne de commande)
5. **Suivre les rapports S1** (acceptation, exécution, achèvement)
6. **Vérifier le résultat** (télémesure HK, événements)

### Exemple 1 : changement de mode simple

**Objectif :** faire passer l'AOCS du mode nominal nadir au mode survie

**Étape 1 : vérifier que l'on peut poursuivre en sécurité**

```
MCS: Query HK_AOCS (S3 subtype 27, SID=2)
Check:
  - aocs.mode = 4 (NOMINAL)
  - aocs.att_error < 0.5° (attitude good)
  - aocs.total_momentum < 50 Nms (wheels not saturated)
  - Power: eps.bus_voltage > 30.9V (sufficient power)
Status: OK, proceed
```

**Étape 2 : composer la commande**

```
MCS Command Builder:
  Service: 8 (Function Management)
  Subtype: 1 (Execute Function)
  Function ID: 0 (AOCS_SET_MODE)
  Parameter: mode = 1 (safe_boot)
```

**Étape 3 : soumettre**

```
MCS: Click "Send Command"
Response (immediate):
  S1.1: Acceptance report (request_id=1234)
```

**Étape 4 : suivre l'exécution**

```
MCS Event Log (real-time):
  T+0 sec:  S1.1 Acceptance (mode transition accepted)
  T+0 sec:  S1.3 Execution start
  T+1 sec:  S1.5 Progress (step 1/3 - stabilize quaternion)
  T+2 sec:  S1.5 Progress (step 2/3 - reduce wheel speeds)
  T+3 sec:  S1.5 Progress (step 3/3 - coarse sun pointing)
  T+5 sec:  S1.7 Completion (mode transition complete)
  T+5 sec:  S5.0200 AOCS_MODE_CHANGE event
```

**Étape 5 : vérifier**

```
MCS: Query HK_AOCS (S3 subtype 27, SID=2)
Check:
  - aocs.mode = 1 (safe_boot) ✓
  - aocs.att_error < 2° (stabilizing)
  - aocs.rw[1-4]_speed → 0 RPM (wheels spinning down)
Status: Transition complete, spacecraft safe
```

### Exemple 2 : commande complexe — passage de prise de vue

**Objectif :** acquérir une image d'un lieu géographique précis pendant un contact sol

**Chronologie :**
- T-5 min : passer l'AOCS en pointage fin
- T-2 min : activer la prise de vue sur la charge utile
- T+0 min : acquérir l'image (60 s)
- T+30 min : télécharger l'image via la station sol

**Étape 1 : préparation avant le passage (T-5 min)**

```
MCS Command 1: AOCS fine point
  S8 func_id=0, mode=5
  Response: S1 reports, mode change event

MCS Command 2: Enable payload
  S8 func_id=26 (PAYLOAD_SET_MODE), mode=2
  Response: S1 reports, mode change event

MCS Command 3: Set cooler temperature
  S8 func_id=36 (PAYLOAD_COOLER_SETPOINT), temp=-15°C
  Response: S1 reports
```

**Étape 2 : prise de vue (T+0 min)**

```
MCS Command 4: Capture image
  S8 func_id=28 (PAYLOAD_CAPTURE)
  Parameters: scene_id=42, lines=4096
  Response: S1.3 (execution start)

MCS Monitoring:
  T+0 sec:   S5.0600 IMAGING_START event
  T+30 sec:  HK_Payload shows image_count incrementing
  T+60 sec:  S5.0601 IMAGING_STOP event
  T+60 sec:  S1.7 Execution complete
```

**Étape 3 : vérifier l'acquisition de l'image**

```
MCS: Query HK_Payload (S3 subtype 27, SID=5)
Check:
  - image_count = previous+1
  - storage_used increased by ~2 MB
  - compression_ratio = 4.2:1
  - snr_avg = 32 dB (good quality)
Status: Image captured successfully
```

**Étape 4 : programmer le téléchargement (T+30 min, pendant le contact sol)**

Option A : **téléchargement immédiat** (si la station sol est en visibilité)

```
MCS: Check contact schedule
  AOS (Acquisition of Signal): T+30 min
  LOS (Loss of Signal): T+37 min
  Link margin: 8 dB (adequate)
  Downlink capacity: ~3 Mbps

MCS Command: S13 subtype 1 (initiate transfer)
  transfer_id=1, data_type=image_0042, block_size=4096

MCS Monitoring: S13 subtype 3 (request blocks)
  [Automatically downloads 512 blocks × 4KB = 2 MB in ~10 seconds]
  MCS plots download progress bar
  CRC verified per block

MCS Command: S13 subtype 5 (end transfer)
  transfer_id=1
  Response: S1.7 (transfer complete)
```

Option B : **programmer le téléchargement pour plus tard** (en cas de contrainte de temps)

```
MCS: Use Mission Planner
  Schedule imaging for known ocean target (7 targets configured)
  Planner outputs: AOS/LOS, contact duration, data volume
  Automatically schedules S11 TC activity

MCS: Monitor S11 execution at scheduled time
  S1 reports confirm auto-executed commands
```

### Reprise après erreur de commande

**Scénario : commande rejetée par un contrôle de sécurité**

```
MCS: Send S8 func_id=0 (AOCS_SET_MODE), mode=1 (safe)

Response (immediate):
  S1.2: Acceptance failure
  error_code=0x0003
  reason="Cannot transition to safe: wheels still desaturating"

Recovery:
  1. Check S5 event log
     Found: DESATURATION_START (5 min ago)
  2. Query HK_AOCS
     aocs.total_momentum = 45 Nms (still declining)
  3. Wait 2 minutes for desaturation to complete
  4. Monitor S5.0208 DESATURATION_COMPLETE event
  5. Retry command
     S1.1: Acceptance success
     Mode transition proceeds
```

---

## Utilisation du planificateur de mission

### Objet

Le planificateur de mission programme les activités (prises de vue, téléchargements, maintenance) en respectant les contraintes :
- **Puissance :** limites de SoC et de DoD de la batterie
- **Thermique :** limites de température des zones, capacité du refroidisseur
- **AOCS :** durée des basculements, réserve de moment cinétique, précision de pointage
- **Données :** limites de stockage de la charge utile, capacité de la liaison descendante

### Déroulement

**1. Définir les objectifs de la mission**

```
MCS Planner: Click "New Mission"
Mission name: "EOSAT-1 Week-3 Operations"
Start time: 2026-04-11 00:00 UTC
Duration: 7 days
```

**2. Définir les contraintes**

```
MCS Planner: Constraint Manager
Power:
  - Minimum battery SoC: 20%
  - Maximum DoD: 50%
Thermal:
  - Maximum battery temp: 40°C
  - Maximum FPA temp: -3°C
AOCS:
  - Pointing accuracy: < 0.5°
  - Momentum reserve: > 10 Nms
Data:
  - Maximum payload storage: 95%
  - Minimum downlink per pass: 500 MB
```

**3. Définir les activités**

```
MCS Planner: Activity Library
Available activities:
  - IMAGING_PASS (5+ targets, configurable lat/lon)
  - DATA_DOWNLOAD (to ground station)
  - SAFE_MODE_RECOVERY (post-anomaly)
  - PAYLOAD_MAINTENANCE (calibration, diagnostics)
  - SYSTEM_HEALTH_CHECK (subsystem test)
```

**4. Programmer les activités**

```
MCS Planner: Schedule Builder
Activity 1: IMAGING_PASS
  Target: "Agulhas Current Region" (lat=−40, lon=20)
  Duration: 60 sec
  Power budget: 200 W additional
  Earliest start: 2026-04-11 02:15 UTC (next AOS over target)

Activity 2: DATA_DOWNLOAD
  Ground station: "Canberra" (Australia)
  Start: 2026-04-11 03:00 UTC (AOS)
  Duration: 7 min (contact window)
  Data volume: 500 MB (payload images)

Activity 3: SAFE_MODE_RECOVERY
  Start: 2026-04-12 12:00 UTC (scheduled maintenance)
  Duration: 15 min
  Power budget: 150 W

[Continue scheduling for 7 days...]
```

**5. Optimiser le planning**

```
MCS Planner: Constraint Checker
Analysis:
  ✓ All power constraints satisfied (SoC never < 22%)
  ✓ All thermal constraints satisfied (max temp 38°C)
  ✓ All AOCS constraints satisfied (momentum reserve maintained)
  ✓ Downlink capacity sufficient (15 GB/week, need 12 GB)

Warning:
  ! FPA cooling rate limiting on 2026-04-14 (3 consecutive imaging passes)
  Recommendation: Reduce 2nd pass duration to 45 sec, extend cooler off-time by 10 min

Optimization:
  Click "Apply Recommendation"
  [Plan updated, all constraints re-checked]
  Status: READY TO UPLOAD
```

**6. Envoyer au satellite**

```
MCS Planner: Upload Mission Plan
Action: Convert plan to S11 TC activities
  [24 activities → 24 S11 telecommands]

MCS: Monitor S11 execution
  S1 reports for each scheduled activity
  Automatic execution at scheduled times
  Ground operator monitors and intervenes if needed

Event Log:
  T+0h:  Activity 1 (AOCS fine point) auto-executed
  T+10min: Activity 2 (Payload imaging) auto-executed
  T+70min: Activity 3 (Data download) auto-executed
  ...
  T+7d: Final activity complete
  Status: Mission plan executed successfully
```

### Intégration des stations sol

**Station de Canberra (exemple) :**

```
MCS Planner: Ground Stations
Station name: Canberra, Australia
Location: lat=−35.4, lon=149.0
Antenna: 70m parabolic, X-band
Elevation mask: 5° (minimum elevation for lock)
Downlink band: 8 GHz (center frequency)
Uplink band: 7 GHz (center frequency)

Contact prediction:
  AOS: 2026-04-11 03:15 UTC (elevation 5°)
  MAX: 2026-04-11 03:21 UTC (elevation 87°, max link margin)
  LOS: 2026-04-11 03:28 UTC (elevation 5°)
  Contact duration: 13 minutes
  Average link margin: 8 dB (good for high-rate downlink)
  Predicted data volume: 500 MB at 1 Mbps
```

---

## Procédures de traitement des anomalies

### Anomalies AOCS

#### Survitesse d'une roue de réaction

**Événement :** S5.0201 RW_OVERSPEED (vitesse de roue > 5000 tr/min)

**Réponse autonome :**
- La surveillance S12 détecte la violation
- La règle S19 se déclenche : « survitesse RW → désactiver la roue »
- La commande S8 AOCS_DISABLE_WHEEL est exécutée automatiquement

**Forçage manuel (si la reprise autonome échoue) :**

```
MCS: Check which wheel is overspeed
  S3 request HK_AOCS (SID=2)
  aocs.rw1_speed = 5200 RPM ← problematic
  aocs.rw2_speed = 1800 RPM
  aocs.rw3_speed = 1850 RPM
  aocs.rw4_speed = 1900 RPM

MCS Command: Disable wheel 1
  S8 func_id=2 (AOCS_DISABLE_WHEEL), param=0
  Response: S1 reports

MCS Verification:
  Re-query HK_AOCS after 5 sec
  aocs.rw1_enabled = 0 (disabled)
  aocs.rw1_speed → 0 (spun down)
  S5.0201 event should stop repeating
```

#### Senseur stellaire ébloui

**Événement :** S5.0203 ST_BLIND (le senseur stellaire a perdu son accrochage)

**Réponse autonome :**
- La surveillance S12 détecte l'état ST = BLIND
- La règle S19 se déclenche : « ST1 ébloui → basculer sur ST2 »
- La commande S8 ST_SELECT est exécutée et bascule sur le senseur stellaire redondant

**Reprise manuelle (si les deux senseurs sont éblouis) :**

```
MCS: Check AOCS status
  S3 request HK_AOCS (SID=2)
  aocs.st1_status = 3 (blind)
  aocs.st2_status = 3 (blind)
  aocs.mode = 4 (NOMINAL, unsustainable without ST)

MCS Commands:
  1. S8 func_id=0 (AOCS_SET_MODE), mode=3 (coarse_sun_pointing)
     Status: Mode transition accepted, spacecraft uses CSS + magnetometer

  2. S8 func_id=4 (ST1_POWER), on=0
     Status: Power off to let ST1 cool, clear Sun blindness

  3. [Wait 5 minutes]

  4. S8 func_id=4 (ST1_POWER), on=1
     Status: Power on, ST1 boots and reacquires

  5. Monitor S5.0204 ST_RECOVERY event

  6. S8 func_id=0 (AOCS_SET_MODE), mode=5 (fine_point)
     Status: Mode transition back to nominal
```

#### Saturation du moment cinétique

**Événement :** S5.0205 MOMENTUM_SATURATION (moment cinétique > 90 % de la limite)

**Réponse autonome :**
- La surveillance S12 détecte total_momentum > 90 Nms
- La règle S19 se déclenche : « moment cinétique saturé → désaturer »
- La commande S8 AOCS_DESATURATE est exécutée automatiquement

**Surveillance pendant la désaturation :**

```
MCS: Track momentum as wheels desat
  Plot: aocs.total_momentum vs. time

Normal behavior:
  T+0 sec:   momentum = 95 Nms (saturated)
  T+5 sec:   momentum = 80 Nms (declining)
  T+10 sec:  momentum = 50 Nms (good progress)
  T+15 sec:  momentum = 20 Nms (nearly complete)
  T+20 sec:  S5.0208 DESATURATION_COMPLETE event

Expected duration: 15-25 seconds depending on wheel authority
```

---

### Anomalies EPS

#### SoC batterie critique

**Événement :** S5.0102 BATTERY_SOC_CRITICAL (SoC < 10 %)

**Réponse autonome :**
- La surveillance S12 détecte SoC < 10 %
- Les règles S19 se déclenchent :
  1. « SoC critique → charge utile éteinte » (réduction de la charge électrique)
  2. « SoC critique → refroidisseur du FPA éteint » (réduction de la charge thermique)
- Les commandes S8 sont exécutées et le niveau de délestage 1 est activé

**Intervention manuelle :**

```
MCS: Assess power situation
  S3 request HK_EPS (SID=1)
  eps.bat_soc = 8%
  eps.power_gen = 1100 W (sunlit)
  eps.power_cons = 400 W (after payload off)
  eps.power_margin = +700 W (positive, recovering)

Decision: Condition temporary, battery recovering in sunlight

MCS Monitoring:
  Re-query HK every 30 sec
  Watch eps.bat_soc trend upward
  Expected recovery time: 10-15 minutes (one orbit)

When recovered (SoC > 20%):
  S5.0101 BATTERY_SOC_WARNING event fires (informational)
  MCS alerts operator, no action required
```

#### Sous-tension du bus

**Événement :** S5.0104 BUS_UNDERVOLTAGE_CRITICAL (tension du bus < 27,7 V)

**Réponse autonome :**
- La surveillance S12 détecte une tension du bus < 27,7 V
- La règle S19 se déclenche : « sous-tension → charge utile éteinte »
- La commande S8 EPS_PAYLOAD_MODE est exécutée (mode=0, éteint)

**Diagnostic et reprise :**

```
MCS: Investigate cause
  S3 request HK_EPS (SID=1)
  eps.bus_voltage = 27.5V (critically low)
  eps.bat_voltage = 27.5V (the bus follows the battery)
  eps.eclipse_flag = 1 (in eclipse)

Scenario: Heavy power consumption in eclipse
  Power generation: 0 W (dark side of Earth)
  Power consumption: 1500 W (TTC TX active, AOCS wheels active)
  Battery discharge rate: 1500 W

MCS Command: Reduce power consumption
  1. S8 func_id=26 (PAYLOAD_SET_MODE), mode=0
     Already off (from S19 rule)

  2. S8 func_id=68 (TTC_SET_TX_POWER), level=1
     Reduce TTC transmitter power
     Response: S1 reports

  3. S8 func_id=25 (EPS_EMERGENCY_LOAD_SHED), stage=3
     Activate maximum load shedding
     Response: S1 reports

  4. S3 request HK_EPS
     eps.bus_voltage = 28.4V (recovering)

MCS Monitoring:
  Wait for eclipse exit (AOS to illuminated region)
  eps.power_gen → 1200W (solar arrays reilluminated)
  eps.bus_voltage → ~32V (nominal)
  eps.bat_soc recovering
```

---

### Anomalies TCS

#### Surchauffe du FPA

**Événement :** S5.0604 FPA_OVERTEMP (température du FPA > -3 °C)

**Réponse autonome :**
- La surveillance S12 détecte FPA_temp > -3 °C
- La règle S19 se déclenche : « surchauffe FPA → charge utile éteinte »
- La commande S8 EPS_PAYLOAD_MODE est exécutée (mode=0, éteint)
- L'événement S5 PAYLOAD_MODE_CHANGE est généré
- Le refroidisseur du FPA continue de fonctionner pour le refroidir

**Actions manuelles :**

```
MCS: Monitor FPA cooldown
  S3 request HK_Payload (SID=5)
  fpa_temp = -1°C (overtemp)
  fpa_cooler_state = ON

MCS Plot: FPA temperature vs. time
  T+0 min:   FPA = -1°C (overtemp)
  T+5 min:   FPA = -4°C (recovering)
  T+10 min:  FPA = -15°C (at setpoint)

When cooled to nominal:
  S5.040A FPA_THERMAL_READY event fires
  MCS can re-enable payload if needed

MCS Command: Resume imaging (if mission-critical)
  S8 func_id=26 (PAYLOAD_SET_MODE), mode=2
  Response: S1 reports

  If FPA warms up again:
    S12 rule triggers again
    Payload auto-disabled (S19 rule)
    Indicates cooler failure (hardware fault)
    Escalate to FDIR procedures
```

---

### Anomalies TTC

#### Marge de liaison critique

**Événement :** S5.0507 LINK_MARGIN_CRITICAL (Eb/N0 < 3 dB)

**Réponse autonome :**
- La surveillance S12 détecte link_margin < 3 dB
- La règle S19 se déclenche : « liaison critique → augmenter la puissance d'émission »
- La commande S8 TTC_PA_POWER est exécutée (augmentation à 80-90 %)

**Actions manuelles :**

```
MCS: Check contact window
  S3 request HK_TTC (SID=6)
  ttc.link_margin = 2.5 dB (critical)
  ttc.pa_temp = 45°C (room for power increase)
  ttc.ber = 3e-5 (some bit errors, acceptable)

MCS Command: Increase TX power further
  S8 func_id=68 (TTC_SET_TX_POWER), level=95
  Response: S1 reports

MCS Monitoring:
  Re-query HK every 10 sec
  ttc.link_margin improving as ground station gets closer

T+5 min: Link margin recovers to 6 dB (good threshold)
  Reduce TX power to 75% (heat management)
  S8 func_id=68 (TTC_SET_TX_POWER), level=75
```

#### Arrêt du PA sur surchauffe

**Événement :** S5.0509 PA_OVERTEMP_SHUTDOWN (température du PA > 65 °C)

**Réponse autonome :**
- La surveillance S12 détecte PA_temp > 65 °C
- La règle S19 se déclenche : « surchauffe PA → PA éteint »
- La commande S8 TTC_PA_POWER est exécutée (power=0, arrêt)
- La liaison descendante est perdue jusqu'au refroidissement du PA

**Reprise manuelle :**

```
MCS: Assess situation
  S3 request HK_TTC (SID=6)
  ttc.pa_temp = 70°C (above shutdown limit)
  ttc.pa_powered = 0 (already off from S19)
  ttc.carrier_locked = 0 (no downlink)

  Contact window: 5 minutes remaining

MCS Actions:
  1. Wait 3 minutes for PA to cool (passive)
  2. S3 request HK_TTC
     ttc.pa_temp = 55°C (cooled sufficiently)

  3. S8 func_id=68 (TTC_SET_TX_POWER), level=25
     Low power restart to prevent thermal cycling
     Response: S1 reports

  4. Monitor for carrier lock acquisition
     S5.0500 CARRIER_LOCK_ACQUIRED
     Link margin should be adequate for low power

  5. Gradually increase TX power as contact continues
     func_id=68, level 0 → 1 → 2
```

---

## Scénarios opérationnels courants

### Scénario 1 : passage de prise de vue standard (60 minutes)

**Chronologie :**

| Instant | Action | Commande | Vérification |
|------|--------|---------|--------------|
| T-5m | Activer le pointage fin de l'AOCS | S8 func 0, mode=5 | S1 terminé, mode=5 |
| T-2m | Activer la charge utile | S8 func 26, mode=2 | S1 terminé, charge utile allumée |
| T+0m | Lancer la prise de vue | S8 func 28, scène/lignes | S5.0600 IMAGING_START |
| T+30m | Contrôle à mi-passage | S3 SID=5 (HK_Payload) | Stockage en hausse, FPA nominal |
| T+60m | Arrêter la prise de vue | (automatique selon la durée) | S5.0601 IMAGING_STOP, S1.7 |
| T+70m | Télécharger l'image | S13 initialisation + blocs | S13 sous-type 3, 512 blocs |
| T+80m | Vérifier le téléchargement | S3 SID=5 (HK_Payload) | Stockage diminué de 2 Mo |

**Impact attendu sur la puissance :**
- Référence : 800 W
- + charge utile : +200 W
- + prise de vue : +100 W
- Total : 1100 W (gérable en phase éclairée)

---

### Scénario 2 : reprise après mode survie (après une anomalie)

**Déclencheur :** le satellite passe en mode survie à la suite d'une survitesse de roue de réaction

**Chronologie de la reprise :**

```
T+0s:   Anomaly detected (S5.0201 RW_OVERSPEED)
        S19 rule: disable overspeed wheel
        Mode: Fine point → Coarse sun (CSS + mag)

T+30s:  MCS operator checks S5 event log
        Confirms: RW1 overspeed, now disabled
        Decision: Full safe mode transition

MCS Command 1: Set safe mode
  S8 func_id=0, mode=1 (safe_boot)
  Response: S1.3 (exec start), S5.0200 mode change

T+60s:  Mode transition complete
        Wheels spinning down to 0 RPM
        Attitude: Coarse sun pointing, body X toward sun
        Power: 600 W (all non-essential off)

T+120s: MCS operator verifies status
  HK_AOCS check:
    mode=1 ✓
    rw_speed all < 500 RPM ✓
    att_error < 2° ✓
  Status: Safe mode stable

T+600s: Decision to resume operations
  MCS Command 2: Exit safe mode
    S8 func_id=0, mode=5 (fine_point)
    S8 func_id=12 (BEGIN_ACQUISITION)
    Response: Attitude acquisition sequence starts

T+900s: Fine point attitude achieved
  S5.0204 ST_RECOVERY (both trackers locked)
  aocs.att_error < 0.1°
  Ready to resume mission

Total recovery time: 15 minutes
Imaging resume: +5 minutes
```

---

### Scénario 3 : batterie faible en éclipse (contingence)

**Contexte :** satellite en éclipse, SoC de la batterie proche du niveau critique

**Déclencheur :** S5.0102 BATTERY_SOC_CRITICAL (SoC < 10 %)

**Actions autonomes (règles S19) :**
1. Charge utile éteinte (S8 func 26, mode=0)
2. Refroidisseur du FPA éteint (S8 func 43, on=0)
3. Niveau de délestage 1 activé

**Si la baisse se poursuit :**

```
MCS Monitoring:
  T+0:  SoC = 10% (trigger threshold)
  T+30: SoC = 8% (still declining, eclipse continues 10 min more)
  T+60: SoC = 6% (critical, eclipse exit in 5 min)

MCS Command: Emergency load shedding stage 2
  S8 func_id=25 (EPS_EMERGENCY_LOAD_SHED), stage=2
  Effect: TTC TX power OFF, AOCS wheels OFF
  Power consumption: 400 W → 150 W

MCS Monitoring:
  T+90:  SoC = 5% (still declining, 3 min to eclipse exit)
        Spacecraft in safe mode (wheels off)
  T+120: Eclipse exit, sunlight begins
        Power generation: 0 → 1200 W
        SoC reverses trend: 5% → 8% → 12% (recovering)

T+300: SoC = 25% (safe, load shedding stages off)
       Resume normal operations
       S8 func_id=0 (AOCS fine point mode)
       S8 func_id=26 (PAYLOAD_SET_MODE, mode=2)
```

---

### Scénario 4 : fenêtre de maintenance programmée

**Objectif :** réaliser des diagnostics et des mises à jour de paramètres planifiés

**Chronologie :**

```
Pre-maintenance:
  MCS: Schedule S11 activity (system maintenance at T+6 hours)

At T+6h:
  MCS Command 1: Safe mode entry
    S8 func_id=0, mode=1

  MCS Command 2: OBDH diagnostics
    S8 func_id=61 (OBC_DIAGNOSTIC)
    Response: S1 reports, diagnostic results in TM

  MCS Command 3: Update AOCS control gains
    S20 subtype 1 (set parameter)
    param_id: attitude_control_gain
    value: 1.2 (increase by 20%)
    Response: S1 reports

  MCS Command 4: Memory scrub
    S8 func_id=51 (OBC_MEMORY_SCRUB)
    Response: S1.3 (start), S1.5 (progress updates), S1.7 (complete)
    Duration: ~5 minutes

  MCS Command 5: Exit safe mode
    S8 func_id=0, mode=5 (fine point)
    S8 func_id=12 (BEGIN_ACQUISITION)

Verification:
  MCS Command 6: Request test HK
    S3 subtype 27 (HK_AOCS, SID=2)
    Verify new control law active (tighter attitude tracking)
```

---

## Tendances et historique

**Onglet : Tendances.** Les graphes en direct répondent à « que fait-il maintenant ? ». Les tendances répondent à « qu'a-t-il
fait jusqu'ici ? », qui est la question que soulève réellement une anomalie.

1. **Choisir les paramètres.** N'importe quel paramètre catalogué qui parvient au sol —
   plusieurs à la fois, sur des axes communs ou séparés.
2. **Choisir une fenêtre.** Les 15 dernières min / 1 h / 6 h / 12 h, ou une plage explicite.
   L'axe est le **temps bord (CUC)**, et non le temps réel : sous accélération
   du temps, les deux sont sans rapport et seul le CUC a un sens.
3. **Lire les superpositions.**
   - Les plages de limites sont ombrées : « il dérive vers la limite » est donc visible
     avant de devenir une alarme.
   - Les **arcs d'éclipse** sont ombrés — la plupart des comportements thermiques et électriques ne
     s'interprètent qu'au regard de ces arcs.
   - Les **arcs de contact** sont signalés — une lacune dans les données pendant un arc hors contact
     est due à la liaison, pas au satellite.

Les données proviennent de l'archive TM du MCS, qui stocke chaque échantillon de paramètre
qu'il reçoit. Elles survivent à un rechargement du navigateur et à un redémarrage de la console.

**L'habitude la plus utile à enseigner :** avant de commander quoi que ce soit en réaction à
une valeur, afficher le paramètre dans Tendances et regarder la dernière heure. Environ la moitié
des « anomalies » des scénarios de formation sont un cycle orbital normal observé
un échantillon à la fois.

---

## Rapports

**`http://<server>:9090/reports`** (et le même générateur sur le simulateur, port
8080, ainsi qu'en version autonome dans la visionneuse de TM différée, port 8092).

Trois modèles :

| Modèle | Répond à |
|---|---|
| **Revue quotidienne des opérations** | Ce qui s'est passé sur la période : changements de mode, alarmes, commandes envoyées et résultats de leur vérification, enveloppes de puissance et thermiques, volume de données produit et téléchargé |
| **Rapport de passage** | Ce qui s'est passé pendant un contact : AOS/LOS, station, marge de liaison, commandes, vidages, et **ce que la liaison vous a coûté** |
| **Enquête sur anomalie** | Tout ce qui entoure un événement : les tracés des paramètres avant et après, la chaîne S12/S19 qui s'est déclenchée, la procédure de reprise et les commandes de l'opérateur |

La sortie est un **fichier HTML autonome** — aucun serveur n'est nécessaire pour le relire plus tard.

### La grandeur qu'il faut comprendre

L'archive des vidages S15 est l'enregistrement **complet** : chaque paquet que le satellite
a restitué, que le sol l'ait reçu ou non. La vue en direct du MCS est
**incomplète** — les paquets émis pendant que la liaison est coupée sont perdus.

*Archive moins direct* est donc une réponse mesurée à la question « que m'a coûté
la liaison », et elle fait l'objet d'une section du rapport plutôt que d'une note de bas de page. Si vous avez vidé la mémoire
pendant un passage affecté par des évanouissements, c'est ici que cela apparaît.

### Sélection de la période

Toujours **fondée sur le CUC**. Les *noms de fichiers* des vidages portent l'heure réelle à laquelle le fichier
a été écrit ; les horodatages des paquets portent le temps bord. À ×60, une minute réelle
correspond à une heure simulée : sélectionner une période d'après l'horodatage des fichiers renverrait
la mauvaise heure de la mission. L'outil de rapport ne le fait jamais ; si vous écrivez des scripts autour de lui,
ne le faites pas non plus.

---

## Consulter la configuration

**`http://<server>:9090/config`** — en lecture seule, et en lecture seule *par
construction* : les routes de modification n'existent ni sur le MCS ni sur le planificateur ;
il n'y a donc rien à désactiver et aucune erreur possible. L'éditeur en lecture-écriture
n'existe que sur le port de l'enseignant (8080).

À quoi il sert, pour un opérateur :

- **« Quelle est la limite, au juste ? »** — lire la plage directement dans
  `mcs/limits.yaml` plutôt que sur une fiche qui a peut-être une révision de retard.
- **« Pourquoi cette règle s'est-elle déclenchée ? »** — lire la définition S12 et la règle S19.
- **« Cela a-t-il changé ? »** — chaque révision indique qui l'a faite, quand, pourquoi,
  et qui l'a contre-vérifiée. Consulter l'historique de la configuration est la manière dont une vraie
  salle de contrôle répond à « en a-t-il toujours été ainsi ? », et cela mérite d'être fait au
  moins une fois au cours d'une séance de formation.

La configuration, c'est la mission : la fiche matérielle, le catalogue des commandes, le
dictionnaire de télémesure, les structures de servitude, les moniteurs, le modèle
FDIR et les procédures s'y trouvent tous. Savoir s'y retrouver représente une
part plus importante des opérations que n'importe quelle vue prise isolément.


---

## Dépannage

### Le MCS ne se connecte pas au simulateur

**Symptôme :** le MCS affiche l'erreur « Connection refused »

**Diagnostic :**
```
1. Check simulator is running
   Terminal: ps aux | grep smo_simulator

2. Check port is correct
   MCS config: port 5678
   Simulator: --port 5678 (must match)

3. Check firewall
   Linux: sudo iptables -L | grep 5678

4. Check network route
   Terminal: netstat -tulpn | grep 5678
   Should show: LISTEN on 127.0.0.1:5678 (localhost)
```

**Solution :**
```bash
# Restart simulator on correct port
python -m smo_simulator --config configs/eosat1/ --port 5678

# In separate terminal, verify connection
telnet localhost 5678
# Should connect, then Ctrl+C to exit
```

---

### Commandes envoyées mais sans réponse

**Symptôme :** le rapport d'acceptation S1.1 n'est jamais reçu

**Diagnostic :**
```
1. Check telemetry is flowing
   MCS: Request HK (S3 subtype 27)
   If no response: Simulator may be hung

2. Check command queue
   MCS: View command history
   Command shows "pending" status?

3. Check simulator logs
   Terminal: tail -f /tmp/smo_simulator.log
   Look for error messages
```

**Solution :**
```bash
# Increase logging verbosity
python -m smo_simulator --config configs/eosat1/ --port 5678 --verbose

# Restart if simulator hung
pkill -f smo_simulator
python -m smo_simulator --config configs/eosat1/ --port 5678
```

---

### Valeurs de télémesure anormales

**Symptôme :** pics du SoC de la batterie, quaternion d'attitude invalide, etc.

**Diagnostic :**
```
1. Check time scale
   Simulator running at --time-scale 10.0?
   Telemetry may look wrong (1s = 10s simulated)

2. Check scenario is loaded
   MCS Contact Schedule shows realistic pass predictions?
   If ground stations always overhead: orbit may not be initialized

3. Check subsystem configuration
   configs/eosat1/subsystems/*.yaml
   Are parameter values realistic?

4. Check failure scenario
   Simulator started with --scenario battery_discharge.yaml?
   Intentional anomalies may cause "weird" data
```

**Solution :**
```bash
# Verify configuration
python -c "
import yaml
with open('configs/eosat1/mission.yaml') as f:
    cfg = yaml.safe_load(f)
print('Orbit:', cfg['orbit']['altitude_km'], 'km')
print('Initial SoC:', cfg['initial_state']['eps.bat_soc'], '%')
"

# Verify scenario (if loaded)
python -m smo_simulator --config configs/eosat1/ --scenario '' \
  # (empty scenario = no failures, nominal only)
```

---

### Les règles S19 ne se déclenchent pas de manière autonome

**Symptôme :** un paramètre franchit un seuil S12, mais aucune action S19 n'est exécutée

**Diagnostic :**
```
1. Check S19 rules are enabled
   MCS: View S19 configuration
   All rules show "enabled: true"?

2. Check S12 rules detect violation
   MCS: View S12 violations
   Corresponding S5 event generated?

3. Check S19 rule action is valid
   Action func_id exists in S8 commands?

4. Check logs for errors
   Terminal: grep -i "S19" /tmp/smo_simulator.log
```

**Solution :**
```bash
# Reload S19 rules with verbose output
python -m smo_simulator --config configs/eosat1/ --verbose 2>&1 | grep -E "S12|S19|rule"

# Check rule syntax in YAML
python -c "
import yaml
with open('configs/eosat1/monitoring/s19_rules.yaml') as f:
    rules = yaml.safe_load(f)
for rule in rules['s19_rules']:
    print(f\"Rule {rule['ea_id']}: event 0x{rule['event_type']:04x} -> func {rule['action_func_id']}\")
"
```

---

## Scénarios de formation

### Débutant : « Bonjour, satellite » (5 minutes)

**Objectif :** envoyer une première commande et recevoir le rapport de vérification S1

**Étapes :**
1. Démarrer le simulateur (temps réel)
2. Connecter le MCS
3. Envoyer la commande d'écho NOOP S17
4. Observer le rapport d'acceptation S1.1 dans le journal des événements du MCS
5. Interpréter : « le satellite a reçu et accusé réception de ma commande »

**Acquis principal :** cycle de vie S1 du PUS (requête → acceptation → achèvement)

---

### Intermédiaire : « Crise de gestion de la puissance » (30 minutes)

**Objectif :** réagir à une batterie faible

**Mise en place :**
```bash
python -m smo_simulator --config configs/eosat1/ --time-scale 5.0 \
  --scenario configs/eosat1/scenarios/battery_discharge.yaml
```

**Mission :**
1. Attendre l'événement S5.0102 BATTERY_SOC_CRITICAL (SoC < 10 %)
2. Reconnaître la réponse autonome S19 (charge utile éteinte, refroidisseur éteint)
3. Déclencher manuellement un délestage supplémentaire pour stabiliser le SoC
4. Suivre le rétablissement du SoC en phase éclairée
5. Reprendre les opérations normales après la sortie d'éclipse

**Résultats attendus :**
- Comprendre les opérations autonomes S12/S19
- S'exercer au délestage
- Apprendre à établir un bilan de puissance

---

### Avancé : « Campagne de prises de vue » (2 heures)

**Objectif :** planifier et exécuter une mission de prise de vue sur plusieurs passages

**Mission :**
1. Définir 5 cibles de courants océaniques (dans le planificateur)
2. Programmer 5 passages de prise de vue sur 24 heures (en respectant les contraintes de puissance et thermiques)
3. Envoyer les activités TC S11 au satellite
4. Suivre l'exécution automatique (rapports S1, événements S5)
5. Télécharger toutes les images lors des contacts avec les stations sol (S13)
6. Vérifier la qualité des images (RSB, compression, sommes de contrôle)

**Situations à gérer :**
- Le stockage de la charge utile approche 95 % (suspendre les prises de vue)
- Contrainte thermique du FPA (période de refroidissement)
- Dégradation de la marge de liaison (gérer la puissance d'émission)
- Fenêtre de contact avec la station sol (hiérarchiser les téléchargements)

**Résultats attendus :**
- Maîtriser la planification de mission
- Programmation autonome S11
- Transfert de gros volumes de données S13
- Gestion des contraintes thermiques et de puissance

---

### Expert : « Exercice de traitement des anomalies » (3 heures)

**Objectif :** diagnostiquer des défaillances en cascade et assurer la reprise

**Mise en place :**
```bash
python -m smo_simulator --config configs/eosat1/ --time-scale 10.0 \
  --scenario configs/eosat1/scenarios/cascading_fdir.yaml
```

**Pannes injectées :**
1. Senseur stellaire 1 ébloui (5 min après le début du scénario)
2. Survitesse de la roue de réaction 1 (10 min)
3. Surchauffe de la batterie (15 min)
4. Surchauffe du PA du TTC (20 min)

**Tâches de l'opérateur :**
1. Reconnaître chaque panne (interprétation des événements S5)
2. Évaluer la réponse autonome (efficacité des règles S19)
3. Décider d'un éventuel forçage manuel (sécurité contre mission)
4. Exécuter les commandes de reprise
5. Documenter la chronologie et la justification des décisions

**Arbre de défaillances à reconstituer :**
```
Survitesse RW1 (0x0201)
  ├─ Auto : désactiver la roue (règle S19)
  ├─ Manuel : vérifier la saturation du moment cinétique (désaturation préalable parfois nécessaire)
  └─ Reprise : réactiver après refroidissement

ST1 aveuglé (0x0203)
  ├─ Auto : basculer sur ST2 (règle S19)
  ├─ Manuel : si les deux sont aveuglés, mode survie + pointage solaire grossier
  └─ Reprise : attendre que le Soleil se déplace, réacquérir

Surchauffe batterie (0x0109)
  ├─ Auto : réduire les charges chauffantes (charge utile coupée)
  ├─ Manuel : si cela persiste, réduire le biais de vitesse des roues AOCS
  └─ Reprise : refroidissement passif en éclipse

Surchauffe du PA (0x0509)
  ├─ Auto : arrêt du PA (règle S19)
  ├─ Manuel : attendre 3-5 min le refroidissement passif
  └─ Reprise : redémarrer à faible puissance, augmenter progressivement
```

**Résultats attendus :**
- Maîtriser le diagnostic des pannes
- Comprendre les effets en cascade de la FDIR
- S'exercer aux procédures de reprise manuelle
- Gagner en assurance dans le traitement des anomalies

---

## Annexe : référence rapide des commandes courantes

### Commandes les plus rapides (< 1 seconde)

```
S3 subtype 27:  Request one-shot HK
S17 subtype 1:  NOOP echo test
S5 subtype 5:   Enable event type
S8 func 0:      Set AOCS mode
```

### Commandes les plus lentes (> 10 secondes)

```
S8 func 1:      Desaturate wheels (15-25 sec)
S8 func 12:     Attitude acquisition (60+ sec, mode-dependent)
S8 func 47:     Decontamination sequence (5-10 min)
S13 subtype 3:  Large data transfer (block time: 4KB block, ~10 ms)
```

### Commandes les plus critiques (limitantes pour la sécurité)

```
S8 func 0:      Mode transition (power, thermal, attitude checks)
S8 func 25:     Emergency load shedding (cascades to payload, AOCS)
S8 func 43:     FPA cooler control (thermal runaway if misused)
S13 subtype 1:  Transfer initiation (blocks other downlink activities)
```

---

## Séquence LEOP et recette en orbite

### Vue d'ensemble

La séquence de phase de lancement et de début d'orbite (LEOP) et de recette en orbite d'EOSAT-1 mène le satellite de la séparation jusqu'aux opérations nominales en 24 heures environ, sur 16 passages au-dessus des stations sol. Le satellite évolue sur une orbite héliosynchrone d'environ 513 km (altitude moyenne) inclinée à 97,39°, de LTAN ~10:00 (période d'environ 94,5 min, 15,24 révolutions/jour). Le réseau compte cinq stations sol (Iqaluit, Troll, Svalbard, Inuvik, O'Higgins ; manuel 05 §5) ; la chronologie indicative ci-dessous n'en utilise que deux : Troll (Antarctique, −72,012° S) et Iqaluit (Canada, 63,747° N).

### Phases du satellite

Le simulateur modélise 7 phases distinctes du satellite :

| Phase | Nom | SID HK actifs | Description |
|-------|------|----------------|-------------|
| 0 | PRE_SEPARATION | Aucun | Sur le lanceur, tous les systèmes éteints |
| 1 | SEPARATION_TIMER | Aucun | Minuterie de vol balistique de 30 minutes après la séparation |
| 2 | INITIAL_POWER_ON | 11 | L'OBC démarre sur le chargeur d'amorçage |
| 3 | BOOTLOADER_OPS | 11 | Chargeur d'amorçage en fonctionnement, balise uniquement |
| 4 | LEOP | Tous | Logiciel applicatif démarré, TM complète, mémoires en ligne |
| 5 | COMMISSIONING | Tous | Vérification des sous-systèmes en cours |
| 6 | NOMINAL | Tous | Opérations normales |

**Important :** dans les phases 0 à 3, un seul SID minimal est actif : le **SID 11 (balise, 30 s)**, émis depuis l'**APID du chargeur d'amorçage** (0x002), et non depuis l'APID applicatif (0x001). Aucune mémoire de TM n'existe en mode chargeur d'amorçage, il n'y a pas de contrôle d'attitude, et seuls les sous-systèmes EPS, TTC et OBDH sont calculés à chaque pas. Tous les autres SID HK, les quatre mémoires de TM bord, les opérations AOCS, TCS et charge utile, ainsi que le flux de données de l'APID applicatif ne sont mis en service qu'au passage en phase 4 (LEOP), déclenché par un `OBC_BOOT_APP` (func_id 55) réussi. Un redémarrage de l'OBC dans les phases 4 à 6 ramène automatiquement le satellite en BOOTLOADER_OPS (balise uniquement, mémoires supprimées) jusqu'au redémarrage du logiciel applicatif.

### Planning des passages au-dessus des stations sol (lancement depuis Chennai)

La chronologie suivante suppose un lancement depuis Chennai/Sriharikota sur une orbite initiale en arc descendant vers le sud. Troll (Antarctique) obtient le premier contact ; Iqaluit (Arctique) entre en jeu après environ 9 heures.

| Passage | Station | AOS (T+) | Durée | Activité principale |
|------|---------|----------|----------|------------------|
| P1 | Troll | T+00:21 | ~8 min | Surveillance de la séparation, premier signal |
| P2 | Troll | T+01:53 | ~8 min | Amorçage de l'OBC et contrôle initial de l'alimentation |
| P3 | Troll | T+03:25 | ~8 min | Recette de l'EPS et déploiement de l'antenne |
| P4 | Troll | T+04:58 | ~8 min | Recette de l'OBDH |
| P5 | Troll | T+06:34 | ~8 min | Vérification initiale de l'AOCS |
| — | INTERVALLE | 2,5 h | — | Amortissement autonome des vitesses angulaires (pas de contact) |
| P6 | Iqaluit | T+09:04 | ~8 min | Recette de l'AOCS — vérification de l'amortissement |
| P7 | Iqaluit | T+10:36 | ~8 min | Recette de l'AOCS — pointage fin |
| P8 | Iqaluit | T+12:09 | ~8 min | Recette du TCS |
| P9 | Iqaluit | T+13:42 | ~8 min | Mise sous tension de la charge utile |
| P10 | Troll | T+16:03 | ~8 min | Configuration de la charge utile |
| P11 | Troll | T+17:35 | ~8 min | Étalonnage de la charge utile |
| P12 | Iqaluit | T+18:14 | ~8 min | Vérification du pointage fin |
| P13 | Troll | T+19:08 | ~8 min | Essai de liaison descendante à haut débit |
| P14 | Iqaluit | T+19:45 | ~8 min | Armement de la FDIR et essai système |
| P15 | Troll | T+20:40 | ~8 min | Première prise de vue opérationnelle |
| P16 | Iqaluit | T+21:17 | ~8 min | Passage aux opérations nominales |
| P17-19 | — | T+22–24 | — | Réserve pour contingences |

### Séquence nominale de recette en orbite (73 étapes)

#### Passage 1 — surveillance de la séparation (Troll, T+00:21)

**Objectif :** confirmer la séparation, vérifier la balise, établir la liaison bidirectionnelle.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 1 | Attendre l'acquisition de la balise | — | Balise SID 11 reçue sur l'APID 0x002 du chargeur d'amorçage |
| 2 | Écho NOOP S17.1 | — | Acceptation S1.1 |
| 3 | S3.27 demande du SID 11 (balise) | — | OBC actif en chargeur d'amorçage, sw_image=0 |
| 4 | Confirmer l'APID du chargeur d'amorçage (0x002) sur toute la TM | — | Pas encore de trafic sur l'APID applicatif |

**GO/NO-GO :** accrochage de la balise obtenu, écho NOOP reçu.
**Contingence :** en l'absence de balise — vérifier la minuterie de déploiement de l'antenne, contrôler la fréquence TTC. Nouvelle tentative en P2.

#### Passage 2 — amorçage de l'OBC et alimentation initiale (Troll, T+01:53)

**Objectif :** démarrer le logiciel applicatif de l'OBC, activer la télémesure complète, contrôle initial de l'EPS.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 5 | S8.1 OBC_BOOT_APP | 55 | S1.7 terminé, sw_image → 1 |
| 6 | S8.1 OBC_WATCHDOG_ENABLE | 59 | S1.7 terminé |
| 7 | S3.5 activer le SID HK 1 (EPS) | — | Flux de télémesure EPS actif |
| 8 | S3.5 activer le SID HK 4 (OBDH) | — | Flux de télémesure OBDH actif |
| 9 | S3.27 demande du SID 1 (EPS) | — | bat_soc > 70 %, bus_voltage > 30,9 V |
| 10 | S3.27 demande du SID 4 (OBDH) | — | Mode OBC=0 (nominal), reboot_cnt=0 |

**GO/NO-GO :** OBC en mode applicatif, EPS sain (SoC > 60 %, bus > 30,9 V).
**Contingence :** si l'amorçage de l'OBC échoue — S8.1 func_id=56 (BOOT_INHIBIT, inhibit=0), puis nouvelle tentative avec func_id=55. En cas d'échecs répétés, rester en chargeur d'amorçage et faire remonter l'anomalie.

#### Passage 3 — recette de l'EPS et déploiement de l'antenne (Troll, T+03:25)

**Objectif :** vérification complète de l'EPS, déploiement de l'antenne, vérification des générateurs solaires.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 11 | S8.1 TTC_DEPLOY_ANTENNA | 69 | S1.7 terminé, événement S5 |
| 12 | S3.27 demande du SID 6 (TTC) | — | link_margin améliorée |
| 13 | S8.1 EPS_SWITCH_LOAD (ligne 0, allumée) | 22 | Ligne d'alimentation 0 active |
| 14 | S8.1 EPS_SWITCH_LOAD (ligne 1, allumée) | 22 | Ligne d'alimentation 1 active |
| 15 | S3.27 demande du SID 1 (EPS) | — | power_gen > 0 W (phase éclairée) |
| 16 | S8.1 TTC_SET_DATA_RATE (rate=0, LOW) | 65 | S1.7, ttc.tm_data_rate = 16000 bit/s — le palier des opérations de routine |
| 17 | S8.1 TTC_PA_ON | 66 | PA activé, marge de liaison en hausse |

**GO/NO-GO :** antenne déployée, PA allumé, marge de liaison > 6 dB, générateur solaire en production.
**Contingence :** si le déploiement de l'antenne échoue — nouvelle tentative avec func_id=69. Si l'échec persiste, utiliser la voie TTC de secours (func_id=64, transpondeur redondant).

#### Passage 4 — recette de l'OBDH (Troll, T+04:58)

**Objectif :** vérifier la santé de l'OBC, configurer le chien de garde, lancer les diagnostics.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 18 | S8.1 OBC_DIAGNOSTIC | 61 | Rapport de diagnostic nominal |
| 19 | S8.1 OBC_ERROR_LOG | 62 | Aucune erreur critique |
| 20 | S8.1 OBC_SET_WATCHDOG_PERIOD | 58 | Période configurée |
| 21 | S8.1 OBC_SELECT_BUS (bus A) | 54 | Bus CAN A actif |
| 22 | S6.9 contrôle CRC de la mémoire | — | CRC concordant |
| 23 | S3.5 activer le SID HK 2 (AOCS) | — | Flux de télémesure AOCS actif |
| 24 | S3.5 activer le SID HK 3 (TCS) | — | Flux de télémesure TCS actif |

**GO/NO-GO :** OBC sain, aucune erreur mémoire, bus CAN nominal.
**Contingence :** en cas d'erreurs sur le bus CAN — S8.1 func_id=54 (OBC_SELECT_BUS, bus=1) pour basculer sur le bus B. Si les diagnostics échouent — S8.1 func_id=53 (OBC_SWITCH_UNIT) vers l'OBC redondant.

#### Passage 5 — vérification initiale de l'AOCS (Troll, T+06:34)

**Objectif :** mettre sous tension les capteurs d'attitude, lancer l'amortissement des vitesses angulaires.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 25 | S3.27 demande du SID 2 (AOCS) | — | Vitesses angulaires visibles (culbutage) |
| 26 | S8.1 AOCS_SET_MODE (detumble) | 0 | mode=2, changement de mode S5 |
| 27 | S8.1 MTQ_ENABLE | 9 | Magnétocoupleurs actifs |
| 28 | S8.1 ST1_POWER (on) | 4 | Senseur stellaire 1 alimenté |
| 29 | S8.1 ST2_POWER (on) | 5 | Senseur stellaire 2 alimenté |

**GO/NO-GO :** mode d'amortissement actif, vitesses angulaires en baisse, capteurs alimentés.
**Autonome (entre les passages) :** l'amortissement se poursuit de manière autonome pendant environ 2,5 heures jusqu'à P6. Les vitesses angulaires doivent passer d'environ 5 deg/s à moins de 0.5 deg/s.
**Contingence :** si les magnétocoupleurs tombent en panne — compter sur le gradient de gravité pour une stabilisation passive ; faire remonter l'anomalie au passage P6.

#### Passage 6 — recette de l'AOCS : vérification de l'amortissement (Iqaluit, T+09:04)

**Objectif :** vérifier la réussite de l'amortissement, commencer l'acquisition d'attitude.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 30 | S3.27 demande du SID 2 (AOCS) | — | Vitesses angulaires < 1 deg/s |
| 31 | S8.1 AOCS_CHECK_MOMENTUM | 11 | Moment cinétique < 50 Nms |
| 32 | S8.1 AOCS_BEGIN_ACQUISITION | 12 | Séquence d'acquisition lancée |
| 33 | S8.1 AOCS_SET_MODE (coarse sun) | 0 | mode=3, pointage solaire |

**GO/NO-GO :** vitesses angulaires < 1 deg/s, pointage solaire obtenu.
**Contingence :** si les vitesses angulaires restent élevées — S8.1 func_id=1 (DESATURATE), puis relancer l'amortissement. Si les deux senseurs stellaires sont éblouis — utiliser le mode CSS+magnétomètre (mode=3).

#### Passage 7 — recette de l'AOCS : pointage fin (Iqaluit, T+10:36)

**Objectif :** passer en pointage fin, vérifier la précision d'attitude.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 34 | S8.1 ST_SELECT (unit 1) | 6 | Senseur stellaire principal sélectionné |
| 35 | S3.27 demande du SID 2 (AOCS) | — | aocs.mag_enabled (0x025C) = 1 (magnétomètre unique) |
| 36 | S8.1 AOCS_SET_MODE (nadir) | 0 | mode=4, pointage nadir |
| 37 | S3.27 demande du SID 2 (AOCS) | — | att_error < 0.5° |
| 38 | S8.1 AOCS_SET_MODE (fine point) | 0 | mode=5, pointage fin |
| 39 | S8.1 AOCS_SET_DEADBAND | 15 | Bande morte réglée à 0.1° |

**GO/NO-GO :** pointage fin obtenu, att_error < 0.1°, roues équilibrées.
**Contingence :** si l'erreur d'attitude dépasse 1° — revenir au mode nadir, vérifier l'état des senseurs stellaires. S8.1 func_id=13 (GYRO_CALIBRATION) en cas de suspicion de dérive des gyromètres.

#### Passage 8 — recette du TCS (Iqaluit, T+12:09)

**Objectif :** vérifier l'état thermique, configurer les réchauffeurs, préparer la charge utile.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 40 | S3.27 demande du SID 3 (TCS) | — | Toutes les zones dans leur plage |
| 41 | S8.1 HEATER_BATTERY (on) | 40 | Réchauffeur de batterie actif |
| 42 | S8.1 HEATER_OBC (on) | 41 | Réchauffeur de l'OBC actif |
| 43 | S8.1 HEATER_SET_SETPOINT (battery) | 44 | Consigne configurée |
| 44 | S8.1 HEATER_AUTO_MODE (battery) | 45 | Régulation automatique active |
| 45 | S8.1 TCS_GET_THERMAL_MAP | 49 | État thermique complet |
| 46 | S8.1 FPA_COOLER (on) | 43 | Le refroidisseur commence à refroidir le FPA |

**GO/NO-GO :** toutes les zones thermiques nominales, réchauffeurs réactifs, FPA en cours de mise en froid.
**Contingence :** si un réchauffeur reste bloqué — S8.1 func_id=46 (SET_HEATER_DUTY_LIMIT) pour limiter le rapport cyclique. Si le refroidisseur du FPA tombe en panne — reporter la recette de la charge utile, analyser en P10.

#### Passage 9 — mise sous tension de la charge utile (Iqaluit, T+13:42)

**Objectif :** mettre sous tension l'électronique de la charge utile, vérifier la santé du détecteur.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 47 | S3.27 demande du SID 3 (TCS) | — | Température du FPA < -5 °C (refroidi) |
| 48 | S8.1 PAYLOAD_SET_MODE (standby) | 26 | Charge utile en veille |
| 49 | S3.5 activer le SID HK 5 (charge utile) | — | Flux de télémesure charge utile actif |
| 50 | S3.27 demande du SID 5 (charge utile) | — | Température du FPA nominale, stockage correct |
| 51 | S3.5 activer le SID HK 6 (TTC) | — | Flux de télémesure TTC actif |

**GO/NO-GO :** charge utile alimentée, FPA < -5 °C, détecteur réactif.
**Contingence :** si le FPA est trop chaud — attendre le refroidisseur, nouvelle tentative en P10. Si la charge utile ne répond pas — vérifier la ligne d'alimentation EPS (func_id=17), couper puis rétablir l'alimentation.

#### Passage 10 — configuration de la charge utile (Troll, T+16:03)

**Objectif :** configurer les bandes spectrales, les temps d'intégration et la compression.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 52 | S8.1 PAYLOAD_SET_BAND_CONFIG | 33 | Les 4 bandes activées |
| 53 | S8.1 PAYLOAD_SET_INTEGRATION_TIME | 34 | Temps réglés par bande |
| 54 | S8.1 PAYLOAD_SET_GAIN | 35 | Gain nominal |
| 55 | S8.1 PAYLOAD_COOLER_SETPOINT | 36 | Cible -15 °C |
| 56 | S8.1 PAYLOAD_SET_COMPRESSION | 39 | Compression automatique |

**GO/NO-GO :** toutes les bandes configurées, temps d'intégration vérifiés, compression active.
**Contingence :** si le masque de bandes est erroné — renvoyer func_id=33 avec le bon masque. Si les temps d'intégration sont refusés — vérifier les plages de paramètres dans tc_catalog.yaml.

#### Passage 11 — étalonnage de la charge utile (Troll, T+17:35)

**Objectif :** effectuer l'étalonnage par image d'obscurité et par champ plat.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 57 | S8.1 PAYLOAD_START_CALIBRATION | 37 | Séquence d'étalonnage en cours |
| 58 | S3.27 demande du SID 5 (charge utile) | — | Étalonnage en cours |
| 59 | Surveiller les événements S5 | — | Événement CALIBRATION_COMPLETE |
| 60 | S8.1 PAYLOAD_SET_MODE (imaging) | 26 | mode=2, prêt pour la prise de vue |

**GO/NO-GO :** étalonnage terminé, charge utile prête pour la prise de vue.
**Contingence :** si l'étalonnage échoue — S8.1 func_id=38 (STOP_CALIBRATION), puis nouvelle tentative. En cas d'échecs répétés — poursuivre sans étalonnage et le signaler pour analyse au sol.

#### Passage 12 — vérification du pointage fin (Iqaluit, T+18:14)

**Objectif :** vérifier la chaîne de pointage de bout en bout avec la charge utile en fonctionnement.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 61 | S3.27 demande du SID 2 (AOCS) | — | att_error < 0.1° |
| 62 | S8.1 AOCS_SLEW_TO (cible d'essai) | 10 | Basculement terminé |
| 63 | S3.27 demande du SID 2 (AOCS) | — | Nouvelle attitude atteinte |

**GO/NO-GO :** précision de pointage < 0.1° avec la charge utile active.
**Contingence :** si le pointage est dégradé — vérifier le moment cinétique des roues (func_id=11), désaturer si nécessaire (func_id=1).

#### Passage 13 — essai de liaison descendante à haut débit (Troll, T+19:08)

**Objectif :** vérifier la liaison descendante de TM à haut débit, essayer le transfert de gros volumes de données S13.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 63a | S8.1 TTC_SET_DOWNLINK_MODE (on=1) | 79 | ttc.downlink_mode = 1 — la condition de mode pour HIGH |
| 64 | S8.1 TTC_SET_DATA_RATE (rate=1, HIGH) | 65 | ttc.tm_data_rate = 128000 bit/s, ttc.tm_tier = ttc.tm_tier_cmd = 2. Les 10 deg sont une règle sol (le MCS avertit en dessous de 10 deg) ; à bord, HIGH exige l'antenne déployée, le mode DOWNLINK et le mode balise désactivé |
| 65 | S13.1 lancer un transfert d'essai | — | Session de transfert ouverte |
| 66 | S13.3 demander les blocs de données | — | Blocs reçus, CRC correct |
| 67 | S13.5 terminer le transfert | — | Transfert terminé |

**GO/NO-GO :** liaison descendante au débit maximal, aucune erreur de bloc.
**Contingence :** si le TEB est élevé — réduire le débit (func_id=65, rate=0), vérifier la marge de liaison. Si le transfert échoue — recommencer avec une taille de bloc plus petite.

#### Passage 14 — armement de la FDIR et essai système (Iqaluit, T+19:45)

**Objectif :** activer la protection autonome contre les défaillances, armer les règles S12/S19.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 68 | S12 activer toutes les règles de surveillance | — | S12 armé |
| 69 | S19 activer toutes les règles événement-action | — | S19 armé |
| 70 | Écho NOOP S17.1 (contrôle final de la liaison) | — | Écho reçu |

**GO/NO-GO :** toutes les règles FDIR armées, système sain sur l'ensemble des sous-systèmes.
**Contingence :** si l'activation des règles S12/S19 échoue — activer les règles une par une, rechercher des conflits dans event_catalog.yaml.

#### Passage 15 — première prise de vue opérationnelle (Troll, T+20:40)

**Objectif :** acquérir la première image, vérifier la chaîne de prise de vue de bout en bout.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 71 | S8.1 PAYLOAD_CAPTURE | 28 | Événement S5 IMAGING_START |
| 72 | S3.27 demande du SID 5 (charge utile) | — | Image stockée, RSB > 20 dB |

**GO/NO-GO :** image acquise et stockée, RSB acceptable.
**Contingence :** si l'image est corrompue — vérifier la température du FPA, relancer l'étalonnage (func_id=37). En cas de dépassement du délai d'acquisition — vérifier le pointage AOCS, vérifier que le mode de la charge utile est à 2.

#### Passage 16 — passage aux opérations nominales (Iqaluit, T+21:17)

**Objectif :** déclarer les opérations nominales, configuration finale.

| Étape | Commande | func_id | Vérification |
|------|---------|---------|--------------|
| 73 | Instructeur : set_phase 6 (NOMINAL) | — | Phase = NOMINAL |

**GO/NO-GO :** tous les sous-systèmes recettés, toute la FDIR armée, première image acquise.

### Synthèse des procédures de contingence

#### Échec de l'amorçage de l'OBC (blocage en phase 3)
```
1. S8.1 func_id=56 (BOOT_INHIBIT), inhibit=0    — allow auto-boot
2. S8.1 func_id=55 (OBC_BOOT_APP)                — retry boot
3. If fails 3x → S8.1 func_id=53 (OBC_SWITCH_UNIT)  — switch to redundant OBC
4. If both OBCs fail → remain in bootloader, beacon SID 11 only (bootloader APID), escalate
```

#### Échec du déploiement de l'antenne
```
1. Retry S8.1 func_id=69 (TTC_DEPLOY_ANTENNA)    — 2nd attempt
2. S8.1 func_id=64 (TTC_SWITCH_REDUNDANT)         — try backup transponder
3. If no link improvement → rely on dipole antenna (reduced margin)
4. Continue commissioning with low data rate
```

#### Échec de l'amortissement (vitesses angulaires qui ne diminuent pas)
```
1. S3.27 SID 2 → check rates and momentum
2. S8.1 func_id=1 (DESATURATE)                    — manual desaturation
3. S8.1 func_id=9 (MTQ_ENABLE), enable=1          — verify magnetorquers on
4. S8.1 func_id=0, mode=2 (detumble)              — restart detumble
5. If rates still high after 3 passes → safe mode, ground analysis
```

#### Urgence d'alimentation pendant la recette en orbite
```
1. S8.1 func_id=26 (PAYLOAD_SET_MODE), mode=0     — payload off
2. S8.1 func_id=43 (FPA_COOLER), on=0             — cooler off
3. S8.1 func_id=25 (EPS_EMERGENCY_LOAD_SHED), stage=1 — non-critical loads off
4. Wait for eclipse exit, monitor SoC recovery
5. If SoC < 5% → S8.1 func_id=25 (EPS_EMERGENCY_LOAD_SHED), stage=3
6. Resume commissioning when SoC > 30%
```

#### Senseurs stellaires éblouis (les deux unités)
```
1. S8.1 func_id=0, mode=3 (coarse_sun_pointing)   — CSS+mag mode
2. S8.1 func_id=4 (ST1_POWER), on=0               — power off to clear Sun blind
3. Wait 5 minutes
4. S8.1 func_id=4 (ST1_POWER), on=1               — power back on
5. Monitor S5.0204 (ST_RECOVERY) event
6. Resume fine pointing when ST reacquires
```

### Commandes instructeur pour la formation LEOP

Le simulateur permet à l'enseignant de piloter les phases :

```
start_separation    — Begin LEOP from Phase 0 (pre-separation)
set_phase N         — Jump to any phase (0-6)
                      Phase ≤ 3: only SID 11 (Beacon) active on bootloader APID, no stores
                      Phase ≥ 4: application APID, all HK SIDs enabled, stores online
inject_fault NAME   — Inject failure scenario mid-LEOP
set_time_scale N    — Accelerate/decelerate sim time
```

Pour le plan de passages complet et interactif de la recette en orbite, avec visualisation de la chronologie, voir `docs/EOSAT1_Commissioning_Pass_Plan.html`.

---

## Assistance et documentation

- **Référence des services PUS :** `/docs/PUS_SERVICE_REFERENCE.md`
- **Document d'architecture :** `/docs/architecture.md`
- **Journal des modifications :** `/docs/CHANGELOG.md`
- **Configuration :** `/configs/eosat1/`
- **Code du simulateur :** `/packages/smo-simulator/`
- **Code du MCS :** `/packages/smo-mcs/`

---

**Version 1.0 — avril 2026**

Pour tout problème, contacter l'équipe projet EOSAT-1.
