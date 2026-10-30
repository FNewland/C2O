# Simulateur d'opérations de mission spatiale — Architecture logicielle

**Manual-Scope:** system — documentation du système de formation, ne fait pas partie du manuel d'opérations de vol.

## Synthèse

**SMO** (*Space Mission Operations Simulator*) est un simulateur d'opérations spatiales haute fidélité qui implémente la norme ECSS-E-ST-70-41C (PUS-C) pour la mission EOSAT-1. EOSAT-1 est une plateforme CubeSat 6U conçue pour la surveillance des courants océaniques sur une orbite héliosynchrone d'environ 513 km.

SMO est conçu pour quatre cas d'usage principaux :

1. **Formation des opérateurs** : former les opérateurs de vol dans des phases de mission réalistes (LEOP, opérations nominales, traitement des contingences)
2. **Répétition de la recette en orbite** : exécuter les procédures de mission avant le contact avec le satellite
3. **Validation de la FDIR** : éprouver les algorithmes de détection, d'isolation et de reprise des défauts dans des scénarios maîtrisés
4. **Exercices en Cyber Range** : déployer des simulations isolées pour la formation à la cybersécurité

Le simulateur comprend cinq microservices :
- **Simulateur** (8080) : moteur physique et moteur TC/TM PUS-C
- **MCS** (9090) : centre de contrôle de mission web avec contrôle d'accès par rôle
- **Planificateur** (9091) : planification de mission et programmation des activités
- **Visualiseur de TM différée** (8092) : navigateur de télémesure archivée
- **Outils d'orbite** (8093) : utilitaires de conversion TLE/vecteur d'état

Tous les services sont orchestrés par un point d'entrée unique, un script shell, avec une communication interprocessus fondée sur Redis, et sont conçus pour un déploiement rapide dans des environnements isolés du réseau (*air-gapped*).

---

## Vue d'ensemble de l'architecture du système

### Topologie des microservices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Postes de travail opérateurs                   │
│           (navigateur web, poste fixe, terminal mobile)         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │    MCS       │ │ Planificateur│ │Vis. TM diff. │
        │   (9090)     │ │   (9091)     │ │   (8092)     │
        │   HTTP/WS    │ │   HTTP/WS    │ │   HTTP/WS    │
        └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
               │                │                │
               └────────────────┼────────────────┘
                                │
                   ┌────────────▼────────────┐
                   │                         │
                   │  Bus de messages Redis  │
                   │  (TM/TC/événements)    │
                   │                         │
                   └────────────┬────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
   ┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
   │ Simulateur  │    │ Outils d'orbite │    │  start.sh    │
   │   (8080)    │    │    (8093)       │    │ Gestion proc.│
   │             │    │   HTTP/WS       │    │              │
   │  TC:8001 ◄──┼────┤                 │    └──────────────┘
   │  TM:8002 ──►│    └─────────────────┘
   │  I/F:8003   │
   │  HTTP/WS    │
   └─────────────┘
```

### Spécifications des services

#### **Simulateur (port 8080)**
Moteur de simulation central implémentant l'ECSS-E-ST-70-41C (PUS-C).

**Interfaces réseau :**
- **Liaison montante TC (TCP:8001)** : récepteur de paquets spatiaux CCSDS monothread ; en-tête primaire de 6 octets + en-tête secondaire PUS-C + charge utile de données
- **Liaison descendante TM (TCP:8002)** : flux diffusé multiclient ; paquets temps réel à 1 Hz (nominal) ou à une cadence de pas configurable
- **Interface instructeur (TCP:8003)** : commandes JSON-RPC de pilotage des scénarios (pause/reprise/réinitialisation/injection de défauts)
- **HTTP (8080)** : API REST pour les requêtes d'état et la gestion des scénarios
- **WebSocket (/ws)** : abonnement à la télémesure en temps réel pour le MCS

**Composants principaux :**
- SimulationEngine : orchestrateur à 1 Hz (vitesse configurable de 0,1x à 10x le temps réel)
- ServiceDispatcher : 14 services PUS et plus de 80 identifiants de fonction
- 6 modèles de sous-systèmes : EPS, AOCS, TCS, OBDH, TTC, charge utile
- Gestionnaire FDIR : automatisation multiniveau des réponses aux défauts
- Files de paquets : tm_queue, tc_queue, instr_queue, event_queue

#### **Système de contrôle de mission (port 9090)**
Centre de contrôle de mission web avec une interface d'application monopage.

**Fonctionnalités :**
- Tableau de bord de télémesure en temps réel (8 onglets de sous-systèmes)
- Autorité de commande fondée sur le poste (6 postes de vol)
- Constructeur de télécommandes avec modèles de services PUS-C
- Exécution et suivi des procédures
- Calculateurs de planning des contacts et de bilan de puissance
- Signalisation des événements et des alarmes
- Intégration avec le visualiseur de télémesure archivée

**Protocole :**
- REST HTTP pour l'interrogation de l'état (cadence de 100 ms)
- Abonnement WebSocket au flux de TM du simulateur
- Contrôle d'accès par rôle appliqué à chaque requête

#### **Planificateur de mission (port 9091)**
Outil de programmation des activités et de composition de procédures.

**Responsabilités :**
- Charger, modifier et valider les procédures opérationnelles
- Programmer les TC datées (S11)
- Détection des conflits et optimisation
- Export vers des fichiers de chargement de TC
- Intégration avec la prédiction d'orbite

#### **Visualiseur de télémesure différée (port 8092)**
Navigateur de télémesure archivée pour l'analyse après passage.

**Fonctionnalités :**
- Parcourir les paquets HK par plage horaire et par SID
- Exporter des produits de données CSV/HDF5
- Superposer les événements et les alarmes
- Comparer des scénarios

#### **Outils d'orbite (port 8093)**
Utilitaires TLE/vecteur d'état pour la gestion des éphémérides.

**Capacités :**
- Analyser et valider des jeux de TLE NORAD
- Propager des vecteurs d'état (SGP4)
- Calculer les fenêtres de visibilité des stations sol
- Générer des prédictions de passages

---

## Architecture des paquets

Tous les paquets utilisent le système de construction **hatchling** (pyproject.toml) avec des versions de dépendances figées.

### **smo-common** (bibliothèque partagée)

Protocoles centraux, modèles de données et bibliothèques mathématiques.

**Modules clés :**
- `config.py` : chargement de la configuration YAML (schémas validés par pydantic v2)
- `orbit.py` : enveloppe de propagation SGP4 + calcul du vecteur Soleil
- `codec.py` : codeur/décodeur des en-têtes primaire CCSDS et secondaire PUS-C
- `telemetry.py` : catalogue des paramètres et définitions des paquets HK
- `models.py` : classe abstraite de base SubsystemModel (interface des sous-systèmes)

**Dépendances :**
```
pydantic>=2.0
pyyaml>=6.0
sgp4>=2.20
numpy>=1.24
```

**Points d'entrée :** aucun (bibliothèque uniquement)

### **smo-simulator** (moteur central)

Physique de la simulation du satellite et implémentation des services PUS-C.

**Modules clés :**
- `engine.py` : orchestrateur de la boucle principale SimulationEngine
- `service_dispatcher.py` : 14 services PUS + 80 identifiants de fonction (S1, S2, S3, S5, S6, S8, S9, S11, S12, S13, S15, S17, S19, S20)
- `subsystems/` :
  - `eps_basic.py` : bilan de puissance, générateur solaire, batterie, 8 lignes d'alimentation
  - `aocs_basic.py` : contrôle d'attitude, senseurs stellaires, roues de réaction, GPS
  - `tcs_basic.py` : gestion thermique, commande des réchauffeurs
  - `obdh_basic.py` : gestion bord des données, modèle du processeur
  - `ttc_basic.py` : bilan de liaison des télécommunications, pointage d'antenne
  - `payload_basic.py` : opérations de l'imageur, stockage des données
- `fdir.py` : surveillance bord (S12) + liens événement-action (S19)
- `server.py` : serveur web aiohttp + gestionnaires de sockets TCP
- `scenarios.py` : chargeur de scénarios de mission prédéfinis

**Dépendances :**
```
smo-common
aiohttp>=3.9
```

**Point d'entrée :**
```
[project.scripts]
smo-simulator = "smo_simulator.server:main"
```

### **smo-mcs** (contrôle de mission)

Interface web de contrôle de mission.

**Modules clés :**
- `tm_processor.py` : décodeur du flux HK en temps réel et mise en cache
- `tc_manager.py` : file d'envoi et suivi de l'état des commandes
- `procedure_runner.py` : moteur d'exécution des procédures avec prise en charge des points de reprise
- `archive.py` : stockage des paquets TM et interface de requête
- `web_ui.py` : application HTML monopage (intégrée)
- `server.py` : API REST aiohttp + abonnement WebSocket à la TM

**Dépendances :**
```
smo-common
aiohttp>=3.9
```

**Point d'entrée :**
```
[project.scripts]
smo-mcs = "smo_mcs.server:main"
```

### **smo-planner** (planification de mission)

Programmation des activités et composition de procédures.

**Modules clés :**
- `procedures.py` : définition et validation des procédures
- `scheduler.py` : programmation des commandes datées (intégration S11)
- `conflict_checker.py` : application des contraintes de programmation
- `export.py` : génération des fichiers de chargement de TC

**Dépendances :**
```
smo-common
aiohttp>=3.9
```

**Point d'entrée :**
```
[project.scripts]
smo-planner = "smo_planner.server:main"
```

### **smo-gateway** (relais réseau)

Relais TM/TC inter-segments facultatif pour les déploiements distribués.

**Modules clés :**
- `gateway.py` : relais TCP avec filtrage et limitation de débit
- `routing.py` : correspondance service–hôte

**Dépendances :**
```
smo-common
```

**Point d'entrée :**
```
[project.scripts]
smo-gateway = "smo_gateway.gateway:main"
```

---

## Moteur de simulation

### Boucle principale de SimulationEngine

Située dans `smo_simulator.engine:SimulationEngine`. Elle orchestre le cycle de pas à 1 Hz :

```python
async def tick(dt_sim):
    # 1. Drain instructor commands (pause/resume/reset/inject faults)
    await self._drain_instr_queue()
    
    # 2. Process incoming TeleCommands via ServiceDispatcher
    await self._drain_tc_queue()
    
    # 3. Execute time-tagged TCs from S11 scheduler
    self._execute_scheduled_tcs()
    
    # 4. Propagate orbit state (SGP4)
    orbit_state = self.orbit.advance(dt_sim)
    
    # 5. Update spacecraft phase state machine
    self._tick_spacecraft_phase(dt_sim)
    
    # 6. Tick each subsystem (EPS, AOCS, TCS, OBDH, TTC, Payload)
    for subsystem in self.subsystems:
        subsystem.tick(dt_sim, orbit_state, self.shared_params)
    
    # 7. S12 Parameter Limit Monitoring
    self._tick_s12_monitoring()
    
    # 8. FDIR Detection/Isolation/Recovery
    self._tick_fdir()
    
    # 9. S5 Event Generation and Reporting
    self._check_subsystem_events()
    
    # 10. Contact/Eclipse Transition Detection
    self._check_transitions(orbit_state)
    
    # 11. Emit HK Reports (per SID schedule)
    await self._emit_hk_packets(dt_sim)
    
    # 12. S15 Paced Telemetry Dump
    await self._tick_dump_emission(dt_sim)
    
    # 13. Injected Failure Progression
    self.failure_manager.tick(dt_sim)
```

### Modèle temporel

- **dt_sim** : pas de temps simulé par pas de boucle = `(1.0 / tick_hz) * sim_speed`
- **tick_hz** : configurable (1 Hz par défaut, plage de 0,1 à 100 Hz)
- **sim_speed** : multiplicateur du temps réel (0,1x–10x)

Exemple : avec une cadence de 10 Hz et une vitesse 2x : dt_sim = 0.1 s * 2.0 = 0.2 s/pas

### Mémoire partagée des paramètres

Dictionnaire d'état central indexé par identifiant de paramètre (hexadécimal) :

```
shared_params: dict[int, float] = {
    0x0100: 85.5,      # battery_soc (%)
    0x0110: 28.3,      # battery_voltage (V)
    0x0200: 5,         # aocs_mode (enum)
    0x0240: 1,         # st1_status (online)
    ...
}
```

### Files de paquets

Quatre files asynchrones :
- **tm_queue** : télémesure sortante vers TM:8002 et Redis
- **tc_queue** : télécommandes entrantes depuis TC:8001
- **instr_queue** : commandes instructeur (pause, réinitialisation, injection de défauts)
- **event_queue** : événements système (événements signalés S5)

---

## Implémentation des services PUS-C

ServiceDispatcher achemine toutes les télécommandes entrantes (APID 0x0001) vers 14 services implémentés :

| Service | Nom | Sous-types | Description |
|---------|------|----------|-------------|
| S1 | Vérification des requêtes | 1,2,3,4,5,6,7 | Rapports de succès/échec d'acceptation de TC et d'acceptation + démarrage/progression/achèvement |
| S2 | Accès aux équipements | 1,5,6 | Marche/arrêt des équipements, vérification d'état |
| S3 | Données de servitude | 1,2,25 | Collecte HK par SID, réglage des propriétés, définition des rapports HK |
| S5 | Signalement d'événements | 1,2 | Activation/désactivation du signalement d'événements ; paquets TM d'événements |
| S6 | Gestion de la mémoire | 1,2 | Contrôle et vidage de la mémoire |
| S8 | Gestion des fonctions | 1,2 | Exécution/désactivation de fonctions (plus de 80 identifiants de fonction sur l'ensemble des sous-systèmes) |
| S9 | Gestion du temps | 1,2 | Réglage/rapport du temps bord |
| S11 | Programmation des TC | 4,5 | Insertion/suppression/suppression totale de TC datées |
| S12 | Surveillance bord | 1,2,5 | Définition des limites des paramètres, activation/désactivation de la surveillance, rapport des dépassements de limites |
| S13 | Transfert de gros volumes de données | 1,3 | Lancement/rapport d'une descente segmentée |
| S15 | Stockage bord | 1,2 | Demande/rapport de vidage de TM |
| S17 | Test | 1 | Test de connexion (écho/ping) |
| S19 | Liens événement-action | 1,2 | Définition/suppression de règles autonomes de TC déclenchées par événement |
| S20 | Gestion des paramètres | 2 | Interrogation/rapport de la valeur des paramètres |

### Répartition des fonctions S8

Les identifiants de fonction couvrent sept domaines de sous-systèmes, avec une condition d'autorisation en deux étapes. La liste complète,
générée, est `09_command_reference.md` (à partir de `commands/tc_catalog.yaml`) ; les plages sont les suivantes :

- **AOCS :** 0–15, 84–91, 96 (0 `AOCS_SET_MODE`, 2/3 désactivation/activation de roue, 4/5 alimentation de ST1/ST2, 6 `ST_SELECT` ; la 7 est retirée)
- **EPS :** 16–25, 81–83 (19/20 `EPS_POWER_ON`/`EPS_POWER_OFF`, 81 `EPS_DEPLOY_WING`)
- **Charge utile :** 26–39, 92–95, 119 (26 `PAYLOAD_SET_MODE`, 28 `PAYLOAD_CAPTURE`)
- **TCS :** 40–49 (40 `HEATER_BATTERY`, 41 `HEATER_OBC`, 42 `HEATER_THRUSTER`, 43 `FPA_COOLER`)
- **OBDH :** 50–62, 80 (55 `OBC_BOOT_APP`, 80 `OBC_GPS_TIME_SYNC`)
- **TTC :** 63–79, 97–98 (65 `TTC_SET_DATA_RATE`, 69 `TTC_DEPLOY_ANTENNA`, 97/98 balise UHF)
- **Propulsion :** 108–118 ; alias hérités 100–107 ; 120 `SYS_SET_MISSION_PHASE`

**Condition d'autorité :**

```python
def is_function_authorized(func_id, eps_state, subsys_state):
    # Stage 1: Check EPS power line for target subsystem
    subsys = get_subsystem_for_func(func_id)
    power_line = subsystem_to_power_line(subsys)
    
    if power_line_status(power_line) == OFF:
        return False  # EPS power gated
    
    # Stage 2: Check subsystem mode != MODE_OFF
    # Exception: Equipment management commands (func_ids in {0,2,3,4,5,6,7,9,26})
    #            bypass subsystem mode check (can power on equipment)
    
    if func_id not in EQUIPMENT_MGMT_BYPASS_SET:
        if subsys_state.mode == MODE_OFF:
            return False
    
    return True
```

---

## Modèles des sous-systèmes

Chaque sous-système hérite de `SubsystemModel` (classe de base abstraite de smo-common) et implémente `tick(dt, orbit_state, shared_params)`.

### EPS (sous-système d'alimentation électrique) — `eps_basic.py`

**Variables d'état :**
- Batterie : SoC [0–100 %], tension [23–34 V], courant [±50 A]
- Générateur solaire : 5 panneaux fixés sur la structure + 2 ailes déployables, avec pondération selon l'attitude par rapport au Soleil
- Lignes d'alimentation : 8 voies (5 commutables, 3 non commutables)
- Profil de charge : courant consommé par bus
- Mode thermique : agit sur le rapport cyclique du réchauffeur de batterie

**Physique principale :**
- Projection du vecteur Soleil par panneau : P_gen = P_max * max(0, cos(sun_angle))
- Détection des éclipses à partir d'orbit_state
- Charge/décharge de la batterie : dSoC/dt = (P_in – P_out) / battery_capacity
- Détection de surintensité par ligne d'alimentation : I > I_max → indicateur de défaut
- Cascade de délestage : charges non critiques → charge utile → roues de réaction → réchauffeur de l'OBC

**Conditions de contact :**
- TX TTC autorisé lorsque : solar_array_power > 150 W ET battery_soc > 20 %
- RX TTC autorisé lorsque : battery_soc > 5 %

### AOCS (système de contrôle d'attitude et d'orbite) — `aocs_basic.py`

**Variables d'état :**
- Attitude : quaternion (q0, q1, q2, q3) normalisé
- Vitesses angulaires : ω [°/s] dans le repère satellite
- Erreur de pointage : angles d'Euler par rapport à la cible
- Automate des modes : 10 modes (OFF, SAFE_BOOT, DETUMBLE, COARSE_SUN, NOMINAL, FINE_POINT, SLEW, DESAT, ECLIPSE, INERTIAL ; `aocs/aocs_mode_codes.yaml`)

**Modèles matériels :**
- Senseurs stellaires : 2×, redondance froide ; minuterie d'amorçage proportionnelle à dt_sim ; précision angulaire ±0,05°
- Senseur solaire grossier : 8 voies analogiques ; précision ±3°
- Gyromètres : dérive du biais (~0,1°/h) ; plancher de bruit ~0,01°/s
- Roues de réaction : 4× en configuration tétraédrique ; saturation du moment cinétique ; désaturation par magnétocoupleurs
- Magnétomètre : 1 (sans redondance) ; modèle du champ terrestre
- Récepteur GPS : type de point (0 = aucun, 1 = 2D, 2 = 3D, 3 = 3D + vitesse) ; PDOP [1–10] ; nombre de satellites [0–12]

**Logique du mode DETUMBLE :**
```python
# Detumble via B-dot law (magnetometer feedback)
if mode == DETUMBLE:
    B_prev = magnetometer_measurement(time - dt)
    B_curr = magnetometer_measurement(time)
    dB_dt = (B_curr - B_prev) / dt
    M_desired = -k_bdot * dB_dt  # Magnetic dipole moment
    set_magnetorquer_moment(M_desired)
    
    # Exit condition: angular rate < 5°/s
    if np.linalg.norm(angular_rates) < np.radians(5):
        mode = SUN_SAFE
```

### TCS (sous-système de contrôle thermique) — `tcs_basic.py`

**Variables d'état :**
- Températures des composants : OBC, batterie, FPA, 6 panneaux extérieurs [K]
- Modèle de radiateur : surface rayonnante effective par panneau
- État des réchauffeurs : 3 réchauffeurs (OBC, batterie, roues de réaction) avec rapport cyclique [0–100 %]
- Mode de contact : éclipse ou éclairement

**Bilan thermique :**
```
dT_i/dt = (Q_solar_i + Q_internal_i + Q_heater_i - Q_rad_i) / (m_i * c_p_i)

Q_rad_i = σ * ε * A_rad * (T_i^4 - T_space^4)  # Stefan-Boltzmann
Q_solar_i = α * G_solar * A_panel * cos(sun_angle)
Q_internal_i = P_dissipation(subsystem_activity)
```

**Contraintes :**
- Plage de fonctionnement de l'OBC : 0–50 °C ; activation du mode survie si T > 60 °C
- Plage de la batterie : −20–50 °C ; le réchauffeur s'enclenche si T < 0 °C
- FPA sensible : 0–30 °C optimal ; dégradation au-delà de 35 °C

### OBDH (gestion bord des données) — `obdh_basic.py`

**Variables d'état :**
- Charge du processeur : [0–100 %]
- Occupation mémoire : totale, libre, occupée [octets]
- Compteur de temps de fonctionnement : [secondes]
- Automate des modes : OFF, BOOT, NOMINAL, SAFE
- Image logicielle : version, CRC, indicateur d'amorçage

**Machine à états d'amorçage :**
```
OFF → BOOT (chargeur d'amorçage 30 s) → contrôle du CRC logiciel
     ↓ CRC OK
   NOMINAL ← SAFE (si le mode survie thermique s'est déclenché)
     ↓ charge processeur > 90% pendant 60 s
   SAFE (débit TM réduit, puissance minimisée)
```

**Modèle de mémoire :**
- Totale : 512 Mo (flash) + 128 Mo (RAM)
- Cache des paramètres : 2 ko
- Définitions des SID HK : 3 ko
- Journal des événements : tampon circulaire, 64 ko
- File du programmateur de TC : jusqu'à 100 TC datées

### TT&C (télémesure, poursuite et télécommande) — `ttc_basic.py`

**Variables d'état :**
- Bilan de liaison : RSSI [dBm], état de verrouillage (verrouillé/non verrouillé), débit [kbit/s]
- Modulation : QPSK (4,8 kbit/s), OQPSK (19,2 kbit/s), OQPSK+FEC (76,8 kbit/s)
- Perte de dépointage de l'antenne : plage [0–20 dB] selon l'attitude du satellite par rapport à la station sol
- Synchronisation trame : délai d'acquisition de 10 s ; perte de verrouillage après 2 erreurs de trame consécutives

**Détection des contacts :**
```python
# From orbit_state, compute ground station elevation angle
elevation = compute_elevation(orbit_state, ground_station_latlon)

# TTC transmit enabled if:
#   (1) elevation > 5° (radio horizon)
#   (2) EPS power > 150W (from EPS model)
#   (3) TTC mode != OFF

if elevation > 5:
    contact_active = True
    # Compute link budget (simplified)
    path_loss = -32.5 - 20*log10(range_km) - 20*log10(freq_mhz)
    antenna_gain_gs = 15 dBi
    antenna_gain_sc = 0 + pointing_loss  # Omni, but pointing loss
    RSSI = tx_power + path_loss + antenna_gain_gs + antenna_gain_sc
    lock = (RSSI > threshold_for_modulation)
else:
    contact_active = False
    lock = False
```

### Charge utile (imageur) — `payload_basic.py`

**Variables d'état :**
- Mode de l'imageur : OFF, STANDBY, IMAGING, CALIBRATION
- Nombre d'images : total des images acquises
- Volume de données : [Go] sur l'enregistreur statique
- Taux d'occupation du stockage : [0–100 %]
- Température du FPA : couplée au modèle TCS

**Contraintes opérationnelles :**
- Prise de vue uniquement si : mode = IMAGING ET pointing_error < 0,5° ET satellite éclairé (hors éclipse)
- Débit de génération de données : 2 Go/h pendant la prise de vue
- Stockage max. : 128 Go ; charge utile désactivée si l'occupation dépasse 95 %
- Cycle d'étalonnage : recommandé tous les 7 jours ; met à jour la table d'étalonnage en vol

---

## Architecture de la télémesure

### SID de servitude (S3)

| SID | Sous-système | Cadence | Paramètres |
|-----|-----------|------|-----------|
| 1 | EPS | 1 Hz | SoC, tension et courant de la batterie, puissance solaire par panneau, état des lignes d'alimentation, état du délestage |
| 2 | AOCS | 1 Hz | Quaternion d'attitude, vitesses angulaires, erreur de pointage, mode, vitesses des roues, état des senseurs stellaires, état du GPS |
| 3 | TCS | 1 Hz | Températures des composants, état des radiateurs, rapports cycliques des réchauffeurs, mode thermique |
| 4 | Plateforme | 1 Hz | Phase du satellite, temps de fonctionnement, position/vitesse orbitales, indicateur d'éclipse, passage en contact avec une station sol |
| 5 | Charge utile | 1 Hz | Mode de l'imageur, nombre d'images, volume de données, occupation du stockage, température du FPA |
| 6 | TTC | 1 Hz | RSSI, état de verrouillage, débit, perte de dépointage de l'antenne, élévation du contact, mode de modulation |
| 11 | Balise | toutes les 30 s | SoC de la batterie, mode, temps, synthèse de santé du satellite (descente cadencée pendant le contact) |

### Catalogue des paramètres

Plus de 120 paramètres définis dans `configs/eosat1/telemetry/parameters.yaml`. Exemples d'entrées :

```yaml
parameters:
  0x0100:
    name: battery_soc
    unit: "%"
    min: 0
    max: 100
    scale: 0.1
  0x0110:
    name: battery_voltage
    unit: "V"
    min: 23
    max: 34
    scale: 0.01
  0x0200:
    name: aocs_mode
    unit: "enum"
    values:
      0: OFF
      1: DETUMBLE
      2: SUN_SAFE
      5: FINE_POINTING
  0x0240:
    name: st1_status
    unit: "enum"
    values:
      0: OFFLINE
      1: ONLINE
      2: FAILED
```

### Structures des paquets HK

Définies dans `configs/eosat1/telemetry/hk_structures.yaml` :

```yaml
SID_1_EPS:
  parameters:
    - {param_id: 0x0100, offset: 0, bytes: 1}  # battery_soc
    - {param_id: 0x0110, offset: 1, bytes: 2}  # battery_voltage
    - {param_id: 0x0120, offset: 3, bytes: 2}  # battery_current
    - {param_id: 0x0140, offset: 5, bytes: 1}  # solar_power
    - {param_id: 0x0150, offset: 6, bytes: 1}  # power_line_status (bitmask)
  pack_format: ">BHhBBB"  # struct.pack format
  total_length: 8
```

### Format des paquets TM

```
Décalage     |  Champ                      |  Longueur (octets)
─────────────┼─────────────────────────────┼─────────────────
   0–5       |  En-tête primaire CCSDS     |  6
   6–14      |  En-tête secondaire PUS-C   |  9
   15–(N-1)  |  Données (données HK du SID)|  variable
   N–(N+1)   |  Contrôle d'erreur (CRC)    |  2
```

En-tête primaire : APID (11 bits), compteur de séquence, longueur
En-tête secondaire : version PUS, service, sous-type, temps

---

## Architecture FDIR

### Surveillance bord (S12)

Définitions des limites des paramètres dans `configs/eosat1/monitoring/limits.yaml` :

```yaml
0x0100_battery_soc:  # Parameter ID
  warning_high: 95
  warning_low: 20
  alarm_high: 100
  alarm_low: 5
  action_alarm_low: "LOAD_SHEDDING"
  
0x0110_battery_voltage:
  warning_high: 32.5
  warning_low: 26.0
  alarm_high: 34.0
  alarm_low: 23.5
  action_alarm_low: "SAFE_MODE"
```

À chaque pas HK, comparer tous les paramètres aux seuils ; générer des événements S5 lors des transitions.

### Liens événement-action (S19)

Règles d'injection autonome de TC définies dans `configs/eosat1/monitoring/s19_rules.yaml` (exemple schématique ci-dessous ; voir ce fichier pour le format réel des règles) :

```yaml
event_52:  # Battery SoC Low Alarm
  actions:
    - send_tc: S8.1 func_id=40   # HEATER_BATTERY(on=0)
    - send_tc: S8.1 func_id=26   # PAYLOAD_SET_MODE(mode=0)
    - send_tc: S8.1 func_id=43   # FPA_COOLER(on=0)
  delay_sec: 2
  max_repeat: 1
  
event_61:  # Temperature High Alarm (OBC)
  actions:
    - send_tc: S8.1 func_id=41   # HEATER_OBC(on=0)
    - send_tc: S8.1 func_id=0    # AOCS_SET_MODE(mode=3) COARSE_SUN
  delay_sec: 5
  max_repeat: 3
```

### Gestionnaire FDIR avancé

Stratégie de réponse multiniveau dans `fdir.py` :

```python
def tick_fdir_advanced(dt_sim):
    # Tier 1: Warning thresholds
    for param_id, value in shared_params.items():
        if warning_low <= value <= warning_high:
            log_event(WARNING, param_id)  # S5 event
    
    # Tier 2: Isolation (equipment shutdown)
    for param_id, value in shared_params.items():
        if value > alarm_high or value < alarm_low:
            execute_isolation_procedure(param_id)
            log_event(ALARM, param_id)
    
    # Tier 3: Recovery (mode transition)
    if num_alarms > THRESHOLD:
        transition_to_safe_mode()
        send_event_report(S5.1)
    
    # Tier 4: Emergency (safe mode with minimal load)
    if battery_soc < 5 or any_structural_failure:
        activate_emergency_mode()
```

---

## Schéma de configuration

Arborescence de configuration enracinée dans `configs/eosat1/` :

```
configs/eosat1/
├── mission.yaml               # Spacecraft identity, APID, PUS version
├── orbit.yaml                 # TLE, ground stations (Iqaluit, Troll)
├── subsystems/
│   ├── eps.yaml              # EPS model parameters
│   ├── aocs.yaml             # AOCS initial conditions
│   ├── tcs.yaml              # Thermal constants
│   ├── obdh.yaml             # Processor specs
│   ├── ttc.yaml              # Link budget params
│   └── payload.yaml          # Imager specifications
├── telemetry/
│   ├── parameters.yaml       # 120+ parameter definitions
│   ├── hk_structures.yaml    # SID packet layouts
│   └── event_catalog.yaml    # 100+ event definitions
├── commands/
│   └── tc_catalog.yaml       # TC definitions for all 14 services
├── monitoring/
│   ├── limits.yaml           # S12 parameter thresholds
│   └── event_actions.yaml    # S19 event-action rules
├── mcs/
│   └── positions.yaml        # Role-based access control (func_id ranges)
├── procedures/               # 51 operational procedures
│   ├── leop/
│   ├── nominal/
│   ├── contingency/
│   └── emergency/
├── scenarios/                # 29 pre-configured scenarios
│   ├── scenario_001_detumble.yaml
│   ├── scenario_002_sun_safe.yaml
│   └── ...
└── manual/                   # 14 operator manual sections
    ├── software_architecture.md
    ├── ops_procedures.md
    └── ...
```

### mission.yaml

```yaml
spacecraft:
  name: EOSAT-1
  form_factor: 6U_CubeSat
  dry_mass_kg: 12.0
  apid: 0x0001
  
pus_version: 2  # PUS-C, ECSS-E-ST-70-41C
time_epoch: "2000-01-01T12:00:00"   # J2000

operators:
  flight_director:
    description: "Mission authority; full command access"
  eps_tcs:
    description: "Power and thermal subsystem ops"
  aocs:
    description: "Attitude control and pointing"
  ttc:
    description: "Communications and link budget"
  payload_ops:
    description: "Imager and data collection"
  fdir_systems:
    description: "Fault isolation and recovery"
```

---

## Interface web du MCS

Application monopage (SPA) avec navigation par onglets et abonnement à la télémesure en temps réel.

### Onglets du tableau de bord

1. **Overview** : trace au sol de l'orbite, prédiction des passages, phase du satellite (BOOT/LEOP/NOMINAL), temps de fonctionnement
2. **EPS** : graphique de l'état de charge de la batterie, puissance du générateur solaire par panneau, matrice des commutateurs des lignes d'alimentation, état du délestage
3. **AOCS** : quaternion d'attitude/angles d'Euler, vecteur des vitesses angulaires, erreur de pointage, sélecteur de mode, vitesses des roues de réaction, état des senseurs stellaires (froid/tiède/prêt), position/vitesse GPS
4. **TCS** : télémesure de température (OBC/batterie/FPA/panneaux), rapports cycliques des réchauffeurs, sélecteur de mode thermique
5. **TTC** : courbe temporelle du RSSI, indicateur d'état de verrouillage, sélecteur de débit, tracé de l'élévation pendant le passage
6. **Payload** : sélecteur de mode de l'imageur, nombre d'images, barre d'occupation du stockage, température du FPA
7. **OBDH** : charge du processeur, occupation de la mémoire, version du logiciel, compteur de temps de fonctionnement
8. **Commanding** : constructeur de TC selon le poste avec sélecteur de fonctions S8.1, compositeur de paquets PUS bruts
9. **Procedures** : chargement d'un fichier de procédure opérationnelle, exécution pas à pas, pose de points de reprise, consultation du journal des événements
10. **On-Demand** : planificateur des contacts, calculateur de bilan de puissance, visualiseur des alarmes FDIR
11. **Manual** : documentation opérateur intégrée (14 sections)

### Contrôle d'accès par poste

Sept postes de vol avec des restrictions sur les function_id (`mcs/positions.yaml`) :

```yaml
flight_director:
  allowed_commands: all          # Unrestricted
eps_tcs:
  func_ids_allowed: [16–25, 40–49, 81–83, 100–107]   # EPS + TCS
aocs:
  func_ids_allowed: [0–15, 84–91, 96]   # AOCS only
ttc:
  func_ids_allowed: [63–79]      # TTC only
payload_ops:
  func_ids_allowed: [26–39, 92–95, 119]   # Payload only
fdir_systems:
  func_ids_allowed: [50–62, 80, 97, 98]   # OBDH, GPS time sync, UHF beacon
propulsion:
  func_ids_allowed: [42, 108–118]   # Catbed heater + propulsion
```

### Abonnement WebSocket

Le MCS établit une connexion WS avec le point d'accès `/ws` du simulateur :

```javascript
ws = new WebSocket("ws://localhost:8080/ws");

ws.onmessage = (event) => {
    const tm_packet = JSON.parse(event.data);
    // Parse CCSDS + PUS-C headers
    // Extract parameters from HK data field
    // Update dashboard widgets
};
```

---

## Protocole réseau

### Liaison montante TC (TCP:8001)

Flux brut de paquets spatiaux CCSDS. Le serveur monothread applique un délai d'attente de réception de 1 seconde.

**Format des paquets :**
```
Octets 0–1 :  identifiant de paquet CCSDS (version=0, type=1 [TC], sec hdr flag=1, apid=0x0001)
Octets 2–3 :  contrôle de séquence   (indicateurs de groupage + compteur de séquence)
Octets 4–5 :  longueur des données   (octets après l'en-tête primaire, moins 1)
Octets 6–8 :  en-tête secondaire PUS TC — 3 octets : 0x20 | pus_version, service, subtype
Octets 9–(N-3) :  champ de données du service
Octets (N-2)–(N-1) :  contrôle d'erreur (CRC-16 CCITT)
```

L'en-tête secondaire TC ne porte **aucun** champ de temps (`TC_SEC_HDR_LEN == 3`).

### Liaison descendante TM (TCP:8002)

Diffusion multiclient. Tous les récepteurs connectés reçoivent un flux de paquets identique.

**Format des paquets :** même structure de paquet spatial CCSDS, mais l'en-tête secondaire **TM** PUS
fait **9 octets**, et non 3, car il porte l'horodatage CUC
de bord (`TM_SEC_HDR_LEN == 9` ; voir `manual/12_time_and_clocks.md`) :

```
Octets 0–5 :   en-tête primaire CCSDS (type=0 [TM])
Octet 6 :      0x10 | pus_version
Octet 7 :      service
Octet 8 :      subtype
Octets 9–12 :  CUC coarse (uint32 BE, secondes depuis J2000)
Octets 13–14 : CUC fine   (uint16 BE, unités de 1/65536 s)
Octets 15–(N-3) :  champ de données du service
Octets (N-2)–(N-1) :  contrôle d'erreur (CRC-16 CCITT)
```

Le champ de données commence donc à l'offset **15**, et non 13 : tout ce qui
codait en dur l'ancienne disposition CUC en secondes entières est faux. Utiliser
`smo_common.protocol.ecss_packet.decommutate_packet()` ou `TM_SEC_HDR_LEN`.

**Débit de sortie :**
- Nominal : 1 paquet HK/s par SID à une cadence de pas de 1 Hz
- Balise (SID 11) : un paquet toutes les 30 s
- Vidage cadencé (S15) : débit de vidage configurable (p. ex. 50 kbit/s)

### Interface instructeur (TCP:8003)

Commandes JSON-RPC de pilotage des scénarios.

**Exemples de commandes :**
```json
{"method": "pause", "params": {}}
{"method": "resume", "params": {}}
{"method": "reset", "params": {"scenario": "scenario_001"}}
{"method": "inject_fault", "params": {"subsystem": "eps", "fault_type": "battery_disconnect"}}
{"method": "set_sim_speed", "params": {"speed": 2.0}}
```

### REST HTTP (port 8080)

```
GET  /api/state                   → Current spacecraft state (JSON)
GET  /api/orbits                  → Ephemeris query
POST /api/tc/send                 → Submit TC (raw bytes)
GET  /api/scenarios               → List pre-loaded scenarios
POST /api/scenarios/{id}/load     → Load scenario
GET  /api/hk/{sid}                → Query HK by SID
GET  /api/events                  → Event log
```

### WebSocket (/ws)

Abonnement à la TM en temps réel (paquets HK encodés en JSON).

---

## Architecture des tests

**Suite de tests :** 64 fichiers de test, environnement pytest + pytest-asyncio.

**Domaines couverts :**
- Tests unitaires : chaque modèle de sous-système (6 modules × 4–6 tests chacun)
- Tests d'intégration : recette en orbite de bout en bout (LEOP → contact nominal)
- Tests de répartition des services : les 14 services PUS (plus de 80 identifiants de fonction)
- Synchronisation du MCS : ingestion de la TM en temps réel et mise à jour du tableau de bord
- Chargement des scénarios : 29 missions préconfigurées
- Logique FDIR : évaluation des règles événement-action

**Exemple de test :**
```python
@pytest.mark.asyncio
async def test_eps_load_shedding_on_low_battery():
    """S12 alarm → S8.1 load shedding TC injection via S19 event-action."""
    engine = SimulationEngine(scenario="battery_discharge")
    
    # Simulate 3 hours of eclipse
    for _ in range(3 * 3600):
        await engine.tick()
    
    # Verify battery SoC < 5%
    assert engine.shared_params[0x0100] < 5
    
    # Verify S19 triggered load shedding
    tc_queue_cmds = engine.tc_queue.get_all()
    assert any(tc.service == 8 and tc.func_id == 17 for tc in tc_queue_cmds)
```

---

## Modes de déploiement

### Autonome (hôte unique)

Tous les services sur localhost via `start.sh` :

```bash
./start.sh  # Launches:
#  - smo-simulator on 8080
#  - smo-mcs on 9090
#  - smo-planner on 9091
#  - Delayed TM Viewer on 8092
#  - Orbit Tools on 8093
#  - Redis (if not running)
```

**Cas d'usage :** formation, développement, répétition de la recette en orbite.

### Distribué (plusieurs hôtes)

smo-gateway permet le relais TM/TC entre segments de réseau.

**Topologie :**
```
[TC Generator] → [Gateway:8001] → [Simulator:8001]
[Simulator:8002] → [Gateway:8002] → [MCS:8002 multi-cast]
```

**Configuration :**
```yaml
gateway:
  listen_tc_port: 8001
  forward_tc_to: simulator_host:8001
  listen_tm_port: 8002
  forward_tm_to: [mcs_host:8002, backup_mcs_host:8002]
```

**Cas d'usage :** centres de contrôle géographiquement séparés (principal + secours).

### Cyber Range (isolé du réseau)

Déploiement isolé avec des paquets wheel hors ligne.

**Construction :**
```bash
pip install --offline smo-common*.whl smo-simulator*.whl smo-mcs*.whl
python -m venv /cyberrange/smo
source /cyberrange/smo/bin/activate
./start.sh --data-root /cyberrange/data
```

**Cas d'usage :** formation à la cybersécurité sans connectivité réseau.

### Développement (installations modifiables)

Pour itérer rapidement :

```bash
pip install -e ./smo-common
pip install -e ./smo-simulator
pip install -e ./smo-mcs
```

**Avantages :** les modifications du code sont prises en compte immédiatement (pas de reconstruction) ; intégration avec pytest.

---

## Conclusion

Le simulateur d'opérations de mission spatiale offre une architecture modulaire et haute fidélité pour la formation aux opérations satellite et la validation de mission. Sa conception en microservices, son implémentation complète de PUS-C et son schéma de configuration riche permettent de composer et de déployer rapidement des scénarios dans des environnements opérationnels variés.

Principaux atouts de l'architecture :
1. **Séparation des responsabilités** : physique (simulateur), interface (MCS), planification (planificateur), réseau (passerelle)
2. **Conformité aux normes** : implémente l'ECSS-E-ST-70-41C (PUS-C) et le format de paquet spatial CCSDS
3. **Extensibilité** : la classe de base SubsystemModel permet d'implémenter des sous-systèmes sur mesure
4. **Testabilité** : suite de tests complète avec pytest-asyncio pour la validation asynchrone
5. **Déployabilité** : lancement par une seule commande via start.sh ; mode Cyber Range isolé pris en charge

---

**Version du document :** 1.0  
**Dernière mise à jour :** 2026-04-09  
**Responsable de l'architecture :** équipe de développement SMO
