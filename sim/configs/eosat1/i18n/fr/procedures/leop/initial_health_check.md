# LEOP-002 : Bilan de santé initial
**Sous-système :** Tous / OBDH
**Phase :** LEOP
**Révision :** 2.0 --- refonte du déroulement 2026-08c (états d'entrée et de sortie ; l'AOCS et la charge utile
sont ÉTEINTS à ce stade et ne sont plus « vérifiés » ; les contrôles des roues sont déplacés dans
COM-004, où les roues sont effectivement activées)
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de LEOP-001 --- image applicative en cours d'exécution, liaison sur le
échelon LOW, SID HK 1/3/4/6/11 activés, horloge non réglée. AOCS (`aocs_wheels`), charge utile,
refroidisseur du FPA, réchauffeurs et lignes de propulsion tous sur OFF.

## Objet
Évaluer l'état de santé des sous-systèmes ALIMENTÉS à ce stade de la
LEOP --- EPS, TCS, OBDH et TT&C --- et confirmer positivement que tout le reste est
toujours éteint. Établir les valeurs de télémesure de référence de la mission. Cette fiche
ne met rien sous tension et ne commande aucun mode : elle observe.

## Prérequis
- [ ] LEOP-001 (Première acquisition) terminée avec succès
- [ ] Liaison bidirectionnelle en bande S active avec une marge de liaison > 3 dB
- [ ] Au moins 8 minutes restantes dans le passage station sol en cours
- [ ] Archivage de la télémesure du MCS confirmé actif

## Déroulement

### Étape 1 --- Demander l'ensemble des données de servitude EPS
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.bus_voltage` (0x0105) dans la plage [26.0V, 30.0V] sous 10s
**Verify:** `eps.bat_voltage` (0x0100) rapportée sous 10s
**Verify:** `eps.bat_soc` (0x0101) > 50 % sous 10s
**Verify:** `eps.power_gen` (0x0107) > 0W (confirme un éclairement au moins partiel) sous 10s — uniquement au Soleil : avec `eps.eclipse_flag` (0x0108) = 1, 0 W est attendu (la séparation par défaut place cette carte dans la première éclipse) ; le consigner et revérifier après la sortie d'éclipse
**GO/NO-GO:** Paramètres EPS dans les limites nominales post-séparation

### Étape 2 --- Confirmer que les sous-systèmes non alimentés sont éteints
**Action:** Le même rapport du SID 1 contient tous les indicateurs de ligne du PDM. Confirmer que
l'état d'alimentation du démarrage à froid est toujours exactement celui laissé par LEOP-001 : rien d'autre que
l'OBC, le récepteur et l'émetteur (armé automatiquement) n'est alimenté.
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 0 --- ensemble AOCS non alimenté (alimenté dans LEOP-007)
**Verify:** `eps.pl_payload` (0x0113) = 0 --- ligne charge utile coupée (alimentée dans COM-009)
**Verify:** `eps.pl_fpa_cooler` (0x0114) = 0 --- ligne du refroidisseur coupée (alimentée dans COM-010)
**Verify:** `eps.pl_prop` (0x014A) = 0 --- ligne de propulsion coupée (alimentée uniquement pour les manœuvres)
**Note:** NE PAS demander ici les SID HK 2 (AOCS) ou 5 (charge utile) : ces SID ne sont
pas encore activés (seuls 1/3/4/6/11 le sont), et leurs sous-systèmes ne sont pas alimentés --- les
indicateurs de ligne ci-dessus constituent le contrôle de santé honnête d'une unité éteinte. Il n'y a aucun mode AOCS
à vérifier ni aucune télémesure des roues à lire à ce stade ; les étapes de l'ancienne fiche
« vérifier `aocs.mode` = DETUMBLE » et « vérifier que les quatre roues de réaction
répondent » décrivaient un état du satellite qui n'existe qu'à partir de
LEOP-007 et de COM-004 respectivement.
**GO/NO-GO:** L'état d'alimentation est conforme au plan LEOP --- rien n'est alimenté prématurément

### Étape 3 --- Demander les données de servitude thermiques
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27)
**Verify:** `tcs.temp_obc` (0x0406) dans la plage [-5C, +45C] sous 10s
**Verify:** `tcs.temp_battery` (0x0407) dans la plage [0C, +35C] sous 10s
**Verify:** `tcs.temp_fpa` (0x0408) rapportée (charge utile non alimentée, valeur ambiante attendue) sous 10s
**Note:** Toutes les LIGNES de réchauffeurs sont coupées. Si `tcs.temp_battery` tend vers
0C, le signaler pour LEOP-007, étape 2, qui alimente la ligne du réchauffeur batterie si
nécessaire --- ne pas l'alimenter depuis cette fiche.
**GO/NO-GO:** Toutes les zones thermiques dans les limites de survie

### Étape 4 --- Demander les données de servitude OBDH
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27)
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) ou 1 (SAFE) sous 10s
**Verify:** `obdh.cpu_load` (0x0302) < 70 % sous 10s
**Note:** `OBC_SET_MODE` (func 50) code 0 = NOMINAL, 1 = SAFE, 2 =
EMERGENCY, et `obdh.mode` (0x0300) relit le même codage.
**GO/NO-GO:** OBDH fonctionnant dans ses paramètres nominaux

### Étape 5 --- Demander les données de servitude TT&C
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27)
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) sous 10s
**Verify:** page TT&C (sol) : `ttc.rssi` (0x0502) > -126 dBm sous 10s
**Verify:** page TT&C (sol) : `ttc.link_margin` (0x0503) > 3.0 dB sous 10s
**GO/NO-GO:** Liaison TT&C nominale avec une marge suffisante

### Étape 6 --- Établir le rapport d'évaluation de santé
**Action:** Comparer toute la télémesure reçue aux valeurs attendues après la séparation. Signaler tout paramètre hors de la plage nominale. Produire la synthèse d'évaluation de santé pour le directeur de vol.
**GO/NO-GO:** Tous les sous-systèmes alimentés nominaux --- feu vert pour poursuivre avec LEOP-004

## Conduite à tenir hors nominal
- Si `eps.bat_soc` < 50 % : reporter les opérations non essentielles. Donner la priorité au déploiement des panneaux (LEOP-004) et à l'acquisition du Soleil (LEOP-005). Réduire la demande de TM pour économiser l'énergie.
- Si `tcs.temp_battery` < 0C : se reporter immédiatement à LEOP-007, étape 2 --- cette étape alimente la ligne `htr_bat` (`EPS_POWER_ON(line_index=5)`) et active le réchauffeur batterie. Surveiller la remontée de la température.
- Si `obdh.cpu_load` > 80 % : rechercher un ordonnancement anormal des tâches. Un passage de l'OBC en SAFE (`OBC_SET_MODE(mode=1)`) requiert l'accord du directeur de vol ; rétablir ensuite NOMINAL avec `OBC_SET_MODE(mode=0)`.
- Si un SID HK activé ne répond pas : renouveler la demande deux fois. En l'absence persistante de réponse, contrôler la qualité de la liaison TM. Consigner une anomalie pour investigation.
- Si l'un des indicateurs de ligne de l'étape 2 vaut 1 : un équipement a été alimenté hors séquence. Identifier qui l'a commandé, consigner l'anomalie et remettre la ligne hors tension (`EPS_POWER_OFF`), sauf si une fiche ultérieure l'a déjà légitimement prise en charge.

## État de sortie
- IDENTIQUE à l'état d'entrée --- cette fiche ne commande aucun changement d'état. Toutes
  les valeurs observées sont archivées comme référence de la mission.

## Postconditions
- [ ] SID HK 1, 3, 4, 6 reçus et archivés comme référence de la mission
- [ ] EPS, TCS, OBDH, TT&C confirmés nominaux
- [ ] Lignes AOCS / charge utile / refroidisseur / propulsion confirmées positivement sur OFF
- [ ] Rapport d'évaluation de santé diffusé à l'équipe de mission

**PROCÉDURE SUIVANTE :** LEOP-004 (Vérification du générateur solaire)
