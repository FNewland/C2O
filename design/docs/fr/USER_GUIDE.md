# Guide de l'utilisateur de SpaceCDF

## Vue d'ensemble

SpaceCDF est un centre de conception concourante assisté par l'IA pour la conception de missions spatiales. Il vous accompagne de la définition du problème jusqu'à une conception de CubeSat complète et vérifiée, assortie d'une documentation conforme aux normes ECSS.

---

## Prise en main

### Installation

**Prérequis :** Python 3.11+, Node.js 18+

```bash
git clone https://github.com/FNewland/SpaceCDF.git
cd SpaceCDF

# Backend
pip install -e packages/spacecdf-common
pip install -e packages/spacecdf-agents
pip install -e packages/spacecdf-kb
pip install -e packages/spacecdf-server
uvicorn spacecdf_server.app:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Ouvrez http://localhost:5173 dans votre navigateur.

### Connexion à une instance distante

Modifiez `frontend/vite.config.ts` et changez la cible du proxy :
```javascript
proxy: { '/api': 'http://REMOTE_HOST:8000' }
```

---

## Déroulement

### Étape 1 : besoin de mission

1. Cliquez sur **Step 1 (Need)** (besoin) dans la barre d'étapes à gauche
2. Saisissez votre **énoncé du problème** (le QUOI, pas le COMMENT)
3. Ajoutez les **parties prenantes** avec leurs rôles et leurs besoins
4. Définissez des **objectifs** assortis de critères de réussite mesurables
5. L'outil détecte automatiquement le type de mission à partir des mots-clés des objectifs

### Étape 2 : exploration de concepts

1. Cliquez sur **Step 2 (Concept)**
2. Saisissez les paramètres du compromis : GSD, revisite, couverture, latence, budget
3. Cliquez sur **« Lancer l'analyse »** (Run Analysis) pour évaluer les solutions spatiales et non spatiales
4. Examinez les résultats notés → l'outil indique si une solution spatiale se justifie

### Étape 3 : exigences

1. Cliquez sur **Step 3 (Requirements)** (exigences)
2. **Orbit Advisor** (assistant orbite) : saisissez les objectifs, cliquez sur « Compute » (calculer) → orbites candidates notées. Cliquez sur « Use » (utiliser) pour appliquer.
3. **Class Advisor** (assistant de classe) : saisissez les paramètres connus (tous facultatifs). Cliquez sur « Compute » → recommandation de classe de satellite.
4. Renseignez dans le formulaire les paramètres d'orbite, de charge utile et de mission
5. Cliquez sur **« Run Design (solo) »** (lancer la conception en solo) → 20 agents font converger la conception

### Étape 4 : phase de conception

Une fois la conception lancée, l'outil bascule vers l'espace de conception à onglets, organisé en 5 groupes :

**Design (conception) :** Dashboard (tableau de bord), ConOps, Functions (fonctions), Requirements (exigences), Interfaces
**Analysis (analyse) :** Link Budget (bilan de liaison), Trade Studies (études de compromis), Optimizer (optimiseur), Cost (coût)
**Verify (vérifier) :** Compliance (conformité), V&V Matrix (matrice V&V), Gate Review (revue de jalon)
**Team (équipe) :** Positions (postes), Q&A (questions-réponses)
**Data (données) :** Exports, Parametric (paramétrique), Changes (modifications), Help (aide)

---

## Fonctionnalités principales

### Dashboard (tableau de bord)

La vue principale de conception affiche :
- **Cartes d'indicateurs clés (KPI) :** marge de masse, marge de puissance, marge de liaison, coût, durabilité, fiabilité, conflits
- Les graphiques **cascade de masse** et **profil de puissance**
- **Budget Breakdown** (ventilation des bilans) : masse et puissance par sous-système, avec allocations modifiables
- **Bilans d'ingénierie :** pointage (RSS), données (flux de la chaîne de traitement), temps (chronologie de l'orbite)
- **Spectrum Selector** (sélecteur de spectre) : choix du type de licence et de la bande de fréquences
- **Launch Selector** (sélecteur de lancement) : choix d'un fournisseur avec mise à jour en direct de l'allocation de masse
- **ECSS Margin Enforcement** (application des marges ECSS) : vérification des marges de chaque domaine par rapport à la politique

### Navigateur d'équipements

Cliquez sur « Équipements » (Equipment) dans la barre d'en-tête :
- **18 catégories** regroupées par domaine (puissance, AOCS, communications, propulsion, structure, données, thermique, intégration)
- **Annotations de besoin :** point bleu = requis, cercle = facultatif, grisé = inutile
- **Sélection multiple :** sélection de plusieurs éléments par catégorie (p. ex. 4 roues de réaction)
- **Compatibilité RF :** avertissement en cas de sélection d'un transpondeur et d'une antenne de bandes incompatibles
- **Barre de bilan en direct :** totaux cumulés de masse, de puissance et de coût
- **Mode comparaison :** comparaison côte à côte de 3 composants au plus

### Études de compromis

Deux modes :
- **Parametric Sweep** (balayage paramétrique) : faire varier un paramètre et observer son effet sur les indicateurs clés (graphique)
- **Tabular Trade** (compromis tabulaire) : définir des critères pondérés, ajouter des options, noter de façon quantitative ou qualitative (faible/moyen/élevé), consulter le classement obtenu

### Outil de bilan de liaison

Cascade interactive complète : puissance d'émission → gain d'antenne → pertes → affaiblissement en espace libre (FSPL) → pertes atmosphériques, de dépointage et de polarisation → gain en réception → G/T → C/N₀ → Eb/N₀ → marge. Chaque terme est modifiable, et la marge est codée par couleur.

### Optimiseur

- **Objectif unique :** minimiser la masse ou le coût, ou maximiser la marge de liaison
- **Pareto (NSGA-II) :** multiobjectif, jusqu'à 10 objectifs
- **Prise en compte du type de mission :** variables filtrées automatiquement selon la mission (pas de variables de propulsion sans propulsion)
- **Sensibilité (Morris) :** classe les paramètres selon leur influence sur l'objectif

### Exports

Génère plus de 18 types de documents :
- **ECSS :** MRD, TS, IRD, SEMP, RMP, ConOps, VP, plan d'essais
- **Réglementaires :** API de l'UIT, coordination IARU, LSTS, contrôle des exportations, CUPEEA, rapport de fin de vie
- **Données de conception :** données du modèle paramétrique, rapports cycliques, contrôle de cohérence, application des marges

### Réactivité entre outils

- **Design State Bar** (barre d'état de la conception) : signale que la conception est périmée après toute modification de paramètre
- **Auto-Reconverge** (reconvergence automatique) : option facultative → relance automatiquement la conception après chaque modification
- **Conflict Review** (examen des conflits) : une fenêtre modale s'ouvre lorsque des conflits critiques sont détectés ; leur résolution est obligatoire
- **Impact Preview** (aperçu de l'impact) : montre quels agents et quels bilans une modification affectera, avant de l'accepter
- **Change Audit** (journal des modifications) : historique complet avec possibilité d'annulation

### Onglet Analyses (atelier)

L'atelier par niveau (Level Workbench) comporte un onglet **Analyses** (panneau inférieur, après **Décider**). Il affiche une carte par analyse d'ingénierie, avec l'heure de la dernière exécution, un badge `ok` / `stale` / `failed` (stale = le modèle a changé depuis l'exécution), deux ou trois valeurs clés tirées du résumé de l'exécution, le nombre de conflits ouverts qu'elle a levés et un bouton **Run** (exécuter). Cliquez sur une carte pour ouvrir son panneau complet sous la grille ; le bouton **Options ▸** ouvre la comparaison des options A/B. Une liste **Conflicts** (conflits) en bas fusionne les conflits de la boucle de conception avec ceux de chaque analyse (badge de source, gravité, pastilles d'éléments — cliquez sur l'une d'elles pour cibler cet élément dans **Blocs** —, correction suggérée et **Resolve** (résoudre)).

L'option de conception active se choisit dans le sélecteur **Option** de la barre de présence (zone en haut à gauche, à côté de l'état de l'IA). Chaque exécution et chaque lecture de paramètre sur cet onglet portent sur cette option ; le référentiel n'envoie aucune option.

Ce dont chaque analyse a besoin dans le modèle pour que son résultat ait un sens :

| Carte | Lit | Écrit (racine de la mission) | Nécessite |
|------|-------|----------------------|-------|
| Design loop (boucle de conception) | exigences, sous-systèmes par domaine | paramètres des agents, bilans | une racine de mission portant des exigences d'orbite, de charge utile et de durée de vie, et des sous-systèmes dotés d'un `subsystem_domain` |
| Mission simulation (simulation de mission) | modes opérationnels, batterie `capacity_wh`, générateur `sa_power_eol_w`, charge utile `data_rate_bps`, orbite | `sim_min_soc_pct`, `sim_energy_balance_wh_per_orbit`, `sim_data_backlog_end_gb`, `sim_time_in_safe_pct` | au moins un mode opérationnel (ConOps) avec une puissance et un débit ; une batterie et un générateur solaire sous le sous-système de puissance |
| Ground segment (segment sol) | stations sol sélectionnées, bande / débit TT&C, orbite, données générées | `gs_contact_min_per_day`, `gs_data_return_gb_per_day`, `gs_data_generated_gb_per_day`, `gs_min_link_margin_db` | une ou plusieurs stations sol sélectionnées dans le catalogue (panneau Ground segment → ajouter), une radio dans le sous-système de communications, dans une bande que la station prend en charge |
| Physics (physique) | masses / dimensions / positions des composants dans le satellite, roue de réaction, exigence de pointage, dissipations | propriétés de masse `mp_*`, couples `aocs_*` et marge de roue, `thermal_worst_margin_c` | des masses sur les composants ; des positions (panneau Physics → placement, ou placement automatique dans l'enveloppe de la structure) ; une roue ou une exigence de pointage pour la partie AOCS ; des dissipations pour la partie thermique |
| V&V | exigences avec méthode de vérification et paramètres de seuil | `vv_closure_pct`, `vv_items_*` | des exigences portant un seuil (`param op value`) ; les exécutions d'analyse clôturent ensuite automatiquement ces éléments |
| FMECA (AMDEC) | composants avec domaine, quantité / redondance, fonctions allouées | `fmeca_max_rpn`, `fmeca_single_point_failures` | des fonctions allouées aux composants (onglet **Fonctions** (Functions)) afin de repérer les points de défaillance unique sur les fonctions critiques |

La barre de marges située sous la barre d'état s'enrichit des indicateurs **SoC** (état de charge minimal de la batterie issu de la simulation, comparé à un plancher de 20 %) et **Data** (fraction des données générées effectivement rapatriées) dès que ces paramètres existent sur la racine de la mission.

---

## Modification des données paramétriques

Les modèles de dimensionnement de l'outil reposent sur des données étalonnées pour les CubeSats. Pour les consulter et les modifier :

1. Ouvrez l'onglet **Paramétrique** (Parametric)
2. Quatre sous-onglets : Mass Fractions (fractions de masse), Cost Fractions (fractions de coût), Power Duty Cycles (rapports cycliques de puissance), SA Power (puissance du générateur solaire)
3. Les valeurs sont données par classe de satellite (nano, micro, petit, moyen, grand)
4. Les sources sont citées à côté de chaque tableau

Pour modifier directement les données sources : `packages/spacecdf-common/src/spacecdf_common/physics/heritage_mass.py`

---

## Mise à jour de la base de données d'équipements

Les données des composants se trouvent dans des fichiers YAML : `packages/spacecdf-kb/src/spacecdf_kb/data/components/`

Pour ajouter un composant, ajoutez une entrée au fichier YAML approprié :
```yaml
- id: unique-id
  name: "Component Name"
  manufacturer: "Vendor"
  mass_kg: 0.15
  power_w: 8.0
  cost_keur: 30
  trl: 8
  frequency_band: S  # for RF components
```

L'API permet aussi l'import : `POST /api/lifecycle/equipment/import`

---

## Séances de conception concourante

1. Cliquez sur **« Start Session »** (démarrer une séance) dans l'en-tête
2. Choisissez votre ou vos postes et saisissez un nom d'affichage
3. Partagez l'URL avec les membres de l'équipe → ils rejoignent la même séance
4. Les modifications se propagent en temps réel par WebSocket
5. Chaque poste ne peut modifier que les paramètres dont il est propriétaire
6. La convergence s'exécute automatiquement après chaque modification

---

## Raccourcis clavier

| Touche | Action |
|-----|--------|
| Ctrl+Entrée | Run Design (lancer la conception) |
| Échap | Fermer la fenêtre modale |

---

## Dépannage

| Problème | Solution |
|-------|---------|
| « Socket not connected » | Démarrez ou rejoignez d'abord une séance pour sélectionner des équipements |
| La conception n'affiche aucun résultat | Cliquez sur « Run Design » à l'étape 3 |
| Onglet Exigences (Requirements) vide | Un identifiant d'étude est nécessaire → lancez la conception au moins une fois |
| L'optimiseur ne démarre pas | Une séance est nécessaire (ou utilisez le mode « solo ») |

---

## Nouvelles fonctionnalités (UP6)

### Déblocage progressif des niveaux

L'outil suit désormais le cycle en V, en 5 niveaux progressifs :
- **Niveau 0** : aide uniquement (définir d'abord le besoin de mission)
- **Niveau 1** : architecture de la mission (une fois le besoin défini) — ConOps, fonctions, exigences
- **Niveau 2** : architecture du système (après une exécution de la conception) — options d'architecture, interfaces, bilans, études de compromis, gestion de projet
- **Niveau 3** : conception des sous-systèmes (une fois l'architecture choisie) — bilan de liaison, optimiseur, coût, navigateur d'équipements
- **Niveau 4** : vérification (après la conception des sous-systèmes) — conformité, matrice V&V, revue de jalon

La barre d'indication du niveau montre où vous en êtes et ce qu'il reste à faire.

### Éditeur interactif de l'architecture de mission

Dans l'onglet ConOps, un éditeur de diagrammes par glisser-déposer vous permet de construire l'architecture de votre mission :
- **6 types de nœuds** : satellite, station sol, traitement, utilisateur, capteur, GNSS/externe
- Faites glisser les nœuds pour les positionner et reliez-les par des lignes étiquetées
- L'architecture détermine les systèmes à définir au niveau suivant

### Choix de l'architecture du système

Dans l'onglet Architecture :
- **Moitié supérieure** : choix des options d'architecture pour chacun des 8 sous-systèmes (EPS, AOCS, TTC, thermique, structure, propulsion, OBC, sol)
- **Moitié inférieure** : schéma fonctionnel généré automatiquement, montrant les sous-systèmes et leurs liaisons
- Chaque choix fait dériver des exigences (étiquetées performance/interface/bilan/fonctionnelle)

### Bilans d'ingénierie (vue unifiée)

Le nouvel onglet « Eng. Budgets » (bilans d'ingénierie) présente les 8 bilans au même endroit :
- Masse, puissance, liaison, pointage, delta-V, volume, données, coût
- **Marges configurables** selon la phase de conception (phase A : 20 %, B : 15 %, C : 10 %)
- Ventilation par sous-système avec origine de la marge (COTS ou conception nouvelle)
- Consolidation à partir des choix d'équipements

### Moteur de propagation des contraintes

187 interconnexions entre points de conception sont détectées automatiquement :
- Lorsqu'un paramètre change, le moteur identifie TOUS les bilans concernés
- Il propose des options de résolution des violations, avec une analyse des compromis entre bilans
- Il détecte les dépendances circulaires (boucles de compromis qui exigent une décision de l'équipe)

### Gestion de projet

Le nouvel onglet « Project Mgmt » (gestion de projet) comprend :
- **Matrice des risques 5x5** : interactive, codée par couleur selon le score V×C (vraisemblance × conséquence)
- **Planning** : 10 jalons, de la MCR jusqu'à la recette en orbite
- **WBS** : 9 lots de travaux avec heures d'effort et suivi d'avancement
- Ajout du poste **Project Manager** (chef de projet)

### Export au format Word

Les documents ECSS peuvent désormais être exportés en fichiers .docx modifiables :
- Cliquez sur le bouton « Word » à côté de MRD, ConOps ou VP dans l'onglet Exports
- Les documents sont remplis à partir de l'état courant de la conception
- Modifiables dans Microsoft Word ou LibreOffice

### Persistance de la séance

L'état de votre conception persiste désormais après un rafraîchissement de la page :
- Toutes les données sont enregistrées automatiquement dans le localStorage du navigateur
- Inutile d'« enregistrer » : c'est toujours enregistré
- Pour effacer : DevTools du navigateur → Application → Local Storage → supprimer 'spacecdf-design-state'
