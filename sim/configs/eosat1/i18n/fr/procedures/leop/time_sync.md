# LEOP-006 : Synchronisation temporelle
**Sous-système :** OBDH / gestion du temps
**Phase :** LEOP
**Révision :** 3.0 --- refonte du déroulement 2026-08c. Cette fiche UNIQUE porte désormais toute la
logique LEOP « amorcer puis synchroniser », selon les deux voies : le réglage SOL (S9.1) comme
action immédiate, puis l'asservissement GPS (S8.1 func 80) dès que le récepteur --- alimenté dans
LEOP-007 --- dispose d'un point. L'étape `SET_TIME` en double qui figurait autrefois dans
LEOP-001 a été supprimée ; NOM-008 reste la fiche d'horloge des opérations courantes.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de LEOP-005 --- maintien solaire COARSE_SUN, image applicative
en cours d'exécution, horloge NON RÉGLÉE (`obdh.time_ref` 0x0A13 = 0, décompte depuis J2000), récepteur
GPS sur ON (équipement 0x020F, LEOP-007, étape 4) et en acquisition ; SID HK 12 pas encore
activé.

## Objet
Établir pour la première fois la référence de temps du satellite après la séparation.
Tant que cette fiche n'a pas été exécutée, l'horloge de l'OBC n'est **pas seulement imprécise --- elle n'a jamais
été réglée**. Le chargeur d'amorçage démarre l'horloge à CUC 0, qui correspond à l'époque de la mission
J2000 (2000-01-01T12:00:00 UTC), et `obdh.time_ref` (0x0A13) vaut 0 (NONE).
Chaque paquet de servitude, chaque événement et chaque enregistrement de TM stockée produit
avant cette fiche porte un horodatage de l'an 2000, et c'est un comportement
correct, pas une erreur de décodage.

Il en va de même après **chaque** redémarrage de l'OBC : le chargeur d'amorçage réinitialise l'horloge et
l'amorçage de l'image applicative ne la restaure pas ; un redémarrage pendant la LEOP impose donc
d'exécuter de nouveau cette fiche. Cette procédure établit la référence initiale dont dépendent
toutes les opérations datées, tous les journaux d'événements et toutes les données scientifiques ultérieurs.

## Prérequis
- [ ] LEOP-001 Première acquisition terminée --- liaison bidirectionnelle en bande S établie
      ET OBC sur l'image APPLICATION (`obdh.sw_image` 0x0311 = 1).
      `set_time` ne figure PAS sur la liste des fonctions autorisées par le chargeur d'amorçage OBDH
      (`obdh_basic._BOOTLOADER_ALLOWED` n'admet que les fonctions d'amorçage et de maintenance) ;
      l'étape 4 est donc rejetée d'emblée tant que le satellite est encore dans le
      chargeur d'amorçage.
- [ ] Liaison TTC verrouillée : `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Référence UTC sol disponible (NTP de strate 1 ou horloge asservie au GPS)
- [ ] OBC en mode SAFE ou NOMINAL : `obdh.mode` (0x0300) = 0 ou 1
- [ ] Aucune séquence de commandes datées chargée à bord (état post-séparation
      vierge). Toute date d'exécution envoyée avant le réglage de l'horloge a été calculée par rapport à une
      horloge indiquant l'an 2000 et ne se déclenchera pas comme prévu.
- [ ] Récepteur GPS alimenté (LEOP-007, étape 4) --- équipement `S2_AOCS_GPS_RECEIVER`
      0x020F sur ON. La voie B ci-dessous exige `aocs.gps_fix` (0x0274) >= 2 ; un démarrage à froid
      peut prendre jusqu'à 15 minutes, ce que la voie sol n'attend pas
- [ ] Le directeur de vol a autorisé la synchronisation temporelle

## Déroulement

### Étape 1 --- Vérifier l'état de l'OBC et la communication
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- demander les données de servitude OBDH
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- demander les données de servitude TT&C
**Verify:** `obdh.mode <= 1` (0x0300, timeout 5 s) --- 0 = NOMINAL ou 1 = SAFE, tous deux acceptables à ce stade
**Verify:** `obdh.cpu_load` (0x0302) < 80 %
**Verify:** page TT&C (sol) : `ttc.link_margin` (0x0503) > 3.0 dB
**Note:** Consigner `obdh.uptime` (0x0308) et `obdh.reboot_count` (0x030A). Un
temps de fonctionnement court avec un compteur de redémarrages incrémenté signifie que l'OBC a redémarré depuis la
séparation --- l'horloge est revenue à J2000 et cette fiche est exactement ce qu'il
faut.
**GO/NO-GO:** OBC réactif et liaison de communication saine.

### Étape 2 --- Lire l'horloge, sa référence et la distance oblique
**TC:** `REQUEST_TIME` (Service 9, Subtype 2) --- demander l'heure courante de l'OBC ; la réponse est une TM(9,2)
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- données de servitude TT&C, pour l'état de la liaison
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- données de servitude plateforme, pour le contrôle croisé de l'horloge
**Verify:** Rapport de temps TM(9,2) reçu sous 10 s
**Action:** Consigner le temps bord T_obc = `obdh.obc_time` (0x0309) +
`obdh.obc_time_fine` (0x0A12) / 65536, en **secondes CUC depuis J2000**
(2000-01-01T12:00:00 UTC). Après la séparation, avant toute synchronisation, s'attendre à une valeur
de quelques heures au plus --- l'horloge compte depuis la dernière réinitialisation du chargeur d'amorçage, et non
depuis le lancement.
**Action:** Consigner `obdh.time_ref` (0x0A13). S'attendre ici à **0 (NONE)** : jamais réglée
depuis la dernière réinitialisation du chargeur d'amorçage. 1 = GROUND, 2 = GPS (asservie), 3 =
HOLDOVER (était en GPS, point perdu).
**Action:** Consigner `obdh.time_since_sync_s` (0x0A14). S'attendre à 4294967295
(0xFFFFFFFF) = JAMAIS SYNCHRONISÉE. Toute autre valeur signifie que l'horloge a déjà été
réglée au cours de cette mission --- établir par qui avant de continuer.
**Action:** Consigner l'heure UTC sol au moment de la réception du rapport de temps sous le nom
T_ground, exprimée dans les mêmes secondes CUC depuis J2000.
**Action:** Lire le temps de propagation aller sur la page PUS, onglet S9 TIME
(« Temps de propagation aller (géométrie sol) ») : la distance oblique jusqu'à la station
en visibilité divisée par c, OWLT_ms = range_km / 299792.458 * 1000. S'attendre à 3-22 ms ;
le consigner, et noter qu'il est inférieur de deux ordres de grandeur au seuil d'acceptation de 1,0 s
de cette fiche.
**Note:** `REQUEST_TIME` est le mnémonique du catalogue (`tc_catalog.yaml`).
`TIME_REPORT_REQUEST` est un alias --- il est résolu à l'émission, mais un opérateur
qui le cherche dans le panneau de commande ne le trouvera pas.
**Note:** La distance oblique est un produit SOL : le MCS propage le TLE de la mission
jusqu'à la station en visibilité. Le satellite ne la transmet pas ---
`ttc.range_km` (0x0509) ne figure dans aucun SID HK --- elle se lit donc au sol : le réseau
de stations sol de la page TT&C affiche la distance et l'OWLT de la station en contact
(1000-2000 km pendant un passage).
**Note:** L'horloge de l'OBC est AUSSI transmise en continu sous la forme `obdh.obc_time`
(0x0309) dans le SID HK 4, demandé ci-dessus. Recouper la valeur TM(9,2) avec
celle-ci : les deux doivent concorder à la période de collecte du SID 4 près (8 s). Elles arrivent
par des voies différentes --- l'une par un rapport de temps explicite, l'autre par un échantillon
de servitude --- un désaccord signifie donc que le service de temps et l'échantillonneur de servitude
divergent sur l'horloge, ce qui est une panne différente d'une horloge
fausse.
**GO/NO-GO:** Rapport de temps TM(9,2) valide reçu, `obdh.time_ref` (0x0A13) lu,
OWLT consigné et 0x0309 concordant.

### Étape 3 --- Calculer l'écart de temps
**Action:** Calculer le décalage d'horloge :
  delta_t = T_obc - (T_ground - OWLT)
Un delta_t NÉGATIF d'environ l'âge de la mission est la signature attendue en LEOP : une
horloge non réglée comptant depuis J2000 alors que le sol lit la date réelle de la mission.
**Évaluer :** Consigner la valeur absolue et le signe de delta_t.
**Évaluer :** Si `obdh.time_ref` (0x0A13) = 0 (NONE) --- l'horloge n'a jamais été
réglée. delta_t correspondra au décalage complet depuis J2000 (des années). C'est le cas normal
en LEOP ; effectuer la correction.
**Évaluer :** Si |delta_t| < 1.0 s --- l'horloge est déjà exacte, ce qui
après la séparation signifie que quelqu'un l'a déjà réglée. Recouper avec
`obdh.time_ref` et `obdh.time_since_sync_s` avant de conclure qu'aucune correction n'est
nécessaire ; le contrôle de dérive de `STEP-6` reste applicable.
**Évaluer :** Si 1.0 s <= |delta_t| < 86400 s (24 heures) --- horloge réglée qui a
dérivé, ou synchronisation partielle. Effectuer la correction.
**Évaluer :** Si |delta_t| >= 86400 s avec `time_ref` = 1 (GROUND) --- horloge
qui A ÉTÉ réglée et qui est désormais décalée de plusieurs jours. Se mettre en attente (*Hold*) et consulter l'ingénieur OBDH avant
de corriger ; il ne s'agit pas d'une dérive ordinaire, qui est d'environ 12 ppm (~1 s/jour).
**GO/NO-GO:** delta_t expliqué par l'état de la référence de temps (NONE = jamais réglée, GROUND/HOLDOVER = dérive). Le directeur de vol approuve la correction.

### Étape 4 --- Envoyer la commande de mise à l'heure
**Action:** Calculer T_corrected = T_ground_at_send + OWLT + processing_delay
(typiquement 50 ms), en **secondes CUC depuis J2000**.
**Action:** Confirmer que T_corrected est rapporté à l'époque J2000. Un horodatage Unix serait ici
trop grand d'environ 9.5e8 s ; le satellite l'accepte et tous les horodatages
suivants sont faux d'une trentaine d'années.
**TC:** `SET_TIME(cuc_seconds=T_corrected)` (Service 9, Subtype 1) --- régler l'horloge de l'OBC
**Verify:** Télémesure d'acceptation de la commande (Service 1, Subtype 1) reçue sous 5 s
**Verify:** Aucun rejet de commande (Service 1, Subtype 2) reçu
**Note:** L'argument doit rester À L'INTÉRIEUR des accents graves. Écrit à l'extérieur,
l'extracteur produit une étape `SET_TIME` sans argument et le paquet émis contient
cuc_seconds = 0 --- une remise à zéro de l'époque, et non une synchronisation.
**Note:** La commande `SET_TIME` applique la nouvelle heure à la prochaine impulsion PPS
à bord.
**Note:** Le satellite émet l'événement **`OBC_TIME_SET` (0x030C)** qui porte le
saut SIGNÉ en secondes et la référence résultante, sous la forme
`OBC clock set by ground (S9,1): jump +831000000.000s, time_ref=GROUND`. Lors de la
première synchronisation en LEOP, ce saut représente tout le décalage depuis J2000 et sera un très
grand nombre ; c'est la lecture attendue, et c'est la mesure, par le satellite lui-même, de l'écart
de l'horloge.
**Note:** Si la commande est rejetée, vérifier d'abord `obdh.sw_image` (0x0311) --- un
`SET_TIME` envoyé alors que l'OBC est dans le chargeur d'amorçage est refusé avant l'amorçage.
**GO/NO-GO:** Commande de mise à l'heure acceptée par l'OBC.

### Étape 5 --- Vérifier l'exactitude du temps
**TC:** `REQUEST_TIME` (Service 9, Subtype 2) --- demander l'heure de l'OBC mise à jour
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- données de servitude plateforme, pour l'état de la référence
**Verify:** `obdh.time_ref == 1` (0x0A13, timeout 15 s) --- GROUND : le réglage a été appliqué et la référence est désormais un réglage sol
**Verify:** `obdh.mode == 0` (0x0300, timeout 10 s) --- l'OBC n'a pas été perturbé par le saut de temps
**Action:** Consigner le nouveau temps CUC bord sous le nom T_obc_new et calculer le
résidu :
  delta_residual = T_obc_new - (T_ground_verify - OWLT)
**Verify:** |delta_residual| < 1.0 s (seuil de précision initial en LEOP)
**Note:** `obdh.time_since_sync_s` (0x0A14) doit désormais afficher un petit nombre au lieu
de 4294967295. S'il indique toujours « jamais synchronisée », l'horloge n'a pas été réglée, quoi
qu'affiche 0x0309.
**Note:** En LEOP, une précision inférieure à la seconde suffit. `SET_TIME` ne transporte que des secondes
CUC entières ; une précision plus fine provient de l'asservissement GPS, et le seuil plus strict
de 0,1 s relève de NOM-008 en opérations nominales.
**GO/NO-GO:** Écart résiduel inférieur à 1.0 s. Synchronisation temporelle réussie.

### Étape 6 --- Valider la dérive de l'horloge
**LABEL:** `STEP-6`
**TC:** `REQUEST_TIME` (Service 9, Subtype 2) --- seconde demande de confirmation
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- second échantillon du SID 4
**Verify:** Rapport de temps reçu sous 10 s
**Action:** Comparer deux échantillons séparés par un intervalle sol connu :
  drift_ppm = ((T_obc_2 - T_obc_1) - (T_ground_2 - T_ground_1)) / interval * 1e6
**Verify:** Erreur de dérive de l'horloge < 100 ppm (seuil LEOP ; NOM-008 applique un seuil
plus strict en opérations nominales)
**Note:** S'attendre à environ 12 ppm (~1 s/jour) sur une unité saine, avec une dispersion de quelques ppm
d'une unité à l'autre. Une dérive proche de 500 ppm (~43 s/jour) est très au-delà de la spécification
de l'oscillateur : une panne d'oscillateur plutôt qu'un composant vieillissant.
**Note:** Une dérive mesurée sur un intervalle court est dominée par la résolution
d'échantillonnage : 12 ppm sur 60 s représentent 0,7 ms, bien en deçà de ce que deux échantillons du SID 4 peuvent
résoudre. Utiliser l'intervalle le plus long que permet le passage, ou reporter l'estimation de la dérive au
passage suivant et en suivre la tendance.
**Note:** Si l'horloge était asservie au GPS (`obdh.time_ref` 0x0A13 = 2), le contrôle de
dérive mesurerait la boucle d'asservissement plutôt que l'oscillateur, et n'aurait aucun sens.
Pendant la LEOP, la référence est normalement GROUND.

### Étape 6a --- VOIE B : asservissement temporel GPS (dès que le récepteur dispose d'un point)
**TC:** `HK_ENABLE(sid=12)` (Service 3, Subtype 5) --- données de servitude GPS_NAV, 8 s.
NON activé par défaut : sans cette commande, la solution PVT n'atteint jamais le
sol et LEOP-003 s'exécute à l'aveugle.
**Verify:** Le SID 12 périodique commence à être émis en l'espace d'une période de structure de 8 s
**Verify:** `aocs.gps_fix` (0x0274) >= 2 sous 900s --- point 3D (codage
0=aucun, 1=2D, 2=3D, 3=3D+vitesse ; la commande de synchronisation refuse en dessous de 2). Le TTFF à froid peut atteindre 15 minutes à compter de
la mise sous tension en LEOP-007 ; si le point n'est pas encore acquis, poursuivre le passage et envoyer
la synchronisation au contact suivant --- la référence sol de l'étape 4 porte la
mission entre-temps.
**TC:** `OBC_GPS_TIME_SYNC` (Service 8, Subtype 1, func_id 80)
**Verify:** Acceptation S1.1 + fin d'exécution S1.7 reçues sous 5s
**Verify:** `obdh.time_ref` (0x0A13) = 2 (GPS) sous 15s --- asservie ; 3
(HOLDOVER) est acceptable si le point se dégrade juste après la synchronisation, et signifie le
même réglage réussi, l'asservissement attendant le point suivant
**Verify:** `obdh.time_since_sync_s` (0x0A14) affiche une petite valeur
**Note:** L'ORDRE COMPTE : comme le réglage sol (étape 4) a déjà placé l'horloge
à moins d'une seconde du temps vrai, le saut GPS est ici de quelques millisecondes --- très en deçà du
saut de 5 secondes qui force l'AOCS en SAFE_BOOT (événement 0x020F, CTG-027). Exécuter
cette voie EN PREMIER sur une horloge jamais réglée ferait sauter tout le décalage depuis J2000
et réinitialiserait l'AOCS en pleine LEOP. Cet ordre est la raison d'être de cette fiche.
**Note:** Tant que `time_ref` = 2, l'horloge est asservie en continu et le
contrôle de dérive de l'étape 6 mesure la boucle d'asservissement, pas l'oscillateur --- consigner
la valeur de dérive mesurée AVANT cette étape.
**GO/NO-GO:** Horloge asservie au GPS (ou HOLDOVER avec une horloge réglée par le sol)

### Étape 7 --- Confirmer l'horodatage et consigner le résultat
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- confirmer l'état de l'OBDH après la synchronisation
**Verify:** `obdh.uptime` (0x0308) > 0 --- l'OBC n'a pas redémarré pendant la synchronisation
**Verify:** `obdh.time_ref` (0x0A13) dans {1, 2, 3} --- GROUND si la voie B a été
reportée, GPS/HOLDOVER une fois qu'elle a été exécutée
**Action:** Confirmer que les paquets de servitude portent désormais des horodatages plausibles à la date
de la mission dans l'en-tête secondaire PUS, et non des valeurs de l'an 2000.
**Action:** Consigner les éléments suivants dans le registre de synchronisation temporelle de la LEOP :
  - Écart avant correction : delta_t, avec `obdh.time_ref` et
    `obdh.time_since_sync_s` tels que lus avant la correction
  - Saut signalé par l'événement 0x030C
  - Résidu après correction : delta_residual
  - Correction appliquée : OUI / NON
  - Erreur de dérive d'horloge estimée (ppm) et intervalle de mesure
  - Temps de fonctionnement de l'OBC et compteur de redémarrages au moment de la synchronisation
  - Toute anomalie observée
**Note:** La TM stockée et les événements produits AVANT cette fiche conservent leur horodatage
de l'an 2000. Ils ne sont pas corrompus ; l'horloge de bord indiquait réellement cette valeur
lors de leur production. Noter l'heure de synchronisation dans le registre LEOP afin que les premières données puissent
être interprétées.

## Conduite à tenir hors nominal
- Si `REQUEST_TIME` (S9.2) n'est pas acquittée : vérifier l'intégrité de la liaison TTC. Renvoyer
  une fois. Toujours sans réponse : le service de gestion du temps de l'OBC n'est peut-être pas
  initialisé --- avec l'accord du FD, faire passer l'OBC par SAFE puis revenir :
  `OBC_SET_MODE(mode=1)` (SAFE) puis `OBC_SET_MODE(mode=0)` (NOMINAL --- toujours
  rétablir ; ne jamais quitter la fiche avec un OBC en SAFE) et réessayer. Noter qu'un redémarrage
  COMPLET (func 52) réinitialise de nouveau l'horloge : un redémarrage impose donc de réexécuter cette
  fiche ensuite.
- Si `obdh.time_ref` (0x0A13) indique de nouveau 0 (NONE) après une synchronisation réussie : l'OBC
  a redémarré. Contrôler `obdh.uptime` (0x0308) et `obdh.reboot_count` (0x030A).
  Le chargeur d'amorçage remet l'horloge à J2000 à chaque réinitialisation et l'amorçage de
  l'image applicative ne la restaure pas --- un redémarrage implique toujours une resynchronisation.
- Si `SET_TIME` est rejetée : vérifier d'abord `obdh.sw_image` (0x0311) --- la commande
  est refusée tant que l'OBC est dans le chargeur d'amorçage. Sinon, contrôler les bornes de
  validation à bord et consulter l'ingénieur OBDH.
- Si |delta_t| n'est pas expliqué par la référence de temps : la cause habituelle est une erreur d'époque côté
  sol. L'époque de la mission est J2000
  (2000-01-01T12:00:00 UTC), déclarée une seule fois dans `mission.yaml` sous `time_epoch` et
  utilisée par tout le segment sol. Une valeur à l'époque Unix diffère d'environ
  9,46e8 s ; une valeur à l'époque GPS d'environ 6,3e8 s.
- Si |delta_residual| > 1.0 s après la correction : la correction n'a peut-être pas
  été appliquée au front PPS attendu. Confirmer que `obdh.time_since_sync_s`
  (0x0A14) est reparti de zéro, puis renvoyer `SET_TIME` avec un T_corrected mis à jour.
- Si l'erreur de dérive de l'horloge dépasse 100 ppm : l'oscillateur de l'OBC est peut-être dégradé ou fonctionne
  hors de son domaine de qualification thermique. Vérifier que `obdh.temp` (0x0301) est compris entre -20 C et
  +60 C, programmer des synchronisations temporelles plus fréquentes et le signaler pour investigation pendant la
  recette en orbite.
- Si le satellite est asservi au GPS plus tard dans la mission
  (`obdh.time_ref` = 2), l'horloge conserve le temps vrai sans dérive ; la perte du point
  la fait passer à 3 (HOLDOVER), déclenche l'événement `OBC_TIME_REF_LOST` (0x030E), et la dérive
  reprend. La synchronisation GPS et ses effets de bord sur l'AOCS relèvent de CTG-027 --- noter
  qu'un saut de synchronisation GPS supérieur à 5 s force l'AOCS en SAFE_BOOT (événement 0x020F).

## État de sortie
- Horloge réglée à 1,0 s près de l'UTC ; `obdh.time_ref` (0x0A13) = 2 (GPS) --- ou 1
  (GROUND) si la voie B a été reportée au passage suivant, ou 3 (HOLDOVER) si le point
  s'est dégradé après la synchronisation
- SID HK 12 (GPS_NAV) activé et émis --- l'état d'entrée de LEOP-003
- Récepteur GPS toujours sur ON avec l'état de point tel que lu ; mode AOCS INCHANGÉ
  (COARSE_SUN) --- l'ordre « sol d'abord » garantit l'absence de bascule en SAFE_BOOT
- Aucun autre état modifié par cette fiche

## Postconditions
- [ ] Horloge de bord synchronisée sur l'UTC à 1,0 s près (seuil de précision LEOP)
- [ ] `obdh.time_ref` (0x0A13) dispose d'une référence (1 GROUND / 2 GPS / 3 HOLDOVER)
- [ ] `obdh.time_since_sync_s` (0x0A14) affiche une petite valeur, et non plus 4294967295
- [ ] Dérive de l'horloge vérifiée < 100 ppm (mesurée AVANT l'asservissement GPS), avec l'intervalle de mesure consigné
- [ ] Entrée du journal de synchronisation temporelle complétée pour le registre LEOP
- [ ] Les paquets de télémesure de servitude portent des horodatages CUC à la date de la mission
- [ ] Mode de l'OBC inchangé et aucun redémarrage pendant la synchronisation
- [ ] OWLT consigné (page PUS, S9 TIME)
- [ ] `obdh.obc_time` (0x0309) concorde avec le rapport TM(9,2)

**PROCÉDURE SUIVANTE :** LEOP-003 (Restitution d'orbite initiale --- clôt la LEOP par la déclaration
de phase 5)

---
*AIG --- contenu généré par intelligence artificielle*
*Référence : https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/*
