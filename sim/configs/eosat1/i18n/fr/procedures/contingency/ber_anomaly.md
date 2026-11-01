# CTG-014 : Anomalie de TEB

**Catégorie :** Contingence
**Poste responsable :** TT&C
**Postes associés :** Directeur de vol
**Difficulté :** Intermédiaire

## Objectif
Analyser une hausse anormale du taux d'erreur binaire (TEB) sur la liaison descendante de télémesure.
Cette procédure contrôle de façon systématique les paramètres de qualité de liaison, l'état de l'amplificateur de puissance
et celui du transpondeur afin d'identifier la cause racine. Les actions correctives comprennent la réduction du
débit et le basculement sur le transpondeur redondant si l'unité principale est dégradée.

## Prérequis
- [ ] Anomalie de TEB détectée — `ttc.ber` (0x050C) >= -5 (TEB plus mauvais que 1e-5)
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] La station sol a confirmé que l'anomalie ne provient pas du segment sol
- [ ] Directeur de vol informé

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| ttc.ber | 0x050C | < -5 en nominal ; >= -5 déclenche cette procédure |
| ttc.eb_n0 | 0x0519 | > 10 dB en nominal |
| ttc.pa_temp | 0x050F | < 55 °C en nominal |
| ttc.pa_on | 0x0516 | 1 (PA actif) |
| ttc.tx_fwd_power | 0x050D | Puissance incidente nominale |
| ttc.link_margin | 0x0503 | > 3 dB en nominal |
| ttc.rssi | 0x0502 | Niveau du signal |
| ttc.xpdr_temp | 0x0507 | < 50 °C en nominal |
| ttc.carrier_lock | 0x0510 | 1 (verrouillée) |
| ttc.bit_sync | 0x0511 | 1 (synchronisé) |
| ttc.frame_sync | 0x0512 | 1 (synchronisé) |
| ttc.tm_data_rate | 0x0506 | Débit d'information actif (SAFE 1000 / LOW 16000 / HIGH 128000 bit/s) |
| ttc.tm_tier | 0x0539 | Indice du palier ACTIF (0=SAFE, 1=LOW, 2=HIGH) |
| ttc.tm_tier_cmd | 0x053A | Indice du palier COMMANDÉ |
| ttc.downlink_mode | 0x053C | 1 pendant un vidage en cours |
| ttc.contact_elevation | 0x050A | Élévation courante (HIGH exige >= 10°) |

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| TTC_SET_DATA_RATE | 8 | 1 | 65 | Descendre d'un palier dans l'échelle des débits TM (0=LOW 16 kbit/s, 1=HIGH 128 kbit/s) |
| TTC_SET_DOWNLINK_MODE | 8 | 1 | 79 | Quitter le mode DOWNLINK en cas d'abandon d'un vidage à haut débit |
| TTC_SWITCH_REDUNDANT | 8 | 1 | 64 | Basculer sur le transpondeur redondant |
| TTC_SWITCH_PRIMARY | 8 | 1 | 63 | Revenir sur le transpondeur principal |
| TTC_PA_OFF | 8 | 1 | 67 | Arrêter l'amplificateur de puissance |
| TTC_PA_ON | 8 | 1 | 66 | Mettre en marche l'amplificateur de puissance |
| TTC_SET_TX_POWER | 8 | 1 | 68 | Ajuster le niveau de puissance d'émission |

## Déroulement

### Étape 1 : Caractériser l'anomalie de TEB
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Demander les données de servitude TTC
**Verify:** page radio (sol) : `ttc.ber` (0x050C) — consigner la valeur courante (attendue >= -5)
**Verify:** page radio (sol) : `ttc.eb_n0` (0x0519) — consigner la valeur d'Eb/N0
**Verify:** page TT&C (sol) : `ttc.link_margin` (0x0503) — consigner la marge de liaison
**Verify:** page TT&C (sol) : `ttc.rssi` (0x0502) — consigner le RSSI
**Verify:** `ttc.tm_data_rate` (0x0506) — consigner le débit courant
**Verify:** page TT&C (sol) : `ttc.contact_elevation` (0x050A) — consigner l'angle d'élévation
**Verify:** `ttc.carrier_lock` (0x0510), `ttc.bit_sync` (0x0511), `ttc.frame_sync` (0x0512)
**Note:** Si l'élévation est faible (< 10°), la dégradation du TEB peut être normale, du fait de
l'atténuation atmosphérique et d'un gain faible. Attendre une élévation plus haute avant de déclarer l'anomalie.
**GO/NO-GO:** Anomalie de TEB confirmée comme non due à la géométrie — engager l'analyse du PA.

### Étape 2 : Contrôler la température de l'amplificateur de puissance
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Demander les données de servitude TTC
**Verify:** `ttc.pa_temp` (0x050F) — consigner la valeur
**Verify:** `ttc.pa_on` (0x0516) = 1 (PA actif)
**Verify:** `ttc.tx_fwd_power` (0x050D) — consigner la puissance incidente
**Action:** Évaluer l'état du PA :
- Si `ttc.pa_temp` > 55 °C : le PA surchauffe. L'étape 3 (réduction de la charge thermique) s'applique.
- Si `ttc.pa_temp` < 55 °C et que `ttc.tx_fwd_power` est plus basse que prévu : le PA est peut-être
  dégradé. L'étape 4 (réduction du débit) s'applique.
- Si tous les paramètres du PA sont nominaux : le problème vient peut-être du segment sol ou d'interférences.
  L'étape 4 (réduction du débit) s'applique comme mesure d'atténuation.
**GO/NO-GO:** Évaluation du PA terminée — suivre la branche appropriée.
**BRANCH:** `ttc.pa_temp > 55` -> GO `STEP-3` | NO-GO `STEP-4` (timeout 10 s)

### Étape 3 : Surchauffe du PA — réduction de la charge thermique
**LABEL:** `STEP-3`
**Note:** Si la température du PA est > 55 °C, réduire la charge thermique :
**TC:** `TTC_PA_OFF` (Service 8, Subtype 1, func_id 67) — Commander l'arrêt du PA
**Note:** Attendre 120 s pour le refroidissement
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Demander les données de servitude TTC
**Note:** **Verify:** `ttc.pa_temp` (0x050F) en baisse
**TC:** `TTC_PA_ON` (Service 8, Subtype 1, func_id 66) — Commander la remise en marche du PA
**Note:** **Verify:** `ttc.pa_on` (0x0516) = 1 en moins de 5 s
**Note:** Si la température du PA reste > 50 °C après la remise en marche, réduire le niveau de puissance d'émission :
**BRANCH:** `ttc.pa_temp > 50` -> GO `STEP-3B` | NO-GO `STEP-3C` (timeout 10 s)
**LABEL:** `STEP-3B`
**TC:** `TTC_SET_TX_POWER(level=0)` (Service 8, Subtype 1, func_id 68) — régler sur la puissance basse (1 W)
**LABEL:** `STEP-3C`
**Verify:** `ttc.pa_temp` (0x050F) en cours de stabilisation
**Verify:** page radio (sol) : `ttc.ber` (0x050C) — vérifier si le TEB s'améliore avec un PA plus froid
**Note:** Si la surchauffe du PA persiste, appliquer EMG-006 pour l'analyse thermique
de la zone du transpondeur.
**GO/NO-GO:** Si le TEB s'est amélioré, poursuivre la surveillance. Sinon, l'étape 4 s'applique.
**BRANCH:** `ttc.ber < -5` -> GO `STEP-END` | NO-GO `STEP-4` (timeout 30 s)

### Étape 4 : Descendre dans l'échelle des débits
**LABEL:** `STEP-4`
**Note:** Utile uniquement si le palier ACTIF (0x0539) est au-dessus de LOW. Passer de HIGH
(128 kbit/s) à LOW (16 kbit/s) fait gagner 9,03 dB d'Eb/N0 — le terme `-10*log10(R)` — et
change aussi la forme d'onde, de QPSK RS(255,223) à BPSK conv(7,1/2)+RS, soit 1,5 dB
de gain de codage supplémentaire. Si la liaison est déjà en LOW, il n'existe aucun palier opérationnel en dessous :
SAFE (1 kbit/s, ex-BEACON) est la liaison de secours du chargeur d'amorçage et ne peut pas être commandé ici ; l'étape 5 s'applique alors directement.
**BRANCH:** `ttc.tm_tier > 1` -> GO `STEP-4H` | NO-GO `STEP-5` (timeout 10 s)
**LABEL:** `STEP-4H`
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) — Descendre au palier LOW
**Verify:** `ttc.tm_data_rate` (0x0506) = 16000 bit/s en moins de 10 s
**Verify:** `ttc.tm_tier` (0x0539) = 1 (LOW) et égal à `ttc.tm_tier_cmd` (0x053A)
**Verify:** `ttc.tm_symbol_rate` (0x053B) = 16000 Bd (BPSK)
**Verify:** `ttc.carrier_lock` (0x0510) = 1
**Verify:** `ttc.bit_sync` (0x0511) = 1
**Action:** Si un vidage était en cours, libérer également la porte :
**BRANCH:** `ttc.downlink_mode == 1` -> GO `STEP-4D` | NO-GO `STEP-4W` (timeout 10 s)
**LABEL:** `STEP-4D`
**TC:** `TTC_SET_DOWNLINK_MODE(on=0)` (Service 8, Subtype 1, func_id 79)
**Verify:** `ttc.downlink_mode` (0x053C) = 0
**LABEL:** `STEP-4W`
**Note:** Attendre 30 s que le TEB se stabilise, puis demander les données de servitude TTC :
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27)
**Verify:** page radio (sol) : `ttc.ber` (0x050C) < -5 (TEB amélioré au palier inférieur)
**Verify:** page radio (sol) : `ttc.eb_n0` (0x0519) > 10 dB au palier inférieur
**Action:** Si le TEB s'est amélioré :
- la cause racine est probablement une marge de liaison insuffisante en HIGH pour la géométrie de ce passage ;
- rester en LOW pour ce contact — LOW est le débit des opérations courantes, seul le vidage est donc
  perdu. Replanifier le vidage sur un passage plus haut et réévaluer le bilan de
  liaison (`tools/link_budget_ladder.py`) avant la prochaine tentative à haut débit.
**Action:** Si le TEB ne s'est PAS amélioré en LOW : le problème ne tient pas seulement au débit.
L'étape 5 (basculement de transpondeur) s'applique.
**GO/NO-GO:** Si le TEB est acceptable en LOW, surveiller et consigner. Sinon, l'étape 5 s'applique.
**BRANCH:** `ttc.ber < -5` -> GO `STEP-END` | NO-GO `STEP-5` (timeout 30 s)

### Étape 5 : Tenter un basculement de transpondeur
**LABEL:** `STEP-5`
**TC:** `TTC_SWITCH_REDUNDANT` (Service 8, Subtype 1, func_id 64) — Basculer sur le transpondeur redondant
**Verify:** Attendre 15 s l'initialisation du transpondeur redondant
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Demander les données de servitude TTC
**Verify:** `ttc.carrier_lock` (0x0510) = 1 (réacquisition sur l'unité redondante)
**Verify:** `ttc.bit_sync` (0x0511) = 1
**Verify:** `ttc.frame_sync` (0x0512) = 1
**Verify:** page radio (sol) : `ttc.ber` (0x050C) — vérifier si le TEB s'est amélioré
**Verify:** `ttc.xpdr_temp` (0x0507) — consigner la température du transpondeur redondant
**Action:** Si le TEB s'est amélioré sur le transpondeur redondant : le transpondeur principal est dégradé.
Consigner une anomalie matérielle. Poursuivre les opérations sur l'unité redondante.
**BRANCH:** `ttc.ber < -5` -> GO `STEP-END` | NO-GO `STEP-5B` (timeout 30 s)
**LABEL:** `STEP-5B`
**Note:** Si le TEB ne s'est PAS amélioré : le problème est probablement externe (interférences, segment sol,
ou problème d'antenne). Revenir au transpondeur principal :
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1, func_id 63)
**Note:** Rester en LOW (16 kbit/s) et faire remonter pour une analyse du segment sol.
**GO/NO-GO:** Évaluation du transpondeur terminée. Consigner les constats et poursuivre dans la meilleure
configuration.

## Critères de vérification
**LABEL:** `STEP-END`
- [ ] `ttc.ber` (0x050C) < -5 (TEB acceptable rétabli)
- [ ] `ttc.carrier_lock` (0x0510) = 1
- [ ] `ttc.bit_sync` (0x0511) = 1 et `ttc.frame_sync` (0x0512) = 1
- [ ] `ttc.pa_temp` (0x050F) < 55 °C
- [ ] Cause racine identifiée ou circonscrite
- [ ] Rapport d'anomalie déposé avec toutes les valeurs de télémesure consignées

## Contingence
- Si la liaison est perdue pendant le basculement de transpondeur : la station sol doit balayer pour rechercher le signal
  sur la fréquence du nouveau transpondeur. Attendre jusqu'à 60 s la réacquisition. Sans liaison après
  60 s, tenter de revenir en arrière : `TTC_SWITCH_PRIMARY` (func_id 63). Toujours sans liaison,
  appliquer CTG-003.
- Si les deux transpondeurs présentent un TEB dégradé : suspecter un problème d'antenne ou de réseau d'alimentation d'antenne. Rester
  en LOW (16 kbit/s — le plus bas échelon opérationnel commandable ; le échelon SAFE est réservé au chargeur d'amorçage)
  et porter la puissance d'émission au niveau haut : `TTC_SET_TX_POWER(level=2)`.
  Faire remonter à l'équipe d'ingénierie.
- Si le PA ne se remet pas en marche après refroidissement : il est peut-être en panne définitive. Basculer sur le
  transpondeur redondant, qui dispose de son propre PA : `TTC_SWITCH_REDUNDANT` (func_id 64).
- Si le TEB continue de se dégrader pendant le contact : risque de perte totale de la liaison. Envoyer
  immédiatement toute commande critique tant que la liaison est disponible. Se préparer à des opérations
  autonomes jusqu'au contact suivant.
