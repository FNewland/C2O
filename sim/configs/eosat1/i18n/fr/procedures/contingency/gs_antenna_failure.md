# CTG-020 : Panne d'antenne de station sol

**Catégorie :** Contingence
**Poste responsable :** TT&C
**Postes associés :** Directeur de vol
**Difficulté :** Intermédiaire

## Objectif
Traiter une panne d'équipement de station sol provoquant une perte du signal pendant un
passage. Cette procédure guide l'opérateur pour confirmer que l'anomalie se situe
côté sol (et non à bord du satellite), se coordonner avec le directeur de vol pour basculer
sur une station sol de secours et gérer l'impact opérationnel d'une fenêtre de contact perdue ou
écourtée.

## Prérequis
- [ ] La liaison était établie et nominale avant la perte du signal
- [ ] La perte du signal est soudaine et totale (pas de dégradation progressive)
- [ ] La télémesure TTC du satellite était nominale juste avant la coupure
- [ ] Le directeur de vol est en console et disponible pour la coordination
- [ ] Les coordonnées de la station sol de secours sont disponibles

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| ttc.link_status | 0x0501 | 0 (NO_LINK) — était à 2 (LOCKED) avant la panne |
| ttc.rssi | 0x0502 | Tombé sous le seuil du récepteur |
| ttc.link_margin | 0x0503 | Était > 3 dB avant la panne |
| ttc.carrier_lock | 0x0510 | 0 (perdue) — était à 1 avant la panne |
| ttc.contact_elevation | 0x050A | Consigner la valeur au moment de la perte |
| ttc.gs_equipment_status | 0x0524 | Masque binaire de l'état des équipements de la station sol |
| ttc.active_gs | 0x0523 | Indice de la station sol courante |

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | -- | Demander un rapport HK ponctuel (en aveugle) |
| CONNECTION_TEST | 17 | 1 | -- | Test de connexion S17 (en aveugle) |

## Déroulement

### Étape 1 : Confirmer que la perte du signal ne vient pas du satellite
**Action:** Examiner la dernière trame de télémesure reçue avant la perte du signal :
- `ttc.rssi` (0x0502) — était-il nominal (> -90 dBm) ?
- `ttc.link_margin` (0x0503) — était-elle saine (> 3 dB) ?
- `ttc.pa_on` (0x0516) — le PA était-il actif ?
- `ttc.pa_temp` (0x050F) — la température du PA était-elle normale (< 55 °C) ?
**Action:** Examiner les caractéristiques de la perte du signal :
- chute soudaine au niveau du plancher de bruit = panne d'équipement (antenne, LNA, câblage) ;
- dégradation progressive = problème atmosphérique, de pointage ou du satellite.
**Action:** Vérifier l'état de poursuite de l'antenne de la station sol :
- l'antenne est-elle toujours en poursuite ? Rechercher des défauts sur le contrôleur d'antenne ;
- la source et le LNA sont-ils alimentés ? Consulter le tableau d'état des équipements de la station sol.
**Action:** Contrôler la chaîne de réception de la station sol :
- alimentation du LNA ;
- état de verrouillage du convertisseur abaisseur de fréquence ;
- traitement FI/bande de base.
**Note:** Une chute de signal de 30 dB avec un satellite sain indique fortement une panne
d'équipement de la station sol (panne d'entraînement d'antenne, panne du LNA ou défaut de la source).
**GO/NO-GO:** Panne d'équipement de la station sol confirmée (ou fortement suspectée) — l'étape 2 s'applique. Si le satellite est suspecté, appliquer plutôt CTG-019 ou CTG-003. -> GO `STEP-2` | NO-GO `STEP-END`

### Étape 2 : Tenter un rétablissement local de la station sol
**LABEL:** `STEP-2`
**Action:** Vérifier si l'antenne peut être réinitialisée ou repointée :
- lancer une réinitialisation du contrôleur d'antenne si elle est disponible ;
- commander la réacquisition de la poursuite du satellite.
**Action:** En cas de suspicion de panne du LNA ou de la chaîne de réception :
- basculer sur le LNA de secours s'il existe ;
- contrôler toutes les connexions des câbles RF et les alimentations.
**Action:** Attendre jusqu'à 2 minutes le résultat de la tentative de rétablissement local de la station.
**Verify:** Vérifier le retour du signal sur le récepteur.
**Note:** Pendant la tentative de rétablissement de la station, le satellite continue d'émettre normalement.
Aucune donnée n'est perdue à bord — les données HK et charge utile continuent d'être stockées dans
la mémoire de masse du satellite.
**GO/NO-GO:** Si la station se rétablit, reprendre les opérations du passage et consigner l'incident. Si la station ne se rétablit PAS en moins de 2 minutes, l'étape 3 s'applique. -> GO `STEP-END` | NO-GO `STEP-3`

### Étape 3 : Informer le directeur de vol et évaluer l'impact
**LABEL:** `STEP-3`
**Action:** Rendre compte au directeur de vol :
- « GS [station name] antenna failure confirmed at [time]. No spacecraft anomaly.
  Spacecraft is healthy, transmitting normally. Ground cannot receive. »
**Action:** Évaluer l'impact du contact perdu :
- combien de temps de passage reste-t-il sur la station courante ?
- des commandes critiques devaient-elles être envoyées pendant ce passage ?
- des données stockées doivent-elles être descendues en urgence ?
- des opérations à échéance critique sont-elles en attente (manœuvre orbitale, tâche charge utile) ?
**Action:** Si des commandes critiques étaient en attente :
- peuvent-elles attendre le prochain passage programmé ?
- existe-t-il une station de secours avec une visibilité qui se chevauche ou est proche ?
**GO/NO-GO:** Impact évalué — si des opérations critiques sont en attente, l'étape 4 s'applique immédiatement. En l'absence de besoin urgent, l'étape 5 (replanification) s'applique. -> GO `STEP-4` | NO-GO `STEP-5`

### Étape 4 : Coordonner le basculement sur une station sol de secours
**LABEL:** `STEP-4`
**Action:** Demander au directeur de vol d'autoriser le contact par une station sol de secours.
**Action:** Rechercher les prochaines fenêtres de passage disponibles sur les stations de secours :
- Troll (Antarctique) — vérifier la fenêtre de visibilité ;
- autres stations du réseau — vérifier la disponibilité et la programmation.
**Action:** Contacter les opérations de la station de secours :
- demander une réservation d'urgence ou prioritaire ;
- fournir les éléments orbitaux du satellite et le plan de fréquences ;
- confirmer les capacités de l'antenne (bande S, débits pris en charge).
**Action:** Si une station de secours a une fenêtre de passage dans les 30 minutes :
- préparer la passation : fournir les prévisions de passage, les fréquences, les données de pointage ;
- confirmer que la configuration des liaisons montante et descendante correspond aux réglages du satellite.
**Action:** Si aucun passage de secours n'est disponible à court terme :
- confirmer que les opérations autonomes du satellite le maintiendront dans un état sûr ;
- vérifier que le programme bord ne contient aucune commande critique exigeant une confirmation du sol.
**Note:** Le satellite ne sait pas qu'il a perdu le contact avec le sol. Il poursuit ses
opérations normales, y compris tout programme bord préchargé.
**GO/NO-GO:** Station de secours coordonnée — ou — aucune station de secours disponible, satellite
dans un état autonome sûr.

### Étape 5 : Replanifier le programme des contacts
**LABEL:** `STEP-5`
**Action:** Replanifier le programme des contacts avec le directeur de vol :
- retirer la station défaillante du programme à court terme jusqu'à confirmation de sa réparation ;
- ajouter des passages de remplacement sur les stations de secours ;
- évaluer l'impact cumulé sur le temps de contact au cours des 24-48 heures suivantes.
**Action:** Déterminer si des commandes bord doivent être mises à jour :
- tâches de prise de vue programmées supposant une liaison descendante disponible ;
- gestion de la batterie pendant une période prolongée sans contact ;
- capacité de stockage des données à bord (risque d'écrasement si les données ne sont pas descendues).
**Action:** Informer l'équipe d'ingénierie de la panne de la station pour réparation :
- fournir la description de la panne et son heure d'apparition ;
- demander une estimation du délai de réparation ;
- demander une confirmation avant de réintégrer la station dans le programme opérationnel.
**Action:** Consigner l'incident :
- heure de la panne de la station ;
- nom de la station et équipements touchés ;
- durée du contact perdu ;
- impact sur les opérations (commandes non envoyées, données non descendues) ;
- station de secours utilisée (le cas échéant).
**GO/NO-GO:** Programme replanifié, incident consigné — procédure terminée.

## Critères de vérification
**LABEL:** `STEP-END`
- [ ] Panne de la station sol confirmée comme cause racine (et non le satellite)
- [ ] Directeur de vol informé et impact évalué
- [ ] Station de secours coordonnée (si des opérations critiques étaient en attente)
- [ ] Programme des contacts replanifié en contournant la station défaillante
- [ ] Équipe d'ingénierie de la station sol informée pour réparation
- [ ] Rapport d'incident déposé avec tous les détails utiles

## Contingence
- Si la panne est ambiguë (impossible de trancher entre le sol et le satellite) : envoyer des commandes
  en aveugle par la station dégradée : `CONNECTION_TEST` (S17.1) et `HK_REQUEST(sid=5)`.
  Si plusieurs commandes en aveugle restent sans réponse et qu'une station de secours ne reçoit pas non plus de
  signal, le problème vient peut-être du satellite. Appliquer CTG-003.
- Si aucune station de secours n'est disponible pendant > 6 heures : vérifier la temporisation du mode
  survie autonome du satellite. Si la temporisation d'absence de contact de 24 heures doit expirer avant le
  prochain contact, le satellite passera en mode survie autonome. Prévoir la reprise
  en conséquence.
- Si plusieurs stations sol sont touchées simultanément : suspecter un problème au niveau du réseau
  (panne du NOC, interférence de fréquence, événement solaire). Faire remonter aus opérations du
  réseau et le directeur de vol.
- Si la station défaillante se rétablit partiellement (signal intermittent) : tenter d'envoyer
  les commandes les plus prioritaires pendant les fenêtres de signal. Maintenir la liaison descendante en LOW
  (16 kbit/s) : préparer `TTC_SET_DATA_RATE(rate=0)` (func_id 65) pour le prochain contact
  stable, et NE PAS planifier de vidage — le palier HIGH exige une élévation >= 10° et une
  station capable de tenir le verrouillage QPSK à 64 kBd.
- Si des commandes critiques à exécution différée figuraient dans le programme bord et doivent être
  annulées : elles ne peuvent pas l'être sans liaison montante. Évaluer les conséquences
  de l'exécution autonome de ces commandes programmées.
