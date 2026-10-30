# CTG-018 : Reprise par le chargeur d'amorçage

**Catégorie :** Contingence
**Poste responsable :** FDIR / Systèmes
**Postes associés :** (directeur de vol pour information)
**Difficulté :** Avancé

## Objectif
Rétablir l'OBC lorsqu'il reste bloqué dans le chargeur d'amorçage (le logiciel applicatif
ne s'est pas chargé). Cette procédure diagnostique la cause, tente de démarrer l'image
applicative et, si l'image est corrompue, inhibe le démarrage automatique et lance un contrôle mémoire ou un
rechargement mémoire pour restaurer l'application.

## Prérequis
- [ ] OBC détecté dans le chargeur d'amorçage — `obdh.sw_image` (0x0311) = 0
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Directeur de vol informé
- [ ] Le chargeur d'amorçage répond aux commandes (les demandes HK renvoient des données)

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| obdh.sw_image | 0x0311 | 0 (chargeur d'amorçage) — condition de déclenchement |
| obdh.last_reboot_cause | 0x0316 | Consigner la valeur (1=commandé, 2=chien de garde, 3=mémoire, 4=basculement) |
| obdh.reboot_count | 0x030A | Consigner la valeur |
| obdh.active_obc | 0x030C | Unité OBC active |
| obdh.mode | 0x0300 | Mode courant (limité dans le chargeur d'amorçage) |
| obdh.temp | 0x0301 | Température de l'OBC dans les limites |
| obdh.cpu_load | 0x0302 | Consigner la valeur |
| obdh.boot_count_a | 0x0317 | Nombre total de démarrages de l'OBC-A |
| obdh.boot_count_b | 0x0318 | Nombre total de démarrages de l'OBC-B |
| eps.bus_voltage | 0x0105 | > 27.0 V |
| ttc.link_status | 0x0501 | 2 (LOCKED) |

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| OBC_BOOT_APP | 8 | 1 | 55 | Démarrer le logiciel applicatif |
| OBC_BOOT_INHIBIT | 8 | 1 | 56 | Inhiber/autoriser le démarrage automatique |
| MEM_CHECK | 6 | 9 | — | Contrôler le CRC mémoire |
| MEM_LOAD | 6 | 2 | — | Charger des données dans la mémoire de bord |
| OBC_SWITCH_UNIT | 8 | 1 | 53 | Basculer sur l'OBC redondant (dernier recours) |

## Déroulement

### Étape 1 : Détecter l'état « chargeur d'amorçage »
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander les données de servitude OBDH
**Verify:** `obdh.sw_image` (0x0311) = 0 (chargeur d'amorçage, application non lancée)
**Verify:** `obdh.last_reboot_cause` (0x0316) — consigner la cause :
- 0 = aucune (inattendu — l'OBC ne devrait pas être dans le chargeur d'amorçage sans cause) ;
- 1 = commandé (redémarrage à l'initiative de l'opérateur) ;
- 2 = chien de garde (plantage de l'application, réinitialisation par le chien de garde, pas de démarrage automatique par le chargeur d'amorçage) ;
- 3 = mémoire (erreur mémoire détectée, démarrage interrompu) ;
- 4 = basculement (changement d'unité OBC tout juste effectué).
**Verify:** `obdh.reboot_count` (0x030A) — consigner la valeur
**Verify:** `obdh.active_obc` (0x030C) — consigner l'unité active
**Verify:** `obdh.temp` (0x0301) — dans les limites
**Note:** Si `last_reboot_cause` = 3 (mémoire), l'image applicative est peut-être corrompue.
Si la cause = 2 (chien de garde), l'application a peut-être planté, mais l'image peut être intacte.
**GO/NO-GO:** État « chargeur d'amorçage » confirmé — engager le diagnostic.

### Étape 2 : Contrôler la cause du dernier redémarrage et évaluer
**Action:** Selon `obdh.last_reboot_cause` :

**Si la cause = 2 (chien de garde) ou 1 (commandé) :**
- l'image applicative est peut-être intacte, mais a planté en cours d'exécution ;
- l'étape 3 (tentative de démarrage de l'application) s'applique.

**Si la cause = 3 (mémoire) :**
- l'image applicative est peut-être corrompue ;
- l'étape 4 (contrôle mémoire avant toute tentative de démarrage) s'applique.

**Si la cause = 4 (basculement) :**
- situation normale après un basculement d'OBC. L'étape 3 s'applique.

**Si la cause = 0 (aucune) :**
- état « chargeur d'amorçage » inattendu. L'étape 4 (contrôle mémoire) s'applique, avec prudence.

**GO/NO-GO:** Évaluation terminée — suivre la voie appropriée.
**BRANCH:** `obdh.last_reboot_cause == 3` -> GO `STEP-4` | NO-GO `STEP-2B` (timeout 10 s)
**LABEL:** `STEP-2B`
**BRANCH:** `obdh.last_reboot_cause == 0` -> GO `STEP-4` | NO-GO `STEP-3` (timeout 10 s)

### Étape 3 : Tenter le démarrage de l'application
**LABEL:** `STEP-3`
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55) — Commander le démarrage de l'application
**Verify:** Attendre 30 s l'initialisation de l'application.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander les données de servitude OBDH
**Verify:** `obdh.sw_image` (0x0311) = 1 (application en cours d'exécution)
**Verify:** `obdh.sw_version` (0x030B) — version applicative correcte
**Verify:** `obdh.mode` (0x0300) — l'OBC entre en SAFE ou NOMINAL
**Verify:** `obdh.cpu_load` (0x0302) < 80 %
**Action:** Si l'application a démarré correctement :
- les étapes 3a (sortie du mode balise) puis 7 (vérification) s'appliquent.
**Action:** Si `obdh.sw_image` vaut toujours 0 après 30 s :
- l'application n'a pas démarré. L'étape 4 (contrôle mémoire) s'applique.
**GO/NO-GO:** Démarrage de l'application réussi — l'étape 3a s'applique. Ou démarrage en échec — l'étape 4 s'applique.
**BRANCH:** `obdh.sw_image == 1` -> GO `STEP-3A` | NO-GO `STEP-4` (timeout 30 s)

### Étape 3a : Sortir du mode balise et rétablir le palier LOW
**LABEL:** `STEP-3A`
**Note:** Le démarrage de l'application ne fait **PAS** sortir du mode balise. L'entrée dans le chargeur d'amorçage
a verrouillé `ttc.beacon_mode` (0x0521) = 1, et ce verrouillage persiste une fois l'application
lancée. Tant qu'il est actif, le palier SAFE (1 000 bit/s, ex-BEACON) est le SEUL palier autorisé et chaque
`TTC_SET_DATA_RATE` revient en échec d'exécution S1.8, erreur `0x0007`, avec le
message d'échec « TM rate is forced to the beacon tier in beacon mode (LOW refused) » —
également émis sous forme d'événement S5 `0x030B COMMAND_REJECTED`.
**TC:** `TTC_SET_BEACON_MODE(on=0)` (Service 8, Subtype 1, func_id 70) — Sortir du mode balise
**Verify:** Acceptation S1.1 + fin d'exécution S1.7 en moins de 5 s
**Verify:** `ttc.beacon_mode` (0x0521) = 0 en moins de 10 s
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) — Sélectionner le palier des opérations courantes
**Verify:** Fin d'exécution S1.7 — et NON un S1.8
**Verify:** `ttc.tm_data_rate` (0x0506) = 16000 et `ttc.tm_tier` (0x0539) = 1 (LOW)
**Action:** Reconfigurer le démodulateur sol de 1 kBd à 16 kBd.
**Note:** Ordre des conditions sur l'échelle des débits — **mode balise désactivé** -> LOW sélectionnable ; **antenne
déployée** (func 69) **+ mode DOWNLINK activé** (func 79) -> HIGH
sélectionnable (l'élévation de 10° est une règle sol : le MCS avertit, le satellite ne refuse pas). Les trois conditions à bord renvoient toutes l'erreur `0x0007` : lire le message d'échec, pas le
code. Liste complète dans `docs/LINK_BUDGET_AND_RATES.md`, section 6.3.
**GO/NO-GO:** Mode balise désactivé et liaison descendante en LOW — l'étape 7 s'applique.
**BRANCH:** `ttc.beacon_mode == 0` -> GO `STEP-7` | NO-GO `STEP-END` (timeout 10 s)

### Étape 4 : Activer l'inhibition d'amorçage et contrôler la mémoire
**LABEL:** `STEP-4`
**TC:** `OBC_BOOT_INHIBIT(inhibit=1)` (Service 8, Subtype 1, func_id 56) — Inhiber le démarrage automatique pour éviter une boucle de redémarrage
**Verify:** L'OBC reste dans le chargeur d'amorçage (aucune tentative de démarrage automatique)
**Note:** Effectuer un contrôle CRC de la zone mémoire de l'image applicative :
**TC:** `MEM_CHECK(memory_id=1, address=0x00000000, length=0x00100000)` (Service 6, Subtype 9)
**Note:** Les valeurs d'adresse et de longueur correspondent à l'image applicative stockée en EEPROM.
Les ajuster selon la carte mémoire réelle si elle diffère.
**Verify:** Attendre le rapport de résultat du contrôle mémoire.
**Action:** Évaluer le résultat du CRC :
- si le CRC correspond à la valeur attendue : l'image est intacte. L'échec du démarrage est peut-être dû à une
  erreur transitoire. L'étape 5 (nouvelle tentative de démarrage) s'applique ;
- si le CRC ne correspond PAS : l'image est corrompue. L'étape 6 (rechargement mémoire) s'applique.
**GO/NO-GO:** Contrôle mémoire terminé — CRC conforme à la valeur attendue -> GO `STEP-5` | NO-GO `STEP-6`

### Étape 5 : Retenter le démarrage de l'application après le contrôle mémoire
**LABEL:** `STEP-5`
**TC:** `OBC_BOOT_INHIBIT(inhibit=0)` (Service 8, Subtype 1, func_id 56) — Lever l'inhibition d'amorçage
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55) — Commander le démarrage de l'application
**Verify:** Attendre 30 s l'initialisation de l'application.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander les données de servitude OBDH
**Verify:** `obdh.sw_image` (0x0311) = 1 (application en cours d'exécution)
**Verify:** `obdh.sw_version` (0x030B) — version correcte
**Action:** Si le démarrage réussit, les étapes 3a (sortie du mode balise) puis 7 s'appliquent. En cas de nouvel échec, l'étape 6 s'applique.
**GO/NO-GO:** Démarrage réussi — les étapes 3a puis 7 s'appliquent. Ou nouvel échec du démarrage — l'étape 6 s'applique.
**BRANCH:** `obdh.sw_image == 1` -> GO `STEP-3A` | NO-GO `STEP-6` (timeout 30 s, max 1)

### Étape 6 : Tenter un rechargement mémoire
**LABEL:** `STEP-6`
**TC:** `OBC_BOOT_INHIBIT(inhibit=1)` (Service 8, Subtype 1, func_id 56) — S'assurer que l'inhibition d'amorçage est active
**Note:** Envoyer l'image du logiciel applicatif en EEPROM au moyen de commandes de chargement mémoire :
**TC:** `MEM_LOAD(memory_id=1, address=ADDR, data=BLOCK)` (Service 6, Subtype 2)
**Note:** Il faut pour cela envoyer l'image applicative complète par blocs, par télécommande.
L'opération est longue (elle peut demander plusieurs contacts avec les stations sol, selon la
taille de l'image et le débit de la liaison montante).
**Note:** Une fois l'envoi terminé, vérifier l'image :
**TC:** `MEM_CHECK(memory_id=1, address=0x00000000, length=0x00100000)` (Service 6, Subtype 9)
**Verify:** Le CRC correspond à la valeur attendue pour l'image envoyée.
**Note:** Si le CRC correspond, lever l'inhibition d'amorçage et démarrer :
**TC:** `OBC_BOOT_INHIBIT(inhibit=0)` (Service 8, Subtype 1, func_id 56)
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55)
**Verify:** `obdh.sw_image` (0x0311) = 1 en moins de 30 s
**Action:** Si le démarrage réussit, les étapes 3a (sortie du mode balise) puis 7 s'appliquent. En cas d'échec, appliquer la section « Contingence ».
**GO/NO-GO:** Rechargement mémoire et démarrage tentés — engager la vérification en cas de succès.
**BRANCH:** `obdh.sw_image == 1` -> GO `STEP-3A` | NO-GO `STEP-END` (timeout 30 s, max 1)

### Étape 7 : Vérifier que tous les sous-systèmes sont nominaux
**LABEL:** `STEP-7`
**Note:** Demander les données HK de tous les sous-systèmes :
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — TCS
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TTC
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Charge utile
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Données de servitude plateforme/OBDH
**Verify:** Toutes les réponses HK reçues.
**Verify:** `eps.bus_voltage` (0x0105) > 27.0 V
**Verify:** `aocs.mode` (0x020F) — consigner et rétablir si nécessaire
**Verify:** `payload.mode` (0x0600) — consigner et rétablir si nécessaire
**Verify:** `obdh.mode` (0x0300) — si SAFE, rétablir NOMINAL : `OBC_SET_MODE(mode=0)`
**Action:** Consigner l'événement de reprise avec :
- la cause du démarrage, le nombre de tentatives de démarrage, les résultats du contrôle mémoire ;
- le temps passé dans le chargeur d'amorçage ;
- la version applicative confirmée ;
- l'état des sous-systèmes après la reprise.
**GO/NO-GO:** Tous les sous-systèmes nominaux — reprise terminée.

## Critères de vérification
**LABEL:** `STEP-END`
- [ ] `obdh.sw_image` (0x0311) = 1 (application en cours d'exécution)
- [ ] `obdh.sw_version` (0x030B) = version applicative correcte
- [ ] `obdh.mode` (0x0300) = 0 (NOMINAL)
- [ ] Tous les rapports HK des sous-systèmes reçus et nominaux
- [ ] `obdh.cpu_load` (0x0302) < 80 %
- [ ] Aucun redémarrage inattendu pendant au moins 30 minutes
- [ ] Événement de reprise documenté dans le journal des anomalies

## Contingence
- Si l'application ne démarre pas après le rechargement mémoire : le matériel de l'OBC est peut-être endommagé.
  Envisager le basculement sur l'OBC redondant : `OBC_SWITCH_UNIT` (func_id 53) selon
  CTG-011. L'OBC courant n'est pas récupérable depuis le sol.
- Si le chargement mémoire échoue (erreurs sur la liaison montante) : vérifier la qualité de la liaison TTC. Renvoyer les
  blocs en échec. La liaison montante de TÉLÉCOMMANDE a un débit fixe de 4 kbit/s et ne fait pas partie de l'échelle des débits TM ;
  il n'y a donc pas de débit montant à réduire. Ce qui aide, c'est de maintenir la LIAISON DESCENDANTE en LOW
  (`TTC_SET_DATA_RATE(rate=0)`, func_id 65), afin que la télémesure de vérification de chaque bloc
  revienne sur la forme d'onde opérationnelle la plus robuste.
- Si l'OBC entre dans une boucle d'amorçage (redémarrages répétés) : commander immédiatement
  `OBC_BOOT_INHIBIT(inhibit=1)` pour interrompre le cycle. Chaque redémarrage incrémente le compteur
  de redémarrages et, au-delà de 4, la FDIR peut déclencher le mode EMERGENCY du satellite.
- Si le chargeur d'amorçage lui-même ne répond plus : il s'agit d'une panne critique — aucune reprise
  logicielle n'est possible sur cette unité OBC. Basculer immédiatement sur l'OBC redondant.
- Si le contrôle mémoire révèle une corruption dans la zone du chargeur d'amorçage : NE PAS tenter de chargement
  mémoire dans la zone du chargeur d'amorçage. Basculer sur l'OBC redondant. Une corruption du chargeur d'amorçage
  ne peut pas être réparée en sécurité.
