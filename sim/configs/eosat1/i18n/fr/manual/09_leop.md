# Guide des opérations LEOP d'EOSAT-1 {#eosat-1-leop-operations-guide}

**Référence du document :** EOSAT1-UM-LEOP-010
**Édition :** 1.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Objet {#1-purpose}

Ce document constitue le guide d'opérations complet de la phase de lancement et de début d'orbite
(LEOP) de la mission EOSAT-1. Il couvre la séquence de séparation, le premier contact sol,
les opérations en mode chargeur d'amorçage, l'amorçage de l'application, la mise sous tension séquentielle des sous-systèmes, la recette en orbite du SCAO
et la transition vers les opérations nominales. Tous les points de contrôle GO/NO-GO y sont identifiés.

## 2. Vue d'ensemble de la LEOP {#2-leop-overview}

**Ordre définitif des fiches de procédure (refonte de l'enchaînement 2026-08c).** Les fiches de vol
LEOP s'exécutent dans cet ordre — et NON dans l'ordre de leur numéro — ; chaque fiche
déclare son état d'entrée (*Entry state*) et son état de sortie (*Exit state*) et se termine par un NEXT explicite :

1. **LEOP-001** Première acquisition du signal et amorçage de l'OBC — liaison, image applicative,
   levée du mode balise, échelon LOW, SID HK de la plateforme.
2. **LEOP-002** Bilan de santé initial — observation seule ; confirme que les
   sous-systèmes non alimentés (AOCS, charge utile, refroidisseur, propulsion) sont toujours éteints.
3. **LEOP-004** Vérification du générateur solaire — déploiement des ailes.
4. **LEOP-007** Mise sous tension séquentielle — UNIQUEMENT les charges LEOP : lignes des réchauffeurs
   selon le besoin, ligne de l'ensemble AOCS, équipements magnétomètre + magnétocoupleurs + GPS,
   puis le DETUMBLE commandé. La ligne de la charge utile relève de COM-009, le refroidisseur
   du FPA de COM-010, l'ENABLE des roues de COM-004, la ligne de propulsion de la
   préparation des manœuvres.
5. **LEOP-005** Acquisition du Soleil — OBSERVE la transition automatique DETUMBLE →
   COARSE_SUN (rien n'est commandé) ; la LEOP s'arrête en attente sur le Soleil.
6. **LEOP-006** Synchronisation temporelle — LES DEUX voies dans une même fiche : SET_TIME
   sol immédiatement, puis OBC_GPS_TIME_SYNC dès que le point GPS est acquis ;
   active le SID HK 12 (GPS_NAV).
7. **LEOP-003** Restitution d'orbite initiale — vérifie la PVT du SID 12 et,
   en tant que DERNIÈRE fiche LEOP, déclare `SYS_SET_MISSION_PHASE(phase=5)` et passe la main
   à la recette en orbite (COM-001).

La recette en orbite enchaîne ensuite COM-001 … COM-010, **COM-012 (première lumière),
COM-011 (étalonnage)**, COM-013 — COM-003 (étalonnage des gyromètres,
réalisable pendant l'attente en COARSE_SUN) étant délibérément placée AVANT COM-004 (activation
des roues), et COM-013 étant seule à déclarer la phase 6.

La LEOP commence à la séparation du satellite et du lanceur et s'achève lorsque le satellite
est déclaré opérationnel en mode nominal. La phase dure typiquement de 1 à 3 jours et franchit
les grands jalons suivants :

| Jalon                      | Temps approx.   | Description                          |
|----------------------------|-----------------|--------------------------------------|
| Séparation                 | T+0             | Largage par le lanceur, démarrage de la minuterie |
| Déploiement de l'antenne   | T+30 min        | Activation du fil thermofusible            |
| Premier contact            | T+30 min à T+6 h | Acquisition de la balise à Iqaluit ou à Troll |
| Amorçage de l'application  | Premier contact | Sortie du chargeur d'amorçage        |
| Fin de l'amortissement     | T+1 à T+12 h   | Vitesses angulaires < 0,5°/s         |
| Déploiement des ailes solaires | T+2 à T+14 h | Déploiement des ailes solaires +Y et -Y |
| Mise sous tension séquentielle | T+12 à T+24 h | Activation des sous-systèmes       |
| Recette en orbite du SCAO  | T+24 à T+72 h  | Vérification des capteurs et actionneurs |
| Transition vers le nominal | T+48 à T+72 h  | Pleine capacité opérationnelle       |

## 3. Séquence de séparation {#3-separation-sequence}

### 3.1 Machine à états de séparation {#31-separation-state-machine}

La séquence de séparation suit une machine à états à 7 phases implémentée dans l'OBC :

| Phase             | Déclencheur                | Durée      | Actions                           |
|-------------------|----------------------------|------------|-----------------------------------|
| PRE_SEPARATION    | Mise sous tension (dans le lanceur) | —   | Tous les systèmes éteints sauf le circuit de minuterie |
| SEP_DETECTED      | Ouverture du contact de séparation | Instantané | Démarrage de la minuterie ; PDM non commutable sous tension |
| POWER_STABILIZE   | PDM non commutable actif   | ~30 s      | Amorçage de l'OBC ; mise sous tension du RX |
| TIMER_WAIT        | Fin de l'amorçage de l'OBC | ~30 min    | Aucune émission RF ; OBC dans le chargeur d'amorçage |
| ANTENNA_DEPLOY    | Expiration de la minuterie de 30 min | ~60 s | Fil à chaud commandé ; déploiement de l'antenne |
| BEACON_START      | Déploiement de l'antenne confirmé | ~10 s | TX activé ; balise SID 11 sur le palier SAFE (1 kbit/s ; anciennement BEACON, renommé en 2026-08c) |
| NOMINAL           | Émission de la balise active | —        | Prêt pour le contact sol          |

### 3.2 Mise sous tension des lignes non commutables {#32-unswitchable-line-power-on}

Dès la détection de la séparation, les lignes non commutables du PDM s'activent automatiquement :

- **UNSW-1 (OBC)** : l'OBC principal (OBC-A) se met sous tension et s'amorce dans le chargeur d'amorçage.
- **UNSW-2 (RX)** : le récepteur du transpondeur se met sous tension, prêt à accepter les commandes sol
  via le canal de commande dédié du PDM.

Aucune commande sol n'est requise pour ces lignes. Elles sont câblées pour s'activer dès que
le contact de séparation s'ouvre et que le circuit de minuterie s'initialise.

### 3.3 Attente de 30 minutes sur minuterie {#33-30-minute-timer-hold}

Pendant la phase TIMER_WAIT :

- l'OBC fonctionne dans le chargeur d'amorçage mais n'émet pas ;
- le récepteur est alimenté et à l'écoute des commandes (aucune n'est attendue avant le déploiement) ;
- toutes les lignes commutables du PDM restent inhibées ;
- le satellite est en culbutage libre (aucun contrôle d'attitude dans le chargeur d'amorçage) ;
- la batterie alimente cette configuration minimale indéfiniment.

L'attente de 30 minutes répond aux exigences réglementaires qui interdisent toute émission RF
immédiatement après la séparation du lanceur.

### 3.4 Déploiement de l'antenne {#34-antenna-deployment}

À l'expiration de la minuterie de 30 minutes :

1. L'OBC commande le circuit de fil thermofusible principal.
2. Un courant traverse le fil de retenue (~2 A pendant 5 secondes).
3. Le fil fond et des charnières à ressort déploient les éléments d'antenne.
4. Le déploiement est vérifié par la surveillance de microcontacts (s'il y en a) ou par
   l'amélioration du RSSI une fois les émissions commencées.
5. Si le fil thermofusible principal ne parvient pas à déployer l'antenne, l'OBC commande le
   circuit de fil thermofusible redondant après un délai d'attente de 60 secondes.

### 3.5 Début de l'émission de la balise {#35-beacon-transmission-start}

Une fois l'antenne déployée :

1. La ligne commutable TX du PDM (SW-1) est activée.
2. L'émetteur et l'amplificateur de puissance se mettent sous tension.
3. L'OBC commence à émettre des paquets balise (**SID 11**) sur le **palier SAFE** de l'échelle des débits TM (anciennement BEACON, renommé en 2026-08c — « balise » désigne désormais toujours l'émetteur UHF à antenne fouet) — 1 kbit/s, 1 kBd, BPSK avec conv(7,1/2)+RS, ~3,1 kHz de bande occupée — en provenance de l'**APID du chargeur d'amorçage (0x002)**. C'est le SEUL paquet HK émis en mode chargeur d'amorçage — les SID 1–6 restent muets jusqu'à l'amorçage de l'application. Aucun stockage de TM, aucun contrôle d'attitude et aucune opération de charge utile ne sont possibles en mode chargeur d'amorçage. SAFE est un échelon de survie, pas un débit d'exploitation : à 1 kbit/s, il transporte le SID 11 avec une marge de plus de 100 fois, mais ne peut absolument pas transporter le flux périodique de servitude à 1557 bit/s.
4. La minuterie de coupure automatique du TX de 15 minutes démarre, mais elle est réarmée à chaque émission de balise.

Le satellite est alors prêt pour l'acquisition sol.

**Point de contrôle GO/NO-GO 1 : séquence de séparation terminée**
- Critères : émission de la balise active, antenne déployée.
- Décision : poursuivre par les opérations de premier contact.

## 4. Premier contact — acquisition RF {#4-first-contact--rf-acquisition}

### 4.1 Préparation de la station sol {#41-ground-station-preparation}

Avant la fenêtre prévue du premier contact :

1. Configurer l'antenne de la station sol pour l'acquisition en bande S à l'azimut/élévation prédits de l'AOS.
2. Régler le démodulateur sur le palier SAFE : 1 kBd, BPSK, conv(7,1/2)+RS. C'est la seule
   forme d'onde qu'émet le chargeur d'amorçage ; un démodulateur configuré pour le palier LOW (16 kBd)
   ne s'y verrouillera pas.
3. Charger le plan de fréquences d'EOSAT-1 (liaison descendante à 2200,0 MHz, liaison montante à 2025,0 MHz, bande S).
4. Préparer la séquence de commandes LEOP planifiée à l'avance.

### 4.2 Interprétation de la TM balise {#42-beacon-tm-interpretation}

Le paquet balise (SID 11) contient des informations de santé minimales mais essentielles :

| Paramètre       | Valeur attendue        | Préoccupant si                    |
|-----------------|------------------------|-----------------------------------|
| sw_image        | 0 (chargeur d'amorçage) | Toute autre valeur                |
| bat_voltage     | 30.9-33.4 V                | < 29.6 V (batterie faible)          |
| bat_soc         | > 60 %                 | < 40 % (consommation inattendue)  |
| obc_temp        | 10-40 °C               | Hors plage (problème thermique)   |
| uptime          | ~1800 s et plus (30 min et plus) | < 1800 s (réinitialisation récente) |
| reboot_count    | 0 ou 1                 | > 1 (réinitialisations multiples, à analyser) |

### 4.3 Procédure de premier contact {#43-first-contact-procedure}

1. Acquérir le signal de la balise à l'AOS. Vérifier le verrouillage de la porteuse sur le récepteur sol.
2. Décoder le paquet balise (SID 11). Consigner toutes les valeurs des paramètres.
3. Vérifier la santé du satellite d'après les paramètres de la balise (voir le tableau ci-dessus).
4. Ne pas encore envoyer `SET_TIME` : S9.1 est acceptée sous chargeur d'amorçage, mais échoue à l'exécution.
5. Relever l'écart d'horodatage de la balise ; l'horloge est réglée après `OBC_BOOT_APP` (LEOP-006).

**Point de contrôle GO/NO-GO 2 : bilan de santé au premier contact**
- Critères : balise reçue, tous les paramètres nominaux, OBC dans le chargeur d'amorçage.
- Décision : poursuivre par l'amorçage de l'application.

## 5. Opérations en mode chargeur d'amorçage {#5-bootloader-operations}

### 5.1 HK limitées dans le chargeur d'amorçage {#51-limited-hk-in-the-bootloader}

Dans le chargeur d'amorçage, **seul le SID 11 (balise)** est émis, et il provient de l'**APID dédié du chargeur d'amorçage (0x002)** — distinct de l'APID applicatif (0x001) utilisé une fois l'application de l'OBC en marche. Le sol dispose ainsi d'une signature claire et sans ambiguïté de l'état chargeur d'amorçage ou application :

- paquet balise (SID 11) toutes les 30 s sur l'APID 0x002 du chargeur d'amorçage ;
- aucun stockage de TM n'existe — les vidages commandés échouent, il n'y a aucune mémoire de paquets à activer ;
- aucune HK AOCS / TCS / charge utile et aucune télémesure au niveau des sous-systèmes ;
- aucun journal d'événements périodique : seuls sont émis les événements de gravité ≥ 2 générés par le chargeur d'amorçage lui-même.

La télémesure de servitude complète (SID 1–6 par sous-système) et les mémoires de TM de bord ne deviennent disponibles qu'après l'amorçage réussi du logiciel applicatif (phase 4). Un redémarrage de l'OBC à n'importe quelle phase ultérieure ramène automatiquement le satellite dans cet état chargeur d'amorçage/balise seule jusqu'au réamorçage de l'application.

### 5.2 Commandes restreintes dans le chargeur d'amorçage {#52-restricted-commands-in-the-bootloader}

Seules les commandes suivantes sont acceptées :

| Commande             | Usage pendant la LEOP                             |
|----------------------|---------------------------------------------------|
| OBC_BOOT_APP (S8.1 fonction 55) | Amorcer le logiciel applicatif          |
| SET_TIME (S9.1)      | Acceptée, mais échoue à l'exécution tant que l'application ne tourne pas — régler l'heure après OBC_BOOT_APP (LEOP-006) |
| HK_REQUEST (SID 11)  | Demander un paquet balise immédiat (au lieu d'attendre 30 s) |
| OBC_REBOOT, OBC_SWITCH_UNIT, OBC_SELECT_BUS, OBC_BOOT_INHIBIT, OBC_CLEAR_REBOOT_CNT, OBC_DIAGNOSTIC (fonctions 52–54, 56, 57, 61) ; S17.1 ; S20.1/S20.3 | Maintenance du chargeur d'amorçage, test de connexion, lecture/écriture de paramètres |
| EPS_POWER_ON / EPS_POWER_OFF (19/20), TTC_PA_ON / TTC_PA_OFF (66/67), TTC_DEPLOY_ANTENNA (69), SYS_SET_MISSION_PHASE (120) | Lignes d'alimentation, émetteur, antenne et phase de mission pour le premier contact |

Toutes les autres commandes sont rejetées à l'acceptation avec le code d'échec 0x0006. Ne pas tenter de commander les sous-systèmes dans le chargeur d'amorçage.

## 6. Amorçage de l'application et vérification {#6-application-boot-and-verification}

### 6.1 Procédure d'amorçage {#61-boot-procedure}

1. Vérifier que la santé indiquée par la balise est nominale (point de contrôle 2 franchi).
2. Envoyer `OBC_BOOT_APP` (S8.1 fonction 55) pour commander la transition du chargeur d'amorçage vers l'application.
3. Attendre 30 secondes que le logiciel applicatif se charge et exécute son POST.
4. Surveiller l'apparition de la télémesure de servitude complète (SID 1-6).
5. Si aucune HK n'apparaît dans les 60 secondes, l'amorçage de l'application a peut-être échoué.
   Vérifier si la balise réapparaît (signe d'un repli dans le chargeur d'amorçage).

### 6.2 Vérification après amorçage {#62-post-boot-verification}

Une fois le logiciel applicatif en marche, vérifier :

| Contrôle                       | Paramètre        | Valeur attendue             |
|--------------------------------|------------------|-----------------------------|
| Mode de l'OBC                  | obc_mode (0x0300)| 0 (NOMINAL) ou 1 (SAFE)     |
| Charge CPU                     | cpu_load (0x0302)| < 50 % (stabilisation après amorçage) |
| Génération des HK              | tm_pkt_count     | S'incrémente à 1 Hz         |
| Santé de la batterie           | bat_soc (0x0101) | > 50 %                      |
| Tension du bus                 | bus_voltage      | 30.9-33.4 V                     |
| Traitement des TC              | tc_exec_count    | S'incrémente normalement    |

### 6.3 Reprise après un amorçage échoué {#63-recovery-from-failed-boot}

Si l'application ne démarre pas :

1. Attendre que l'OBC se replie dans le chargeur d'amorçage (3 réinitialisations consécutives par chien de garde).
2. Évaluer reboot_count dans le paquet balise.
3. Suivre la CTG-021 (Reprise du chargeur d'amorçage de l'OBC) ; il n'existe pas de commande `SW_UPLOAD`.
4. Si aucun correctif n'est disponible, maintenir le satellite dans le chargeur d'amorçage en mode balise
   jusqu'à ce qu'un correctif puisse être préparé et envoyé lors des contacts suivants.

**Point de contrôle GO/NO-GO 3 : amorçage de l'application réussi**
- Critères : télémesure HK complète reçue, OBC en mode NOMINAL ou SAFE.
- Décision : poursuivre par la mise sous tension séquentielle.

## 6A. Déploiement des ailes solaires {#6a-solar-wing-deployment}

Après l'amorçage de l'application et l'amortissement initial (vitesses angulaires < 0,5°/s), les ailes
solaires déployables des faces +Y et -Y doivent être déployées pour fournir la pleine capacité
de production de puissance. Cette étape est réalisée avant la mise sous tension séquentielle afin de garantir une marge
de puissance suffisante pour l'activation des sous-systèmes.

### 6A.1 Contrôles avant déploiement {#6a1-pre-deployment-checks}

1. Vérifier que le logiciel applicatif est en marche (mode OBC = NOMINAL ou SAFE).
2. Vérifier que les vitesses angulaires sont < 0.5°/s (amortissement terminé ou suffisant).
3. Vérifier que le SoC de la batterie est > 50 % (le déploiement d'une aile demande ~2 A pendant 30 s).
4. Demander les HK EPS (`HK_REQUEST SID=1`) et confirmer que la tension du bus est nominale.

### 6A.2 Déploiement de l'aile +Y {#6a2-deploy-y-wing}

1. Envoyer `EPS_DEPLOY_WING` (func_id 81, wing=0) pour déployer l'aile solaire +Y.
2. Surveiller le décompte de `wing_deploy_timer` (0x0145) à partir de ~30 s.
3. Attendre l'événement 0x0112 (WING_PY_DEPLOYED) confirmant le déploiement.
4. Vérifier que le bit 0 de `wing_status` (0x0144) est positionné.
5. Surveiller l'augmentation du courant `sa_py_current` (0x012D) si le satellite est éclairé.
6. Attendre 60 secondes que le transitoire d'attitude s'amortisse.

### 6A.3 Déploiement de l'aile -Y {#6a3-deploy--y-wing}

1. Envoyer `EPS_DEPLOY_WING` (func_id 81, wing=1) pour déployer l'aile solaire -Y.
2. Surveiller le décompte de `wing_deploy_timer` (0x0145) à partir de ~30 s.
3. Attendre l'événement 0x0113 (WING_MY_DEPLOYED) confirmant le déploiement.
4. Vérifier que le bit 1 de `wing_status` (0x0144) est positionné.
5. Surveiller l'augmentation du courant `sa_my_current` (0x012E) si le satellite est éclairé.

### 6A.4 Vérification après déploiement {#6a4-post-deployment-verification}

1. Demander les HK EPS et vérifier que `power_gen` (0x0107) a augmenté.
2. Confirmer que `wing_status` (0x0144) = 0x03 (les deux ailes déployées).
3. Comparer la production de puissance totale à la prédiction pour la configuration déployée
   (surface totale de 0,438 m² contre 0,198 m² repliée).
4. Consigner les heures de déploiement et les relevés de puissance dans le journal LEOP.

### 6A.5 Hors nominal : échec du déploiement d'une aile {#6a5-off-nominal-wing-deployment-failure}

Si une aile ne se déploie pas (aucun événement généré dans les 60 s, bit de wing_status non positionné) :

1. Attendre 60 secondes que le fil thermofusible refroidisse.
2. Renouveler la commande de déploiement pour l'aile en échec.
3. Si la seconde tentative échoue, poursuivre la LEOP avec une seule aile déployée.
4. Évaluer la viabilité du bilan de puissance avec la surface solaire réduite.
5. Programmer une analyse détaillée pendant la recette en orbite.

**Point de contrôle GO/NO-GO 3A : déploiement des ailes solaires**
- Critères : les deux ailes déployées (wing_status = 0x03), production de puissance accrue.
- Décision : poursuivre par la mise sous tension séquentielle.

## 7. Procédure de mise sous tension séquentielle {#7-sequential-power-on-procedure}

Après l'amorçage de l'application et le déploiement des ailes solaires, les sous-systèmes sont mis sous tension un par un
pour vérifier leur santé et maîtriser le bilan de puissance. L'ordre est essentiel — chaque étape doit être
vérifiée avant de continuer.

### 7.1 Séquence de mise sous tension {#71-power-on-sequence}

| Étape | Sous-système        | Ligne PDM | Vérification                         | Impact sur la puissance |
|------|---------------------|----------|---------------------------------------|--------------|
| 1    | Réchauffeur de batterie | SW-5 | UNIQUEMENT si bat_temp < +5 °C : ligne du réchauffeur sous tension, température en stabilisation | +8 W |
| 2    | Magnétomètre        | SW-2     | aocs.mag_enabled (0x025C) = 1 ; mesures du magnétomètre nominales | +1 W |
| 3    | Magnétocoupleurs    | SW-2     | MTQ_ENABLE accepté ; aocs.mtq_enabled (0x025E) = 1 | +2 W |
| 4    | Récepteur GPS       | SW-2     | TTFF en cours (le point GPS peut demander 15-30 min) | +1 W |

Commander ensuite DETUMBLE (`AOCS_SET_MODE(mode=2)`) — la commande de mode est REFUSÉE si
le magnétomètre ou les magnétocoupleurs sont absents (0x0A20 / 0x0A21), d'où
la place des étapes 2-3 en premier.

**Délibérément NON alimentés ni activés pendant la LEOP (2026-08c) :**

| Charge | Activée par | Raison du report |
|------|-----------|--------------|
| Senseurs stellaires, gyromètres | COM-003 | inutiles pour l'attente sûre au Soleil |
| ENABLE des roues de réaction | COM-004 | la ligne SW-2 est sous tension, mais les roues restent désactivées — un interrupteur d'alimentation ne donne jamais la main à la boucle de commande |
| Ligne de la charge utile (SW-4) | COM-009 | charge de la recette en orbite, pas un besoin LEOP |
| Refroidisseur du FPA | COM-010 | ~15 W en continu ; l'allumer en LEOP a consommé de la marge pendant des jours (constat du propriétaire) |
| Ligne de propulsion | NOM-004/NOM-013 | uniquement pour la préparation des manœuvres |

### 7.2 Surveillance du bilan de puissance {#72-power-budget-monitoring}

Après chaque étape de mise sous tension, vérifier que :

- `power_cons` (0x0106) a augmenté de la quantité attendue ;
- `bat_soc` (0x0101) ne baisse pas excessivement ;
- `power_gen` (0x0107) dépasse `power_cons` pendant les portions éclairées de l'orbite.

**Point de contrôle GO/NO-GO 4 : mise sous tension séquentielle terminée**
- Critères : le jeu de charges LEOP (et lui seul) est alimenté et sain ; DETUMBLE
  actif sur magnétomètre + magnétocoupleurs ; roues toujours désactivées.
- Décision : poursuivre avec LEOP-005 (observer l'acquisition automatique du Soleil).

## 8. Séquence de recette en orbite du SCAO {#8-adcs-commissioning-sequence}

La recette en orbite du SCAO vérifie chaque composant de détermination et de contrôle d'attitude dans un
ordre précis : d'abord les capteurs, puis les algorithmes de détermination, puis les actionneurs, puis
les boucles de commande.

### 8.1 Phase 1 : recette des capteurs {#81-phase-1-sensor-commissioning}

#### Étape 1 : étalonnage du magnétomètre {#step-1-magnetometer-calibration}

1. Vérifier que le magnétomètre est alimenté et que `aocs.mag_enabled` (0x025C) = 1.
2. Enregistrer les mesures du magnétomètre sur une orbite complète.
3. Comparer le champ magnétique mesuré au modèle IGRF pour la position courante.
4. Calculer et envoyer des décalages d'étalonnage si les résidus dépassent 500 nT.
5. Vérifier que les mesures étalonnées concordent avec le modèle à 200 nT près.

#### Étape 2 : vérification des CSS {#step-2-css-verification}

1. Pendant la portion éclairée, vérifier que les 6 têtes CSS fournissent des valeurs non nulles sur
   les faces éclairées.
2. Vérifier que les faces à l'ombre fournissent des valeurs quasi nulles.
3. Contrôler que la direction calculée du vecteur Soleil est cohérente avec le modèle orbital
   (direction attendue du Soleil pour la position orbitale et la saison courantes).
4. Vérifier la cohérence géométrique : des faces opposées doivent fournir des mesures complémentaires
   (si une face voit le Soleil, la face opposée doit être dans l'ombre).

#### Étape 3 : recette de la caméra stellaire {#step-3-star-camera-commissioning}

1. S'assurer que les vitesses angulaires sont inférieures à 0.1°/s (l'amortissement doit être suffisant).
2. Mettre sous tension la caméra stellaire zénith (ST-Zenith sur la face +Z).
3. Attendre que la caméra stellaire effectue son acquisition « lost-in-space » (jusqu'à 60 secondes).
4. Vérifier la validité du quaternion d'attitude fourni (les quatre composantes non nulles).
5. Comparer l'attitude de la caméra stellaire au vecteur Soleil (issu des CSS) pour un contrôle de cohérence.
6. Vérifier que la caméra stellaire n'est pas éblouie (angle du Soleil par rapport à l'axe de visée +Z > 15°).

#### Étape 4 : étalonnage du biais des gyromètres {#step-4-gyro-bias-calibration}

1. La caméra stellaire fournissant une attitude valide, activer l'algorithme d'estimation du biais des gyromètres.
2. Accumuler des données d'étalonnage pendant au moins 10 minutes.
3. Vérifier que les estimations du biais des gyromètres convergent (les valeurs de biais se stabilisent).
4. Accepter l'étalonnage et l'enregistrer dans la mémoire non volatile de l'OBC.
5. Vérifier que les mesures de vitesse étalonnées concordent avec les vitesses déduites de la caméra stellaire à
   0.01°/s près.

**Point de contrôle GO/NO-GO 5 : recette des capteurs terminée**
- Critères : tous les capteurs étalonnés et fournissant des données valides.
- Décision : poursuivre par la validation de la détermination d'attitude.

### 8.2 Phase 2 : validation de la détermination d'attitude {#82-phase-2-attitude-determination-validation}

1. Vérifier que la solution d'attitude fusionnée (caméra stellaire, magnétomètre, gyromètres) est stable.
2. Confirmer que `att_error` (0x0217) est calculé et vraisemblable.
3. Vérifier la continuité du quaternion d'attitude (aucun saut entre les mises à jour).
4. Recouper la position déduite du GPS avec l'orbite attendue pour en vérifier la cohérence.
5. Enregistrer la solution d'attitude sur au moins une orbite complète pour analyse au sol.

**Point de contrôle GO/NO-GO 6 : détermination d'attitude validée**
- Critères : solution d'attitude stable, cohérente d'un capteur à l'autre.
- Décision : poursuivre par la recette des actionneurs.

### 8.3 Phase 3 : recette des actionneurs {#83-phase-3-actuator-commissioning}

#### Étape 5 : contrôle du signe des magnétocoupleurs {#step-5-magnetorquer-sign-check}

1. Commander un courant connu dans chaque bobine de magnétocoupleur (X, Y, Z), une à une.
2. Observer le couple résultant sur le satellite à l'aide des mesures de vitesse des gyromètres.
3. Vérifier que le sens du couple est cohérent avec l'interaction attendue entre
   le moment dipolaire commandé et le champ magnétique mesuré.
4. Confirmer l'absence d'erreur de signe (un sens erroné indiquerait un problème de câblage).
5. En cas d'erreur de signe, mettre à jour dans le logiciel la configuration de polarité des magnétocoupleurs.

#### Étape 6 : essai de mise en rotation des roues de réaction {#step-6-reaction-wheel-spin-up-test}

1. Commander chaque roue, une à une, à faible vitesse (+100 tr/min).
2. Vérifier que la télémesure de vitesse de roue correspond à la valeur commandée.
3. Vérifier que le satellite subit un léger contre-couple dans le sens attendu.
4. Faire tourner chaque roue à -100 tr/min et vérifier l'inversion correcte du sens de rotation.
5. Ramener toutes les roues à 0 tr/min.
6. Vérifier que les températures des roues restent nominales tout au long de l'essai.

#### Étape 7 : vérification des gains de commande {#step-7-control-gain-verification}

1. Activer la loi de commande AOCS avec des gains prudents (faibles).
2. Commander un petit décalage d'attitude (1°) et observer la réponse.
3. Vérifier que le satellite réagit dans le bon sens et à une vitesse raisonnable.
4. Rechercher un dépassement ou une oscillation — ajuster les gains si nécessaire.
5. Revenir à un décalage nul et vérifier la convergence.

**Point de contrôle GO/NO-GO 7 : recette des actionneurs terminée**
- Critères : tous les actionneurs vérifiés, sens et amplitude corrects.
- Décision : poursuivre par les essais de contrôle actif.

### 8.4 Phase 4 : validation du contrôle actif {#84-phase-4-active-control-validation}

#### Étape 8 : essai d'amortissement des vitesses {#step-8-rate-damping-test}

1. Commander l'AOCS en mode DETUMBLE (s'il n'y est pas déjà).
2. Si les vitesses sont déjà quasi nulles, introduire une petite perturbation au moyen des magnétocoupleurs.
3. Vérifier que l'amortissement des vitesses par les magnétocoupleurs converge sous 0.5°/s.
4. Vérifier la transition autonome vers COARSE_SUN (mode 3) lorsque les vitesses sont suffisamment faibles.

#### Étape 9 : vérification du pointage solaire {#step-9-sun-pointing-verification}

1. En mode COARSE_SUN, vérifier que le satellite oriente sa face +X vers le Soleil.
2. Surveiller la convergence de `att_error` vers zéro.
3. Vérifier la cohérence entre le vecteur Soleil déduit des CSS et l'attitude de la caméra stellaire.
4. Surveiller la production de puissance — confirmer que `power_gen` augmente à mesure que le pointage solaire s'améliore.

#### Étape 10 : essai de pointage nadir {#step-10-nadir-pointing-test}

1. Commander l'AOCS en mode NOMINAL (nadir) via `AOCS_SET_MODE` (mode=4).
2. Vérifier la transition de l'attitude vers le pointage nadir.
3. Surveiller `att_error` — il doit converger sous 0.1° en 5 minutes.
4. Vérifier que les vitesses des roues de réaction restent dans la plage nominale.
5. Surveiller pendant au moins une orbite complète pour vérifier la stabilité lors des transitions d'éclipse.

**Point de contrôle GO/NO-GO 8 : recette en orbite du SCAO terminée**
- Critères : pointage nadir stable, tous les composants du SCAO vérifiés.
- Décision : poursuivre par la transition vers le nominal.

## 9. Transition vers les opérations nominales {#9-transition-to-nominal-operations}

### 9.1 Liste de vérification avant transition {#91-pre-transition-checklist}

Avant de déclarer le satellite opérationnel, vérifier les points suivants :

| Point | Contrôle                                 | État requis               |
|------|------------------------------------------|---------------------------|
| 1    | Mode de l'OBC                            | NOMINAL (mode=0)          |
| 2    | Mode de l'AOCS                           | NOMINAL (mode=4)          |
| 3    | Erreur d'attitude                        | < 0.5° (durablement)   |
| 4    | SoC de la batterie                       | > 60 %                    |
| 5    | Marge de puissance                       | power_gen > power_cons    |
| 6    | Tous les capteurs opérationnels          | Mesures valides de tous   |
| 7    | Tous les actionneurs opérationnels       | Répondent aux commandes   |
| 8    | Liaison TTC                              | Stable aux deux stations  |
| 9    | Point GPS                                | Valide et cohérent        |
| 10   | Environnement thermique                  | Toutes les zones dans les limites |
| 11   | Surveillance S12 activée                 | Toutes les règles FDIR actives |
| 12   | Événements-actions S19 activés           | Toutes les réponses automatiques actives |

### 9.2 Séquence de commandes de transition vers le nominal {#92-nominal-transition-command-sequence}

1. Vérifier la liste de vérification avant transition (tous les points conformes).
2. Le directeur de vol lance le tour de table GO/NO-GO de tous les postes.
3. Tous les postes annoncent GO.
4. Activer toutes les définitions de surveillance S12 (si ce n'est déjà fait).
5. Activer toutes les définitions d'événement-action S19.
6. Commander la télémesure de servitude à pleine cadence (1 Hz, tous les SID).
7. Confirmer que l'échelle des débits TM est sur **LOW (16 kbit/s)** — le `default_tier`, débit
   auquel se déroulent les opérations de routine. `ttc.tm_data_rate` (0x0506) = 16000 et `ttc.tm_tier`
   (0x0539) = 1. Ne PAS laisser le satellite commandé en HIGH : ce palier est relevé pour chaque
   vidage (NOM-011 / NOM-003), puis relâché.
8. **Déclarer la phase de mission.** `SYS_SET_MISSION_PHASE(phase=6, flags=0)`
   (Service 8, Subtype 1, func_id 120). Vérifier que `eps.spacecraft_phase` (0x0129) = 6
   et confirmer la présence de l'événement `MISSION_PHASE_CHANGED` (0x0055) dans le journal.
9. Consigner l'heure de la transition dans le journal de mission.

**À propos de la déclaration de phase.** Il s'agit d'une véritable télécommande, et non d'une écriture administrative. La
machine à états des phases de bord n'avance d'elle-même
que jusqu'à LEOP (4) ; COMMISSIONING (5) et NOMINAL (6) sont des déclarations du sol.
Tant que la phase 6 n'est pas déclarée :

* `sat.mode` (0x0001) et l'en-tête de la console restent sur **SAFE**, quel que soit
  l'état de santé du satellite — la condition de phase prime sur les verrouillages FDIR dans
  la dérivation de `sc_mode` ;
* le modèle avancé de propagation de défaillance est **désarmé**, de même que les deux
  règles FDIR historiques conditionnées par la phase (`aocs.wheels_enabled`, `aocs.att_error`) ;
* le verrouillage de la propulsion refuse l'armement — `prop.yaml` déclare
  `min_phase: 6`, si bien qu'**aucune manœuvre n'est possible** (NOM-004 / NOM-013
  échoueront à PROP_ARM).

La phase 5 est déclarée plus tôt, à l'étape 7 de LEOP-003 — la dernière fiche de la séquence
LEOP (la déclaration a été retirée de LEOP-007 lors de la refonte 2026-08c, afin
qu'une seule fiche soit responsable de chaque déclaration). Un retour en arrière (NOMINAL →
COMMISSIONING ou → LEOP) est refusé sauf si l'indicateur FORCE est positionné (bit 0 de `flags`
= 1) ; ne l'utiliser que pour annuler une déclaration prématurée, et en consigner la raison.
Les phases 0–2 sont des états antérieurs à la séparation et ne sont jamais commandables depuis le sol. L'inventaire complet
des conditions figure dans `00_mission_overview.md` §6.0.

**Point de contrôle GO/NO-GO 9 : transition vers les opérations nominales**
- Critères : tous les points de la liste de vérification conformes, tous les postes annoncent GO.
- Décision : satellite déclaré opérationnel ; phase LEOP terminée ; phase = 6.

### 9.3 Activités après la LEOP {#93-post-leop-activities}

Une fois la phase LEOP terminée, les activités de recette suivantes se poursuivent pendant
la phase de recette en orbite :

| Activité                           | Calendrier      | Responsabilité |
|------------------------------------|-----------------|----------------|
| Recette en orbite de la charge utile | Jours 3–7     | Opérateur PLD  |
| Premier essai de prise de vue      | Jours 7–10      | PLD + FD       |
| Convergence de la restitution d'orbite | Jours 3–5   | Opérateur AOCS |
| Corrélation du modèle thermique    | Jours 3–14      | Opérateur PT   |
| Affinage des seuils FDIR           | Jours 7–21      | Tous les postes |
| Optimisation des contacts avec les stations sol | Jours 3–10 | Opérateur TTC |
| Premières prises de vue scientifiques | Jours 14–30  | PLD + FD       |

## 10. Procédures d'urgence pendant la LEOP {#10-emergency-procedures-during-leop}

### 10.1 Pas de balise après la séparation {#101-no-beacon-after-separation}

Si aucune balise n'est reçue au premier contact prévu :

1. Attendre la fenêtre de contact suivante à la station de secours.
2. Toujours sans signal, envoyer en aveugle un `HK_REQUEST` (SID 11) vers la position
   prédite du satellite.
3. Rechercher toute énergie RF sur la fréquence de liaison descendante attendue.
4. Sans réponse après 24 heures de tentatives, envisager une possible défaillance du déploiement
   de l'antenne et commander en aveugle le circuit de fil thermofusible redondant.

### 10.2 OBC bloqué dans le chargeur d'amorçage {#102-obc-stuck-in-the-bootloader}

Si l'OBC ne parvient pas à passer du chargeur d'amorçage à l'application :

1. Demander un paquet balise via `HK_REQUEST` (SID 11).
2. Contrôler `reboot_count` — s'il est élevé, l'application plante peut-être.
3. Renouveler `OBC_BOOT_APP` (S8.1 fonction 55).
4. En cas d'échecs répétés, maintenir l'OBC en chargeur d'amorçage (`OBC_BOOT_INHIBIT`) et analyser.
5. Se reporter à la CTG-021 (`procedures/contingency/obc_bootloader_recovery.md`) pour la procédure de reprise détaillée.

### 10.3 Vitesses de culbutage excessives {#103-excessive-tumble-rates}

Si les vitesses angulaires dépassent 5°/s après une tentative d'amortissement :

1. Vérifier que les mesures du magnétomètre sont valides (ni figées, ni bruitées).
2. Le magnétomètre n'est pas redondé — il n'existe pas de MAG-B sur lequel basculer. Avec une unité
   défaillante, la loi B-dot est aveugle ; s'attendre à dépendre de l'amortissement passif, et faire remonter à l'équipe de soutien du constructeur du satellite.
3. Si les vitesses continuent d'augmenter, rechercher un magnétocoupleur bloqué (appliquant un couple dans le mauvais
   sens).
4. En dernier recours, couper tous les actionneurs SCAO et laisser agir l'amortissement magnétique passif
   (il faut des heures, voire des jours).

---

*Ce document a été produit avec l'aide de l'IA. Source : https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/*

---

*Fin du document — EOSAT1-UM-LEOP-010*
