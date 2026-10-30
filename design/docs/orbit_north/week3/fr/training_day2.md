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

Le manuel du cours, partie 2, §§ 9.1 et 9.2, sert de texte à la séance et de
carte de référence : le schéma d'appel (« FD, AOCS — go for star-tracker
enable » : la station appelée, puis l'appelant, puis le message), l'échange
GO/NO-GO, la règle du micro ouvert (alternat ; seul le FD passe en micro
ouvert, et il l'annonce), la discipline de la boucle, et la règle selon
laquelle le FD autorise tandis que le poste responsable commande. Faire les
trois exercices du §9.2 : schéma d'appel, GO/NO-GO avec suspension, et annonce
d'anomalie.

Les annonces restent en anglais pour tous les équipages. L'édition française
du manuel donne la signification de chaque annonce en français dans le même
tableau (§9.2, *Vocabulaire des annonces*), qui sert de glossaire anglais-français.

### 1.1 Annonces standard

Le tableau des annonces se trouve dans le manuel du cours, partie 2, §9.2,
*Vocabulaire des annonces* : 15 annonces avec leur signification et la réponse
attendue, de « Comm check 1-2-3 » à « Loop discipline », dont « Standby plus
30 », « AOS in N » et « Pass closed ». L'imprimer comme carte de la boucle
vocale.

### 1.2 Protocole GO/NO-GO

Avant toute commande qui modifie l'état du satellite, le FD interroge les
postes concernés (« AOCS, EPS, FDIR — go for ST1_POWER ? »). Chacun répond dans
l'ordre du tour de table : *Go*, *No-go, [reason]* ou *Hold, [reason]*. Le FD
décide et l'annonce sur la boucle : « Go for ST1_POWER » ou « Hold on
ST1_POWER, [reason] ». Le poste responsable ne commande que sur ce GO explicite.
Préparer la commande (première clé) avant le GO est permis ; l'émettre avant
le GO est une violation. Source : manuel du cours, partie 2, §9.2, *Protocole
GO / NO-GO*.

---

## 2. Revue commentée des procédures

### 2.1 NOM-001 Ouverture de passage

Le manuel du cours, partie 2, §9.3, déroule NOM-001 étape par étape face au
MCS : les calculs préalables, la liste de contrôle, les post-conditions, les
écarts courants, et les fiches que le MCS peut exécuter seul. L'utiliser comme
texte de la séance, avec `procedures/nominal/startup.md` ouvert sur la page PRC
pour que les étudiants voient chaque étape devenir une ligne du panneau.

### 2.2 CTG-003 Rétablissement après perte de liaison TTC

Le manuel du cours, partie 2, §9.4, en est le déroulé : la figure de
l'échelle d'escalade (vérifier que la station sol poursuit, commander en aveugle
le transpondeur principal, basculer sur le redondant, réessayer le principal,
vérifier, escalader vers EMG-004), la liste de contrôle à lire et exécuter, la
raison de cette structure, et ce que les opérateurs oublient souvent. La boucle
à souligner est détecter (`ttc.link_status`, 0x0501, quitte 2) → évaluer (sol ou
espace ?) → rétablir (l'échelon le moins intrusif d'abord).

---

## 3. Entraînement à la passation de consignes (NOM-012)

Le manuel du cours, partie 2, §9.5, donne le modèle de NOM-012 et
l'exercice. Chaque équipe effectue deux passations : le FD sortant informe le
FD entrant de l'état du satellite, des anomalies ouvertes, des travaux en cours
et du plan du prochain passage ; le FD entrant le relit mot pour mot ; puis
l'autorité est transmise sur la boucle. L'enseignant chronomètre chacune.
Objectif : moins de 6 minutes.

---

## 4. Atelier de dynamique du vol

> **À FAIRE (auteur) :** Rédiger l'atelier de dynamique du vol de 400 mots et
> ses trois figures Python (trace au sol avec les cônes de visibilité des cinq
> stations ; élévation en fonction du temps pour un passage typique
> d'Iqaluit ; fraction d'éclipse sur une fenêtre de 24 h). Exercices : lire le
> TLE de `configs/eosat1/orbit.yaml` et calculer la période (94,5 min) et le
> nombre de révolutions par jour (15,24) ; prédire les heures d'AOS
> d'Iqaluit sur les 24 h suivantes ; durée du passage en fonction de
> l'élévation maximale (9,3 min au zénith à 513 km avec le masque de 5°,
> 7,5 min en moyenne) ; où commence l'éclipse, combien de temps elle dure
> (33,2 à 35,2 min sur l'année), et ses conséquences sur la puissance
> et la thermique. Le manuel du cours, partie 2, §9.6 et §§ 13.2 et 13.3,
> contient déjà les calculs.

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

> **À FAIRE (auteur) :** Rédiger l'épreuve de 15 questions (QCM et réponses
> courtes, 30 minutes), avec les corrigés sur une page distincte pour le
> dossier de l'enseignant : discipline de la boucle vocale (3 questions),
> navigation dans le MCS (3), interprétation de la télémesure — limites et
> SID (3), structure des procédures (2), réponse aux anomalies (2), et
> chronologie des passages — calcul de l'AOS, du TCA et du LOS (2).

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
