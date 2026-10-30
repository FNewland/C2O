# CTG-026 : Reprise après blocage d'un actionneur SCAO
**Sous-système :** AOCS
**Phase :** CONTINGENCY
**Révision :** 1.0
**Approuvé par :** Directeur des opérations de vol

## Objet
Rétablir la situation après le grippage d'une roue de réaction dont le roulement s'est bloqué et qui
ne répond plus aux commandes de couple. À la différence d'une dégradation de roulement (perte
progressive de performance), un grippage est une panne soudaine et complète : la roue se fige à sa
vitesse courante ou tombe à une vitesse nulle, et la boucle de contrôle du SCAO ne peut plus utiliser cette
roue pour produire du couple. Les trois roues restantes doivent absorber le moment cinétique de la roue
perdue, ce qui, sans intervention, les mène vers la saturation. Cette procédure guide
l'opérateur à travers la détection, la confirmation, l'isolement de la roue, la reconfiguration en mode
trois roues et la gestion du moment cinétique, afin de rétablir un contrôle d'attitude stable.

EOSAT-1 emporte quatre roues de réaction en configuration pyramidale. Les opérations nominales
exigent les quatre roues pour des performances optimales, mais le système peut maintenir un contrôle
trois axes avec trois roues opérationnelles quelconques, au prix d'une précision de pointage légèrement dégradée.

## Prérequis
- [ ] La télémesure SCAO (SID 2) est reçue à >= 1 Hz
- [ ] Au moins trois roues de réaction étaient fonctionnelles avant le grippage
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Directeur de vol informé de l'anomalie SCAO
- [ ] Procédure CTG-007 (Anomalie de roue de réaction) relue pour référence

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| aocs.rw1_speed | 0x0207 | Surveiller — identifier la roue bloquée |
| aocs.rw2_speed | 0x0208 | Surveiller — identifier la roue bloquée |
| aocs.rw3_speed | 0x0209 | Surveiller — identifier la roue bloquée |
| aocs.rw4_speed | 0x020A | Surveiller — identifier la roue bloquée |
| aocs.rw1_temp | 0x0218 | Surveiller — le grippage provoque un échauffement |
| aocs.rw2_temp | 0x0219 | Surveiller — le grippage provoque un échauffement |
| aocs.rw3_temp | 0x021A | Surveiller — le grippage provoque un échauffement |
| aocs.rw4_temp | 0x021B | Surveiller — le grippage provoque un échauffement |
| aocs.mode | 0x020F | Mode SCAO courant |
| aocs.att_error | 0x0217 | Surveiller — peut augmenter pendant la reprise |
| aocs.rate_roll | 0x0204 | Vitesse angulaire en roulis |
| aocs.rate_pitch | 0x0205 | Vitesse angulaire en tangage |
| aocs.rate_yaw | 0x0206 | Vitesse angulaire en lacet |
| aocs.mag_x | 0x020B | Champ magnétique mesuré X (magnétomètre) |
| aocs.mag_y | 0x020C | Champ magnétique mesuré Y (magnétomètre) |
| aocs.mag_z | 0x020D | Champ magnétique mesuré Z (magnétomètre) |
| aocs.mag_enabled | 0x025C | Magnétomètre valide/activé (nécessaire à la désaturation) |

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| SET_PARAM | 20 | 1 | — | Régler un paramètre bord |
| AOCS_DISABLE_WHEEL | 8 | 1 | 2 | Désactiver (isoler) une roue de réaction — contrôle 3 sur 4 |
| AOCS_ENABLE_WHEEL | 8 | 1 | 3 | Réactiver une roue de réaction |
| AOCS_SET_MODE | 8 | 1 | 0 | Régler le mode SCAO |
| AOCS_DESATURATE | 8 | 1 | 1 | Commander le déchargement du moment cinétique par magnétocoupleurs |

## Déroulement

### Étape 1 : Détecter et identifier la roue bloquée
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander les données de servitude SCAO
**Verify:** Consigner toutes les vitesses de roue :
- `aocs.rw1_speed` (0x0207) — vitesse de RW-1 en tr/min
- `aocs.rw2_speed` (0x0208) — vitesse de RW-2 en tr/min
- `aocs.rw3_speed` (0x0209) — vitesse de RW-3 en tr/min
- `aocs.rw4_speed` (0x020A) — vitesse de RW-4 en tr/min
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Attendre 30 s et demander un second échantillon
**Action:** Comparer les deux échantillons. Une roue bloquée présente :
- une vitesse qui ne varie pas d'un échantillon à l'autre (figée à la vitesse de grippage) ;
- OU une vitesse tombée brutalement à 0 tr/min ;
- tandis que les trois autres roues divergent de plus en plus en vitesse pour compenser.
**Verify:** Consigner toutes les températures de roue :
- `aocs.rw1_temp` (0x0218), `aocs.rw2_temp` (0x0219)
- `aocs.rw3_temp` (0x021A), `aocs.rw4_temp` (0x021B)
**Action:** Une roue grippée présente une température élevée ou en hausse rapide, due au
frottement dans le roulement bloqué. Rapprocher la roue à vitesse figée de la roue chaude
pour confirmer le diagnostic de grippage.
**Verify:** `aocs.att_error` (0x0217) — consigner la valeur courante. Elle peut augmenter tandis que
la boucle de contrôle tente de commander la roue qui ne répond plus.
**GO/NO-GO:** Une seule roue identifiée comme bloquée (vitesse figée + température
en hausse). Noter l'indice de la roue (0-3 = RW-1 à RW-4). Si plusieurs roues sont
bloquées, passer à CTG-002, étape 7 (panne de plusieurs roues).

### Étape 2 : Désactiver la roue bloquée
**Note:** Désactiver la roue grippée pour la retirer de la boucle de contrôle :
**TC:** `AOCS_DISABLE_WHEEL(wheel_idx=N)` (Service 8, Subtype 1, func_id 2)
**Note:** N étant l'indice de la roue bloquée (0-3).
**Verify:** Attendre 10 s, puis demander les données de servitude SCAO : `HK_REQUEST(sid=2)`
**Verify:** La vitesse de la roue désactivée doit commencer à décroître (le frottement la ralentit
puisqu'aucun couple n'est appliqué). Remarque : si le roulement est complètement grippé, la vitesse peut
déjà être à 0.
**Verify:** `aocs.att_error` (0x0217) — surveiller une éventuelle hausse transitoire. Une hausse
jusqu'à 5° est acceptable pendant la transition, le temps que la boucle de contrôle s'adapte.
**Verify:** `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205),
`aocs.rate_yaw` (0x0206) — toutes les vitesses angulaires doivent rester inférieures à 1.0 °/s.
**Note:** Si les vitesses angulaires dépassent 1.0 °/s, commander immédiatement `AOCS_SET_MODE(mode=2)` (DETUMBLE)
pour obtenir une attitude sûre, puis poursuivre avec l'étape 3 depuis le mode DETUMBLE.
**GO/NO-GO:** Roue désactivée, vitesses angulaires du satellite bornées sous 1.0 °/s — engager
la reconfiguration à trois roues.

### Étape 3 : Commander le mode de contrôle à trois roues
**Note:** Il n'existe pas de télécommande distincte de mode trois roues. L'isolation 3 sur 4 est
`AOCS_DISABLE_WHEEL(wheel_idx=<N>)` (Service 8, Subtype 1, func_id 2), déjà envoyée à l'étape 2 ;
la boucle de contrôle fonctionne désormais sur les trois roues restantes. Rétablissement par `AOCS_ENABLE_WHEEL` (func_id 3), étape 7.
**Verify:** Attendre 15 s que la boucle de contrôle se reconfigure.
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander les données de servitude SCAO
**Verify:** `aocs.att_error` (0x0217) — doit commencer à converger. Objectif : < 2.0°
dans les 60 s suivant la reconfiguration.
**Verify:** Les vitesses des trois roues restantes s'ajustent — le moment cinétique est
redistribué sur les trois roues opérationnelles.
**Verify:** Aucune vitesse de roue restante ne dépasse 5000 tr/min (approche de la saturation).
**Note:** Le mode trois roues offre une précision de pointage légèrement réduite (typiquement
1.0-1.5° contre 0.5° avec quatre roues) et une capacité de stockage du moment cinétique réduite.
**GO/NO-GO:** Mode trois roues actif, erreur d'attitude convergeant sous 2.0° —
engager la gestion du moment cinétique.

### Étape 4 : Décharger le moment cinétique avec les magnétocoupleurs
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Vérifier l'état du moment cinétique des roues restantes
**Verify:** `aocs.rw1_speed` à `aocs.rw4_speed` (roues actives uniquement) — si une
roue active dépasse 3000 tr/min, une désaturation est nécessaire.
**Verify:** `aocs.mag_enabled` (0x025C) = 1 — le magnétomètre doit être opérationnel pour
le déchargement du moment cinétique par magnétocoupleurs.
**TC:** `AOCS_DESATURATE` (Service 8, Subtype 1, func_id 1) — Commander le déchargement du moment cinétique
**Verify:** Vitesses des roues actives tendant vers 0 tr/min en 120-300 s
**Verify:** `aocs.mtq_x_duty` (0x0258), `aocs.mtq_y_duty` (0x0259), `aocs.mtq_z_duty` (0x025A)
— les magnétocoupleurs sont pilotés (rapport cyclique non nul pendant le déchargement). 0x020B-0x020D sont les
axes du magnétomètre `aocs.mag_x/y/z`, et non des commandes des magnétocoupleurs.
**Verify:** `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205),
`aocs.rate_yaw` (0x0206) — toutes < 0.5 °/s pendant la manœuvre de désaturation
**Verify:** Aucune roue restante ne dépasse 5000 tr/min pendant la redistribution.
**Action:** Attendre la fin de la désaturation — toutes les roues actives sous 2000 tr/min.
**Note:** Avec trois roues seulement, l'enveloppe de moment cinétique est réduite. La désaturation
peut devoir être effectuée plus souvent (nominalement toutes les 3-4 orbites au lieu de
toutes les 6-8 orbites en mode quatre roues).
**GO/NO-GO:** Moment cinétique déchargé — toutes les roues actives < 2000 tr/min, vitesses
angulaires < 0.2 °/s — continuer.

### Étape 5 : Vérifier la stabilité du pointage en mode trois roues
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander les données de servitude SCAO — un échantillon toutes les 60 s pendant
5 minutes.
**Verify:** `aocs.att_error` (0x0217) < 1.5° de façon durable (tolérance assouplie par rapport à la
valeur nominale de 1.0° pour les opérations à trois roues)
**Verify:** `aocs.rate_roll` (0x0204) < 0.1 °/s
**Verify:** `aocs.rate_pitch` (0x0205) < 0.1 °/s
**Verify:** `aocs.rate_yaw` (0x0206) < 0.1 °/s
**Verify:** Températures de toutes les roues actives < 55 °C
**Verify:** Vitesses de toutes les roues actives < 4000 tr/min et stables
**Note:** Si le satellite est actuellement en mode DETUMBLE, tenter la transition vers NOMINAL (nadir) :
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0)
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL) en moins de 15 s
**Verify:** `aocs.att_error` (0x0217) converge sous 1.5° en moins de 120 s
**GO/NO-GO:** Performances de pointage acceptables pour les opérations de mission à trois roues —
engager la planification post-reprise.

### Étape 6 : Établir le plan d'opérations à trois roues
**Action:** Confirmer l'indice de la roue désactivée et le consigner dans le journal des anomalies.
**Action:** Mettre à jour les contraintes opérationnelles du mode trois roues :
- précision de pointage : assouplie à 1.5° (au lieu de 1.0°) ;
- fréquence de déchargement du moment cinétique : toutes les 3-4 orbites (au lieu de 6-8 orbites) ;
- vitesse de basculement maximale : réduite de 25 % pour éviter la saturation des roues pendant les manœuvres.
**Action:** Informer la planification de mission :
- la prise de vue reste possible, mais avec une précision de pointage réduite ;
- les manœuvres d'agilité (basculements de cible en cible) seront plus longues ;
- les créneaux de gestion du moment cinétique doivent être programmés plus fréquemment.
**Action:** Évaluer la possibilité de récupérer la roue :
- Grippage (roulement bloqué) : en général non récupérable en orbite. Prévoir des opérations
  permanentes à trois roues.
- Si la température revient à la normale après plusieurs orbites : le roulement s'est peut-être
  partiellement libéré. Une tentative de reprise exige l'autorisation du sol (voir l'étape 7).
**Verify:** Surveiller la température de la roue désactivée pendant les 2 orbites suivantes — si elle descend
sous 45 °C, signaler la roue pour une éventuelle évaluation de reprise.
**GO/NO-GO:** Plan d'opérations à trois roues établi — procédure terminée.

### Étape 7 : Tentative de reprise de la roue (sur autorisation du sol uniquement)
**Note:** Cette étape ne doit être tentée qu'après autorisation explicite de
l'équipe d'ingénierie au sol et au moins 2 orbites d'opérations stables à trois roues.
**Condition :** La température de la roue désactivée est revenue sous 45 °C, ce qui laisse penser
que le roulement n'est peut-être pas grippé de façon permanente.
**TC:** `AOCS_ENABLE_WHEEL(wheel_idx=N)` (Service 8, Subtype 1, func_id 3) — Réactiver la roue à basse vitesse
**Verify:** La roue commence à prendre de la vitesse en moins de 10 s
**Verify:** La vitesse de la roue atteint la valeur commandée sans à-coups (ni oscillation, ni calage)
**Verify:** La température de la roue n'augmente pas de plus de 5 °C pendant la montée en vitesse
**Action:** Surveiller pendant 5 minutes à la vitesse commandée.
**Verify:** Vitesse stable (pas de gigue > +/- 100 tr/min)
**Verify:** Température stable et < 50 °C
**Note:** En cas de reprise réussie, le contrôle à quatre roues est déjà rétabli : `AOCS_ENABLE_WHEEL`
suffit (il n'existe pas de paramètre `aocs.wheel_config` à écrire).
**Verify:** `aocs.att_error` (0x0217) s'améliore jusqu'à < 1.0° en moins de 120 s
**Note:** En cas d'échec de la reprise (calage, pic de température, oscillation) :
**TC:** `AOCS_DISABLE_WHEEL(wheel_idx=N)` (Service 8, Subtype 1, func_id 2) — Désactiver immédiatement la roue à nouveau
**Note:** Maintenir de façon permanente les opérations à trois roues.
**GO/NO-GO:** Si la reprise réussit — opérations à quatre roues rétablies. En cas d'échec — opérations
à trois roues confirmées comme configuration permanente.

## Critères de vérification
- [ ] Roue bloquée/grippée identifiée (RW-1/2/3/4) et documentée
- [ ] Roue défaillante désactivée et retirée de la boucle de contrôle
- [ ] Mode de contrôle à trois roues confirmé actif et stable
- [ ] `aocs.att_error` (0x0217) < 1.5° en NOMINAL (trois roues)
- [ ] Vitesses de toutes les roues actives < 4000 tr/min après désaturation
- [ ] Températures de toutes les roues actives < 55 °C
- [ ] Déchargement du moment cinétique mené à bien
- [ ] Plan d'opérations mis à jour pour les contraintes à trois roues
- [ ] Possibilité de reprise de la roue évaluée et documentée

## Conduite à tenir hors nominal
- Si une deuxième roue tombe en panne pendant cette procédure : commander immédiatement `AOCS_SET_MODE(mode=2)`
  (DETUMBLE). Un contrôle à deux roues ne permet pas le pointage trois axes.
  Passer à CTG-002, étape 7, et EMG-005 (Perte d'attitude). La situation est critique pour la mission.
- Si l'erreur d'attitude dépasse 10° pendant la désactivation de la roue : commander
  immédiatement `AOCS_SET_MODE(mode=3)` (COARSE_SUN). Attendre que les vitesses angulaires se stabilisent
  sous 0.5 °/s avant de tenter le mode trois roues.
- Si la désaturation est inefficace (roues toujours > 4000 tr/min après une tentative) :
  la géométrie orbitale ne permet peut-être pas un déchargement efficace du moment cinétique à la position actuelle.
  Prévoir une désaturation prolongée sur les 3 orbites suivantes, avec un contrôle continu
  par magnétocoupleurs.
- Si l'erreur de pointage à trois roues dépasse 3.0° : réduire les exigences de prise de vue
  et informer la planification de mission. La perte de la quatrième roue a pu révéler un
  biais de moment cinétique asymétrique qui exige une mise à jour des paramètres de contrôle.
- Si la température de la roue désactivée continue de monter au-delà de 70 °C : risque de dommage
  thermique aux composants voisins. Couper complètement la ligne d'alimentation de la roue :
  `EPS_POWER_OFF(line_index=7)` (func_id 20) — attention, cela coupe TOUTES les roues de
  cette ligne d'alimentation. Si les roues sont sur des lignes distinctes, isoler uniquement la roue concernée
  par SET_PARAM.
- Si le magnétomètre n'est pas valide (nécessaire à la désaturation) : EOSAT-1 n'a qu'un magnétomètre
  et aucune unité redondante — l'éteindre puis le rallumer via le dispositif S2 0x0209. S'il reste invalide,
  la désaturation par magnétocoupleurs est impossible. Le moment cinétique s'accumulera jusqu'à ce que
  la saturation des roues force le passage en mode survie.
