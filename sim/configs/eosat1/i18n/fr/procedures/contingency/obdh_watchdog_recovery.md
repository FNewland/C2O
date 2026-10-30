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
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27)
**Verify:** Le temps bord est cohérent avec la référence sol (dérive < 2 s acceptable après un redémarrage)
**Verify:** État de la file des télécommandes stockées — confirmer qu'aucune commande n'a été perdue
**Verify:** État des partitions de la mémoire de masse — confirmer que les données scientifiques et les archives HK sont intactes
**GO/NO-GO:** Intégrité des données confirmée — continuer. Si la dérive temporelle dépasse 5 s, effectuer la synchronisation temporelle avec `SET_TIME(cuc_seconds=<T_corrected>)` (Service 9, Subtype 1), comme le fait CTG-021, ou avec `OBC_GPS_TIME_SYNC` (func_id 80) lorsque le GPS a un point.

### Étape 5 — Évaluer les indices de cause première
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Action:** Examiner la tendance de `obdh.cpu_load` (0x0302) — le processeur était-il à 100 % avant la réinitialisation ?
**Action:** Examiner les données EPS — une chute de la tension du bus a-t-elle pu provoquer une baisse de tension ?
**Verify:** `eps.bus_voltage` (0x0105) > 27.0 V (stable)
**Action:** Consulter les données d'environnement radiatif si la télémesure de servitude de la charge utile en fournit
**GO/NO-GO:** Si la cause première semble transitoire (SEU, brève chute de tension) : consigner et poursuivre en nominal. Si elle est systémique (charge processeur élevée répétée, erreur mémoire) : l'étape 6 s'applique.

### Étape 6 — Rétablir le mode nominal si l'OBC est en SAFE
**TC:** `OBC_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 50)
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) en 10 s
**Verify:** `obdh.cpu_load` (0x0302) reste < 70 % après la transition
**Verify:** `aocs.mode` (0x020F) — confirmer que le changement de mode n'a pas perturbé le SCAO
**GO/NO-GO:** OBC en NOMINAL, tous les sous-systèmes stables — reprise terminée

## Conduite à tenir hors nominal
- Si l'OBC redémarre de nouveau pendant cette procédure : commander `OBC_SET_MODE(mode=1)` pour passer en SAFE, interrompre la procédure et faire remonter à l'équipe logiciel sol pour une revue de code
- Si `obdh.reboot_count` (0x030A) augmente de plus de 3 en 1 heure : suspecter une boucle d'amorçage — commander `OBC_SET_MODE(mode=2)` pour passer en EMERGENCY et exécuter EMG-003
- Si la charge processeur reste > 90 % après le redémarrage : commander `SET_PARAM(param_id=obdh.task_shed, value=1)` pour désactiver les tâches de fond non critiques
- Si le SCAO est revenu en DETUMBLE après la réinitialisation de l'OBC : exécuter CTG-002 pour rétablir le pointage une fois l'OBC confirmé stable

## Postconditions
- [ ] `obdh.mode` (0x0300) = 0 (NOMINAL)
- [ ] `obdh.cpu_load` (0x0302) < 70 %
- [ ] `obdh.reboot_count` (0x030A) documenté ; aucune autre incrémentation inattendue
- [ ] HK de tous les sous-systèmes vérifiée nominale
- [ ] Cause première classée transitoire ou systémique, avec action de suivi attribuée
