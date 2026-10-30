# COM-003 : Étalonnage des capteurs SCAO
**Sous-système :** AOCS
**Phase :** COMMISSIONING
**Révision :** 3.0 --- s'exécute APRÈS COM-004, en NOMINAL contrôlé par les roues
(décision de l'auteur Q16, 2026-10-30). La condition préalable à l'étalonnage est la
configuration de l'estimateur elle-même (ST sélectionné suivant >= 5 étoiles ET
`aocs.est_source` 0x02C1 bit 0) ainsi que tous les gyromètres alimentés et |vitesse - référence| <= 0.10 deg/s. Le verrou de 0.10 deg/s est conservé ; ce sont les roues qui le rendent atteignable.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-004 --- les quatre roues ACTIVÉES
(`aocs.wheels_enabled` 0x0260 = 4), AOCS en NOMINAL commandé sur les roues
(`aocs.mode` 0x020F = 4, ou 8 en éclipse), senseurs stellaires et gyromètres sur OFF,
SID 2 transmis, phase de mission 5.

## Objet
Recetter la chaîne de détermination de l'AOCS : mettre en service les trois gyromètres,
intégrer un senseur stellaire dans la boucle de détermination, et exécuter l'étalonnage du biais
des gyromètres à bord afin que la voie de vitesse soit compensée en biais avant que le satellite
ne doive tenir un pointage fin.

**Historique des révisions (1.0 → 3.0).** La révision 1.0 de cette fiche était presque
entièrement inventée. Elle commandait l'étalonnage avec
`SET_PARAM(param_id=0x0250, value=1)`, lisait l'état dans `0x0251` et le biais dans
`0x0252-0x0254`, lançait un étalonnage du magnétomètre à `0x0260`, alimentait le
senseur stellaire avec `0x0270` et l'intégrait dans la boucle avec `0x0275`. **Aucun de
ces paramètres n'existe**, `SET_PARAM` ne peut de toute façon pas écrire une commande, et il
n'existe aucun étalonnage du magnétomètre à bord. Un opérateur suivant l'ancienne
fiche envoyait sept télécommandes sans effet, puis consignait des chiffres
inventés. La vraie commande est `AOCS_GYRO_CALIBRATION` (Service 8, Subtype 1,
func_id 13), et jusqu'à la révision 2.0, elle n'était elle-même qu'un bouchon qui remettait à zéro un
nombre interne et signalait un succès sans rien estimer. La révision
3.0 (2026-08c) a remplacé le verrou de mode par la condition préalable de l'estimateur et exécutait
la fiche avant COM-004, dans le maintien COARSE_SUN roues coupées. À l'époque du 2026-08-20,
le contrôle par magnétocoupleurs seuls dans ce maintien oscille entre 0.1 et 0.4 deg/s
en permanence et n'a jamais satisfait le verrou de 0.10 deg/s ; la décision de l'auteur du
2026-10-30 (Q16) a donc placé la fiche après COM-004, où les roues tiennent NOMINAL
assez calmement, et a conservé le verrou.

**À propos de l'alimentation de l'IMU.** EOSAT-1 emporte trois gyromètres mono-axe et **ni IMU
redondante ni ligne d'alimentation IMU**. Les unités sont alimentées individuellement en tant qu'équipements S2
`S2_AOCS_GYROSCOPE_0/1/2` (identifiants d'équipement 0x0206, 0x0207, 0x0208 = 518, 519, 520),
une par axe satellite. Il n'y a aucune télécommande « IMU ON » à chercher ; ces trois
commandes d'équipement sont les seules.

## Prérequis
- [ ] COM-001, COM-002 et COM-004 terminées. COM-004 EST un prérequis (décision
      Q16) : les roues doivent être activées (`aocs.wheels_enabled` 0x0260 == 4)
      et tenir NOMINAL, car le maintien par magnétocoupleurs roues coupées ne peut pas
      garder les vitesses angulaires sous le verrou d'étalonnage de 0.10 deg/s
- [ ] `eps.pl_aocs_wheels` (0x0117) == 1 — la ligne de l'ensemble AOCS est sur ON (LEOP-007)
- [ ] `eps.bat_soc` (0x0101) > 60 %
- [ ] OBC exécutant l'application (et non le chargeur d'amorçage)
- [ ] Liaison bidirectionnelle en bande S active
- [ ] Au moins 20 minutes de passage station sol restantes. L'étalonnage
      lui-même est un arc de 300 s et la fiche se termine par le contrôle de détermination de
      cinq minutes de l'étape 10 ; un passage court ne couvrira donc pas toute la procédure.
- [ ] **Pas** d'entrée ou de sortie d'éclipse dans les 10 prochaines minutes — l'AOCS
      passe en ECLIPSE (mode 8) au terminateur. C'est sans conséquence pour
      l'étalonnage (le senseur reste dans la boucle), mais cela modifie `aocs.mode`
      à l'insu de l'opérateur, ce que les vérifications ci-dessous prennent en compte.

## Déroulement

### Étape 1 — Activer les données de servitude de détermination AOCS
**TC:** `HK_ENABLE(sid=2)` (Service 3, Subtype 5) --- données de servitude AOCS, 8 s
**TC:** `HK_ENABLE(sid=7)` (Service 3, Subtype 5) --- détermination AOCS, 4 s
**Note:** Le SID 7 `AOCS_DETERMINATION` transporte les voies d'étalonnage
(`aocs.gyro_cal_state` 0x02C9, `aocs.gyro_cal_progress` 0x02CA,
`aocs.gyro_cal_bias_x/y/z` 0x02CB-0x02CD, `aocs.gyro_cal_comp_mag` 0x02CE,
`aocs.gyro_cal_result` 0x02CF, `aocs.gyro_cal_reject` 0x02D0) à une cadence de 4 s.
S'il n'est pas activé, l'étalonnage se déroule sans visibilité depuis le sol.
**Verify:** `obdh.hk_sids_enabled` rapporté sous 20s
**GO/NO-GO:** Les deux structures de servitude AOCS sont transmises

### Étape 2 — Confirmer que les trois gyromètres sont alimentés
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.gyro_units_on` (0x0294) == 3 sous 20s
**Verify:** `aocs.gyro_units_mask` (0x02D1) == 7 sous 20s
**Note:** 0x02D1 est un masque de bits — bit0 = unité X (équipement 0x0206), bit1 = Y
(0x0207), bit2 = Z (0x0208). Le décompte seul ne permet pas de savoir *quelle* voie
manque, et perdre le tangage sur un satellite en suivi nadir n'est pas le même problème
que perdre le roulis.
**Note:** Si une unité est éteinte, la mettre sous tension avec la commande d'équipement correspondante
avant de continuer ; un étalonnage avec une voie morte est refusé avec le code
0x0A02.
**TC:** `S2_AOCS_GYROSCOPE_0(device_id=518, state=1)` (Service 2, Subtype 1) --- unité X sur ON
**TC:** `S2_AOCS_GYROSCOPE_1(device_id=519, state=1)` (Service 2, Subtype 1) --- unité Y sur ON
**TC:** `S2_AOCS_GYROSCOPE_2(device_id=520, state=1)` (Service 2, Subtype 1) --- unité Z sur ON
**Verify:** `aocs.gyro_units_mask` (0x02D1) == 7 sous 20s
**GO/NO-GO:** Les trois gyromètres alimentés

### Étape 3 — Intégrer un senseur stellaire dans la boucle de détermination
**TC:** `ST1_POWER(on=1)` (Service 8, Subtype 1, func_id 4)
**TC:** `ST2_POWER(on=1)` (Service 8, Subtype 1, func_id 5)
**TC:** `ST_SELECT(unit=1)` (Service 8, Subtype 1, func_id 6) --- sélectionner ST1.
Le codage émis est **1 = ST1, 2 = ST2 ; 0 est REFUSÉ** (décision 2026-08c --- l'ancien
texte « 0=ST1, 1=ST2 » faisait envoyer aux opérateurs un octet refusé pour ST1 et sélectionnait silencieusement
ST1 lorsqu'ils voulaient ST2).
**Note:** Chaque senseur met environ 60 s à démarrer et à acquérir.
**Verify:** `aocs.st1_status` (0x0240) == 2 sous 120s --- TRACKING
**Verify:** `aocs.st1_num_stars` (0x0241) >= 5 sous 120s
**Verify:** `aocs.st2_status` (0x0243) == 2 sous 120s --- l'unité redondante est également en suivi
**Note:** Il n'existe pas de voie de télémesure distincte « senseur valide » ; l'état
de l'unité sélectionnée (`aocs.st_selected` 0x0244 la désigne) EST la validité.
**GO/NO-GO:** Le senseur sélectionné suit au moins cinq étoiles

### Étape 4 — Attendre que le senseur assiste l'estimateur (aucune commande de mode)
**Action:** Rester dans le NOMINAL contrôlé par les roues laissé par COM-004. Une fois le
véhicule au repos (|vitesse| < 0,25°/s) et le senseur sélectionné suivant
>= 5 étoiles, le ST assiste le MEKF et le bit 0 de `aocs.est_source` (0x02C1) se positionne.
Aucun mode n'est commandé ici : la condition préalable est la configuration de l'estimateur,
pas le mode. (DETUMBLE ne positionne jamais le bit 0 ; un étalonnage dans ce mode est
toujours refusé avec 0x0A03.)
**Note:** Au terminateur, NOMINAL passe la main à ECLIPSE (mode 8), puis la reprend. C'est
sans conséquence pour l'étalonnage : les modes 4 et 8 satisfont tous deux la
condition préalable de l'estimateur une fois le bit 0 positionné.
**Verify:** `aocs.est_source` (0x02C1) bit 0 positionné sous 600s --- assistance ST
**Verify:** `aocs.knowledge_err_3sig` (0x02A7) < 300 sous 600s --- arcsec
**GO/NO-GO:** Senseur stellaire alimentant l'estimateur

### Étape 5 — Consigner le biais avant étalonnage
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.gyro_bias_x` (0x0270) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_bias_y` (0x0271) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_bias_z` (0x0272) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_bias_resid` (0x02D2) rapporté sous 20s --- consigner
**Note:** 0x0270-0x0272 indiquent le biais présent en **sortie** du gyromètre, c.-à-d.
après toute compensation déjà chargée ; 0x02D2 est la norme de la même
grandeur. Sur une unité saine non étalonnée, s'attendre à quelques 1e-5 deg/s
(instabilité de biais de 0,1°/h). Une valeur proche de 0.05 deg/s ou supérieure signifie qu'un biais réel
est présent et que `GYRO_BIAS_HIGH` (0x020B) aura été levé.
**GO/NO-GO:** Biais avant étalonnage consigné

### Étape 6 — Commander l'étalonnage du biais des gyromètres
**TC:** `AOCS_GYRO_CALIBRATION(action=0, duration_s=300)` (Service 8, Subtype 1, func_id 13)
**Note:** `duration_s=0` sélectionne l'arc par défaut configuré
(`sensors.gyro.calibration.duration_s`, 300 s) ; toute autre valeur est bornée à
[30, 1800] s. Le satellite répond par une TM(8,130) indiquant l'état, l'avancement et l'arc
effectivement accepté.
**Note:** Le satellite moyenne le biais gyrométrique observé par le filtre d'attitude sur
l'arc (en écartant les 30 premières secondes, le temps que le filtre se stabilise), puis écrit le
résultat dans une table de compensation de bord appliquée sur la chaîne de mesure gyrométrique.
Ce n'est ni instantané, ni une réinitialisation.
**Verify:** `aocs.gyro_cal_state` (0x02C9) == 1 sous 20s --- RUNNING
**Verify:** `event 0x0210 AOCS_GYRO_CAL_START` reçu sous 20s
**Note:** La fin d'exécution S1.7 de cette télécommande arrive à la FIN DE L'ARC, et non à l'acceptation — la ligne de vérification reste ouverte pendant tout l'arc, et un abandon en cours de route est signalé par un S1.8 sur la même télécommande, portant le code bloquant.
**Note:** Si la commande est refusée, l'avis d'échec S1.8 nomme le verrou.
0x0A01 = AOCS non alimenté, 0x0A02 = un gyromètre est éteint (étape 2), 0x0A03 = aucun senseur
stellaire dans la boucle (étapes 3-4), 0x0A04 = vitesse angulaire au-dessus de la limite
d'étalonnage de 0.10 deg/s, 0x0A05 = un étalonnage est déjà en cours. Le même code est
mémorisé dans `aocs.gyro_cal_reject` (0x02D0).
**Note:** En cas de retour 0x0A04, attendre une période calme (toutes les vitesses
< 0.08 deg/s sur le SID 2) et réessayer. En NOMINAL contrôlé par les roues, le véhicule
se stabilise sous le verrou et l'étalonnage démarre généralement du premier coup ; un
refus signifie normalement qu'un basculement, une désaturation ou un transitoire de roue est encore
en cours. C'est pourquoi la fiche s'exécute après COM-004 (décision Q16) : dans le
maintien COARSE_SUN roues coupées, le contrôle par magnétocoupleurs oscille entre 0.1 et 0.4 deg/s à
l'époque du 2026-08-20 et le verrou n'a jamais été satisfait.
**GO/NO-GO:** Étalonnage RUNNING

### Étape 7 — Surveiller l'arc d'étalonnage
**TC:** `HK_REQUEST(sid=7)` (Service 3, Subtype 27) --- interroger toutes les 30 s
**Verify:** `aocs.gyro_cal_progress` (0x02CA) > 0 sous 60s
**Verify:** `aocs.gyro_cal_progress` (0x02CA) >= 100 sous 330s
**Note:** NE PAS effectuer de basculement, de désaturation ni de changement de mode pendant l'arc.
Toute manœuvre au-dessus de la limite de repos de 0.10 deg/s interrompt l'étalonnage
avec `AOCS_GYRO_CAL_ABORT` (0x0212) plutôt que de moyenner des valeurs absurdes. C'est le
cas d'abandon 0x0A04 ; réexécuter l'étalonnage (étape 6) une fois stabilisé (voir la conduite
à tenir hors nominal ci-dessous).
**Note:** Pour abandonner délibérément l'exécution, envoyer
`AOCS_GYRO_CALIBRATION(action=1, duration_s=0)` ; l'abandon est signalé avec le
code 0x0A08.
**GO/NO-GO:** Étalonnage parvenu à 100 % sans abandon

### Étape 8 — Vérifier le résultat de l'étalonnage
**TC:** `HK_REQUEST(sid=7)` (Service 3, Subtype 27)
**Verify:** `aocs.gyro_cal_state` (0x02C9) == 2 sous 30s --- COMPLETE
**Verify:** `aocs.gyro_cal_result` (0x02CF) == 1 sous 30s --- SUCCESS
**Verify:** `aocs.gyro_cal_reject` (0x02D0) == 0 sous 30s
**Verify:** `event 0x0211 AOCS_GYRO_CAL_COMPLETE` reçu sous 30s
**TC:** `GET_PARAM(param_id=0x02CB)` (Service 20, Subtype 3) --- biais X estimé
**TC:** `GET_PARAM(param_id=0x02CC)` (Service 20, Subtype 3) --- biais Y estimé
**TC:** `GET_PARAM(param_id=0x02CD)` (Service 20, Subtype 3) --- biais Z estimé
**Verify:** `aocs.gyro_cal_bias_x` (0x02CB) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_cal_bias_y` (0x02CC) rapporté sous 20s --- consigner
**Verify:** `aocs.gyro_cal_bias_z` (0x02CD) rapporté sous 20s --- consigner
**Note:** Chaque axe doit se situer à +/- 0.5 deg/s. Une unité saine ressort de l'étalonnage
à quelques 1e-5 deg/s ; une valeur proche de 0.05 deg/s signifie qu'un biais réel était
présent et qu'il est désormais compensé, ce qui est un étalonnage réussi, et non un
échec.
**GO/NO-GO:** L'étalonnage indique SUCCESS avec un biais plausible sur chaque axe

### Étape 9 — Confirmer que la compensation a pris effet
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.gyro_bias_resid` (0x02D2) < 0.005 sous 60s
**TC:** `HK_REQUEST(sid=7)` (Service 3, Subtype 27)
**Verify:** `aocs.gyro_cal_comp_mag` (0x02CE) rapporté sous 60s --- consigner
**Note:** Ces deux nombres sont toute la raison d'être de la fiche et ce sont
délibérément des grandeurs différentes. 0x02CE est la norme de la compensation
désormais appliquée à bord ; 0x02D2 est ce qui RESTE en sortie du gyromètre. Un étalonnage
réussi fait passer le biais de 0x02D2 dans 0x02CE.
**Note:** `aocs.gyro_bias_injected` (0x0296) donne à l'instructeur la visibilité d'une
panne matérielle `gyro_bias` injectée et n'est **délibérément pas modifié** par un
étalonnage. Compenser un biais ne répare pas l'unité : 0x0296 continue de
signaler la panne tandis que 0x02D2 montre que le véhicule n'en souffre plus.
Si 0x0296 est non nul, il s'agit d'un scénario de formation, et non d'une anomalie.
**GO/NO-GO:** Biais résiduel compensé

### Étape 10 — Contrôle de la détermination après étalonnage
**TC:** `HK_REQUEST(sid=7)` (Service 3, Subtype 27) --- interroger toutes les 60 s pendant 5 minutes
**Verify:** `aocs.knowledge_err_3sig` (0x02A7) < 120 sous 300s --- arcsec
**Verify:** `aocs.control_err` (0x02A8) < 1.0 sous 300s --- deg
**Verify:** `aocs.est_source` (0x02C1) >= 9 sous 300s
**Verify:** `aocs.gyro_cal_state` (0x02C9) == 2 sous 300s --- toujours COMPLETE, pas de nouvel abandon
**Note:** L'intérêt opérationnel de l'étalonnage n'apparaît que lorsque le
senseur stellaire n'est PAS disponible : avec un gyromètre compensé, l'estimation se poursuit sur le
gyromètre pendant une indisponibilité du senseur de façon quasi plate, alors qu'un biais non compensé de 0,05°/s
fait dériver l'estimation de plusieurs dizaines de degrés en dix minutes et déclenche la règle FDIR
`aocs.att_error`. Ne pas provoquer une indisponibilité du senseur pour le prouver sur
un satellite réel ; c'est démontré dans le scénario de formation.
**GO/NO-GO:** Détermination AOCS stable après l'étalonnage

## Conduite à tenir hors nominal
- **Commande refusée, `aocs.gyro_cal_reject` (0x02D0) = 0x0A02.** Un gyromètre est
  éteint. Lire `aocs.gyro_units_mask` (0x02D1) pour savoir lequel, puis l'alimenter avec la
  commande `S2_AOCS_GYROSCOPE_n` correspondante et relancer l'étalonnage.
- **Refus avec 0x0A03.** Le senseur stellaire n'est pas dans la boucle de détermination.
  Soit le senseur ne suit pas (`aocs.st1_status` 0x0240 != 2 — renouveler la
  mise sous tension du senseur), soit il n'a pas encore rejoint l'estimateur : attendre le
  bit 0 de `aocs.est_source` (0x02C1) (étape 4) et réessayer.
- **Refus avec 0x0A04.** La vitesse angulaire dépasse 0.10 deg/s par rapport à la
  référence. Attendre la fin du basculement ou de la désaturation
  (`aocs.slew_state` 0x0292 = 0, `aocs.mode` 0x020F != 7) et réessayer.
- **Refus avec 0x0A05.** Un étalonnage est déjà en cours. Soit l'attendre
  (`aocs.gyro_cal_progress` 0x02CA), soit l'abandonner avec `action=1`.
- **`AOCS_GYRO_CAL_ABORT` (0x0212) levé en cours d'arc.** La moyenne a été
  écartée et RIEN n'a été appliqué — la compensation précédente, s'il y en a une, reste
  en vigueur et `aocs.gyro_cal_result` (0x02CF) indique 2. Corriger la cause
  indiquée par 0x02D0 et réexécuter l'étalonnage (étape 6). L'abandon est le comportement correct ;
  sinon, un étalonnage ayant perdu sa référence d'attitude chargerait une table de biais
  construite à partir de bruit.
- **Biais estimé > 0.5 deg/s sur un axe.** Ne pas l'accepter. Relancer avec un
  arc plus long (`duration_s=900`) après avoir confirmé que le véhicule est réellement
  au repos. Si le problème persiste, l'unité est hors spécification — émettre un rapport
  d'anomalie satellite et envisager de voler avec l'unité de cet axe éteinte,
  en acceptant une connaissance dégradée sur cet axe (`aocs.gyro_units_mask` 0x02D1
  enregistre la configuration).
- **Le senseur stellaire n'acquiert pas en 120 s.** Rechercher la présence du Soleil ou de la Lune
  dans le champ de vue (`aocs.st1_status` 0x0240 = 3 signifie BLIND, et non une panne) et
  attendre que l'attitude évolue. Essayer l'unité redondante avec
  `ST_SELECT(unit=2)` (Service 8, Subtype 1, func_id 6).
- **Étalonnage du magnétomètre.** La révision 1.0 de cette fiche exécutait un étalonnage
  du magnétomètre (fer dur/fer doux) par rapport à l'IGRF aux paramètres 0x0260-0x0262.
  **Cette fonction n'existe pas à bord et ces paramètres non plus.** Le
  magnétomètre est utilisé tel quel sur la voie grossière à deux vecteurs ; rien dans cette fiche
  ne l'étalonne. Ne pas tenter de le commander.

## Postconditions
- [ ] Les trois gyromètres alimentés — `aocs.gyro_units_mask` (0x02D1) == 7
- [ ] Senseur stellaire suivant >= 5 étoiles (`aocs.st1_status` 0x0240 == 2) et dans
      la boucle de détermination —
      `aocs.est_source` (0x02C1) bit0 et bit3 tous deux positionnés
- [ ] Étalonnage du biais des gyromètres COMPLETE et SUCCESS —
      `aocs.gyro_cal_state` (0x02C9) == 2, `aocs.gyro_cal_result` (0x02CF) == 1
- [ ] Biais estimé par axe consigné à partir de 0x02CB-0x02CD
- [ ] Compensation appliquée (`aocs.gyro_cal_comp_mag` 0x02CE) et biais résiduel
      inférieur à 0.005 deg/s (`aocs.gyro_bias_resid` 0x02D2)
- [ ] Erreur de connaissance d'attitude inférieure à 120 arcsec 3σ (`aocs.knowledge_err_3sig`
      0x02A7)
- [ ] Rapport d'étalonnage des capteurs établi avec les valeurs de biais consignées et le
      résidu avant/après

## État de sortie
- Les trois gyromètres sur ON, les deux senseurs stellaires sur ON, ST1 sélectionné et en suivi
- Étalonnage du biais des gyromètres COMPLETE/SUCCESS avec compensation appliquée
- AOCS toujours dans le NOMINAL commandé sur les roues (mode 4, ou 8 en
  éclipse), désormais avec le senseur stellaire dans la boucle de détermination ; roues ACTIVÉES
  (0x0260 = 4)
- Aucun état de ligne d'alimentation ni de TTC touché

**PROCÉDURE SUIVANTE :** COM-005 (Transitions de modes SCAO)
