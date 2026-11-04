# LEOP-001 : Première acquisition du signal et amorçage de l'OBC

**Sous-système :** TT&C / OBDH / segment sol
**Phase :** LEOP
**Révision :** 3.0 — refonte du déroulement 2026-08c (états d'entrée et de sortie, contact
uniquement pendant les passages prédits, synchronisation temporelle déplacée dans LEOP-006, nommage du palier SAFE)
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** démarrage à froid — OBC dans le chargeur d'amorçage, seules les lignes `obc` et `ttc_rx`
alimentées, toutes les lignes réchauffeurs / AOCS / charge utile sur OFF, horloge non réglée (J2000),
aucun contact encore établi. C'est la première fiche de la LEOP.

## Objet
Établir la première voie de commande avec EOSAT-1 après la séparation, faire sortir
l'OBDH du chargeur d'amorçage vers l'image applicative et consigner l'horloge de bord encore non réglée (LEOP-006 la synchronise).
Au démarrage à froid, le satellite est muet sur la liaison descendante : seules les lignes du récepteur
(`ttc_rx`) et de l'OBC (`obc`) sont alimentées. Les lignes de l'émetteur
(`ttc_tx`), de tous les réchauffeurs, des roues AOCS, de la charge utile et du refroidisseur du FPA sont
sur OFF, et l'OBC exécute l'image du chargeur d'amorçage. Cette procédure est ce qui
transforme le satellite, simple récepteur à sens unique, en une plateforme pleinement bidirectionnelle
exécutant son logiciel applicatif.

## Prérequis
- [ ] Séparation du lanceur confirmée (télémesure du fournisseur de lancement)
- [ ] Antenne de la station sol d'Iqaluit configurée sur la fréquence de réception en bande S d'EOSAT-1
- [ ] Démodulateur de la station sol configuré pour le échelon **SAFE** de l'échelle de débits
      TM (le échelon à 1000 bit/s, renommé de BEACON en 2026-08c — « balise » désigne désormais
      toujours l'émetteur UHF distinct à antenne fouet) — BPSK, conv(7,1/2)+RS,
      1 kBd, ~3,1 kHz de bande occupée. C'est le SEUL débit émis par le chargeur d'amorçage
      (`subsystems/ttc.yaml` `beacon_tier: SAFE`) ; le démodulateur
      doit être reconfiguré à 16 kBd après l'amorçage de l'application (étape 5)
- [ ] Un passage réel de station sol est PROGRAMMÉ pour cette fiche (AOS/LOS prédits
      à partir du TLE de lancement). Le contact n'est attendu que pendant un passage prédit
      — aucune fiche de ce déroulement ne demande à l'opérateur de forcer le contact
- [ ] Chronologie AOS/LOS prédite chargée dans le planning de la station sol
- [ ] La dynamique du vol a fourni le TLE initial du fournisseur de lancement
- [ ] Base de données du MCS chargée avec les définitions TM/TC d'EOSAT-1
- [ ] Toutes les positions de console armées et nominales

## Déroulement

### Étape 1 — Configurer le récepteur de la station sol pour le passage programmé
**Action:** Commander à la station sol d'Iqaluit de pointer vers l'azimut et l'élévation prédits de l'AOS du passage PROGRAMMÉ. Activer la poursuite automatique sur la fréquence de liaison descendante en bande S. Régler la bande du récepteur en mode acquisition large (fenêtre Doppler de +/- 40 kHz).
**Action:** Régler le démodulateur sur le palier SAFE : 1 kBd BPSK avec conv(7,1/2)+RS. À 1000 bit/s, ce palier boucle avec environ 56 dB de marge à 5° d'élévation, même vers la station la moins performante du réseau, ce qui est toute la raison d'être de ce palier : la première acquisition ne doit pas dépendre d'un bon passage.
**Action:** Attendre l'AOS prédit. Au démarrage à froid, `ttc_tx` est sur OFF ; il n'y a donc aucune porteuse à acquérir passivement ; la première émission montante de l'étape 2 est envoyée à l'aveugle dans la fenêtre programmée, et le maintien automatique de l'émetteur (auto-TX) du satellite y répond.
**Verify:** État de la station sol = TRACKING_READY à l'AOS prédit
**GO/NO-GO:** Station sol prête, fenêtre du passage programmé ouverte

### Étape 2 — Envoyer la première TC (test de connexion)
**TC:** `CONNECTION_TEST` (Service 17, Subtype 1)
**Action:** Le ping du service 17 figure sur la liste des TC autorisées par le chargeur d'amorçage ; il est donc accepté par l'OBC avant même le chargement de l'image applicative. Dès l'acceptation, le **maintien automatique de l'émetteur (auto-TX)** de la plateforme entre en jeu : toute TC acceptée met de façon autonome `ttc_tx` sur ON pendant 15 minutes, ce qui alimente la liaison descendante sans autre commande.
**Verify:** Acceptation S1.1 (Service 1, Subtype 1) reçue sous 10s
**Verify:** Rapport de test de connexion S17.2 reçu sous 10s
**Verify:** Les paquets balise (SID 11) commencent à arriver sous 30 s — la liaison descendante existe. Le chargeur d'amorçage n'émet que le SID 11, et le SID 11 ne transporte pas `eps.pl_ttc_tx` (0x0112) : cette ligne est confirmée à l'étape 7, une fois que l'application émet le SID 1
**GO/NO-GO:** Liaison bidirectionnelle établie, liaison descendante visible par l'opérateur

### Étape 3 — Vérifier le verrouillage de la porteuse et la qualité de la liaison
**Action:** Confirmer que le récepteur de la station sol a verrouillé la porteuse. Consigner le décalage Doppler mesuré pour la dynamique du vol.
**Verify:** Les trames balise sont décodées en continu (barre supérieure : « Je le vois ? » actif) sous 30s. `ttc.link_status` (0x0501) est dans le SID 6, que le chargeur d'amorçage n'émet pas : il est vérifié = 2 (LOCKED) à l'étape 5a
**Verify:** page TT&C (sol) : `ttc.rssi` (0x0502) > -126 dBm sous 30s
**Verify:** page TT&C (sol) : `ttc.link_margin` (0x0503) > 3.0 dB
**GO/NO-GO:** Verrouillage stable de la porteuse avec une marge de liaison positive

### Étape 4 — Confirmer que l'OBC est dans le chargeur d'amorçage
**TC:** `HK_REQUEST(sid=11)` (Service 3, Subtype 27) — SID de balise
**Verify:** Paquet de balise reçu (le chargeur d'amorçage n'émet que le SID 11 ; la structure de balise contient `obdh.sw_image` 0x0311)
**Verify:** `obdh.sw_image` (0x0311) = 0 (BOOTLOADER) sous 10s
**Note:** Aucun SID de sous-système n'est encore émis périodiquement. Le chargeur d'amorçage n'émet que le SID 11, et même une fois l'application en cours d'exécution, l'ensemble activé à la mise sous tension est `simulation.yaml` `default_enabled_sids: [1, 11]` — tout autre SID doit être activé par commande avec `HK_ENABLE` (Service 3, Subtype 5). C'est le comportement attendu.
**GO/NO-GO:** Chargeur d'amorçage confirmé ; prêt pour l'amorçage de l'application

### Étape 5 — Amorcer l'OBC sur l'image applicative
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55)
**Action:** Envoyer la commande d'amorçage de l'application. Le modèle OBDH vérifie le CRC de l'application sur une fenêtre de 10s, puis fait passer `sw_image` à APPLICATION (1). Tant que cette transition n'est pas terminée, seul le jeu de commandes du chargeur d'amorçage est accepté.
**Verify:** Acceptation S1.1 + début d'exécution S1.3 reçus sous 5s
**Note:** `obdh.boot_state` (0x0A15) = 1 (VERIFYING) et `obdh.boot_time_remaining_s` (0x0A16) en décompte signalent la fenêtre de CRC ouverte, mais les deux sont dans le SID 4, que le chargeur d'amorçage n'émet pas : pendant la fenêtre, la console ne les montre que dans un avis de refus. `obdh.boot_state` est vérifié après `HK_ENABLE(sid=4)` ci-dessous
**Verify:** Fin d'exécution S1.7 reçue sous 15s. Elle arrive à la FERMETURE de la fenêtre de CRC, et non à l'acceptation : c'est donc la confirmation que l'amorçage a réellement eu lieu. Un échec du CRC est signalé par un S1.8 indiquant la cause, ainsi que par l'événement 0x0305 BOOT_FAILURE ; un succès est signalé par l'événement 0x0310 BOOT_COMPLETE.
**Verify:** `obdh.sw_image` (0x0311) = 1 (APPLICATION) sous 15s (le SID 11 de la balise le transporte)
**Note:** Ne pas envoyer la télécommande suivante avant l'arrivée de ce S1.7. Pendant la fenêtre de CRC, l'OBC est toujours le chargeur d'amorçage, et tout ce qui sort de son sous-ensemble est refusé par un S1.2 — l'avis de refus indique `0x0A15 = 1 VERIFYING` et demande d'attendre.
**Verify:** Les HK périodiques **SID 1 (EPS) et SID 11 (balise)** — et uniquement ces deux-là — commencent à apparaître sur la liaison descendante. L'amorçage de l'application réapplique `simulation.yaml` `default_enabled_sids: [1, 11]` (`engine.py::_apply_default_hk_enable`, appelé par le gestionnaire d'amorçage) ; tous les autres SID (2 AOCS, 3 TCS, 4 OBDH/plateforme, 5 charge utile, 6 TT&C, 8 EPS étendu, 9 PROP) sont donc DÉSACTIVÉS à l'amorçage et doivent être activés par commande avec `HK_ENABLE(sid=N)` (Service 3, Subtype 5). Alimenter la ligne d'un sous-système n'active pas son SID.
**TC:** `HK_ENABLE(sid=3)` (Service 3, Subtype 5) — données de servitude périodiques TCS
**TC:** `HK_ENABLE(sid=4)` (Service 3, Subtype 5) — données de servitude périodiques OBDH / plateforme
**TC:** `HK_ENABLE(sid=6)` (Service 3, Subtype 5) — données de servitude périodiques TT&C
**Verify:** `obdh.boot_state` (0x0A15) = 2 sous 15s (SID 4, désormais activé)
**Verify:** Les SID périodiques 3, 4 et 6 commencent à apparaître en l'espace d'une période de structure (SID 3 = 60 s, SID 4 = 8 s, SID 6 = 8 s). Les SID 2 (AOCS) et 5 (charge utile) sont activés dans LEOP-007, une fois leurs lignes alimentées.
**Note:** L'amorçage de l'application ne désactive **PAS** le mode balise. `ttc.beacon_mode` (0x0521) reste à 1 et le satellite reste sur le palier BEACON jusqu'à ce que ce mode soit explicitement désactivé à l'étape 5a. D'ici là, tout `TTC_SET_DATA_RATE` est REFUSÉ par un S1.8 avec l'erreur `0x0007` et l'avis d'échec « TM rate is forced to the beacon tier in beacon mode (LOW refused) ».
**GO/NO-GO:** Image applicative en cours d'exécution, ensemble complet des services PUS disponible — l'étape 5a (sortie du mode balise) précède tout changement de débit

### Étape 5a — Désactiver le mode balise et passer sur le palier LOW
**TC:** `TTC_SET_BEACON_MODE(on=0)` (Service 8, Subtype 1, func_id 70)
**Action:** Désactiver le mode balise. C'est le verrou de toute l'échelle de débits : tant que le mode balise est verrouillé, BEACON est le SEUL palier autorisé et LOW comme HIGH sont refusés. C'est une étape distincte et délibérée, car le palier balise est la ligne de vie — le satellite ne le quitte jamais par accident.
**Verify:** Acceptation S1.1 + fin d'exécution S1.7 reçues sous 5s
**Verify:** `ttc.beacon_mode` (0x0521) = 0 sous 10s
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) sous 15s (SID 6, activé à l'étape 5)
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) (LOW)
**Action:** Sélectionner le `default_tier` de l'échelle — **LOW, 16 000 bit/s, BPSK conv(7,1/2)+RS, 16 kBd**. Reconfigurer le démodulateur sol à 16 kBd AVANT d'attendre les SID des sous-systèmes : le démodulateur de balise ne se verrouillera pas à 16 kbit/s.
**Verify:** Acceptation S1.1 + fin d'exécution S1.7 (et NON un S1.8) sous 5s
**Verify:** `ttc.tm_data_rate` (0x0506) = 16000 bps et `ttc.tm_tier` (0x0539) = 1 (LOW)
**Verify:** `ttc.tm_symbol_rate` (0x053B) = 16000 Bd
**Note:** L'ordre complet des verrous BORD de l'échelle est : **mode balise désactivé** → LOW sélectionnable ; **antenne déployée** (func 69, COM-006) **+ mode DOWNLINK activé** (func 79) → HIGH sélectionnable. Il n'existe AUCUN verrou bord sur l'élévation (2026-08c) : la règle des 10° pour HIGH relève de la politique d'autorisation SOL — le MCS avertit d'après sa propre géométrie de contact et le planificateur programme les vidages en HIGH au-dessus de ce seuil. Chaque verrou bord non satisfait est signalé par son propre avis d'échec S1.8 qui nomme ce verrou ; lire l'avis, pas le code (ils renvoient tous `0x0007`). Voir `docs/LINK_BUDGET_AND_RATES.md` §6.3.
**Note:** LOW transporte l'ensemble complet des HK périodiques (1588 bit/s de canal après RS et tramage TM) à moins de 10 % du temps : le satellite ne prend donc jamais de retard sur les données de servitude au débit courant. Le palier HIGH (128 kbit/s) n'est PAS utilisé ici — il ne sert qu'aux vidages (voir NOM-011).
**GO/NO-GO:** Mode balise désactivé, liaison descendante en LOW, démodulateur sol reconfiguré à 16 kBd

### Étape 6 — Noter que l'horloge n'est pas réglée (NE PAS synchroniser ici)
**Action:** Consigner que `obdh.time_ref` (0x0A13) vaut 0 (NONE) : l'horloge n'a
jamais été réglée et l'horodatage CUC de chaque paquet indique l'an 2000. C'est un
comportement correct, pas une panne.
**Note:** La synchronisation temporelle **relève de LEOP-006** — la voie sol
(réglage de l'heure S9.1) comme la voie GPS (S8.1 func 80) figurent dans cette seule fiche, de sorte que
la logique « amorcer puis synchroniser » n'est écrite qu'une fois. Cette fiche n'envoie aucune commande de temps.
**GO/NO-GO:** État de l'horloge compris et consigné

### Étape 7 — Demander les données de servitude EPS (contrôle de cohérence de l'alimentation)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.bus_voltage` (0x0105) dans la plage [29.6V, 34.6V] sous 10s
**Verify:** `eps.bat_soc` (0x0101) > 50 % sous 10s
**Verify:** `eps.pl_ttc_tx` (0x0112) = 1 — le maintien auto-TX de l'étape 2 (SID 1)
**Verify:** `eps.power_gen` (0x0107) rapportée (valeur faible tant que le satellite est en rotation libre et pas encore pointé vers le Soleil)
**GO/NO-GO:** État d'alimentation plausible pour les conditions post-séparation

### Étape 8 — Consigner et rendre compte
**Action:** Consigner l'heure de l'AOS, l'heure de la première TC acceptée, l'heure de l'amorçage de l'application et toutes les valeurs HK reçues. Diffuser le rapport de première acquisition. Confirmer que la durée du passage suffit pour exécuter LEOP-002 (bilan de santé initial) sur ce contact, ou programmer le passage suivant.
**GO/NO-GO:** Données suffisantes recueillies et OBC sur l'image applicative — feu vert pour LEOP-002

## Conduite à tenir hors nominal
- **Aucun S1.1 en retour à CONNECTION_TEST :** le maintien automatique de l'émetteur de la plateforme ne se déclenche que sur des TC acceptées ; si aucun S1.1 n'arrive, soit la liaison montante ne passe pas (contrôler la géométrie du passage et le pointage de la station sol), soit le récepteur est défaillant. Réessayer une fois. Toujours rien : repointer et tenter avec Troll lors de son prochain passage programmé.
- **`obdh.sw_image` ne change pas après OBC_BOOT_APP :** le décompte d'amorçage de l'application est de 10s. Lire d'abord `obdh.boot_state` (0x0A15) : 1 = toujours VERIFYING (attendre le S1.7), 3 = FAILED, le CRC de l'application échoue — on observera aussi un S1.8 sur la télécommande d'amorçage de l'application et l'événement 0x0305 BOOT_FAILURE. En cas d'amorçage FAILED, faire remonter à l'ingénieur OBDH et envisager `OBC_BOOT_INHIBIT(0)` puis `OBC_REBOOT`.
- **SID 1 non émis après boot_app, ou SID 3/4/6 toujours absents après les `HK_ENABLE` de l'étape 5 :** vérifier que `obdh.sw_image` est réellement passé à 1. Si oui, se rappeler que l'amorçage de l'application réapplique `default_enabled_sids: [1, 11]` et désactive tout le reste : tout SID activé avant l'amorçage est donc de nouveau désactivé. Renvoyer `HK_ENABLE(sid=N)` (Service 3, Subtype 5) pour chaque SID manquant après l'amorçage.
- **`TTC_SET_DATA_RATE` refusé par un S1.8 avec l'erreur 0x0007 après l'amorçage de l'application :** le mode balise est toujours verrouillé — l'étape 5a a été omise ou son `TTC_SET_BEACON_MODE(on=0)` n'a pas été accepté. Lire l'avis d'échec S1.8 : il nomme le verrou mot pour mot (« TM rate is forced to the beacon tier in beacon mode (LOW refused) »), et le même texte apparaît comme événement S5 `0x030B COMMAND_REJECTED` dans le journal des événements et le journal FDIR. Exécuter de nouveau l'étape 5a. L'amorçage de l'application ne désactive délibérément pas le mode balise.
- **Le maintien automatique de l'émetteur expire avant la fin de la procédure :** toute TC acceptée ultérieurement réarme la temporisation à 15 minutes ; cela ne devrait donc pas se produire au cours d'un passage normal. Si l'opérateur reste 15 minutes sans envoyer de commande, la liaison tombe — renvoyer une TC quelconque pour la réalimenter.

## État de sortie
- Liaison bidirectionnelle en bande S établie (maintien automatique de l'émetteur actif ; `ttc_tx`
  retombe si l'opérateur reste 15 min sans envoyer de commande — les fiches LEOP
  qui ont besoin de la liaison descendante la rétablissent, elles ne la supposent pas acquise)
- OBC sur l'image applicative (`obdh.sw_image` 0x0311 = 1) ; phase de mission = 4
  (LEOP, avancée automatiquement par l'amorçage)
- Mode balise désactivé (`ttc.beacon_mode` 0x0521 = 0), liaison descendante sur le échelon LOW
  (`ttc.tm_tier` 0x0539 = 1) ; SID HK 1, 3, 4, 6, 11 activés — les SID 2/5/7/8/9/12
  restent désactivés jusqu'à ce que la fiche qui alimente leur sous-système les active
- Horloge toujours NON RÉGLÉE (`obdh.time_ref` 0x0A13 = 0) — synchronisée dans LEOP-006
- Toutes les lignes réchauffeurs, AOCS, charge utile, refroidisseur et propulsion toujours sur OFF ; rien d'autre
  que la liaison et l'image de l'OBC n'a été modifié par cette fiche

## Postconditions
- [ ] Rapport de première acquisition diffusé
- [ ] État de sortie ci-dessus vérifié

**PROCÉDURE SUIVANTE :** LEOP-002 (Bilan de santé initial)
