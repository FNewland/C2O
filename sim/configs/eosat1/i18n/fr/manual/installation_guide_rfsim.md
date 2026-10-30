# Guide de démarrage EOSAT-1 — modes avec et sans RF {#eosat-1-startup-guide--rf-and-non-rf-modes}

**Manual-Scope:** system — documentation du système de formation, ne fait pas partie du manuel d'opérations de vol.

**Référence du document :** EOSAT1-UM-START-012
**Édition :** 1.0
**Date :** 2026-04-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Aide-mémoire {#1-quick-reference}

| Mode | Commande | Ports MCS | Simulation RF | Interface radio |
|------|---------|-----------|--------|-----------|
| **Sans RF** (par défaut) | `./start.sh` | TM:8002, TC:8001 | Aucune | Aucune |
| **Mode FRAME** | `SMO_RF_MODE=FRAME ./start.sh` | TM:8012, TC:8011 | Tramage CCSDS + TEB | http://localhost:8094 |
| **Mode RF** | `SMO_RF_MODE=RF ./start.sh` | TM:8012, TC:8011 | Modulation/démodulation BPSK | http://localhost:8094 |

---

## 2. Démarrage sans simulation RF (par défaut) {#2-starting-without-rf-simulation-default}

C'est le mode d'exploitation standard. Les paquets circulent directement entre le
simulateur et le MCS sur TCP, avec un tramage préfixé par la longueur.

```bash
cd /path/to/SpaceMissionSimulation
./start.sh
```

**Services démarrés :**

| Service | URL | Port |
|---------|-----|------|
| Simulateur | http://localhost:8080 | TC:8001, TM:8002, WS:8080 |
| MCS | http://localhost:9090 | HTTP:9090 |
| Planificateur | http://localhost:9091 | HTTP:9091 |
| Visualiseur de TM différée | http://localhost:8092 | HTTP:8092 |
| Outils d'orbite (Orbit Tools) | http://localhost:8093 | HTTP:8093 |

Le MCS se connecte directement aux ports TM (8002) et TC (8001) du simulateur.
Ni surdébit de tramage, ni simulation de canal. Convient pour :
- le déroulé des procédures et la formation ;
- le développement et les essais logiciels ;
- les démonstrations rapides.

---

## 3. Démarrage avec simulation RF (mode FRAME) {#3-starting-with-rf-simulation-frame-mode}

Le mode FRAME insère le tramage de transfert CCSDS entre le simulateur et le MCS.
C'est le mode recommandé pour une formation réaliste au segment sol.

```bash
SMO_RF_MODE=FRAME ./start.sh
```

**Service supplémentaire démarré :**

| Service | URL | Port |
|---------|-----|------|
| Passerelle RF (RF Bridge) | — | TM sortie:8012, TC entrée:8011 |
| Frontal radio | http://localhost:8094 | HTTP:8094 |

**Chemin des données :**
```
Simulateur (TM:8002) → pont RF → mise en trames CCSDS → modèle de canal → MCS (TM:8012)
MCS (TC:8011) → pont RF → codage CLTU → modèle de canal → simulateur (TC:8001)
```

**Ce qu'apporte le mode FRAME :**
- trames de transfert TM avec ASM (0x1ACFFC1D), FECF (CRC-16), canaux virtuels ;
- CLTU de TC avec correction d'erreurs BCH(64,56) ;
- injection d'erreurs binaires configurable, fondée sur Eb/N0 ;
- synchroniseur de trames (machine à états SEARCH → VERIFY → LOCK) ;
- tableau de bord radio web avec diagramme de constellation, indicateurs de verrouillage et graphiques.

**Aucune dépendance supplémentaire** — uniquement du Python pur.

---

## 4. Démarrage avec simulation RF (mode RF) {#4-starting-with-rf-simulation-rf-mode}

Le mode RF ajoute la modulation/démodulation BPSK au mode FRAME.
Il se replie sur un modèle de canal fondé sur numpy si GNU Radio n'est pas installé.

```bash
SMO_RF_MODE=RF ./start.sh
```

Avec GNU Radio installé (facultatif) :
```bash
brew install gnuradio   # macOS
SMO_RF_MODE=RF ./start.sh
```

**Ce qu'apporte le mode RF en plus du mode FRAME :**
- modulation BPSK avec mise en forme d'impulsion RRC (si GNU Radio est disponible) ;
- récupération de porteuse par boucle de Costas + récupération d'horloge M&M ;
- simulation de canal AWGN + Doppler via GNU Radio ou numpy ;
- codage convolutif (rendement 1/2, K=7) + décodage de Viterbi ;
- codage + décodage Reed-Solomon RS(255,223) (correction de 16 symboles).

---

## 5. Passerelle RF autonome (utilisation avancée) {#5-standalone-rf-bridge-advanced}

La passerelle RF peut être lancée indépendamment de `start.sh` :

```bash
# Start simulator first
smo-simulator --config configs/eosat1/ &

# Start RF bridge
smo-rfsim --config configs/eosat1/rfsim.yaml --mode FRAME --radio-web --eb-n0 12.0

# Start MCS pointing at bridge ports
smo-mcs --config configs/eosat1/ --port 9090 --tm-port 8012 --tc-port 8011 &
```

**Options de la ligne de commande :**

| Option | Description |
|--------|-------------|
| `--config` | Chemin de rfsim.yaml |
| `--mode PACKET\|FRAME\|RF` | Mode de fonctionnement |
| `--eb-n0 <dB>` | Forcer la valeur d'Eb/N0 |
| `--radio-web` | Activer le tableau de bord web (port 8094) |
| `--radio-ui` | Activer le tableau de bord en terminal (nécessite `rich`) |
| `-v` | Journalisation détaillée |

---

## 6. Tableau de bord du frontal radio {#6-radio-front-end-dashboard}

Ouvrir http://localhost:8094 en mode FRAME ou RF.

### 6.1 Panneaux d'affichage {#61-display-panels}

| Panneau | Affiche |
|-------|-------|
| Lock Status | Voyants de verrouillage de porteuse, de synchronisation bit et de synchronisation trame ; barre de qualité du signal |
| RF Measurements | RSSI, Eb/N0, TEB, marge de liaison avec bargraphes |
| Dynamics | Doppler, distance, débit, temps de propagation |
| Eb/N0 & BER History | Courbe temporelle glissante sur 120 points |
| Counters | Trames bonnes/mauvaises, CLTU envoyées/acquittées, taux d'erreur trame |
| Frame Rate | Graphique des trames bonnes/mauvaises par seconde |
| Virtual Channels | Voyants d'activité VC0/1/7, cadence des CLTU |
| **BPSK Constellation** | Nuage de points I/Q montrant la qualité des symboles démodulés |
| **Ground Failure Injection** | Liste déroulante pour injecter/effacer des pannes du segment sol |

### 6.2 Diagramme de constellation {#62-constellation-diagram}

Le nuage de points I/Q montre 128 symboles BPSK démodulés. À Eb/N0 élevé,
les symboles se regroupent étroitement autour des points idéaux (+1,0) et (-1,0). À mesure que
la qualité du signal se dégrade, les nuages s'étalent. En cas de perte du verrouillage de la porteuse,
les symboles tournent aléatoirement dans le plan I/Q.

**Lecture de la constellation :**
- nuages serrés à ±1 → bon verrouillage, TEB faible ;
- nuages étalés → Eb/N0 faible, erreurs de trame à prévoir ;
- nuage en rotation → verrouillage de la porteuse perdu ;
- nuage unique à l'origine → aucun signal.

---

## 7. Injection de pannes {#7-failure-injection}

### 7.1 Pannes du segment spatial (via l'interface instructeur du simulateur) {#71-space-segment-failures-via-simulator-instructor}

Elles s'injectent par l'interface instructeur du simulateur à
http://localhost:8080/instructor ou par l'API HTTP :

```bash
# PA overheat (gradual, 300s ramp)
curl -X POST http://localhost:8080/api/command -H 'Content-Type: application/json' \
  -d '{"type":"failure_inject","subsystem":"ttc","failure":"pa_overheat","magnitude":1.0,"onset":"gradual","onset_duration_s":300}'

# High BER (ionospheric interference)
curl -X POST http://localhost:8080/api/command -H 'Content-Type: application/json' \
  -d '{"type":"failure_inject","subsystem":"ttc","failure":"high_ber","magnitude":0.5}'

# Uplink loss
curl -X POST http://localhost:8080/api/command -H 'Content-Type: application/json' \
  -d '{"type":"failure_inject","subsystem":"ttc","failure":"uplink_loss","magnitude":1.0}'

# Receiver degradation
curl -X POST http://localhost:8080/api/command -H 'Content-Type: application/json' \
  -d '{"type":"failure_inject","subsystem":"ttc","failure":"receiver_degrade","magnitude":0.8}'

# Primary transponder failure
curl -X POST http://localhost:8080/api/command -H 'Content-Type: application/json' \
  -d '{"type":"failure_inject","subsystem":"ttc","failure":"primary_failure","magnitude":1.0}'

# Clear a failure
curl -X POST http://localhost:8080/api/command -H 'Content-Type: application/json' \
  -d '{"type":"failure_clear","failure_id":"<id>"}'
```

**Pannes TTC du segment spatial disponibles :**

| Panne | Effet | Amplitude typique |
|---------|--------|-------------------|
| `primary_failure` | Panne du transpondeur A, perte de liaison | 1.0 |
| `redundant_failure` | Panne du transpondeur B | 1.0 |
| `high_ber` | Décalage d'Eb/N0 (brouillage) | 0.1–1.0 (= 1–10 dB) |
| `pa_overheat` | Emballement thermique du PA, arrêt automatique à 70 °C | 0.5–1.0 |
| `uplink_loss` | Signal de liaison montante perdu, aucune commande | 1.0 |
| `receiver_degrade` | Hausse du facteur de bruit RX | 0.1–1.0 (= 0.5–5 dB) |
| `antenna_deploy_failed` | Antenne bloquée, TX inhibé | 1.0 |

### 7.2 Pannes du segment sol (via l'API radio) {#72-ground-segment-failures-via-radio-api}

Elles s'injectent par le tableau de bord radio web ou par l'API sur le port 8094.
Elles dégradent l'Eb/N0 effectif vu par le synchroniseur de trames.

**Par l'interface web :** utiliser le panneau « Ground Segment Failure Injection » —
choisir un type de panne, régler l'amplitude avec le curseur, cliquer sur « Inject ».

**Par l'API :**

```bash
# Inject LNA degradation at 50% magnitude (3 dB penalty)
curl -X POST http://localhost:8094/api/failure/inject \
  -H 'Content-Type: application/json' \
  -d '{"name":"lna_degradation","magnitude":0.5}'

# Inject antenna tracking loss at full magnitude (15 dB)
curl -X POST http://localhost:8094/api/failure/inject \
  -H 'Content-Type: application/json' \
  -d '{"name":"tracking_loss","magnitude":1.0}'

# Clear a specific failure
curl -X POST http://localhost:8094/api/failure/clear \
  -H 'Content-Type: application/json' \
  -d '{"name":"lna_degradation"}'

# Clear all ground failures
curl -X POST http://localhost:8094/api/failure/clear \
  -H 'Content-Type: application/json' -d '{}'

# List available and active failures
curl http://localhost:8094/api/failures
```

**Pannes du segment sol disponibles :**

| Panne | Pénalité max. | Description |
|---------|-------------|-------------|
| `lna_degradation` | 6 dB | Hausse du facteur de bruit de l'amplificateur faible bruit |
| `antenna_mispoint` | 10 dB | Erreur de pointage de l'antenne (dérive des servomécanismes) |
| `feed_loss` | 4 dB | Pertes d'insertion du cornet d'alimentation / du guide d'ondes |
| `rfi_interference` | 8 dB | Un brouillage radioélectrique relève le plancher de bruit |
| `hpa_degradation` | 5 dB | Baisse de la puissance de sortie de l'amplificateur de puissance (liaison montante) |
| `reference_oscillator_drift` | 3 dB | La dérive de l'oscillateur de référence dégrade la démodulation |
| `tracking_loss` | 15 dB | Panne complète du système de poursuite de l'antenne |

L'amplitude va de 0.0 (aucun effet) à 1.0 (pénalité complète). Plusieurs
pannes s'additionnent.

### 7.3 Scénarios combinés {#73-combined-scenarios}

La formation la plus réaliste combine pannes spatiales et pannes sol :

1. **Démarrer la passerelle RF :** `SMO_RF_MODE=FRAME ./start.sh`
2. **Injecter une panne spatiale :** surchauffe du PA via l'interface instructeur
3. **Injecter une panne sol :** dégradation du LNA via la radio
4. **Observer l'effet combiné :** l'Eb/N0 baisse sous l'effet des deux sources
5. **Diagnostiquer :** la radio affiche explicitement les pannes sol ; les pannes spatiales exigent une analyse de la TM
6. **Rétablir :** effacer les pannes sol via la radio ; commander la reprise du satellite via le MCS

---

## 8. Référence de configuration {#8-configuration-reference}

Modifier `configs/eosat1/rfsim.yaml` pour changer les valeurs par défaut :

```yaml
mode: PACKET           # PACKET | FRAME | RF
ccsds:
  tm_frame_length: 1115
  scid: 1
  fecf_present: true
channel:
  eb_n0_db: 10.0       # Baseline Eb/N0 (dB)
  doppler_hz: 0.0
  delay_ms: 3.0
network:
  sim_tm_port: 8002
  sim_tc_port: 8001
  mcs_tm_port: 8012
  mcs_tc_port: 8011
  radio_port: 8094
```

---

## 9. Dépannage {#9-troubleshooting}

| Problème | Cause | Correctif |
|-------|-------|-----|
| Le MCS n'affiche aucune télémesure | MCS connecté aux mauvais ports | S'assurer que le MCS utilise TM:8012, TC:8011 en mode FRAME |
| La radio affiche tous les voyants en rouge | Passerelle non connectée au simulateur | Vérifier que le simulateur tourne sur 8002/8001 |
| La constellation se réduit à une seule tache | Porteuse non verrouillée | Vérifier qu'Eb/N0 > 3 dB, effacer les pannes sol |
| Synchronisation trame bloquée en SEARCH | Trop d'erreurs binaires | Augmenter Eb/N0 ou supprimer les dégradations du canal |
| « smo-rfsim not found » | Paquet non installé | Exécuter `pip install -e packages/smo-rfsim` |
