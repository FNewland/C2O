# CTG-003 : Rétablissement après perte de liaison TTC
**Sous-système :** TT&C
**Phase :** CONTINGENCY
**Révision :** 1.1 --- 2026-11-02 (décision de Franz S4) : quand les deux transpondeurs sont en
panne, la liaison est réellement coupée (aucune TC reçue, aucune TM, balise comprise) ; la fiche indique
donc ce que les étapes en aveugle peuvent atteindre ou non, et l'étape 6 nomme l'autonomie de bord réelle
(temporisateur de perte de commande FDIR TTC-01, 24 h).
**Approuvé par :** directeur des opérations de vol

## Objet
Rétablir les communications avec le satellite EOSAT-1 lorsque la liaison TT&C est perdue pendant
une fenêtre d'acquisition du signal (AOS) prévue. La perte de liaison est confirmée lorsque
`ttc.link_status` = 0 persiste plus de 30 secondes après l'AOS prévue, ou lorsqu'une
liaison établie tombe de façon inattendue en cours de passage. Cette procédure tente une commutation de transpondeur
et le rétablissement de la liaison avant de passer aux opérations autonomes d'urgence.

## Prérequis
- [ ] L'antenne de la station sol poursuit bien le satellite avec un pointage valide
- [ ] La prévision d'orbite est à jour (propagée dans les 6 dernières heures) et les heures d'AOS/LOS sont valides
- [ ] La chaîne RF de la station sol a été vérifiée nominale (puissance de liaison montante, fréquence, polarisation)
- [ ] Il reste au moins 5 minutes de passage pour la tentative de rétablissement
- [ ] La procédure d'urgence EMG-004 est disponible pour l'escalade

## Déroulement

### Étape 1 — Confirmer que la perte de liaison n'est pas un problème sol
**Action:** Vérifier l'état de la station sol — poursuite de l'antenne, puissance de l'émetteur de liaison montante, verrouillage du récepteur
**Action:** Confirmer que la précompensation Doppler est correctement appliquée pour le passage en cours
**Action:** Rechercher un brouillage RF local ou une atténuation d'origine météorologique à la station sol
**GO/NO-GO:** Si une anomalie de la station sol est identifiée, la résoudre localement. Si le sol est confirmé nominal, procéder au rétablissement côté satellite.

### Étape 2 — Tenter une réacquisition sur le transpondeur principal
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — commande en aveugle, aucune télémesure attendue
**Action:** Attendre 30 s que le transpondeur traite la commande et tente la réacquisition de la liaison descendante
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) en 30 s
**Verify:** page TT&C (sol) : `ttc.rssi` (0x0502) > -126 dBm si la liaison se rétablit
**GO/NO-GO:** Si la liaison se rétablit, l'étape 5 (contrôle de santé) s'applique. Sans réponse, l'étape 3 s'applique.
**BRANCH:** `ttc.link_status == 2` -> GO `STEP-5` | NO-GO `STEP-3` (timeout 30 s)

### Étape 3 — Basculer sur le transpondeur redondant
**LABEL:** `STEP-3`
**TC:** `TTC_SWITCH_REDUNDANT` (Service 8, Subtype 1) — commande en aveugle
**Note:** Les transpondeurs sont en redondance froide : le basculement n'est reçu que par l'unité
SÉLECTIONNÉE. Si le transpondeur principal est en panne, il n'entend rien et cette commande est perdue ---
le basculement ne se fait alors qu'à bord, à l'expiration du temporisateur de perte de commande (étape 6).
Il vaut quand même la peine de l'envoyer : si la perte vient de la chaîne d'émission (PA coupé, ligne
`ttc_tx` délestée), le récepteur fonctionne et l'exécute.
**Action:** Attendre 45 s la mise sous tension et le verrouillage en fréquence du transpondeur redondant
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) en 45 s
**Verify:** `ttc.mode` (0x0500) indique que l'unité redondante est active
**GO/NO-GO:** Si la liaison se rétablit sur l'unité redondante, l'étape 5 s'applique. Sans réponse, l'étape 4 s'applique.
**BRANCH:** `ttc.link_status == 2` -> GO `STEP-5` | NO-GO `STEP-4` (timeout 45 s)

### Étape 4 — Deuxième tentative : réessayer le transpondeur principal
**LABEL:** `STEP-4`
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1) — commande en aveugle
**Action:** Attendre 45 s la réinitialisation du transpondeur principal
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) en 45 s
**GO/NO-GO:** Si la liaison se rétablit, l'étape 5 s'applique. Toujours sans liaison après essai des deux transpondeurs, l'étape 6 (escalade) s'applique.
**BRANCH:** `ttc.link_status == 2` -> GO `STEP-5` | NO-GO `STEP-6` (timeout 45 s)

### Étape 5 — Vérifier la qualité de la liaison et la santé des sous-systèmes
**LABEL:** `STEP-5`
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27)
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED)
**Verify:** page TT&C (sol) : `ttc.rssi` (0x0502) > -126 dBm (niveau de signal nominal)
**Verify:** page TT&C (sol) : `ttc.link_margin` (0x0503) > 3.0 dB
**Verify:** `ttc.mode` (0x0500) — consigner le transpondeur actif
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Télémesure de servitude plateforme/OBDH
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Télémesure de servitude TT&C
**Verify:** `eps.bus_voltage` (0x0105) > 27.0 V — confirmer qu'aucune anomalie EPS n'a causé la perte de liaison
**Verify:** `obdh.mode` (0x0300) — confirmer que l'OBC n'est pas passé en mode safe/emergency
**GO/NO-GO:** Marge de liaison > 3 dB et tous les sous-systèmes nominaux — rétablissement terminé -> GO `STEP-END` | NO-GO `STEP-6`

### Étape 6 — Escalade : liaison non rétablie
**LABEL:** `STEP-6`
**Action:** Consigner l'échec de la tentative de rétablissement avec l'horodatage de toutes les commandes envoyées en aveugle
**Action:** Informer le directeur de mission et la dynamique du vol de la perte de liaison persistante
**Action:** Programmer le prochain passage disponible sur une station sol pour une tentative de réacquisition
**Action:** Consigner l'heure de la dernière télécommande ACCEPTÉE (dernier S1.1). Le temporisateur de perte de commande de bord (FDIR TTC-01, `ttc.time_since_last_tc` 0x053D) bascule le satellite sur le transpondeur redondant 24 h après celle-ci (événement CMD_LOSS_TIMEOUT 0x0514, S19 ea 4003) : programmer les premiers passages qui suivent cette heure. Les commandes en aveugle qui ne sont pas reçues ne le remettent pas à zéro
**GO/NO-GO:** Sans liaison après deux passages consécutifs, passer à EMG-004 (Perte de communication)

## Conduite à tenir hors nominal
- Si la liaison se rétablit mais avec un RSSI < -95 dBm ou une marge < 1.5 dB : descendre l'échelle de débits TM jusqu'au échelon LOW (16 kbit/s) via `TTC_SET_DATA_RATE(rate=0)` (func_id 65) pour améliorer la marge. LOW est le échelon des opérations de routine — la liaison conserve toute la télémesure de servitude, elle ne peut simplement pas effectuer de vidage
- Si l'OBC est en mode SAFE après le rétablissement de la liaison : exécuter CTG-010 (Reprise après chien de garde OBDH) avant de reprendre les opérations nominales
- Si le transpondeur redondant est lui aussi défaillant : aucune télécommande ne peut être reçue et aucune télémesure n'est émise, balise comprise ; le basculement TTC-01 est refusé. Rien depuis le sol ne peut y remédier : passer à EMG-004 et rester à l'écoute du rétablissement d'un transpondeur (dans le simulateur, l'instructeur qui efface une panne de transpondeur)
- Si la liaison est intermittente (bascule) : suspecter une anomalie de déploiement d'antenne ou un problème d'attitude — demander la télémesure AOCS et contrôler `aocs.att_error` (0x0217)

## Postconditions
**LABEL:** `STEP-END`
- [ ] `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] `ttc.link_margin` (0x0503) > 3.0 dB
- [ ] Transpondeur actif identifié et consigné
- [ ] Cause première documentée (problème sol, panne de transpondeur, attitude ou EPS)
- [ ] En l'absence de rétablissement : escalade EMG-004 lancée, avec le plan du prochain passage
