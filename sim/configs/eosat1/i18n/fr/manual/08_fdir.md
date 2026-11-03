# Détection, isolation et reprise des défaillances (FDIR) d'EOSAT-1 {#eosat-1-fault-detection-isolation-and-recovery-fdir}

**Référence du document :** EOSAT1-UM-FDIR-009
**Édition :** 2.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Vue d'ensemble {#1-overview}

Le système de détection, isolation et reprise des défaillances (FDIR) d'EOSAT-1 assure une protection
bord autonome contre les anomalies susceptibles de mettre en danger le satellite ou sa mission.
La FDIR fonctionne de manière hiérarchique, avec des niveaux d'autonomie et de gravité croissants,
depuis les réactions locales au niveau d'un sous-système jusqu'aux passages en mode survie de l'ensemble du satellite.

La mise en œuvre de la FDIR utilise le service PUS 12 (surveillance bord) pour le contrôle des limites
des paramètres et le service PUS 19 (événement-action) pour le déclenchement automatique des réactions. Les deux
services sont évalués à chaque cycle de traitement bord, ce qui assure une couverture
de surveillance continue.

## 2. Hiérarchie de la FDIR {#2-fdir-hierarchy}

### 2.1 Niveaux d'autonomie {#21-autonomy-levels}

| Niveau | Périmètre       | Temps de réaction | Autorité             | Exemple                     |
|-------|-----------------|---------------|------------------------|-----------------------------|
| 0     | Équipement      | < 1 s         | Matériel               | Disjonction sur surintensité du PCDU |
| 1     | Sous-système    | 1–10 s        | Logiciel du sous-système | Régulation par thermostat d'un réchauffeur |
| 2     | Système         | 10–60 s       | Application FDIR de l'OBC | Transition de mode, délestage |
| 3     | Sol             | Minutes–heures | Équipe de contrôle du vol | Procédures de reprise manuelles |

### 2.2 Principes de conception {#22-design-philosophy}

- **Sécurité intrinsèque** : toute anomalie irrécupérable entraîne une transition vers un état à bilan de puissance positif,
  sûr sur le plan thermique et commandable (mode survie).
- **Intervention minimale** : la FDIR n'agit que pour préserver la sécurité du satellite. Le rétablissement
  des opérations nominales est une activité commandée depuis le sol (niveau 3).
- **Tolérance à une panne** : la conception de la FDIR tolère une défaillance unique sans perte de la
  sécurité du satellite.

## 3. Définition du mode survie {#3-safe-mode-definition}

Lorsqu'une règle FDIR critique déclenche un passage en mode survie, l'OBC exécute de manière autonome
la séquence suivante :

| Étape | Action                                         | Sous-système |
|------|-------------------------------------------------|-----------|
| 1    | Régler le mode de l'OBC sur SAFE                | OBDH      |
| 2    | Commander l'AOCS en mode COARSE_SUN (3)         | AOCS      |
| 3    | Mettre la charge utile hors tension             | PLD       |
| 4    | Délester les charges non essentielles           | EPS       |
| 5    | Activer les réchauffeurs essentiels (batterie, OBC) | TCS   |
| 6    | Réduire la cadence TM à 0,1 Hz                  | OBDH      |
| 7    | Placer la TTC en mode priorité à la réception   | TTC       |
| 8    | Générer le paquet d'événement de mode survie    | OBDH      |

Le mode survie est conçu pour avoir un bilan de puissance positif dans toutes les conditions d'éclairement, ce qui garantit
que le satellite peut se maintenir indéfiniment jusqu'à l'intervention du sol.

## 4. Règles et déclencheurs FDIR {#4-fdir-rules-and-triggers}

### 4.1 Règles EPS {#41-eps-rules}

| ID de règle | Condition                  | Détection       | Réaction                    |
|---------|--------------------------------|----------------|-----------------------------|
| EPS-01  | bat_soc < 15 %                  | 0x0101 < 15    | Passage en mode survie      |
| EPS-02  | bus_voltage < 26.5 V           | 0x0105 < 26.5  | Passage en mode survie      |
| EPS-03  | bat_temp > 45 C                | 0x0102 > 45    | Inhiber la charge de la batterie |
| EPS-04  | bat_temp < 0 C                 | 0x0102 < 0     | Thermostat du réchauffeur de batterie (voir TCS-01) |
| EPS-05  | Rendement de chaîne < 70 % en éclairement, 30 s | 0x014C / 0x014D (valide tant que le bit de 0x014E est positionné) | Ligne charge utile hors tension (S19 ea 1004 / 1005) |
| EPS-06  | bus_voltage > 29.5 V           | 0x0105 > 29.5  | Dériver l'excédent de puissance (shunt) |

**EPS-05 n'est évaluée qu'en éclairement.** Jusqu'en novembre 2026, les règles
des panneaux solaires (S19 ea 1004/1005) surveillaient les courants bruts des
chaînes 0x0103/0x0104 face à un plancher de 0.1 A. Chaque entrée en éclipse
franchit ce plancher : les deux règles se déclenchaient donc à chaque éclipse.
Les surveillances S12 portent désormais sur le **rendement** de chaque chaîne :
le courant mesuré en pourcentage de ce que fournirait une chaîne saine dans la
géométrie solaire du moment (0x014C `eps.sa_a_yield_pct`, 0x014D
`eps.sa_b_yield_pct`). Elles portent aussi une condition de validité PUS-C :
une surveillance n'est contrôlée que tant que le bit de sa chaîne est positionné dans
0x014E `eps.sa_string_lit` (bit 0 = A, bit 1 = B). Ce bit est positionné lorsque le
satellite est éclairé, que la chaîne est activée et qu'une chaîne saine
fournirait au moins 0.2 A. En éclipse, en pénombre profonde ou lorsque la
chaîne est dos au Soleil, la surveillance est *non contrôlée*, et non en
violation. Un nombre de répétitions de 30 (30 s à 1 Hz) absorbe les
manœuvres d'attitude et la frontière d'ombre. Une perte réelle en éclairement (chaîne défaillante ou panneau
endommagé) déclenche toujours la règle en 30 s environ et met la ligne de
la charge utile hors tension. Tant que la panne persiste, la surveillance la
signale de nouveau après chaque sortie d'éclipse ; répéter l'action est sans
conséquence. Diagnostic : CTG-009.

### 4.2 Règles AOCS {#42-aocs-rules}

| ID de règle | Condition                  | Détection       | Réaction                    |
|---------|--------------------------------|----------------|-----------------------------|
| AOCS-01 | att_error > 2 deg (persistante) | 0x0217 > 2    | Transition vers COARSE_SUN  |
| AOCS-02 | Vitesse angulaire > 2 deg/s    | 0x0204–0206    | Transition vers DETUMBLE    |
| AOCS-03 | Vitesse de roue > 5500 tr/min  | 0x0207–020A    | Lancer une désaturation     |
| AOCS-04 | Température de roue > 70 C     | 0x0218–021B    | Réduire la demande de couple des roues |
| AOCS-05 | Défaillance du senseur stellaire | Indicateur de validité | Basculer sur la propagation gyrométrique |

### 4.3 Règles OBDH {#43-obdh-rules}

| ID de règle | Condition                  | Détection       | Réaction                    |
|---------|--------------------------------|----------------|-----------------------------|
| OBDH-01 | Expiration du chien de garde   | Chien de garde matériel | Réinitialisation de l'OBC |
| OBDH-02 | 3 réinitialisations consécutives par le chien de garde | reboot_count | Maintien dans le chargeur d'amorçage (`sw_image` = 0) |
| OBDH-03 | cpu_load > 98 %                 | 0x0302 > 98    | Ajustement des priorités des tâches |
| OBDH-04 | mmm_used > 95 %                 | 0x0303 > 95    | Inhiber l'acquisition de la charge utile |

### 4.4 Règles TCS {#44-tcs-rules}

| ID de règle | Condition                  | Détection       | Réaction                    |
|---------|--------------------------------|----------------|-----------------------------|
| TCS-01  | bat_temp < 1 C                 | 0x0407 < 1     | Réchauffeur de batterie rendu au thermostat (`HEATER_AUTO_MODE`) |
| TCS-02  | obc_temp > 70 C (rouge haut)   | 0x0406 > 70    | OBC en SAFE (S19 ea 3003, limite haute seulement) |
| TCS-03  | obc_temp < -20 C (rouge bas)   | 0x0406 < -20   | Aucune action à bord : thermostat du réchauffeur de l'OBC ; rapport S12 au sol |
| TCS-04  | fpa_temp au-dessus de +17.5 C  | Alarme S12 sur 0x0408 | Mettre la charge utile hors tension (S19 ea_id 3001) |
| TCS-05  | bat_temp > 42 C                | 0x0407 > 42    | Réchauffeur de batterie arrêté ; rendu au thermostat à ≤ 42 C |

TCS-04 se déclenche sur l'**alarme S12** de 0x0408, dont la bande est dérivée de
`subsystems/tcs.yaml: fpa_envelope` (DECISIONS §3). Le seuil documenté
était auparavant un simple `> 12 C`, qui se situe *à l'intérieur* de l'état de repos normal non refroidi
(+11,5 °C mesurés, crête à +12,4 °C) : la règle aurait mis hors tension une
charge utile déjà correctement éteinte, à chaque orbite.

**Les règles de température n'agissent que d'un côté.** Une surveillance S12
de température a une limite basse et une limite haute. Jusqu'en novembre 2026,
toute règle S19 rattachée à une telle surveillance se déclenchait sur l'*un ou
l'autre* franchissement. Ainsi, ea 3003 (surchauffe de l'OBC → OBC en SAFE)
mettait l'OBC en SAFE à chaque refroidissement prolongé, et ea 3002 (surchauffe
de la batterie → émetteur arrêté) coupait l'émetteur lorsque la batterie était
froide. Les règles de surchauffe 3001, 3002, 3003, 4002 et 6002 ne sont
désormais armées que sur la limite haute (`limit: high` dans
`s19_rules.yaml`, section 7.1). Le franchissement bas reste signalé au sol par
TM(12,9) et par un événement S5 (0x9406 pour l'OBC).

**Sous-température de l'OBC (TCS-03).** La réaction à bord à un OBC froid est
le thermostat du réchauffeur de l'OBC, actif tant que la ligne EPS 6
(`htr_obc`) est alimentée. Le mode survie n'est pas utilisé : le SAFE ne
réchauffe pas l'OBC, et le délestage qui l'accompagne retire de la chaleur
interne. Le rapport S12 de limite basse et son événement S5 informent le sol.
Le sol vérifie alors la ligne 6 et l'état du réchauffeur (manuel 03) et
décide. Aucun changement de mode autonome n'a lieu pour un OBC froid.

**Réchauffeur de batterie (TCS-01, TCS-05).** Le réchauffeur de batterie est
piloté par thermostat. La FDIR n'intervient que lorsque le thermostat ne tient
manifestement pas la bande, et elle ne laisse jamais le réchauffeur en mode
manuel derrière elle :

- Sous 1 C (TCS-01), la FDIR rend le réchauffeur au thermostat
  (`HEATER_AUTO_MODE`). À cette température, le thermostat l'allume aussitôt.
- Au-dessus de 42 C (TCS-05), la FDIR force l'arrêt du réchauffeur. Elle le
  rend au thermostat dès que la batterie est de nouveau à 42 C ou moins
  (`on_clear` dans `subsystems/fdir.yaml`).

Jusqu'en novembre 2026, la réaction au froid était une mise en marche manuelle
que rien n'annulait jamais. Après une excursion froide, la batterie restait
alors à +15 à +18 C, au-dessus du point d'arrêt de
+10 C. La FDIR ne réalimente pas la ligne de réchauffeur 5 (`htr_bat`) si le
délestage ou le sol l'a coupée. Cette décision reste au sol.

### 4.5 Règles TTC {#45-ttc-rules}

| ID de règle | Condition                  | Détection       | Réaction                    |
|---------|--------------------------------|----------------|-----------------------------|
| TTC-01  | Aucune télécommande valide depuis > 24 heures | 0x053D ≥ 86400 s (puis à chaque nouvelle tranche de 86400 s) → événement 0x0514 | Basculer sur l'autre transpondeur (S19 ea 4003) |
| TTC-02  | Température du transpondeur hors plage | 0x0507  | Changer de transpondeur     |
| TTC-03  | Décrochage de la liaison montante (verrouillage perdu puis retrouvé en moins de 60 s) | événement 0x0513 | Puissance TX HIGH, 5 W (S19 ea 4001) |

**Ce que le satellite voit et ne voit pas.** La marge de liaison (0x0503), le TEB (0x050C),
l'Eb/N0 (0x0519), la CAG (0x051A) et le RSSI descendant (0x0502) sont mesurés par le
récepteur **sol** (`visibility: ground_derived`). Le satellite ne peut pas les mesurer ;
aucune règle de bord ne peut donc s'en servir. Jusqu'en novembre 2026, les règles 4001 et
4003 se déclenchaient sur la marge de liaison et le TEB, et ne pouvaient donc jamais se
déclencher. Les deux règles d'autonomie TTC se déclenchent désormais sur ce que le
récepteur et l'OBC de bord observent réellement :

- **TTC-01 : minuterie de perte de commande (ea 4003).** 0x053D `ttc.time_since_last_tc`
  compte les secondes écoulées depuis la dernière télécommande acceptée par l'OBC ; chaque
  acceptation S1.1 la remet à zéro. Lorsqu'elle atteint `cmd_loss_switch_timeout_s` dans
  `subsystems/ttc.yaml` (86400 s), l'événement 0x0514 CMD_LOSS_TIMEOUT est émis et la
  règle S19 ea 4003 envoie `TTC_SWITCH_OTHER` (S8 func 99), qui sélectionne le
  transpondeur qui n'est pas sélectionné. Si la chaîne de réception sélectionnée est
  devenue sourde, l'autre peut encore entendre le sol. La minuterie se réarme : toujours
  sans télécommande acceptée, elle se déclenche de nouveau à 48 h, 72 h, ..., en basculant
  à chaque fois ; la règle fonctionne donc dans les deux sens (un transpondeur REDONDANT
  en panne est quitté au profit du principal ; jusqu'au 2026-11-02 l'action était
  `TTC_SWITCH_REDUNDANT`, qui ne le permettait pas). Le basculement se fait à l'aveugle :
  l'équipement de secours est hors tension (redondance froide), et l'OBC ne peut donc pas
  le vérifier avant de le sélectionner. Si les deux équipements sont en panne, la
  minuterie continue de basculer toutes les 24 h, sans conséquence, et retrouve en moins
  de 24 h un équipement qui se rétablit. Le basculement autonome n'est pas une
  télécommande acceptée : il ne remet pas la minuterie à zéro. La valeur de 24 h est
  longue à dessein : un week-end calme ne doit pas faire changer de transpondeur. Une fois
  la liaison rétablie, toute télécommande acceptée empêche le basculement suivant. Le sol peut toujours commander le basculement (`TTC_SWITCH_REDUNDANT`, voir
  `05_ttc.md` §6.1). L'événement 0x0511 UPLINK_TIMEOUT est un autre signal (pas de
  verrouillage de la liaison montante pendant 300 s) et il est émis après chaque LOS.
- **TTC-03 : décrochage de la liaison montante (ea 4001).** À bord, une LOS normale et
  un évanouissement du signal sont identiques au moment où le verrouillage de la porteuse
  est perdu. Ils ne diffèrent que par la suite : après un évanouissement, le verrouillage
  revient en quelques secondes ; après une LOS, il disparaît pendant des dizaines de
  minutes. L'événement 0x0513 UPLINK_LOCK_DROPOUT est donc émis lorsque le verrouillage est
  *retrouvé* moins de 60 s après avoir été perdu. La règle S19 ea 4001 commande alors
  `TTC_SET_TX_POWER` niveau 2 (HIGH, 5 W), ce qui donne à la station sol environ 4 dB de
  liaison descendante supplémentaires tant que le passage reste marginal. Cette
  augmentation est **maintenue** : une fois le passage compris, le sol rétablit NOMINAL
  (`TTC_SET_TX_POWER` niveau 1). Laisser le PA à 5 W coûte environ 17 W continus à chaque
  passage et échauffe le PA vers la limite TTC-02/ea 4002.

Le côté sol de la même histoire figure sur la page radio et sur la page TT&C : le pont RF
calcule le TEB et la CAG au récepteur sol et les place en alarme avec des limites
étiquetées **sol** (voir `05_ttc.md`).

### 4.6 Règles charge utile {#46-payload-rules}

| ID de règle | Condition                  | Détection       | Réaction                    |
|---------|--------------------------------|----------------|-----------------------------|
| PLD-01  | checksum_errors > seuil        | 0x0609         | Alerte, inhiber la prise de vue |
| PLD-02  | Prise de vue avec att_error > 1 deg | 0x0217    | Interrompre la prise de vue, passer en STANDBY |

## 5. Procédures de reprise {#5-recovery-procedures}

### 5.1 Reprise après mode survie (niveau 3 — sol) {#51-safe-mode-recovery-level-3--ground}

1. Établir le contact sol et vérifier la télémesure du satellite.
2. Examiner le journal d'événements et l'historique des déclenchements FDIR.
3. Identifier et traiter la cause première de l'anomalie.
4. Vérifier que tous les paramètres des sous-systèmes sont dans les limites nominales.
5. Commander `OBC_SET_MODE` (mode=0) pour revenir en NOMINAL.
6. Commander `AOCS_SET_MODE` (mode=4) pour revenir en NOMINAL (nadir).
7. Réactiver la charge utile et reprendre les opérations nominales.

### 5.2 Reprise du transpondeur {#52-transponder-recovery}

1. Si le transpondeur principal ne répond pas, envoyer `TTC_SWITCH_REDUNDANT`.
2. Attendre 30 secondes la mise en température du transpondeur.
3. Vérifier l'acquisition de la liaison par `link_status` (0x0501).
4. Si le redondant est également défaillant, attendre la tentative de contact suivante (à l'initiative du sol).

### 5.3 Reprise de l'AOCS depuis DETUMBLE {#53-aocs-recovery-from-detumble}

1. Surveiller la décroissance des vitesses angulaires (0x0204–0x0206) vers zéro.
2. Dès que les vitesses restent < 0.5 deg/s pendant 30 s, l'AOCS passe de manière autonome en COARSE_SUN.
3. Le sol commande `AOCS_SET_MODE` (mode=4) pour passer en NOMINAL (nadir) le moment venu.

## 6. Service PUS 12 — surveillance bord {#6-pus-service-12--onboard-monitoring}

Le service 12 met en œuvre le cadre de surveillance des paramètres utilisé par le système FDIR. Toutes
les définitions de surveillance sont évaluées à chaque cycle de traitement bord
(1 Hz en nominal), ce qui assure une couverture continue du contrôle de limites.

### 6.1 Application de la surveillance {#61-monitoring-enforcement}

Chaque définition de surveillance précise :

| Champ               | Description                                        |
|---------------------|----------------------------------------------------|
| ID de paramètre     | Le paramètre de télémesure à surveiller            |
| Type de contrôle    | Contrôle de limites, valeur attendue ou contrôle de variation |
| Limite basse        | Seuil inférieur du contrôle de limites             |
| Limite haute        | Seuil supérieur du contrôle de limites             |
| ID d'événement      | Événement S5 généré en cas de violation            |
| Nombre de répétitions | Nombre de violations consécutives avant déclenchement |
| Condition de validité | `validity: {param_id, mask, value}` facultatif : contrôle seulement tant que `(param & mask) == value` |
| Activé              | Indique si cette surveillance est actuellement active |

Le nombre de répétitions (`repetition`, 1 par défaut) et la condition de
validité suivent PUS-C. Tant que la condition de validité est fausse, la
définition est *non contrôlée* : ni en violation, ni nominale. Les
surveillances de rendement des panneaux solaires (EPS-05) utilisent ces deux
champs. Aucun des deux ne figure dans l'enregistrement TM(12,13). Le rapport
de transition indique quelle limite a été franchie, basse ou haute.

Lorsqu'un contrôle de surveillance échoue, l'OBC génère un paquet d'événement PUS S5 portant
l'ID d'événement correspondant. Cet événement est :

1. stocké dans le tampon d'événements pour une transmission ultérieure au sol ;
2. transmis au service événement-action S19 pour une réaction automatique ;
3. mis à disposition du journal des alarmes du MCS pour informer les opérateurs.

### 6.2 Commandes de surveillance {#62-monitoring-commands}

| Commande          | Mnémonique        | Sous-type | Description                                              |
|-------------------|-------------------|---------|------------------------------------------------------------|
| Activer le service | `MON_ENABLE`     | S12.1   | Activer globalement le contrôle de limites bord            |
| Désactiver le service | `MON_DISABLE` | S12.2   | Désactiver globalement le contrôle de limites bord         |
| Activer une définition | `MON_ENABLE_DEF` | S12.3 | Activer UNE définition, désignée par `mon_id`             |
| Désactiver une définition | `MON_DISABLE_DEF` | S12.4 | Désactiver UNE définition, désignée par `mon_id`     |
| Ajouter une définition | `MON_ADD_DEF` | S12.6   | `mon_id`, `param_id`, `check_type`, limites basse et haute |
| Supprimer une définition | `MON_DEL_DEF` | S12.7 | Supprimer UNE définition, désignée par `mon_id`           |
| Rapport des définitions | `MON_REPORT_DEFS` | S12.12 | Rapporter la table complète des définitions bord → **TM(12,13)** |

Il n'existe pas de S12.15/S12.16 : 12.1 et 12.2 sont les commutateurs du service entier et
12.3/12.4 ceux de chaque définition. `mon_id` désigne la *définition*, et non
le paramètre — un paramètre peut porter plusieurs surveillances (un niveau WARNING et un
niveau ALARM), d'où un identifiant distinct.

**TC(12,12) → TM(12,13)** permet au sol de relire ce que le satellite
détient réellement, plutôt que ce que la base de données sol croit avoir chargé. C'est
ce qu'envoie le bouton « Refresh from Spacecraft » du panneau FDIR du MCS. Le rapport
se compose de `count(u16)` suivi de `count` enregistrements fixes de 14 octets :

| Champ | Type | Signification |
|---|---|---|
| `mon_id`     | uint16  | Identifiant de la définition |
| `param_id`   | uint16  | Paramètre surveillé |
| `check_type` | uint8   | 0 = absolu (valeur dans la bande), 1 = variation (écart depuis le dernier contrôle) |
| `enabled`    | uint8   | État d'activation de la définition (S12.3 / S12.4) |
| `low_limit`  | float32 | Limite basse |
| `high_limit` | float32 | Limite haute |

Les *transitions* de limites sont signalées séparément, par TM(12,9) (entrée en dépassement de limite) et
TM(12,10) (retour au nominal).

## 7. Service PUS 19 — déclenchement événement-action {#7-pus-service-19--event-action-triggering}

Le service 19 relie les événements S5 (générés par la surveillance S12 ou par d'autres sources) à des actions
automatiques, mettant ainsi en œuvre la chaîne de réaction FDIR autonome.

### 7.1 Mécanisme événement-action {#71-event-action-mechanism}

Lorsqu'un événement S5 est émis :

1. L'OBC vérifie s'il existe une définition événement-action S19 active pour cet ID d'événement.
2. Si elle existe et est activée, l'action associée (une télécommande stockée) est exécutée.
3. L'exécution de l'action est consignée dans le tampon d'événements.
4. L'action peut elle-même déclencher d'autres événements, ce qui permet des réactions en cascade.

Une règle rattachée à une surveillance S12 (déclencheur de type `param`) peut
être limitée à un seul côté de la bande. Avec `limit: high`, elle ne se
déclenche que sur un franchissement de la limite haute ; avec `limit: low`,
que sur un franchissement de la limite basse ; avec `any` (valeur par défaut),
sur les deux. Les règles de surchauffe utilisent `high`, les règles de
rendement des panneaux solaires `low`, et les bandes symétriques comme la
survitesse des roues gardent `any`. Une règle ajoutée depuis le sol par
TC(19,1) utilise toujours `any`.

### 7.2 Commandes événement-action {#72-event-action-commands}

| Commande               | Sous-type | Description                            |
|------------------------|---------|------------------------------------------|
| Activer un lien événement-action | S19.1 | Activer un lien événement-action donné |
| Désactiver un lien événement-action | S19.2 | Désactiver un lien événement-action donné |
| Rapport des liens événement-action | S19.8 | Rapporter toutes les définitions événement-action actives |

### 7.3 Exemple type de chaîne FDIR {#73-typical-fdir-chain-example}

```
Surveillance S12 : bat_soc < 25%
  --> Événement S5 : EPS_LOW_SOC_WARNING
    --> Action S19 : OBC_SET_MODE(SAFE)
      --> Exécution de la séquence de mode survie
        --> Événement S5 : SAFE_MODE_ENTERED
```

## 8. Seuils de délestage progressif {#8-progressive-load-shed-thresholds}

La FDIR de l'EPS met en œuvre une stratégie de délestage par niveaux, fondée sur l'état de charge de la batterie.
Chaque seuil déclenche une réduction de puissance de plus en plus énergique :

| Seuil de SoC  | Niveau FDIR | Actions                                              |
|---------------|------------|-------------------------------------------------------|
| < 50 %         | Niveau 1   | Inhiber la prise de vue ; réduire la cadence HK à 0,5 Hz |
| < 35 %         | Niveau 2   | Commander l'AOCS en COARSE_SUN ; délester les charges non essentielles |
| < 25 %         | Niveau 3   | Passage en mode survie ; seules les charges essentielles restent alimentées |
| < 15 %         | Niveau 4   | Mode urgence ; OBC + TTC uniquement ; toutes les autres charges coupées |

Chaque niveau comprend toutes les actions des niveaux précédents. Le rétablissement après délestage est une
activité commandée depuis le sol — la FDIR ne réalimente pas automatiquement les charges lorsque le SoC
remonte.

## 9. Matrice de réaction aux contingences {#9-contingency-response-matrix}

La matrice suivante met en correspondance les scénarios de contingence et les procédures utilisées
pour leur détection et leur reprise :

| Scénario                    | Méthode de détection          | Fichier de procédure                  |
|-----------------------------|-------------------------------|---------------------------------------|
| Absence de télémesure TTC   | Aucune TM à l'AOS attendue    | `procedures/contingency/no_telemetry_at_pass.md` |
| Panne d'antenne de station sol | Surveillance des équipements sol | `procedures/contingency/gs_antenna_failure.md` |
| OBC bloqué en chargeur d'amorçage | Balise SID 11 avec `sw_image` = 0 | `procedures/contingency/obc_bootloader_recovery.md` |
| Isolation de bus nécessaire | Anomalies sur plusieurs sous-systèmes | `procedures/contingency/bus_failure_isolation.md` |
| Délestage progressif        | bat_soc franchissant les seuils | `procedures/contingency/progressive_load_shed.md` |
| Perte d'un panneau solaire  | Courant du panneau = 0 de façon persistante | `procedures/contingency/solar_panel_loss_response.md` |
| Défaillance en cascade des capteurs SCAO | Plusieurs capteurs invalides | `procedures/contingency/aocs_sensor_loss_recovery.md` |
| Actionneur AOCS bloqué      | Vitesse de roue constante malgré la commande | `procedures/contingency/aocs_actuator_stuck_recovery.md` |

Chaque procédure de contingence comprend :
- **les critères d'entrée** : comment reconnaître le scénario ;
- **les actions immédiates** : étapes urgentes pour stabiliser le satellite ;
- **les étapes d'analyse** : comment identifier la cause première ;
- **les actions de reprise** : étapes de rétablissement des opérations nominales ;
- **les points de contrôle GO/NO-GO** : points de décision soumis à l'autorisation du directeur de vol.

## 10. Configuration de la FDIR {#10-fdir-configuration}

Les seuils FDIR et les indicateurs d'activation/désactivation sont configurables par des commandes `SET_PARAM`.
Chaque règle peut être désactivée individuellement à des fins d'essai ou de recette en orbite. La désactivation
de règles FDIR exige une autorisation explicite du sol et devrait être limitée dans le temps.

| Paramètre de configuration   | Défaut  | Modifiable |
|------------------------------|---------|------------|
| Seuil de SoC du mode survie  | 15 %     | Oui        |
| Seuil de tension du mode survie | 26.5 V | Oui      |
| Limite rouge d'erreur d'attitude | 2 deg | Oui      |
| Limite rouge de vitesse angulaire | 2 deg/s | Oui   |
| Délai du chien de garde      | 10 s    | Non        |
| Délai de perte de commande (TTC-01) | 24 h | Oui    |
| Seuil du niveau 1 de délestage | 50 %   | Oui        |
| Seuil du niveau 2 de délestage | 35 %   | Oui        |
| Seuil du niveau 3 de délestage | 25 %   | Oui        |
| Seuil du niveau 4 de délestage | 15 %   | Oui        |

### 10.1 Conditionnement des règles FDIR par la phase {#101-phase-gating-of-fdir-rules}

Deux mécanismes sont conditionnés par la phase de mission (`eps.spacecraft_phase`, 0x0129) :

* le **modèle avancé de propagation de défaillance** (`fdir/fault_propagation.yaml`) n'est
  armé qu'à la phase 6 (NOMINAL), dans son ensemble ;
* les **règles de seuil historiques** individuelles (`subsystems/fdir.yaml`) peuvent porter un
  champ facultatif `min_phase:`. En son absence — cas par défaut —, une règle est armée dans
  toutes les phases.

`min_phase` existe pour les règles dont la condition de déclenchement *est* l'état attendu d'un
satellite non encore recetté. Deux règles le portent, toutes deux avec `min_phase: 6` :

| Règle | Motif du conditionnement |
|---|---|
| `aocs.wheels_enabled < 2` | Le chargeur d'amorçage démarre avec les quatre roues de réaction désactivées, et elles le restent jusqu'à ce que COM-004 commande `AOCS_ENABLE_WHEEL`. Sans condition, cette règle de niveau 2 se verrouillait dès le premier cycle de chaque exécution, bloquait le mode satellite sur SAFE et faisait sortir `aocs.mode` de NOMINAL. |
| `aocs.att_error > 5 deg` (persistance de 420 s) | Une erreur d'attitude importante est attendue pendant l'amortissement des vitesses angulaires en LEOP et pendant les basculements de la vérification AOCS (COM-004/005/013). Les performances de pointage ne deviennent une exigence qu'une fois le satellite déclaré opérationnel. |

**Tout le reste demeure armé dans toutes les phases, délibérément.** Le SoC de la batterie et
la tension du bus, les températures de la batterie, de l'OBC, des roues et du PA, le nombre de redémarrages et l'état du bus CAN
relèvent de la protection du matériel : la LEOP est précisément le moment où un satellite mal piloté
vide sa batterie, et un `phase >= 6` appliqué en bloc à l'ensemble des règles
désactiverait ces protections pendant tout le début de la mission.

Une règle en dessous de son `min_phase` est **désarmée, et non masquée** : tout verrou qu'elle
détient est levé et son accumulateur de persistance est remis à zéro, de sorte qu'un retour
sous le seuil — un redémarrage de l'OBC vers le chargeur d'amorçage, par exemple — ne peut
laisser derrière lui une contingence périmée.

### 10.2 Un seul mode satellite {#102-one-spacecraft-mode}

`sat.mode` (0x0001) est le mot de mode satellite télémesuré — la même valeur, sur
la même échelle, que celle affichée dans l'en-tête de la console du MCS :

| Valeur | Mode | Signification |
|---|---|---|
| 0 | SAFE      | Une contingence FDIR de niveau survie est verrouillée, **ou** la phase est inférieure à 6 |
| 1 | NOMINAL   | Recetté, aucune contingence, pas de prise de vue |
| 2 | SCIENCE   | Recetté, aucune contingence, charge utile en prise de vue active |
| 3 | EMERGENCY | Une contingence FDIR de niveau urgence est verrouillée |

Il en existait auparavant une seconde dérivation, indépendante, qui ne lisait que les verrous
FDIR et ignorait le conditionnement par la phase : un `GET_PARAM(0x0001)` renvoyait ainsi NOMINAL
alors que l'en-tête de la console affichait SAFE pendant toute la LEOP. Il n'existe plus désormais qu'une seule
dérivation (`Engine._update_sc_mode`), et 0x0001 est écrit à partir d'elle.

## 11. Remarques d'exploitation {#11-operational-notes}

1. Après chaque passage en mode survie, une analyse détaillée de l'anomalie doit être menée à bien avant
   le retour aux opérations nominales.
2. Les règles FDIR ne devraient pas être désactivées pendant les opérations nominales. Les exceptions exigent une
   approbation formelle et une évaluation des risques.
3. Le journal d'événements FDIR conserve les 100 derniers événements en mémoire non volatile et résiste
   aux redémarrages de l'OBC. Les événements sont stockés dans un tampon linéaire ; les données de servitude utilisent un tampon circulaire
   (politique store-1).
4. Pendant la recette en orbite, les règles FDIR peuvent être temporairement élargies (p. ex. limite d'erreur
   d'attitude portée à 5 deg) pour permettre les activités d'étalonnage.
5. La surveillance S12 est évaluée à chaque cycle. Un paramètre qui viole transitoirement une limite
   pendant moins que le nombre de répétitions configuré ne déclenche pas de réaction.
6. Les liens événement-action S19 peuvent être désactivés individuellement à des fins d'essai. Cela permet de
   générer les événements FDIR (pour la visibilité) sans déclencher d'action corrective automatique.
7. Le journal des alarmes du MCS affiche tous les événements S5 et toutes les violations S12 avec des badges de gravité,
   des fonctions d'acquittement et d'effacement et un filtrage par sous-système. La section 12 donne les règles
   qui décident du moment où une alarme quitte la liste active.

## 12. Cycle de vie des alarmes du MCS {#12-mcs-alarm-lifecycle}

Le tiroir des alarmes du MCS suit les états d'alarme de la norme ISA-18.2. Chaque alarme porte deux
informations indépendantes : la condition est-elle toujours présente (active ou revenue à la normale), et un
opérateur l'a-t-il acquittée ?

| État | Condition | Acquittée | Liste des alarmes actives |
|-------|-----------|--------------|-----------------|
| Non acquittée, active | présente | non | affichée, signalée |
| Acquittée, active | présente | oui | affichée (alarme permanente) |
| Non acquittée, revenue à la normale | disparue | non | affichée, marquée « revenue à la normale » |
| Acquittée, revenue à la normale | disparue | oui | retirée (conservée dans le journal et l'archive) |

Une alarme ne quitte donc la liste active que lorsque sa condition a disparu **et** qu'elle a été
acquittée, dans un ordre ou dans l'autre. Ce qui ramène une alarme à la normale dépend de sa source :

- **Limite sol** (`mcs/limits.yaml`) : le paramètre est revenu dans sa bande (avec
  hystérésis), ou une nouvelle bande sur le même paramètre la remplace (du jaune au rouge, du rouge au jaune).
- **Surveillance S12** : TM(12,10) de retour dans les limites pour la même surveillance, ou la surveillance est désactivée
  ou supprimée (TM(12,13)). Au début de chaque passage, après une reconnexion TM et après une
  discontinuité du temps de mission (rechargement ou redémarrage de l'état de bord), le MCS compare aussi les valeurs
  temps réel récentes à la bande de la surveillance, car la TM(12,10) peut ne jamais arriver en temps réel (celle émise hors
  couverture se trouve dans la mémoire de bord).
- **Événement S5** : un événement n'a pas de condition qui puisse revenir à la normale. Il reste dans la liste jusqu'à ce qu'il
  soit acquitté, et son acquittement le retire. Les événements S5 0x9xxx et 0xAxxx reflètent
  les transitions S12 et ne lèvent pas d'alarme propre.

Une alarme sur un paramètre qui n'est plus transmis reste active : sa dernière valeur connue est
toujours hors limites, et le paramètre est affiché comme périmé.

**La télémesure stockée n'atteint jamais les affichages temps réel.** Un vidage S15 transmet les paquets stockés sur
le canal virtuel 1 (VC1), et la télémesure temps réel utilise le VC0. Le MCS archive les événements S5
relus à leur heure de bord et compte les paquets (`/api/tm-stored`). Les paquets relus
ne lèvent ni n'effacent d'alarme, ne modifient pas les valeurs temps réel et n'alimentent ni le journal
FDIR, ni le GO/NO-GO, ni les tracés temps réel, ni le journal des paquets. Analysez un vidage hors ligne dans le
visualiseur de TM différée ou sur la page `/dumps` du MCS.

---

*Fin du document — EOSAT1-UM-FDIR-009*
