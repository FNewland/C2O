# CTG-011 : Basculement sur l'OBC redondant

**Catégorie :** Contingence
**Poste responsable :** FDIR / Systèmes
**Postes associés :** directeur de vol, tous les postes
**Difficulté :** Avancé

## Objectif
Basculer de l'ordinateur de bord principal en anomalie (OBC-A) vers l'unité redondante
(OBC-B) lorsque l'OBC-A présente des défauts persistants tels que des redémarrages répétés par chien de garde,
une corruption mémoire ou des erreurs logicielles irrécupérables. Cette procédure commande le basculement
d'unité, vérifie l'amorçage sur le chargeur d'amorçage, confirme le chargement correct de l'image du logiciel
applicatif et vérifie le retour de tous les sous-systèmes en fonctionnement nominal.

## Prérequis
- [ ] Anomalie de l'OBC-A confirmée — redémarrages répétés, erreurs mémoire ou absence de réponse
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Le directeur de vol autorise le basculement d'OBC (commande critique)
- [ ] OBC de secours (OBC-B) en STANDBY — `obdh.obc_b_status` (0x030D) = 1
- [ ] Tous les opérateurs de poste informés du basculement d'OBC imminent

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| obdh.mode | 0x0300 | Mode courant de l'OBC |
| obdh.active_obc | 0x030C | 0 (OBC-A) avant le basculement |
| obdh.obc_b_status | 0x030D | 1 (STANDBY) — unité redondante prête |
| obdh.sw_image | 0x0311 | 0 (chargeur d'amorçage) après le basculement, puis 1 (logiciel applicatif) |
| obdh.reboot_count | 0x030A | Consigner avant et après |
| obdh.last_reboot_cause | 0x0316 | 4 (basculement) attendu après la transition |
| obdh.sw_version | 0x030B | Version applicative correcte après l'amorçage |
| obdh.cpu_load | 0x0302 | < 80 % après stabilisation |
| obdh.temp | 0x0301 | Dans les limites |
| eps.bus_voltage | 0x0105 | > 27.0 V |
| aocs.mode | 0x020F | Vérifier après le basculement |
| payload.mode | 0x0600 | Vérifier après le basculement |
| ttc.link_status | 0x0501 | 2 (LOCKED) |

## Télécommandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| OBC_SWITCH_UNIT | 8 | 1 | 53 | Basculer sur l'OBC redondant (critique) |
| OBC_BOOT_APP | 8 | 1 | 55 | Amorcer le logiciel applicatif depuis le chargeur d'amorçage |
| OBC_SET_MODE | 8 | 1 | 50 | Régler le mode de l'OBC |

## Déroulement

### Étape 1 : Vérifier l'anomalie de l'OBC-A
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander la télémesure de servitude OBDH
**Verify:** `obdh.mode` (0x0300) — consigner le mode courant
**Verify:** `obdh.reboot_count` (0x030A) — consigner la valeur (élevée en cas de redémarrages par chien de garde)
**TC:** `GET_PARAM(param_id=0x0316)` (Service 20, Subtype 3) — `obdh.last_reboot_cause` (à la demande : aucun SID HK ne le transporte)
**Verify:** `obdh.last_reboot_cause` (0x0316) — consigner la cause :
- 0 = aucune, 1 = commandé, 2 = chien de garde, 3 = mémoire, 4 = basculement
**Verify:** `obdh.cpu_load` (0x0302) — consigner la valeur (peut être anormalement élevée)
**Verify:** `obdh.active_obc` (0x030C) = 0 (l'OBC-A est actif)
**Verify:** `obdh.obc_b_status` (0x030D) = 1 (l'OBC-B est en STANDBY et disponible)
**Action:** Confirmer que l'anomalie est persistante et irrécupérable sur l'OBC-A.
Si `obdh.reboot_count` > 4, la FDIR a peut-être déjà déclenché le mode survie.
**GO/NO-GO:** Anomalie de l'OBC-A confirmée, OBC-B en STANDBY — procéder au basculement.

### Étape 2 : Commander le basculement d'OBC
**Action:** Annoncer « COMMANDING OBC SWITCHOVER » sur la boucle opérations.
**Action:** Tous les opérateurs de poste se préparent à une perte temporaire de télémesure.
**TC:** `OBC_SWITCH_UNIT` (Service 8, Subtype 1, func_id 53) — Commander le basculement d'OBC
**Note:** COMMANDE CRITIQUE — elle va :
1. arrêter le fonctionnement de l'OBC-A ;
2. mettre sous tension le processeur de l'OBC-B ;
3. amorcer l'OBC-B sur son chargeur d'amorçage ;
4. laisser les unités des sous-systèmes conserver elles-mêmes l'état de chaque sous-système ;
5. entraîner 30 à 60 s sans télémesure pendant la transition.
**Verify:** Attendre 30 s pour l'amorçage initial.
**GO/NO-GO:** Commande envoyée — attendre la confirmation du chargeur d'amorçage.

### Étape 3 : Vérifier l'amorçage sur le chargeur d'amorçage
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander la télémesure de servitude OBDH
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Télémesure de servitude TT&C
**Note:** En l'absence de réponse sous 15 s, renouveler la demande. L'OBC-B est peut-être encore en début d'amorçage.
**Verify:** `obdh.active_obc` (0x030C) = 1 (l'OBC-B est désormais actif)
**Verify:** `obdh.sw_image` (0x0311) = 0 (chargeur d'amorçage — logiciel applicatif pas encore lancé)
**TC:** `GET_PARAM(param_id=0x0316)` (Service 20, Subtype 3) — `obdh.last_reboot_cause` (à la demande : aucun SID HK ne le transporte)
**Verify:** `obdh.last_reboot_cause` (0x0316) = 4 (basculement)
**TC:** `GET_PARAM(param_id=0x0301)` (Service 20, Subtype 3) — `obdh.temp` (à la demande : aucun SID HK ne le transporte)
**Verify:** `obdh.temp` (0x0301) — température de l'OBC-B dans les limites
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) — liaison TTC maintenue
**GO/NO-GO:** OBC-B en chargeur d'amorçage — procéder à l'amorçage applicatif.

### Étape 4 : Vérifier l'image logicielle et amorcer le logiciel applicatif
**Note:** Vérifier la validité de l'image du logiciel applicatif avant l'amorçage :
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — vérifier que `obdh.sw_version` (0x030B) est disponible dans le contexte du chargeur d'amorçage (peut indiquer la version du chargeur d'amorçage).
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55) — Commander l'amorçage applicatif
**Verify:** Attendre 30 s l'initialisation du logiciel applicatif.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander la télémesure de servitude OBDH
**Verify:** `obdh.sw_image` (0x0311) = 1 (logiciel applicatif en cours d'exécution)
**TC:** `GET_PARAM(param_id=0x030B)` (Service 20, Subtype 3) — `obdh.sw_version` (à la demande : aucun SID HK ne le transporte)
**Verify:** `obdh.sw_version` (0x030B) — version correcte du logiciel applicatif
**Verify:** `obdh.mode` (0x0300) — l'OBC devrait entrer en mode SAFE ou NOMINAL
**Verify:** `obdh.cpu_load` (0x0302) < 80 % (aucune charge anormale sur la nouvelle unité)
**GO/NO-GO:** Logiciel applicatif amorcé correctement sur l'OBC-B — procéder à la vérification des sous-systèmes.

### Étape 5 : Vérifier que tous les sous-systèmes sont nominaux
**Note:** Demander la HK de tous les sous-systèmes :
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — TCS
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TTC
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Charge utile
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Télémesure de servitude plateforme/OBDH
**Verify:** Toutes les réponses HK sont reçues en 15 s.
**Verify:** `eps.bus_voltage` (0x0105) > 27.0 V
**Verify:** `eps.bat_soc` (0x0101) — consigner la valeur
**Verify:** `aocs.mode` (0x020F) — consigner le mode. Le SCAO est peut-être revenu en COARSE_SUN
pendant le basculement. Si c'est le cas, rétablir le mode nominal après avoir confirmé la stabilité.
**Verify:** `payload.mode` (0x0600) — consigner le mode. La charge utile est peut-être passée en OFF pendant
le basculement. La remettre en STANDBY après avoir confirmé la stabilité de l'OBC.
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED)
**Note:** Si `obdh.mode` (0x0300) = 1 (SAFE), revenir en NOMINAL une fois tous les sous-systèmes confirmés :
**TC:** `OBC_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 50) — OBC en NOMINAL
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) en 10 s
**GO/NO-GO:** Tous les sous-systèmes nominaux sur l'OBC-B — basculement terminé.

### Étape 6 : Documentation après basculement
**Action:** Consigner l'événement de basculement d'OBC :
- heure de la commande de basculement ;
- symptômes de l'anomalie de l'OBC-A et nombre de redémarrages ;
- durée d'amorçage de l'OBC-B et version applicative ;
- état de tous les sous-systèmes après le basculement ;
- sous-systèmes dont le mode a dû être rétabli.
**Note:** Facultatif, et sur décision du directeur de vol — le compteur de redémarrages est le
seul enregistrement bord du nombre de fois où cela s'est produit.
**TC:** `OBC_CLEAR_REBOOT_CNT` (Service 8, Subtype 1, func_id 57) — remettre à zéro le compteur de redémarrages
**Action:** Informer le directeur de vol : « OBC switchover complete. Operating on OBC-B.
OBC-A is offline and requires engineering assessment before reuse. »
**Note:** Le satellite fonctionne désormais sur l'OBC redondant, sans plus aucune
redondance d'OBC. Toute défaillance de l'OBC-B est critique pour la mission.

## Critères de vérification
- [ ] `obdh.active_obc` (0x030C) = 1 (OBC-B actif)
- [ ] `obdh.sw_image` (0x0311) = 1 (logiciel applicatif en cours d'exécution)
- [ ] `obdh.sw_version` (0x030B) = version correcte
- [ ] `obdh.mode` (0x0300) = 0 (NOMINAL)
- [ ] Tous les rapports HK des sous-systèmes reçus et nominaux
- [ ] Aucun redémarrage anormal sur l'OBC-B
- [ ] Rapport d'anomalie établi pour la défaillance de l'OBC-A

## Cas de contingence
- Si l'OBC-B ne répond pas après le basculement (aucune HK en 60 s) : le basculement a peut-être
  échoué ou l'OBC-B présente un défaut. Attendre jusqu'à 120 s. Toujours sans réponse, l'OBC-B est peut-être
  dans une boucle d'amorçage. Essayer `OBC_BOOT_INHIBIT(inhibit=1)` (func_id 56) pour arrêter
  les cycles d'amorçage automatique, puis `OBC_BOOT_APP` manuellement.
- Si `obdh.sw_image` reste à 0 (bloqué en chargeur d'amorçage) : l'image applicative est peut-être corrompue.
  Suivre CTG-021 (reprise par le chargeur d'amorçage de l'OBC) pour le contrôle mémoire et la reprise.
- Si l'OBC-B s'amorce mais enchaîne aussitôt les redémarrages : commander
  `OBC_BOOT_INHIBIT(inhibit=1)` pour rester en chargeur d'amorçage. Poursuivre l'analyse depuis le chargeur d'amorçage. Il peut être nécessaire de charger
  une image applicative neuve via `MEM_LOAD`.
- Si les sous-systèmes ne reprennent pas l'émission de HK après l'amorçage de l'OBC-B : le bus CAN est peut-être touché aussi.
  Suivre CTG-017 (basculement sur panne de bus) pour vérifier le bus et en changer.
- S'il est impossible de basculer sur l'OBC-B (commande refusée ou `obc_b_status` = 0) :
  l'OBC-B n'est peut-être pas en STANDBY ou présente une panne matérielle. Tenter de rétablir l'OBC-A
  avec `OBC_REBOOT` (func_id 52). Si l'OBC-A ne peut pas non plus être rétabli, il s'agit d'une
  urgence critique pour la mission — faire remonter l'anomalie immédiatement.
