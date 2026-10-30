# Séquence complète de recette en orbite d'EOSAT-1 : du satellite éteint aux opérations de charge utile {#eosat-1-full-commissioning-sequence-spacecraft-off--payload-operations}

**Référence :** du démarrage à froid à la recette en orbite complète, étape par étape.
**Révision :** 2.0
**Date :** 2026-04-09

Ce document passe en revue chaque commande et chaque vérification de télémesure, de la première mise sous tension jusqu'à une charge utile prête à l'emploi, en indiquant pour chacune l'écran du MCS sur lequel confirmer le résultat.

---

## Référence des onglets du MCS {#mcs-tab-reference}

| Onglet | Ce qu'il affiche |
|-----|---------------|
| **overview** | Synthèse de la plateforme, santé de tous les sous-systèmes, fenêtres de visibilité, trace au sol |
| **eps** | Lignes d'alimentation, batterie, tension du bus, générateurs solaires, tendance du SoC, niveau de délestage |
| **tcs** | Zones de température, états des réchauffeurs, refroidisseur du FPA, tendances thermiques |
| **aocs** | Machine à états des modes, vitesses angulaires, erreur d'attitude, senseurs stellaires, CSS, rapport cyclique des MTQ, roues de réaction, données orbitales |
| **obdh** | Mode de l'OBC, charge CPU, remplissage des tampons, sw_image, temps de fonctionnement, compteurs de TC/TM |
| **ttc** | État de la liaison, RSSI, marge de liaison, température du PA, verrouillage porteuse/bit/trame, déploiement de l'antenne |
| **payload** | Mode de l'imageur, température du FPA, puissance du refroidisseur, stockage, catalogue d'images |
| **commanding** | Saisie des TC, historique des commandes, journal des acceptations/rejets |
| **pus** | Interface des services PUS (requêtes HK S3, exécution de fonctions S8, temps S9, lecture/écriture de paramètres S20) |
| **ondemand** | Lectures de paramètres S20.3 à la demande |

---

## Phase 0 — Configuration avant contact (sol uniquement) {#phase-0--pre-contact-configuration-ground-only}

Aucune commande satellite. Configurer la station sol.

### 0.1 Configurer la station sol et forcer le passage {#01-configure-ground-station--override-pass}

**Action:** Régler le paramètre de forçage de passage pour imposer `in_contact = True`

**TC:** `SET_PARAM(param_id=0x05FF, value=1)` (Service 20, Subtype 1)

**Écran MCS :** onglet **commanding** → envoyer le SET_PARAM S20 → vérifier l'acceptation dans l'historique des commandes. Le panneau des fenêtres de visibilité de l'onglet **overview** doit afficher « IN CONTACT » dès que le forçage prend effet.

---

## Phase 1 — Premier signal : réception de la télémesure du chargeur d'amorçage {#phase-1--first-signal-bootloader-telemetry-reception}

Le satellite est en mode chargeur d'amorçage (`sw_image = 0`). Seuls l'OBC et le RX TTC sont alimentés. La balise SID 11 est la seule télémesure disponible (7 paramètres, toutes les 30 s). Aucun SID du mode applicatif (1–6) n'est encore actif.

### 1.1 Interroger le satellite (essai de connexion) {#11-ping-the-spacecraft-connection-test}

**TC:** `CONNECTION_TEST` (Service 17, Subtype 1)

**Objet :** vérifie que la liaison montante est reçue. Le maintien automatique de l'émetteur (auto-TX hold-down) se déclenche : le moteur alimente `ttc_tx` pendant 15 minutes dès l'acceptation de toute TC valide.

**Écran MCS :**
- onglet **commanding** → TM d'acceptation S1.1 reçue (ligne verte dans l'historique des commandes)
- onglet **ttc** → `link_status` passe de 0 (NO LINK) à 1 (ACQUIRING) puis à 2 (LOCKED) ; `rssi` remonte de -120 dBm vers > -110 dBm
- onglet **eps** → la ligne d'alimentation `ttc_tx` indique ON (maintien auto-TX activé)

### 1.2 Vérifier la télémesure balise (SID 11) {#12-verify-beacon-telemetry-sid-11}

**TC:** `HK_REQUEST(sid=11)` (Service 3, Subtype 27)

**Objet :** demander le paquet balise du chargeur d'amorçage. C'est la seule HK disponible avant OBC_BOOT_APP.

**Écran MCS — onglet overview** (paramètres de la balise) :

| Paramètre | ID hexa | Attendu | Emplacement sur le MCS |
|-----------|--------|----------|--------------|
| `bat_voltage` | 0x0100 | ~26.4 V | onglet **eps** → panneau Battery |
| `bat_soc` | 0x0101 | ~75 % | onglet **eps** → panneau Battery |
| `obc_mode` | 0x0300 | 0 (pas un indicateur d'amorçage — lire `sw_image`) | onglet **obdh** → champ Mode |
| `reboot_count` | 0x030A | 0 | onglet **obdh** → Reboot Count |
| `sw_image` | 0x0311 | 0 (BOOTLOADER) | onglet **obdh** → champ SW Image |
| `active_obc` | 0x030C | 0 (OBC-A) | onglet **obdh** → Active OBC |
| `spacecraft_phase` | 0x0129 | 3 (BOOTLOADER_OPS) | onglet **overview** → Phase |

**GO/NO-GO:** Balise reçue, `sw_image = 0` confirmé, batterie > 50 %, liaison verrouillée.

**⚠ En cas d'échec de cette étape :** voir [Procédures de contingence de la recette en orbite](10_commissioning_contingency_procedures.md#phase-1--spacecraft-activation) — couvre l'absence de télémesure, la défaillance de liaison et un état inattendu de l'OBC.

---

## Phase 2 — Déploiement de l'antenne {#phase-2--antenna-deployment}

L'antenne est initialement repliée (`antenna_deployment_sensor = 1`). Même si vous disposez peut-être déjà d'un signal via l'antenne repliée, il faut la déployer pour obtenir la pleine marge de liaison.

### 2.1 Déployer l'antenne {#21-deploy-antenna}

**TC:** `TTC_DEPLOY_ANTENNA` (Service 8, Subtype 1, func_id 69)

**Objet :** déclenche le fil thermofusible qui libère l'antenne. Commande à coup unique, sans paramètre.

**Note:** Cette commande appartient à la plage de func_id du TTC (63–78). Elle franchit la condition du chargeur d'amorçage : le sous-ensemble autorisé par le moteur est `{19, 20, 52, 53, 54, 55, 56, 57, 61, 66, 67, 69, 120}`, la func_id 69 est donc acceptée avant OBC_BOOT_APP.

**Écran MCS :**
- onglet **commanding** → acceptation S1.1 + fin d'exécution S1.7
- onglet **ttc** → `antenna_deployed` (0x0520) = 1, `antenna_deployment_sensor` (0x0536) = 2 (DEPLOYED)
- onglet **ttc** → `link_margin` doit s'améliorer (gain accru entre position repliée et déployée)

**Verify:** `rssi` s'améliore, `link_margin` (0x0503) > 3.0 dB.

**GO/NO-GO:** Antenne déployée. Si le capteur indique 3 (PARTIAL/JAMMED), faire remonter l'anomalie — voir la CTG-019 (Absence de télémesure en début de passage).

**⚠ En cas d'échec de cette étape :** voir [Procédures de contingence de la recette en orbite](10_commissioning_contingency_procedures.md#phase-2--antenna-deployment) — couvre l'échec du déploiement, le déploiement partiel et les problèmes de qualité de liaison.

---

## Phase 3 — Amorçage de l'OBC sur l'image applicative {#phase-3--boot-obc-to-application-image}

### 3.1 OBC_BOOT_APP {#31-obc_boot_app}

**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55)

**Objet :** déclenche une vérification CRC de 10 s de l'image applicative, puis la transition du chargeur d'amorçage vers l'application. Ensuite, le jeu complet de commandes PUS devient disponible et les SID du mode applicatif (1–6) s'activent.

**Écran MCS :**
- onglet **commanding** → acceptation S1.1 en moins de 5 s, puis fin d'exécution S1.7 en moins de 15 s
- onglet **obdh** → `sw_image` (0x0311) passe de 0 → 1 (APPLICATION)
- onglet **obdh** → `spacecraft_phase` (0x0129) doit passer de 3 à 4 (LEOP)

**GO/NO-GO:** `sw_image = 1`. Jeu complet de commandes disponible. Si `sw_image` reste à 0, l'image applicative est peut-être corrompue — voir l'action de reprise 2 d'EMG-003.

**⚠ En cas d'échec de cette étape :** voir [Procédures de contingence de la recette en orbite](10_commissioning_contingency_procedures.md#phase-3--obc-boot) — couvre l'échec d'amorçage, l'image corrompue et les boucles de redémarrage.

---

## Phase 4 — Bilan de santé initial de la plateforme {#phase-4--initial-platform-health-check}

Le satellite est désormais en mode applicatif. Tous les SID sont disponibles. Tout vérifier avant de mettre les sous-systèmes sous tension.

### 4.1 Demander toutes les données de servitude {#41-request-all-housekeeping}

**Séquence de TC** (six commandes, envoyables en succession rapide) :

| TC | SID | Sous-système | Onglet MCS |
|----|-----|-----------|---------|
| `HK_REQUEST(sid=1)` (S3.27) | 1 | EPS | **eps** |
| `HK_REQUEST(sid=2)` (S3.27) | 2 | AOCS | **aocs** |
| `HK_REQUEST(sid=3)` (S3.27) | 3 | TCS | **tcs** |
| `HK_REQUEST(sid=4)` (S3.27) | 4 | OBDH/plateforme | **obdh** |
| `HK_REQUEST(sid=5)` (S3.27) | 5 | Charge utile | **payload** |
| `HK_REQUEST(sid=6)` (S3.27) | 6 | TTC | **ttc** |

### 4.2 Vérifier l'état d'alimentation EPS {#42-verify-eps-power-status}

**Écran MCS : onglet eps**

| Paramètre | ID hexa | Valeur attendue au démarrage à froid | Contrôle |
|-----------|--------|--------------------------|-------|
| `bus_voltage` | 0x0105 | 28.2 V (régulée) | ∈ [27.0, 29.5] V |
| `bat_voltage` | 0x0100 | ~26.4 V | ∈ [24.0, 28.0] V |
| `bat_soc` | 0x0101 | ~75 % | > 50 % |
| `bat_temp` | 0x0102 | ~15 °C | ∈ [0, 35] °C |
| `power_gen` | 0x0107 | dépend du Soleil | > 0 W si éclairé |
| `power_cons` | 0x0106 | ~8 W (OBC 6 W + RX 1,5 W) | < 30 W |
| `eclipse_flag` | 0x0108 | 0 ou 1 | à noter pour le contexte |

### 4.3 Vérifier l'état des commutateurs des lignes d'alimentation {#43-verify-power-line-switch-states}

**Écran MCS : onglet eps → panneau Power Lines**

| Ligne | Indice | ID hexa | Attendu | Remarques |
|------|-------|--------|----------|-------|
| obc | 0 | 0x0110 | ON (1) | Non commutable |
| ttc_rx | 1 | 0x0111 | ON (1) | Non commutable |
| ttc_tx | 2 | 0x0112 | ON (1) | Maintien auto-TX actif |
| payload | 3 | 0x0113 | OFF (0) | Pas encore alimentée |
| fpa_cooler | 4 | 0x0114 | OFF (0) | Pas encore alimentée |
| htr_bat | 5 | 0x0115 | OFF (0) | Pas encore alimentée |
| htr_obc | 6 | 0x0116 | OFF (0) | Pas encore alimentée |
| aocs_wheels | 7 | 0x0117 | OFF (0) | Pas encore alimentée |

Toutes les lignes sur OFF sont attendues — elles n'ont pas encore été mises sous tension.

### 4.4 Vérifier l'état de l'OBDH {#44-verify-obdh-status}

**Écran MCS : onglet obdh**

| Paramètre | ID hexa | Attendu |
|-----------|--------|----------|
| `obc_mode` | 0x0300 | 0 (NOMINAL) |
| `cpu_load` | 0x0302 | ~35 % de base |
| `sw_image` | 0x0311 | 1 (APPLICATION) |
| `reboot_count` | 0x030A | 0 |
| `active_obc` | 0x030C | 0 (OBC-A) |
| `active_bus` | 0x030E | 0 (bus CAN A) |
| `bus_a_status` | 0x030F | 0 (OK) |

### 4.5 Vérifier la qualité de la liaison TTC {#45-verify-ttc-link-quality}

**Écran MCS : onglet ttc**

| Paramètre | ID hexa | Attendu |
|-----------|--------|----------|
| `link_status` | 0x0501 | 2 (LOCKED) |
| `rssi` | 0x0502 | > -110 dBm |
| `link_margin` | 0x0503 | > 3.0 dB |
| `carrier_lock` | 0x050F | 1 |
| `bit_sync` | 0x0510 | 1 |
| `frame_sync` | 0x0511 | 1 |
| `antenna_deployed` | 0x0520 | 1 (si la phase 2 est faite) |

### 4.6 Vérifier les températures de référence du TCS {#46-verify-tcs-baseline-temperatures}

**Écran MCS : onglet tcs → tableau Temperature Zones**

| Paramètre | ID hexa | Attendu (ambiante) | Plage acceptable |
|-----------|--------|---------------------|-----------------|
| `temp_obc` | 0x0406 | ~20 °C | [-5, +45] °C |
| `temp_battery` | 0x0407 | ~15 °C | [0, +35] °C |
| `temp_fpa` | 0x0408 | ~+11.5 °C (ambiante interne, non refroidi) | [-22.0, +14.0] °C (bande jaune) |
| Températures des panneaux | 0x0400–0x0405 | plage 8–20 °C | [-40, +60] °C |

### 4.7 Vérifier que l'AOCS et la charge utile sont éteints {#47-verify-aocs-and-payload-are-off}

**Écran MCS : onglet aocs** → `mode` (0x020F) = 0 (OFF). Roues non alimentées.
**Écran MCS : onglet payload** → `mode` (0x0600) = 0 (OFF). C'est l'état attendu.

**GO/NO-GO:** Plateforme saine. Tension du bus nominale, batterie chargée, OBC en mode applicatif, liaison verrouillée, températures dans la plage, tous les sous-systèmes non alimentés confirmés sur OFF.

**⚠ En cas d'échec de cette étape :** voir [Procédures de contingence de la recette en orbite](10_commissioning_contingency_procedures.md#phase-4--health-check) — couvre les anomalies de tension, les dépassements thermiques et les défauts de bus.

---

## Phase 5 — Activation de la mise en mémoire de la télémesure (TM stockée) {#phase-5--enable-telemetry-buffering-stored-tm}

### 5.1 Activer les rapports HK périodiques pour tous les SID {#51-enable-periodic-hk-reporting-for-all-sids}

**Séquence de TC :**

| TC | SID | Période |
|----|-----|----------|
| `HK_ENABLE(sid=1)` (S3.5) | EPS | 1.0 s |
| `HK_ENABLE(sid=2)` (S3.5) | AOCS | 4.0 s |
| `HK_ENABLE(sid=3)` (S3.5) | TCS | 60.0 s |
| `HK_ENABLE(sid=4)` (S3.5) | OBDH | 8.0 s |
| `HK_ENABLE(sid=5)` (S3.5) | Charge utile | 8.0 s |
| `HK_ENABLE(sid=6)` (S3.5) | TTC | 8.0 s |

**Écran MCS :**
- onglet **commanding** → les six acceptations S1.1
- tous les onglets des sous-systèmes doivent désormais afficher des valeurs **mises à jour en direct** (plus besoin de HK_REQUEST manuel)
- onglet **obdh** → les niveaux de remplissage des tampons (`hk_store` 0x0312) doivent commencer à augmenter à mesure que les paquets sont stockés pour relecture hors visibilité

**Objet :** une fois les HK activées, l'OBC stocke la télémesure dans le tampon de la mémoire de masse, même hors contact. Vous pourrez la récupérer plus tard par un vidage de TM S15. Chaque onglet de sous-système dispose pour cela d'un bouton « Request S15 TM Dump ».

---

## Phase 6 — Réglage du temps bord {#phase-6--set-on-board-time}

### 6.1 Demander le temps courant {#61-request-current-time}

**TC:** `REQUEST_TIME` (Service 9, Subtype 2)

**Écran MCS : onglet obdh** → le champ OBC Time (CUC) affiche l'horloge de bord courante. Avant SET_TIME, il affiche « 0 (not set) ». L'horloge SC TIME de la barre d'état supérieure affiche « NOT SET ».

### 6.2 Envoyer le temps corrigé {#62-upload-corrected-time}

Deux options dans le panneau **onglet obdh → TIME CORRELATION (S9)** :

**Option A — synchroniser sur l'UTC sol :**
cliquer sur le bouton « Sync Time to Ground ». Il envoie `SET_TIME(cuc_seconds=<ground_utc>)`, où l'UTC sol tient compte de l'époque de simulation du MCS si elle est configurée.

**Option B — régler une heure arbitraire :**
saisir un horodatage ISO 8601 (p. ex. `2026-03-10T12:00:00Z`) dans le champ « Set Arbitrary Time ». L'équivalent CUC s'affiche sous le champ. Cliquer sur « Set SC Time » pour envoyer la S9.1.

**TC:** `SET_TIME(cuc_seconds=<UTC_epoch>)` (Service 9, Subtype 1)

**Écran MCS :**
- onglet **commanding** → acceptation S1.1
- onglet **obdh** → `OBC Time (CUC)` affiche désormais l'horodatage UTC réglé
- **barre supérieure** → l'horloge SC TIME se met à jour et affiche le temps bord (HH:MM:SS UTC)
- `uptime` (0x0308) continue de s'incrémenter indépendamment
- redemander `REQUEST_TIME` pour vérifier que l'écart sol–satellite est < 1.0 s

**GO/NO-GO:** Horloge de bord synchronisée sur l'UTC à 1 seconde près. Horloge SC TIME active.

---

## Phase 7 — Mise sous tension séquentielle (réchauffeurs d'abord, puis AOCS) {#phase-7--sequential-power-on-heaters-first-then-aocs}

Cette phase suit l'ordre de LEOP-007. Chaque étape consiste en une mise sous tension de ligne suivie d'une commande de mode.

### 7.1 Réchauffeur de batterie sous tension {#71-battery-heater-on}

**TC:** `EPS_POWER_ON(line_idx=5)` (S8.1, func_id 19, data byte = 5)

**Note:** Le réchauffeur de batterie est commandé par thermostat — la ligne d'alimentation EPS doit être sur ON pour que le thermostat fonctionne. Une fois la ligne alimentée, le réchauffeur fonctionne automatiquement en cycle entre 1 °C (seuil de mise en marche) et 5 °C (seuil d'arrêt).

**Écran MCS :**
- onglet **eps** → ligne d'alimentation `htr_bat` (0x0115) = 1 (ON)
- onglet **eps** → `power_cons` augmente d'environ 6 W
- onglet **tcs** → `htr_battery` (0x040A) = 1 (actif lorsque le thermostat demande de la chaleur), `temp_battery` (0x0407) tend vers la consigne

### 7.2 Réchauffeur de l'OBC sous tension {#72-obc-heater-on}

**TC:** `EPS_POWER_ON(line_idx=6)` (S8.1, func_id 19, data byte = 6)

**Note:** Le réchauffeur de l'OBC se commande uniquement à la main — il reste en marche tant que la ligne d'alimentation EPS est sur ON. Pas de thermostat.

**Écran MCS :**
- onglet **eps** → ligne d'alimentation `htr_obc` (0x0116) = 1 (ON)
- onglet **eps** → `power_cons` augmente d'environ 3 W
- onglet **tcs** → `htr_obc` (0x040B) = 1 (actif)

### 7.3 Alimentation des roues AOCS {#73-aocs-wheels-power-on}

**TC:** `EPS_POWER_ON(line_idx=7)` (S8.1, func_id 19, data byte = 7)

**Note:** Cette commande alimente l'électronique des roues. Les roues ne sont pas encore actives individuellement — utiliser `AOCS_ENABLE_WHEEL` pour activer chaque roue une à une.

**Écran MCS :**
- onglet **eps** → ligne d'alimentation `aocs_wheels` (0x0117) = 1 (ON)
- onglet **eps** → `power_cons` augmente d'environ 12 W

### 7.3a Activer les roues de réaction une à une {#73a-enable-individual-reaction-wheels}

Activer chaque roue individuellement (seules 3 roues sur 4 sont nécessaires à une solution de contrôle) :

**Séquence de TC :**
- `AOCS_ENABLE_WHEEL(wheel_idx=0)` (S8.1, func_id 3, data byte = 0) — RW1
- `AOCS_ENABLE_WHEEL(wheel_idx=1)` (S8.1, func_id 3, data byte = 1) — RW2
- `AOCS_ENABLE_WHEEL(wheel_idx=2)` (S8.1, func_id 3, data byte = 2) — RW3
- `AOCS_ENABLE_WHEEL(wheel_idx=3)` (S8.1, func_id 3, data byte = 3) — RW4

Pour désactiver une roue donnée : `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8.1, func_id 2, data byte = N)

**Écran MCS : onglet aocs**
- Les indicateurs des roues de réaction passent au vert pour les roues activées
- Les vitesses des roues (0x0207–0x020A) affichent de faibles valeurs (bruit de frottement) une fois activées
- Les roues n'atteignent une vitesse significative que lorsque le contrôleur AOCS est actif (DETUMBLE ou supérieur)

**Note:** Tant que l'AOCS reste en mode OFF, les vitesses angulaires et les données YPR affichent 0 (aucune détermination d'attitude active). C'est normal — l'AOCS doit être dans un mode actif pour fournir les vitesses.

### 7.4 Mode AOCS : DETUMBLE {#74-aocs-set-mode-detumble}

**TC:** `AOCS_SET_MODE(mode=2)` (S8.1, func_id 0, data byte = 2)

**Note:** La func_id 0 de l'AOCS (`set_mode`) bénéficie d'une **exemption de la condition de mode** — elle est admise même lorsque le mode du sous-système AOCS est OFF/0, précisément pour permettre cette transition de mode initiale.

**Écran MCS : onglet aocs**
- La machine à états des modes montre la transition vers DETUMBLE (mode 2)
- Les vitesses angulaires (0x0204–0x0206) doivent être visibles et orientées à la baisse
- L'erreur d'attitude (0x0217) est affichée
- Le rapport cyclique des magnétocoupleurs (MTQ X/Y/Z) devient non nul lorsque le contrôleur B-dot s'engage

**Surveiller pendant plusieurs minutes :** les vitesses doivent décroître depuis le culbutage initial jusqu'à < 0.5°/s en 15 minutes.

### 7.5 Vérifier le bilan de puissance après la mise sous tension de l'AOCS {#75-verify-power-budget-after-aocs-power-on}

**Écran MCS : onglet eps**

| Paramètre | Attendu après l'étape 7.3 |
|-----------|------------------------|
| `power_cons` | ~40 W (OBC ~6 W + RX ~1,5 W + TX ~11 W + réchauffeurs ~9 W + roues ~12 W) |
| `bus_voltage` | > 27.0 V |
| `bat_soc` | toujours > 60 % |
| `power_gen` - `power_cons` | marge positive si éclairé |

**GO/NO-GO:** Tous les réchauffeurs actifs, AOCS en DETUMBLE, bilan de puissance positif.

**⚠ En cas d'échec de cette étape :** voir [Procédures de contingence de la recette en orbite](10_commissioning_contingency_procedures.md#phase-7--power-on-subsystems) — couvre la surintensité, le mode survie EPS, les anomalies de roues et les échecs de mode AOCS.

---

## Phase 8 — Envoi du TLE pour la restitution d'orbite {#phase-8--upload-tle-for-orbit-determination}

### 8.1 Envoyer le TLE / vecteur d'état orbital {#81-upload-tle--orbit-state-vector}

**Outil :** utiliser les outils d'orbite pour convertir un TLE ou un vecteur d'état au format de commande S20.1 :

```bash
# TLE mode — propagate to a specific epoch
python3 tools/orbit_tools.py --tle "1 99999U ..." "2 99999 ..." --epoch 2026-03-10T12:00:00

# State vector mode — direct ECEF position/velocity (meters, m/s)
python3 tools/orbit_tools.py --sv 6878000 0 0 0 7612 0

# Web interface (interactive form with TLE and state vector tabs)
python3 tools/orbit_tools.py --serve  # opens on port 8093
```

L'outil produit des chaînes de commande hexadécimales pour des commandes SET_PARAM S20.1 visant :
- 0x0231–0x0233 : position ECEF GPS X/Y/Z (mètres)
- 0x0234–0x0236 : vitesse ECEF GPS X/Y/Z (m/s)

**Séquence de TC** (6 × SET_PARAM S20.1 — copier les chaînes hexadécimales de la sortie d'orbit_tools) :

**Écran MCS :**
- onglet **pus** ou onglet **ondemand** → envoyer les commandes SET_PARAM S20
- onglet **aocs** → panneau Orbital Data → latitude, longitude et altitude doivent se remplir avec les valeurs propagées
- onglet **aocs** → le champ Eclipse doit désormais prédire les transitions éclipse/éclairement

---

## Phase 9 — Progression des modes AOCS : amortissement des vitesses → pointage solaire → nadir {#phase-9--aocs-mode-progression-rate-damping--sun-pointing--nadir}

### 9.1 Confirmer l'amortissement des vitesses {#91-confirm-rates-damped}

**Écran MCS : onglet aocs** → panneau Body Rates

| Paramètre | ID hexa | Cible |
|-----------|--------|--------|
| `rate_roll` | 0x0204 | < 0.5°/s |
| `rate_pitch` | 0x0205 | < 0.5°/s |
| `rate_yaw` | 0x0206 | < 0.5°/s |

Consulter aussi le **graphique BODY RATES** (en bas de l'onglet aocs) pour confirmer la tendance — les vitesses doivent présenter une courbe de décroissance nette.

### 9.2 Observer la transition AUTOMATIQUE vers COARSE_SUN (pointage sûr) {#92-observe-the-automatic-transition-to-coarse_sun-safe-pointing}

**Aucune TC.** Une fois que les vitesses angulaires sont restées sous 0.5°/s pendant 30 s, l'AOCS passe
de lui-même de DETUMBLE à COARSE_SUN — c'est une transition AUTOMATIQUE
(`docs/plan_2026-08c/AOCS_MODE_TRANSITIONS.md` §1.2). Ne pas commander le mode 3
ici : ce serait commander le mode dans lequel le satellite est sur le point d'entrer de
lui-même. COARSE_SUN est de même une ATTENTE transitoire, jamais une destination — dès qu'un
senseur stellaire est en poursuite (phase 12), l'AOCS passe automatiquement au mode commandé ; ne
jamais « vérifier mode = 3 » quelques minutes après la tenue du verrouillage.

**Écran MCS : onglet aocs**
- La machine à états des modes indique COARSE_SUN (mode 3), atteint sans commande
- `att_error` (0x0217) doit décroître vers < 15° en 10 minutes
- Le panneau CSS Sun Vector affiche un vecteur Soleil valide (composantes X/Y/Z)
- onglet **eps** → `power_gen` doit augmenter à mesure que les générateurs font face au Soleil

### 9.3 Télécharger la TM différée — premier contrôle sur une orbite complète {#93-download-delayed-tm--first-whole-orbit-check}

**Action:** Utiliser les boutons de vidage de TM S15 de chaque onglet de sous-système pour récupérer la télémesure stockée.

**Écran MCS :** chaque onglet dispose d'un bouton « Request S15 TM Dump » :
- onglet **aocs** → le bouton de vidage récupère les données AOCS stockées → contrôler le graphique des vitesses angulaires sur l'orbite complète
- onglet **eps** → bouton de vidage → contrôler la courbe du SoC sur le cycle éclipse/éclairement et la stabilité de la tension du bus
- onglet **tcs** → bouton de vidage → contrôler les profils de température sur l'orbite
- onglet **obdh** → bouton de vidage → rechercher d'éventuels événements/alarmes pendant la période d'ombre

**Points à examiner :**
- les vitesses angulaires sont restées amorties (pas de pic soudain) ;
- les températures sont restées dans la plage pendant l'éclipse ;
- le SoC de la batterie s'est rétabli après la sortie d'éclipse ;
- aucun redémarrage ni événement inattendu ;
- l'AOCS a maintenu le pointage pendant l'éclipse (le mode ECLIPSE (8) doit s'engager automatiquement).

### 9.4 Contrôler les signes et facteurs d'échelle de l'AOCS {#94-check-aocs-signs-and-scaling}

Avec les données d'une orbite complète, vérifier que :
- les vitesses des roues respectent la convention de signe (positif = rotation avant) ;
- les mesures du magnétomètre correspondent au modèle de champ attendu pour l'orbite ;
- le vecteur Soleil des CSS pointe vers le Soleil au moment attendu ;
- l'erreur d'attitude est corrélée à la production de puissance (erreur plus faible → puissance plus élevée).

**Écran MCS : onglet aocs** — recouper à l'aide des graphiques Body Rates et Attitude Error.

### 9.5 Transition vers NOMINAL (pointage nadir) {#95-transition-to-nominal-nadir-pointing}

**TC:** `AOCS_SET_MODE(mode=4)` (S8.1, func_id 0, data byte = 4)

**Écran MCS : onglet aocs**
- Mode = 4 (NOMINAL)
- `att_error` (0x0217) → < 1.0° en 2 minutes, puis < 0.1° une fois stabilisé
- Les vitesses des roues de réaction s'ajustent pour maintenir le pointage nadir
- onglet **eps** → `power_gen` doit être proche du maximum avec un angle solaire optimal

**GO/NO-GO:** Pointage nadir atteint, erreur d'attitude < 1°, stable sur plusieurs orbites.

**⚠ En cas d'échec de cette étape :** voir [Procédures de contingence de la recette en orbite](10_commissioning_contingency_procedures.md#phase-9--aocs-mode-progression-detumble--nadir--sun-point) — couvre l'échec de l'amortissement des vitesses, la perte de capteurs et les problèmes de transition de mode.

---

## Phase 10 — Vérification complémentaire des données sur une orbite complète {#phase-10--further-whole-orbit-data-verification}

### 10.1 Attendre une orbite complète, puis refaire un vidage {#101-wait-for-full-orbit-then-dump-again}

**Action:** Laisser le satellite effectuer au moins une orbite complète (~95 min) en pointage nadir, puis vider de nouveau toute la TM stockée.

**Écran MCS** — pour chaque onglet de sous-système, demander un vidage S15 et vérifier :

| Contrôle | Onglet | Points à examiner |
|-------|-----|-----------------|
| Stabilité thermique | **tcs** | Toutes les températures restent dans la plage, cyclage des réchauffeurs conforme |
| Équilibre de puissance | **eps** | Bilan énergétique moyen sur l'orbite positif, SoC en remontée |
| Stabilité d'attitude | **aocs** | att_error < 1° en permanence, aucune transition de mode |
| Santé de l'OBC | **obdh** | Charge CPU stable, aucun redémarrage, tampon sans remplissage excessif |
| Qualité de liaison | **ttc** | RSSI/marge réguliers pendant les passages sol |

### 10.2 Contrôler les événements et les alarmes {#102-check-events-and-alarms}

**Écran MCS : onglet overview** → le panneau des alarmes affiche les alarmes actives. Il doit y en avoir zéro.

**Écran MCS : onglet obdh** → contrôler le nombre d'événements FDIR. Si des événements S5 ont été générés pendant l'orbite, les analyser.

---

## Phase 11 — Activation du GPS et vérification du démarrage à froid {#phase-11--enable-gps-and-verify-cold-start}

### 11.1 Activer le récepteur GPS {#111-enable-gps-receiver}

**TC:** `S2_AOCS_GPS_RECEIVER(device_id=0x020F, state=1)` (S2.1) — mise sous tension du récepteur GPS

**Écran MCS : onglet aocs → panneau Orbital Data**
- L'état du point GPS doit progresser : 0 (pas de point) → 1 (2D) → 2 (3D) → 3 (3D + vitesse)
- `gps_num_sats` doit augmenter de 0 vers ≥ 4
- Latitude, longitude et altitude doivent se remplir avec des valeurs réelles
- Un démarrage à froid peut demander 5–15 minutes avant le premier point

**Vérifier dans l'onglet aocs :**

| Paramètre | ID hexa | Cible |
|-----------|--------|--------|
| Point GPS | 0x0274 | 3 (3D + vitesse) |
| Satellites | 0x0276 | ≥ 4 |
| Altitude | 0x0212 | ~513 km ± 20 km |

**GO/NO-GO:** GPS verrouillé, position cohérente avec l'orbite propagée à partir du TLE.

### 11.2 Synchroniser l'horloge de bord sur le temps GPS {#112-synchronise-onboard-clock-with-gps-time}

**TC:** `OBC_GPS_TIME_SYNC` (S8.1, func_id 80)

**Prérequis :** type de point GPS ≥ 2 (point 3D). La commande est rejetée si le point GPS est insuffisant.

**ATTENTION :** un grand saut de temps (> 5 secondes d'écart entre l'ancien temps bord et le temps GPS) amène l'AOCS à voir le satellite à un autre point de l'orbite. L'AOCS passe automatiquement en mode SAFE_BOOT (mode 1) et doit être réinitialisé en reparcourant la progression des modes (DETUMBLE → COARSE_SUN → NOMINAL).

**Écran MCS :**
- onglet **commanding** → acceptation S1.1
- onglet **obdh** → `OBC Time (CUC)` se met à jour sur l'UTC issu du GPS
- **barre supérieure** → l'horloge SC TIME affiche le temps synchronisé sur le GPS
- Si le saut de temps est > 5 s : onglet **aocs** → le mode retombe en SAFE_BOOT (1), événement S5 0x020F généré
- Après la synchronisation GPS, rétablir le pointage AOCS : refaire la phase 9 (DETUMBLE → COARSE_SUN → NOMINAL)

---

## Phase 12 — Recette en orbite des senseurs stellaires {#phase-12--star-tracker-commissioning}

### 12.1 Mettre sous tension le senseur stellaire 1 {#121-power-on-star-tracker-1}

**TC:** `ST1_POWER(on=1)` (S8.1, func_id 4, data byte = 1)

**Écran MCS : onglet aocs → panneau Star Trackers**
- `ST1 Status` passe de OFF à ACQUIRING, puis à TRACKING
- `ST1 Stars` doit indiquer ≥ 5 étoiles suivies en 90 s
- `att_error` (0x0217) doit s'améliorer (le senseur stellaire offre une précision de l'ordre de la seconde d'arc)

### 12.2 Mettre sous tension le senseur stellaire 2 (redondant) {#122-power-on-star-tracker-2-redundant}

**TC:** `ST2_POWER(on=1)` (S8.1, func_id 5, data byte = 1)

**Écran MCS : onglet aocs → panneau Star Trackers**
- `ST2 Status` passe à TRACKING
- Recoupement : les deux senseurs doivent s'accorder sur l'attitude

### 12.3 Sélectionner le senseur stellaire principal {#123-select-primary-star-tracker}

**TC:** `ST_SELECT(unit=1)` (S8.1, func_id 6, data byte = 1) — sélectionner ST1 comme principal

### 12.4 Couper ST2 (retour au nominal — un seul senseur actif) {#124-power-off-st2-return-to-nominal--one-tracker-active}

**TC:** `ST2_POWER(on=0)` (S8.1, func_id 5, data byte = 0)

Le bon fonctionnement de ST2 est désormais vérifié ; revenir à l'exploitation sur un seul senseur pour économiser de la puissance. ST2 reste disponible comme secours actif.

### 12.5 Transition vers FINE_POINT {#125-transition-to-fine_point}

**TC:** `AOCS_SET_MODE(mode=5)` (S8.1, func_id 0, data byte = 5)

**Écran MCS : onglet aocs**
- Mode = 5 (FINE_POINT)
- `att_error` < 0.1° en 3 minutes
- Vitesses angulaires < 0.01°/s sur tous les axes

**GO/NO-GO:** Pointage fin atteint avec le senseur stellaire. C'est la précision de pointage nécessaire à la prise de vue.

**⚠ En cas d'échec de cette étape :** voir [Procédures de contingence de la recette en orbite](10_commissioning_contingency_procedures.md#phase-12--star-tracker-checkout) — couvre l'expiration du délai d'amorçage du senseur, l'éblouissement et la panne du senseur.

---

## Phase 13 — Vérification des équipements redondants {#phase-13--redundant-equipment-checkout}

### 13.1 Contrôle du bus CAN de secours {#131-backup-can-bus-check}

**TC:** `OBC_SELECT_BUS(bus=1)` (S8.1, func_id 54, data byte = 1) — basculer sur le bus B

**Écran MCS : onglet obdh**
- `active_bus` (0x030E) = 1 (bus B)
- `bus_b_status` (0x0310) = 0 (OK)
- Les HK de tous les sous-systèmes doivent continuer d'arriver (vérifier que tous les onglets se mettent toujours à jour)

**TC:** `OBC_SELECT_BUS(bus=0)` (S8.1, func_id 54, data byte = 0) — revenir au bus A

**Verify:** `active_bus` = 0, `bus_a_status` (0x030F) = 0 (OK)

### 13.2 Contrôle du transpondeur redondant {#132-redundant-transponder-check}

**TC:** `TTC_SWITCH_REDUNDANT` (func_id 64)

**Écran MCS : onglet ttc**
- `ttc_mode` (0x0500) = 1 (REDUNDANT)
- `link_status` réacquiert le verrouillage
- `rssi` à moins de 2 dB du principal

**TC:** `TTC_SWITCH_PRIMARY` (func_id 63) — revenir au principal

**Verify:** `ttc_mode` = 0, liaison verrouillée.

### 13.3 Contrôle de santé du magnétomètre (non redondé — aucune redondance à exercer) {#133-magnetometer-health-check-single-string--no-redundancy-to-exercise}

EOSAT-1 n'embarque QU'UN magnétomètre 3 axes (décision du propriétaire 2026-08c) — comme pour les
gyromètres, il n'y a ni rechange ni MAG_SELECT. Cette étape vérifie que l'unique unité est
saine au lieu d'exercer un basculement qui n'existe pas. (Une commande `MAG_SELECT` obsolète
— S8, fonction 7 — est désormais refusée avec un code explicatif 0x0007.)

**Écran MCS : onglet aocs** → `aocs.mag_enabled` (0x025C) = 1 ; `aocs.mag_x/y/z`
(0x020B-0D) vraisemblables par rapport au champ IGRF à la position courante ;
`aocs.mag_field_total` (0x0277) entre 20 000 et 55 000 nT sur l'orbite d'environ 513 km.

**GO/NO-GO:** Magnétomètre sain. Une défaillance ici est une dégradation au niveau de la
mission (la loi B-dot et la désaturation magnétique deviennent aveugles) — la signaler, ne pas
la contourner.

**⚠ En cas d'échec de cette étape :** voir [Procédures de contingence de la recette en orbite](10_commissioning_contingency_procedures.md#phase-13--redundancy-checkout) — couvre l'échec du basculement de bus, les problèmes de transpondeur et la perte des communications.

---

## Phase 14 — Vérification des télécommandes datées {#phase-14--time-tagged-command-verification}

### 14.1 Envoyer une télécommande datée d'essai {#141-upload-a-test-time-tagged-command}

**TC:** Envoi via le service 11 — une commande sans conséquence (p. ex. `HK_REQUEST(sid=1)`) programmée à une heure future connue (p. ex. dans 5 minutes).

**Écran MCS : onglet commanding** → l'historique des commandes doit montrer l'envoi S11 accepté.

### 14.2 Vérifier l'exécution pendant le passage {#142-verify-execution-in-pass}

**Surveiller :** à l'heure programmée, guetter l'arrivée automatique du paquet HK S3.27.

**Écran MCS :**
- onglet **commanding** → la télécommande datée affiche l'état « EXECUTED »
- onglet **eps** → des données HK EPS fraîches arrivent à l'heure programmée

### 14.3 Vérifier l'exécution hors passage {#143-verify-execution-out-of-pass}

**Action:** Envoyer une autre télécommande datée programmée pendant une interruption de la couverture. Après le contact suivant, vider la TM stockée et vérifier que la commande s'est exécutée.

**Écran MCS :** après le rétablissement du contact :
- onglet **obdh** → le vidage de TM S15 montre que le paquet HK a été généré à l'heure programmée
- onglet **commanding** → exécution datée confirmée dans le journal des événements stocké

**GO/NO-GO:** La commande datée fonctionne aussi bien en visibilité qu'hors visibilité.

**⚠ En cas d'échec de cette étape :** voir [Procédures de contingence de la recette en orbite](10_commissioning_contingency_procedures.md#phase-14--time-tagged-commands) — couvre l'échec d'exécution du plan et les anomalies de TEB.

---

## Phase 15 — Mise sous tension et recette en orbite de la charge utile {#phase-15--payload-power-on-and-commissioning}

### 15.1 Alimenter la ligne de la charge utile {#151-power-payload-line}

**TC:** `EPS_POWER_ON(line_idx=3)` (S8.1, func_id 19, data byte = 3)

**Écran MCS :**
- onglet **eps** → ligne d'alimentation `payload` (0x0113) = 1 (ON)
- onglet **eps** → `power_cons` augmente d'environ 8–10 W

### 15.2 Passer la charge utile en STANDBY {#152-set-payload-to-standby}

**TC:** `PAYLOAD_SET_MODE(mode=1)` (S8.1, func_id 26, data byte = 1)

**Note:** La func_id 26 de la charge utile bénéficie d'une **exemption de la condition de mode** — elle est admise même lorsque le mode de la charge utile est OFF/0, afin de permettre cette transition initiale.

**Écran MCS : onglet payload**
- `mode` (0x0600) = 1 (STANDBY)
- `imager_temp` (0x0603) renseigné (~20 °C ambiante)
- `store_used` (0x0604) = 0 %
- `data_rate` (0x0608) renseigné

### 15.3 Alimenter le refroidisseur du FPA {#153-power-fpa-cooler}

**TC:** `EPS_POWER_ON(line_idx=4)` (S8.1, func_id 19, data byte = 4)

**Écran MCS :**
- onglet **eps** → ligne d'alimentation `fpa_cooler` (0x0114) = 1 (ON)
- onglet **eps** → `power_cons` augmente d'environ 8–12 W

### 15.4 Activer le refroidisseur du FPA {#154-activate-fpa-cooler}

**TC:** `FPA_COOLER(on=1)` (S8.1, func_id 43, data byte = 1) — octets transmis `2B 01`

Pour réguler à une température autre que la valeur par défaut de -15 °C, enchaîner avec
`PAYLOAD_COOLER_SETPOINT(setpoint = -10.00 degC)` (S8.1, func_id 36) — octets transmis
`24 66 CB`. La consigne est transmise en **centikelvins** non signés
(`raw = (T_degC + 273.15) x 100`), si bien qu'une valeur Celsius négative ne
nécessite jamais de valeur brute en complément à deux. Relecture : `payload.fpa_setpoint` (0x0631).

**Écran MCS : onglet tcs**
- `cooler_fpa` (0x040C) = 1 (ACTIVE)
- **onglet payload** → `fpa_temp` (0x0601) commence à baisser depuis l'ambiante vers la consigne de -15 °C

**Suivi de la mise en froid dans l'onglet payload (température du FPA) et l'onglet tcs (état du refroidisseur) :**
- T+5 min : < +15 °C
- T+10 min : < 0 °C
- T+20 min : < -10 °C
- T+30 min : stable à -15 °C ± 2 °C

### 15.5 Première lumière — prise d'une image d'essai {#155-first-light--capture-test-image}

Prérequis : AOCS en FINE_POINT (phase 12.5), FPA stable à la consigne.

**TC:** `PAYLOAD_SET_MODE(mode=2)` (S8.1, func_id 26, data byte = 2) — mode IMAGING

**Écran MCS : onglet payload**
- `mode` (0x0600) = 2 (IMAGING)

**TC:** `PAYLOAD_CAPTURE(scene_id=1, lines=2048)` (S8.1, func_id 28) — déclencher la prise d'image  
**Octets émis :** `1C 00 01 08 00`

Le OÙ est fixé par le QUAND : programmer cette TC avec S11.4 au survol de la
cible. La géolocalisation n'est **pas** un argument — le satellite inscrit la
latitude/longitude du point subsatellite dans l'entrée du catalogue d'images à l'ouverture de l'obturateur, à partir
de l'éphéméride propagée, exactement comme le fait un véritable imageur à balayage de lignes.
`scene_id` 0 laisse la charge utile attribuer l'identifiant automatiquement ; un identifiant attribué par le sol permet au
même plan de réserver à l'avance la descente (`PAYLOAD_DOWNLOAD_IMAGE` y fait référence).

**Écran MCS : onglet payload**
- `image_count` (0x0605) passe à 1
- `store_used` (0x0604) augmente (50–200 Mo par image)
- `scene_id` (0x0606) prend la valeur de la scène acquise

**TC:** `PAYLOAD_SET_MODE(mode=1)` (S8.1, func_id 26, data byte = 1) — retour en STANDBY

**GO/NO-GO:** Première image acquise. La télécharger et en contrôler la qualité au sol.

**⚠ En cas d'échec de cette étape :** voir [Procédures de contingence de la recette en orbite](10_commissioning_contingency_procedures.md#phase-15--payload-commissioning) — couvre la défaillance d'alimentation de la charge utile, les problèmes de refroidissement du FPA et l'échec de la prise d'image.

---

## Phase 16 — Configuration finale et remise aux opérations nominales {#phase-16--final-configuration-and-handover-to-nominal-ops}

### 16.1 Vérification finale du bilan de puissance {#161-final-power-budget-verification}

**Écran MCS : onglet eps**

| Paramètre | Attendu (recette en orbite achevée) |
|-----------|------------------------------|
| `power_cons` | ~65–80 W (tous les sous-systèmes sous tension) |
| `power_gen` | > 40 W en éclairement (ailes déployées, ~64 W en crête) |
| Marge | positive en moyenne sur l'orbite |
| `bat_soc` | > 60 % et stable/en charge |

### 16.2 Confirmer l'état de tous les sous-systèmes {#162-confirm-all-subsystem-states}

**Écran MCS : onglet overview** — tous les indicateurs de santé des sous-systèmes doivent être nominaux (verts).

| Sous-système | État attendu |
|-----------|---------------|
| OBC | NOMINAL (mode 0), sw_image = 1 |
| EPS | Les 8 lignes d'alimentation sur ON, marge positive |
| AOCS | FINE_POINT (mode 5), att_error < 0.1° |
| TCS | Tous les réchauffeurs en cyclage normal, refroidisseur du FPA actif |
| TTC | Transpondeur principal, liaison verrouillée |
| Charge utile | STANDBY (mode 1), FPA à la consigne |

### 16.3 Passer la phase du satellite à NOMINAL {#163-set-spacecraft-phase-to-nominal}

Déclarer COMMISSIONING puis NOMINAL avec `SYS_SET_MISSION_PHASE(phase=5)` puis `(phase=6)` (S8.1 fonction 120) ; rien ne fait passer automatiquement `spacecraft_phase` (0x0129) au-delà de 4. Vérifier dans l'onglet **overview**.

---

## Synthèse : nombre de commandes par poste {#summary-command-count-by-position}

| Poste | Commandes clés | Onglets MCS à surveiller |
|----------|-------------|-------------------|
| **Directeur de vol** | GO/NO-GO à chaque jalon de phase | **overview** (synthèse de santé, alarmes) |
| **TTC** | SET_PARAM(0x05FF), ping S17.1, déploiement de l'antenne, basculement de transpondeur | **ttc** (état de liaison, RSSI, marge, antenne) |
| **FDIR/Systèmes** | OBC_BOOT_APP, OBC_SELECT_BUS, HK_ENABLE ×6, essais de commandes datées | **obdh** (sw_image, mode, CPU, tampons), **commanding** (journal des acceptations) |
| **EPS/TCS** | EPS_POWER_ON ×5, vérification des réchauffeurs, activation du refroidisseur | **eps** (lignes d'alimentation, SoC, tension du bus), **tcs** (températures, réchauffeurs, refroidisseur) |
| **AOCS** | AOCS_SET_MODE ×4, alimentation des ST ×2, activation du GPS | **aocs** (mode, vitesses, att_error, roues, senseurs stellaires, GPS) |
| **Opérations charge utile** | PAYLOAD_SET_MODE ×3, PAYLOAD_CAPTURE, refroidisseur du FPA | **payload** (mode, température du FPA, stockage, nombre d'images) |

---

## Référence des outils {#tools-reference}

| Outil | Port | Fonction |
|------|------|---------|
| MCS | 9090 | Interface web du système de contrôle de mission |
| Visualiseur de TM différée (Delayed TM Viewer) | 8092 | Analyse de la TM stockée avec graphiques |
| Outils d'orbite (Orbit Tools) | 8093 | Convertisseur TLE/vecteur d'état en commande TC |

---

*AIG — contenu généré par intelligence artificielle*
