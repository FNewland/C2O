# CTG-017 : Basculement sur panne de bus

**Catégorie :** Contingence
**Poste responsable :** FDIR / Systèmes
**Postes associés :** Directeur de vol, tous les postes
**Difficulté :** Avancé

## Objectif
Traiter une panne de bus CAN entraînant la perte de la télémesure de servitude d'un ou
plusieurs sous-systèmes. Cette procédure identifie le bus défaillant, commande le basculement sur
le bus redondant et vérifie que les données de servitude de tous les sous-systèmes reprennent sur le nouveau bus.

## Prérequis
- [ ] Données de servitude absentes pour un ou plusieurs sous-systèmes (paquets HK non reçus)
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] L'OBC répond — `obdh.mode` (0x0300) peut être interrogé
- [ ] Directeur de vol informé, ayant autorisé le basculement de bus

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| obdh.bus_a_status | 0x030F | 0 (OK) ou 1 (ERROR) |
| obdh.bus_b_status | 0x0310 | 0 (OK) ou 1 (ERROR) |
| obdh.active_bus | 0x030E | 0 (bus A) ou 1 (bus B) |
| obdh.mode | 0x0300 | Mode OBC courant |
| obdh.cpu_load | 0x0302 | Surveiller toute hausse anormale |
| eps.bat_soc | 0x0101 | Consigner la valeur courante |
| eps.bus_voltage | 0x0105 | Consigner la valeur courante |
| aocs.mode | 0x020F | Vérifier après le basculement |
| payload.mode | 0x0600 | Vérifier après le basculement |
| ttc.link_status | 0x0501 | 2 (LOCKED) |

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| OBC_SELECT_BUS | 8 | 1 | 54 | Sélectionner le bus CAN actif (0=A, 1=B) |

## Déroulement

### Étape 1 : Détecter l'absence de données de servitude
**Action:** Identifier les sous-systèmes absents de la télémesure de servitude.
**Note:** Demander un rapport HK à chaque sous-système :
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — TCS
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — OBDH
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TTC
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Charge utile
**Verify:** Relever les SID dont la réponse est reçue et ceux qui manquent.
**Note:** Si seul l'OBDH répond (SID 4), le bus CAN qui raccorde les sous-systèmes externes
est probablement en panne. Si aucune réponse n'est reçue, le problème vient peut-être de l'OBC ou du TTC
plutôt que du bus.
**GO/NO-GO:** Absence de données HK confirmée pour plusieurs sous-systèmes — engager le diagnostic du bus.

### Étape 2 : Contrôler l'état des bus
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander les données de servitude OBDH
**Verify:** `obdh.bus_a_status` (0x030F) — consigner la valeur :
- 0 = OK
- 1 = ERROR
**Verify:** `obdh.bus_b_status` (0x0310) — consigner la valeur
**Verify:** `obdh.active_bus` (0x030E) — consigner le bus actuellement actif :
- 0 = bus A
- 1 = bus B
**Action:** Déterminer le défaut :
- si le bus actif indique l'état ERROR, un basculement est nécessaire ;
- si les deux bus indiquent OK mais que les données HK manquent, le problème est peut-être ailleurs (panne au niveau
  d'un sous-système). Analyser chaque sous-système avant tout basculement de bus.
**GO/NO-GO:** Bus actif confirmé en état ERROR — engager le basculement.

### Étape 3 : Commander le basculement de bus
**Note:** Commander le basculement sur le bus redondant :
**TC:** `OBC_SELECT_BUS(bus=1)` (Service 8, Subtype 1, func_id 54) — Si le bus actuel est le bus A (0x030E = 0) :    — basculer sur le bus B
**TC:** `OBC_SELECT_BUS(bus=0)` (Service 8, Subtype 1, func_id 54) — Si le bus actuel est le bus B (0x030E = 1) :    — basculer sur le bus A
**Note:** ATTENTION — Cette commande interrompt brièvement toutes les communications sur le bus pendant
le basculement. Prévoir une interruption de 5-10 s des communications avec les sous-systèmes.
**Verify:** Attendre 15 s la fin du basculement.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander les données de servitude OBDH
**Verify:** `obdh.active_bus` (0x030E) indique le nouveau bus
**Verify:** `obdh.bus_a_status` (0x030F) et `obdh.bus_b_status` (0x0310) — consigner les nouveaux états
**GO/NO-GO:** Basculement de bus confirmé — engager la vérification.

### Étape 4 : Vérifier la reprise de toutes les données de servitude
**Note:** Demander les données HK de tous les sous-systèmes :
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — TCS
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — OBDH
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TTC
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Charge utile
**Verify:** Réponses de tous les SID reçues en moins de 15 s.
**Verify:** Les valeurs de télémesure sont cohérentes et plausibles (aucune valeur figée, aucun zéro).
**Verify:** `eps.bat_soc` (0x0101) — consigner la valeur (inchangée par rapport à l'avant-basculement)
**Verify:** `eps.bus_voltage` (0x0105) — consigner la valeur
**Verify:** `aocs.mode` (0x020F) — mode SCAO inchangé
**Verify:** `payload.mode` (0x0600) — mode de la charge utile inchangé
**Verify:** `obdh.cpu_load` (0x0302) — pas anormalement élevée
**Action:** Annoncer « ALL HK RESTORED » sur la boucle opérations.
**GO/NO-GO:** Données HK de tous les sous-systèmes reçues et nominales — passer à l'évaluation post-basculement.

### Étape 5 : Évaluation post-basculement
**Action:** Consigner l'événement de panne de bus :
- heure de détection de la perte des données HK ;
- bus défaillant (A ou B) ;
- durée de l'interruption des données HK ;
- sous-systèmes touchés ;
- nouveau bus actif.
**Action:** Vérifier que l'état du bus défaillant est enregistré pour l'évaluation par l'ingénierie.
**Action:** Poursuivre les opérations sur le nouveau bus. Ne PAS revenir sur le bus défaillant
sans accord et essais de l'équipe d'ingénierie.
**Note:** Le satellite fonctionne désormais sur un bus unique, sans redondance.
Toute panne du bus restant est critique pour la mission.

## Critères de vérification
- [ ] `obdh.active_bus` (0x030E) indique le nouveau bus (redondant)
- [ ] Les 6 rapports HK des sous-systèmes reçus
- [ ] Aucun changement de mode d'un sous-système pendant le basculement
- [ ] Toutes les valeurs de télémesure cohérentes et plausibles
- [ ] `obdh.cpu_load` (0x0302) nominale (< 80 %)
- [ ] Rapport d'anomalie déposé avec le détail de la panne de bus

## Contingence
- Si les données HK ne reprennent pas après le basculement : le bus redondant est peut-être lui aussi défaillant. Contrôler
  `obdh.bus_b_status` (ou `obdh.bus_a_status` pour le nouveau bus). Si les deux bus indiquent
  ERROR, il s'agit d'une panne critique. L'OBC peut encore communiquer par la liaison TTC. Faire remonter
  immédiatement au directeur de vol et l'équipe d'ingénierie.
- Si seuls certains sous-systèmes retrouvent leurs données HK : il peut s'agir d'une panne partielle du bus ou d'un
  défaut au niveau d'un sous-système. Pour les sous-systèmes toujours absents, rechercher si leur interface
  bus est tombée en panne indépendamment.
- Si l'OBC ne répond pas à la commande de sélection de bus : l'OBC est peut-être dans un état dégradé.
  Tenter `OBC_REBOOT` (func_id 52) en dernier recours. Si l'OBC ne répond toujours pas, appliquer
  CTG-011 (Basculement sur l'OBC redondant).
- Si le mode d'un sous-système a changé pendant le basculement (p. ex. passage du SCAO en mode survie) : la
  brève interruption du bus a pu déclencher un dépassement de délai au niveau du sous-système. Ramener le
  sous-système concerné à son mode d'avant le basculement, après avoir vérifié la stabilité du bus.
- Si le basculement de bus provoque des redémarrages continus de l'OBC : l'OBC détecte peut-être des erreurs sur
  les deux bus. Commander `OBC_BOOT_INHIBIT(inhibit=1)` (func_id 56) pour rester dans le chargeur d'amorçage
  et empêcher le redémarrage automatique. Poursuivre l'analyse depuis le chargeur d'amorçage.
