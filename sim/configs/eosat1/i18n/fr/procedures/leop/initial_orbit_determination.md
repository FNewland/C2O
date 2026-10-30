# LEOP-003 : Restitution d'orbite initiale
**Sous-système :** AOCS / dynamique du vol
**Phase :** LEOP
**Révision :** 2.0 --- refonte du déroulement 2026-08c. C'est désormais la DERNIÈRE fiche LEOP : elle
s'exécute APRÈS la mise sous tension du récepteur GPS (LEOP-007), la synchronisation de l'horloge
(LEOP-006) et l'activation du SID HK 12, vérifie la solution PVT sur les paramètres
que le satellite transmet réellement au sol (0x0210-0x0212 / 0x0231-0x0236 --- l'ancienne
fiche lisait 0x0230-0x0236 comme latitude/longitude/altitude, qui sont désormais l'état ECEF), et
clôt la LEOP par la déclaration de la phase 5.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de LEOP-006 --- maintien solaire COARSE_SUN, horloge référencée
(0x0A13 dans {1,2,3}), récepteur GPS sur ON avec `aocs.gps_fix` (0x0274) >= 2, SID HK
12 (GPS_NAV) activé et émis toutes les 8 s.

## Objet
Vérifier la solution de navigation GPS de bord, comparer l'orbite mesurée à
l'orbite héliosynchrone prédite par le lanceur, diffuser les éléments affinés
à la dynamique du vol et au réseau de stations sol --- puis, sur un GO de toutes les
positions, DÉCLARER LA FIN DE LA LEOP en commandant la phase de mission 5
(COMMISSIONING). Rien à bord ne fait avancer la phase au-delà de 4 ; la déclaration
est la télécommande de vol propre à cette fiche, envoyée une seule fois, ici et nulle part ailleurs.

## Prérequis
- [ ] LEOP-001 à LEOP-007 (ordre définitif 001, 002, 004, 007, 005,
      006) terminées
- [ ] `aocs.gps_fix` (0x0274) >= 2 et SID HK 12 sur la liaison descendante (LEOP-006)
- [ ] Temps bord référencé (`obdh.time_ref` 0x0A13 != 0, LEOP-006)
- [ ] Liaison bidirectionnelle en bande S active sur un passage programmé
- [ ] Équipe de dynamique du vol prête, avec le TLE prédit fourni par le fournisseur de lancement

## Déroulement

### Étape 1 --- Vérifier que la solution de navigation GPS est transmise
**TC:** `HK_REQUEST(sid=12)` (Service 3, Subtype 27) --- rapport GPS_NAV ponctuel
**Verify:** `aocs.gps_fix` (0x0274) >= 2 sous 10s --- point 3D (0=aucun, 1=2D, 2=3D, 3=3D+vitesse)
**Verify:** `aocs.gps_num_sats` (0x0276) >= 4 sous 10s --- satellites en nombre suffisant pour une solution 3D
**Verify:** `aocs.gps_pdop` (0x0275) rapporté sous 10s --- consigner la dilution
**Note:** Les canaux PVT sont « honnêtement invalides » : la position (0x0210-0x0212,
0x0231-0x0233) vaut zéro en dessous du point de type 2 et la vitesse (0x0234-0x0236) vaut zéro
en dessous du type 3. Une solution à zéro signifie ici ATTENDRE le point, et non « l'orbite est
au centre de la Terre ».
**GO/NO-GO:** Qualité du point suffisante pour la restitution d'orbite

### Étape 2 --- Lire le point de position
**TC:** `GET_PARAM(param_id=0x0210)` (Service 20, Subtype 3) --- `aocs.gps_lat` (deg)
**TC:** `GET_PARAM(param_id=0x0211)` (Service 20, Subtype 3) --- `aocs.gps_lon` (deg)
**TC:** `GET_PARAM(param_id=0x0212)` (Service 20, Subtype 3) --- `aocs.gps_alt` (km)
**Verify:** `aocs.gps_lat` (0x0210) dans la plage [-90, +90] sous 10s
**Verify:** `aocs.gps_lon` (0x0211) dans la plage [-180, +180] sous 10s
**Verify:** `aocs.gps_alt` (0x0212) dans la plage [495 km, 540 km] sous 10s --- la plage de CONTRÔLE
**Note:** Plage de contrôle = intervalle d'altitude géodésique propagé à partir du TLE (503-530 km sur
une orbite, moyenne 513 km) plus ~8-10 km de marge. L'ancienne déclaration de 450 km
a été abandonnée par la décision du propriétaire de 2026-08 : le TLE de orbit.yaml
(moyen mouvement 15,24 tours/jour) fait foi et `altitude_km` enregistre désormais la
moyenne propagée, 513 km.
**Note:** La plage plus large de 400-550 km est la plage d'ANOMALIE (conduite à tenir
hors nominal) : ce n'est qu'en dehors de celle-ci que l'injection elle-même est suspecte. Une lecture
hors de la plage de contrôle mais dans la plage d'anomalie fait échouer ce contrôle --- vérifier le PDOP,
prendre un second point et le signaler à la dynamique du vol.
**GO/NO-GO:** Point de position valide et altitude dans la plage de contrôle de 495-540 km

### Étape 3 --- Lire le vecteur d'état ECEF
**TC:** `GET_PARAM(param_id=0x0231)` (Service 20, Subtype 3) --- ECEF X (m)
**TC:** `GET_PARAM(param_id=0x0232)` (Service 20, Subtype 3) --- ECEF Y (m)
**TC:** `GET_PARAM(param_id=0x0233)` (Service 20, Subtype 3) --- ECEF Z (m)
**TC:** `GET_PARAM(param_id=0x0234)` (Service 20, Subtype 3) --- vitesse ECEF X (m/s)
**TC:** `GET_PARAM(param_id=0x0235)` (Service 20, Subtype 3) --- vitesse ECEF Y (m/s)
**TC:** `GET_PARAM(param_id=0x0236)` (Service 20, Subtype 3) --- vitesse ECEF Z (m/s)
**Verify:** Norme de la position sqrt(X^2+Y^2+Z^2) dans la plage [6700 km, 6950 km]
**Verify:** Norme de la vitesse dans la plage [7400 m/s, 7900 m/s] --- vitesse d'orbite
circulaire à l'altitude mesurée (sqrt(mu/a), mu = 398600.4418 km^3/s^2)
**Action:** Consigner le vecteur d'état complet avec son horodatage GPS pour la dynamique
du vol.
**GO/NO-GO:** Vecteur d'état cohérent (r x v plausible pour une LEO quasi circulaire)

### Étape 4 --- Comparaison par la dynamique du vol
**Action:** Transmettre le vecteur d'état issu du GPS à la dynamique du vol. La dynamique
du vol calcule les éléments osculateurs et les compare à l'orbite prédite par le lanceur :
inclinaison à 0,2° près de 97,39°, excentricité < 0,01, LTAN
à 15 minutes près de l'exigence de mission.
**Action:** Confirmer la période orbitale à partir du moyen mouvement du TLE ; noter
l'écart d'altitude relevé à l'étape 2 dans la comparaison.
**GO/NO-GO:** Éléments orbitaux cohérents avec une injection héliosynchrone

### Étape 5 --- Contrôle de cohérence d'un second point
**Action:** Attendre 10 minutes (le SID 12 continue d'échantillonner toutes les 8 s).
**TC:** `HK_REQUEST(sid=12)` (Service 3, Subtype 27) --- second rapport GPS_NAV
**Verify:** `aocs.gps_alt` (0x0212) à 20 km près de la lecture de l'étape 2
**Verify:** `aocs.gps_fix` (0x0274) toujours >= 2
**Action:** Confirmer que la position s'est déplacée le long de la trace de façon cohérente avec
l'orbite propagée sur l'intervalle.
**GO/NO-GO:** Points GPS cohérents et reproductibles

### Étape 6 --- Diffuser le rapport de restitution d'orbite
**Action:** Rassembler toutes les lectures GPS, les éléments calculés, la comparaison avec
l'orbite prédite et la vérification du LTAN. Diffuser le rapport de restitution
d'orbite et le TLE affiné au réseau de stations sol pour la mise à jour des
prédictions de passage.
**GO/NO-GO:** Restitution d'orbite terminée

### Étape 7 --- Tour de table GO/NO-GO et déclaration de phase de FIN DE LEOP
**Action:** Le FD lance le tour de table GO/NO-GO sur toutes les positions. Chaque position
rend compte de l'état de son sous-système. C'est le SEUL endroit où la déclaration de phase 5 est
envoyée ; aucune autre fiche ne la contient.
**Note:** La commande est `critical` --- la phase conditionne l'acceptation des télécommandes,
le mode satellite dérivé, l'armement de la FDIR et le verrouillage d'armement de la propulsion ---
relire donc l'argument avant de déclarer l'étape terminée. C'est aussi la
commande rapide du FD (groupe OBDH, « Set Mission Phase ») dans le MCS.
**TC:** `SYS_SET_MISSION_PHASE(phase=5, flags=0)` (Service 8, Subtype 1, func_id 120)
**Verify:** `eps.spacecraft_phase` (0x0129) = 5 sous 5s
**Action:** Confirmer que l'événement `MISSION_PHASE_CHANGED` (0x0055) apparaît dans le
journal des événements avec `4 (LEOP) -> 5 (COMMISSIONING)`.
**GO/NO-GO:** Toutes les positions GO ; phase = COMMISSIONING --- la LEOP est terminée

## Conduite à tenir hors nominal
- Si `aocs.gps_fix` < 2 : confirmer que l'équipement récepteur est sur ON (`S2_AOCS_GPS_RECEIVER` équipement 0x020F, LEOP-007). Attendre la fin du démarrage à froid (jusqu'à 15 min). Sans point au bout de 30 minutes, se rabattre sur les mesures de distance et Doppler sol du réseau de stations pour l'orbite initiale et programmer une investigation GPS pendant la recette en orbite ; la déclaration de phase peut tout de même avoir lieu sur une orbite restituée depuis le sol, avec l'accord du FD.
- Si le SID 12 est absent de la liaison descendante : `HK_ENABLE(sid=12)` (Service 3, Subtype 5) a été oublié ou perdu (LEOP-006, étape 6a) --- le renvoyer.
- Si l'altitude sort même de la plage d'anomalie [400, 550] km : vérifier d'abord le PDOP. Avec un bon point, il s'agit d'une anomalie d'injection --- alerter la dynamique du vol et évaluer une manœuvre de correction avant de déclarer la phase 5.
- Si l'inclinaison s'écarte de 97,39° de plus de 0,2° : le signaler à la dynamique du vol ; la précession héliosynchrone et la durée de vie de la mission sont affectées.
- Si `SYS_SET_MISSION_PHASE` est refusée : 0x0C03 signifie que l'OBC est (de nouveau) dans le chargeur d'amorçage --- exécuter d'abord de nouveau LEOP-001, étape 5, puis LEOP-006. 0x0C04 signifie une déclaration à rebours sans FORCE.

## État de sortie
- Phase de mission = 5 (COMMISSIONING) ; `sat.mode` (0x0001) dérive toujours SAFE ---
  seule la déclaration de phase 6 à la FIN de la recette en orbite (COM-013) déverrouille
  NOMINAL
- Satellite toujours en maintien COARSE_SUN, roues désactivées, charge utile éteinte ---
  exactement l'état d'entrée déclaré par COM-001
- Récepteur GPS sur ON, SID 12 émis (laissé en fonctionnement : la recette en orbite et les
  opérations nominales l'utilisent)

## Postconditions
- [ ] PVT GPS vérifiée sur les canaux du SID 12 transmis au sol
- [ ] Vecteur d'état consigné et remis à la dynamique du vol
- [ ] Rapport de restitution d'orbite + TLE affiné diffusés
- [ ] Phase 5 déclarée (événement 0x0055 journalisé) --- LEOP terminée

**PROCÉDURE SUIVANTE :** Recette en orbite, en commençant par COM-001 (Vérification de l'EPS). L'ordre définitif
de la recette en orbite est COM-001 à COM-013 tel qu'indexé, avec COM-004 (activation
des roues, NOMINAL commandé) AVANT COM-003 (étalonnage des capteurs), conformément à la
décision de l'auteur Q16.
