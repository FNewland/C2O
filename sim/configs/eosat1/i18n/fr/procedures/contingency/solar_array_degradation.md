# CTG-009 : Dégradation du générateur solaire
**Sous-système :** EPS
**Phase :** CONTINGENCY
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Traiter une dégradation détectée de la puissance fournie par le générateur solaire, signalée par un courant
inférieur à la valeur attendue pour les conditions d'éclairement du moment. EOSAT-1 dispose de six panneaux montés sur les faces et de deux
ailes solaires déployables (+/-Y) qui fournissent ensemble environ 64 W sous un angle solaire optimal
(ailes déployées, surface totale de 0,78 m²). Un déficit de courant persistant de plus de 20 % par rapport aux valeurs prévues sur l'un ou l'autre
des générateurs impose une investigation et, le cas échéant, des ajustements opérationnels pour maintenir un
bilan de puissance positif sur chaque orbite.

Le satellite détecte une chaîne dégradée (surveillance S12 du rendement, TM(12,9) et événement S5
0x914C / 0x914D) mais n'agit pas : mettre ou non la charge utile hors tension est une décision de
l'équipe, prise à l'étape 4 selon la gravité de la perte (rendement des chaînes et bilan de
puissance). Si la puissance vient réellement à manquer avant, le délestage bord sur tension bus
(sous 28.4 V, charge utile d'abord) met la charge utile hors tension tout seul ; c'est le filet de
sécurité, pas le plan.

## Prérequis
- [ ] La télémesure EPS (SID 1) est reçue à >= 0.5 Hz
- [ ] Les données d'éclairement de l'orbite courante sont disponibles — angle bêta, fraction éclairée, angles d'incidence
- [ ] Les courants SA-A et SA-B prévus pour l'attitude et l'éclairement courants sont affichés en console (réf. : EOSAT1-PWR-BUD-001)
- [ ] Le SCAO est en NOMINAL ou en COARSE_SUN, avec une orientation connue du générateur solaire
- [ ] `eps.bat_soc` (0x0101) > 25 % — marge suffisante pour la durée de l'investigation

## Déroulement

### Étape 1 — Quantifier la dégradation
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.sa_a_current` (0x0103) — consigner la valeur et la comparer à la prévision (> 1.0 A attendu en conditions optimales)
**Verify:** `eps.sa_b_current` (0x0104) — consigner la valeur et la comparer à la prévision (> 1.0 A attendu en conditions optimales)
**Verify:** `eps.power_gen` (0x0107) — consigner la production totale
**TC:** `GET_PARAM(param_id=0x014C)` (Service 20, Subtype 3) — `eps.sa_a_yield_pct`
**TC:** `GET_PARAM(param_id=0x014D)` (Service 20, Subtype 3) — `eps.sa_b_yield_pct`
**TC:** `GET_PARAM(param_id=0x014E)` (Service 20, Subtype 3) — `eps.sa_string_lit`
**Verify:** `eps.sa_a_yield_pct` (0x014C) et `eps.sa_b_yield_pct` (0x014D) — rendement bord de chaque chaîne par rapport à une chaîne saine dans la même géométrie solaire (valide seulement tant que le bit de la chaîne est positionné dans `eps.sa_string_lit` (0x014E)). Sous 70 % pendant 30 s en éclairement, le satellite le signale (TM(12,9) et événement S5 0x914C pour A, 0x914D pour B) et ne fait rien d'autre : la charge utile est toujours dans l'état où vous l'avez laissée. Vérifier `eps.pl_payload` (0x0113) : si elle est déjà hors tension, c'est le délestage sur tension bus qui l'a coupée (événement 0x0106) et la situation de puissance est déjà grave
**Action:** Calculer le déficit en pourcentage : (prévu - réel) / prévu x 100 pour chaque générateur
**GO/NO-GO:** Si le déficit dépasse 20 % sur l'un des générateurs pendant une phase éclairée confirmée, continuer. S'il est < 20 %, consigner pour le seul suivi de tendance. -> GO `STEP-2` | NO-GO `STEP-END`

### Étape 2 — Comparer les performances de SA-A et de SA-B
**LABEL:** `STEP-2`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — échantillonner 3 fois à 30 s d'intervalle
**Action:** Calculer le rapport des courants SA-A / SA-B (rapport nominal compris entre 0.9 et 1.1)
**Verify:** `eps.sa_a_current` (0x0103) et `eps.sa_b_current` (0x0104) — déterminer si la dégradation touche un seul générateur ou les deux
**Action:** Si un seul générateur est dégradé, suspecter une défaillance localisée (cellules endommagées, câblage, problème de déploiement). Si les deux sont dégradés proportionnellement, suspecter une erreur d'attitude ou un facteur environnemental.
**GO/NO-GO:** Origine de la dégradation identifiée (un seul générateur ou les deux) — continuer

### Étape 3 — Vérifier que l'attitude n'est pas en cause
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL) ou 3 (COARSE_SUN)
**Verify:** `aocs.att_error` (0x0217) < 2.0° — une erreur d'attitude importante pourrait réduire l'éclairement du générateur
**Action:** Si l'erreur d'attitude dépasse 5°, exécuter d'abord CTG-002, puis réévaluer les performances du générateur
**GO/NO-GO:** Attitude confirmée nominale — la dégradation est intrinsèque au matériel du générateur ou à l'environnement

### Étape 4 — Décider : délester la charge utile ou poursuivre
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.power_gen` (0x0107) — production réelle
**Verify:** `eps.power_cons` (0x0106) — consommation courante
**Action:** Calculer la marge de puissance = production - consommation (doit être > 0 W en moyenne sur l'orbite)
**Action:** Calculer le déficit énergétique d'éclipse dans le cas le plus défavorable avec les valeurs de production dégradées
**Verify:** `eps.bat_soc` (0x0101) — extrapoler le SoC minimal en fin de prochaine éclipse
**Action:** Juger la gravité d'après le rendement (étape 1) et ce bilan de puissance. Une chaîne sous 70 % avec une marge positive en moyenne sur l'orbite est une tendance à suivre ; une chaîne proche de 0 %, deux chaînes basses, ou une marge négative avec la charge utile allumée, c'est grave. La charge utile est la charge qui tranche : poursuivre seulement si le bilan boucle avec la charge utile dans son mode prévu
**Action:** Le directeur de vol annonce la décision sur la boucle (« PAYLOAD SHED » ou « CONTINUE, MONITORING ») et elle est consignée avec le rendement et le SoC extrapolé
**GO/NO-GO:** Si le SoC minimal extrapolé est > 25 % et que la marge moyenne sur l'orbite est positive, poursuivre les opérations nominales sous surveillance. S'il est < 25 % ou si la marge est négative, délester la charge utile à l'étape 5. -> GO `STEP-7` | NO-GO `STEP-5`

### Étape 5 — Réduire les charges pour les adapter au bilan de puissance dégradé
**LABEL:** `STEP-5`
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1) — passer d'IMAGING à STANDBY
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) en 10 s
**Verify:** `eps.power_cons` (0x0106) diminue de >= 12 W
**GO/NO-GO:** Marge toujours insuffisante après le passage en STANDBY -> GO `STEP-5B` | NO-GO `STEP-6`
**LABEL:** `STEP-5B`
**Note:** Uniquement si la marge reste insuffisante après le passage en STANDBY.
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) — arrêt complet de la charge utile
**Note:** Le réchauffeur du lit catalytique du propulseur est `HEATER_THRUSTER` (func 42, argument
`on` uniquement — cette commande n'a pas d'argument `circuit`). Ne l'envoyer que si
aucune manœuvre n'est prévue ; `HEATER_CONTROL` est un alias de HEATER_BATTERY et
aurait commuté le mauvais circuit.
**TC:** `HEATER_THRUSTER(on=0)` (Service 8, Subtype 1, func_id 42) — réchauffeur du lit catalytique sur OFF
**Verify:** `eps.power_cons` (0x0106) — recalculer la marge avec les charges réduites
**GO/NO-GO:** Marge de puissance positive avec au moins 3 W de réserve — continuer

### Étape 6 — Optimiser l'attitude pour l'éclairement du générateur solaire
**LABEL:** `STEP-6`
**TC:** `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) — COARSE_SUN pour une orientation optimale vers le Soleil
**Verify:** `aocs.mode` (0x020F) = 3 en 15 s
**Verify:** `eps.sa_a_current` (0x0103) et `eps.sa_b_current` (0x0104) — constater l'amélioration du courant
**Verify:** `eps.power_gen` (0x0107) augmente par rapport aux valeurs en NOMINAL
**GO/NO-GO:** Production suffisamment améliorée pour maintenir une marge positive — passer à la surveillance

### Étape 7 — Établir un plan de surveillance à long terme
**LABEL:** `STEP-7`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — mesure de référence
**Action:** Consigner le courant SA-A, le courant SA-B, la production de puissance et le SoC comme nouvelle référence
**Action:** Programmer une comparaison quotidienne de la tendance du courant du générateur avec la prévision sur les 7 jours suivants
**Action:** Se coordonner avec la planification de mission pour adapter le programme de prise de vue au bilan de puissance dégradé
**Action:** Si la défaillance d'une aile est confirmée, évaluer l'exploitation avec une surface solaire réduite (~42 W en crête avec une seule aile, ~32 W avec les seuls panneaux de structure). Contrôler l'état de déploiement des ailes :
**TC:** `GET_PARAM(param_id=0x0144)` (Service 20, Subtype 3) — `eps.wing_status`
(0x0144 figure désormais aussi dans la HK SID 1 ; un SID 1 activé le transporte donc déjà).
**GO/NO-GO:** Plan de surveillance établi et plan d'opérations adapté — reprise terminée

## Conduite à tenir hors nominal
**LABEL:** `STEP-END`
- Si les courants des deux générateurs descendent sous 0.2 A en phase éclairée : suspecter une défaillance totale du générateur ou une erreur d'attitude grave — exécuter immédiatement CTG-005 (mode survie EPS)
- Si le SoC descend sous 20 % pendant cette procédure : l'interrompre et exécuter CTG-005
- Si l'erreur d'attitude est la cause première : exécuter CTG-002, puis relancer cette procédure depuis son début (étape 1)
- Si la dégradation est progressive (> 5 % par jour) : revoir à la hausse les priorités de transmission au sol des données de mission et planifier un profil de mission à puissance réduite

## Postconditions
- [ ] Dégradation du générateur quantifiée (déficit en pourcentage documenté pour chaque générateur)
- [ ] Bilan de puissance recalculé avec les valeurs dégradées et confirmé positif
- [ ] Plan d'opérations adapté (fréquence des prises de vue, utilisation des réchauffeurs, mode SCAO)
- [ ] Suivi de tendance lancé, avec compte rendu quotidien au directeur de mission
- [ ] Hypothèse de cause première documentée (dégradation des cellules, déploiement, câblage, rayonnement)
