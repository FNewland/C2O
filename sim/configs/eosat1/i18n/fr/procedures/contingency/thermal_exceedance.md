# CTG-004 : Dépassement thermique
**Sous-système :** TCS
**Phase :** CONTINGENCY
**Révision :** 1.1 --- 2026-11-02 (décision de Franz P1) : chaque commande de réchauffeur du
cas froid est précédée d'un `EPS_POWER_ON` de sa ligne, avec contrôle. Ligne hors tension, la mise sur
ON du réchauffeur est refusée S1.8 et rien ne chauffe --- ainsi, en contingence, quand une zone s'est
refroidie, l'équipe peut toujours allumer son réchauffeur.
**Approuvé par :** directeur des opérations de vol

## Objet
Traiter un dépassement de limite thermique dans l'une quelconque des zones surveillées du satellite EOSAT-1.
Les limites jaunes indiquent que le paramètre approche de la limite opérationnelle et qu'une action
corrective est nécessaire pour éviter d'endommager le matériel. Cette procédure identifie la zone concernée,
applique les actions de contrôle thermique appropriées (activation des réchauffeurs dans les cas froids, délestage
dans les cas chauds) et surveille la tendance de température jusqu'au retour de la zone dans la plage nominale.

## Prérequis
- [ ] La télémesure TCS (SID 3) est reçue à >= 0.5 Hz
- [ ] La base de données des limites thermiques est disponible en console (réf. : EOSAT1-TCS-LIM-001)
- [ ] L'EPS dispose d'une marge de puissance suffisante pour activer les réchauffeurs — `eps.bat_soc` (0x0101) > 25 %
- [ ] L'angle bêta de l'orbite courante et la durée d'éclipse sont connus grâce à la dynamique du vol

### Référence des limites jaunes thermiques
| Zone | Paramètre | ID TM | Jaune froid | Jaune chaud |
|-------------|---------------------|--------|-------------|------------|
| OBC | `tcs.temp_obc` | 0x0406 | -10 °C | +55 °C |
| Batterie | `tcs.temp_battery` | 0x0407 | +2 °C | +42 °C |
| FPA | `tcs.temp_fpa` | 0x0408 | -45 °C | -15 °C |

## Déroulement

### Étape 1 — Identifier la zone thermique concernée
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27)
**Verify:** `tcs.temp_obc` (0x0406) — consigner la valeur, la comparer aux limites
**Verify:** `tcs.temp_battery` (0x0407) — consigner la valeur, la comparer aux limites
**Verify:** `tcs.temp_fpa` (0x0408) — consigner la valeur, la comparer aux limites
**Action:** Identifier la ou les zones en dépassement de limite jaune et déterminer si le dépassement est chaud ou froid
**GO/NO-GO:** Au moins une zone confirmée en jaune — suivre la branche appropriée

### Étape 2 A — Cas froid : activer le réchauffeur de la zone concernée
**Condition :** La température de la zone est inférieure à la limite jaune froide
**BRANCH:** `tcs.temp_battery < 2` -> GO `STEP-2A-BAT` | NO-GO `STEP-2A-OBC` (timeout 10 s)
**LABEL:** `STEP-2A-BAT`
**Note:** Batterie froide :
**TC:** `EPS_POWER_ON(line_index=5)` (Service 8, Subtype 1, func_id 19) — d'abord la ligne `htr_bat` (sans effet si déjà sur ON)
**Verify:** `eps.pl_htr_bat` (0x0115) = 1 sous 5s
**TC:** `HEATER_BATTERY(on=1)` (Service 8, Subtype 1, func_id 40)
**TC:** `GET_PARAM(param_id=0x040A)` (Service 20, Subtype 3) — `tcs.htr_battery` : le SID 3 n'est périodique que toutes les 60 s : lire la valeur que ce contrôle utilise
**Verify:** `tcs.htr_battery` (0x040A) = 1 (ON) en 5 s
**LABEL:** `STEP-2A-OBC`
**BRANCH:** `tcs.temp_obc < -10` -> GO `STEP-2A-OBCON` | NO-GO `STEP-2B` (timeout 10 s)
**LABEL:** `STEP-2A-OBCON`
**Note:** OBC froid :
**TC:** `EPS_POWER_ON(line_index=6)` (Service 8, Subtype 1, func_id 19) — d'abord la ligne `htr_obc` (sans effet si déjà sur ON)
**Verify:** `eps.pl_htr_obc` (0x0116) = 1 sous 5s
**TC:** `HEATER_OBC(on=1)` (Service 8, Subtype 1, func_id 41)
**TC:** `GET_PARAM(param_id=0x040B)` (Service 20, Subtype 3) — `tcs.htr_obc` : le SID 3 n'est périodique que toutes les 60 s : lire la valeur que ce contrôle utilise
**Verify:** `tcs.htr_obc` (0x040B) = 1 (ON) en 5 s
**Verify:** `eps.power_cons` (0x0106) augmente de la consommation attendue du réchauffeur (3 à 7 W par circuit)
**GO/NO-GO:** Réchauffeur confirmé actif et bilan de puissance tenable — passer à la surveillance

### Étape 2B — Cas chaud : réduire la charge thermique de la zone concernée
**LABEL:** `STEP-2B`
**Condition :** La température de la zone est supérieure à la limite jaune chaude
**BRANCH:** `tcs.temp_fpa > -15` -> GO `STEP-2B-FPA` | NO-GO `STEP-2B-OBC` (timeout 10 s)
**LABEL:** `STEP-2B-FPA`
**Note:** FPA chaud :
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) — supprimer la charge thermique de l'électronique
**Verify:** `payload.mode` (0x0600) = 0 (OFF) en 10 s
**LABEL:** `STEP-2B-OBC`
**BRANCH:** `tcs.temp_obc > 55` -> GO `STEP-2B-OBCHOT` | NO-GO `STEP-2B-BATCHK` (timeout 10 s)
**LABEL:** `STEP-2B-OBCHOT`
**Note:** OBC chaud : couper le réchauffeur de l'OBC, puis placer l'OBC en SAFE. Il
n'existe à bord aucun paramètre de délestage des tâches ; le mode SAFE de l'OBC est la
réduction commandée.
**TC:** `HEATER_OBC(on=0)` (Service 8, Subtype 1, func_id 41) — réchauffeur de l'OBC sur OFF
**TC:** `GET_PARAM(param_id=0x040B)` (Service 20, Subtype 3) — `tcs.htr_obc` : le SID 3 n'est périodique que toutes les 60 s : lire la valeur que ce contrôle utilise
**Verify:** `tcs.htr_obc` (0x040B) = 0 (OFF) en 5 s
**TC:** `OBC_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 50) — OBC en SAFE
**Verify:** `obdh.mode == 1` (0x0300, timeout 10 s) — SAFE
**LABEL:** `STEP-2B-BATCHK`
**BRANCH:** `tcs.temp_battery > 42` -> GO `STEP-2B-BAT` | NO-GO `STEP-3` (timeout 10 s)
**LABEL:** `STEP-2B-BAT`
**Note:** Batterie chaude : vérifier que `tcs.htr_battery` (0x040A) = 0 (OFF) ; s'il est sur ON, le couper :
**BRANCH:** `tcs.htr_battery == 1` -> GO `STEP-2B-BATOFF` | NO-GO `STEP-3` (timeout 10 s)
**LABEL:** `STEP-2B-BATOFF`
**TC:** `HEATER_BATTERY(on=0)` (Service 8, Subtype 1, func_id 40)
**TC:** `GET_PARAM(param_id=0x040A)` (Service 20, Subtype 3) — `tcs.htr_battery` : le SID 3 n'est périodique que toutes les 60 s : lire la valeur que ce contrôle utilise
**Verify:** `tcs.htr_battery` (0x040A) = 0 (OFF) en 5 s
**GO/NO-GO:** Actions de réduction de charge confirmées — passer à la surveillance

### Étape 3 — Surveiller la tendance de température
**LABEL:** `STEP-3`
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — données de servitude TCS ; répéter toutes les 60 s pendant 15 minutes
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — données de servitude EPS (SoC de la batterie)
**Verify:** La température de la zone concernée évolue vers la plage nominale à >= 0.2 °C/min
**Verify:** Aucune autre zone ne dérive vers ses limites jaunes par effet secondaire
**Verify:** `eps.bat_soc` (0x0101) > 20 % — le fonctionnement des réchauffeurs ne vide pas excessivement la batterie
**GO/NO-GO:** Tendance de température nominale — poursuivre la surveillance. En l'absence d'amélioration au bout de 15 min, l'étape 4 s'applique. -> GO `STEP-5` | NO-GO `STEP-4`

### Étape 4 — Ajuster les consignes des réchauffeurs ou faire remonter l'anomalie
**LABEL:** `STEP-4`
**GO/NO-GO:** Cas froid — relever le thermostat du réchauffeur -> GO `STEP-4C` | NO-GO `STEP-4H`
**LABEL:** `STEP-4C`
**TC:** `HEATER_SET_SETPOINT(circuit=<0 battery | 1 obc | 2 thruster>, on_temp=<current +5 C>, off_temp=<on_temp +5 C>)` (Service 8, Subtype 1, func_id 44)  
**Octets émis :** `2C <circuit:uint8> <on_temp:float32> <off_temp:float32>` — p. ex. circuit 0, on 5.0 / off 10.0 °C = `2C 00 40 A0 00 00 41 20 00 00`
**Note:** Il n'existe pas de paramètre `tcs.htr_<zone>_setpoint` — les thermostats des réchauffeurs se reconfigurent par la fonction S8 44, pas par écriture de paramètre S20.
**Verify:** Le rapport cyclique du réchauffeur augmente (cycles ON plus fréquents observés dans la télémesure)
**LABEL:** `STEP-4H`
**GO/NO-GO:** Cas chaud et température encore en hausse — passer en COARSE_SUN -> GO `STEP-4HS` | NO-GO `STEP-4E`
**LABEL:** `STEP-4HS`
**TC:** `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) — COARSE_SUN, pour optimiser l'attitude du satellite pour la dissipation thermique
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — données de servitude SCAO (aocs.mode est dans le SID 2, pas dans le SID 3 thermique)
**Verify:** `aocs.mode` (0x020F) = 3 en 15 s
**LABEL:** `STEP-4E`
**GO/NO-GO:** Si la température se stabilise dans un délai supplémentaire de 15 min, l'étape 5 s'applique. À l'approche d'une limite rouge, faire remonter l'anomalie. -> GO `STEP-5` | NO-GO `STEP-4X`
**LABEL:** `STEP-4X`
**Note:** L'escalade dépend de l'état du réchauffeur de la zone concernée. Un
réchauffeur sur ON dans une zone au-dessus de sa limite chaude est la signature d'un
emballement thermique (EMG-006) ; réchauffeur sur OFF, la chaleur vient d'ailleurs et le
satellite passe en mode survie d'urgence (EMG-001). La branche exploitable par la machine
est celle du réchauffeur de la batterie ; pour la zone OBC, lire `tcs.htr_obc` (0x040B) à la place.
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — relire l'état du réchauffeur
**BRANCH:** `tcs.htr_battery == 1` -> GO `STEP-4X-EMG006` | NO-GO `STEP-4X-EMG001` (timeout 70 s)
**LABEL:** `STEP-4X-EMG006`
**Note:** Réchauffeur sur ON — exécuter EMG-006 (emballement thermique) maintenant.
**GO/NO-GO:** Relais passé à EMG-006 -> GO `STEP-END` | NO-GO `STEP-END`
**LABEL:** `STEP-4X-EMG001`
**Note:** Réchauffeur sur OFF — exécuter EMG-001 (mode survie d'urgence) maintenant ;
son étape 1 commande le mode EMERGENCY de l'OBC.
**GO/NO-GO:** Relais passé à EMG-001 -> GO `STEP-END` | NO-GO `STEP-END`

### Étape 5 — Confirmer la reprise et rétablir les opérations
**LABEL:** `STEP-5`
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27)
**Verify:** Toutes les températures des zones dans la plage nominale (verte)
**Note:** Uniquement si des réchauffeurs ont été activés pour le cas froid. Circuits : 0 batterie,
1 OBC, 2 propulseur. Les octets de codage du circuit batterie sont `2D 00`.
**GO/NO-GO:** Des réchauffeurs ont été activés pour le cas froid -> GO `STEP-5A` | NO-GO `STEP-5B`
**LABEL:** `STEP-5A`
**TC:** `HEATER_AUTO_MODE(circuit=0)` (Service 8, Subtype 1, func_id 45) — retour du circuit batterie sous thermostat
**LABEL:** `STEP-5B`
**Action:** Si des charges ont été délestées pour le cas chaud, les réactiver dans l'ordre de LEOP-007 (Mise sous tension séquentielle), comme dans les étapes de rétablissement de CTG-023 (Délestage progressif)
**GO/NO-GO:** Toutes les températures nominales et opérations rétablies — reprise terminée

## Conduite à tenir hors nominal
- Si la température de la batterie dépasse +45 °C (limite rouge) : faire remonter selon l'état du réchauffeur de la batterie, comme à l'étape 4 — réchauffeur sur ON (`tcs.htr_battery` (0x040A) = 1) : exécuter EMG-006 (emballement thermique) ; réchauffeur sur OFF : exécuter EMG-001 (mode survie d'urgence), qui commande le mode EMERGENCY
- Si la température de l'OBC dépasse +60 °C : commander immédiatement `OBC_SET_MODE(mode=1)` pour passer en SAFE
- Si un circuit de réchauffeur ne s'active pas : suspecter une défaillance matérielle du réchauffeur, consigner l'anomalie, ajuster l'attitude pour un contrôle thermique passif
- Si plusieurs zones dépassent simultanément leurs limites : suspecter un changement de géométrie orbitale ou une anomalie SCAO — contrôler `aocs.mode` (0x020F) et exécuter CTG-002 si l'attitude est hors nominal

## Postconditions
**LABEL:** `STEP-END`
- [ ] Toutes les zones thermiques dans les limites nominales (vertes)
- [ ] États des réchauffeurs documentés (auto/manuel/arrêt pour chaque circuit)
- [ ] Bilan de puissance réévalué avec les éventuelles nouvelles charges de réchauffeurs
- [ ] Rapport d'anomalie établi avec les courbes de tendance thermique et une hypothèse de cause première

## Chemin de reprise — remise sous tension des charges délestées
Une fois le bus stabilisé par cette procédure et la cause première comprise, **tout sous-système dont les lignes d'alimentation ont été mises hors tension lors du délestage doit être remis en service dans l'ordre maîtrisé défini par LEOP-007 (mise sous tension séquentielle)**. Ne **pas** se contenter de réactiver les lignes au coup par coup : LEOP-007 impose le bon enchaînement sous-système→ligne→mode, l'espacement des courants d'appel, le préconditionnement thermique des réchauffeurs OBC/batterie et les exemptions set_mode AOCS/charge utile au verrou d'alimentation à deux niveaux des TC. Référence croisée : `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
