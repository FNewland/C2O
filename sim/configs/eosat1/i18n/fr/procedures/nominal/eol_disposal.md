# NOM-014 : Retrait de service en fin de vie (abaissement du périgée et passivation)

**Sous-système :** Propulsion / dynamique du vol / tous sous-systèmes
**Phase :** NOMINAL (fin de mission)
**Révision :** 1.0 --- nouvelle fiche (décision de l'auteur Q3 modifiée, 2026-10-30)
**Approuvé par :** directeur des opérations de vol

## Objet
Abaisser le périgée avec le propulseur existant afin qu'EOSAT-1 rentre dans l'atmosphère en moins de
5 ans même au minimum solaire, puis passiver le satellite : épuiser le
propergol, décharger la batterie et faire taire les émetteurs.

**Pourquoi une poussée est nécessaire.** Depuis l'orbite opérationnelle de 513 km (coefficient
balistique B = 77.9 kg/m2), le déclin d'orbite naturel prend environ 5,0 ans à activité solaire
moyenne et environ 14 ans au minimum solaire. L'ancien « 1,7-4,8 ans, aucune capacité
de désorbitation » avait été établi à l'altitude abandonnée de 450 km. Calcul et
bilan : `subsystems/prop.yaml`.

| Conception du retrait de service | Valeur |
|-----------------|-------|
| Orbite visée | apogée ~513 km, périgée 390 km |
| Delta-V de retrait de service | 34,3 m/s rétrograde, en six poussées d'environ 5,72 m/s |
| Durée de vie résiduelle | ~1,5 an (activité solaire moyenne), ~4,2 ans (minimum solaire) |
| Lieu des poussées | les six poussées au même point de l'orbite, qui devient l'apogée |
| Durée des poussées | ~320-480 s chacune à la poussée de fin de vie (0,15-0,22 N) |
| Propergol | ~0,21 kg sur les 0,400 kg chargés |

Chaque poussée rétrograde abaisse l'orbite du côté opposé : le point de poussée
reste l'apogée et chaque poussée abaisse le même périgée. Six poussées maintiennent chacune
dans les verrouillages d'armement (jour, erreur d'attitude < 2 deg) et dans le chien de garde
de poussée de 600 s réglé à l'étape 3.

## Prérequis
- [ ] Fin de mission déclarée par le directeur de vol ; campagne de prise de vue close
      et dernières données scientifiques transmises au sol
- [ ] Phase de mission 6 (NOMINAL) : `eps.spacecraft_phase` (0x0129) = 6 --- le
      verrouillage d'armement de la propulsion l'exige
- [ ] `prop.dv_remaining` (0x0B0C) >= 38 m/s (la poussée de 34,3 m/s plus la réserve de dispersion
      de 10 %)
- [ ] Propulsion en bonne santé : `prop.state` (0x0B00) = 0, aucune inhibition
      verrouillée, pression du réservoir 6,0-24,0 bar (`prop.tank_pressure` 0x0B01)
- [ ] SoC de la batterie > 55 % : `eps.bat_soc` (0x0101)
- [ ] La dynamique du vol dispose de l'orbite courante issue du GPS (`aocs.gps_alt` 0x0212)
      et d'un plan de six poussées consécutives de jour

## Déroulement

### Étape 1 --- Plan de retrait de service du FDS
**Évaluer :** Choisir le point de poussée (argument de latitude) de jour et, si possible,
au-dessus d'une station sol. Pour chacune des six poussées : dV, époque de poussée,
durée de poussée prévue à l'état courant du réservoir et périgée prévu après la
poussée (513 -> ~492 -> ~471 -> ~451 -> ~431 -> ~410 -> 390 km).
**Évaluer :** Attitude rétrograde : le quaternion inertiel qui fait tourner
l'attitude nominale de 180 deg en lacet afin que +X corps pointe vers l'opposé de la
vitesse au milieu de la poussée. Pendant une poussée de 480 s, la direction de la vitesse
tourne d'environ 30 deg dans l'espace inertiel ; tenir l'attitude du milieu de poussée coûte environ 1 %
du dV, que la réserve couvre.
**Consigner :** Les six époques de poussée (CUC), le dV par poussée, le quaternion cible.
**GO/NO-GO:** Le directeur de vol autorise le plan de retrait de service

### Étape 2 --- Contrôle de santé de la propulsion
**TC:** `HK_ENABLE(sid=9)` (Service 3, Subtype 5) --- données de servitude PROP
**Verify:** `prop.state` (0x0B00) = 0 sous 20s
**Verify:** `prop.tank_pressure` (0x0B01) dans l'intervalle [6.0, 24.0] sous 20s
**Verify:** `prop.propellant_mass` (0x0B02) rapporté sous 20s --- consigner
**Verify:** `prop.dv_remaining` (0x0B0C) >= 38 sous 20s
**Verify:** `prop.arm_inhibit_mask` (0x0B15) rapporté sous 20s --- consigner
**GO/NO-GO:** Propulsion capable de fournir le delta-V de retrait de service ; sinon appliquer
d'abord CTG-028

### Étape 3 --- Relever le chien de garde de poussée
**TC:** `PROP_SET_LIMITS(att_err_max_deg=2.0, p_min_bar=4.0, catbed_max_c=350.0, t_burn_max_s=600.0)` (Service 8, Subtype 1, func_id 115) --- le chien de garde par défaut est de 300 s
**Note:** En fin de vie, une poussée de 5,72 m/s dure jusqu'à ~480 s. Seul le chien de garde
de poussée change ; les limites d'interruption sur l'attitude, la pression et le lit catalytique gardent leurs
valeurs par défaut.

### Étape 4 --- Alimentation, préchauffage et vannes (T-25 min)
**TC:** `EPS_POWER_ON(line_index=8)` (Service 8, Subtype 1) func_id = 19 --- alimenter la ligne de propulsion
**TC:** `HEATER_THRUSTER(on=1)` (Service 8, Subtype 1) func_id = 42 --- préchauffage du lit catalytique, 12 W
**TC:** `PROP_ISO_OPEN(branch=2)` (Service 8, Subtype 1, func_id 113) --- ouvrir les deux branches de vannes à verrouillage
**Verify:** `eps.pl_prop` (0x014A) = 1 sous 10s
**Verify:** `prop.latch_a_state` (0x0B06) = 1 sous 10s
**TC:** `GET_PARAM(param_id=0x0409)` (Service 20, Subtype 3) — `tcs.temp_thruster` (à la demande : aucun SID HK ne le transporte)
**Verify:** `tcs.temp_thruster` (0x0409) >= 180 sous 1500s
**GO/NO-GO:** Lit catalytique chaud et circuit de propergol ouvert

### Étape 5 --- Attitude rétrograde
**TC:** `AOCS_SET_TARGET_QUAT(q_x=QX, q_y=QY, q_z=QZ, q_w=QW)` (Service 8, Subtype 1, func_id 86) --- le quaternion rétrograde de l'étape 1
**TC:** `AOCS_SET_MODE(mode=9)` (Service 8, Subtype 1) func_id = 0 --- maintien INERTIAL
**Verify:** `aocs.mode` (0x020F) = 9 sous 120s
**Verify:** `aocs.att_error` (0x0217) < 0.5 sous 600s
**Note:** Le lacet de 180 deg retourne la face -X du propulseur afin que l'axe de poussée +X
pointe à l'opposé de la vitesse. Prévoir la fin du basculement avant l'armement.

### Étape 6 --- Poussée de retrait de service (à répéter pour chacune des six poussées)
**TC:** `PROP_SET_BURN(dv_m_s=5.72, direction=1, mode=1, t_start_cuc=0)` (Service 8, Subtype 1, func_id 110) --- rétrograde, coupure en boucle fermée sur le dV
**Verify:** `prop.burn_time_cmd` (0x0B10) à 10 % près de la prévision du FDS
**TC:** `PROP_ARM(arm_code=0xA5C3)` (Service 8, Subtype 1) func_id = 108 --- dans les 300 s qui suivent SET_BURN
**Verify:** `prop.state` (0x0B00) = 1 sous 10s
**TC:** `PROP_EXECUTE` (Service 8, Subtype 1) func_id = 111 --- lancer la poussée (ou la programmer par S11 comme dans NOM-004)
**Verify:** `prop.state` (0x0B00) = 2 sous 10s
**Surveiller :** `prop.thrust_est` (0x0B09), `aocs.att_error` (0x0217),
`prop.burn_time_elapsed` (0x0B11). Les critères d'interruption et l'interruption manuelle sont
ceux de NOM-013, étape 5.
**Verify:** événement PROP_BURN_COMPLETE (0x0804) reçu sous 600s
**Verify:** `prop.burn_dv_achieved` (0x0B0F) à 2 % près de 5.72
**TC:** `PROP_DISARM` (Service 8, Subtype 1) func_id = 109 --- ARMED -> SAFED ; PROP_ARM est refusé (0x0B10) si le système n'est pas SAFED
**Verify:** `prop.state` (0x0B00) = 0 sous 10s
**Note:** Laisser le réchauffeur du lit catalytique allumé entre des poussées sur des orbites consécutives. Après
chaque poussée, revenir en NOMINAL (`AOCS_SET_MODE`, mode 4) pour l'éclipse et
reprendre le maintien rétrograde avant la suivante. Répéter les étapes 5 et 6 jusqu'à ce que
les six poussées soient terminées ; le périgée prévu après chaque poussée figure à l'étape 1.
**GO/NO-GO:** Poussée réalisée ; enchaîner la poussée suivante ou l'étape 7

### Étape 7 --- Confirmer l'orbite de retrait de service
**TC:** `HK_REQUEST(sid=12)` (Service 3, Subtype 27) --- navigation GPS, échantillonnée sur une orbite complète
**Verify:** `aocs.gps_alt` (0x0212) minimum sur l'orbite dans l'intervalle [380, 400]
**Évaluer :** Le FDS ajuste l'orbite (demi-grand axe attendu ~6830 km) et calcule la durée de vie résiduelle à activité
moyenne et au minimum solaire. Si la durée de vie au minimum solaire dépasse 5 ans,
prévoir une poussée de correction (de nouveau l'étape 6, dV plus faible) avant la passivation.
**GO/NO-GO:** Périgée à ~390 km ; durée de vie résiduelle < 5 ans au minimum solaire

### Étape 8 --- Épuisement du propergol
**Note:** L'effectuer depuis le maintien rétrograde de l'étape 5, de jour, comme une poussée de retrait de service.
**TC:** `PROP_SET_BURN(dv_m_s=DVREM, direction=1, mode=0, t_start_cuc=0)` (Service 8, Subtype 1, func_id 110) --- DVREM = la lecture courante de `prop.dv_remaining`, rétrograde, boucle ouverte
**TC:** `PROP_ARM(arm_code=0xA5C3)` (Service 8, Subtype 1) func_id = 108
**TC:** `PROP_EXECUTE` (Service 8, Subtype 1) func_id = 111 --- poussée jusqu'à épuisement
**Verify:** `prop.propellant_mass` (0x0B02) < 5 sous 900s
**Note:** Brûler le reliquat en rétrograde abaisse encore le périgée, ce qui ne fait que
raccourcir le déclin d'orbite. En dessous de 5 g, le verrouillage d'armement refuse (0x0B03) : ce reliquat
ne peut pas être expulsé et il est consigné. Fractionner la poussée si elle devait dépasser le chien de garde
de 600 s.

### Étape 9 --- Mise en sécurité de la propulsion
**TC:** `PROP_DISARM` (Service 8, Subtype 1) func_id = 109 --- ARMED -> SAFED
**TC:** `HEATER_THRUSTER(on=0)` (Service 8, Subtype 1) func_id = 42 --- réchauffeur du lit catalytique coupé
**TC:** `PROP_INHIBIT_SET(on=1)` (Service 8, Subtype 1, func_id 116) --- verrouiller l'inhibition sol pour que plus rien ne puisse tirer
**Verify:** `prop.state` (0x0B00) = 0 sous 10s
**Verify:** `prop.arm_inhibit_mask` (0x0B15) bit 9 positionné sous 10s --- inhibition verrouillée
**TC:** `EPS_POWER_OFF(line_index=8)` (Service 8, Subtype 1) func_id = 20 --- couper la ligne de propulsion
**Verify:** `eps.pl_prop` (0x014A) = 0 sous 10s
**Note:** Le modèle n'a pas de circuit de mise à l'air du pressurisant : la pression résiduelle du réservoir
(environ 9-10 bar) ne peut pas être évacuée avec les commandes existantes. La consigner dans le
rapport de retrait de service comme limitation connue.

### Étape 10 --- Arrêt de la charge utile et de l'attitude
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1) func_id = 26 --- charge utile sur OFF
**TC:** `EPS_POWER_OFF(line_index=3)` (Service 8, Subtype 1) func_id = 20 --- ligne de la charge utile coupée
**TC:** `AOCS_RW_RAMP_DOWN(wheel_idx=255, target_rpm=0)` (Service 8, Subtype 1, func_id 14) --- arrêter toutes les roues
**Verify:** `payload.mode` (0x0600) = 0 sous 30s
**Verify:** `aocs.total_momentum` (0x025B) < 0.01 sous 120s
**Note:** Roues arrêtées, le satellite n'est plus stabilisé trois axes.
C'est voulu : il ne reste aucune énergie cinétique stockée dans les roues.

### Étape 11 --- Passivation de la batterie
**TC:** `S2_EPS_CHARGE_REGULATOR(device_id=271, state=0)` (Service 2, Subtype 1) --- régulateur de charge sur OFF : les panneaux ne peuvent plus charger la batterie
**Verify:** `eps.bat_soc` (0x0101) en baisse au cours des 30 minutes suivantes en éclairement
**Note:** Les charges restantes (OBC, récepteur, émetteur) déchargent désormais la
batterie. À ~20 W, elle est vide en quelques heures ; le satellite s'éteint alors
définitivement. Les étapes 11 et 12 doivent être envoyées pendant le même passage.

### Étape 12 --- Silence radio (dernières commandes)
**TC:** `TTC_BEACON_TX_OFF` (Service 8, Subtype 1) func_id = 98 --- émetteur de balise UHF coupé
**TC:** `TTC_PA_OFF` (Service 8, Subtype 1) func_id = 67 --- amplificateur de puissance bande S coupé
**TC:** `EPS_TRANSPONDER_TX(on=0)` (Service 8, Subtype 1) func_id = 18 --- émetteur bande S coupé
**Note:** Après cette étape, aucune télémesure ne peut plus être reçue. La perte du signal est la
vérification attendue. Confirmer aux deux passages programmés suivants qu'aucune porteuse
n'est reçue.
**GO/NO-GO:** Satellite silencieux --- retrait de service terminé

## Écarts
- **Une poussée est interrompue.** Appliquer NOM-013 (étape 5) et CTG-028. Le dV partiel est déjà
  dans l'orbite ; le FDS replanifie les poussées restantes à partir de la nouvelle orbite.
- **`prop.dv_remaining` inférieur au plan.** Abaisser le périgée autant que le
  propergol le permet et rapporter la durée de vie résiduelle obtenue. Chaque tranche de 1 m/s de
  dV rétrograde abaisse le périgée d'environ 3,6 km.
- **Propulsion inutilisable en fin de vie.** Le satellite subit un déclin d'orbite naturel en
  environ 5 ans à activité solaire moyenne, 14 au minimum solaire. Passiver (étapes
  9-12) et signaler la non-conformité.
- **Phase de mission.** Il n'existe pas de phase DISPOSAL dans `SYS_SET_MISSION_PHASE`
  (phases 3-6 seulement). Le satellite reste en phase 6 tout du long ; le verrouillage
  de la propulsion l'exige.

## Postconditions
- [ ] Périgée ~390 km confirmé par le GPS et l'ajustement d'orbite du FDS
- [ ] Durée de vie résiduelle < 5 ans au minimum solaire
- [ ] Propergol épuisé (< 5 g) et propulsion inhibée
- [ ] Voie de charge de la batterie désactivée
- [ ] Tous les émetteurs coupés ; perte du signal confirmée à deux passages
- [ ] Rapport de retrait de service établi (orbite, dV consommé, propergol résiduel, pression résiduelle du réservoir)
