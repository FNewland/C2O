# EMG-003 : Redémarrage de l'OBC
**Sous-système :** OBDH
**Phase :** EMERGENCY
**Révision :** 1.1 --- 2026-11-02 (décision de Franz P1) : l'étape 8 alimente la ligne du
réchauffeur OBC avant de rétablir le réchauffeur (l'ancien `HEATER_OBC(on=1)` était refusé S1.8
« EPS power line 6 is OFF ») et le rend à son thermostat.
**Approuvé par :** directeur des opérations de vol

## Objet
Redémarrage d'urgence commandé du calculateur de bord lorsque l'OBC ne répond pas,
présente un comportement dégradé (charge CPU élevée, erreurs mémoire, rejets de commandes) ou reste bloqué
dans un état anormal. Cette procédure réinitialise l'OBC sur le chargeur d'amorçage, qui
relance ensuite le logiciel de vol depuis le banc mémoire sûr désigné. Le redémarrage efface tout
l'état volatil, réinitialise les compteurs et tampons internes et réinitialise toutes les interfaces
de communication avec les sous-systèmes. C'est une action de reprise de dernier recours qui interrompt toutes les
opérations de bord ; elle exige donc l'autorisation du directeur de vol et la confirmation que
toutes les opérations non critiques ont été suspendues.

## Prérequis
- [ ] Anomalie de l'OBC confirmée par au moins deux indicateurs indépendants :
  - `obdh.cpu_load` (0x0302) > 90 % de façon prolongée, OU
  - `obdh.tc_rej_count` (0x0306) s'incrémentant sur des commandes valides, OU
  - `obdh.mem_errors` (0x031E) > 0 et en hausse, OU
  - `obdh.mode` (0x0300) ne répondant pas aux commandes de changement de mode, OU
  - télémesure de servitude périmée (aucun nouveau paquet depuis > 30 s)
- [ ] Autorisation du directeur de vol obtenue (signée dans le journal de console)
- [ ] Toutes les opérations non critiques suspendues :
  - charge utile OFF : `payload.mode` (0x0600) = 0
  - aucune séquence de télécommandes datées en attente
  - aucun chargement mémoire en cours
- [ ] Liaison TTC active : `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] SoC de la batterie > 30 % : `eps.bat_soc` (0x0101) > 30 (marge pour la séquence d'amorçage)
- [ ] Directeur de vol et opérateurs FDIR/systèmes à la console

## Déroulement

### Étape 1 --- Relevé de l'état avant redémarrage
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- demander les données de servitude OBDH (si l'OBC répond)
**Action:** Consigner tous les paramètres OBDH disponibles pour comparaison après redémarrage :
  - `obdh.mode` (0x0300) : mode actuel
  - `obdh.cpu_load` (0x0302) : taux d'occupation du CPU
  - `obdh.mmm_used` (0x0303) : occupation mémoire
  - `obdh.reboot_count` (0x030A) : compteur de redémarrages actuel
  - `obdh.sw_version` (0x030B) : version logicielle en cours d'exécution
  - `obdh.active_obc` (0x030C) : unité OBC active (A=0, B=1)
  - `obdh.sw_image` (0x0311) : image en cours d'exécution (0=chargeur d'amorçage, 1=application)
  - `obdh.last_reboot_cause` (0x0316) : cause du redémarrage précédent
  - `obdh.seu_count` (0x0319) : compteur d'événements singuliers (SEU)
  - `obdh.mem_errors` (0x031E) : nombre d'erreurs mémoire
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- demander les données de servitude EPS
**Verify:** `eps.bat_soc` (0x0101) > 30 %
**Note:** Si l'OBC ne répond plus du tout (aucune HK reçue), consigner « NO RESPONSE » ;
l'étape 2 s'applique alors directement. La commande de redémarrage peut encore être acceptée au niveau du décodeur
matériel de commandes, même si le logiciel applicatif est bloqué.
**GO/NO-GO:** État avant redémarrage relevé (ou absence de réponse confirmée). Le directeur de vol approuve le redémarrage.

### Étape 2 --- Suspendre la charge utile et délester les charges non critiques
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) --- charge utile OFF
**Verify:** `payload.mode` (0x0600) = 0 (OFF) sous 10 s (si l'OBC répond)
**TC:** `HEATER_OBC(on=0)` (Service 8, Subtype 1, func_id 41) --- réchauffeur OBC OFF
**Note:** Le réchauffeur OBC sera réactivé après le redémarrage, une fois l'état thermique évalué.
**Action:** Si l'OBC n'accepte pas les commandes, ces charges resteront dans leur état actuel
pendant le redémarrage. Le chargeur d'amorçage appliquera des valeurs par défaut sûres au redémarrage.
**GO/NO-GO:** Charges non critiques délestées (ou absence de réponse de l'OBC confirmée).

### Étape 3 --- Envoyer le redémarrage commandé
**TC:** `OBC_REBOOT` (Service 8, Subtype 1, func_id 52) --- commander un redémarrage de l'OBC
**Note:** Était `FUNC_PERFORM func_id=42`. La fonction S8 42 est `HEATER_THRUSTER` — l'étape
« redémarrer l'OBC » de la fiche d'urgence OBC REBOOT aurait basculé le réchauffeur du lit catalytique
du propulseur et laissé l'OBC en fonctionnement.
**Action:** L'OBC arrête immédiatement l'application en cours, réinitialise le processeur
et entre dans le chargeur d'amorçage. Toute la mémoire volatile est effacée. Le chargeur d'amorçage effectue
un autotest à la mise sous tension (POST), puis charge l'image applicative depuis le banc mémoire
sûr désigné.
**Note:** La télémesure cesse dès l'acceptation de la commande de redémarrage. C'est attendu.
**Verify:** Télémesure d'acceptation de la commande (Service 1, Subtype 1) reçue --- ce peut être
le dernier paquet avant que l'OBC ne se déconnecte.
**Note:** Si l'OBC est bloqué et n'acquitte pas la commande, le chien de garde matériel
(typiquement 120 s) peut déclencher un redémarrage autonome. Dans ce cas, le redémarrage
se produit sans acquittement explicite.
**GO/NO-GO:** Commande de redémarrage envoyée. Commencer la surveillance de la séquence d'amorçage.

### Étape 4 --- Attendre la séquence d'amorçage
**Action:** Attendre 60 secondes que l'OBC achève la séquence d'amorçage :
  - 0--10 s : réinitialisation du processeur, POST, autotest mémoire
  - 10--30 s : le chargeur d'amorçage charge l'image applicative depuis le banc mémoire sûr
  - 30--50 s : initialisation de l'application, activation des interfaces avec les sous-systèmes
  - 50--60 s : redémarrage du service de télémesure HK, premiers paquets produits
**Surveiller :** Le récepteur TTC, pour toute reprise de la télémesure descendante.
**Délai maximal :** Si aucune télémesure n'est reçue sous 90 s, prolonger l'attente jusqu'à 120 s.
**Critique :** Si aucune télémesure n'est reçue sous 120 s, l'OBC est peut-être bloqué dans le chargeur d'amorçage
ou n'a pas du tout réussi à démarrer. Exécuter l'action de reprise 1.

### Étape 4b --- Amorcer l'OBC sur l'image applicative
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55)
**Note:** Après le redémarrage, l'OBC démarre sur le chargeur d'amorçage (`obdh.sw_image`
(0x0311) = 0) et n'accepte que le jeu de commandes autorisé par le chargeur d'amorçage (fonctions d'amorçage et
de maintenance, plus mise sous/hors tension des lignes EPS). L'étape `OBC_BOOT_APP` ci-dessus
lance la vérification CRC de 10 s de l'image applicative. Tant qu'elle n'est pas achevée,
toute télécommande applicative figurant plus loin dans cette fiche est rejetée avec l'erreur 0x0004.
**Verify:** acceptation S1.1 + fin d'exécution S1.7 reçues sous 15 s
**Verify:** `obdh.sw_image` (0x0311) = 1 (APPLICATION) sous 15 s
**GO/NO-GO:** Image applicative en cours d'exécution, ensemble complet des services PUS disponible.

### Étape 5 --- Vérifier le signal de vie et le mode de l'OBC
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- demander les données de servitude OBDH
**Verify:** `obdh.mode` (0x0300) = 1 (SAFE) sous 10 s --- l'OBC démarre en mode SAFE après un redémarrage
**Verify:** `obdh.sw_image` (0x0311) = 1 (application) --- exécution depuis l'image applicative, et non depuis le chargeur d'amorçage
**Verify:** `obdh.reboot_count` (0x030A) = previous_count + 1 --- un seul redémarrage a eu lieu
**TC:** `GET_PARAM(param_id=0x0316)` (Service 20, Subtype 3) — `obdh.last_reboot_cause` (à la demande : aucun SID HK ne le transporte)
**Verify:** `obdh.last_reboot_cause` (0x0316) = 1 (commandé) --- le redémarrage provient de notre commande
**TC:** `GET_PARAM(param_id=0x030B)` (Service 20, Subtype 3) — `obdh.sw_version` (à la demande : aucun SID HK ne le transporte)
**Verify:** `obdh.sw_version` (0x030B) = version attendue --- logiciel correct chargé
**Verify:** `obdh.cpu_load` (0x0302) < 50 % --- CPU plus surchargé
**Verify:** `obdh.mem_errors` (0x031E) = 0 --- erreurs mémoire effacées par le redémarrage
**GO/NO-GO:** OBC vivant, en mode SAFE, exécutant la bonne application. Battement de cœur confirmé.

### Étape 6 --- Contrôler la source d'amorçage et l'OBC actif
**Verify:** `obdh.active_obc` (0x030C) --- confirmer qu'il s'agit de la même unité OBC qu'avant le redémarrage (A=0, B=1)
**Verify:** `obdh.active_bus` (0x030E) --- confirmer l'affectation du bus CAN (principal=0)
**Verify:** `obdh.bus_a_status` (0x030F) = 0 (OK) --- bus CAN A opérationnel
**Verify:** `obdh.bus_b_status` (0x0310) = 0 (OK) --- bus CAN B opérationnel
**Verify:** `obdh.obc_b_status` (0x030D) --- consigner l'état de l'OBC de secours (0=OFF, 1=STANDBY)
**Note:** Si l'OBC est passé sur l'unité de secours (active_obc modifié), un basculement autonome
a pu se produire. Cela indique une panne matérielle plus grave sur l'unité
principale. Faire remonter à l'ingénieur OBDH pour analyse.
**GO/NO-GO:** Source d'amorçage et identité de l'OBC confirmées. Aucun basculement inattendu.

### Étape 7 --- Réactiver les comptes rendus HK et vérifier la communication avec les sous-systèmes
**TC:** `HK_ENABLE(sid=1)` (Service 3, Subtype 5) --- activer le compte rendu périodique EPS
**TC:** `HK_ENABLE(sid=2)` (Service 3, Subtype 5) --- activer le compte rendu périodique AOCS
**TC:** `HK_ENABLE(sid=3)` (Service 3, Subtype 5) --- activer le compte rendu périodique TCS
**TC:** `HK_ENABLE(sid=6)` (Service 3, Subtype 5) --- activer le compte rendu périodique TTC
**Verify:** paquets HK périodiques de tous les SID activés reçus sous 30 s
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- demander les données de servitude EPS
**Verify:** `eps.bus_voltage` (0x0105) > 32.1 V --- bus d'alimentation nominal
**Verify:** `eps.bat_soc` (0x0101) > 25 % --- charge suffisante
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- demander les données de servitude AOCS
**Verify:** `aocs.mode` (0x020F) --- consigner le mode AOCS actuel (peut être revenu par défaut à COARSE_SUN ou DETUMBLE)
**Verify:** `aocs.att_error` (0x0217) --- consigner l'erreur d'attitude actuelle
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) --- demander les données de servitude TCS
**Verify:** `tcs.temp_obc` (0x0406) dans la plage [-10 °C, +50 °C] --- température de l'OBC dans les limites
**Verify:** `tcs.temp_battery` (0x0407) dans la plage [-10 °C, +45 °C]
**GO/NO-GO:** Tous les sous-systèmes répondent via le bus CAN. Télémesure nominale.

### Étape 8 --- Rétablir le mode opérationnel et consigner les résultats
**TC:** `OBC_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 50) --- faire passer l'OBC en mode NOMINAL
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) sous 5 s
**TC:** `EPS_POWER_ON(line_index=6)` (Service 8, Subtype 1, func_id 19) --- d'abord la ligne du réchauffeur OBC (sans effet si déjà sur ON)
**Verify:** `eps.pl_htr_obc` (0x0116) = 1 sous 5 s
**TC:** `HEATER_AUTO_MODE(circuit=1)` (Service 8, Subtype 1, func_id 45) --- rétablir le réchauffeur OBC : de nouveau sous thermostat (l'étape 2 l'a mis sur OFF manuellement)
**Verify:** `tcs.htr_obc` (0x040B) cohérent avec le thermostat --- 1 tant que `tcs.temp_obc` (0x0406) est sous -10 C, 0 au-dessus de -5 C
**Note:** Si l'OBC est froid et ne remonte pas, forcer le réchauffeur avec `HEATER_OBC(on=1)`
(func_id 41) et le rendre au mode AUTO une fois réchauffé.
**Action:** Consigner les résultats du redémarrage :
  - cause du redémarrage (description de l'anomalie)
  - état avant redémarrage : charge CPU, erreurs mémoire, mode, nombre de SEU
  - durée de l'amorçage (temps entre la commande de redémarrage et le premier paquet HK)
  - état après redémarrage : mode, charge CPU, erreurs mémoire, sw_version
  - état de la communication avec les sous-systèmes
  - tout comportement inattendu pendant l'amorçage
**Action:** Si l'anomalie d'origine provenait d'un défaut logiciel, programmer une analyse
logicielle et un éventuel chargement de correctif (NOM-006).
**Action:** Si l'anomalie provenait d'un événement singulier (SEU), consigner le nombre de SEU
et surveiller toute récurrence.
**GO/NO-GO:** OBC en mode NOMINAL. Reprise après redémarrage terminée.

## Actions de reprise

### Action de reprise 1 --- L'OBC ne démarre pas (aucune télémesure au bout de 120 s)
1. Vérifier que la liaison TTC est toujours active : `ttc.link_status` (0x0501) doit toujours valoir 2 (LOCKED)
   (le TTC fonctionne indépendamment de l'état d'amorçage de l'OBC).
2. Attendre une orbite supplémentaire (95 min) --- le chien de garde matériel peut déclencher une seconde
   tentative de redémarrage.
3. Toujours sans réponse : l'OBC est peut-être bloqué dans le chargeur d'amorçage ou en panne matérielle.
4. Tenter un basculement de redondance de l'OBC :
   **TC:** `OBC_SWITCH_UNIT` (Service 8, Subtype 1, func_id 53) --- basculer sur l'OBC de secours
   (était `FUNC_PERFORM func_id=43`, qui correspond à `FPA_COOLER`).
   (Cette commande est acheminée via l'unité de distribution de puissance de l'EPS, indépendante du
   logiciel applicatif de l'OBC.)
5. Attendre 90 s l'amorçage de l'OBC de secours.
6. Si l'OBC de secours répond : poursuivre avec l'unité de secours active, à partir de la vérification de l'OBC (étape 5).
7. Si aucun OBC ne répond : faire remonter à l'équipe d'urgence. Le satellite est en mode autonome
   et s'appuie sur la FDIR matérielle.

### Action de reprise 2 --- L'OBC ne démarre que sur le chargeur d'amorçage
1. Si `obdh.sw_image` (0x0311) = 0 (chargeur d'amorçage) : l'image applicative est peut-être corrompue.
2. **Note:** Il n'existe pas de commande de « sélection du banc mémoire alternatif » ; l'ancienne fiche
   envoyait `FUNC_PERFORM func_id=21`, qui correspond à `EPS_RESET_OC_FLAG`. Utiliser
   `OBC_SELECT_BUS` (func 54) pour le bus CAN et `OBC_SWITCH_UNIT` (func 53)
   pour l'OBC redondant ; une image applicative corrompue se récupère en
   la rechargeant (CTG-021).
3. **TC:** `OBC_REBOOT` (Service 8, Subtype 1, func_id 52) --- redémarrer.
4. Attendre 90 s et vérifier que `obdh.sw_image` (0x0311) = 1 (application).
5. En cas de réussite : le banc d'image principal est probablement corrompu. Programmer un rechargement du logiciel
   dans le banc défaillant via NOM-006 lorsque les conditions le permettront.
6. Si les deux bancs échouent : l'OBC restera sur le chargeur d'amorçage. Les commandes de base sont disponibles,
   mais les données de servitude et l'autonomie sont limitées. Faire remonter l'anomalie pour résolution.

## Conduite à tenir hors nominal
- Si `obdh.reboot_count` (0x030A) s'incrémente de > 1 : l'OBC a peut-être subi
  plusieurs cycles de redémarrage (boucle d'amorçage). Vérifier `obdh.last_reboot_cause` (0x0316). Si la cause
  est 2 (chien de garde), l'application plante peut-être au démarrage. Tenter le mode chargeur d'amorçage seul
  et sélectionner le banc d'image alternatif.
- Si `obdh.active_obc` (0x030C) a changé de façon inattendue : un basculement autonome de l'OBC
  s'est produit. L'OBC principal présente peut-être une panne matérielle. Consigner l'événement et poursuivre avec
  l'unité de secours. Programmer l'analyse de l'unité principale.
- Si l'AOCS est en DETUMBLE après le redémarrage : l'AOCS s'est replié par défaut en mode sûr. C'est
  le comportement attendu. Surveiller les vitesses et passer en COARSE_SUN puis NOMINAL une fois les
  vitesses < 0.1 deg/s.
- Si `eps.bat_soc` descend sous 20 % après le redémarrage : la consommation de la séquence d'amorçage a peut-être
  été excessive. Délester immédiatement toutes les charges non essentielles. Maintenir l'OBC en mode SAFE
  jusqu'à ce que le SoC remonte au-dessus de 30 %.
- Si l'anomalie périodique réapparaît après le redémarrage : la cause racine est peut-être une panne matérielle (basculement
  de bit en mémoire, dégradation du processeur) plutôt qu'un problème logiciel. Envisager de basculer sur
  l'unité OBC de secours comme solution à plus long terme.

## Postconditions
- [ ] OBC redémarré et fonctionnant en mode NOMINAL : `obdh.mode` (0x0300) = 0
- [ ] Version logicielle correcte confirmée : `obdh.sw_version` (0x030B) conforme à l'attendu
- [ ] Exécution depuis l'image applicative : `obdh.sw_image` (0x0311) = 1
- [ ] `obdh.cpu_load` (0x0302) < 50 % (anomalie résolue)
- [ ] `obdh.mem_errors` (0x031E) = 0
- [ ] Communication rétablie avec tous les sous-systèmes (EPS, AOCS, TCS, TTC et charge utile répondent)
- [ ] Comptes rendus HK périodiques réactivés pour tous les SID requis
- [ ] Réchauffeur OBC rétabli : `tcs.htr_obc` (0x040B) = 1
- [ ] `obdh.reboot_count` (0x030A) = previous_count + 1 (un seul redémarrage, pas de boucle d'amorçage)
- [ ] Rapport d'anomalie établi avec les données avant et après redémarrage
- [ ] Analyse de la cause racine lancée
- [ ] Le directeur de vol a confirmé la reprise et autorisé le retour aux opérations nominales

---
*AIG --- contenu généré par l'intelligence artificielle*
*Référence : https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/*
