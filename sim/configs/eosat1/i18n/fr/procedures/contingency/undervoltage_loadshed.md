# CTG-001 : Délestage sur sous-tension

**Catégorie :** Contingence
**Poste responsable :** Puissance et thermique (EPS/TCS)
**Postes associés :** directeur de vol, tous les postes
**Difficulté :** Avancé
**Révision :** 1.1 --- 2026-11-02 (décision de Franz P3 : « si le satellite ne déleste pas, le sol
doit le faire --- mais vérifier d'abord le satellite »). Chaque niveau de délestage lit maintenant
d'abord l'état de la ligne et ne déleste depuis le sol que ce que la FDIR de bord n'a pas déjà coupé ;
le rétablissement réalimente chaque ligne avant la commande de mode de son unité.

## Objectif
Traiter une sous-tension sur le bus d'alimentation principal en achevant depuis le sol le délestage
que le satellite n'a pas déjà fait, dans un ordre de priorité maîtrisé. L'EPS déleste de lui-même sous
25,0 V (charge utile → refroidisseur du FPA → `ttc_tx` → roues AOCS → prop, une ligne par seconde,
événements LOAD_SHED_STAGE_1..3 0x0106-0x0108), et les modes safe/emergency de l'EPS ainsi que les
règles S19 sur l'état de charge ouvrent aussi des lignes : au moment où cette fiche est exécutée,
certaines lignes peuvent déjà être coupées. Les charges sont délestées en commençant par la plus basse
priorité (charge utile), puis le refroidisseur du FPA, l'émetteur TX et les roues
de réaction, afin d'enrayer la baisse de la tension du bus et de protéger les fonctions critiques du satellite. Le rétablissement
est surveillé jusqu'au retour de l'état de charge de la batterie et de la tension du bus à des niveaux sûrs.

## Prérequis
- [ ] Indicateur de sous-tension détecté — `eps.uv_flag` (0x010E) = 1 ou tension du bus observée < 27.0 V
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Directeur de vol informé, autorisant le délestage manuel
- [ ] Prévision d'orbite à jour disponible (heures d'entrée et de sortie d'éclipse)

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| eps.uv_flag | 0x010E | 1 (sous-tension détectée) |
| eps.bus_voltage | 0x0105 | Surveillance — < 27.0 V attendu à la détection |
| eps.bat_soc | 0x0101 | Surveillance — consigner la tendance |
| eps.bat_voltage | 0x0100 | Surveillance — consigner la valeur |
| eps.bat_current | 0x0109 | Négatif (décharge) |
| eps.power_cons | 0x0106 | Surveillance — consigner avant/après chaque délestage |
| eps.power_gen | 0x0107 | Consigner — peut valoir 0 en éclipse |
| eps.eclipse_flag | 0x0108 | État courant Soleil/éclipse |
| payload.mode | 0x0600 | Mode courant de la charge utile |
| tcs.cooler_fpa | 0x040C | État courant du refroidisseur |
| ttc.pa_on | 0x0516 | État courant de l'amplificateur de puissance |
| aocs.mode | 0x020F | Mode courant du SCAO |
| eps.load_shed_stage | 0x0134 | Palier de délestage de bord (0 = rien de délesté à bord) |
| eps.pl_payload | 0x0113 | Ligne charge utile (0 = déjà délestée) |
| eps.pl_fpa_cooler | 0x0114 | Ligne du refroidisseur du FPA (0 = déjà délestée) |
| eps.pl_ttc_tx | 0x0112 | Ligne TX (0 = déjà délestée) |
| eps.pl_aocs_wheels | 0x0117 | Ligne des roues AOCS (0 = déjà délestée) |

## Télécommandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| PAYLOAD_SET_MODE | 8 | 1 | 26 | Mettre la charge utile en mode OFF |
| FPA_COOLER | 8 | 1 | 43 | Désactiver le refroidisseur du FPA |
| TTC_PA_OFF | 8 | 1 | 67 | Désactiver l'amplificateur de puissance (TX) |
| EPS_POWER_OFF | 8 | 1 | 20 | Mettre une ligne d'alimentation sur OFF |
| OBC_SET_MODE | 8 | 1 | 50 | Régler le mode de l'OBC (safe/emergency) |
| EPS_POWER_ON | 8 | 1 | 19 | Réalimenter une ligne avant de rétablir son unité |
| TTC_PA_ON | 8 | 1 | 66 | Réactiver l'amplificateur de puissance |
| AOCS_SET_MODE | 8 | 1 | 0 | Relancer le SCAO une fois sa ligne rétablie |

## Déroulement

### Étape 1 : Détecter et confirmer la sous-tension
**LABEL:** `STEP-1`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander la télémesure de servitude EPS
**Verify:** `eps.uv_flag == 1` (0x010E, timeout 10 s)
**Verify:** `eps.bus_voltage` (0x0105) — consigner la valeur courante (< 27.0 V attendu)
**Verify:** `eps.bat_soc` (0x0101) — consigner la valeur courante
**Verify:** `eps.bat_voltage` (0x0100) — consigner la valeur courante
**Verify:** `eps.power_cons` (0x0106) — consigner la consommation totale
**Verify:** `eps.power_gen` (0x0107) — consigner la production de puissance
**Verify:** `eps.eclipse_flag` (0x0108) — déterminer si le satellite est en éclipse
**Verify:** `eps.load_shed_stage` (0x0134) — consigner ce que le délesteur de bord a déjà fait
**Verify:** `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_ttc_tx` (0x0112), `eps.pl_aocs_wheels` (0x0117) — consigner chacune : 1 = encore sur ON, 0 = déjà délestée à bord
**Note:** VÉRIFIER D'ABORD LE SATELLITE. Une ligne que la FDIR a déjà ouverte ne peut pas être
délestée une seconde fois : sa commande est refusée S1.8 « power line … is OFF », et les données de
servitude de l'unité s'arrêtent, si bien que son paramètre de mode (p. ex. `payload.mode`) reste figé à
sa dernière valeur et ne peut jamais indiquer le nouvel état. Chaque niveau ci-dessous se branche donc sur
la LIGNE : ne délester depuis le sol que ce qui est encore sur ON.
**Action:** Annoncer « UNDERVOLTAGE — completing load shed from the ground » sur la boucle opérations.
**GO/NO-GO:** Sous-tension confirmée. Le directeur de vol autorise le délestage — continuer.

### Étape 2 : Délester la charge de priorité 1 — charge utile sur OFF
**LABEL:** `STEP-2`
**BRANCH:** `eps.pl_payload == 1` -> GO `STEP-2-SHED` | NO-GO `STEP-2-CHECK` (timeout 10 s)
**Note:** GO — la ligne de la charge utile est encore sur ON : la délester depuis le sol. NO-GO — la
FDIR de bord l'a déjà ouverte : ne rien envoyer et passer au contrôle de tension.

**LABEL:** `STEP-2-SHED`
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) — Mettre la charge utile sur OFF
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Télémesure de servitude charge utile
**Verify:** `payload.mode` (0x0600) = 0 (OFF) en 10 s
**Verify:** `eps.power_cons` (0x0106) diminue (-45 W attendus en prise de vue, -8 W en STANDBY)

**LABEL:** `STEP-2-CHECK`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Attendre 30 s et contrôler de nouveau la tension du bus
**Verify:** `eps.bus_voltage` (0x0105) — consigner la nouvelle valeur
**BRANCH:** `eps.bus_voltage > 26.5` -> GO `STEP-6` | NO-GO `STEP-3` (timeout 60 s)
**Note:** GO — le délestage a suffi ; MAINTENIR (HOLD) ce niveau, la suite est directement la surveillance.
NO-GO — la tension baisse encore ; le niveau de délestage suivant s'applique. La temporisation de 60 s
de la branche correspond à ce que la prose appelait « attendre 30 s et contrôler de nouveau » : elle laisse au bus deux
échantillons SID 1 à 1 Hz pour se stabiliser avant l'évaluation du prédicat.

### Étape 3 : Délester la charge de priorité 2 — refroidisseur du FPA sur OFF
**LABEL:** `STEP-3`
**BRANCH:** `eps.pl_fpa_cooler == 1` -> GO `STEP-3-SHED` | NO-GO `STEP-3-CHECK` (timeout 10 s)
**Note:** GO — la ligne du refroidisseur est encore sur ON : la délester. NO-GO — déjà délestée à bord.

**LABEL:** `STEP-3-SHED`
**TC:** `FPA_COOLER(on=0)` (Service 8, Subtype 1, func_id 43) — Désactiver le refroidisseur du FPA
**TC:** `GET_PARAM(param_id=0x040C)` (Service 20, Subtype 3) — `tcs.cooler_fpa` : le SID 3 n'est périodique que toutes les 60 s : lire la valeur que ce contrôle utilise
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — Télémesure de servitude TCS
**Verify:** `tcs.cooler_fpa` (0x040C) = 0 (OFF) en 5 s
**Verify:** `eps.power_cons` (0x0106) diminue d'environ 15 W

**LABEL:** `STEP-3-CHECK`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Attendre 30 s et contrôler de nouveau la tension du bus
**Verify:** `eps.bus_voltage` (0x0105) — consigner la nouvelle valeur
**BRANCH:** `eps.bus_voltage > 26.0` -> GO `STEP-6` | NO-GO `STEP-4` (timeout 60 s)

### Étape 4 : Délester la charge de priorité 3 — émetteur TX sur OFF
**LABEL:** `STEP-4`
**BRANCH:** `eps.pl_ttc_tx == 1` -> GO `STEP-4-SHED` | NO-GO `STEP-4-CHECK` (timeout 10 s)
**Note:** GO — la ligne `ttc_tx` est encore sur ON : couper le PA. NO-GO — la ligne est déjà ouverte
à bord (`TTC_PA_OFF` serait refusé S1.8) et la liaison descendante en bande S a déjà disparu.

**LABEL:** `STEP-4-SHED`
**TC:** `TTC_PA_OFF` (Service 8, Subtype 1, func_id 67) — Désactiver l'amplificateur de puissance
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Télémesure de servitude TT&C
**Verify:** `ttc.pa_on` (0x0516) = 0 en 5 s
**Verify:** `eps.power_cons` (0x0106) diminue d'environ 20 W
**Note:** AVERTISSEMENT — Cette action supprime la capacité de liaison descendante. La liaison montante (RX) reste active.
Le satellite peut encore recevoir des commandes mais ne peut plus émettre de télémesure.

**LABEL:** `STEP-4-CHECK`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Attendre 30 s et contrôler de nouveau la tension du bus
**Verify:** `eps.bus_voltage` (0x0105) — consigner la nouvelle valeur
**BRANCH:** `eps.bus_voltage > 25.5` -> GO `STEP-6` | NO-GO `STEP-5` (timeout 60 s)
**Note:** Après cette étape, la liaison descendante en bande S est INHIBÉE — `ttc.tx_active`
(0x0525) passe à 0 et la télémesure s'arrête. La balise UHF est une radio distincte, sur la
ligne non commutable `ttc_rx`, et continue d'émettre la HK SID 11 : le sol peut donc encore
voir l'état du satellite ; le prédicat de la branche est évalué à partir du dernier
échantillon SID 1 reçu avant la coupure de l'amplificateur, ou à partir de la balise.

### Étape 5 : Délester la charge de priorité 4 — roues de réaction sur OFF
**LABEL:** `STEP-5`
**BRANCH:** `eps.pl_aocs_wheels == 1` -> GO `STEP-5-SHED` | NO-GO `STEP-5-CHECK` (timeout 10 s)
**Note:** GO — la ligne des roues est encore sur ON : l'ouvrir. NO-GO — déjà délestée à bord (le SCAO
est déjà retombé sur OFF, `aocs.mode` 0).

**LABEL:** `STEP-5-SHED`
**TC:** `EPS_POWER_OFF(line_index=7)` (Service 8, Subtype 1, func_id 20) — Mettre hors tension les roues AOCS
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 0 (OFF) en 5 s
**Note:** AVERTISSEMENT — Le satellite va perdre le contrôle d'attitude actif. Le moment cinétique résiduel
provoquera une lente dérive. L'amortissement magnétique (s'il existe) ou le gradient de gravité
n'assureront qu'une stabilisation passive.

**LABEL:** `STEP-5-CHECK`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Attendre 30 s et contrôler de nouveau
**Verify:** `eps.bus_voltage` (0x0105) — consigner la nouvelle valeur
**BRANCH:** `eps.bus_voltage > 25.0` -> GO `STEP-6` | NO-GO `STEP-5B` (timeout 60 s)

### Étape 5B : Dernier recours — mode EMERGENCY de l'OBC
**LABEL:** `STEP-5B`
**Note:** Atteinte uniquement lorsque tous les niveaux de délestage ont été appliqués et que le bus reste
sous 25.0 V.
**TC:** `OBC_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 50) — EMERGENCY
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Télémesure de servitude plateforme/OBDH
**Verify:** `obdh.mode == 2` (0x0300, timeout 15 s) — EMERGENCY
**Note:** Cette étape n'existait que sous forme de prose dans la ligne GO/NO-GO de l'étape 5. Exécutée à plat,
l'ancienne fiche l'aurait envoyée à CHAQUE exécution — y compris dans le cas courant
où le délestage de la seule charge utile suffisait à rétablir le bus.

### Étape 6 : Surveiller le rétablissement
**LABEL:** `STEP-6`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Surveiller la télémesure EPS toutes les 60 s
**Verify:** `eps.bus_voltage` (0x0105) — en hausse
**Verify:** `eps.bat_soc` (0x0101) — en hausse (surtout en phase éclairée)
**Verify:** `eps.power_gen` (0x0107) > 0 W au Soleil
**Verify:** `eps.bat_current` (0x0109) — positif (charge) au Soleil
**Action:** Poursuivre la surveillance jusqu'à ce que :
- `eps.bus_voltage` > 28.0 V ;
- `eps.bat_soc` > 40 %.
**Note:** Le rétablissement peut prendre plusieurs orbites selon la profondeur de décharge et
la puissance disponible du générateur solaire.
**GO/NO-GO:** Tension du bus > 28.0 V et SoC > 40 % — passer au rétablissement des charges.

### Étape 7 : Rétablir les charges dans l'ordre de priorité inverse
**Note:** Réactiver les charges une par une, en attendant 5 min entre chacune pour vérifier la stabilité.
Ne rétablir que ce qui a été délesté (à bord ou par cette fiche), et toujours réalimenter la LIGNE avant la
commande de mode de l'unité : ligne ouverte, toute commande de mode est refusée S1.8.
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19) — 1. Ligne des roues AOCS, si `eps.pl_aocs_wheels` (0x0117) = 0
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 1 en 5 s
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0) — DETUMBLE, seulement si `aocs.mode` (0x020F) = 0 : le SCAO est retombé sur OFF quand sa ligne s'est ouverte et ne redémarre pas seul ; il passe de lui-même en COARSE_SUN une fois les vitesses faibles
**GO/NO-GO:** Bus stable pendant 5 min avec les roues AOCS rétablies — rétablir la charge suivante
**TC:** `EPS_POWER_ON(line_index=2)` (Service 8, Subtype 1, func_id 19) — d'abord la ligne `ttc_tx`, si `eps.pl_ttc_tx` (0x0112) = 0 : ligne ouverte, `TTC_PA_ON` est refusé par un S1.8 « power line 'ttc_tx' is OFF » (la FDIR de bord l'ouvre lors d'un délestage profond)
**TC:** `TTC_PA_ON` (Service 8, Subtype 1, func_id 66) — 2. Émetteur TX : vérifier `ttc.pa_on` (0x0516) = 1
**GO/NO-GO:** Bus stable pendant 5 min avec l'émetteur rétabli — rétablir la charge suivante
**TC:** `EPS_POWER_ON(line_index=4)` (Service 8, Subtype 1, func_id 19) — d'abord la ligne `fpa_cooler`, si `eps.pl_fpa_cooler` (0x0114) = 0
**TC:** `FPA_COOLER(on=1)` (Service 8, Subtype 1, func_id 43) — 3. Refroidisseur du FPA : vérifier `tcs.cooler_fpa` (0x040C) = 1
**GO/NO-GO:** Bus stable pendant 5 min avec le refroidisseur du FPA rétabli — rétablir la charge suivante
**TC:** `EPS_POWER_ON(line_index=3)` (Service 8, Subtype 1, func_id 19) — d'abord la ligne `payload`, si `eps.pl_payload` (0x0113) = 0 : sinon la commande de mode est refusée par un S1.8 « power line 'payload' is OFF »
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) — 4. Charge utile en STANDBY : vérifier `payload.mode` = 1
**Verify:** Après chaque ajout de charge, confirmer que `eps.bus_voltage` (0x0105) reste > 27.5 V
et que `eps.bat_soc` (0x0101) reste > 35 %.
**GO/NO-GO:** Toutes les charges rétablies et bilan de puissance positif — procédure terminée.

## Critères de vérification
- [ ] `eps.uv_flag` (0x010E) = 0 (retombé)
- [ ] `eps.bus_voltage` (0x0105) > 28.0 V
- [ ] `eps.bat_soc` (0x0101) > 40 %
- [ ] Tous les sous-systèmes revenus dans leurs modes de fonctionnement nominaux
- [ ] Bilan de puissance positif (production > consommation) avec marge
- [ ] Aucune nouvelle sous-tension pendant au moins 2 orbites

## Cas de contingence
- Si la tension du bus descend sous 25.0 V après le délestage de toutes les charges : commander
  `OBC_SET_MODE(mode=2)` pour passer en mode EMERGENCY. Le satellite devrait passer de lui-même en configuration
  de puissance minimale.
- Si la tension du bus ne remonte pas après la sortie d'éclipse : suspecter une défaillance du générateur solaire.
  Contrôler `eps.sa_a_current` (0x0103) et `eps.sa_b_current` (0x0104). S'ils sont tous deux proches de
  zéro, passer à la procédure de dégradation du générateur solaire.
- Si le SoC de la batterie descend sous 10 % : risque de décharge profonde de la batterie et de dommages permanents.
  Commander immédiatement le mode EMERGENCY. Toutes les fonctions non essentielles seront désactivées
  par la FDIR de bord.
- Si les charges ne peuvent pas être rétablies sans déclencher de nouveau une sous-tension : réduire le
  bilan de puissance opérationnel. Fonctionner avec un rapport cyclique de charge utile réduit ou sans le refroidisseur
  du FPA. Consulter l'équipe de planification de mission.
- Si la sous-tension se reproduit dans les 2 orbites suivant le rétablissement : suspecter un déficit de puissance
  persistant. Réévaluer le bilan de puissance avec la dynamique du vol (dégradation du générateur,
  durée d'éclipse, biais d'attitude).

## Chemin de reprise — remise sous tension des charges délestées
Une fois le bus stabilisé par cette procédure et la cause première comprise, **tout sous-système dont les lignes d'alimentation ont été mises hors tension lors du délestage doit être remis en service dans l'ordre maîtrisé défini par LEOP-007 (mise sous tension séquentielle)**. Ne **pas** se contenter de réactiver les lignes au coup par coup : LEOP-007 impose le bon enchaînement sous-système→ligne→mode, l'espacement des courants d'appel, le préconditionnement thermique des réchauffeurs OBC/batterie et les exemptions set_mode AOCS/charge utile au verrou d'alimentation à deux niveaux des TC. Référence croisée : `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
