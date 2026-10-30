# LEOP-007 : Mise sous tension séquentielle

**Sous-système :** Tous
**Phase :** LEOP
**Révision :** 3.0 --- refonte du déroulement 2026-08c. La LEOP n'alimente QUE ce dont la LEOP a besoin :
les réchauffeurs si nécessaire, l'ensemble AOCS (magnétomètre, magnétocoupleurs, GPS) et le
mode DETUMBLE. La ligne charge utile et le refroidisseur du FPA sont des charges de recette en orbite et ont
été déplacés dans COM-009 / COM-010 ; les roues de réaction restent DÉSACTIVÉES jusqu'à COM-004 ;
la transition vers COARSE_SUN est AUTOMATIQUE et s'observe dans LEOP-005, elle n'est pas
commandée ici ; la déclaration de phase 5 a été déplacée dans LEOP-003, la dernière
fiche LEOP.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de LEOP-004 --- image applicative en cours d'exécution, liaison en LOW,
panneaux déployés et produisant de l'énergie, toutes les lignes commutables sauf `ttc_tx` sur OFF,
satellite en rotation aux vitesses de séparation, AOCS en MODE_OFF.

## Objet
Mettre en service les lignes d'alimentation EPS et les modes de sous-systèmes dont le RESTE DE LA LEOP
a besoin --- pas davantage --- dans l'ordre des dépendances, en vérifiant chaque étape avant la suivante.
À savoir : les lignes de réchauffeurs si (et seulement si) leurs zones ont besoin de chaleur ; la ligne de
l'ensemble AOCS ; les équipements magnétomètre, magnétocoupleurs et récepteur GPS ; et la
transition commandée vers DETUMBLE. Tout le reste demeure éteint et relève de
la fiche de recette en orbite qui l'utilise.

## Prérequis
- [ ] LEOP-001, LEOP-002, LEOP-004 terminées (`obdh.sw_image` 0x0311 = 1,
      panneaux déployés)
- [ ] Passage station sol programmé en cours (ou passage suivant réservé ---
      les étapes 1-6 tiennent dans un seul contact de 8 minutes)
- [ ] SoC de la batterie > 60 % et tension du bus 26-30V (vérifiés à l'étape 1)

## Ce que cette fiche n'alimente PAS (et qui s'en charge)
| Charge | Reste | Alimentée par |
|---|---|---|
| `payload` (ligne 3) | OFF | COM-009 Mise sous tension de la charge utile |
| `fpa_cooler` (ligne 4) | OFF | COM-010 Activation du refroidisseur du FPA (toute voie de refroidissement l'alimente) |
| Roues de réaction (état d'activation) | DÉSACTIVÉES | COM-004 Vérification des actionneurs (`AOCS_ENABLE_WHEEL` x4) |
| Senseurs stellaires / gyromètres | OFF | COM-003 Étalonnage des capteurs |
| `prop` (ligne 8) | OFF | Préparation des manœuvres NOM-004/NOM-013 uniquement |

Noter que la ligne EPS `aocs_wheels` (7) alimente l'ENSEMBLE AOCS ---
capteurs, magnétocoupleurs, GPS et électronique de commande des roues sans distinction --- et doit donc être
alimentée ici ; l'alimenter n'active PAS les roues (`aocs.wheels_enabled`
0x0260 reste à 0 jusqu'à COM-004, par conception : une commutation de ligne d'alimentation ne doit jamais
rendre silencieusement l'autorité d'attitude à la boucle de contrôle).

## Déroulement

### Étape 1 --- Vérifier l'état de référence de l'EPS
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.bus_voltage` (0x0105) dans la plage [26.0V, 30.0V] sous 10s
**Verify:** `eps.bat_soc` (0x0101) > 60 % sous 10s
**Verify:** `eps.power_gen` (0x0107) > 20W (panneaux déployés, éclairement partiel)
**GO/NO-GO:** État de référence de l'EPS nominal

### Étape 2 --- Alimenter les lignes de réchauffeurs SI NÉCESSAIRE (conditionnel)
**Action:** Lire `tcs.temp_battery` (0x0407) et `tcs.temp_obc` (0x0406) dans
le flux SID 3 en cours. N'alimenter une ligne de réchauffeur QUE si sa zone a besoin de chaleur ;
une ligne de réchauffeur alimentée « parce que la fiche le dit » est exactement la dérive d'état que
le propriétaire a rencontrée en vol --- COM-002 a ensuite trouvé un réchauffeur dont l'alimentation était cyclée alors qu'il
n'avait jamais été légitimement allumé.
**TC:** `EPS_POWER_ON(line_index=5)` (Service 8, Subtype 1, func_id 19) --- htr_bat, UNIQUEMENT si `tcs.temp_battery` < +5C
**Verify:** `eps.pl_htr_bat` (0x0115) = 1 sous 5s --- seulement si commandée
**TC:** `EPS_POWER_ON(line_index=6)` (Service 8, Subtype 1, func_id 19) --- htr_obc, UNIQUEMENT si `tcs.temp_obc` < 0C
**Verify:** `eps.pl_htr_obc` (0x0116) = 1 sous 5s --- seulement si commandée
**Action:** Consigner dans le journal LEOP QUELLES lignes de réchauffeurs cette fiche a alimentées (la
vérification des réchauffeurs de COM-002 lit cet enregistrement comme état d'entrée).
**GO/NO-GO:** Zones thermiques protégées ; lignes non commandées confirmées toujours coupées

### Étape 3 --- Alimenter la ligne de l'ensemble AOCS et activer ses données de servitude
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19) --- aocs_wheels (l'alimentation de l'ensemble AOCS)
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 1 sous 5s
**Note:** L'AOCS est toujours en MODE_OFF --- la ligne sous tension permet seulement au modèle
de tourner. Alimenter la ligne n'active PAS le SID 2 : l'ensemble activé à la mise sous tension est
`simulation.yaml` `default_enabled_sids: [1, 11]` ; le SID 2 doit donc être activé
explicitement par commande.
**TC:** `HK_ENABLE(sid=2)` (Service 3, Subtype 5) --- activer les données de servitude AOCS périodiques
**Verify:** Le SID 2 périodique commence à être émis en l'espace d'une période de structure de 4 s
**Verify:** `aocs.wheels_enabled` (0x0260) = 0 --- roues DÉSACTIVÉES, comme prévu
**GO/NO-GO:** Ensemble AOCS alimenté, SID 2 transmis, roues toujours désactivées

### Étape 4 --- Activer les capteurs et actionneurs de DETUMBLE AVANT de commander ce mode
**Action:** DETUMBLE est la loi B-dot : magnétomètre en entrée, magnétocoupleurs en sortie.
Depuis 2026-08c, la commande de mode REFUSE explicitement si l'une des branches manque
(0x0A20 pas de magnétomètre, 0x0A21 pas de magnétocoupleurs, 0x0004 ligne coupée) --- cette
étape établit donc D'ABORD les deux branches.
**TC:** `S2_AOCS_MAGNETOMETER(device_id=521, state=1)` (Service 2, Subtype 1) --- l'unique magnétomètre 3 axes (équipement 0x0209)
**TC:** `MTQ_ENABLE(enable=1)` (Service 8, Subtype 1, func_id 9) --- jeu de magnétocoupleurs
**TC:** `S2_AOCS_GPS_RECEIVER(device_id=527, state=1)` (Service 2, Subtype 1) --- récepteur GPS (équipement 0x020F) ; LEOP-006 (temps) et LEOP-003 (orbite) ont besoin que son TTFF coure dès maintenant
**Verify:** `aocs.mtq_enabled` (0x025E) = 1 sous 10s
**GO/NO-GO:** Magnétomètre et magnétocoupleurs activés, récepteur GPS en acquisition

### Étape 5 --- Commander DETUMBLE et vérifier sur la télémesure du magnétomètre
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0) --- DETUMBLE
**Note:** Il s'agit d'une transition COMMANDÉE (voir
`docs/plan_2026-08c/AOCS_MODE_TRANSITIONS.md` 1.1). Le func_id 0 est exempté du
verrou de mode du sous-système ; il peut donc faire sortir l'AOCS de OFF.
**Verify:** Acceptation S1.1 + fin d'exécution S1.7 reçues sous 5s
**Verify:** `aocs.mode` (0x020F) = 2 (DETUMBLE) sous 10s
**Verify:** `aocs.mag_enabled` (0x025C) = 1 sous 10s --- magnétomètre valide
**Verify:** `aocs.mag_x` (0x020B), `aocs.mag_y` (0x020C), `aocs.mag_z` (0x020D)
indiquent un champ mesuré en repère satellite sous 10s
**Verify:** `aocs.mag_field_total` (0x0277) dans la plage [5000, 70000] nT ---
norme de champ plausible en LEO, cohérente avec sqrt(Bx^2+By^2+Bz^2)
**Verify:** `aocs.rate_roll`, `aocs.rate_pitch`, `aocs.rate_yaw`
(0x0204..0x0206) rapportées ; en décroissance sous 60s
**GO/NO-GO:** AOCS en DETUMBLE avec une mesure de champ active, vitesses angulaires
en décroissance

### Étape 6 --- Confirmer l'état d'alimentation de sortie
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.pl_payload` (0x0113) = 0 --- ligne charge utile toujours sur OFF (relève de COM-009)
**Verify:** `eps.pl_fpa_cooler` (0x0114) = 0 --- ligne du refroidisseur toujours sur OFF (relève de COM-010)
**Verify:** `eps.pl_prop` (0x014A) = 0 --- ligne de propulsion toujours sur OFF
**Verify:** `aocs.wheels_enabled` (0x0260) = 0 --- roues toujours DÉSACTIVÉES (relève de COM-004)
**Verify:** Marge de puissance positive : `eps.power_gen` (0x0107) supérieure à la charge
indiquée par `eps.power_cons` (0x0106), ou SoC stable/en hausse
**GO/NO-GO:** Seules les charges LEOP sont actives ; marge positive

## Conduite à tenir hors nominal
- **SoC inférieur à 40 % :** ARRÊTER, délester la dernière ligne alimentée (`EPS_POWER_OFF`), attendre que la charge remonte > 60 %, puis continuer.
- **`AOCS_SET_MODE(mode=2)` refusée avec 0x0004 :** l'écriture de la ligne `aocs_wheels` n'a pas pris. Renvoyer `EPS_POWER_ON(line_index=7)`, vérifier 0x0117, réessayer.
- **Refus avec 0x0A20 (pas de magnétomètre) :** la commande d'équipement S2 de l'étape 4 n'a pas pris ou l'unité est défaillante. Renvoyer `S2_AOCS_MAGNETOMETER(device_id=521, state=1)` ; si le refus persiste, il s'agit d'une anomalie matérielle --- il n'y a pas de magnétomètre redondant.
- **Refus avec 0x0A21 (pas de magnétocoupleurs) :** renvoyer `MTQ_ENABLE(enable=1)` et contrôler l'état de chaque barreau (équipements 0x020B-0x020D).
- **Les vitesses angulaires ne diminuent pas en DETUMBLE :** vérifier 0x025C = 1 et la plausibilité de 0x0277 (un champ à zéro signifie que le magnétomètre est coupé ou défaillant). Si les vitesses augmentent, commander `AOCS_SET_MODE(mode=0)` (OFF) et analyser la cause.
- **Tension du bus < 26V :** délestage immédiat selon CTG-001 ; couper d'abord la ligne activée le plus récemment.

## État de sortie
- Lignes de réchauffeurs : telles que consignées à l'étape 2 (chacune sur ON seulement si sa zone avait besoin de chaleur)
- Ligne `aocs_wheels` sur ON ; SID 2 activé ; magnétomètre + MTQ activés ; récepteur
  GPS sur ON et en acquisition ; AOCS en DETUMBLE, vitesses en décroissance
- Roues DÉSACTIVÉES (0x0260 = 0) ; lignes payload / fpa_cooler / prop sur OFF
- Aucun changement de palier de débit, de mode de liaison descendante ou de mode OBC effectué par cette fiche

## Postconditions
- [ ] État d'alimentation LEOP établi exactement selon le tableau ci-dessus
- [ ] DETUMBLE actif avec une télémesure magnétomètre active
- [ ] Marge de puissance positive
- [ ] Le journal LEOP indique quelles lignes de réchauffeurs ont été alimentées

**PROCÉDURE SUIVANTE :** LEOP-005 (Acquisition du Soleil --- OBSERVE le passage automatique
DETUMBLE -> COARSE_SUN ; rien à commander)
