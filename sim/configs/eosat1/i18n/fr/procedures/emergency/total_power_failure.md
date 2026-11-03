# EMG-002 : Perte totale d'alimentation
**Sous-système :** EPS
**Phase :** EMERGENCY
**Révision :** 1.1 --- 2026-11-02 (décisions de Franz P1/P3) : vérifier ce que la FDIR de bord
a déjà délesté avant de délester depuis le sol ; alimenter la ligne EPS d'une unité avant toute commande
de réchauffeur ou de mode qui lui est destinée ; le réchauffeur batterie passe sous thermostat avec
`HEATER_AUTO_MODE`, et non en ON manuel.
**Approuvé par :** directeur des opérations de vol

## Objet
Procédure d'urgence d'EOSAT-1 lorsque l'état de charge de la batterie tombe sous 10 % ou que la tension du bus
descend sous 26 V. Cette procédure définit le délestage immédiat permettant d'atteindre la configuration minimale
de survie (~20 W), assure le pointage solaire des générateurs pour une production de puissance maximale et
fournit un plan de rétablissement par étapes. Aucune charge ne peut être réactivée tant que le SoC n'a pas dépassé 30 %.

## Prérequis
- [ ] `eps.bat_soc` (0x0101) < 10 % OU `eps.bus_voltage` (0x0105) < 26.0 V confirmé
- [ ] Liaison de communication active --- `ttc.link_status` (0x0501) = 2 (LOCKED) (sinon, la procédure est exécutée en aveugle)
- [ ] Flux de télémesure EPS actif ou dernières valeurs connues datant de < 60 s
- [ ] Ingénieur systèmes de puissance à la console
- [ ] Le directeur de vol a déclaré l'URGENCE PUISSANCE

## Bilan de puissance --- configuration minimale de survie
| Sous-système | Composant | Puissance (W) | État |
|---|---|---|---|
| OBC | Calculateur de vol | 6 | ON --- essentiel |
| TT&C | Récepteur (RX) | 1.5 | ON --- essentiel |
| AOCS | COARSE_SUN (magnétocoupleurs + senseurs solaires) | 4 | ON --- pour l'acquisition du Soleil |
| TCS | Réchauffeur batterie, lorsque le thermostat l'enclenche | 8 | THERMOSTAT --- survie uniquement |
| Charge utile | Instrument | 0 | OFF |
| TCS | Réchauffeur OBC | 0 | OFF |
| **Total** | | **~20 W** | |
| TT&C | Émetteur, pendant un passage uniquement | +5 | ON pendant les passages (~25 W en passage) |

Ce sont les charges que facture le simulateur (`subsystems/eps.yaml` : OBC 6 W, RX
1.5 W, TX 5 W ; réchauffeur batterie 8 W ; AOCS 4 W en COARSE_SUN). La limite GO de < 50 W
utilisée à l'étape 1 est le contrôle du délestage, pas le bilan de survie.

Capacité des générateurs solaires en pointage solaire : ~64 W (début de vie, ailes déployées, SSO à ~513 km). Fraction d'éclipse : ~36–38 %.
Puissance produite moyenne sur l'orbite en pointage solaire : ~35 W. Marge par rapport à la survie : ~15 W en moyenne sur l'orbite — la préserver en ne rétablissant rien avant le seuil de l'étape 8.

## Déroulement

### Étape 1 --- Délestage immédiat (CRITIQUE --- à exécuter sous 60 s)
**Contrôler :** À cette tension de bus, le délesteur de bord a généralement déjà agi (sous 25,0 V,
il ouvre payload, fpa_cooler, ttc_tx, aocs_wheels, prop dans cet ordre, une ligne par seconde). Lire
`eps.load_shed_stage` (0x0134) et l'état des lignes avant de commander : une ligne que la FDIR a
ouverte ne peut pas être délestée une seconde fois --- la commande est refusée S1.8 et le paramètre de
mode de l'unité reste figé à sa dernière valeur.
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- données de servitude EPS (états des lignes)
**Verify:** `eps.pl_payload` (0x0113), `eps.pl_aocs_wheels` (0x0117), `eps.pl_ttc_tx` (0x0112) --- consigner chacune (0 = déjà délestée à bord)
**BRANCH:** `eps.pl_payload == 1` -> GO `STEP-1-PLD` | NO-GO `STEP-1-HTR` (timeout 10 s)
**Note:** GO --- charge utile encore alimentée : la délester maintenant. NO-GO --- la FDIR a déjà ouvert sa ligne.

**LABEL:** `STEP-1-PLD`
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) --- charge utile OFF immédiatement.
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- données de servitude de la charge utile
**Verify:** `payload.mode` (0x0600) = OFF sous 5 s.

**LABEL:** `STEP-1-HTR`
**TC:** `HEATER_OBC(on=0)` (Service 8, Subtype 1, func_id 41) --- réchauffeur OBC OFF.
**TC:** `HEATER_THRUSTER(on=0)` (Service 8, Subtype 1, func_id 42) --- réchauffeur du propulseur OFF.
**Verify:** `eps.power_cons` (0x0106) < 50 W sous 15 s.
**GO/NO-GO:** Consommation totale confirmée sous 50 W. Sinon, identifier et couper les charges non essentielles restantes.

### Étape 2 --- Placer le réchauffeur batterie en mode thermostat seul
**Contrôler :** Vérifier que la ligne d'alimentation EPS 5 du réchauffeur batterie (`eps.pl_htr_bat`, 0x0115) est ON.
Le thermostat du réchauffeur batterie a besoin de cette ligne pour fonctionner.
**Note:** `EPS_POWER_ON` sur une ligne déjà sous tension est sans effet ; la commande
est donc envoyée sans condition plutôt que de constituer un branchement caché.
**TC:** `EPS_POWER_ON(line_index=5)` (Service 8, Subtype 1, func_id 19) — ligne d'alimentation du réchauffeur batterie
**Verify:** `eps.pl_htr_bat` (0x0115) = 1 (ligne d'alimentation ON) — condition préalable au fonctionnement du thermostat.
**TC:** `HEATER_AUTO_MODE(circuit=0)` (Service 8, Subtype 1, func_id 45) --- réchauffeur batterie
uniquement sous contrôle du thermostat (enclenchement sous +5 °C, déclenchement au-dessus de +10 °C).
`HEATER_BATTERY(on=1)` le forcerait au contraire sur ON en continu (manuel), exactement ce que cet
état de puissance ne peut pas se permettre.
**Verify:** `tcs.htr_battery` (0x040A) cohérent avec le thermostat : 1 seulement tant que `tcs.temp_battery` (0x0407) est sous +5 °C.
**Verify:** `tcs.temp_battery` (0x0407) dans la plage de survie (-10 °C à +45 °C).
**Justification :** La batterie ne doit pas geler pendant l'éclipse, mais le réchauffeur ne doit pas fonctionner en continu dans cet état de puissance.
La ligne d'alimentation doit être ON pour que le thermostat puisse s'enclencher.
**GO/NO-GO:** Température de la batterie > +5 °C (réchauffeur sans consommation en phase éclairée) et `eps.pl_htr_bat` = 1.

### Étape 3 --- Commander le mode d'urgence de l'OBC
**TC:** `OBC_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 50) --- mode EMERGENCY.
**Verify:** `obdh.mode` (0x0300) = EMERGENCY (2) sous 5 s.
**Effet :** Le logiciel de bord désactive toute la programmation autonome de la charge utile, réduit la cadence
de production des données de servitude à 1/60 s et désactive l'enregistrement des données non essentielles.
**GO/NO-GO:** Mode d'urgence de l'OBC confirmé.

### Étape 4 --- Vérifier ou commander l'acquisition du Soleil
**Contrôler :** `aocs.mode` (0x020F) --- s'il n'est pas en COARSE_SUN (3), commander l'acquisition du Soleil.
**Contrôler :** `eps.pl_aocs_wheels` (0x0117) --- un AOCS qui indique OFF (0) a généralement perdu
cette ligne au profit du délesteur de bord, et ses commandes de mode sont refusées S1.8 tant qu'elle
est hors tension. La réalimenter d'abord (sans effet si elle est déjà sur ON) : le bilan de survie
ci-dessus inclut l'AOCS précisément pour cette raison.
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19) --- la ligne `aocs_wheels` (suite AOCS), si 0x0117 = 0
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 1 sous 5 s
**TC:** `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) --- mode COARSE_SUN (si nécessaire).
**Verify:** `aocs.mode` (0x020F) = COARSE_SUN (3) sous 5 s.
**Verify:** `aocs.att_error` (0x0217) < 10.0 deg sous 15 minutes.
**Surveiller :** `eps.power_gen` (0x0107) --- s'attendre à une hausse à mesure que les générateurs solaires atteignent le pointage solaire.
**Critique :** Si l'AOCS est indisponible (vitesses > 2 deg/s), exécuter d'abord l'étape 2 d'EMG-005.
**GO/NO-GO:** Générateurs solaires éclairés --- `eps.sa_a_current` (0x0103) > 0.3 A et `eps.sa_b_current` (0x0104) > 0.3 A.

### Étape 5 --- Surveiller le rétablissement de la puissance (première phase éclairée)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- HK EPS toutes les 60 s.
**Surveiller :** `eps.bat_soc` (0x0101) --- doit être en tendance à la hausse.
**Surveiller :** `eps.bus_voltage` (0x0105) --- doit être stable ou en hausse.
**Surveiller :** `eps.bat_voltage` (0x0100) --- vérifier que la batterie accepte la charge (tension > 27 V).
**Surveiller :** `eps.power_gen` (0x0107) par rapport à `eps.power_cons` (0x0106) --- confirmer le bilan de puissance positif.
**Attendu :** Avec ~20 W de charge de survie (~25 W en passage) et ~64 W de production de crête (~35 W en moyenne sur l'orbite), la marge moyenne sur l'orbite est d'environ 15 W. Suivre la tendance mesurée du SoC : c'est elle, et non cette estimation, qui décide du rétablissement.
**GO/NO-GO:** Bilan de puissance positif confirmé (production > consommation).

### Étape 6 --- Surveillance de l'éclipse (CRITIQUE)
**Contrôle avant éclipse :** Consigner la valeur de `eps.bat_soc` (0x0101) à l'entrée en éclipse.
**Seuil critique :** Si SoC < 8 % à l'entrée en éclipse, le satellite peut entrer en coupure sur sous-tension.
**Surveiller :** `eps.bus_voltage` (0x0105) pendant toute l'éclipse --- doit rester > 25.0 V.
**Surveiller :** `tcs.temp_battery` (0x0407) --- vérifier que le thermostat du réchauffeur batterie s'enclenche si nécessaire.
**Durée :** L'éclipse dure ~34–36 minutes sur la SSO à ~513 km.
**Décharge attendue :** ~20 W x 35 min = ~12 Wh consommés. Capacité de la batterie 100 Wh, soit ~12 % de SoC consommés.
**GO/NO-GO:** Tension du bus maintenue > 25.0 V pendant toute l'éclipse. Si la tension descend sous 25.0 V,
la protection contre les sous-tensions déconnecte automatiquement les bus non essentiels.

### Étape 7 --- Surveillance prolongée du rétablissement (orbites 2--5)
**Durée :** Surveiller pendant au moins 5 orbites (~8 heures).
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) --- à chaque passage.
**Suivre :** Tendance de remontée du SoC --- objectif minimal de 3 % de gain net par orbite.
**Verify:** `tcs.temp_obc` (0x0406) dans la plage opérationnelle (-20 °C à +50 °C).
**Verify:** `tcs.temp_battery` (0x0407) dans la plage opérationnelle (-10 °C à +45 °C).
**Action:** Si le SoC n'est pas en hausse au bout de 3 orbites, rechercher une anomalie des générateurs solaires
(comparaison de `eps.sa_a_current` (0x0103) et `eps.sa_b_current` (0x0104)).
**GO/NO-GO:** SoC au-dessus de 20 % et en hausse constante.

### Étape 8 --- Condition de reprise des charges (SoC > 30 %)
**Condition :** NE réactiver AUCUNE charge tant que `eps.bat_soc` (0x0101) > 30 % n'est pas confirmé sur 3 échantillons HK consécutifs.
**TC:** `EPS_POWER_ON(line_index=6)` (Service 8, Subtype 1, func_id 19) --- d'abord la ligne du réchauffeur OBC (sans effet si déjà sur ON)
**Verify:** `eps.pl_htr_obc` (0x0116) = 1 sous 5 s
**TC:** `HEATER_AUTO_MODE(circuit=1)` (Service 8, Subtype 1, func_id 45) --- rétablir d'abord le réchauffeur OBC, de nouveau sous thermostat (l'étape 1 l'a mis sur OFF manuellement).
**Verify:** hausse de `eps.power_cons` (0x0106) < 10 W après l'activation du réchauffeur.
**Verify:** le bilan de puissance du satellite reste positif après le rétablissement du réchauffeur.
**Suite :** Lorsque le SoC > 40 %, enchaîner sur EMG-001 pour le rétablissement par étapes vers le nominal.
**GO/NO-GO:** SoC > 30 % stable, bilan de puissance positif maintenu avec le réchauffeur OBC rétabli.

## Seuils du rétablissement par étapes
| Seuil de SoC | Action autorisée | Temps estimé depuis l'urgence |
|---|---|---|
| < 10 % | Charges de survie uniquement (~20 W) | T+0 (condition d'entrée) |
| 10--20 % | Aucun changement, surveillance uniquement | T+3 à T+6 heures |
| 20--30 % | Aucun changement, préparer le plan de rétablissement | T+6 à T+10 heures |
| 30--40 % | Rétablir le réchauffeur OBC, augmenter le débit TM | T+10 à T+14 heures |
| 40--60 % | Rétablir l'AOCS en mode complet, activer le réchauffeur du propulseur | T+14 à T+20 heures |
| > 60 % | Rétablir la charge utile en attente, reprendre les opérations nominales | T+20 à T+30 heures |

## Conduite à tenir hors nominal
- Si la tension du bus descend sous 25.0 V : la protection contre les sous-tensions s'active de façon autonome. S'attendre à une perte du TT&C jusqu'à la phase éclairée suivante. Surveiller depuis la station sol la réacquisition de la balise.
- Si le SoC n'augmente pas en phase éclairée : panne possible d'un générateur solaire. Comparer `eps.sa_a_current` (0x0103) et `eps.sa_b_current` (0x0104). Si une aile est à zéro, la survie sur une seule aile est possible, mais avec une marge réduite (~42 W de production de crête).
- Si la température de la batterie descend sous -10 °C : le thermostat du réchauffeur batterie est peut-être défaillant. Confirmer `eps.pl_htr_bat` (0x0115) = 1 (`EPS_POWER_ON(line_index=5)` sinon), puis commander `HEATER_BATTERY(on=1)` manuellement. Accepter une consommation accrue pour éviter d'endommager la batterie.
- Si `obdh.reboot_count` (0x030A) s'incrémente : l'OBC subit peut-être des réinitialisations par baisse de tension. Couper toutes les charges optionnelles restantes et accepter une télémesure réduite.
- Si l'AOCS ne parvient pas à maintenir le pointage solaire : accepter le culbutage avec une production moyenne de puissance dégradée (~15-20 W en moyenne). La survie reste possible si la température de la batterie est maintenue.

## Postconditions
- [ ] `eps.bat_soc` (0x0101) > 30 % et en tendance à la hausse
- [ ] `eps.bus_voltage` (0x0105) > 27.0 V stable
- [ ] `eps.power_gen` (0x0107) > `eps.power_cons` (0x0106) confirmé sur 3 orbites ou plus
- [ ] Température de la batterie dans la plage nominale : `tcs.temp_battery` (0x0407) entre -5 °C et +35 °C
- [ ] Cause racine de l'urgence puissance identifiée ou analyse en cours
- [ ] Plan de rétablissement par étapes convenu avec le directeur de vol pour la remise en service des charges
- [ ] Transition vers EMG-001 lorsque le SoC > 40 %, pour le retour aux opérations nominales

## Voie de rétablissement — remise sous tension des charges délestées
Une fois que cette procédure a stabilisé le bus et que la cause racine est comprise, **tous les sous-systèmes dont les lignes d'alimentation ont été coupées lors du délestage doivent être remis sous tension dans l'ordre maîtrisé défini par LEOP-007 (mise sous tension séquentielle)**. Ne **pas** se contenter de réactiver les lignes au coup par coup : LEOP-007 impose le bon séquencement sous-système→ligne→mode, l'espacement des courants d'appel, le préconditionnement thermique par les réchauffeurs de l'OBC et de la batterie, et les exemptions set_mode AOCS/charge utile de la condition d'alimentation à deux étages des TC. Renvoi : `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
