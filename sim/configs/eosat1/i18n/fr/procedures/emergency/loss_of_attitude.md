# EMG-005 : Perte d'attitude
**Sous-système :** AOCS
**Phase :** EMERGENCY
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Procédure de reprise d'EOSAT-1 lorsque le satellite est en culbutage avec des vitesses angulaires supérieures à
2 deg/s sur un axe quelconque. Cette procédure commande une séquence maîtrisée d'amortissement des vitesses angulaires, déleste les charges
non essentielles pour préserver la puissance face à une géométrie solaire potentiellement défavorable, et rétablit une attitude sûre
de pointage solaire. Contrainte critique : l'attitude doit être stabilisée avant l'épuisement de la batterie pendant les
éclipses (~36 min d'éclipse au maximum, SoC minimal de survie = 10 %).

## Prérequis
- [ ] La télémesure confirme `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205) ou `aocs.rate_yaw` (0x0206) > 2.0 deg/s
- [ ] Liaison de communication active --- `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] `eps.bat_soc` (0x0101) actuel > 20 % (en dessous de 20 %, exécuter EMG-002 en parallèle)
- [ ] Télémesure d'ingénierie AOCS activée (SID 2)
- [ ] Équipe de dynamique du vol à la console avec estimation d'attitude en temps réel

## Déroulement

### Étape 1 --- Délestage immédiat
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) --- charge utile OFF.
**TC:** `HEATER_OBC(on=0)` (Service 8, Subtype 1, func_id 41) --- réchauffeur de l'OBC sur OFF (seule charge de réchauffage non critique ; le réchauffeur de la batterie reste sous thermostat).
**Verify:** `payload.mode` (0x0600) = OFF sous 5 s.
**Verify:** `eps.power_cons` (0x0106) diminue de >= 15 W sous 10 s.
**Justification :** Réduire la consommation pour prolonger l'autonomie de la batterie pendant le culbutage, lorsque la production
du générateur solaire peut être fortement dégradée par une orientation défavorable.
**GO/NO-GO:** Consommation < 60 W confirmée avant de continuer.

### Étape 2 --- Commander le mode d'amortissement
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0) --- mode DETUMBLE.
**Verify:** `aocs.mode` (0x020F) = DETUMBLE (2) sous 5 s.
**Verify:** activation des magnétocoupleurs confirmée par la télémesure AOCS.
**Surveiller :** `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) ---
les vitesses doivent commencer à baisser dans les 2--3 minutes.
**GO/NO-GO:** Mode AOCS confirmé en DETUMBLE et au moins un axe de magnétocoupleur actif.

### Étape 3 --- Évaluer l'état des roues de réaction
**Surveiller :** `aocs.rw1_speed` (0x0207), `aocs.rw2_speed` (0x0208), `aocs.rw3_speed` (0x0209),
`aocs.rw4_speed` (0x020A).
**Verify:** au moins 3 roues sur 4 répondent, avec des vitesses dans les limites opérationnelles (< 6000 tr/min).
**Action:** Si une roue indique une vitesse > 6000 tr/min ou ne répond pas, noter l'identifiant de la roue pour une analyse
ultérieure. Le mode d'amortissement n'utilise que les magnétocoupleurs et n'a pas besoin des roues.
**GO/NO-GO:** Amortissement par magnétocoupleurs confirmé actif, quel que soit l'état des roues.

### Étape 4 --- Surveiller la réduction des vitesses (orbite 1)
**Durée :** Surveiller pendant 1 orbite complète (~95 minutes).
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- demander les HK AOCS toutes les 30 s pendant le passage.
**Attendu :** Les vitesses angulaires doivent diminuer d'environ 50 % par orbite sous la loi B-dot.
**Verify:** vitesses sur tous les axes < 1.0 deg/s à la fin de la première orbite.
**Critique :** Suivre `eps.bat_soc` (0x0101) tout du long --- si le SoC descend sous 15 % à un moment quelconque,
exécuter immédiatement l'étape 1 d'EMG-002 (délestage à la charge minimale de survie).
**GO/NO-GO:** Vitesses en baisse sur les trois axes.

### Étape 5 --- Surveiller la réduction des vitesses (orbite 2)
**Durée :** Poursuivre la surveillance pendant la deuxième orbite.
**Attendu :** Vitesses sur tous les axes < 0.5 deg/s.
**Verify:** `eps.bat_soc` (0x0101) stable ou en hausse pendant la phase éclairée.
**Verify:** `eps.power_gen` (0x0107) remontant à mesure que le culbutage ralentit (meilleur éclairement du générateur solaire).
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- évaluation EPS complète.
**GO/NO-GO:** Toutes les vitesses < 0.5 deg/s ET `eps.bat_soc` (0x0101) > 15 %.

### Étape 6 --- Confirmer la fin de l'amortissement
**Verify:** `aocs.rate_roll` (0x0204) < 0.1 deg/s.
**Verify:** `aocs.rate_pitch` (0x0205) < 0.1 deg/s.
**Verify:** `aocs.rate_yaw` (0x0206) < 0.1 deg/s.
**Durée :** Toutes les vitesses doivent rester sous 0.1 deg/s pendant au moins 10 minutes consécutives.
**GO/NO-GO:** État amorti stable confirmé. Si les vitesses oscillent au-dessus du seuil,
poursuivre l'amortissement pendant une orbite supplémentaire avant de continuer.

### Étape 7 --- Commander le pointage solaire sûr
**TC:** `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) --- COARSE_SUN (acquisition du Soleil).
**Verify:** `aocs.mode` (0x020F) = COARSE_SUN (3) sous 5 s.
**Verify:** `aocs.att_error` (0x0217) décroissant vers 0 deg sous 10 minutes.
**Surveiller :** Vitesses des roues de réaction --- s'attendre à une montée en vitesse pendant que les roues acquièrent l'attitude de pointage solaire.
**Verify:** `eps.power_gen` (0x0107) en hausse à mesure que les générateurs solaires sont éclairés par le Soleil.
**GO/NO-GO:** `aocs.att_error` (0x0217) < 5.0 deg sous 15 minutes.

### Étape 8 --- Vérifier que le bilan de puissance est positif
**Verify:** `eps.power_gen` (0x0107) > `eps.power_cons` (0x0106) (bilan positif).
**Verify:** `eps.bat_soc` (0x0101) en tendance à la hausse.
**Verify:** `eps.sa_a_current` (0x0103) et `eps.sa_b_current` (0x0104) tous deux > 0.5 A (les deux générateurs éclairés).
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- confirmer l'état complet de l'EPS.
**Durée :** Maintenir COARSE_SUN pendant au moins 2 orbites avant toute action de rétablissement.
**GO/NO-GO:** Bilan de puissance positif confirmé. Enchaîner sur EMG-001 pour le rétablissement par étapes jusqu'au nominal.

## Contraintes de temps
| Condition | Seuil | Action |
|---|---|---|
| SoC de la batterie pendant le culbutage | < 15 % | Exécuter EMG-002 en parallèle |
| Entrée en éclipse avec des vitesses > 1 deg/s | ~36 min avant épuisement | Priorité : réduire les vitesses avant l'éclipse |
| Amortissement qui ne converge pas (vitesses constantes après 2 orbites) | ~190 min | Rechercher une panne de magnétocoupleur, envisager un secours par les roues |
| Délai d'acquisition du Soleil dépassé | > 20 min avec att_error > 10 deg | Commander de nouveau COARSE_SUN, vérifier les données du senseur solaire |

## Conduite à tenir hors nominal
- Si les magnétocoupleurs ne répondent pas : tenter une réduction des vitesses par les roues en commandant les vitesses individuelles des roues par forçage direct de l'AOCS. Exige un spécialiste de la dynamique du vol.
- Si les vitesses augmentent au lieu de diminuer : erreur possible du modèle de champ magnétique ou inversion de polarité d'un magnétocoupleur. Commander AOCS OFF, attendre une orbite, retenter l'amortissement.
- Si seules 2 roues sur 4 sont opérationnelles après l'amortissement : rester en COARSE_SUN avec le jeu de roues réduit. NE PAS tenter NOMINAL tant que l'anomalie des roues n'est pas résolue.
- Si la puissance descend sous 10 % pendant l'amortissement : la préservation de la batterie est prioritaire. Commander `OBC_SET_MODE(mode=2)` pour entrer en mode d'urgence, ce qui coupe toutes les charges non nécessaires à la survie.
- Si l'attitude oscille en COARSE_SUN : rechercher un propulseur bloqué ou une roue déséquilibrée. Revenir en DETUMBLE, analyser les données des capteurs.

## Postconditions
- [ ] Toutes les vitesses angulaires < 0.1 deg/s maintenues pendant >= 10 minutes
- [ ] `aocs.mode` (0x020F) = COARSE_SUN (3) et `aocs.att_error` (0x0217) < 5.0 deg
- [ ] Bilan de puissance du satellite positif : `eps.power_gen` (0x0107) > `eps.power_cons` (0x0106)
- [ ] `eps.bat_soc` (0x0101) > 20 % et en tendance à la hausse
- [ ] État des roues de réaction évalué --- au moins 3 sur 4 opérationnelles
- [ ] Cause racine de la perte d'attitude en cours d'analyse
- [ ] Transition vers EMG-001 pour le rétablissement par étapes vers les opérations nominales
