# Procédures de contingence de la recette en orbite {#commissioning-contingency-procedures}

## Vue d'ensemble {#overview}

Ce document est une référence d'accompagnement du **Déroulé de la séquence de recette en orbite** (commissioning_sequence_walkthrough.md). Il met en correspondance chaque phase de la recette en orbite et ses modes de défaillance possibles avec les procédures de contingence et d'urgence à suivre lorsqu'une étape échoue.

Chaque mode de défaillance comprend :
- **Symptômes :** indicateurs observables sur le MCS (système de contrôle de mission) et dans la télémesure
- **Procédure :** code de référence (CTG-XXX pour une contingence, EMG-XXX pour une urgence) et nom de la procédure
- **Reprise :** synthèse de haut niveau des résultats attendus et des étapes suivantes

Pendant la recette en orbite, consulter ce document dès qu'un comportement inattendu se présente. Suivre exactement les procédures référencées et faire remonter au contrôle de mission si elles ne résolvent pas le problème.

---

## Phase 0 — Premier contact (passage 1) {#phase-0--first-contact-pass-1}

### Défaillance : aucune télémesure reçue {#failure-no-telemetry-received}

**Symptômes :**
- Le MCS n'affiche aucun indicateur de puissance du signal reçu (RSSI)
- Aucune trame de télémesure décodée après toute la durée du passage
- Récepteur de la station sol opérationnel et correctement pointé

**Procédure :** [CTG-019](../procedures/contingency/no_telemetry_at_pass.md) (no_telemetry_at_pass.md)

**Reprise :** suivre l'arbre de dépannage de la chaîne de réception, de la puissance de l'émetteur et de l'orientation de l'antenne. Programmer des passages de suivi sur d'autres stations sol si possible. Vérifier l'orientation du satellite et l'état de déploiement du générateur solaire au passage suivant.

---

### Défaillance : télémesure reçue mais la liaison TTC ne se verrouille pas {#failure-telemetry-received-but-ttc-link-wont-lock}

**Symptômes :**
- Signal RSSI détecté et stable
- Taux d'erreur binaire (TEB) > 1×10⁻³ et fluctuant
- Aucune synchronisation symbole verrouillée dans le démodulateur
- Codes de mesure de distance (ranging) non acquis

**Procédure :** [CTG-003](../procedures/contingency/ttc_link_loss.md) (ttc_link_loss.md)

**Reprise :** contrôler le décalage de fréquence et la compensation Doppler. Vérifier la sortie de l'amplificateur de puissance RF. Si la liaison se verrouille après ajustement de la fréquence, reprendre la séquence normale. Si la liaison reste instable, soupçonner un problème de déploiement de l'antenne et se reporter aux modes de défaillance de la phase 2.

---

### Défaillance : OBC dans un état inattendu (pas en mode chargeur d'amorçage) {#failure-obc-in-unexpected-state-not-bootloader}

**Symptômes :**
- Télémesure reçue, mais message balise non reconnu ou corrompu
- L'OBC semble être en mode scientifique ou dans un état inconnu
- Pas d'expiration du chien de garde observée
- Corruption de la mémoire ou de l'image soupçonnée

**Procédure :** [CTG-015](../procedures/contingency/corrupted_image.md) (corrupted_image.md) ou [CTG-021](../procedures/contingency/obc_bootloader_recovery.md) (obc_bootloader_recovery.md)

**Reprise :** évaluer la gravité d'après le contenu de la télémesure. Si l'image est corrompue mais que le chargeur d'amorçage répond, procéder à la reprise de l'amorçage (CTG-021). Si l'image est intacte mais dans un mode inattendu, suivre la séquence d'arrêt sûr et de redémarrage. Si la corruption empêche d'atteindre un état sûr, passer aux procédures d'urgence.

---

## Phase 1 — Activation du satellite {#phase-1--spacecraft-activation}

### Défaillance : l'envoi de commandes échoue {#failure-command-uplinking-fails}

**Symptômes :**
- Commande montante émise non acquittée
- Aucun écho de la commande dans la télémesure
- TEB acceptable, mais l'analyseur de commandes ne répond pas

**Procédure :** [CTG-003](../procedures/contingency/ttc_link_loss.md) (ttc_link_loss.md)

**Reprise :** vérifier le format des commandes par rapport à la spécification du protocole en bande S. Confirmer que l'OBC est à l'écoute du récepteur de commandes (un changement de mode par commande en aveugle peut être nécessaire). Si la commutation du récepteur échoue, attendre le basculement automatique sur le transpondeur redondant (s'il existe).

---

### Défaillance : la batterie du satellite ne répond pas aux commandes {#failure-spacecraft-battery-not-responding-to-commands}

**Symptômes :**
- Aucune variation de la consommation après les commandes EPS
- Tension de la batterie figée dans la balise
- Aucune réponse aux commandes de mise sous tension de quelque sous-système que ce soit

**Procédure :** [CTG-013](../procedures/contingency/battery_cell_failure.md) (battery_cell_failure.md) ou demander des instructions au directeur de vol

**Reprise :** contrôler l'état de l'interrupteur d'isolement de la batterie dans la télémesure si possible.

---

## Phase 2 — Déploiement de l'antenne {#phase-2--antenna-deployment}

### Défaillance : commande de déploiement de l'antenne acquittée, mais aucun déploiement physique {#failure-antenna-deployment-command-acknowledged-but-no-physical-deployment}

**Symptômes :**
- Commande de déploiement renvoyée en écho dans la télémesure
- Le RSSI chute juste après la commande (perte de l'antenne fouet)
- Le registre d'état indique toujours l'antenne à l'état STOWED
- La puissance du signal ne s'améliore pas

**Procédure :** [CTG-019](../procedures/contingency/no_telemetry_at_pass.md) (no_telemetry_at_pass.md) (antenne de bord ; la CTG-020 est la fiche de l'antenne de la station sol) — vérifier si antenna_deployment_sensor est à l'état JAMMED

**Reprise :** examiner la télémesure à la recherche d'indicateurs de défaut du capteur. Si le capteur indique JAMMED, le mécanisme de déploiement est peut-être bloqué — ne pas renouveler la tentative. Si le capteur fonctionne mais que l'antenne n'est pas déployée, vérifier l'alimentation de l'actionneur de déploiement par l'EPS. Une intervention mécanique peut être nécessaire après revue de mission.

---

### Défaillance : l'antenne se déploie, mais la qualité de la liaison ne s'améliore pas {#failure-antenna-deploys-but-link-quality-doesnt-improve}

**Symptômes :**
- L'état de l'antenne indique DEPLOYED
- RSSI toujours faible ou instable
- Le TEB reste élevé après le déploiement
- Caractéristique du signal semblable à celle de l'antenne fouet

**Procédure :** [CTG-019](../procedures/contingency/no_telemetry_at_pass.md) (no_telemetry_at_pass.md) — vérifier l'intégrité de la chaîne TTC

**Reprise :** soupçonner un déploiement manqué (antenne physiquement repliée malgré l'état du registre). Effectuer le diagnostic TTC complet : contrôler l'état des commutateurs RF, la continuité du diplexeur, le gain du LNA et la sortie de l'émetteur. Si tous les systèmes côté sol sont nominaux, l'antenne est probablement bloquée mécaniquement. Programmer le renvoi de la commande de déploiement au passage suivant.

---

## Phase 3 — Amorçage de l'OBC {#phase-3--obc-boot}

### Défaillance : l'OBC reste en mode chargeur d'amorçage après la commande d'amorçage {#failure-obc-remains-in-bootloader-after-boot-command}

**Symptômes :**
- Le signal de vie du chargeur d'amorçage continue après la commande d'amorçage S1
- `sw_image` (0x0311) vaut 0 : l'OBC est toujours dans le chargeur d'amorçage
- Aucune tentative de chargement de l'image applicative
- Le délai d'attente expire sans repli

**Procédure :** [CTG-021](../procedures/contingency/obc_bootloader_recovery.md) (obc_bootloader_recovery.md)

**Reprise :** suivre l'arbre de reprise pour identifier une corruption d'image, un défaut mémoire ou un plantage de l'OBC. Si l'image est intacte, envoyer une commande d'amorçage forcé. Si l'image est corrompue, utiliser l'image d'amorçage de secours (si elle a été préchargée). Passer à CTG-015 si la corruption est confirmée.

---

### Défaillance : l'OBC s'amorce correctement mais redémarre au bout de quelques minutes {#failure-obc-boots-successfully-but-reboots-within-minutes}

**Symptômes :**
- La télémesure montre d'abord l'OBC en mode NOMINAL
- Redémarrage inattendu au bout de 2–10 minutes
- Expiration du chien de garde ou réinitialisation externe signalée dans les journaux
- Le schéma se répète sur plusieurs passages

**Procédure :** [CTG-011](../procedures/contingency/obc_redundancy_switchover.md) (obc_redundancy_switchover.md)

**Reprise :** envoyer la commande de basculement sur le CPU secondaire de l'OBC. Si le basculement réussit, utiliser le secondaire pour la recette en orbite et diagnostiquer le principal hors ligne. Si les deux CPU présentent le même défaut, soupçonner un défaut mémoire ou d'alimentation — passer à CTG-016 ou CTG-013.

---

### Défaillance : défaillance d'un segment mémoire détectée pendant l'amorçage {#failure-memory-segment-failure-detected-during-boot}

**Symptômes :**
- L'OBC signale des erreurs EDAC mémoire dans la télémesure de santé
- Le processus d'amorçage aboutit, mais le nombre d'erreurs augmente
- Erreurs localisées dans une plage d'adresses précise
- Le système semble par ailleurs fonctionner normalement

**Procédure :** [CTG-016](../procedures/contingency/memory_segment_failure.md) (memory_segment_failure.md)

**Reprise :** mettre hors service le segment mémoire défaillant par une commande OBC si possible. Si les erreurs touchent une zone de code critique, procéder avec prudence et surveiller la croissance du taux d'erreurs. Programmer le transfert de la mémoire vers le sol si les erreurs s'aggravent. Ne pas engager les phases suivantes avant la stabilisation du taux d'erreurs.

---

## Phase 4 — Bilan de santé {#phase-4--health-check}

### Défaillance : tension de la batterie sous le seuil minimal {#failure-battery-voltage-below-minimum-threshold}

**Symptômes :**
- Télémesure de tension de la batterie < 29.6 V (ou minimum défini)
- Tension en baisse d'une balise à l'autre
- Le délestage EPS est peut-être actif
- Température de la batterie nominale

**Procédure :** [CTG-001](../procedures/contingency/undervoltage_loadshed.md) (undervoltage_loadshed.md) ou [CTG-023](../procedures/contingency/progressive_load_shed.md) (progressive_load_shed.md)

**Reprise :** envoyer une commande de délestage pour désactiver les sous-systèmes non essentiels. L'EPS appliquera l'ordre de priorité : OBDH > TTC > TCS > charge utile. Recharger la batterie en orientant le générateur solaire vers le Soleil. Ne reprendre la recette en orbite qu'une fois la tension remontée au-dessus de 31.5 V pendant au moins 30 minutes. Si la tension ne remonte pas, soupçonner une dégradation de la batterie — se reporter à CTG-013.

---

### Défaillance : défaillance ou déséquilibre d'éléments de batterie détecté {#failure-battery-cell-failure-or-imbalance-detected}

**Symptômes :**
- La télémesure montre un écart de tension > 0.5 V entre éléments
- Tension d'un élément < 3.2 V alors que les autres sont nominaux
- Pic de température de la batterie (> 45 °C)
- La tension fluctue avec les transitoires de charge

**Procédure :** [CTG-013](../procedures/contingency/battery_cell_failure.md) (battery_cell_failure.md)

**Reprise :** désactiver les charges non essentielles et stabiliser l'état de la batterie. L'EPS peut contourner automatiquement l'élément défaillant si une redondance existe. Si la défaillance de l'élément persiste, fonctionner avec un bilan de puissance réduit et allonger le calendrier de la mission. Prévenir le directeur de vol pour une évaluation des risques avant de poursuivre.

---

### Défaillance : tension du bus hors plage {#failure-bus-voltage-out-of-range}

**Symptômes :**
- Tension du bus principal hors de la fenêtre 24,0–33,4 V (batterie BPX 8S-1P, plafond du bus 33,4 V)
- Tension du bus secondaire également affectée s'il est alimenté
- Pics transitoires ou écart durable observés
- Corrélation avec les événements de commutation de charges

**Procédure :** [CTG-022](../procedures/contingency/bus_failure_isolation.md) (bus_failure_isolation.md) ou [CTG-017](../procedures/contingency/bus_failure_switchover.md) (bus_failure_switchover.md)

**Reprise :** envoyer une commande d'isolement pour identifier le chemin de distribution de puissance défaillant. Si le bus principal tombe en panne, transférer les charges sur le bus secondaire (CTG-017). Si les deux bus sont affectés, soupçonner un défaut de la batterie ou du régulateur — passer à CTG-013 ou contacter le directeur de vol. Ne revenir aux opérations normales qu'après 10 minutes de tension stable.

---

### Défaillance : température hors plage (sous-système) {#failure-temperature-out-of-range-subsystem}

**Symptômes :**
- La température d'un sous-système dépasse les limites nominales (typiquement de −20 °C à +50 °C)
- Zone thermique précise affectée (p. ex. batterie, OBC, charge utile)
- Alarme de température levée dans la télémesure de santé
- La vitesse de variation indique un échauffement actif ou une perte de refroidissement

**Procédure :** [CTG-004](../procedures/contingency/thermal_exceedance.md) (thermal_exceedance.md)

**Reprise :** réduire l'alimentation du sous-système en surchauffe si cela ne présente pas de danger (cela peut provoquer son arrêt). Orienter le satellite pour améliorer la vue du radiateur sur l'espace profond si possible. Si la surchauffe persiste, réduire le bilan de puissance global et retarder les phases à forte puissance. Si la température reste élevée pendant > 30 minutes, passer à EMG-006 (emballement thermique).

---

## Phase 5 — Configuration de la mise en mémoire tampon de la TM {#phase-5--tm-buffering-configuration}

### Défaillance : les données de servitude ne circulent pas après la commande d'activation {#failure-housekeeping-not-flowing-after-enable-command}

**Symptômes :**
- Commande d'activation des données de servitude acquittée
- Aucune trame HK visible dans la télémesure descendante
- L'état du sous-système HK indique NOT_ACTIVE
- Le mode de l'OBC ne prend peut-être pas en charge le flux HK

**Procédure :** vérifier le mode de l'OBC et l'état des sous-systèmes par lecture directe de la télémesure. Se reporter aux diagnostics de la phase 5 du déroulé de recette en orbite.

**Reprise :** confirmer que l'OBC exécute l'application (`sw_image` = 1) en mode NOMINAL (et non SAFE). Envoyer une commande explicite de démarrage des HK avec le bon identifiant de flux. Vérifier que les paramètres S5 sont correctement réglés dans la mémoire de l'OBC. Toujours sans données, soupçonner un problème logiciel de l'OBC — passer à CTG-021.

---

### Défaillance : anomalie de remplissage du tampon ou utilisation excessive du tampon {#failure-buffer-fill-anomaly-or-excessive-buffer-usage}

**Symptômes :**
- Pourcentage de remplissage du tampon en hausse inattendue
- Cadence des trames HK supérieure à la cadence commandée
- Utilisation mémoire en alarme dans la télémesure de santé
- Risque de débordement du tampon et de perte de données

**Procédure :** se reporter à [CTG-016](../procedures/contingency/memory_segment_failure.md) (memory_segment_failure.md) si un problème de mémoire est soupçonné

**Reprise :** réduire la cadence de la télémesure HK par une commande S5.x. Vider immédiatement le contenu du tampon vers le sol lors d'un passage à haut débit. Contrôler l'ordonnancement des tâches de l'OBC à la recherche de tâches emballées. En cas de débordement du tampon, la perte de données est inévitable — documenter la période de perte et reprendre à cadence réduite.

---

## Phase 6 — Réglage du temps {#phase-6--set-time}

### Défaillance : commande de réglage du temps rejetée {#failure-time-set-command-rejected}

**Symptômes :**
- Commande S9.1 (`SET_TIME`) rejetée ou non acquittée
- Valeur du temps dans l'OBC non mise à jour
- L'OBC est peut-être dans un mode inadapté aux commandes de temps
- Erreur de décalage temporel signalée dans la réponse

**Procédure :** vérifier que l'OBC est en mode NOMINAL. Contrôler que le jeu de paramètres S9 est accessible. Confirmer que le format du temps correspond au format attendu (p. ex. secondes UTC depuis l'époque).

**Reprise :** renouveler le réglage du temps avec une heure exacte vérifiée et le bon format. En cas de nouveau rejet, l'OBC applique peut-être un verrouillage de synchronisation temporelle — attendre un événement de synchronisation automatique ou envoyer une réinitialisation de mode. Ne pas engager la phase 7 avec un temps non réglé, car la propagation des TLE et la programmation des commandes dépendent d'un temps exact.

---

### Défaillance : la synchronisation du temps sur le GPS perturbe l'AOCS {#failure-time-sync-with-gps-causes-aocs-disruption}

**Symptômes :**
- Commande d'étiquette de temps GPS envoyée avec succès
- Juste après, l'AOCS passe en mode survie ou présente une anomalie d'amortissement
- Pic des vitesses angulaires ou perte de verrouillage du senseur stellaire
- Désaccord de temps entre l'OBC et le sous-système AOCS

**Procédure :** [CTG-027](../procedures/contingency/gps_time_sync_recovery.md) (gps_time_sync_recovery.md)

**Reprise :** anomalie AOCS déclenchée par un saut de temps brutal. Envoyer la commande de sortie du mode survie de l'AOCS et laisser l'attitude se réacquérir. Resynchroniser le temps par petits incréments si possible, ou coordonner la mise à jour du temps pendant une éclipse, lorsque l'AOCS est moins sensible. Vérifier le décalage d'horloge de l'AOCS après la reprise.

---

## Phase 7 — Mise sous tension (sous-systèmes) {#phase-7--power-on-subsystems}

### Défaillance : la ligne d'alimentation ne commute pas malgré la commande {#failure-power-line-wont-switch-despite-command}

**Symptômes :**
- Commande de mise sous tension acquittée
- Le sous-système ne répond pas sur le bus
- L'état du sous-système reste OFF dans la télémesure
- Le relais ou le disjoncteur de l'EPS ne s'actionne pas

**Procédure :** contrôler le mode de l'EPS et vérifier l'absence de verrouillage sur surintensité. Se reporter à [CTG-012](../procedures/contingency/overcurrent_response.md) (overcurrent_response.md) si une surintensité est détectée.

**Reprise :** envoyer la commande de la ligne d'alimentation redondante si elle existe. Vérifier que l'EPS n'est pas en mode survie (CTG-005). Si un relais mécanique est bloqué, tenter un cycle de réchauffage (brève impulsion de puissance) ou attendre le cycle thermique suivant. Faire remonter au directeur de vol si la ligne reste inerte.

---

### Défaillance : déclenchement sur surintensité d'une ligne d'alimentation {#failure-overcurrent-trip-on-power-line}

**Symptômes :**
- La commande de mise sous tension provoque un pic de courant immédiat
- Le disjoncteur de surintensité de l'EPS s'ouvre automatiquement
- Le sous-système s'arrête au bout de < 1 seconde
- Alarme de limite de courant dans la télémesure

**Procédure :** [CTG-012](../procedures/contingency/overcurrent_response.md) (overcurrent_response.md)

**Reprise :** soupçonner un court-circuit ou un défaut interne du sous-système. Ne pas renouveler immédiatement la mise sous tension — attendre 5 minutes le réarmement thermique du disjoncteur. Lancer des diagnostics pour rechercher des indications de défaut sur le sous-système. Si la surintensité se répète, le sous-système est défaillant ; isoler la ligne et prévenir le directeur de vol. Traiter le sous-système suivant et revenir à cette ligne après analyse de mission.

---

### Défaillance : problèmes de générateur solaire (sous-performance ou intermittence) {#failure-solar-array-issues-underperforming-or-intermittent}

**Symptômes :**
- Courant du générateur solaire inférieur à l'attendu pour l'angle solaire
- Le courant fluctue ou tombe à zéro
- Tension instable sur le bus non régulé
- Production de puissance insuffisante pour la charge

**Procédure :** [CTG-009](../procedures/contingency/solar_array_degradation.md) (solar_array_degradation.md) ou [CTG-024](../procedures/contingency/solar_panel_loss_response.md) (solar_panel_loss_response.md)

**Reprise :** confirmer l'orientation du générateur solaire et l'angle solaire. Rechercher une ombre portée par des appendices déployés. En cas de perte partielle du générateur, réduire le bilan de puissance et ajuster l'attitude pour maximiser l'exposition des panneaux restants. En cas de suspicion de panne complète du générateur, passer sur batterie et faire remonter l'anomalie — le satellite ne peut pas maintenir ses opérations sans production solaire.

---

### Défaillance : l'EPS passe en mode survie de manière inattendue {#failure-eps-enters-safe-mode-unexpectedly}

**Symptômes :**
- Le sous-système EPS se trouve soudain à l'état SAFE_MODE
- Aucune commande de délestage envoyée
- Régulation de puissance anormale
- Batterie en décharge malgré une attitude de pointage solaire

**Procédure :** [CTG-005](../procedures/contingency/eps_safe_mode.md) (eps_safe_mode.md)

**Reprise :** suivre la procédure de sortie du mode survie : confirmer la stabilité des tensions du bus, dérouler la séquence de délestage, puis déclencher une commande explicite de transition de mode. Identifier la condition de déclenchement (sous-tension, surtension, défaut de température) dans la télémesure et traiter la cause première. Ne reprendre la séquence normale de mise sous tension qu'une fois la sortie du mode survie achevée.

---

### Défaillance : l'AOCS refuse d'entrer en mode DETUMBLE {#failure-aocs-wont-enter-detumble-mode}

**Symptômes :**
- Commande de mode DETUMBLE non acquittée ou rejetée
- L'AOCS reste en STANDBY ou dans le mode précédent
- Roues de réaction non mises en rotation
- L'attitude du satellite ne se stabilise pas

**Procédure :** [CTG-002](../procedures/contingency/aocs_anomaly.md) (aocs_anomaly.md)

**Reprise :** vérifier que l'AOCS est alimenté, que l'OBC est opérationnel et que les données des capteurs d'attitude sont valides. Contrôler la télémesure de santé des roues de réaction à la recherche de défauts mécaniques. Renouveler la commande d'amortissement après un bref délai. Si l'AOCS ne répond toujours pas, confirmer que le senseur stellaire et le gyromètre sont alimentés. Passer à CTG-026 si une roue de réaction est soupçonnée d'être bloquée.

---

### Défaillance : roue de réaction bloquée ou ne répondant pas {#failure-reaction-wheel-stuck-or-unresponsive}

**Symptômes :**
- La commande de vitesse de la roue de réaction ne modifie pas sa vitesse
- Courant consommé nul malgré la commande
- Vibrations mécaniques ou bruit de frottement détectés sur le satellite
- Couple produit par la roue sensiblement réduit

**Procédure :** [CTG-026](../procedures/contingency/aocs_actuator_stuck_recovery.md) (aocs_actuator_stuck_recovery.md) ou [CTG-007](../procedures/contingency/reaction_wheel_anomaly.md) (reaction_wheel_anomaly.md)

**Reprise :** si la roue est bloquée, ne pas forcer — confirmer le défaut dans la télémesure. L'AOCS peut continuer avec 2 roues sur 3 ; isoler la roue défaillante et utiliser les roues redondantes pour le contrôle d'attitude. Envoyer une commande d'impulsion mécanique (brève accélération inverse) pour libérer la roue si cela ne présente pas de danger. Si la roue reste bloquée, la documenter pour analyse après mission et continuer avec les actionneurs disponibles.

---

## Phase 8 — Envoi des TLE et propagation d'orbite {#phase-8--tle-upload-and-orbit-propagation}

### Défaillance : l'état orbital ne se propage pas correctement {#failure-orbit-state-does-not-propagate-correctly}

**Symptômes :**
- Les paramètres S20 semblent acceptés (aucune réponse d'erreur)
- La propagation hors ligne d'orbit_tools ne concorde pas avec le calcul de l'OBC
- Heures de passage prédites décalées par rapport aux passages réels
- Éphéméride de position divergeant des mises à jour GPS (phase 11)

**Procédure :** vérifier que les paramètres S20 sont correctement formatés et acceptés. Contrôler que la configuration d'orbit_tools correspond au modèle de l'OBC. Se reporter aux diagnostics de la phase 8 du déroulé de recette en orbite.

**Reprise :** renvoyer le TLE avec des constantes de propagation vérifiées. Confirmer que l'OBC dispose du modèle de densité atmosphérique le plus récent. Si l'écart persiste après le nouvel envoi, comparer la propagation de l'OBC avec les points GPS de référence de la phase 11 pour quantifier l'erreur. Documenter le biais pour la planification de la mission.

---

## Phase 9 — Progression des modes AOCS (amortissement → nadir → pointage solaire) {#phase-9--aocs-mode-progression-detumble--nadir--sun-point}

### Défaillance : les vitesses angulaires ne s'amortissent pas pendant le DETUMBLE {#failure-attitude-rates-not-damping-during-detumble}

**Symptômes :**
- Les vitesses angulaires du satellite restent élevées (> 5°/s)
- Roues de réaction actives mais amortissement inefficace
- Mode DETUMBLE actif depuis > 20 minutes sans amélioration
- Possible ombrage des panneaux solaires entraînant une perte d'autorité de commande

**Procédure :** [CTG-002](../procedures/contingency/aocs_anomaly.md) (aocs_anomaly.md)

**Reprise :** confirmer que les roues de réaction disposent d'une alimentation électrique et d'une autorité en couple suffisantes. Contrôler les données des gyromètres à la recherche d'erreurs de facteur d'échelle ou de biais. Vérifier que l'orientation de pointage solaire permet au générateur solaire de produire de la puissance. Si les gyromètres ou les roues sont défaillants, passer à CTG-007 ou CTG-025. Allonger le délai d'attente de l'amortissement ou passer au contrôle magnétique s'il est disponible.

---

### Défaillance : perte d'un capteur pendant une transition de mode {#failure-sensor-loss-during-mode-transition}

**Symptômes :**
- Le senseur stellaire ou le gyromètre perd le verrouillage ou le signal
- L'incertitude d'attitude augmente
- La commande de transition de mode reste en suspens dans l'attente de la reprise du capteur
- Possible problème thermique ou d'alimentation affectant le capteur

**Procédure :** [CTG-025](../procedures/contingency/aocs_sensor_loss_recovery.md) (aocs_sensor_loss_recovery.md)

**Reprise :** confirmer que l'alimentation du capteur est active. Contrôler les conditions thermiques — si le capteur est en surchauffe, réduire la puissance ou attendre qu'il refroidisse. Laisser au capteur le temps d'un démarrage à froid et d'une réacquisition (jusqu'à 60 secondes). Vérifier qu'un capteur redondant est disponible et basculer dessus si le principal est défaillant. Si les deux capteurs sont perdus, passer à une procédure EMG et revenir en mode survie.

---

### Défaillance : échec d'une transition de mode AOCS (impossible d'atteindre le pointage solaire ou nadir) {#failure-aocs-mode-transition-fails-cannot-reach-sun-point-or-nadir}

**Symptômes :**
- Commande de transition de mode envoyée mais non exécutée
- L'AOCS reste dans le mode précédent
- Aucune réponse d'erreur indiquant la raison du rejet de la transition
- Possible problème de loi de commande ou de données capteurs

**Procédure :** [CTG-002](../procedures/contingency/aocs_anomaly.md) (aocs_anomaly.md)

**Reprise :** vérifier que l'AOCS dispose de données capteurs valides (vitesses, vecteur Soleil, senseur stellaire). Contrôler que les gains de la loi de commande ne sont pas saturés. Confirmer que la cible d'attitude (vecteur de pointage solaire ou vecteur nadir) est atteignable avec les actionneurs disponibles. Renouveler la transition de mode. En cas d'échecs répétés, soupçonner un défaut logiciel de l'OBC ou de communication — passer à CTG-021.

---

## Phase 10 — Vérification sur une orbite complète {#phase-10--whole-orbit-verification}

### Défaillance : emballement thermique détecté {#failure-thermal-runaway-detected}

**Symptômes :**
- Température en hausse incontrôlée dans une zone thermique
- Vitesse de hausse > 1 °C par minute
- Le sous-système de contrôle thermique ne parvient pas à enrayer la hausse
- Alarme de surchauffe imminente ou déclenchée

**Procédure :** [EMG-006](../procedures/emergency/thermal_runaway.md) (thermal_runaway.md)

**Reprise :** il s'agit d'une situation d'urgence. Délester immédiatement les sous-systèmes concernés si possible. Orienter les radiateurs à l'opposé du Soleil (attitude d'urgence). Lancer une transition en mode survie pour minimiser la puissance dissipée. Si l'emballement se poursuit, préparer l'arrêt forcé du sous-système concerné ou le mode survie au niveau du satellite. Contacter immédiatement le directeur de vol.

---

### Défaillance : perte totale d'alimentation {#failure-total-power-failure}

**Symptômes :**
- Tous les sous-systèmes perdent l'alimentation simultanément
- La télémesure descendante s'interrompt
- Seul le signal de vie de la balise continue (s'il est sur batterie indépendante)
- Tension de la batterie nulle ou sortie du régulateur défaillante

**Procédure :** [EMG-002](../procedures/emergency/total_power_failure.md) (total_power_failure.md)

**Reprise :** il s'agit d'une urgence. Si elle se produit, le satellite a perdu son bus d'alimentation principal. Attendre la reprise de la recharge solaire au passage éclairé suivant. Si aucun retour de l'alimentation n'est détecté après 2 passages, le satellite est probablement irrécupérable.

---

### Défaillance : passage inattendu en mode survie {#failure-unexpected-safe-mode-triggered}

**Symptômes :**
- L'AOCS passe soudain en mode survie sans commande
- Délestage actif
- Contrôle d'attitude par les seuls magnétocoupleurs
- La logique FDIR a peut-être détecté un défaut

**Procédure :** [EMG-005](../procedures/emergency/loss_of_attitude.md) (loss_of_attitude.md)

**Reprise :** rechercher dans la télémesure la condition de déclenchement FDIR : perte de capteur, dépassement de limite de vitesse, sous-tension, ou expiration d'un délai de commande. Vérifier que tous les systèmes sont nominaux. Envoyer la commande de sortie du mode survie une fois les conditions stables. Si le satellite repasse en mode survie de manière répétée, faire remonter au directeur de vol. Ne pas forcer la sortie tant que la cause première n'est pas identifiée.

---

## Phase 11 — Activation du GPS et reprise du temps {#phase-11--gps-activation-and-time-recovery}

### Défaillance : le GPS n'acquiert pas de verrouillage {#failure-gps-wont-acquire-lock}

**Symptômes :**
- Récepteur GPS sous tension mais ne signalant pas de verrouillage
- Nombre de satellites nul ou très faible
- Sortie position/temps peu fiable ou figée
- Reprise par démarrage à chaud du récepteur insuffisante

**Procédure :** laisser le GPS effectuer un démarrage à froid (5–20 minutes selon le type de récepteur). Vérifier que l'antenne GPS a une vue dégagée du ciel. Contrôler l'alimentation du récepteur et la qualité du signal. Confirmer que l'OBC ne supprime pas les mises à jour GPS.

**Reprise :** l'acquisition GPS peut prendre un temps considérable à la première mise sous tension (démarrage à froid). Poursuivre la recette en orbite avec l'orbite propagée jusqu'à l'obtention du verrouillage. Une fois le GPS verrouillé, valider la cohérence de la position par rapport à l'orbite propagée (typiquement < 10 km). Si le GPS continue d'échouer, il peut s'agir d'un problème d'antenne ou d'un défaut du récepteur — faire remonter au directeur de vol pour un diagnostic approfondi.

---

### Défaillance : la synchronisation du temps sur le GPS provoque une réinitialisation ou une anomalie de l'AOCS {#failure-gps-time-sync-causes-aocs-reset-or-anomaly}

**Symptômes :**
- Commande d'étiquette de temps GPS exécutée
- L'AOCS passe immédiatement en mode survie ou signale une anomalie
- Discontinuité temporelle détectée dans les journaux
- Contrôle d'attitude dégradé après la synchronisation

**Procédure :** [CTG-027](../procedures/contingency/gps_time_sync_recovery.md) (gps_time_sync_recovery.md)

**Reprise :** la synchronisation du temps sur le GPS provoque un saut de temps brutal que l'AOCS peut ne pas tolérer. L'AOCS se rétablira à l'éclipse suivante ou après un redémarrage de mode. Envoyer la sortie du mode survie de l'AOCS et laisser la réinitialisation se faire. Pour les synchronisations futures, les coordonner avec le mode de l'AOCS (p. ex. pendant STANDBY) afin de limiter les perturbations. Valider le décalage temporel avant la synchronisation suivante.

---

## Phase 12 — Vérification du senseur stellaire {#phase-12--star-tracker-checkout}

### Défaillance : le senseur stellaire reste à l'état BOOT {#failure-star-tracker-stays-in-boot-state}

**Symptômes :**
- Alimentation du senseur stellaire confirmée, mais pas de passage à IDLE
- L'état reste BOOT au bout de > 60 secondes
- Aucune donnée d'attitude fournie
- Possible problème d'alimentation ou d'initialisation

**Procédure :** vérifier que l'alimentation du senseur stellaire est stable. Laisser s'écouler les 60 secondes complètes d'amorçage. Contrôler la ligne d'alimentation à la recherche de baisses de tension. Confirmer qu'aucun arrêt sur surchauffe ne s'est produit.

**Reprise :** laisser un temps d'amorçage supplémentaire (jusqu'à 120 secondes au total). S'il est toujours en BOOT, effectuer un cycle d'alimentation de la ligne (coupée 30 secondes, puis rétablie). Vérifier que la tension d'alimentation est conforme à la spécification (12 V ± 2 V typique). Si le senseur stellaire ne répond toujours pas, soupçonner un défaut interne et faire remonter au directeur de vol. Poursuivre avec un contrôle d'attitude sur gyromètres seuls.

---

### Défaillance : senseur stellaire ébloui (aucune étoile visible) {#failure-star-tracker-blinded-no-stars-visible}

**Symptômes :**
- Le senseur stellaire signale un nombre d'étoiles insuffisant
- Sortie d'attitude indisponible ou erratique
- Se produit typiquement lorsque le Soleil est proche du champ de vue
- Normal pendant la moitié éclairée de l'orbite

**Procédure :** l'éblouissement du senseur stellaire est normal si le Soleil est dans le champ de vue. Aucune action corrective n'est nécessaire.

**Reprise :** ce comportement est attendu. Le senseur stellaire se rétablit dès que le Soleil quitte le champ de vue ou en éclipse. Ne pas tenter de rétablir un senseur ébloui — attendre le rétablissement naturel en éclipse ou lors d'un changement de position orbitale. Planifier les activités de recette en orbite de façon à éviter les périodes de reflet solaire si des mesures d'attitude prolongées sont nécessaires.

---

### Défaillance : panne matérielle du senseur stellaire {#failure-star-tracker-hardware-failure}

**Symptômes :**
- Le senseur stellaire signale un code d'erreur interne
- Perte persistante des données d'attitude, même hors reflet solaire
- Un cycle d'alimentation ne rétablit pas la situation
- L'erreur persiste sur plusieurs passages

**Procédure :** [CTG-008](../procedures/contingency/star_tracker_failure.md) (star_tracker_failure.md)

**Reprise :** isoler le senseur stellaire défaillant si une redondance existe. L'AOCS peut fonctionner avec un contrôle sur gyromètres seuls ou avec le senseur stellaire secondaire. Informer le directeur de vol de la panne du principal. Si les deux senseurs stellaires tombent en panne, passer à CTG-025 (aocs_sensor_loss_recovery.md) et préparer un mode de contrôle sur gyromètres seuls ou magnétique.

---

### Défaillance : les deux senseurs stellaires en panne ou indisponibles {#failure-both-star-trackers-fail-or-unavailable}

**Symptômes :**
- Senseurs stellaires principal et secondaire tous deux hors service
- Le contrôle d'attitude ne repose que sur les gyromètres
- Aucune référence externe pour la détermination d'attitude
- La dérive des gyromètres limite la durée de la mission

**Procédure :** [CTG-025](../procedures/contingency/aocs_sensor_loss_recovery.md) (aocs_sensor_loss_recovery.md)

**Reprise :** il s'agit d'une configuration dégradée. L'AOCS peut continuer avec un contrôle fondé sur les gyromètres, mais avec une incertitude croissante dans le temps. Augmenter la fréquence de la détermination d'attitude au sol. Envisager d'utiliser les bobines magnétiques pour la correction d'attitude si elles sont disponibles. Mener les activités de recette critiques ; reporter les activités non essentielles dans l'attente du rétablissement d'un senseur stellaire. Faire remonter au directeur de vol si aucune référence d'attitude n'est disponible.

---

## Phase 13 — Vérification des redondances {#phase-13--redundancy-checkout}

### Défaillance : échec du basculement de bus {#failure-bus-switchover-fails}

**Symptômes :**
- Commande de basculement acquittée mais non exécutée
- Le bus principal alimente toujours les charges
- Bus redondant non activé
- Distribution de puissance inchangée

**Procédure :** [CTG-022](../procedures/contingency/bus_failure_isolation.md) (bus_failure_isolation.md) ou [CTG-017](../procedures/contingency/bus_failure_switchover.md) (bus_failure_switchover.md)

**Reprise :** vérifier que le matériel de basculement de l'EPS fonctionne. Rechercher des conditions de tension empêchant la commutation (un forçage manuel du seuil peut être nécessaire). Confirmer que le bus secondaire est sain avant de renouveler la tentative. Si la commande de basculement échoue encore, soupçonner un défaut du micrologiciel de l'EPS ou du matériel de commutation. Faire remonter au directeur de vol et poursuivre les essais de redondance restants sur les autres systèmes.

---

### Défaillance : échec des communications sur le transpondeur redondant {#failure-redundant-transponder-communication-fails}

**Symptômes :**
- Basculement sur le transpondeur secondaire commandé
- Aucun signal descendant sur la fréquence secondaire
- Le transpondeur principal fonctionne toujours
- Le temps de verrouillage du récepteur dépasse le seuil normal sur le secondaire

**Procédure :** [CTG-003](../procedures/contingency/ttc_link_loss.md) (ttc_link_loss.md)

**Reprise :** vérifier que le transpondeur secondaire dispose de sa puissance RF et émet sur la bonne fréquence. Contrôler que le récepteur de la station sol est accordé sur la fréquence secondaire. Si le secondaire présente un défaut matériel, continuer avec le transpondeur principal. Si les deux fonctionnent mais que le secondaire montre de faibles performances, le documenter pour analyse après mission et utiliser le principal pour le reste de la mission. Faire remonter les essais critiques au directeur de vol si la redondance secondaire ne peut pas être vérifiée.

---

### Défaillance : perte des communications pendant l'essai de redondance {#failure-loss-of-communication-during-redundancy-test}

**Symptômes :**
- Commande montante reçue, mais la communication est interrompue
- Signal descendant perdu pendant > 5 minutes (tout le passage)
- La balise n'est plus reçue
- Probablement causée par une erreur de transition de mode pendant l'essai

**Procédure :** [EMG-004](../procedures/emergency/loss_of_communication.md) (loss_of_communication.md)

**Reprise :** il s'agit d'une situation d'urgence. Le satellite est peut-être en mode survie, balise seule. Attendre le passage suivant pour rétablir le contact. N'envoyer aucune autre commande avant le rétablissement des communications. Vérifier que la commande d'essai de redondance était sûre (p. ex. retour à un état connu comme sain). Une fois les communications rétablies, confirmer le mode du satellite et renouveler l'essai avec une séquence plus maîtrisée.

---

## Phase 14 — Télécommandes datées {#phase-14--time-tagged-commands}

### Défaillance : une commande programmée ne s'exécute pas à l'heure prévue {#failure-scheduled-command-does-not-execute-at-designated-time}

**Symptômes :**
- Commande envoyée et vérifiée dans la mémoire du plan
- L'heure d'exécution prévue passe sans effet de la commande
- Aucun écho de la commande dans la télémesure
- Possible problème de synchronisation temporelle ou d'analyse du plan

**Procédure :** vérifier que le temps de l'OBC est synchronisé (comparer avec l'horodatage transmis au sol). Contrôler l'état de la mémoire du plan S11 et le nombre de commandes. Confirmer que le format de la commande et l'heure d'exécution sont correctement codés.

**Reprise :** valider le temps de l'OBC par rapport à une source de référence au sol ou au temps GPS. Renvoyer la commande avec un décalage temporel vérifié. Rechercher une saturation de la file de commandes de l'OBC (trop de commandes en attente). Si le sous-système de programmation est défaillant, envoyer les commandes en exécution immédiate, sans programmation. Passer à CTG-021 si le processeur de commandes de l'OBC est défaillant.

---

### Défaillance : anomalie de taux d'erreur binaire pendant la montée des commandes {#failure-bit-error-rate-anomaly-during-command-uplink}

**Symptômes :**
- L'écho de commande reçu présente des inversions de bits
- Pic de TEB pendant certains types de commandes ou certaines fenêtres de liaison montante
- Corruption de commande détectée par le CRC
- Des erreurs intermittentes suggèrent un problème RF ou de récepteur

**Procédure :** [CTG-014](../procedures/contingency/ber_anomaly.md) (ber_anomaly.md)

**Reprise :** augmenter la puissance de la liaison montante (si la station sol le permet) ou retransmettre sur plusieurs trames avec un codage correcteur d'erreurs. Vérifier que le récepteur de la station sol fonctionne normalement. Si le TEB reste élevé, soupçonner une dégradation du récepteur du satellite. Pour les commandes critiques, mettre en œuvre une séquence de répétition et de vérification des commandes. Utiliser la voie montante redondante si elle est disponible.

---

## Phase 15 — Recette en orbite de la charge utile {#phase-15--payload-commissioning}

### Défaillance : la charge utile ne se met pas sous tension {#failure-payload-wont-power-on}

**Symptômes :**
- Commande de mise sous tension de la charge utile acquittée
- La charge utile ne répond pas sur le bus de données
- Aucun courant consommé observé sur la ligne d'alimentation
- L'état de la charge utile indique OFF

**Procédure :** vérifier que la ligne d'alimentation de la charge utile est activée dans l'EPS. Rechercher un verrouillage sur surintensité (CTG-012). Confirmer que la charge utile reçoit une tension d'alimentation stable.

**Reprise :** renouveler la commande de mise sous tension. Vérifier que l'EPS n'est pas dans un mode de délestage affectant la ligne de la charge utile. Si une surintensité est observée, soupçonner un court-circuit interne de la charge utile — isoler la ligne et prévenir le directeur de vol avant toute nouvelle tentative. Si aucune puissance n'arrive à la charge utile, il peut s'agir d'un défaut de connexion mécanique ou électrique nécessitant une analyse après mission.

---

### Défaillance : le plan focal (FPA) ne refroidit pas {#failure-focal-plane-array-fpa-wont-cool}

**Symptômes :**
- FPA sous tension, mais refroidisseur non activé
- La température du FPA ne baisse pas vers la consigne
- Courant du refroidisseur nul malgré l'alimentation
- Possible défaut du compresseur ou du sous-système de contrôle thermique

**Procédure :** vérifier que la ligne d'alimentation du refroidisseur est active. Contrôler l'état du sous-système de contrôle thermique (TCS) dans la télémesure. Confirmer que la boucle de fluide de refroidissement n'est ni obstruée ni gelée.

**Reprise :** vérifier que le TCS est configuré pour le refroidissement du FPA (il est peut-être en veille). Contrôler les capteurs de température d'entrée/sortie du refroidisseur à la recherche d'anomalies. Si le refroidisseur est bloqué mécaniquement, tenter un cycle de réchauffage (brève impulsion de puissance). Si la température du FPA dépasse les limites pendant les opérations scientifiques, basculer sur le refroidisseur secondaire (s'il existe) ou passer à une prise de vue à rapport cyclique réduit avec refroidissement naturel. Faire remonter au directeur de vol si le contrôle thermique ne peut pas être rétabli.

---

### Défaillance : anomalie ou dysfonctionnement de la charge utile {#failure-payload-anomaly-or-malfunction}

**Symptômes :**
- La télémesure de santé de la charge utile affiche un code d'erreur
- Données scientifiques corrompues ou manquantes
- Les transitions de mode de la charge utile échouent ou se bloquent
- Possible problème interne de micrologiciel ou de matériel

**Procédure :** [CTG-006](../procedures/contingency/payload_anomaly.md) (payload_anomaly.md)

**Reprise :** se reporter aux procédures d'anomalie propres à la charge utile. Effectuer un cycle d'alimentation de la charge utile si l'anomalie persiste. Vérifier que l'interface de commande OBC–charge utile fonctionne. Rechercher des collisions sur le bus de données ou des problèmes de synchronisation. Si l'anomalie n'est pas résolue, retirer la charge utile des opérations scientifiques et la documenter pour un dépannage après mission. Poursuivre les autres phases de recette en orbite avec la charge utile secondaire si elle existe.

---

### Défaillance : échec de la prise d'image ou aucune donnée d'image reçue {#failure-image-capture-fails-or-no-image-data-received}

**Symptômes :**
- Commande de prise d'image acquittée
- Aucune donnée de télémesure d'image transmise au sol
- L'état du tampon d'images n'indique aucune donnée
- L'attitude de pointage AOCS semble correcte

**Procédure :** vérifier que l'attitude AOCS est pointée vers la scène cible. Confirmer que la charge utile est en mode image (et non en veille). Contrôler l'allocation de bande passante de la liaison descendante pour le flux de données d'image. Vérifier que le FPA est alimenté et refroidi à sa température de fonctionnement.

**Reprise :** renouveler la prise d'image avec un pointage sur cible vérifié. Confirmer que l'AOCS a convergé vers la consigne d'attitude (attendre la stabilisation de la boucle de commande). Contrôler l'état du mode de la charge utile et son horloge — la prise d'image peut exiger une fenêtre temporelle précise de l'OBC. Si aucune image n'est toujours acquise, vérifier que le capteur du FPA fonctionne au moyen des diagnostics de mise sous tension. Passer à CTG-006 si le matériel de prise d'image est défaillant.

---

## Phase 16 — Remise aux opérations de mission {#phase-16--handover-to-mission-operations}

### Défaillance : bilan de puissance négatif (production insuffisante) {#failure-power-budget-negative-insufficient-generation}

**Symptômes :**
- La consommation moyenne dépasse la capacité de production solaire
- Batterie en décharge même pendant la portion éclairée de l'orbite
- Tension en baisse d'une orbite à l'autre
- Impossible de maintenir indéfiniment la configuration actuelle

**Procédure :** [CTG-023](../procedures/contingency/progressive_load_shed.md) (progressive_load_shed.md)

**Reprise :** mettre en œuvre un délestage progressif pour réduire la consommation. Donner la priorité à l'OBDH et au TTC ; reporter les activités scientifiques de la charge utile ou en réduire le rapport cyclique. Ajuster l'attitude pour maximiser la production du générateur solaire. Allonger la durée de survie en éclipse si nécessaire. Se coordonner avec les opérations de mission pour établir un profil de puissance soutenable avant la remise finale. Si le bilan de puissance reste négatif, la durée de la mission est limitée — faire remonter au directeur de vol pour une planification de contingence.

---

### Défaillance : sous-système non nominal en fin de recette en orbite {#failure-subsystem-not-nominal-at-end-of-commissioning}

**Symptômes :**
- Un ou plusieurs sous-systèmes en mode DEGRADED ou SAFE
- Anomalie non résolue ou défaillance partielle identifiée
- Fonctionnel, mais ne respectant pas les spécifications de conception opérationnelle
- La procédure de contingence n'a pas entièrement rétabli le système

**Procédure :** se reporter à la phase concernée (0–15) et à la procédure de contingence applicable. Consulter l'index des procédures de contingence pour le sous-système concerné.

**Reprise :** documenter l'état dégradé et le mode de défaillance. Mettre en œuvre des procédures de contournement dans les opérations de mission si cela ne présente pas de danger. Si le sous-système est sur le chemin critique de la mission, faire remonter au directeur de vol pour une décision de contingence : poursuivre avec une capacité réduite, ou reporter le début de la mission dans l'attente d'une réparation ou d'une analyse. S'assurer que toutes les limitations connues sont communiquées aux opérations de mission et documentées lors du briefing final de remise.

---

## Principes généraux de reprise {#general-recovery-principles}

### Quand une procédure échoue {#when-any-procedure-fails}

1. **Documenter :** consigner toute la télémesure, les commandes envoyées et la chronologie
2. **Faire remonter :** contacter immédiatement le directeur de vol ; ne pas continuer sans instructions
3. **Vérifier :** revérifier toutes les hypothèses et mesures avant toute nouvelle tentative
4. **Enchaînement :** suivre exactement la procédure ; ne pas omettre d'étapes ni en modifier l'ordre
5. **Temporisation :** laisser 10–30 minutes entre deux tentatives infructueuses, sauf instruction contraire

### Communication pendant les contingences {#communication-during-contingencies}

- Maintenir une liaison en temps réel avec le directeur de vol pendant la reprise active
- Rendre compte de la situation toutes les 5 minutes en l'absence de progrès
- Utiliser les procédures établies du réseau vocal (et non des commandes envoyées vers le bord)
- Préparer un briefing de contingence pour le passage suivant si le problème n'est pas résolu

### Étapes après la reprise {#post-recovery-steps}

- Ramener le sous-système concerné à l'état nominal une fois la procédure terminée
- Effectuer un bilan de santé de suivi (phase 4) pour confirmer la stabilité
- Documenter toutes les anomalies pour l'analyse de mission
- Faire un débriefing avec le directeur de vol avant d'engager la phase suivante

---

**Gestion du document :** Référence des procédures de contingence de la recette en orbite v1.0  
**Dernière mise à jour :** 2026-04-09  
**Approbateur :** directeur de vol  
**Documents associés :** Déroulé de la séquence de recette en orbite (09_leop.md), manuels des sous-systèmes (01–08), index des procédures
