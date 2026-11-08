# Partie 5 — Cahier d'exercices de la semaine 3 d'OrbitNorth

Cette partie du cahier d'exercices est le bloc-notes de l'opérateur pour la formation de cinq jours
aux opérations satellite de la **semaine 3 d'OrbitNorth**. Elle se déroule
du lundi 17 août au vendredi 21 août 2026 au Cyber Range de l'Université
d'Ottawa.

Sa structure reprend la partie 2 du manuel. Pour chaque procédure nominale
et de contingence exécutée pendant la semaine, il existe une
fiche **à confirmer étape par étape** : vous cochez chaque étape une fois
vérifiée, vous inscrivez la valeur de télémesure réelle dans la colonne *note*,
et vous signalez tout élément hors nominal. Les fiches d'anomalie, les modèles de
passation, les fiches d'observation et les pages de débriefing de fin de quart
sont intercalés entre les fiches de chaque journée.

**Comment utiliser ces fiches.**

- Apportez la fiche imprimée à la console au début de
  chaque quart.
- Écrivez au stylo pour que les corrections restent visibles (barrez, ne
  gommez pas).
- Remplissez chaque case, même si la réponse est « nominal » ou
  « s.o. — non exécuté ».
- Remettez la fiche remplie à l'enseignant en fin de quart.
  Le registre de retour d'expérience de la promotion s'en nourrit.

Les identifiants des fiches suivent le modèle `WB-5.X-NAME`, ce qui permet de
les rapprocher sans ambiguïté des chapitres du manuel.

---

# Fiche WB-5.0 — Vérification des acquis préalables

**Usage :** à remplir *avant* d'arriver au Cyber Range le lundi
matin. Elle vous amène au même niveau de départ que le reste de la
promotion.

**Nom :** _________________________________   **Date :** ______________

### Section A — Données de la mission

Renseignez chaque valeur. Source : manuel, §5.0.7.

| Élément | Votre réponse |
|------|-------------|
| Plateforme d'EOSAT-1 (type de plateforme, unités) | |
| Altitude de l'orbite (km) | |
| Inclinaison de l'orbite (°) | |
| Heure locale du nœud ascendant (LTAN) | |
| Bande de la mission | |
| Nombre de bandes de l'imageur et longueurs d'onde centrales (nm) | |
| Stations sol — les cinq (nom et latitude) | |
| Capacité de la batterie (Wh) | |
| Technologie de la batterie et configuration des éléments | |
| Fauchée de l'instrument (km) et GSD (m) | |
| Exigence de pointage en NOMINAL, mode 4 (°) | |
| Exigence de pointage en FINE_POINT, mode 5 (°) | |
| Propulsion : type et Δv total (m/s) | |

### Section B — Postes de la salle de contrôle

Pour chaque poste, rédigez sa mission en une phrase, avec vos propres mots.

| Poste | Mission (une phrase) |
|----------|------------------------|
| Directeur de vol | |
| SPACON / FDIR et systèmes | |
| Ingénieur SCAO | |
| Ingénieur EPS | |
| Ingénieur thermique | |
| Ingénieur TT&C | |
| Opérations charge utile | |
| FDS / analyste orbite | |
| Ingénieur segment sol | |
| Responsable de mission | |

### Section C — Réflexion avant la semaine

Quelle partie du travail d'opérations attendez-vous le plus ?

_____________________________________________________________

_____________________________________________________________

Quelle partie vous inquiète le plus ?

_____________________________________________________________

_____________________________________________________________

---

# Fiche WB-5.1 — Cartes de score par poste (tour de rôle)

**Usage :** lundi après-midi, 13 h 00 – 15 h 00 : un briefing de 15 minutes, puis
sept ateliers de 15 minutes, un par console MCS configurée
(`configs/eosat1/mcs/positions.yaml`). Une carte par console. À la
fin du créneau de 15 minutes de chaque atelier, inscrivez une observation d'une phrase
sous « Enseignement » et une question d'une phrase sous
« Question à poser ». Le responsable de mission et le segment sol sont des rôles
de salle, et non des consoles ; les vérifications du segment sol figurent sur la carte TT&C.

**Nom :** _________________________________

## 5.1.1 Directeur de vol

- **Tâche :** conduire un tour de table GO/NO-GO depuis l'onglet **GO/NO-GO** du MCS (tiroir
  du bas). Interroger trois postes pour un *go for* `CONNECTION_TEST` (S17.1) — ce satellite
  n'a ni commande NOOP ni commande de battement de cœur ; consigner les réponses.
- **Postes interrogés :** _____________ , _____________ , _____________
- **Réponses consignées (mot pour mot) :**
  - _____________________________________________
  - _____________________________________________
  - _____________________________________________
- **Temps passé au poste de FD :** ____ : ____  à  ____ : ____
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

## 5.1.2 Puissance et thermique

- **Tâche :** prédire le SoC de la batterie à la sortie de la prochaine éclipse, puis
  identifier le réchauffeur dont le rapport cyclique est actuellement le plus élevé et
  prédire s'il saturera à la prochaine éclipse. Lire les heures et la durée de l'éclipse
  sur la page EPS, **Prévisions → Prochaine éclipse** ; les rapports cycliques des
  réchauffeurs sur la page TCS, **Équipements → DUTY BAT / DUTY OBC**.
- **SoC à l'entrée en éclipse :** ____ %   **Durée de la prochaine éclipse :** ____ min
- **SoC prédit en sortie :** ____ %
- **Méthode :** SoC_sortie = SoC_entrée − P × t / E_batt, avec E_batt = 100 Wh, t la durée de l'éclipse et P la consommation lue sur la page EPS (environ 22,7 W, charge utile en STANDBY)
- **Comparaison avec la prédiction de la console (flux de puissance EPS, « en sortie d'éclipse ») :** ☐ concorde  ☐ écart de ____ %
- **Réchauffeur au rapport cyclique le plus élevé :** _______________   **Rapport cyclique :** ____ %
- **Rapport cyclique prédit à la prochaine éclipse :** ____ %   **Saturera-t-il :** ☐ oui ☐ non
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

## 5.1.3 Dynamique du vol

- **Tâche :** lire `aocs.att_error` (0x0217) et vérifier qu'elle respecte
  le bilan du mode NOMINAL (mode 4, suivi du nadir), soit < 1.0°. En
  FINE_POINT (mode 5), le bilan est < 0.1°. Lire ensuite l'AOS, le TCA
  et le LOS du prochain passage d'Iqaluit dans la liste des passages des
  outils d'orbite et les comparer avec le tableau **Prochains contacts** du planificateur.
- **Lecture :** ______ °   **Dans la plage :** ☐ oui  ☐ non
- **Mode SCAO (`aocs.mode` 0x020F) :** ____ (0 OFF, 1 SAFE_BOOT,
  2 DETUMBLE, 3 COARSE_SUN, 4 NOMINAL, 5 FINE_POINT, 6 SLEW,
  7 DESAT, 8 ECLIPSE, 9 INERTIAL)
- **État des senseurs stellaires** — 0=éteint, 1=amorçage, 2=poursuite, 3=aveuglé, 4=en panne :
- **ST1 (`aocs.st1_status` 0x0240) :** ____   **ST2 (`aocs.st2_status` 0x0243) :** ____   **Sélectionné (`aocs.st_selected` 0x0244) :** ____
- **Prochain passage d'Iqaluit :** AOS ______ TCA ______ LOS ______ él. max ____ °
- **Concordance avec le planificateur :** ☐ exacte  ☐ écart < 5 s  ☐ écart > 5 s
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

## 5.1.4 TT&C

- **Tâche :** parcourir l'échelle de débits TM à l'AOS et confirmer quelle station
  sol assure le passage. L'échelle comporte trois
  échelons — **SAFE 1 kbit/s / LOW 16 kbit/s / HIGH 128 kbit/s**
  (`ttc.tm_data_rate` 0x0506 en bit/s, `ttc.tm_tier` 0x0539 =
  0/1/2). LOW est l'échelon des opérations de routine ; HIGH est réservé aux vidages
  et exige l'antenne déployée et le mode DOWNLINK activé (func 79) ;
  la règle des 10° d'élévation est une politique d'autorisation sol, pas un verrou bord.
  SAFE (appelé BEACON jusqu'en 2026-08c) ne peut pas être sélectionné avec
  `TTC_SET_DATA_RATE` (S8 func 65).
  EOSAT-1 utilise le référentiel pédagogique à **cinq stations** (`orbit.yaml`).
- **Débit SAFE (kbit/s) :** ______   **Débit LOW de routine (kbit/s) :** ______
  **Débit HIGH de vidage (kbit/s) :** ______
- **Marge de liaison après la transition (dB) :** ______ (`ttc.link_margin` 0x0503)
- **Lecture du TEB (`ttc.ber` 0x050C, log10) :** ____________________
- **Station en contact (page TT&C, Réseau de stations sol) :** ☐ Iqaluit ☐ Troll ☐ Svalbard ☐ Inuvik ☐ O'Higgins
- **Configuration de la bande de base (débit, débit symbole, codage — vue Radio, Liaison de données et Bilan de liaison) :** ______________________
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

## 5.1.5 Opérations charge utile

- **Tâche :** programmer une séance de prise de vue dans le planificateur
  (**Opportunités de prise de vue → Planifier**). Confirmer que la température
  du FPA est à la consigne avant d'envoyer la commande.
- **Cible de prise de vue choisie :** _______________________________
- **Lecture de la température du FPA (`payload.fpa_temp` 0x0601, °C) :** ______
- **À la consigne (`payload.fpa_ready` 0x0610 = 1) :** ☐ oui ☐ non — la condition est l'indicateur de disponibilité, et non une température retenue de mémoire. Consigne par défaut −15 °C (`payload.fpa_setpoint` 0x0631 ; enveloppe commandable de −20 °C à 0 °C).
- **Occupation du stockage (`payload.mem_used_mb` 0x060B) :** ______ / 20 000 Mo
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

## 5.1.6 FDIR / systèmes

- **Tâche :** présenter une surveillance de bord dans le tableau **Surveillance bord (S12)**
  de la page FDIR ; expliquer son déclencheur, son seuil, sa persistance, sa gravité
  et la procédure de contingence à laquelle elle renvoie.
- **Surveillance choisie (colonne Nom) :** _____________________________
- **Paramètre déclencheur :** _____________________________
- **Seuil :** ___________________   **Persistance :** _________
- **Gravité :** ____   **Procédure recommandée :** ________________
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

## 5.1.7 Propulsion

- **Tâche :** sans envoyer aucune commande, lire l'état de la propulsion et
  nommer le verrouillage qui empêche actuellement l'armement (page PRP,
  **Verrouillages d'armement**). Contexte : manuel 07 *Opérations orbitales*, §6.
- **État (`prop.state` 0x0B00 ; 0 SAFED, 1 ARMED, 2 FIRING, 3 INHIBIT) :** ____
- **Pression du réservoir (`prop.tank_pressure` 0x0B01, bar) :** ______
  **Ergol (`prop.propellant_mass` 0x0B02, g) :** ______ / 400
- **Masque des verrouillages d'armement (`prop.arm_inhibit_mask` 0x0B15) :** ______
  **Bits levés** (b0 lit catalytique, b1 pression réservoir, b2 ergol, b3 mode SCAO,
  b4 erreur d'attitude, b5 SoC, b6 phase, b7 éclipse, b8 vannes, b9 inhibition
  verrouillée, b10 aucune poussée chargée) : ______________________
- **Verrouillage qui bloque l'armement, en clair :** ______________________
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

---

# Fiche WB-5.3-PP — Jour 1 : exercice d'équipe de plan de passage

**Équipe :** ☐ Borealis  ☐ Austral   **Responsable :** _______________

| Champ | Saisie |
|-------|-------|
| Passage visé (station + heure d'AOS) | |
| Heure du TCA | |
| Heure du LOS | |
| Durée du passage (min) | |
| Procédures à exécuter (ID, dans l'ordre) | |
| ID de la cible de prise de vue | |
| Fenêtre de prise de vue dans le passage | |
| Bandes sélectionnées et temps d'intégration | |
| Fauchée au sol prévue (km) | |
| Débit de liaison descendante prévu (kbit/s) | |
| Durée prévue de la transmission (s) | |
| **Panne plausible 1** | |
| Procédure de reprise pour la panne 1 | |
| **Panne plausible 2** | |
| Procédure de reprise pour la panne 2 | |

### Notes de la lecture à voix haute

Ce que l'autre équipe a contesté : ________________________________

___________________________________________________________________

Ce que nous avons accepté : _________________________________________________

Ce que nous avons défendu : _________________________________________________

---

# Fiche WB-5.4-VL — Jour 2 : exercice d'entraînement aux annonces de boucle vocale

**Usage :** mardi, 09 h 00 – 10 h 00. Exercice en binôme. L'un joue le FD,
l'autre le sous-système désigné. Consignez ce qui a été dit.

| N° | Situation | Votre annonce (mot pour mot) | Réussi/Échoué |
|---|----------|------------------------|-----------|
| 1 | Le FD demande à l'AOCS un compte rendu de pointage | | ☐ ☐ |
| 2 | L'AOCS annonce un pointage de 0.28°, nominal | | ☐ ☐ |
| 3 | Le FD demande à l'EPS la prédiction d'entrée en éclipse | | ☐ ☐ |
| 4 | L'EPS annonce une entrée en éclipse à T+04:12, SoC en sortie 78 % | | ☐ ☐ |
| 5 | Le FD interroge 3 postes pour un GO de mise sous tension de la charge utile | | ☐ ☐ |
| 6 | L'EPS répond : « no-go, payload line 3 already drawing 0.35 A with the line commanded OFF » | | ☐ ☐ |
| 7 | Le FD annonce un HOLD sur la mise sous tension de la charge utile | | ☐ ☐ |
| 8 | Le TT&C annonce une anomalie : TEB monté à 1e-3 | | ☐ ☐ |
| 9 | Le FD demande un repli de débit | | ☐ ☐ |
| 10 | Le TT&C annonce que le palier est descendu de HIGH→LOW, débit 16 kbit/s, TEB 1e-7 nominal | | ☐ ☐ |

**Autoévaluation (sur 10) :** ______

**Une annonce que je veux travailler davantage :** ____________________

---

# Fiche WB-5.4-N001 — NOM-001 Ouverture de passage (confirmer chaque étape)

**Usage :** répétition à blanc du mardi après-midi, puis chaque passage nominal.

**Opérateur :** ___________________   **Passage :** ___________________

| N° | Responsable | Action | Vérification attendue | ☐ fait | Note / valeur réelle |
|---|-------|--------|----------------------|:------:|---------------------|
| 1 | SPACON | Vérifier l'état de l'OBC : `HK_REQUEST(sid=4)` (S3.27) | `obdh.mode` (0x0300) = 0 (NOMINAL) et `obdh.cpu_load` (0x0302) < 80 % en 10 s ; `obdh.uptime` (0x0308) cohérent avec la dernière valeur connue. `obdh.mode` ≠ 0 : interrompre le passage, exécuter CTG-010 | ☐ | |
| 2 | EPS | Vérifier la santé de l'EPS : `HK_REQUEST(sid=1)` | `eps.bat_soc` (0x0101) > 50 % ; `eps.bus_voltage` (0x0105) > 30.9 V ; `eps.power_gen` (0x0107) > `eps.power_cons` (0x0106). Une des deux limites non tenue : CTG-005, aucune opération de charge utile | ☐ | |
| 3 | AOCS | Vérifier le pointage AOCS : `HK_REQUEST(sid=2)` | `aocs.mode` (0x020F) dans {4, 8} (NOMINAL, ou ECLIPSE côté ombre) ; `aocs.att_error` (0x0217) < 1.0° (prévoir 400 s de reconvergence après une perturbation) ; `aocs.rate_roll` (0x0204) et `aocs.rate_yaw` (0x0206) à ±0.05°/s ; `aocs.rate_pitch` (0x0205) dans [0.043, 0.083]°/s — le suivi du nadir porte la vitesse orbitale, +0.063°/s | ☐ | |
| 4 | TT&C | Établir la liaison : `TTC_SWITCH_PRIMARY` (S8.1) | `ttc.link_status` (0x0501) = **2** (LOCKED) en 15 s ; page TT&C (sol) : `ttc.rssi` (0x0502) > −126 dBm, `ttc.link_margin` (0x0503) > 3.0 dB. Pas de liaison en 15 s : `TTC_SWITCH_REDUNDANT` et vérifier de nouveau ; échec des deux → anomalie TT&C | ☐ | |
| 5 | SPACON | Collecte complète des données de servitude : `HK_REQUEST` (S3.27) des SID 1 EPS, 2 AOCS, 3 TCS, 4 OBDH, 5 charge utile, 6 TT&C | les six paquets en 30 s ; aucun paramètre hors limites signalé par le contrôle de limites du MCS | ☐ | |
| 6 | Charge utile | Préparation de la charge utile, seulement si une prise de vue ou un vidage est prévu : `PAYLOAD_SET_MODE(mode=1)` STANDBY (S8.1 func 26) | `payload.mode` (0x0600) = 1 en 20 s ; `tcs.cooler_fpa` (0x040C) = 0 (le mode STANDBY ne fait pas fonctionner le refroidisseur ; il est mis en marche lors de la préparation de la prise de vue, étape 2 de NOM-002) ; `payload.store_used` (0x0604) < 90 % | ☐ | non prévu ☐ |
| 7 | FD | Déclaration de disponibilité pour le passage : tour de table GO / NO-GO | EPS : SoC > 50 %, bus > 30.9 V, marge positive · AOCS : NOMINAL, erreur < 1°, vitesses de roulis et de lacet < 0.05°/s, tangage à la vitesse orbitale · TT&C : liaison établie, RSSI > −126 dBm, marge > 3 dB · TCS : chaque zone dans les limites de la page TCS · OBDH : NOMINAL, CPU < 80 % · Charge utile : STANDBY si nécessaire, mémoire < 90 %. Tout NO-GO : d'abord sa procédure hors nominal | ☐ | |

Les lectures à la demande se font par `HK_REQUEST` (S3.27) ; l'émission
périodique s'active par `HK_ENABLE` (S3.5). Seuls les SID 1 (EPS) et 11
(balise) sont actifs à l'amorçage ; les autres sont activés par les fiches qui
alimentent leur sous-système.

Pas de liaison à l'étape 4 alors que le sol est nominal : la chaîne bande S
n'émet que si `ttc.tx_active` (0x0525) = 1, et `ttc.tx_gate_status` (0x052B)
indique l'autorisation manquante — c'est CTG-019, pas cette fiche.

**Éléments hors nominal observés :** __________________________________

___________________________________________________________________

**Signature du FD :** ________________   **Heure de fin :** _________

---

# Fiche WB-5.4-C003 — CTG-003 Rétablissement après perte de liaison TTC (confirmer chaque étape)

**Opérateur :** ___________________   **Heure de déclenchement :** _________

La perte de liaison est confirmée quand `ttc.link_status` = 0 plus de 30 s
après l'AOS prévue, ou quand une liaison établie tombe en cours de passage.
Toute commande après l'étape 1 est envoyée **en aveugle** : aucune télémesure
n'est attendue avant le retour de la liaison.

| N° | Responsable | Action | Vérification attendue | ☐ fait | Note / valeur réelle |
|---|-------|--------|----------------------|:------:|---------------------|
| 1 | Segment sol | Confirmer que la perte de liaison n'est pas un problème sol : poursuite de l'antenne, puissance de l'émetteur montant, verrouillage du récepteur, précompensation Doppler, brouillage local ou météo | défaut sol → le résoudre sur place ; sol confirmé nominal → reprise côté satellite | ☐ | |
| 2 | TT&C | Réacquérir sur le transpondeur principal : `HK_REQUEST(sid=6)` (S3.27) en aveugle, attendre 30 s | `ttc.link_status` (0x0501) = **2** (LOCKED) en 30 s ; page TT&C (sol) : `ttc.rssi` (0x0502) > −126 dBm. Liaison revenue → étape 5 ; aucune réponse → étape 3 | ☐ | |
| 3 | TT&C | Basculer sur le transpondeur redondant : `TTC_SWITCH_REDUNDANT` (S8.1 func 64) en aveugle, attendre 45 s | `ttc.link_status` = 2 en 45 s ; `ttc.mode` (0x0500) indique l'équipement redondant. Liaison revenue → étape 5 ; rien → étape 4 | ☐ | |
| 4 | TT&C | Deuxième tentative sur le principal : `TTC_SWITCH_PRIMARY` (S8.1 func 63) en aveugle, attendre 45 s | `ttc.link_status` = 2 en 45 s. Liaison revenue → étape 5 ; toujours rien après les deux équipements → étape 6 | ☐ | |
| 5 | TT&C | Vérifier la qualité de la liaison et la santé des sous-systèmes : `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` | `ttc.link_status` = 2 ; page TT&C (sol) : `ttc.rssi` > −126 dBm, `ttc.link_margin` (0x0503) > 3.0 dB ; équipement actif `ttc.mode` (0x0500) consigné ; `eps.bus_voltage` (0x0105) > 30.9 V ; `obdh.mode` (0x0300) ni SAFE ni EMERGENCY. Marge > 3 dB et tout nominal → rétabli | ☐ | équipement : ____ |
| 6 | TT&C | Escalade, pas de liaison : consigner chaque commande en aveugle avec son heure ; prévenir le directeur de mission et la dynamique du vol ; réserver le passage suivant ; noter l'heure de la dernière télécommande **acceptée** (dernier S1.1) | premiers passages prévus après T+24 h et T+48 h : la minuterie de perte de commande `ttc.time_since_last_tc` (0x053D, FDIR TTC-01) bascule sur l'AUTRE transpondeur 24 h après la dernière TC acceptée (événement CMD_LOSS_TIMEOUT 0x0514), puis toutes les 24 h suivantes. Sans liaison après deux passages consécutifs → **EMG-004** | ☐ | dernier S1.1 : ____ |

Les commandes en aveugle qui ne sont pas reçues ne relancent pas la minuterie
de perte de commande. Au retour de la liaison, envoyer aussitôt une
télécommande, sinon la minuterie quitte l'équipement qui fonctionne 24 h plus
tard. Avec les deux transpondeurs en panne, la liaison est réellement coupée —
aucune télécommande n'est reçue et rien n'est émis, balise comprise — et rien
depuis le sol ne peut la rétablir : passer à EMG-004 et rester à l'écoute.

**Étape à laquelle la liaison a été rétablie (le cas échéant) :** ______

**Numéro de la fiche d'anomalie :** ______

**Signature du FD :** ________________   **Heure de fin :** _________

---

# Fiche WB-5.4-N012 — NOM-012 Modèle de passation de consignes

**Usage :** à chaque changement de quart. Le FD sortant lit chaque ligne ; le FD
entrant collationne les points 3 et 7. Objectif : moins de 6 minutes.

**FD sortant :** _____________   **FD entrant :** _____________
**Fin du quart :** _______________   **Début de la passation :** _________

| N° | Point | Ce que dit le FD sortant | Collationné par le FD entrant ? |
|---|------|------------------|:----------------------:|
| 1 | Phase et heure | | |
| 2 | Dernier passage terminé | | |
| 3 | **Anomalies ouvertes** (nom de la règle, état, étape de la procédure de reprise) | | ☐ |
| 4 | Travaux en cours (procédures en cours d'exécution) | | |
| 5 | Prochain passage (station, AOS, procédures prévues, opérateur désigné) | | |
| 6 | Engagements client en cours (prises de vue et vidages réservés dans le planificateur) | | |
| 7 | **Autorisations GO en suspens** | | ☐ |
| 8 | Ambiance sur la boucle vocale (équipe reposée / tendue / etc.) | | |

**Fin de la passation :** _________   **Durée :** ____ : ____ (objectif < 6:00)

**Les deux FD signent ci-dessous pour attester que la passation est terminée.**

Sortant : ____________________  Entrant : ____________________

---

# Fiche WB-5.4-FD — Jour 2 : atelier de dynamique du vol

**Opérateur :** ___________________

### Exercice 1 — Prédire les trois prochaines heures d'AOS

Outil : les outils d'orbite (**Utiliser les éléments d'EOSAT-1**, puis **Convertir le TLE**) :
lire la liste des passages (AOS, TCA, LOS) et la chronologie des contacts sur 24 h. Comparer
avec le tableau **Prochains contacts** du planificateur.

| Passage | Station | AOS (votre prédiction, UTC) | AOS (planificateur, UTC) | Δ (s) |
|------|---------|---------------------------|----------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

### Exercice 2 — Durée du passage en fonction de l'élévation maximale

| Passage | Él. max (°) | Durée prédite (min) | Durée dans le planificateur (min) |
|------|------------|---------------------------|-------------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

Formule utilisée (à écrire ici) : _____________________________________

### Exercice 3 — Calculs d'éclipse

- **Éclipse la plus longue dans les 24 h à venir :** ____________ UTC, durée ____ min
- **SoC prédit en sortie** (avec $SoC_{exit} = SoC_{entry} - P_{avg} \cdot t / E_{battery}$) :
  ____ %
- **SoC réel en sortie :** ____ %   **Δ :** ____ %
- **Préoccupation ?** ☐ non  ☐ oui — note : _____________________________

---

# Fiche WB-5.4-Q — Jour 2 : feuille de réponses du quiz de formation aux opérations

**Nom :** ___________________   **Heure de début :** _____________

Seuil de réussite : 11 sur 15. Corrigés au verso du dossier de l'enseignant.

### Discipline de boucle vocale (3 questions)

1. ____________________________________________________________
2. ____________________________________________________________
3. ____________________________________________________________

### Navigation dans l'interface du MCS (3 questions)

4. ____________________________________________________________
5. ____________________________________________________________
6. ____________________________________________________________

### Interprétation de la télémesure — limites et SID (3 questions)

7. ____________________________________________________________
8. ____________________________________________________________
9. ____________________________________________________________

### Structure des procédures (2 questions)

10. ____________________________________________________________
11. ____________________________________________________________

### Traitement des anomalies (2 questions)

12. ____________________________________________________________
13. ____________________________________________________________

### Calculs d'horaires de passage (2 questions)

14. ____________________________________________________________
15. ____________________________________________________________

**Note obtenue après correction :** ____ / 15   **Réussi ?** ☐ oui ☐ non

---

# Fiche WB-5.5-PB — Jour 3 : liste de vérification du briefing avant passage LEOP

**Équipe :** ☐ Borealis ☐ Austral   **Passage :** ☐ Passage 1 ☐ Passage 2

| Point | ☐ |
|------|:--:|
| Affectations des postes confirmées et affichées | ☐ |
| Vérification des communications effectuée (tous les postes audibles) | ☐ |
| BP-2 (`first_contact.yaml`) chargé ; satellite en phase 3 (BOOTLOADER) | ☐ |
| Un vrai passage d'Iqaluit est programmé pour le premier contact (le forçage de passage est une commande de l'enseignant ; aucun opérateur ne force le contact) | ☐ |
| Le FD a chargé le jeu de procédures LEOP dans le panneau de procédures | ☐ |
| SPACON a passé en revue le jeu de règles FDIR dans le panneau FDIR (il n'existe **aucune** télécommande de chargement de table FDIR — le jeu de règles est `subsystems/fdir.yaml` + `monitoring/`) | ☐ |
| L'AOCS a passé en revue les vitesses de culbutage résiduelles (environ 1–2 °/s par axe dues à l'impulsion de séparation) | ☐ |
| L'EPS confirme un SoC d'environ 90 % (`eps.bat_soc` 0x0101) ; seules les lignes non commutables `obc` (ligne 0) et `ttc_rx` (ligne 1) sont sur ON — toutes les lignes commutables sont sur OFF par défaut | ☐ |
| Le TT&C a confirmé la réception de la balise UHF : le SID 11 de la balise arrive (page PUS, S3 HK, colonne Observé) ; noter que la balise est une radio distincte de la chaîne principale bande S | ☐ |
| Le segment sol a confirmé que l'antenne d'Iqaluit est sur la cible, démodulateur sur l'échelon **SAFE** (1 000 bit/s, BPSK, conv(7,1/2)+RS, 1 kBd) | ☐ |
| La FDS a produit le planning des passages sur 24 h et l'a remis au FD, au TT&C et au segment sol | ☐ |
| Formulaires de fiche d'anomalie imprimés vierges et disponibles à chaque console | ☐ |
| Langue de la boucle vocale déclarée (annonces en anglais) | ☐ |

**Annonce « prêt » du FD (mot pour mot) :** ________________________________

**Début du passage (UTC) :** _____________

---

# Fiche WB-5.5-L001 — LEOP-001 Première acquisition du signal et amorçage de l'OBC (confirmer chaque étape)

**Opérateur (responsable TT&C) :** ___________________   **Début du passage :** ________

État d'entrée : démarrage à froid — OBC dans le chargeur d'amorçage, seules les
lignes `obc` et `ttc_rx` alimentées, horloge non réglée. Le passage est un
passage **programmé** : le forçage de passage est une commande de
l'enseignant, et aucune fiche ne demande à un opérateur de forcer le contact.

| N° | Responsable | Action | Vérification attendue | ☐ fait | Note réelle |
|---|-------|--------|----------------------|:------:|-------------|
| 1 | Segment sol | Configurer le récepteur d'Iqaluit pour le passage programmé : pointage sur l'AOS prévue, poursuite automatique, acquisition large (±40 kHz), démodulateur sur le palier **SAFE** (1 kBd BPSK, conv(7,1/2)+RS) | station TRACKING_READY à l'AOS prévue ; fenêtre de passage ouverte | ☐ | |
| 2 | TT&C | Première TC montante, envoyée en aveugle dans la fenêtre : `CONNECTION_TEST` (S17.1) | acceptation S1.1 < 10 s ; rapport S17.2 < 10 s ; SID 11 de la balise reçu < 30 s — le maintien automatique de l'émetteur a alimenté la ligne `ttc_tx` | ☐ | |
| 3 | TT&C | Vérifier le verrouillage de la porteuse et la qualité de la liaison | trames de balise décodées en continu < 30 s ; page TT&C (sol) : `ttc.rssi` (0x0502) > −126 dBm, `ttc.link_margin` (0x0503) > 3.0 dB. `ttc.link_status` est dans le SID 6, que le chargeur d'amorçage n'émet pas : il est vérifié à l'étape 5a | ☐ | Doppler : ____ |
| 4 | SPACON | Confirmer le chargeur d'amorçage : `HK_REQUEST(sid=11)` (S3.27) | paquet de balise reçu ; `obdh.sw_image` (0x0311) = 0 (BOOTLOADER) < 10 s | ☐ | |
| 5 | SPACON | Amorcer l'applicatif : `OBC_BOOT_APP` (S8.1 func 55) ; après son S1.7, `HK_ENABLE(sid=3)`, `HK_ENABLE(sid=4)`, `HK_ENABLE(sid=6)` (**S3.5**) | S1.1 + S1.3 < 5 s ; S1.7 < 15 s (événement 0x0310 BOOT_COMPLETE ; un échec de CRC donne un S1.8 et 0x0305 BOOT_FAILURE) ; `obdh.sw_image` = 1 < 15 s ; `obdh.boot_state` (0x0A15) = 2 ; seuls les SID 1 et 11 sont émis après l'amorçage, puis les SID 3 (60 s), 4 (8 s) et 6 (8 s) apparaissent | ☐ | |
| 5a | TT&C | Lever le mode balise, puis sélectionner LOW : `TTC_SET_BEACON_MODE(on=0)` (S8.1 func 70), `TTC_SET_DATA_RATE(rate=0)` (func 65). Reconfigurer d'abord le démodulateur sol à 16 kBd | S1.1 + S1.7, et non S1.8, < 5 s chacune ; `ttc.beacon_mode` (0x0521) = 0 ; `ttc.link_status` (0x0501) = **2** (LOCKED) < 15 s ; `ttc.tm_data_rate` (0x0506) = 16000 bit/s, `ttc.tm_tier` (0x0539) = 1, `ttc.tm_symbol_rate` (0x053B) = 16000 Bd | ☐ | |
| 6 | SPACON | Noter que l'horloge n'est pas réglée — **ne pas synchroniser ici** : le temps relève de LEOP-006 | `obdh.time_ref` (0x0A13) = 0 (NONE) ; les horodatages indiquent l'an 2000 en CUC — comportement correct, pas un défaut | ☐ | |
| 7 | SPACON | Contrôle de cohérence de l'alimentation : `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) de 29.6 à 34.6 V ; `eps.bat_soc` (0x0101) > 50 % ; `eps.pl_ttc_tx` (0x0112) = 1 (maintien automatique de l'émetteur) ; `eps.power_gen` (0x0107) remontée, faible pendant le culbutage | ☐ | |
| 8 | TT&C | Consigner et rendre compte : AOS, première TC acceptée, amorçage applicatif, valeurs HK ; confirmer que le passage suffit pour LEOP-002 ou réserver le suivant | rapport de première acquisition diffusé ; feu vert pour LEOP-002 | ☐ | |

**Valeurs consignées :**
- Heure d'AOS (UTC) : ____________
- Première TC acceptée : ____________
- Amorçage applicatif terminé : ____________
- `obdh.time_ref` (attendu : 0) : ____
- `eps.bus_voltage` : ____ V    `eps.bat_soc` : ____ %

**Erreurs fréquentes à éviter (récapitulatif de l'enseignant) :**
- Envoyer, avant que l'applicatif ait amorcé, une télécommande absente de la
  liste d'autorisation du chargeur d'amorçage (code d'échec S1.8 **0x0006**,
  « Not permitted in bootloader »). Pendant la fenêtre de CRC, l'OBC est
  encore le chargeur d'amorçage : attendre le S1.7 de `OBC_BOOT_APP`.
- Synchroniser l'horloge dans cette fiche. `SET_TIME` relève de LEOP-006.
- Laisser expirer en cours de procédure le maintien automatique de l'émetteur
  (`auto_tx_hold_s` dans `simulation.yaml`, réarmé par chaque TC acceptée).
- Tenter `TTC_SET_DATA_RATE` avant d'avoir levé le mode balise — refusée avec
  0x0007 ; l'amorçage applicatif ne le lève **pas**.
- S'attendre aux SID 2 et 5 après l'étape 5 (le SID 2 est activé dans LEOP-007
  et le SID 5 dans COM-009, une fois leurs lignes alimentées), ou à tout SID
  autre que 1 et 11 sans `HK_ENABLE` (S3.5) explicite.

**Critère de sortie atteint ?** ☐ oui ☐ non   **Signature du FD :** _______________

---

# Fiche WB-5.5-L006 — LEOP-006 Synchronisation temporelle (confirmer chaque étape)

**Opérateur (SPACON) :** ___________________

| N° | Action | Vérification attendue | ☐ fait | Note |
|---|--------|----------------------|:------:|------|
| 1 | Vérifier l'état de l'OBC et la liaison : `HK_REQUEST(sid=4)`, `HK_REQUEST(sid=6)` (S3.27) | `obdh.mode` (0x0300) ≤ 1 (NOMINAL ou SAFE) ; `obdh.cpu_load` (0x0302) < 80 % ; page TT&C (sol) : `ttc.link_margin` (0x0503) > 3.0 dB | ☐ | |
| 2 | Lire l'horloge, sa référence et la distance oblique : `REQUEST_TIME` (**S9.2**), `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=4)` | TM(9,2) < 10 s. T_obc = `obdh.obc_time` (0x0309) + `obdh.obc_time_fine` (0x0A12) / 65536, en secondes CUC depuis J2000 ; `obdh.time_ref` (0x0A13), attendu 0 (NONE) ; `obdh.time_since_sync_s` (0x0A14), attendu 4294967295 (jamais synchronisée) ; T_sol ; OWLT = distance oblique / c, lu sur la page PUS, S9 TIME (temps de propagation aller, d'après la prédiction d'orbite du sol), attendu **3–22 ms** | ☐ | OWLT : ____ ms |
| 3 | Calculer l'écart de temps : Δt = T_obc − (T_sol − OWLT) | un Δt négatif d'environ l'âge de la mission est la signature attendue en LEOP ; le FD approuve la correction | ☐ | Δt : ____ s |
| 4 | Envoyer la mise à l'heure : `SET_TIME(cuc_seconds=T_corrected)` (**S9.1**), avec T_corrected = T_sol à l'envoi + OWLT + environ 50 ms, sur l'époque J2000 — un temps Unix est trop grand d'environ 9.5e8 s, et l'argument se place *à l'intérieur* des backticks : un `SET_TIME` nu envoie cuc_seconds = 0 | S1.1 < 5 s ; aucun rejet S1.2 | ☐ | T_corrected : ____ |
| 5 | Vérifier l'exactitude du temps : `REQUEST_TIME` (S9.2), `HK_REQUEST(sid=4)` | `obdh.time_ref` = 1 (GROUND) < 15 s ; `obdh.mode` = 0 < 10 s ; résidu = T_obc_nouveau − (T_sol − OWLT) à ±1.0 s (seuil LEOP ; NOM-008 le resserre) | ☐ | résidu : ____ s |
| 6 | Valider la dérive de l'horloge : un deuxième rapport de temps (S9.2) et un échantillon du SID 4 après un intervalle sol connu | rapport < 10 s ; dérive = ((T_obc2 − T_obc1) − (T_sol2 − T_sol1)) / intervalle × 1e6 < 100 ppm | ☐ | ____ ppm |
| 6a | Voie B, asservissement temporel GPS, dès que le récepteur a un point : `HK_ENABLE(sid=12)` (S3.5), puis `OBC_GPS_TIME_SYNC` (S8.1 func **80**) — réglage sol d'abord, GPS ensuite | SID 12 périodique en 8 s ; `aocs.gps_fix` (0x0274) ≥ 2 (TTFF jusqu'à 15 min après LEOP-007 ; pas encore de point → synchroniser au contact suivant) ; S1.1 + S1.7 < 5 s ; `obdh.time_ref` = 2 (GPS) < 15 s, 3 (HOLDOVER) acceptable ; `obdh.time_since_sync_s` faible | ☐ | |
| 7 | Confirmer l'horodatage et consigner : `HK_REQUEST(sid=4)` | `obdh.uptime` (0x0308) > 0 (pas de redémarrage) ; `obdh.time_ref` dans {1, 2, 3} ; les paquets HK portent des horodatages à la date de la mission. Consigner Δt, le saut de l'événement 0x030C, le résidu et la dérive | ☐ | |

**Critère de sortie atteint ?** ☐ oui ☐ non

---

# Fiche WB-5.5-L002 — LEOP-002 Bilan de santé initial (confirmer chaque étape)

**Opérateur (SPACON consolide) :**  ___________________

| N° | Responsable | Action | Vérification attendue | ☐ fait | Note |
|---|-------|--------|----------------------|:------:|------|
| 1 | EPS | Données de servitude EPS complètes : `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) de 29.6 à 34.6 V ; `eps.bat_voltage` (0x0100) remontée ; `eps.bat_soc` (0x0101) > 50 % ; `eps.power_gen` (0x0107) > 0 W au Soleil — 0 W est attendu avec `eps.eclipse_flag` (0x0108) = 1 : contrôler de nouveau après la sortie d'éclipse | ☐ | ☐ OK ☐ NOT-OK |
| 2 | EPS | Confirmer que les sous-systèmes non alimentés sont éteints (même rapport SID 1) | `eps.pl_aocs_wheels` (0x0117) = 0 (jusqu'à LEOP-007) ; `eps.pl_payload` (0x0113) = 0 (jusqu'à COM-009) ; `eps.pl_fpa_cooler` (0x0114) = 0 (jusqu'à COM-010) ; `eps.pl_prop` (0x014A) = 0 | ☐ | ☐ éteint ☐ alimenté trop tôt |
| 3 | Thermique | Données de servitude thermiques : `HK_REQUEST(sid=3)` | `tcs.temp_obc` (0x0406) dans les limites OBC de la page TCS ; `tcs.temp_battery` (0x0407) de 0 à +35 °C ; `tcs.temp_fpa` (0x0408) remontée (charge utile non alimentée : ambiante) | ☐ | ☐ OK ☐ NOT-OK |
| 4 | SPACON | Données de servitude OBDH : `HK_REQUEST(sid=4)` | `obdh.mode` (0x0300) = 0 (NOMINAL) ou 1 (SAFE) ; `obdh.cpu_load` (0x0302) < 70 % | ☐ | ☐ OK ☐ NOT-OK |
| 5 | TT&C | Données de servitude TT&C : `HK_REQUEST(sid=6)` | `ttc.link_status` (0x0501) = **2** (LOCKED) ; page TT&C (sol) : `ttc.rssi` (0x0502) > −126 dBm, `ttc.link_margin` (0x0503) > 3.0 dB | ☐ | ☐ OK ☐ NOT-OK |
| 6 | SPACON | Établir la synthèse du bilan de santé pour le FD ; signaler toute valeur hors de sa plage post-séparation | tous les sous-systèmes alimentés nominaux → feu vert pour LEOP-004 | ☐ | |

**Bilan consolidé PASS / FAIL :** ☐ PASS ☐ FAIL

**En cas de FAIL, procédure de contingence déclenchée :** _________________

**Critère de sortie atteint ?** ☐ oui ☐ non

---

# Fiche WB-5.5-L007 — LEOP-007 Mise sous tension séquentielle (confirmer chaque étape)

**Opérateur (responsable SPACON) :**  ___________________

LEOP-007 n'alimente que ce dont le reste de la LEOP a besoin — les réchauffeurs
si leurs zones ont besoin de chaleur, la ligne de la suite AOCS, le
magnétomètre, les magnétocoupleurs et le récepteur GPS — et commande
DETUMBLE. Les étapes 1–6 tiennent dans un contact de 8 minutes. Chaque
nouvelle ligne est un événement de commande distinct, avec GO du FD. La
charge utile, le refroidisseur, les roues, les senseurs stellaires et les
gyroscopes restent éteints : leurs fiches de recette les mettent en service.

**Correspondance des indices de ligne d'alimentation** (`EPS_POWER_ON` / `EPS_POWER_OFF` /
`EPS_RESET_OC_FLAG` prennent toutes `line_index`, plage **0–8**) :
0 `obc`, 1 `ttc_rx` (toutes deux non commutables), 2 `ttc_tx`, 3 `payload`,
4 `fpa_cooler`, 5 `htr_bat`, 6 `htr_obc`, 7 `aocs_wheels`, 8 `prop`.
Toute ligne commutable est **OFF** par défaut. Il n'existe pas de ligne d'alimentation IMU —
les trois gyroscopes sont les équipements S2 `S2_AOCS_GYROSCOPE_0/1/2`.

| N° | Responsable | Action | Vérification | ☐ fait | Note |
|---|-------|--------|--------------|:------:|------|
| 1 | EPS | Vérifier l'état de référence de l'EPS : `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) de 29.6 à 34.6 V ; `eps.bat_soc` (0x0101) > 60 % ; `eps.power_gen` (0x0107) > 20 W | ☐ | |
| 2 | EPS | Lignes de réchauffeurs **seulement si nécessaire** : lire `tcs.temp_battery` (0x0407) et `tcs.temp_obc` (0x0406) dans le SID 3 ; `EPS_POWER_ON(line_index=5)` (S8.1 func **19**) seulement si la batterie est sous +5 °C ; `EPS_POWER_ON(line_index=6)` seulement si la zone OBC est sous −10 °C (seuil de mise en marche de son réchauffeur) | `eps.pl_htr_bat` (0x0115) / `eps.pl_htr_obc` (0x0116) = 1 en 5 s pour chaque ligne commandée ; les autres toujours éteintes. Consigner les lignes alimentées par cette fiche : COM-002 s'en sert comme état d'entrée | ☐ | lignes alimentées : ____ |
| 3 | EPS / AOCS | Alimenter la ligne de la suite AOCS et activer sa HK : `EPS_POWER_ON(line_index=7)` (func 19), puis `HK_ENABLE(sid=2)` (**S3.5**) | `eps.pl_aocs_wheels` (0x0117) = 1 en 5 s ; SID 2 périodique en un intervalle de 4 s ; les roues restent désactivées jusqu'à COM-004 | ☐ | |
| 4 | AOCS | Les deux éléments de DETUMBLE d'abord, et le récepteur GPS : `S2_AOCS_MAGNETOMETER(device_id=521, state=1)`, `MTQ_ENABLE(enable=1)` (S8.1 func_id **9**), `S2_AOCS_GPS_RECEIVER(device_id=527, state=1)` | `aocs.mtq_enabled` (0x025E) = 1 en 10 s | ☐ | |
| 5 | AOCS | Commander DETUMBLE : `AOCS_SET_MODE(mode=2)` (S8.1 func_id **0**) — mode **2 = DETUMBLE** | S1.1 + S1.7 < 5 s ; `aocs.mode` (0x020F) = 2 ; `aocs.mag_enabled` (0x025C) = 1 ; `aocs.mag_field_total` (0x0277) de 5000 à 70000 nT ; `aocs.rate_roll`, `aocs.rate_pitch`, `aocs.rate_yaw` (0x0204–0x0206) en baisse en 60 s | ☐ | |
| 6 | EPS | Confirmer l'état d'alimentation de sortie : `HK_REQUEST(sid=1)`, `GET_PARAM(param_id=0x0260)` (S20.3) | `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_prop` (0x014A) = 0 ; `aocs.wheels_enabled` (0x0260) = 0 ; marge positive — `eps.power_gen` (0x0107) au-dessus de `eps.power_cons` (0x0106), ou SoC stable ou en hausse | ☐ | |

La commande DETUMBLE est refusée s'il manque un élément (0x0A20 pas de
magnétomètre, 0x0A21 pas de magnétocoupleurs, 0x0004 ligne coupée) : c'est
pourquoi l'étape 4 passe en premier.

**État en fin de passage :**
- Phase (0x0129) : ____ (attendu : 4 LEOP)   Mode SCAO (0x020F) : ____ (attendu : 2 DETUMBLE)
- Vitesses angulaires roulis/tangage/lacet (°/s) : __/__/__ (en baisse)
- Roues activées (`aocs.wheels_enabled` 0x0260) : ____ (attendu : 0)
- SoC : ____ %   `tcs.temp_battery` : ____ °C
- SID périodiques : 1 ☐ 2 ☐ 3 ☐ 4 ☐ 6 ☐ 11 ☐

**Critère de sortie atteint ?** ☐ oui ☐ non   **Signature du FD :** _______________

---

# Fiche WB-5.5-L005 — LEOP-005 Acquisition du Soleil (observer, confirmer chaque étape)

**Opérateur (AOCS) :**  ___________________

Cette fiche ne commande **aucun** changement de mode : le passage de
DETUMBLE à COARSE_SUN est automatique.

| N° | Action | Vérification | ☐ fait | Note |
|---|--------|--------------|:------:|------|
| 1 | Consigner les vitesses angulaires initiales : `HK_REQUEST(sid=2)` (S3.27) | `aocs.mode` (0x020F) = 2 (DETUMBLE) ; `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) consignées — 0.5 à 5.0°/s par axe est typique | ☐ | __/__/__ °/s |
| 2 | Surveiller l'amortissement — ne rien commander : `HK_REQUEST(sid=2)` de nouveau à T+5 min | les trois vitesses en baisse (la loi B-dot les divise environ par deux toutes les 10–15 min) ; `aocs.mag_field_total` (0x0277) non nul — nul signifie que le magnétomètre a décroché et que la loi B-dot est aveugle | ☐ | |
| 3 | Observer la transition **automatique** vers COARSE_SUN : vitesses sous 0.5°/s pendant 30 s → l'AOCS bascule de lui-même. N'envoyer aucune commande de mode | `aocs.mode` (0x020F) = 3 (COARSE_SUN) dans les 1800 s après le passage des vitesses sous 0.5°/s ; événement « AOCS mode change » DETUMBLE → COARSE_SUN dans le journal des événements | ☐ | heure : ____ |
| 4 | Vérifier le maintien au Soleil : `HK_REQUEST(sid=2)` toutes les 60 s pendant 5 min, `GET_PARAM(param_id=0x0215)` (S20.3) | `aocs.att_error` (0x0217) < 15° en 600 s ; `aocs.css_sun_confidence` (0x0215) > 0.5 ; `aocs.rate_roll`, `aocs.rate_pitch`, `aocs.rate_yaw` < 0.5°/s | ☐ | erreur : ____ ° |
| 5 | Vérifier la production électrique pendant le maintien : `HK_REQUEST(sid=1)` | `eps.power_gen` (0x0107) > 40 W au Soleil — avec `eps.eclipse_flag` (0x0108) = 1, attendre la sortie d'éclipse (jusqu'à 35 min) et contrôler de nouveau ; `eps.bat_soc` (0x0101) stable ou en hausse | ☐ | ____ W |
| 6 | Consigner l'état final de l'AOCS : vitesses, erreur d'attitude, confiance CSS, puissance. Le satellite **reste** en COARSE_SUN : sans senseur stellaire alimenté (COM-003), la promotion automatique ne peut pas se déclencher — c'est l'état de stationnement voulu en LEOP | rapport d'acquisition du Soleil diffusé | ☐ | |

La convergence de la loi B-dot est **lente** : le seuil de 0.5°/s demande
typiquement environ 1 200 s, et un culbutage de séparation complet de 14°/s
environ 3.5e3 s.

**Critère de sortie atteint ?** ☐ oui ☐ non

---

# Fiche WB-5.5-L003 — LEOP-003 Restitution d'orbite initiale et fin de la LEOP (confirmer chaque étape)

**Opérateur (FDS, avec le FD pour l'étape 7) :**  ___________________

| N° | Action | Vérification | ☐ fait | Note |
|---|--------|--------------|:------:|------|
| 1 | Vérifier la solution de navigation GPS : `HK_REQUEST(sid=12)` (S3.27) | `aocs.gps_fix` (0x0274) ≥ 2 (3D) ; `aocs.gps_num_sats` (0x0276) ≥ 4 ; `aocs.gps_pdop` (0x0275) consigné | ☐ | PDOP : ____ |
| 2 | Lire le point de position : `GET_PARAM(param_id=0x0210)`, `GET_PARAM(param_id=0x0211)`, `GET_PARAM(param_id=0x0212)` (S20.3) | `aocs.gps_lat` (0x0210) dans [−90, +90]° ; `aocs.gps_lon` (0x0211) dans [−180, +180]° ; `aocs.gps_alt` (0x0212) dans la bande de contrôle de 495–540 km | ☐ | alt. : ____ km |
| 3 | Lire le vecteur d'état ECEF : `GET_PARAM(param_id=0x0231)` … `GET_PARAM(param_id=0x0236)` | norme de la position de 6700 à 6950 km ; norme de la vitesse de 7400 à 7900 m/s ; vecteur et son heure GPS consignés pour la dynamique du vol | ☐ | |
| 4 | Comparaison par la dynamique du vol avec l'orbite prédite par le lanceur — **rien n'est envoyé au satellite** | i à 0.2° près de 97.39° ; e < 0.01 ; LTAN à 15 min près de l'exigence de mission ; période conforme au mouvement moyen du TLE | ☐ | i : ____ ° |
| 5 | Contrôle de cohérence d'un second point, 10 min plus tard : `HK_REQUEST(sid=12)` | `aocs.gps_alt` (0x0212) à 20 km près de l'étape 2 ; `aocs.gps_fix` (0x0274) toujours ≥ 2 ; la position a avancé le long de la trace comme prévu par la propagation | ☐ | |
| 6 | Diffuser le rapport de restitution d'orbite et le TLE affiné au réseau sol (planificateur, FDS, stations) | prédictions de passage rafraîchies | ☐ | |
| 7 | FD : tour de table GO/NO-GO de toutes les positions, puis **déclarer COMMISSIONING par télécommande** : `SYS_SET_MISSION_PHASE(phase=5, flags=0)` (S8.1 func **120**) — la seule fiche qui l'envoie ; rien à bord ne fait avancer la phase au-delà de 4 | `eps.spacecraft_phase` (0x0129) = 5 en 5 s ; événement MISSION_PHASE_CHANGED (0x0055) 4 (LEOP) → 5 (COMMISSIONING) | ☐ | |

**Critère de sortie atteint ?** ☐ oui ☐ non   **Signature du FD :** _______________

---

# Fiche WB-5.5-AT — Jour 3 : fiche d'anomalie (3 exemplaires)

Imprimez-en trois. Utilisez-en une par anomalie observée (injections prévues ou
non). Chaque fiche est signée par le FD.

### Fiche — exemplaire 1

| Champ | Saisie |
|-------|-------|
| ID de la fiche (attribué automatiquement) | |
| Passage / quart | |
| Date / heure UTC du premier indice | |
| Paramètre déclencheur et valeur | |
| Règle FDIR déclenchée (le cas échéant) | |
| Gravité (0–4) | |
| Premier opérateur à l'annoncer (poste) | |
| Heure de la première action | |
| Procédure déclenchée (ID) | |
| Actions de reprise menées (mot pour mot depuis la boucle) | |
| Résultat (rétabli / en sécurité / reporté) | |
| Hypothèse de cause première | |
| Points ouverts pour le quart suivant | |
| Signature du FD | |

### Fiche — exemplaire 2

| Champ | Saisie |
|-------|-------|
| ID de la fiche | |
| Passage / quart | |
| Date / heure UTC | |
| Paramètre et valeur | |
| Règle FDIR | |
| Gravité | |
| Premier opérateur | |
| Heure de la première action | |
| Procédure déclenchée | |
| Actions menées | |
| Résultat | |
| Hypothèse de cause première | |
| Points ouverts | |
| Signature du FD | |

### Fiche — exemplaire 3

| Champ | Saisie |
|-------|-------|
| ID de la fiche | |
| Passage / quart | |
| Date / heure UTC | |
| Paramètre et valeur | |
| Règle FDIR | |
| Gravité | |
| Premier opérateur | |
| Heure de la première action | |
| Procédure déclenchée | |
| Actions menées | |
| Résultat | |
| Hypothèse de cause première | |
| Points ouverts | |
| Signature du FD | |

---

# Fiche WB-5.5-GO — Jour 3 : grille GO/NO-GO de fin de passage

**Évaluateur :** ______________   **Passage :** ☐ Passage 1 (équipe A) ☐ Passage 2 (équipe B)

| Critère | ☐ atteint |
|-----------|:----------:|
| Logiciel applicatif de l'OBC en cours d'exécution (`obdh.sw_image` 0x0311 = 1) | ☐ |
| Temps bord réglé, résidu < 1.0 s | ☐ |
| Mode balise levé, liaison descendante sur LOW (`ttc.tm_tier` 0x0539 = 1) | ☐ |
| Antenne toujours repliée, `ttc.antenna_deployed` (0x0520) = 0 — COM-006 la déploie ; LOW n'exige pas le déploiement | ☐ |
| Lignes de réchauffeurs alimentées seulement là où leur zone avait besoin de chaleur, et consignées (LEOP-007 étape 2) | ☐ |
| Ligne des roues du SCAO sur ON, SCAO passé par DETUMBLE (2) jusqu'à COARSE_SUN (3) | ☐ |
| Vitesses angulaires < 0.5°/s sur tous les axes ; `aocs.att_error` < 15° dans le maintien COARSE_SUN | ☐ |
| Fiche d'anomalie remplie pour chaque injection | ☐ |
| Phase passée à COMMISSIONING (5) avec `SYS_SET_MISSION_PHASE` (fonction 120) (passage 2 uniquement) | ☐ |

**Score :** ____ / 9 (passage 1) ou ____ / 9 (passage 2)

**Notes pour le débriefing :** _________________________________________

---

# Fiche WB-5.5-OBS — Jour 3 : fiches d'observation (axes utilisés : Communications + Technique)

(Imprimez les deux. Chaque observateur en remplit une par passage observé.)

### Fiche d'observation — axe Communications

**Observateur :** _____________  **Passage observé :** _____________

| Élément | Note (horodatage + quoi + qui) |
|------|-------------------------------|
| Discipline de boucle vocale (annonces, micro ouvert) | |
| Protocole GO/NO-GO respecté | |
| Interférences de parole (nombre + horodatages) | |
| Messagerie du MCS — utilisée pour quoi ? | |
| Passation : moment, contenu, exhaustivité | |
| Confusion silencieuse (un opérateur a fait une erreur parce que personne n'a rien dit) ? | |

**Points forts :** _________________________________________________

**À améliorer :** ______________________________________________

**Recommandation précise :** _____________________________________

### Fiche d'observation — axe Technique

**Observateur :** _____________  **Passage observé :** _____________

| Élément | Note |
|------|------|
| Respect des procédures — des étapes sautées ou exécutées dans le désordre ? | |
| Délai de détection des anomalies — du premier indice à la première action | |
| Interprétation de la télémesure — des erreurs de lecture ? | |
| Discipline de commande — des commandes non autorisées ? | |
| Utilisation du panneau FDIR — quelqu'un le surveillait-il ? | |
| Résultat par rapport aux critères de passage | |

**Points forts :** _________________________________________________

**À améliorer :** ______________________________________________

**Recommandation précise :** _____________________________________

---

# Fiche WB-5.5-HO — Jour 3 : fiche de passation entre passages

**Usage :** entre le passage 1 et le passage 2 (équipe A → équipe B). Une par
poste ; l'opérateur sortant signe, l'opérateur entrant signe.

Imprimez 9 exemplaires (un par poste de console).

### Passation — poste : ______________________

| Champ | Saisie |
|-------|-------|
| Opérateur sortant | |
| Opérateur entrant | |
| Valeurs actuelles des paramètres (3 mnémoniques principaux) | |
| État actuel de la procédure (ID du fichier + étape) | |
| Page de console laissée ouverte pour l'opérateur suivant (page, panneau) | |
| Question ouverte pour le quart suivant | |
| Signature du sortant | |
| Signature de l'entrant | |
| Heure | |

---

# Fiche WB-5.5-DB — Jour 3 : réflexion de débriefing après le quart

**Nom :** _____________________

1. Quelle décision avez-vous prise pendant le quart que, avec le recul,
   vous ne reprendriez pas ? Pourquoi ?

   ___________________________________________________________
   ___________________________________________________________

2. Quelle décision vous a surpris par son efficacité ?

   ___________________________________________________________
   ___________________________________________________________

3. Quelle annonce vocale avez-vous eu le plus de mal à faire en temps
   réel ?

   ___________________________________________________________

4. Qu'est-ce que l'équipe a mieux fait collectivement que vous ne
   l'attendiez ?

   ___________________________________________________________

5. Quelle chose précise ferez-vous différemment demain ?

   ___________________________________________________________

---

# Fiche WB-5.6-PB — Jour 4 : briefing avant la série de passages de recette en orbite

| Point | ☐ |
|------|:-:|
| Scénario BP-3 `commissioning_day_start.yaml` chargé (rédigé par l'enseignant — voir le guide de l'enseignant ; il ne fait pas partie du jeu livré `configs/eosat1/scenarios/`) | ☐ |
| Satellite en phase 4 (LEOP), `eps.spacecraft_phase` (0x0129) = 4 — COMMISSIONING (5) est déclaré par LEOP-003 étape 7 | ☐ |
| Affectations des postes affichées (équipe différente de la veille) | ☐ |
| Chronologie de la série de passages comprise (4 passages simulés en 2,5 h de temps réel) | ☐ |
| Les 13 procédures de recette en orbite (COM-001…COM-013) chargées dans l'index des procédures | ☐ |
| L'EPS confirme un SoC d'environ 90 %, `eps.pl_payload` (0x0113) = 0 | ☐ |
| Le poste thermique confirme que le FPA est à son équilibre non refroidi, `payload.fpa_temp` (0x0601) d’environ −5 à +7 °C | ☐ |
| Les opérations charge utile ont étudié en détail COM-009/-010/-011/-012 | ☐ |
| Cible candidate pour la première lumière choisie (FDS) | ☐ |
| Multiplicateur de vitesse du temps compressé réglé (enseignant) | ☐ |

---

# Fiche WB-5.6-C001 — COM-001 Vérification de l'EPS (confirmer chaque étape)

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Tension de bus de référence — `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) ∈ [28.4, 34.0] V (la bande jaune de la console ; le bus n'est pas régulé — il suit la batterie jusqu'au plafond de 33.4 V) | ☐ | V : ____ |
| 2 | Tension et SoC de la batterie — `GET_PARAM(param_id=0x0100)`, `GET_PARAM(param_id=0x0101)` (S20.3) | `eps.bat_voltage` (0x0100) ∈ [24.0, 33.6] V (GomSpace BPX 8S-1P de 100 Wh : 24.0 V vide, 28.8 V nominal, 33.6 V pleine) ; `eps.bat_soc` (0x0101) > 70 % | ☐ | V : ____ SoC : ____ |
| 3 | Performances du générateur solaire au Soleil — `HK_REQUEST(sid=1)`, éclairé et pointé vers le Soleil | `eps.power_gen` (0x0107) ∈ [40, 90] W (88.6 W est la crête de l'ensemble du satellite ; environ 80 W est normal en pointage solaire) | ☐ | ____ W |
| 4 | Décharge en éclipse — `HK_REQUEST(sid=1)` à l'entrée et à mi-éclipse | `eps.power_gen` ~0 W dans les 30 s après l'entrée ; `eps.bat_soc` en baisse de moins de 1.5 %/min ; `eps.bus_voltage` > 30.9 V | ☐ | |
| 5 | Reprise de charge en sortie d'éclipse — `HK_REQUEST(sid=1)` à la sortie + 5 min | `eps.power_gen` > 35 W dans les 60 s après la sortie ; `eps.bat_soc` en hausse dans les 120 s | ☐ | |
| 6 | Bilan de puissance — `GET_PARAM(param_id=0x0108)` ; production moyenne sur l'orbite comparée à la consommation | production moyenne sur l'orbite > consommation ; SoC en fin d'éclipse > 50 % sous charge nominale | ☐ | marge : ____ W |
| 7 | Régulation du bus lors d'un transitoire de charge — consigner d'abord `eps.pl_htr_bat` (0x0115), puis `EPS_POWER_ON(line_index=5)` (S8.1 func_id **19**), et `EPS_POWER_OFF(line_index=5)` (func **20**) seulement si la ligne était éteinte à l'entrée. Pas la charge utile : sa ligne est OFF jusqu'à COM-009 | `eps.bus_voltage` reste dans [30.2, 34.0] V en 5 s et revient dans [30.9, 34.0] V en 10 s ; `eps.pl_htr_bat` revenu à sa valeur d'entrée | ☐ | V min : ____ |

Référence de bilan pour l'étape 6 : la charge nominale moyenne sur l'orbite est
d'environ **22.7 W** (charge utile en STANDBY, refroidisseur du FPA arrêté) pour
une production d'environ 45.1 W à l'angle bêta le moins productif, β = −31.2°
(marge +22.4 W, rapport 1.98 ; 1.71 avec les prises de vue intégrées au cycle),
sur la batterie de **100 Wh**.

**Sortie ?** ☐ oui ☐ non   **GO COM-002 :** ☐

---

# Fiche WB-5.6-C002 — COM-002 Vérification du TCS (confirmer chaque étape)

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | HK thermique — `HK_REQUEST(sid=3)` (S3.27 ; SID 3 = TCS, cadence de 60 s) | `tcs.temp_obc` (0x0406) dans les limites OBC de la page TCS ; `tcs.temp_battery` (0x0407) ∈ [+5, +35] °C ; `tcs.temp_fpa` (0x0408) remontée — charge utile éteinte et non refroidie, d’environ −5 à +7 °C | ☐ | obc :__ bat :__ fpa :__ |
| 2 | Profil en phase éclairée — `HK_REQUEST(sid=3)` toutes les 120 s pendant 30 min | `tcs.temp_obc` stable ou en hausse de moins de 1 °C/min ; `tcs.temp_battery` stable | ☐ | |
| 3 | Profil en éclipse — `HK_REQUEST(sid=3)` à l'entrée, à mi-éclipse et à la sortie | `tcs.temp_obc` au-dessus de la limite basse OBC de la page TCS pendant toute l'éclipse ; `tcs.temp_battery` > +5 °C pendant toute l'éclipse ; vitesses de refroidissement consignées (OBC environ 0.5 °C/min, batterie tamponnée) | ☐ | |
| 4 | Circuit du réchauffeur batterie, ligne d'abord : consigner `eps.pl_htr_bat` (0x0115) ; `EPS_POWER_ON(line_index=5)` (S8.1 func 19) ; `HEATER_BATTERY(on=1)`, puis `HEATER_BATTERY(on=0)` (func **40**) ; `HEATER_AUTO_MODE(circuit=0)` (func **45**) | `eps.pl_htr_bat` = 1 en 5 s ; ON et OFF acquittés ; `tcs.temp_battery` (0x0407) en hausse ou stable sur 3 min ; la ligne **reste sur ON** sous la régulation du thermostat (marche sous +5 °C, arrêt au-dessus de +10 °C) | ☐ | entrée : ____ |
| 5 | Circuit du réchauffeur OBC, ligne d'abord : consigner `eps.pl_htr_obc` (0x0116) ; `EPS_POWER_ON(line_index=6)` ; `HEATER_OBC(on=1)`, puis `HEATER_OBC(on=0)` (func **41** — et non 42, le réchauffeur du lit catalytique du propulseur) ; `HEATER_AUTO_MODE(circuit=1)` | `eps.pl_htr_obc` = 1 en 5 s ; ON et OFF acquittés ; `tcs.temp_obc` (0x0406) stable ou en hausse sur 2 min ; la ligne **reste sur ON** sous son thermostat | ☐ | entrée : ____ |
| 6 | Lire les seuils des thermostats des réchauffeurs — `GET_PARAM(param_id=0x0330)`, `GET_PARAM(param_id=0x0331)` (S20.3) | batterie : marche à +5 °C (arrêt à +10 °C), OBC : marche à −10 °C (arrêt à −5 °C) ; la fiche les lit, elle ne les modifie pas | ☐ | |
| 7 | Interface du refroidisseur du FPA avant activation — `GET_PARAM(param_id=0x040C)`, `GET_PARAM(param_id=0x0114)` | `tcs.cooler_fpa` (0x040C) = 0 ; `eps.pl_fpa_cooler` (0x0114) = 0 ; `tcs.temp_fpa` (0x0408) à l'équilibre non refroidi, d’environ −5 à +7 °C — consignée pour COM-010 | ☐ | T_fpa : ____ °C |
| 8 | Établir le rapport thermique de référence : minimum, maximum et moyenne de chaque zone sur une orbite, comparés au modèle thermique | conforme à la prédiction du modèle à ± 5 °C | ☐ | |

Les deux lignes de réchauffeurs restent sur **ON** à la fin de cette fiche :
la régulation par thermostat est désormais la configuration nominale. Un
réchauffeur dont la ligne est coupée obéit à la commande et ne chauffe rien —
c'est pourquoi chaque circuit commence par alimenter sa ligne.

**Sortie ?** ☐ oui ☐ non   **GO COM-005 :** ☐

---

# Fiche WB-5.6-C005 — COM-005 Transitions de modes SCAO (confirmer chaque étape)

**Codes de mode** (`aocs/aocs_mode_codes.yaml`, référence) : 0 OFF,
1 SAFE_BOOT, 2 DETUMBLE, 3 COARSE_SUN, 4 NOMINAL, 5 FINE_POINT,
6 SLEW, 7 DESAT, 8 ECLIPSE, 9 INERTIAL. Chaque transition commandée se fait par
`AOCS_SET_MODE(mode=N)` (S8.1 **func_id 0**).

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Mémoriser le mode commandé : `AOCS_SET_MODE(mode=4)` — NOMINAL | `aocs.mode` (0x020F) dans {4, 8} en 300 s (8 = ECLIPSE, le passage automatique côté ombre) ; `aocs.commanded_mode` (0x0297) = 4 en 10 s ; `aocs.att_error` (0x0217) < 1.0° en 600 s, côté éclairé | ☐ | |
| 2 | Commandée NOMINAL → FINE_POINT par son verrou : `AOCS_FINE_READY_CHECK` (S8.1 func **89**), puis `AOCS_SET_MODE(mode=5)` | `aocs.fine_ready` (0x02C5) = 0, les sept conditions au vert (en éclipse, le bit 5 le maintient non nul : attendre l'arc éclairé) ; `aocs.mode` = 5 en 30 s ; `aocs.att_error` < 0.1° en 300 s | ☐ | masque : ____ erreur : ____ ° |
| 3 | Commandée FINE_POINT → NOMINAL : `AOCS_SET_MODE(mode=4)` | `aocs.mode` = 4 en 30 s ; `aocs.commanded_mode` (0x0297) = 4 en 10 s | ☐ | |
| 4 | Commandée NOMINAL → INERTIAL et retour : `AOCS_SET_MODE(mode=9)`, puis `AOCS_SET_MODE(mode=4)` | `aocs.mode` = 9, puis 4, chacun en 30 s | ☐ | |
| 5 | COARSE_SUN est un maintien, pas une destination : `AOCS_SET_MODE(mode=3)`, puis **attendre** — ne rien envoyer | `aocs.mode` = 3 en 30 s et `aocs.mode_demoted` (0x0298) = 1 ; puis `aocs.mode` = 4 **de lui-même** en 3600 s (environ 1850 s en plein Soleil ; ajouter un arc d'éclipse si le maintien franchit le terminateur) et 0x0298 revenu à 0 | ☐ | promotion : ____ s |
| 6 | Passage automatique en éclipse, observé au passage — aucune commande | dans l'archive : `aocs.mode` dans {4, 8} à chaque échantillon depuis l'étape 3 ; NOMINAL → ECLIPSE (8) à l'entrée et retour à la sortie, `aocs.commanded_mode` (0x0297) = 4 tout du long | ☐ | |
| 7 | Commandée avec sortie automatique — désaturation : `AOCS_DESATURATE` (S8.1 func **1**) | `aocs.mode` = 7 (DESAT) en 30 s, puis 4 en 900 s sans commande ; une désaturation inefficace se termine sur temporisation (0x029C, événement 0x020E) | ☐ | |
| 8 | Documenter la matrice des transitions : les lignes commandées portent la TC et sa vérification, les lignes automatiques le déclencheur et l'heure observée | chaque ligne justifiée — gestion des modes AOCS recettée | ☐ | |

Un jeu de 3 roues sur 4 permet toujours FINE_POINT : le bit 1 de
`aocs.fine_ready` signifie *moins de trois* roues, et un jeu dégradé est
signalé par `aocs.fine_degraded` (0x0299), et non refusé.

**Sortie ?** ☐ oui ☐ non

---

# Fiche WB-5.6-C006 — COM-006 Vérification de la liaison TTC (confirmer chaque étape)

L'échelle de débits TM comporte exactement trois paliers : **SAFE 1 kbit/s /
LOW 16 kbit/s / HIGH 128 kbit/s** (SAFE s'appelait BEACON jusqu'en 2026-08c ;
« balise » désigne désormais seulement l'émetteur UHF distinct). SAFE ne peut
pas être sélectionné avec `TTC_SET_DATA_RATE` — sa référence provient du
passage LEOP-001. HIGH exige l'antenne déployée et le mode DOWNLINK ; la règle
des 10° d'élévation est une politique sol, pas un verrou bord.

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 0 | Configurer la chaîne bande S : `EPS_POWER_ON(line_index=2)` (func 19), `TTC_PA_ON` (func **66**), `TTC_SET_BEACON_MODE(on=0)` (func **70**), `TTC_DEPLOY_ANTENNA` (func **69**), `HK_REQUEST(sid=6)` | `eps.pl_ttc_tx` (0x0112) = 1 ; `ttc.pa_on` (0x0516) = 1 ; `ttc.beacon_mode` (0x0521) = 0 ; `ttc.antenna_deployed` (0x0520) = 1 en 30 s ; `ttc.tx_active` (0x0525) = 1 (si 0, `ttc.tx_gate_status` (0x052B) indique l'autorisation manquante) | ☐ | |
| 1 | Référence du transpondeur principal : `HK_REQUEST(sid=6)` | `ttc.link_status` (0x0501) = **2** (LOCKED) ; page TT&C (sol) : `ttc.rssi` (0x0502) > −126 dBm, `ttc.link_margin` (0x0503) > 6.0 dB ; élévation et station consignées | ☐ | ____ dB @ ____ ° |
| 2 | RSSI en fonction de l'élévation, lu sur la page TT&C à 10°, 30° et 60° et plus | `ttc.rssi` (0x0502) > −126 dBm basse, > −118 dBm moyenne, > −114 dBm haute ; `ttc.link_margin` (0x0503) > 3.0 dB à basse élévation ; à ± 3 dB du bilan de liaison | ☐ | __ / __ / __ dBm |
| 2a | Référence de chaque palier, au-dessus de 30° : `TTC_SET_DATA_RATE(rate=0)` (func **65**) LOW ; `TTC_SET_DOWNLINK_MODE(on=1)` (func **79**) ; `TTC_SET_DATA_RATE(rate=1)` HIGH ; puis `TTC_SET_DATA_RATE(rate=0)` et `TTC_SET_DOWNLINK_MODE(on=0)` | LOW : `ttc.tm_data_rate` (0x0506) = 16000 bit/s, `ttc.tm_tier` (0x0539) = 1, marge **55–59 dB** à 30°. HIGH : `ttc.downlink_mode` (0x053C) = 1, 128000 bit/s, palier 2, `ttc.tm_symbol_rate` (0x053B) = 64000 Bd (QPSK), marge **45–48 dB**. Écart marge(LOW) − marge(HIGH) = **10.5 ± 0.5 dB** ; retour à 16000 bit/s avec le mode DOWNLINK à 0 | ☐ | écart : ____ dB |
| 2b | Politique d'autorisation sol sur HIGH (aucun verrou bord) : sous 10° d'élévation, tenter d'armer HIGH dans le panneau de commande du MCS **sans** confirmer l'autorisation | le MCS lève son avertissement de basse élévation et ne libère rien ; aucune télécommande n'atteint le satellite ; la liaison reste en LOW | ☐ | |
| 3 | Basculer sur le transpondeur redondant : `TTC_SWITCH_REDUNDANT` (func **64**) | `ttc.link_status` = 2 en 60 s ; `ttc.rssi` > −126 dBm (la station peut devoir réacquérir brièvement) | ☐ | |
| 4 | Performances du transpondeur redondant : `HK_REQUEST(sid=6)` | `ttc.link_margin` (0x0503) > 6.0 dB ; RSSI à 2.0 dB près du principal à élévation comparable | ☐ | Δ : ____ dB |
| 5 | Rétablir le principal : `TTC_SWITCH_PRIMARY` (func **63**) | `ttc.link_status` = 2 en 60 s ; `ttc.rssi` > −126 dBm | ☐ | |
| 6 | Débit de commandes : six `GET_PARAM(param_id=0x0105)` … `GET_PARAM(param_id=0x010A)` rapprochées (S20.3), puis `GET_PARAM(param_id=0x0306)` | les six réponses en 30 s ; `obdh.tc_rej_count` (0x0306) inchangé sur la rafale | ☐ | |
| 7 | Vérification multistation aux passages suivants : répéter les étapes 1–2 sur chaque station du réseau | marge > 3 dB à 10° d'élévation depuis chaque station | ☐ | stations : ____ |
| 8 | Établir le rapport de bilan de liaison : marge en fonction de l'élévation **et** du palier de débit pour chaque station, comparée au tableau de référence de la fiche | écarts documentés ; élévation opérationnelle minimale établie pour chaque station | ☐ | |
| 9 | Mettre la liaison en configuration sûre : `TTC_SET_DATA_RATE(rate=0)`, `TTC_SET_DOWNLINK_MODE(on=0)`, `TTC_SWITCH_PRIMARY`, `HK_REQUEST(sid=6)` | `ttc.tm_tier` (0x0539) = 1 et `ttc.tm_tier_cmd` (0x053A) = 1 ; `ttc.downlink_mode` (0x053C) = 0 ; `ttc.beacon_mode` (0x0521) = 0 ; `ttc.antenna_deployed` (0x0520) = 1 et `ttc.pa_on` (0x0516) = 1 — les deux restent ainsi pour les opérations nominales | ☐ | |

Un changement de débit refusé revient en S1.8 0x0007 avec un avis qui nomme le
verrou bord (mode balise, antenne, mode DOWNLINK). Lire l'avis, pas le code :
l'élévation n'en fait jamais partie.

**Sortie ?** ☐ oui ☐ non

---

# Fiche WB-5.6-C007 — COM-007 Vérification de l'OBDH (confirmer chaque étape)

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Vérifier le mode de l'OBC : `HK_REQUEST(sid=4)` (S3.27) | `obdh.mode` (0x0300) = 0 (NOMINAL ; 1 SAFE, 2 EMERGENCY). SAFE ici signifie qu'une fiche précédente n'a pas rétabli une excursion — enquêter avant de poursuivre | ☐ | |
| 2 | Charge du processeur : `GET_PARAM(param_id=0x0302)` (S20.3) | `obdh.cpu_load` (0x0302) ∈ [10, 50] % (au repos, environ 15–25 %) | ☐ | ____ % |
| 3 | État de la mémoire : `GET_PARAM(param_id=0x0303)` (`obdh.mmm_used`), `GET_PARAM(param_id=0x031E)` (`obdh.mem_errors`), `GET_PARAM(param_id=0x0319)` (`obdh.seu_count`) | mémoire de masse < 70 % ; `obdh.mem_errors` (0x031E) et `obdh.seu_count` (0x0319) consignés comme références et stables entre deux lectures | ☐ | occupé : ____ % |
| 4 | Compteurs de paquets TC/TM : `GET_PARAM(param_id=0x0304)`, `GET_PARAM(param_id=0x0306)`, `GET_PARAM(param_id=0x0307)` | `obdh.tc_rx_count` > 0, conforme au journal sol ; `obdh.tc_rej_count` = 0 ; `obdh.tm_pkt_count` > 0 et en hausse | ☐ | |
| 5 | Confirmer les services du mode NOMINAL — aucune commande de mode : commander le mode où l'on est déjà ne prouve rien | `obdh.mode` (0x0300) = 0 ; `obdh.cpu_load` (0x0302) < 60 % sur 30 s | ☐ | |
| 6 | Génération autonome des HK : `GET_PARAM(param_id=0x0307)`, attendre 60 s **sans** envoyer de TC, `GET_PARAM(param_id=0x0307)` de nouveau | `obdh.tm_pkt_count` a augmenté | ☐ | |
| 7 | Chien de garde : `OBC_DIAGNOSTIC` (S8.1 func **61**), `GET_PARAM(param_id=0x0316)` | octet 5 de la réponse du diagnostic = 1 (chien de garde armé — il figure dans cette réponse seulement, pas dans un paramètre de télémesure) ; `obdh.last_reboot_cause` (0x0316) = 0 | ☐ | |
| 8 | Excursion de mode de l'OBC NOMINAL → SAFE → NOMINAL : `OBC_SET_MODE(mode=1)`, puis `OBC_SET_MODE(mode=0)` (S8.1 func **50**) | `obdh.mode` = 1 en 15 s, puis 0 en 15 s — **la fiche ne doit pas se terminer en SAFE** ; le bandeau de contingence du MCS est attendu pendant SAFE | ☐ | |
| 9 | Consigner la référence de l'OBDH : charge CPU, occupation mémoire, compteurs d'erreurs et de SEU, statistiques TC/TM, état du chien de garde | rapport de vérification de l'OBDH déposé — la référence de la détection d'anomalies en opérations nominales | ☐ | |

Il n'existe aucune télécommande de réarmement du chien de garde : son état se
lit dans la réponse de `OBC_DIAGNOSTIC`.

**Sortie ?** ☐ oui ☐ non

---

# Fiche WB-5.6-C008 — COM-008 Configuration de la FDIR (confirmer chaque étape)

Il n'existe **aucune** télécommande de chargement de table FDIR. Le jeu de règles est une
configuration statique (`subsystems/fdir.yaml` plus les définitions de limites S12
et les règles événement-action S19) ; la recette en orbite le vérifie
et l'éprouve, elle ne l'envoie pas.

Gardez les deux échelles bien distinctes : **gravité FDIR 0–4** (gravité de
l'événement) et **niveau d'autonomie 0–3** (qui est autorisé à agir —
0 matériel, 1 logiciel du sous-système, 2 FDIR de l'OBC, 3 sol). Ce ne sont pas
la même échelle et elles ne doivent jamais être confondues sur la boucle.

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Activer et inventorier la surveillance S12 : `MON_ENABLE` (**S12.1**), `MON_REPORT_DEFS` (S12.12) | rapport de définitions TM(12,13) en 10 s ; toutes les définitions livrées de `monitoring/s12_defs` présentes, aucune inattendue | ☐ | nombre : ____ |
| 2 | Inventorier la table événements-actions S19 : `EA_REPORT_DEFS` (S19.8) | rapport TM(19,128) en 10 s ; règles livrées présentes et ACTIVÉES — la chaîne du moment cinétique (surveillance S12 de `aocs.h_env_frac` (0x02BA) → ea 2001 → S8 func 1, la désaturation) et la chaîne de mise en sécurité sur surchauffe TCS (ea 3003) | ☐ | |
| 3 | Télémesure de synthèse FDIR : `GET_PARAM(param_id=0x0700)`, `GET_PARAM(param_id=0x0701)` (S20.3) | `fdir.level` (0x0700) = 0 ; `fdir.active_alarms` (0x0701) = 0. Toute valeur non nulle est une alarme verrouillée : la résoudre avant l'étape 4 | ☐ | |
| 4 | Essai fonctionnel du verrou de délestage commandé : consigner `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_ttc_tx` (0x0112) ; `EPS_EMERGENCY_LOAD_SHED(stage=1)` (S8.1 func **25**), puis `EPS_EMERGENCY_LOAD_SHED(stage=0)`. Jamais l'étage 2 ou 3 ici | étage 1 : `eps.load_shed_stage` (0x0134) = 1 et **se verrouille**, événement LOAD_SHED_STAGE_1 (0x0106), `eps.pl_payload` = 0. Étage 0 : retour à 0 et chaque indicateur de ligne **inchangé** — l'étage 0 ne réalimente rien | ☐ | |
| 5 | Confirmer l'absence d'état de protection résiduel : `GET_PARAM(param_id=0x0700)`, `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` | `fdir.level` = 0 ; `eps.load_shed_stage` = 0 ; `obdh.mode` (0x0300) = 0 — cette fiche ne fait aucune excursion de mode de l'OBC | ☐ | |

Lire les seuils FDIR dans le panneau FDIR et dans `subsystems/fdir.yaml`, pas
de mémoire : les limites sont de la configuration, et elles changent.

**Sortie ?** ☐ oui ☐ non

---

# Fiche WB-5.6-C009 — COM-009 Mise sous tension de la charge utile (confirmer chaque étape)

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Référence EPS avant mise sous tension : `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) ∈ [28.4, 34.0] V ; `eps.bat_soc` (0x0101) > 75 % ; `eps.power_gen` (0x0107) > 40 W — les trois consignés | ☐ | |
| 2 | Vérifier que la charge utile est sur OFF : `HK_REQUEST(sid=5)` | `payload.mode` (0x0600) = 0 (OFF) | ☐ | |
| 3 | Alimenter la ligne, puis STANDBY : `EPS_POWER_ON(line_index=3)` (S8.1 func_id **19**), `HK_REQUEST(sid=1)`, `PAYLOAD_SET_MODE(mode=1)` (func **26**), `HK_ENABLE(sid=5)` (**S3.5**), `HK_REQUEST(sid=5)` | `eps.pl_payload` (0x0113) = 1 en 10 s ; `payload.mode` = 1 (STANDBY) en 60 s, et **toujours 1** à une nouvelle demande du SID 5 60 s plus tard — un mode qui revient à 0 signifie que la ligne est coupée | ☐ | |
| 4 | Consommation de la charge utile : `HK_REQUEST(sid=1)`, `GET_PARAM(param_id=0x0106)` (S20.3) | `eps.bus_voltage` > 30.9 V ; `eps.power_cons` (0x0106) en hausse de **2–3 W** sur la référence (STANDBY environ 2.4 W ; le refroidisseur de 15 W n'est pas en marche avant COM-010) | ☐ | ____ W |
| 5 | Santé de l'électronique : `HK_REQUEST(sid=5)`, `GET_PARAM(param_id=0x0611)`, `GET_PARAM(param_id=0x0603)` | `payload.imager_status` (0x0611) sans bit de défaut ; `payload.imager_temp` (0x0603) dans sa plage de fonctionnement | ☐ | |
| 6 | Température du FPA avant le refroidisseur : `GET_PARAM(param_id=0x0601)` | `payload.fpa_temp` (0x0601) ∈ [+5, +30] °C — consignée pour COM-010 | ☐ | ____ °C |
| 7 | Interface de données : `GET_PARAM(param_id=0x0604)`, `GET_PARAM(param_id=0x0648)`, `GET_PARAM(param_id=0x0647)` | `payload.store_used` (0x0604) environ 20 % (remplissage préexistant : la référence à vide, pas un défaut) ; `payload.product_count` (0x0648) = 0 et `payload.product_mb` (0x0647) = 0 | ☐ | |
| 8 | Maintenir STANDBY 10 min pour la stabilisation thermique : `HK_REQUEST(sid=3)` à T+5 et T+10 min, `HK_REQUEST(sid=5)` | `tcs.temp_obc` (0x0406) stable ; `payload.fpa_temp` stable ; `payload.mode` = 1 maintenu | ☐ | |
| 9 | Consigner le rapport de mise sous tension de la charge utile : chronologie, consommation, mot d'état de l'imageur, températures de l'imageur et du FPA, référence de la mémoire | prêt pour COM-010 | ☐ | |

Modes de la charge utile : 0 OFF, 1 STANDBY, 2 IMAGING, **3 CALIBRATION**.
STANDBY consomme environ 0.08 A sous 32 V sur la ligne 3.

**Sortie ?** ☐ oui ☐ non   **GO COM-010 :** ☐

---

# Fiche WB-5.6-C010 — COM-010 Activation du refroidisseur du FPA (confirmer chaque étape ; s'étend sur une éclipse)

Le refroidisseur du FPA est un **cryoréfrigérateur miniature de type Stirling** fonctionnant
à environ 23 % du rendement de Carnot (`fpa_cooler_carnot_fraction` 0.23) — et non un
empilement Peltier. Sa capacité diminue à mesure que l'écart de température augmente, de sorte que le
plancher atteignable varie avec la température du puits thermique et la charge
de prise de vue. Consigne par défaut **−15 °C** ; enveloppe commandable de **−20 °C à
0 °C** (`PAYLOAD_COOLER_SETPOINT`, S8.1 func **36**, l'argument est un
uint16 en **centikelvins** — −15 °C correspond à 0x64D7). La boucle se stabilise en
environ 10 minutes et ne dépasse jamais la consigne.

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Consigner l'état avant activation, refroidisseur sur OFF (mise en froid T = 0) : `HK_REQUEST(sid=3)`, `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=5)` (S3.27) | `payload.fpa_temp` (0x0601) ∈ [+8, +14] °C ; `tcs.temp_fpa` (0x0408) cohérente avec elle ; `payload.mode` (0x0600) = 1 | ☐ | T_fpa : ____ °C |
| 2 | Activer le refroidisseur : `FPA_COOLER(on=1)` (S8.1 func_id **43**), puis `GET_PARAM(param_id=0x040C)`, `GET_PARAM(param_id=0x0114)` | `tcs.cooler_fpa` (0x040C) = 1 **et** `eps.pl_fpa_cooler` (0x0114) = 1 — les deux, sinon le refroidisseur ne fonctionne pas réellement | ☐ | |
| 3 | Consommation du refroidisseur : `HK_REQUEST(sid=1)`, `GET_PARAM(param_id=0x0106)` (S20.3) | `eps.power_cons` (0x0106) en hausse de **14–16 W** sur la référence d'avant refroidissement en 30 s ; `eps.bus_voltage` (0x0105) > 30.9 V | ☐ | ____ W |
| 4 | 5 premières minutes : `GET_PARAM(param_id=0x0601)` à T+2 et T+5 min (chaque minute sur WB-5.6-FPA) | `payload.fpa_temp` < +4 °C à T+2 et < −8 °C à T+5. La rampe est exponentielle : plus lente à T+5 qu'à T+2, c'est normal | ☐ | T+5 : __ °C |
| 5 | Stabilisation : `GET_PARAM(param_id=0x0601)` à T+10 et T+15 min | T+10 ∈ [−16.0, −14.0] °C ; T+15 ∈ [−16.0, −15.0] °C. Une lecture sous −16.5 °C est un **défaut de régulation**, pas un refroidisseur plus performant que prévu | ☐ | T+15 : __ °C |
| 6 | Température opérationnelle : `GET_PARAM(param_id=0x0601)`, `GET_PARAM(param_id=0x0610)`, `GET_PARAM(param_id=0x0631)`, `GET_PARAM(param_id=0x064A)`, `GET_PARAM(param_id=0x064B)` | `payload.fpa_temp` ∈ [−16.5, −14.5] °C ; `payload.fpa_ready` (0x0610) = 1 en 60 s (hystérésis) ; `payload.fpa_setpoint` (0x0631) = −15.0 ; `payload.cooler_margin_k` (0x064B) > 0 (environ +5 K) ; plancher indiqué par `payload.cooler_floor_c` (0x064A) | ☐ | marge : ____ K |
| 7 | Stabilité : `GET_PARAM(param_id=0x0601)` à T+35, T+40 et T+45 min | `payload.fpa_temp` ∈ [−16.5, −14.5] °C à chaque échantillon ; crête à crête < 1.0 °C sur 10 min (sous 0.5 °C, c'est la régulation normale) | ☐ | c-c : ____ °C |
| 8 | Pendant l'éclipse, si le passage en comporte une : `GET_PARAM(param_id=0x0601)` | `payload.fpa_temp` ∈ [−16.5, −14.5] °C ; `eps.bus_voltage` (0x0105) > 30.9 V avec la charge du refroidisseur | ☐ | |
| 9 | Établir le rapport d'activation du refroidisseur : courbe de mise en froid, puissance du refroidisseur, données de stabilité et d'éclipse | prêt pour COM-011 | ☐ | |

**Si `cooler_margin_k` ≤ 0 :** le refroidisseur ne peut physiquement pas atteindre la
consigne commandée avec le puits thermique et la charge actuels. La solution est une
**consigne plus chaude**, pas une attente plus longue.

C'est l'indicateur de disponibilité, et non une température retenue de mémoire,
qui autorise la prise de vue. La consommation propre du refroidisseur est
`payload.cooler_pwr` (0x0602), environ 15 W.

**Sortie ?** ☐ oui ☐ non   **GO COM-011 :** ☐

---

# Fiche WB-5.6-FPA — Fiche de suivi de la mise en froid du FPA

**Usage :** pendant COM-010. La boucle se ferme en environ 10 minutes : relevez donc
`payload.fpa_temp` (0x0601) toutes les minutes pendant les
15 premières minutes, puis toutes les 5 minutes pendant le maintien de stabilité.

| Temps écoulé | T_fpa (°C) | `payload.cooler_pwr` 0x0602 (W) | Éclipse ? | Note |
|---------|-----------|------------------|:--------:|------|
| 0:00 | | | ☐ | début, d’environ −5 à +7 °C |
| 0:01 | | | ☐ | |
| 0:02 | | | ☐ | attendu < +4 °C |
| 0:03 | | | ☐ | |
| 0:04 | | | ☐ | |
| 0:05 | | | ☐ | attendu < −8 °C |
| 0:06 | | | ☐ | |
| 0:07 | | | ☐ | |
| 0:08 | | | ☐ | |
| 0:09 | | | ☐ | |
| 0:10 | | | ☐ | attendu de −16.0 à −14.0 °C |
| 0:11 | | | ☐ | |
| 0:12 | | | ☐ | |
| 0:13 | | | ☐ | |
| 0:14 | | | ☐ | |
| 0:15 | | | ☐ | plage de consigne attendue à ce stade |
| 0:20 | | | ☐ | maintien de stabilité |
| 0:25 | | | ☐ | |
| 0:30 | | | ☐ | |
| 0:35 | | | ☐ | |
| 0:40 | | | ☐ | |
| 0:45 | | | ☐ | variation crête à crête < 1.0 °C sur le maintien |

**`payload.fpa_ready` (0x0610) positionné à :** ______ min
**`payload.cooler_margin_k` (0x064B) à la consigne :** ______ K

---

# Fiche WB-5.6-C011 — COM-011 Étalonnage de la charge utile (confirmer chaque étape)

L'étalonnage radiométrique est un mode à part entière de la charge utile : `payload.mode`
(0x0600) = **3 (CALIBRATION)**. L'étalonnage d'obscurité n'exige plus
le mode IMAGING. Si un étalonnage est refusé, lisez le code de motif —
0x0024 refusé car en IMAGING, 0x0025 FPA non prêt, 0x0026
obturateur dans la mauvaise position, 0x0027 lampe dans le mauvais état,
0x0028 capture avec l'obturateur fermé.

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | État avant étalonnage, refroidisseur EN MARCHE d'abord : `FPA_COOLER(on=1)` (S8.1 func **43**), `HK_REQUEST(sid=3)`, `HK_REQUEST(sid=5)` (S3.27), `GET_PARAM(param_id=0x060B)`, `GET_PARAM(param_id=0x060A)` (S20.3) | `tcs.cooler_fpa` (0x040C) = 1 en 10 s ; `payload.mode` (0x0600) = 1 (STANDBY) ; `payload.fpa_ready` (0x0610) = 1 en 600 s (mise en froid d'environ 6.5 min) ; `payload.fpa_temp` (0x0601) ∈ [−16.5, −14.5] °C ; mémoire libre (total − occupé) > 1000 Mo | ☐ | libre : ____ Mo |
| 2 | Fermer l'obturateur : `PAYLOAD_SET_SHUTTER(position=0)` (S8.1 func **119**), `GET_PARAM(param_id=0x063C)` | `payload.shutter_pos` (0x063C) = 0 (CLOSED) | ☐ | |
| 3 | Jeu d'obscurité, depuis STANDBY sans commande de mode (STANDBY arrêterait le refroidisseur) : `PAYLOAD_CAL_LAMP(on=0)` (func **95**), `PAYLOAD_START_CALIBRATION(mode=0)` (func **37**, 0 = DARK), `HK_REQUEST(sid=5)` deux fois, `GET_PARAM(param_id=0x0642)` | `payload.mode` = 3 (CALIBRATION) en 15 s ; `payload.calibration_active` (0x062A) = 1, puis 0 en 120 s ; `payload.cal_abort_reason` (0x0645) = 0 ; `payload.dark_frame_cnt` (0x0642) > 0 | ☐ | images : ____ |
| 3a | Jeu de champs plats : `PAYLOAD_SET_SHUTTER(position=1)`, `PAYLOAD_CAL_LAMP(on=1)`, `GET_PARAM(param_id=0x0615)`, `GET_PARAM(param_id=0x063C)`, `PAYLOAD_START_CALIBRATION(mode=1)` (1 = FLAT), `HK_REQUEST(sid=5)`, `PAYLOAD_CAL_LAMP(on=0)` | `payload.cal_lamp_on` (0x0615) = 1 ; `payload.shutter_pos` = 1 (OPEN) ; `payload.calibration_active` = 0 en 120 s ; `payload.cal_abort_reason` = 0 ; `payload.cal_valid_mask` (0x0646) = 15 — biais et gain sur les quatre bandes | ☐ | masque : ____ |
| 4 | Qualité des images d'obscurité, au sol sur les images transmises : `GET_PARAM(param_id=0x0642)` | signal d'obscurité moyen < 100 DN (12 bits, 0–4095) ; écart type < 10 DN | ☐ | moy. __ σ __ |
| 5 | Ouvrir l'obturateur ; le séquenceur a déjà ramené la charge utile en STANDBY, refroidisseur en marche — aucune commande de mode : `PAYLOAD_SET_SHUTTER(position=1)`, `HK_REQUEST(sid=5)`, `GET_PARAM(param_id=0x063C)` | `payload.mode` = 1 en 15 s ; `payload.shutter_pos` (0x063C) = 1 | ☐ | |
| 6 | Survol du site d'étalonnage : `AOCS_FINE_READY_CHECK` (func 89), puis `AOCS_SET_MODE(mode=5)` (func 0) — FINE_POINT est le mode **5** | `aocs.fine_ready` (0x02C5) = 0 ; `aocs.mode` (0x020F) = 5 en 30 s ; `aocs.att_error` (0x0217) < 0.1° en 300 s | ☐ | survol : ____ |
| 7 | Image du site au survol : `PAYLOAD_SET_MODE(mode=2)` (IMAGING), `PAYLOAD_CAPTURE(scene_id=0, lines=2048)` (func 28) | `payload.mode` = 2 en 30 s ; `payload.last_scene_id` (0x060C, par `GET_PARAM`) incrémenté en 30 s ; heure, position GPS, angle solaire et géométrie de visée consignés | ☐ | scène : ____ |
| 8 | Paire de linéarité : `PAYLOAD_SET_INTEGRATION_TIME(blue_ms=1.00, green_ms=1.00, red_ms=1.00, nir_ms=1.00)` (func 34) et `PAYLOAD_CAPTURE(scene_id=0, lines=2048)` ; puis `PAYLOAD_SET_INTEGRATION_TIME(blue_ms=4.00, green_ms=4.00, red_ms=4.00, nir_ms=4.00)` et une deuxième capture | au sol : la moyenne à demi-intégration vaut environ la moitié de la nominale ; la double environ le double, sans écrêtage à 4095 DN | ☐ | |
| 9 | Revenir à la configuration standard : `PAYLOAD_SET_MODE(mode=1)`, `PAYLOAD_SET_INTEGRATION_TIME(blue_ms=2.00, green_ms=2.00, red_ms=2.00, nir_ms=2.00)`, `AOCS_SET_MODE(mode=4)` | `payload.mode` = 1 en 15 s ; `tcs.cooler_fpa` (0x040C) = 0 (le mode STANDBY arrête le refroidisseur) ; temps d'intégration rétabli ; `aocs.mode` = 4 en 30 s | ☐ | |
| 10 | Données stockées, vidage programmé : `GET_PARAM(param_id=0x0647)`, `GET_PARAM(param_id=0x0648)` | stockage cohérent avec environ 13 images (10 d'obscurité + 3 du site) ; vidage complet réservé au passage suivant | ☐ | |

Un étalonnage terminé consigne aussi l'événement S5 0x060B CALIBRATION_COMPLETE.

**Sortie ?** ☐ oui ☐ non   **GO COM-012 :** ☐

---

# Fiche WB-5.6-C012 — COM-012 Première lumière (confirmer chaque étape)

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | AOCS en FINE_POINT : `AOCS_FINE_READY_CHECK` (func 89) — le masque doit valoir 0, sinon le mode 5 est refusé en TM(1,8) — puis `AOCS_SET_MODE(mode=5)` | `aocs.mode` (0x020F) = 5 en 30 s ; `aocs.total_pointing_err_3sig` (0x02AA) < 0.05° en 300 s (le verrou de capture) ; `aocs.att_error` (0x0217) < 0.1° en 180 s ; `aocs.rate_pitch` (0x0205) ∈ [0.053, 0.073]°/s (vitesse orbitale du suivi du nadir) ; `aocs.rate_yaw` (0x0206) < 0.01°/s | ☐ | |
| 2 | Température du FPA : `GET_PARAM(param_id=0x0601)` (S20.3) | `payload.fpa_temp` (0x0601) ∈ [−16.5, −14.5] °C — `payload.fpa_ready` (0x0610) = 1 dit la même chose | ☐ | T : ____ °C |
| 3 | Charge utile prête, références : `HK_REQUEST(sid=5)`, `GET_PARAM(param_id=0x0604)`, `GET_PARAM(param_id=0x0605)`, `GET_PARAM(param_id=0x060B)` | `payload.mode` (0x0600) = 1 ; `payload.store_used` (0x0604) < 97 % ; `payload.image_count` (0x0605) et `payload.mem_used_mb` (0x060B) consignés | ☐ | nombre __ Mo __ |
| 4 | IMAGING : `PAYLOAD_SET_MODE(mode=2)` (func **26**) | `payload.mode` = 2 (IMAGING) en 30 s | ☐ | |
| 5 | Première capture : `PAYLOAD_CAPTURE(scene_id=1, lines=2048)` (S8.1 func **28**) | `payload.last_scene_id` (0x060C) = 1 en 30 s et `payload.image_count` (0x0605) = 1 en 10 s, tous deux par `GET_PARAM`. 2048 lignes à 244 Hz = 8.4 s ≈ 59 km le long de la trace | ☐ | scène : ____ |
| 6 | Image écrite : `GET_PARAM(param_id=0x0604)`, `GET_PARAM(param_id=0x060B)` | `payload.store_used` (0x0604) en hausse ; `payload.mem_used_mb` (0x060B) en hausse de 1.0–4.0 Mo depuis l'étape 3 (une image : 4 Mo brute, 1.0–2.7 Mo compressée ; 0x060B est le total, seule la différence compte) | ☐ | Δ : ____ Mo |
| 7 | Retour en STANDBY : `PAYLOAD_SET_MODE(mode=1)` | `payload.mode` = 1 en 15 s ; `tcs.cooler_fpa` (0x040C) = 0 en 10 s — le mode STANDBY arrête le refroidisseur | ☐ | |
| 8 | Vidage par le service 13 : `TTC_SET_DOWNLINK_MODE(on=1)`, `TTC_SET_DATA_RATE(rate=1)` (HIGH), `S13_CREATE_TRANSFER(scene_id=1, size_mb=0)`, `S13_REPORT_STATUS(transfer_id=T)`, `S13_END_TRANSFER(transfer_id=T)`, `TTC_SET_DATA_RATE(rate=0)`, `TTC_SET_DOWNLINK_MODE(on=0)` | `ttc.tm_data_rate` (0x0506) = 128000 bit/s ; rapport d'ouverture TM(13,2) — identifiant du transfert, nombre de blocs et CRC-32 consignés ; `payload.transfer_active` (0x062D) = 1, `payload.transfer_progress` (0x062E) en hausse, puis 0x062D = 0 ; retour à 16000 bit/s avec `ttc.downlink_mode` (0x053C) = 0 ; CRC-32 correct au sol | ☐ | heure de réception : ______ |
| 9 | Évaluation de la première lumière : `AOCS_SET_MODE(mode=4)`, `HK_REQUEST(sid=2)`, `HK_REQUEST(sid=5)` | `aocs.mode` = 4 en 30 s ; `payload.mode` = 1 ; `payload.cooler_pwr` (0x0602) = 0 (refroidisseur arrêté à l'étape 7) ; équipe charge utile : géométrie, quatre bandes présentes, aucun artefact, courant d'obscurité ; rapport de première lumière | ☐ | qualité : ____ |

La qualité de l'image et le géoréférencement se notent sur WB-5.6-FL. Une
capture consigne aussi l'événement S5 0x0613 IMAGE_CAPTURED.

**Sortie ?** ☐ oui ☐ non   **Première lumière déclarée ?** ☐ oui ☐ formellement reportée

**En cas de report, justification :** ______________________________________

---

# Fiche WB-5.6-FL — Évaluation de l'image de première lumière

| Champ | Saisie |
|-------|-------|
| ID de l'image | |
| Nom de la cible | |
| Heure UTC d'acquisition | |
| Mode SCAO à l'acquisition | |
| Température du FPA à l'acquisition (°C) | |
| Temps d'intégration par bande (ms), bandes à 443/560/665/865 nm | / / / |
| Taille de l'image (Mo) — attendu 1.0–2.7 stockée (4 brute) | |
| Fauchée au sol (km) — `payload.swath_width_km` (0x0619) | 273 |
| GSD (m) — `payload.gsd_m` (0x0628) | 33,4 |
| DN moyen par bande | |
| Couverture nuageuse (%) | |
| Erreur de géoréférencement (m) — `aocs.geoloc_err_m` (0x02C7) | |
| Verdict de qualité | ☐ exploitable pour la science ☐ limite ☐ à reprendre |
| Bulletin client rédigé ? (responsable de mission) | ☐ oui |

---

# Fiche WB-5.6-MA — Jour 4 : formulaire de traitement d'anomalies multiples

**Usage :** si l'enseignant injecte plus d'une anomalie au cours d'une
série de passages. Une ligne par anomalie ; signée par le FD à la fin de la reprise.

| Anomalie n° | Heure du premier indice | Poste qui l'a signalée | Procédure déclenchée | Durée de reprise (s) | Résultat | Sig. FD |
|-----------|---------------------|--------------------:|-------------------|-------------------|---------|--------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

**Ordre de priorité retenu :** _________________________________

**Conflits rencontrés (la procédure A exige X, la procédure B exige non-X) :**

___________________________________________________________________

**Résolution des conflits :** _________________________________________

---

# Fiche WB-5.6-GO — Jour 4 : grille des critères de la série de passages

**Évaluateur :** ______________   **Série de passages :** ☐ Série 1 (équipe A) ☐ Série 2 (équipe B)

| Critère | ☐ atteint |
|-----------|:----------:|
| Phase passée à COMMISSIONING (5) — `SYS_SET_MISSION_PHASE` (fonction 120) envoyée et vérifiée | ☐ |
| Vérification de l'EPS terminée, sans défaut | ☐ |
| SCAO en NOMINAL (mode 4) atteint, `aocs.att_error` < 1.0° ; FINE_POINT (5) démontré à < 0.1° | ☐ |
| Jeu de règles FDIR vérifié et éprouvé dans le panneau FDIR | ☐ |
| Charge utile sous tension (`eps.pl_payload` 0x0113 = 1, `payload.mode` = 1) | ☐ |
| Refroidisseur du FPA démontré à sa consigne commandée (−15 °C par défaut) dans COM-010, `payload.fpa_ready` (0x0610) = 1, `cooler_margin_k` > 0 | ☐ |
| Image de première lumière acquise ou formellement reportée | ☐ |
| Fiches d'anomalie remplies pour toutes les injections | ☐ |

**Score :** ____ / 8

---

# Fiche WB-5.6-OBS — Jour 4 : fiches d'observation (axes : Équipe + Occupation de l'espace)

### Fiche d'observation — axe Équipe

**Observateur :** _____________

| Élément | Note |
|------|------|
| Chaque poste connaissait-il son rôle ? | |
| Le FD faisait-il autorité ? | |
| Quelqu'un était-il surchargé ou sous-employé ? | |
| Quelqu'un a-t-il fait le travail d'un autre poste ? | |
| La fatigue a-t-elle été gérée (pauses, eau) ? | |
| Comment l'équipe a-t-elle géré les désaccords ? | |

**Points forts :** ________________________   **À améliorer :** _______________________

**Recommandation précise :** _________________________________________

### Fiche d'observation — axe Occupation de l'espace

**Observateur :** _____________

| Élément | Note |
|------|------|
| Disposition des consoles — chaque poste voyait-il ce dont il avait besoin ? | |
| Lignes de vue — le FD voyait-il tous les postes ? | |
| Distractions (téléphones, apartés, musique) ? | |
| Éclairage, température, bruit — des problèmes ? | |
| Déplacements dans la salle (procédures, eau) | |
| Confort physique — chaises, écrans, posture | |

**Points forts :** ________________________   **À améliorer :** _______________________

**Recommandation précise :** _________________________________________

---

# Fiche WB-5.6-HO — Jour 4 : fiche de passation entre passages

(Même format que WB-5.5-HO ; imprimez 9 exemplaires, un par poste de
console.)

### Passation — poste : ______________________

| Champ | Saisie |
|-------|-------|
| Opérateur sortant | |
| Opérateur entrant | |
| Valeurs actuelles des paramètres (3 principaux) | |
| État actuel de la procédure (ID du fichier + étape) | |
| Page de console laissée ouverte pour l'opérateur suivant (page, panneau) | |
| Règles FDIR actuellement actives (acquittées) | |
| Question ouverte pour le quart suivant | |
| Signature du sortant | |
| Signature de l'entrant | |
| Heure | |

---

# Fiche WB-5.6-DB — Jour 4 : réflexion de débriefing après le quart

(Mêmes cinq questions que WB-5.5-DB.)

1. Quelle décision avez-vous prise pendant le quart que, avec le recul,
   vous ne reprendriez pas ? Pourquoi ?

   ___________________________________________________________

2. Quelle décision vous a surpris par son efficacité ?

   ___________________________________________________________

3. Quelle étape de procédure avez-vous eu le plus de mal à exécuter en temps
   réel ?

   ___________________________________________________________

4. Qu'est-ce que l'équipe a mieux fait collectivement que vous ne
   l'attendiez ?

   ___________________________________________________________

5. Quelle chose précise retiendrez-vous pour votre futur travail
   d'ingénieur ?

   ___________________________________________________________

---

# Fiche WB-5.7-SA — Jour 5 : autoévaluation personnelle

**Nom :** _____________________

Pour chaque ligne, attribuez-vous une note de 1–3 (1 = en progression, 2 = compétent,
3 = solide). Soyez honnête — la moyenne de la promotion est de 2,0.

| Ligne | Compétence | Note (1–3) | Éléments probants |
|-----|------------|:-----------:|----------|
| 1 | Discipline de boucle vocale | | |
| 2 | Respect des procédures | | |
| 3 | Interprétation de la télémesure | | |
| 4 | Délai de traitement des anomalies | | |
| 5 | Qualité de la passation | | |
| 6 | Achèvement du tour des postes | | |
| 7 | Qualité du plan de passage (exercice du jour 1) | | |
| 8 | Note au quiz / 15 | | |
| 9 | Contribution au débriefing | | |

**Total :** ____ / 27   **Seuil de mention :** 22

**Les trois choses dont je suis le plus fier cette semaine :**

1. ___________________________________________________________
2. ___________________________________________________________
3. ___________________________________________________________

**Les trois choses sur lesquelles je veux continuer à travailler :**

1. ___________________________________________________________
2. ___________________________________________________________
3. ___________________________________________________________

---

# Fiche WB-5.7-LL — Contribution au retour d'expérience de la promotion

**Nom :** _____________________

Chaque membre de la promotion ajoute au moins trois enseignements au registre
de la promotion. Le registre est lu par la promotion de l'année suivante.

### Enseignement 1

**Titre :** ____________________________________________________

**Ce que nous avons observé :** _________________________________________

**Pourquoi c'est important :** ____________________________________________

**Recommandation :** ___________________________________________

### Enseignement 2

**Titre :** ____________________________________________________

**Ce que nous avons observé :** _________________________________________

**Pourquoi c'est important :** ____________________________________________

**Recommandation :** ___________________________________________

### Enseignement 3

**Titre :** ____________________________________________________

**Ce que nous avons observé :** _________________________________________

**Pourquoi c'est important :** ____________________________________________

**Recommandation :** ___________________________________________

---

# Fiche WB-5.7-WI — Réflexion sur la branche « Et si ? »

Si l'enseignant a fait rejouer une branche, remplissez cette fiche.

**Décision d'origine :** _____________________________________

**Autre décision essayée lors de la reprise :** ____________________

**Ce qui a changé au cours des 15 minutes simulées suivantes :**

___________________________________________________________________

**Quelle décision prendriez-vous la prochaine fois ? Pourquoi ?**

___________________________________________________________________

---

# Fiche WB-5.7-FR — Préparation de la revue finale de mission

La promotion produit un document CFMR (revue finale de mission) de 4–6 pages l'après-midi du jour 5.
Utilisez cette fiche pour rassembler la matière.

### Section 1 — Objectifs de la mission

Les objectifs de la semaine 3 ont-ils été atteints ? (Jour 5, lister chacun avec PASS/FAIL.)

| Objectif | PASS / FAIL | Éléments probants |
|-----------|:-----------:|----------|
| Avoir tenu les 9 postes pendant au moins un passage complet | ☐ / ☐ | |
| Avoir mené un cycle de planification de bout en bout | ☐ / ☐ | |
| Avoir exécuté une procédure nominale en tant que responsable | ☐ / ☐ | |
| Avoir exécuté une procédure de contingence en tant que responsable | ☐ / ☐ | |
| Avoir critiqué le quart d'une équipe de pairs | ☐ / ☐ | |
| Avoir produit une main courante et une fiche d'anomalie | ☐ / ☐ | |

### Section 2 — Synthèse de la télémesure sur la semaine

Les trois paramètres les plus surveillés et leurs valeurs typiques :

1. ___________________________________________________________
2. ___________________________________________________________
3. ___________________________________________________________

### Section 3 — Journal des anomalies

| Date | Anomalie | Procédure | Résultat | Cause première |
|------|---------|-----------|---------|------------|
| Mer. | | | | |
| Mer. | | | | |
| Jeu. | | | | |
| Jeu. | | | | |

### Section 4 — Conformité à l'ECSS-E-ST-70-11C

Cochez chaque clause dont vous pouvez démontrer le respect à partir des
mains courantes et des fiches de la promotion.

| Domaine de clause | ☐ |
|-------------|:-:|
| 5.1 Principes d'opérabilité | ☐ |
| 5.2 Préparation des opérations | ☐ |
| 5.3 Conception des procédures | ☐ |
| 5.4 Gestion des anomalies | ☐ |
| 5.5 Comptes rendus et revue | ☐ |

### Section 5 — Autoévaluation des performances de l'équipage

(Agrégée à partir des fiches WB-5.7-SA de la promotion.)

| Poste | Note moyenne de la promotion (1–3) |
|----------|:-----------------------:|
| FD | |
| SPACON | |
| AOCS | |
| EPS | |
| Thermique | |
| TT&C | |
| Charge utile | |
| FDS | |
| Segment sol | |
| Responsable de mission | |

### Section 6 — Recommandations pour le prochain cycle

1. ___________________________________________________________
2. ___________________________________________________________
3. ___________________________________________________________

---

# Fiche WB-5.7-CE — Évaluation du cours

**Anonyme.** À déposer dans la boîte près de la porte.

| Élément | 1 (médiocre) | 2 | 3 | 4 | 5 (excellent) |
|------|:--------:|:-:|:-:|:-:|:-------------:|
| Structure des séances (lun./mar.) | ☐ | ☐ | ☐ | ☐ | ☐ |
| Réalisme du simulateur (mer./jeu.) | ☐ | ☐ | ☐ | ☐ | ☐ |
| Accompagnement par l'enseignant | ☐ | ☐ | ☐ | ☐ | ☐ |
| Installations du Cyber Range | ☐ | ☐ | ☐ | ☐ | ☐ |
| Utilité du cahier d'exercices | ☐ | ☐ | ☐ | ☐ | ☐ |
| Rythme (trop lent / adapté / trop rapide) | lent ☐ | ☐ | adapté ☐ | ☐ | rapide ☐ |
| Confiance pour assurer dès maintenant un vrai quart | faible ☐ | ☐ | moyenne ☐ | ☐ | élevée ☐ |

**Une chose que vous changeriez pour l'an prochain :**

___________________________________________________________________

___________________________________________________________________

**Une chose que vous garderiez exactement telle quelle :**

___________________________________________________________________

___________________________________________________________________

---

# Annexe WB-A — Contingences à confirmer étape par étape (probables en semaine 3)

Les pages de confirmation des contingences ci-dessous servent de référence : elles figurent dans
ce cahier pour que, si l'enseignant injecte un scénario, l'équipe dispose
d'une page déjà imprimée à suivre en console.

## CTG-001 Délestage sur sous-tension

La FDIR de bord déleste d'elle-même sous 28.4 V (charge utile → refroidisseur
du FPA → `ttc_tx` → roues AOCS → propulsion, une ligne par seconde, événements
0x0106–0x0108). **Vérifier d'abord le satellite** : chaque palier ci-dessous
n'est un GO que si sa ligne est encore sur ON ; si la FDIR l'a déjà ouverte,
ne rien envoyer et passer au contrôle de tension. Un délestage efficace : en
rester à ce palier et passer directement à l'étape 6.

| N° | Responsable | Action | Vérification | ☐ | Note |
|---|-------|--------|--------------|:-:|------|
| 1 | EPS | Détecter et confirmer, et lire ce que la FDIR a déjà délesté : `HK_REQUEST(sid=1)` (S3.27). Le FD autorise ; annoncer « UNDERVOLTAGE — completing load shed from the ground » | `eps.uv_flag` (0x010E) = 1 ; consigner `eps.bus_voltage` (0x0105, attendu < 28.4 V), `eps.bat_soc` (0x0101), `eps.bat_voltage` (0x0100), `eps.power_cons` (0x0106), `eps.power_gen` (0x0107), `eps.eclipse_flag` (0x0108), `eps.load_shed_stage` (0x0134), et `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_ttc_tx` (0x0112), `eps.pl_aocs_wheels` (0x0117) : 1 = encore sur ON, 0 = déjà délestée | ☐ | étage : __ V : __ |
| 2 | EPS | Priorité 1, charge utile sur OFF (ligne de la charge utile encore sur ON) : `PAYLOAD_SET_MODE(mode=0)` (S8.1 func **26**), `HK_REQUEST(sid=5)`, `HK_REQUEST(sid=1)` 30 s plus tard | `payload.mode` (0x0600) = 0 en 10 s ; `eps.power_cons` en baisse ; `eps.bus_voltage` consignée | ☐ | V : ____ |
| 3 | EPS | Priorité 2, refroidisseur du FPA sur OFF (ligne du refroidisseur encore sur ON) : `FPA_COOLER(on=0)` (func **43**), `GET_PARAM(param_id=0x040C)`, `HK_REQUEST(sid=3)`, `HK_REQUEST(sid=1)` 30 s plus tard | `tcs.cooler_fpa` (0x040C) = 0 en 5 s ; `eps.power_cons` en baisse d'environ 15 W ; `eps.bus_voltage` consignée | ☐ | V : ____ |
| 4 | EPS | Priorité 3, émetteur sur OFF (ligne `ttc_tx` encore sur ON) : `TTC_PA_OFF` (func **67**), `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=1)` 30 s plus tard | `ttc.pa_on` (0x0516) = 0 en 5 s ; `eps.power_cons` en baisse d'environ 20 W ; `eps.bus_voltage` consignée. La liaison descendante bande S est perdue ; la liaison montante reste | ☐ | V : ____ |
| 5 | EPS | Priorité 4, ligne des roues sur OFF (encore sur ON) : `EPS_POWER_OFF(line_index=7)` (func **20**), `HK_REQUEST(sid=1)` 30 s plus tard | `eps.pl_aocs_wheels` (0x0117) = 0 en 5 s ; `eps.bus_voltage` consignée. Le contrôle d'attitude actif est perdu | ☐ | V : ____ |
| 5B | EPS | Dernier recours seulement, tous les paliers pris et le bus toujours en baisse — OBC en EMERGENCY : `OBC_SET_MODE(mode=2)` (func **50**), `HK_REQUEST(sid=4)` | `obdh.mode` (0x0300) = 2 en 15 s | ☐ | inutile ☐ |
| 6 | EPS | Surveiller le rétablissement : `HK_REQUEST(sid=1)` toutes les 60 s | `eps.bus_voltage` et `eps.bat_soc` en hausse ; `eps.power_gen` > 0 W au Soleil ; `eps.bat_current` (0x0109) positif (en charge). Rétablir quand le bus > 32.1 V **et** le SoC > 40 % | ☐ | heure : ____ |
| 7 | EPS | Rétablir dans l'ordre de priorité inverse, bus stable 5 min entre deux charges, chaque ligne alimentée avant son équipement : `EPS_POWER_ON(line_index=7)` (+ `AOCS_SET_MODE(mode=2)` seulement si `aocs.mode` (0x020F) = 0) ; `EPS_POWER_ON(line_index=2)` si `eps.pl_ttc_tx` = 0, puis `TTC_PA_ON` ; `EPS_POWER_ON(line_index=4)` si `eps.pl_fpa_cooler` = 0, le refroidisseur lui-même restant ARRÊTÉ (il ne fonctionne que pour préparer une prise de vue ; la commande STANDBY ci-dessous l'arrêterait) ; `EPS_POWER_ON(line_index=3)` si `eps.pl_payload` = 0, puis `PAYLOAD_SET_MODE(mode=1)` | `eps.pl_aocs_wheels` = 1 en 5 s ; après chaque charge, `eps.bus_voltage` > 31.5 V et `eps.bat_soc` > 35 % ; toutes les charges rétablies, bilan de puissance positif | ☐ | |

Avec le PA bande S coupé, **la balise UHF subsiste** : c'est une radio
distincte, et le SID 11 de HK continue d'arriver (page PUS, S3 HK, colonne Observé).
Rien de ce que la FDIR ou cette fiche a coupé ne revient de soi-même : l'étape 7
réalimente chaque ligne explicitement.

## CTG-002 Reprise après anomalie SCAO

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Évaluer l'état de l'AOCS : `HK_REQUEST(sid=2)` (S3.27) | `aocs.mode` (0x020F) et `aocs.att_error` (0x0217) reçus en 5 s — télémesure vivante | ☐ | mode __ err. __ |
| 2 | État des roues : `HK_REQUEST(sid=2)` | `aocs.rw1_speed` … `aocs.rw4_speed` (0x0207–0x020A) à ±6000 tr/min ; `aocs.rw1_temp` … `aocs.rw4_temp` (0x0218–0x021B) < 60 °C. Une roue ≥ 60 °C ou oscillant de plus de ±500 tr/min/s → étape 3 ; toutes nominales → étape 5 | ☐ | roue : ____ |
| 3 | Désactiver la roue défaillante : `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8.1 func **2**) | sa vitesse décroît vers 0 tr/min en 30 s ; `aocs.att_error` jamais au-dessus de 10° | ☐ | N = __ |
| 4 | Désaturer : `AOCS_DESATURATE` (S8.1 func **1**) | roues actives tendant vers 0 tr/min en 120 s ; `aocs.rate_roll`, `aocs.rate_pitch`, `aocs.rate_yaw` (0x0204–0x0206) < 0.5°/s ; moment cinétique < 20 % de la capacité sur chaque roue active | ☐ | |
| 5 | Vitesses angulaires stables : `HK_REQUEST(sid=2)` | `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) < 0.1°/s | ☐ | |
| 6 | Rétablir NOMINAL : `AOCS_SET_MODE(mode=4)` (S8.1 func **0**) | `aocs.mode` = 4 en 10 s ; `aocs.att_error` < 1.0° en 120 s → rétabli ; sinon étape 7 | ☐ | |
| 7 | Escalade en cas de panne de plusieurs roues seulement : `AOCS_SET_MODE(mode=2)` — DETUMBLE | `aocs.mode` = 2 en 5 s ; vitesses tendant vers 0 en 300 s ; pas sous 2.0°/s en 300 s → EMG-001 | ☐ | inutile ☐ |

Il n'existe pas de mode SAFE_POINT ; le mode 1 est SAFE_BOOT, un état de
propagation seule après amorçage, et non une cible de reprise. Une panne de
senseur stellaire relève de CTG-008.

## CTG-007 Anomalie de roue de réaction

EOSAT-1 embarque **quatre** roues en pyramide. Les vitesses sont en LECTURE SEULE
dans `aocs.rw1..rw4_speed` (0x0207–0x020A) ; températures 0x0218–0x021B ;
courants 0x0250–0x0253 ; état des roulements 0x0284–0x0287. La vitesse se
commande avec `RW_SET_SPEED_BIAS` (S8.1 func **8** — le biais est
**ajouté** à la vitesse actuelle) et `AOCS_RW_RAMP_DOWN` (func
**14**, `wheel_idx` 255 = toutes).

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Identifier la roue : `HK_REQUEST(sid=2)` (S3.27) | `aocs.rw1_speed` … `aocs.rw4_speed` (0x0207–0x020A) valeur et vitesse de variation ; `aocs.rw1_temp` … `aocs.rw4_temp` (0x0218–0x021B). Signaler une oscillation de plus de ±500 tr/min/10 s, une vitesse > 6500 tr/min ou une température > 60 °C. Plus d'une roue → CTG-002 étape 7 | ☐ | roue : ____ |
| 2 | La désactiver : `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8.1 func **2**) | sa vitesse commence à décroître en 10 s ; transitoire de `aocs.att_error` (0x0217) ≤ 5° ; `aocs.rate_roll`, `aocs.rate_pitch`, `aocs.rate_yaw` (0x0204–0x0206) < 1.0°/s | ☐ | |
| 3 | Contrôle à trois roues : observer la reconfiguration de l'AOCS — aucune commande | boucle de contrôle reconfigurée en 15 s ; `aocs.att_error` de nouveau sous 2.0° en 60 s ; les trois roues restantes se partagent le moment cinétique | ☐ | |
| 4 | Désaturer les trois : `AOCS_DESATURATE` (S8.1 func **1**) | roues actives vers 0 tr/min sur 120 s, aucune au-dessus de 5000 tr/min ; vitesses < 0.5°/s pendant la manœuvre ; terminé quand chaque roue < 2000 tr/min et les vitesses < 0.2°/s | ☐ | |
| 5 | Pointage stable sur trois roues : `HK_REQUEST(sid=2)` toutes les 60 s pendant 5 min | `aocs.att_error` (0x0217) < 1.5° (assoupli depuis 1.0°) ; `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) < 0.1°/s ; températures des roues actives < 55 °C | ☐ | erreur : ____ ° |
| 6 | NOMINAL sur trois roues : `AOCS_SET_MODE(mode=4)` (S8.1 func **0**) | `aocs.mode` (0x020F) = 4 en 15 s ; `aocs.att_error` < 1.5° en 120 s | ☐ | |
| 7 | Reprise de la roue, tentative autorisée par le sol seulement : `AOCS_ENABLE_WHEEL(wheel_idx=N)` (S8.1 func **3**) | montée en vitesse régulière en 30 s, sans oscillation → contrôle à quatre roues rétabli ; sinon rester sur trois. Surchauffe : la surveiller 2 orbites (récupérable sous 45 °C) ; oscillation : analyse des roulements ; divergence : électronique de pilotage, pas de réactivation sans correctif | ☐ | |

Un sous-ensemble de 3 roues sur 4 engendre toujours R³ : **FINE_POINT fonctionne
toujours** sur trois roues — signalé par `aocs.fine_degraded` (0x0299), et non
refusé.

## CTG-008 Panne du senseur stellaire

EOSAT-1 emporte **deux** senseurs stellaires, ST1 et ST2 — il s'agit d'un
basculement sur redondance, et non de la perte d'une tête unique. Il n'existe pas de
commande `AOCS_EST_SET` ni de nom de source `ss_imu` : la source de
l'estimateur est le masque de bits en lecture seule `aocs.est_source` (**0x02C1** ;
bit0 ST, bit1 CSS, bit2 MAG, bit3 gyro), et la seule commande de
l'estimateur est `AOCS_EST_RESET` (S8.1 func **91**, `mode` 0 = à froid,
1 = à chaud).

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirmer la panne de ST1 : `HK_REQUEST(sid=2)` (S3.27) | `aocs.st1_status` (0x0240) = 4 (FAILED) en 15 s ; `aocs.st1_num_stars` (0x0241) = 0 ; consigner `aocs.mode` (0x020F), `aocs.att_error` (0x0217, peut augmenter) et les vitesses angulaires (0x0204–0x0206) | ☐ | ST1 : __ |
| 2 | Mettre ST2 sous tension : `ST2_POWER(on=1)` (S8.1 func **5**), `HK_REQUEST(sid=2)` | `aocs.st2_status` (0x0243) 0 → 1 (BOOT) en 5 s → 2 (TRACKING) en 60 s ; toujours 1 après 60 s : attendre jusqu'à 120 s au total | ☐ | |
| 3 | Sélectionner ST2 : `ST_SELECT(unit=2)` (S8.1 func **6** ; codage 1 = ST1, 2 = ST2), `HK_REQUEST(sid=2)` 10 s plus tard | `aocs.st2_status` = 2 (TRACKING, stable) en 15 s ; `aocs.att_error` en baisse ; `aocs.mode` dans (ou revenu dans) le mode d'avant la panne | ☐ | |
| 4 | Isoler ST1 : `ST1_POWER(on=0)` (S8.1 func **4**), `HK_REQUEST(sid=2)` | `aocs.st1_num_stars` (0x0241) = 0 en 15 s ; `aocs.att_error` < 0.1° ; `aocs.rate_roll` et `aocs.rate_yaw` < 0.01°/s ; `aocs.rate_pitch` ∈ [0.053, 0.073]°/s (nadir) | ☐ | |
| 5 | Repli, **les deux** senseurs en panne : `AOCS_SET_MODE(mode=3)` COARSE_SUN (S8.1 func **0**), `HK_REQUEST(sid=2)`, `PAYLOAD_SET_MODE(mode=0)` | `aocs.mode` = 3 en 20 s ; `aocs.css_valid` (0x0248) = 1 ; `aocs.css_sun_x` … `aocs.css_sun_z` (0x0245–0x0247) mesurés ; `aocs.att_error` < 5°. Prévenir le FD : pointage fin perdu, aucune prise de vue | ☐ | inutile ☐ |
| 6 | Fin de la procédure : un dernier `HK_REQUEST(sid=2)` | état final de l'AOCS consigné ; panne de ST1 et activation de ST2 dans le rapport d'anomalie | ☐ | |

`ST_SELECT(unit=1)` resélectionnerait sans bruit le ST1 en panne : 0 est
refusé, 1 est ST1, 2 est ST2.

## CTG-009 Dégradation du générateur solaire

Le satellite **signale** une chaîne dégradée (surveillance S12 du
rendement sous 70 % en éclairement : TM(12,9) et événement S5 0x914C pour
A, 0x914D pour B) mais n'agit pas. Mettre ou non la charge utile hors
tension est une décision de l'équipe, prise à la ligne 4 selon la gravité
de la perte. Si personne ne décide et que la batterie se vide, le
délestage sur tension bus coupe la charge utile à 28.4 V : c'est le filet
de sécurité, pas le plan.

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Quantifier la perte : `HK_REQUEST(sid=1)` (S3.27), `GET_PARAM(param_id=0x014C)`, `GET_PARAM(param_id=0x014D)`, `GET_PARAM(param_id=0x014E)` (S20.3) | consigner `eps.sa_a_current` (0x0103), `eps.sa_b_current` (0x0104), `eps.power_gen` (0x0107) ; `eps.sa_a_yield_pct` (0x014C) et `eps.sa_b_yield_pct` (0x014D) sont valides tant que le bit de la chaîne est positionné dans `eps.sa_string_lit` (0x014E) ; `eps.pl_payload` (0x0113) toujours dans l'état où vous l'avez laissée (déjà 0 = le délestage l'a coupée) | ☐ | rendement A __ % B __ % |
| 2 | Comparer les chaînes : `HK_REQUEST(sid=1)` trois fois, à 30 s d'intervalle | rapport `eps.sa_a_current` / `eps.sa_b_current` (nominal 0.9–1.1) : une chaîne dégradée ou les deux | ☐ | rapport : ____ |
| 3 | Écarter l'attitude : `HK_REQUEST(sid=2)` | `aocs.mode` (0x020F) = 4 ou 3 ; `aocs.att_error` (0x0217) < 2.0° ; au-delà de 5° → CTG-002 d'abord | ☐ | |
| 4 | **Décider : délester la charge utile ou poursuivre.** `HK_REQUEST(sid=1)` ; juger la gravité d'après le rendement (ligne 1) et le bilan de puissance ; le FD annonce « PAYLOAD SHED » ou « CONTINUE, MONITORING » | `eps.power_gen` − `eps.power_cons` (0x0106) positif sur l'orbite **et** `eps.bat_soc` (0x0101) extrapolé au-dessus de 25 % en fin de prochaine éclipse → poursuivre (ligne 7) ; sinon délester (ligne 5) | ☐ | DÉLESTER ☐ POURSUIVRE ☐ SoC min __ % |
| 5 | Délester : `PAYLOAD_SET_MODE(mode=1)` (S8.1 func **26**, STANDBY) ; toujours insuffisant : `PAYLOAD_SET_MODE(mode=0)` et, si aucune manœuvre n'est prévue, `HEATER_THRUSTER(on=0)` (func **42**) | `payload.mode` (0x0600) = 1 (ou 0) en 10 s ; `eps.power_cons` en baisse d'au moins 12 W ; marge ≥ 3 W | ☐ | |
| 6 | Attitude optimale au Soleil : `AOCS_SET_MODE(mode=3)` (S8.1 func **0**, COARSE_SUN) | `aocs.mode` = 3 en 15 s ; `eps.sa_a_current`, `eps.sa_b_current` et `eps.power_gen` plus élevés qu'en NOMINAL | ☐ | |
| 7 | Plan de surveillance : `HK_REQUEST(sid=1)` comme nouvelle référence ; un panneau perdu : `GET_PARAM(param_id=0x0144)` | référence de `eps.sa_a_current`, `eps.sa_b_current`, `eps.power_gen`, `eps.bat_soc` consignée ; `eps.wing_status` (0x0144) lu ; tendance quotidienne pendant 7 jours | ☐ | |

## CTG-010 Reprise après chien de garde OBDH

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirmer la réinitialisation par chien de garde : `HK_REQUEST(sid=4)` (S3.27) | `obdh.reboot_count` (0x030A) incrémenté depuis la dernière valeur connue ; consigner `obdh.mode` (0x0300, attendu 0) et `obdh.cpu_load` (0x0302, attendu < 70 %) | ☐ | compteur : ____ |
| 1b | Seulement si `obdh.sw_image` (0x0311) = 0 (chargeur d'amorçage) : `OBC_BOOT_APP` (S8.1 func **55**) — avant tout `HK_ENABLE` ou `OBC_SET_MODE` | S1.1 + S1.7 en 15 s ; `obdh.sw_image` = 1 en 15 s | ☐ | inutile ☐ |
| 2 | État après redémarrage : `HK_REQUEST(sid=4)` | `obdh.mode` (0x0300) = 0 (NOMINAL ; 1 SAFE signifie que la réinitialisation a trouvé un problème — poursuivre avec prudence) ; `obdh.cpu_load` (0x0302) < 70 % | ☐ | |
| 3 | Toutes les données de servitude : `HK_REQUEST` (S3.27) des SID 1, 2, 3, 4, 5, 6 | les six trames en 30 s ; aucun sous-système dans un mode inattendu ou hors limites (sinon → sa fiche CTG) | ☐ | |
| 4 | Temps et intégrité des données : `HK_REQUEST(sid=2)` pour `aocs.gps_fix`, `SET_TIME(cuc_seconds=T_corrected)` (S9.1), `OBC_GPS_TIME_SYNC` (S8.1 func **80**), `HK_REQUEST(sid=4)`, `REQUEST_TIME` (S9.2) | `obdh.time_ref` (0x0A13) ≠ 0 (1 GROUND ou 2 GPS) en 15 s ; T_obc à ±1 s du temps sol ; file des commandes stockées et partitions de la mémoire de masse intactes | ☐ | résidu : ____ s |
| 5 | Indices de cause première : `HK_REQUEST(sid=1)` ; examiner la tendance de `obdh.cpu_load` (0x0302) et les données EPS d'avant la réinitialisation | `eps.bus_voltage` (0x0105) > 30.9 V ; transitoire (SEU, creux bref) → le consigner ; systémique (CPU élevée répétée, erreurs mémoire) → équipe logiciel sol | ☐ | cause : ____ |
| 6 | Rétablir NOMINAL si l'OBC est en SAFE : `OBC_SET_MODE(mode=0)` (S8.1 func **50**) | `obdh.mode` (0x0300) = 0 en 10 s ; `obdh.cpu_load` < 70 % ; `aocs.mode` (0x020F) non perturbé | ☐ | inutile ☐ |

Une réinitialisation qui passe par le chargeur d'amorçage réapplique
`default_enabled_sids: [1, 11]` à l'amorçage applicatif : tous les autres SID
sont de nouveau désactivés tant qu'on ne les réactive pas avec `HK_ENABLE` (S3.5).

## CTG-012 Traitement d'une surintensité

Les indices de ligne vont de **0 à 8** : 0 `obc`, 1 `ttc_rx`, 2 `ttc_tx`,
3 `payload`, 4 `fpa_cooler`, 5 `htr_bat`, 6 `htr_obc`,
7 `aocs_wheels`, 8 `prop`.

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Identifier la ou les lignes déclenchées : `HK_REQUEST(sid=1)` (S3.27) | `eps.oc_trip_flags` (0x010D) décodé : bit N = ligne N (les bits 0–1 sont les lignes non commutables `obc` et `ttc_rx`) | ☐ | ligne : ____ |
| 2 | Courant de chaque ligne : `HK_REQUEST(sid=1)` | courant de la ligne déclenchée (0x0118–0x011F) proche de 0 A — le LCL l'a ouverte ; toujours élevé = défaut persistant : ne PAS réactiver, escalader. État de ligne (0x0110–0x0117) sur OFF ; `eps.bus_voltage` (0x0105) > 30.9 V | ☐ | I : ____ A |
| 3 | Isoler le défaut — se coordonner avec la position du sous-système concerné (TT&C, charge utile, EPS/TCS, AOCS) : état connu avant le déclenchement ? appel de courant lors d'un changement de mode ou d'une mise sous tension ? | transitoire probable → étape 4 ; dommage matériel soupçonné → HOLD et escalader | ☐ | |
| 4 | Réinitialiser l'indicateur de surintensité : `EPS_RESET_OC_FLAG(line_index=N)` (S8.1 func **21**) | bit de la ligne dans `eps.oc_trip_flags` (0x010D) à zéro, et toujours à zéro 5 s plus tard | ☐ | |
| 5 | Réactiver la ligne : `EPS_POWER_ON(line_index=N)` (S8.1 func **19**) | état de ligne (0x0110 + N) = 1 en 5 s ; courant de ligne (0x0118 + N) revenu au nominal ; `eps.oc_trip_flags` toujours à zéro après 30 s | ☐ | |
| 6 | Reprise en aval : `HK_REQUEST` du SID du propriétaire (2 AOCS, 5 charge utile, 6 TT&C, 3 réchauffeurs) et `HK_REQUEST(sid=1)` | le sous-système fonctionne de nouveau ; `eps.power_cons` (0x0106) reflète la charge ; `eps.bus_voltage` > 30.9 V | ☐ | |

Le LCL a normalement ouvert la ligne avant que quiconque voie le déclenchement :
cette fiche n'a jamais à couper une ligne déclenchée, seulement à décider si
elle peut revenir.

## CTG-015 Reprise après image corrompue

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Détecter et quantifier : `HK_REQUEST(sid=5)` (S3.27) | écart de `payload.checksum_errors` (0x0609) par rapport à la référence ; `payload.last_scene_id` (0x060C) — la scène touchée ; aperçu sol de son dernier produit : lignes manquantes, traînées, blocs corrompus ? ; `payload.image_count` (0x0605) consigné | ☐ | Δ erreurs : ____ |
| 2 | Contrôle du FPA : `HK_REQUEST(sid=5)`, `HK_REQUEST(sid=3)` | `payload.fpa_temp` (0x0601) consignée et recoupée avec `tcs.temp_fpa` (0x0408) ; `payload.fpa_ready` (0x0610) = 1 ? ; `tcs.cooler_fpa` (0x040C) = 1 ? FPA chaud (non prêt) → étape 3 ; froid et prêt → étape 4 | ☐ | T : ____ °C |
| 3 | FPA chaud — interrompre et refroidir : `PAYLOAD_SET_MODE(mode=1)` (S8.1 func **26**), `FPA_COOLER(on=1)` (func **43**), `GET_PARAM(param_id=0x040C)`, `HK_REQUEST(sid=5)` toutes les 60 s, `HK_REQUEST(sid=3)` | `payload.mode` (0x0600) = 1 en 10 s ; `tcs.cooler_fpa` (0x040C) = 1 en 5 s ; `payload.fpa_temp` en baisse jusqu'à `payload.fpa_ready` = 1 → étape 5 | ☐ | |
| 4 | Segments mémoire : `HK_REQUEST(sid=5)` | `payload.mem_segments_bad` (0x0612) et `payload.store_used` (0x0604) consignés. > 0 → CTG-016 marque d'abord le segment défectueux ; 0 avec un FPA froid → transitoire (SEU) → étape 5 | ☐ | segments : ____ |
| 5 | Supprimer et acquérir de nouveau : `PAYLOAD_DELETE_IMAGE(scene_id=N)` (func **30**), puis `PAYLOAD_CAPTURE(scene_id=N, lines=L)` (func **28**) — seulement avec `payload.fpa_ready` = 1, aucun segment défectueux non marqué et `aocs.att_error` (0x0217) < 0.1° | suppression : `payload.store_used` en baisse, `payload.image_count` (0x0605) −1 ; capture : `payload.image_count` +1 ; `payload.checksum_errors` (0x0609) n'augmente pas | ☐ | nouvelle scène : ____ |
| 6 | Vérification après acquisition : `HK_REQUEST(sid=5)` | `payload.checksum_errors` sans nouvelle hausse ; au sol, le CRC32 du nouveau produit concorde avec le rapport de transfert de bord et l'aperçu est propre ; `payload.store_used` dans la capacité. Consigner scène, nombre d'erreurs, cause première (thermique / mémoire / transitoire) et résultat | ☐ | cause : ____ |

La fiche part en général de l'événement S5 0x0607 IMAGE_CHECKSUM_ERROR. Juger si
le FPA était chaud d'après l'indicateur de disponibilité `payload.fpa_ready`,
et non d'après une température retenue de mémoire.

## CTG-017 Basculement sur panne de bus

Basculer de **bus** et basculer d'**unité OBC** sont deux
commandes différentes. `OBC_SELECT_BUS` (func 54) change de bus CAN ;
`OBC_SWITCH_UNIT` (func 53) bascule sur l'OBC redondant et relève de
CTG-011, pas de cette carte.

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Détecter l'absence de données de servitude : `HK_REQUEST` (S3.27) des SID 1, 2, 3, 4, 5, 6 | quels SID répondent et lesquels manquent ; absence pour plusieurs sous-systèmes → étape 2 | ☐ | manquants : ____ |
| 2 | État des bus : `HK_REQUEST(sid=4)` | `obdh.bus_a_status` (0x030F), `obdh.bus_b_status` (0x0310) (0 OK, 1 ERROR) et `obdh.active_bus` (0x030E) (0 A, 1 B) consignés. Bus actif en ERROR → basculer ; les deux OK → examiner plutôt les sous-systèmes | ☐ | A __ B __ actif __ |
| 3 | Basculer de bus : `OBC_SELECT_BUS(bus=1)` de A vers B, ou `OBC_SELECT_BUS(bus=0)` de B vers A (S8.1 func_id **54**) ; `HK_REQUEST(sid=4)` 15 s plus tard | `obdh.active_bus` (0x030E) indique le nouveau bus ; `obdh.bus_a_status` et `obdh.bus_b_status` consignés | ☐ | |
| 4 | Vérifier la reprise de toutes les données de servitude : `HK_REQUEST` des SID 1–6 de nouveau | chaque SID répond en 15 s ; valeurs cohérentes (ni valeurs figées, ni zéros) ; `eps.bat_soc` (0x0101) et `eps.bus_voltage` (0x0105) consignés ; `aocs.mode` (0x020F) et `payload.mode` (0x0600) inchangés ; `obdh.cpu_load` (0x0302) non élevée ; annoncer « ALL HK RESTORED » | ☐ | |
| 5 | Évaluation post-basculement : consigner l'heure de la perte des HK, le bus en panne, la durée de l'interruption, les sous-systèmes touchés et le nouveau bus ; rester sur le nouveau bus — pas de retour sans approbation ni essais de l'ingénierie | bus en panne consigné pour l'ingénierie | ☐ | |

Après un basculement, il ne reste **plus aucune redondance de bus** tant que
l'ingénierie n'a pas requalifié le bus en panne.

## CTG-019 Absence de télémesure en début de passage

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirmer que la station sol est nominale : poursuite de l'antenne avec un pointage valide, émetteur montant sur la bonne fréquence et la bonne polarisation, précompensation Doppler, ni brouillage local ni météo, récepteur sur la fréquence descendante attendue | sol nominal → diagnostic côté satellite | ☐ | |
| 2 | `HK_REQUEST(sid=1)` en aveugle (S3.27) ; attendre 30 s. Toute TC acceptée alimente aussi la ligne `ttc_tx` pendant 300 s (maintien d'émission automatique) : cette demande est donc le test | télémesure revenue → en lire la raison (`eps.pl_ttc_tx` (0x0112), `ttc.pa_on` (0x0516), événements EPS), continuer à commander, étape 6 ; rien → la ligne est hors de cause, étape 3 (étape 4 si la balise UHF, SID 11, lit `ttc.pa_on` (0x0516) = 0) | ☐ | |
| 3 | Basculement de transpondeur, en aveugle : `TTC_SWITCH_REDUNDANT` (func **64**), attendre 45 s ; puis `TTC_SWITCH_PRIMARY` (func **63**). Redondance froide : un principal en panne ne l'entend pas (seul le temporisateur de 24 h bascule, étape 7) | porteuse sur la fréquence de l'équipement redondant → étape 6 ; aucun des deux → étape 4 | ☐ | |
| 4 | PA en marche, en aveugle : `TTC_PA_ON` (func **66**), attendre 15 s ; toujours rien : `TTC_PA_OFF` (func **67**), 10 s, `TTC_PA_ON`, 15 s | porteuse descendante après le PA ON → étape 6 ; toujours rien → étape 5 | ☐ | |
| 5 | Antenne, seulement si son déploiement est incertain ou si elle est connue repliée : `TTC_DEPLOY_ANTENNA` (func **69**) — fil thermofusible irréversible ; attendre 30 s | avec de la TM : `ttc.antenna_deployed` (0x0520) = 1 et `ttc.antenna_deployment_sensor` (0x0536) = 2 ; signal plus fort de 15–25 dB (`ttc.antenna_deployment_ready` (0x0535) = 0 auparavant signale un défaut de continuité pyrotechnique : la commande ne se déclenchera pas). Signal → étape 6 ; rien → étape 7 | ☐ | |
| 6 | Vérifier la qualité de la liaison et la santé des sous-systèmes : `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` | `ttc.link_status` (0x0501) = 2 ; page TT&C (sol) : `ttc.rssi` (0x0502) > −126 dBm, `ttc.link_margin` (0x0503) > 3.0 dB ; `ttc.pa_on` (0x0516) = 1 ; `ttc.pa_temp` (0x050F) < 55 °C ; `ttc.antenna_deployed` = 1 ; `ttc.carrier_lock` (0x0510) = 1 ; `ttc.bit_sync` (0x0511) = 1 ; page radio : `ttc.eb_n0` (0x0519) > 10 dB ; `eps.bus_voltage` (0x0105) > 30.9 V ; `eps.pl_ttc_tx` (0x0112) = 1 ; `obdh.mode` (0x0300) ni SAFE ni EMERGENCY | ☐ | rétablie à l'étape : ____ |
| 7 | Escalade, pas de liaison : `TTC_SET_TX_POWER(level=2)` (S8.1 func **68**) pour la tentative suivante ; consigner chaque commande en aveugle avec son heure ; prévenir le FD et le directeur de mission ; réserver le passage suivant | sans liaison après deux passages consécutifs → **EMG-004** (Perte de communication) | ☐ | |

La balise UHF est une **radio distincte** : si le SID 11 de HK arrive toujours
alors que la bande S est muette (page PUS, S3 HK, colonne Observé), la panne se situe
dans la chaîne bande S, pas dans l'OBC. La seule autonomie de bord face à une
liaison muette est la minuterie de perte de commande : elle bascule sur l'autre
transpondeur 24 h après la dernière télécommande acceptée, puis toutes les 24 h
suivantes (CTG-003 étape 6).

## CTG-020 Panne d'antenne de station sol

CTG-020 est une fiche **consultative** (`advisory: true` dans
`procedure_index.yaml`) — elle n'est pas exécutable par la machine et ne
contient **aucune télécommande vers le satellite**. Il s'agit d'une panne du segment
sol : tout se fait côté sol. N'envoyez aucune commande au
satellite pour la traiter.

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirmer que la perte du signal ne vient pas du satellite. Dernière trame avant la perte : `ttc.rssi` (0x0502) nominal, `ttc.link_margin` (0x0503) > 3 dB, `ttc.pa_on` (0x0516) = 1, `ttc.pa_temp` (0x050F) < 55 °C. Une chute brutale au plancher de bruit = matériel. Contrôler la poursuite de l'antenne, le LNA, le convertisseur abaisseur, la FI et la bande de base | panne de matériel sol confirmée ou fortement soupçonnée → étape 2 ; côté satellite soupçonné → CTG-019 ou CTG-003 | ☐ | |
| 2 | Tenter un rétablissement local de la station sol : réinitialisation du contrôleur d'antenne ou réacquisition de la poursuite ; LNA de secours, câbles, alimentations — jusqu'à 2 min | station rétablie → reprendre et consigner ; pas rétablie en 2 min → étape 3 | ☐ | résultat : ______ |
| 3 | Informer le directeur de vol et évaluer l'impact : « GS [station] antenna failure at [time] ; spacecraft healthy and transmitting ; ground cannot receive » ; temps de passage restant, commandes en attente, données urgentes, opérations à échéance | opérations critiques en attente → étape 4 tout de suite ; sinon → étape 5 | ☐ | |
| 4 | Coordonner une station sol de secours (le FD autorise) : prochaines fenêtres aux autres stations du réseau, réservation prioritaire, éléments orbitaux et plan de fréquences, configuration montante et descendante conforme | station de secours coordonnée — ou aucune disponible et le satellite en sécurité de lui-même | ☐ | station : ______ |
| 5 | Replanifier le programme des contacts : retirer la station en panne jusqu'à sa réparation, ajouter des passages de secours, évaluer le temps de contact sur 24–48 h et les plans de bord de prise de vue, de batterie et de stockage ; prévenir l'ingénierie ; consigner l'incident | programme replanifié, incident consigné | ☐ | |

L'état du côté sol se lit dans la surveillance propre de la station (la vue radio et
l'opérateur de la station), pas dans la télémesure du satellite ; un satellite sain
continue d'émettre tout du long.

---

# Annexe WB-B — Main courante de clôture de la semaine (exemplaire de la promotion)

**Usage :** remplie par le FD à la fin de chaque quart. Une feuille par
quart. Versée aux archives de la promotion.

| Champ | Saisie |
|-------|-------|
| Date du quart | |
| FD du quart | |
| Équipe | ☐ Borealis ☐ Austral |
| Passage(s) couvert(s) | |
| Procédures exécutées | |
| Anomalies (nombre + ID des fiches) | |
| Règles FDIR déclenchées | |
| Issue du GO/NO-GO | |
| Engagements client (réservations du planificateur) tenus / reportés | |
| Synthèse en une ligne pour les archives de la promotion | |
| Signature du FD | |

---

# Annexe WB-C — Autocontrôle du cahier

À la fin de la semaine 3, le cahier doit contenir :

- ☐ WB-5.0 vérification des acquis préalables (remplie avant lundi)
- ☐ WB-5.1 sept cartes de score par poste (une par console MCS)
- ☐ WB-5.3-PP résultat de l'exercice de plan de passage
- ☐ WB-5.4-VL réponses à l'exercice de boucle vocale
- ☐ WB-5.4-N001 NOM-001 à confirmer étape par étape (une par passage)
- ☐ WB-5.4-C003 CTG-003 à confirmer étape par étape (si déclenchée)
- ☐ WB-5.4-N012 passation NOM-012 (une par passation)
- ☐ WB-5.4-FD résultat de l'atelier de dynamique du vol
- ☐ WB-5.4-Q feuille de réponses du quiz (corrigée)
- ☐ WB-5.5-PB liste de vérification du briefing avant passage LEOP (une par passage)
- ☐ WB-5.5-L001 / -L006 / -L002 / -L007 / -L005 à confirmer étape par étape (une de chaque par passage exploité)
- ☐ WB-5.5-AT fiches d'anomalie (≥ 1 par passage exploité)
- ☐ WB-5.5-GO grille de fin de passage
- ☐ WB-5.5-OBS fiche d'observation (une par passage observé)
- ☐ WB-5.5-HO passation entre passages (une par poste)
- ☐ WB-5.5-DB réflexion de débriefing
- ☐ WB-5.6-PB briefing avant la série de passages
- ☐ WB-5.6-C001 à WB-5.6-C012 à confirmer étape par étape (une de chaque)
- ☐ WB-5.6-FPA fiche de suivi de la mise en froid
- ☐ WB-5.6-FL évaluation de la première lumière
- ☐ WB-5.6-MA formulaire d'anomalies multiples (le cas échéant)
- ☐ WB-5.6-GO grille de la série de passages
- ☐ WB-5.6-OBS fiche d'observation
- ☐ WB-5.6-HO passation entre passages
- ☐ WB-5.6-DB réflexion de débriefing
- ☐ WB-5.7-SA autoévaluation personnelle
- ☐ WB-5.7-LL ≥ 3 contributions au retour d'expérience de la promotion
- ☐ WB-5.7-WI réflexion « Et si ? » (si une branche a été rejouée)
- ☐ WB-5.7-FR préparation de la revue finale de mission (exemplaire de la promotion)
- ☐ WB-5.7-CE évaluation du cours (anonyme ; dans la boîte)
- ☐ WB-A pages de contingence à confirmer étape par étape, utilisées au besoin
- ☐ WB-B main courante par quart

**Signature du FD à la fin de la semaine 3 :** _______________________

**Cahier remis à l'enseignant :** ____ : ____ (UTC)
