---
title: "Spécification des points de reprise du simulateur — semaine 3"
subtitle: "ORBIT NORTH · semaine 3 · états de scénario du simulateur"
course-codes: "GNG 3100 · SYS 5186"
term: "Été 2026"
version: "v1 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
audience: "enseignant + opérateur du simulateur"
---

# Semaine 3 — spécification des points de reprise du simulateur

Ce document spécifie les quatre états du simulateur dont la semaine 3
d'ORBIT NORTH a besoin. Trois d'entre eux existent déjà sous forme de
fichiers de scénario YAML dans
`~/SpaceMissionSimulation/configs/eosat1/scenarios/`. Le quatrième doit être
créé.

Pour chaque point de reprise, nous indiquons :
- **Objet** — la séance de la semaine 3 qu'il sert ;
- **Phase de mission** — numéro de phase d'EOSAT-1 (0=PRE_SEPARATION,
  3=BOOTLOADER_OPS, 4=LEOP, 5=COMMISSIONING, 6=NOMINAL) ;
- **État du satellite** — lignes d'alimentation, mode SCAO, antennes, charge utile, batterie ;
- **Géométrie de passage** — station sol concernée, nombre de minutes avant l'AOS ;
- **Scénario existant** — chemin du fichier YAML à utiliser, ou **NOUVEAU**.

---

## BP-1 — Nominal après recette en orbite *(existant)*

**Objet.** Tour de rôle de la journée de formation 1, répétitions à blanc de la
journée de formation 2, et exemple de *quart nominal* utilisé pour se
familiariser avec les procédures.

**Phase de mission.** 6 (NOMINAL).

**État du satellite.**

- Toutes les antennes déployées ; TT&C sur l'échelon LOW (16 kbit/s) pour les
  contacts de routine, HIGH (128 kbit/s) uniquement pour les vidages au-dessus de 10° d'élévation.
- Mode SCAO : NOMINAL (4, pointage nadir), vitesses angulaires < 0,01 °/s, roues de réaction
  lancées.
- EPS : batterie à 90 % de SoC, générateurs solaires nominaux, toutes les lignes d'alimentation principales sur ON.
- TCS : réchauffeurs pilotés par thermostat, toutes les zones dans la plage verte.
- Charge utile : imageur en STANDBY, refroidisseur du FPA arrêté (le STANDBY ne le
  fait pas tourner ; NOM-002 le met en marche environ 10 min avant une fenêtre de prise de vue).
- OBDH : image applicative en cours d'exécution (`obdh.sw_image` = 1), FDIR activée.

**Géométrie de passage.** La valeur par défaut de `nominal_ops.yaml` laisse le
propagateur d'orbite générer des passages naturels. Pour la journée de formation 1,
l'enseignant choisit une époque de départ environ 10 min avant le prochain AOS
d'Iqaluit, afin que les stagiaires voient un passage complet jusqu'au LOS.

**Scénario existant.** `scenarios/nominal_ops.yaml`. Aucune modification nécessaire.

---

## BP-2 — Début de la journée LEOP *(existant)*

**Objet.** Journée de simulation du mercredi 19 août.

**Phase de mission.** 3 (BOOTLOADER_OPS).

**État du satellite.**

- OBC exécutant le micrologiciel du chargeur d'amorçage, émettant la TM balise (SID 11
  uniquement) sur l'APID du chargeur d'amorçage.
- Toutes les autres lignes d'alimentation sur OFF : ttc_tx en mode balise seule,
  aocs_wheels OFF, payload OFF, fpa_cooler OFF, htr_bat OFF, htr_obc OFF.
- Antennes PAS encore déployées — seule l'antenne patch de la balise est
  disponible.
- SCAO en mode OFF, avec des vitesses de culbutage résiduelles d'environ 1–2 °/s dues à
  l'impulsion de séparation (déjà partiellement amorties).
- Batterie EPS à environ 85 % de SoC, générateurs solaires nominaux mais pointage
  solaire non contrôlé.
- TCS : passif uniquement, toutes les zones à température ambiante environ.

**Géométrie de passage.** Passage d'Iqaluit commençant à T+0 du scénario ;
l'enseignant règle l'horloge du simulateur de sorte que l'AOS ait lieu au
début du scénario.

**Scénario existant.** `scenarios/first_contact.yaml`. L'indicateur
`override_passes: true` de ce fichier garantit une visibilité continue
pendant toute la durée nécessaire à l'équipe.

**Critères de passage côté opérateur pour la journée.** À la fin du deuxième passage
(changement d'équipe), le satellite doit être en phase 4 (LEOP), antennes
déployées, logiciel applicatif amorcé, heure réglée, et toutes les lignes d'alimentation nécessaires à
l'amortissement (htr_bat, aocs_wheels) sur ON.

---

## BP-3 — Début de la journée de recette en orbite *(NOUVEAU — à créer)*

**Objet.** Journée de simulation du jeudi 20 août. La mission vient de
sortir de la LEOP — antennes déployées, logiciel applicatif en cours d'exécution, amortissement
terminé, heure réglée, mais aucune activité de recette en orbite n'a commencé.

**Phase de mission.** 4 (LEOP terminée) → passe en 5
(COMMISSIONING) dès que l'équipe commande le changement de phase.

**État du satellite requis au début du scénario.**

- Toutes les antennes DÉPLOYÉES.
- Logiciel applicatif EN COURS D'EXÉCUTION, télémesure de servitude (HK) complète active (tous les SID 1–N émis toutes les 4 s).
- Mode SCAO : DETUMBLE terminé, vitesses angulaires < 0,05 °/s, roues de réaction
  ALIMENTÉES mais à 0 tr/min.
- Batterie EPS à 90 % de SoC ; bus principal nominal ; payload OFF ; fpa_cooler OFF ;
  htr_bat ON ; htr_obc ON ; htr_payload OFF.
- TCS : zone charge utile à environ +5 °C (pas encore de contrôle actif) ; FPA à température ambiante.
- OBDH : phase 4, FDIR partiellement configurée (jeu LEOP uniquement), FDIR
  nominale pas encore activée.
- Temps : horloge de bord synchronisée.

**Géométrie de passage.** Premier passage d'Iqaluit commençant à T+0 du scénario.

**YAML proposé à ajouter au simulateur** —
`configs/eosat1/scenarios/commissioning_day_start.yaml` :

```yaml
name: "Commissioning Day Start"
difficulty: INTERMEDIATE
duration_s: 14400          # 4 hours of compressed time across multiple passes
briefing: |
  EOSAT-1 has just exited LEOP. Antennas are deployed, app SW is
  running, detumble has completed, time is set, and the spacecraft
  is in phase 4 with FDIR configured for the LEOP-only fault set.
  Your shift covers the first 4 hours of commissioning across
  ~4 ground passes (compressed).
  Goals for the shift:    1. Transition the spacecraft to phase 5 (COMMISSIONING) if LEOP-003 has not.    2. Run COM-001, COM-002, COM-004, COM-003, then COM-005 to COM-008.
    3. Power on the payload, cool the FPA, and complete COM-012
       (First Light) before LOS at end of pass 4.

initial_conditions:
  spacecraft_phase: 4
  override_passes: true
  soc_pct: 90.0
  power_lines:
    ttc_tx: true
    htr_bat: true
    htr_obc: true
    aocs_wheels: true
    payload: false
    fpa_cooler: false
    prop: false
  params:    0x020F: 3        # aocs.mode = COARSE_SUN (COM-004 enables the wheels and commands NOMINAL 4)
    0x0600: 0        # payload.mode = OFF

events:
  - time_offset_s: 600
    action: message
    params:
      text: "Optional: easy anomaly - inject eps overcurrent on line 3 during COM-009 payload power-on"

  - time_offset_s: 5400
    action: message
    params:
      text: "Optional: medium anomaly - inject tcs cooler_failure during COM-010 FPA cool-down"

expected_responses:
  - { category: command, description: "Declare COMMISSIONING: SYS_SET_MISSION_PHASE(phase=5) (S8 func_id 120)" }
  - { category: command, description: "Run COM-001 EPS Checkout" }  - { category: command, description: "Run COM-004 AOCS Actuator Checkout, then COM-003 AOCS Sensor Calibration (ruling Q16)" }
  - { category: command, description: "Run COM-005 AOCS Mode Transitions" }
  - { category: command, description: "Run COM-006 TTC Link Verification" }
  - { category: command, description: "Run COM-008 FDIR Configuration — enable S12 monitoring (MON_ENABLE) and verify the S12/S19 rule sets; there is no table to load" }
  - { category: command, description: "Run COM-009 Payload Power On" }
  - { category: command, description: "Run COM-010 FPA Cooler Activation" }
  - { category: command, description: "Run COM-012 First Light — capture and assess one image" }
```

**Critères de passage côté opérateur pour la journée.** Deux des quatre passages doivent
se dérouler avec le refroidisseur du FPA sur ON ; la première lumière doit être acquise ou formellement
reportée avec justification avant la fin du passage 4.

---

## BP-4 — Branche « Et si ? » de fin de simulation *(facultatif)*

**Objet.** Clôture du vendredi. Permet à l'enseignant de rejouer un point de
décision du mercredi ou du jeudi avec un autre choix d'équipe, afin de rendre le
débriefing concret.

**Mise en œuvre.** Le simulateur prend déjà en charge les instantanés d'état.
L'enseignant prend un instantané au moment de la décision (p. ex. juste
avant que l'équipe ne s'engage dans le passage en mode survie) ; pendant la clôture du vendredi, la
simulation est restaurée à partir de cet instantané et une autre équipe commande
la branche alternative. Aucun nouveau fichier de scénario n'est nécessaire.

**Procédure.** Il n'existe pas d'outil en ligne de commande `sim`. Les points
de reprise s'enregistrent et se restaurent depuis la console de l'enseignant (panneau
**Breakpoints** : SAVE, puis LOAD sur le nom enregistré) ou par l'API HTTP de
l'enseignant sur le port du simulateur (8080 par défaut,
`$SMO_SIM_HTTP_PORT`) :

```
curl -X POST http://localhost:8080/api/breakpoint/save \
     -H 'Content-Type: application/json' -d '{"name": "snap_<scenario>_<event>"}'
curl -X POST http://localhost:8080/api/breakpoint/load \
     -H 'Content-Type: application/json' -d '{"name": "snap_<scenario>_<event>"}'
curl http://localhost:8080/api/breakpoints
```

Un point de reprise enregistré est écrit dans `workspace/breakpoints/<name>.json`
sous le répertoire de travail du simulateur ; il survit donc à un redémarrage.
L'enregistrement et le chargement s'exécutent tous deux entre deux pas de simulation :
une restauration ne tombe jamais au milieu d'un pas. Voir le guide de l'enseignant, §5.10.1.

---

## Annexe — conventions des fichiers de scénario

Structure YAML des scénarios EOSAT-1 (commune à tous les fichiers de
`scenarios/`) :

| Clé | Signification |
|-----|---------|
| `name` | Nom affiché |
| `difficulty` | BASIC / INTERMEDIATE / ADVANCED |
| `duration_s` | Secondes simulées (multiplicateur de temps compressé défini séparément) |
| `briefing` | Texte de briefing opérateur sur plusieurs lignes |
| `initial_conditions` | Phase du satellite, forçages d'état facultatifs, multiplicateur de vitesse facultatif |
| `events` | Liste d'événements datés, déclenchés par l'enseignant ou automatiques |
| `expected_responses` | Liste de vérification des actions opérateur utilisée par l'évaluateur |

Le nouveau fichier `commissioning_day_start.yaml` suit cette convention.
