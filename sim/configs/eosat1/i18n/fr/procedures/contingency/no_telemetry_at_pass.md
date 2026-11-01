# CTG-019 : Absence de télémesure en début de passage

**Catégorie :** Contingence
**Poste responsable :** TT&C
**Postes associés :** Directeur de vol, EPS/TCS
**Difficulté :** Avancé

## Objectif
Rétablir la liaison descendante de télémesure lorsqu'aucun signal du satellite n'est reçu à l'heure
prévue d'acquisition du signal (AOS). Cette procédure parcourt méthodiquement la
chaîne RF, de la station sol jusqu'au transpondeur, à l'amplificateur de puissance
et au système d'antennes du satellite, afin d'identifier et de résoudre la cause racine. Elle couvre la vérification de la ligne
d'alimentation EPS, la commande du PA, les contrôles du déploiement d'antenne et le basculement de transpondeur.

## Prérequis
- [ ] La station sol poursuit le satellite avec un pointage d'antenne valide
- [ ] La prévision d'orbite est à jour (propagée au cours des 6 dernières heures)
- [ ] Chaîne RF de la station sol vérifiée : émetteur montant en marche, récepteur verrouillé sur la fréquence attendue
- [ ] Précompensation Doppler appliquée pour la géométrie du passage courant
- [ ] Il reste au moins 8 minutes de passage prévu
- [ ] Directeur de vol informé de l'absence de TM

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| ttc.link_status | 0x0501 | 2 (LOCKED) — actuellement 0 (NO_LINK) ou 1 (ACQUIRING) (condition de déclenchement) |
| ttc.rssi | 0x0502 | > -95 dBm lorsque la liaison est active |
| ttc.link_margin | 0x0503 | > 3.0 dB lorsque la liaison est active |
| ttc.pa_on | 0x0516 | 1 (PA en marche) |
| ttc.pa_temp | 0x050F | < 55 °C |
| ttc.tx_fwd_power | 0x050D | Puissance incidente nominale |
| ttc.carrier_lock | 0x0510 | 1 (verrouillée) |
| ttc.bit_sync | 0x0511 | 1 (synchronisé) |
| ttc.antenna_deployed | 0x0520 | 1 (déployée) |
| ttc.eb_n0 | 0x0519 | > 10 dB lorsque la liaison est active |
| ttc.ber | 0x050C | < -5 lorsque la liaison est active |
| eps.pl_ttc_tx | 0x0112 | 1 (ligne d'alimentation TX sous tension) |
| eps.bus_voltage | 0x0105 | > 27.0 V |

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | -- | Demander un rapport HK ponctuel |
| EPS_POWER_ON | 8 | 1 | 19 | Mettre une ligne d'alimentation sur ON |
| TTC_PA_ON | 8 | 1 | 66 | Mettre en marche l'amplificateur de puissance |
| TTC_PA_OFF | 8 | 1 | 67 | Arrêter l'amplificateur de puissance |
| TTC_DEPLOY_ANTENNA | 8 | 1 | 69 | Activer le fil thermofusible de déploiement de l'antenne |
| TTC_SWITCH_REDUNDANT | 8 | 1 | 64 | Basculer sur le transpondeur redondant |
| TTC_SWITCH_PRIMARY | 8 | 1 | 63 | Basculer sur le transpondeur principal |
| TTC_SET_TX_POWER | 8 | 1 | 68 | Régler le niveau de puissance d'émission |
| CONNECTION_TEST | 17 | 1 | -- | Test de connexion S17 (ping) |

## Déroulement

### Étape 1 : Confirmer que la station sol est nominale
**Action:** Vérifier que l'antenne de la station sol poursuit le satellite avec des données de pointage valides.
**Action:** Confirmer que l'émetteur montant est alimenté et réglé sur la bonne fréquence et la bonne polarisation.
**Action:** Vérifier que la précompensation Doppler est appliquée pour la géométrie du passage courant.
**Action:** Rechercher d'éventuelles interférences RF locales ou des conditions météorologiques défavorables à la station sol.
**Action:** Confirmer que le récepteur balaie la fréquence descendante attendue.
**Note:** Si la station sol s'avère en défaut (antenne en position de repos, émetteur arrêté, mauvaise
fréquence), résoudre le problème localement. Ne pas engager la reprise côté satellite tant que le sol
n'est pas confirmé nominal.
**GO/NO-GO:** Station sol confirmée nominale — engager le diagnostic côté satellite.

### Étape 2 : Contrôler l'état de la ligne d'alimentation TX du TTC
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Envoyer une demande HK en aveugle — EPS
**Note:** Il s'agit d'une commande en aveugle — aucun retour de télémesure n'est attendu si la liaison descendante est hors service.
Le but est de déclencher une activité sur la liaison descendante et de rechercher un signal faible.
**Action:** Attendre 30 s et vérifier si le récepteur de la station sol indique un signal.
**Action:** Si le récepteur sol détecte une porteuse faible, l'étape 4 (analyse du PA) s'applique.
**GO/NO-GO:** Le récepteur sol détecte une porteuse faible -> GO `STEP-4` | NO-GO `STEP-2B`
**LABEL:** `STEP-2B`
**Action:** En l'absence totale de signal, évaluer si la ligne d'alimentation TX du TTC peut être coupée.
**Note:** Le paramètre `eps.pl_ttc_tx` (0x0112) indique l'état de la ligne d'alimentation TX, mais sa lecture
exige une liaison descendante opérationnelle. Si la ligne d'alimentation TX a disjoncté sur une surintensité,
le transpondeur n'a plus d'alimentation pour émettre.
**TC:** `EPS_POWER_ON(line_index=2)` (Service 8, Subtype 1, func_id 19) — Envoyer une commande de mise sous tension en aveugle
cette commande met la ligne d'alimentation TX du TTC sur ON.
**Verify:** Attendre 30 s la mise sous tension et la réacquisition du transpondeur.
**Verify:** Rechercher la porteuse descendante sur le récepteur de la station sol.
**GO/NO-GO:** Si un signal apparaît, l'étape 6 (vérification de la liaison) s'applique. Toujours sans signal, l'étape 3 s'applique. -> GO `STEP-6` | NO-GO `STEP-3`

### Étape 3 : Commander le basculement de transpondeur (en aveugle)
**LABEL:** `STEP-3`
**Note:** Le transpondeur principal est peut-être en panne. Tenter un basculement en aveugle :
**TC:** `TTC_SWITCH_REDUNDANT` (Service 8, Subtype 1, func_id 64) — commande en aveugle
**Verify:** Attendre 45 s la mise sous tension et le verrouillage en fréquence du transpondeur redondant.
**Verify:** Rechercher la porteuse descendante sur la fréquence du transpondeur redondant, sur le récepteur de la station sol.
**Action:** Si un signal est détecté sur le transpondeur redondant : l'étape 6 (vérification de la liaison) s'applique.
**GO/NO-GO:** Signal détecté sur le transpondeur redondant -> GO `STEP-6` | NO-GO `STEP-3B`
**LABEL:** `STEP-3B`
**Note:** Uniquement si le transpondeur redondant n'a pas non plus produit de signal.
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1, func_id 63) — revenir au transpondeur principal
**Action:** Attendre 30 s.
**GO/NO-GO:** Si aucun des deux transpondeurs ne produit de signal, l'étape 4 (contrôle du PA) s'applique.

### Étape 4 : Commander la mise en marche du PA (en aveugle)
**LABEL:** `STEP-4`
**Note:** Le PA est peut-être désactivé. Envoyer en aveugle la commande de mise en marche du PA :
**TC:** `TTC_PA_ON` (Service 8, Subtype 1, func_id 66)
**Verify:** Attendre 15 s la mise sous tension du PA.
**Verify:** Rechercher la porteuse descendante sur le récepteur de la station sol.
**Action:** Si un signal est détecté : l'étape 6 (vérification de la liaison) s'applique.
**GO/NO-GO:** Signal détecté après la mise en marche du PA -> GO `STEP-6` | NO-GO `STEP-4B`
**LABEL:** `STEP-4B`
**Note:** En l'absence de signal : la mise en marche du PA n'a peut-être pas pris effet. Tenter un cycle du PA :
**TC:** `TTC_PA_OFF` (Service 8, Subtype 1, func_id 67) — attendre 10 s
**TC:** `TTC_PA_ON` (Service 8, Subtype 1, func_id 66) — attendre 15 s
**Verify:** Rechercher la porteuse descendante sur le récepteur de la station sol.
**GO/NO-GO:** Si un signal est détecté, l'étape 6 s'applique. Toujours sans signal, l'étape 5 s'applique. -> GO `STEP-6` | NO-GO `STEP-5`

### Étape 5 : Contrôler le déploiement de l'antenne et la déployer si nécessaire
**LABEL:** `STEP-5`
**Action:** Si le satellite est en début de mission (après séparation) ou si l'état de déploiement de
l'antenne est incertain, les antennes sont peut-être encore repliées. Une antenne repliée
produit un signal fortement atténué (perte >20 dB).
**GO/NO-GO:** État de déploiement de l'antenne réellement incertain, ou antenne connue comme repliée -> GO `STEP-5D` | NO-GO `STEP-7`
**LABEL:** `STEP-5D`
**Note:** Envoyer en aveugle la commande de déploiement de l'antenne. Le mnémonique est
`TTC_DEPLOY_ANTENNA` (au singulier) et la fonction est la **69**.
**DANGER — corrigé en 2026-08b :** cette carte indiquait auparavant `func_id 56`.
La func 56 est `OBC_BOOT_INHIBIT`, dont l'octet de données maintient l'OBC dans le
chargeur d'amorçage. Envoyée en aveugle, sur un satellite déjà privé de télémesure, dans
l'hypothèse d'une antenne repliée, elle aurait INHIBÉ LE DÉMARRAGE AUTOMATIQUE — la
seule action qui transforme un problème RF récupérable en un satellite qui redémarre
dans le chargeur d'amorçage avec le PA bande S inhibé et seulement le SID HK 11 sur la balise
UHF. Comme elle était envoyée en aveugle, personne ne s'en serait aperçu.
**TC:** `TTC_DEPLOY_ANTENNA` (Service 8, Subtype 1, func_id 69) — active le fil thermofusible de libération de l'antenne
**ATTENTION :** Il s'agit d'une commande pyrotechnique irréversible, à coup unique. Ne l'exécuter que si
l'état de déploiement de l'antenne est réellement incertain ou si l'antenne est connue comme repliée.
**Verify:** Attendre 30 s que le mécanisme de déploiement agisse et que l'antenne se
déploie. Si une télémesure est reçue, `ttc.antenna_deployed` (0x0520)
passe à 1 et `ttc.antenna_deployment_sensor` (0x0536) indique 2 (DEPLOYED) ;
`ttc.antenna_deployment_ready` (0x0535) = 0 avant la tentative signifierait que
la continuité pyrotechnique est déjà défaillante et que la commande ne s'exécutera pas.
**Verify:** Rechercher la porteuse descendante sur le récepteur de la station sol. Le déploiement de l'antenne devrait
améliorer considérablement le niveau du signal (gain supplémentaire de 15-25 dB).
**GO/NO-GO:** Si un signal est détecté, l'étape 6 (vérification de la liaison) s'applique. Toujours sans signal après tous les contrôles de la chaîne RF, l'étape 7 (escalade) s'applique. -> GO `STEP-6` | NO-GO `STEP-7`

### Étape 6 : Vérifier la qualité de la liaison et l'état des sous-systèmes
**LABEL:** `STEP-6`
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Demander les données de servitude TTC
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED)
**Verify:** page TT&C (sol) : `ttc.rssi` (0x0502) > -126 dBm (niveau de signal nominal)
**Verify:** page TT&C (sol) : `ttc.link_margin` (0x0503) > 3.0 dB
**Verify:** `ttc.pa_on` (0x0516) = 1
**Verify:** `ttc.pa_temp` (0x050F) < 55 °C
**Verify:** `ttc.antenna_deployed` (0x0520) = 1
**Verify:** `ttc.carrier_lock` (0x0510) = 1
**Verify:** `ttc.bit_sync` (0x0511) = 1
**Verify:** page radio (sol) : `ttc.eb_n0` (0x0519) > 10 dB
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander les données de servitude EPS
**Verify:** `eps.bus_voltage` (0x0105) > 27.0 V — confirmer l'absence d'anomalie EPS
**Verify:** `eps.pl_ttc_tx` (0x0112) = 1 — ligne d'alimentation TX confirmée sur ON
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander les données de servitude OBDH
**Verify:** `obdh.mode` (0x0300) — confirmer que l'OBC n'est pas passé en mode survie ou EMERGENCY
**Action:** Consigner l'étape de reprise qui a rétabli la liaison :
- étape 2 : la ligne d'alimentation TX était coupée ;
- étape 3 : panne du transpondeur principal, fonctionnement désormais sur le redondant ;
- étape 4 : le PA était désactivé ;
- étape 5 : les antennes étaient repliées.
**GO/NO-GO:** Marge de liaison > 3 dB, tous les sous-systèmes nominaux — reprise terminée. -> GO `STEP-END` | NO-GO `STEP-7`

### Étape 7 : Escalade — liaison non rétablie
**LABEL:** `STEP-7`
**Action:** Consigner toutes les commandes envoyées en aveugle, avec leur horodatage.
**Action:** Informer le directeur de vol et le directeur de mission de la persistance de l'absence de TM.
**Action:** Confirmer que la temporisation du mode survie autonome du satellite est active (déclenchement après 24 h sans contact).
**Action:** Programmer le prochain passage disponible sur une station sol pour une tentative de réacquisition.
**TC:** `TTC_SET_TX_POWER(level=2)` (Service 8, Subtype 1, func_id 68) — mode haute puissance pour la prochaine tentative, afin d'améliorer le bilan de liaison.
**GO/NO-GO:** Sans liaison après deux tentatives sur des passages consécutifs, passer à EMG-004
(Urgence : perte de communication).

## Critères de vérification
**LABEL:** `STEP-END`
- [ ] `ttc.link_status` (0x0501) = 2 (liaison LOCKED établie)
- [ ] `ttc.rssi` (0x0502) > -90 dBm
- [ ] `ttc.link_margin` (0x0503) > 3.0 dB
- [ ] `ttc.pa_on` (0x0516) = 1
- [ ] `ttc.antenna_deployed` (0x0520) = 1
- [ ] `eps.pl_ttc_tx` (0x0112) = 1 (ligne d'alimentation TX sur ON)
- [ ] Cause racine identifiée et documentée
- [ ] En l'absence de rétablissement : escalade EMG-004 engagée

## Contingence
- Si la liaison se rétablit mais que le RSSI est < -95 dBm ou la marge < 1.5 dB : descendre en LOW
  (16 kbit/s) au moyen de `TTC_SET_DATA_RATE(rate=0)` (func_id 65) pour gagner 9,03 dB d'Eb/N0
  plus 1,5 dB de gain de codage. LOW est le débit des opérations courantes : la seule perte
  est la possibilité de vidage. Rechercher une dégradation de l'antenne ou du PA.
- Si le PA se remet en marche mais s'arrête aussitôt : sa protection thermique ou contre les surintensités a peut-être
  disjoncté. Contrôler `ttc.pa_temp` (0x050F). Au-delà de 65 °C, la protection thermique du PA
  est active. Attendre le refroidissement avant de réessayer.
- Si la commande de déploiement de l'antenne a été envoyée sans amélioration du signal : le mécanisme de
  déploiement est peut-être en panne (fil thermofusible non activé, antenne coincée). Il s'agit d'une
  panne matérielle définitive. S'appuyer sur l'antenne courte, avec un bilan de liaison réduit.
- Si l'OBC est trouvé en mode SAFE ou EMERGENCY après le rétablissement de la liaison : appliquer
  CTG-010 (Reprise après chien de garde OBDH) ou CTG-011 (Basculement sur l'OBC redondant) selon le cas avant de reprendre les
  opérations nominales.
- Si le signal est intermittent (alternance présence/absence) : suspecter un problème d'attitude plaçant
  l'antenne dans un creux du diagramme de rayonnement. Demander la télémesure SCAO : contrôler `aocs.att_error` (0x0217)
  et `aocs.mode` (0x020F).
