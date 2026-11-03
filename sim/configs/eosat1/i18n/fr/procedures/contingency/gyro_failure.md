# CTG-029 : Rétablissement après défaillance d'un gyromètre
**Sous-système :** AOCS
**Phase :** COMMISSIONING / NOMINAL
**Révision :** 1.0 --- nouvelle fiche (décision de l'auteur Q22 modifiée, 2026-10-30). Elle
remplace la fiche provisoire CTG-B01 « Anomalie IMU / gyromètre » du livre d'opérations et repose sur
ce que le simulateur modélise : un biais de vitesse persistant sur une voie gyrométrique ou sur les trois
(panne `gyro_bias`), un gyromètre mis hors tension (équipements S2 0x0206-0x0208) et
la saturation en vitesse.
**Approuvé par :** directeur des opérations de vol

**État d'entrée :** l'un des cas suivants
- événement `GYRO_BIAS_HIGH` (0x020B) --- le biais encore présent en sortie du gyromètre
  dépasse 0.05 deg/s (`aocs.gyro_bias_resid` 0x02D2) ;
- `aocs.gyro_units_mask` (0x02D1) != 7 --- un gyromètre est hors tension ;
- `aocs.gyro_saturated` (0x0295) = 1 --- une voie est en butée de sa plage de mesure ;
- l'estimation d'attitude dérive (`aocs.att_error` 0x0217 en hausse) alors que le
  senseur stellaire est hors de la boucle.

## Objet
Identifier la voie gyrométrique touchée, rétablir une référence de vitesse sans biais grâce à
l'étalonnage du biais à bord et, si la voie ne peut pas être récupérée, l'isoler
et poursuivre la détermination d'attitude avec les capteurs restants.

**Ce que le simulateur modélise.** EOSAT-1 emporte trois gyromètres monoaxes, un par
axe du corps, et **aucune unité de secours** : équipements S2 `S2_AOCS_GYROSCOPE_0/1/2`
(identifiants 0x0206, 0x0207, 0x0208 = 518, 519, 520). Il n'existe ni ligne d'alimentation IMU
ni unité sur laquelle basculer.
- Une panne de biais gyroscopique est un décalage matériel **persistant** sur un axe ou
  sur les trois. Il ne disparaît pas avec le temps. L'étalonnage à bord
  (`AOCS_GYRO_CALIBRATION`, func_id 13) le compense dans la chaîne de mesure ; il
  ne répare pas l'unité.
- Une unité hors tension est une **voie morte** : elle indique une vitesse nulle et le filtre
  d'attitude cesse de faire confiance à cet axe.
- Une voie au-delà de sa plage de mesure est écrêtée, et `aocs.gyro_saturated` (0x0295)
  reste positionné jusqu'à ce que la vitesse revienne dans la plage.

Les trois valeurs de biais sont des grandeurs différentes. L'instabilité de biais d'une unité saine est
d'environ 3e-5 deg/s (0,1 deg/h). L'événement 0x020B se déclenche à 0.05 deg/s de biais résiduel.
La limite S12 sur `aocs.gyro_bias_x/y/z` (0x0270-0x0272) est de +/-0.5 deg/s. Cette fiche
réagit à l'événement de 0.05 deg/s, le premier signal exploitable.

## Prérequis
- [ ] Liaison bande S bidirectionnelle active, au moins 15 minutes de passage restantes
      (l'arc d'étalonnage dure 300 s)
- [ ] OBC sur le logiciel applicatif (`obdh.sw_image` 0x0311 = 1)
- [ ] `eps.bat_soc` (0x0101) > 40 %
- [ ] Aucun basculement, aucune désaturation ni aucune manœuvre propulsive en cours ou prévue
      dans les 15 prochaines minutes

## Déroulement

### Étape 1 --- Recueillir la télémesure des gyromètres et de la détermination
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- données de servitude AOCS
**TC:** `HK_REQUEST(sid=7)` (Service 3, Subtype 27) --- détermination AOCS
**Verify:** `aocs.gyro_units_on` (0x0294) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_units_mask` (0x02D1) rapporté sous 20s --- consigner (bit0 X, bit1 Y, bit2 Z)
**Verify:** `aocs.gyro_saturated` (0x0295) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_bias_x` (0x0270) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_bias_y` (0x0271) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_bias_z` (0x0272) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_bias_resid` (0x02D2) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_temp` (0x0273) rapporté sous 20s --- consigner
**Note:** L'axe dont le biais se distingue dans 0x0270-0x0272 est la voie
touchée. Si les trois ont bougé ensemble, la panne porte sur tous les axes.
**GO/NO-GO:** Panne classée : unité hors tension (0x02D1 != 7), biais (0x02D2 > 0.05),
saturation (0x0295 = 1), ou une combinaison

### Étape 2 --- Protéger l'estimation d'attitude
**Verify:** `aocs.mode` (0x020F) rapporté sous 20s --- consigner
**Verify:** `aocs.est_source` (0x02C1) rapporté sous 20s --- bit 0 = senseur stellaire en assistance
**Verify:** `aocs.st1_status` (0x0240) == 2 sous 20s --- senseur sélectionné en TRACKING
**Verify:** `aocs.att_error` (0x0217) < 1.0 sous 20s
**Note:** Avec un senseur stellaire dans la boucle, le filtre estime le biais et
l'attitude reste bornée. Sans senseur, l'estimation se propage sur le gyromètre défaillant : un
biais de 0.05 deg/s fait dériver l'attitude de plusieurs dizaines de degrés en dix minutes et déclenche la
règle FDIR sur `aocs.att_error`. Si le senseur ne suit pas, le rétablir d'abord
(CTG-008 Panne du senseur stellaire), puis revenir à cette fiche.
**Note:** Une saturation (0x0295 = 1) signifie que le véhicule tourne plus vite que la
plage du gyromètre. C'est une anomalie d'attitude, pas une panne de gyromètre : appliquer CTG-002, puis revenir
une fois les vitesses maîtrisées.
**GO/NO-GO:** Senseur stellaire dans la boucle de détermination et erreur d'attitude bornée

### Étape 3 --- Remettre sous tension une unité éteinte
**Note:** Nécessaire seulement si l'étape 1 a trouvé `aocs.gyro_units_mask` (0x02D1) != 7. Les
commandes ci-dessous sont idempotentes : une unité déjà sur ON reste sur ON.
**TC:** `S2_AOCS_GYROSCOPE_0(device_id=518, state=1)` (Service 2, Subtype 1) --- unité X sur ON
**TC:** `S2_AOCS_GYROSCOPE_1(device_id=519, state=1)` (Service 2, Subtype 1) --- unité Y sur ON
**TC:** `S2_AOCS_GYROSCOPE_2(device_id=520, state=1)` (Service 2, Subtype 1) --- unité Z sur ON
**Verify:** `aocs.gyro_units_mask` (0x02D1) == 7 sous 20s
**Verify:** `aocs.gyro_units_on` (0x0294) == 3 sous 20s
**GO/NO-GO:** Les trois gyromètres alimentés (un étalonnage avec une voie morte est
refusé avec 0x0A02)

### Étape 4 --- Exécuter l'étalonnage du biais à bord
**Note:** Le véhicule doit être au repos : vitesses à moins de 0.10 deg/s de la
référence. Maintenir NOMINAL (mode 4, ou 8 en éclipse) ; ni basculement ni désaturation.
**TC:** `AOCS_GYRO_CALIBRATION(action=0, duration_s=300)` (Service 8, Subtype 1, func_id 13)
**Verify:** `aocs.gyro_cal_state` (0x02C9) == 1 sous 20s --- RUNNING
**Verify:** `event 0x0210 AOCS_GYRO_CAL_START` reçu sous 20s
**Note:** Si la commande est refusée, l'avis d'échec S1.8 et
`aocs.gyro_cal_reject` (0x02D0) nomment le verrou : 0x0A01 AOCS non alimenté,
0x0A02 une unité est éteinte (étape 3), 0x0A03 aucun senseur stellaire dans la boucle (étape 2),
0x0A04 vitesse au-dessus de 0.10 deg/s, 0x0A05 un étalonnage est déjà en cours.
**Note:** Le compte rendu de fin d'exécution S1.7 arrive à la fin de l'arc, pas à
l'acceptation.
**GO/NO-GO:** Étalonnage RUNNING

### Étape 5 --- Surveiller l'arc d'étalonnage
**TC:** `HK_REQUEST(sid=7)` (Service 3, Subtype 27) --- interroger toutes les 30 s
**Verify:** `aocs.gyro_cal_progress` (0x02CA) >= 100 sous 330s
**Note:** Toute manœuvre au-delà de la limite de 0.10 deg/s interrompt l'arc avec
`AOCS_GYRO_CAL_ABORT` (0x0212). Rien n'est appliqué après une interruption ; corriger la cause
nommée dans 0x02D0 et relancer l'étape 4.
**GO/NO-GO:** Arc terminé sans interruption

### Étape 6 --- Vérifier le résultat et consigner le biais
**Verify:** `aocs.gyro_cal_state` (0x02C9) == 2 sous 30s --- COMPLETE
**Verify:** `aocs.gyro_cal_result` (0x02CF) == 1 sous 30s --- SUCCESS
**Verify:** `event 0x0211 AOCS_GYRO_CAL_COMPLETE` reçu sous 30s
**TC:** `GET_PARAM(param_id=0x02CB)` (Service 20, Subtype 3) --- biais X estimé
**TC:** `GET_PARAM(param_id=0x02CC)` (Service 20, Subtype 3) --- biais Y estimé
**TC:** `GET_PARAM(param_id=0x02CD)` (Service 20, Subtype 3) --- biais Z estimé
**Verify:** `aocs.gyro_cal_bias_x` (0x02CB) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_cal_bias_y` (0x02CC) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_cal_bias_z` (0x02CD) rapporté sous 20s --- consigner
**GO/NO-GO:** SUCCESS, et chaque axe dans +/-0.5 deg/s. Au-delà, ne pas
accepter le résultat : appliquer l'étape 7.

### Étape 7 --- Isoler une voie irrécupérable (seulement si l'étape 6 a échoué)
**Note:** Ignorer cette étape si l'étape 6 a donné GO. N'isoler une voie que si son biais
dépasse 0.5 deg/s après un étalonnage de 900 s, ou si deux étalonnages successifs sont interrompus
avec 0x0A06. Ne mettre sur OFF que l'axe défaillant ; l'unité X est montrée. Utiliser
l'équipement 519 pour Y ou 520 pour Z.
**TC:** `S2_AOCS_GYROSCOPE_0(device_id=518, state=0)` (Service 2, Subtype 1) --- unité défaillante sur OFF (X montrée)
**TC:** `AOCS_EST_RESET(mode=1)` (Service 8, Subtype 1, func_id 91) --- réinitialisation à chaud : conserver l'attitude, regonfler la covariance
**Verify:** `aocs.gyro_units_mask` (0x02D1) rapporté sous 20s --- le bit défaillant est à zéro
**Verify:** `aocs.est_source` (0x02C1) rapporté sous 60s --- bit 0 toujours positionné
**Note:** Avec une voie éteinte, la vitesse sur cet axe ne vient plus que du senseur stellaire.
Le pointage fin et la prise de vue sur cet axe restent dégradés jusqu'à la fin de la
mission ; il n'y a pas d'unité de secours. Pendant une indisponibilité du senseur, l'estimateur n'a aucune
référence de vitesse sur cet axe.
**GO/NO-GO:** Voie défaillante isolée, estimateur en reconvergence

### Étape 8 --- Confirmer le rétablissement
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.gyro_bias_resid` (0x02D2) < 0.005 sous 60s
**TC:** `HK_REQUEST(sid=7)` (Service 3, Subtype 27) --- interroger toutes les 60 s pendant 5 minutes
**Verify:** `aocs.gyro_cal_comp_mag` (0x02CE) rapporté sous 60s --- consigner
**Verify:** `aocs.knowledge_err_3sig` (0x02A7) < 120 sous 300s --- arcsec
**Verify:** `aocs.control_err` (0x02A8) < 1.0 sous 300s --- deg
**Note:** Un étalonnage réussi fait passer le biais de 0x02D2 (ce qui reste en
sortie) à 0x02CE (compensation appliquée). L'événement 0x020B disparaît parce qu'il est
mesuré sur le résidu ; la panne matérielle est toujours là.
**GO/NO-GO:** Référence de vitesse rétablie ou voie isolée ; détermination stable

## Conduite à tenir hors nominal
- **Les trois unités éteintes ou défaillantes.** Le filtre n'a plus de référence de vitesse et se propage sur
  le senseur stellaire, les capteurs solaires et le magnétomètre seuls. Maintenir NOMINAL si le senseur
  est valide ; sinon appliquer EMG-005 (Perte d'attitude).
- **Refus avec 0x0A03.** Aucun senseur stellaire dans la boucle. Rétablir le senseur
  (CTG-008), attendre le bit 0 de `aocs.est_source` (0x02C1), puis relancer l'étape 4.
- **Refus avec 0x0A04.** Le véhicule n'est pas au repos. Attendre la fin de tout basculement ou
  de toute désaturation (`aocs.mode` 0x020F != 6 et != 7) et réessayer.
- **Le biais réapparaît après un bon étalonnage.** Une dérive d'origine thermique suit
  `aocs.gyro_temp` (0x0273) ; relancer l'étalonnage après le transitoire thermique.
  Un biais qui revient à température constante signale une unité qui se dégrade : ouvrir un rapport
  d'anomalie.
- **L'étalonnage surcompense après la disparition de la panne.** Si le biais
  matériel disparaît après un étalonnage, la compensation enregistrée surcompense désormais
  avec le signe opposé (0x02D2 et 0x02CE tous deux non nuls). Relancer
  l'étape 4 pour charger une nouvelle compensation.

## Postconditions
- [ ] Voie touchée identifiée et consignée
- [ ] Soit `aocs.gyro_cal_result` (0x02CF) = 1 avec `aocs.gyro_bias_resid`
      (0x02D2) < 0.005 deg/s, soit l'unité défaillante isolée et enregistrée dans
      `aocs.gyro_units_mask` (0x02D1)
- [ ] Erreur de connaissance d'attitude inférieure à 120 arcsec à 3 sigma (`aocs.knowledge_err_3sig` 0x02A7)
- [ ] Rapport d'anomalie ouvert avec les biais, la température et la décision consignés

## État de sortie
- AOCS en NOMINAL (mode 4, ou 8 en éclipse) avec le senseur stellaire dans la boucle
- Biais gyrométrique compensé, ou une voie isolée avec une connaissance de vitesse dégradée sur
  cet axe
- Aucun état de ligne d'alimentation, de TT&C ou de charge utile modifié

**PROCÉDURE SUIVANTE :** reprendre l'activité interrompue. Si une voie a été isolée, vérifier
`aocs.fine_ready` (0x02C5) avant la prochaine séance de prise de vue : FINE_POINT est
refusé tant qu'il n'est pas nul.
