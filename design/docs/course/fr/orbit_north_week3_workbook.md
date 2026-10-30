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

- **Tâche :** conduire un tour de table GO/NO-GO sur le tableau de bord en direct. Interroger trois
  postes pour un *go for* `CONNECTION_TEST` (S17.1) — ce satellite n'a ni commande NOOP
  ni commande de battement de cœur ; consigner les réponses.
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
  prédire s'il saturera à la prochaine éclipse.
- **SoC à l'entrée en éclipse :** ____ %   **Durée de l'éclipse :** ____ min
  (33,2 à 35,2 min sur l'année)
- **SoC prédit en sortie :** ____ %   **(Méthode :** P_avg × t / E_batt,
  avec E_batt = **100 Wh** et une charge nominale moyenne sur l'orbite
  P_avg ≈ **28,8 W** **)**
- **Comparaison avec le modèle d'éclipse :** ☐ concorde  ☐ écart de ____ %
- **Réchauffeur au rapport cyclique le plus élevé :** _______________   **Rapport cyclique :** ____ %
- **Rapport cyclique prédit à la prochaine éclipse :** ____ %   **Saturera-t-il ?** ☐ oui ☐ non
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

## 5.1.3 Dynamique du vol

- **Tâche :** lire `aocs.att_error` (0x0217) et vérifier qu'elle respecte
  le bilan du mode NOMINAL (mode 4, suivi du nadir), soit < 1.0°. En
  FINE_POINT (mode 5), le bilan est < 0.1°. Calculer ensuite l'AOS, le TCA
  et le LOS du prochain passage d'Iqaluit et les comparer avec le planning
  des contacts du MPS.
- **Lecture :** ______ °   **Dans la plage ?** ☐ oui  ☐ non
- **Mode SCAO (`aocs.mode` 0x020F) :** ____ (0 OFF, 1 SAFE_BOOT,
  2 DETUMBLE, 3 COARSE_SUN, 4 NOMINAL, 5 FINE_POINT, 6 SLEW,
  7 DESAT, 8 ECLIPSE, 9 INERTIAL)
- **État des senseurs stellaires** (`aocs.st1_status` 0x0240 / `aocs.st2_status`
  0x0243 ; 0=éteint, 1=amorçage, 2=poursuite, 3=aveuglé, 4=en panne) :
  ST1 ____  ST2 ____   **Sélectionné** (`aocs.st_selected` 0x0244) : ____
- **Prochain passage d'Iqaluit :** AOS ______ TCA ______ LOS ______ él. max ____ °
- **Concordance avec le MPS :** ☐ exacte  ☐ écart < 5 s  ☐ écart > 5 s
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

## 5.1.4 TT&C

- **Tâche :** parcourir l'échelle de débits TM à l'AOS et confirmer quelle station
  sol assure le passage. L'échelle comporte trois
  échelons — **BEACON 1 kbit/s / LOW 16 kbit/s / HIGH 128 kbit/s**
  (`ttc.tm_data_rate` 0x0506 en bit/s, `ttc.tm_tier` 0x0539 =
  0/1/2). LOW est l'échelon des opérations de routine ; HIGH est réservé aux vidages
  et exige le mode DOWNLINK activé (func 79) ainsi qu'une élévation ≥ 10°.
  BEACON ne peut pas être sélectionné avec `TTC_SET_DATA_RATE` (S8 func 65).
  EOSAT-1 utilise le référentiel pédagogique à **cinq stations** (`orbit.yaml`).
- **Débit de la balise (kbit/s) :** ______   **Débit LOW de routine (kbit/s) :** ______
  **Débit HIGH de vidage (kbit/s) :** ______
- **Marge de liaison après la transition (dB) :** ______ (`ttc.link_margin` 0x0503)
- **Lecture du TEB (`ttc.ber` 0x050C, log10) :** ____________________
- **Station active (`ttc.active_gs` 0x0523) :** ______  ☐ Iqaluit
  ☐ Troll ☐ Svalbard ☐ Inuvik ☐ O'Higgins
- **Configuration de la bande de base (débit, codage) :** ______________________
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

## 5.1.5 Opérations charge utile

- **Tâche :** programmer une séance de prise de vue via le MPS. Confirmer que la température
  du FPA est à la consigne avant d'envoyer la commande.
- **Cible de prise de vue choisie :** _______________________________
- **Lecture de la température du FPA (`payload.fpa_temp` 0x0601, °C) :** ______
  **À la consigne ?** ☐ oui ☐ non — la condition est `payload.fpa_ready`
  (0x0610) = 1, et non une température retenue de mémoire. Consigne par défaut
  **−15 °C** (`payload.fpa_setpoint` 0x0631 ; enveloppe commandable
  de −20 °C à 0 °C).
- **Occupation du stockage (`payload.mem_used_mb` 0x060B) :** ______ / 20 000 Mo
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

## 5.1.6 FDIR / systèmes

- **Tâche :** présenter une règle FDIR dans le panneau FDIR ; expliquer
  son déclencheur, son seuil, sa gravité et la procédure de contingence
  à laquelle elle renvoie.
- **Nom de la règle choisie :** _____________________________
- **Paramètre déclencheur :** _____________________________
- **Seuil :** ___________________   **Persistance :** _________
- **Gravité :** ____   **Procédure recommandée :** ________________
- **Enseignement :** _________________________________________________
- **Question à poser :** _________________________________________

## 5.1.7 Propulsion

- **Tâche :** sans envoyer aucune commande, lire l'état de la propulsion et
  nommer le verrouillage qui empêche actuellement l'armement. Fiche de rôle :
  `configs/eosat1/mcs/role_analysis/propulsion_role.md`.
- **État (`prop.state` 0x0B00 ; 0 SAFED, 1 ARMED, 2 FIRING,
  3 INHIBIT) :** ____
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
| 1 | Segment sol | Confirmer que la station programmée est en poursuite | station = TRACKING dans le MPS (réseau de cinq stations) | ☐ | |
| 2 | TT&C | Vérifier que la chaîne bande S émet | `ttc.pa_on` (0x0516) = 1 et `ttc.tx_active` (0x0525) = 1 avant AOS-2 min ; si 0, lire `ttc.tx_gate_status` (0x052B) | ☐ | |
| 3 | TT&C | À l'AOS, vérifier l'accrochage de la liaison | `ttc.link_status` (0x0501) = **2** (LOCKED) dans les 30 s suivant l'AOS ; `ttc.carrier_lock` (0x0510) = 1 | ☐ | |
| 4 | SPACON | Envoyer `CONNECTION_TEST` (S17.1) | Acquittement S1.1 + rapport S17.2 reçus | ☐ | |
| 5 | SPACON | Vérifier que la HK complète est émise | SID 1, 2, 3, 4, 5, 6 périodiques (seuls 1 EPS et 11 balise sont actifs à la mise sous tension — les autres nécessitent `HK_ENABLE`, S3.5) ; les lectures à la demande utilisent `HK_REQUEST`, **S3.27** | ☐ | |
| 6 | AOCS | Confirmer le mode et les vitesses du SCAO | `aocs.mode` (0x020F) = **4** (NOMINAL, suivi du nadir) ; `aocs.rate_roll`/`rate_yaw` (0x0204/0x0206) < 0.05°/s, `aocs.rate_pitch` (0x0205) ≈ −0.063 ± 0.02°/s (vitesse de suivi du nadir) | ☐ | |
| 7 | EPS | Confirmer l'état de la batterie et du bus | `eps.bat_soc` (0x0101) > 50 %, `eps.bus_voltage` (0x0105) > 27.0 V (plage nominale 26–30 V ; sous-tension FDIR à **24.5 V**) | ☐ | |
| 8 | Thermique | Confirmer que les zones sont dans la plage | Toutes les zones au vert | ☐ | |
| 9 | Charge utile | Confirmer que l'état de la charge utile correspond au plan | mode = conforme au plan | ☐ | |
| 10 | SPACON | Consigner le début du passage dans la main courante | Entrée créée | ☐ | |

**Éléments hors nominal observés :** __________________________________

___________________________________________________________________

**Signature du FD :** ________________   **Heure de fin :** _________

---

# Fiche WB-5.4-C003 — CTG-003 Rétablissement après perte de liaison TTC (confirmer chaque étape)

**Opérateur :** ___________________   **Heure de déclenchement :** _________

| N° | Responsable | Action | Vérification attendue | ☐ fait | Note / valeur réelle |
|---|-------|--------|----------------------|:------:|---------------------|
| 1 | TT&C | Confirmer la perte de liaison sur `ttc.link_status` (0x0501) et `ttc.frame_sync` (0x0512) | link_status ≠ 2, synchronisation trame perdue | ☐ | |
| 2 | Segment sol | Vérifier que la station sol est toujours en poursuite | Pointage de l'antenne correct, bande de base nominale | ☐ | |
| 3 | SPACON | Ouvrir le panneau FDIR ; identifier la règle déclenchée | règle + `fdir.level` (0x0700) consignés | ☐ | |
| 4 | TT&C | Envoyer en aveugle `HK_REQUEST(sid=6)` (S3.27), puis `CONNECTION_TEST` (S17.1) | S'il répond, aller à l'étape 8 | ☐ | |
| 5 | TT&C | Si l'étape 4 échoue, envoyer en aveugle `TTC_SWITCH_REDUNDANT` (S8 func 64), puis `TTC_SWITCH_PRIMARY` (func 63) | `ttc.link_status` = 2 dans les 45 s | ☐ | |
| 6 | TT&C | Une fois accroché, vérifier la qualité de la liaison et la santé des sous-systèmes : `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` (S3.27) | RSSI (0x0502) > −90 dBm ; marge (0x0503) > 3.0 dB ; bus > 27.0 V ; consigner le transpondeur actif (`ttc.mode` 0x0500) | ☐ | |
| 7 | TT&C | Si le silence persiste après les deux transpondeurs : consigner chaque commande en aveugle, prévenir le directeur de mission et le FDS, réserver le passage suivant | minuterie d'absence de contact de 24 h confirmée en marche | ☐ | |
| 8 | SPACON | Acquitter la règle FDIR, consigner les actions de reprise | FDIR effacée, entrée au journal | ☐ | |
| 9 | TT&C | Remplir une fiche d'anomalie. Sans liaison après deux passages consécutifs, passer à **EMG-004** Perte de communication | Fiche consignée | ☐ | |

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
| 6 | Engagements client en cours | | |
| 7 | **Autorisations GO en suspens** | | ☐ |
| 8 | Ambiance sur la boucle vocale (équipe reposée / tendue / etc.) | | |

**Fin de la passation :** _________   **Durée :** ____ : ____ (objectif < 6:00)

**Les deux FD signent ci-dessous pour attester que la passation est terminée.**

Sortant : ____________________  Entrant : ____________________

---

# Fiche WB-5.4-FD — Jour 2 : atelier de dynamique du vol

**Opérateur :** ___________________

### Exercice 1 — Prédire les trois prochaines heures d'AOS

Outil : `python3 tools/orbit_tools.py predict --hours 24`. Comparer
avec le planning des contacts du MPS.

| Passage | Station | AOS (votre prédiction, UTC) | AOS (MPS, UTC) | Δ (s) |
|------|---------|---------------------------|----------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

### Exercice 2 — Durée du passage en fonction de l'élévation maximale

| Passage | Él. max (°) | Durée prédite (min) | Durée réelle d'après le MPS (min) |
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
| `pass_override = 1` confirmé (param 0x05FF) | ☐ |
| Le FD a chargé le jeu de procédures LEOP dans le panneau de procédures | ☐ |
| SPACON a passé en revue le jeu de règles FDIR dans le panneau FDIR (il n'existe **aucune** télécommande de chargement de table FDIR — le jeu de règles est `subsystems/fdir.yaml` + `monitoring/`) | ☐ |
| L'AOCS a passé en revue les vitesses de culbutage résiduelles (environ 1–2 °/s par axe dues à l'impulsion de séparation) | ☐ |
| L'EPS confirme un SoC d'environ 90 % (`eps.bat_soc` 0x0101) ; seules les lignes non commutables `obc` (ligne 0) et `ttc_rx` (ligne 1) sont sur ON — toutes les lignes commutables sont sur OFF par défaut | ☐ |
| Le TT&C a confirmé la réception de la balise UHF (`ttc.beacon_active` 0x0527 = 1) ; noter que la balise est une radio distincte de la chaîne principale bande S | ☐ |
| Le segment sol a confirmé que l'antenne d'Iqaluit est sur la cible, démodulateur sur le échelon **BEACON** (1 000 bit/s, BPSK, conv(7,1/2)+RS, 1 kBd) | ☐ |
| La FDS a produit le planning des passages sur 24 h et l'a remis au FD, au TT&C et au segment sol | ☐ |
| Formulaires de fiche d'anomalie imprimés vierges et disponibles à chaque console | ☐ |
| Langue de la boucle vocale déclarée (annonces en anglais) | ☐ |

**Annonce « prêt » du FD (mot pour mot) :** ________________________________

**Début du passage (UTC) :** _____________

---

# Fiche WB-5.5-L001 — LEOP-001 Première acquisition du signal et amorçage de l'OBC (confirmer chaque étape)

**Opérateur (responsable TT&C) :** ___________________   **Début du passage :** ________

| N° | Responsable | Action | Vérification attendue | ☐ fait | Note réelle |
|---|-------|--------|----------------------|:------:|-------------|
| 1 | Segment sol | Configurer le récepteur de la station sur le barreau BEACON ; forcer le passage dans le MCS | GS = TRACKING_READY ; `pass_override = 1` (0x05FF) | ☐ | |
| 2 | TT&C | Envoyer la première TC montante : `CONNECTION_TEST` (S17.1) | Acquittement S1.1 < 10 s ; S17.2 < 10 s ; `eps.pl_ttc_tx` (0x0112) = 1 (maintien automatique de l'émetteur armé) | ☐ | |
| 3 | TT&C | Vérifier l'accrochage de la porteuse et la qualité de la liaison | `ttc.link_status` (0x0501) = **2** (LOCKED) < 30 s ; `ttc.rssi` (0x0502) > −110 dBm ; `ttc.link_margin` (0x0503) > 3 dB | ☐ | |
| 4 | SPACON | Demander le SID balise : `HK_REQUEST(sid=11)` (**S3.27**) | Balise reçue ; `obdh.sw_image` (0x0311) = 0 (BOOTLOADER) < 10 s | ☐ | |
| 5 | SPACON | Amorcer l'OBC sur l'applicatif : `OBC_BOOT_APP` (S8.1 func_id 55) | Acquittements S1.1 + S1.7 < 5 s ; `obdh.sw_image` = 1 < 15 s. L'amorçage réapplique `default_enabled_sids: [1, 11]` — **seuls les SID 1 et 11 sont émis** | ☐ | |
| 5a | SPACON | Activer les SID de plateforme : `HK_ENABLE(sid=3)`, `(sid=4)`, `(sid=6)` (**S3.5**) | Les SID 3 (60 s), 4 (8 s), 6 (8 s) démarrent en moins d'un intervalle de structure | ☐ | |
| 5b | TT&C | Lever le palier balise forcé, puis sélectionner LOW : `TTC_SET_BEACON_MODE(on=0)` (S8 func 70), `TTC_SET_DATA_RATE(rate=0)` (S8 func 65) | `ttc.beacon_mode` (0x0521) = 0 ; `ttc.tm_data_rate` (0x0506) = 16000 bit/s ; `ttc.tm_tier` (0x0539) = 1. Reconfigurer d'abord le démodulateur sol à 16 kBd | ☐ | |
| 6 | SPACON | Synchroniser le temps bord : `SET_TIME(cuc_seconds=T_corrected)` (S9.1), puis `REQUEST_TIME` (S9.2) | Acquittement + exécution < 5 s ; \|T_obc − T_gnd\| < 1 s | ☐ | |
| 7 | SPACON | Demander la HK EPS : `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) 26–30 V ; `eps.bat_soc` (0x0101) > 50 % | ☐ | |
| 8 | TT&C | Consigner les heures — AOS, forçage, première TC acceptée, amorçage applicatif, résidu de synchronisation temporelle, valeurs HK | Toutes les heures consignées | ☐ | |

**Valeurs consignées :**
- Heure d'AOS (UTC) : ____________
- Forçage activé : ____________
- Première TC acceptée : ____________
- Amorçage applicatif terminé : ____________
- Résidu de synchronisation temporelle : ____ s
- `eps.bus_voltage` : ____ V    `eps.bat_soc` : ____ %

**Erreurs fréquentes à éviter (récapitulatif de l'enseignant) :**
- Oublier `pass_override` avant les TC.
- Envoyer, avant l'amorçage applicatif, des TC absentes de la liste d'autorisation du chargeur d'amorçage (renvoie le code
  d'échec S1.8 **0x0006**, « Not permitted in bootloader »). `SET_TIME`
  en fait partie.
- Laisser expirer en cours de procédure le maintien automatique de l'émetteur de **5 minutes**
  (`auto_tx_hold_s` = 300 s, réarmé par chaque TC acceptée).
- Tenter `TTC_SET_DATA_RATE` avant d'avoir levé le mode balise — refusée avec
  0x0007 ; l'amorçage applicatif ne le lève **pas**.
- S'attendre à voir apparaître les SID 2 et 5 après l'étape 5 (ce n'est pas le cas — le SID 2
  est activé dans LEOP-007 et le SID 5 pendant la recette, une fois leurs lignes alimentées), ou s'attendre à voir un
  SID autre que 1 et 11 sans `HK_ENABLE` (S3.5) explicite.

**Critère de sortie atteint ?** ☐ oui ☐ non   **Signature du FD :** _______________

---

# Fiche WB-5.5-L006 — LEOP-006 Synchronisation temporelle (confirmer chaque étape)

**Opérateur (SPACON) :** ___________________

| N° | Action | Vérification attendue | ☐ fait | Note |
|---|--------|----------------------|:------:|------|
| 1 | `HK_REQUEST(sid=4)` (S3.27) ; lire le temps bord dans `obdh.obc_time` (0x0309) | horodatage consigné | ☐ | |
| 2 | Envoyer `REQUEST_TIME` (**S9.2**) pour le rapport TM(9,2), **et** `HK_REQUEST(sid=6)` pour `ttc.range_km` (0x0509) — le SID 6 est la structure qui transporte la distance oblique | T_obc consigné ; le TM(9,2) concorde avec 0x0309 | ☐ | |
| 3 | Calculer OWLT = `ttc.range_km` / 299792.458 × 1000 ms (valeur attendue **3–22 ms**), puis Δt = T_obc − (T_gnd − OWLT) | OWLT (ms) : ______  Δt (s) : ______ | ☐ | |
| 4 | Envoyer `SET_TIME(cuc_seconds=T_corrected)` (**S9.1**) — l'argument se place *à l'intérieur* des backticks ; un `SET_TIME` nu encode cuc_seconds = 0, soit une remise à zéro de l'époque | acquittement + exécution < 5 s, pas de S1.2 | ☐ | |
| 5 | Renvoyer `REQUEST_TIME` (S9.2) ; vérifier un résidu < 1.0 s par rapport à la référence sol (seuil LEOP ; NOM-008 le resserre en opérations nominales) | résidu (s) : ______ | ☐ | |
| 6 | Activer la HK de navigation GPS `HK_ENABLE(sid=12)` (S3.5) ; dès que `aocs.gps_fix` (0x0274) ≥ 2, asservir l'horloge avec `OBC_GPS_TIME_SYNC` (S8.1 func **80**) — réglage sol d'abord, GPS ensuite | `obdh.time_ref` (0x0A13) = 2 (GPS) en 15 s ; pas encore de point → contact suivant | ☐ | |

**Critère de sortie atteint ?** ☐ oui ☐ non

---

# Fiche WB-5.5-L002 — LEOP-002 Bilan de santé initial (confirmer chaque étape)

**Opérateur (SPACON consolide) :**  ___________________

| Sous-système | Opérateur | Onglet lu | État annoncé | ☐ fait | Note |
|-----------|----------|----------|-----------------|:------:|------|
| OBDH | SPACON | obdh | ☐ OK ☐ NOT-OK | ☐ | |
| EPS | EPS | eps | ☐ OK ☐ NOT-OK | ☐ | |
| TCS | Thermique | tcs | ☐ OK ☐ NOT-OK | ☐ | |
| TT&C | TT&C | ttc | ☐ OK ☐ NOT-OK | ☐ | |
| AOCS | AOCS | eps (indicateur de ligne 0x0117) | ☐ éteint (ligne OFF jusqu'à LEOP-007) ☐ alimenté trop tôt | ☐ | |
| Charge utile | Charge utile | eps (indicateur de ligne 0x0113) | ☐ éteinte (ligne OFF jusqu'à COM-009) ☐ alimentée trop tôt | ☐ | |

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
| 1 | EPS | Vérifier l'état de référence de l'EPS : `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) 26–30 V ; `eps.bat_soc` (0x0101) > 60 % ; `eps.power_gen` (0x0107) > 0 W | ☐ | |
| 2 | EPS | Réchauffeurs **seulement si nécessaire** : `EPS_POWER_ON(line_index=5)` (S8.1 func_id **19**) si `tcs.temp_battery` (0x0407) < +5 °C ; `EPS_POWER_ON(line_index=6)` si `tcs.temp_obc` (0x0406) < 0 °C | `eps.pl_htr_bat` (0x0115) / `eps.pl_htr_obc` (0x0116) = 1 pour chaque ligne alimentée | ☐ | lignes alimentées : ____ |
| 3 | EPS / AOCS | Alimenter la ligne de la suite AOCS et activer sa HK : `EPS_POWER_ON(line_index=7)` (func 19), puis `HK_ENABLE(sid=2)` (**S3.5**) | `eps.pl_aocs_wheels` (0x0117) = 1 ; SID 2 émis. Les roues restent DISABLED : `aocs.wheels_enabled` (0x0260) = 0 jusqu'à COM-004 | ☐ | |
| 4 | AOCS | Activer les éléments de DETUMBLE et le récepteur GPS : `S2_AOCS_MAGNETOMETER(device_id=521, state=1)`, `MTQ_ENABLE(enable=1)` (S8.1 func_id **9**), `S2_AOCS_GPS_RECEIVER(device_id=527, state=1)` | `aocs.mtq_enabled` (0x025E) = 1 | ☐ | |
| 5 | AOCS | Commander DETUMBLE : `AOCS_SET_MODE(mode=2)` (S8.1 func_id **0**) — mode **2 = DETUMBLE** | `aocs.mode` (0x020F) = 2 ; `aocs.mag_enabled` (0x025C) = 1, champ de 5–70 µT ; `aocs.rate_roll/pitch/yaw` (0x0204–0x0206) en baisse | ☐ | |
| 6 | EPS | Confirmer l'état d'alimentation de sortie : `HK_REQUEST(sid=1)` | `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_prop` (0x014A) = 0 ; marge de puissance positive | ☐ | |
| 7 | SPACON | Consigner toutes les heures d'étapes, les vitesses et les courants de ligne | consigné | ☐ | |

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
| 1 | Confirmer que DETUMBLE est actif et consigner les vitesses : `HK_REQUEST(sid=2)` (S3.27) | `aocs.mode` (0x020F) = 2 (DETUMBLE) ; vitesses roulis/tangage/lacet : __/__/__ °/s | ☐ | |
| 2 | Suivre la convergence de la loi B-dot — ne rien commander. Elle est **lente** : le seuil de 0,5°/s demande environ 1 200 s, et un culbutage de séparation complet de 14°/s environ 3,5e3 s | vitesses en baisse sur tous les axes ; `aocs.mag_field_total` (0x0277) non nul | ☐ | |
| 3 | Observer le passage **automatique** : vitesses sous 0,5°/s pendant 30 s → mode 3 de lui-même. Ne **pas** envoyer `AOCS_SET_MODE(mode=3)` | `aocs.mode` = 3 (COARSE_SUN) en 1800 s au plus | ☐ | heure : ____ |
| 4 | Vérifier le maintien au Soleil : `HK_REQUEST(sid=2)` toutes les 60 s pendant 5 min | `aocs.att_error` (0x0217) < 15° ; `aocs.css_sun_confidence` (0x0215) > 0,5 ; vitesses < 0,5°/s | ☐ | |
| 5 | Vérifier l'amélioration du bilan de puissance : `HK_REQUEST(sid=1)` | `eps.power_gen` (0x0107) > 40 W ; marge `eps.power_margin_w` (0x0135) : ____ W | ☐ | |
| 6 | Consigner l'état final. Le satellite reste en COARSE_SUN : aucun senseur stellaire n'est alimenté avant COM-003 | erreur : ____ ° | ☐ | |

**Critère de sortie atteint ?** ☐ oui ☐ non

---

# Fiche WB-5.5-L003 — LEOP-003 Restitution d'orbite initiale et fin de la LEOP (confirmer chaque étape)

**Opérateur (FDS, avec le FD pour l'étape 5) :**  ___________________

| N° | Action | Vérification | ☐ fait | Note |
|---|--------|--------------|:------:|------|
| 1 | Demander le rapport de navigation GPS : `HK_REQUEST(sid=12)` (S3.27) | `aocs.gps_fix` (0x0274) ≥ 2 ; `aocs.gps_num_sats` (0x0276) ≥ 4 | ☐ | PDOP : ____ |
| 2 | Lire la position : `GET_PARAM(param_id=0x0212)` (S20.3) et l'état ECEF 0x0231–0x0236 | `aocs.gps_alt` 495–540 km | ☐ | alt. : ____ km |
| 3 | FDS : comparer à l'orbite prédite par le lanceur | i à 0,2° près de 97,39° ; e < 0,01 ; LTAN à 15 min près de 10 h 00 | ☐ | i : ____ ° |
| 4 | Transmettre le TLE affiné aux outils sol (planificateur, FDS, stations) — **rien n'est envoyé au satellite** | prédictions de passage rafraîchies | ☐ | |
| 5 | FD : tour de table GO/NO-GO, puis **déclarer COMMISSIONING par télécommande** : `SYS_SET_MISSION_PHASE(phase=5, flags=0)` (S8.1 func **120**) — rien à bord ne fait avancer la phase au-delà de 4 | `eps.spacecraft_phase` (0x0129) = 5 (COMMISSIONING) < 5 s | ☐ | |

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
| Déploiement de l'antenne confirmé (`ttc.antenna_deployed` 0x0520 = 1) | ☐ |
| Ligne du réchauffeur batterie sur ON (`eps.pl_htr_bat` 0x0115 = 1) | ☐ |
| Ligne des roues du SCAO sur ON, SCAO passé par DETUMBLE (2) jusqu'à COARSE_SUN (3) | ☐ |
| Vitesses angulaires < 0.5°/s sur tous les axes ; `aocs.att_error` < 5° | ☐ |
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
| Widget épinglé ? | |
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
| Satellite en phase 4 (LEOP terminée), `eps.spacecraft_phase` (0x0129) = 4 | ☐ |
| Affectations des postes affichées (équipe différente de la veille) | ☐ |
| Chronologie de la série de passages comprise (4 passages simulés en 2,5 h de temps réel) | ☐ |
| Les 13 procédures de recette en orbite (COM-001…COM-013) chargées dans l'index des procédures | ☐ |
| L'EPS confirme un SoC d'environ 90 %, `eps.pl_payload` (0x0113) = 0 | ☐ |
| Le poste thermique confirme que le FPA est à son équilibre non refroidi, `payload.fpa_temp` (0x0601) de +8 à +14 °C | ☐ |
| Les opérations charge utile ont étudié en détail COM-009/-010/-011/-012 | ☐ |
| Cible candidate pour la première lumière choisie (FDS) | ☐ |
| Multiplicateur de vitesse du temps compressé réglé (enseignant) | ☐ |

---

# Fiche WB-5.6-C001 — COM-001 Vérification de l'EPS (confirmer chaque étape)

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Tension de bus de référence — `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) ∈ [27.5, 28.5] V | ☐ | V : ____ |
| 2 | Tension et SoC de la batterie — `GET_PARAM(param_id=0x0100)`, `GET_PARAM(param_id=0x0101)` (S20.3) | `eps.bat_voltage` ∈ [26.5, 29.2] V (batterie 8S : 21,5 V à 0 %, 26,4 V en nominal, 29,2 V à 100 %) ; `eps.bat_soc` > 70 % | ☐ | V : ____ SoC : ____ |
| 3 | Performances du générateur solaire en phase éclairée | `eps.power_gen` (0x0107) ∈ [40, 65] W (crête de l'ensemble du satellite 88,6 W ; ailes de 0,120 m² chacune à 267,9 W/m² en fin de vie) | ☐ | ____ W |
| 4 | Surveillance de la décharge en éclipse | `power_gen` ~0 W < 30 s après l'entrée ; baisse du SoC < 1.5 %/min ; `bus_voltage` > 27.0 V à mi-éclipse | ☐ | |
| 5 | Reprise de la charge en sortie d'éclipse | `power_gen` > 35 W < 60 s ; SoC en hausse < 120 s | ☐ | |
| 6 | Vérification du bilan de puissance — production moyenne sur l'orbite > consommation | charge nominale moyenne sur l'orbite ≈ **28,8 W** pour une production ≈ 45,1 W à l'angle bêta le moins productif, β = −31,2° (marge +16,3 W, rapport 1,57 ; 1,38 pendant la prise de vue) ; SoC en fin d'éclipse > 50 % sur la batterie de **100 Wh** | ☐ | marge : ____ W |
| 7 | Régulation du bus lors d'un transitoire de charge — consigner `eps.pl_htr_bat` (0x0115), puis `EPS_POWER_ON(line_index=5)` (S8.1 func_id **19**), et `EPS_POWER_OFF(line_index=5)` (func **20**) seulement si la ligne était éteinte à l'entrée. Pas la charge utile : sa ligne est OFF jusqu'à COM-009 | le bus reste dans [26.5, 29.5] V, revient dans [27.0, 29.0] V ; ligne revenue à son état d'entrée | ☐ | V min : ____ |

**Sortie ?** ☐ oui ☐ non   **GO COM-002 :** ☐

---

# Fiche WB-5.6-C002 — COM-002 Vérification du TCS (confirmer chaque étape)

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | HK thermique — `HK_REQUEST(sid=3)` (S3.27 ; SID 3 = TCS, cadence de 60 s) | `tcs.temp_obc` (0x0406) ∈ [−5, +45] °C ; `tcs.temp_battery` (0x0407) ∈ [+5, +35] °C ; `tcs.temp_fpa` (0x0408) remontée | ☐ | obc :__ bat :__ fpa :__ |
| 2 | Exercer chaque réchauffeur avec sa ligne alimentée — `EPS_POWER_ON(line_index=5)` puis `HEATER_BATTERY(on=1)` / `(on=0)` (S8.1 func **40**) ; `EPS_POWER_ON(line_index=6)` puis `HEATER_OBC(on=1)` / `(on=0)` (func **41**) ; ne recouper chaque ligne que si elle était éteinte à l'entrée | `eps.pl_htr_bat` (0x0115) / `eps.pl_htr_obc` (0x0116) = 1 ; température de zone en hausse ou stable ; lignes rétablies | ☐ | |
| 3 | Lire les seuils du thermostat autonome de la batterie — `GET_PARAM(param_id=0x0410)`, `GET_PARAM(param_id=0x0411)` (S20.3) | mise en marche à +5 °C, arrêt à +10 °C ; la fiche les lit, elle ne les modifie pas | ☐ | |
| 4 | Confirmer les performances du radiateur d'après la réponse des zones TCS en éclipse | zones stables, pas d'emballement | ☐ | |

**Sortie ?** ☐ oui ☐ non   **GO COM-005 :** ☐

---

# Fiche WB-5.6-C005 — COM-005 Transitions de modes SCAO (confirmer chaque étape)

**Codes de mode** (`aocs/aocs_mode_codes.yaml`, référence) : 0 OFF,
1 SAFE_BOOT, 2 DETUMBLE, 3 COARSE_SUN, 4 NOMINAL, 5 FINE_POINT,
6 SLEW, 7 DESAT, 8 ECLIPSE, 9 INERTIAL. Chaque transition se fait par
`AOCS_SET_MODE(mode=N)` (S8.1 **func_id 0**).

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Verrouiller le mode commandé : `AOCS_SET_MODE(mode=4)` — l'AOCS vole en NOMINAL depuis COM-004 | `aocs.mode` (0x020F) = 4 (ou 8 en éclipse) ; `aocs.commanded_mode` (0x0297) = 4 ; att_error < 1,0° | ☐ | |
| 2 | Lire le masque des préconditions FINE : `AOCS_FINE_READY_CHECK` (S8.1 func **89**) | `aocs.fine_ready` (0x02C5) = 0. Bit 1 = *moins de trois* roues — un jeu de 3 roues sur 4 permet toujours FINE, signalé par `aocs.fine_degraded` (0x0299) | ☐ | masque : ____ |
| 3 | Passer en FINE_POINT (`AOCS_SET_MODE(mode=5)`), puis revenir en NOMINAL (`AOCS_SET_MODE(mode=4)`) | mode = 5 dans les 30 s ; att_error < 0,1° dans les 300 s ; puis mode = 4 dans les 30 s | ☐ | erreur : ____ ° |
| 4 | INERTIAL et retour : `AOCS_SET_MODE(mode=9)`, puis `AOCS_SET_MODE(mode=4)` | mode 9, puis mode 4, chacun dans les 30 s | ☐ | |
| 5 | Commander le maintien COARSE_SUN (`AOCS_SET_MODE(mode=3)`), puis **attendre** le retour automatique | mode 3 et `aocs.mode_demoted` (0x0298) = 1 ; puis mode 4 de lui-même en 1800 s et 0x0298 = 0 | ☐ | |
| 6 | Désaturer : `AOCS_DESATURATE` (S8.1 func **1**) — DESAT se termine d'elle-même | mode 7 (DESAT), puis retour à 4 en 900 s sans commande | ☐ | |

**Sortie ?** ☐ oui ☐ non

---

# Fiche WB-5.6-C006 — COM-006 Vérification de la liaison TTC (confirmer chaque étape)

L'échelle de débits TM comporte exactement trois échelons : **BEACON 1 kbit/s /
LOW 16 kbit/s / HIGH 128 kbit/s**. BEACON ne peut pas être sélectionné avec
`TTC_SET_DATA_RATE` — sa référence provient du passage LEOP-001.

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 0 | Configurer la chaîne bande S : `EPS_POWER_ON(line_index=2)` (func 19), `TTC_PA_ON` (func **66**), `TTC_SET_BEACON_MODE(on=0)` (func **70**), `TTC_DEPLOY_ANTENNA` (func **69**) | `eps.pl_ttc_tx` (0x0112) = 1 ; `ttc.pa_on` (0x0516) = 1 ; `ttc.beacon_mode` (0x0521) = 0 ; `ttc.antenna_deployed` (0x0520) = 1 ; `ttc.tx_active` (0x0525) = 1 (sinon lire `ttc.tx_gate_status` 0x052B) | ☐ | |
| 1 | Établir la référence du transpondeur principal à LOW : `TTC_SET_DATA_RATE(rate=0)` (S8.1 func **65**) | `ttc.link_status` (0x0501) = **2** (LOCKED) ; `ttc.tm_data_rate` (0x0506) = 16000 bit/s ; `ttc.tm_tier` (0x0539) = 1 ; `ttc.link_margin` (0x0503) > 6 dB (attendu **55–59 dB** à 30° — cette liaison n'est pas limitée en puissance) | ☐ | ____ dB |
| 2 | Passer à HIGH : `TTC_SET_DOWNLINK_MODE(on=1)` (func **79**) puis `TTC_SET_DATA_RATE(rate=1)` (func 65) | `tm_data_rate` = 128000 bit/s ; `tm_tier` = 2 ; `ttc.tm_symbol_rate` (0x053B) = 64000 Bd (QPSK) ; marge attendue **45–48 dB** à 30° | ☐ | ____ dB |
| 3 | Calculer l'écart entre échelons : marge(LOW) − marge(HIGH) | **10.5 ± 0.5 dB**. Toute autre valeur est une erreur de modélisation, pas un problème de liaison | ☐ | écart : ____ dB |
| 4 | Sous 10° d'élévation (`ttc.contact_elevation` 0x050A), retenter HIGH | Commande **rejetée**, erreur S1.8 0x0007 indiquant la condition d'élévation ; le débit reste à 16000 bit/s. C'est le comportement correct, pas une anomalie | ☐ | |
| 5 | Mettre la liaison en sécurité : `TTC_SET_DATA_RATE(rate=0)`, `TTC_SET_DOWNLINK_MODE(on=0)`, `TTC_SWITCH_PRIMARY` (func **63**) | `tm_tier` = 1, `ttc.tm_tier_cmd` (0x053A) = 1, `ttc.downlink_mode` (0x053C) = 0. L'antenne reste déployée et le PA reste sur ON | ☐ | |
| 6 | Consigner les marges aux deux échelons opérationnels dans la main courante | consigné | ☐ | |

**Sortie ?** ☐ oui ☐ non

---

# Fiche WB-5.6-C007 — COM-007 Vérification de l'OBDH (confirmer chaque étape)

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Vérifier le chien de garde : `OBC_DIAGNOSTIC` (S8.1 func **61**), `GET_PARAM(param_id=0x0316)` (S20.3). (Il n'existe pas de commande `OBC_WATCHDOG_KICK`) | réponse du diagnostic : chien de garde armé ; `obdh.last_reboot_cause` = 0 ; `obdh.reboot_count` (0x030A) inchangé | ☐ | |
| 2 | Lire et vérifier l'occupation de la mémoire de masse — `HK_REQUEST(sid=4)` (S3.27) | `obdh.mmm_used` (0x0303, %) conforme ; stockage charge utile `payload.mem_used_mb` (0x060B) sur `payload.mem_total_mb` (0x060A) | ☐ | occupé : ____ Mo |
| 3 | Relever comme référence les compteurs d'erreurs mémoire et de SEU — `GET_PARAM(param_id=0x031E)`, `GET_PARAM(param_id=0x0319)` (S20.3) ; puis l'excursion de mode `OBC_SET_MODE(mode=1)`, `OBC_SET_MODE(mode=0)` (func **50**) | compteurs stables entre deux lectures ; `obdh.mode` (0x0300) revenu à 0 — la fiche se termine en NOMINAL | ☐ | |
| 4 | Vérifier l'état des bus A et B | `obdh.bus_a_status` (0x030F) = 0 et `obdh.bus_b_status` (0x0310) = 0 (0 = OK) ; bus actif indiqué par `obdh.active_bus` (0x030E) | ☐ | |

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
| 1 | Lire l'état de la FDIR — `GET_PARAM(param_id=0x0700)` (S20.3) | `fdir.level` = 0 (0 nominal, 1 attention, 2 avertissement, 3 critique) ; `fdir.active_alarms` (0x0701) = 0 | ☐ | |
| 2 | Passer en revue le jeu de règles dans le panneau FDIR en le comparant à `subsystems/fdir.yaml` | seuils clés confirmés : `eps.bus_voltage` < **24.5 V**, `eps.bat_soc` < 20 % / < 15 %, `aocs.att_error` > 5° maintenu 420 s, `obdh.temp` > 65 °C | ☐ | nombre : ____ règles |
| 3 | Activer / vérifier le service de surveillance S12 — `MON_ENABLE` (**S12.1**), `MON_REPORT_DEFS` (S12.12) | liste des définitions renvoyée ; alarmes visibles dans le MCS | ☐ | |
| 4 | Essai fonctionnel du verrouillage de délestage commandé : `EPS_EMERGENCY_LOAD_SHED(stage=1)` (S8.1 func **25**), puis `EPS_EMERGENCY_LOAD_SHED(stage=0)`. Jamais l'étage 2 ou 3 ici — l'étage 3 coupe `ttc_tx` | étage 1 : `eps.load_shed_stage` (0x0134) = 1 et **se verrouille**, événement 0x0106 ; étage 0 : retour à 0 et **aucune ligne réalimentée** | ☐ | |
| 5 | Confirmer l'absence d'état de protection résiduel : `GET_PARAM(param_id=0x0700)`, `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` | `fdir.level` = 0 ; `eps.load_shed_stage` = 0 ; `obdh.mode` (0x0300) = 0 — aucune excursion de mode de l'OBC | ☐ | |

**Sortie ?** ☐ oui ☐ non

---

# Fiche WB-5.6-C009 — COM-009 Mise sous tension de la charge utile (confirmer chaque étape)

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | GO du FD confirmé | consigné | ☐ | |
| 2 | Alimenter la ligne charge utile : `EPS_POWER_ON(line_index=3)` (S8.1 func_id **19**) | `eps.pl_payload` (0x0113) = 1 < 5 s ; `eps.line_current_3` (0x011B) dans l'enveloppe — l'attente consomme 2,4 W, soit ≈ **0.09 A** sous 28 V (le seuil de surintensité de cette ligne est de 2.5 A) | ☐ | I : ____ A |
| 3 | Commander STANDBY : `PAYLOAD_SET_MODE(mode=1)` (S8.1 func_id **26**) | `payload.mode` (0x0600) = 1 (STANDBY). Modes : 0 OFF, 1 STANDBY, 2 IMAGING, **3 CALIBRATION** | ☐ | |
| 4 | Activer la HK charge utile : `HK_ENABLE(sid=5)` (**S3.5**), puis `HK_REQUEST(sid=5)` (S3.27) | SID 5 périodique en moins d'un intervalle de 8 s ; `payload.imager_status` (0x0611) sans bit de défaut ; `payload.fpa_temp` (0x0601) valide, de +8 à +14 °C | ☐ | |
| 5 | Vérifier que le stockage est initialisé | `payload.mem_used_mb` (0x060B) sur `payload.mem_total_mb` (0x060A) = 20000 Mo ; `payload.product_count` (0x0648) | ☐ | ____ Mo |

**Sortie ?** ☐ oui ☐ non   **GO COM-010 :** ☐

---

# Fiche WB-5.6-C010 — COM-010 Activation du refroidisseur du FPA (confirmer chaque étape ; s'étend sur une éclipse)

Le refroidisseur du FPA est un **cryoréfrigérateur miniature de type Stirling** fonctionnant
à environ 23 % du rendement de Carnot (`fpa_cooler_carnot_fraction` 0.23) — et non un
empilement Peltier. Sa capacité diminue à mesure que l'écart de température augmente, de sorte que le
plancher atteignable varie avec la température du puits thermique et la charge
de prise de vue. Consigne par défaut **−15 °C** ; enveloppe commandable de **−20 °C à
0 °C** (`PAYLOAD_COOLER_SETPOINT`, S8.1 func **36**, l'argument est un
uint16 en **centikelvins** — −15 °C correspond à 0x64D7). La boucle se stabilise en
environ 10 minutes et ne dépasse jamais la consigne.

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Consigner l'état avant activation ; refroidisseur sur OFF | `payload.fpa_temp` (0x0601) à l'équilibre non refroidi, de +8 à +14 °C ; `payload.mode` (0x0600) = 1 | ☐ | T_fpa : ____ °C |
| 2 | Activer le refroidisseur : `FPA_COOLER(on=1)` (S8.1 func_id **43**) | `tcs.cooler_fpa` (0x040C) = 1 **et** `eps.pl_fpa_cooler` (0x0114) = 1 — les deux, sinon le refroidisseur ne fonctionne pas réellement | ☐ | |
| 3 | Vérifier la puissance consommée — `HK_REQUEST(sid=1)` (S3.27) | `eps.power_cons` (0x0106) en hausse de **14–16 W** ; `payload.cooler_pwr` (0x0602) ≈ 15 W ; `eps.bus_voltage` (0x0105) > 27.0 V | ☐ | ____ W |
| 4 | Surveiller la rampe (exponentielle, non linéaire — une décroissance plus lente à T+5 qu'à T+2 est normale) | T+2 min < +4 °C ; T+5 min < −8 °C | ☐ | T à 5 min : __ °C |
| 5 | Surveiller la stabilisation | T+10 min ∈ [−16.0, −14.0] °C ; T+15 min ∈ [−16.0, −15.0] °C. Une lecture inférieure à −16.5 °C est un **défaut de régulation**, pas un refroidisseur plus performant que prévu | ☐ | T à 15 min : __ °C |
| 6 | Vérifier la disponibilité et la marge | `payload.fpa_ready` (0x0610) = 1 (hystérésis de 60 s) ; `payload.fpa_setpoint` (0x0631) = −15.0 ; `payload.cooler_margin_k` (0x064B) > 0 (attendu ≈ +5 K) ; plancher indiqué par `payload.cooler_floor_c` (0x064A) | ☐ | marge : ____ K |
| 7 | Maintenir pendant l'éclipse | T_fpa reste dans [−16.5, −14.5] °C ; bus > 27.0 V | ☐ | |

**Si `cooler_margin_k` ≤ 0 :** le refroidisseur ne peut physiquement pas atteindre la
consigne commandée avec le puits thermique et la charge actuels. La solution est une
**consigne plus chaude**, pas une attente plus longue.

**Sortie ?** ☐ oui ☐ non   **GO COM-011 :** ☐

---

# Fiche WB-5.6-FPA — Fiche de suivi de la mise en froid du FPA

**Usage :** pendant COM-010. La boucle se ferme en environ 10 minutes : relevez donc
`payload.fpa_temp` (0x0601) toutes les minutes pendant les
15 premières minutes, puis toutes les 5 minutes pendant le maintien de stabilité.

| Temps écoulé | T_fpa (°C) | `payload.cooler_pwr` 0x0602 (W) | Éclipse ? | Note |
|---------|-----------|------------------|:--------:|------|
| 0:00 | | | ☐ | début, de +8 à +14 °C |
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
| 1 | Fermer l'obturateur : `PAYLOAD_SET_SHUTTER(position=0)` (S8.1 func **119**) | `payload.shutter_pos` (0x063C) = 0 (fermé) | ☐ | |
| 2 | Série d'obscurité : `PAYLOAD_SET_MODE(mode=1)` (func 26), `PAYLOAD_CAL_LAMP(on=0)` (func **95**), `PAYLOAD_START_CALIBRATION(mode=0)` (func **37**, 0 = DARK) | `payload.mode` = 3 (CALIBRATION) ; `payload.calibration_active` (0x062A) = 1 ; à la fin, événement S5 **0x060B CALIBRATION_COMPLETE** ; `payload.dark_frame_cnt` (0x0642) > 0 | ☐ | images : ____ |
| 3 | Série de champ plat : `PAYLOAD_SET_SHUTTER(position=1)` (func 119), `PAYLOAD_CAL_LAMP(on=1)` (func 95), `PAYLOAD_START_CALIBRATION(mode=1)` (func 37, 1 = FLAT) | `payload.cal_lamp_on` (0x0615) = 1 ; `payload.bias_frame_cnt` (0x0643) > 0 ; lampe ramenée sur OFF ensuite | ☐ | images : ____ |
| 4 | Vérifier que le jeu de corrections est valide sur les quatre bandes | `payload.cal_valid_mask` (0x0646) bits 0–3 (bleu/vert/rouge/PIR) tous positionnés ; `payload.snr` (0x0616) consigné | ☐ | masque : ____ |
| 5 | Survol du site d'étalonnage : `AOCS_FINE_READY_CHECK` (func 89), puis `AOCS_SET_MODE(mode=5)` (func 0) — FINE_POINT est le mode **5** | `aocs.fine_ready` (0x02C5) = 0 ; `aocs.mode` (0x020F) = 5 | ☐ | |
| 6 | Retour : `PAYLOAD_SET_MODE(mode=1)` STANDBY, obturateur OUVERT, `AOCS_SET_MODE(mode=4)` NOMINAL | `payload.mode` = 1 ; `payload.shutter_pos` = 1 ; `aocs.mode` = 4 | ☐ | |

**Sortie ?** ☐ oui ☐ non   **GO COM-012 :** ☐

---

# Fiche WB-5.6-C012 — COM-012 Première lumière (confirmer chaque étape)

| N° | Action | Attendu | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | GO du FD pour la première lumière | consigné | ☐ | |
| 2 | SCAO en FINE_POINT : `AOCS_FINE_READY_CHECK` (func 89), `AOCS_SET_MODE(mode=5)` (func 0) | `aocs.fine_ready` (0x02C5) = 0 ; `aocs.mode` (0x020F) = 5 | ☐ | |
| 3 | Vérifier que le FPA est à température | `payload.fpa_ready` (0x0610) = 1 ; `payload.fpa_temp` (0x0601) ∈ [−16.5, −14.5] °C | ☐ | T : ____ °C |
| 4 | Vérifier que la charge utile est prête et consigner les références : `HK_REQUEST(sid=5)` (S3.27) | `payload.mode` (0x0600) = 1 ; `payload.store_used` (0x0604) < 97 % ; consigner `payload.image_count` (0x0605) et `payload.mem_used_mb` (0x060B) | ☐ | nombre : ____ |
| 5 | Commander IMAGING et capturer : `PAYLOAD_SET_MODE(mode=2)` (func **26**), puis `PAYLOAD_CAPTURE(scene_id=1, lines=2048)` (S8.1 func **28**) | Acceptation S1.1 + exécution S1.7 ; événement S5 0x0613 IMAGE_CAPTURED. 2048 lignes à 244 Hz = 8,4 s ≈ 59 km le long de la trace à 7,06 km/s | ☐ | scène : ____ |
| 6 | Vérifier que le produit est stocké | `payload.mem_used_mb` (0x060B) en hausse ; `payload.product_count` (0x0648) +1 ; taille ≈ **4 Mo** (`image_size_mb`, l'abstraction pédagogique) | ☐ | ____ Mo |
| 7 | Revenir en STANDBY (`PAYLOAD_SET_MODE(mode=1)`), puis transmettre par le service 13 : `TTC_SET_DOWNLINK_MODE(on=1)`, `TTC_SET_DATA_RATE(rate=1)`, `S13_CREATE_TRANSFER(scene_id=1, size_mb=0)` … `S13_END_TRANSFER(transfer_id=T)`, puis retour en LOW | 128000 bit/s ; `payload.transfer_active` (0x062D) = 1, `payload.transfer_progress` (0x062E) en hausse, puis 0x062D = 0 ; CRC-32 correct au sol | ☐ | heure de réception : ______ |
| 8 | Évaluation de la qualité (au passage suivant si nécessaire) | DN moyen, contraste, géoréférencement ; `payload.last_scene_quality` (0x060D) ; `aocs.geoloc_err_m` (0x02C7) | ☐ | qualité : ____ |

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
| Taille de l'image (Mo) — attendu ~4 | |
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
| Refroidisseur du FPA à sa consigne commandée (−15 °C par défaut), `payload.fpa_ready` (0x0610) = 1, `cooler_margin_k` > 0 | ☐ |
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
| Widget épinglé ? | |
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

| N° | Responsable | Action | Vérification | ☐ | Note |
|---|-------|--------|--------------|:-:|------|
| 1 | EPS | Confirmer que `eps.bus_voltage` (0x0105) est sous le seuil de sous-tension FDIR de **24.5 V** (le délestage modélisé commence à 25.0 V ; avertissement bus 27.0 V, bus critique 25.0 V) | consigné | ☐ | V : ____ |
| 2 | EPS | Rendre compte au FD ; recommander le délestage de priorité 1 | recommandation consignée | ☐ | |
| 3 | FD | GO pour le délestage | accordé | ☐ | |
| 4 | EPS | Priorité 1 — charge utile coupée : `PAYLOAD_SET_MODE(mode=0)` (S8.1 func **26**) | `payload.mode` (0x0600) = 0 | ☐ | |
| 5 | EPS | Priorité 2 — refroidisseur coupé : `FPA_COOLER(on=0)` (func **43**) | `tcs.cooler_fpa` (0x040C) = 0 | ☐ | |
| 6 | EPS | Priorité 3 — PA coupé : `TTC_PA_OFF` (func **67**). Noter que la TM bande S s'arrête mais que **la balise UHF subsiste** — c'est une radio distincte, sur la ligne non commutable `ttc_rx`, de sorte que le SID 11 de HK continue d'arriver | `ttc.pa_on` (0x0516) = 0, `ttc.beacon_active` (0x0527) toujours à 1 | ☐ | |
| 7 | EPS | Priorité 4 — ligne des roues coupée : `EPS_POWER_OFF(line_index=7)` (func **20**) | `eps.pl_aocs_wheels` (0x0117) = 0 | ☐ | |
| 8 | EPS | (Dernier recours) délestage par étages `EPS_EMERGENCY_LOAD_SHED(stage=N)` (S8.1 func **25**, étages 1–3) ou `OBC_SET_MODE(mode=2)` EMERGENCY (func **50**) | `eps.load_shed_stage` (0x0134) | ☐ | |
| 9 | EPS | Vérifier que le SoC cesse de baisser ; le bus remonte au-dessus de 25.5 V (seuil de délestage + 0.5 V d'hystérésis ; la remise en service automatique rétablit ensuite les lignes une par une à chaque pas de simulation, dans l'ordre inverse du délestage) | durée de reprise : ____ s | ☐ | |
| 10 | SPACON | Acquitter la règle FDIR ; consigner | consigné | ☐ | |
| 11 | EPS | Remplir une fiche d'anomalie | fiche n° : ____ | ☐ | |

## CTG-002 Reprise après anomalie SCAO

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Lire dans le panneau FDIR quel capteur / actionneur est en défaut ; `HK_REQUEST(sid=2)` (S3.27) | identifié : ____________ | ☐ | |
| 2 | Commander le attente sûre au Soleil : `AOCS_SET_MODE(mode=3)` (S8.1 func **0**) — mode **3 = COARSE_SUN**. (Il n'existe pas de mode SAFE_POINT ; le mode 1 est SAFE_BOOT, un état de propagation seule après amorçage, et non une cible de reprise) | `aocs.mode` (0x020F) = 3 | ☐ | |
| 3 | Vérifier que le satellite est stable | vitesses (0x0204–0x0206) < 0.05°/s ; `aocs.att_error` (0x0217) < 5° ; aucune nouvelle alarme | ☐ | |
| 4 | Si le moment cinétique est en cause, le décharger : `AOCS_DESATURATE` (S8.1 func **1**) — DESAT est le mode 7. Prévoir **20–50 min** pour un déchargement complet ; la prise de vue est inhibée et le satellite revient ensuite à son mode antérieur à la désaturation | `aocs.h_body_mag` (0x02B9) en baisse ; `aocs.desat_ineffective` (0x029C) = 0 | ☐ | |
| 5 | Suivre la sous-procédure propre au composant défaillant (CTG-007 roue / CTG-008 senseur stellaire) | ID de la sous-procédure : ____ | ☐ | |
| 6 | Rétablir NOMINAL : `AOCS_SET_MODE(mode=4)` ; ne remonter jusqu'à DETUMBLE (`mode=2`) qu'en cas de panne de plusieurs roues | `aocs.mode` = 4 | ☐ | |
| 7 | Remplir une fiche d'anomalie | fiche n° : ____ | ☐ | |

## CTG-007 Anomalie de roue de réaction

EOSAT-1 embarque **quatre** roues en pyramide. Les vitesses sont en LECTURE SEULE
dans `aocs.rw1..rw4_speed` (0x0207–0x020A) ; températures 0x0218–0x021B ;
courants 0x0250–0x0253 ; état des roulements 0x0284–0x0287. La vitesse se
commande avec `RW_SET_SPEED_BIAS` (S8.1 func **8** — le biais est
**ajouté** à la vitesse actuelle) et `AOCS_RW_RAMP_DOWN` (func
**14**, `wheel_idx` 255 = toutes).

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Identifier la roue concernée (indice 0–3) d'après la vitesse, le courant et l'état du roulement | roue : ____ | ☐ | |
| 2 | La désactiver : `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8.1 func **2**) | `aocs.rwN_enabled` (0x0254–0x0257) = 0 ; `aocs.wheels_enabled` (0x0260) = 3 | ☐ | |
| 3 | Désaturer le jeu restant : `AOCS_DESATURATE` (func **1**) | `aocs.h_body_mag` (0x02B9) en baisse ; prévoir **20–50 min** | ☐ | |
| 4 | Vérifier le pointage sur trois roues. Un sous-ensemble de 3 roues sur 4 engendre toujours R³ : **FINE_POINT fonctionne toujours** — signalé, et non refusé | `aocs.att_error` (0x0217) : ____ ° ; `aocs.fine_degraded` (0x0299) = 1 ; bit 1 de `aocs.fine_ready` (0x02C5) à zéro | ☐ | |
| 5 | Si le pointage est acceptable, rester en NOMINAL (`AOCS_SET_MODE(mode=4)`) ; sinon se replier sur COARSE_SUN (**3**) | mode : ____ | ☐ | |
| 6 | Remplir une fiche d'anomalie | fiche n° : ____ | ☐ | |

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
| 1 | Confirmer la panne : `HK_REQUEST(sid=2)` (S3.27) | `aocs.st1_status` (0x0240) = 3 (aveuglé) ou 4 (en panne) ; `aocs.est_innov_rej_count` (0x02C2) en hausse | ☐ | ST1 : __ ST2 : __ |
| 2 | Mettre en service l'autre tête : `ST2_POWER(on=1)` (S8.1 func **5**) | `aocs.st2_status` (0x0243) = 2 (poursuite) dans son temps d'amorçage | ☐ | |
| 3 | La sélectionner : `ST_SELECT(unit=2)` (S8.1 func **6**) | `aocs.st_selected` (0x0244) mis à jour ; bit 0 de `aocs.est_source` (0x02C1) toujours positionné | ☐ | |
| 4 | Isoler la tête défaillante : `ST1_POWER(on=0)` (S8.1 func **4**) | `aocs.st1_status` = 0 (éteint) | ☐ | |
| 5 | Si la solution d'attitude a divergé, la réinitialiser : `AOCS_EST_RESET(mode=1)` (S8.1 func **91**, à chaud) — ou `mode=0` pour une réinitialisation à froid après un saut de temps | `aocs.knowledge_err_3sig` (0x02A7) en cours de stabilisation ; les rejets d'innovation cessent d'augmenter | ☐ | |
| 6 | Si les **deux** têtes sont perdues, se replier sur le attente sûre au Soleil : `AOCS_SET_MODE(mode=3)` COARSE_SUN, et `PAYLOAD_SET_MODE(mode=0)` | `aocs.mode` (0x020F) = 3 ; `aocs.est_source` indique CSS+MAG+gyro, bit ST à zéro | ☐ | mode : ____ |
| 7 | Si une tête est rétablie, revenir en NOMINAL (`AOCS_SET_MODE(mode=4)`) ; sinon rester en COARSE_SUN | mode : ____ | ☐ | |
| 8 | Remplir une fiche d'anomalie | fiche n° : ____ | ☐ | |

## CTG-010 Reprise après chien de garde OBDH

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirmer le redémarrage : `HK_REQUEST(sid=4)` (S3.27) | `obdh.reboot_count` (0x030A) incrémenté ; `obdh.last_reboot_cause` (0x0316) = 1 (chien de garde) ; `obdh.uptime` (0x0308) proche de zéro | ☐ | horodatage : ______ |
| 2 | Si le satellite est revenu dans le chargeur d'amorçage (`obdh.sw_image` 0x0311 = 0), réamorcer l'applicatif : `OBC_BOOT_APP` (S8.1 func **55**) | `obdh.sw_image` = 1 dans les 15 s | ☐ | |
| 3 | Réactiver la télémesure de servitude — l'amorçage applicatif réapplique `default_enabled_sids: [1, 11]`, de sorte que **tous les autres SID sont à nouveau désactivés** : `HK_ENABLE(sid=2/3/4/5/6)` (**S3.5**) | tous les SID requis de nouveau périodiques | ☐ | |
| 4 | Resynchroniser le temps : `SET_TIME(cuc_seconds=T_corrected)` (S9.1), vérifier avec `REQUEST_TIME` (S9.2) | résidu < 1.0 s | ☐ | |
| 5 | Vérifier le mode de l'OBC ; rétablir NOMINAL s'il est en SAFE : `OBC_SET_MODE(mode=0)` (S8.1 func **50**) | `obdh.mode` (0x0300) = 0 | ☐ | mode : ____ |
| 6 | Réappliquer les réglages perdus lors de la réinitialisation (consignes des réchauffeurs, forçages de limites S12, palier TM, mode balise) | réglages rétablis | ☐ | |
| 7 | Remplir une fiche d'anomalie | fiche n° : ____ | ☐ | |

## CTG-012 Traitement d'une surintensité

Les indices de ligne vont de **0 à 8** : 0 `obc`, 1 `ttc_rx`, 2 `ttc_tx`,
3 `payload`, 4 `fpa_cooler`, 5 `htr_bat`, 6 `htr_obc`,
7 `aocs_wheels`, 8 `prop`.

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Identifier la ligne déclenchée d'après `eps.oc_trip_flags` (0x010D) et les courants par ligne `eps.line_current_0..7` (0x0118–0x011F ; la ligne 8 est en 0x014B) | ligne : ______ | ☐ | I : ____ A |
| 2 | Rendre compte au FD ; noter que l'action autonome de la FDIR a généralement déjà ouvert la ligne | consigné | ☐ | |
| 3 | GO du FD | accordé | ☐ | |
| 4 | S'assurer que la ligne est ouverte : `EPS_POWER_OFF(line_index=N)` (S8.1 func **20**) | bit d'état `eps.pl_*` = 0 | ☐ | |
| 5 | Vérifier que le courant de la ligne vaut 0 | I : ____ A | ☐ | |
| 6 | Seulement une fois le défaut compris, effacer le verrou et réactiver : `EPS_RESET_OC_FLAG(line_index=N)` (S8.1 func **21**), puis `EPS_POWER_ON(line_index=N)` (func **19**) | bit de `eps.oc_trip_flags` à zéro ; courant de la ligne revenu dans l'enveloppe | ☐ | |
| 7 | Remplir une fiche d'anomalie ; cause première pour le quart suivant | fiche n° : ____ | ☐ | |

## CTG-015 Reprise après image corrompue

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirmer l'événement S5 **0x0607 IMAGE_CHECKSUM_ERROR** et lire `payload.checksum_errors` (0x0609) | événement consigné | ☐ | nombre : ____ |
| 2 | Vérifier le FPA : `HK_REQUEST(sid=5)` et `(sid=3)` (S3.27) | `payload.fpa_temp` (0x0601) dans la plage et `payload.fpa_ready` (0x0610) = 1 au moment de la capture ? | ☐ | T : ____ °C |
| 3 | Si le FPA était chaud, revenir en STANDBY (`PAYLOAD_SET_MODE(mode=1)`, func 26), réactiver le refroidisseur (`FPA_COOLER(on=1)`, func **43**) et attendre `fpa_ready` | ready = 1 | ☐ | |
| 4 | Vérifier la mémoire : `payload.mem_segments_bad` (0x0612) ; marquer un segment défectueux avec `PAYLOAD_MARK_BAD_SEGMENT(segment_id=N)` (S8.1 func **31**) | segments : ____ | ☐ | |
| 5 | Supprimer et recapturer : `PAYLOAD_DELETE_IMAGE(scene_id=N)` (func **30**), puis `PAYLOAD_CAPTURE(scene_id=N, lines=L)` (func **28**) | nouvelle scène : ______ ; S5 0x0613 IMAGE_CAPTURED | ☐ | |
| 6 | En cas de récurrence, examiner la température du FPA ou le pointage | constat : ____________ | ☐ | |
| 7 | Remplir une fiche d'anomalie | fiche n° : ____ | ☐ | |

## CTG-017 Basculement sur panne de bus

Basculer de **bus** et basculer d'**unité OBC** sont deux
commandes différentes. `OBC_SELECT_BUS` (func 54) change de bus CAN ;
`OBC_SWITCH_UNIT` (func 53) bascule sur l'OBC redondant et relève de
CTG-011, pas de cette carte.

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirmer le défaut de bus : `HK_REQUEST(sid=4)` (S3.27) | `obdh.bus_a_status` (0x030F) = 1 (ERROR) ; `obdh.active_bus` (0x030E) = 0 (A) | ☐ | |
| 2 | GO du FD pour le basculement de bus | accordé | ☐ | |
| 3 | Envoyer `OBC_SELECT_BUS(bus=1)` (S8.1 func_id **54**) pour passer sur le bus B (utiliser `bus=0` pour revenir sur A) | Acceptation S1.1 + exécution S1.7 | ☐ | |
| 4 | Vérifier que le bus B est utilisé et que toute la télémesure de servitude reprend | `obdh.active_bus` = 1 ; `obdh.bus_b_status` (0x0310) = 0 ; SID 1–6 de nouveau émis | ☐ | |
| 5 | Remplir une fiche d'anomalie. Noter qu'il ne reste désormais **plus aucune redondance de bus** | fiche n° : ____ | ☐ | |

## CTG-019 Absence de télémesure en début de passage

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Vérifier la station programmée et la configuration de bande de base (réseau de cinq stations) | OK | ☐ | |
| 2 | Vérifier la prédiction d'orbite / de passage (la géométrie peut être en cause) | prédiction OK | ☐ | |
| 3 | Commander en aveugle la chaîne d'émission : `HK_REQUEST(sid=1)` (S3.27), `EPS_POWER_ON(line_index=2)` (func **19**), `TTC_PA_ON` (func **66**) | `eps.pl_ttc_tx` (0x0112) = 1 ; `ttc.pa_on` (0x0516) = 1 dès le retour de la TM | ☐ | |
| 4 | Permuter en aveugle les transpondeurs : `TTC_SWITCH_REDUNDANT` (func **64**), puis `TTC_SWITCH_PRIMARY` (func **63**) | `ttc.link_status` (0x0501) = **2** (LOCKED) | ☐ | |
| 5 | Si l'antenne n'a jamais été déployée, `TTC_DEPLOY_ANTENNA` (func **69**) — fil thermofusible irréversible | `ttc.antenna_deployed` (0x0520) = 1 | ☐ | |
| 6 | Se rappeler que la balise UHF est une **radio distincte** : si le SID 11 de HK arrive toujours alors que la bande S est muette, la panne se situe dans la chaîne bande S, pas dans le satellite | `ttc.beacon_active` (0x0527) : ____ | ☐ | |
| 7 | Si la liaison est établie, exécuter NOM-001 ; sans liaison après deux passages consécutifs, passer à **EMG-004** (Perte de communication) | voie suivie : ____ | ☐ | |
| 8 | Remplir une fiche d'anomalie | fiche n° : ____ | ☐ | |

## CTG-020 Panne d'antenne de station sol

CTG-020 est une fiche **consultative** (`advisory: true` dans
`procedure_index.yaml`) — elle n'est pas exécutable par la machine et ne
contient **aucune télécommande vers le satellite**. Il s'agit d'une panne du segment
sol : tout se fait côté sol. N'envoyez aucune commande au
satellite pour la traiter.

| N° | Action | Vérification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirmer que la panne est côté sol et non côté satellite (masque de bits `ttc.gs_equipment_status` 0x0524 ; un satellite sain continue d'émettre) | confirmé | ☐ | |
| 2 | Tenter une reprise locale de la station avec l'opérateur de la station | résultat : ______ | ☐ | |
| 3 | Informer le FD et le responsable de mission ; évaluer l'impact sur le plan du quart | consigné | ☐ | |
| 4 | Replanifier les activités restantes sur la station suivante du réseau de cinq stations ; vérifier sa bande de base et sa poursuite | station : ______ | ☐ | |
| 5 | Remplir une fiche d'anomalie | fiche n° : ____ | ☐ | |

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
| Engagements client tenus / reportés | |
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
