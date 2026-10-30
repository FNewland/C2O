# CTG-023 : Délestage progressif
**Sous-système :** EPS
**Phase :** CONTINGENCY
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Exécuter une séquence de délestage progressive et maîtrisée pendant une éclipse prolongée,
lorsque l'état de charge (SoC) de la batterie diminue et que le satellite ne peut pas produire
de puissance. Les charges sont délestées dans un ordre de priorité strict, à des seuils de SoC définis, afin de maximiser
l'autonomie de la batterie et d'éviter les dommages dus à une décharge profonde. Une fois l'éclipse terminée et la batterie
en cours de recharge, les charges sont rétablies dans l'ordre de priorité inverse, avec une vérification de stabilité
à chaque étape.

Cette procédure se distingue de CTG-001 (délestage sur sous-tension) en ce qu'elle est déclenchée
par la baisse du SoC et non par un seuil de tension, et qu'elle comporte des points de décision GO/NO-GO
explicites à chaque niveau de délestage, pour permettre au directeur de vol de décider en connaissance de cause
du rythme et de la profondeur du délestage.

## Prérequis
- [ ] SoC de la batterie en baisse — `eps.bat_soc` (0x0101) en tendance descendante
- [ ] Phase d'éclipse confirmée — `eps.eclipse_flag` (0x0108) = 1
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Directeur de vol informé du scénario d'éclipse prolongée
- [ ] Prévision d'orbite à jour disponible — heure de sortie d'éclipse connue
- [ ] Bilan de puissance (production comparée à la consommation) calculé et négatif

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| eps.bat_soc | 0x0101 | Surveillance — baisse vers les seuils |
| eps.bus_voltage | 0x0105 | Surveillance — baisse attendue avec le SoC |
| eps.bat_voltage | 0x0100 | Surveillance — consigner la tendance |
| eps.bat_current | 0x0109 | Négatif (décharge) pendant l'éclipse |
| eps.power_cons | 0x0106 | Consigner avant/après chaque palier de délestage |
| eps.power_gen | 0x0107 | 0 W pendant l'éclipse |
| eps.eclipse_flag | 0x0108 | 1 (éclipse) |
| payload.mode | 0x0600 | Mode courant de la charge utile |
| tcs.cooler_fpa | 0x040C | État courant du refroidisseur du FPA |
| ttc.pa_on | 0x0516 | État courant de l'amplificateur de puissance |
| aocs.mode | 0x020F | Mode courant du SCAO |
| eps.uv_flag | 0x010E | Surveiller — peut se déclencher en décharge profonde |

## Télécommandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| PAYLOAD_SET_MODE | 8 | 1 | 26 | Mettre la charge utile en mode OFF |
| FPA_COOLER | 8 | 1 | 43 | Désactiver le refroidisseur du FPA |
| TTC_PA_OFF | 8 | 1 | 67 | Désactiver l'amplificateur de puissance (TX) |
| EPS_POWER_OFF | 8 | 1 | 20 | Mettre une ligne d'alimentation sur OFF |
| EPS_POWER_ON | 8 | 1 | 19 | Mettre une ligne d'alimentation sur ON |
| TTC_PA_ON | 8 | 1 | 66 | Activer l'amplificateur de puissance (TX) |
| AOCS_SET_MODE | 8 | 1 | 0 | Régler le mode SCAO |
| OBC_SET_MODE | 8 | 1 | 50 | Régler le mode de l'OBC (safe/emergency) |

## Déroulement

### Étape 1 : Confirmer l'éclipse prolongée et établir la référence
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander la télémesure de servitude EPS
**Verify:** `eps.eclipse_flag` (0x0108) = 1 — le satellite est en éclipse
**Verify:** `eps.bat_soc` (0x0101) — consigner la valeur courante (~70 % attendu au départ)
**Verify:** `eps.bus_voltage` (0x0105) — consigner la référence
**Verify:** `eps.bat_current` (0x0109) — confirmer qu'il est négatif (décharge)
**Verify:** `eps.power_cons` (0x0106) — consigner la consommation totale
**Verify:** `eps.power_gen` (0x0107) = 0 W — aucune production solaire
**Action:** Calculer la vitesse de décharge : power_cons / bat_capacity, pour estimer le temps restant avant
chaque seuil.
**Action:** Obtenir de la dynamique du vol l'heure prévue de sortie d'éclipse.
**Action:** Annoncer « EXTENDED ECLIPSE — battery declining, initiating load shed
monitoring » sur la boucle opérations.
**GO/NO-GO:** Éclipse confirmée, SoC en baisse, vitesse de décharge calculée — passer
à la surveillance des seuils.

### Étape 2 : SoC < 50 % — délester la charge de priorité 1 (charge utile sur OFF)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Télémesure de servitude EPS ; surveiller `eps.bat_soc` (0x0101) toutes les 60 s
**Déclencheur :** Lorsque `eps.bat_soc` < 50 % :
**Action:** Annoncer « SoC below 50 % — shedding payload » sur la boucle opérations.
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) — Mettre la charge utile sur OFF
**Verify:** `payload.mode` (0x0600) = 0 (OFF) en 10 s
**Verify:** `eps.power_cons` (0x0106) diminue (-45 W attendus en prise de vue, -8 W en STANDBY)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Attendre 30 s et contrôler de nouveau
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Télémesure de servitude charge utile
**Verify:** `eps.bat_soc` (0x0101) — consigner la nouvelle valeur
**Verify:** `eps.bus_voltage` (0x0105) — consigner la nouvelle valeur
**Action:** Recalculer la vitesse de décharge avec la consommation réduite.
**GO/NO-GO:** Charge utile délestée. Si la vitesse de décharge est tenable jusqu'à la sortie d'éclipse
prévue, MAINTENIR (HOLD) ce niveau et surveiller. Si le SoC doit atteindre 35 % avant la sortie d'éclipse,
préparer le niveau de délestage suivant.

### Étape 3 : SoC < 35 % — délester la charge de priorité 2 (refroidisseur du FPA sur OFF)
**Déclencheur :** Lorsque `eps.bat_soc` (0x0101) < 35 % :
**Action:** Annoncer « SoC below 35 % — shedding FPA cooler » sur la boucle opérations.
**TC:** `FPA_COOLER(on=0)` (Service 8, Subtype 1, func_id 43) — Désactiver le refroidisseur du FPA
**Verify:** `tcs.cooler_fpa` (0x040C) = 0 (OFF) en 5 s
**Verify:** `eps.power_cons` (0x0106) diminue d'environ 15 W
**Note:** La température du détecteur du FPA va commencer à monter. Consigner la température courante du FPA
pour l'évaluation après la reprise. Le redémarrage du refroidisseur nécessitera une mise en froid progressive.
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Attendre 30 s et contrôler de nouveau
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — Télémesure de servitude TCS
**Verify:** `eps.bat_soc` (0x0101) — consigner la nouvelle valeur
**Verify:** `eps.bus_voltage` (0x0105) — consigner la nouvelle valeur
**Action:** Recalculer la vitesse de décharge.
**GO/NO-GO:** Refroidisseur du FPA délesté. Si la vitesse de décharge est tenable jusqu'à la sortie d'éclipse,
MAINTENIR et surveiller. Si le SoC doit atteindre 25 % avant la sortie d'éclipse, préparer le niveau suivant.

### Étape 4 : SoC < 25 % — délester la charge de priorité 3 (émetteur TTC sur OFF)
**Déclencheur :** Lorsque `eps.bat_soc` (0x0101) < 25 % :
**Action:** Annoncer « SoC below 25 % — shedding TTC transmitter. DOWNLINK WILL BE
LOST. Spacecraft will receive commands only. » sur la boucle opérations.
**TC:** `TTC_PA_OFF` (Service 8, Subtype 1, func_id 67) — Désactiver l'amplificateur de puissance
**Verify:** `ttc.pa_on` (0x0516) = 0 en 5 s
**Verify:** `eps.power_cons` (0x0106) diminue d'environ 20 W
**Note:** AVERTISSEMENT — La liaison descendante de télémesure est désormais coupée. Le satellite peut encore recevoir
des commandes (le RX est sur une alimentation non commutable) mais ne peut plus émettre de télémesure. Toute vérification
ultérieure doit s'appuyer sur l'acceptation des commandes (les rapports de vérification du service 1 seront
mis en file d'attente mais non transmis).
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Attendre 30 s puis envoyer — la réponse sera mise en file d'attente à bord.
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Télémesure de servitude TT&C
**GO/NO-GO:** TX délesté. La tension du bus devrait se stabiliser. Si le SoC continue de baisser
sous 15 %, passer au niveau d'urgence. Le directeur de vol doit autoriser l'étape suivante.

### Étape 5 : SoC < 15 % — délester la charge de priorité 4 (roues AOCS sur OFF) — URGENCE
**Déclencheur :** Lorsque `eps.bat_soc` (0x0101) < 15 % (estimé à partir de la vitesse mesurée avant le délestage du TX) :
**Action:** Annoncer « SoC below 15 % — EMERGENCY — shedding AOCS reaction wheels.
Spacecraft will LOSE active attitude control. » sur la boucle opérations.
**TC:** `EPS_POWER_OFF(line_index=7)` (Service 8, Subtype 1, func_id 20) — Mettre hors tension les roues AOCS
**Note:** AVERTISSEMENT — Le satellite va perdre le contrôle d'attitude actif trois axes.
Le moment cinétique résiduel provoquera un lent culbutage. L'amortissement magnétique passif
(s'il existe) n'assure qu'une stabilisation grossière. Les générateurs solaires risquent de ne pas être pointés de façon optimale
à la sortie d'éclipse, ce qui retardera la reprise de la production de puissance.
**Note:** Uniquement si le SCAO est encore commandable. Le mode 2 est DETUMBLE, l'amortisseur de vitesses angulaires
par magnétocoupleurs seuls — le mode 1 est SAFE_BOOT, qui n'actionne rien.
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0) — DETUMBLE, stabilisation par magnétocoupleurs
seuls avant la mise hors tension des roues
**GO/NO-GO:** Toutes les charges non essentielles délestées. Surveiller la stabilisation de la tension du bus.
Si la tension du bus descend sous 25.0 V malgré le délestage de toutes les charges, commander
`OBC_SET_MODE(mode=2)` pour passer en mode EMERGENCY en dernier recours.

### Étape 6 : Surveiller la sortie d'éclipse et la recharge de la batterie
**Action:** Surveiller `eps.eclipse_flag` (0x0108) — attendre son passage à 0 (éclairé).
**Note:** Si le TX est coupé, l'opérateur ne peut pas recevoir de télémesure. Utiliser l'heure prévue de sortie d'éclipse
fournie par la dynamique du vol. Après la sortie prévue + 60 s, tenter de réactiver le TX :
**Note:** Uniquement si le TX a été délesté à l'étape 4.
**TC:** `TTC_PA_ON` (Service 8, Subtype 1, func_id 66) — réactiver l'amplificateur de puissance
**Verify:** `ttc.pa_on` (0x0516) = 1 en 10 s (si la télémesure reprend)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander la télémesure de servitude EPS
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Télémesure de servitude TT&C
**Verify:** `eps.eclipse_flag` (0x0108) = 0 — éclairement confirmé
**Verify:** `eps.power_gen` (0x0107) > 0 W — production solaire active
**Verify:** `eps.bat_current` (0x0109) — positif (charge)
**Verify:** `eps.bat_soc` (0x0101) — consigner et commencer à suivre la tendance de recharge
**Action:** Surveiller toutes les 60 s jusqu'à ce que `eps.bat_soc` > 25 %.
**GO/NO-GO:** Sortie d'éclipse et charge de la batterie confirmées — passer au rétablissement.

### Étape 7 : Rétablir les charges dans l'ordre de priorité inverse
**Action:** Rétablir les charges une par une, en attendant au moins 5 minutes entre chacune
pour vérifier la stabilité du bilan de puissance. Ne rétablir une charge que lorsque le SoC dépasse le seuil
de délestage + 10 % de marge.

**Étape 7a — Rétablir les roues AOCS (si délestées) — lorsque SoC > 25 % :**
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19)
**TC:** `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) — COARSE_SUN, pour amorcer la reprise d'attitude.
**Verify:** `aocs.mode` (0x020F) = 3 (COARSE_SUN) en 15 s
**Verify:** Vitesses angulaires `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205),
`aocs.rate_yaw` (0x0206) — en baisse vers zéro
**Verify:** `eps.bus_voltage` (0x0105) reste > 26.0 V après la montée en vitesse des roues
**Action:** Attendre 5 minutes et confirmer que le SoC poursuit sa hausse.
**GO/NO-GO:** Roues AOCS rétablies et attitude en cours de reprise — continuer.

**Étape 7b — Rétablir le TTC TX (si délesté) — lorsque SoC > 35 % :**
**TC:** `TTC_PA_ON` (Service 8, Subtype 1, func_id 66)
**Verify:** `ttc.pa_on` (0x0516) = 1 en 5 s
**Verify:** `eps.bus_voltage` (0x0105) reste > 26.5 V
**Action:** Attendre 5 minutes et confirmer que le SoC poursuit sa hausse.
**GO/NO-GO:** TX rétabli et télémesure reçue — continuer.

**Étape 7c — Rétablir le refroidisseur du FPA — lorsque SoC > 45 % :**
**TC:** `FPA_COOLER(on=1)` (Service 8, Subtype 1, func_id 43)
**Verify:** `tcs.cooler_fpa` (0x040C) = 1 en 5 s
**Note:** La mise en froid du FPA de la température ambiante à la température de fonctionnement prend environ
20 minutes. Les prises de vue ne doivent pas reprendre avant que le FPA ait atteint sa température de fonctionnement.
**Verify:** `eps.bus_voltage` (0x0105) reste > 27.0 V
**Action:** Attendre 5 minutes et confirmer que le SoC poursuit sa hausse.
**GO/NO-GO:** Refroidisseur du FPA rétabli — continuer.

**Étape 7d — Remettre la charge utile en STANDBY — lorsque SoC > 60 % :**
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26)
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) en 10 s
**Verify:** `eps.bus_voltage` (0x0105) reste > 27.5 V
**Verify:** `eps.bat_soc` (0x0101) reste > 55 %
**GO/NO-GO:** Toutes les charges rétablies. Bilan de puissance positif — procédure terminée.

### Étape 8 : Vérification après la reprise
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Télémesure de servitude EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Télémesure de servitude AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — Télémesure de servitude TCS
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Télémesure de servitude charge utile
**Verify:** `eps.bus_voltage` (0x0105) > 28.0 V
**Verify:** `eps.bat_soc` (0x0101) > 55 % et en hausse
**Verify:** `eps.power_gen` (0x0107) > `eps.power_cons` (0x0106) — marge positive
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL) s'il est rétabli, ou 3 (COARSE_SUN) s'il est encore en attente
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY)
**Verify:** Toutes les températures des sous-systèmes dans leurs plages nominales
**GO/NO-GO:** Tous les systèmes rétablis et nominaux — procédure terminée.

## Critères de vérification
- [ ] Toutes les décisions de délestage/rétablissement documentées, avec le SoC et la tension du bus à chaque étape
- [ ] `eps.uv_flag` (0x010E) = 0 (retombé)
- [ ] `eps.bus_voltage` (0x0105) > 28.0 V
- [ ] `eps.bat_soc` (0x0101) > 55 % et en hausse
- [ ] Tous les sous-systèmes revenus dans leurs modes de fonctionnement nominaux
- [ ] Bilan de puissance positif (production > consommation) avec une marge d'au moins 5 W
- [ ] Aucune nouvelle sous-tension pendant au moins 2 orbites après le rétablissement

## Conduite à tenir hors nominal
- Si la tension du bus descend sous 25.0 V après le délestage de toutes les charges : commander
  `OBC_SET_MODE(mode=2)` pour passer en mode EMERGENCY. Le satellite passera de lui-même en configuration
  de puissance minimale.
- Si le SoC descend sous 10 % : risque de décharge profonde de la batterie et d'endommagement permanent des éléments.
  Commander immédiatement le mode EMERGENCY. Informer le directeur de mission d'une possible
  dégradation de la batterie.
- Si la durée de l'éclipse dépasse la prévision de plus de 10 minutes : réévaluer
  les paramètres d'orbite avec la dynamique du vol. Éclipse imprévue possible, due à des débris
  ou à une erreur de manœuvre.
- Si la puissance ne revient pas après la sortie d'éclipse : suspecter une défaillance du générateur solaire. Contrôler
  les courants par panneau, de `eps.sa_px_current` (0x012B) à `eps.sa_mz_current`
  (0x0130). S'ils sont tous proches de zéro, passer à CTG-009 (Dégradation du générateur solaire).
- Si les charges ne peuvent pas être rétablies sans nouvelle baisse du SoC : le satellite est peut-être
  en bilan de puissance durablement négatif. Réduire le cycle d'utilisation opérationnel, désactiver
  les prises de vue et exploiter le satellite en mode d'économie d'énergie. Se coordonner avec la planification
  de mission pour un profil de puissance révisé.
- Si le SCAO ne parvient pas à rétablir l'attitude après le rétablissement des roues : commander
  d'abord `AOCS_SET_MODE(mode=2)` (DETUMBLE), puis passer en COARSE_SUN (mode 3) une fois les
  vitesses angulaires inférieures à 0.5 deg/s. Le pointage fin risque de ne pas être atteignable avant la recharge complète
  de la batterie.

## Chemin de reprise — remise sous tension des charges délestées
Une fois le bus stabilisé par cette procédure et la cause première comprise, **tout sous-système dont les lignes d'alimentation ont été mises hors tension lors du délestage doit être remis en service dans l'ordre maîtrisé défini par LEOP-007 (mise sous tension séquentielle)**. Ne **pas** se contenter de réactiver les lignes au coup par coup : LEOP-007 impose le bon enchaînement sous-système→ligne→mode, l'espacement des courants d'appel, le préconditionnement thermique des réchauffeurs OBC/batterie et les exemptions set_mode AOCS/charge utile au verrou d'alimentation à deux niveaux des TC. Référence croisée : `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
