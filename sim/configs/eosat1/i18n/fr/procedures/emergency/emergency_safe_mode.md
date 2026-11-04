# EMG-001 : Mode survie d'urgence
**Sous-système :** OBDH / All Subsystems
**Phase :** EMERGENCY
**Révision :** 1.1 --- 2026-11-02 (décisions de Franz P1/P3) : vérifier ce que la FDIR de bord
a déjà délesté AVANT de délester depuis le sol, et alimenter la ligne EPS d'une unité avant toute
commande de réchauffeur ou de mode qui lui est destinée. L'ancienne fiche commandait des charges dont la
FDIR avait déjà ouvert la ligne (refus S1.8 « power line … is OFF ») et allumait des réchauffeurs
dont la ligne était hors tension.
**Approuvé par :** directeur des opérations de vol

## Objet
Procédure maîtresse d'entrée d'EOSAT-1 en mode survie d'urgence lorsque plusieurs anomalies simultanées sont
détectées ou que le satellite est passé de lui-même en mode EMERGENCY. Cette procédure
coordonne la mise de l'OBC en mode d'urgence, vérifie le délestage automatique, confirme une attitude sûre
de pointage solaire, établit la communication et fournit un calendrier de rétablissement orbite par orbite
jusqu'au retour aux opérations nominales.

## Prérequis
- [ ] Plusieurs indicateurs d'anomalie présents OU `obdh.mode` (0x0300) = EMERGENCY (2) confirmé
- [ ] Le directeur de vol a déclaré l'urgence satellite
- [ ] Équipe d'intervention d'urgence au complet (ingénieurs puissance, AOCS, TT&C, thermique, charge utile)
- [ ] Toutes les stations sol alertées pour une poursuite prioritaire
- [ ] Journal d'anomalie ouvert avec la chronologie des événements

## Conditions de déclenchement (au moins deux)
- `eps.bat_soc` (0x0101) < 15 % --- puissance faible
- `aocs.att_error` (0x0217) > 30 deg --- anomalie d'attitude
- Toute vitesse angulaire > 2 deg/s --- culbutage
- `obdh.reboot_count` (0x030A) incrémenté de >= 2 en 1 heure --- instabilité de l'OBC
- `tcs.temp_battery` (0x0407) hors de la plage -10 °C à +45 °C --- violation thermique
- `ttc.link_status` (0x0501) != 2 (pas LOCKED) pendant > 1 passage --- communication dégradée
- `obdh.mode` (0x0300) = EMERGENCY (2) --- transition autonome détectée

## Déroulement

### Étape 1 --- Commander le mode d'urgence (si la transition autonome n'a pas eu lieu)
**TC:** `OBC_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 50) --- mode EMERGENCY.
**Verify:** `obdh.mode` (0x0300) = EMERGENCY (2) sous 5 s.
**Effet :** Le logiciel de bord exécute la séquence de délestage automatique, réduit le débit de télémesure,
désactive toutes les opérations programmées et active la distribution de puissance de survie seule.
**GO/NO-GO:** Mode d'urgence de l'OBC confirmé. Si l'OBC ne répond pas, poursuivre par la commande manuelle de l'étape 2.

### Étape 2 --- Vérifier le délestage automatique (vérifier d'abord le satellite)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- données de servitude EPS complètes.
**Verify:** `eps.load_shed_stage` (0x0134) --- consigner ce que le délesteur de bord a déjà fait (événements LOAD_SHED_STAGE_1..3, 0x0106-0x0108)
**Verify:** `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_ttc_tx` (0x0112), `eps.pl_aocs_wheels` (0x0117) --- consigner chacune : 0 = déjà délestée à bord
**Note:** Une ligne que la FDIR de bord a ouverte ne peut pas être délestée une seconde fois --- les
commandes de son unité sont refusées S1.8 « power line … is OFF » et ses données de servitude s'arrêtent,
si bien que son paramètre de mode (p. ex. `payload.mode`) reste figé à sa dernière valeur. Juger un
délestage d'après l'état de la LIGNE. Ne délester depuis le sol que ce qui est encore alimenté.
**Verify:** `eps.power_cons` (0x0106) < 50 W.
**BRANCH:** `eps.pl_payload == 1` -> GO `STEP-2-PLD` | NO-GO `STEP-2-HTR` (timeout 10 s)
**Note:** GO --- la ligne de la charge utile est encore sur ON : délester la charge utile depuis le sol.
NO-GO --- la FDIR l'a déjà ouverte : rien à envoyer.

**LABEL:** `STEP-2-PLD`
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) --- charge utile OFF.
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — données de servitude de la charge utile
**Verify:** `payload.mode` (0x0600) = 0 (OFF) sous 10 s.

**LABEL:** `STEP-2-HTR`
**TC:** `HEATER_OBC(on=0)` (Service 8, Subtype 1, func_id 41) --- réchauffeur OBC OFF (si nécessaire).
**TC:** `HEATER_THRUSTER(on=0)` (Service 8, Subtype 1, func_id 42) --- réchauffeur du propulseur OFF.
**Verify:** `eps.power_cons` (0x0106) < 50 W dans les 15 s qui suivent la commande manuelle.
**GO/NO-GO:** Consommation totale du satellite confirmée sous 50 W.

### Étape 3 --- Vérifier le pointage sûr de l'AOCS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- données de servitude AOCS.
**Contrôler :** `aocs.mode` (0x020F) --- doit être COARSE_SUN (3) ou DETUMBLE (2).
**Note:** NE PAS commander COARSE_SUN. L'AOCS passe de lui-même de DETUMBLE à
COARSE_SUN dès que les vitesses angulaires sont restées sous 0.5 deg/s pendant
30 s (le même passage automatique que celui observé par LEOP-005). Le commander est
inutile, et un COARSE_SUN engagé au-dessus du seuil de vitesse ne tient pas.
**BRANCH:** `aocs.mode == 0` -> GO `STEP-3-DETUMBLE` | NO-GO `STEP-3-WAIT` (timeout 10 s)
**Note:** GO --- l'AOCS est OFF : commander d'abord DETUMBLE. NO-GO --- l'AOCS est
déjà dans un mode : ne rien commander et attendre la tenue de pointage solaire.

**LABEL:** `STEP-3-DETUMBLE`
**Note:** Un AOCS qui indique OFF a généralement perdu sa ligne `aocs_wheels` lors d'un délestage de
bord (l'AOCS retombe sur OFF quand la ligne s'ouvre) ; DETUMBLE est alors refusé « EPS aocs_wheels
line (0x0117) is off ». Réalimenter d'abord la ligne --- `EPS_POWER_ON` sur une ligne déjà sur ON
est sans effet.
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19) --- la ligne `aocs_wheels` (suite AOCS)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- données de servitude EPS (états des lignes)
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 1 sous 5 s
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0) --- DETUMBLE (l'AOCS était OFF).

**LABEL:** `STEP-3-WAIT`
**BRANCH:** `aocs.mode == 3` -> GO `STEP-4` | NO-GO `STEP-3-EMG-005` (timeout 1800 s)
**Note:** GO --- COARSE_SUN, déjà tenu ou atteint par le passage automatique :
passer à l'étape 4, qui vérifie le pointage solaire. NO-GO --- pas de COARSE_SUN
au bout de 30 min : le satellite culbute ou l'amortissement ne converge pas.

**LABEL:** `STEP-3-EMG-005`
**Note:** Exécuter EMG-005 (perte d'attitude) maintenant. Ne reprendre cette carte, à
l'étape 4, que lorsque EMG-005 a laissé l'AOCS en COARSE_SUN.
**GO/NO-GO:** EMG-005 terminée et AOCS en COARSE_SUN --- reprise à l'étape 4 -> GO `STEP-4` | NO-GO `STEP-END`

### Étape 4 --- Vérifier l'acquisition du Soleil et l'état de puissance
**LABEL:** `STEP-4`
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg (pointage solaire obtenu).
**Verify:** `eps.sa_a_current` (0x0103) > 0.5 A --- générateur solaire A éclairé.
**Verify:** `eps.sa_b_current` (0x0104) > 0.5 A --- générateur solaire B éclairé.
**Verify:** `eps.power_gen` (0x0107) > `eps.power_cons` (0x0106) --- bilan de puissance positif.
**Verify:** `eps.bat_soc` (0x0101) --- consigner la valeur et commencer le suivi de tendance.
**TC:** `EPS_POWER_ON(line_index=5)` (Service 8, Subtype 1, func_id 19) --- d'abord la ligne du réchauffeur batterie : un réchauffeur dont la ligne est hors tension ne chauffe rien et sa commande ON est refusée
**Verify:** `eps.pl_htr_bat` (0x0115) = 1 sous 5 s
**TC:** `HEATER_AUTO_MODE(circuit=0)` (Service 8, Subtype 1, func_id 45) --- s'assurer que le thermostat de la batterie est actif (ON sous +5 °C, OFF au-dessus de +10 °C).
**Note:** Si la batterie est déjà plus froide que la plage du thermostat et ne remonte pas, forcer le
réchauffeur : `HEATER_BATTERY(on=1)` (func_id 40) ; le rendre à `HEATER_AUTO_MODE(circuit=0)` dès que
`tcs.temp_battery` (0x0407) est revenue au-dessus de +10 °C.
**GO/NO-GO:** Bilan de puissance positif confirmé. Sinon, exécuter EMG-002.

### Étape 5 --- Établir une communication stable
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED).
**Verify:** page TT&C (sol) : `ttc.rssi` (0x0502) > -128 dBm.
**Verify:** `ttc.mode` (0x0500) = NOMINAL ou SAFE.
**Action:** Si la liaison est limite, ne programmer les passages suivants qu'avec des stations sol à forte élévation (> 20 deg).
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- données de servitude du sous-système TT&C.
**GO/NO-GO:** Communication bidirectionnelle stable. Si elle est instable, se reporter à EMG-004.

### Étape 6 --- Évaluation complète des données de servitude
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- HK EPS.
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- HK AOCS.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- HK OBDH.
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) --- HK TCS.
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- HK TT&C.
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- HK charge utile.
**Action:** L'équipe d'ingénierie examine tous les paramètres par rapport aux plages nominales.
**Consigner :** `obdh.reboot_count` (0x030A) --- noter toute incrémentation inattendue.
**Consigner :** Toutes les températures : `tcs.temp_obc` (0x0406), `tcs.temp_battery` (0x0407).
**Consigner :** `eps.bat_voltage` (0x0100), `eps.bus_voltage` (0x0105) --- état complet de la puissance.
**GO/NO-GO:** La commission d'examen des anomalies se réunit pour évaluer les données et approuver le plan de rétablissement.

### Étape 7 --- Attente de stabilisation (3 orbites au minimum)
**LABEL:** `STEP-7`
**Durée :** Maintenir le mode survie d'urgence pendant au moins 3 orbites (~4,75 heures).
**Surveiller :** Tous les paramètres critiques à chaque passage sur une station sol.
**Confirmer :** Aucune nouvelle anomalie, aucun redémarrage supplémentaire de l'OBC, températures stables, puissance en tendance positive.
**Verify:** `eps.bat_soc` (0x0101) > 25 % à la fin de la période de stabilisation.
**Action:** L'équipe d'ingénierie achève l'analyse des causes racines des anomalies déclenchantes.
**GO/NO-GO:** Le directeur de vol approuve le passage au rétablissement par étapes.

## Calendrier de rétablissement orbite par orbite

### Orbite de rétablissement R+1 --- Rétablir le contrôle thermique (SoC > 30 % requis)
**TC:** `EPS_POWER_ON(line_index=6)` (Service 8, Subtype 1, func_id 19) --- d'abord la ligne du réchauffeur OBC (sans effet si déjà sur ON)
**Verify:** `eps.pl_htr_obc` (0x0116) = 1 sous 5 s
**TC:** `HEATER_AUTO_MODE(circuit=1)` (Service 8, Subtype 1, func_id 45) --- rendre le réchauffeur OBC à son thermostat (l'étape 2 l'a mis sur OFF manuellement).
**Note:** Si l'OBC est sous -10 °C et ne remonte pas, le forcer sur ON avec `HEATER_OBC(on=1)`
(func_id 41) et le rendre au mode AUTO une fois réchauffé.
**Verify:** `tcs.temp_obc` (0x0406) tendant vers la plage nominale (-10 °C à +40 °C).
**Verify:** hausse de `eps.power_cons` (0x0106) < 10 W. Le bilan de puissance du satellite reste positif.
**GO/NO-GO:** Sous-système thermique nominal, le bilan de puissance absorbe la charge ajoutée ; aucune nouvelle anomalie -> GO `STEP-R2` | NO-GO `STEP-7` (max 2)

### Orbite de rétablissement R+2 --- Rétablir l'AOCS complet (SoC > 40 % requis)
**LABEL:** `STEP-R2`
**TC:** `OBC_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 50) --- OBC en mode SAFE (depuis EMERGENCY).
**Verify:** `obdh.mode` (0x0300) = SAFE (1) sous 5 s.
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19) --- la ligne `aocs_wheels` avant la commande de mode (sans effet si l'étape 3 l'a déjà réalimentée)
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 1 sous 5 s
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0) --- mode NOMINAL.
**Verify:** `aocs.mode` (0x020F) = NOMINAL (4) sous 5 s.
**Verify:** `aocs.att_error` (0x0217) < 1.0 deg sous 20 minutes.
**Verify:** `aocs.rw1_speed` (0x0207) à `aocs.rw4_speed` (0x020A) toutes dans les limites.
**GO/NO-GO:** Contrôle d'attitude complet rétabli, les 4 roues opérationnelles ; aucune nouvelle anomalie -> GO `STEP-R3` | NO-GO `STEP-7` (max 2)

### Orbite de rétablissement R+3 --- Rétablir le réchauffeur du propulseur et le contrôle thermique complet (SoC > 50 % requis)
**LABEL:** `STEP-R3`
**Note:** Le réchauffeur du lit catalytique (propulseur) est sur OFF en opérations nominales, et sa
ligne `prop` (8) aussi : il n'est alimenté que pour le préchauffage d'une manœuvre (NOM-013). N'envoyer
les deux commandes ci-dessous que si une manœuvre est prévue ; sinon, il n'y a rien à rétablir et cette
orbite ne fait que vérifier l'état thermique.
**TC:** `EPS_POWER_ON(line_index=8)` (Service 8, Subtype 1, func_id 19) --- d'abord la ligne `prop` ; HEATER_THRUSTER est refusé tant qu'elle est hors tension
**Verify:** `eps.pl_prop` (0x014A) = 1 sous 5 s
**TC:** `HEATER_THRUSTER(on=1)` (Service 8, Subtype 1, func_id 42) --- rétablir le réchauffeur du propulseur.
**Verify:** `eps.power_cons` (0x0106) dans le bilan nominal (< 90 W).
**Verify:** toutes les températures dans les plages nominales.
**GO/NO-GO:** Contrôle thermique complet rétabli, marge de puissance suffisante ; aucune nouvelle anomalie -> GO `STEP-R4` | NO-GO `STEP-7` (max 2)

### Orbite de rétablissement R+4 --- Rétablir le mode nominal de l'OBC (SoC > 55 % requis)
**LABEL:** `STEP-R4`
**TC:** `OBC_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 50) --- OBC en mode NOMINAL.
**Verify:** `obdh.mode` (0x0300) = NOMINAL (0) sous 5 s.
**Verify:** ordonnancement de bord repris, données de servitude à la cadence nominale.
**Verify:** aucune incrémentation anormale du compteur de redémarrages : `obdh.reboot_count` (0x030A) stable.
**GO/NO-GO:** Opérations nominales de l'OBC confirmées ; aucune nouvelle anomalie -> GO `STEP-R5` | NO-GO `STEP-7` (max 2)

### Orbite de rétablissement R+5 --- Rétablir la charge utile (SoC > 60 % requis)
**LABEL:** `STEP-R5`
**TC:** `EPS_POWER_ON(line_index=3)` (Service 8, Subtype 1, func_id 19) --- d'abord la ligne `payload` : un délestage de bord l'a ouverte, et la commande de mode est refusée S1.8 tant qu'elle est hors tension
**Verify:** `eps.pl_payload` (0x0113) = 1 sous 5 s
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) --- charge utile en STANDBY.
**Verify:** `payload.mode` (0x0600) = STANDBY (1) sous 10 s.
**Verify:** `eps.power_cons` (0x0106) dans le bilan opérationnel complet (< 110 W).
**Verify:** le bilan de puissance du satellite reste positif sur une orbite complète, éclipse comprise.
**GO/NO-GO:** Opérations nominales complètes rétablies ; aucune nouvelle anomalie. Clore l'urgence et reprendre le calendrier de la mission. -> GO `STEP-END` | NO-GO `STEP-7` (max 2)
**LABEL:** `STEP-END`

## Synthèse du calendrier de rétablissement
| Phase | Orbite | Seuil de SoC | Durée depuis l'urgence | Action clé |
|---|---|---|---|---|
| Attente d'urgence | R+0 à R+3 | -- | 0 à 4,75 h | Stabiliser, évaluer, planifier |
| Rétablissement thermique | R+1 rétablissement | > 30 % | ~6,3 h | Réchauffeur OBC ON |
| Rétablissement AOCS | R+2 rétablissement | > 40 % | ~7,9 h | Pointage nadir |
| Thermique complet | R+3 rétablissement | > 50 % | ~9,5 h | Réchauffeur du propulseur ON (seulement si une manœuvre est prévue) |
| OBC nominal | R+4 rétablissement | > 55 % | ~11,1 h | Reprise de l'ordonnancement |
| Charge utile en attente | R+5 rétablissement | > 60 % | ~12,6 h | Mission reprise |

## Conduite à tenir hors nominal
- Si l'OBC n'accepte pas les commandes de mode : demander un rapport de santé de l'OBC avec `OBC_DIAGNOSTIC` (func_id 61) et, si le directeur de vol l'autorise, le réinitialiser avec `OBC_REBOOT` (func_id 52), puis renvoyer la commande. Si le problème persiste, le satellite reste en mode d'urgence autonome jusqu'au prochain cycle de redémarrage de l'OBC.
- Si plusieurs roues sont tombées en panne pendant l'anomalie : rester en COARSE_SUN indéfiniment. Le pointage nadir exige au moins 3 roues. Planifier des opérations à capacité réduite.
- Si le SoC n'atteint pas 30 % en 10 orbites : dégradation possible du générateur solaire. Réévaluer le bilan de puissance pour des opérations réduites à long terme. Se reporter à EMG-002.
- Si une nouvelle anomalie survient pendant le rétablissement : arrêter le rétablissement, se replacer dans l'attente de stabilisation (étape 7) et réévaluer avant de continuer. C'est la branche NO-GO de chaque point de décision des orbites de rétablissement, et cette boucle est bornée (max 2) : si le même point de décision échoue une troisième fois, arrêter le rétablissement par étapes, maintenir le mode survie d'urgence et réunir le comité d'examen des anomalies.
- Si `obdh.reboot_count` (0x030A) continue de s'incrémenter : soupçonner une panne matérielle de l'OBC. Maintenir le mode d'urgence, réduire les commandes au minimum, planifier un correctif mémoire de l'OBC ou un basculement sur la redondance froide si elle est disponible.

## Postconditions
- [ ] `obdh.mode` (0x0300) = NOMINAL (0)
- [ ] `aocs.mode` (0x020F) = NOMINAL (4) avec `aocs.att_error` (0x0217) < 1.0 deg
- [ ] `eps.bat_soc` (0x0101) > 60 % et stable
- [ ] `eps.bus_voltage` (0x0105) > 32.1 V
- [ ] Tous les réchauffeurs opérationnels, températures dans les plages nominales
- [ ] `payload.mode` (0x0600) = STANDBY (1) ou supérieur
- [ ] `ttc.link_status` (0x0501) = 2 (LOCKED) lors des passages programmés
- [ ] Causes racines de toutes les anomalies identifiées ou enquête formelle ouverte
- [ ] Le directeur de vol a formellement levé la déclaration d'urgence
- [ ] Retour d'expérience documenté et mises à jour des procédures lancées si nécessaire

## Voie de rétablissement — remise sous tension des charges délestées
Une fois que cette procédure a stabilisé le bus et que la cause racine est comprise, **tous les sous-systèmes dont les lignes d'alimentation ont été coupées lors du délestage doivent être remis sous tension dans l'ordre maîtrisé défini par LEOP-007 (mise sous tension séquentielle)**. Ne **pas** se contenter de réactiver les lignes au coup par coup : LEOP-007 impose le bon séquencement sous-système→ligne→mode, l'espacement des courants d'appel, le préconditionnement thermique par les réchauffeurs de l'OBC et de la batterie, et les exemptions set_mode AOCS/charge utile de la condition d'alimentation à deux étages des TC. Renvoi : `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
