# CTG-021 : Reprise par le chargeur d'amorçage de l'OBC

**Catégorie :** Contingence
**Poste responsable :** FDIR / Systèmes
**Postes associés :** directeur de vol
**Difficulté :** Avancé

## Objectif
Rétablir l'OBC lorsqu'il reste bloqué en mode chargeur d'amorçage après un plantage ou un
redémarrage inattendu. En mode chargeur d'amorçage, seule la structure HK de balise (SID 11) est disponible,
et elle est émise sur l'APID dédié du chargeur d'amorçage (0x002) — distinct de
l'APID applicatif (0x001). Aucun stockage de TM n'existe en mode chargeur d'amorçage ; les opérations d'attitude,
thermiques et de charge utile sont toutes à l'arrêt. Le premier indice dont dispose le sol d'une
entrée dans le chargeur d'amorçage est l'arrêt de tout le trafic sur l'APID applicatif : seule subsiste une
balise SID 11 sur l'APID du chargeur d'amorçage. Le logiciel applicatif complet ne s'exécute pas, ce qui signifie
aucune opération de charge utile, aucune commande programmée et une capacité FDIR réduite. Cette
procédure vérifie l'état du chargeur d'amorçage, évalue la cause du redémarrage, tente
d'amorcer le logiciel applicatif et, en cas d'échec, effectue des contrôles d'intégrité de la mémoire
avant d'envisager un rechargement mémoire ou un basculement d'OBC.

## Prérequis
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] OBC confirmé en chargeur d'amorçage — `obdh.sw_image` (0x0311) = 0
- [ ] Directeur de vol informé
- [ ] Le chargeur d'amorçage répond aux demandes HK (balise SID 11 reçue)
- [ ] Valeur précédente de `obdh.reboot_count` (0x030A) connue depuis le dernier passage nominal

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| obdh.sw_image | 0x0311 | 0 (chargeur d'amorçage) — condition de déclenchement |
| obdh.last_reboot_cause | 0x0316 | Consigner la valeur (1=commandé, 2=chien de garde, 3=mémoire, 4=basculement) |
| obdh.reboot_count | 0x030A | Consigner la valeur — comparer à la dernière valeur connue |
| obdh.active_obc | 0x030C | Unité OBC active (0=A, 1=B) |
| obdh.mode | 0x0300 | Mode courant (limité en chargeur d'amorçage) |
| obdh.temp | 0x0301 | Température de l'OBC dans les limites (< 50 °C) |
| obdh.cpu_load | 0x0302 | Consigner la valeur |
| obdh.boot_count_a | 0x0317 | Nombre total d'amorçages de l'OBC-A |
| obdh.boot_count_b | 0x0318 | Nombre total d'amorçages de l'OBC-B |
| obdh.bus_a_status | 0x030F | 0 (OK) ou 1 (ERROR) |
| obdh.bus_b_status | 0x0310 | 0 (OK) ou 1 (ERROR) |
| eps.bus_voltage | 0x0105 | > 30.9 V |
| ttc.link_status | 0x0501 | 2 (LOCKED) |

## Télécommandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | -- | Demander un rapport HK ponctuel |
| OBC_BOOT_APP | 8 | 1 | 55 | Amorcer le logiciel applicatif depuis le chargeur d'amorçage |
| OBC_BOOT_INHIBIT | 8 | 1 | 56 | Inhiber/autoriser l'amorçage automatique |
| MEM_CHECK | 6 | 9 | -- | Contrôler l'intégrité CRC de la mémoire |
| MEM_LOAD | 6 | 2 | -- | Charger des données dans la mémoire de bord |
| OBC_SWITCH_UNIT | 8 | 1 | 53 | Basculer sur l'OBC redondant (dernier recours) |
| OBC_REBOOT | 8 | 1 | 52 | Forcer le redémarrage de l'OBC |

## Déroulement

### Étape 1 : Confirmer l'état du chargeur d'amorçage et consigner les diagnostics
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander la télémesure de servitude OBDH
**Note:** En mode chargeur d'amorçage, seul le SID 11 (balise) peut répondre. Si le SID 4 ne
revient pas, demander plutôt le SID 11.
**Verify:** `obdh.sw_image` (0x0311) = 0 (chargeur d'amorçage, logiciel applicatif arrêté)
**TC:** `GET_PARAM(param_id=0x0316)` (Service 20, Subtype 3) — `obdh.last_reboot_cause` (à la demande : aucun SID HK ne le transporte)
**Verify:** `obdh.last_reboot_cause` (0x0316) — consigner la valeur :
- 0 = aucune (inattendu — l'OBC ne devrait pas être en chargeur d'amorçage sans cause)
- 1 = commandé (redémarrage à l'initiative de l'opérateur)
- 2 = chien de garde (plantage du logiciel applicatif, déclenchement du chien de garde)
- 3 = mémoire (erreur mémoire détectée, amorçage interrompu)
- 4 = basculement (un basculement d'unité OBC a eu lieu)
**Verify:** `obdh.reboot_count` (0x030A) — consigner et comparer à la dernière valeur connue
**Verify:** `obdh.active_obc` (0x030C) — consigner l'unité OBC active
**TC:** `GET_PARAM(param_id=0x0301)` (Service 20, Subtype 3) — `obdh.temp` (à la demande : aucun SID HK ne le transporte)
**Verify:** `obdh.temp` (0x0301) — dans les limites (< 50 °C)
**Verify:** `obdh.cpu_load` (0x0302) — consigner (devrait être faible en chargeur d'amorçage)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander la télémesure de servitude EPS
**Verify:** `eps.bus_voltage` (0x0105) > 30.9 V — confirmer que l'alimentation est stable
**Note:** Si la tension du bus est limite (< 31.5 V), une baisse de tension a pu provoquer le plantage.
Traiter l'EPS avant de tenter l'amorçage applicatif.
**GO/NO-GO:** État du chargeur d'amorçage confirmé, diagnostics consignés — passer à l'évaluation.

### Étape 2 : Évaluer la cause du redémarrage et déterminer le chemin de reprise
**Action:** En fonction de `obdh.last_reboot_cause`, suivre le chemin approprié :

**Si cause = 2 (chien de garde) ou cause = 1 (commandé) :**
- L'image applicative est probablement intacte, mais elle a planté en cours d'exécution.
- Étape suivante : étape 3 (tentative d'amorçage applicatif).

**Si cause = 3 (mémoire) :**
- L'image applicative est peut-être corrompue. L'amorçage a été interrompu par le contrôle CRC du chargeur d'amorçage.
- Étape suivante : étape 4 (contrôle d'intégrité mémoire avant toute tentative d'amorçage).

**Si cause = 4 (basculement) :**
- Situation normale après un basculement d'unité OBC. L'image devrait être intacte.
- Étape suivante : étape 3 (tentative d'amorçage applicatif).

**Si cause = 0 (aucune) :**
- État inattendu. Procéder avec prudence ; l'étape 4 (contrôle mémoire d'abord) s'applique.

**Action:** Consigner la justification de l'évaluation dans le journal des opérations.
**GO/NO-GO:** Évaluation terminée — suivre le chemin approprié.
**TC:** `GET_PARAM(param_id=0x0316)` (Service 20, Subtype 3) — `obdh.last_reboot_cause` (à la demande : aucun SID HK ne le transporte)
**BRANCH:** `obdh.last_reboot_cause == 3` -> GO `STEP-4` | NO-GO `STEP-2B` (timeout 10 s)
**LABEL:** `STEP-2B`
**BRANCH:** `obdh.last_reboot_cause == 0` -> GO `STEP-4` | NO-GO `STEP-3` (timeout 10 s)

### Étape 3 : Tenter l'amorçage applicatif
**LABEL:** `STEP-3`
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55) — Commander l'amorçage applicatif
**Note:** Le chargeur d'amorçage va tenter de charger et de démarrer le logiciel applicatif.
Cela prend environ 10 à 30 secondes.
**Verify:** Attendre 30 s l'initialisation du logiciel applicatif.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander la télémesure de servitude OBDH
**Verify:** `obdh.sw_image` (0x0311) = 1 (logiciel applicatif en cours d'exécution)
**TC:** `GET_PARAM(param_id=0x030B)` (Service 20, Subtype 3) — `obdh.sw_version` (à la demande : aucun SID HK ne le transporte)
**Verify:** `obdh.sw_version` (0x030B) — version applicative correcte
**Verify:** `obdh.mode` (0x0300) — l'OBC devrait entrer en mode SAFE ou NOMINAL
**Verify:** `obdh.cpu_load` (0x0302) < 80 % — charge normale après amorçage
**Action:** Si le logiciel applicatif a démarré correctement :
- Étapes suivantes : étape 3a (sortie du mode balise), puis étape 7 (vérification complète du système).
**Action:** Si `obdh.sw_image` vaut toujours 0 après 30 s :
- Échec de l'amorçage applicatif. Étape suivante : étape 4 (contrôle d'intégrité mémoire).
**GO/NO-GO:** Amorçage réussi — étape 3a. Amorçage en échec — étape 4.
**BRANCH:** `obdh.sw_image == 1` -> GO `STEP-3A` | NO-GO `STEP-4` (timeout 30 s)

### Étape 3a : Sortir du mode balise et rétablir le palier LOW
**LABEL:** `STEP-3A`
**Note:** L'amorçage du logiciel applicatif ne fait **PAS** sortir du mode balise. L'entrée dans le
chargeur d'amorçage a verrouillé `ttc.beacon_mode` (0x0521) = 1, et ce verrouillage persiste une fois le
logiciel applicatif en cours d'exécution. Tant qu'il est verrouillé, le palier SAFE (1 000 bit/s, ex-BEACON) est le SEUL
palier autorisé : toute `TTC_SET_DATA_RATE` est refusée par un échec d'exécution S1.8, erreur
`0x0007`, dont l'avis d'échec indique « TM rate is forced to the SAFE tier in beacon
mode (LOW refused) ». Le même texte est émis comme événement S5 `0x030B COMMAND_REJECTED`.
**TC:** `TTC_SET_BEACON_MODE(on=0)` (Service 8, Subtype 1, func_id 70) — Sortir du mode balise
**Verify:** acceptation S1.1 + exécution S1.7 terminée en 5 s
**Verify:** `ttc.beacon_mode` (0x0521) = 0 en 10 s
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) — Sélectionner le palier des opérations de routine
**Verify:** exécution S1.7 terminée — PAS de S1.8
**Verify:** `ttc.tm_data_rate` (0x0506) = 16000 et `ttc.tm_tier` (0x0539) = 1 (LOW)
**Action:** Reconfigurer le démodulateur sol de 1 kBd à 16 kBd avant d'attendre
les SID 1–6 ; le démodulateur balise ne se verrouille pas à 16 kbit/s.
**Note:** Ordre des verrous sur l'échelle — **mode balise désactivé** → LOW sélectionnable ; **antenne
déployée** (func 69) **+ mode DOWNLINK actif** (func 79) → HIGH
sélectionnable (l'élévation de 10 deg est une règle sol : le MCS avertit, le satellite ne refuse pas). Les trois verrous à bord renvoient tous l'erreur `0x0007` : lire l'avis d'échec, pas le
code. Liste complète dans `docs/LINK_BUDGET_AND_RATES.md` §6.3.
**GO/NO-GO:** Mode balise désactivé et liaison descendante au palier LOW — l'étape 7 s'applique.
**BRANCH:** `ttc.beacon_mode == 0` -> GO `STEP-7` | NO-GO `STEP-END` (timeout 10 s)

### Étape 4 : Inhiber l'amorçage automatique et contrôler l'intégrité de la mémoire
**LABEL:** `STEP-4`
**Note:** Inhiber l'amorçage automatique pour éviter une boucle d'amorçage :
**TC:** `OBC_BOOT_INHIBIT(inhibit=1)` (Service 8, Subtype 1, func_id 56)
**Verify:** L'OBC reste en chargeur d'amorçage (aucune tentative d'amorçage automatique).
**Note:** Effectuer un contrôle CRC de la mémoire sur la zone de l'image applicative :
**TC:** `MEM_CHECK(memory_id=1, address=0x00000000, length=0x00100000)` (Service 6, Subtype 9)
**Note:** L'adresse et la longueur se rapportent à l'image applicative en EEPROM. Les ajuster
selon la cartographie mémoire réelle.
**Verify:** Attendre le rapport de résultat du contrôle mémoire.
**Action:** Évaluer le résultat du CRC :
- **CRC conforme à la valeur attendue :** l'image est intacte. L'échec d'amorçage est peut-être transitoire.
  Étape suivante : étape 5 (nouvelle tentative d'amorçage).
- **CRC NON conforme :** l'image est corrompue. Étape suivante : étape 6 (rechargement mémoire).
**GO/NO-GO:** Contrôle mémoire terminé — CRC conforme à la valeur attendue -> GO `STEP-5` | NO-GO `STEP-6`

### Étape 5 : Retenter l'amorçage applicatif après vérification de la mémoire
**LABEL:** `STEP-5`
**TC:** `OBC_BOOT_INHIBIT(inhibit=0)` (Service 8, Subtype 1, func_id 56) — Lever l'inhibition d'amorçage
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55) — Commander l'amorçage applicatif
**Verify:** Attendre 30 s l'initialisation du logiciel applicatif.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander la télémesure de servitude OBDH
**Verify:** `obdh.sw_image` (0x0311) = 1 (logiciel applicatif en cours d'exécution)
**TC:** `GET_PARAM(param_id=0x030B)` (Service 20, Subtype 3) — `obdh.sw_version` (à la demande : aucun SID HK ne le transporte)
**Verify:** `obdh.sw_version` (0x030B) — version applicative correcte
**Action:** Si l'amorçage réussit : étapes suivantes : étape 3a (sortie du mode balise), puis étape 7 (vérification complète du système).
**Action:** Si l'amorçage échoue de nouveau : l'étape 6 (rechargement mémoire ou basculement d'OBC) s'applique.
**GO/NO-GO:** Amorçage réussi — étape 3a, puis étape 7. Nouvel échec d'amorçage — étape 6.
**BRANCH:** `obdh.sw_image == 1` -> GO `STEP-3A` | NO-GO `STEP-6` (timeout 30 s, max 1)

### Étape 6 : Escalade — rechargement mémoire ou basculement d'OBC
**LABEL:** `STEP-6`
**TC:** `OBC_BOOT_INHIBIT(inhibit=1)` (Service 8, Subtype 1, func_id 56) — S'assurer que l'inhibition d'amorçage est active
**GO/NO-GO:** La durée du passage permet un rechargement mémoire (option A) ; sinon option B -> GO `STEP-6A` | NO-GO `STEP-6B`

**Option A — Rechargement mémoire (si la durée du passage le permet) :**
**LABEL:** `STEP-6A`
**Note:** Téléverser l'image du logiciel applicatif au moyen des commandes de chargement mémoire :
**TC:** `MEM_LOAD(memory_id=1, address=ADDR, data=BLOCK)` (Service 6, Subtype 2)
**Note:** Le chargement d'une image complète est une opération longue qui peut nécessiter plusieurs contacts
selon la taille de l'image et le débit de la liaison montante.
**TC:** `MEM_CHECK(memory_id=1, address=ADDR, length=LEN)` (Service 6, Subtype 9) — Après le chargement, vérifier l'image
**Verify:** Le CRC correspond à la valeur attendue.
**Note:** Lever l'inhibition d'amorçage et amorcer :
**TC:** `OBC_BOOT_INHIBIT(inhibit=0)` (Service 8, Subtype 1, func_id 56)
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55)
**Verify:** `obdh.sw_image` (0x0311) = 1 en 30 s.
**Action:** Si l'amorçage réussit, étapes suivantes : étape 3a (sortie du mode balise), puis étape 7.
**BRANCH:** `obdh.sw_image == 1` -> GO `STEP-3A` | NO-GO `STEP-6B` (timeout 30 s, max 1)

**Option B — Basculement d'unité OBC (si le rechargement mémoire n'est pas réalisable) :**
**LABEL:** `STEP-6B`
**Note:** Commander le basculement sur l'OBC redondant :
**TC:** `OBC_SWITCH_UNIT` (Service 8, Subtype 1, func_id 53)
**ATTENTION :** Il s'agit d'une commande critique. L'OBC actif va s'éteindre et
l'unité redondante va s'amorcer à partir de sa propre image EEPROM.
**Verify:** Attendre 60 s l'amorçage de l'OBC redondant.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander la télémesure de servitude OBDH
**Verify:** `obdh.active_obc` (0x030C) indique la nouvelle unité
**Verify:** `obdh.sw_image` (0x0311) = 1 (logiciel applicatif en cours d'exécution sur l'unité de secours)
**Action:** Si l'OBC de secours s'amorce correctement, étapes suivantes : étape 3a (sortie du mode balise), puis étape 7.

**GO/NO-GO:** Logiciel applicatif rétabli par rechargement ou basculement — étape 3a, puis étape 7.
Si aucune des deux options n'aboutit, passer à EMG-003.
**BRANCH:** `obdh.sw_image == 1` -> GO `STEP-3A` | NO-GO `STEP-END` (timeout 30 s, max 1)

### Étape 7 : Vérifier que tous les sous-systèmes sont nominaux
**LABEL:** `STEP-7`
**Note:** Demander la HK de tous les sous-systèmes :
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — TCS
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TTC
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Charge utile
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Télémesure de servitude plateforme/OBDH
**Verify:** Les cinq réponses HK sont reçues en 30 s.
**Verify:** `eps.bus_voltage` (0x0105) > 30.9 V
**Verify:** `aocs.mode` (0x020F) — consigner et rétablir si nécessaire
**Verify:** `payload.mode` (0x0600) — consigner et rétablir si nécessaire
**Verify:** `obdh.mode` (0x0300) — si SAFE, envisager le retour en NOMINAL :
`OBC_SET_MODE(mode=0)` (func_id 50)
**Note:** Vérifier le temps bord par rapport à la référence sol :
**TC:** `SET_TIME(cuc_seconds=T_corrected)` (Service 9, Subtype 1) — si la dérive dépasse 5 s, synchroniser le temps bord avec cette commande
**Action:** Consigner l'événement de reprise :
- cause et nombre de redémarrages ;
- nombre de tentatives d'amorçage nécessaires ;
- résultats du contrôle mémoire (le cas échéant) ;
- temps passé en chargeur d'amorçage ;
- version applicative confirmée ;
- état des sous-systèmes après la reprise.
**GO/NO-GO:** Tous les sous-systèmes nominaux, logiciel applicatif en cours d'exécution — reprise terminée.

## Critères de vérification
**LABEL:** `STEP-END`
- [ ] `obdh.sw_image` (0x0311) = 1 (logiciel applicatif en cours d'exécution)
- [ ] `obdh.sw_version` (0x030B) = version applicative correcte
- [ ] `obdh.mode` (0x0300) = 0 (NOMINAL) ou 1 (SAFE) selon le cas
- [ ] `obdh.cpu_load` (0x0302) < 80 %
- [ ] Tous les rapports HK des sous-systèmes reçus et nominaux
- [ ] `obdh.reboot_count` (0x030A) documenté
- [ ] Aucun redémarrage inattendu pendant au moins 30 minutes
- [ ] Événement de reprise documenté dans le journal des anomalies

## Cas de contingence
- Si l'OBC redémarre de nouveau pendant la tentative d'amorçage applicatif : commander immédiatement
  `OBC_BOOT_INHIBIT(inhibit=1)` (func_id 56) pour éviter une boucle d'amorçage. Si
  `obdh.reboot_count` augmente de plus de 3 en 1 heure, suspecter une boucle d'amorçage.
  Passer à EMG-003 (redémarrage d'urgence de l'OBC).
- Si le chargeur d'amorçage lui-même ne répond plus (aucune HK) : il s'agit d'une défaillance
  critique. Aucune reprise logicielle n'est possible sur cette unité OBC. Basculer immédiatement sur l'OBC
  redondant : `OBC_SWITCH_UNIT` (func_id 53).
- Si le rechargement mémoire échoue à cause d'erreurs de liaison montante : vérifier la qualité de la liaison TTC. Renvoyer
  les blocs en échec. Maintenir la liaison descendante au échelon LOW (16 kbit/s, BPSK conv(7,1/2)+RS — le
  échelon des opérations de routine et le plus robuste des échelons commandables) :
  `TTC_SET_DATA_RATE(rate=0)` (func_id 65). À noter : la liaison montante de TÉLÉCOMMANDE est
  fixe à 4 kbit/s et n'est pas concernée par l'échelle de débits TM ; ce que LOW apporte ici, c'est
  une liaison descendante plus calme et mieux verrouillée pour vérifier chaque bloc.
- Si l'OBC de secours ne parvient pas non plus à amorcer le logiciel applicatif : les deux images applicatives sont peut-être
  corrompues. Il faut alors un double rechargement mémoire — un par unité OBC. Se coordonner avec
  l'équipe logiciel sol et planifier une campagne de chargement sur plusieurs contacts.
- Si le SCAO est revenu en DETUMBLE après le redémarrage de l'OBC : exécuter CTG-002 (reprise après anomalie
  SCAO) pour rétablir le pointage une fois l'OBC confirmé stable.
- Si le contrôle mémoire révèle une corruption dans la zone du chargeur d'amorçage : NE PAS tenter
  d'écrire dans la zone du chargeur d'amorçage. Basculer sur l'OBC redondant. Une corruption du chargeur d'amorçage
  ne peut pas être réparée depuis le sol en toute sécurité.
