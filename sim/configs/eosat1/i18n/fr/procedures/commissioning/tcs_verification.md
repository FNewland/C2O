# COM-002 : Vérification du TCS
**Sous-système :** TCS
**Phase :** COMMISSIONING
**Révision :** 2.0 --- point 2026-08c sur la gestion des réchauffeurs : l'ancienne fiche
faisait cycler des réchauffeurs dont les LIGNES EPS n'avaient jamais été mises sous tension (l'interrupteur
du réchauffeur obéissait, rien ne chauffait, et les étapes « vérifier le chauffage » lisaient la dérive
ambiante). Chaque essai de réchauffeur ÉTABLIT désormais SON ÉTAT D'ABORD --- alimenter la ligne,
puis cycler le réchauffeur, puis rétablir la ligne dans son état d'entrée. Les anciennes
étapes 4/5 commandaient en outre les MAUVAISES fonctions (func 41 HEATER_OBC étiquetée
« batterie », func 42 HEATER_THRUSTER étiquetée « OBC ») ; les fonctions correspondent désormais aux
circuits : 40 = batterie, 41 = OBC.
**Révision :** 2.1 --- 2026-11-02 (constat P1, décision de Franz) : la fiche ne remet plus
les lignes de réchauffeurs sur OFF. Avec les lignes 5/6 hors tension pendant toute la phase nominale,
la batterie dérivait de +17 C jusqu'au rouge (-0,3 C) en éclipse, et toutes les commandes de réchauffeur
des fiches d'urgence étaient refusées. Un petit satellite laisse ses lignes de réchauffeurs batterie et OBC
sous tension, sous contrôle thermostatique, après la mise en service ; EOSAT-1 aussi, désormais. Chaque essai
se termine par `HEATER_AUTO_MODE`, qui rend le circuit à son thermostat.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-001 --- maintien COARSE_SUN, phase 5. Les lignes de réchauffeurs
`htr_bat` (5) / `htr_obc` (6) sont sur OFF, sauf si LEOP-007, étape 2, en a alimenté une pour
une raison précise ; lire le journal LEOP ainsi que `eps.pl_htr_bat` (0x0115) / `eps.pl_htr_obc`
(0x0116) avant de commencer, et consigner les deux. Cette fiche laisse les deux lignes sur ON,
réchauffeurs sous contrôle thermostatique, quel que soit l'état d'entrée.

## Objet
Vérifier le sous-système de contrôle thermique en comparant toutes les zones thermiques surveillées
aux plages de température prédites. Valider le fonctionnement des circuits de réchauffeurs de la batterie et de la
propulsion (le cas échéant). Établir les profils thermiques de référence sur une orbite complète
(phase éclairée et éclipse) et vérifier l'interface du refroidisseur du FPA avant l'activation de la charge utile.

## Prérequis
- [ ] COM-001 (Vérification de l'EPS) terminée — bilan de puissance vérifié
- [ ] Satellite en mode COARSE_SUN avec un pointage solaire stable
- [ ] Au moins une orbite complète de télémesure thermique archivée
- [ ] Liaison bidirectionnelle en bande S active
- [ ] `eps.bat_soc` (0x0101) > 60 %

## Déroulement

### Étape 1 — Demander les données de servitude thermiques
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27)
**Verify:** `tcs.temp_obc` (0x0406) dans la plage [-5C, +45C] sous 10s
**Verify:** `tcs.temp_battery` (0x0407) dans la plage [+5C, +35C] sous 10s
**Verify:** `tcs.temp_fpa` (0x0408) rapportée (charge utile hors tension, non refroidie : +8C à +14C attendus) sous 10s
**GO/NO-GO:** Toutes les zones thermiques dans les limites opérationnelles

### Étape 2 — Surveiller le profil thermique pendant la phase éclairée
**Action:** Recueillir des échantillons de télémesure thermique toutes les 2 minutes pendant 30 minutes en phase éclairée. Consigner les tendances de température de toutes les zones.
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — renouveler toutes les 120s
**Verify:** `tcs.temp_obc` (0x0406) stable ou en lente hausse (< 1C/min) sous 10s
**Verify:** `tcs.temp_battery` (0x0407) stable sous 10s
**GO/NO-GO:** Tendances thermiques nominales en phase éclairée

### Étape 3 — Surveiller le profil thermique pendant l'éclipse
**Action:** Poursuivre la surveillance thermique pendant l'entrée en éclipse et toute la durée de l'éclipse.
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — à l'entrée en éclipse, à mi-éclipse, à la sortie d'éclipse
**Verify:** `tcs.temp_obc` (0x0406) > -5C pendant toute l'éclipse sous 10s
**Verify:** `tcs.temp_battery` (0x0407) > +5C pendant toute l'éclipse sous 10s
**Action:** Consigner les vitesses de baisse de température. Refroidissement attendu de l'OBC ~0,5 °C/min ; la batterie doit être protégée par son inertie thermique.
**GO/NO-GO:** Toutes les zones au-dessus des limites opérationnelles minimales pendant l'éclipse

### Étape 4 — Essayer le circuit du réchauffeur batterie (établir l'état D'ABORD)
**Action:** Consigner l'état d'entrée de `eps.pl_htr_bat` (0x0115). Un réchauffeur
dont la LIGNE est hors tension obéit à la commande d'interrupteur et ne chauffe rien — exactement le
piège dans lequel l'ancienne fiche était tombée.
**TC:** `EPS_POWER_ON(line_index=5)` (Service 8, Subtype 1, func_id 19) — alimenter la ligne htr_bat
**Verify:** `eps.pl_htr_bat` (0x0115) = 1 sous 5s
**TC:** `HEATER_BATTERY(on=1)` (Service 8, Subtype 1, func_id 40) — le circuit batterie (func 40, et non 41)
**Verify:** Mise sur ON du réchauffeur batterie acquittée sous 5s
**Action:** Surveiller `tcs.temp_battery` (0x0407) pendant 3 minutes pour confirmer l'effet de chauffage.
**Verify:** `tcs.temp_battery` (0x0407) en hausse ou stable (le réchauffeur compense le refroidissement) sous 180s
**TC:** `HEATER_BATTERY(on=0)` (Service 8, Subtype 1, func_id 40)
**Verify:** Mise sur OFF du réchauffeur batterie acquittée sous 5s
**TC:** `HEATER_AUTO_MODE(circuit=0)` (Service 8, Subtype 1, func_id 45) — rendre le circuit batterie à son thermostat (ON sous +5 C, OFF au-dessus de +10 C)
**Verify:** `eps.pl_htr_bat` (0x0115) = 1 --- la ligne RESTE sur ON : c'est désormais la configuration nominale
**GO/NO-GO:** Circuit du réchauffeur batterie opérationnel, ligne sur ON sous contrôle thermostatique

### Étape 5 — Essayer le circuit du réchauffeur OBC (établir l'état D'ABORD)
**Action:** Consigner l'état d'entrée de `eps.pl_htr_obc` (0x0116).
**TC:** `EPS_POWER_ON(line_index=6)` (Service 8, Subtype 1, func_id 19) — alimenter la ligne htr_obc
**Verify:** `eps.pl_htr_obc` (0x0116) = 1 sous 5s
**TC:** `HEATER_OBC(on=1)` (Service 8, Subtype 1, func_id 41) — le circuit OBC (func 41, et non 42 — 42 est le réchauffeur du lit catalytique du PROPULSEUR, qui n'est pas touché en dehors de la préparation des manœuvres)
**Verify:** Mise sur ON du réchauffeur OBC acquittée sous 5s
**Verify:** `tcs.temp_obc` (0x0406) stable ou en hausse sous 120s
**TC:** `HEATER_OBC(on=0)` (Service 8, Subtype 1, func_id 41)
**Verify:** Mise sur OFF du réchauffeur OBC acquittée sous 5s
**TC:** `HEATER_AUTO_MODE(circuit=1)` (Service 8, Subtype 1, func_id 45) — rendre le circuit OBC à son thermostat (ON sous +5 C, OFF au-dessus de +10 C)
**Verify:** `eps.pl_htr_obc` (0x0116) = 1 --- la ligne RESTE sur ON : c'est désormais la configuration nominale
**GO/NO-GO:** Circuit du réchauffeur OBC opérationnel, ligne sur ON sous contrôle thermostatique

### Étape 6 — Vérifier les réglages des thermostats autonomes des réchauffeurs
**TC:** `GET_PARAM(param_id=0x0410)` (Service 20, Subtype 3) — seuil de mise sur ON du réchauffeur batterie
**TC:** `GET_PARAM(param_id=0x0411)` (Service 20, Subtype 3) — seuil de mise sur OFF du réchauffeur batterie
**Verify:** Seuil ON du réchauffeur batterie = +5C sous 10s
**Verify:** Seuil OFF du réchauffeur batterie = +10C sous 10s
**Action:** Confirmer que le thermostat autonome maintiendra la batterie dans la plage [+5C, +35C] sans intervention du sol.
**GO/NO-GO:** Seuils autonomes des réchauffeurs correctement configurés

### Étape 7 — Contrôle de l'interface du refroidisseur du FPA (avant activation)
**Action:** Vérifier l'interface d'alimentation du refroidisseur du FPA et la relecture de la thermistance avant la recette en orbite de la charge utile.
**TC:** `GET_PARAM(param_id=0x040C)` (Service 20, Subtype 3) — `tcs.cooler_fpa`, l'état effectif du refroidisseur
**Verify:** `tcs.cooler_fpa` (0x040C) = 0 (refroidisseur sur OFF) sous 10s
**TC:** `GET_PARAM(param_id=0x0114)` (Service 20, Subtype 3) — `eps.pl_fpa_cooler`, l'alimentation EPS du refroidisseur
**Verify:** `eps.pl_fpa_cooler` (0x0114) = 0 (ligne non alimentée) sous 10s
**Verify:** `tcs.temp_fpa` (0x0408) cohérente avec l'équilibre non refroidi (+8C à +14C) sous 10s
**Action:** Consigner la température de référence du FPA pour comparaison lors de l'activation du refroidisseur (COM-010).
**GO/NO-GO:** Interface thermique du FPA saine, température de référence consignée

### Étape 8 — Établir le rapport thermique de référence
**Action:** Produire le profil thermique orbital indiquant les températures min/max/moyenne de chaque zone sur une orbite complète. Les comparer aux prédictions du modèle thermique. Documenter tout écart.
**GO/NO-GO:** Performances thermiques conformes aux prédictions du modèle (tolérance de +/- 5C)

## Conduite à tenir hors nominal
- Si `tcs.temp_battery` < +5C et que le réchauffeur ne répond pas : il n'existe AUCUN circuit de réchauffeur batterie redondant : `subsystems/tcs.yaml` ne déclare que trois
  circuits — 0 batterie, 1 obc, 2 propulseur. Envisager un ajustement d'attitude pour
  augmenter l'échauffement solaire, et délester des charges pour protéger les éléments. Alerter l'ingénieur thermique.
- Si `tcs.temp_obc` > +45C : vérifier que l'attitude de pointage solaire ne provoque pas un échauffement solaire excessif du panneau de l'OBC. Envisager un décalage d'attitude temporaire. Vérifier si le réchauffeur de l'OBC est bloqué sur ON via `GET_PARAM(param_id=0x040B)` (`tcs.htr_obc`).
- Si les températures en éclipse baissent plus vite que prévu : le modèle thermique doit peut-être être mis à jour. Rechercher des indices d'endommagement du MLI. Augmenter le rapport cyclique des réchauffeurs à l'approche des limites de survie.
- Si la lecture de température du FPA est invalide (hors de la bande d'alarme S12 de -25.5C à +17.5C, refroidisseur sur OFF) : recouper avec `payload.fpa_temp` (0x0601), qui lit la même chaîne physique avec 0,5 K de moins. Une concordance signifie que le FPA est réellement hors bande ; un désaccord met en cause l'un des deux capteurs. Si la thermistance du TCS est défaillante, la recette en orbite de la charge utile peut se poursuivre sur 0x0601, la perte de redondance étant consignée.
- Si les zones thermiques présentent une asymétrie inattendue : cela peut indiquer un décollement partiel d'une couverture MLI ou une modification des facteurs de vue. Documenter et suivre la tendance sur plusieurs orbites.

## Postconditions
- [ ] Toutes les zones thermiques vérifiées dans les limites opérationnelles
- [ ] Profil thermique sur une orbite complète consigné et archivé
- [ ] Circuit du réchauffeur batterie vérifié opérationnel
- [ ] Circuit du réchauffeur OBC vérifié opérationnel
- [ ] Seuils autonomes des réchauffeurs confirmés corrects
- [ ] Interface du refroidisseur du FPA contrôlée, température de référence consignée
- [ ] Rapport thermique de référence établi

## État de sortie
- Lignes de réchauffeurs `htr_bat` (5) et `htr_obc` (6) sur ON, les deux circuits en mode AUTO
  (thermostat) : la configuration nominale pour le reste de la mission. Toute commande de réchauffeur
  d'une fiche ultérieure trouve sa ligne déjà alimentée
- Aucun mode, palier ou verrou modifié par cette fiche

**PROCÉDURE SUIVANTE :** COM-004 (Vérification des actionneurs SCAO --- active les roues et commande NOMINAL ; COM-003 la suit, décision Q16)
