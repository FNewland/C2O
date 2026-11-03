# COM-012 : Première lumière
**Sous-système :** Charge utile / AOCS
**Phase :** COMMISSIONING
**Révision :** 2.0 --- 2026-08c : l'étape de transfert d'image met désormais en œuvre la VRAIE
chaîne du service 13 (S13.1 création -> 0x062D monte -> 0x062E se vide -> S13.5
fin), qui fonctionne de bout en bout depuis les corrections du simulateur 2026-08c ---
`PAYLOAD_INITIATE_TRANSFER` (func 94) reste la commande de mise en file à bord, mais
le vidage d'un produit vers le sol passe par le S13. Codes de mode et bandes du FPA
corrigés. États d'entrée et de sortie déclarés. S'exécute AVANT COM-011 (l'étalonnage
exige une chaîne image vérifiée --- et « première lumière » désigne la PREMIÈRE image).
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-010 --- charge utile en STANDBY, refroidisseur EN MARCHE avec
`payload.fpa_ready` (0x0610) = 1 à la consigne de -15C, AOCS en NOMINAL
commandé, liaison descendante en LOW, mode DOWNLINK désactivé.

## Objet
Acquérir la première image avec l'imageur multispectral d'EOSAT-1. Faire passer la
charge utile du mode STANDBY au mode IMAGING, acquérir une scène d'essai au-dessus d'une cible
au sol connue, vérifier le stockage des données d'image en mémoire de masse, et transmettre au sol un aperçu pour
une première évaluation de la qualité. Ce jalon confirme la capacité de prise de vue de bout en bout.

## Prérequis
- [ ] COM-009 (Mise sous tension de la charge utile) terminée — charge utile en STANDBY
- [ ] COM-010 (Activation du refroidisseur du FPA) terminée — `payload.fpa_ready` (0x0610) = 1 à la consigne commandée (-15C : bande de -16.5C à -14.5C)
- [ ] AOCS en NOMINAL (mode 4) — l'étape 1 le fait passer en FINE_POINT (mode 5)
- [ ] `aocs.att_error` (0x0217) < 0.5 deg (précision de pointage suffisante pour la prise de vue)
- [ ] `eps.bat_soc` (0x0101) > 70 %
- [ ] Satellite à l'approche d'un site d'étalonnage au sol connu (p. ex. Libya-4, Railroad Valley)
- [ ] Stockage à bord vérifié disponible (COM-009, étape 7)
- [ ] Liaison bidirectionnelle en bande S active
- [ ] Ingénieurs charge utile et AOCS en console

## Déroulement

### Étape 1 — Faire passer l'AOCS en FINE_POINT
**TC:** `AOCS_FINE_READY_CHECK` (func 89) — vérifier que le masque de bits de conditions préalables 0x02C5
vaut 0 (le mode 5 est sinon refusé par une TM(1,8))
**TC:** `AOCS_SET_MODE(mode=5)` (Service 8, Subtype 1)
**Verify:** `aocs.mode` (0x020F) = 5 (FINE_POINT) sous 30s
**Verify:** `aocs.total_pointing_err_3sig` (0x02AA) < 0.05 deg sous 300s
(le verrou d'acquisition de la charge utile)
**Verify:** `aocs.att_error` (0x0217) < 0.1 deg sous 180s
**Verify:** `aocs.rate_pitch` (0x0205) dans la plage [0.053, 0.073] deg/s sous 180s (le suivi du nadir impose la vitesse orbitale, +0.063 deg/s sur cette console ; une vitesse de tangage nulle signifierait que le satellite NE suit PAS le nadir)
**Verify:** `aocs.rate_yaw` (0x0206) < 0.01 deg/s sous 180s
**GO/NO-GO:** FINE_POINT atteint — la précision de pointage satisfait l'exigence de prise de vue

### Étape 2 — Vérifier la température du FPA avant la prise de vue
**TC:** `GET_PARAM(param_id=0x0601)` (Service 20, Subtype 3) — température du FPA
**Verify:** `payload.fpa_temp` (0x0601) dans la plage [-16.5C, -14.5C] sous 10s —
la bande de consigne de -15C (`payload.fpa_ready` 0x0610 = 1 exprime la même chose)
**GO/NO-GO:** FPA à la température opérationnelle

### Étape 3 — Vérifier que la charge utile est prête pour la prise de vue
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27)
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) sous 10s
**TC:** `GET_PARAM(param_id=0x0604)` (Service 20, Subtype 3) — `payload.store_used` (remplissage de la mémoire, %)
**Verify:** `payload.store_used` (0x0604) < 97 % (au moins 500 MB libres sur les 20 GB de la mémoire pour l'image d'essai) sous 10s
**TC:** `GET_PARAM(param_id=0x0605)` (Service 20, Subtype 3) — `payload.image_count`
**Verify:** Consigner `payload.image_count` (0x0605) comme référence avant acquisition sous 10s
**TC:** `GET_PARAM(param_id=0x060B)` (Service 20, Subtype 3) — `payload.mem_used_mb` (mémoire charge utile utilisée au total, Mo)
**Verify:** Consigner `payload.mem_used_mb` (0x060B) comme référence avant acquisition sous 10s
**GO/NO-GO:** Charge utile prête à passer en IMAGING

### Étape 4 — Commander la charge utile en mode IMAGING
**TC:** `PAYLOAD_SET_MODE(mode=2)` (Service 8, Subtype 1)
**Verify:** `payload.mode` (0x0600) = 2 (IMAGING) sous 30s
**Action:** L'intégration du détecteur de la charge utile commence. L'acquisition d'image démarrera au prochain déclenchement de scène valide ou à la prochaine acquisition commandée.
**GO/NO-GO:** Charge utile en mode IMAGING

### Étape 5 — Déclencher l'acquisition de la première image
**TC:** `PAYLOAD_CAPTURE(scene_id=1, lines=2048)` (Service 8, Subtype 1, func_id 28) — déclencher l'acquisition de première lumière  
**Octets émis :** `1C 00 01 08 00` (identifiant de produit 1 attribué par le sol ; la géolocalisation est apposée à bord à partir des éphémérides à l'ouverture de l'obturateur)
**Action:** La charge utile acquiert une image multispectrale plein format. Le temps d'intégration est automatique, fondé sur l'estimation de la luminance de la scène. Volume de données attendu : une image fait 4 Mo brute et est stockée sur 1.0-2.7 Mo après compression à bord.
**Verify:** `GET_PARAM(param_id=0x060C)` (Service 20, Subtype 3) — `payload.last_scene_id` = 1 sous 30 s
**Verify:** `GET_PARAM(param_id=0x0605)` (Service 20, Subtype 3) — `payload.image_count` incrémenté à 1 sous 10 s
**GO/NO-GO:** Première image acquise avec succès

### Étape 6 — Vérifier l'écriture des données d'image en mémoire
**TC:** `GET_PARAM(param_id=0x0604)` (Service 20, Subtype 3) — `payload.store_used` (remplissage de la mémoire, %)
**Action:** Comparer au stockage avant acquisition. La différence doit correspondre au volume de données de l'image.
**Verify:** `payload.store_used` (0x0604) en hausse (image stockée) sous 10s
**TC:** `GET_PARAM(param_id=0x060B)` (Service 20, Subtype 3) — `payload.mem_used_mb` (mémoire charge utile utilisée au total, Mo)
**Verify:** La variation de `payload.mem_used_mb` (0x060B) depuis la référence de l'étape 3 est de 1.0-4.0 Mo sous 10s --- une image stockée (1.0-2.7 Mo compressée, au plus la trame brute de 4 Mo). 0x060B est la mémoire utilisée TOTALE ; seule la différence mesure le nouveau produit
**GO/NO-GO:** Données d'image stockées en mémoire de masse

### Étape 7 — Ramener la charge utile en STANDBY
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1)
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) sous 15s
**Verify:** `tcs.cooler_fpa` (0x040C) = 0 sous 10 s --- le mode STANDBY arrête le refroidisseur du FPA (2026-11-03)
**Action:** La charge utile revient en STANDBY et le refroidisseur du FPA s'arrête (environ 15 W de charge en moins). Les données d'image restent en mémoire.
**GO/NO-GO:** Charge utile ramenée sans incident en STANDBY après l'acquisition

### Étape 8 — Vider le produit par le service 13
**Action:** Transmettre au sol le produit de première lumière par la véritable chaîne de données en masse.
Monter d'abord dans l'échelle : HIGH exige le mode DOWNLINK + l'antenne déployée
(COM-006) ; la règle des 10° d'élévation relève de la politique d'autorisation SOL, ce n'est pas un
verrou bord.
**TC:** `TTC_SET_DOWNLINK_MODE(on=1)` (Service 8, Subtype 1, func_id 79)
**TC:** `TTC_SET_DATA_RATE(rate=1)` (Service 8, Subtype 1, func_id 65) — HIGH
**Verify:** `ttc.tm_data_rate` (0x0506) = 128000 bps sous 10 s
**TC:** `S13_CREATE_TRANSFER(scene_id=1, size_mb=0)` (Service 13, Subtype 1) — ouvrir le transfert sur le produit de première lumière catalogué
**Verify:** Rapport d'ouverture de transfert TM(13,2) reçu sous 10 s — consigner
l'identifiant de transfert, `total_blocks` et le CRC-32 (le sol contrôle le produit
reconstitué par rapport à celui-ci)
**Verify:** `payload.transfer_active` (0x062D) = 1 sous 15 s
**Verify:** `payload.transfer_progress` (0x062E) en hausse sur les échantillons successifs
du SID 5 — le transfert se vide au débit d'information ACTIF et se bloque
si la liaison tombe
**TC:** `S13_REPORT_STATUS(transfer_id=T)` (Service 13, Subtype 9) — état à mi-vidage
**TC:** `S13_END_TRANSFER(transfer_id=T)` (Service 13, Subtype 5) — fermer la session
**Verify:** `payload.transfer_active` (0x062D) = 0 sous 15 s
**Note:** La fermeture d'une session ENTIÈREMENT vidée supprime le produit à bord et
libère son espace de stockage ; une session partielle le laisse pour le passage suivant.
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) — retour en LOW
**TC:** `TTC_SET_DOWNLINK_MODE(on=0)` (Service 8, Subtype 1, func_id 79) — libérer le verrou
**Verify:** `ttc.tm_data_rate` (0x0506) = 16000 bps et `ttc.downlink_mode` (0x053C) = 0
**Action:** Calculer au sol le CRC-32 du produit reconstitué et le comparer à la valeur
de la TM(13,2) ; l'équipe charge utile évalue la géométrie, la présence des bandes, les pixels morts et le contenu.
**GO/NO-GO:** Produit vidé par le S13, somme de contrôle correcte, HIGH libéré

### Étape 9 — Évaluation de la première lumière
**Action:** L'équipe charge utile procède à une évaluation préliminaire de l'image d'aperçu :
- géométrie de la scène conforme à la position prédite de la trace au sol ;
- toutes les bandes multispectrales présentes dans les données ;
- aucun artefact d'image systématique (rayures, bandes, saturation) ;
- courant d'obscurité du FPA cohérent avec la consigne de fonctionnement de −15 °C ;
- image ni vide ni entièrement saturée.
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0) — quitter FINE_POINT, retour en NOMINAL commandé
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — relecture de l'état AOCS
**Verify:** `aocs.mode` (0x020F) = 4 sous 30s
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — contrôle final de l'état de la charge utile
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) sous 10s
**Verify:** `payload.cooler_pwr` (0x0602) = 0 sous 10s --- le refroidisseur a été arrêté à l'étape 7 (STANDBY) ; le FPA se réchauffe vers son équilibre non refroidi
**Action:** Consigner l'horodatage de la première lumière, les métadonnées de l'image et l'évaluation préliminaire de la qualité. Diffuser le rapport de première lumière.
**GO/NO-GO:** Jalon de première lumière atteint — chaîne image fonctionnelle

## Conduite à tenir hors nominal
- Si FINE_POINT n'est pas atteint avant le survol de la cible : le verrou d'acquisition EXIGE FINE_POINT avec une erreur totale < 0.05 deg — il refusera en NOMINAL. Relancer le contrôle de disponibilité FINE, corriger le bit de masque indiqué, et viser le survol suivant.
- Si la charge utile ne passe pas en IMAGING (mode 2) : réessayer une fois. En cas de persistance, contrôler la température de l'électronique de l'imageur (`payload.imager_temp`) via `GET_PARAM(param_id=0x0603)` et la température du FPA via `GET_PARAM(param_id=0x0601)`. La charge utile peut refuser IMAGING si le FPA n'est pas à la consigne. Revenir en STANDBY et rechercher la cause.
- Si `payload.last_scene_id` ne progresse pas : contrôler les verrous d'acquisition — `payload.mode` (0x0600) = 2, `payload.fpa_ready` (0x0610) = 1, `aocs.mode` (0x020F) = 5 FINE_POINT avec une erreur totale (0x02AA) < 0.05 deg. Une acquisition refusée renvoie une TM(1,8) nommant le verrou en défaut. Si l'intégration du détecteur a échoué, relancer l'acquisition. En cas de persistance, contrôler l'électronique du FPA via `HK_REQUEST(sid=5)`. Effectuer un cycle d'alimentation de la charge utile si nécessaire.
- Si l'image stockée est vide ou très petite (variation de 0x060B < 0.5 Mo) : échec d'écriture des données. Contrôler l'interface de la mémoire de masse. Relancer l'acquisition. Si le stockage est plein, supprimer les données d'essai et réessayer.
- Si l'aperçu montre une image entièrement sombre : vérifier si le satellite survolait le côté nuit. Vérifier que le pointage AOCS était nadir. Si l'image a été prise côté jour et reste sombre, examiner le biais du détecteur du FPA ou le mécanisme d'obturateur.
- Si le produit transmis au sol est saturé (l'aperçu montre des zones blanches écrêtées sur les scènes claires) : le temps d'intégration est trop long pour la scène. Commander `PAYLOAD_SET_INTEGRATION_TIME(blue_ms=1.00, green_ms=1.00, red_ms=1.00, nir_ms=1.00)` (func_id 34, octets `22 00 64 00 64 00 64 00 64`) ou réduire le gain avec `PAYLOAD_SET_GAIN(gain=0.500)` (func_id 35, octets `23 01 F4`) et réessayer à l'opportunité suivante.

## Postconditions
- [ ] Première image acquise et stockée en mémoire de masse
- [ ] Produit vidé par le S13 avec CRC-32 vérifié
- [ ] Géométrie de la scène, contenu spectral et qualité d'image : résultat préliminaire PASS
- [ ] Charge utile ramenée en STANDBY (refroidisseur arrêté)
- [ ] Métadonnées de l'image et indicateurs de qualité consignés
- [ ] Rapport de première lumière diffusé à l'équipe de mission

## État de sortie
- Charge utile en STANDBY, refroidisseur arrêté (le mode STANDBY l'arrête), `payload.transfer_active` (0x062D) = 0
- AOCS ramené en NOMINAL commandé (mode 4) après la fenêtre de prise de vue
- Liaison descendante revenue en LOW, mode DOWNLINK libéré — le verrou HIGH n'est jamais laissé
  ouvert en sortie de fiche
- Produit de première lumière vidé (supprimé à bord si la session s'est achevée)

**PROCÉDURE SUIVANTE :** COM-011 (Étalonnage radiométrique de la charge utile)
