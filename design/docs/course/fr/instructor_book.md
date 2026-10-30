# Guide de l'enseignant SpaceCDF

**Supplément à SpaceCDF_Textbook.pdf · Public : opérateur du simulateur et enseignant chargé de l'accompagnement**

Ce court volume couvre les contenus côté simulateur auxquels renvoie la
partie 2 du manuel (Opérations d'un CubeSat). Il n'est pas destiné aux stagiaires en
console ; c'est le guide d'exploitation de la personne qui pilote le simulateur et
de l'enseignant qui observe la salle.

Sommaire :

1. Mise en place du simulateur et points de reprise
2. Catalogue des scénarios d'anomalie (YAML par scénario, moments de déclenchement, réponse attendue des opérateurs)
3. Composition de plusieurs anomalies
4. Protocoles d'accompagnement et notation selon les critères de passage

---

# Chapitre 5.10 — Catalogue des scénarios

Ce chapitre constitue le menu d'injection d'anomalies de l'enseignant. Pour
chaque scénario, le tableau donne le nom du fichier YAML, le nom du scénario, la
difficulté, la durée simulée, la procédure de reprise de référence et
le moment de déclenchement recommandé (à quel moment du passage l'injecter).

## 5.10.0 Démarrer le simulateur

Le simulateur accepte `--config` (par défaut `configs/eosat1/`),
`--speed` (par défaut 1.0), `--host` et **`--port`**. `--port`
prend par défaut la valeur de `$SMO_SIM_HTTP_PORT`, puis **8080** ; le MCS et
le planificateur ont leur propre `--port` : si le port 8080 est déjà utilisé
sur la machine d'enseignement, déplacez le simulateur plutôt que les clients :

```
python -m smo_simulator --config configs/eosat1/ --port 8081 --speed 1.0
```

Deux règles d'exploitation conditionnent tout ce qui suit :

* **Au-delà de la LEOP, le changement de phase est une télécommande de vol.** Rien à
  bord ne fait avancer la phase au-delà de 4 (LEOP) : l'équipe déclare
  COMMISSIONING (5) et NOMINAL (6) avec `SYS_SET_MISSION_PHASE(phase=N)`
  (S8.1 fonction 120 ; l'indicateur FORCE autorise un retour en arrière). La commande
  `set_phase` de la console instructeur (phases 0–6) est un forçage de l'enseignant pour
  préparer ou réparer une séance, et `SET_PHASE` n'est l'alias de rien
  — attendez-vous à ce que l'équipe envoie la fonction 120 à la fin de LEOP-007 et de COM-013.
* Les commandes instructeur (`set_speed`, `freeze`, `resume`, `inject`,
  `clear_failure`, `override_passes`, `set_phase`, les appels
  `scenario_*`, l'enregistrement et le chargement des points de reprise) passent par le canal HTTP
  instructeur. Ce canal **rejette les télécommandes du satellite
  avec une erreur HTTP 403** — les vraies TC doivent passer par le MCS.

## 5.10.1 Points de reprise (4)

Les points de reprise sont des instantanés nommés de l'état complet, enregistrés et rechargés depuis
l'interface instructeur (`/api/breakpoint/save`, `/api/breakpoint/load`).
Un enregistrement qui ne parvient pas à sérialiser tous les composants échoue purement et simplement
au lieu d'écrire un instantané partiel.

| ID | Nom | Phase | Usage |
|---|---|---|---|
| BP-1 | Nominal après recette en orbite | 6 (NOMINAL) | Entraînement aux passages de routine (`scenarios/nominal_ops.yaml`) |
| BP-2 | Début de la journée LEOP | 3 (BOOTLOADER) | jour 3 (`scenarios/first_contact.yaml`) |
| BP-3 | Début de la journée de recette en orbite | 4 (LEOP terminée) | jour 4 (`scenarios/commissioning_day_start.yaml` — rédigé par l'enseignant, voir ci-dessous ; ne fait pas partie du jeu livré) |
| BP-4 | Branche « Et si ? » | (toute phase) | rejeu du jour 5 — enregistrer un point de reprise avant le point de décision, puis le recharger depuis l'interface instructeur |

### YAML du scénario BP-3 à ajouter au simulateur

Rédigé selon le schéma que le chargeur accepte réellement.
`initial_conditions` ne prend en charge que `spacecraft_phase`, `speed`,
`override_passes`, `soc_pct`, `power_lines` (par nom de ligne),
`params` (par identifiant numérique de paramètre) et `failures`. Les événements doivent utiliser
`time_offset_s` (ou une `condition`) plus l'une des actions
prises en charge — `inject`, `clear`, `set_parameter`, `message`,
`set_speed`, `set_phase`. Tout le reste est ignoré au chargement et
signalé par un événement `SCENARIO_CONFIG_INVALID` : un scénario
d'apparence correcte peut donc, sans bruit, ne rien faire. `difficulty` doit valoir
BASIC / BEGINNER / INTERMEDIATE / ADVANCED.

```yaml
name: "Commissioning Day Start"
difficulty: INTERMEDIATE
duration_s: 14400          # 4 hours of compressed time across multiple passes
briefing: |
  EOSAT-1 has just exited LEOP. The S-band antenna is deployed, the
  application image is running, detumble has completed, time is set,
  and the spacecraft is in phase 4 (LEOP) holding COARSE_SUN.
  Your shift covers the first 4 hours of commissioning across
  ~4 ground passes (compressed).
  Goals for the shift:
    1. Complete the commissioning entry criteria and call for the
       phase advance to 5 (COMMISSIONING). The instructor performs
       that advance on the console — there is no telecommand.
    2. Run COM-001 through COM-008 in order.
    3. Power on the payload, cool the FPA to its -15 C setpoint, and
       complete COM-012 (First Light) before LOS at end of pass 4.

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
  params:
    0x020F: 3        # aocs.mode = COARSE_SUN
    0x0600: 0        # payload.mode = OFF

events:
  - time_offset_s: 600
    action: message
    params:
      text: "Optional: inject eps overcurrent on line 3 during COM-009 payload power-on"
  - time_offset_s: 5400
    action: message
    params:
      text: "Optional: inject tcs cooler_failure during COM-010 FPA cool-down"

expected_responses:
  - { category: command, description: "Report commissioning entry criteria met and request the console phase advance to 5" }
  - { category: command, description: "Run COM-001 EPS Checkout" }
  - { category: command, description: "Run COM-005 AOCS Mode Transitions (COARSE_SUN 3 -> NOMINAL 4 -> FINE_POINT 5)" }
  - { category: command, description: "Run COM-006 TTC Link Verification (LOW 16 kbps / HIGH 128 kbps)" }
  - { category: command, description: "Run COM-008 FDIR Configuration — verify and exercise the rule set; there is no table to load" }
  - { category: command, description: "Run COM-009 Payload Power On (EPS_POWER_ON line_index=3, then PAYLOAD_SET_MODE mode=1)" }
  - { category: command, description: "Run COM-010 FPA Cooler Activation (FPA_COOLER on=1, S8 func 43)" }
  - { category: command, description: "Run COM-012 First Light — capture and assess one image" }
```

Les anomalies facultatives sont laissées sous forme de repères `message` plutôt que d'injections
pré-armées, afin que l'enseignant garde la décision. Injectez-les en direct
depuis l'interface instructeur le moment venu.

## 5.10.2 Catalogue des scénarios d'anomalie (36)

Chaque fichier ci-dessous existe dans `configs/eosat1/scenarios/`. Les durées
simulées sont la valeur `duration_s` du fichier.

| Fichier | Difficulté | Durée simulée | Effet | Procédure de référence | Jour suggéré |
|---|---|---|---|---|---|
| `aocs_actuator_stuck.yaml` | Moyen | continu | Grippe une roue de réaction (`rw_seizure`) — 4 roues sont embarquées, il en reste donc 3 | CTG-026 / CTG-007 | jour 3, LEOP |
| `aocs_sensor_cascade.yaml` | Difficile | 2700 s | Panne de ST1, panne de la tête CSS +X, panne du magnétomètre, puis à T+600 s un **biais gyrométrique persistant de 0,05 °/s** sur les trois voies | CTG-008 → CTG-002 | jour 4 |
| `aocs_star_tracker_failure.yaml` | Moyen | continu | Panne franche du senseur stellaire | CTG-008 | jour 3 ou 4 |
| `aocs_wheel_failure.yaml` | Difficile | continu | Défaillance du roulement d'une roue en milieu de passage | CTG-007 | jour 4 (enchaîner avec `transponder_failure.yaml`) |
| `eps_anomaly.yaml` | Moyen | variable | Défaut EPS générique, souvent associé à `eps_undervoltage` | CTG-001 / CTG-012 | jour 3 ou 4 |
| `eps_overcurrent.yaml` | Facile | continu | Surintensité persistante sur la ligne choisie | CTG-012 | jours 2, 3, 4 |
| `eps_progressive_load_shed.yaml` | Difficile | 1800 s | Un élément de batterie se dégrade, impose un délestage progressif | CTG-001 | jour 4 |
| `eps_solar_panel_loss.yaml` | Difficile | continu | Panne d'une chaîne du générateur solaire | CTG-001 | jour 3 |
| `eps_undervoltage.yaml` | Moyen | continu | La tension descend sous la plage d'attention | CTG-001 | jour 3 ou 4 |
| `first_contact.yaml` | (BP-2) | 5400 s | Scénario de début de la journée LEOP | — | jour 3 |
| `fpa_overtemp.yaml` | Moyen | 1200 s | Refroidisseur du FPA sous-performant : il ne peut pas tenir la consigne commandée (par défaut **−15 °C** ; enveloppe de −20 à 0 °C), de sorte que `payload.cooler_margin_k` (0x064B) devient ≤ 0 | CTG-004 | jour 4 |
| `gs_antenna_failure.yaml` | Très difficile | continu | Panne de l'antenne sol principale en milieu de passage | CTG-020 (fiche **consultative** — côté sol uniquement, aucune TC vers le satellite) | jour 4 |
| `gs_rf_degradation.yaml` | Facile | 600 s | Le TEB augmente au cours du passage | CTG-014 / CTG-003 | jour 3 |
| `gs_tracking_loss.yaml` | Moyen | 300 s | L'antenne sol perd brièvement la poursuite | CTG-020 | jour 3 ou 4 |
| `nominal_ops.yaml` | (BP-1) | continu | Satellite sain pour s'exercer aux outils | — | jours 1, 2 |
| `obc_bus_failure.yaml` | Difficile | continu | Perte du bus CAN A | CTG-017 | jour 3 |
| `obc_crash.yaml` | Difficile | ponctuel | Plantage du logiciel applicatif de l'OBC, redémarrage nécessaire | CTG-010 | jour 3 |
| `obc_watchdog.yaml` | Difficile | ponctuel | Événement chien de garde en cours de procédure | CTG-010 | jour 3 |
| `obdh_bootloader_recovery.yaml` | Moyen | continu | Le chargeur d'amorçage ne parvient pas à lancer le logiciel applicatif | propre au chargeur d'amorçage | jour 3 |
| `obdh_bus_isolation.yaml` | Moyen | continu | Isolation d'un nœud CAN de sous-système | CTG-017 | jour 3 |
| `payload_corrupt_image.yaml` | Moyen | ponctuel | L'image suivante revient corrompue | CTG-015 | jour 4 |
| `payload_memory_failure.yaml` | Difficile | continu | Erreurs ECC croissantes sur la mémoire de masse | propre à la charge utile | jour 4 |
| `rw_bearing.yaml` | Moyen | progressif | Usure du roulement d'une roue, le courant augmente au fil des heures | CTG-007 | jour 4 |
| `separation.yaml` | (LEOP) | ponctuel | Événement de séparation | — | sans objet en semaine 3 |
| `separation_sequence.yaml` | (LEOP) | ponctuel | Séparation complète jusqu'à l'amortissement | — | sans objet en semaine 3 |
| `sequential_checkout.yaml` | (recette en orbite) | continu | Déroulé de LEOP-007 | — | référence pour le jour 3 |
| `transponder_failure.yaml` | Difficile | continu | Panne du transpondeur bande S | CTG-003 → **EMG-004** (Perte de communication) | jour 4 |
| `ttc_no_tm_at_aos.yaml` | Facile | continu | Balise UHF présente mais pas de HK en bande S — ce sont deux radios distinctes | CTG-019 | jour 3 |
| `ttc_pa_overheat.yaml` | Moyen | progressif | Surchauffe de l'amplificateur de puissance bande S | CTG-003 | jour 3 ou 4 |
| `debris_impact_hermes3.yaml` | Difficile | ponctuel | Étude de cas de conjonction / d'impact de débris | CTG-028 / NOM-004 | jour 3 ou 4 |
| `scenario_2_cerise_adcs_fault.yaml` | Difficile | continu | Étude de cas d'une panne SCAO de type Cerise | CTG-002 | jour 4 |
| `prop_slow_leak.yaml` | Moyen | progressif | Fuite lente d'ergol, pression du réservoir en baisse | CTG-028 | jour 3 ou 4 |
| `prop_underperformance.yaml` | Moyen | ponctuel | La poussée fournit moins de Δv que prévu | CTG-028 → replanification NOM-004 | jour 3 ou 4 |
| `prop_valve_stuck_open.yaml` | Difficile | continu | Vanne d'isolement bloquée ouverte | CTG-028 | jour 4 |
| `prop_burn_eclipse_power.yaml` | Difficile | ponctuel | Manœuvre tentée dans un creux de puissance dû à l'éclipse | CTG-028 / CTG-001 | jour 4 |
| `prop_attitude_loss_mid_burn.yaml` | Très difficile | ponctuel | L'erreur d'attitude dépasse la limite de poussée en cours d'allumage ; interruption à bord | CTG-028 → CTG-002 | jour 4 |

**EO-Sat-1 embarque une propulsion.** Un système à monergol vert de 1U, 66,9 m/s au total,
pour l'évitement de débris et un maintien d'orbite limité (pas pour la désorbitation
en fin de vie). Les télécommandes de propulsion sont les fonctions S8 108–118, la base de
télémesure est 0x0B00, le SID de HK est le **9**. Une poussée réajuste le jeu d'éléments SGP4, de sorte que
les passages et les éclipses se décalent réellement ensuite (1 m/s donne Δa
+1,800 km et −33,5 s à +24 h), et l'accélération du temps est limitée
à ≤ 10× pendant une poussée. Ne décrivez pas cette mission comme
dépourvue de propulsion.

### Injections de pannes sans fichier de scénario

L'interface instructeur peut injecter directement toute panne que les modèles mettent en œuvre,
sans scénario. Celles qu'il faut connaître cette semaine :

| Sous-système | Injection | Effet |
|---|---|---|
| eps | `sada_stuck` | Grippe l'entraînement du générateur solaire. `eps.solar_array_drive_angle` (0x0133) reste plat tandis que les courants des ailes (0x0146 / 0x0147) se mettent à varier au rythme de l'orbite — la production tombe à celle d'ailes fixes |
| eps | `solar_panel_loss`, `bus_short`, `overcurrent`, `undervoltage`, `bat_cell` | l'échelle EPS |
| aocs | `gyro_bias` | Décalage de vitesse **persistant** — voir 18.10 |
| aocs | `rw_seizure`, `rw_bearing`, `st_failure`, `st_blind`, `mag_failure`, `css_head_fail`, `mtq_failure` | le jeu SCAO |
| tcs | `cooler_failure`, `heater_stuck_on`, `heater_open_circuit`, `sensor_drift` | le jeu thermique |
| ttc | `primary_failure`, `pa_overheat`, `high_ber`, `antenna_deploy_failed`, `gs_*` (côté sol) | le jeu liaison |
| obdh | `watchdog_reset`, `obc_crash`, `bus_failure`, `stuck_in_bootloader` | le jeu plateforme |

## 5.10.3 Règles de composition de plusieurs anomalies

Si vous enchaînez deux scénarios, le second ne se déclenche qu'une fois le
premier acquitté (ou après un délai fixe s'il ne l'est pas). Enchaînements
recommandés :

- `aocs_wheel_failure.yaml` + `transponder_failure.yaml` — teste
  le traitement d'anomalies touchant plusieurs systèmes. Jour 4, très difficile.
- `eps_overcurrent.yaml` (ligne charge utile) + `payload_corrupt_image.yaml`
  — teste une anomalie persistante + un effet en cascade. Jour 4, moyen à difficile.
- `gs_antenna_failure.yaml` (Iqaluit) + `gs_rf_degradation.yaml`
  (Troll au passage suivant) — oblige l'équipe à travailler avec des moyens sol
  dégradés uniquement. Jour 4, très difficile.

N'enchaînez pas *trois* anomalies, sauf si la promotion est exceptionnelle ;
la charge cognitive dépasse l'intention pédagogique de la semaine de formation en salle de contrôle.

---

---

# Chapitre 2 — Journée de simulation de mission (déroulé pour l'enseignant)

> **Lectures attendues avant cette séance.** Cal Poly CDS Rev 14, §5 (ICD de lancement) ; SMAD4, chap. 18.



**Prérequis :** séances 5.1-5.2 (segment sol conçu, concepts d'opérations définis)
**Références :** ECSS-E-ST-70-11C (*Operability*), ECSS-E-ST-70-32C (*Procedures*), ESA *OPS-G Training Manual*, NASA *Mission Operations Directorate Training Handbook*

---

## Objectifs d'apprentissage

À la fin de cette séance, les participants seront capables de :
1. Exécuter une séquence LEOP simulée, de la séparation jusqu'à la première télémesure
2. Mener des activités de recette en orbite à l'aide des procédures opérationnelles
3. Réagir aux anomalies injectées à l'aide de l'architecture FDIR et des procédures de contingence
4. Documenter en temps réel le traitement des anomalies à l'aide de formulaires structurés
5. Conduire des opérations scientifiques nominales avec un suivi en direct du bilan de données

---

## 1. Vue d'ensemble de la simulation et rôles
Cette séance est une **simulation pratique** des opérations de mission. L'animateur joue « l'Univers » -- il injecte des événements, des anomalies et des sauts dans le temps. L'équipe exploite la mission à l'aide de SpaceCDF et de ses procédures du chapitre 5.2.

### Attribution des rôles

| Rôle | Responsabilité | Fonction SpaceCDF utilisée |
|------|---------------|---------------------|
| **Directeur de vol (FD)** | Autorité de décision globale ; coordonne l'équipe | Tableau de bord, tous les onglets |
| **Contrôleur satellite (SC)** | Envoie les commandes ; surveille la télémesure de servitude | Éditeur de ConOps, commande des modes |
| **Opérateur de station sol (GSO)** | Gère la programmation de l'antenne ; acquisition de la liaison | Bilan de données, bilan de liaison |
| **Opérateur charge utile (PO)** | Planifie et exécute les observations scientifiques | Paramètres de la charge utile, bilan de données |
| **Dynamique du vol (FD-nav)** | Surveille l'orbite ; planifie et annonce les manœuvres (EO-Sat-1 dispose d'une propulsion à monergol vert de 1U, 66,9 m/s) | Paramètres orbitaux, onglet PROP, durabilité |
| **Secrétaire des anomalies** | Documente tous les événements, anomalies et décisions | Fiche 5.3 |

*Pour les équipes plus petites, cumulez les rôles : SC+GSO et PO+FD-nav sont des associations naturelles.*

### Chronologie de la simulation

| Temps simulé | Temps réel | Phase | Événements |
|----------|----------|-------|--------|
| T+0 à T+1 h | 0-20 min | LEOP | Séparation, acquisition de la balise, déploiement, contrôle de santé |
| T+1 h à T+24 h | 20-35 min | Début de LEOP | Déploiement du générateur solaire, initialisation du SCAO, validation de la chaîne de communication |
| T+1 jour à T+7 jours | 35-50 min | Recette en orbite | Vérification des sous-systèmes, première activation de la charge utile |
| T+7 jours à T+30 jours | 50-65 min | Début de l'exploitation | Science nominale, maintien d'orbite |
| *Injection d'anomalies* | 65-85 min | Contingence | Exercice de traitement des anomalies |
| T+30 jours à T+1 an | 85-100 min | Opérations nominales | Opérations de routine, revue des données |
| Débriefing | 100-120 min | Clôture | Retour d'expérience, revue de la documentation |

---

## 2. Simulation LEOP
L'animateur raconte la simulation. Le temps est compressé. Chaque équipe exécute sa procédure LEOP.

### Script de l'animateur -- LEOP

**[T+0 -- Séparation]**
*« Votre satellite s'est séparé du déployeur. Les interrupteurs de déploiement sont libérés. La minuterie de 30 minutes a démarré. Vous êtes en silence radio -- aucune émission RF autorisée avant l'expiration de la minuterie. Que fait votre satellite en ce moment ? »*

Réponse type : la minuterie décompte. La batterie fournit l'alimentation. Aucun sous-système actif, à part l'OBC qui fait tourner la minuterie.

**[T+30 min -- Expiration de la minuterie]**
*« La minuterie de 30 minutes a expiré. Votre OBC a commandé le déploiement des antennes. Qu'attendez-vous ? »*

Attendu : commande de déploiement des antennes envoyée. La balise doit commencer à émettre.

**[T+35 min -- Premier passage au-dessus de la station sol]**
*« Votre station sol de [lieu] a le satellite en visibilité. L'opérateur d'antenne signale : porteuse détectée à [fréquence] avec un décalage Doppler de -25 kHz. Le niveau du signal est de -110 dBm. Est-ce ce que vous attendiez ? »*

Les équipes doivent vérifier :
- que la fréquence porteuse correspond à la valeur attendue (compte tenu du décalage Doppler) ;
- que le niveau du signal est cohérent avec le bilan de liaison à la distance actuelle ;
- que le débit de la balise est conforme à la conception.

**[T+40 min -- Première télémesure]**
*« Verrouillage sur la balise obtenu. Vous recevez la télémesure de servitude. Je vais vous lire la première trame HK : »*

| Paramètre | Mnémonique (id) | Valeur | Plage attendue | État |
|-----------|---------------|-------|---------------|--------|
| Tension du bus | `eps.bus_voltage` (0x0105) | 27.9 V | 26 - 30 V | Nominal |
| SoC de la batterie | `eps.bat_soc` (0x0101) | 88 % | > 50 % | Nominal |
| Production de puissance | `eps.power_gen` (0x0107) | 12 W | faible en culbutage | Nominal |
| Température de l'OBC | `tcs.temp_obc` (0x0406) | 22 °C | -5 à +45 °C | Nominal |
| Température de la batterie | `tcs.temp_battery` (0x0407) | 19 °C | +5 à +35 °C | Nominal |
| Mode SCAO | `aocs.mode` (0x020F) | 2 (DETUMBLE) | Attendu | Nominal |
| Vitesses angulaires | `aocs.rate_roll/pitch/yaw` (0x0204-06) | 1.4 deg/s | En baisse | Nominal |
| Image en cours d'exécution | `obdh.sw_image` (0x0311) | 0 (BOOTLOADER) | Attendu avant amorçage | Nominal |
| État de l'antenne | `ttc.antenna_deployed` (0x0520) | 0 (repliée) | déployée dans LEOP-007 | -- |
| Balise | `ttc.beacon_active` (0x0527) | 1 | Attendu | Nominal |
| État de la liaison | `ttc.link_status` (0x0501) | 2 (LOCKED) | 2 = LOCKED | Nominal |
| État de la liaison montante | -- | Pas encore tentée | -- | -- |

Remarque sur le bus : EO-Sat-1 utilise une batterie **8S de 100 Wh** — 21,5 V à vide,
26,4 V en nominal, 29,2 V à pleine charge, avec un bus d'environ 28 V. Une lecture de 7-8 V
correspond à un CubeSat 2S, pas à ce satellite. La FDIR de sous-tension se déclenche à
**24,5 V**.

*« Tous les paramètres sont nominaux. Poursuivez la séquence LEOP. »*

**[T+1 h -- Validation de la liaison montante]**
*« Vous tentez maintenant votre première commande en liaison montante. Envoyez une commande 'NOP' (aucune opération) pour vérifier la chaîne montante. »*

Les équipes doivent : composer la commande, vérifier le codage, l'émettre, attendre l'acquittement dans la télémesure.

---

## 3. Simulation de la recette en orbite
### Script de l'animateur -- Recette en orbite

**[Saut dans le temps : T+24 h]**
*« Votre satellite a terminé l'amortissement. Le SCAO est en COARSE_SUN (mode 3). Tous les paramètres HK sont nominaux après 8 passages sol. Vous êtes prêts à commencer la recette en orbite. Quelle est votre première activité ? »*

Attendu : étalonnage des capteurs SCAO (COM-003) — contrôle de validité du magnétomètre (unité unique, rien à sélectionner), état des têtes du senseur solaire, et étalonnage **à bord** du biais gyrométrique avec `AOCS_GYRO_CALIBRATION` (S8 func 13). Il n'y a pas d'envoi d'un biais calculé au sol.

**[T+3 jours -- Première lumière de la charge utile]**
*« Le SCAO est étalonné et tient le mode NOMINAL (mode 4) avec une erreur d'attitude de 0,3 degré. Vous êtes prêts pour la première lumière de la charge utile. Détaillez-moi votre procédure. »*

Les équipes exécutent leur procédure d'observation scientifique de la fiche 5.2.

**[T+5 jours -- Premier téléchargement de données]**
*« La charge utile a acquis 150 Mo d'images. Votre prochain passage dure 12 minutes au-dessus de [station]. Pouvez-vous transmettre toutes les données au sol en un seul passage ? »*

Les équipes doivent calculer :
- débit × durée du passage × efficacité protocolaire = capacité disponible ;
- comparer à 150 Mo -- déterminer si plusieurs passages sont nécessaires ;
- planifier la séquence de téléchargement.

---

## 4. Scénarios d'injection d'anomalies
L'animateur choisit 2-3 anomalies dans la liste ci-dessous, adaptées à la conception de la mission. Les équipes réagissent à l'aide de leurs règles FDIR et de leurs procédures de contingence.

### Menu des anomalies (l'animateur en choisit 2-3)

#### Anomalie A : sous-tension batterie

*« Pendant l'éclipse, vous recevez une alerte : la tension du bus est tombée à 24,2 V, sous le seuil de sous-tension FDIR de 24,5 V (la plage d'attention commence à 27,0 V et le délestage modélisé à 25,0 V). La température de la batterie est de 5 °C. Le SoC est estimé à 18 %. »*

Réponse attendue :
1. Vérifier que la FDIR a déclenché le délestage (charge utile éteinte, réchauffeurs non essentiels éteints)
2. Vérifier le bilan de puissance : la consommation dépasse-t-elle la production ?
3. Causes possibles : dégradation du générateur solaire, charge inattendue, dégradation de la batterie, éclipse longue
4. Action immédiate : vérifier le mode survie ; désactiver manuellement les charges non essentielles
5. Analyse : examiner les tendances de puissance des dernières 24 heures ; les comparer au bilan de puissance

#### Anomalie B : perte de communication

*« Vous n'avez reçu aucune télémesure lors des 3 derniers passages programmés (18 heures). La station sol indique que le pointage et la fréquence sont corrects, mais aucune porteuse n'est détectée. »*

Réponse attendue :
1. Vérifier les équipements de la station sol (antenne, LNA, modem) -- écarter une panne sol
2. Se renseigner auprès d'autres stations sol (SatNOGS) sur une éventuelle détection du signal
3. Envisager les causes : panne de l'émetteur, échec du déploiement de l'antenne, perte d'attitude (antenne mal pointée)
4. Vérifier si la balise UHF est toujours reçue. C'est une radio distincte, sur la ligne non commutable `ttc_rx` : **couper le PA supprime la TM en bande S tandis que la balise subsiste.** Balise présente + bande S muette isole la panne dans la chaîne bande S.
5. Autonomie bord : la minuterie d'absence de contact de 24 heures fera basculer sur le transpondeur redondant (FDIR TTC-01)
6. Plan : commander la chaîne d'émission en aveugle selon CTG-019 ; si toujours rien après deux passages consécutifs, passer à EMG-004 (Perte de communication)

#### Anomalie C : anomalie SCAO -- perte du pointage fin

*« `aocs.att_error` (0x0217) est passée de 0,1 degré à 5 degrés. Le senseur stellaire sélectionné signale l'état 4 (en panne). `aocs.momentum_saturation_pct` (0x0282) indique 80 % -- proche de la saturation. »*

Réponse attendue :
1. Diagnostiquer : quelle tête ? `aocs.st1_status` (0x0240) / `aocs.st2_status` (0x0243), codes 0 éteint / 1 amorçage / 2 poursuite / 3 aveuglé / 4 en panne. Contamination optique ? Soleil dans le champ de vue ?
2. Il y a **deux** senseurs stellaires -- allumer l'autre (`ST2_POWER` func 5 / `ST1_POWER` func 4) puis `ST_SELECT` (func 6) avant de conclure à une perte d'attitude.
3. Vérifier le masque de bits de la source de l'estimateur `aocs.est_source` (0x02C1) : bit0 ST, bit1 CSS, bit2 MAG, bit3 gyro.
4. Commander la désaturation avec `AOCS_DESATURATE` (S8 func 1). Prévoir **20-50 min** pour un déchargement complet, pas cinq minutes ; la prise de vue est inhibée pendant toute la durée et le satellite revient ensuite à son mode antérieur à la désaturation. Surveiller `aocs.h_body_mag` (0x02B9) et `aocs.desat_ineffective` (0x029C).
5. Si les deux têtes sont perdues : `AOCS_SET_MODE(mode=3)` COARSE_SUN, le attente sûre au Soleil.
6. Évaluation de l'impact : la science peut-elle continuer avec seulement les CSS, le magnétomètre et le gyro ?

#### Anomalie D : passage inattendu en mode survie

*« Votre satellite est passé de manière autonome en mode survie. La dernière télémesure avant ce passage montrait : compteur de redémarrages de l'OBC incrémenté de 3 en 10 minutes. Tous les autres paramètres étaient nominaux. »*

Réponse attendue :
1. Enquêter : des redémarrages multiples évoquent un SEU (aléa logique) ou un bogue du micrologiciel
2. Vérifier l'environnement radiatif : le satellite était-il dans la SAA (anomalie de l'Atlantique Sud) ?
3. Examiner les journaux FDIR (stockés en mémoire non volatile) pour identifier les déclencheurs de défaut
4. Plan de reprise : `OBC_SET_MODE(mode=0)` (S8 func 50) pour revenir en NOMINAL et `AOCS_SET_MODE` pour revenir au mode opérationnel ; renvoyer `HK_ENABLE` pour tout SID perdu lors d'un redémarrage ; surveiller toute récurrence. Noter la règle FDIR : `obdh.reboot_count` > 4 déclenche l'escalade vers l'urgence satellite.
5. En cas de récurrence : envoyer un correctif logiciel renforçant la robustesse aux SEU

#### Anomalie E : dépassement thermique

*« `payload.fpa_temp` (0x0601) est montée à +19 °C pendant une observation scientifique, hors de la plage de bon fonctionnement du FPA de −25,5 à +17,5 °C, et `payload.fpa_ready` (0x0610) est retombé à 0. `tcs.temp_battery` (0x0407) vaut 43 °C — au-delà du seuil FDIR de coupure du réchauffeur à 42 °C et proche de l'événement de surtempérature à 45 °C. »*

Réponse attendue :
1. Immédiat : désactiver la charge utile pour stopper la production de chaleur
2. Vérifier l'attitude : la face radiateur chaude est-elle tournée vers le Soleil ?
3. Revoir le modèle thermique : cette géométrie orbitale (angle bêta élevé) était-elle prévue ?
4. Atténuation : ajuster le rapport cyclique ; planifier les observations dans les portions plus froides de l'orbite
5. Si le problème est structurel : il faudra peut-être mettre à jour le modèle thermique et les contraintes opérationnelles

### Documentation des anomalies

Pour chaque anomalie injectée, les équipes remplissent le **formulaire de traitement d'anomalie** de la fiche 5.3 :

| Champ | Que consigner |
|-------|---------------|
| Heure (simulée) | Moment où l'anomalie a été détectée |
| Observation | Valeurs exactes de télémesure et symptômes |
| Évaluation initiale | **Gravité FDIR 0–4** (gravité de l'événement). À consigner séparément du **niveau d'autonomie 0–3** (qui a agi : 0 matériel, 1 logiciel du sous-système, 2 FDIR de l'OBC, 3 sol). Ces deux échelles sont distinctes et ne doivent jamais être confondues. |
| Diagnostic | Cause première présumée |
| Action entreprise | Commandes envoyées, procédures exécutées |
| Résultat | État du système après le traitement |
| Suite à donner | Investigations complémentaires, mises à jour des procédures |

---

## 5. Opérations nominales et débriefing
### Opérations nominales
**[Saut dans le temps : T+30 jours à T+1 an]**
*« Votre mission est opérationnelle depuis un mois. Toutes les activités de recette en orbite sont terminées. Vous êtes maintenant en opérations nominales. Passons en revue vos indicateurs opérationnels. »*

Les équipes présentent :
- le volume total de données transmises au sol en 30 jours par rapport au plan ;
- le nombre d'observations scientifiques réalisées par rapport au plan ;
- les anomalies rencontrées (lors de l'exercice d'injection) ;
- l'état actuel des bilans : marge de puissance (charge nominale moyenne sur l'orbite ≈ 28,7 W pour une production ≈ 38 W au pire angle bêta), marge de données, ergol restant sur les 66,9 m/s au total ;
- l'état de l'orbite : des alertes de conjonction ? La conformité aux règles sur les débris est-elle respectée ?

### Débriefing
1. **Qu'est-ce qui a bien fonctionné ?**
   - Quelles procédures ont fonctionné telles qu'écrites ?
   - Quelles règles FDIR se sont déclenchées correctement ?
   - À quels moments l'équipe a-t-elle bien communiqué ?

2. **Qu'est-ce qui pourrait être amélioré ?**
   - Quelles procédures ont dû être modifiées en temps réel ?
   - La conception de la FDIR présentait-elle des lacunes ?
   - À quels moments la prise de décision a-t-elle ralenti ?

3. **Enseignements pour la conception :**
   - La simulation a-t-elle révélé des faiblesses de conception ?
   - Faut-il modifier certaines exigences à la lumière de l'expérience opérationnelle ?
   - Quelle autonomie supplémentaire serait utile ?

---

## Notes pour l'animateur

### Préparation

- Revoir le ConOps, les règles FDIR et les procédures de chaque équipe issus du chapitre 5.2
- Choisir des anomalies adaptées au point atteint par l'équipe (p. ex. ne pas injecter d'anomalie charge utile avant que COM-009 ait mis la charge utile sous tension). EO-Sat-1 *dispose bien* d'une propulsion : les scénarios `prop_*` sont donc tous utilisables une fois NOM-004 présentée en briefing.
- Préparer les tableaux de données HK pour chaque phase (adapter les valeurs de la section 2 aux paramètres de mission de l'équipe)
- Garder des anomalies de réserve si les équipes résolvent rapidement les injections

### Rythme

- La simulation LEOP doit donner une impression d'urgence (passages courts, décisions rapides)
- La recette en orbite peut être plus détendue
- L'injection d'anomalies doit être exigeante mais soluble avec les procédures de l'équipe
- Prévoir plus de temps pour le débriefing -- c'est là que l'apprentissage est le plus profond

### Critères d'évaluation

Observer et noter (pour le retour, pas pour une notation formelle) :
- L'équipe a-t-elle suivi ses procédures ou improvisé ?
- Le directeur de vol a-t-il coordonné efficacement ?
- Le traitement des anomalies a-t-il été méthodique (détecter-diagnostiquer-planifier-exécuter-vérifier) ?
- L'équipe a-t-elle documenté les événements en temps réel ?
- Quelqu'un a-t-il identifié un défaut de conception pendant les opérations ?

---

## Synthèse de la séance

| Thème | Point clé |
|-------|-------------|
| LEOP | Les 72 premières heures sont critiques ; chaque étape est contrainte par le temps |
| Recette en orbite | Vérification méthodique des sous-systèmes avant les opérations charge utile |
| Traitement des anomalies | Suivre le processus : détecter, évaluer, diagnostiquer, planifier, exécuter, vérifier, documenter |
| Documentation | La journalisation en temps réel est essentielle -- la mémoire n'est pas fiable sous stress |
| Validation de la FDIR | La simulation révèle des lacunes de conception de la FDIR que l'analyse seule ne peut pas trouver |
| Coordination de l'équipe | Des rôles clairs, des protocoles de communication et une autorité de décision sont essentiels |
| Retour sur la conception | L'expérience opérationnelle doit alimenter la conception (exigences, FDIR, procédures) |

---

# Menus d'injection d'anomalies (déplacés des chapitres 10 et 11 du manuel)

*Ces sections sont réservées à l'enseignant : elles listent les fichiers YAML de scénario, les moments de déclenchement et les protocoles d'accompagnement pour l'injection d'anomalies pendant les journées de simulation. Les stagiaires en console ne doivent pas en prendre connaissance à l'avance.*


## Menu d'injection d'anomalies LEOP

## 10.6 Menu d'injection d'anomalies (enseignant)


## Accompagnement pendant le quart LEOP

## 10.8 Accompagnement pendant le quart


## Menu d'injection d'anomalies de la recette en orbite

## 11.6 Menu d'injection d'anomalies



---

# Chapitre 18 — Cartes d'aide aux anomalies

Pour chaque scénario des menus enseignant du jour 3 et du jour 4,
ce chapitre fournit une carte d'aide détaillée d'une page que
l'enseignant utilise pendant la simulation et que l'équipe utilise pendant
le débriefing.

Format des cartes :

- **Fichier de scénario**
- **Moment de déclenchement** (ce qui doit se dérouler dans le passage au moment où
  l'injection se déclenche)
- **Premier indice** (ce que les opérateurs verront en premier)
- **Procédure de reprise** (la réponse de référence)
- **Critère de réussite du passage** (ce qui définit une reprise réussie)
- **Cinq questions de débriefing** à poser à l'équipe après le passage

### 18.1 Absence de TM en début de passage (facile)

- **Moment de déclenchement.** Injecter à T+0 du scénario, avant toute commande
  des opérateurs. Le satellite est en BOOTLOADER_OPS ; la balise est
  présente, mais l'OBC ne produira pas de HK complète, même après
  OBC_BOOT_APP.
- **Premier indice.** SPACON voit `obdh.sw_image` (0x0311)
  passer correctement à 1 après l'étape 5, mais aucun paquet du SID 1 n'arrive
  dans l'intervalle de 1 seconde qui suit, et les SID que l'opérateur
  active ensuite avec `HK_ENABLE` (**S3.5**) — 3 (TCS, 60 s),
  4 (plateforme, 8 s), 6 (TT&C, 8 s) — n'apparaissent pas non plus.
  Attention au piège qui n'est *pas* l'anomalie : l'amorçage applicatif
  réapplique `default_enabled_sids: [1, 11]`, de sorte que seuls l'EPS et la
  balise sont actifs par défaut. Une équipe qui a simplement oublié
  d'envoyer `HK_ENABLE` n'a pas trouvé de panne.
- **Procédure de reprise.** CTG-019 Absence de télémesure en début de passage.
- **Critère de réussite du passage.** L'équipe identifie correctement que le
  satellite répond aux commandes (acquittements S1 présents) mais que le flux de TM
  est interrompu ; elle déclenche CTG-019 dans les 60 secondes suivant
  l'absence de TM ; elle poursuit la procédure en commande en aveugle
  (en s'appuyant uniquement sur les acquittements S1 comme confirmation).
- **Questions de débriefing.**
  1. Comment SPACON s'est-il rendu compte que la HK complète n'arrivait pas (autrement qu'en
     l'attendant) ?
  2. L'équipe a-t-elle correctement distingué *absence de TM* et *absence de
     commande* ?
  3. Quelqu'un a-t-il proposé de déclencher EMG-004 (Perte de communication) ?
     Était-ce justifié ? (EMG-003 correspond au redémarrage de l'OBC, une autre
     carte.)
  4. À quel moment l'équipe a-t-elle décidé de poursuivre en commande en aveugle
     plutôt que d'attendre ?
  5. Quel a été l'impact sur les étapes suivantes de la procédure ?

### 18.2 Surintensité sur une ligne d'alimentation (facile — jour 3 ou 4)

- **Moment de déclenchement.** Pendant la mise sous tension séquentielle de LEOP-007, injecter
  sur la ligne sur le point d'être activée — `aocs_wheels`
  (`line_index=7`) ou `payload` (`line_index=3`). Ou bien pendant la
  mise sous tension de la charge utile de COM-009. Les indices de ligne vont de 0 à 8 : 0 obc,
  1 ttc_rx, 2 ttc_tx, 3 payload, 4 fpa_cooler, 5 htr_bat,
  6 htr_obc, 7 aocs_wheels, 8 prop.
- **Premier indice.** L'EPS voit le courant de la ligne
  (`eps.line_current_N`, 0x0118+N) dépasser son seuil de déclenchement
  (payload 2,5 A, aocs_wheels 0,8 A) pendant le temps de déclenchement de 50 ms ;
  `eps.oc_trip_flags` (0x010D) positionne le bit et la ligne est
  ouverte de manière autonome.
- **Procédure de reprise.** CTG-012 Traitement d'une surintensité.
- **Critère de réussite du passage.** L'équipe acquitte la règle FDIR dans les
  20 s ; identifie la ligne concernée ; remplit une fiche d'anomalie ;
  ne réactive PAS la ligne pendant le même passage (l'action autonome
  est correcte — la laisser coupée ; analyser la cause au quart suivant).
- **Questions de débriefing.**
  1. L'équipe a-t-elle compris que la FDIR avait déjà ouvert la
     ligne, ou a-t-elle tenté d'envoyer manuellement `EPS_POWER_OFF(line_index=N)`
     (S8 func 20) ? Quelqu'un s'est-il souvenu que la réactivation
     exige *d'abord* `EPS_RESET_OC_FLAG(line_index=N)` (func 21) ?
  2. Quelqu'un a-t-il proposé de réactiver la ligne pendant le même passage ?
  3. La fiche d'anomalie a-t-elle été remplie avant la fin du passage ?
  4. Quelles étapes de procédure en aval ont été affectées ?
  5. L'équipe aurait-elle dû déclencher elle-même la réponse autonome
     au lieu de laisser la FDIR agir (une question de
     justification — les deux réponses sont valables selon le contexte) ?

### 18.3 Roue de réaction bloquée (moyen)

- **Moment de déclenchement.** Pendant l'étape 4 de LEOP-007 (ligne des roues alimentée
  et SCAO amorcé en DETUMBLE). Injecter `rw_seizure` sur une roue
  pendant sa mise en rotation.
- **Premier indice.** L'AOCS voit la vitesse de cette roue
  (`aocs.rw2_speed`, 0x0208 pour l'indice de roue 1) bloquée à 0 tr/min
  tandis que son courant (`aocs.rw2_current`, 0x0251) reste élevé —
  le moteur tente d'entraîner un rotor bloqué — et que l'état de son roulement
  (`aocs.rw2_bearing_health`, 0x0285) s'effondre.
- **Procédure de reprise.** CTG-026 Reprise après blocage d'un actionneur SCAO /
  CTG-007 Anomalie de roue de réaction.
- **Critère de réussite du passage.** L'équipe identifie la roue concernée dans les
  60 s ; la désactive avec `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8
  func 2) ; confirme que `aocs.wheels_enabled` (0x0260) = 3 ; vérifie que
  l'amortissement se poursuit (la loi B-dot utilise les **magnétocoupleurs**, pas les
  roues, de sorte qu'une roue bloquée ne l'interrompt pas) ; remplit une fiche d'anomalie.
- **Questions de débriefing.**
  1. L'AOCS a-t-il repéré la roue bloquée grâce au courant consommé, ou seulement
     grâce à la règle FDIR ?
  2. Le GO du FD pour désactiver la roue a-t-il été recueilli correctement ?
  3. L'équipe a-t-elle choisi à juste titre de poursuivre l'amortissement plutôt
     que d'abandonner — et quelqu'un a-t-il remarqué que l'amortissement n'a jamais
     eu besoin des roues ?
  4. L'équipe a-t-elle su prédire l'impact sur le bilan de pointage avec
     1 roue sur 4 hors service ? (Très faible en moyenne : une pyramide de 3 roues sur 4
     engendre toujours R³ et FINE_POINT tient 0,0188° contre
     0,0208° avec quatre roues. Ce qui est perdu, c'est l'espace nul — régulation de la
     vitesse de biais et évitement du passage par zéro — si bien que la gigue à court terme
     est plus forte, et le mode est signalé par
     `aocs.fine_degraded` 0x0299 avec une bande morte relâchée d'un facteur 4×.)
  5. Quelle est l'implication à long terme pour la mission (p. ex.
     agilité réduite, désaturations plus fréquentes) ?

### 18.4 Panne du senseur stellaire (moyen — jour 3 ou 4)

- **Moment de déclenchement.** En fin d'acquisition du Soleil de LEOP-005 (jour 3), ou
  pendant la transition vers NOMINAL de COM-005 (jour 4).
- **Premier indice.** L'AOCS voit `aocs.st1_status` (0x0240) passer à
  **3 (aveuglé)** ou **4 (en panne)** — les codes sont 0 éteint, 1 amorçage,
  2 poursuite, 3 aveuglé, 4 en panne — et `aocs.att_error` (0x0217)
  commencer à augmenter. `aocs.est_innov_rej_count` (0x02C2) augmente à mesure que
  l'estimateur écarte les mesures erronées.
- **Procédure de reprise.** CTG-008 Panne du senseur stellaire.
- **Critère de réussite du passage.** L'équipe identifie la panne dans les 30 s ;
  **met en service la seconde tête** (`ST2_POWER(on=1)`, S8 func 5) et
  la sélectionne (`ST_SELECT`, func 6) avant de considérer l'attitude comme
  perdue ; éteint la tête en panne (`ST1_POWER(on=0)`, func 4) ;
  réinitialise l'estimateur avec `AOCS_EST_RESET(mode=1)`
  (func 91, à chaud) si la solution a divergé ; ne commande COARSE_SUN
  (`AOCS_SET_MODE(mode=3)`) que si les *deux* têtes sont perdues ;
  remplit une fiche d'anomalie.
- **Questions de débriefing.**
  1. L'AOCS a-t-il distingué aveuglé (3) et en panne (4), et quelle est
     la différence opérationnelle ?
  2. Quelqu'un a-t-il pensé d'abord à la tête redondante, ou l'équipe
     est-elle passée directement au mode survie ? Ce satellite possède
     deux senseurs stellaires.
  3. L'équipe a-t-elle envisagé de reporter la prise de vue si ST2 tombe aussi en panne ?
  4. Quel est le bilan de pointage avec seulement les CSS, le magnétomètre et le gyro ?
     (Il se dégrade à environ un degré — la classe de performances de COARSE_SUN,
     pas le bilan inférieur à 0,1° de FINE_POINT.)
  5. Impact sur la mission : combien de jours le satellite peut-il être exploité
     en mode dégradé sans senseur stellaire avant que des livrables scientifiques
     ne soient manqués ?

### 18.5 Réinitialisation de l'OBC par le chien de garde (difficile)

- **Moment de déclenchement.** En plein LEOP-007, vers l'étape 4 (ligne des roues et
  amorçage du SCAO). Injecter `watchdog_reset` sur obdh.
- **Premier indice.** Toute la télémesure s'arrête pendant environ 15 s ; puis la
  balise UHF revient avec l'OBC en BOOTLOADER
  (`obdh.sw_image` 0x0311 = 0), `obdh.reboot_count` (0x030A)
  incrémenté et `obdh.last_reboot_cause` (0x0316) = 1
  (chien de garde).
- **Procédure de reprise.** CTG-010 Reprise après chien de garde OBDH.
- **Critère de réussite du passage.** L'équipe reconnaît le redémarrage inattendu
  dans les 30 s suivant la reprise de la TM ; déclenche CTG-010 ; rétablit
  l'amorçage applicatif (`OBC_BOOT_APP`, S8 func 55 — étape 5 de LEOP-001) ;
  **renvoie `HK_ENABLE` (S3.5) pour chaque SID sauf 1 et 11**,
  car l'amorçage applicatif réapplique
  `default_enabled_sids: [1, 11]` ; rétablit la synchronisation temporelle
  (`SET_TIME` S9.1) ; désactive à nouveau le mode balise et resélectionne le palier
  LOW ; consigne chaque étape perdue ; remplit une fiche d'anomalie.
- **Questions de débriefing.**
  1. SPACON a-t-il immédiatement reconnu la signature de la balise du chargeur
     d'amorçage ?
  2. L'équipe a-t-elle évité d'envoyer des commandes dans la précipitation pendant que l'OBC
     redémarrait ?
  3. Combien de temps s'est-il écoulé entre le redémarrage et la reprise complète du satellite ?
     (Dans l'industrie : < 5 min pour une reprise propre après chien de garde.)
  4. L'équipe a-t-elle correctement identifié les étapes de procédure
     à réexécuter et celles qui étaient préservées ?
  5. Quelle est la bonne façon de *prévenir* ce cas lors des quarts suivants ?
     (Indice : faire figurer le rafraîchissement du chien de garde dans les préconditions
     de la procédure pour les activités de longue durée.)

### 18.6 Panne du bus de l'OBC (difficile)

- **Moment de déclenchement.** Pendant LEOP-007, après l'étape 4 (ligne des roues
  alimentée, apparition du SID 2 de HK SCAO).
- **Premier indice.** Le SID 2 de HK SCAO cesse d'arriver ; la HK OBDH
  (SID 4) montre `obdh.bus_a_status` (0x030F) = 1 (ERROR) avec
  `obdh.active_bus` (0x030E) = 0 (A).
- **Procédure de reprise.** CTG-017 Basculement sur panne de bus.
- **Critère de réussite du passage.** SPACON reconnaît la panne du bus A dans les
  30 s ; commande **`OBC_SELECT_BUS(bus=1)` (S8 func_id 54)** —
  *et non* `OBC_SWITCH_UNIT` (func 53), qui bascule l'unité
  OBC et relève de CTG-011 ; vérifie que `obdh.active_bus` = 1, que le bus B est
  sain et que la HK SCAO a repris ; remplit une fiche.
- **Questions de débriefing.**
  1. Comment SPACON a-t-il distingué *absence de HK SCAO* et *panne du bus
     A* ?
  2. Le GO du FD pour le basculement a-t-il été donné proprement ?
  3. La reprise a-t-elle été plus rapide que celle du chien de garde ? Pourquoi
     devrait-elle l'être ?
  4. Impact sur la mission : fonctionnons-nous désormais sur le bus redondant
     pour le reste de la mission ? (Oui — le bus B ne peut pas revenir sur A
     sans intervention du sol.)
  5. Quelle est la conséquence à long terme (plus de redondance de bus) ?

### 18.7 Panne d'antenne de station sol (très difficile — jour 4)

- **Moment de déclenchement.** En milieu de passage au-dessus d'Iqaluit, idéalement pendant une
  action commandée.
- **Premier indice.** Le poste segment sol voit le gain de l'antenne d'Iqaluit
  chuter ; l'Eb/N0 en bande de base s'effondre ; le TT&C voit le TEB augmenter et
  la perte de verrouillage en réception.
- **Procédure de reprise.** CTG-020 Panne d'antenne de station
  sol — une fiche **consultative**. Elle ne contient aucune télécommande
  vers le satellite : le traitement se fait entièrement côté sol.
- **Critère de réussite du passage.** L'équipe identifie correctement une
  panne côté sol (et non bord) — `ttc.gs_equipment_status`
  (0x0524) est le masque de bits, et un satellite sain continue
  d'émettre ; reconnaît que le passage en cours est de fait perdu ;
  replanifie les activités restantes sur la station suivante du
  réseau de cinq stations (Iqaluit, Troll, Svalbard, Inuvik,
  O'Higgins) ; remplit une fiche ; informe le client (responsable de mission).
- **Questions de débriefing.**
  1. L'équipe a-t-elle distingué une panne d'antenne sol d'une
     panne TT&C bord ?
  2. Quelqu'un a-t-il proposé une escalade vers EMG-004 (Perte de communication) ?
     Était-ce justifié ? (Cela ne devrait pas l'être — le satellite va
     bien.)
  3. La replanification sur la station suivante a-t-elle été faite dans le planning
     sol, ou quelqu'un a-t-il tenté de commander le satellite pour
     une panne sol ?
  4. Quel a été l'impact sur le calendrier de la recette en orbite ? L'équipe
     a-t-elle manqué une activité critique dans le temps (p. ex. une fenêtre
     d'éclipse pour la mise en froid du FPA) ?
  5. Responsable de mission : comment le bulletin client a-t-il été formulé ?

### 18.8 Refroidisseur du FPA sous-performant (moyen)

- **Moment de déclenchement.** Pendant l'activation du refroidisseur du FPA de COM-010. La boucle
  se ferme normalement en environ **10 minutes** : injecter donc entre T+3 et
  T+5 min, pendant que le FPA est encore sur la rampe entre +4 °C
  et -8 °C.
- **Premier indice.** Le poste thermique voit la mise en froid du FPA plafonner
  avant la consigne ; `payload.fpa_ready` (0x0610) n'est jamais positionné ;
  `payload.cooler_margin_k` (0x064B) devient **≤ 0** et
  `payload.cooler_floor_c` (0x064A) remonte au-dessus de la consigne
  commandée. La paire miroir `tcs.fpa_cooler_floor_c` (0x0424) et
  `tcs.fpa_cooler_margin_k` (0x0425) raconte la même histoire dans
  l'onglet thermique.
- **Procédure de reprise.** CTG-004 Dépassement thermique +
  mise en sécurité de la charge utile.
- **Critère de réussite du passage.** L'équipe admet que le refroidisseur est
  sous-performant et comprend *pourquoi la solution est une consigne plus chaude,
  et non une attente plus longue* — le refroidisseur est une machine miniature
  de type Stirling à environ 23 % du rendement de Carnot : sa capacité
  diminue à mesure que l'écart de température augmente, et une marge négative signifie que la
  consigne est physiquement inatteignable avec le puits thermique actuel.
  Décide (a) soit de commander une consigne plus chaude avec
  `PAYLOAD_COOLER_SETPOINT` (S8 func 36, uint16 en
  **centikelvins**, enveloppe de -20 à 0 °C) et de poursuivre avec une
  qualité d'image dégradée, (b) soit d'abandonner COM-010 et de replanifier ;
  remplit une fiche ; en cas de poursuite, exécute l'étalonnage COM-011 et la première lumière
  COM-012 avec le FPA plus chaud.
- **Questions de débriefing.**
  1. Le poste thermique a-t-il repéré le plafonnement de la mise en froid sur la
     courbe de tendance, ou seulement quand `fpa_ready` n'a pas été positionné ?
  2. Le FD a-t-il pris une décision go/no-go claire sur la poursuite ?
  3. Quelqu'un a-t-il lu `cooler_margin_k` et compris qu'attendre
     plus longtemps ne pouvait pas fonctionner ? Quel coût en RSB la consigne
     plus chaude entraîne-t-elle (`payload.snr`, 0x0616) ?
  4. En cas de poursuite, le bulletin client a-t-il été mis à jour pour signaler
     l'impact sur la qualité scientifique ?
  5. Quel est l'impact à long terme sur la mission si le refroidisseur reste
     définitivement sous-performant ?

### 18.9 Image acquise corrompue (moyen)

- **Moment de déclenchement.** Pendant l'étape de capture de COM-012
  (`PAYLOAD_CAPTURE`, S8 func 28), injecter la corruption de sorte que
  l'image obtenue échoue à son évaluation de qualité.
- **Premier indice.** Le poste charge utile voit l'événement S5 **0x0607
  IMAGE_CHECKSUM_ERROR** après le stockage du produit, et
  `payload.checksum_errors` (0x0609) s'incrémente.
- **Procédure de reprise.** CTG-015 Reprise après image corrompue.
- **Critère de réussite du passage.** L'équipe marque l'image comme ratée ; la reprogramme
  pour une nouvelle acquisition au passage suivant ; recherche la cause première
  (généralement la température du FPA, l'impact d'un rayon cosmique pendant l'intégration,
  ou une oscillation du pointage) ; remplit une fiche ; si la nouvelle acquisition réussit
  au passage suivant, la première lumière est déclarée.
- **Questions de débriefing.**
  1. Le poste charge utile a-t-il correctement identifié la corruption grâce à
     l'événement 0x0607, ou ne s'en est-il rendu compte qu'à l'évaluation de
     qualité ? A-t-il supprimé l'image avant de relancer la capture
     (`PAYLOAD_DELETE_IMAGE`, func 30, puis `PAYLOAD_CAPTURE`,
     func 28) ?
  2. La nouvelle acquisition a-t-elle été déclenchée proprement (c.-à-d. l'équipe
     a-t-elle replanifié plutôt que relancé en aveugle la commande
     ayant échoué) ?
  3. Quelle est l'hypothèse de cause première ? (Généralement un rayon cosmique pour
     un cas isolé ; la température du FPA pour une panne récurrente.)
  4. L'équipe a-t-elle mis à jour le bulletin client pour tenir compte du
     report de la première lumière ?
  5. Combien de tentatives de prise de vue l'équipe est-elle prête à faire en un
     quart avant de reporter formellement la première lumière ?

### 18.10 Cascade de pannes de capteurs SCAO (difficile)

Il s'agit de `aocs_sensor_cascade.yaml`, et c'est là que **la « dérive de l'IMU »
est réelle**. Le scénario dure 2700 s et déclenche quatre injections :

| T+ | Injection | Effet |
|---|---|---|
| 60 s | `st_failure` unité 1 | ST1 → état 4 ; la FDIR bord devrait basculer sur ST2, mais l'opérateur doit le vérifier |
| 180 s | `css_head_fail` face px | La tête du senseur solaire grossier +X tombe en panne ; le vecteur Soleil composite se dégrade |
| 300 s | `mag_failure` | Le magnétomètre unique tombe en panne (pas d'unité B, aucun basculement possible) ; l'opérateur doit reconnaître la perte de la loi B-dot et de la désaturation par magnétocoupleurs, et protéger le moment cinétique |
| 600 s | `gyro_bias` axis=all bias=0.05 | **Biais de 0,05 °/s sur les trois voies gyrométriques** |

Le biais gyrométrique est le point pédagogique, et il doit être décrit
avec précision. Il est écrit dans le **décalage injecté persistant**
(`aocs.gyro_bias_injected`, 0x0296 — visible par l'instructeur), et non
dans l'état vrai de Gauss-Markov : il ne **revient donc pas** à la moyenne
sur la constante de temps du biais de 1800 s, et il **survit aux pas de simulation et
aux enregistrements / chargements de points de reprise jusqu'à ce qu'il soit explicitement effacé**. Si vous
rechargez un point de reprise en attendant un satellite sain, effacez d'abord la
panne.

0,05 °/s représente environ 1800× l'instabilité de biais de 0,1 °/h sur laquelle le MEKF
est construit — et c'est **supportable tant qu'un senseur stellaire est
sain** : l'état de biais du filtre absorbe un décalage constant. Les
seuls symptômes pour l'opérateur sont une marche dans le compteur de rejets
d'innovation (`aocs.est_innov_rej_count`, 0x02C2) et
l'écart croissant de `aocs.gyro_bias_x/y/z` (0x0270–0x0272) par rapport à
l'estimation. Cela devient fatal pour la mission dès que le senseur stellaire est lui aussi
perdu avant que le filtre ait reconvergé, car ECLIPSE et toutes les
phases de propagation seule dérivent alors à 0,05 °/s = **3 °/min**.

Notez que les gyros sont trois unités mono-axe **sans unité
redondante**, qu'il n'y a ni ligne d'alimentation IMU ni délai d'amorçage à froid
de l'IMU, et que l'étalonnage du biais gyrométrique se fait à bord
(`AOCS_GYRO_CALIBRATION`, S8 func 13) — il ne s'agit pas d'un envoi
calculé au sol.

- **Moment de déclenchement.** Lancer le scénario juste avant COM-011 (Étalonnage de la
  charge utile), de sorte que l'injection gyrométrique à T+600 s survienne vers la
  transition vers FINE_POINT.
- **Premier indice.** `aocs.st1_status` (0x0240) → 4 (en panne) ;
  puis les dégradations du vecteur Soleil et du magnétomètre ; puis
  `aocs.est_innov_rej_count` (0x02C2) augmente par paliers et
  `aocs.att_error` (0x0217) croît.
- **Procédure de reprise.** CTG-008 Panne du senseur stellaire → CTG-002
  Anomalie SCAO (± CTG-025 Reprise après perte de capteur SCAO) + report de la
  première lumière.
- **Critère de réussite du passage.** L'équipe traite les pannes dans l'ordre : vérifie
  le basculement sur ST2 (`ST_SELECT`, func 6) au lieu de le supposer ;
  reconnaît que le magnétomètre n'a pas de rechange (il n'existe pas de `MAG_SELECT`) et protège le moment cinétique ; lit
  `aocs.est_source` (0x02C1) pour voir ce que l'estimateur utilise
  réellement ; identifie le biais gyrométrique à partir de 0x0270–0x0272 et du
  compteur de rejets ; rétablit la connaissance gyrométrique avec
  `AOCS_EST_RESET(mode=1)` (S8 **func 91**, à chaud) une fois le biais
  borné, ou accepte une détermination par ST seul. Si le bilan de pointage
  n'est plus respecté, commande COARSE_SUN
  (`AOCS_SET_MODE(mode=3)`), reporte formellement la première lumière, remplit une
  fiche, informe le responsable de mission.
- **Questions de débriefing.**
  1. L'équipe a-t-elle correctement enchaîné les procédures (CTG-008 pour le
     senseur stellaire, CTG-002 pour la réponse SCAO) ?
  2. Quelqu'un a-t-il remarqué le biais gyrométrique *avant* la fin du travail sur le
     senseur stellaire — et a-t-il compris pourquoi le senseur sain
     le masquait ?
  3. Que devient ce satellite à la prochaine entrée en éclipse
     si le biais n'est pas effacé ? (Propagation seule à 3 °/min.)
  4. Quelqu'un a-t-il proposé de tenter malgré tout la première lumière ? Était-ce
     justifié ou risqué ?
  5. La décision de report formel a-t-elle été prise par le FD avec un accord
     clair de l'équipe, ou unilatéralement ?

### 18.11 Délestage progressif de la batterie (difficile)

- **Moment de déclenchement.** Pendant COM-010 (activation du refroidisseur du FPA), au début
  de la mise en froid.
- **Premier indice.** L'EPS voit `eps.bus_voltage` (0x0105)
  baisser de façon inattendue et le SoC chuter environ
  deux fois plus vite que prévu. L'échelle que l'équipe va descendre :
  événement d'avertissement bus à 27,0 V, délestage modélisé à **25,0 V**
  (ordre payload → fpa_cooler → ttc_tx → aocs_wheels → prop),
  bus critique à 25,0 V, mode survie FDIR sur sous-tension à
  **24,5 V**. Les étages de délestage pilotés par le SoC se situent à 30 / 20 / 10 %
  (`eps.load_shed_stage`, 0x0134).
- **Procédure de reprise.** CTG-001 Délestage sur sous-tension
  (CTG-023 Délestage progressif pour la version par étages).
- **Critère de réussite du passage.** L'équipe déleste progressivement par ordre de priorité —
  charge utile coupée (`PAYLOAD_SET_MODE(mode=0)`), refroidisseur coupé
  (`FPA_COOLER(on=0)`, func 43), PA coupé (`TTC_PA_OFF`, func 67),
  ligne des roues coupée (`EPS_POWER_OFF(line_index=7)`) — en guettant le
  rétablissement entre chaque étape, plutôt que de tout couper d'un coup ;
  maintient l'OBC et la chaîne de réception (lignes 0 et 1, toutes deux
  non commutables) ; comprend que la remise en service automatique rétablit
  les lignes une par une à chaque pas de simulation dès que le bus repasse au-dessus de 25,5 V ; remplit une
  fiche ; informe le responsable de mission.
- **Questions de débriefing.**
  1. L'EPS a-t-il repéré la tendance inattendue du SoC avant le déclenchement de la FDIR,
     ou seulement après ?
  2. L'escalade du délestage a-t-elle été correcte (priorité 1 d'abord, observer,
     puis faire remonter l'anomalie) ?
  3. L'équipe a-t-elle mis en balance le délestage du refroidisseur du FPA — qui
     fait perdre le travail de mise en froid — et le fait qu'il s'agit de la
     plus grosse charge commutable, à 15 W ?
  4. La chaîne de GO du FD a-t-elle été correcte à chaque escalade ?
  5. Hypothèse de cause première ? (Généralement la dégradation d'un élément de batterie
     dans les missions réelles.)

### 18.12 `aocs_wheel_failure.yaml` + `transponder_failure.yaml` (très difficile — jour 4)

C'est le scénario à anomalies multiples — deux pannes en succession
rapide.

- **Moment de déclenchement.** Panne de roue injectée au milieu du passage 3 pendant
  la prise de vue ; panne du transpondeur injectée au début du passage 4.
- **Premier indice (roue).** L'AOCS voit le courant de cette roue
  (`aocs.rwN_current`, 0x0250–0x0253) faire un pic et sa vitesse
  (0x0207–0x020A) tomber à 0 ; `aocs.wheels_enabled` (0x0260)
  descend à 3.
- **Premier indice (transpondeur).** Le TT&C voit la liaison en bande S
  tomber à l'AOS du passage 4 — `ttc.link_status` (0x0501) ≠ 2, aucun acquittement
  S1, aucune TM — **alors que la balise UHF continue d'arriver** (SID de HK
  11, `ttc.beacon_active` 0x0527 = 1). Ce contraste est révélateur :
  la balise est une radio distincte, sur une bande distincte.
- **Procédures de reprise.** CTG-007 (roue) → CTG-003 (liaison).
- **Critère de réussite du passage.** L'équipe traite la panne de roue pendant le
  passage 3, prend une décision réfléchie pour le passage 4 (reporter la
  prise de vue ? prendre l'image avec les trois roues restantes, en acceptant
  `fine_degraded` ?), puis, lorsque le
  transpondeur tombe en panne à l'AOS, reconnaît la seconde anomalie,
  déclenche la reprise de liaison CTG-003 et rétablit la liaison
  avant le LOS.
- **Questions de débriefing.**
  1. L'équipe a-t-elle correctement traité la première anomalie sans
     la laisser se propager ?
  2. Lorsque la seconde anomalie s'est déclenchée, quelqu'un a-t-il confondu les
     symptômes avec une suite de la première ?
  3. La priorisation du FD a-t-elle été claire (transpondeur d'abord, puis
     travail sur la roue) ?
  4. Quelle leçon en tirer sur la charge cognitive ? C'est face aux anomalies multiples
     que les équipes craquent généralement.
  5. Responsable de mission : comment le bulletin client de la promotion a-t-il été
     formulé lorsque *deux* choses ont mal tourné en un seul quart ?

---
