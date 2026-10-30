# Référence des services PUS — simulateur du satellite EOSAT-1 {#pus-service-reference--eosat-1-spacecraft-simulator}

**Conformité à la norme ECSS-E-ST-70-41C**

Ce document constitue une référence complète de tous les services PUS (*Packet Utilization Standard*, norme d'utilisation des paquets) mis en œuvre dans le simulateur EOSAT-1. Il vous permet de comprendre comment commander le satellite et interpréter les réponses en télémesure.

---

## Table des matières {#table-of-contents}

1. [Vue d'ensemble des services](#service-overview)
2. [Service 1 : vérification des requêtes](#service-1-request-verification)
3. [Service 2 : accès aux équipements](#service-2-device-access)
4. [Service 3 : données de servitude](#service-3-housekeeping)
5. [Service 5 : signalement d'événements](#service-5-event-reporting)
6. [Service 6 : gestion de la mémoire](#service-6-memory-management)
7. [Service 8 : gestion des fonctions](#service-8-function-management)
8. [Service 9 : gestion du temps](#service-9-time-management)
9. [Service 11 : programmation des activités](#service-11-activity-scheduling)
10. [Service 12 : surveillance bord](#service-12-on-board-monitoring)
11. [Service 13 : transfert de gros volumes de données](#service-13-large-data-transfer)
12. [Service 15 : stockage de la TM](#service-15-tm-storage)
13. [Service 17 : test de connexion](#service-17-connection-test)
14. [Service 18 : procédures de contrôle bord](#service-18-on-board-control-procedures)
15. [Service 19 : événement-action](#service-19-event-action)
16. [Service 20 : gestion des paramètres](#service-20-parameter-management)

---

## Vue d'ensemble des services {#service-overview}

| Service | Sous-types mis en œuvre (TC → TM) | Rôle | Sous-systèmes |
|---------|-------------------------------|---------|-----------|
| S1 | (TM seulement) 1, 2, 3, 4, 5, 6, 7, 8 | Rapports d'acceptation et d'exécution des commandes | Tous |
| S2 | 1, 5, 6 → 6 | Marche/arrêt bas niveau des équipements + rapport d'état | EPS, AOCS, TCS, TTC, OBDH, charge utile |
| S3 | 1, 2, 3, 4, 5, 6, 27, 31 → 25 | Collecte périodique de données de télémesure | Tous |
| S5 | 5, 6, 7, 8 → 1, 2, 3, 4 | Génération autonome d'événements | Tous |
| S6 | 2, 5, 9 → 6, 10 | Vidage, chargement et vérification de la mémoire bord | OBDH |
| S8 | 1 (func_id 0–98, 100–120) → — | Exécution directe de fonctions et de commandes | Tous |
| S9 | 1, 2 → 2 | Synchronisation et corrélation du temps bord | OBDH, TTC |
| S11 | 4, 7, 9, 11, 13, 17 → 5, 18 | Programmation temporelle des télécommandes | OBDH |
| S12 | 1, 2, 3, 4, 6, 7, 12 → 9, 10, 13 | Surveillance de seuils de paramètres | Tous |
| S13 | 1, 3, 5, 9 → 2, 4, 10 | Transmission de données par blocs (images) | Charge utile |
| S15 | 1, 2, 9, 11, 13 → 14 | Gestion du stockage de la télémesure | OBDH |
| S17 | 1 → 2 | Test de connexion, validation de la liaison | TTC |
| S18 | 1, 2, 3, 4, 6 → 7 | Procédures de contrôle bord (OBCP) | OBDH |
| S19 | 1, 2, 4, 5, 8 → 128 | Réponse autonome déclenchée par un événement | Tous |
| S20 | 1 (écriture), 3 (lecture) → 2 (rapport) | Écriture de paramètres / lecture à la demande. **L'allocation des sous-types s'écarte de l'ECSS — voir le service 20** | Tous les sous-systèmes |

Les sous-types 3/4 de S3 sont des alias historiques des sous-types ECSS 5/6 (activation/désactivation de la HK périodique) ;
S3.1/S3.2 créent et suppriment un SID personnalisé. Les sous-types 7/8 de S5 sont des raccourcis
« tout activer » et « tout désactiver ».

La liste de référence est `ServiceDispatcher.dispatch()` dans
`packages/smo-simulator/src/smo_simulator/service_dispatch.py` ; tout service ou
sous-type absent du tableau ci-dessus est ignoré sans signalement par l'OBC (journalisé au niveau DEBUG,
sans rejet S1.2).

---

## Service 1 : vérification des requêtes {#service-1-request-verification}

**Rôle :** fournir les rapports d'acceptation, d'état d'exécution et d'achèvement des commandes.

**Sous-types :**

| Sous-type | Sens | Description |
|---------|-----------|-------------|
| TC 1 | TC → — | Demande de rapport (demande de rapport d'acceptation) |
| TC 2 | TC → — | Demande de rapport (demande de rapport d'échec d'exécution) |
| TM 1 | — → TM | Rapport d'acceptation (commande acceptée par le bord) |
| TM 2 | — → TM | Échec d'acceptation (commande rejetée) |
| TM 3 | — → TM | Rapport de début d'exécution |
| TM 4 | — → TM | Échec du début d'exécution (l'exécution de la commande a échoué) |
| TM 5 | — → TM | Avancement de l'exécution (étape N sur M) |
| TM 7 | — → TM | Fin d'exécution (commande terminée) |

**Exemple de cycle de vie :**

```
Ground sends S8 command (SET_AOCS_MODE)
  ↓
Spacecraft S1.1: Acceptance report (request_id=1234)
  ↓
Spacecraft S1.3: Execution start (request_id=1234)
  ↓
Spacecraft S1.5: Progress (request_id=1234, step=1/3)
  ↓
Spacecraft S1.5: Progress (request_id=1234, step=2/3)
  ↓
Spacecraft S1.5: Progress (request_id=1234, step=3/3)
  ↓
Spacecraft S1.7: Execution complete (request_id=1234, result=OK)
```

**Traitement des erreurs :**

Si la commande est rejetée à l'acceptation :
```
Ground sends invalid S8 command
  ↓
Spacecraft S1.2: Acceptance failure (request_id=1234, error_code=0x0001)
```

Si la commande démarre mais échoue en cours d'exécution :
```
Spacecraft S1.3: Execution start (request_id=1234)
  ↓
[Error occurs during execution]
  ↓
Spacecraft S1.4: Execution failure (request_id=1234, error_code=0x0005)
```

### Rapports d'échec et notice d'échec (défaut n° 87) {#failure-reports-and-the-failure-notice-defect-87}

L'ECSS-E-ST-70-41 autorise un rapport d'échec S1 à porter un champ de données
**notice d'échec** (*failure notice*) après le code d'échec. EOSAT-1 utilise cet emplacement pour la
raison lisible que le logiciel de bord a produite en refusant la commande. Avant l'existence de ce champ,
`ttc_basic._tier_permission_error` rédigeait une excellente raison (« TM rate
is forced to the beacon tier in beacon mode (LOW refused) »), le répartiteur
la stockait, et le S1.8 n'empaquetait que le code — l'opérateur ne voyait donc qu'un
`1,8` nu avec un nombre, sans aucun moyen de savoir lequel des nombreux verrous partageant le code
`0x0007` s'était déclenché.

**Format sur la liaison.** La notice est `reason_len(uint8) + reason(UTF-8)`, ajoutée
**strictement après** les champs historiques. Elle est entièrement omise lorsqu'il n'y a
pas de raison, et tronquée à **160 octets** (jamais au milieu d'un caractère) lorsqu'elle est plus longue.

| Rapport | Format sur la liaison |
|--------|-------------|
| TM 1,1 / 1,7 | `request_id(u32)` |
| TM 1,2 échec d'acceptation | `request_id(u32) + error_code(u16) [+ reason_len(u8) + reason]` |
| TM 1,4 échec du début d'exécution | `request_id(u16) + error_code(u16) [+ reason_len(u8) + reason]` |
| TM 1,8 échec d'exécution | `request_id(u32) + error_code(u16) [+ reason_len(u8) + reason]` |
| TM 1,3 | `request_id(u16)` |
| TM 1,5 | `request_id(u16) + step(u8)` |

1,4 conserve un identifiant de requête sur **16 bits**, car c'est ce que
`ServiceDispatcher.generate_s1_exec_fail` a toujours émis ; 1,2 et 1,8 conservent
la forme sur 32 bits `((apid & 0x7FF) << 14) | (seq & 0x3FFF)` construite par
`TMBuilder`. Les deux formats sont décodés par
`smo_common.protocol.pus_services.VerificationData.parse`.

**Rétrocompatibilité.** Comme la notice est ajoutée après les champs
fixes, un analyseur qui ne lit que `>IH` (1,2 / 1,8) ou `>HH` (1,4) n'est
pas affecté et continue de fonctionner face à un satellite qui en envoie une. De même, un
segment sol qui lit la notice gère un satellite qui n'en envoie aucune —
le champ est simplement décodé comme absent (chaîne vide).

**Codes d'échec.** Le vocabulaire est
`smo_common.protocol.pus_services.FAILURE_CODES`, partagé par le répartiteur
de bord et le MCS afin que les deux ne puissent pas diverger :

| Code | Signification |
|------|---------|
| `0x0001` | Échec générique / service inconnu |
| `0x0002` | Sous-type inconnu |
| `0x0003` | Paramètre ou longueur de données invalide |
| `0x0004` | Sous-système non alimenté ou injoignable |
| `0x0005` | Invalide dans le mode courant |
| `0x0006` | Non autorisé sous le chargeur d'amorçage |
| `0x0007` | Non autorisé dans l'état courant |

Le service 6 réutilise les codes bas avec des significations propres à la mémoire
(`MEMORY_FAILURE_CODES` : adresse illégale, protégée en écriture, argument erroné,
longueur dépassée) — voir le [service 6](#service-6-memory-management).

Le code seul est volontairement insuffisant : plusieurs verrous distincts partagent
`0x0007`, et c'est précisément pourquoi la notice existe. **Lisez la notice, pas le
numéro.**

**Événement.** Chaque refus — à l'acceptation *ou* à l'exécution — lève aussi
l'événement S5 `0x030B COMMAND_REJECTED` (gravité MEDIUM), dont le texte auxiliaire
porte l'identité de la commande (`S8.1 func 65`), le code d'échec et la même
raison. Il apparaît donc dans le journal des événements, la mémoire d'alarmes de bord et
le journal FDIR du MCS, et pas seulement sur la ligne de vérification que l'opérateur
ne surveille peut-être pas. `TC(5,6)` avec le type d'événement 2 le supprime si un scénario
de formation exige de faire taire ce bruit.

---

## Service 2 : accès aux équipements {#service-2-device-access}

**Rôle :** mettre en marche et arrêter des équipements de bord individuels, en deçà du niveau
des commandes de fonction des sous-systèmes (service 8), et relire leur état. C'est
ce qu'utilise un opérateur pour couper l'alimentation d'une unité précise — une surveillance S12 dont l'équipement
source est éteint est neutralisée au lieu de lever une alarme de limite intempestive.

**Sous-types :**

| Sous-type | Sens | Signification | Format sur la liaison |
|---------|-----------|---------|-------------|
| 1 | TC | Distribuer marche/arrêt | `device_id (uint16) + state (uint8)` |
| 5 | TC | Distribuer marche/arrêt avec vérification → TM(2,6) | `device_id (uint16) + state (uint8)` |
| 6 | TC | Rendre compte de l'état marche/arrêt → TM(2,6) | `device_id (uint16)` |
| 6 | TM | Rapport d'état d'équipement | `device_id (uint16) + state (uint8)` |

**Plages d'identifiants d'équipement** (`ServiceDispatcher._set_device_state`) : 0x0100–0x010F EPS,
0x0200–0x021F AOCS, 0x0300–0x030F TCS, 0x0400–0x040F TT&C, 0x0500–0x050F OBDH,
0x0600–0x060F charge utile. Les entrées `S2_*` du catalogue nomment les équipements livrés.

Les sous-types 2 et 3 (chargement / vidage de registres) sont **déclarés dans le commentaire
du code source mais non mis en œuvre** — ils sont acceptés et ignorés.

---

## Service 3 : données de servitude {#service-3-housekeeping}

**Rôle :** demander ou recevoir des données de télémesure périodiques (rapports HK).

**Structures :**

| SID | Nom | Période | Paramètres | Sous-système |
|-----|------|----------|------------|-----------|
| 1 | HK_EPS | 1 s | Batterie, générateur solaire, bus, puissance | EPS |
| 2 | HK_AOCS | 4 s | Attitude, vitesses angulaires, roues, capteurs | AOCS |
| 3 | HK_TCS | 60 s | Température par zone | TCS |
| 4 | HK_OBDH | 8 s | Mode de l'OBC, mémoire, CPU, CAN | OBDH |
| 5 | HK_Payload | 8 s | Température du FPA, stockage, compression | Charge utile |
| 6 | HK_TTC | 8 s | Marge de liaison, température de l'amplificateur de puissance, état de verrouillage | TTC |
| 11 | Beacon | 30 s | Balise condensée de l'état de santé du satellite — la SEULE HK émise en mode chargeur d'amorçage (phase ≤ 3), issue de l'APID du chargeur d'amorçage 0x002 | Chargeur d'amorçage / tous |

**Contrat de télémesure en mode chargeur d'amorçage :** tant que l'OBC exécute le chargeur d'amorçage (phases 0–3), seul le SID 11 est actif, émis depuis l'APID distinct du chargeur d'amorçage (0x002 par défaut). Les SID 1–6 n'apparaissent qu'une fois le logiciel applicatif démarré (phase ≥ 4) et sont émis depuis l'APID applicatif (0x001). Les opérateurs au sol doivent s'attendre à voir le trafic basculer de l'APID 0x002 → 0x001 : c'est le signe visible d'un démarrage réussi de l'application de l'OBC. Un redémarrage imprévu de l'OBC ramène automatiquement le satellite en mode chargeur d'amorçage, et le trafic revient à l'APID 0x002 / SID 11 seulement.

**Commandes :**

### S3 sous-type 27 — Demander un rapport HK ponctuel {#s3-subtype-27--request-one-shot-hk-report}
```
Paramètre : SID (identifiant de structure, uint16)
Exemple : demander HK_EPS (SID=1)
Réponse : rapport HK de 35 paramètres (SoC batterie, tension, courant, etc.)
```

### S3 sous-type 5 — Activer la HK périodique {#s3-subtype-5--enable-periodic-hk}
```
Paramètre : SID (identifiant de structure, uint16)
Intervalle par défaut : 4 secondes
Réponse : rapports HK émis toutes les 4 s jusqu'à désactivation
```

### S3 sous-type 6 — Désactiver la HK périodique {#s3-subtype-6--disable-periodic-hk}
```
Paramètre : SID (identifiant de structure, uint16)
Réponse : l'émission HK s'arrête (réactivable par S3.5)
```

### S3 sous-type 31 — Modifier la période HK {#s3-subtype-31--change-hk-interval}
```
Paramètres : SID (uint16), interval_s (float32)
Exemple : passer l'intervalle de HK_AOCS à 2 secondes
Réponse : rapports HK désormais émis toutes les 2 s
Plage valide : 1 — 3600 secondes
```

**Exemples de paramètres HK :**

**Structure EPS (SID=1) :**
```
eps.bat_voltage        [V]      Battery voltage (nominal 28.5V)
eps.bat_soc            [%]      Battery state of charge (0-100%)
eps.bat_temp           [C]      Battery temperature (-5 to +50°C)
eps.bus_voltage        [V]      Main bus voltage (27-35V nominal)
eps.power_gen          [W]      Total solar power generation
eps.power_cons         [W]      Total power consumption
eps.load_shed_stage    [0-3]    Current load shedding stage
eps.power_margin_w     [W]      Generation - consumption
```

**Structure AOCS (SID=2) :**
```
aocs.att_q1, q2, q3, q4  [—]    Attitude quaternion (xyzw)
aocs.rate_roll/pitch/yaw [deg/s] Angular velocity
aocs.rw1/2/3/4_speed     [RPM]  Reaction wheel speeds
aocs.mode                 [0-9]  AOCS mode (0=off, 1=safe_boot, etc.)
aocs.total_momentum       [Nms]  System angular momentum
aocs.att_error           [deg]  Pointing error magnitude
```

**Structure TTC (SID=6) :**
```
ttc.link_margin        [dB]   Eb/N0 value (link quality)
ttc.pa_temp            [C]    Power amplifier temperature
ttc.carrier_locked     [0/1]  Carrier lock status
ttc.bit_sync_locked    [0/1]  Bit synchronization status
ttc.frame_sync_locked  [0/1]  Frame synchronization status
ttc.ber                [—]    Bit error rate (1e-6 to 1e-4)
```

---

## Service 5 : signalement d'événements {#service-5-event-reporting}

**Rôle :** signaler les événements autonomes du satellite (alarmes, changements d'état, anomalies de capteurs).

**Catégories d'événements :**

| Catégorie | Plage d'ID | Exemples | Gravité |
|----------|----------|----------|----------|
| Orbite | 0x0001-0x001F | AOS, LOS, entrée/sortie d'éclipse | INFO |
| EPS | 0x0100-0x011F | Avertissement de SoC, sous-tension du bus, délestage | INFO à HIGH |
| AOCS | 0x0200-0x02FF | Changement de mode, survitesse de RW, ST aveuglé | INFO à HIGH |
| TCS | 0x0400-0x04FF | Alarmes de température, réchauffeur bloqué | INFO à HIGH |
| TTC | 0x0500-0x05FF | Marge de liaison, thermique de l'amplificateur de puissance, perte de verrouillage | INFO à HIGH |
| OBDH | 0x0300-0x03FF | Redémarrage, erreur mémoire, défaillance de bus | INFO à HIGH |
| Charge utile | 0x0600-0x06FF | Thermique du FPA, stockage plein, erreur de somme de contrôle | INFO à HIGH |
| FDIR | 0x0F00-0x0F0B | Panne détectée, reprise lancée | INFO à HIGH |

**Exemples d'événements :**

```
0x0101: BATTERY_SOC_WARNING
  Severity: MEDIUM (yellow alert)
  When: Battery SoC drops below 20%
  Action: Reduce non-critical loads (via S19)

0x0201: RW_OVERSPEED
  Severity: MEDIUM (yellow alert)
  When: Reaction wheel speed exceeds ±5000 RPM
  Action: Disable overspeed wheel or trigger desaturation

0x0401: TCS_OVERTEMP_ALARM
  Severity: HIGH (red alert)
  When: Thermal zone exceeds alarm threshold (e.g., FPA > -3°C)
  Action: Payload off (via S19)

0x0501: CARRIER_LOCK_LOST
  Severity: MEDIUM (yellow alert)
  When: Downlink carrier lock lost
  Action: Increase TX power (via S19)
```

**Commandes :**

### S5 sous-type 5 — Activer un type d'événement {#s5-subtype-5--enable-event-type}
```
Paramètre : event_id (uint16)
Exemple : activer RW_OVERSPEED (0x0201)
Réponse : des paquets S5 seront générés lorsqu'une survitesse de roue est détectée
```

### S5 sous-type 6 — Désactiver un type d'événement {#s5-subtype-6--disable-event-type}
```
Paramètre : event_id (uint16)
Exemple : désactiver BATTERY_SOC_WARNING (0x0101)
Réponse : aucun paquet S5 ne sera généré pour cet événement
```

**Format du paquet d'événement :**
```
En-tête primaire (PUS)
Horodatage [8 octets] : secondes UTC + microsecondes
Identifiant d'événement [2 octets] : identifiant unique de l'événement
Type d'événement [1 octet] : 0=INFO, 1=WARNING, 2=ALARM, 3=CRITICAL
Message [0-256 octets] : données facultatives propres à l'événement
```

---

## Service 6 : gestion de la mémoire {#service-6-memory-management}

**Rôle :** charger, vider et vérifier la mémoire de bord (SRAM, EEPROM).

**Commandes :**

### S6 sous-type 2 — Charger la mémoire {#s6-subtype-2--load-memory}
```
Paramètres :
  memory_id [0=SRAM, 1=EEPROM]
  address [uint32, octets depuis le début]
  data [longueur variable]
Exemple : charger 256 octets de correctif logiciel en EEPROM à partir de 0x8000
Réponse : rapport de vérification S1
Limites : implémentation simplifiée, pas de CRC par bloc
```

### S6 sous-type 5 — Vider la mémoire {#s6-subtype-5--dump-memory}
```
Paramètres :
  memory_id [0=SRAM, 1=EEPROM]
  address [uint32]
  length [uint16]
Exemple : vider 512 octets de la SRAM à partir de 0x2000
Réponse : paquet TM contenant la mémoire (peut s'étendre sur plusieurs paquets pour les grands vidages)
Limites : renvoie des données fictives, pas de modèle de mémoire réel
```

### S6 sous-type 9 — Vérifier le CRC de la mémoire {#s6-subtype-9--check-memory-crc}
```
Paramètres :
  memory_id [0=SRAM, 1=EEPROM]
  address [uint32]
  length [uint16]
Exemple : vérifier le CRC du micrologiciel applicatif (bloc de 64 Ko)
Réponse : succès S1 avec la valeur du CRC (codée en dur pour l'instant)
Limites : simplifié, ne reflète pas l'état réel de la mémoire
```

---

## Service 8 : gestion des fonctions {#service-8-function-management}

**Rôle :** exécuter les fonctions du satellite (commandes destinées à chaque sous-système).

**Structure :**
```
Service: 8
Subtype: 1 (execute function)
Function_ID: 0-255 (command selector)
Data: function-specific parameters
```

**Fonctions AOCS (func_id 0-15) :**

| ID de fonction | Nom | Paramètres | Effet |
|---------|------|-----------|--------|
| 0 | AOCS_SET_MODE | mode (0-9) | Régler le mode opérationnel (survie, amortissement, pointage fin, etc.) |
| 1 | AOCS_DESATURATE | — | Lancer la séquence de désaturation des roues de réaction |
| 2 | AOCS_DISABLE_WHEEL | wheel_idx (0-3) | Désactiver une roue de réaction donnée |
| 3 | AOCS_ENABLE_WHEEL | wheel_idx (0-3) | Activer une roue de réaction donnée |
| 4 | ST1_POWER | on (0/1) | Allumer/éteindre le senseur stellaire 1 |
| 5 | ST2_POWER | on (0/1) | Allumer/éteindre le senseur stellaire 2 |
| 6 | ST_SELECT | unit (1/2) | Sélectionner le senseur stellaire principal (1=ST1, 2=ST2 ; 0 est refusé) |
| 7 | MAG_SELECT (retirée) | — | Supprimée : un seul magnétomètre est monté ; refusée avec 0x0007 |
| 8 | RW_SET_SPEED_BIAS | wheel, bias_rpm | Régler le biais de vitesse d'une roue de réaction |
| 9 | MTQ_ENABLE | enable (0/1) | Activer/désactiver les magnétocoupleurs |
| 10 | AOCS_SLEW_TO | q_x, q_y, q_z, q_w, rate_dps | Basculer vers le quaternion cible |
| 11 | AOCS_CHECK_MOMENTUM | — | Interroger l'état de saturation du moment cinétique |
| 12 | AOCS_BEGIN_ACQUISITION | — | Lancer l'acquisition d'attitude automatique |
| 13 | AOCS_GYRO_CALIBRATION | — | Réinitialiser l'estimation du biais des gyromètres |
| 14 | AOCS_RW_RAMP_DOWN | wheel_idx/255, target_rpm | Réduire progressivement la vitesse d'une roue |
| 15 | AOCS_SET_DEADBAND | deadband_deg | Régler la bande morte d'erreur d'attitude |

**Fonctions EPS (func_id 16-25, 81-83) :**

| ID de fonction | Nom | Paramètres | Effet |
|---------|------|-----------|--------|
| 16 | EPS_PAYLOAD_MODE | mode (0=off, 1=standby, 2=imaging) | Commander l'alimentation de la charge utile |
| 17 | EPS_FPA_COOLER | on (0/1) | Activer/désactiver le refroidisseur du FPA |
| 18 | EPS_TRANSPONDER_TX | on (0/1) | Activer/désactiver l'émission du transpondeur |
| 19 | EPS_POWER_ON | line_index (0-8; 8 = prop) | Mettre une ligne d'alimentation sous tension |
| 20 | EPS_POWER_OFF | line_index (0-8; 8 = prop) | Mettre une ligne d'alimentation hors tension |
| 21 | EPS_RESET_OC_FLAG | line_index (0-8; 8 = prop) | Réarmer l'indicateur de surintensité et réactiver la ligne |
| 22 | EPS_SWITCH_LOAD | load_id (0-7), state (0/1) | Commuter une charge d'alimentation individuelle |
| 23 | EPS_SET_CHARGE_RATE | rate_a (float, A; 0=auto) | Forcer le courant de charge de la batterie |
| 24 | EPS_SOLAR_ARRAY_DRIVE | angle_deg (int16, centi-degrees, -9000..9000) | Régler l'angle d'entraînement du générateur solaire |
| 25 | EPS_EMERGENCY_LOAD_SHED | stage (0-3) | Délester immédiatement jusqu'au niveau indiqué |
| 81 | EPS_DEPLOY_WING | wing (0=+Y, 1=-Y, 2=both) | Déployer une aile solaire (fil thermofusible) |
| 82 | EPS_WING_STATUS | — | Interroger l'état de déploiement des ailes solaires |
| 83 | EPS_SET_MODE | mode (0=nominal, 1=safe, 2=emergency) | Régler le mode de fonctionnement de l'EPS |

**Fonctions de la charge utile (func_id 26-39) :**

| ID de fonction | Nom | Paramètres | Effet |
|---------|------|-----------|--------|
| 26 | PAYLOAD_SET_MODE | mode (0=off, 1=standby, 2=imaging, 3=calibration) | Régler le mode de fonctionnement de la charge utile |
| 27 | PAYLOAD_SET_SCENE | scene_id (uint16) | Régler l'ID de scène pour la prise de vue |
| 28 | PAYLOAD_CAPTURE | scene_id, lines | Déclencher l'acquisition d'image |
| 29 | PAYLOAD_DOWNLOAD_IMAGE | scene_id | Mettre l'image en file d'attente pour la liaison descendante |
| 30 | PAYLOAD_DELETE_IMAGE | scene_id | Supprimer l'image de la mémoire |
| 31 | PAYLOAD_MARK_BAD_SEGMENT | segment_id (0-7) | Déclarer un segment mémoire inutilisable (num_memory_segments = 8) |
| 32 | PAYLOAD_GET_IMAGE_CATALOG | — | Demander le catalogue des images stockées |
| 33 | PAYLOAD_SET_BAND_CONFIG | mask (bits 0-3: B/G/R/NIR) | Régler le masque d'activation des bandes spectrales |
| 34 | PAYLOAD_SET_INTEGRATION_TIME | blue/green/red/nir_ms | Régler les temps d'intégration par bande |
| 35 | PAYLOAD_SET_GAIN | gain (0.1-10.0) | Régler le gain du détecteur |
| 36 | PAYLOAD_COOLER_SETPOINT | setpoint_C (-20 to 0) | Régler la température cible du refroidisseur du FPA |
| 37 | PAYLOAD_START_CALIBRATION | — | Lancer la séquence d'étalonnage |
| 38 | PAYLOAD_STOP_CALIBRATION | — | Interrompre la séquence d'étalonnage |
| 39 | PAYLOAD_SET_COMPRESSION | ratio (0=auto, else manual) | Forcer le taux de compression |

**Fonctions TCS (func_id 40-49) :**

| ID de fonction | Nom | Paramètres | Effet |
|---------|------|-----------|--------|
| 40 | HEATER_BATTERY | on (0/1) | Marche/arrêt du réchauffeur batterie |
| 41 | HEATER_OBC | on (0/1) | Marche/arrêt du réchauffeur de l'OBC |
| 42 | HEATER_THRUSTER | on (0/1) | Marche/arrêt du réchauffeur du propulseur |
| 43 | FPA_COOLER | on (0/1) | Marche/arrêt du refroidisseur du FPA |
| 44 | HEATER_SET_SETPOINT | circuit, on_temp, off_temp | Régler les consignes du thermostat |
| 45 | HEATER_AUTO_MODE | circuit (0-2) | Rendre le réchauffeur au pilotage automatique |
| 46 | TCS_SET_HEATER_DUTY_LIMIT | circuit, max_duty_pct | Limiter le rapport cyclique du réchauffeur |
| 47 | TCS_DECONTAMINATION_START | target_temp_c | Lancer le chauffage de décontamination |
| 48 | TCS_DECONTAMINATION_STOP | — | Interrompre la décontamination |
| 49 | TCS_GET_THERMAL_MAP | — | Demander l'état thermique de toutes les zones |

**Fonctions OBDH (func_id 50-62) :**

| ID de fonction | Nom | Paramètres | Effet |
|---------|------|-----------|--------|
| 50 | OBC_SET_MODE | mode (0=nom, 1=safe, 2=emerg) | Régler le mode de fonctionnement de l'OBC |
| 51 | OBC_MEMORY_SCRUB | — | Déclencher un nettoyage (*scrubbing*) manuel de la mémoire |
| 52 | OBC_REBOOT | — | Forcer le redémarrage de l'OBC (CRITICAL) |
| 53 | OBC_SWITCH_UNIT | — | Basculer sur l'OBC redondant (CRITICAL) |
| 54 | OBC_SELECT_BUS | bus (0=A, 1=B) | Sélectionner le bus CAN actif |
| 55 | OBC_BOOT_APP | — | Démarrer l'application depuis le chargeur d'amorçage |
| 56 | OBC_BOOT_INHIBIT | inhibit (0/1) | Inhiber/autoriser le démarrage automatique |
| 57 | OBC_CLEAR_REBOOT_CNT | — | Remettre à zéro le compteur de redémarrages |
| 58 | OBC_SET_WATCHDOG_PERIOD | period_ticks (1-1000) | Configurer le délai du chien de garde |
| 59 | OBC_WATCHDOG_ENABLE | — | Activer la surveillance par chien de garde |
| 60 | OBC_WATCHDOG_DISABLE | — | Désactiver la surveillance par chien de garde |
| 61 | OBC_DIAGNOSTIC | — | Demander un diagnostic de santé de l'OBC |
| 62 | OBC_ERROR_LOG | — | Demander le journal des erreurs récentes |

**Fonctions TTC (func_id 63-79, 97-98) :**

| ID de fonction | Nom | Paramètres | Effet |
|---------|------|-----------|--------|
| 63 | TTC_SWITCH_PRIMARY | — | Basculer sur le transpondeur principal |
| 64 | TTC_SWITCH_REDUNDANT | — | Basculer sur le transpondeur redondant |
| 65 | TTC_SET_DATA_RATE | rate (code de palier uint8 : 0=LOW, 1=HIGH, 255=SAFE) | Sélectionner un échelon de l'échelle de débits TM — voir ci-dessous |
| 66 | TTC_PA_ON | — | Activer l'amplificateur de puissance |
| 67 | TTC_PA_OFF | — | Désactiver l'amplificateur de puissance |
| 68 | TTC_SET_TX_POWER | level uint8 (0=LOW 1.0 W, 1=NOMINAL 2.0 W, 2=HIGH 5.0 W) | Sélectionner un point de fonctionnement du SSPA. Paliers discrets uniquement ; un code inconnu est rejeté par S1.8 avec l'erreur 0x0003, jamais écrêté. L'ancien « 2 = 8 W » dépassait pa_max_power_w = 5.0 W et n'a jamais été exécutable. |
| 69 | TTC_DEPLOY_ANTENNA | — | Déployer l'antenne (fil thermofusible) |
| 70 | TTC_SET_BEACON_MODE | on (0/1) | Activer/désactiver le mode balise |
| 71 | TTC_CMD_CHANNEL_START | — | Ouvrir le canal de commande (15 min) |
| 72 | TTC_SET_UL_FREQ | freq_mhz (2025-2110) | Régler la fréquence de la liaison montante |
| 73 | TTC_SET_DL_FREQ | freq_mhz (2200-2290) | Régler la fréquence de la liaison descendante |
| 74 | TTC_SET_MODULATION | mode (0=BPSK, 1=QPSK, 2=8PSK, 3=OQPSK) | Régler le mode de modulation |
| 75 | TTC_SET_RX_GAIN | agc_db (-100 to 0) | Régler la consigne de CAG du récepteur |
| 76 | TTC_RANGING_START | — | Lancer la séquence de mesure de distance |
| 77 | TTC_RANGING_STOP | — | Arrêter la séquence de mesure de distance |
| 78 | TTC_SET_COHERENT_MODE | mode (0/1) | Sélectionner le mode cohérent/non cohérent |
| 79 | TTC_SET_DOWNLINK_MODE | on (uint8, 0/1) | Entrer dans le mode DOWNLINK (vidage de la charge utile) ou en sortir — le verrou de mode du palier HIGH |
| 97 | TTC_BEACON_TX_ON | — | Mettre en marche l'émetteur balise UHF |
| 98 | TTC_BEACON_TX_OFF | — | Arrêter l'émetteur balise UHF (supprime la dernière liaison descendante indépendante) |

#### Fonction 65 — TTC_SET_DATA_RATE et l'échelle de débits TM {#func-65--ttc_set_data_rate-and-the-tm-rate-ladder}

La liaison descendante est une échelle à trois échelons définie dans
`configs/eosat1/subsystems/ttc.yaml tm_rate_tiers`, et non un simple commutateur haut/bas.
La fonction 65 prend **un seul uint8** portant le `command_code` d'un palier :

| Code | Palier | Débit | Modulation / codage | Débit symbole | Sélectionnable ? |
|------|------|------|---------------------|-------------|-------------|
| `0x00` | LOW | 16 000 bit/s | BPSK, conv(7,1/2)+RS | 16 kBd | Toujours. **Le débit des opérations courantes** et le repli en mode survie / FDIR |
| `0x01` | HIGH | 128 000 bit/s | QPSK, RS(255,223) | 64 kBd | Uniquement avec l'antenne déployée et le mode DOWNLINK actif (fonction 79) ; l'élévation minimale de 10° est une règle sol (avertissement du MCS), pas un verrou de bord |
| `0xFF` | SAFE | 1000 bit/s | BPSK, conv(7,1/2)+RS | 1 kBd | **Pas** par cette commande — on y entre par la fonction 70 (`TTC_SET_BEACON_MODE`) ou par le chargeur d'amorçage |

**L'ancien codage est conservé tel quel.** `rate=0` a toujours signifié « le débit bas »
et `rate=1` « le débit haut » ; ils sélectionnent désormais LOW et HIGH. Les procédures existantes, les OBCP
et l'action FDIR `ttc_reduce_power` conservent donc leur signification et aboutissent à des débits
opérationnels utilisables. Une forme brute en bit/s sur 4 octets gros-boutiste reste acceptée pour les anciens clients :
une valeur égale au `bps` d'un palier configuré sélectionne ce palier.

**Rejet, pas écrêtage.** Un palier dont les verrous ne sont pas satisfaits est refusé par un
échec d'exécution S1.8, erreur `0x0007`, et le texte d'échec nomme le verrou ouvert. Un
code de palier non reconnu donne l'erreur `0x0003`. Rien n'est substitué en silence.

**Commandé ou actif.** La fonction 65 règle le palier COMMANDÉ (`ttc.tm_tier_cmd`, 0x053A).
Le cycle TT&C en déduit le palier ACTIF (`ttc.tm_tier`, 0x0539) en descendant
l'échelle jusqu'à ce que tous les verrous soient satisfaits : HIGH revient donc automatiquement en arrière lorsqu'un verrou se ferme (p. ex.
sortie du mode DOWNLINK), et reprend dès qu'il se rouvre, sans nouvelle commande.

Télémesure associée : `ttc.tm_data_rate` (0x0506, débit binaire actif), `ttc.tm_tier` (0x0539),
`ttc.tm_tier_cmd` (0x053A), `ttc.tm_symbol_rate` (0x053B), `ttc.downlink_mode` (0x053C).

#### Fonction 79 — TTC_SET_DOWNLINK_MODE {#func-79--ttc_set_downlink_mode}

```
Parameter: on (uint8) — 0 = leave DOWNLINK mode, 1 = enter DOWNLINK/dump mode
```

Le mode DOWNLINK est le verrou de *mode* du palier HIGH. La transmission en masse doit être engagée
délibérément, de sorte qu'un vidage d'images S13 ou une relecture de télémesure différée S15 soit une activité
planifiée du passage, et non un état dans lequel le satellite glisse par inadvertance. Entrer dans le mode DOWNLINK ne
change pas à lui seul le débit ; en sortir n'efface pas le palier commandé — le palier ACTIF
retombe simplement sur LOW jusqu'à ce que l'on revienne dans le mode DOWNLINK.

**Exemple de séquence de commandes S8 — passage de prise de vue :**

```
1. Enable AOCS fine point mode
   S8 func_id=0, mode=5

2. Set payload to imaging mode
   S8 func_id=26 (PAYLOAD_SET_MODE), mode=2

3. Begin imaging (assuming ground target in view)
   S8 func_id=28 (PAYLOAD_CAPTURE), scene_id=42, lines=4096
   S5 event: IMAGING_START (0x0600)

4. Check image storage
   S3 request SID=5 (HK_Payload)
   Response: storage_used=1200 MB, SNR=35 dB

5. Download image
   S8 func_id=29 (PAYLOAD_DOWNLOAD_IMAGE), scene_id=42
   S13 request transfer (see Service 13)
```

---

## Service 9 : gestion du temps {#service-9-time-management}

**Rôle :** synchroniser le temps bord avec le temps sol.

**Mise en œuvre :** assurée par les sous-systèmes OBDH et TTC.
- l'OBC entretient une horloge UTC interne ;
- le TTC peut corréler l'horodatage d'une commande avec le temps bord ;
- tous les paquets TM sont horodatés (8 octets : secondes + microsecondes).

---

## Service 11 : programmation des activités {#service-11-activity-scheduling}

**Rôle :** programmer des télécommandes pour qu'elles s'exécutent à des instants précis.

**Sous-types :**

| Sous-type | Sens | Signification | Format sur la liaison |
|---------|-----------|---------|-------------|
| 4 | TC | **Insérer** une télécommande datée | `exec_time_cuc (uint32)` + le paquet TC complet encapsulé |
| 7 | TC | Supprimer UNE commande programmée | `cmd_id (uint16)` |
| 9 | TC | Désactiver le plan bord (file conservée, rien ne s'exécute) | — |
| 11 | TC | Supprimer TOUTES les commandes programmées | — |
| 13 | TC | Activer le plan bord | — |
| 17 | TC | Demander un rapport détaillé du plan bord | — |
| 5 | TM | Accusé d'insertion | `cmd_id (uint16)` — l'identifiant à utiliser avec le sous-type 7 |
| 18 | TM | Rapport détaillé du plan bord (réponse au 17) | voir ci-dessous |

**L'insertion est le sous-type 4, pas le sous-type 11.** Des révisions antérieures de ce document
décrivaient « S11 subtype 11 (insert scheduled activity) ». Le sous-type 11 est la
*suppression totale* — l'envoyer à la place d'une insertion efface sans avertissement tout le
plan bord. Voir `ServiceDispatcher._handle_s11`.

**Exemple :** commander une prise de vue à l'AOS (acquisition du signal) :

```
TC (from MCS):
  S11 subtype 4 (insert time-tagged command)
  Data: exec_time_cuc (uint32, absolute CUC seconds — TLE propagation + AOS prediction)
      + the whole TC packet to run, e.g. S8.1 func_id=28 (PAYLOAD_CAPTURE),
        scene_id=42, lines=4096

Response:
  TM(11,5): cmd_id (uint16) — the on-board handle for this activity
  S1.1 / S1.7 for the S11 telecommand itself (it was accepted and executed)
  [At the scheduled CUC time]
  The embedded TC is dispatched exactly as if uplinked, so it produces
  its own S1.1 / S1.7 and any S5 events (e.g. IMAGING_START).
```

**TM(11,18) — rapport détaillé du plan bord** (étendu par le défaut n° 72 pour que le rapport
porte l'*identité* de la commande, et pas seulement une date) :

```
Header: count (uint16) + schedule_enabled (uint8) + next_id (uint16)
Record: id (uint16) + exec_time_cuc (uint32) + apid (uint16)
      + service (uint8) + subtype (uint8) + data_len (uint8)
      + n_bytes (uint8) + data[n_bytes]
```

Le paquet encapsulé lui-même reste à bord ; seuls son identité et au plus 255
octets de son champ de données sont rapportés.

**Contraintes :**
- la file du programmateur est **non bornée** (`TCScheduler._commands` est un simple
  dict). Des révisions antérieures annonçaient une limite de 1000 activités ; cette limite n'existe pas ;
- programmation en temps CUC **absolu** uniquement. Il n'existe pas de sous-type relatif ou à décalage —
  le sol calcule l'instant d'exécution absolu ;
- les ID de commande sont attribués de façon monotone à partir de 1 et ne sont pas réutilisés après
  suppression ;
- vérification de l'exécution : la commande *programmée* émet ses propres rapports S1 lorsqu'elle
  s'exécute. Un vidage programmé qui s'exécute hors d'une fenêtre de visibilité consomme quand même
  la mémoire, et ses paquets sont perdus (voir le service 15).

**Chaîne côté sol.** Vous n'avez pas à assembler à la main le champ de données de la TC(11,4) :
le MCS expose `POST /api/schedule/upload-s11`, qui convertit les étapes de commande d'une activité
du planificateur en insertions S11 datées à l'instant d'exécution prévu
(défaut n° 46). Les étapes de vérification de télémesure et de GO/NO-GO ne peuvent pas être datées et
sont écartées avec un avertissement explicite — le programmateur de bord exécute
des commandes, pas des décisions. Utilisez une OBCP (service 18) lorsque la séquence doit
attendre une télémesure ou se ramifier selon sa valeur.

---

## Service 12 : surveillance bord {#service-12-on-board-monitoring}

**Rôle :** surveillance autonome de seuils de paramètres. Les violations génèrent un
rapport de transition de contrôle TM(12,9), un événement S5, et peuvent déclencher une action S19.

**Sous-types :**

| Sous-type | Sens | Signification | Format sur la liaison |
|---------|-----------|---------|-------------|
| 1 / 2 | TC | Activer / désactiver la surveillance globalement | — |
| 3 / 4 | TC | Activer / désactiver UNE définition | `mon_id (uint16)` |
| 6 | TC | Ajouter une définition | 13 octets : `mon_id(u16) + param_id(u16) + check_type(u8) + low(f32) + high(f32)`. Une forme historique sur 11 octets omet `mon_id` et réutilise `param_id`. |
| 7 | TC | Supprimer une définition | `mon_id (uint16)` |
| 12 | TC | Rendre compte de toutes les définitions → TM(12,13) | — |
| 9 / 10 | TM | Transition de contrôle : **entrée** en violation / **retour au nominal** | émis à chaque transition |
| 13 | TM | Rapport des définitions (réponse au 12) | — |

**check_type :** `0` = absolu (la valeur doit rester dans `[low, high]`),
`1` = delta (la *variation* depuis le contrôle précédent doit rester dans `[low, high]` ;
le premier échantillon après un démarrage ou une mise hors tension n'a pas de référence et ne peut pas être en violation).
Les deux sont mis en œuvre ; **les 38 définitions livrées utilisent toutes check_type 0**.

**Règles de surveillance : 38 configurées** (`configs/eosat1/monitoring/s12_definitions.yaml`
— 30 WARNING, 8 ALARM)

| Paramètre | Règle | Seuil | Événement | Action S19 |
|-----------|------|-----------|-------|-----------|
| `eps.bat_soc` | Bas | < 20 % | 0x0101 | Réduire les charges |
| `eps.bat_soc` | Critique | < 10 % | 0x0102 | Délestage d'urgence |
| `eps.bus_voltage` | Bas | < 27 V | 0x0103 | Arrêt de la charge utile |
| `eps.bus_voltage` | Critique | < 25 V | 0x0104 | Arrêt de tout le non-essentiel |
| `aocs.rw1_speed` | Survitesse | > ±5000 tr/min | 0x0201 | Désactiver la roue 1 |
| `aocs.total_momentum` | Saturation | > 90 Nms | 0x0205 | Déclencher la désaturation |
| `aocs.att_error` | Élevée | > 1° | 0x0206 | Mode survie |
| `tcs.fpa_temp` | Surchauffe | > -3 °C | 0x0604 | Arrêt de la charge utile |
| `ttc.link_margin` | Critique | < 3 dB | 0x0507 | Augmenter la puissance d'émission |
| `ttc.pa_temp` | Coupure | > 65 °C | 0x0509 | Arrêt du PA |

**Signalement des violations** — les violations sont **déclenchées sur front** : un rapport lorsque le
paramètre *entre* en violation et un autre lorsqu'il en *sort*. Rien n'est émis tant
qu'il reste en violation.

```
Quand un paramètre franchit un seuil (OK → violé) :
  1. Violation S12 détectée par ServiceDispatcher.check_monitoring()
     (entièrement ignorée si le sous-système source du paramètre n'est pas alimenté)
  2. Rapport de transition de contrôle TM(12,9) « limite atteinte » — la vraie télémesure
     de surveillance que décode le sol (ajoutée par le défaut #69)
  3. Événement S5 généré, event_id = 0x9000 | (param_id & 0x0FFF)
  4. Règle S19 déclenchée (si l'une correspond à l'identifiant d'événement, ou à l'identifiant
     de paramètre dans l'espace des paramètres — trigger_kind lève l'ambiguïté)
  5. Commande S8 exécutée de façon autonome
  6. Événement consigné dans le stockage TM S15

Au rétablissement (violé → OK) :
  1. Rapport de transition de contrôle TM(12,10) « retour au nominal »
  2. Événement S5, event_id = 0xA000 | (mon_id & 0x0FFF), gravité INFO
```

L'ID d'événement est `0x9000 | param_id`, **et non** `0x8000 + param_id`.

**Exemple de déroulement — SoC batterie critique :**

```
Battery SoC drops from 12% to 9%
  ↓
S12 rule: "EPS Battery SoC Critical" detects < 10%
  ↓
S5 event: 0x0102 (BATTERY_SOC_CRITICAL) generated
  ↓
S19 rule: "Battery SoC critical → Payload off" matches
  ↓
S8 command: func_id=26, mode=0 (PAYLOAD_SET_MODE off)
  ↓
S1 verification: Execution complete
  ↓
S5 event: 0x0602 (PAYLOAD_MODE_CHANGE) generated
  ↓
MCS displays alert: Battery critical, Payload disabled
```

---

## Service 13 : transfert de gros volumes de données {#service-13-large-data-transfer}

**Rôle :** transmission efficace par blocs de gros volumes de télémesure (images de la charge utile).

**Gestion des sessions :**

```
1. Ground: S13 subtype 1 (initiate transfer)
   Parameters: transfer_id, data_type (image), block_size
   Response: S1.1 (accepted), TM packet with transfer_id

2. Ground: S13 subtype 3 (request data block)
   Parameters: transfer_id, block_number
   Response: TM packet with 4 KB of image data + CRC

3. Ground: S13 subtype 3 (repeat for all blocks)
   Image size: 2 MB → 512 blocks × 4 KB

4. Ground: S13 subtype 5 (end transfer)
   Parameters: transfer_id
   Response: S1.7 (transfer complete)
```

**Protocole de transfert :**

| Phase | Sous-type | Sens | Rôle |
|-------|---------|-----------|---------|
| Ouverture | 1 | TC → — | Ouvrir la session de transfert |
| Données | 3 | TC → TM | Demander / recevoir un bloc de données |
| Fin | 5 | TC → — | Clore le transfert |
| État | 9 | TC → TM | Rendre compte de l'état du transfert (S13_REPORT_STATUS) |

**Exemple de déroulement — téléchargement d'une image :**

```
Ground: S13.1 initiate transfer
  Parameters: transfer_id=1, data_type=image_id_42, block_size=4096
  Response: S1.1 (accepted)

Ground: S13.3 request block 0
  Parameters: transfer_id=1, block_num=0
  Response: TM (4096 bytes of image data + CRC)

Ground: [verify CRC, store block]

Ground: S13.3 request block 1
  ...repeat for blocks 1-511...

Ground: S13.5 end transfer
  Parameters: transfer_id=1
  Response: S1.7 (transfer complete, total_bytes=2097152)

Result: 2 MB image downloaded in ~131 s at HIGH (128 kbit/s)
```

**Caractéristiques :**
- jusqu'à 16 sessions de transfert simultanées ;
- taille de bloc : de 256 octets à 64 Ko (configurable) ;
- CRC-32 par bloc (détection automatique des erreurs) ;
- reprise possible (les blocs déjà téléchargés sont sautés) ;
- délai d'attente de transfert : 60 secondes d'inactivité ;
- taille maximale de transfert : 256 Mo par session.

---

## Service 15 : stockage de la TM {#service-15-tm-storage}

**Rôle :** stockage à bord et relecture des paquets de télémesure.

**Structure (telle que mise en œuvre) :**

```
4 stockages :
  Stockage 1 : HK_Store       — circulaire, capacité 5000   paquets (alimenté par la HK S3)
  Stockage 2 : Event_Store    — linéaire,   capacité 1000   paquets (alimenté par les événements S5)
  Stockage 3 : Science_Store  — linéaire,   capacité 10000  paquets (fourre-tout : charge utile, science, etc.)
  Stockage 4 : Alarm_Store    — linéaire,   capacité 500    paquets (événements S5 de gravité ≥ ALARM)

Routage : service 3 (HK) → stockage 1 ; service 5 (événements) → stockage 2 et (si gravité≥2) stockage 4 ;
          toute autre TM → stockage 3.
Le stockage circulaire 1 écrase le paquet le plus ancien lorsqu'il est plein. Les stockages 2–4 cessent
d'enregistrer en cas de débordement et lèvent un indicateur de débordement rapporté par la requête d'état.
Tous les stockages sont activés à l'amorçage ; S15.1/S15.2 ne font que basculer l'indicateur d'activation.
```

**Commandes :**

### S15 sous-type 1 — Activer une mémoire de paquets {#s15-subtype-1--enable-store}
```
Paramètre : store_id (uint8)
Effet : autorise l'enregistrement de paquets dans le stockage. (Les stockages sont déjà activés
        à l'amorçage : cette commande n'est donc utile qu'après S15.2.)
```

### S15 sous-type 2 — Désactiver une mémoire de paquets {#s15-subtype-2--disable-store}
```
Paramètre : store_id (uint8)
Effet : arrête l'enregistrement dans le stockage. Les paquets existants sont conservés.
```

### S15 sous-type 9 — Vider une mémoire de paquets (cadencé) {#s15-subtype-9--dump-store-paced}
```
Paramètre : store_id (uint8)
Effet : met en file la totalité (ALL) des paquets présents dans le stockage pour une transmission
        cadencée. Les paquets sont libérés sur plusieurs pas de simulation, à l'échelon ACTIVE
        de l'échelle des débits TM — 16 kbps en LOW, 128 kbps en HIGH (et 1 kbps en mode
        balise, où un vidage n'a pas de sens). Passer d'abord le débit en HIGH : func 79 pour
        entrer en mode DOWNLINK, puis func 65 avec rate=1. Le stockage est automatiquement
        effacé une fois le vidage terminé.
Réponse : rapport d'avancement S1.5 indiquant le nombre de paquets mis en file.
Comportement de la liaison descendante :
  - Si la liaison descendante est active lorsqu'un paquet est libéré, il parvient au MCS.
  - Si la liaison descendante n'est pas active (NOT active), ce paquet est perdu (LOST) : la radio
    aurait émis dans le vide ; le vidage continue de consommer le stockage.
  - L'indicateur de forçage des passages du simulateur impose downlink_active=True et
    délivre donc tous les paquets vidés, quel que soit le contact orbital.
  - Les vidages programmés (via la planification d'activités S11) se comportent à l'identique : si
    le vidage programmé se déclenche hors d'une fenêtre de visibilité, les paquets sont perdus.
```

### S15 sous-type 11 — Effacer une mémoire de paquets {#s15-subtype-11--delete-store}
```
Paramètre : store_id (uint8)
Effet : efface tous les paquets du stockage, réinitialise l'indicateur de débordement et les horodatages.
```

### S15 sous-type 13 — Demande d'état {#s15-subtype-13--status-request}
```
Paramètres : aucun
Réponse : rapport d'état S15.14 listant tous les stockages avec :
            - store_id (uint8)
            - nombre de paquets (uint16)
            - capacité (uint16)
            - indicateur d'activation (uint8)
```

### S15 sous-type 14 — Rapport d'état {#s15-subtype-14--status-report}
```
TM response to S15.13. See format above.
```

**Remarques et limites :**
- il n'existe pas de filtre par plage temporelle des paquets lors des vidages ; S15.9 vide la totalité de la mémoire ;
- il n'existe pas de commande de durée de conservation (TTL) ; l'expiration ne se produit que par débordement linéaire ou par effacement S15.11 ;
- la cadence de vidage suit le `ttc.tm_data_rate` courant. Changer de débit en cours de vidage
  (func_id 65, TTC_SET_DATA_RATE) modifie immédiatement le rythme de libération des paquets.

---

## Service 17 : test de connexion {#service-17-connection-test}

**Rôle :** valider la liaison de commande (test NOOP en écho).

**Commandes :**

### S17 sous-type 1 — Test de connexion {#s17-subtype-1--connection-test}
```
Paramètres : aucun n'est utilisé. Tout champ de données est accepté et ignoré (IGNORED).
Réponse :  S1.1 (acceptée) + TM(17,2), rapport de test de connexion avec un champ de données
           vide (EMPTY ; seul l'horodatage CUC figure dans l'en-tête secondaire).
```

Il s'agit d'un test de connexion, **et non** d'un écho : `build_connection_test_report()`
(`packages/smo-common/src/smo_common/telemetry/tm_builder.py`) empaquette
`data=b''`. N'attendez pas que les octets envoyés vous reviennent.

**Cas d'usage :** vérifier la connectivité de la liaison montante avant une phase de commande critique — l'arrivée
de la TM(17,2) prouve que l'OBC a accepté et exécuté une télécommande.

---

## Service 18 : procédures de contrôle bord {#service-18-on-board-control-procedures}

**Rôle :** charger, lancer, arrêter et surveiller des OBCP — de petits programmes à étapes que l'OBC
exécute de façon autonome, sans le sol dans la boucle. L'interpréteur d'étapes réside dans
`ObcpManager` (`packages/smo-simulator/src/smo_simulator/obcp.py`) et est cadencé
par la boucle principale du moteur. Les procédures livrées se trouvent dans `configs/eosat1/obcp/`
(préparation de passage, passage en mode survie, contrôle fonctionnel de la charge utile).

**Sous-types :**

| Sous-type | Sens | Signification | Format sur la liaison |
|---------|-----------|---------|-------------|
| 1 | TC | Charger directement une procédure | `proc_id` + nom + étapes sérialisées (voir `ObcpManager.parse_load_blob`) |
| 2 | TC | Supprimer une procédure | `proc_id (uint16)` |
| 3 | TC | Activer (lancer) une procédure | `proc_id (uint16)` + `param (uint8)` facultatif |
| 4 | TC | Arrêter / interrompre une procédure | `proc_id (uint16)` ; `0` = tout arrêter |
| 6 | TC | Demander l'état des procédures → TM(18,7) | — |
| 7 | TM | Rapport d'état des procédures | `count(u8)` + pour chaque procédure `proc_id(u16) + status(u8) + current_step(u8) + n_steps(u8)` |

**Les échecs sont signalés, pas passés sous silence :** un chargement dont le blob ne peut être analysé, un
chargement dans une mémoire pleine, une suppression ou un arrêt d'une procédure absente, et le
lancement d'une procédure non chargée ou déjà en cours produisent chacun un
rapport d'échec d'exécution S1.8 (codes d'erreur 0x0003 argument erroné / 0x0007 objet
inconnu). Voir `docs/OBCP_GUIDE.md` pour la rédaction des procédures.

---

## Service 19 : événement-action {#service-19-event-action}

**Rôle :** réponse autonome aux événements, sans intervention du sol.

**Sous-types :**

| Sous-type | Sens | Signification | Format sur la liaison |
|---------|-----------|---------|-------------|
| 1 | TC | Ajouter une définition événement-action | 6 octets : `ea_id(u16) + trigger_kind(u8) + trigger_id(u16) + action_func_id(u8)`. Une forme historique sur 4 octets (`ea_id(u16) + event_type(u8) + action_func_id(u8)`) est encore acceptée, mais ne peut exprimer aucun ID d'événement réel d'EOSAT-1 — tous sont ≥ 0x0100. |
| 2 | TC | Supprimer une définition | `ea_id (uint16)` |
| 4 / 5 | TC | Activer / désactiver une définition | `ea_id (uint16)` |
| 8 | TC | Rendre compte de toutes les définitions → TM(19,128) | — |
| 128 | TM | Rapport des définitions | `count(u16)` + pour chaque règle `ea_id(u16) + trigger_kind(u8) + trigger_id(u16) + action_func_id(u8) + enabled(u8)` |

**`trigger_kind` compte.** Les ID d'événements S5 et les ID de paramètres surveillés par S12
occupent tous la plage 0x0000–0x0FFF : un ID seul est donc ambigu, et la correspondance exige que l'ID
*et* l'espace de noms concordent. Avant le défaut n° 70, seul l'ID était comparé, et 17
des 26 règles livrées se déclenchaient deux fois.

**Une action est exactement un appel de fonction S8 sans paramètre** — ni séquence, ni
argument, ni délai, ni condition. Utilisez une OBCP (service 18) lorsqu'il vous faut une
séquence.

**Verrou du chargeur d'amorçage :** les fonctions 52, 53, 55 et 56 (redémarrage, basculement d'unité OBC, démarrage de l'application,
inhibition du démarrage) sont refusées sur la voie autonome S19 tant que l'OBC est sous le
chargeur d'amorçage, de sorte qu'aucune règle ne peut démarrer ou redémarrer l'OBC à l'insu de l'opérateur.

**Règles : 26 configurées** (`configs/eosat1/monitoring/s19_rules.yaml`)

> **Point ouvert connu :** 13 des 26 règles livrées appellent un `action_func_id`
> qui ne correspond pas à leur `description` (p. ex. ea 1001 « payload off » appelle
> la fonction 10, qui est `AOCS_SLEW_TO`). Le mécanisme est correct ; le *contenu* est
> en cours de revue. Le tableau ci-dessous montre le comportement voulu, pas le câblage actuel.

| ID de règle | Déclencheur | Action | Rôle |
|---------|---------|--------|---------|
| 1001 | Sous-tension du bus (0x0103) | Arrêt de la charge utile | Économie d'énergie |
| 1002 | SoC batterie critique (0x0102) | Arrêt du refroidisseur du FPA | Économie d'énergie |
| 2001 | Saturation du moment cinétique (0x0205) | Désaturer les roues | Contrôle SCAO |
| 2002 | Senseur stellaire 1 aveuglé (0x0203) | Basculer sur ST2 | Contrôle d'attitude |
| 3001 | Surchauffe du FPA (0x0604) | Arrêt de la charge utile | Protection thermique |
| 4001 | Marge de liaison critique (0x0507) | Augmenter la puissance d'émission | Rétablissement de la liaison |
| 5001 | Redémarrage de l'OBC (0x0301) | Acquitter | Surveillance du système |
| 6001 | Stockage plein (0x0609) | Arrêter la prise de vue | Gestion des données |

**Déroulement de l'exécution :**

```
Événement déclenché (S5) :
  ↓
Une règle S19 correspond (event_type présent dans la base de règles)
  ↓
Contrôle de l'indicateur d'activation de la règle
  ↓
Exécution de action_func_id (fonction S8)
  ↓
Vérification S1 générée
  ↓
Nouvel événement émis (LOAD_SHED_ACTIVATED, etc.)
  ↓
Le MCS alerte l'opérateur (information)
```

**Exemple de configuration :**

```yaml
s19_rules:
  - ea_id: 1001
    event_type: 0x0103  # Bus undervoltage
    action_func_id: 26  # PAYLOAD_SET_MODE OFF
    description: "Undervoltage -> Payload off"
    enabled: true
```

---

## Service 20 : gestion des paramètres {#service-20-parameter-management}

**Rôle :** ajuster les paramètres réglables par télécommande (gains, décalages, constantes), et
lire à la demande tout paramètre catalogué.

> **Allocation des sous-types — un écart délibéré par rapport à l'ECSS-E-ST-70-41.**
>
> | Sous-type | Cette suite | ECSS-E-ST-70-41 |
> |---|---|---|
> | **20,1** | **écriture** d'un paramètre (`param_id` + valeur float32) | *demande* de rapport des valeurs de paramètres |
> | **20,2** | rapport de valeur de paramètre (liaison descendante) | rapport des valeurs de paramètres |
> | **20,3** | **lecture** d'un paramètre (`param_id` → rapport 20,2) | écriture des valeurs de paramètres |
>
> La mise en œuvre est `service_dispatch._handle_s20`, et `tc_catalog.yaml`,
> le constructeur de commandes du MCS, les procédures et `tools/procedure_audit.py` suivent tous
> **ce tableau**, pas la norme. Jusqu'à la phase G, les *procédures* suivaient
> l'ECSS tandis que la liaison suivait la mise en œuvre : un opérateur qui déroulait une
> fiche envoyait le mauvais sous-type à 79 endroits répartis dans dix fichiers — la fiche indiquait
> « GET_PARAM (Service 20, Subtype 1) » et le satellite écrivait dans le paramètre
> ce qui se trouvait par hasard dans le tampon.
>
> L'écart n'est pas défendu comme une bonne conception ; il est consigné parce que
> réallouer un protocole en service entre six consommateurs est un changement plus lourd
> que la confusion qu'il dissiperait, et `tests/test_content/test_procedure_audit_gate.py`
> contraint désormais chaque consommateur à une réponse unique.

**Cas d'usage :**
- ajuster les gains de contrôle du SCAO ;
- mettre à jour la bande morte d'erreur d'attitude ;
- modifier les seuils de charge de l'EPS ;
- étalonner le zéro des capteurs.

**Exemple :** modifier la bande morte d'attitude du SCAO

```
TC (from MCS):
  S20 subtype 1 (set parameter)
  param_id: 0x2064 (aocs.att_deadband)
  value: 0.5 (degrees)

Response:
  S1.1: Parameter set accepted
  S1.7: Parameter update complete
  S3 HK: New value reflected in next report
```

---

## Commande depuis le MCS {#commanding-from-the-mcs}

**Exemple pas à pas : exécuter un passage de prise de vue**

### 1. Vérifier le bilan de puissance {#1-check-power-budget}
```
MCS: S3 request HK_EPS (SID=1)
Response:
  Battery SoC: 78%
  Power generation: 1200 W
  Power consumption: 850 W
  Load shedding stage: 0 (no shedding)
Status: OK to proceed
```

### 2. Régler l'attitude {#2-set-attitude}
```
MCS: S8 func_id=0 (AOCS_SET_MODE), param=5 (fine_point)
Response:
  S1.1: Accepted
  S1.3: Execution start
  S1.7: Completion
  S5: AOCS_MODE_CHANGE (0x0200)
```

### 3. Activer la prise de vue {#3-enable-imaging}
```
MCS: S8 func_id=26 (PAYLOAD_SET_MODE), param=2 (imaging)
Response:
  S1.1: Accepted
  S1.7: Completion
  S5: PAYLOAD_MODE_CHANGE (0x0602)
```

### 4. Acquérir l'image {#4-capture-image}
```
MCS: S8 func_id=28 (PAYLOAD_CAPTURE), scene_id=42, lines=4096
Response:
  S1.1: Accepted
  S1.3: Execution start
  S5: IMAGING_START (0x0600)
  [60 seconds of imaging]
  S5: IMAGING_STOP (0x0601)
  S1.7: Completion
```

### 5. Télécharger l'image {#5-download-image}
```
MCS: S13 subtype 1 (initiate transfer), transfer_id=1
Response:
  S1.1: Transfer initiated

MCS: S13 subtype 3 (request blocks 0-511)
Response:
  512 × TM packets, each 4 KB image data
  [Block download continues in background]

MCS: S13 subtype 5 (end transfer)
Response:
  S1.7: Transfer complete
```

### 6. Vérifier l'état {#6-verify-status}
```
MCS: S3 request HK_Payload (SID=5)
Response:
  Storage used: 1200 MB (image added)
  FPA temp: -15°C (setpoint)
  Cooler: ON
  Compression ratio: 4.2:1
```

---

## Dialogue de commande du MCS (exemple textuel) {#mcs-command-dialog-text-example}

```
MCS> list_commands AOCS
Available AOCS commands:
  func 0:  AOCS_SET_MODE              (mode 0-8)
  func 1:  AOCS_DESATURATE            (-)
  func 10: AOCS_SLEW_TO               (q_x, q_y, q_z, q_w, rate_dps)
  func 11: AOCS_CHECK_MOMENTUM        (-)
  func 12: AOCS_BEGIN_ACQUISITION     (-)

MCS> send_command AOCS 10 0.0 0.707 0.0 0.707 5.0
Command: AOCS_SLEW_TO
  Parameters: q_x=0.0, q_y=0.707, q_z=0.0, q_w=0.707, rate_dps=5.0
  Target: Body +Z axis pointing to spacecraft +X axis
  Rate: 5 deg/sec

Status: S1.1 Acceptance report received
Status: S1.3 Execution start
Status: S1.5 Progress (step 1/3)
Status: S1.5 Progress (step 2/3)
Status: S1.5 Progress (step 3/3)
Status: S1.7 Execution complete (result=OK)

MCS> query_telemetry aocs.att_q1 aocs.att_q2 aocs.att_q3 aocs.att_q4
AOCS Attitude:
  q1 (X): 0.002
  q2 (Y): 0.706
  q3 (Z): -0.004
  q4 (W): 0.708
Status: Slew complete, fine point attitude achieved
```

---

## Traitement des erreurs {#error-handling}

**Codes d'erreur courants :**

| Code | Signification | Reprise |
|------|---------|----------|
| 0x0001 | Échec générique / service inconnu | Vérifier le type de service et le format du paquet |
| 0x0002 | Sous-type inconnu | Vérifier que le sous-type est mis en œuvre pour ce service |
| 0x0003 | Paramètre ou longueur de données invalide | Vérifier le type, le nombre et les plages des paramètres |
| 0x0004 | Sous-système hors tension ou injoignable | Mettre l'équipement sous tension ; vérifier l'état FDIR |
| 0x0005 | Invalide dans le mode courant | Changer d'abord de mode ; lire le texte d'échec S1.8 |
| 0x0006 | Interdit dans le chargeur d'amorçage | Démarrer d'abord l'application (OBC_BOOT_APP, fonction 55) |
| 0x0007 | Interdit dans l'état courant | Lire dans le texte d'échec S1.8 le verrou ouvert |

**Exemple — échec du passage en mode survie :**

```
MCS: Send S8 func_id=0 (AOCS_SET_MODE), mode=1 (safe)

Response:
  S1.2: Acceptance failure (error_code=0x0007)
  Message: "AOCS mode transition rejected: wheels not desaturated"

Troubleshooting:
  1. Check momentum saturation
  2. Send AOCS_DESATURATE (func_id=1)
  3. Wait for DESATURATION_COMPLETE event
  4. Retry AOCS_SET_MODE to safe
```

---

## Aide-mémoire — séquences de commandes courantes {#quick-reference--common-command-sequences}

### Reprise après mode survie (suite à une anomalie) {#safe-mode-recovery-after-anomaly}
```
1. S8 func_id=26 (PAYLOAD_SET_MODE, mode=0 → payload off)
2. S8 func_id=12 (AOCS_BEGIN_ACQUISITION)
3. S8 func_id=0 (AOCS_SET_MODE, mode=1)
4. Verify S5: SAFE_MODE_ENTRY
```

### Délestage (urgence énergétique) {#load-shedding-power-emergency}
```
There is ONE load-shed function; the stage is its argument.
1. S8 func_id=25 (EPS_EMERGENCY_LOAD_SHED), stage=1
2. S8 func_id=25 (EPS_EMERGENCY_LOAD_SHED), stage=2
3. S8 func_id=25 (EPS_EMERGENCY_LOAD_SHED), stage=3
4. Verify S5: LOAD_SHED_STAGE_N events
(func_id 23 is EPS_SET_CHARGE_RATE and 24 is EPS_SOLAR_ARRAY_DRIVE — earlier
 revisions of this document mislabelled 23/24/25 as three shed stages.)
Alternatively S8 func_id=83 (EPS_SET_MODE), mode=1 (safe) or 2 (emergency)
sheds the two least-essential loads, or all of them, in one command.
```

### Désaturation du moment cinétique {#momentum-desaturation}
```
1. S8 func_id=1 (AOCS_DESATURATE)
2. S3 request HK_AOCS (SID=2)
3. Monitor total_momentum until < 80 Nms
4. Verify S5: DESATURATION_COMPLETE
```

### Passage de prise de vue (automatisé) {#imaging-pass-automated}
```
1. S11 subtype 4 (insert time-tagged command)   ← subtype 4, NOT 11
   Data: exec_time_cuc (absolute CUC, from TLE propagation + AOS prediction)
       + the embedded TC: S8.1 func_id=28 (PAYLOAD_CAPTURE)
   Reply: TM(11,5) with the on-board cmd_id
2. Optional: S11 subtype 17 → TM(11,18) to read the schedule back and confirm
   the queued command's apid/service/subtype before the pass
3. Spacecraft executes automatically at the scheduled time
4. Ground downloads via S13 after LOS
(Subtype 11 is DELETE-ALL; sending it here wipes the on-board schedule.)
```

---

## Remarques de mise en œuvre {#implementation-notes}

- Tous les horodatages sont en UTC (temps universel coordonné).
- Le temps bord est entretenu par l'OBDH, de façon synchrone avec le sol.
- Les événements sont ordonnés dans le temps et journalisés dans le stockage S15.
- Les actions S19 s'exécutent immédiatement (sans approbation du sol), à l'exception des
  fonctions 52/53/55/56, critiques pour l'OBC, qui sont bloquées tant que l'OBC est sous le
  chargeur d'amorçage.
- Les violations S12 sont **déclenchées sur front** : une TM(12,9) + un événement S5 à l'entrée et
  une TM(12,10) + un événement S5 au retour. Elles ne se répètent PAS à chaque période de contrôle
  tant que le paramètre reste hors limites.
- Les contrôles S12 sont entièrement neutralisés pour les paramètres dont le sous-système source
  n'est pas alimenté, de sorte qu'un capteur éteint ne génère pas d'alarme de limite.
- La télémesure peut être stockée à bord (S15) si la liaison descendante est indisponible.

---

## Références {#references}

- ECSS-E-ST-70-41C : *Telemetry and Telecommand Packet Utilization Standard*
- Configuration d'EOSAT-1 : `configs/eosat1/commands/tc_catalog.yaml`
- Définitions des événements : `configs/eosat1/events/event_catalog.yaml`
- Règles de surveillance : `configs/eosat1/monitoring/s12_definitions.yaml`
- Règles événement-action : `configs/eosat1/monitoring/s19_rules.yaml`
- Procédures de contrôle bord : `configs/eosat1/obcp/`, `docs/OBCP_GUIDE.md`
- **Mise en œuvre de référence :**
  `packages/smo-simulator/src/smo_simulator/service_dispatch.py` — lorsque ce
  document et le répartiteur divergent, c'est le répartiteur qui a raison.
