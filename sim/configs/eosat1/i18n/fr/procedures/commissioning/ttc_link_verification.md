# COM-006 : Vérification de la liaison TTC
**Sous-système :** TT&C
**Phase :** COMMISSIONING
**Révision :** 2.0 --- 2026-08c : nommage des paliers de débit (le palier à 1 kbit/s est SAFE,
ex-BEACON --- « balise » désigne désormais toujours l'antenne fouet UHF) ; le contrôle d'élévation du palier HIGH
est réécrit --- il n'existe PLUS de verrou bord sur l'élévation, la règle
des 10° relève de la politique d'autorisation SOL ; états d'entrée et de sortie déclarés.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-005 --- AOCS en NOMINAL commandé, phase 5,
liaison descendante en LOW, antenne REPLIÉE (cette fiche la déploie), `ttc_tx` éventuellement
retombé du fait du maintien automatique de l'émetteur pendant les fenêtres d'observation calmes de COM-005
(l'étape 0 le rétablit --- ne rien supposer).

## Objet
Vérifier les performances de la liaison TT&C en bande S avec les transpondeurs principal et redondant.
Mesurer la puissance du signal reçu (RSSI) et la marge de liaison à différents angles d'élévation, et
confirmer la fiabilité des échanges de commandes et de télémesure avec les deux stations sol (Iqaluit et
Troll). Valider les prédictions du bilan de liaison par rapport aux valeurs mesurées.

## Marges de liaison de référence (remesurées le 2026-07-29)

C'est dans cette fiche que les références du bilan de liaison de la mission sont *établies* ; les valeurs
qu'elle vérifie doivent donc être celles que le modèle de vol produit réellement. Elles ont été
remesurées avec `python tools/link_budget_ladder.py`, qui pilote la même fonction
`TTCBasicModel.link_margin_for` que celle du simulateur, sur la base du fichier livré
`subsystems/ttc.yaml` (PIRE 10 dBW + 3 dBi, atmosphère 0,5 / polarisation 0,3 / implémentation 2,0 dB, G/T
dégradé de −1,5 dB sous 10° et de −0,5 dB sous 30°, exigence non codée de 9,6 dB diminuée
du gain de codage du palier).

**Marge de liaison (dB) par palier, station et élévation :**

| Station | G/T | SAFE à 5° | LOW à 5° | HIGH à 5° | SAFE à 30° | LOW à 30° | HIGH à 30° | SAFE à 90° | LOW à 90° | HIGH à 90° |
|---|---|---|---|---|---|---|---|---|---|---|
| Svalbard | 21,5 | 59,3 | 47,2 | 36,7 | 70,6 | 58,5 | 48,0 | 75,8 | 63,8 | 53,3 |
| Inuvik | 22,0 | 59,8 | 47,7 | 37,2 | 71,1 | 59,0 | 48,5 | 76,3 | 64,3 | 53,8 |
| Iqaluit | 20,0 | 57,8 | 45,7 | 35,2 | 69,1 | 57,0 | 46,5 | 74,3 | 62,3 | 51,8 |
| O'Higgins | 20,0 | 57,8 | 45,7 | 35,2 | 69,1 | 57,0 | 46,5 | 74,3 | 62,3 | 51,8 |
| Troll | 18,5 | 56,3 | 44,2 | 33,7 | 67,6 | 55,5 | 45,0 | 72,8 | 60,8 | 50,3 |

**Cas le plus défavorable de toute la matrice : HIGH à Troll, 5° = 33,7 dB.** Chaque échelon boucle
avec des dizaines de dB à chaque station et dans chaque géométrie — cette liaison n'est pas limitée en puissance.
Deux conséquences pour cette fiche :

* Les seuils GO/NO-GO ci-dessous (3 dB, 6 dB) sont des seuils de *cohérence*. Une mesure
  qui s'en approche signifie qu'un problème affecte le modèle, l'attitude ou la station
  sol — et non que la géométrie est marginale.
* Le **verrou de 10° sur le palier HIGH est un verrou de politique, pas un verrou de marge.** HIGH boucle
  avec 33,7 dB à 5°. Il est refusé sous 10° parce que le vidage en masse est une activité planifiée
  et méritée, et parce que la poursuite, la vitesse de variation du Doppler et les trajets multiples à faible élévation font
  d'un vidage QPSK à 64 kBd un pari risqué — et non parce que la liaison ne boucle pas.

Les échelons sont séparés exactement de ce qu'indique le bilan : de SAFE à LOW, −12,04 dB
(débit ×16) ; de LOW à HIGH, −10,53 dB (débit ×8 = −9,03 dB, plus conv+RS 7,5 dB -> RS
6,0 dB = −1,5 dB de codage). Tout jeu de mesures ne présentant pas ces deux marches
révèle une erreur de modélisation, et non un problème de liaison.

## Prérequis
- [ ] COM-001 à COM-003 terminées
- [ ] OBC en mode NOMINAL
- [ ] Attitude du satellite stable en COARSE_SUN (`aocs.mode` 0x020F = 3) ou
      NOMINAL (4). Les codes de mode sont définis dans
      `configs/eosat1/aocs/aocs_mode_codes.yaml` : 0 OFF, 1 SAFE_BOOT,
      2 DETUMBLE, 3 COARSE_SUN, 4 NOMINAL, 5 FINE_POINT, 6 SLEW, 7 DESAT,
      8 ECLIPSE, 9 INERTIAL.
- [ ] Passages programmés sur au moins deux stations sol
- [ ] Transpondeur principal actuellement actif
- [ ] Liaison bidirectionnelle en bande S active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] OBC sur l'image APPLICATION (`obdh.sw_image` 0x0311 = 1). C'est l'amorçage de
      l'application qui LÈVE l'inhibition de l'amplificateur de puissance (PA) bande S imposée par le chargeur d'amorçage ;
      jusque-là, la balise UHF est la seule liaison descendante et l'étape 0 ci-dessous ne peut pas
      être vérifiée.

## Déroulement

### Étape 0 — Configurer la chaîne bande S pour la mesure
**Note:** Cette étape n'existait pas, et sans elle l'étape 2a ne pouvait pas réussir.
`TTCBasicModel._tier_refusal` conditionne l'échelle de débits à quatre éléments que cette fiche
n'établissait jamais : la ligne d'alimentation EPS `ttc_tx`, le PA, une antenne DÉPLOYÉE
(`requires_antenna` vaut true pour HIGH ; LOW boucle sur le patch replié), et la désactivation de `beacon_mode`
— tant que le mode balise est verrouillé, les DEUX paliers opérationnels sont refusés avec
l'erreur S1.8 `0x0007`, « TM rate is forced to the beacon tier in beacon mode ».
Le mode balise survit à l'amorçage de l'application ; un satellite peut donc arriver à cette
fiche encore verrouillé.
**TC:** `EPS_POWER_ON(line_index=2)` (Service 8, Subtype 1, func_id 19) — la ligne `ttc_tx`
**TC:** `TTC_PA_ON` (Service 8, Subtype 1, func_id 66) — amplificateur de puissance bande S
**TC:** `TTC_SET_BEACON_MODE(on=0)` (Service 8, Subtype 1, func_id 70) — lever le palier balise forcé
**TC:** `TTC_DEPLOY_ANTENNA` (Service 8, Subtype 1, func_id 69) — déploiement de l'antenne bande S
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — données de servitude TT&C
**Verify:** `eps.pl_ttc_tx == 1` (0x0112, timeout 10 s) — ligne de l'émetteur alimentée
**Verify:** `ttc.pa_on == 1` (0x0516, timeout 10 s) — PA en marche
**Verify:** `ttc.beacon_mode == 0` (0x0521, timeout 10 s) — aucun palier forcé
**Verify:** `ttc.antenna_deployed == 1` (0x0520, timeout 30 s) — antenne déployée
**Verify:** `ttc.tx_active == 1` (0x0525, timeout 10 s) — la chaîne principale bande S
émet réellement. C'est le paramètre de verrou ajouté en phase 3 ; s'il vaut 0,
`ttc.tx_gate_status` (0x052B) indique laquelle des quatre autorisations manque
(bit0 PA, bit1 ligne `ttc_tx`, bit2 station en visibilité, bit6 antenne).
**Note:** L'émetteur de balise UHF est une radio DISTINCTE sur la ligne non commutable
`ttc_rx` et n'est pas touché par cette fiche. `ttc.beacon_active` (0x0527) reste
à 1 tout du long, ce qui explique que le SID HK 11 continue d'arriver même si la chaîne bande S est
mal configurée. Ne pas confondre `ttc.beacon_mode` (0x0521, le palier TM forcé,
désactivé ci-dessus) avec `ttc.beacon_tx_on` (0x0526, l'émetteur UHF).
**GO/NO-GO:** Chaîne bande S configurée, antenne déployée, aucun palier forcé

### Étape 1 — Performances de référence du transpondeur principal
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27)
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) sous 10s
**Verify:** `ttc.rssi` (0x0502) > -100 dBm sous 10s
**Verify:** `ttc.link_margin` (0x0503) > 6.0 dB sous 10s
**Action:** Consigner les valeurs à l'angle d'élévation actuel. Noter la station sol et la configuration d'antenne.
**GO/NO-GO:** Liaison du transpondeur principal nominale

### Étape 2 — Mesurer le profil RSSI en fonction de l'élévation
**Action:** Pendant le passage station sol, demander les HK TT&C à faible (10°), moyenne (30°) et forte (60° et plus) élévation afin de caractériser les performances de la liaison.
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — données de servitude TT&C à ~10° d'élévation
**Verify:** `ttc.rssi` (0x0502) > -108 dBm (faible élévation) sous 10s
**Verify:** `ttc.link_margin` (0x0503) > 3.0 dB (minimum à faible élévation) sous 10s
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — données de servitude TT&C à ~30° d'élévation
**Verify:** `ttc.rssi` (0x0502) > -100 dBm (élévation moyenne) sous 10s
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — données de servitude TT&C à ~60° d'élévation
**Verify:** `ttc.rssi` (0x0502) > -95 dBm (forte élévation) sous 10s
**GO/NO-GO:** Profil RSSI cohérent avec la prédiction du bilan de liaison (+/- 3 dB)

### Étape 2a — Mesurer la référence de chaque palier de l'échelle de débits TM
**Action:** À une élévation stable supérieure à 30°, parcourir l'échelle et consigner la marge à
chaque palier. C'est cette mesure qui établit les références de la mission figurant dans le tableau
ci-dessus.
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) — LOW, 16 kbit/s
**Verify:** `ttc.tm_data_rate` (0x0506) = 16000 bps et `ttc.tm_tier` (0x0539) = 1
**Verify:** `ttc.link_margin` (0x0503) — consigner ; 55-59 dB attendus à 30 deg
**TC:** `TTC_SET_DOWNLINK_MODE(on=1)` (Service 8, Subtype 1, func_id 79)
**Verify:** `ttc.downlink_mode` (0x053C) = 1
**TC:** `TTC_SET_DATA_RATE(rate=1)` (Service 8, Subtype 1, func_id 65) — HIGH, 128 kbit/s
**Verify:** `ttc.tm_data_rate` (0x0506) = 128000 bps et `ttc.tm_tier` (0x0539) = 2
**Verify:** `ttc.tm_symbol_rate` (0x053B) = 64000 Bd (le passage en QPSK est visible sur
l'analyseur de spectre de la station sol : même débit d'information, moitié de la bande occupée)
**Verify:** `ttc.link_margin` (0x0503) — consigner ; 45-48 dB attendus à 30 deg
**Action:** Calculer la marche : marge(LOW) - marge(HIGH). Elle doit valoir 10,5 +/- 0,5 dB.
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) — redescendre en LOW
**TC:** `TTC_SET_DOWNLINK_MODE(on=0)` (Service 8, Subtype 1, func_id 79) — libérer le mode DOWNLINK
**Verify:** `ttc.tm_data_rate == 16000` (0x0506, timeout 10 s)
**Verify:** `ttc.downlink_mode == 0` (0x053C, timeout 10 s)
**Note:** La libération figurait auparavant en prose dans l'annotation `**TC:**` de la ligne
précédente ; l'extracteur produisait donc une seule commande là où il en faut deux — alors que
les postconditions de cette fiche exigent `downlink_mode` = 0. Une fiche qui laisse le mode
DOWNLINK verrouillé transmet à l'équipe suivante un satellite qui acceptera un palier HIGH
qu'elle n'a pas demandé.
**Note:** Le palier SAFE (1 kbit/s, ex-BEACON) ne peut pas être mesuré ici — il n'est pas
sélectionnable par la func 65 dans le logiciel nominal. Sa référence provient du passage de
première acquisition de la LEOP (LEOP-001).
**GO/NO-GO:** Les deux paliers opérationnels mesurés, et la marche entre eux vaut 10.5 +/- 0.5 dB

### Étape 2b — Mettre en œuvre la politique d'autorisation SOL sur HIGH (aucun verrou bord)
**Action:** Il n'existe PLUS de verrou bord sur l'élévation (2026-08c) : un satellite réel
ne connaît pas son élévation vue d'une station ; le logiciel de vol ne refuse donc ni ne
rétrograde HIGH en fonction de l'élévation. La règle des 10° relève de la politique
SOL — le MCS avertit d'après sa propre géométrie de contact lorsque HIGH est
commandé sous 10° (autorisation forcée : l'opérateur doit confirmer explicitement
malgré l'avertissement), et le planificateur ne programme les vidages en HIGH qu'au-dessus de ce seuil.
**Action:** Lorsque le passage redescend sous 10°, tenter d'armer HIGH dans le panneau de commande
du MCS SANS confirmer l'autorisation forcée.
**Verify:** Le MCS lève son avertissement de faible élévation et la commande n'est PAS
libérée sans la confirmation explicite ; aucune télécommande n'atteint le satellite.
**Note:** Les verrous BORD sur HIGH sont exactement : antenne déployée + mode DOWNLINK
activé + verrou du mode balise levé. Si les trois sont satisfaits, le satellite
ACCEPTERA un HIGH à faible élévation — et la physique se fera sentir honnêtement à travers
l'affaiblissement atmosphérique en cosécante, la dégradation du G/T et le TEB observé au sol.
Consigner la mise en œuvre de la politique (texte de l'avertissement, décision de l'opérateur) dans le rapport
de bilan de liaison.
**GO/NO-GO:** Politique d'autorisation sol démontrée ; liaison toujours en LOW

### Étape 3 — Basculer sur le transpondeur redondant
**TC:** `TTC_SWITCH_REDUNDANT` (Service 8, Subtype 1, func_id 64)
**Note:** Annoté `Service 11, Subtype 2` jusqu'en 2026-08b. Le service 11 est
la programmation de TC datées ; la sélection de transpondeur est la fonction S8 func 64.
**Action:** Attendre le verrouillage du transpondeur redondant. La station sol peut nécessiter une brève réacquisition.
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) sous 60s
**Verify:** `ttc.rssi` (0x0502) > -100 dBm sous 60s
**GO/NO-GO:** Transpondeur redondant opérationnel et verrouillé

### Étape 4 — Contrôle des performances du transpondeur redondant
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27)
**Verify:** `ttc.link_margin` (0x0503) > 6.0 dB sous 10s
**Action:** Comparer le RSSI et la marge de liaison du transpondeur redondant à ceux du principal à élévation similaire. Les valeurs doivent être à 2 dB près de celles du principal.
**Verify:** |RSSI_redundant - RSSI_primary| < 2.0 dB
**GO/NO-GO:** Performances du transpondeur redondant comparables à celles du principal

### Étape 5 — Rétablir le transpondeur principal
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1, func_id 63)
**Note:** Annoté `Service 11, Subtype 1` jusqu'en 2026-08b — voir l'étape 3.
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) sous 60s
**Verify:** `ttc.rssi` (0x0502) > -100 dBm sous 10s
**GO/NO-GO:** Transpondeur principal rétabli et verrouillé

### Étape 6 — Essai de débit de commandes
**TC:** `GET_PARAM(param_id=0x0105)` (Service 20, Subtype 3) — envoyer une salve de commandes successives pour vérifier la cadence de traitement des TC et le temps de réponse en TM.
**TC:** `GET_PARAM(param_id=0x0105)` à `GET_PARAM(param_id=0x010A)` (Service 20, Subtype 3) — 6 demandes rapides
**Verify:** Les 6 réponses reçues sous 30s
**TC:** `GET_PARAM(param_id=0x0306)` (Service 20, Subtype 3) — `obdh.tc_rej_count`
**Verify:** `obdh.tc_rej_count` (0x0306) inchangé pendant la salve. (Cette ligne lisait
0x0311, c'est-à-dire `obdh.sw_image` — l'image en cours d'exécution, et non un compteur de rejets.)
**GO/NO-GO:** Débit de commandes nominal

### Étape 7 — Vérification multistation (passages ultérieurs)
**Action:** Programmer des contrôles de liaison identiques (étapes 1-2) lors des passages au-dessus des autres stations sol. Consigner le RSSI et la marge de liaison de chacune.
- Iqaluit (63,7° N) : station polaire nord principale — 2 à 4 passages/jour attendus
- Troll (72,0° S) : couverture polaire sud — 2 à 4 passages/jour attendus
**Verify:** Marge de liaison > 3 dB à 10 deg d'élévation depuis chaque station
**GO/NO-GO:** Toutes les stations sol vérifiées (peut s'étendre sur plusieurs orbites)

### Étape 8 — Établir le rapport de bilan de liaison
**Action:** Tabuler le RSSI et la marge de liaison mesurés en fonction de l'élévation **et du palier
de débit** pour chaque station. Les comparer au tableau de référence figurant en tête de cette fiche
(le régénérer avec `python tools/link_budget_ladder.py` si la configuration RF a
changé). Documenter tout écart. Établir l'angle d'élévation opérationnel minimal
de chaque station, et confirmer que l'avertissement du MCS à 10° sur le palier HIGH se déclenche à chacune (une règle
sol : le satellite ne refuse pas HIGH en fonction de l'élévation).
**GO/NO-GO:** Vérification du bilan de liaison terminée

### Étape 9 — Mettre la liaison en configuration sûre
**Note:** Cette étape n'existait pas. La fiche laissait le satellite dans l'état
où l'analyse de l'étape 8 l'avait trouvé, alors que ses propres postconditions affirmaient
LOW et `downlink_mode` = 0. Une configuration qu'une fiche affirme mais ne commande jamais est
une configuration dont l'équipe suivante hérite par chance.
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) — LOW est le palier courant
**TC:** `TTC_SET_DOWNLINK_MODE(on=0)` (Service 8, Subtype 1, func_id 79) — mode DOWNLINK libéré
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1, func_id 63) — transpondeur principal pour les opérations nominales
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — données de servitude TT&C
**Verify:** `ttc.tm_tier == 1` (0x0539, timeout 10 s) — le palier ACTIF est LOW
**Verify:** `ttc.tm_tier_cmd == 1` (0x053A, timeout 10 s) — et le palier COMMANDÉ concorde
**Verify:** `ttc.downlink_mode == 0` (0x053C, timeout 10 s)
**Verify:** `ttc.beacon_mode == 0` (0x0521, timeout 10 s) — pas de nouveau verrouillage
**Verify:** `ttc.antenna_deployed == 1` (0x0520, timeout 10 s) — le déploiement est irréversible et demeure
**Verify:** `ttc.pa_on == 1` (0x0516, timeout 10 s) — le PA reste sur ON pour les opérations nominales
**Note:** L'antenne n'est PAS repliée et le PA n'est PAS éteint. Ces deux choix sont
délibérés : le déploiement par fil chaud est irréversible, et une fiche de recette en orbite qui
se terminerait en rendant l'émetteur muet transmettrait au passage suivant un satellite réduit à
la seule balise.
**GO/NO-GO:** Liaison laissée en LOW sur le transpondeur principal, mode DOWNLINK libéré

## Conduite à tenir hors nominal
- Si le transpondeur redondant ne se verrouille pas : attendre jusqu'à 120s. À défaut de verrouillage, revenir sur le principal via `TTC_SWITCH_PRIMARY`. Consigner le transpondeur redondant comme anormal. Poursuivre la recette en orbite sur le principal — programmer une investigation du transpondeur.
- Si la marge de liaison < 3 dB à toute élévation > 10 deg : contrôler l'attitude du satellite — un dépointage réduit le gain d'antenne. Vérifier la poursuite de l'antenne de la station sol. Si la marge reste faible, examiner le diagramme de l'antenne de bord.
- Si le RSSI s'écarte de la prédiction de plus de 5 dB : rechercher des interférences à la station sol. Vérifier la puissance de sortie du transpondeur via `GET_PARAM(param_id=0x050D)` — `ttc.tx_fwd_power`
  en dBm — et la PIRE en temps réel dans `ttc.eirp_dbw` (0x052C). (Cette fiche lisait 0x0510,
  c'est-à-dire `ttc.carrier_lock`, un indicateur 0/1 : un opérateur qui cherchait une « faible puissance
  de sortie » lisait un booléen.) Si la puissance incidente vaut 0, contrôler `ttc.tx_active`
  (0x0525) et `ttc.tx_gate_status` (0x052B) avant de suspecter le matériel.
- Si une TC est rejetée pendant l'essai de débit : réduire la cadence des commandes. Rechercher des erreurs d'authentification ou de compteur de séquence. Vérifier le format des paquets TC.
- Si une station sol ne parvient pas à se verrouiller : vérifier la configuration de fréquence de la station. Contrôler l'exactitude du TLE utilisé pour la prédiction des passages. Tenter le passage suivant. En cas de persistance, examiner les problèmes propres à la station.

## Postconditions
- [ ] Transpondeur principal vérifié — RSSI et marge de liaison nominaux
- [ ] Transpondeur redondant vérifié — performances comparables à celles du principal
- [ ] Profil RSSI en fonction de l'élévation caractérisé
- [ ] Marge de liaison mesurée en LOW et en HIGH, et marche de 10,5 dB entre paliers confirmée
- [ ] Règle sol des 10° du palier HIGH vérifiée : le MCS avertit sous 10° (le satellite ne refuse pas HIGH en fonction de l'élévation)
- [ ] Satellite laissé en LOW avec `ttc.downlink_mode` (0x053C) = 0 — COMMANDÉ par
      l'étape 9, et non simplement supposé
- [ ] `ttc.antenna_deployed` (0x0520) = 1 et `ttc.beacon_mode` (0x0521) = 0
- [ ] `ttc.tx_active` (0x0525) = 1 pendant le contact, `ttc.tx_gate_status` (0x052B) = 0xFF
- [ ] Débit de commandes nominal
- [ ] Vérification multistation effectuée (ou programmée)
- [ ] Rapport de bilan de liaison établi
- [ ] Transpondeur principal actif pour les opérations nominales

## État de sortie
- Transpondeur principal actif ; liaison descendante en LOW (`ttc.tm_tier` 0x0539 = 1) ;
  mode DOWNLINK libéré (`ttc.downlink_mode` 0x053C = 0)
- Antenne DÉPLOYÉE (irréversible) — désormais, HIGH est disponible pour toute fiche
  qui prend le mode DOWNLINK ; ligne `ttc_tx` sous tension avec le maintien automatique de l'émetteur actif
- Aucun état AOCS, OBC, charge utile ou réchauffeur touché

**PROCÉDURE SUIVANTE :** COM-007 (Vérification de l'OBDH)
