# NOM-010 : Transition d'éclipse

**Catégorie :** Nominal
**Poste responsable :** Puissance et thermique (EPS/TCS)
**Postes associés :** dynamique du vol (AOCS), TT&C
**Difficulté :** Intermédiaire

## Objectif
Coordonner la traversée maîtrisée d'une période d'éclipse orbitale par le satellite, en s'assurant que
l'état de charge de la batterie est suffisant, que les consignes des réchauffeurs sont configurées pour la
phase froide, que le mode de propagation d'éclipse de l'AOCS est engagé et que la tension du bus reste stable
tout du long. Cette procédure couvre aussi la vérification de la reprise de la production de puissance après
la sortie d'éclipse.

## Prérequis
- [ ] Satellite en opérations nominales — `obdh.mode` (0x0300) = 0 (NOMINAL)
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Prévision d'orbite à jour disponible, avec les heures d'entrée et de sortie d'éclipse
- [ ] Aucune anomalie en suspens ni procédure de contingence active
- [ ] Séances de prise de vue terminées ou suspendues avant l'entrée en éclipse

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| eps.bat_soc | 0x0101 | > 60 % avant l'entrée en éclipse |
| eps.bus_voltage | 0x0105 | > 28.0 V |
| eps.eclipse_flag | 0x0108 | 0 (éclairé) avant l'entrée, 1 pendant l'éclipse |
| eps.power_gen | 0x0107 | > 0 W au Soleil, ~0 W pendant l'éclipse |
| eps.bat_current | 0x0109 | Négatif (décharge) pendant l'éclipse |
| tcs.htr_battery | 0x040A | État du réchauffeur |
| tcs.htr_obc | 0x040B | État du réchauffeur |
| tcs.temp_battery | 0x0407 | Entre 0 et 40 °C |
| tcs.temp_obc | 0x0406 | Entre 5 et 55 °C |
| aocs.mode | 0x020F | 8 (ECLIPSE) pendant l'éclipse |
| aocs.att_error | 0x0217 | < 1.0 deg |

## Commandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| HEATER_SET_SETPOINT | 8 | 1 | 44 | Modifier les consignes de thermostat des réchauffeurs pour l'éclipse |
| HEATER_AUTO_MODE | 8 | 1 | 45 | Rendre le réchauffeur au contrôle autonome par thermostat |
| AOCS_SET_MODE | 8 | 1 | 0 | Mettre l'AOCS en mode de propagation d'éclipse |
| FPA_COOLER | 8 | 1 | 43 | Couper le refroidisseur du FPA pour économiser la puissance |

## Déroulement

### Étape 1 : Vérifier l'état de charge de la batterie
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — demander les données de servitude EPS
**Verify:** `eps.bat_soc` (0x0101) > 60 %
**Verify:** `eps.bus_voltage` (0x0105) > 28.0 V
**Verify:** `eps.bat_temp` (0x0102) entre 0 et 40 °C
**Verify:** `eps.bat_current` (0x0109) — consigner la valeur de référence
**GO/NO-GO:** Si SoC <= 60 %, se mettre en attente (HOLD). Envisager de différer les charges non essentielles ou d'attendre
un temps de charge supplémentaire. Si SoC < 50 %, NE PAS continuer — réduire les charges
et réévaluer après un passage éclairé supplémentaire.

### Étape 2 : Vérifier et ajuster les consignes des réchauffeurs pour l'éclipse
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — demander les données de servitude TCS
**Verify:** `tcs.htr_battery` (0x040A) — consigner l'état actuel
**Verify:** `tcs.htr_obc` (0x040B) — consigner l'état actuel
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — données de servitude EPS : les états de ligne ci-dessous sont dans le SID 1
**Verify:** `eps.pl_htr_bat` (0x0115) = 1 et `eps.pl_htr_obc` (0x0116) = 1 — une consigne ne fait rien sur une ligne de réchauffeur non alimentée. La recette en vol peut laisser les deux lignes sur OFF (COM-002 rétablit son état d'entrée), et la batterie passe alors sous la limite jaune de 2 C en ~2 h (mesuré le 2026-11-02) : si l'une d'elles vaut 0, l'alimenter d'abord
**TC:** `EPS_POWER_ON(line_index=5)` (Service 8, Subtype 1, func_id 19) — ligne `htr_bat`, seulement si 0x0115 = 0
**TC:** `EPS_POWER_ON(line_index=6)` (Service 8, Subtype 1, func_id 19) — ligne `htr_obc`, seulement si 0x0116 = 0
**Verify:** `tcs.temp_battery` (0x0407) > 5 °C
**Verify:** `tcs.temp_obc` (0x0406) > 10 °C
**Note:** Si la marge de température de la batterie est faible (< 8 °C), relever la consigne du réchauffeur batterie
**TC:** `HEATER_SET_SETPOINT(circuit=0, on_temp=3.0, off_temp=8.0)` (Service 8, Subtype 1, func_id 44) — consigne
**Note:** Si la marge de température de l'OBC est faible (< 12 °C), relever la consigne du réchauffeur OBC :
**TC:** `HEATER_SET_SETPOINT(circuit=1, on_temp=8.0, off_temp=13.0)` (Service 8, Subtype 1, func_id 44) — réchauffeur OBC ON 8 °C / OFF 13 °C
**GO/NO-GO:** Consignes des réchauffeurs configurées pour la phase froide de l'éclipse — continuer.

### Étape 3 : Couper le refroidisseur du FPA pour économiser la puissance
**Note:** Si la charge utile est en STANDBY ou OFF, couper le refroidisseur du FPA pour réduire la puissance consommée pendant l'éclipse :
**TC:** `FPA_COOLER(on=0)` (Service 8, Subtype 1, func_id 43) — refroidisseur du FPA sur OFF
**TC:** `GET_PARAM(param_id=0x040C)` (Service 20, Subtype 3) — `tcs.cooler_fpa` : le SID 3 n'est périodique que toutes les 60 s : lire la valeur que ce contrôle utilise
**Verify:** `tcs.cooler_fpa` (0x040C) = 0 (OFF) sous 5 s
**Verify:** `eps.power_cons` (0x0106) diminue d'environ 15 W
**Note:** Le refroidisseur du FPA sera réactivé après la sortie d'éclipse, lorsque le bilan de puissance sera positif.
**GO/NO-GO:** Refroidisseur coupé et consommation réduite — continuer.

### Étape 4 : Vérifier la transition de l'AOCS en mode éclipse
**TC:** `AOCS_SET_MODE(mode=8)` (Service 8, Subtype 1, func_id 0) — commander l'AOCS en mode de propagation d'éclipse
**Verify:** `aocs.mode` (0x020F) = 8 (ECLIPSE) sous 15 s
**Verify:** `aocs.att_error` (0x0217) < 1.0 deg
**Note:** En mode de propagation d'éclipse, l'AOCS propage l'attitude sur les seuls gyroscopes, sans mise à jour
par le senseur stellaire (celui-ci peut perdre la poursuite dans l'ombre de la Terre).
**GO/NO-GO:** AOCS confirmé en mode de propagation d'éclipse — continuer.

### Étape 5 : Surveiller la tension du bus à l'entrée en éclipse
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — surveiller la télémesure EPS toutes les 30 s
**Verify:** `eps.eclipse_flag` (0x0108) = 1 (éclipse confirmée)
**Verify:** `eps.power_gen` (0x0107) tombe à ~0 W (générateurs solaires dans l'ombre)
**Verify:** `eps.bus_voltage` (0x0105) reste > 27.0 V
**Verify:** `eps.bat_soc` (0x0101) — surveiller la vitesse de décharge, consigner le SoC toutes les 5 min
**Verify:** `eps.bat_current` (0x0109) est négatif (batterie en décharge)
**Action:** Si la tension du bus descend sous 27.0 V, procéder au délestage selon
CTG-001 (délestage sur sous-tension).
**GO/NO-GO:** Tension du bus stable au-dessus de 27.0 V — poursuivre la surveillance.

### Étape 6 : Surveiller les conditions thermiques pendant l'éclipse
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — surveiller la télémesure TCS toutes les 60 s
**Verify:** `tcs.temp_battery` (0x0407) reste > 0 °C
**Verify:** `tcs.temp_obc` (0x0406) reste > 5 °C
**Verify:** `tcs.htr_battery` (0x040A) — le réchauffeur cycle comme prévu
**Verify:** `tcs.htr_obc` (0x040B) — le réchauffeur cycle comme prévu
**Action:** Si une température approche de sa limite basse, vérifier que le réchauffeur est ON. Si le réchauffeur
ne répond pas, suivre EMG-006 (urgence emballement thermique) pour le diagnostic des
réchauffeurs.
**GO/NO-GO:** Toutes les températures dans les limites — poursuivre la surveillance.

### Étape 7 : Vérifier la reprise de la production de puissance après la sortie d'éclipse
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — surveiller la télémesure EPS pendant la sortie d'éclipse du satellite
**Verify:** `eps.eclipse_flag` (0x0108) = 0 (éclairé)
**Verify:** `eps.power_gen` (0x0107) > 25 W dans les 60 s qui suivent la sortie d'éclipse
**Verify:** `eps.sa_a_current` (0x0103) > 0.3 A
**Verify:** `eps.sa_b_current` (0x0104) > 0.3 A
**Verify:** `eps.bus_voltage` (0x0105) remontant au-dessus de 28.0 V
**Verify:** `eps.bat_soc` (0x0101) — consigner le SoC après éclipse et confirmer la tendance à la charge
**GO/NO-GO:** Production de puissance confirmée et batterie en charge — passer au rétablissement.

### Étape 8 : Rétablir la configuration nominale
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0) — ramener l'AOCS en pointage nadir nominal
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL) sous 30 s
**Verify:** `aocs.att_error` (0x0217) < 0.1 deg sous 300 s (phase C : la dérive d'éclipse sur gyroscopes seuls doit être réestimée et le correcteur PD reconverge dans son temps de stabilisation réel)
**Note:** Uniquement si une prise de vue est prévue sur cette orbite — le refroidisseur est une charge de 15 W.
**TC:** `FPA_COOLER(on=1)` (Service 8, Subtype 1, func_id 43) — réactiver le refroidisseur du FPA.
Depuis la phase 4, cette voie alimente aussi la ligne EPS 4 (`eps.pl_fpa_cooler`, 0x0114) ;
ce n'était pas le cas auparavant, d'où le fait que le FPA n'atteignait jamais sa consigne.
**TC:** `GET_PARAM(param_id=0x040C)` (Service 20, Subtype 3) — `tcs.cooler_fpa` : le SID 3 n'est périodique que toutes les 60 s : lire la valeur que ce contrôle utilise
**Verify:** `tcs.cooler_fpa` (0x040C) = 1 (ACTIVE) sous 5 s
**Note:** Rétablir les consignes nominales des réchauffeurs si elles ont été modifiées à l'étape 2.
**TC:** `HEATER_AUTO_MODE(circuit=0)` (Service 8, Subtype 1, func_id 45) — circuit batterie rendu au thermostat
**TC:** `HEATER_AUTO_MODE(circuit=1)` (Service 8, Subtype 1, func_id 45) — circuit OBC rendu au thermostat
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — données de servitude EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — données de servitude AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — données de servitude TCS
**Verify:** Tous les sous-systèmes nominaux dans la collecte HK complète.

## Critères de vérification
- [ ] SoC de la batterie resté au-dessus de 40 % pendant toute l'éclipse (consigner le SoC minimal)
- [ ] Tension du bus restée au-dessus de 27.0 V pendant toute l'éclipse
- [ ] Toutes les températures restées dans les limites opérationnelles
- [ ] AOCS ayant maintenu l'attitude à 1.0 deg près pendant la propagation d'éclipse
- [ ] Production de puissance reprise dans les 60 s qui suivent la sortie d'éclipse
- [ ] Tous les sous-systèmes revenus en configuration nominale après l'éclipse

## Contingence
- Si la tension du bus descend sous 27.0 V pendant l'éclipse : exécuter CTG-001
  (délestage sur sous-tension) — délester les charges par ordre de priorité.
- Si le SoC de la batterie descend sous 30 % pendant l'éclipse : délester immédiatement les charges de la charge utile et du
  refroidisseur. Si le SoC descend sous 20 %, exécuter CTG-001.
- Si le réchauffeur ne s'active pas et que la température tend vers sa limite basse : commander manuellement le
  réchauffeur sur ON. En l'absence de réponse, envisager de délester la ligne d'alimentation du réchauffeur et d'accepter le
  dépassement de température jusqu'à la sortie d'éclipse.
- Si l'AOCS ne passe pas en mode de propagation d'éclipse : conserver le mode actuel.
  Surveiller étroitement l'erreur d'attitude. Si l'erreur d'attitude dépasse 5 deg, exécuter
  CTG-008 ou l'entrée en mode survie.
- Si la production de puissance ne reprend pas après la sortie d'éclipse : vérifier l'orientation des générateurs solaires.
  Contrôler `eps.sa_a_current` et `eps.sa_b_current`. S'ils sont tous deux proches de zéro, soupçonner un problème de générateur ou
  d'attitude AOCS. Exécuter la reprise en mode de pointage solaire de l'AOCS.
