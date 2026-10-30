# Gestion bord des données (OBDH) d'EOSAT-1 {#eosat-1-on-board-data-handling-obdh}

**Référence du document :** EOSAT1-UM-OBDH-005
**Édition :** 2.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Vue d'ensemble {#1-overview}

Le sous-système de gestion bord des données (OBDH) assure le traitement central, le stockage des données,
le décodage des télécommandes, la mise en forme de la télémesure et la gestion du temps du satellite EOSAT-1.
Il se compose d'une paire de calculateurs de bord en redondance froide (OBC-A et OBC-B) avec mémoire de masse
intégrée, d'un chien de garde matériel et d'interfaces vers tous les autres sous-systèmes par un double bus CAN.

## 2. Architecture {#2-architecture}

### 2.1 Calculateur de bord (redondance froide A/B) {#21-on-board-computer-cold-redundant-ab}

EOSAT-1 embarque deux OBC identiques en configuration de redondance froide :

| Paramètre            | OBC-A (principal)             | OBC-B (redondant)             |
|----------------------|-------------------------------|-------------------------------|
| Processeur           | LEON3-FT (SPARC durci aux radiations) | LEON3-FT (SPARC durci aux radiations) |
| Fréquence d'horloge  | 80 MHz                        | 80 MHz                        |
| RAM                  | 256 Mo (protégée par EDAC)    | 256 Mo (protégée par EDAC)    |
| Mémoire de masse     | 2 Go (Flash, protégée par EDAC) | 2 Go (Flash, protégée par EDAC) |
| Système d'exploitation | RTEMS (temps réel)          | RTEMS (temps réel)            |
| Bus de données       | Double bus CAN (A + B)        | Double bus CAN (A + B)        |
| Ligne PDM            | Non commutable `obc` (ligne 0) | Non commutable `obc` (ligne 0) |

Les deux unités sont alimentées par la ligne PDM non commutable `obc` (ligne 0), de sorte que l'OBC est toujours
opérationnel après la séparation. Le choix de l'unité est interne à l'OBC ; l'OBC-B est normalement hors tension (redondance froide).
Les deux OBC ont accès au double bus CAN pour communiquer avec les sous-systèmes.

### 2.2 Minuterie de chien de garde {#22-watchdog-timer}

Le chien de garde matériel exige un signal de vie périodique du logiciel applicatif de l'OBC. Si
ce signal n'est pas reçu dans un délai de 10 secondes, le chien de garde déclenche une réinitialisation de l'OBC. Après
trois réinitialisations consécutives par le chien de garde, l'OBC reste dans le chargeur d'amorçage (`sw_image` = 0) et attend une
intervention du sol.

### 2.3 Gestion de la mémoire de masse {#23-mass-memory-management}

La mémoire de masse sert :

- **au stockage des données de la charge utile** : fichiers image de l'imageur multispectral ;
- **à l'archive de télémesure** : paquets de servitude et d'événements enregistrés pour une transmission ultérieure au sol ;
- **aux chargements de logiciel** : images applicatives corrigées chargées depuis le sol.

Le paramètre `mmm_used` (0x0303) indique le taux d'occupation actuel de la mémoire, en pourcentage.

## 3. Modes de l'OBC {#3-obc-modes}

| ID de mode | Nom du mode | Description                                          |
|---------|--------------|------------------------------------------------------|
| 0       | NOMINAL      | Toutes les fonctions disponibles, tous les sous-systèmes actifs |
| 1       | SAFE         | Opérations réduites, charges non essentielles mises hors tension |
| 2       | EMERGENCY    | Mode de contingence commandé (`OBC_SET_MODE` mode=2) ; chien de garde suspendu |

Le mode de l'OBC n'indique pas quel logiciel s'exécute. C'est le rôle d'un indicateur distinct,
l'image logicielle `sw_image` (0x0311) : **0 = chargeur d'amorçage**, 1 = application. L'avancement de l'amorçage
figure dans `boot_state` (0x0A15 : 0 chargeur d'amorçage au repos, 1 vérification du CRC de l'image, 2 application
en cours d'exécution, 3 échec du dernier amorçage). Un OBC dans le chargeur d'amorçage se reconnaît à `sw_image` = 0,
jamais à `obc_mode`, qui vaut 1 (SAFE) après un redémarrage.

### 3.1 Transitions de mode {#31-mode-transitions}

```
Allumage --> chargeur d'amorçage (sw_image=0) --> application (sw_image=1), NOMINAL
                 |                             |
                 |                  SAFE / EMERGENCY <--> NOMINAL
                 |                             |
                 +<--- 3x WD ------------------+
                 |
                 +<--- plantage/réinitialisation de l'OBC
```

- **De la mise sous tension au chargeur d'amorçage** : systématique. L'OBC démarre toujours d'abord dans le chargeur d'amorçage (`sw_image` = 0).
- **Du chargeur d'amorçage à l'application** : sur commande sol via `OBC_BOOT_APP` (S8.1 fonction 55) après l'autotest ;
  `sw_image` passe à 1 et le mode de l'OBC à NOMINAL (0).
  À la première mise sous tension, le chargeur d'amorçage ne bascule PAS de lui-même — une commande sol est nécessaire. Après un
  redémarrage, il tente de lui-même l'amorçage de l'application au bout de 10 s, sauf si `OBC_BOOT_INHIBIT` est positionné.
- **De NOMINAL à SAFE ou EMERGENCY** : sur commande sol via `OBC_SET_MODE` (mode=1 ou 2) ou par la FDIR autonome.
- **De SAFE ou EMERGENCY à NOMINAL** : sur commande sol via `OBC_SET_MODE` (mode=0), après levée de l'anomalie.
- **De tout mode au chargeur d'amorçage** : trois réinitialisations consécutives par le chien de garde ou commande sol (`OBC_REBOOT`, fonction 52).
  `sw_image` revient à 0 et le mode de l'OBC passe à SAFE (1).
- **D'un plantage de l'OBC au chargeur d'amorçage** : une exception logicielle irrécupérable provoque une réinitialisation, et après
  3 réinitialisations consécutives, l'OBC reste dans le chargeur d'amorçage dans l'attente d'une intervention du sol.

### 3.2 Automate d'états du chargeur d'amorçage {#32-bootloader-state-machine}

Le chargeur d'amorçage est un environnement d'exécution minimal conçu pour la récupération du satellite.
Il offre des fonctions limitées qui garantissent que le satellite reste commandable.
Dans le chargeur d'amorçage, la télémesure est émise depuis l'**APID dédié du chargeur d'amorçage (0x002)** —
distinct de l'APID applicatif (0x001). Seul le **SID 11 (balise)** est émis ;
toutes les mémoires de TM bord ainsi que les opérations AOCS, TCS et charge utile sont indisponibles tant que le
logiciel applicatif n'a pas démarré (phase ≥ 4). Un redémarrage de l'OBC ramène automatiquement le satellite
dans cet état chargeur d'amorçage/balise seule.

#### Capacités du chargeur d'amorçage {#bootloader-capabilities}

| Capacité                | Disponible | Remarques                                 |
|-------------------------|-----------|--------------------------------------------|
| Télémesure de balise (SID 11) | Oui | HK minimale : température de l'OBC, tension, mode, temps de fonctionnement |
| Données de servitude complètes | Non | HK de niveau applicatif indisponible     |
| Réception des commandes | Oui       | Par le canal de commande PDM dédié          |
| Jeu de commandes        | Restreint | Seules les commandes essentielles sont acceptées |
| Contrôle AOCS           | Non       | Aucun contrôle d'attitude dans le chargeur d'amorçage |
| Opérations charge utile | Non       | Charge utile hors tension                   |
| Commande des sous-systèmes | Non    | Commandes internes à l'OBC uniquement       |

#### Jeu de commandes restreint du chargeur d'amorçage {#restricted-command-set-in-the-bootloader}

Seules les commandes suivantes sont acceptées tant que `sw_image` = 0 :

| Commande             | Rôle                                             |
|----------------------|--------------------------------------------------|
| OBC_BOOT_APP (S8.1 fonction 55) | Amorcer l'image applicative             |
| OBC_REBOOT, OBC_SWITCH_UNIT, OBC_SELECT_BUS, OBC_BOOT_INHIBIT, OBC_CLEAR_REBOOT_CNT, OBC_DIAGNOSTIC (S8.1 fonctions 52–54, 56, 57, 61) | Maintenance du chargeur d'amorçage |
| SET_TIME (S9.1)      | Acceptée, mais échoue à l'exécution tant que l'application ne tourne pas — régler l'heure après OBC_BOOT_APP |
| HK_REQUEST (SID 11), S17.1, S20.1/S20.3 | Paquet de balise, test de connexion, lecture/écriture de paramètres |
| EPS_POWER_ON / EPS_POWER_OFF (fonctions 19/20), TTC_PA_ON / TTC_PA_OFF (66/67), TTC_DEPLOY_ANTENNA (69) | Lignes d'alimentation, émetteur et antenne pour le premier contact |
| SYS_SET_MISSION_PHASE (fonction 120) | Déclaration de la phase de mission (phases applicatives refusées tant que l'OBC n'a pas amorcé) |

Toutes les autres commandes sont rejetées à l'acceptation avec le code d'échec 0x0006.

#### Paquet de balise (SID 11) {#beacon-packet-sid-11}

Le paquet de balise émis pendant que l'OBC exécute le chargeur d'amorçage contient un jeu minimal de paramètres :

| Paramètre       | Contenu                               |
|-----------------|---------------------------------------|
| obc_mode        | 0/1/2 — pas un indicateur d'amorçage  |
| sw_image        | 0 (chargeur d'amorçage) — l'indicateur d'amorçage |
| obc_temp        | Température de la carte OBC           |
| bat_voltage     | Tension de la batterie                |
| bat_soc         | État de charge de la batterie         |
| uptime          | Secondes écoulées depuis le dernier amorçage |
| reboot_count    | Nombre total de redémarrages          |
| sw_version      | Identifiant de version du chargeur d'amorçage |

Cette balise est émise à faible cadence (0,01 Hz) afin d'économiser l'énergie et la bande passante.

### 3.3 Transition du chargeur d'amorçage vers l'application {#33-bootloader-to-application-transition}

La transition du chargeur d'amorçage vers l'application (`sw_image` 0 → 1, mode OBC NOMINAL) se déroule comme suit :

1. Le sol reçoit le paquet de balise et vérifie la santé de l'OBC.
2. Le sol envoie `OBC_BOOT_APP` (S8.1 fonction 55).
3. L'OBC charge le logiciel applicatif depuis la mémoire flash.
4. L'application exécute l'autotest de mise sous tension (POST).
5. Si le POST réussit, l'OBC passe en mode NOMINAL.
6. La télémesure de servitude complète démarre à 1 Hz.
7. Le sol vérifie que tous les paramètres de télémesure sont nominaux.

Si le POST échoue, l'OBC reste dans le chargeur d'amorçage et génère un événement d'échec. Le sol doit
alors analyser la situation (voir CTG-021, Reprise par le chargeur d'amorçage de l'OBC).

### 3.4 Processus de reprise après plantage de l'OBC {#34-obc-crash-recovery-workflow}

Lorsque l'OBC subit un plantage irrécupérable :

1. **Détection du plantage** : expiration du chien de garde matériel (aucun signal de vie pendant 10 secondes).
2. **Première réinitialisation** : l'OBC redémarre dans le chargeur d'amorçage, puis tente automatiquement de démarrer l'application.
3. **Deuxième réinitialisation** : identique à la première. `reboot_count` est incrémenté.
4. **Troisième réinitialisation** : l'OBC reste dans le chargeur d'amorçage de façon permanente jusqu'à une commande sol.
   Aucune tentative de démarrage automatique.
5. **Reprise par le sol** : lors du contact suivant, le sol observe un paquet de balise avec
   `sw_image = 0` et un `reboot_count` élevé. Le sol analyse l'archive de télémesure,
   charge un correctif logiciel si nécessaire et commande `OBC_BOOT_APP` pour redémarrer.

### 3.5 Comportement en mode survie {#35-safe-mode-behaviour}

En mode SAFE, l'OBC :

- désactive les opérations et l'alimentation de la charge utile ;
- commande l'AOCS en mode COARSE_SUN ;
- réduit la cadence de la télémesure de servitude à 0,1 Hz ;
- active le réchauffeur de batterie (le seul élément thermique actif) ;
- maintient la liaison TTC pour la commande depuis le sol.

### 3.6 Architecture du bus CAN et isolation des pannes {#36-can-bus-architecture-and-failure-isolation}

EOSAT-1 utilise un double bus CAN (bus A et bus B) pour les communications internes entre l'OBC
et tous les sous-systèmes :

| Bus   | Rôle principal              | Sous-systèmes connectés       |
|-------|-----------------------------|-------------------------------|
| CAN-A | Bus de données principal    | Tous les sous-systèmes        |
| CAN-B | Bus de données redondant    | Tous les sous-systèmes        |

Les deux bus véhiculent un trafic identique en conditions nominales. Si CAN-A présente un défaut
(bus-off, bit dominant bloqué, etc.), l'OBC bascule automatiquement sur CAN-B pour toutes les communications
avec les sous-systèmes.

**Procédure d'isolation d'une panne de bus CAN :**

1. Surveiller les compteurs de télémesure `can_a_errors` et `can_b_errors`.
2. Si le nombre d'erreurs sur un bus dépasse le seuil, l'OBC isole ce bus.
3. Toutes les communications se poursuivent sur le bus sain restant.
4. Le sol analyse le bus défaillant lors de la fenêtre de visibilité suivante.
5. Si les deux bus sont défaillants, seules les fonctions internes de l'OBC restent opérationnelles — la commande des
   sous-systèmes est perdue. Il s'agit d'une urgence satellite qui exige une analyse immédiate.

## 4. Traitement des télécommandes {#4-telecommand-processing}

### 4.1 Compteurs de TC {#41-tc-counters}

L'OBDH tient trois compteurs de télécommandes :

| ID param. | Nom              | Description                                |
|----------|-------------------|--------------------------------------------|
| 0x0304   | tc_recv_count     | Total des télécommandes reçues             |
| 0x0305   | tc_exec_count     | Télécommandes exécutées avec succès        |
| 0x0306   | tc_reject_count   | Télécommandes rejetées (CRC/authentification/invalides) |

Un écart entre `tc_recv_count` et `tc_exec_count + tc_reject_count` signale
une anomalie de traitement qui doit être analysée.

### 4.2 Authentification des TC {#42-tc-authentication}

Toutes les télécommandes sont validées par une somme de contrôle CRC-16. En outre, les commandes critiques
(changements de mode, commande des réchauffeurs) exigent un code d'authentification de commande. Les commandes qui échouent
à la validation sont rejetées et incrémentent `tc_reject_count`.

## 5. Génération de la télémesure {#5-telemetry-generation}

La télémesure de servitude est générée à des cadences configurables :

| Mode      | Cadence HK | Taille de paquet | Contenu                 |
|-----------|------------|-------------|-----------------------------|
| NOMINAL   | 1 Hz       | 256 octets  | Tous les paramètres des sous-systèmes |
| SAFE      | 0,1 Hz     | 128 octets  | Paramètres essentiels uniquement |
| Chargeur d'amorçage | 0,01 Hz | 64 octets   | Santé de l'OBC uniquement   |

Le paramètre `tm_pkt_count` (0x0307) comptabilise le nombre total de paquets de télémesure générés
depuis le dernier redémarrage.

## 6. Paramètres de télémesure {#6-telemetry-parameters}

| ID param. | Nom            | Unité  | Description                          |
|----------|-----------------|--------|--------------------------------------|
| 0x0300   | obc_mode        | enum   | Mode OBC (0 NOMINAL, 1 SAFE, 2 EMERGENCY) |
| 0x0301   | obc_temp        | °C     | Température de la carte OBC          |
| 0x0302   | cpu_load        | %      | Taux d'occupation du processeur de l'OBC |
| 0x0303   | mmm_used        | %      | Taux d'occupation de la mémoire de masse |
| 0x0304   | tc_recv_count   | nombre | Total des TC reçues                  |
| 0x0305   | tc_exec_count   | nombre | TC exécutées avec succès             |
| 0x0306   | tc_reject_count | nombre | TC rejetées                          |
| 0x0307   | tm_pkt_count    | nombre | Total des paquets TM générés         |
| 0x0308   | uptime          | s      | Secondes écoulées depuis le dernier amorçage de l'OBC |
| 0x030A   | reboot_count    | nombre | Total des redémarrages de l'OBC depuis le déploiement |

## 7. Définition des limites {#7-limit-definitions}

| Paramètre       | Jaune bas  | Jaune haut  | Rouge bas | Rouge haut |
|-----------------|------------|-------------|---------|----------|
| cpu_load (%)    | 0          | 85          | 0       | 98       |

Une charge processeur durablement supérieure à 85 % traduit une demande de traitement excessive et devrait conduire à
analyser les tâches en cours. Au-delà de 98 %, le chien de garde risque d'expirer.

## 8. Commandes {#8-commands}

| Commande          | Service  | Paramètres         | Description                        |
|-------------------|----------|--------------------|------------------------------------|
| OBC_SET_MODE      | S8,S1    | mode (0/1/2)       | Régler le mode de fonctionnement de l'OBC |
| HK_REQUEST        | S3,S27   | sid=3              | Demander le paquet de servitude OBDH |
| SET_TIME          | S9,S1    | cuc_seconds        | Régler le temps bord (format CUC)  |
| GET_PARAM         | S20,S3   | param_id           | Lire un paramètre OBDH individuel  |
| SET_PARAM         | S20,S1   | param_id, value    | Modifier un paramètre de configuration OBDH |

### 8.1 Gestion du temps {#81-time-management}

L'OBC tient le temps bord au format CCSDS Unsegmented Code (CUC) : un champ grossier de 4 octets
(1 s) et un champ fin de 2 octets (1/65536 s), voir 12_time_and_clocks.md. Le temps est synchronisé depuis le sol au moyen de la commande `SET_TIME`. La dérive d'horloge
devrait rester inférieure à 1 ms/jour grâce à l'oscillateur à quartz compensé en température.

## 9. Remarques d'exploitation {#9-operational-notes}

1. Après chaque redémarrage de l'OBC, `reboot_count` (0x030A) est incrémenté. Consulter `uptime` (0x0308)
   pour confirmer que l'OBC n'a pas subi de réinitialisation inattendue.
2. L'occupation de la mémoire de masse (`mmm_used`) devrait être surveillée et maintenue sous 90 % afin de garantir
   un espace suffisant pour les données de la charge utile et l'archivage de la télémesure.
3. Les correctifs logiciels sont chargés par un service dédié de chargement mémoire et doivent être vérifiés par le sol
   avant leur activation.
4. Le paquet de servitude OBDH (SID=3) comprend tous les paramètres énumérés à la section 6.

---

*Fin du document — EOSAT1-UM-OBDH-005*
