# CTG-025 : Reprise après perte de capteur SCAO
**Sous-système :** AOCS
**Phase :** CONTINGENCY
**Révision :** 1.0
**Approuvé par :** Directeur des opérations de vol

## Objet
Traiter la défaillance d'un ou plusieurs capteurs du SCAO (senseurs stellaires, têtes de senseur
solaire grossier, magnétomètres). EOSAT-1 emporte des capteurs d'attitude redondants : deux senseurs stellaires
(ST1/ST2) et six têtes de senseur solaire grossier (+X, -X, +Y, -Y, +Z, -Z) ;
son magnétomètre unique n'a pas d'unité redondante. Cette procédure fournit une démarche systématique pour
déterminer quel capteur est défaillant, basculer sur les unités redondantes lorsqu'elles existent,
évaluer l'impact cumulé sur la capacité de détermination d'attitude et décider
si les capteurs restants permettent les opérations de mission ou imposent un repli
vers un mode de pointage dégradé.

Cette procédure est particulièrement utile en cas de pannes en cascade, lorsque plusieurs capteurs
tombent en panne successivement. Chaque panne est traitée séparément, mais l'effet cumulé
doit être évalué après chaque action de reprise.

## Prérequis
- [ ] La télémesure SCAO (SID 2) est reçue à >= 1 Hz
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Directeur de vol informé de l'anomalie de capteur d'attitude
- [ ] Alimentation de la plateforme nominale — `eps.bus_voltage` (0x0105) > 27.0 V
- [ ] La procédure CTG-002 (Reprise après anomalie SCAO) a été relue pour les voies d'escalade
- [ ] La procédure CTG-008 (Panne du senseur stellaire) a été relue pour les étapes propres aux ST

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| aocs.st1_status | 0x0240 | 2 (TRACKING) ou 4 (FAILED) |
| aocs.st1_num_stars | 0x0241 | > 3 en poursuite |
| aocs.st2_status | 0x0243 | 0 (OFF), 1 (BOOT), 2 (TRACKING) ou 4 (FAILED) |
| aocs.mode | 0x020F | Mode SCAO courant |
| aocs.att_error | 0x0217 | Surveiller — augmente avec la perte de capteurs |
| aocs.rate_roll | 0x0204 | Vitesse angulaire en roulis |
| aocs.rate_pitch | 0x0205 | Vitesse angulaire en tangage |
| aocs.rate_yaw | 0x0206 | Vitesse angulaire en lacet |
| aocs.css_valid | 0x0248 | Validité du vecteur Soleil CSS |
| aocs.css_px | 0x027A | Éclairement CSS de la face +X |
| aocs.css_mx | 0x027B | Éclairement CSS de la face -X |
| aocs.css_py | 0x027C | Éclairement CSS de la face +Y |
| aocs.css_my | 0x027D | Éclairement CSS de la face -Y |
| aocs.css_pz | 0x027E | Éclairement CSS de la face +Z |
| aocs.css_mz | 0x027F | Éclairement CSS de la face -Z |
| aocs.mag_x | 0x020B | Champ mesuré Bx, nT (unité 3 axes unique) |
| aocs.mag_y | 0x020C | Champ mesuré By, nT |
| aocs.mag_z | 0x020D | Champ mesuré Bz, nT |
| aocs.mag_field_total | 0x0277 | Norme du champ total, nT |
| aocs.mag_enabled | 0x025C | Magnétomètre valide/activé (0=off, 1=valid) |
| aocs.sun_body_x | 0x0220 | Vecteur Soleil, axe X satellite (composite CSS) |
| aocs.sun_body_y | 0x0221 | Vecteur Soleil, axe Y satellite (composite CSS) |
| aocs.sun_body_z | 0x0222 | Vecteur Soleil, axe Z satellite (composite CSS) |

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| ST2_POWER | 8 | 1 | 5 | Mise sous/hors tension du senseur stellaire 2 |
| ST_SELECT | 8 | 1 | 6 | Sélectionner le senseur stellaire principal (codage : 1=ST1, 2=ST2, 0 refusé) |
| ST1_POWER | 8 | 1 | 4 | Mise sous/hors tension du senseur stellaire 1 |
| S2_AOCS_MAGNETOMETER | 2 | 1 | — | Cycle d'alimentation du magnétomètre unique (équipement 0x0209) |
| AOCS_SET_MODE | 8 | 1 | 0 | Régler le mode SCAO |
| PAYLOAD_SET_MODE | 8 | 1 | 26 | Régler le mode de la charge utile (pour l'entrée en mode survie) |

## Déroulement

### Étape 1 : Évaluation initiale de l'état des capteurs
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander les données de servitude SCAO
**Verify:** `aocs.st1_status` (0x0240) — consigner l'état (0=OFF, 1=BOOT, 2=TRACKING, 3=BLIND, 4=FAILED)
**Verify:** `aocs.st1_num_stars` (0x0241) — consigner le nombre d'étoiles poursuivies
**Verify:** `aocs.st2_status` (0x0243) — consigner l'état
**Verify:** `aocs.css_valid` (0x0248) — consigner la validité CSS (1=valide)
**Verify:** `aocs.mag_enabled` (0x025C) — consigner la validité du magnétomètre (il n'y a
qu'UN SEUL magnétomètre ; aucune sélection d'unité n'existe)
**Verify:** `aocs.mode` (0x020F) — consigner le mode SCAO courant
**Verify:** `aocs.att_error` (0x0217) — consigner l'erreur d'attitude courante
**Action:** Documenter l'état de tous les capteurs pour établir lesquels sont sains et
lesquels sont défaillants ou dégradés.
**GO/NO-GO:** État de référence des capteurs établi — engager le traitement de la panne concernée.

### Étape 2 : Traitement d'une panne de senseur stellaire
**Condition :** `aocs.st1_status` (0x0240) = 4 (FAILED) ou `aocs.st1_num_stars` (0x0241) = 0

**Étape 2a — Vérifier la disponibilité de ST2 :**
**Verify:** `aocs.st2_status` (0x0243) — vérifier si ST2 est déjà actif
- Si ST2 = 2 (TRACKING) : la FDIR a basculé automatiquement. L'étape 2c s'applique.
- Si ST2 = 0 (OFF) : mise sous tension manuelle nécessaire. L'étape 2b s'applique.
- Si ST2 = 4 (FAILED) : les deux ST sont en panne. L'étape 5 s'applique directement.

**Étape 2b — Mettre ST2 sous tension et le sélectionner :**
**TC:** `ST2_POWER(on=1)` (Service 8, Subtype 1, func_id 5) — Commander la mise sous tension de ST2
**Action:** Attendre 60 s la fin de la séquence de démarrage.
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander les données de servitude SCAO
**Verify:** `aocs.st2_status` (0x0243) passe à 2 (TRACKING) en moins de 120 s
**Note:** Uniquement si la vérification précédente a confirmé TRACKING. Si ST2 n'a pas atteint
TRACKING, NE PAS envoyer cette TC — appliquer plutôt la section « Conduite à tenir hors nominal ».
**TC:** `ST_SELECT(unit=2)` (Service 8, Subtype 1, func_id 6) — sélectionner ST2 comme
senseur principal. LE CODAGE EST 1=ST1, 2=ST2 (0 est refusé) : l'ancien `unit=1` ici
SÉLECTIONNAIT SILENCIEUSEMENT ST1 — l'unité défaillante — alors que la carte visait ST2 (2026-08c)
**Verify:** `aocs.att_error` (0x0217) commence à diminuer en moins de 30 s

**Étape 2c — Isoler ST1 défaillant :**
**TC:** `ST1_POWER(on=0)` (Service 8, Subtype 1, func_id 4) — Mettre ST1 hors tension
**Verify:** `aocs.st1_num_stars` (0x0241) = 0 en moins de 5 s (`aocs.st1_status` peut rester à 4 = FAILED après la mise hors tension ; voir CTG-008, étape 4)
**Verify:** `aocs.att_error` (0x0217) < 1.0° avec ST2 fournissant l'attitude
**Action:** Consigner au journal : « ST1 FAILED — operating on ST2 only. No star tracker redundancy. »
**GO/NO-GO:** ST2 opérationnel et fournissant une attitude valide — traiter la panne
suivante le cas échéant. Si ST2 n'a pas atteint TRACKING, l'étape 5 s'applique.

### Étape 3 : Traitement d'une panne de tête CSS
**Condition :** Une ou plusieurs têtes CSS présentent des mesures anormales

**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander les données de servitude SCAO
**Verify:** Contrôler la valeur d'éclairement de chaque tête CSS :
- `aocs.css_px` (0x027A) — face +X
- `aocs.css_mx` (0x027B) — face -X
- `aocs.css_py` (0x027C) — face +Y
- `aocs.css_my` (0x027D) — face -Y
- `aocs.css_pz` (0x027E) — face +Z
- `aocs.css_mz` (0x027F) — face -Z

**Action:** Pour chaque face éclairée (face censée être exposée au Soleil compte tenu de
l'attitude courante), vérifier que la mesure CSS est plausible :
- une mesure de 0.0 sur une face qui devrait être éclairée indique une tête défaillante ;
- une mesure erratique ou figée indique une tête dégradée.

**Action:** Documenter la ou les têtes CSS défaillantes et la ou les faces concernées.
**Verify:** `aocs.css_valid` (0x0248) — toujours à 1 si le vecteur Soleil composite peut être calculé
à partir des têtes restantes.

**Évaluation de l'impact de la perte de têtes CSS :**
- 1 tête perdue : le vecteur Soleil composite est dégradé mais utilisable. La précision du vecteur Soleil
  tombe à environ 5-10 degrés pour certaines plages d'attitude.
- 2 têtes perdues sur des faces opposées (p. ex. +X et -X) : la détermination du vecteur Soleil selon
  cet axe est perdue. Le mode COARSE_SUN aura une précision réduite.
- 3 têtes perdues ou plus : le CSS peut être invalide. Vérifier `aocs.css_valid` (0x0248). S'il est invalide
  (= 0), le pointage solaire est impossible en phase de sortie d'éclipse.

**Note:** Une panne de tête CSS n'affecte pas le pointage fin (modes fondés sur les ST) mais
dégrade les performances du mode survie (COARSE_SUN repose sur le CSS).
**GO/NO-GO:** Dégradation du CSS évaluée. Si css_valid = 1, continuer. Si css_valid = 0
et que les deux ST sont en panne, l'étape 5 s'applique.

### Étape 4 : Traitement d'une panne de magnétomètre
**Condition :** `aocs.mag_enabled` (0x025C) = 0 ou mesures du magnétomètre invalides

**Remarque (2026-08c, décision du responsable) :** EO-Sat-1 emporte **UN SEUL** magnétomètre
3 axes (équipement S2 0x0209). Il n'y a ni unité B, ni télémesure de sélection,
ni `MAG_SELECT` — le gestionnaire bord de l'ancienne func 7 REFUSE désormais
avec 0x0007. L'ancienne reprise de l'étape 4, « basculer sur le magnétomètre redondant »,
était une fiction ; la reprise réaliste consiste en un cycle d'alimentation de l'unique unité, puis en une
décision de configuration dégradée si elle reste hors service.

**Étape 4a — Confirmer la panne :**
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander les données de servitude SCAO
**Verify:** `aocs.mag_x` (0x020B), `aocs.mag_y` (0x020C), `aocs.mag_z` (0x020D)
— toutes proches de zéro avec `aocs.mag_enabled` (0x025C) = 0 : confirme que l'unité est éteinte
ou en panne (les voies publient de vrais zéros lorsqu'elles sont invalides)
**Verify:** `aocs.mag_field_total` (0x0277) — la plage saine en LEO est
d'environ 25000-65000 nT ; une valeur proche de zéro confirme la panne

**Étape 4b — Effectuer un cycle d'alimentation de l'unité :**
**TC:** `S2_AOCS_MAGNETOMETER(device_id=521, state=0)` (Service 2, Subtype 1) — unité OFF
**Action:** Attendre 10 s.
**TC:** `S2_AOCS_MAGNETOMETER(device_id=521, state=1)` (Service 2, Subtype 1) — unité ON
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander les données de servitude SCAO
**Verify:** `aocs.mag_enabled` (0x025C) = 1 en moins de 30 s — unité rétablie
**Verify:** `aocs.mag_field_total` (0x0277) dans la plage attendue (25000-65000 nT)

**Note:** Les données du magnétomètre alimentent la chaîne d'attitude grossière, le DETUMBLE B-dot et
le déchargement du moment cinétique par magnétocoupleurs. Si le cycle d'alimentation ne rétablit pas l'unité,
il n'y a AUCUNE redondance : DETUMBLE sera refusé avec le code 0x0A20, la capacité de désaturation
est perdue et la mission se poursuit sur roues + ST, le moment cinétique n'étant géré que par
biais d'attitude — déclarer la configuration dégradée et émettre un
rapport d'anomalie satellite.

**GO/NO-GO:** Magnétomètre rétabli — ou configuration dégradée sans magnétomètre
déclarée — engager l'évaluation cumulée.

### Étape 5 : Évaluation cumulée des capteurs et choix du mode
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander les données de servitude SCAO
**Action:** Confronter les capteurs restants aux exigences de chaque mode :

**Le pointage fin (NOMINAL mode=4, pointage nadir) exige :**
- au moins un senseur stellaire en poursuite (état de ST1 ou ST2 = 2) ;
- le gyromètre opérationnel (vitesses angulaires corrigées du biais disponibles) ;
- le magnétomètre valide (pour la désaturation périodique) ;
- si toutes les exigences sont satisfaites : le pointage fin est disponible.

**Le pointage solaire grossier (COARSE_SUN, mode=3) exige :**
- le CSS valide (au moins 3-4 têtes CSS fournissant le vecteur Soleil composite) ;
- le magnétomètre valide (complément pour l'estimation d'attitude) ;
- si ces exigences sont satisfaites : le pointage grossier est disponible, mais la prise de vue est IMPOSSIBLE.

**L'amortissement seul (DETUMBLE, mode=2) exige :**
- le magnétomètre valide (pour la loi de commande B-dot) ;
- si cette exigence est satisfaite : l'amortissement des vitesses angulaires est possible. Aucune capacité de pointage.

**Note:** Selon les capteurs restants, choisir le meilleur mode disponible :
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0) — Si un ST est disponible : maintenir NOMINAL ou y revenir
**TC:** `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) — Si aucun ST mais CSS valide : passer en COARSE_SUN
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0) — Si aucun ST et CSS invalide : passer en DETUMBLE

**Verify:** `aocs.mode` (0x020F) = mode commandé en moins de 15 s
**Verify:** `aocs.att_error` (0x0217) — acceptable pour le mode choisi :
- NOMINAL : < 1.0°
- COARSE_SUN : < 5.0°
- DETUMBLE : vitesses angulaires < 1.0 °/s

**Note:** En cas de dégradation vers COARSE_SUN ou DETUMBLE, désactiver la charge utile :
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26)

**GO/NO-GO:** Meilleur mode disponible établi et stable. En cas de dégradation en deçà de
NOMINAL, informer le directeur de vol et la planification de mission de la capacité réduite.

### Étape 6 : Surveillance après reprise
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Surveiller la télémesure SCAO toutes les 60 s pendant 10 minutes
**Verify:** `aocs.att_error` (0x0217) — stable ou en amélioration
**Verify:** `aocs.rate_roll` (0x0204) < 0.1 °/s (pour les modes de pointage)
**Verify:** `aocs.rate_pitch` (0x0205) < 0.1 °/s
**Verify:** `aocs.rate_yaw` (0x0206) < 0.1 °/s
**Verify:** Le senseur stellaire actif (s'il existe) reste en poursuite — `aocs.st*_num_stars` > 3
**Verify:** Le magnétomètre continue de fournir des données valides
**Action:** Documenter l'état de tous les capteurs pour le rapport d'anomalie :
- capteurs défaillants et heure de chaque panne ;
- actions de reprise effectuées ;
- mode de fonctionnement courant et niveau de dégradation ;
- état de la redondance des capteurs restants.
**GO/NO-GO:** SCAO stable dans le mode choisi pendant 10 minutes — procédure terminée.

## Critères de vérification
- [ ] Tous les capteurs défaillants identifiés et documentés
- [ ] Capteurs redondants activés lorsqu'ils existent (ST2)
- [ ] Capteurs défaillants isolés (mis hors tension) pour éviter toute interférence
- [ ] SCAO fonctionnant dans le meilleur mode disponible pour les capteurs restants
- [ ] `aocs.att_error` (0x0217) dans les limites acceptables pour le mode courant
- [ ] Vitesses angulaires dans les limites pour le mode courant
- [ ] État de la redondance des capteurs restants documenté
- [ ] Aucun déclenchement du mode survie par la FDIR pendant la reprise

## Conduite à tenir hors nominal
- Si les deux senseurs stellaires sont en panne : le CSS est la seule référence d'attitude en phase éclairée.
  Commander `AOCS_SET_MODE(mode=3)` (COARSE_SUN). La prise de vue est impossible.
  Cette configuration dégrade la mission — faire remonter à l'équipe d'ingénierie.
- Si ST2 n'atteint pas TRACKING en moins de 120 s : effectuer un cycle d'alimentation de ST2 — `ST2_POWER(on=0)`,
  attendre 10 s, `ST2_POWER(on=1)`. En cas de nouvel échec, traiter comme une double panne de ST.
- Si le magnétomètre est en panne : le mode DETUMBLE est impossible (le B-dot exige les données magnétométriques).
  Les roues de réaction peuvent encore assurer le contrôle d'attitude si elles sont opérationnelles. Le moment cinétique ne peut pas
  être déchargé par les magnétocoupleurs. La situation est critique — prévoir une accumulation maîtrisée du moment cinétique.
- Si le CSS et le magnétomètre tombent en panne en éclipse : aucune référence d'attitude n'est disponible.
  Le satellite n'est pas contrôlé jusqu'à la sortie d'éclipse. Attendre la phase éclairée — le CSS devrait
  acquérir le vecteur Soleil si les têtes sont fonctionnelles. Commander `AOCS_SET_MODE(mode=2)` à
  l'avance, afin que DETUMBLE s'engage automatiquement au retour des données magnétométriques.
- Si l'erreur d'attitude dépasse 10° pendant le basculement de capteurs : la FDIR peut déclencher
  le mode survie de façon autonome. Laisser l'entrée en mode survie se faire, puis reprendre au moyen de CTG-002
  (Reprise après anomalie SCAO).
- Si le bilan de puissance ne permet pas la mise sous tension du capteur redondant : vérifier
  `eps.bat_soc` (0x0101). S'il est < 40 %, ne pas alimenter les deux senseurs stellaires simultanément.
  Fonctionner sur un seul ST jusqu'à ce que la batterie soit suffisante.
