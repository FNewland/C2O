# Simulateur du satellite EOSAT-1 — documentation

**Documentation de référence complète du simulateur d'opérations de la mission EOSAT-1**

Mise à jour : 2026-08-01. Le [`README.md`](../README.md) à la racine du dépôt est le
point d'entrée en une page ; le présent fichier est l'index de la documentation.

---

## Nouveautés de la version 2026-08

| Document | Contenu |
|---|---|
| **[DETERMINISM.md](./DETERMINISM.md)** | Ce qui est reproductible, l'effet de `speed` sur la physique, l'indicateur d'honnêteté du mode séculaire. **À lire avant de préparer un exercice numérique.** |
| **[THREADING_AND_STATE.md](./THREADING_AND_STATE.md)** | Qui écrit quoi, quand l'instantané est publié, ce que capture exactement un point de reprise. **À lire avant de modifier le simulateur.** |
| **[PARAMETER_MAP.md](./PARAMETER_MAP.md)** | Généré à partir de la configuration en CI : paramètre → SID HK → limites sol → moniteur S12 |
| **[STATUS.md](./STATUS.md)** | Ce qui reste ouvert, et ce qui n'est délibérément pas fait. Remplace quatre rapports situés à la racine |
| **[CHANGELOG.md](./CHANGELOG.md)** | Historique des versions, mis à jour |
| `archive/YYYY-MM/` | Rapports remplacés, chaque dossier contenant un `INDEX.md` qui indique ce qui les a remplacés |
| `source_material/` | Les fichiers d'entrée `.docx` et `.skill` à partir desquels les supports de cours ont été produits |
| `plan_2026-08/` | Les artefacts de planification de cette version : liste des fichiers supprimés et errata du manuel |

---

## Navigation rapide

### Pour les opérateurs de mission
Commencez ici pour des conseils pratiques :
- **[OPERATIONS_GUIDE.md](./OPERATIONS_GUIDE.md)** — Démarrer le simulateur, dérouler des scénarios, surveiller la télémesure, envoyer des commandes et traiter les anomalies
  - Guide de démarrage rapide (30 secondes)
  - Options de démarrage du simulateur
  - Navigation dans le tableau de bord du MCS
  - Exemples de commande
  - Scénarios opérationnels courants
  - Procédures de traitement des anomalies
  - Scénarios de formation

### Pour les enseignants qui exploitent la suite sur un serveur
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** — Déploiement en réseau ou en salle de cours
  - Configurations de déploiement (machine unique, serveur + navigateurs clients, distribué)
  - Chaque service, port et adresse d'écoute (vérifiés par rapport à `start.sh`)
  - Ports qui doivent être accessibles depuis un poste étudiant
  - Emplacement de chaque artefact persistant et manière dont un client le récupère
  - Mémoire des vidages de TM différée : règles d'emplacement et API HTTP
  - Points de reprise dans un déploiement en réseau
  - Recette complète pour la salle de cours et dépannage

### Pour les ingénieurs commande-contrôle
Pour comprendre et exécuter les commandes PUS :
- **[PUS_SERVICE_REFERENCE.md](./PUS_SERVICE_REFERENCE.md)** — Référence complète des services PUS-C
  - Les 13 services implémentés (S1, S3, S5-S6, S8-S9, S11-S13, S15, S17, S19-S20)
  - Syntaxe et paramètres des commandes
  - Plus de 50 fonctions S8 réparties sur tous les sous-systèmes
  - Exemples de séquences de commandes
  - Gestion des erreurs et reprise
  - Tableaux de référence rapide

### Pour les architectes système
Pour comprendre la conception et l'implémentation :
- **[architecture.md](./architecture.md)** — Architecture et conception du système
  - Vue d'ensemble des composants (simulateur, MCS, planificateur, passerelle)
  - État d'implémentation des services PUS
  - Détails sous-système par sous-système
  - Paramètres de télémesure (plus de 120)
  - Règles de surveillance (plus de 25)
  - Règles événement-action (plus de 20)
  - Vues du MCS
  - Intégration de la planification
  - Structure de la configuration
  - Caractéristiques de performances

### Pour les chefs de projet et les relecteurs
Pour voir ce qui a été implémenté :
- **[CHANGELOG.md](./CHANGELOG.md)** — Journal détaillé des modifications (avril 2026)
  - Toutes les nouvelles commandes S8 par sous-système (plus de 50 au total)
  - Nouveaux paramètres de télémesure (plus de 120 au total)
  - Nouveaux événements (plus de 120 au total)
  - Règles de surveillance S12 (25 au total)
  - Règles événement-action S19 (20 au total)
  - Nouvelles vues du MCS
  - Améliorations de la FDIR
  - Mises à jour de la configuration

### Pour l'analyse des écarts et la planification
Pour voir ce qui reste à faire :
- **[gap_analysis/subsystem_gap_analysis.md](./gap_analysis/subsystem_gap_analysis.md)** — Analyse détaillée des écarts avec les mises à jour d'avril 2026
  - Avancement global : 50 % (janv. 2026) → 90 % (avr. 2026)
  - État sous-système par sous-système
  - Matrice de couverture des services
  - Limitations connues
  - Feuille de route des améliorations futures

---

## Vue d'ensemble de la documentation

### Architecture et conception
| Document | Objet | Public |
|----------|---------|----------|
| **architecture.md** | Architecture du système, conception des composants, détails des sous-systèmes | Architectes, ingénieurs confirmés |
| **gap_analysis/subsystem_gap_analysis.md** | Analyse des écarts avec les mises à jour d'avril 2026, feuille de route | Chefs de projet, ingénieurs |

### Opérations et formation
| Document | Objet | Public |
|----------|---------|----------|
| **OPERATIONS_GUIDE.md** | Guide pratique des opérations, scénarios, dépannage | Opérateurs, formateurs, nouveaux utilisateurs |
| **DEPLOYMENT.md** | Déploiement sur serveur ou en salle de cours, ports, emplacement des artefacts | Enseignants, administrateurs système |
| **PUS_SERVICE_REFERENCE.md** | Référence complète des commandes PUS, guide de syntaxe | Ingénieurs commande-contrôle |

### Gestion des modifications
| Document | Objet | Public |
|----------|---------|----------|
| **CHANGELOG.md** | Liste détaillée de toutes les modifications (avril 2026) | Chefs de projet, relecteurs |

---

## Synthèse des fonctionnalités

### ✅ Fonctionnalités terminées (avril 2026)

**Services PUS :**
- S1 : vérification des requêtes (cycle de vie complet : acceptation, démarrage, progression, achèvement, échec)
- S3 : données de servitude (6 structures de données, multiparamètres)
- S5 : signalement d'événements (plus de 120 événements, génération active, activation sélective)
- S8 : gestion des fonctions (plus de 50 fonctions réparties sur tous les sous-systèmes)
- S9 : gestion du temps (corrélation UTC, services d'horodatage)
- S11 : programmation des activités (programmateur de TC avec gestion du temps)
- S12 : surveillance bord (plus de 25 règles, contrôles en valeur absolue et en variation, activées automatiquement)
- S13 : transfert de gros volumes de données (téléchargement des images de la charge utile, par blocs)
- S15 : stockage de la TM (4 mémoires tampons circulaires ou linéaires, conservation 24 heures)
- S17 : test de connexion (écho NOOP, validation de la liaison)
- S19 : événement-action (plus de 20 règles de réponse autonome, déclenchement automatique)
- S20 : gestion des paramètres (mise à jour de gain et de décalage)

**Sous-systèmes :**
- **AOCS :** 9 modes, 16 fonctions S8, 5 règles S12, 5 règles S19, dynamique en quaternions
- **EPS :** distribution de puissance, délestage (3 niveaux), 10 fonctions S8, 8 règles S12, 4 règles S19
- **TCS :** modèle thermique à 10 zones, 4 fonctions S8, 8 règles S12, 3 règles S19
- **TTC :** double transpondeur, bilan de liaison, 9 fonctions S8, 4 règles S12, 3 règles S19
- **OBDH :** double OBC, programmateur de TC, nettoyage mémoire (scrub), 4 fonctions S8, 5 règles S12, 4 règles S19
- **Charge utile :** instrument d'imagerie, refroidisseur du FPA, téléchargement S13, 8 fonctions S8, 6 règles S12, 3 règles S19
- **FDIR :** plus de 26 scénarios de défaillance, 51 procédures, autonomie en cascade

**MCS (système de contrôle de mission) :**
- Vue d'ensemble du système (attitude, orbite, phase)
- Suivi du bilan de puissance (tendance du SoC, délestage)
- Panneau d'alarmes FDIR (violations S12, déclenchements S19)
- Planning des contacts (visibilité des stations sol)
- État des procédures (actives, programmées, historique)
- Interface de télécommande (commandes par sous-système)
- Suivi des événements et alertes (flux S5 en temps réel)

**Planificateur de mission :**
- Application des contraintes (puissance, thermique, AOCS, volume de données)
- Programmation des activités (prises de vue, téléchargements, maintenance)
- Intégration des stations sol (propagation des TLE, prévision des passages)
- Génération d'activités sous forme de TC S11
- Optimisation de la mission avec vérification des contraintes

---

## Indicateurs clés

| Indicateur | Nombre |
|--------|-------|
| Services PUS implémentés | 15 (S1–S3, S5, S6, S8, S9, S11–S13, S15, S17–S20) |
| Fonctions S8 | Plus de 110, réparties sur tous les sous-systèmes |
| Paramètres de télémesure | Plus de 450, avec unités et descriptions |
| Types d'événements | Plus de 150, avec niveaux de gravité |
| Règles de surveillance S12 | 41, avec seuils |
| Règles événement-action S19 | 32 réponses autonomes |
| Procédures FDIR | 67 (LEOP, recette en orbite, nominales, de contingence, d'urgence) |
| Scénarios de défaillance | Plus de 26, avec injection et reprise |
| Onglets de vues du MCS | Plus de 7 tableaux de bord opérationnels |
| Fichiers de configuration | Plus de 90 fichiers YAML |

---

## Limitations actuelles

| Limitation | Impact | Atténuation |
|-----------|--------|-----------|
| Modèle mémoire (S6) simplifié | Impossible de simuler de vraies pannes mémoire ni la reprise après SEU | Acceptable pour les opérations, sommes de contrôle codées en dur |
| Évanouissements dus à la pluie non modélisés | Les prévisions de marge de liaison supposent un ciel clair (affaiblissement gazeux pondéré par la cosécante de l'élévation) | Le modèle par ciel clair suffit dans la plupart des cas |

---

## Prise en main

### Étape 1 : démarrer le simulateur
```bash
cd /sessions/beautiful-dazzling-edison/mnt/SpaceMissionSimulation
python -m smo_simulator --config configs/eosat1/ --port 5678 --time-scale 1.0
```

### Étape 2 : démarrer le MCS
```bash
cd /sessions/beautiful-dazzling-edison/mnt/SpaceMissionSimulation
python -m smo_mcs --simulator-host localhost:5678 --mcs-port 8080
```

### Étape 3 : ouvrir le navigateur web
Aller à : `http://localhost:8080/`

### Étape 4 : envoyer la première commande
1. Cliquer sur l'onglet « Commands »
2. Sélectionner « Housekeeping » → « Request HK »
3. Régler SID = 1 (EPS)
4. Cliquer sur « Send »
5. Observer le rapport d'acceptation S1.1 et la télémesure reçue en réponse

**Étapes suivantes :**
- Voir **OPERATIONS_GUIDE.md** pour les procédures détaillées
- Voir **PUS_SERVICE_REFERENCE.md** pour la syntaxe des commandes
- Voir **architecture.md** pour le détail des sous-systèmes

---

## Statistiques de la documentation

| Document | Taille | Sections | Objet |
|----------|------|----------|---------|
| architecture.md | 20 Ko | 20 | Conception et implémentation du système |
| OPERATIONS_GUIDE.md | 34 Ko | 10 | Procédures opérationnelles pratiques |
| PUS_SERVICE_REFERENCE.md | 28 Ko | 14 | Référence et syntaxe des commandes |
| CHANGELOG.md | 21 Ko | 7 sous-systèmes | Journal des modifications et liste des fonctionnalités |
| subsystem_gap_analysis.md | 14 Ko | 7 sous-systèmes | Analyse des écarts et avancement |

**Documentation totale :** environ 117 Ko, 51 sections, plus de 50 tableaux, plus de 100 exemples

---

## Arborescence des fichiers

```
docs/
├── README.md                          ← Vous êtes ici
├── architecture.md                    ← Conception du système
├── OPERATIONS_GUIDE.md                ← Procédures d'exploitation
├── PUS_SERVICE_REFERENCE.md           ← Référence des commandes
├── CHANGELOG.md                       ← Évolutions fonctionnelles (avril 2026)
├── gap_analysis/
│   ├── subsystem_gap_analysis.md      ← Analyse des écarts (mise à jour avril 2026)
│   ├── README.md                      ← Index de l'analyse des écarts
│   └── [autres fichiers d'analyse des écarts]
├── ops_research/
│   ├── aocs_requirements.md
│   ├── eps_tcs_requirements.md
│   └── [autres documents d'exigences]
├── sim_fidelity/
│   ├── aocs_fidelity.md
│   ├── eps_fidelity.md
│   └── [autres évaluations de fidélité]
└── methodology/
    └── agent_based_ops_development.md
```

---

## Configuration et code associés

**Configuration :**
- `configs/eosat1/commands/tc_catalog.yaml` — Définition des plus de 50 commandes S8
- `configs/eosat1/events/event_catalog.yaml` — Définition des plus de 120 événements
- `configs/eosat1/telemetry/parameters.yaml` — Les plus de 120 paramètres de télémesure
- `configs/eosat1/monitoring/s12_definitions.yaml` — Les plus de 25 règles de surveillance
- `configs/eosat1/monitoring/s19_rules.yaml` — Les plus de 20 règles événement-action
- `configs/eosat1/subsystems/*.yaml` — Configuration propre à chaque sous-système (7 fichiers)

**Code du simulateur :**
- `packages/smo-simulator/src/smo_simulator/service_dispatch.py` — Répartiteur PUS
- `packages/smo-simulator/src/smo_simulator/engine.py` — Moteur de simulation principal
- `packages/smo-simulator/src/smo_simulator/models/` — Modèles physiques des sous-systèmes (6 fichiers)
- `packages/smo-simulator/src/smo_simulator/fdir.py` — Moteur FDIR

**Code du MCS :**
- `packages/smo-mcs/src/smo_mcs/` — Tableau de bord web et interface de commande

---

## Historique des révisions

| Date | Version | Modifications |
|------|---------|---------|
| Avril 2026 | 1.0 | Suite documentaire complète : architecture.md, PUS_SERVICE_REFERENCE.md, OPERATIONS_GUIDE.md, CHANGELOG.md, gap_analysis.md mis à jour |
| Janvier 2026 | 0.5 | Analyse initiale des écarts, fonctionnalités achevées à 50 % |

---

## Référence rapide

### Pour les opérateurs
- **Comment démarrer le simulateur ?** → [OPERATIONS_GUIDE.md § Démarrage du simulateur](./OPERATIONS_GUIDE.md#simulator-startup)
- **Comment envoyer une commande ?** → [OPERATIONS_GUIDE.md § Commander le satellite](./OPERATIONS_GUIDE.md#commanding-the-spacecraft)
- **Comment traiter les anomalies ?** → [OPERATIONS_GUIDE.md § Procédures de traitement des anomalies](./OPERATIONS_GUIDE.md#anomaly-response-procedures)
- **Comment surveiller la télémesure ?** → [OPERATIONS_GUIDE.md § Surveillance de la télémesure](./OPERATIONS_GUIDE.md#telemetry-monitoring)

### Pour les ingénieurs
- **Quelles commandes sont disponibles ?** → [PUS_SERVICE_REFERENCE.md § Service 8 : gestion des fonctions](./PUS_SERVICE_REFERENCE.md#service-8-function-management)
- **Quels sont les services PUS ?** → [PUS_SERVICE_REFERENCE.md § Vue d'ensemble des services](./PUS_SERVICE_REFERENCE.md#service-overview)
- **Quels paramètres de télémesure existent ?** → [architecture.md § Détails sous-système par sous-système](./architecture.md#subsystem-implementation-status)
- **Quelles règles de surveillance sont configurées ?** → [architecture.md § Section FDIR](./architecture.md#7-fdir-fault-detection-isolation--recovery)

### Pour les architectes
- **Quelle est l'architecture du système ?** → [architecture.md § Vue d'ensemble](./architecture.md#overview)
- **Comment les sous-systèmes interagissent-ils ?** → [architecture.md § Thèmes transverses aux sous-systèmes](./architecture.md#cross-cutting-themes)
- **Quel est l'état actuel ?** → [CHANGELOG.md § Synthèse](./CHANGELOG.md#summary-of-improvements-april-2026)
- **Quels écarts subsistent ?** → [gap_analysis/subsystem_gap_analysis.md](./gap_analysis/subsystem_gap_analysis.md)

---

## Assistance

Pour toute question sur :
- **Les opérations et les procédures :** consulter [OPERATIONS_GUIDE.md](./OPERATIONS_GUIDE.md)
- **La syntaxe des commandes et les services PUS :** consulter [PUS_SERVICE_REFERENCE.md](./PUS_SERVICE_REFERENCE.md)
- **La conception et l'architecture du système :** consulter [architecture.md](./architecture.md)
- **Les fonctionnalités ajoutées et leur état :** consulter [CHANGELOG.md](./CHANGELOG.md)
- **Les écarts et la feuille de route :** consulter [gap_analysis/subsystem_gap_analysis.md](./gap_analysis/subsystem_gap_analysis.md)

---

**Suite documentaire du simulateur du satellite EOSAT-1**
Version 1.0 — avril 2026
Tous les sous-systèmes implémentés avec des modèles physiques, conformité PUS complète et opérations autonomes
