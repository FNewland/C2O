# SpaceCDF : des règles de conception à la place de l'IA

*2 novembre 2026. S'applique à SpaceCDF 2.x (`design/`).*

SpaceCDF fait ses choix de conception de référence avec **des scripts qui appliquent
des normes publiées et des valeurs par défaut d'ingénierie explicites**, et non avec
un modèle de langage. L'IA est **désactivée par défaut**. Elle n'est conservée que pour
trois tâches rédactionnelles facultatives, et ses productions passent par les mêmes
contrôles que le texte d'un étudiant.

Ce document recense chaque ancienne capacité d'IA, le moteur déterministe qui fait
désormais le travail, et les règles et sources qu'utilise chaque moteur.

## 1. Lire une étiquette de source

Chaque valeur de règle des fichiers de configuration cite une source. Une source est
de l'un des deux types suivants.

| Étiquette dans l'interface et l'API | Signification |
|---|---|
| Une référence documentaire, par exemple `ESA margin philosophy (SCI) 1.3 R-M1-7`, `CDS rev 14.1 2.3.7` ou `ECSS-E-ST-10-02C Rev.1 5.2.2.1` | Une **norme ou un guide cité**, lu et vérifié. La clause est indiquée. |
| `C2O default` | Un **choix de SpaceCDF** : pratique établie ou choix pédagogique. Ce **n'est pas** une citation de norme, même lorsqu'il s'en approche. Un enseignant peut le modifier. |

L'API renvoie `standard_ref` (la chaîne ci-dessus) et `c2o_default` (vrai ou faux)
pour chaque contrôle, de sorte qu'une page peut toujours indiquer de quel type il
s'agit. `GET /api/rules/catalogue` liste toutes les sources, avec `verified: true` pour
les documents vérifiés.

## 2. Anciennes capacités d'IA et ce qui les remplace

L'audit du 2 novembre 2026 a recensé 13 capacités d'IA. Aucune n'était appelée par
l'interface livrée, et la plupart faisaient double emploi avec un moteur existant.

| # | Ancienne capacité d'IA (clé `genai.yaml`) | Désormais réalisée par | Règles et sources | Statut |
|---|---|---|---|---|
| 1a | `design_advisor` : critique du besoin de mission | critères de la revue MCR (`gate_evaluator.py`, `gate_exit_criteria.yaml`), validateurs du besoin de mission, contrôles d'exigences ci-dessous | objectifs de revue de l'ECSS-M-ST-10C ; seuils C2O par défaut | **Règles.** IA conservée uniquement pour une critique rédigée du texte des parties prenantes (facultative). |
| 1b | `design_advisor` : recommandation de composants | `fit_gap_analysis.py`, `equipment.search_compatible_equipment`, `equipment_logic.check_interface_compatibility` / `check_rf_compatibility` | données de la base de connaissances ; ordre de priorité C2O | **Règles** (retirée de l'IA, HTTP 410) |
| 1c | `design_advisor` : génération du ConOps | ConOps par défaut (`studies._generate_default_conops`, `conops_executor.py`) | délais CDS 2.4.4/2.4.5 ; phases ECSS-M-ST-10C | **Règles** (retirée, 410) |
| 1d | `design_advisor` : questions libres | aucun | aucune | **IA conservée** (facultative) |
| 2 | `requirements_decomposition` | `requirement_engine.py` (gabarits d'exigences à partir des paramètres), **nouveau** `requirement_quality.py` | EARS (Mavin et al. 2009) ; sous-ensemble de règles INCOSE GtWR ; listes de mots C2O | **Règles** pour la structure et la qualité. IA conservée pour **reformuler des objectifs en texte libre en exigences « doit »**, toujours contrôlées par `requirement_quality`. |
| 3 | `consistency_checking` | `consistency_engine.py`, agent de conflits de niveau 2, **nouveaux** `margin_policy.py`, `cds_checks.py`, `gate_checks.py` | politique de marges ESA 1.3 ; CDS rev 14.1 ; ECSS-M-ST-10C | **Règles** (retirée, 410) |
| 4 | `trade_analysis` | `tabular_trade.py` (pondérations, seuils, sensibilité), `mission_trade.py`, `orbit_trade.py` | somme pondérée ; pondérations fixées par l'équipe | **Règles** (retirée, 410) |
| 5 | `cost_estimation` | `cost_engine.py` | relations d'estimation de coût du NASA CEH | **Règles** (supprimée) |
| 6 | `report_narrative` | gabarits `did_generator.py`, `semp_generator.py`, `docx_generator.py` | structures des DRD ECSS | **Gabarits.** IA conservée pour la **rédaction narrative et les synthèses** (facultative). |
| 7 | `fmea_generation` | `fmeca_closure.py`, **nouveau** `fmeca_library.py` + `configs/failure_modes.yaml` | méthode ECSS-Q-ST-30-02C ; bibliothèque et échelles C2O par défaut | **Règles** (supprimée) |
| 8 | `cad_scripting` | `physics_closure.place_elements`, `mass_properties.py` | géométrie issue du modèle | **Règles** (supprimée ; un export CadQuery par empilement de boîtes reste possible) |
| 9 | `wiring_generation` | `harness_designer.py` ; le générateur de liaisons (`interface_proposer.py`, `configs/interface_rules.yaml`) | natures d'interface de l'annexe E de l'ECSS-E-ST-10-24C ; matrice d'interfaces C2O par défaut | **Règles** (supprimée) |
| 10 | `fsw_generation` | `exporters/fsw/generator.py`, `mode_manager.py` | squelette déterministe | **Règles** (supprimée) |
| 11 | `aocs_design` | agent SCAO de niveau 1, `physics_closure.run_aocs_closure` | équations de couples perturbateurs du SMAD | **Règles** (supprimée) |
| 12 | `thermal_setup` | `thermal_network.py`, `thermal_transient.py` | modèle nodal | **Règles** (supprimée) |
| 13 | `structural_setup` | `structures.py`, agent structure de niveau 1 | facteurs de charge du lanceur issus de la base | **Règles** (supprimée) |

« Supprimée » signifie que le module de la capacité et son invite ont été retirés de
`packages/spacecdf-ai`. « Retirée, 410 » signifie que `/api/ai/ask` répond HTTP 410
pour ce nom et indique le point d'accès qui l'a remplacée.

## 3. Les moteurs déterministes

Tous les moteurs sont des fonctions pures de `packages/spacecdf-server/src/spacecdf_server/services/`.
Ils lisent des fichiers YAML de `design/configs/`. Le serveur valide ces fichiers au
démarrage (`rule_config.py`) : un identifiant de source inconnu, une valeur manquante
ou une expression régulière erronée est journalisé, affiché par `/api/rules/catalogue`,
et les points d'accès des règles refusent de s'exécuter sur le fichier défectueux
(HTTP 500 avec les motifs).

### 3.1 Politique de marges (`margin_policy.py`, `configs/margin_policy.yaml`)

| Règle | Valeur | Source |
|---|---|---|
| Marge de maturité des équipements, catégorie A ou B (sur étagère) | 5 % | ESA margin philosophy 1.3, R-M1-4 / R-M2-4 (masse), R-P-11..13 (puissance) |
| Catégorie C (modification mineure) | 10 % | idem |
| Catégorie D (nouvelle conception ou modification majeure) | 20 % | idem |
| Catégorie déduite du TRL et de l'héritage (TRL ≥ 8 avec héritage → A ; TRL ≥ 8 → B ; TRL ≥ 6 → C ; sinon D ; ni pièce de la base ni TRL → D) | — | **C2O default** |
| Marge système en masse | 20 % de la masse sèche nominale | ESA 1.3, 2.1.1 R-M1-1 |
| Harnais | 5 % de la masse sèche nominale | ESA 1.3, R-M1-7 |
| Résidus d'ergol | 2 % | ESA 1.3, R-M1-6 |
| Volume des réservoirs | +10 % | ESA 1.3, R-M1-10 |
| Marge système en puissance | 20 % | ESA 1.3, R-P-3 |
| ΔV, manœuvres calculées / maintien d'orbite / contrôle d'attitude | 5 % / 100 % / 100 % | ESA 1.3, R-DV-11 / 12 / 13 |
| Classe de ΔV de chaque paramètre SpaceCDF | — | **C2O default** |
| Mémoire vive embarquée | ≤ 50 % utilisée | ESA 1.3, R-SW-1 (« marge ≥ 50 % », lue comme la moitié de la capacité libre) |
| Charge de pointe du processeur | ≤ 50 % | ESA 1.3, R-SW-2 |
| Marge de stockage en mémoire de masse | 50 % | **C2O default** (calquée sur la règle de la mémoire vive) |
| Marge de rejet thermique | 50 % | ESA 1.3, R-T-2 |

Le cumul utilise **le niveau le plus détaillé qui porte une valeur**. L'estimation d'un
sous-système est remplacée par ses composants dès que l'un d'eux a une masse. Les
éléments du segment sol sont exclus. La masse limite est la limite du CDS pour le
facteur de forme, à défaut la masse cible de l'étude.

*Remarque.* L'ancien `ecss_margin_enforcer.py` (page Phase/ECSS) utilise encore des
tables par phase étiquetées « ECSS-E-HB-10-02A §5.2 ». Cette attribution n'a pas pu
être vérifiée ; considérer ces tables comme des valeurs C2O par défaut jusqu'à
vérification.

### 3.2 Contrôles de la CubeSat Design Specification (`cds_checks.py`, `configs/cds_rules.yaml`)

Source : Cal Poly CubeSat Design Specification rev 14.1 (2022-02-09).

| Contrôle | Règle | Clause du CDS |
|---|---|---|
| Masse par facteur de forme | 1U 2,00 kg … 3U 6,00 kg, 6U 12,00 kg, 12U 24,00 kg (typique ; le déployeur peut différer) | 2.2.10, tableau 1 |
| Centre de gravité | dans la boîte du tableau 2 (p. ex. 3U ±2/±2/±7 cm) ; contrôlé quand chaque unité massive a une position | 2.2.11, tableau 2 |
| Interrupteur de déploiement | ≥ 1 | 2.3.2 |
| Goupille RBF | présente | 2.3.4 / 2.3.5 |
| Inhibitions RF | ≥ 3 indépendantes, si la conception comporte un émetteur (une minuterie ne compte pas) | 2.3.7 |
| Inhibitions des déployables | ≥ 3, si la conception comporte un déployable | 2.3.8 |
| Inhibitions de la propulsion | ≥ 3, si la conception comporte une propulsion | 2.1.4 |
| Délai des déployables | ≥ 30 min après la séparation | 2.4.4 |
| Délai RF | ≥ 45 min après la séparation | 2.4.5 |
| Dépassement | ≤ 6,5 mm du plan des rails | 2.2.3 |
| Dégazage | TML ≤ 1,0 %, CVCM ≤ 0,1 % | 2.1.7 |

La façon dont SpaceCDF trouve les preuves est une **convention C2O**. Il lit les
liaisons proposées ou acceptées de type `electrical_signal` (les liaisons rejetées
sont ignorées). Une liaison `inhibit` qui aboutit à un émetteur, ou au sous-système
qui le contient, compte pour `properties.inhibit_count` inhibitions RF et fournit son
`properties.delay_min`. Une liaison `release` vers un déployable compte de la même
manière pour les déployables. Les liaisons de sous-type `deployment_switch` et `rbf`
comptent pour ces dispositifs. Ce sont les liaisons que crée le générateur de liaisons
(§3.7). Un élément peut aussi déclarer des valeurs dans `performance.cds`, par exemple
`{"rf_inhibits": 3, "rbf": true, "rf_delay_min": 45, "tml_percent": 0.4}`. Un
déployable est reconnu par le champ `deployment` de la base (`body_mounted` n'est pas
un déployable), à défaut par son nom. Si rien n'est déclaré, le contrôle indique
**à surveiller, non déclaré**. Il n'indique **non conforme** que lorsqu'une valeur
déclarée enfreint la règle.

### 3.3 Qualité des exigences (`requirement_quality.py`, `configs/requirement_rules.yaml`)

**Gabarit EARS** (Mavin, Wilkinson, Harwood, Novak, RE'09, IEEE, DOI 10.1109/RE.2009.9) :
permanent, piloté par état (*While*), piloté par événement (*When*), option
(*Where*), comportement indésirable (*If … then*), complexe. Les mots-clés français
(*Tant que*, *Lorsque*, *Si … alors*, *Là où*) sont une **adaptation C2O**.

**Sous-ensemble INCOSE GtWR figé.** La numérotation des règles suit la fiche de
référence rapide communautaire (source secondaire). Les listes de mots sont des
**valeurs C2O par défaut**.

| Id | Règle | Gravité |
|---|---|---|
| R-MODAL | une obligation avec *shall* / *doit* | erreur |
| R18-SINGLE | un seul *doit* par exigence | erreur |
| R7-VAGUE | termes vagues (*adéquat, rapide, convivial …*) | erreur |
| R8-ESCAPE | clauses échappatoires (*si possible, le cas échéant …*) | erreur |
| R9-OPEN | clauses ouvertes (*notamment, etc.*) | avertissement |
| R19-COMBINATOR | *et/ou, à moins que, sinon* | avertissement |
| R24-PRONOUN | pronoms (*il, elle, ceci …*) | avertissement |
| R26-ABSOLUTE | absolus (*toujours, jamais, 100 %*) | avertissement |
| R6-UNITS | un nombre sans unité | avertissement |
| C2O-TBD | points ouverts (TBD, TBC, TBR) | avertissement (**C2O default**) |
| R2-PASSIVE | voix passive avec complément d'agent (*doit être … par*) | information |
| R17-SLASH | « / » entre des mots | information |
| R20-PURPOSE | propositions de but (*afin de, pour que*) | information |
| R33-TOLERANCE | une valeur mesurée sans borne ni tolérance | information |

Une exigence qui comporte une erreur est **non conforme** et doit être réécrite avant
d'entrer dans un référentiel.

### 3.4 Méthodes de vérification par défaut (`verification_defaults.py`)

L'ECSS-E-ST-10-02C Rev.1 définit quatre méthodes : essai (y compris démonstration),
analyse (y compris similarité), revue de conception et inspection (4.2.2). Elle exige
aussi une **évaluation des risques pour toute exigence vérifiée uniquement par analyse
ou par revue de conception** (5.2.2.1). SpaceCDF signale ces exigences.

La correspondance entre type et méthode est une **valeur C2O par défaut**. Elle
s'applique d'abord selon le paramètre de seuil, puis selon des mots-clés.

| Type | Reconnu par | Par défaut |
|---|---|---|
| Bilan, marge ou durée de vie | paramètres `mass.`, `power.`, `systems.`, `orbit.`, `propulsion.` … ; *marge, durée de vie, fiabilité, désorbitation* | A |
| Performance ou fonction | `link.`, `data.`, `aocs.`, `payload.` … ; *débit, pointer, déployer, imager, résister …* | T |
| Conformité ou documentation | *conforme, conformément à, ITU, licence, norme* | R |
| Caractéristique physique ou fabrication | *dimension, enveloppe, étiquette, connecteur, matériau* | I |
| Tout le reste | — | A |

`POST …/rules/verification-defaults/apply` ne remplit que les méthodes **vides**. Il
n'écrase jamais le choix du concepteur.

### 3.5 Squelette d'AMDEC (`fmeca_library.py`, `configs/failure_modes.yaml`)

La méthode suit l'ECSS-Q-ST-30-02C. La bibliothèque est une **valeur C2O par défaut**
compilée à partir de la pratique CubeSat courante : batterie, EPS, générateur
solaire, OBC, émetteur-récepteur, antenne, roue de réaction, viseur d'étoiles,
magnétocoupleur, capteur solaire, GNSS, propulsion, matériel thermique, structure,
charge utile, et un mode générique. Les échelles de gravité, d'occurrence et de
détection de 1–5 sont aussi des valeurs C2O par défaut (l'échelle propre à la norme
n'était pas disponible pour vérification). Chaque élément est associé par sa catégorie
dans la base, puis par son nom, puis par son domaine. Trois ajustements s'appliquent
par élément :

- la redondance abaisse la gravité de 1 ;
- un TRL < 6 relève l'occurrence de 1 ;
- une liaison `data` (télémesure) abaisse la détection de 1.

Une ligne est un **point de défaillance unique** quand la gravité est ≥ 4 sans
redondance. Elle est **critique** quand le RPN est ≥ 60 (C2O default).

### 3.6 Contrôles des jalons de revue (`gate_checks.py`)

Pour chaque jalon, les contrôles calculés suivent les objectifs de revue de
l'ECSS-M-ST-10C Rev.1 (SRR 4.4.3.4.3 ; PDR 4.4.3.4.4 : arbre produit, arbre de
spécifications et plan de vérification publiés). Les moteurs de règles les alimentent :

| Jalon | Contrôles |
|---|---|
| MCR | arbre produit |
| SRR | arbre de spécifications ; qualité des exigences (≥ 80 % sans erreur, **C2O default**) ; une méthode de vérification pour chaque exigence ; marges |
| PDR | arbre produit avec composants ; arbre de spécifications avec exigences de sous-système dérivées ; qualité des exigences (100 %) ; méthodes de vérification ; signalements A/R seulement ; marges ; CDS ; points de défaillance uniques de l'AMDEC |

Les critères de `gate_exit_criteria.yaml` marqués `manual` ou `hybrid` reçoivent des
**preuves calculées** lorsque le modèle peut y répondre. Par exemple, SRR-EC-08 est
évalué à partir du TRL de chaque composant. Le relecteur garde la décision finale.
Le critère d'interfaces PDR-EC-02 est évalué par le service de complétude des
interfaces (voir §3.7).

### 3.7 Liaisons attendues entre éléments

Le générateur de liaisons (`interface_proposer.py`, `configs/interface_rules.yaml`)
crée les liaisons attendues de TM/TC, d'alimentation, RF, mécaniques, thermiques, de
synchronisation, de fluides et de signaux. Il utilise les natures d'interface de
l'annexe E de l'ECSS-E-ST-10-24C. La matrice d'interfaces par défaut est elle-même une
**valeur C2O par défaut**, pas une norme. Chaque proposition porte sa `rationale` et
sa `standard_ref`, et le concepteur l'accepte, la modifie ou la rejette. Les règles
sont décrites dans l'en-tête de ce fichier.

## 4. Où l'IA reste, et comment elle est encadrée

| Capacité conservée | Nom `/api/ai` | Pourquoi un script ne peut pas le faire |
|---|---|---|
| `design_advisor` | `critique_need`, `general` | Lire et critiquer le texte libre des parties prenantes ; questions ouvertes |
| `requirements_decomposition` | `write_requirements` | Reformuler des objectifs en texte libre en exigences « doit » bien rédigées |
| `report_narrative` | `narrative` | Rédaction de type synthèse |

- **Désactivée par défaut.** Dans `configs/genai.yaml`, la valeur livrée est
  `enabled: false`.
- **Un seul interrupteur général.** Quand `enabled` vaut faux ou que la capacité est
  désactivée, chaque point d'accès `/api/ai` répond **503** avant tout appel à un
  modèle. Cela vaut pour le service `spacecdf-ai` comme pour l'ancien chemin direct,
  quelle que soit la clé d'API définie dans l'environnement ou envoyée dans
  `X-API-Key`. Avant cette correction, l'ancien chemin s'exécutait dès qu'une clé était
  présente.
- **Jamais obligatoire.** Aucun flux de travail, jalon ou export n'appelle l'IA.
- **Toujours contrôlée.** Chaque réponse de l'IA est renvoyée avec `rule_checks`.
  Chaque exigence proposée, et chaque phrase contenant *shall* ou *doit* dans un texte
  rédigé, est contrôlée par EARS et le sous-ensemble INCOSE. Les énoncés comportant une
  erreur sont marqués `needs_revision`.
- **Ces trois-là seulement.** `spacecdf_ai.config.RETAINED_CAPABILITIES` contient la
  liste. Tout autre nom est refusé, même si `genai.yaml` l'active.

Défauts corrigés dans le chemin de l'IA : le `context` HTTP n'atteignait aucune
capacité (il est maintenant réparti dans les arguments de la capacité) ; `max_tokens`
était ignoré (il est maintenant transmis et plafonné par `budget.max_tokens_per_call`) ;
le contexte des interfaces lisait des clés inexistantes (désormais `from_element_id`,
`to_element_id`, `interface_type`).

## 5. Points d'accès

| Méthode et chemin | Renvoie |
|---|---|
| `GET /api/rules/catalogue` | fichiers de règles, sources (citées ou C2O default), erreurs de validation, contrôles d'exigences |
| `POST /api/rules/requirement-quality` `{texts, language?}` | contrôles des textes en cours de saisie |
| `GET /api/studies/{sid}/rules/margins?form_factor=` | cumul de masse et de puissance avec marges, ΔV, traitement de données, contrôles |
| `GET /api/studies/{sid}/rules/cds?form_factor=` | contrôles du CDS et preuves utilisées |
| `GET /api/studies/{sid}/rules/requirements-quality` | une ligne par exigence : gabarit EARS, constats, score |
| `GET /api/studies/{sid}/rules/verification-defaults` | méthode par défaut, méthode actuelle, signalement d'évaluation des risques |
| `POST /api/studies/{sid}/rules/verification-defaults/apply` | remplit les méthodes vides |
| `GET /api/studies/{sid}/rules/fmeca-skeleton` | lignes d'AMDEC (texte EN/FR), points uniques, lignes critiques |
| `GET /api/studies/{sid}/rules/gates/{MCR\|SRR\|PDR}` | critères du jalon, contrôles calculés, preuves calculées |
| `GET /api/studies/{sid}/rules/summary` | un résumé par moteur |

Chaque contrôle a la forme `{id, label{en,fr}, status : pass|warn|fail|not_evaluated, severity :
nominal|caution|alarm|info, detail{en,fr}, standard_ref, c2o_default, source, …}`.

## 6. Modifier une valeur par défaut

1. Modifier la valeur dans le fichier YAML de `design/configs/`. Conserver son
   `source:`. Si la nouvelle valeur est votre propre choix, indiquer
   `source: c2o_default`.
2. Redémarrer le serveur. La validation au démarrage signale toute erreur.
3. Exécuter `pytest tests/test_services/test_rule_engines.py` pour voir quels nombres
   figés ont changé.

## 7. Non vérifié, à contrôler avant de le citer comme norme

- Les échelles de gravité et de probabilité et le seuil de criticité de
  l'ECSS-Q-ST-30-02C (la bibliothèque utilise des échelles C2O de 1–5).
- La numérotation des règles INCOSE GtWR (tirée d'une fiche de référence rapide
  secondaire ; figer une version du guide).
- Les valeurs de marge de liaison de l'ECSS-E-ST-50-05C et les marges par phase de
  l'ECSS-E-HB-10-02A utilisées par `ecss_margin_enforcer.py`.
- Les limites propres à chaque déployeur (masse, « tuna can », rails), qui
  l'emportent sur les valeurs typiques du CDS.
- La matrice d'interfaces attendues (`interface_rules.yaml`) est une pratique établie,
  pas une norme.
