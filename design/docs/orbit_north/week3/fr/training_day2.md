---
title: "Semaine 3 — journée de formation 2 : formation aux opérations de mission"
subtitle: "ORBIT NORTH · mardi 18 août 2026 · Cyber Range de l'Université d'Ottawa"
course-codes: "GNG 3100 · SYS 5186"
term: "Été 2026"
version: "v1 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
audience: "étudiantes et étudiants + enseignant"
expected-reading: "L'aide-mémoire des procédures sélectionnées (document séparé) et le §5 de la Référence MCS et MPS (panneau de traitement des anomalies) avant le jour 2 ; une procédure nominale (NOM-001) et une procédure de contingence (CTG-003) avant la répétition à blanc de l'après-midi"
---

# Journée de formation 2 — formation aux opérations de mission

**La journée en un coup d'œil**

| Quand | Quoi | Production |
|------|------|--------|
| 09 h 00 – 10 h 00 | Discipline de boucle vocale + protocole GO/NO-GO | Carte des annonces apprise |
| 10 h 00 – 11 h 30 | Revue commentée des procédures : NOM-001 et CTG-003 | Questions-réponses consignées |
| 11 h 30 – 12 h 00 | Entraînement à la passation de consignes (NOM-012) | Deux passations consignées |
| 13 h 00 – 14 h 00 | Atelier de dynamique du vol | Horaires de passage prédits |
| 14 h 00 – 15 h 30 | Répétition à blanc 1 — passage nominal, sans panne | Mains courantes des opérateurs |
| 15 h 30 – 16 h 30 | Répétition à blanc 2 — passage nominal avec une panne injectée | Fiches d'anomalie, débriefing |
| 16 h 30 – 17 h 00 | **Quiz de formation aux opérations** | Quiz remis |

**Cadre :** Cyber Range de l'Université d'Ottawa. Deux consoles installées pour 09 h 00. Les deux
répétitions à blanc utilisent le point de reprise **Nominal après recette en orbite** (BP-1).

---

## 1. Discipline de boucle vocale

[Claude Code : 350 mots. Présenter la phraséologie de référence utilisée dans les centres de
contrôle de la NASA et de l'ESA. Inclure une carte de référence d'une page comportant :
le schéma d'adressage (« FD, AOCS — go for star-tracker enable »),
l'appel-réponse GO/NO-GO, les règles du micro ouvert, les attentes en matière de
« loop discipline », la règle selon laquelle le FD n'envoie pas lui-même de commandes. Citer
le *Operations Manual for Mission Control* de l'ESA et la norme *Mission
Operations Voice Procedure* de la NASA APPEL —
https://appel.nasa.gov/

Fournir aussi un court glossaire EN/FR des annonces de boucle vocale. L'Université d'Ottawa
est bilingue, mais les annonces restent en anglais pour toutes les équipes ;
le glossaire en explique le sens en français.]

### 1.1 Annonces standard

[Claude Code : produire un tableau de 12 lignes — annonce · signification · réponse.
Exemples : « Comm check 1-2-3 », « Standby plus 30 », « TTC report »,
« AOS in 2 », « Pass closed ».]

### 1.2 Protocole GO/NO-GO

[Claude Code : 150 mots. Le FD interroge chaque poste ; chaque poste
répond GO, NO-GO avec motif, ou HOLD avec motif. Le FD prend
la décision. Aucune commande sans autorisation explicite du FD.]

---

## 2. Revue commentée des procédures

### 2.1 NOM-001 Ouverture de passage

[Claude Code : faire parcourir aux étudiants la procédure
`procedures/nominal/startup.md` étape par étape. Montrer comment chaque étape
correspond à des actions dans l'interface du MCS. Environ 350 mots plus des captures d'écran annotées du MCS.]

### 2.2 CTG-003 Rétablissement après perte de liaison TTC

[Claude Code : faire parcourir aux étudiants
`procedures/contingency/ttc_link_loss.md`. Insister sur la
boucle détection / évaluation / reprise. Environ 350 mots plus des captures d'écran annotées du MCS
montrant le panneau FDIR et la télémesure d'état de la liaison.]

---

## 3. Entraînement à la passation de consignes (NOM-012)

[Claude Code : 150 mots. Utiliser la procédure `nominal/shift_handover.md`.
Chaque équipe effectue deux passations — le FD sortant briefe le FD entrant
à l'aide du modèle NOM-012 — et l'enseignant les chronomètre. Objectif :
moins de 6 minutes.]

---

## 4. Atelier de dynamique du vol

[Claude Code : 400 mots plus trois figures Python. Exercices de
l'atelier :

1. Lire l'orbite (TLE dans `configs/eosat1/orbit.yaml`) ; calculer
   la période et le nombre de révolutions par jour ; prédire les horaires d'AOS d'Iqaluit sur les 24 h à venir.
2. Calculer la durée de passage en fonction de l'élévation maximale ; montrer
   le passage polaire typique de 8–12 minutes.
3. Expliquer l'éclipse : où elle commence sur l'orbite, combien de temps elle dure,
   quelles en sont les conséquences en puissance et en thermique.

Figures (utiliser la feuille de style de la charte graphique de `outputs/sample_figures/`) :

- Trace au sol + cônes de visibilité d'Iqaluit et de Troll
- Profil d'élévation en fonction du temps pour un passage typique d'Iqaluit
- Fraction d'éclipse sur une fenêtre de 24 h]

---

## 5. Répétitions à blanc

### Répétition à blanc 1 — passage nominal

- **Scénario :** BP-1 (Nominal après recette en orbite).
- **Durée :** 90 min de temps réel, 90 min de temps simulé (vitesse 1×).
- **Procédures attendues :** NOM-001 → NOM-002 (prise de vue) → NOM-003
  (transmission des données au sol) → NOM-009 (bilan de santé de routine) → LOS.
- **Injection de panne :** aucune.
- **Productions :** main courante des opérateurs ; l'équipe d'observation utilise
  uniquement la fiche d'évaluation par les pairs *Communications*.

### Répétition à blanc 2 — passage nominal avec une panne

- **Scénario :** BP-1 avec une panne facile injectée vers T+30 min.
- **Injection recommandée :** `eps_overcurrent.yaml` sur la ligne
  `payload` (impose CTG-012 *Traitement d'une surintensité*).
- **Critère de réussite du passage côté opérateur :** anomalie détectée, isolée, et
  procédure CTG-012 exécutée ; le passage se poursuit jusqu'au LOS.
- **Productions :** main courante des opérateurs + fiche d'anomalie ; l'équipe d'observation
  utilise la fiche d'évaluation par les pairs *Technique*.

---

## 6. Quiz de formation aux opérations

[Claude Code : produire une épreuve de 15 questions (QCM + réponses courtes), 30
minutes. Thèmes :

- Discipline de boucle vocale (3 questions)
- Navigation dans l'interface du MCS (3 questions)
- Interprétation de la télémesure — limites et SID (3 questions)
- Structure des procédures — contenu d'un fichier de procédure (2 questions)
- Étapes du traitement des anomalies (2 questions)
- Horaires de passage — calculs AOS / TCA / LOS (2 questions)

Corrigés sur une page séparée pour le dossier de l'enseignant.]

---

## 7. Lectures attendues pour le mercredi

> **Lectures attendues avant la journée LEOP du mercredi.** Lisez les sections
> 1 – 4 de l'extrait destiné aux étudiants du *dossier de l'enseignant de la journée LEOP*
> (version expurgée de `sim_leop_instructor.md`). Temps de
> lecture estimé : 30 minutes. Lisez en entier les procédures **LEOP-001, LEOP-002,
> LEOP-006, LEOP-007**
> (`procedures/leop/*.md`). Temps de lecture estimé : 30 minutes.

---

## 8. Outils, fichiers et références

### Fichiers du simulateur cités

- `configs/eosat1/procedures/nominal/startup.md`
- `configs/eosat1/procedures/contingency/ttc_link_loss.md`
- `configs/eosat1/procedures/nominal/shift_handover.md`
- `configs/eosat1/procedures/leop/*.md` (pour la lecture du soir)
- `configs/eosat1/scenarios/eps_overcurrent.yaml`

### Références ouvertes

- NASA APPEL — normes de boucle vocale et d'opérations de mission —
  https://appel.nasa.gov/
- ESA Operations, *Mission Operations Concept* —
  https://www.esa.int/Enabling_Support/Operations
- ECSS-E-ST-70-11C — *Space segment operability* —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/
- *NASA Systems Engineering Handbook* (SP-2016-6105 Rev 2), §8 —
  https://www.nasa.gov/reference/systems-engineering-handbook/
- Normes CCSDS sur les paquets spatiaux (contexte ; le PUS relève de l'ECSS-E-ST-70-41C) —
  https://public.ccsds.org/Publications/AllPubs.aspx
