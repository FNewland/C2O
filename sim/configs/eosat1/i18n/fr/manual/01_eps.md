# Sous-système d'alimentation électrique (EPS) d'EOSAT-1

**Référence du document :** EOSAT1-UM-EPS-002
**Édition :** 2.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Vue d'ensemble

Le sous-système d'alimentation électrique (EPS) produit, stocke, régule et distribue la puissance
électrique à tous les sous-systèmes du satellite. Il comprend cinq panneaux solaires GaAs fixés sur la structure (toutes les
faces du satellite sauf -Z), deux ailes solaires déployables sur les faces +/-Y, une batterie lithium-ion, un
module de distribution de puissance (PDM) en redondance froide doté de lignes commutables et non commutables, ainsi que
le harnais associé.

## 2. Architecture

### 2.1 Panneaux solaires — panneaux fixés sur la structure et ailes déployables

| Paramètre            | Valeur                     |
|----------------------|----------------------------|
| Configuration        | 5 panneaux fixés sur la structure + 2 ailes déployables (+/-Y) sur un mécanisme d'entraînement du générateur solaire à un axe |
| Technologie des cellules | GaAs triple jonction (rendement de cellule de 29,5 %) |
| Surface fixée sur la structure | 0,198 m² au total (configuration repliée) |
| Surface totale déployée | 0,438 m² (panneaux de structure + les deux ailes) |
| Surface d'une aile   | 0,12 m² de cellules par aile (+Y et -Y, 2 panneaux repliables de 209 x 342 mm) |
| Masse de l'ensemble aile | ~1,07 kg par aile, charnières et HDRM compris |
| Puissance crête (BOL) | ~89 W instantanés, ailes en poursuite solaire à bêta = 0, entièrement déployées (ailes seules 70 W, conforme à la classe de puissance MMA eHaWK 6U) |
| Moyenne sur l'orbite (BOL, nadir) | ~55 W à bêta = 24°, ~42 W à bêta = 50° (éclipse comprise) |
| Performances EOL     | K = 267,2 W/m² de surface projetée (chaîne complète de pertes, EOL à 3 ans, sa_age_factor 0,9175) |
| Tension de fonctionnement | 28 V (bus régulé)     |
| Durée de déploiement d'une aile | ~30 s par aile (libération par fil thermofusible) |

Cinq faces du satellite portent des panneaux solaires fixés sur la structure (la face -Z porte
l'ouverture de l'imageur et le radiateur et n'a pas de cellules). Les ailes solaires déployables sont
montées sur les faces +Y et -Y, sur un mécanisme d'entraînement du générateur solaire à un axe commun
(SADA) dont l'axe de rotation est l'axe Y satellite — la normale à l'orbite dans le repère LVLH
de pointage nadir (z = nadir, y = -normale à l'orbite). En configuration repliée, la
surface totale de captation solaire est de 0,198 m² (panneaux de structure seuls). Après le déploiement
des ailes, la surface totale atteint 0,438 m² (0,12 m² ajoutés par aile). La puissance
produite par chaque panneau de structure dépend de la projection en cosinus du vecteur Soleil
sur la normale au panneau ; la paire d'ailes, lorsque le SADA est en poursuite, suit en continu
la projection du Soleil perpendiculaire à l'axe d'entraînement (loi en cos bêta,
indépendante de la position sur l'orbite) :

| Face du panneau | Orientation (repère de pointage nadir) | Remarques                     |
|------------|------------------------------------|-------------------------------------|
| +X         | Plan de l'orbite                   | Balaie la direction du Soleil à chaque orbite |
| -X         | Plan de l'orbite                   | Balaie la direction du Soleil à chaque orbite |
| +Y         | Plan de l'orbite (aile sur SADA)   | L'aile suit le Soleil lorsque le SADA est activé |
| -Y         | Plan de l'orbite (aile sur SADA)   | L'aile suit le Soleil lorsque le SADA est activé |
| +Z         | Normale à l'orbite                 | Éclairement continu en sin bêta      |
| -Z         | Opposée à la normale à l'orbite    | Ouverture de l'imageur + radiateur, sans cellules |

La puissance produite par panneau se calcule ainsi :

```
P_panel = A_panel * K * max(0, cos(angle_to_sun)) * degradation_factor
```

où `K` est la constante effective dans le plan du générateur, qui intègre la chaîne complète
de pertes (dégradation intrinsèque/taux de remplissage 0,85, température à 65 °C, MPPT 0,97,
harnais 0,95, et vieillissement), et où `degradation_factor` rend compte de l'endommagement des panneaux.
Deux cas de panne du SADA sont à distinguer, tous deux réels et tous deux diagnosticables :

* **Entraînement hors tension** (équipement S2 0x0101). Les ailes cessent de contribuer, mais
  les cinq panneaux FIXÉS sur la structure sont collés à celle-ci et câblés directement
  sur le MPPT — ils n'ont pas besoin de l'entraînement et continuent de produire (~15-18 W en phase éclairée).
  Une production qui tomberait *exactement à zéro* signifierait une perte totale du générateur, et non une
  panne de l'entraînement ; c'est la production résiduelle des panneaux de structure qui permet de distinguer les deux cas.
* **Entraînement BLOQUÉ** (grippage du mécanisme, ou poursuite de l'entraînement désactivée). L'arbre
  se fige dans sa position, de sorte que `solar_array_drive_angle`
  (0x0133) devient plat tandis que le Soleil s'éloigne de la normale figée. Les
  ailes reviennent au rapport cyclique d'ailes fixes en |sin(phase orbitale)| — soit une perte de production
  moyenne sur l'orbite d'environ 36 %, avec une ondulation caractéristique, une fois par orbite,
  sur les courants de chaque aile 0x0146 / 0x0147.

La vitesse de l'entraînement est limitée à `sada_max_rate_deg_s` (1,0°/s). La poursuite solaire
exige une révolution par orbite, soit 0,064°/s : la marge est donc d'environ 15x en
opérations nominales ; un repositionnement commandé de 90° prend environ 90 s et apparaît sous forme de
rampe sur 0x0133.

### 2.1.1 Ailes solaires déployables

Le satellite porte deux ailes solaires déployables, une sur chacune des faces +Y et -Y.
Chaque aile ajoute 0,12 m² de surface de captation solaire et est maintenue en position repliée par un
mécanisme de retenue à fil thermofusible. Le déploiement est commandé par la gestion des fonctions S8 :

| Paramètre            | Valeur                     |
|----------------------|----------------------------|
| Emplacement des ailes | Face +Y et face -Y (arbre SADA commun) |
| Surface par aile     | 0,12 m² de cellules (0,143 m² géométriques, taux de remplissage ~84 %) |
| Mécanisme de déploiement | Fil thermofusible (chauffage résistif) |
| Durée de déploiement | ~30 secondes par aile      |
| Commande de déploiement | EPS_DEPLOY_WING (func_id 81) |
| Interrogation de l'état | EPS_WING_STATUS (func_id 82) |
| Télémesure d'état    | wing_status (0x0144) — masque de bits : bit 0 = +Y, bit 1 = -Y |
| TM de minuterie de déploiement | wing_deploy_timer (0x0145) — compte à rebours en secondes |
| Événements de déploiement | 0x0112 (+Y déployée), 0x0113 (-Y déployée) |

**Procédure de déploiement :**

1. Vérifier que l'attitude du satellite est stable (vitesses angulaires < 0.5 deg/s).
2. Vérifier que le SoC de la batterie est > 50 % (le déploiement consomme ~2 A pendant 30 s par aile).
3. Envoyer `EPS_DEPLOY_WING` avec `wing=0` (+Y), `wing=1` (-Y) ou `wing=2` (les deux).
4. Surveiller le décompte de `wing_deploy_timer` (0x0145) à partir de 30 s.
5. Confirmer le déploiement par le masque de bits `wing_status` (0x0144) et la génération de l'événement.
6. Vérifier l'augmentation de la puissance produite sur les courants des panneaux +Y / -Y correspondants.

**Contraintes :**
- Les ailes devraient être déployées après le déploiement de l'antenne et l'amortissement initial des vitesses angulaires.
- Dans la mesure du possible, déployer une aile à la fois afin de maîtriser la perturbation d'attitude.
- Si une aile ne se déploie pas, une nouvelle tentative peut être commandée après un temps de refroidissement de 60 s.

### 2.2 Batterie

| Paramètre            | Valeur                     |
|----------------------|----------------------------|
| Technologie          | Lithium-ion (Li-ion)       |
| Tension nominale     | 26,4 V (modèle) ; 28,8 V (fiche technique) ; plage 21,5–29,2 V |
| Capacité             | 100 Wh (3 Ah, 8S1P)       |
| Pièce de référence   | GomSpace NanoPower BPX, 8S-1P : 100 Wh, 3 Ah, 28,8 V nominal, ~500 g, éléments 18650 |
| Rendement coulombien | 0,94 (acceptation de charge) |
| Profondeur de décharge | 35 % max. (opérations nominales) |
| Méthode de charge    | CC/CV avec réduction progressive au-dessus de 90 % de SoC, coupure thermique |

### 2.3 Module de distribution de puissance (PDM)

L'EPS utilise un module de distribution de puissance (PDM) en redondance froide qui porte **neuf** lignes
d'alimentation : deux non commutables et sept commutables. L'ensemble des lignes, leur ordre et leurs
états par défaut à la mise sous tension sont fixés par le harnais du PDM et consignés dans la configuration
de la mission (`subsystems/eps.yaml`, `power_lines:`). L'argument `line_index` de
`EPS_POWER_ON` / `EPS_POWER_OFF` (S8 fonctions 19 / 20) est l'indice dans ce tableau.

| Idx | Nom de la ligne | Charge                                | Commutable | État par défaut à la mise sous tension | Param. d'état | Param. de courant | Seuil de disjonction |
|-----|----------------|----------------------------------------|------------|------------------|--------------|---------------|---------|
| 0   | `obc`          | Calculateur OBC                        | Non        | ON               | `eps.pl_obc` 0x0110 | `eps.line_current_0` 0x0118 | 2.0 A |
| 1   | `ttc_rx`       | Récepteur TT&C (y compris le récepteur de balise UHF) | Non | ON      | `eps.pl_ttc_rx` 0x0111 | `eps.line_current_1` 0x0119 | 0.3 A |
| 2   | `ttc_tx`       | Émetteur TT&C + PA                     | Oui        | OFF              | `eps.pl_ttc_tx` 0x0112 | `eps.line_current_2` 0x011A | 1.0 A |
| 3   | `payload`      | Imageur de la charge utile             | Oui        | OFF              | `eps.pl_payload` 0x0113 | `eps.line_current_3` 0x011B | 2.5 A |
| 4   | `fpa_cooler`   | Refroidisseur du FPA                   | Oui        | OFF              | `eps.pl_fpa_cooler` 0x0114 | `eps.line_current_4` 0x011C | 1.0 A |
| 5   | `htr_bat`      | Réchauffeur de batterie                | Oui        | OFF              | `eps.pl_htr_bat` 0x0115 | `eps.line_current_5` 0x011D | 0.5 A |
| 6   | `htr_obc`      | Réchauffeur de l'OBC                   | Oui        | OFF              | `eps.pl_htr_obc` 0x0116 | `eps.line_current_6` 0x011E | 0.3 A |
| 7   | `aocs_wheels`  | Roues de réaction                      | Oui        | OFF              | `eps.pl_aocs_wheels` 0x0117 | `eps.line_current_7` 0x011F | 0.8 A |
| 8   | `prop`         | Propulsion (réchauffeur du lit catalytique + pilotes de vannes) | Oui | OFF | `eps.pl_prop` 0x014A | `eps.line_current_8` 0x014B | 0.8 A |

#### Lignes non commutables

Les lignes 0 (`obc`) et 1 (`ttc_rx`) sont alimentées en permanence après la séparation et ne peuvent pas
être mises hors tension par commande. Elles garantissent que le traitement bord est toujours disponible et que le
satellite peut toujours être commandé. Après l'activation des interrupteurs de séparation, elles se mettent sous tension
automatiquement au cours de la phase POWER_STABILIZE, ce qui garantit que l'OBC et le
récepteur sont opérationnels avant tout contact sol. Leur état global est également
publié sous la forme du masque de bits `eps.pdm_unsw_status` (0x012A).

#### Lignes commutables

Les lignes 2-8 peuvent être mises sous ou hors tension individuellement avec `EPS_POWER_ON(line_index=N)` /
`EPS_POWER_OFF(line_index=N)`. La protection contre les surintensités est assurée sur chaque sortie aux
courants de disjonction ci-dessus (150 % du nominal sous 28 V, disjonction en 50 ms) ; une disjonction positionne le
bit correspondant de `eps.oc_trip_flags` (0x010D) et coupe la ligne jusqu'à sa réinitialisation.

**Toutes les lignes commutables sont à OFF par défaut à la mise sous tension.** Aucune ligne ne démarre
d'elle-même sous tension — c'est LEOP-007 (Mise sous tension séquentielle) qui les alimente, dans l'ordre des dépendances.
La seule exception en pratique est `ttc_tx`, que le maintien automatique de l'émetteur (auto-TX) de la plateforme met
sous tension de façon autonome pendant 15 minutes à chaque télécommande acceptée (voir §2.4).

À noter qu'il n'existe **pas** de lignes distinctes « capteurs AOCS » et « actionneurs AOCS », ni de
lignes dédiées à l'OBC redondant ou au transpondeur redondant : l'ensemble de l'AOCS est sur `aocs_wheels`
(ligne 7), et la redondance de l'OBC et du transpondeur est interne à ces équipements au lieu de disposer d'une ligne
PDM propre.

#### Ordre de délestage

Le délestage sur sous-tension parcourt `LOAD_SHED_ORDER` depuis le début, priorité la plus basse
en premier : `payload` → `fpa_cooler` → `ttc_tx` → `aocs_wheels` → `prop`. La propulsion est
délibérément placée EN DERNIER — la perte de la ligne en pleine poussée déclenche l'interruption de poussée bord (motif 4).
`eps.load_shed_stage` (0x0134) indique jusqu'où l'EPS est descendu dans la liste.

Le délestage peut aussi être COMMANDÉ avec `EPS_EMERGENCY_LOAD_SHED` (S8 fonction 25,
niveau 0-3) : le niveau N déleste immédiatement les N premières lignes de l'ordre (niveau 1
= charge utile, 2 = + refroidisseur du FPA, 3 = + émetteur TTC — le niveau 3 coupe délibérément votre propre
liaison descendante). Sémantique de l'élément 8 de 2026-08c : le délestage est **monotone**
— une commande de délestage ne fait jamais que mettre des lignes à OFF (auparavant, elle réalimentait toutes les lignes
au-delà du niveau commandé), le niveau 0 efface le verrou commandé sans
réalimenter quoi que ce soit, et le rétablissement incombe à l'opérateur, ligne par ligne
(`EPS_POWER_ON`). Le niveau commandé est verrouillé dans 0x0134 et les événements
`LOAD_SHED_STAGE_1..3` (0x0106-0x0108) sont émis une fois par niveau franchi.

#### Voie PDM en redondance froide

Une voie PDM redondante (PDM-B) fournit une voie de distribution de puissance de secours. PDM-B est
normalement hors tension (redondance froide) et peut être activée par commande sol si PDM-A présente
un défaut. Les deux voies PDM partagent la même topologie de lignes non commutables/commutables.

### 2.4 Canal de commande PDM dédié

Le récepteur du transpondeur est alimenté par un canal de commande PDM dédié,
indépendant de la ligne commutable principale de l'émetteur et de l'amplificateur de puissance. Cette
conception garantit que le satellite reste commandable même lorsque l'émetteur est éteint
(p. ex. pendant la minuterie de séparation de 30 minutes). Le canal de commande dédié n'alimente que
la chaîne de réception ; l'émetteur et l'amplificateur de puissance sont sur une ligne commutable distincte,
avec une minuterie d'extinction automatique de 15 minutes après le dernier décodage de commande, afin d'économiser l'énergie.

### 2.5 Circuit de minuterie de séparation

L'EPS comprend un circuit matériel de minuterie de séparation qui impose la période de 30 minutes sans émission
après la séparation du lanceur :

1. Les interrupteurs de séparation s'ouvrent lors de la libération par le lanceur.
2. Le circuit de minuterie inhibe toutes les lignes PDM commutables pendant 30 minutes.
3. Seules les lignes non commutables (OBC + RX) sont actives pendant cette période.
4. À l'échéance de la minuterie, l'OBC commande le déploiement de l'antenne par fil thermofusible.
5. La ligne commutable de l'émetteur est alors activée pour les émissions de balise.

## 3. Modes de puissance

| Mode       | Charges alimentées                             | Consommation type   |
|------------|------------------------------------------------|---------------------|
| NOMINAL    | Tous les sous-systèmes, charge utile en veille | ~29 W en moyenne sur l'orbite |
| NOMINAL+IMAGING | Comme ci-dessus, plus l'imageur et le refroidisseur du FPA par intermittence | ~33 W en moyenne sur l'orbite |
| SAFE       | OBC, TTC, réchauffeurs TCS, AOCS (COARSE_SUN) | ~20 W        |
| EMERGENCY  | OBC, TTC essentiels uniquement                 | ~11 W               |
| ECLIPSE    | Alimentation par la batterie seule, charges non essentielles délestées | ~25 W |

### 3.1 Détail du bilan de puissance (consommation nominale des sous-systèmes)

Chaque puissance indiquée ci-dessous est la valeur que `subsystems/eps.yaml` comptabilise ; elle est dérivée
d'un composant de vol identifié — voir `docs/plan_2026-08b/POWER_SIZING.md` pour les
recherches, les citations et le tableau « classe de composant -> héritage en vol -> valeur retenue ».
Décision R1 : *« un CubeSat n'aurait généralement pas d'émetteur de 20 W et
aurait du mal à produire 114 W crête »* — c'est exact sur les deux points, et c'est ce
tableau qui était erroné, non le modèle.

| Sous-système       | Puissance type | Remarques                        |
|--------------------|---------------|-----------------------------------|
| OBC (principal)    | 6 W           | OBC 3 W + servitude PDU/EPS 3 W   |
| Récepteur TTC (RX) | 1,5 W         | Toujours sous tension (non commutable). Endurosat bande S repos/réception 1,2 W + ~0,3 W récepteur de balise UHF |
| Émetteur TTC+PA    | 5 W palier LOW / 11 W palier HIGH | Sous tension uniquement pendant les contacts. 2 W RF (33 dBm) au palier HIGH — émetteur-récepteur Endurosat bande S, 11 W continus à 33 dBm, 1,2 W au repos |
| Ensemble AOCS      | Capacité de ligne 12 W ; 4 / 9 / 15 W comptabilisés selon le mode (COARSE / NOMINAL / FINE) | Comptabilisé d'après la consommation réelle du modèle AOCS en 0x02C8, et non d'après la capacité de la ligne |
| Charge utile (prise de vue) | 5,5 W | Mode prise de vue du Simera Sense TriScape100, 1100 mA sous 5 V |
| Charge utile (veille) | 2,4 W      | TriScape100 au repos/en lecture, 470 mA sous 5 V |
| Refroidisseur du FPA | 15 W        | Cryoréfrigérateur Stirling miniature (reclassement de la phase 4), ligne d'alimentation propre. Sa capacité est une *fraction de Carnot* (`fpa_cooler_carnot_fraction` = 0.23) : la puissance frigorifique atteignable diminue donc quand dT augmente — les 15 W sont la puissance absorbée, et non une puissance frigorifique fixe |
| Réchauffeur de batterie | 8 W      | Thermostat ON +5 °C / OFF +10 °C  |
| Réchauffeur de l'OBC | 4 W         | Commande manuelle                 |
| Propulsion         | 12 W lit catalytique + 2 W vannes, lorsqu'elle est armée | Ligne à OFF en dehors de la préparation des manœuvres |

**La veille doit consommer moins que la prise de vue.** Jusqu'à 2026-08b, ce tableau et eps.yaml
étaient en désaccord entre eux et avec la physique : la veille était comptabilisée à 6 W contre
5 W pour la prise de vue, autrement dit l'imageur consommait *moins* pendant la prise de vue. Les deux valeurs sont désormais
des chiffres de la fiche technique du TriScape100, et
`tests/test_content/test_eps_config_manual_consistency.py` vérifie
l'ordre comme les valeurs.

### 3.2 Bilan moyen sur l'orbite (bêta le plus défavorable, EOL)

Produit par `tools/power_budget.py`, qui fait tourner les modèles EPS et TCS de production
sur l'orbite réelle propagée — et non par un tableur.

| Profil | Production | Charge | Marge | Rapport |
|---------|-----------|------|--------|-------|
| repos            | 38,0 W | 25,5 W | +12,5 W | 1,49 |
| nominal          | 38,0 W | 28,7 W | +9,3 W  | 1,33 |
| nominal + prise de vue | 38,0 W | 32,5 W | +5,5 W | 1,17 |
| manœuvre         | 38,0 W | 32,0 W | +6,0 W  | 1,19 |

Le critère d'acceptation — la production moyenne sur l'orbite dépasse la charge moyenne sur l'orbite
avec TOUS les systèmes nominaux sous tension, SCAO compris — est satisfait avec un rapport de 1,33x en pointage nadir NOMINAL
à l'angle bêta le plus défavorable de l'année (49,8°), en EOL à 3 ans.

**La prise de vue fonctionne par intermittence, et non en continu.** Le bilan ci-dessus suppose trois
acquisitions de 90 secondes par orbite, le refroidisseur du FPA fonctionnant environ 20 minutes
autour de celles-ci. Maintenir le pointage FINE et le refroidisseur pendant une orbite entière
(le profil `worst`) donne un bilan de puissance NÉGATIF par construction : c'est l'objet de l'exercice, et non une
erreur de dimensionnement.

Lors des transitions d'éclipse, le PCDU bascule de manière autonome de l'alimentation par le générateur solaire à
l'alimentation par la batterie. Le paramètre de télémesure `eclipse_flag` (0x0108) indique l'état
d'éclairement courant.

## 4. Paramètres de télémesure

| ID param. | Nom            | Unité  | Description                          |
|----------|-----------------|--------|--------------------------------------|
| 0x0100   | bat_voltage     | V      | Tension aux bornes de la batterie    |
| 0x0101   | bat_soc         | %      | État de charge de la batterie        |
| 0x0102   | bat_temp        | °C     | Température du bloc batterie         |
| 0x0103   | sa_a_current    | A      | Courant de l'aile A du générateur solaire |
| 0x0104   | sa_b_current    | A      | Courant de l'aile B du générateur solaire |
| 0x0105   | bus_voltage     | V      | Tension du bus principal (régulé)    |
| 0x0106   | power_cons      | W      | Consommation totale                  |
| 0x0107   | power_gen       | W      | Production de puissance totale       |
| 0x0108   | eclipse_flag    | booléen | État d'éclipse (1 = en éclipse)     |
| 0x0109   | bat_current     | A      | Courant de charge/décharge de la batterie |
| 0x010A   | bat_capacity    | Ah     | Capacité restante de la batterie     |
| 0x0144   | wing_status     | masque de bits | État de déploiement des ailes solaires (bit0=+Y, bit1=-Y) |
| 0x0145   | wing_deploy_timer| s     | Minuterie de compte à rebours du déploiement des ailes |

## 5. Définition des limites

| Paramètre     | Jaune bas  | Jaune haut  | Rouge bas | Rouge haut |
|---------------|------------|-------------|---------|----------|
| bat_soc (%)   | 25         | 95          | 15      | 100      |
| bat_voltage (V)| 23        | 29          | 22      | 29.5     |
| bat_temp (°C) | 2          | 40          | 0       | 45       |
| bus_voltage (V)| 27        | 29          | 26.5    | 29.5     |

### 5.1 Réaction aux dépassements de limites

- **Dépassement jaune** : avertissement à l'opérateur ; analyser la tendance.
- **Dépassement rouge (bat_soc < 15 %)** : la FDIR déclenche un délestage autonome et un éventuel
  passage en mode survie (voir `08_fdir.md`).
- **Dépassement rouge (bat_temp)** : ajustement de la régulation des réchauffeurs ; si la température dépasse 45 °C,
  la charge de la batterie est inhibée.

## 6. Commandes utiles

| Commande          | Service  | Description                           |
|-------------------|----------|---------------------------------------|
| HEATER_CONTROL    | S8,S1    | Commander le circuit du réchauffeur de batterie |
| OBC_SET_MODE      | S8,S1    | Passer en SAFE (déclenche le délestage) |
| HK_REQUEST        | S3,S27   | Demander les données de servitude de l'EPS (SID=1) |
| GET_PARAM         | S20,S3   | Lire un paramètre EPS individuel      |
| SET_PARAM         | S20,S1   | Modifier un paramètre de configuration de l'EPS |
| EPS_DEPLOY_WING   | S8,S1    | Déployer une aile solaire (func_id 81) |
| EPS_WING_STATUS   | S8,S1    | Interroger l'état de déploiement des ailes (func_id 82) |

### 6.1 Commande du réchauffeur de batterie

Le réchauffeur de batterie se commande par la commande `HEATER_CONTROL` avec `circuit=battery`
et `on=true/false`. Le réchauffeur maintient la température de la batterie au-dessus de 2 °C pendant l'éclipse.
La régulation autonome du réchauffeur est mise en œuvre dans la logique FDIR du TCS et active le réchauffeur
si `bat_temp` descend sous 5 °C.

## 7. Remarques d'exploitation

1. Pendant la LEOP, le fonctionnement du générateur solaire fixé sur la structure est confirmé en surveillant `sa_a_current`
   et `sa_b_current`. Le déploiement des ailes est confirmé en surveillant `wing_status`
   (0x0144) et les courants des panneaux correspondants. Une augmentation du courant sur le panneau +Y / -Y
   après le déploiement d'une aile indique que celle-ci s'est bien déployée.
2. Le reconditionnement de la batterie n'est pas nécessaire pour les éléments Li-ion. Le système de gestion de la batterie
   équilibre les éléments de manière autonome.
3. L'équilibre entre `power_gen` et `power_cons` devrait être surveillé à chaque orbite. Une marge
   de puissance négative persistante indique un problème de configuration ou une dégradation des performances du générateur solaire.
4. La télémesure du PCDU est échantillonnée à 1 Hz et incluse dans le paquet de servitude de l'EPS
   (SID=1).

## 8. Modes de défaillance

| Défaillance              | Détection                      | Réaction autonome                |
|--------------------------|--------------------------------|----------------------------------|
| Perte d'un panneau solaire (unique) | Courant du panneau = 0 pendant >60s | Délestage si la marge de puissance est négative |
| Dégradation d'un panneau solaire | Courant du panneau réduit par rapport au modèle | Avertissement à l'opérateur ; ajuster le bilan de puissance |
| Perte de plusieurs panneaux | power_gen total < power_cons | Délestage progressif, mode survie |
| Surchauffe de la batterie | bat_temp > 45 C               | Inhiber la charge, alerter       |
| Sous-tension du bus      | bus_voltage < 26.5 V           | Passage en mode urgence          |
| Disjonction d'une sortie PDM | Surveillance individuelle du courant | Une nouvelle tentative automatique, puis isolation |
| Défaillance de PDM-A     | Disjonctions de plusieurs sorties | Le sol commande le basculement sur PDM-B |

### 8.1 Dégradation et perte panneau par panneau

EOSAT-1 utilise cinq panneaux fixés sur la structure plus deux ailes déployables sur les faces +/-Y. La perte
d'un seul panneau ou d'une seule aile réduit la production de puissance totale selon l'élément
touché et l'attitude du moment. L'impact dépend de la face perdue :

| Élément perdu      | Impact                                                       |
|--------------------|--------------------------------------------------------------|
| Aile +Y ou -Y      | Impact fort : surface de production principale en orbite aube-crépuscule |
| Panneau de structure +Y ou -Y | Impact moyen à fort : faces de production principales |
| -Z (zénith)        | Impact moyen : face à exposition solaire significative      |
| +X ou -X           | Impact faible à moyen : faces de production secondaires     |
| +Z (nadir)         | Impact faible : reçoit principalement l'éclairement de l'albédo |

Les opérateurs devraient surveiller la télémesure de courant de chaque panneau et la comparer à la prédiction
du modèle solaire pour l'attitude courante. Un écart persistant supérieur à 20 % indique une dégradation
du panneau qui impose de réévaluer le bilan de puissance.

### 8.2 Seuils de délestage progressif

Lorsque l'état de charge de la batterie diminue, la FDIR de l'EPS applique un délestage progressif :

| Seuil de SoC  | Action                                              |
|---------------|-----------------------------------------------------|
| < 50 %         | Opérations de la charge utile inhibées              |
| < 35 %         | Délestage des charges non essentielles (AOCS en COARSE_SUN) |
| < 25 %         | Passage en mode survie                              |
| < 15 %         | Mode urgence (OBC + TTC uniquement)                 |

Voir `08_fdir.md` pour la matrice complète des réactions FDIR.

---

*Fin du document — EOSAT1-UM-EPS-002*
