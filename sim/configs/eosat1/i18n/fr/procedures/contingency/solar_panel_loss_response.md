# CTG-024 : Traitement de la perte d'un panneau solaire
**Sous-système :** EPS
**Phase :** CONTINGENCY
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Traiter la perte ou la dégradation importante d'un ou de plusieurs panneaux solaires montés sur
la structure. EOSAT-1 dispose de six panneaux solaires, un sur chaque face de la structure du satellite (+X, -X,
+Y, -Y, +Z, -Z). La défaillance d'un panneau réduit la capacité totale de production de puissance et
peut créer un profil de puissance dissymétrique selon l'attitude du satellite. Cette
procédure guide l'opérateur dans la détection, l'identification, le recalcul du bilan
de puissance et les ajustements opérationnels nécessaires pour préserver la viabilité de la mission avec
une production de puissance réduite.

## Prérequis
- [ ] La télémesure EPS (SID 1) est reçue à >= 0.5 Hz
- [ ] Le satellite est en phase éclairée — `eps.eclipse_flag` (0x0108) = 0
- [ ] Le SCAO est en NOMINAL ou dans un mode d'attitude connu — `aocs.mode` (0x020F) connu
- [ ] L'attitude courante est nominale — `aocs.att_error` (0x0217) < 2.0°
- [ ] Les valeurs de référence du courant de chaque panneau sont disponibles pour l'attitude et l'éclairement courants

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| eps.sa_px_current | 0x012B | Courant du panneau, face +X |
| eps.sa_mx_current | 0x012C | Courant du panneau, face -X |
| eps.sa_py_current | 0x012D | Courant du panneau, face +Y |
| eps.sa_my_current | 0x012E | Courant du panneau, face -Y |
| eps.sa_pz_current | 0x012F | Courant du panneau, face +Z |
| eps.sa_mz_current | 0x0130 | Courant du panneau, face -Z |
| eps.sa_a_current | 0x0103 | Courant total du générateur solaire A |
| eps.sa_b_current | 0x0104 | Courant total du générateur solaire B |
| eps.power_gen | 0x0107 | Production totale de puissance |
| eps.power_cons | 0x0106 | Consommation totale de puissance |
| eps.bat_soc | 0x0101 | État de charge de la batterie |
| eps.bus_voltage | 0x0105 | Tension du bus principal |
| eps.eclipse_flag | 0x0108 | Indicateur d'éclipse (doit valoir 0 pour une évaluation valide) |
| aocs.mode | 0x020F | Mode courant du SCAO |
| aocs.att_error | 0x0217 | Erreur d'attitude |

## Télécommandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| PAYLOAD_SET_MODE | 8 | 1 | 26 | Régler le mode de la charge utile |
| FPA_COOLER | 8 | 1 | 43 | Commander le refroidisseur du FPA |
| AOCS_SET_MODE | 8 | 1 | 0 | Régler le mode SCAO |

## Déroulement

### Étape 1 : Détecter et confirmer l'anomalie de production de puissance
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander la télémesure de servitude EPS
**Verify:** `eps.power_gen` (0x0107) — comparer à la valeur attendue pour l'attitude et l'éclairement
courants. Si le déficit dépasse 15 %, poursuivre l'investigation.
**Verify:** `eps.eclipse_flag` (0x0108) = 0 — confirmer que le satellite est en phase éclairée.
En éclipse, attendre la phase éclairée avant d'évaluer les performances des panneaux.
**Verify:** `eps.sa_a_current` (0x0103) — consigner le courant total du générateur A
**Verify:** `eps.sa_b_current` (0x0104) — consigner le courant total du générateur B
**Action:** Si la production totale est inférieure à la valeur attendue, passer à l'analyse panneau par panneau.
**GO/NO-GO:** Déficit de production confirmé en phase éclairée — continuer.

### Étape 2 : Identifier le ou les panneaux concernés par l'analyse du courant de chaque panneau
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander la télémesure de servitude EPS
Échantillonner 3 fois à 30 s d'intervalle pour confirmer la tendance.
**Verify:** `eps.sa_px_current` (0x012B) — courant de la face +X
**Verify:** `eps.sa_mx_current` (0x012C) — courant de la face -X
**Verify:** `eps.sa_py_current` (0x012D) — courant de la face +Y
**Verify:** `eps.sa_my_current` (0x012E) — courant de la face -Y
**Verify:** `eps.sa_pz_current` (0x012F) — courant de la face +Z
**Verify:** `eps.sa_mz_current` (0x0130) — courant de la face -Z
**Action:** Comparer le courant de chaque panneau à la valeur attendue pour l'angle d'éclairement
de sa face. Un panneau qui produit nettement moins de courant (< 50 % de la valeur attendue)
ou un courant nul est considéré comme dégradé ou défaillant.
**Action:** Documenter le ou les panneaux concernés et le degré de dégradation :
- dégradation partielle : produit du courant, mais < 50 % de la valeur attendue ;
- perte totale : produit 0 A bien qu'éclairé.
**Note:** Les panneaux des faces non éclairées (faces à l'ombre dans l'attitude
courante) affichent naturellement ~0 A et ne doivent pas être signalés.
**GO/NO-GO:** Panneau(x) concerné(s) identifié(s) — passer à l'évaluation de l'impact.

### Étape 3 : Écarter une erreur d'attitude comme cause première
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander la télémesure de servitude AOCS
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL) ou 3 (COARSE_SUN)
**Verify:** `aocs.att_error` (0x0217) < 2.0° — confirme que l'attitude est nominale
**Action:** Si `aocs.att_error` > 5.0°, le déficit de puissance peut provenir d'un
mauvais éclairement du générateur solaire dû à l'erreur d'attitude. Exécuter d'abord CTG-002 (reprise après anomalie
SCAO), puis relancer cette procédure depuis son début (étape 1).
**Verify:** `aocs.rate_roll` (0x0204) < 0.1°/s — aucune rotation inattendue
**Verify:** `aocs.rate_pitch` (0x0205) < 0.1°/s
**Verify:** `aocs.rate_yaw` (0x0206) < 0.1°/s
**GO/NO-GO:** Attitude confirmée nominale. La dégradation est intrinsèque au matériel du panneau
— passer au recalcul du bilan de puissance.

### Étape 4 : Recalculer le bilan de puissance avec la production dégradée
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander la télémesure de servitude EPS
**Verify:** `eps.power_gen` (0x0107) — production dégradée réelle (phase éclairée)
**Verify:** `eps.power_cons` (0x0106) — consommation totale courante
**Action:** Calculer la marge de puissance instantanée = production - consommation.
**Action:** Calculer le bilan de puissance moyenné sur l'orbite :
- marge de puissance en phase éclairée x fraction éclairée de l'orbite ;
- consommation en éclipse x fraction d'éclipse de l'orbite ;
- le solde doit être positif pour des opérations durables.
**Action:** Extrapoler le SoC minimal de la batterie en fin de prochaine éclipse avec les valeurs dégradées.
**Verify:** `eps.bat_soc` (0x0101) — consigner la valeur courante comme référence.
**GO/NO-GO:** Si le bilan de puissance moyenné sur l'orbite est positif et le SoC minimal extrapolé > 25 %, poursuivre les opérations nominales sous surveillance. S'il est négatif ou si le SoC extrapolé est < 25 %, l'étape 5 s'applique. -> GO `STEP-7` | NO-GO `STEP-5`

### Étape 5 : Délester des charges pour les adapter au bilan de puissance réduit
**LABEL:** `STEP-5`
**Action:** Annoncer « Solar panel degradation confirmed — reducing power consumption
to match available generation » sur la boucle opérations.

**Étape 5a — Ramener la charge utile en STANDBY :**
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) — passer d'IMAGING à STANDBY
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) en 10 s
**Verify:** `eps.power_cons` (0x0106) diminue de >= 12 W
**GO/NO-GO:** Marge toujours insuffisante après le passage en STANDBY -> GO `STEP-5B` | NO-GO `STEP-5D`

**Étape 5b — Si la marge reste insuffisante, désactiver le refroidisseur du FPA :**
**LABEL:** `STEP-5B`
**TC:** `FPA_COOLER(on=0)` (Service 8, Subtype 1, func_id 43)
**TC:** `GET_PARAM(param_id=0x040C)` (Service 20, Subtype 3) — `tcs.cooler_fpa` : le SID 3 n'est périodique que toutes les 60 s : lire la valeur que ce contrôle utilise
**Verify:** `tcs.cooler_fpa` (0x040C) = 0 en 5 s
**Verify:** `eps.power_cons` (0x0106) diminue d'environ 15 W
**GO/NO-GO:** Marge toujours insuffisante avec le refroidisseur du FPA arrêté -> GO `STEP-5C` | NO-GO `STEP-5D`

**Étape 5c — Si la marge reste insuffisante, arrêter complètement la charge utile :**
**LABEL:** `STEP-5C`
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) — charge utile entièrement sur OFF
**Verify:** `payload.mode` (0x0600) = 0 (OFF) en 10 s

**LABEL:** `STEP-5D`
**Action:** Recalculer le bilan de puissance moyenné sur l'orbite avec les charges réduites.
**Verify:** `eps.power_cons` (0x0106) — confirmer que la marge est positive.
**GO/NO-GO:** Bilan de puissance positif avec au moins 3 W de réserve — continuer.

### Étape 6 : Envisager une optimisation de l'attitude pour récupérer de la puissance
**Action:** Si le ou les panneaux dégradés sont sur une face qui reçoit l'éclairement maximal
en mode NOMINAL, envisager de passer temporairement en COARSE_SUN (orientation optimale vers le Soleil) pour
maximiser la production des panneaux intacts.
**GO/NO-GO:** Panneau(x) dégradé(s) sur la face éclairée en NOMINAL — essayer COARSE_SUN -> GO `STEP-6B` | NO-GO `STEP-7`
**LABEL:** `STEP-6B`
**TC:** `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) — COARSE_SUN
**Verify:** `aocs.mode` (0x020F) = 3 en 15 s
**Action:** Attendre 120 s la stabilisation de la nouvelle attitude, puis demander la HK EPS.
**Verify:** `eps.power_gen` (0x0107) — comparer à la production en NOMINAL.
**Note:** COARSE_SUN sacrifie le pointage nadir (pas de prise de vue) mais peut améliorer
la production de puissance jusqu'à 30 % selon le ou les panneaux perdus.
**GO/NO-GO:** Si COARSE_SUN offre une marge de puissance nettement meilleure, conserver
ce mode jusqu'à ce que la batterie soit suffisamment chargée. Faute d'amélioration, revenir en
NOMINAL : `AOCS_SET_MODE(mode=4)`.

### Étape 7 : Établir le plan de surveillance à long terme et le plan d'opérations
**LABEL:** `STEP-7`
**Action:** Consigner les éléments suivants comme nouvelle référence dégradée :
- courants de chaque panneau (0x012B-0x0130) pour chaque face éclairée ;
- production totale de puissance en modes NOMINAL et COARSE_SUN ;
- bilan de puissance moyenné sur l'orbite avec les opérations réduites.
**Action:** Programmer un suivi de tendance quotidien — vérifier si la dégradation est progressive
(aggravation) ou stable.
**Action:** Se coordonner avec la planification de mission pour :
- adapter le programme de prise de vue au bilan de puissance dégradé ;
- ne planifier les prises de vue que pendant les phases d'orbite offrant le meilleur éclairement des panneaux restants ;
- envisager un fonctionnement par intermittence de la charge utile (prise de vue sur une orbite, recharge sur la suivante).
**Action:** Évaluer l'exploitation à puissance réduite :
- perte d'un panneau (~15 % de capacité en moins) : rapport cyclique de prise de vue réduit ;
- perte de deux panneaux (~30 % en moins) : prises de vue uniquement pendant l'éclairement optimal ;
- perte de trois panneaux ou plus : dégradation de la mission — envisager une exploitation en mode survie uniquement.
**GO/NO-GO:** Plan de surveillance établi et plan d'opérations adapté — procédure
terminée.

## Critères de vérification
**LABEL:** `STEP-END`
- [ ] Panneau(x) concerné(s) identifié(s) par face et niveau de dégradation documenté
- [ ] Erreur d'attitude écartée comme cause première
- [ ] Bilan de puissance recalculé avec la production dégradée — confirmé positif
- [ ] Plan d'opérations adapté à l'enveloppe de puissance disponible
- [ ] Suivi de tendance quotidien lancé
- [ ] `eps.bat_soc` (0x0101) > 25 % et stable ou en hausse
- [ ] `eps.bus_voltage` (0x0105) > 30.9 V

## Conduite à tenir hors nominal
- Si tous les panneaux du côté exposé au Soleil sont perdus : passer immédiatement en COARSE_SUN.
  Si la production totale est < 15 W, commander `OBC_SET_MODE(mode=2)` pour passer en EMERGENCY. Il s'agit
  d'une anomalie critique pour la mission — faire remonter l'anomalie immédiatement.
- Si la dégradation est progressive (> 5 % par jour) : suspecter des dommages dus au rayonnement, une défaillance
  par cyclage thermique ou une dégradation du câblage. Accélérer la transmission au sol des données de mission et
  préparer la contingence de fin de mission.
- Si `eps.bat_soc` descend sous 20 % pendant l'investigation : interrompre cette procédure
  et exécuter CTG-001 (délestage sur sous-tension) ou CTG-023 (délestage progressif).
- Si l'erreur d'attitude était la cause et persiste : le déficit du générateur solaire est un
  symptôme, pas la cause première. Se concentrer d'abord sur la reprise du SCAO.
- Si la télémesure par panneau est incohérente (p. ex. une face éclairée indique 0 A alors que
  le total du générateur est nominal) : suspecter une défaillance du capteur de télémesure plutôt qu'une défaillance
  du panneau. Recouper avec les courants totaux des générateurs (0x0103, 0x0104).
