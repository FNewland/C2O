---
title: "Référence MCS et MPS pour les étudiants"
subtitle: "ORBIT NORTH · aide-mémoire des outils d'exploitation, semaine 3"
course-codes: "GNG 3100 · SYS 5186"
term: "Été 2026"
version: "v1 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
audience: "étudiantes et étudiants"
expected-reading: "Sections 1 – 4 avant la journée de formation 2 ; sections 5 – 7 avant la journée LEOP du mercredi"
---

# Référence MCS et MPS pour les étudiants

Ce document est la référence de l'opérateur pour les deux outils que vous
utiliserez pendant la semaine 3 d'ORBIT NORTH :

- **MCS** — le système de contrôle de mission (télémesure, commande,
  panneau de procédures, panneau FDIR) ;
- **MPS** — le système de planification de mission (cibles de prise de vue, planification
  des passages, détection des conflits).

Vous n'avez **pas** besoin de savoir comment fonctionne le simulateur sous-jacent.
Vous **devez** en revanche maîtriser les interfaces du MCS et du MPS.

---

## 1. La console en un coup d'œil

[Claude Code : inclure une capture d'écran annotée du MCS — le
tableau de bord par défaut du directeur de vol. Légendes : bandeau supérieur (indicatif,
phase, heure), colonne de gauche (onglets des sous-systèmes), centre (mosaïque de
télémesure), colonne de droite (panneau FDIR, boucle vocale, panneau de procédures).
Environ 250 mots décrivant chaque zone.]

### 1.1 Onglets propres à chaque poste

Chaque poste du MCS dispose d'un jeu d'onglets visibles différent, défini dans
`mcs/positions.yaml`. Référence rapide :

| Poste | Onglets visibles |
|----------|-------------|
| Directeur de vol | system_dashboard, power_monitor, fdir_panel, contact_schedule, procedure_panel, overview, eps, aocs, tcs, obdh, ttc, payload, commanding, pus, procedures, manual |
| Puissance et thermique | overview, eps, tcs, commanding, procedures, manual |
| Dynamique du vol (AOCS) | overview, aocs, commanding, procedures, manual |
| TT&C | overview, ttc, commanding, procedures, manual |
| Opérations charge utile | overview, payload, commanding, procedures, manual |
| FDIR / Systèmes | overview, obdh, commanding, pus, procedures, manual |

L'onglet overview est toujours présent afin que chaque poste partage la même
conscience de la situation ; les onglets propres au poste sont ceux où vous faites
votre travail.

[Claude Code : convertir le tableau ci-dessus en carte aide-mémoire par
poste.]

---

## 2. Lire la télémesure

[Claude Code : 400 mots. Traiter :

- la structure de la HK (SID tirés de `telemetry/hk_structures.yaml`,
  paramètres tirés de `telemetry/parameters.yaml`) ;
- la coloration des limites : plages verte / jaune / rouge définies dans
  `mcs/limits.yaml` ;
- l'indicateur de télémesure « périmée » (aucune mise à jour depuis plus de 10 s) ;
- le widget de « suivi » — comment épingler un paramètre pour tout le quart ;
- la lecture d'une courbe : courbe de tendance, lignes de limites, zones d'éclipse grisées.

Inclure une capture d'écran annotée d'une mosaïque de télémesure.]

---

## 3. Envoyer une commande

[Claude Code : 350 mots. Traiter :

- les voies de commande : pilotée par procédure (recommandée) ou commande directe ;
- l'introduction aux services PUS pour les sept services que les étudiants voient le plus :
  S1 (vérification), S3 (HK), S5 (événements), S8 (gestion des fonctions),
  S9 (temps), S11 (programmation bord), S17 (test de liaison). Chacun en 30
  mots. Source : `mcs/pus_services.yaml` ;
- l'autorisation à double clé : de nombreuses commandes destructrices exigent que le
  directeur de vol tourne la seconde clé ;
- la commande depuis une étape de procédure — remplissage automatique des champs ;
- les erreurs fréquentes : paramètre hors plage, mauvais APID, pas d'AOS.

Inclure une capture d'écran annotée du panneau de commande.]

---

## 4. Le panneau de procédures

[Claude Code : 300 mots. Traiter :

- comment charger une procédure (sélecteur de procédures, recherche par ID) ;
- la liste des étapes : chaque étape a un responsable / une action / une vérification / un statut de réussite ;
- « Sauter » et « Suspendre » — quand chacun est autorisé ;
- la journalisation d'une exécution de procédure : horodatage, exécutant, commentaires ;
- où va l'historique des exécutions (journal de quart).

Inclure une capture d'écran annotée de `procedures/nominal/startup.md`
chargée dans le panneau.]

---

## 5. Le panneau FDIR

[Claude Code : 350 mots. Traiter :

- la lecture des règles FDIR (chargées depuis `monitoring/s12_definitions.yaml`
  et `monitoring/s19_rules.yaml`) ;
- la liste des anomalies actives : code couleur de gravité, heure de déclenchement,
  sous-système concerné ;
- acquitter une anomalie ou l'effacer ;
- l'échelle d'escalade : `fdir.level` 0 (nominal) → 3 (critique) ; la gravité des
  événements est une échelle distincte ;
- le forçage manuel — quand et pourquoi ;
- la création d'une fiche d'anomalie : champs obligatoires, emplacement de la fiche.

Inclure une capture d'écran annotée du panneau FDIR.]

---

## 6. Le système de planification de mission (MPS)

[Claude Code : 400 mots. Traiter :

- le sélecteur de cibles de prise de vue — filtre géographique, filtre par bande scientifique
  (configuration dans `planning/imaging_targets.yaml`) ;
- les types d'activités — `planning/activity_types.yaml` (basculement, image,
  transmission au sol, éclipse, gestion du moment cinétique) ;
- le planning des stations sol : AOS, élévation maximale, durée, station
  (`planning/ground_stations.yaml`) ;
- le détecteur de conflits — durée de basculement, bilan de puissance, enveloppe thermique,
  bilan de pointage ;
- l'export du plan — produit la séquence d'activités chargée par l'OBC ;
- l'import du plan dans le panneau de procédures du MCS.

Inclure des captures d'écran de la vue planning du MPS et du résultat du
détecteur de conflits.]

---

## 7. Boucle vocale et messagerie du MCS

[Claude Code : 250 mots. Traiter :

- la boucle vocale : matériel (softphone du Cyber Range), discipline de boucle (voir
  journée de formation 2, §1), schéma d'adressage, règle du micro ouvert ;
- la messagerie de secours du MCS : quand l'utiliser (commentaires peu prioritaires), quand
  ne pas l'utiliser (toute intention de commande) ;
- l'enregistrement de la boucle : chaque annonce est enregistrée pour le débriefing après la simulation.]

---

## 8. Raccourcis clavier rapides

[Claude Code : produire un tableau de 12 lignes des raccourcis clavier courants du MCS.
Exemples :

| Raccourci | Action |
|----------|--------|
| F2 | Activer la mosaïque de télémesure |
| F3 | Activer le panneau de commande |
| F4 | Activer le panneau de procédures |
| Ctrl-K | Sélecteur rapide de commandes |
| Ctrl-, | Afficher / masquer la vue d'ensemble |
| Échap | Annuler la commande en attente |

Vérifier les raccourcis exacts dans l'interface du simulateur.]

---

## 9. Pour aller plus loin

| Sujet | Fichier source dans le simulateur |
|-------|--------------------------|
| Manuels des sous-systèmes (contexte) | `configs/eosat1/manual/0*.md` |
| Analyses des rôles par poste | `configs/eosat1/mcs/role_analysis/*.md` |
| Paramètres de télémesure | `configs/eosat1/telemetry/parameters.yaml` |
| Limites de télémesure | `configs/eosat1/mcs/limits.yaml` |
| Index des procédures | `configs/eosat1/procedures/procedure_index.yaml` |
| Règles FDIR | `configs/eosat1/monitoring/s19_rules.yaml` |

Références externes :

- ECSS-E-ST-70-11C — *Space segment operability* —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/
- ECSS-E-ST-70-32C — *Test and operations procedures* —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-32c-test-and-operations-procedures/
- CCSDS *Packet Utilization Standard* (PUS) —
  https://public.ccsds.org/Pubs/660x0g3.pdf
- NASA *Mission Operations Handbook* — https://nodis3.gsfc.nasa.gov/
