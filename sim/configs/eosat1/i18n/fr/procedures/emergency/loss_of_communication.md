# EMG-004 : Perte de communication
**Sous-système :** TT&C / Ground Segment
**Phase :** EMERGENCY
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Procédure de reprise lorsqu'aucune télémesure n'a été reçue d'EOSAT-1 pendant au moins deux
fenêtres de passage consécutives. Cette procédure définit une escalade structurée allant de la vérification
des stations sol à la commande en aveugle, puis à l'évaluation de la reprise autonome,
avec des jalons de décision à 6 h, 12 h, 24 h et 48 h écoulées depuis le dernier contact.

## Prérequis
- [ ] Perte de télémesure confirmée pendant >= 2 fenêtres de passage consécutives (~3 heures)
- [ ] Page d'état du réseau de stations sol consultée pour les interruptions planifiées
- [ ] Jeu d'éléments à deux lignes (TLE) à jour disponible (propagé il y a < 24 h)
- [ ] Pile de commandes en aveugle préparée et validée sur simulateur
- [ ] Directeur de vol à la console et équipe d'intervention d'urgence prévenue

## Déroulement

### Étape 1 --- Vérifier l'infrastructure des stations sol
**Action:** Confirmer l'état opérationnel de toutes les stations sol principales.
**Contrôler :** État des liaisons d'Iqaluit (IQ1) et de Troll (TR1).
**Verify:** Étalonnage du pointage des antennes nominal ; seuil de verrouillage du récepteur réglé au minimum (-130 dBm).
**GO/NO-GO:** Au moins deux stations sol pleinement opérationnelles avec une visibilité dégagée pour le prochain passage.

### Étape 2 --- Tenter le contact sur toutes les stations sol disponibles
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- émise en aveugle à chaque passage.
**Séquence :** Programmer des tentatives en liaison montante à chaque passage visible (élévation minimale 5 deg) sur
Iqaluit et Troll, par ordre de priorité selon l'élévation maximale.
**Verify:** `ttc.rssi` (0x0502) > -125 dBm et `ttc.link_status` (0x0501) = 2 (LOCKED) dans les 30 s qui suivent l'AOS.
**GO/NO-GO:** Si une télémesure est reçue sur une station quelconque, sortir de l'urgence et effectuer l'évaluation selon EMG-001. Sans réponse après une rotation complète des stations sol, la commande en aveugle sur le transpondeur principal (étape 3) s'applique. -> GO `STEP-END` | NO-GO `STEP-3`

### Étape 3 --- Commande en aveugle sur le transpondeur principal
**LABEL:** `STEP-3`
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1, func_id 63) --- en aveugle, répétée 3x à 10 s d'intervalle.
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- émise 15 s après la commande de basculement.
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) sous 45 s.
**Chronologie :** Exécuter lors d'un passage d'élévation > 20 deg pour maximiser la marge de liaison.
**GO/NO-GO:** Si la liaison est acquise, effectuer un vidage HK complet. Sans réponse, la commande en aveugle sur le transpondeur redondant (étape 4) s'applique.
**BRANCH:** `ttc.link_status == 2` -> GO `STEP-END` | NO-GO `STEP-4` (timeout 45 s)

### Étape 4 --- Commande en aveugle sur le transpondeur redondant
**LABEL:** `STEP-4`
**TC:** `TTC_SWITCH_REDUNDANT` (Service 8, Subtype 1, func_id 64) --- en aveugle, répétée 3x à 10 s
d'intervalle. (Était annotée Subtype 2 ; toute exécution de fonction S8 est en Subtype 1.)
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- émise 15 s après la commande de basculement.
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) sous 45 s.
**Chronologie :** Exécuter au prochain passage disponible à forte élévation (> 20 deg).
**GO/NO-GO:** Si la liaison est acquise, rester sur le transpondeur redondant et évaluer le principal. Sans réponse, l'attente du temporisateur de reprise autonome (étape 5) s'applique.
**BRANCH:** `ttc.link_status == 2` -> GO `STEP-END` | NO-GO `STEP-5` (timeout 45 s)

### Étape 5 --- Attendre le temporisateur de reprise autonome
**LABEL:** `STEP-5`
**Action:** L'autonomie de bord d'EOSAT-1 déclenche une séquence de reprise des communications après 6 heures
sans contact sol. Le satellite passe successivement par différentes configurations de transpondeur et
augmente la puissance de la balise.
**Surveiller :** Toutes les stations sol en écoute seule sur les fréquences principale et redondante.
**Verify:** Détection de la balise sur une station quelconque --- relevés de `ttc.rssi` (0x0502) consignés en continu.
**Durée :** Attendre au moins 4 périodes orbitales (~6,3 heures) après l'activation prévue du temporisateur de bord.

### Étape 6 --- Campagne ciblée sur les passages polaires (seuil de 12 h)
**Action:** Si 12 heures se sont écoulées depuis le dernier contact, concentrer toutes les ressources sur les stations
de haute latitude offrant une géométrie optimale.
**Stations :** Iqaluit et Troll --- toutes deux assurent une couverture de passages quasi polaires toutes les ~95 min.
**Note:** Alterner entre les deux transpondeurs d'un passage à l'autre : envoyer la
sélection du principal à un passage et la sélection du redondant au suivant.
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1, func_id 63) --- passages impairs
**TC:** `TTC_SWITCH_REDUNDANT` (Service 8, Subtype 1, func_id 64) --- passages pairs
**TC:** `OBC_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 50) --- commande en aveugle du mode d'urgence.
(Était annotée Subtype 3, qui n'est pas un sous-type S8 traité par cette suite.)
**Verify:** Tout signal descendant pendant la fenêtre de passage.
**GO/NO-GO:** Si le contact est rétabli, enchaîner sur EMG-001 pour la reprise après mode survie.

### Étape 7 --- Escalade vers le réseau d'urgence (seuil de 24 h)
**Action:** Demander l'appui des stations sol d'agences partenaires (ESA ESTRACK, NASA NEN).
**Développer :** Ajouter les stations de Malindi, Maspalomas et South Point au planning de poursuite.
**Note:** Poursuivre la rotation de commandes en aveugle de l'étape 6 à tous les passages --- les
commandes sont `TTC_SWITCH_PRIMARY` (func 63) et `TTC_SWITCH_REDUNDANT`
(func 64), en alternance. Rien de nouveau n'est envoyé ici ; cette étape ne comporte donc pas
de ligne `**TC:**` propre.
**Informer :** Le Space Debris Office de l'ESA d'un possible statut d'engin spatial non contrôlé.
**GO/NO-GO:** Si 24 h sont dépassées sans contact, réunir la commission d'examen des anomalies.

### Étape 8 --- Évaluation de la perte prolongée (seuil de 48 h)
**Action:** Si 48 heures se sont écoulées sans signal sur aucune station ni fréquence :
**Évaluer :** Le satellite est peut-être en coupure sur sous-tension ou en culbutage irrécupérable.
**Radar :** Demander une poursuite par radar de surveillance de l'espace pour confirmer l'orbite et l'état d'attitude.
**Planifier :** Élaborer un plan de reprise à long terme en supposant que le satellite ne quittera le mode survie que lorsque
des conditions de bilan de puissance positif reviendront (phase orbitale éclairée avec un angle bêta favorable).
**Surveiller :** Maintenir une campagne d'écoute passive pendant au moins 30 jours.

## Synthèse de l'arbre de décision
| Temps écoulé | Action | Escalade |
|---|---|---|
| 0--6 h | Passer par toutes les stations sol, commander en aveugle les deux transpondeurs | Directeur de vol |
| 6--12 h | Attendre le temporisateur de reprise autonome de bord | Équipe d'intervention d'urgence |
| 12--24 h | Campagne ciblée sur les passages polaires, commande en aveugle du mode d'urgence | Responsable de mission |
| 24--48 h | Escalade vers le réseau d'urgence, appui d'agences partenaires | Commission d'examen des anomalies |
| >48 h | Évaluation de la perte prolongée, poursuite radar, écoute de 30 jours | Directeur de programme |

## Conduite à tenir hors nominal
- Si une panne matérielle de station sol est confirmée : basculer sur la source (feed) d'antenne de secours ; contacter l'exploitant de la station pour une maintenance d'urgence.
- Si le satellite est détecté par radar mais sans signal RF : supposer une panne totale des transpondeurs ; prévoir une liaison montante sur la voie de secours en bande S si elle existe.
- Si la télémesure est reçue mais corrompue ou fragmentée : redescendre l'échelle des débits TM jusqu'à LOW
  (`TTC_SET_DATA_RATE(rate=0)`, func_id 65 — 16 kbit/s BPSK conv(7,1/2)+RS, ce qui apporte à la fois
  9,03 dB de marge de débit et 1,5 dB de gain de codage supplémentaire par rapport à HIGH). Si la liaison
  ne se verrouille toujours pas, commander le mode balise (`TTC_SET_BEACON_MODE(on=1)`, func_id 70) :
  il impose l'échelon SAFE (ex-BEACON) — 1 000 bit/s, 1 kBd, ~3,1 kHz de largeur de bande occupée —, qui est
  la forme d'onde la plus étroite et la plus robuste dont dispose le satellite. Reconfigurer le démodulateur
  sol à 1 kBd avant d'attendre un verrouillage.
- Si l'orbite du satellite a nettement décru par rapport à la prévision : récupérer un nouveau TLE auprès du réseau de surveillance de l'espace avant la prochaine tentative de passage.

## Postconditions
**LABEL:** `STEP-END`
- [ ] Communication bidirectionnelle rétablie sur au moins un transpondeur
- [ ] `ttc.mode` (0x0500) confirmé en NOMINAL ou SAFE
- [ ] `ttc.link_status` (0x0501) = 2 (LOCKED) avec un `ttc.rssi` (0x0502) stable > -120 dBm
- [ ] Vidage complet des données de servitude (tous les SID 1--6) reçu et examiné
- [ ] Cause racine de la perte de communication identifiée ou analyse lancée
- [ ] Transition vers EMG-001 pour le rétablissement par étapes si le satellite était en mode survie autonome
