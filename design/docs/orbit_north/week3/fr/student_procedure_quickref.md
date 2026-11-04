---
title: "Aide-mémoire des procédures"
subtitle: "ORBIT NORTH · guide de poche de l'opérateur, semaine 3"
course-codes: "GNG 3100 · SYS 5186"
term: "Été 2026"
version: "v1 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
audience: "étudiantes et étudiants en console"
expected-reading: "Parcourez-le avant chaque journée de simulation. Lisez en entier toute procédure que votre équipe a le plus de chances d'exécuter."
---

# Aide-mémoire des procédures

Les vingt-sept procédures que vous utiliserez le plus probablement pendant la semaine 3, au
format d'une carte chacune. Les fichiers de procédure complets font foi —
ces cartes sont des repères, pas des substituts.

Format des cartes : **ID · Titre · Postes responsables · Déclencheur · 3 étapes principales ·
Critère de sortie · Fichier**.

Référence faisant foi pour les procédures :
`~/SpaceMissionSimulation/configs/eosat1/procedures/procedure_index.yaml`
ainsi que les fichiers de chaque procédure dans les sous-dossiers.

---

## Procédures LEOP

Chaque fiche suit ce modèle ; LEOP-001 est présentée en entier.

> **LEOP-001 · Première acquisition du signal et amorçage de l'OBC**
> *Postes responsables :* directeur de vol · TT&C · FDIR/Systèmes
> *Déclencheur :* premier passage au-dessus d'Iqaluit après expiration de la minuterie de séparation.
> *3 étapes principales :* (1) configurer la station sol, surveiller l'acquisition RF ;
> (2) vérifier la balise du chargeur d'amorçage (SID 11) ; (3) envoyer la commande OBC_BOOT_APP
> (S8 func_id 55).
> *Sortie :* logiciel applicatif en cours d'exécution, HK complète émise.
> *Fichier :* `procedures/leop/first_acquisition.md`

Les autres cartes LEOP, une ligne chacune. Le déclencheur est la condition d'entrée de la fiche. Les étapes principales et le critère de sortie figurent sur la fiche complète du manuel du cours, partie 2, §14.1 ;
le fichier fait foi. LEOP-003 et LEOP-005 s'adressent aux étudiants avancés
qui les atteignent pendant la simulation.

| ID · titre | Postes responsables | Déclencheur | Fichier |
|---|---|---|---|
| LEOP-002 · Bilan de santé initial | Directeur de vol · Puissance et thermique · FDIR / systèmes | Juste après LEOP-001 ; SID 1, 3, 4, 6 et 11 émis | `procedures/leop/initial_health_check.md` |
| LEOP-007 · Mise sous tension séquentielle | Directeur de vol · Puissance et thermique · Dynamique du vol · TT&C · FDIR / systèmes | LEOP-004 terminée (ailes déployées) ; `obdh.sw_image` = 1 ; SoC > 60 %. N'alimente que la suite AOCS et commande DETUMBLE | `procedures/leop/sequential_power_on.md` |
| LEOP-005 · Acquisition du Soleil | Directeur de vol · Dynamique du vol | Après LEOP-007 ; SCAO en DETUMBLE (mode 2) ; SoC > 40 %. Observe le passage automatique en COARSE_SUN | `procedures/leop/sun_acquisition.md` |
| LEOP-006 · Synchronisation temporelle | Directeur de vol | Après LEOP-005 ; image applicative en cours d'exécution ; `ttc.link_status` = 2 | `procedures/leop/time_sync.md` |
| LEOP-003 · Restitution d'orbite initiale | Directeur de vol · Dynamique du vol · TT&C | Après LEOP-006 ; COARSE_SUN ; point GPS et SID 12. Dernière fiche de la LEOP : TLE affiné vers les outils sol, puis déclaration de la phase 5 | `procedures/leop/initial_orbit_determination.md` |

Ordre d'exécution à partir de l'état initial de démarrage à froid : LEOP-001 → LEOP-002 →
LEOP-004 → LEOP-007 → LEOP-005 → LEOP-006 → LEOP-003 (manuel du cours, partie 2,
§14.1).

---

## Procédures de recette en orbite

Le déclencheur est la condition d'entrée de la fiche. Les étapes principales et le critère de sortie figurent sur la fiche complète du manuel du cours, partie 2, §14.2. COM-003 (Étalonnage des capteurs SCAO),
COM-004 (Vérification des actionneurs SCAO) et COM-013 ne figurent pas dans cette liste ;
voir le §14.2.

| ID · titre | Postes responsables | Déclencheur | Fichier |
|---|---|---|---|
| COM-001 · Vérification de l'EPS | Directeur de vol · Puissance et thermique | Début du passage de recette 1 ; COARSE_SUN ; SoC > 70 % | `procedures/commissioning/eps_checkout.md` |
| COM-002 · Vérification du TCS | Directeur de vol · Puissance et thermique | Après le GO de COM-001 | `procedures/commissioning/tcs_verification.md` |
| COM-005 · Transitions de modes SCAO | Directeur de vol · Dynamique du vol | Après le GO de COM-003 (roues activées dans COM-004, gyroscopes étalonnés dans COM-003) | `procedures/commissioning/aocs_mode_transitions.md` |
| COM-006 · Vérification de la liaison TTC | Directeur de vol · TT&C | Après le GO de COM-005 | `procedures/commissioning/ttc_link_verification.md` |
| COM-007 · Vérification de l'OBDH | Directeur de vol · FDIR / systèmes | Passage de recette 2, après le bilan de santé d'ouverture de passage | `procedures/commissioning/obdh_checkout.md` |
| COM-008 · Configuration et essai de la FDIR | Directeur de vol · FDIR / systèmes | Après le GO de COM-007 ; la FDIR passe du jeu LEOP au jeu nominal | `procedures/commissioning/fdir_configuration.md` |
| COM-009 · Mise sous tension de la charge utile | Directeur de vol · Opérations charge utile · Puissance et thermique | Jeu FDIR nominal armé ; SoC > 75 % ; production > 40 W | `procedures/commissioning/payload_power_on.md` |
| COM-010 · Activation du refroidisseur du FPA | Directeur de vol · Opérations charge utile · Puissance et thermique | Juste après le GO de COM-009 ; charge utile en STANDBY | `procedures/commissioning/fpa_cooler_activation.md` |
| COM-011 · Étalonnage de la charge utile | Directeur de vol · Opérations charge utile | FPA dans la plage −16.5…−14.5 °C ; `payload.fpa_ready` = 1 | `procedures/commissioning/payload_calibration.md` |
| COM-012 · Première lumière | Directeur de vol · Opérations charge utile · Dynamique du vol | Après le GO de COM-011 | `procedures/commissioning/first_light.md` |

---

## Procédures nominales

Le déclencheur est la condition d'entrée de la fiche. Les étapes principales et le critère de sortie figurent sur la fiche complète du manuel du cours, partie 2, §14.3.

| ID · titre | Postes responsables | Déclencheur | Fichier |
|---|---|---|---|
| NOM-001 · Ouverture de passage | Directeur de vol · TT&C | AOS sur l'une des cinq stations du réseau | `procedures/nominal/startup.md` |
| NOM-002 · Séance de prise de vue | Opérations charge utile · Dynamique du vol | Ouverture de la fenêtre de prise de vue planifiée ; SCAO en FINE_POINT ou en transition | `procedures/nominal/imaging_session.md` |
| NOM-003 · Transmission des données au sol | TT&C · Opérations charge utile | AOS avec des produits en attente, en général juste après NOM-001 | `procedures/nominal/data_downlink.md` |
| NOM-009 · Bilan de santé de routine | Directeur de vol | À chaque ouverture de passage, dans NOM-001 ; ou à la demande du FD | `procedures/nominal/routine_health_check.md` |
| NOM-012 · Passation de consignes | Directeur de vol | Fin de quart | `procedures/nominal/shift_handover.md` |

---

## Procédures de contingence (les plus probables pendant la semaine 3)

Le déclencheur est la condition d'entrée de la fiche. Les étapes principales et le critère de sortie figurent sur la fiche complète du manuel du cours, partie 2, §14.4.

| ID · titre | Postes responsables | Déclencheur | Fichier |
|---|---|---|---|
| CTG-001 · Délestage sur sous-tension | Directeur de vol · Puissance et thermique | `eps.uv_flag` (0x010E) = 1, déclenchement de la règle ea 1001, ou bus sous 28.4 V | `procedures/contingency/undervoltage_loadshed.md` |
| CTG-002 · Reprise après anomalie SCAO | Directeur de vol · Dynamique du vol | `aocs.att_error` (0x0217) > 5°, une roue au-dessus de 60 °C, ou un senseur stellaire BLIND | `procedures/contingency/aocs_anomaly.md` |
| CTG-003 · Rétablissement après perte de liaison TTC | Directeur de vol · TT&C | `ttc.link_status` (0x0501) = 0 pendant > 30 s après l'AOS, ou liaison perdue en cours de passage | `procedures/contingency/ttc_link_loss.md` |
| CTG-007 · Anomalie de roue de réaction | Directeur de vol · Dynamique du vol | Gigue de vitesse > ±500 tr/min sur 10 s, vitesse > 6500 tr/min, ou roulement au-dessus de 60 °C | `procedures/contingency/reaction_wheel_anomaly.md` |
| CTG-012 · Traitement d'une surintensité | Directeur de vol · Puissance et thermique | Un bit de disjonction levé dans `eps.oc_trip_flags` (0x010D) | `procedures/contingency/overcurrent_response.md` |
| CTG-019 · Absence de télémesure en début de passage | Directeur de vol · TT&C | Ni balise ni HK à l'AOS prévue, ou balise sans HK complète après l'amorçage | `procedures/contingency/no_telemetry_at_pass.md` |

---

## Procédures d'urgence (à lire une fois, en principe jamais déclenchées)

Simple mention — vous devez savoir qu'elles existent :

- EMG-001 Mode survie d'urgence (`procedures/emergency/emergency_safe_mode.md`)
- EMG-002 Perte totale d'alimentation (`total_power_failure.md`)
- EMG-003 Redémarrage de l'OBC (`obc_reboot.md`)
- EMG-004 Perte de communication (`loss_of_communication.md`)
- EMG-005 Perte d'attitude (`loss_of_attitude.md`)
- EMG-006 Emballement thermique (`thermal_runaway.md`)

Si vous êtes sur le point de recourir à l'une d'elles, **appelez d'abord le
FD**. Ces procédures comportent le passage en mode survie parmi leurs étapes, et vous
ne déclenchez pas le mode survie sans autorisation du FD.

---

## Comment lire un fichier de procédure

Chaque fichier de procédure a la même forme ; le manuel du cours, partie 2,
§7.4, en donne le modèle. Ouvrir `procedures/leop/first_acquisition.md`
en parallèle :

1. **En-tête** — `# LEOP-001: First Acquisition of Signal & OBC Boot`,
   puis **Subsystem**, **Phase**, **Revision** et **Approved**. Les fiches
   LEOP indiquent aussi un **Entry state** (ici : démarrage à froid, OBC dans le
   chargeur d'amorçage).
2. **Purpose** — ce que la fiche permet d'obtenir.
3. **Prerequisites** — une liste de contrôle (`- [ ]`) dont tous les points doivent
   être vrais avant l'étape 1.
4. **Procedure Steps** — `### Step N — name`, construites à partir d'étiquettes en
   gras plutôt que d'un tableau : **TC** (la commande avec ses arguments dans les
   accents graves, service et sous-type à côté), **Action**,
   **Verify** (mnémonique, identifiant hexadécimal, seuil et délai) et **Note** ;
   certaines fiches ajoutent **GO/NO-GO** ou **BRANCH**.
5. **Off-Nominal Handling** — que faire quand une vérification échoue, en
   citant le plus souvent une fiche CTG ou EMG par son identifiant.
6. **Exit state** et **Post-Conditions** — le critère de sortie.

La responsabilité ne figure pas dans le fichier. Les postes qui exécutent une
fiche sont ses `required_positions` dans `procedure_index.yaml`, que l'onglet
Procédures du MCS affiche.

---

## Correspondance entre procédures et commandes MCS

Chaque étape de procédure qui comporte une commande indique le service PUS
à utiliser (d'après `mcs/pus_services.yaml`) :

| Service | Usage |
|---------|-----|
| S1 | Vérification des télécommandes (succès / échec de la dernière commande) |
| S3 | Configuration des données de servitude (quels SID sont émis et quand) |
| S5 | Rapports d'événements (événements d'anomalie émis par le satellite) |
| S8 | Gestion des fonctions (appel de fonctions du satellite, p. ex. OBC_BOOT_APP) |
| S9 | Gestion du temps (réglage de l'heure, corrélation temporelle) |
| S11 | Plan bord (télécommandes datées) |
| S15 | Stockage et restitution à bord (transmission au sol de la mémoire de masse) |
| S17 | Test de connexion (contrôle de la liaison montante-descendante) |
| S19 | Service événement-action (déclencher une action de l'OBC sur un événement) |
| S20 | Gestion des paramètres (lecture / écriture de paramètres de l'OBC) |

Vous commandez via l'interface du MCS ; vous n'avez pas à écrire vous-même
les trames PUS.

---

## Quand vous êtes bloqué

1. Faites une pause. Utilisez une annonce : « [Poste], standby. »
2. N'envoyez aucune commande. Relisez le critère de sortie de la procédure.
3. Demandez au FD un « Hold » de 60 secondes.
4. Si le FD accepte, consignez l'attente et consultez la section du manuel
   relative au sous-système concerné
   (`configs/eosat1/manual/0*.md`).
5. Si vous ne parvenez pas à résoudre le problème, le FD annonce *no-go* et l'équipe revient
   au dernier état vérifié.

---

## Références

- Index des procédures du simulateur :
  `~/SpaceMissionSimulation/configs/eosat1/procedures/procedure_index.yaml`
- ECSS-E-ST-70-32C — *Test and operations procedures*
- CCSDS *Mission Operations Services Concept* (CCSDS 520.0-G) —
  https://public.ccsds.org/Pubs/520x0g4.pdf
- NASA *Space Flight Program and Project Management Requirements* (NPR 7120.5F)
