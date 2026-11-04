# CTG-010 : Reprise après chien de garde OBDH
**Sous-système :** OBDH
**Phase :** CONTINGENCY
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Analyser une réinitialisation inattendue de l'ordinateur de bord par chien de garde et en assurer la reprise ; elle se signale par
une incrémentation de `obdh.reboot_count` non commandée par le sol. Une réinitialisation par chien de garde peut
être causée par un blocage logiciel, une surcharge du processeur, un aléa logique (SEU) ou une corruption mémoire.
Cette procédure vérifie que l'OBC s'est correctement réinitialisé, confirme l'absence de perte de données et
évalue si la cause première est transitoire ou systémique.

## Prérequis
- [ ] La liaison TT&C est active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] La valeur précédente de `obdh.reboot_count` (0x030A) est connue depuis le dernier passage nominal
- [ ] La version du logiciel de vol et son niveau de correctifs sont documentés en console
- [ ] La capacité de vidage de la mémoire de masse est disponible si une récupération de données est nécessaire

## Déroulement

### Étape 1 — Confirmer la réinitialisation par chien de garde
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27)
**Verify:** `obdh.reboot_count` (0x030A) — comparer à la dernière valeur connue ; confirmer l'incrémentation
**Verify:** `obdh.mode` (0x0300) — consigner le mode courant (0=NOMINAL attendu après un redémarrage propre)
**Verify:** `obdh.cpu_load` (0x0302) — consigner la valeur (< 70 % attendu après l'amorçage)
**GO/NO-GO:** Le compteur de redémarrages a augmenté et l'OBC répond — procéder à l'évaluation

### Étape 1b — Amorcer l'OBC sur l'image applicative (s'il est en chargeur d'amorçage)
**Verify:** `obdh.sw_image` (0x0311) — si 0 (BOOTLOADER), la réinitialisation par chien de garde a laissé l'OBC dans le chargeur d'amorçage, qui n'accepte que les fonctions d'amorçage et de maintenance.
**BRANCH:** `obdh.sw_image == 0` -> GO `STEP-1B-BOOT` | NO-GO `STEP-2` (timeout 10 s)
**LABEL:** `STEP-1B-BOOT`
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55) — à envoyer uniquement si `obdh.sw_image` = 0
**Verify:** acceptation S1.1 + exécution S1.7 terminée en 15 s
**Verify:** `obdh.sw_image` (0x0311) = 1 (APPLICATION) en 15 s
**GO/NO-GO:** Image applicative en cours d'exécution avant l'envoi de toute TC HK_ENABLE / OBC_SET_MODE.

### Étape 2 — Vérifier l'état nominal de l'OBC après le redémarrage
**LABEL:** `STEP-2`
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27)
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) — si le mode vaut 1 (SAFE), l'OBC a détecté un problème pendant la réinitialisation
**Verify:** `obdh.cpu_load` (0x0302) < 70 % — une charge élevée peut révéler une boucle d'amorçage ou un processus bloqué
**Action:** Si l'OBC est en mode SAFE, décider s'il faut y rester ou tenter le retour en NOMINAL
**GO/NO-GO:** OBC en mode NOMINAL avec une charge processeur < 70 % — continuer. En mode SAFE, continuer avec prudence.

### Étape 3 — Demander toutes les trames de servitude
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — AOCS
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — OBDH
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — TCS
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TT&C
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Charge utile
**Verify:** Les six trames HK sont reçues en 30 s
**Verify:** Aucun sous-système n'est dans un mode inattendu ni ne signale de paramètre hors limites
**GO/NO-GO:** Tous les sous-systèmes nominaux — continuer. Toute anomalie déclenche la procédure CTG correspondante.

### Étape 4 — Vérifier l'intégrité des données et le stockage bord
**Note:** Cette étape resynchronise TOUJOURS l'horloge. Chaque redémarrage de l'OBC
remet l'horloge de bord à J2000 avec `obdh.time_ref` (0x0A13) = 0 (NONE), et le GPS ne
recale jamais de lui-même une horloge à l'état NONE : après une réinitialisation par chien
de garde, il n'existe donc pas de cas « petite dérive, on laisse ».
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — HK SCAO, pour `aocs.gps_fix` (0x0274)
**BRANCH:** `aocs.gps_fix >= 2` -> GO `STEP-4-GPS` | NO-GO `STEP-4-GROUND` (timeout 10 s)
**Note:** GO — le GPS a un point 3D : asservir l'horloge au GPS. NO-GO — pas de
point : régler l'horloge depuis le sol.

**LABEL:** `STEP-4-GROUND`
**TC:** `SET_TIME(cuc_seconds=T_corrected)` (Service 9, Subtype 1) — réglage de l'heure depuis le sol, comme dans LEOP-006 et CTG-021
**GO/NO-GO:** Réglage sol envoyé — poursuivre au contrôle de l'heure -> GO `STEP-4-CHECK` | NO-GO `STEP-4-CHECK`

**LABEL:** `STEP-4-GPS`
**TC:** `OBC_GPS_TIME_SYNC` (Service 8, Subtype 1, func_id 80) — synchronisation de l'heure sur le GPS

**LABEL:** `STEP-4-CHECK`
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — HK OBDH, pour `obdh.time_ref` (0x0A13)
**Verify:** `obdh.time_ref != 0` (0x0A13, timeout 15 s) — l'horloge a de nouveau une référence (1 GROUND ou 2 GPS)
**TC:** `REQUEST_TIME` (Service 9, Subtype 2) — rapport d'heure TM(9,2)
**Verify:** |T_obc − T_ground| < 1 s — la tolérance de NOM-008
**Verify:** État de la file des télécommandes stockées — confirmer qu'aucune commande n'a été perdue
**Verify:** État des partitions de la mémoire de masse — confirmer que les données scientifiques et les archives HK sont intactes
**GO/NO-GO:** Horloge référencée et à moins de 1 s de l'heure sol, intégrité des données confirmée — continuer.

### Étape 5 — Évaluer les indices de cause première
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Action:** Examiner la tendance de `obdh.cpu_load` (0x0302) — le processeur était-il à 100 % avant la réinitialisation ?
**Action:** Examiner les données EPS — une chute de la tension du bus a-t-elle pu provoquer une baisse de tension ?
**Verify:** `eps.bus_voltage` (0x0105) > 30.9 V (stable)
**Action:** Consulter les données d'environnement radiatif si la télémesure de servitude de la charge utile en fournit
**GO/NO-GO:** Cause première classée. Si elle semble transitoire (SEU, brève chute de tension) : la consigner. Si elle est systémique (charge processeur élevée répétée, erreur mémoire) : la faire remonter à l'équipe logiciel sol. Dans les deux cas, c'est le mode de l'OBC qui détermine la suite.
**BRANCH:** `obdh.mode == 1` -> GO `STEP-6` | NO-GO `STEP-END` (timeout 10 s)
**Note:** GO — l'OBC est en SAFE : passer à l'étape 6, qui rétablit NOMINAL. NO-GO — l'OBC
est déjà en NOMINAL : il n'y a rien à rétablir et la reprise est terminée.

### Étape 6 — Rétablir le mode nominal si l'OBC est en SAFE
**LABEL:** `STEP-6`
**TC:** `OBC_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 50)
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) en 10 s
**Verify:** `obdh.cpu_load` (0x0302) reste < 70 % après la transition
**Verify:** `aocs.mode` (0x020F) — confirmer que le changement de mode n'a pas perturbé le SCAO
**GO/NO-GO:** OBC en NOMINAL, tous les sous-systèmes stables — reprise terminée
**LABEL:** `STEP-END`

## Conduite à tenir hors nominal
- Si l'OBC redémarre de nouveau pendant cette procédure : commander `OBC_SET_MODE(mode=1)` pour passer en SAFE, interrompre la procédure et faire remonter à l'équipe logiciel sol pour une revue de code
- Si `obdh.reboot_count` (0x030A) augmente de plus de 3 en 1 heure : suspecter une boucle d'amorçage — commander `OBC_SET_MODE(mode=2)` pour passer en EMERGENCY et exécuter EMG-003
- Si la charge processeur reste > 90 % après le redémarrage : commander `OBC_SET_MODE(mode=1)` (SAFE) et vérifier que `obdh.cpu_load` (0x0302) baisse. Il n'existe à bord aucun paramètre de délestage des tâches ; le mode SAFE est la réduction de charge que propose l'OBC (environ 10 points de pourcentage dans le simulateur).
- Si le SCAO est revenu en DETUMBLE après la réinitialisation de l'OBC : exécuter CTG-002 pour rétablir le pointage une fois l'OBC confirmé stable

## Postconditions
- [ ] `obdh.mode` (0x0300) = 0 (NOMINAL)
- [ ] `obdh.cpu_load` (0x0302) < 70 %
- [ ] `obdh.reboot_count` (0x030A) documenté ; aucune autre incrémentation inattendue
- [ ] HK de tous les sous-systèmes vérifiée nominale
- [ ] Cause première classée transitoire ou systémique, avec action de suivi attribuée
