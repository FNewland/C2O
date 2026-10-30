# CTG-027 : Synchronisation temporelle GPS et reprise SCAO

**Catégorie :** Contingence
**Poste responsable :** OBDH
**Postes associés :** Directeur de vol, AOCS
**Difficulté :** Avancé

## Objectif
Rétablir la situation après des anomalies de synchronisation temporelle causées par la perte du point GPS 3D. La fonction
OBC_GPS_TIME_SYNC (func_id 80) exige un point GPS 3D valide pour synchroniser la source de temps bord. Si un
saut de temps dépasse 5 secondes, le SCAO passe automatiquement en mode SAFE_BOOT par
mesure de protection. Cette procédure vérifie l'état d'accrochage du GPS, exécute la commande de synchronisation
temporelle et, si nécessaire, remet en service le SCAO en lui faisant parcourir les transitions d'état requises.

## Prérequis
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Le récepteur GPS fonctionne depuis >= 5 minutes pour acquérir un point
- [ ] Directeur de vol informé de l'événement de synchronisation temporelle
- [ ] Le SCAO répond aux commandes

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| aocs.gps_fix | 0x0274 | 3 (point 3D + vitesse) — requis pour la synchronisation temporelle |
| aocs.gps_num_sats | 0x0276 | >= 5 satellites poursuivis |
| aocs.gps_pdop | 0x0275 | < 5.0 (dilution de précision en position) |
| obdh.obc_time | 0x0309 | Temps CUC bord courant (secondes depuis l'époque de référence) |
| aocs.mode | 0x020F | 0 = OFF, 1 = SAFE_BOOT, 2 = DETUMBLE, 3 = COARSE_SUN, 4 = NOMINAL, 5 = FINE_POINT, 6 = SLEW, 7 = DESAT, 8 = ECLIPSE, 9 = INERTIAL |
| aocs.att_error | 0x0217 | Erreur de pointage pour le mode courant |

**Note:** Les paramètres GPS appartiennent au sous-système AOCS (HK SID 2). Il n'existe ni espace de noms
`gps.*`, ni `obdh.time_src`, ni `aocs.state` dans
`telemetry/parameters.yaml` ; 0x0605/0x0606/0x0609/0x060A sont des paramètres de la charge utile,
0x0303 est `obdh.mmm_used` et 0x0218 est `aocs.rw1_temp`.

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| OBC_GPS_TIME_SYNC | 8 | 1 | 80 | Synchroniser le temps de l'OBC sur l'UTC GPS |
| AOCS_SET_MODE | 8 | 1 | 0 | Commander le SCAO dans le mode indiqué |

## Déroulement

### Étape 1 : Vérifier l'état du point GPS 3D
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander les données de servitude SCAO (les paramètres GPS relèvent du sous-système AOCS, SID 2 ; 0x0605-0x060A sont des paramètres de la charge utile)
**Verify:** `aocs.gps_fix` (0x0274) = 3 (point 3D + vitesse)
**Verify:** `aocs.gps_num_sats` (0x0276) >= 5 satellites poursuivis
**Verify:** `aocs.gps_pdop` (0x0275) < 5.0 (dilution de précision en position acceptable)
**Note:** Il n'existe aucun paramètre de télémesure UTC GPS dans `telemetry/parameters.yaml` ; l'horloge de bord se lit dans `obdh.obc_time` (0x0309) et la correction issue du GPS est appliquée par `OBC_GPS_TIME_SYNC` (S8 func 80).
**Action:** Si fix_type < 3 :
- attendre 1-2 minutes et redemander les données HK (le GPS est peut-être en cours de réaccrochage) ;
- si le point 3D n'est pas obtenu après 2 nouvelles tentatives, faire remonter à l'ingénierie (dysfonctionnement du récepteur GPS).
**GO/NO-GO:** Point GPS 3D confirmé, avec un temps UTC valide — l'étape 2 s'applique.

### Étape 2 : Consigner le mode SCAO courant
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander les données de servitude SCAO
**Verify:** Consigner la valeur courante de `aocs.mode` (0x020F). Codes selon `aocs/aocs_mode_codes.yaml` :
- 0 = OFF
- 1 = SAFE_BOOT
- 2 = DETUMBLE
- 3 = COARSE_SUN
- 4 = NOMINAL
- 5 = FINE_POINT
- 6 = SLEW
- 7 = DESAT
- 8 = ECLIPSE
- 9 = INERTIAL
**Note:** Si le SCAO est déjà en SAFE_BOOT, la valeur du mode est consignée et servira
à déterminer la séquence de remise en service à l'étape 5.
**Verify:** Consigner `aocs.att_error` (0x0217) comme référence pour l'évaluation après l'événement.
(0x0218 est `aocs.rw1_temp`, et non un mot d'état du SCAO — il n'existe aucun paramètre `aocs.state`.)
**Action:** Noter également la valeur courante de `obdh.obc_time` (0x0309) et la comparer à l'UTC horodaté au sol
pour estimer l'amplitude du saut de temps.
**GO/NO-GO:** Mode SCAO courant consigné — l'étape 3 s'applique.

### Étape 3 : Envoyer la commande de synchronisation temporelle GPS de l'OBC
**TC:** `OBC_GPS_TIME_SYNC` (Service 8, Subtype 1, func_id 80) — Émettre la commande de synchronisation temporelle GPS
**Note:** Cette commande lit le temps UTC du GPS et met à jour l'horloge temps réel (RTC) de bord. Si le saut de temps
dépasse 5 secondes, le SCAO déclenche automatiquement une transition de protection vers SAFE_BOOT.
**Verify:** Attendre 5 secondes l'exécution de la commande et la mise à jour de la télémesure.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Demander les données de servitude OBDH
**Verify:** `obdh.obc_time` (0x0309) saute à la valeur issue du GPS — c'est la preuve que la synchronisation a eu lieu. (Il n'existe aucun paramètre `obdh.time_src` ; 0x0303 est `obdh.mmm_used`, l'occupation de la mémoire de masse.)
**Verify:** Comparer `obdh.obc_time` (0x0309) au temps GPS attendu — il doit désormais correspondre à l'UTC GPS
**Verify:** Demander les données de servitude SCAO : `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Contrôler :** Si `aocs.mode` (0x020F) = 1 (SAFE_BOOT) :
- le saut de temps a dépassé le seuil de 5 secondes ;
- le SCAO est passé de façon autonome en mode de protection SAFE_BOOT ;
- l'étape 5 (remise en service du SCAO) s'applique.
**Contrôler :** Si `aocs.mode` (0x020F) n'a pas changé :
- le saut de temps était < 5 secondes, ou le SCAO n'a pas déclenché sa protection ;
- l'étape 4 (vérification seule) s'applique.
**GO/NO-GO:** Temps de l'OBC synchronisé sur le GPS et état du mode SCAO connu — l'étape 4 ou 5 s'applique selon le cas.
**BRANCH:** `aocs.mode == 1` -> GO `STEP-5` | NO-GO `STEP-4` (timeout 10 s)

### Étape 4 : Vérifier la continuité de fonctionnement du SCAO (s'il n'est pas en SAFE_BOOT)
**LABEL:** `STEP-4`
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander l'ensemble des données de servitude SCAO
**Verify:** `aocs.mode` (0x020F) reste à sa valeur d'avant la synchronisation (pas SAFE_BOOT)
**Verify:** `aocs.att_error` (0x0217) < seuil du mode courant :
- NOMINAL : < 5.0 degrés
- FINE_POINT : < 1.0 degré
**Verify:** Vitesses angulaires dans l'enveloppe nominale
**Action:** Surveiller le SCAO pendant 2-3 orbites pour confirmer la stabilité du fonctionnement après la synchronisation
**GO/NO-GO:** SCAO en fonctionnement nominal — reprise après synchronisation temporelle terminée. Fin de la procédure.
**BRANCH:** `aocs.mode != 1` -> GO `STEP-END` | NO-GO `STEP-5` (timeout 10 s)

### Étape 5 : Remise en service du SCAO (s'il est passé en SAFE_BOOT)
**LABEL:** `STEP-5`
**Objectif :** Faire passer le SCAO de SAFE_BOOT par les phases de mise en service requises pour rétablir
toute sa capacité de contrôle d'attitude. Suivre la séquence de modes SCAO de COM-005
(Transitions de modes SCAO) et la déclaration NOMINAL de COM-013.

**Phase 9 — mode DETUMBLE :**
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0) — DETUMBLE
**Justification :** DETUMBLE utilise les magnétocoupleurs et le senseur solaire pour stabiliser les vitesses angulaires du satellite.
Référence : COM-005 (Transitions de modes SCAO), entrée en DETUMBLE.
**Verify:** `aocs.mode` (0x020F) = 2 (DETUMBLE) en moins de 10 secondes
**Verify:** Les vitesses angulaires commencent à diminuer : `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) tendent vers zéro
**Surveiller :** Durée : ~3-5 orbites en DETUMBLE (les vitesses angulaires doivent décroître sous 1 °/s)
**Verify:** Erreur d'attitude : `aocs.att_error` (0x0217) < 30 degrés
**Attente :** Jusqu'à ce que les vitesses angulaires soient < 0.5 °/s et que l'attitude soit en pointage solaire grossier.
**GO/NO-GO:** Vitesses angulaires amorties et acquisition solaire stable — engager la phase 11.

**Phase 11 — transition vers NOMINAL et FINE_POINT :**
**Note:** Une fois DETUMBLE stable, enchaîner les transitions COARSE_SUN → NOMINAL → FINE_POINT :
**TC:** `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) — COARSE_SUN — attendre 30 secondes, vérifier `aocs.mode` = 3
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0) — NOMINAL — attendre 30 secondes, vérifier `aocs.mode` = 4
**TC:** `AOCS_SET_MODE(mode=5)` (Service 8, Subtype 1, func_id 0) — FINE_POINT — attendre 30 secondes, vérifier `aocs.mode` = 5
**Justification :** Chaque transition laisse au gain de la boucle d'attitude le temps de se rétablir au nouveau niveau.
Référence : COM-005 (Transitions de modes SCAO) et COM-013 (Clôture de la recette du SCAO et déclaration NOMINAL).
**Verify:** Après chaque transition, confirmer que `aocs.mode` est égal à la valeur commandée
**Verify:** `aocs.att_error` (0x0217) diminue à chaque phase :
- objectif COARSE_SUN : < 10 degrés
- objectif NOMINAL : < 5 degrés
- objectif FINE_POINT : < 1 degré
**Surveiller :** `aocs.att_error` (0x0217), jusqu'à convergence
**GO/NO-GO:** SCAO en FINE_POINT avec `aocs.att_error` < 1 degré — remise en service terminée.

### Étape 6 : Vérification après reprise
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Données de servitude plateforme/OBDH
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Données de servitude SCAO (le GPS en fait partie)
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Données de servitude TT&C
**Verify:** `obdh.obc_time` (0x0309) = UTC GPS courant à 1 s près
**Verify:** `aocs.mode` (0x020F) = 5 (FINE_POINT) ou valeur du mode d'avant l'événement
**Verify:** `aocs.att_error` (0x0217) < seuil propre au mode
**Verify:** `aocs.gps_fix` (0x0274) = 3 (point 3D maintenu)
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) — les communications sont restées stables
**Action:** Consigner l'événement avec :
- l'amplitude du saut de temps (temps OBC avant synchronisation comparé au temps GPS) ;
- le passage ou non du SCAO en SAFE_BOOT ;
- la durée de la phase DETUMBLE (le cas échéant) ;
- le temps nécessaire pour obtenir le verrouillage FINE_POINT après la reprise.
**GO/NO-GO:** Tous les systèmes nominaux, temps synchronisé, SCAO remis en service — reprise terminée.

## Critères de vérification
**LABEL:** `STEP-END`
- [ ] Point GPS 3D confirmé (`aocs.gps_fix` 0x0274 = 3)
- [ ] `obdh.obc_time` (0x0309) synchronisé sur l'UTC GPS à 1 s près
- [ ] Mode SCAO soit stable dans le mode d'avant l'événement, SOIT remis en service jusqu'en FINE_POINT
- [ ] `aocs.att_error` (0x0217) dans les limites acceptables pour le mode final
- [ ] Liaison TT&C restée active pendant toute la procédure
- [ ] Aucune anomalie secondaire déclenchée (réinitialisations par chien de garde, entrées en mode survie, etc.)

## Contingence
- Si le point GPS 3D ne peut être acquis après 5 minutes : le récepteur GPS a peut-être un accrochage intermittent.
  Demander une analyse d'ingénierie de la qualité du signal GPS et des conditions ionosphériques. Réessayer après
  1 heure si les conditions ont pu s'améliorer.
- Si la commande de synchronisation temporelle de l'OBC échoue (retour d'erreur) : vérifier que le récepteur GPS répond et que les données HK
  peuvent être décodées. En cas de suspicion de panne du récepteur, faire remonter à l'ingénierie.
- Si le SCAO reste en SAFE_BOOT après la phase 9 de l'étape 5 (vitesses angulaires non amorties) : le magnétocoupleur
  ou le senseur solaire est peut-être hors service. Demander à l'ingénierie d'évaluer l'état du matériel du SCAO.
  Envisager des procédures de contrôle d'attitude de contingence si une panne matérielle est confirmée.
- Si les transitions de mode du SCAO de l'étape 5 ne s'exécutent pas : le SCAO présente peut-être un défaut
  secondaire. Demander un diagnostic complet du SCAO avant toute nouvelle tentative de remise en service.
- Si un saut de temps s'est produit sans que le SCAO passe en SAFE_BOOT : vérifier que le seuil de 5 secondes
  n'a pas été redéfini. Confirmer que la version de la logique d'autonomie du SCAO correspond au comportement attendu
  du logiciel de vol.

## Références
- COM-005 : Transitions de modes SCAO ; COM-013 : Clôture de la recette du SCAO et déclaration NOMINAL
- Dictionnaire de données du récepteur GPS et des sous-systèmes OBDH et SCAO
- EMG-005 : Perte d'attitude (en cas d'échec de la remise en service du SCAO)
