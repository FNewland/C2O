# LEOP-004 : Vérification du générateur solaire
**Sous-système :** EPS / structure
**Phase :** LEOP
**Révision :** 2.1 --- refonte du déroulement 2026-08c (états d'entrée et de sortie, chaînage des procédures suivantes)
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de LEOP-002 --- plateforme saine sur la télémesure de référence,
panneaux REPLIÉS (`eps.wing_status` 0x0144 = 0), lignes AOCS/charge utile/réchauffeurs/propulsion
sur OFF, satellite en rotation lente aux vitesses de séparation.

## Objet
Déployer les panneaux solaires +Y et -Y et vérifier que les générateurs solaires montés sur la structure (SA-A
et SA-B) sont opérationnels après la séparation du lanceur. Confirmer le déploiement des panneaux
par la télémesure, mesurer les courants de chaque chaîne et valider la production électrique totale
par rapport aux prédictions pour l'angle solaire et la position orbitale actuels. Le satellite dispose de
0,30 m² de surface de panneaux montés sur la structure (configuration repliée), portée à 0,78 m² après le déploiement des panneaux
(0,24 m² par panneau sur les faces +Y et -Y).

## Prérequis
- [ ] LEOP-001 (Première acquisition) terminée avec succès
- [ ] LEOP-002 (Bilan de santé initial) terminée — tous les sous-systèmes nominaux
- [ ] Liaison bidirectionnelle en bande S active avec une marge de liaison > 3 dB
- [ ] Satellite dans la partie éclairée de l'orbite (de préférence) ou à l'approche de la sortie d'éclipse
- [ ] Télémesure EPS confirmée disponible (SID 1 répond)
- [ ] La dynamique du vol a fourni l'angle bêta et le vecteur Soleil actuels
- [ ] Vitesses angulaires dans la spécification de séparation du lanceur selon le rapport de séparation.
      REMARQUE : l'AOCS n'est PAS encore alimenté dans ce déroulement --- il n'y a aucune télémesure de vitesse
      à lire. Le déploiement est qualifié pour les vitesses de séparation ; l'amortissement actif
      suit dans LEOP-007/LEOP-005.
- [ ] SoC de la batterie > 50 % (le déploiement consomme ~2 A pendant 30 s par panneau)

## Déroulement

### Étape 0 — Commander le déploiement des panneaux
**TC:** `EPS_DEPLOY_WING(wing=2)` (Service 8, Subtype 1) — déployer les deux panneaux
**Verify:** `eps.wing_status` (0x0144) bit 0x10 ou 0x20 positionné (déploiement en cours) sous 5s
**Action:** Attendre 30 secondes pour la libération par fil chaud et le déploiement par ressort
**Verify:** `eps.wing_status` (0x0144) = 0x03 (les deux panneaux déployés) sous 45s
**GO/NO-GO:** Déploiement des deux panneaux confirmé. Si un seul s'est déployé, tenter une nouvelle commande sur ce seul panneau (voir Conduite à tenir hors nominal).

### Étape 1 — Demander la télémesure EPS détaillée
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.bus_voltage` (0x0105) dans la plage [27.0V, 29.5V] sous 10s
**Verify:** `eps.bat_soc` (0x0101) rapporté sous 10s
**GO/NO-GO:** Télémesure EPS reçue normalement

### Étape 2 — Contrôler l'état de déploiement et le courant du panneau +Y
**TC:** `GET_PARAM(param_id=0x0144)` (Service 20, Subtype 3) — masque de bits de déploiement `eps.wing_status`
**Verify:** `eps.wing_status` (0x0144) bit 0 positionné (0x01, panneau +Y DÉPLOYÉ) sous 10s
**TC:** `GET_PARAM(param_id=0x0146)` (Service 20, Subtype 3) — `eps.sa_wing_py_current`
**Verify:** `eps.sa_wing_py_current` (0x0146) > 0.1A au Soleil sous 10s
**Note:** 0x0144 est l'unique source de vérité du déploiement (bit0=+Y déployé, bit1=-Y déployé,
bit4/bit5 = déploiement en cours). 0x0110-0x0113 sont les indicateurs d'état des LIGNES d'alimentation du PDM
(`eps.pl_obc` / `eps.pl_ttc_rx` / `eps.pl_ttc_tx` / `eps.pl_payload`) et n'indiquent rien sur le
déploiement des panneaux.
**GO/NO-GO:** Panneau +Y confirmé déployé et produisant du courant

### Étape 3 — Contrôler l'état de déploiement et le courant du panneau -Y
**TC:** `GET_PARAM(param_id=0x0144)` (Service 20, Subtype 3) — masque de bits de déploiement `eps.wing_status`
**Verify:** `eps.wing_status` (0x0144) bit 1 positionné (0x02, panneau -Y DÉPLOYÉ) sous 10s
**TC:** `GET_PARAM(param_id=0x0147)` (Service 20, Subtype 3) — `eps.sa_wing_my_current`
**Verify:** `eps.sa_wing_my_current` (0x0147) > 0.1A au Soleil sous 10s
**GO/NO-GO:** Panneau -Y confirmé déployé et produisant du courant

### Étape 4 — Mesurer la production électrique totale
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.power_gen` (0x0107) > 20W (minimum en rotation avec éclairement partiel) sous 10s
**Action:** Consigner la valeur exacte de la production électrique. La comparer à la prédiction de la dynamique du vol fondée sur l'attitude et l'angle solaire actuels.
**GO/NO-GO:** Production électrique cohérente avec le déploiement des deux générateurs

### Étape 5 — Surveiller la puissance pendant la transition d'éclipse (le cas échéant)
**Action:** Si le passage couvre une entrée ou une sortie d'éclipse, surveiller l'évolution de la production électrique.
**Verify:** `eps.power_gen` (0x0107) chute à ~0W pendant l'éclipse, sous 30s après l'entrée prédite
**Verify:** `eps.power_gen` (0x0107) remonte à >20W sous 60s après la sortie d'éclipse prédite
**Verify:** `eps.bat_soc` (0x0101) en baisse pendant l'éclipse à un rythme cohérent avec la charge
**GO/NO-GO:** Profil de puissance en éclipse cohérent avec un fonctionnement nominal du générateur

### Étape 6 — Vérifier la symétrie des panneaux
**Action:** Comparer les courants des panneaux +Y et -Y. Les deux panneaux doivent produire un courant similaire à angles solaires équivalents, à 15 % près l'un de l'autre.
**TC:** `GET_PARAM(param_id=0x0146)` (Service 20, Subtype 3) — `eps.sa_wing_py_current`
**TC:** `GET_PARAM(param_id=0x0147)` (Service 20, Subtype 3) — `eps.sa_wing_my_current`
**Verify:** |0x0146 - 0x0147| / max(0x0146, 0x0147) < 0.15 sous 10s
**Note:** Les courants des générateurs montés sur la structure sont `eps.sa_a_current` (0x0103) et `eps.sa_b_current`
(0x0104) ; les courants par panneau ci-dessus excluent les faces de la structure.
**GO/NO-GO:** Courants des panneaux équilibrés à 15 % près

### Étape 7 — Estimer la marge du bilan de puissance
**Action:** Calculer la consommation électrique actuelle à partir de la tension du bus et du courant de charge. La comparer à la production électrique. Vérifier un bilan énergétique positif sur une orbite (en pointage solaire).
**Verify:** `eps.power_gen` (0x0107) > 50W attendue en pointage solaire (après LEOP-005)
**Action:** Consigner l'estimation du bilan de puissance dans le journal LEOP. Confirmer une marge suffisante pour les activités de recette en orbite.
**GO/NO-GO:** Bilan de puissance positif confirmé ou atteignable après l'acquisition du Soleil

## Conduite à tenir hors nominal
- Si un panneau ne se déploie pas (bit de wing_status non positionné après 45s) : renvoyer la commande pour ce seul panneau avec `EPS_DEPLOY_WING(wing=0)` pour +Y ou `EPS_DEPLOY_WING(wing=1)` pour -Y — accord du directeur de vol requis. En cas de nouvel échec, évaluer la viabilité du bilan de puissance avec un seul panneau (un panneau fournit ~32W au Soleil, marginal pour les opérations nominales).
- Si les deux générateurs sont déployés mais que la production est < 10W au Soleil : vérifier auprès de la dynamique du vol que le satellite est réellement au Soleil. Rechercher une vitesse de rotation excessive réduisant l'incidence solaire effective. Donner la priorité à LEOP-005 (Acquisition du Soleil) pour stabiliser l'attitude.
- Si l'asymétrie des courants des panneaux dépasse 30 % : consigner une anomalie. Un panneau est peut-être partiellement déployé ou une chaîne est défaillante. Poursuivre la LEOP avec un bilan de puissance réduit. Programmer une investigation détaillée de l'EPS pendant la recette en orbite.
- Si `eps.bat_soc` chute rapidement (> 2 % par minute) : réduire la charge du satellite. Ne pas compter sur le réchauffeur du lit catalytique du propulseur : il est déjà sur OFF en LEOP (mode manuel par défaut), donc `HEATER_THRUSTER(on=0)` n'économise rien. S'assurer que l'amortissement AOCS n'utilise que les magnétocoupleurs (consommation plus faible). Donner la priorité à l'acquisition du Soleil.

## État de sortie
- Les deux panneaux DÉPLOYÉS (`eps.wing_status` 0x0144 = 0x03) et produisant de l'énergie ; la totalité
  des 0,78 m² de surface de générateur disponible
- Aucun autre état modifié : lignes AOCS/charge utile/réchauffeurs/propulsion toujours sur OFF

## Postconditions
- [ ] Déploiement du panneau +Y confirmé par `eps.wing_status` (0x0144) bit 0 et `eps.sa_wing_py_current` (0x0146)
- [ ] Déploiement du panneau -Y confirmé par `eps.wing_status` (0x0144) bit 1 et `eps.sa_wing_my_current` (0x0147)
- [ ] Production électrique totale mesurée et consignée (augmentation attendue avec les panneaux)
- [ ] Symétrie des panneaux vérifiée à 15 % près
- [ ] Évaluation du bilan de puissance terminée (0,78 m² de surface déployée)
- [ ] Rapport de vérification du générateur solaire et du déploiement des panneaux diffusé

**PROCÉDURE SUIVANTE :** LEOP-007 (Mise sous tension séquentielle) --- l'ensemble AOCS y est alimenté,
puis LEOP-005 observe l'acquisition du Soleil.
