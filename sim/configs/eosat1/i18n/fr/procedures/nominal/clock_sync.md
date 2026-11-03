# NOM-008 : Synchronisation de l'horloge
**Sous-système :** OBDH
**Phase :** NOMINAL
**Révision :** 2.0
**Approuvé par :** directeur des opérations de vol

## Objet
Mesurer le décalage entre l'horloge de bord et l'UTC sol (temps de simulation), et le corriger
par télécommande sol lorsqu'il dépasse la tolérance. L'OBC est cadencé par un TCXO
libre dont la dérive nominale est d'environ **12 ppm --- soit à peu près 1 seconde par jour** ---, de sorte
qu'une horloge laissée à elle-même dérive de façon régulière et prévisible. La précision du temps importe pour
la géolocalisation des images, pour corréler les événements entre sous-systèmes et surtout pour
les **télécommandes datées S11**, qui se déclenchent sur l'horloge *de bord* : une horloge en
avance de 40 s exécute le plan envoyé 40 s trop tôt en temps mission.

Cette fiche corrige une horloge **référencée GROUND**. Si `obdh.time_ref` (0x0A13)
vaut 2 (GPS), l'horloge est asservie au GPS et tient le temps vrai sans dérive ---
il n'y a rien à corriger, et un décalage apparent dans cet état est une panne,
pas une dérive (voir Conduite à tenir hors nominal). La synchronisation GPS elle-même et ses effets
de bord sur l'AOCS sont traités par CTG-027.

## Prérequis
- [ ] NOM-001 Ouverture de passage achevée avec une déclaration tout GO
- [ ] Liaison TTC établie : `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] OBC exécutant l'image APPLICATION : `obdh.sw_image` (0x0311) = 1.
      `set_time` ne figure pas dans la liste d'autorisation du chargeur d'amorçage OBDH ; l'étape 4 est donc rejetée
      d'emblée tant que le satellite est sous chargeur d'amorçage.
- [ ] Référence de temps sol disponible (strate 1 ou asservie au GPS). Dans le
      simulateur, cette référence est le **temps de simulation**, et non l'horloge de votre poste --- l'horloge du MCS
      est calée sur le simulateur et constitue la bonne référence.
- [ ] Aucune séquence S11 datée ne doit s'exécuter pendant la fenêtre de mise à jour : un
      saut de temps décale toutes les dates enregistrées par rapport au temps mission
- [ ] Aucune séance de prise de vue en cours : `payload.mode` (0x0600) != 2

## Déroulement

### Étape 1 --- Lire l'horloge de bord et sa référence de temps
**LABEL:** `STEP-1`
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- données de servitude plateforme/OBDH : l'horloge, sa référence et le temps écoulé depuis la synchronisation
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- données de servitude TT&C, pour la distance oblique
**TC:** `REQUEST_TIME` (Service 9, Subtype 2) --- rapport de temps TM(9,2) explicite
**Verify:** `obdh.mode == 0` (0x0300, timeout 10 s) --- NOMINAL
**Note:** Consigner le temps bord T_obc = `obdh.obc_time` (0x0309) +
`obdh.obc_time_fine` (0x0A12) / 65536. 0x0309 est la seconde CUC GROSSIÈRE et
0x0A12 la fraction de seconde en unités de 1/65536 s (~15,26 µs). Les deux sont des **secondes CUC
depuis J2000** (2000-01-01T12:00:00 UTC), jamais un horodatage Unix.
**Note:** Consigner `obdh.time_ref` (0x0A13) : 0 = NONE (jamais réglée depuis la dernière
réinitialisation du chargeur d'amorçage --- l'horloge est encore proche de J2000), 1 = GROUND, 2 = GPS
(asservie, sans dérive), 3 = HOLDOVER (était GPS, point perdu, dérive de nouveau).
**Note:** Consigner `obdh.time_since_sync_s` (0x0A14) --- secondes bord écoulées depuis la
dernière synchronisation réussie. La valeur sature au lieu de repasser à zéro ; 4294967295
(0xFFFFFFFF) signifie NEVER SYNCED (jamais synchronisée). La limite sol jaune est à 12 h.
**Note:** Consigner l'UTC sol à l'instant de réception du rapport de temps sous le nom
T_ground, exprimé dans les mêmes secondes CUC depuis J2000.
**Note:** Cette fiche consignait auparavant `obdh.uptime` (0x0308) à la place. L'uptime compte les
secondes depuis l'AMORÇAGE, et non depuis l'époque de référence : un écart calculé à partir de lui revient à soustraire un horodatage UTC
à l'âge du satellite, et aurait déclaré anormale toute horloge
saine. L'uptime reste utile comme indicateur de redémarrage et comme corroboration
de la cadence --- jamais comme époque de référence.
**Note:** Calculer le temps de propagation aller à partir de `ttc.range_km` (0x0509) dans le
rapport SID 6 : OWLT_ms = range_km / 299792.458 * 1000, soit **3–22 ms** sur
cette orbite, négligeable devant le seuil de 1 s.
**Note:** Recouper le rapport TM(9,2) avec 0x0309. Ils arrivent par des
voies différentes --- une réponse du service de temps et un échantillon de servitude ---, de sorte qu'un
désaccord supérieur à l'intervalle de collecte du SID 4 (8 s) signifie que ces deux sources
divergent sur l'horloge, ce qui est une panne différente d'une horloge
fausse.

### Étape 2 --- Évaluer le décalage par rapport à la dérive attendue
**Action:** Calculer le décalage d'horloge :
  delta_t = T_obc - (T_ground - OWLT)
Un delta_t POSITIF signifie que l'horloge de bord AVANCE, c.-à-d. qu'elle est en avance sur le temps mission,
et que les télécommandes datées à bord se déclenchent donc TROP TÔT.
**Action:** Calculer la dérive qu'implique le décalage :
  drift_ppm = delta_t / `obdh.time_since_sync_s` (0x0A14) * 1e6
**Note:** Environ 12 ppm est nominal pour cet oscillateur. Juger le décalage au regard
du temps écoulé depuis la synchronisation, et non isolément : 3 s au bout de trois jours, c'est une horloge saine ;
3 s dix minutes après une synchronisation, ce ne l'est pas.
**Note:** Si `obdh.time_ref` (0x0A13) = 2 (GPS), s'attendre à delta_t ~ 0 --- une
horloge asservie au GPS est recalée sur le temps vrai à chaque top. Un décalage non nul dans
cet état signifie une télémesure périmée ou une panne ; NE PAS appliquer de saut à une horloge asservie.
**Note:** Si `obdh.time_ref` (0x0A13) = 0 (NONE), l'OBC n'a pas été réglé depuis
sa dernière réinitialisation du chargeur d'amorçage et affiche une date proche du 1er janvier 2000. C'est un
redémarrage, pas une dérive --- le confirmer avec `obdh.uptime` (0x0308) et
`obdh.reboot_count` (0x030A), et s'attendre à un écart de plusieurs années.
**Note:** Si |delta_t| < 1.0 s --- dans la tolérance ; aucune correction.
**Note:** Si 1.0 s <= |delta_t| < 10.0 s --- effectuer la correction.
**Note:** Si |delta_t| >= 10.0 s --- anormal pour une horloge synchronisée pendant ce quart.
Se mettre en attente (HOLD), déterminer s'il s'agit d'un redémarrage (time_ref = NONE) ou d'une réelle
dégradation de l'oscillateur, et prendre la branche NO-GO plutôt que de continuer.
**GO/NO-GO:** delta_t est dans [1.0 s, 10.0 s), time_ref vaut 1 (GROUND) ou 3 (HOLDOVER), et une correction est autorisée -> GO `STEP-3` | NO-GO `STEP-6`
**Note:** Il s'agit d'un embranchement décidé par l'opérateur, et non par la télémesure : delta_t est calculé
AU SOL à partir de T_obc, T_ground et de l'OWLT ; aucun paramètre bord ne peut donc
le porter, et un prédicat `**BRANCH:**` serait une fiction. La branche GO effectue la
correction ; la branche NO-GO n'effectue que le contrôle de cadence de `STEP-6`. Exécutée à plat ---
ce qui est tout ce que peut faire un exécuteur linéaire ---, les deux branches s'exécutent et une horloge
déjà juste subit malgré tout un saut.

### Étape 3 --- Préparer la correction de temps
**LABEL:** `STEP-3`
**Action:** Calculer le temps corrigé, en secondes CUC depuis J2000 :
  T_corrected = T_ground_at_send + OWLT + processing_delay
**Action:** Confirmer que T_corrected est rapporté à l'époque **J2000**. Un horodatage Unix ici
est trop grand d'environ 9.5e8 s et projette l'horloge d'une trentaine d'années en avant ; le
satellite l'accepte, et tous les horodatages et toutes les dates d'exécution qui suivent sont faux.
**Action:** Confirmer, si possible, que T_corrected est en avance sur le temps bord courant,
afin que l'horloge saute vers l'avant plutôt que vers l'arrière.
**Note:** `SET_TIME` porte des secondes CUC entières (`cuc_seconds`, uint32). Le
champ de fraction de seconde n'est pas commandable ; la précision inférieure à la seconde provient de l'asservissement
GPS, et non de cette fiche.
**Note:** La correction s'applique à bord au prochain front PPS, ce qui garantit
un saut net plutôt qu'étalé sur un top.

### Étape 4 --- Envoyer la correction de temps
**TC:** `SET_TIME(cuc_seconds=T_corrected)` (Service 9, Subtype 1) --- régler l'horloge de l'OBC
**Verify:** acceptation de la commande (Service 1, Subtype 1) reçue sous 5 s
**Verify:** aucun rejet de commande (Service 1, Subtype 2) reçu
**Note:** Le satellite émet l'événement **`OBC_TIME_SET` (0x030C)** portant le
saut SIGNÉ en secondes et la référence obtenue, sous la forme
`OBC clock set by ground (S9,1): jump +12.345s, time_ref=GROUND`. Consigner ce
saut : c'est la mesure, par le satellite lui-même, de l'erreur de l'horloge, et
il doit concorder avec votre delta_t.
**Note:** Les sauts inférieurs au seuil d'événement configuré (1.0 s) sont
supprimés ; une petite correction peut donc ne déclencher aucun événement. L'absence de l'événement ne
prouve pas que la commande a été ignorée --- lire plutôt 0x0309 et 0x0A14.
**Note:** L'argument doit rester À L'INTÉRIEUR des accents graves. Écrit à l'extérieur,
l'extracteur produit une étape `SET_TIME` sans argument et la trame encode
cuc_seconds = 0 --- une remise à zéro de l'époque, et non une synchronisation.

### Étape 5 --- Vérifier la correction
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- données de servitude plateforme/OBDH
**TC:** `REQUEST_TIME` (Service 9, Subtype 2) --- rapport de temps de confirmation
**Verify:** `obdh.time_ref == 1` (0x0A13, timeout 15 s) --- GROUND, c.-à-d. que le réglage a été appliqué
**Verify:** `obdh.mode == 0` (0x0300, timeout 10 s) --- OBC non affecté par le saut de temps
**Action:** Recalculer le résidu :
  delta_residual = T_obc_new - (T_ground_verify - OWLT)
**Verify:** |delta_residual| < 0.1 s (correction appliquée avec succès)
**Note:** `obdh.time_since_sync_s` (0x0A14) doit être reparti de ~0. S'il
affiche encore 4294967295 ou une valeur élevée, l'horloge n'a pas été réglée, quoi qu'indique
0x0309.
**Note:** Toutes les TC datées S11 déjà à bord ont été calculées par rapport à l'ANCIENNE horloge et
viennent d'être décalées de delta_t en temps mission. Revérifier le plan bord et
renvoyer tout ce qui est critique en temps.

### Étape 6 --- Valider la cadence de l'horloge
**LABEL:** `STEP-6`
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- second échantillon pour le contrôle de cadence
**Verify:** `obdh.mode == 0` (0x0300, timeout 10 s)
**Action:** Prélever deux échantillons SID 4 séparés par un intervalle sol connu et
calculer l'erreur de cadence :
  drift_ppm = ((T_obc_2 - T_obc_1) - (T_ground_2 - T_ground_1)) / interval * 1e6
**Note:** S'attendre à environ 12 ppm (~1 s/jour) sur une unité saine, avec quelques ppm de
dispersion d'une unité à l'autre. `obdh.uptime` (0x0308) s'incrémente à la même cadence et constitue une
corroboration utile --- de la cadence uniquement, jamais de l'époque.
**Note:** Au-delà de ~50 ppm, signaler l'oscillateur pour suivi de tendance et raccourcir l'intervalle
de synchronisation. Environ 500 ppm (~43 s/jour) est très au-delà de la spécification
de l'oscillateur : le traiter comme une panne d'oscillateur, pas comme un vieillissement.
**Note:** Un contrôle de cadence n'a pas de sens tant que `obdh.time_ref` (0x0A13) = 2 (GPS) :
l'horloge est recalée sur le temps vrai, et ce que l'on mesure est la boucle
d'asservissement, et non l'oscillateur.

### Étape 7 --- Consigner le résultat
**Consigner :** Inscrire les éléments suivants dans le journal de synchronisation temporelle :
  - Écart avant correction : delta_t, avec `obdh.time_since_sync_s` à cet instant
  - `obdh.time_ref` avant et après
  - Saut signalé par l'événement 0x030C (s'il a été émis)
  - Résidu après correction : delta_residual (ou N/A si aucune correction n'était nécessaire)
  - Dérive mesurée de l'oscillateur (ppm)
  - Tout plan S11 renvoyé en conséquence
  - Toute anomalie observée

## Conduite à tenir hors nominal
- **`obdh.time_ref` (0x0A13) = 0 (NONE), horloge indiquant l'an 2000 :** l'OBC
  a redémarré et le chargeur d'amorçage a remis l'horloge à J2000. Ce n'est pas une dérive.
  Le confirmer par `obdh.uptime` (0x0308) proche de zéro et `obdh.reboot_count`
  (0x030A) incrémenté, puis effectuer la correction --- l'écart se comptera en années,
  et c'est attendu. Démarrer l'image applicative ne restaure pas
  l'horloge ; un redémarrage impose toujours une resynchronisation.
- **`obdh.time_ref` = 3 (HOLDOVER) :** l'asservissement GPS a été perdu (événement
  `OBC_TIME_REF_LOST`, 0x030E) et l'horloge est libre depuis. Le
  décalage est la dérive accumulée depuis la perte du point GPS. Corriger ici par télécommande
  sol ; le rétablissement de l'asservissement GPS relève de CTG-027.
- **`obdh.time_ref` = 2 (GPS) mais delta_t non nul :** une horloge asservie
  ne dérive pas. Soupçonner une télémesure périmée (vérifier l'âge du SID 4), une mauvaise référence
  sol ou une erreur d'époque dans vos calculs. NE PAS envoyer `SET_TIME` : cela
  ramène la référence à GROUND et relance la dérive.
- **|delta_t| >= 10.0 s avec `time_ref` = 1 (GROUND) et une synchronisation récente :** rendre compte
  au directeur de vol. Dégradation possible de l'oscillateur ; vérifier que `obdh.temp`
  (0x0301) est compris entre -20 °C et +60 °C.
- **`SET_TIME` rejetée :** vérifier `obdh.sw_image` (0x0311) --- la commande ne figure pas
  dans la liste d'autorisation du chargeur d'amorçage. Sinon, vérifier l'intégrité de la liaison TTC et renvoyer
  une fois.
- **|delta_residual| > 1.0 s après la correction :** la correction n'a peut-être pas
  été appliquée. Redemander le SID 4, vérifier que `obdh.time_since_sync_s` est reparti,
  et réévaluer avant d'envoyer un second `SET_TIME`.
- **L'AOCS passe en SAFE_BOOT après un changement d'horloge :** un saut de temps supérieur à 5 s
  appliqué par la voie de synchronisation GPS force l'AOCS en SAFE_BOOT (événement 0x020F),
  car la solution d'attitude a été calculée sur une horloge qui a bougé.
  Effectuer la reprise selon CTG-027.
- **Dérive supérieure à 50 ppm :** programmer des synchronisations plus fréquentes, signaler l'oscillateur
  pour suivi de tendance, et consigner la valeur mesurée en ppm afin de constituer une tendance.

## Postconditions
- [ ] Horloge de bord à moins de 0.1 s de l'UTC sol (ou déjà confirmée dans la tolérance)
- [ ] `obdh.time_ref` (0x0A13) = 1 (GROUND) après un réglage sol, inchangé sinon
- [ ] `obdh.time_since_sync_s` (0x0A14) reparti de ~0 après une correction
- [ ] Dérive de l'oscillateur mesurée et consignée (nominalement ~12 ppm, < 50 ppm)
- [ ] Plan bord S11 revérifié par rapport à l'horloge corrigée
- [ ] Entrée du journal de synchronisation temporelle complétée
- [ ] Aucune perturbation de l'autonomie bord ni de l'exécution des télécommandes datées
- [ ] OBDH toujours en mode NOMINAL
