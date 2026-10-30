# COM-011 : Étalonnage de la charge utile
**Sous-système :** Charge utile
**Phase :** COMMISSIONING
**Révision :** 1.1 --- 2026-08c : états d'entrée et de sortie déclarés ; s'exécute APRÈS COM-012
(première lumière) selon l'ordre définitif de la recette en orbite.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-012 --- chaîne image vérifiée de bout en bout,
charge utile en STANDBY avec le refroidisseur en régulation (`payload.fpa_ready` 0x0610 = 1),
AOCS en NOMINAL commandé, liaison descendante en LOW.

## Objet
Effectuer l'étalonnage radiométrique initial de l'imageur multispectral. Acquérir des images
d'obscurité, obturateur fermé, afin de caractériser le courant d'obscurité et le bruit spatial fixe du FPA
à la température opérationnelle. Acquérir des images d'un site d'étalonnage radiométrique
connu pour vérifier l'étalonnage absolu. Valider la linéarité du détecteur
et le recalage entre bandes.

## Prérequis
- [ ] COM-012 (Première lumière) terminée — chaîne image vérifiée
- [ ] Charge utile en STANDBY (mode 1) avec le refroidisseur du FPA en marche
- [ ] `payload.fpa_temp` (0x0601) stable à la consigne commandée (-15C : bande de -16.5C à -14.5C) et `payload.fpa_ready` (0x0610) = 1 depuis plus de 10 minutes
- [ ] AOCS capable de FINE_POINT — c'est-à-dire le **mode 5**, et non 4 (4 est NOMINAL) —
      avec une précision < 0.1 deg. Depuis la phase 1, FINE est autorisé sur une pyramide à TROIS
      roues ; `aocs.fine_degraded` (0x0299) = 1 l'indique, et un FINE dégradé est
      toujours autorisé à acquérir.
- [ ] `eps.bat_soc` (0x0101) > 70 %
- [ ] Survol du site d'étalonnage au sol prédit pendant l'orbite en cours ou la suivante
- [ ] Passage de vidage complet des images programmé dans les 6 heures
- [ ] Liaison bidirectionnelle en bande S active
- [ ] Ingénieur étalonnage charge utile en console

## Déroulement

### Étape 1 — Vérifier l'état avant étalonnage
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27)
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) sous 10s
**Verify:** `payload.fpa_temp` (0x0601) dans la plage **[-16.5 C, -14.5 C]** — la bande
autour de la consigne nominale de -15 C — sous 10 s
**Verify:** `payload.fpa_ready == 1` (0x0610, timeout 10 s)
**Note:** Cette étape exigeait [-32 C, -28 C]. L'enveloppe de consigne commandable va de
**−20 °C à 0 °C** (`subsystems/tcs.yaml`) ; une plage de −32 à −28 °C sortait donc de tout ce que le
satellite pouvait être commandé à atteindre : le contrôle ne pouvait jamais réussir. Vérifier
`fpa_ready` plutôt qu'un nombre mémorisé — la disponibilité suit la consigne
ACTIVE, et reste donc correcte si la campagne se déroule à −20 °C.
**TC:** `GET_PARAM(param_id=0x060B)` (Service 20, Subtype 3) — `payload.mem_used_mb`
**TC:** `GET_PARAM(param_id=0x060A)` (Service 20, Subtype 3) — `payload.mem_total_mb`
**Verify:** `mem_total_mb - mem_used_mb` > 1000 MB sous 10 s. (0x0605 est
`payload.image_count`, et non l'espace de stockage libre.)
**GO/NO-GO:** Charge utile et stockage prêts pour la séquence d'étalonnage

### Étape 2 — Fermer l'obturateur pour l'acquisition d'images d'obscurité
**TC:** `PAYLOAD_SET_SHUTTER(position=0)` (Service 8, Subtype 1, func_id 119) — CLOSED
**Octets émis :** `77 00`
**TC:** `GET_PARAM(param_id=0x063C)` (Service 20, Subtype 3) — `payload.shutter_pos`
**Verify:** `payload.shutter_pos == 0` (0x063C, timeout 10 s) — CLOSED
**Note:** La func 119 est nouvelle depuis la phase 4 et c'est une commande de position ABSOLUE. Cette
étape utilisait `PAYLOAD_CYCLE_SHUTTER(cycles=1)` en parlant de « cycler jusqu'à CLOSED »,
ce qui revient à jouer à pile ou face : le cyclage compte les TRANSITIONS de la lame, si bien qu'un cycle à partir d'un
obturateur déjà fermé se termine OUVERT. Il n'existait auparavant aucun moyen d'atteindre une position
connue de l'obturateur, et la condition préalable des images d'obscurité ci-dessous est absolue.
**GO/NO-GO:** Obturateur confirmé CLOSED

### Étape 3 — Acquérir le jeu d'images d'obscurité
**Note:** L'étalonnage est désormais conditionné par l'OPTIQUE, et non par le mot de mode, et il
est **refusé depuis IMAGING** avec `code="CAL_REFUSED_IMAGING"` — « a calibration
frame must not see the scene ». Cette étape commandait auparavant IMAGING en premier, ce qui
est exactement le défaut supprimé par la phase 4. Partir de STANDBY (mode 1) ; la charge utile
se promeut d'elle-même dans le nouveau **mode 3 = CALIBRATION** pendant la durée de l'opération.
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) — STANDBY
**TC:** `PAYLOAD_CAL_LAMP(on=0)` (Service 8, Subtype 1, func_id 95) — lampe éteinte pour une image d'obscurité
**TC:** `PAYLOAD_START_CALIBRATION(mode=0)` (Service 8, Subtype 1, func_id 37) — phase DARK
**Octets émis :** `25 00`
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — données de servitude de la charge utile
**Verify:** `payload.mode == 3` (0x0600, timeout 15 s) — CALIBRATION
**Verify:** `payload.calibration_active == 1` (0x062A, timeout 15 s)
**Note:** Les quatre conditions préalables imposées par le modèle, dans l'ordre où il les
vérifie : la charge utile ne doit pas être sur OFF ; elle ne doit pas être en IMAGING ; l'équipement FPA
(0x0600) doit être alimenté ; `fpa_ready` doit valoir 1 ; et pour une phase DARK, l'équipement
obturateur (0x0603) doit être alimenté et `shutter_pos` doit valoir 0.
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — données de servitude de la charge utile
**Verify:** `payload.calibration_active == 0` (0x062A, timeout 120 s) — l'exécution est terminée
**Verify:** `payload.cal_abort_reason == 0` (0x0645, timeout 10 s) — elle s'est achevée
au lieu de s'arrêter prématurément
**Note:** `cal_abort_reason` (0x0645) est le paramètre qui indique POURQUOI un
étalonnage n'a rien produit : 1 détecteur non alimenté, 2 obturateur déplacé, 3 état de la lampe
modifié, 4 FPA sorti de sa bande de régulation, 5 abandon par l'opérateur. Sans lui, l'opérateur
voit une barre d'avancement arrêtée, sans aucune explication.
**Verify:** `payload.dark_frame_cnt` (0x0642) — images d'obscurité acquises, valeur non nulle
**GO/NO-GO:** Jeu d'images d'obscurité acquis avec `cal_abort_reason` = 0

### Étape 3a — Acquérir le jeu de champs plats
**Note:** Chaque moitié complète l'autre. `payload.cal_valid_mask` (0x0646)
atteint `0x0F` lorsque les quatre bandes disposent À LA FOIS d'un coefficient de biais et d'un coefficient de gain ;
DARK puis FLAT et FLAT puis DARK fonctionnent donc tous deux ; `PAYLOAD_START_CALIBRATION(mode=2)`
effectue les deux en une seule commande, le séquenceur de bord pilotant l'optique au
changement de phase.
**TC:** `PAYLOAD_SET_SHUTTER(position=1)` (Service 8, Subtype 1, func_id 119) — OPEN
**TC:** `PAYLOAD_CAL_LAMP(on=1)` (Service 8, Subtype 1, func_id 95) — lampe interne allumée
**TC:** `GET_PARAM(param_id=0x0615)` (Service 20, Subtype 3) — `payload.cal_lamp_on`
**Verify:** `payload.cal_lamp_on == 1` (0x0615, timeout 10 s)
**Verify:** `payload.shutter_pos == 1` (0x063C, timeout 10 s) — OPEN
**TC:** `PAYLOAD_START_CALIBRATION(mode=1)` (Service 8, Subtype 1, func_id 37) — phase FLAT
**Octets émis :** `25 01`
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — données de servitude de la charge utile
**Verify:** `payload.calibration_active == 0` (0x062A, timeout 120 s)
**Verify:** `payload.cal_abort_reason == 0` (0x0645, timeout 10 s)
**Verify:** `payload.cal_valid_mask == 15` (0x0646, timeout 10 s) — les quatre bandes
(B G R N) disposent désormais d'un coefficient de biais et d'un coefficient de gain
**TC:** `PAYLOAD_CAL_LAMP(on=0)` (Service 8, Subtype 1, func_id 95) — lampe éteinte
**GO/NO-GO:** `cal_valid_mask` = 0x0F — l'instrument est entièrement étalonné

### Étape 4 — Vérifier la qualité des données d'obscurité
**TC:** `GET_PARAM(param_id=0x0642)` (Service 20, Subtype 3) — images d'obscurité acquises
**TC:** `GET_PARAM(param_id=0x0616)` (Service 20, Subtype 3) — `payload.snr` (dB) avec le jeu d'obscurité appliqué
**Verify:** Signal d'obscurité moyen < 100 DN (échelle 12 bits, 0-4095) sous 10s
**Verify:** Écart type du signal d'obscurité < 10 DN sous 10s
**Action:** Une moyenne faible indique un courant d'obscurité minimal à la consigne de −15 °C. Un écart type faible indique une réponse uniforme du FPA. Consigner les valeurs comme référence.
**GO/NO-GO:** Statistiques des images d'obscurité conformes à la spécification

### Étape 5 — Ouvrir l'obturateur et revenir en STANDBY
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) — STANDBY
**TC:** `PAYLOAD_SET_SHUTTER(position=1)` (Service 8, Subtype 1, func_id 119) — OPEN
**Octets émis :** `77 01`
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — données de servitude de la charge utile
**Verify:** `payload.mode == 1` (0x0600, timeout 15 s) — STANDBY
**Verify:** `payload.shutter_pos == 1` (0x063C, timeout 10 s) — OPEN
**GO/NO-GO:** Obturateur ouvert, charge utile en STANDBY

### Étape 6 — Préparer le survol du site d'étalonnage
**Action:** Faire passer l'AOCS en FINE_POINT pour l'acquisition des images d'étalonnage au-dessus du site au sol connu.
**TC:** `AOCS_FINE_READY_CHECK` (Service 8, Subtype 1, func_id 89) — lire le masque des conditions préalables
**Verify:** `aocs.fine_ready == 0` (0x02C5, timeout 10 s) — tous les bits de condition préalable à zéro
**TC:** `AOCS_SET_MODE(mode=5)` (Service 8, Subtype 1, func_id 0) — FINE_POINT
**Verify:** `aocs.mode` (0x020F) = 5 (FINE_POINT) sous 30s
**Verify:** `aocs.att_error` (0x0217) < 0.1 deg sous 300s
**Action:** Attendre que le site d'étalonnage entre dans la fauchée. Le sol prédit le survol à T=XX:XX UTC +/- 30s.
**GO/NO-GO:** FINE_POINT atteint, en attente du survol du site d'étalonnage

### Étape 7 — Acquérir l'image du site d'étalonnage
**TC:** `PAYLOAD_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 26) — IMAGING
**Verify:** `payload.mode == 2` (0x0600, timeout 30 s) — IMAGING
**TC:** `PAYLOAD_CAPTURE(scene_id=0, lines=2048)` (Service 8, Subtype 1, func_id 28) — déclencher l'acquisition au survol du site  
**Octets émis :** `1C 00 00 08 00` (scene_id 0 = attribution automatique à bord ; la géolocalisation est apposée à bord)
**Verify:** `GET_PARAM(param_id=0x060C)` (Service 20, Subtype 3) — `payload.last_scene_id` s'incrémente sous 30 s
**Action:** Consigner l'horodatage de l'image, la position du satellite (GPS), l'angle solaire et la géométrie de visée pour l'analyse radiométrique.
**GO/NO-GO:** Image du site d'étalonnage acquise

### Étape 8 — Acquérir une deuxième image d'étalonnage (temps d'intégration différent)
**TC:** `PAYLOAD_SET_INTEGRATION_TIME(blue_ms=1.00, green_ms=1.00, red_ms=1.00, nir_ms=1.00)` (Service 8, Subtype 1, func_id 34) — moitié du nominal  
**Octets émis :** `22 00 64 00 64 00 64 00 64` (0.01 ms/LSB)
**TC:** `PAYLOAD_CAPTURE(scene_id=0, lines=2048)` (Service 8, Subtype 1, func_id 28) — déclencher l'acquisition  
**Octets émis :** `1C 00 00 08 00`
**Verify:** `GET_PARAM(param_id=0x0616)` (Service 20, Subtype 3) — `payload.snr` baisse d'environ 3 dB à chaque division par deux
**TC:** `PAYLOAD_SET_INTEGRATION_TIME(blue_ms=4.00, green_ms=4.00, red_ms=4.00, nir_ms=4.00)` (Service 8, Subtype 1, func_id 34) — double du nominal  
**Octets émis :** `22 01 90 01 90 01 90 01 90`
**TC:** `PAYLOAD_CAPTURE(scene_id=0, lines=2048)` (Service 8, Subtype 1, func_id 28) — déclencher l'acquisition  
**Octets émis :** `1C 00 00 08 00`
**Verify:** `GET_PARAM(param_id=0x0616)` (Service 20, Subtype 3) — `payload.snr` augmente d'environ 3 dB à chaque doublement
**Action:** Trois images à des temps d'intégration différents (nominal, moitié, double) permettent d'évaluer la linéarité du détecteur. Si le signal double lorsque le temps d'intégration double, la réponse du détecteur est linéaire.
**GO/NO-GO:** Jeu d'images de linéarité acquis

### Étape 9 — Ramener la charge utile en STANDBY
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) — STANDBY
**Verify:** `payload.mode == 1` (0x0600, timeout 15 s) — STANDBY
**TC:** `PAYLOAD_SET_INTEGRATION_TIME(blue_ms=2.00, green_ms=2.00, red_ms=2.00, nir_ms=2.00)` (Service 8, Subtype 1, func_id 34) — rétablir le nominal  
**Octets émis :** `22 00 C8 00 C8 00 C8 00 C8`
**Verify:** Temps d'intégration rétabli sous 10s
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0) — retour en NOMINAL
**Verify:** `aocs.mode == 4` (0x020F, timeout 30 s) — NOMINAL
**Note:** Le mode 3 est COARSE_SUN, un MAINTIEN en pointage solaire sans pointage nadir ; le
mode opérationnel à pointage nadir est le 4. La fiche appelait le mode 3 « NOMINAL ».
**GO/NO-GO:** Charge utile et AOCS ramenés dans leur configuration standard

### Étape 10 — Vérifier le stockage des données et programmer le vidage
**TC:** `GET_PARAM(param_id=0x0647)` (Service 20, Subtype 3) — `payload.product_mb`
**Action:** Confirmer que toutes les données d'étalonnage sont stockées (10 images d'obscurité + 3 images d'étalonnage).
**Verify:** Occupation du stockage cohérente avec ~13 images sous 10s
**TC:** `GET_PARAM(param_id=0x0648)` (Service 20, Subtype 3) — `payload.product_count`
**Action:** Programmer le vidage complet des données lors du prochain passage station sol disponible. L'ingénieur étalonnage effectuera une analyse en différé comprenant :
- l'élaboration de la carte du courant d'obscurité à partir de la moyenne des images d'obscurité ;
- la caractérisation du bruit spatial fixe ;
- l'étalonnage radiométrique absolu par rapport à la réflectance connue du site ;
- l'évaluation de la linéarité du détecteur à partir du jeu à temps d'intégration multiples ;
- le contrôle du recalage entre bandes.
**GO/NO-GO:** Données d'étalonnage recueillies et vidage programmé

## Conduite à tenir hors nominal
- Si la moyenne des images d'obscurité dépasse 200 DN : la température du FPA a peut-être dérivé vers le chaud. Contrôler `payload.fpa_temp` (0x0601). Si elle est plus chaude que -14.5 C, attendre que le refroidisseur se restabilise et contrôler
  `payload.cooler_margin_k` (0x064B). Si elle est à la consigne, un courant d'obscurité élevé peut indiquer une dégradation du FPA — consigner une anomalie et poursuivre l'étalonnage.
- Si l'obturateur ne se ferme pas : renvoyer `PAYLOAD_SET_SHUTTER(position=0)` (func 119).
  NE PAS utiliser `PAYLOAD_CYCLE_SHUTTER` pour atteindre une position connue — il compte les transitions
  de la lame ; un nombre impair aboutit donc à la position OPPOSÉE à celle de départ. En cas de persistance, le mécanisme d'obturateur est peut-être bloqué. Renoncer à l'étalonnage d'obscurité par obturateur. Acquérir à la place les images d'obscurité lors d'un passage côté nuit pendant l'éclipse (obscurité naturelle au lieu de l'obturateur mécanique).
- Si le site d'étalonnage est masqué par des nuages : procéder tout de même à l'acquisition pour faire fonctionner le détecteur. Programmer un nouvel étalonnage sur un autre site dégagé (p. ex. Sahara, Antarctique, océan). Plusieurs opportunités d'étalonnage se présentent chaque semaine.
- Si les images de linéarité montrent une réponse non linéaire (écart > 5 % par rapport à l'attendu) : consigner une anomalie. Cela peut indiquer une saturation du détecteur, un problème de CAN ou un artefact de compression. Acquérir des images supplémentaires avec des pas de temps d'intégration plus fins pour une caractérisation détaillée.
- Si le compteur d'images ne s'incrémente pas : échec d'écriture en mémoire. Contrôler la mémoire de masse via `GET_PARAM(param_id=0x060B)` — `payload.mem_used_mb` — et
  `payload.product_count` (0x0648), qui compte les produits CATALOGUÉS plutôt que
  le remplissage brut. En cas de panne de l'interface de stockage, tenter un cycle d'alimentation de la charge utile. En cas de persistance, examiner le contrôleur de mémoire de masse de l'OBDH.
- Si la température du FPA dérive pendant l'étalonnage : le refroidisseur peine peut-être sous la charge de prise de vue (dissipation du détecteur). Surveiller la tendance. Un étalonnage qui sort de la bande de régulation s'interrompt de lui-même avec
  `cal_abort_reason` (0x0645) = 4 et écarte les coefficients à moitié établis, ce qui est le
  comportement correct. Contrôler `payload.cooler_margin_k` (0x064B) : la charge de prise de vue ajoute
  2 W et coûte environ 1,1 K de relèvement atteignable ; une campagne qui tient au repos
  peut donc perdre la régulation dès la lecture du détecteur. Examiner la capacité du refroidisseur.

## Postconditions
- [ ] Jeu d'images d'obscurité acquis à la consigne opérationnelle du FPA (-15 C) avec
      `payload.cal_abort_reason` (0x0645) = 0
- [ ] Jeu de champs plats acquis ; `payload.cal_valid_mask` (0x0646) = 0x0F
- [ ] Courant d'obscurité moyen < 100 DN, écart type < 10 DN
- [ ] Image du site d'étalonnage acquise avec ses métadonnées (position, géométrie, horodatage)
- [ ] Jeu d'images à temps d'intégration multiples acquis pour l'évaluation de la linéarité
- [ ] Toutes les données d'étalonnage stockées en mémoire de masse
- [ ] Vidage des données programmé
- [ ] Charge utile ramenée en STANDBY, refroidisseur en marche
- [ ] AOCS ramené en NOMINAL (mode 4)
- [ ] Rapport d'étalonnage radiométrique à établir après l'analyse des données

## État de sortie
- Charge utile en STANDBY, refroidisseur en marche, obturateur OUVERT, temps d'intégration rétablis à la
  valeur nominale (2,00 ms), lampe d'étalonnage éteinte
- AOCS ramené en NOMINAL commandé (mode 4)
- Produits d'étalonnage stockés à bord, en attente du passage de vidage programmé

**PROCÉDURE SUIVANTE :** COM-013 (Clôture de la recette du SCAO et déclaration NOMINAL)
