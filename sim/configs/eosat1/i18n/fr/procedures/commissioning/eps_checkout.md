# COM-001 : Vérification de l'EPS
**Sous-système :** EPS
**Phase :** COMMISSIONING
**Révision :** 2.0 --- 2026-08c : états d'entrée et de sortie ; l'essai de transitoire de charge
n'emprunte plus la charge utile (sa ligne reste sur OFF jusqu'à COM-009 --- l'ancienne étape 7
commandait un mode charge utile sur une ligne non alimentée et le mode revenait silencieusement en arrière) ;
codages d'OBC_SET_MODE corrigés (0=NOMINAL, 1=SAFE).
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de LEOP-003 --- phase de mission 5, maintien solaire COARSE_SUN,
roues désactivées, lignes charge utile/refroidisseur/réchauffeurs (sauf si LEOP-007 en a alimenté un)/propulsion
sur OFF, liaison descendante en LOW, SID 1/2/3/4/6/11/12 activés.

## Objet
Effectuer une vérification complète du sous-système d'alimentation électrique. Vérifier la régulation de la
tension du bus, l'état de santé de la batterie et ses caractéristiques de charge et de décharge, les performances du générateur solaire
sous différents angles solaires et le bilan de puissance global. Établir les valeurs de performance de référence
pour l'exploitation de la mission.

## Prérequis
- [ ] LEOP terminée --- `eps.spacecraft_phase` (0x0129) = 5
- [ ] Satellite en maintien solaire COARSE_SUN (`aocs.mode` 0x020F = 3 --- toujours
      valable ici : aucun senseur stellaire n'est alimenté avant COM-003, le maintien n'a donc
      aucun critère de promotion automatique)
- [ ] Au moins 2 orbites complètes de télémesure continue archivées depuis la fin de la LEOP
- [ ] Liaison bidirectionnelle en bande S active avec une marge de liaison > 3 dB
- [ ] SOC de la batterie > 70 % au début de la procédure
- [ ] Aucune anomalie active sur le sous-système EPS

## Déroulement

### Étape 1 — Mesure de référence de la tension du bus
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.bus_voltage` (0x0105) dans la plage [28.4V, 34.0V] sous 10s (la bande jaune de la console ; le bus suit la batterie, donc une batterie pleine se situe vers 33.4 V)
**Action:** Consigner la tension du bus. Le bus n'est pas régulé : il suit la batterie jusqu'au plafond de 33.4V.
**GO/NO-GO:** Tension du bus régulée conformément à la spécification

### Étape 2 — Tension et état de charge de la batterie
**TC:** `GET_PARAM(param_id=0x0100)` (Service 20, Subtype 3) — tension de la batterie
**TC:** `GET_PARAM(param_id=0x0101)` (Service 20, Subtype 3) — SOC de la batterie
**Verify:** `eps.bat_voltage` (0x0100) dans la plage [24.0V, 33.6V] sous 10s
**Verify:** `eps.bat_soc` (0x0101) > 70 % sous 10s
**Action:** Consigner les valeurs. La plage de tension de la batterie Li-ion 8S (GomSpace BPX 8S-1P, 100 Wh, 3,5 Ah) va de 24,0 V (vide) à 33,6 V (pleine), tension nominale 28,8 V.
**GO/NO-GO:** Tension et SOC de la batterie dans la plage nominale

### Étape 3 — Performances du générateur solaire au Soleil
**Action:** Effectuer cette étape pendant la phase éclairée de l'orbite, avec un pointage solaire stable.
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.power_gen` (0x0107) dans la plage [40W, 90W] sous 10s (88.6 W est le pic de l'ensemble du satellite dans `subsystems/eps.yaml` ; ~80 W est normal en pointage solaire)
**Action:** Consigner la production électrique. Valeur crête attendue ~64 W à l'angle solaire optimal avec les panneaux déployés (0,78 m², cellules GaAs à 29,5 %). La valeur réelle dépend de l'angle bêta actuel, de l'état de déploiement des panneaux et de la précision d'attitude.
**GO/NO-GO:** Production électrique du générateur solaire dans la plage attendue

### Étape 4 — Surveillance de la décharge en éclipse
**Action:** Surveiller la batterie pendant une éclipse complète (~34–36 minutes sur l'orbite SSO de la mission à ~513 km).
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — à l'entrée en éclipse
**Verify:** `eps.power_gen` (0x0107) = ~0W sous 30s après l'entrée en éclipse
**Verify:** `eps.bat_soc` (0x0101) en baisse à < 1.5 % par minute sous 60s
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — à mi-éclipse
**Verify:** `eps.bus_voltage` (0x0105) > 30.9V (la batterie soutient le bus) sous 10s
**GO/NO-GO:** Rythme de décharge de la batterie nominal, tension du bus maintenue

### Étape 5 — Reprise de charge en sortie d'éclipse
**Action:** Surveiller la reprise de charge de la batterie après la sortie d'éclipse.
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — à la sortie d'éclipse +5 min
**Verify:** `eps.power_gen` (0x0107) > 35W sous 60s après la sortie d'éclipse
**Verify:** `eps.bat_soc` (0x0101) en hausse sous 120s après la sortie d'éclipse
**Action:** Consigner le rythme de reprise de charge. La batterie doit retrouver sa pleine charge pendant la partie éclairée de l'orbite sous charge nominale.
**GO/NO-GO:** Reprise de charge nominale après l'éclipse

### Étape 6 — Vérification du bilan de puissance
**Action:** Calculer la consommation électrique totale du satellite à partir de la télémesure. La comparer à la production électrique et à la capacité de la batterie. Vérifier un bilan énergétique positif sur une orbite complète.
**TC:** `GET_PARAM(param_id=0x0108)` (Service 20, Subtype 3) — puissance totale des charges
**Verify:** Production électrique moyenne sur l'orbite > consommation moyenne sur l'orbite
**Verify:** SOC en fin d'éclipse > 50 % sous charge nominale
**Action:** Documenter le bilan de puissance avec ses marges pour la recette en orbite et les opérations nominales.
**GO/NO-GO:** Bilan énergétique moyen sur l'orbite positif confirmé

### Étape 7 — Régulation de la tension du bus sous transitoire de charge
**Action:** Éprouver la régulation du bus en commandant une variation de charge connue. NE PAS utiliser
la charge utile pour cela : sa ligne reste sur OFF jusqu'à COM-009, et une commande de mode sur une
ligne non alimentée revient silencieusement en arrière. La ligne du réchauffeur batterie (8 W, réchauffeurs de `tcs.yaml`) sert de
source de transitoire et est ensuite rétablie dans son état d'entrée.
**Action:** Consigner d'abord l'état d'entrée de `eps.pl_htr_bat` (0x0115).
**TC:** `EPS_POWER_ON(line_index=5)` (Service 8, Subtype 1, func_id 19) — htr_bat (essai bref)
**Verify:** `eps.bus_voltage` (0x0105) reste dans la plage [30.2V, 34.0V] sous 5s
**TC:** `EPS_POWER_OFF(line_index=5)` (Service 8, Subtype 1, func_id 20) — rétablir, UNIQUEMENT si la ligne était coupée à l'entrée
**Verify:** `eps.pl_htr_bat` (0x0115) revenu à sa valeur d'entrée sous 5s
**Verify:** `eps.bus_voltage` (0x0105) revient dans [30.9V, 34.0V] sous 10s
**GO/NO-GO:** Régulation du bus stable sous charge transitoire, état de la ligne rétabli

## Conduite à tenir hors nominal
- Si la tension du bus < 30.9V : contrôler le SOC de la batterie. Si le SOC < 30 %, réduire immédiatement les charges. Désactiver les réchauffeurs non essentiels. Vérifier l'attitude de pointage solaire. Si la tension du bus < 29.6V, exécuter CTG-001 (délestage) et, avec l'accord du FD, `OBC_SET_MODE(mode=1)` — 1 correspond à SAFE (0 à NOMINAL ; l'ancien texte inversait le codage).
- Si la production électrique < 35W au Soleil avec un bon pointage solaire : contrôler les courants de chaque aile via `GET_PARAM(param_id=0x0146)` (aile +Y) et `GET_PARAM(param_id=0x0147)` (aile −Y). Si un panneau est sous-performant, consigner une anomalie. Évaluer la viabilité du bilan de puissance avec un seul panneau.
- Si le SOC de la batterie < 50 % en fin d'éclipse : réduire la charge opérationnelle. Reporter les activités de recette en orbite exigeant beaucoup de puissance. Réévaluer le bilan de puissance.
- Si le rythme de reprise de charge est inférieur à la prédiction : rechercher une dégradation du générateur solaire. Vérifier le régulateur de charge de la batterie via `GET_PARAM(param_id=0x0109)`. En cas de panne suspectée du régulateur de charge, examiner la voie redondante.
- Si une oscillation de la tension du bus est détectée : contrôler le mode de régulation via `GET_PARAM(param_id=0x010A)`. Consigner une anomalie pour examen par l'ingénieur EPS. En cas d'instabilité, commander `OBC_SET_MODE(mode=1)` (SAFE) avec l'accord du FD ; rétablir avec mode=0 (NOMINAL) après investigation.

## Postconditions
- [ ] Tension du bus confirmée suivant la batterie (au plus le plafond de 33.4V)
- [ ] Tension et SOC de la batterie nominaux (> 70 % après charge complète)
- [ ] Générateur solaire produisant 40-90W au Soleil (panneaux déployés, pointage solaire)
- [ ] Rythme de décharge en éclipse conforme à la prédiction
- [ ] Reprise de charge nominale après la sortie d'éclipse
- [ ] Bilan énergétique moyen sur l'orbite positif confirmé
- [ ] Régulation du bus stable sous charges transitoires
- [ ] Rapport de vérification de l'EPS établi avec les valeurs de référence

## État de sortie
- IDENTIQUE à l'état d'entrée : toute ligne touchée par cette fiche (htr_bat à
  l'étape 7) est rétablie ; aucun mode, palier ou verrou modifié

**PROCÉDURE SUIVANTE :** COM-002 (Vérification du TCS)
