---
title: "Simulation de recette en orbite du jeudi — dossier de l'enseignant"
subtitle: "ORBIT NORTH · jeudi 20 août 2026 · Cyber Range de l'Université d'Ottawa"
course-codes: "GNG 3100 · SYS 5186"
term: "Été 2026"
version: "v1 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
audience: "enseignant + opérateur du simulateur"
---

# Simulation de recette en orbite du jeudi — dossier de l'enseignant

**Confidentiel — réservé à l'enseignant et à l'opérateur du simulateur.**

Ce dossier couvre la journée de simulation du jeudi. Les équipes échangent les rôles
d'opérateur et d'observateur par rapport au mercredi. L'objectif de la journée est la **première lumière**
de l'imageur multispectral.

---

## 1. La journée en un coup d'œil

| Quand | Quoi | Modalité |
|------|------|------|
| 09 h 00 – 09 h 30 | Point du matin, briefing du scénario aux deux équipes | Animé par l'enseignant |
| 09 h 30 – 12 h 00 | **Série de passages 1** — l'équipe A exploite deux passages en temps compressé ; l'équipe B observe | Simulation de recette en orbite |
| 12 h 00 – 13 h 00 | Déjeuner + préparation des observateurs | — |
| 13 h 00 – 13 h 15 | Réinitialisation + briefing de la série de passages 2 | Animé par l'enseignant |
| 13 h 15 – 15 h 45 | **Série de passages 2** — l'équipe B exploite deux passages en temps compressé ; l'équipe A observe | Simulation de recette en orbite |
| 15 h 45 – 17 h 00 | Débriefing commun, présentations des observateurs, fiches d'anomalie | Plénière + individuel |

Chaque série de passages couvre environ 4 passages sol simulés en 2,5 h de temps réel,
grâce à un multiplicateur de temps compressé (3×–5× entre les passages, 1× pendant
les passages). L'opérateur du simulateur change la vitesse à la main (§2).

---

## 2. Configuration du scénario

- **Point de reprise :** BP-3 — Début de la journée de recette en orbite (NOUVEAU ; spécification dans
  `breakpoint_spec.md`).
- **Phase au départ :** 4 (LEOP terminée).
- **Visibilité initiale :** Iqaluit, AOS à T+0 du scénario.
- **Passages prévus pendant le quart :** 4 (Iqaluit, Troll, Iqaluit,
  Troll — la visibilité réelle dépend de l'orbite).
- **Facteur d'accélération :** piloté par l'enseignant ; 3× par défaut
  entre les passages, 1× pendant les passages.

Le seul paramètre de démarrage est `--speed` (1.0 par défaut). Pendant le
quart, changer la vitesse avec les boutons de vitesse de la console de
l'enseignant (0.5×, 1×, 2×, 5×, 10×) ou par l'API de l'enseignant, par ex.
`{"type": "set_speed", "value": 3}` envoyé à `/api/command` pour un
réglage à 3× que les boutons n'offrent pas. `simulation.yaml` plafonne
toute demande à 1000×, et le simulateur se maintient à ≤ 10× pendant une
poussée. Le simulateur ne change **pas** de vitesse de lui-même autour des
passages : l'opérateur du simulateur s'en charge à la main, d'après le
planning des contacts.

---

## 3. Déroulement attendu des procédures

L'équipe doit mener la recette en orbite à peu près dans cet
ordre sur les quatre passages :

**Passage 1.** COM-001 Vérification de l'EPS · COM-002 Vérification du TCS ·
COM-004 Vérification des actionneurs SCAO (roues activées, NOMINAL commandé) ·
COM-003 Étalonnage des capteurs SCAO (étalonnage des gyroscopes dans ce NOMINAL,
décision Q16) · COM-005 Transitions de modes SCAO · COM-006 Vérification de la liaison
TTC.

**Passage 2.** COM-007 Vérification de l'OBDH · COM-008 Configuration de la FDIR
(activation de la surveillance S12, vérification des jeux de règles S12/S19).

**Passage 3.** COM-009 Mise sous tension de la charge utile · COM-010 Activation du refroidisseur du FPA
(se poursuit pendant l'éclipse et jusqu'au passage 4 — évacuation de la chaleur pendant
l'éclipse, mise en froid côté jour).

**Passage 4.** COM-011 Étalonnage de la charge utile · **COM-012 Première lumière** —
acquérir une image d'une cible de courant océanique répertoriée dans
`planning/imaging_targets.yaml`.

État visé en fin de quart : phase 5+ (prêt pour NOMINAL), charge utile
étalonnée, une image exploitable acquise.

---

## 4. Menu d'injection d'anomalies

Choisir une anomalie principale et, en option, une secondaire par équipe. Les fichiers
d'injection se trouvent dans `~/SpaceMissionSimulation/configs/eosat1/scenarios/`.

| Gravité | Fichier de scénario | Ce que voient les stagiaires | Reprise |
|----------|--------------|-------------------|----------|
| Facile | `eps_overcurrent.yaml` (line=`payload`) | Surintensité à la mise sous tension de la charge utile | CTG-012 Traitement d'une surintensité |
| Facile | `gs_rf_degradation.yaml` | Le TEB augmente en milieu de passage | CTG-014 Anomalie de TEB |
| Moyen | `fpa_overtemp.yaml` | Le refroidisseur du FPA ne tient pas sa consigne de −15 °C | CTG-004 Dépassement thermique + mise en sécurité de la charge utile |
| Moyen | `payload_corrupt_image.yaml` | La première image revient corrompue | CTG-015 Reprise après image corrompue |
| Difficile | `aocs_sensor_cascade.yaml` | Le senseur stellaire se dégrade ; le bilan de pointage n'est plus respecté | CTG-008 Panne du senseur stellaire → CTG-002 + report de la première lumière |
| Difficile | `eps_progressive_load_shed.yaml` | La dégradation de la batterie impose un délestage progressif pendant l'activation du refroidisseur | CTG-001 Délestage sur sous-tension |
| Très difficile | `aocs_wheel_failure.yaml` suivi de `transponder_failure.yaml` | Une roue se bloque en fin de passage 3, puis le transpondeur tombe en panne au passage suivant — traitement d'anomalies multiples | CTG-007 → CTG-003 |

Les cartes d'aide de six des sept scénarios se trouvent dans le guide de
l'enseignant, chapitre 18 : `eps_overcurrent.yaml` §18.2 (injecter sur `payload`,
`line_index=3`, pendant COM-009), `fpa_overtemp.yaml` §18.8,
`payload_corrupt_image.yaml` §18.9, `aocs_sensor_cascade.yaml`
§18.10, `eps_progressive_load_shed.yaml` §18.11 et la paire
`aocs_wheel_failure.yaml` + `transponder_failure.yaml` §18.12.
La septième figure ci-dessous, sur le même modèle.

**`gs_rf_degradation.yaml` — Dégradation de la chaîne RF de la station sol (facile)**

- **Moment de déclenchement.** La lancer une fois que COM-006 a établi la
  marge de liaison de référence, pour que l'équipe dispose d'un repère. Ses
  événements surviennent à T+60 s (`high_ber` côté satellite, amplitude 0.3,
  en rampe sur 120 s), T+180 s (LNA sol, facteur de bruit +3 dB) et T+360 s
  (dépointage de l'antenne sol, 3 dB). Le briefing du fichier demande le
  pont RF en mode FRAME (`SMO_RF_MODE=FRAME ./start.sh`).
- **Premier indice.** Le Eb/N0 (`ttc.eb_n0`, 0x0519) baisse et le TEB
  (`ttc.ber`, 0x050C) monte sur l'affichage TT&C tandis que la marge de
  liaison (`ttc.link_margin`, 0x0503) s'érode.
- **Procédure de reprise.** CTG-014 Anomalie de TEB ; CTG-003 si la
  liaison est perdue.
- **Critère de réussite du passage.** L'équipe compare le RSSI (`ttc.rssi`,
  0x0502) au Eb/N0 pour distinguer la dégradation côté satellite des deux
  dégradations côté sol avant de commander quoi que ce soit à bord, et
  ouvre une fiche par cause.
- **Questions de débriefing.**
  1. Quelle mesure vous a indiqué qu'une partie de la perte venait du sol ?
  2. Quelqu'un a-t-il commandé le satellite pour corriger une panne au sol ?
  3. Quand le poste TT&C a-t-il annoncé la tendance sur la boucle pour la première fois ?
  4. Le vidage en palier HIGH a-t-il été reporté ou déplacé vers un autre passage ?
  5. Que vérifieriez-vous en premier la prochaine fois ?

---

## 5. Critères de réussite du passage côté opérateur

| Critère | Série de passages 1 (équipe A) | Série de passages 2 (équipe B) |
|-----------|---------------------|---------------------|
| Phase passée à COMMISSIONING (5) | ✓ | ✓ |
| Vérification de l'EPS terminée sans défaut | ✓ | ✓ |
| Mode NOMINAL (4) du SCAO atteint, pointage < 0,5° | ✓ | ✓ |
| Jeux de règles de la FDIR activés et vérifiés (COM-008) | ✓ | ✓ |
| Charge utile sous tension (ON) | ✓ | ✓ |
| Refroidisseur du FPA à sa consigne (−15 °C) | ✓ | ✓ |
| Image de première lumière acquise (ou formellement reportée) | ✓ | ✓ |
| Fiches d'anomalie remplies pour toutes les injections | ✓ | ✓ |

L'option « formellement reportée » est réelle : si l'équipe diagnostique
correctement que le pointage est insuffisant et choisit de reporter
la prise de vue, elle satisfait le critère. Si elle prend l'image malgré tout et obtient
une image inexploitable, elle échoue.

---

## 6. Accompagnement pendant le quart

Comme le dossier LEOP, §6 : discipline de la boucle vocale, respect des
procédures, indice au niveau du panneau FDIR après cinq minutes de blocage,
et aucune pause pendant un passage. Deux ajouts propres à la recette en orbite :

- **Changements de vitesse uniquement entre les passages.** La compression
  relève de l'opérateur du simulateur, jamais de l'équipe, et l'horloge
  tourne à 1× de l'AOS au LOS.
- **Qualité de la passation entre passages.** À chaque changement de passage,
  le FD rappelle les points ouverts, la procédure en cours et l'objectif du
  passage suivant ; noter tout ce qui est oublié. La continuité d'un passage à
  l'autre est plus difficile que la continuité au sein d'un passage, et la
  première lumière en dépend.

---

## 7. Débriefing

Même structure et mêmes durées que le dossier LEOP, §7 : retour à chaud
(15 min), revue de l'anomalie (20 min), lecture des fiches d'évaluation par
les pairs (20 min), synthèse des enseignements (15 min) et briefing pour
vendredi (5 min). Les fiches d'observation utilisées aujourd'hui sont
*Équipe* et *Occupation de l'espace* ; mercredi a utilisé *Communications* et
*Technique*. Les questions de débriefing de chaque procédure se trouvent dans
le manuel du cours, partie 2, §11.8.

---

## 8. Sécurité, lignes rouges, références

La sécurité et les lignes rouges sont celles du dossier LEOP, §8 : aucune
commande sans autorisation du FD, aucune pause du simulateur pour gagner un
exercice (la compression entre passages est fixée par l'opérateur du
simulateur, pas par l'équipe), et pas de FD silencieux.

Les références sont celles du dossier LEOP, §9, plus :

- `configs/eosat1/scenarios/commissioning_day_start.yaml` (NOUVEAU,
  rédigé par l'enseignant à partir de la spécification BP-3 ; absent du jeu
  livré)
- `configs/eosat1/procedures/commissioning/*.md`
- `configs/eosat1/mcs/role_analysis/payload_ops_role.md` (la journée
  sollicite fortement les opérations charge utile)
- Manuel du cours, partie 2, chapitre 11 (opérations de recette en orbite), et
  guide de l'enseignant, chapitre 18 (cartes d'aide)
