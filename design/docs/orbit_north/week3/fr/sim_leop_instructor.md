---
title: "Simulation LEOP du mercredi — dossier de l'enseignant"
subtitle: "ORBIT NORTH · mercredi 19 août 2026 · Cyber Range de l'Université d'Ottawa"
course-codes: "GNG 3100 · SYS 5186"
term: "Été 2026"
version: "v1 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
audience: "enseignant + opérateur du simulateur"
---

# Simulation LEOP du mercredi — dossier de l'enseignant

**Confidentiel — réservé à l'enseignant et à l'opérateur du simulateur.**

Ce dossier couvre la journée de simulation du mercredi. Deux équipes d'étudiants
échangent les rôles d'opérateur et d'observateur entre deux passages. Les choix d'injection
d'anomalies sont listés ; l'enseignant choisit selon le niveau de chaque équipe après
le quiz de formation du mardi.

---

## 1. La journée en un coup d'œil

| Quand | Quoi | Modalité |
|------|------|------|
| 09 h 00 – 09 h 30 | Point du matin, briefing du scénario aux deux équipes | Animé par l'enseignant |
| 09 h 30 – 11 h 30 | **Passage 1** — l'équipe A exploite ; l'équipe B observe | Simulation LEOP |
| 11 h 30 – 12 h 30 | Déjeuner + préparation des observateurs | — |
| 12 h 30 – 12 h 45 | Réinitialisation + briefing du passage 2 | Animé par l'enseignant |
| 12 h 45 – 14 h 45 | **Passage 2** — l'équipe B exploite ; l'équipe A observe | Simulation LEOP |
| 14 h 45 – 16 h 00 | Débriefing commun, présentations des observateurs | Plénière |
| 16 h 00 – 17 h 00 | Finalisation des fiches d'anomalie + mains courantes | Individuel |

Chaque passage dure 90 min de temps réel / 90 min de temps simulé (vitesse 1×).

---

## 2. Configuration du scénario

- **Point de reprise :** BP-2 — Début de la journée LEOP (scénario existant
  `scenarios/first_contact.yaml`).
- **Phase au départ :** 3 (BOOTLOADER_OPS).
- **Visibilité initiale :** Iqaluit, AOS à T+0 du scénario.
- Indicateur **`override_passes`** activé pour que le contact dure toute la
  durée du passage.
- **Facteur d'accélération :** 1× (temps réel).

[Claude Code : confirmer l'invocation du scénario en ligne de commande. Forme attendue :
`sim run scenarios/first_contact.yaml --duration 5400 --inject <anomaly_yaml>`]

---

## 3. Déroulement attendu des procédures

L'équipe d'opérateurs doit amener le satellite de la phase 3
(chargeur d'amorçage, antennes non déployées) à la phase 4 (LEOP, HK complète, amortissement
terminé), à peu près dans cet ordre :

1. **LEOP-001** Première acquisition du signal et amorçage de l'OBC
2. **LEOP-006** Synchronisation temporelle
3. **(LEOP-002)** Bilan de santé initial
4. **LEOP-007** Mise sous tension séquentielle (c'est la plus longue — réchauffeur
   batterie, roues de réaction, amortissement par le SCAO ; voir la procédure pour la remarque
   complète sur l'ordre)
5. (Facultatif, si le temps le permet) **LEOP-005** Acquisition du Soleil

État final typique du passage 1 : phase 4, antennes déployées, logiciel applicatif en cours d'exécution,
htr_bat ON, aocs_wheels ON, vitesses angulaires < 0,05 °/s.

État final typique du passage 2 : identique, avec en plus le bus charge utile en attente, les jeux
de règles de la FDIR vérifiés, prêt pour la recette en orbite du jeudi.

---

## 4. Menu d'injection d'anomalies

Choisir **une** injection principale par équipe, et une secondaire facultative
(« injection glissante ») si la principale est résolue proprement. Les fichiers
cités sont des fichiers de scénario YAML situés dans
`~/SpaceMissionSimulation/configs/eosat1/scenarios/` ; les déclencher
depuis l'interface opérateur du scénario en cours d'exécution.

| Gravité | Fichier de scénario | Ce que voient les stagiaires | Procédure de reprise |
|----------|--------------|-------------------|--------------------|
| Facile | `ttc_no_tm_at_aos.yaml` | Balise présente, la HK complète n'arrive jamais malgré OBC_BOOT_APP | CTG-019 Absence de TM en début de passage |
| Facile | `eps_overcurrent.yaml` | Surintensité soudaine sur une ligne d'alimentation pendant la mise sous tension séquentielle | CTG-012 Traitement d'une surintensité |
| Moyen | `aocs_actuator_stuck.yaml` | Une roue de réaction bloquée à 0 tr/min pendant l'amortissement | CTG-007 Anomalie de roue de réaction |
| Moyen | `aocs_star_tracker_failure.yaml` | Le senseur stellaire principal se dégrade en fin d'amortissement | CTG-008 Panne du senseur stellaire |
| Difficile | `obc_watchdog.yaml` | Réinitialisation de l'OBC par le chien de garde en plein déploiement | CTG-010 Reprise après chien de garde OBDH |
| Difficile | `obc_bus_failure.yaml` | Le bus CAN A tombe en pleine mise sous tension séquentielle | CTG-017 Basculement sur panne de bus |
| Très difficile | `gs_antenna_failure.yaml` | Antenne d'Iqaluit dégradée en milieu de passage ; l'équipe doit reporter la fin du passage sur Troll | CTG-020 Panne d'antenne de station sol |

[Claude Code : vérifier les noms de fichiers dans le simulateur. Les quatre scénarios
*moyens* et *difficiles* figurent dans
`scenarios/aocs_*.yaml`, `obc_*.yaml`, etc.]

### Carte d'injection

Pour chaque injection, l'enseignant doit connaître :

1. **Moment de déclenchement** — à quel point de la procédure LEOP injecter ;
2. **Premier indice** — ce que les opérateurs verront en premier
   (paramètre de télémesure, alarme FDIR, indice vocal) ;
3. **Critère de réussite du passage** — à quoi ressemble une « reprise réussie » pour
   le passage ;
4. **Cinq questions de débriefing** à poser après le passage.

[Claude Code : produire une carte d'injection d'une page par scénario.]

---

## 5. Critères de réussite du passage côté opérateur

Critères GO/NO-GO de fin de passage (utilisés par l'enseignant pour l'évaluation) :

| Critère | Passage 1 (équipe A) | Passage 2 (équipe B) |
|-----------|-----------------|-----------------|
| Logiciel applicatif de l'OBC en cours d'exécution | ✓ | ✓ |
| Temps bord réglé, dérive < 0,5 s | ✓ | ✓ |
| Antennes déployées, liaison haut débit | ✓ | ✓ |
| Réchauffeur batterie sur ON | ✓ | ✓ |
| Roues de réaction sur ON, SCAO en DETUMBLE | ✓ | ✓ |
| Vitesses angulaires < 0,05 °/s | facultatif | ✓ |
| Fiche d'anomalie remplie pour chaque injection | ✓ | ✓ |
| Jeux de règles de la FDIR activés et vérifiés | — | ✓ |

Chaque critère contribue à la note de **performance en simulation**
de l'équipe (ligne d'évaluation de la semaine 3).

---

## 6. Accompagnement pendant le quart

L'enseignant (dans le rôle de directeur de mission) s'assoit derrière le poste du FD
et n'intervient que par exception :

- **Discipline de boucle vocale.** Si l'équipe commence à parler en même temps,
  arrêter, nommer la règle, reprendre.
- **Respect des procédures.** Si un poste envoie une commande sans GO du
  FD, arrêter, le consigner, le traiter comme une infraction à la sécurité.
- **Traitement des anomalies.** Si l'équipe est bloquée plus de 5 minutes, glisser un
  indice au niveau du panneau FDIR (sans nommer la procédure).
- **Pression temporelle.** Maintenir l'horloge en temps réel — pas de pause de la
  simulation pour discuter. Le passage se termine quand l'orbite le termine.

---

## 7. Débriefing (commun)

Structure du débriefing de 75 minutes en fin de journée :

1. **Débriefing à chaud (15 min).** Le FD de chaque équipe lit les faits marquants de sa
   main courante. Pas encore de critique.
2. **Revue des anomalies (20 min).** L'équipe d'opérateurs retrace
   le traitement de l'anomalie ; l'équipe d'observation la questionne.
3. **Restitution des fiches d'évaluation par les pairs (20 min).** Chaque équipe d'observation
   lit à voix haute sa fiche à quatre axes (équipe / communications / espace /
   technique). L'équipe d'opérateurs répond par une acceptation et une
   défense par axe.
4. **Synthèse du retour d'expérience (15 min).** L'enseignant consolide
   en une liste unique, consignée dans le registre de retour d'expérience de la promotion.
5. **Briefing du jeudi (5 min).** Lecture à faire : au minimum les fiches de procédure COM-001
   à COM-008 avant le lendemain.

---

## 8. Sécurité et lignes rouges

- **Aucune commande sans autorisation du FD.** Infraction → l'enseignant
  interrompt le quart, l'équipe consigne l'infraction, sans pénalité si la leçon est retenue.
- **Pas de pause du simulateur pour gagner un exercice.** L'horloge tourne.
- **Pas de FD silencieux.** Le directeur de vol doit être sur la boucle. Si le
  FD est débordé, l'enseignant annonce un « Hold » de 30 secondes et
  réinitialise le poste.

---

## 9. Références et fichiers

- Scénario du simulateur : `configs/eosat1/scenarios/first_contact.yaml`
- Scénarios d'anomalie : voir le tableau du §4
- Fichiers de procédure : `configs/eosat1/procedures/leop/*.md`
- Postes du MCS : `configs/eosat1/mcs/positions.yaml`
- Limites de télémesure : `configs/eosat1/mcs/limits.yaml`
- ECSS-E-ST-70-11C — *Space segment operability*
- NASA *Mission Operations Handbook* — https://nodis3.gsfc.nasa.gov/
- ESA *Mission Operations Concept* —
  https://www.esa.int/Enabling_Support/Operations
