# CTG-022 : Isolation d'une panne de bus CAN

**Catégorie :** Contingence
**Poste responsable :** FDIR / Systèmes
**Postes associés :** Directeur de vol, tous les postes
**Difficulté :** Avancé

## Objectif
Détecter, diagnostiquer et isoler une panne de bus CAN entraînant la perte de la télémesure
de servitude d'un ou plusieurs sous-systèmes. Lorsque le bus CAN actif tombe en panne, l'OBC ne peut
plus communiquer avec l'électronique des sous-systèmes raccordés à ce bus. Cette procédure
identifie le bus défaillant, commande le basculement sur le bus redondant, vérifie que
toutes les communications avec les sous-systèmes sont rétablies et évalue les conséquences opérationnelles
d'un fonctionnement sur un bus sans redondance.

## Prérequis
- [ ] Données de servitude absentes pour un ou plusieurs sous-systèmes depuis > 30 s
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] L'OBC répond aux commandes — `obdh.mode` (0x0300) peut être interrogé
- [ ] Directeur de vol informé, ayant autorisé l'analyse du bus
- [ ] Le logiciel applicatif de l'OBC est en cours d'exécution — `obdh.sw_image` (0x0311) = 1

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| obdh.bus_a_status | 0x030F | 0 (OK) ou 1 (ERROR) |
| obdh.bus_b_status | 0x0310 | 0 (OK) ou 1 (ERROR) |
| obdh.active_bus | 0x030E | 0 (bus A) ou 1 (bus B) |
| obdh.mode | 0x0300 | Mode OBC courant |
| obdh.cpu_load | 0x0302 | Surveiller toute hausse anormale |
| obdh.temp | 0x0301 | Température de l'OBC dans les limites |
| eps.bus_voltage | 0x0105 | > 27.0 V |
| eps.bat_soc | 0x0101 | Consigner la valeur courante |
| aocs.mode | 0x020F | Vérifier après le basculement |
| payload.mode | 0x0600 | Vérifier après le basculement |
| ttc.link_status | 0x0501 | 2 (LOCKED) |

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | -- | Demander un rapport HK ponctuel |
| OBC_SELECT_BUS | 8 | 1 | 54 | Sélectionner le bus CAN actif (0=A, 1=B) |
| OBC_REBOOT | 8 | 1 | 52 | Forcer le redémarrage de l'OBC (dernier recours) |

## Déroulement

### Étape 1 : Détecter et caractériser l'absence de données de servitude
**Note:** Demander un rapport HK à chaque sous-système pour déterminer lesquels
**Note:** sont touchés :
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — TCS
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — OBDH
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TTC
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Charge utile
**Verify:** Consigner les SID dont la réponse est reçue et ceux qui manquent au bout de 15 s.
**Action:** Classer le profil de panne :
- **L'OBDH répond mais les autres sous-systèmes manquent :** le bus CAN qui raccorde les
  sous-systèmes externes est probablement en panne. L'étape 2 s'applique.
- **Tous les sous-systèmes manquent, OBDH compris :** le problème vient peut-être de l'OBC ou du TTC,
  et non du bus. Analyser d'abord l'état de l'OBC.
- **Un seul sous-système manque :** il s'agit peut-être d'une panne au niveau du sous-système, et non du bus.
  Analyser ce sous-système avant tout basculement de bus.
- **Plusieurs sous-systèmes (mais pas tous) manquent :** il peut s'agir d'une panne partielle du bus.
  L'étape 2 (diagnostic du bus) s'applique.
**GO/NO-GO:** Absence de données HK confirmée pour plusieurs sous-systèmes — engager le diagnostic du bus.

### Étape 2 : Diagnostiquer l'état des bus
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander les données de servitude OBDH
**Verify:** `obdh.active_bus` (0x030E) — consigner le bus actuellement actif :
- 0 = bus A
- 1 = bus B
**Verify:** `obdh.bus_a_status` (0x030F) — consigner l'état :
- 0 = OK
- 1 = ERROR
**Verify:** `obdh.bus_b_status` (0x0310) — consigner l'état
**Verify:** `obdh.mode` (0x0300) — confirmer que l'OBC n'est pas passé en mode SAFE à cause de l'erreur de bus
**Verify:** `obdh.cpu_load` (0x0302) — une charge élevée peut indiquer des relances sur dépassement de délai du bus
**Verify:** `obdh.temp` (0x0301) — dans les limites

**Action:** Évaluer le défaut :
- **Le bus actif indique ERROR :** panne de bus confirmée. L'étape 3 (basculement) s'applique.
- **Le bus actif indique OK mais les données HK manquent :** le registre d'état du bus n'est peut-être pas encore
  à jour, ou le problème se situe au niveau du sous-système. Attendre 15 s et interroger à nouveau.
  Si l'état reste OK mais que les données HK manquent toujours, l'étape 3 s'applique, avec prudence.
- **Les deux bus indiquent ERROR :** situation critique. Les deux bus sont peut-être dégradés.
  L'étape 3 s'applique, mais s'attendre au mieux à un rétablissement partiel.

**Action:** Consigner l'état avant basculement :
- bus actif et son état ;
- état du bus en attente ;
- mode et charge CPU de l'OBC ;
- tension EPS (si disponible dans la dernière trame connue).
**GO/NO-GO:** Bus actif confirmé en état ERROR (ou perte de données HK confirmée, le bus
étant la cause probable) — engager le basculement.

### Étape 3 : Commander le basculement de bus
**Action:** Prévenir tous les postes de la console : « CAN bus switchover imminent. Expect
brief HK gap of 5-10 seconds. »
**Note:** Commander le basculement sur le bus redondant :
**BRANCH:** `obdh.active_bus == 0` -> GO `STEP-3A` | NO-GO `STEP-3B` (timeout 10 s)
**LABEL:** `STEP-3A`
**Note:** - Si le bus actuel est le bus A (0x030E = 0) :
**TC:** `OBC_SELECT_BUS(bus=1)` (Service 8, Subtype 1, func_id 54) — basculer sur le bus B
**BRANCH:** `obdh.active_bus == 1` -> GO `STEP-3V` | NO-GO `STEP-END` (timeout 15 s)
**LABEL:** `STEP-3B`
**Note:** - Si le bus actuel est le bus B (0x030E = 1) :
**TC:** `OBC_SELECT_BUS(bus=0)` (Service 8, Subtype 1, func_id 54) — basculer sur le bus A
**LABEL:** `STEP-3V`
**ATTENTION :** Cette commande interrompt brièvement toutes les communications sur le bus CAN pendant
le basculement. Les données HK des sous-systèmes seront indisponibles pendant 5-10 secondes. C'est normal.
**Verify:** Attendre 15 s la fin du basculement.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander les données de servitude OBDH
**Verify:** `obdh.active_bus` (0x030E) indique le nouveau bus
**Verify:** `obdh.bus_a_status` (0x030F) — consigner l'état mis à jour
**Verify:** `obdh.bus_b_status` (0x0310) — consigner l'état mis à jour
**GO/NO-GO:** Basculement de bus confirmé — engager la vérification.

### Étape 4 : Vérifier la reprise de toutes les données de servitude sur le nouveau bus
**Note:** Demander les données HK de tous les sous-systèmes :
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — TCS
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — OBDH
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TTC
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Charge utile
**Verify:** Réponses des six SID reçues en moins de 15 s.
**Verify:** Les valeurs de télémesure sont cohérentes et plausibles :
- aucune valeur figée ni aucun zéro inattendu ;
- valeurs cohérentes avec les mesures d'avant la panne.
**Verify:** `eps.bus_voltage` (0x0105) > 27.0 V — alimentation stable
**Verify:** `eps.bat_soc` (0x0101) — inchangé par rapport à l'avant-basculement
**Verify:** `aocs.mode` (0x020F) — mode SCAO inchangé par rapport à l'état d'avant la panne
**Verify:** `payload.mode` (0x0600) — mode de la charge utile inchangé
**Verify:** `obdh.cpu_load` (0x0302) — pas anormalement élevée (< 80 %)
**Action:** Annoncer sur la boucle opérations : « ALL HK RESTORED on [Bus A/B]. Bus switchover
successful. »
**GO/NO-GO:** Données HK de tous les sous-systèmes reçues et nominales — engager l'évaluation post-basculement.

### Étape 5 : Évaluation et documentation post-basculement
**Action:** Consigner l'événement de panne de bus avec les informations suivantes :
- heure de la première détection de la perte des données HK ;
- bus défaillant (A ou B) ;
- durée de l'interruption des données HK (de la détection au rétablissement) ;
- sous-systèmes touchés ;
- identifiant du nouveau bus actif ;
- tout changement de mode d'un sous-système survenu pendant l'interruption.
**Action:** Vérifier que l'état d'erreur du bus défaillant est enregistré pour l'évaluation par l'ingénierie.
**Action:** Évaluer l'impact opérationnel :
- **Bus sans redondance :** le satellite fonctionne désormais sur un seul bus, sans redondance
  CAN. Toute panne du bus restant serait critique pour la mission.
- **Conséquences pour la FDIR :** vérifier si des règles FDIR bord font référence à l'état des bus.
  Confirmer que la FDIR ne tentera pas de revenir sur le bus défaillant.
**Action:** Informer le directeur de vol de la redondance réduite.
**Action:** Poursuivre les opérations sur le nouveau bus. Le retour sur le bus défaillant est INTERDIT
sans analyse et accord de l'équipe d'ingénierie.
**GO/NO-GO:** Évaluation terminée, incident documenté — procédure terminée.

## Critères de vérification
**LABEL:** `STEP-END`
- [ ] `obdh.active_bus` (0x030E) indique le nouveau bus (redondant)
- [ ] État du bus défaillant à ERROR : `obdh.bus_a_status` (0x030F) ou `obdh.bus_b_status` (0x0310) = 1
- [ ] Les 6 rapports HK des sous-systèmes reçus sur le nouveau bus
- [ ] Aucun changement de mode d'un sous-système pendant le basculement
- [ ] Toutes les valeurs de télémesure cohérentes avec les valeurs d'avant la panne
- [ ] `obdh.cpu_load` (0x0302) < 80 %
- [ ] `eps.bus_voltage` (0x0105) > 27.0 V
- [ ] Rapport d'anomalie déposé avec le détail de la panne de bus
- [ ] Directeur de vol informé de la redondance réduite des bus

## Contingence
- Si les données HK ne reprennent pas après le basculement : le bus redondant est peut-être lui aussi défaillant.
  Contrôler le registre d'état du nouveau bus actif. Si les deux bus indiquent ERROR, il s'agit
  d'une double panne de bus critique. L'OBC peut encore communiquer par la liaison TTC, mais ne peut pas
  joindre les sous-systèmes. Faire remonter immédiatement au directeur de vol et l'équipe d'ingénierie.
- Si seuls certains sous-systèmes retrouvent leurs données HK après le basculement : il peut exister une panne partielle du bus ou
  une panne de l'interface bus d'un sous-système. Pour les sous-systèmes toujours
  absents, le problème se situe au niveau du sous-système, et non du bus. Les analyser
  un par un.
- Si l'OBC ne répond pas à la commande de sélection de bus : l'OBC est peut-être dans un état
  dégradé. Tenter `OBC_REBOOT` (func_id 52) en dernier recours. Si l'OBC ne
  répond toujours pas, appliquer CTG-011 (Basculement sur l'OBC redondant).
- Si le mode d'un sous-système a changé pendant le basculement (p. ex. passage du SCAO en SAFE ou en
  DETUMBLE) : la brève interruption du bus a pu déclencher un dépassement de délai du sous-système.
  Après avoir confirmé la stabilité du bus, ramener le sous-système concerné à son
  mode d'avant le basculement au moyen de la commande de mode appropriée.
- Si le basculement de bus provoque des redémarrages continus de l'OBC : l'OBC détecte peut-être des
  erreurs sur les deux bus. Commander `OBC_BOOT_INHIBIT(inhibit=1)` (func_id 56) pour
  rester dans le chargeur d'amorçage et arrêter le cycle de redémarrage. Poursuivre l'analyse depuis le chargeur d'amorçage.
- Si le bus défaillant se rétablit de lui-même (panne intermittente) : NE PAS revenir
  dessus sans analyse de l'ingénierie. Les pannes de bus intermittentes révèlent un
  état matériel marginal, susceptible de devenir une panne définitive à tout moment.
