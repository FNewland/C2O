# NOM-012 : Passation de consignes

**Catégorie :** Nominal
**Poste responsable :** directeur de vol
**Postes associés :** tous les postes (EPS/TCS, AOCS, TT&C, charge utile, FDIR/systèmes)
**Difficulté :** Débutant

## Objectif
Exécuter une passation de consignes structurée entre le directeur de vol sortant et le directeur de vol entrant. Cette
procédure garantit que tous les états des sous-systèmes sont passés en revue, que les alarmes en attente sont acquittées ou
traitées, que les prochains contacts avec les stations sol et les commandes programmées sont vérifiés, et que
la connaissance de la situation opérationnelle est entièrement transmise à l'équipe du quart entrant.

## Prérequis
- [ ] Directeur de vol entrant et équipe du quart présents aux consoles
- [ ] Tous les opérateurs de poste ont préparé la synthèse de l'état de leur sous-système
- [ ] Journal de passage du quart en cours à jour
- [ ] Aucune procédure d'urgence active en cours (si une urgence est active, la passation
  doit explicitement porter sur l'état de l'urgence et les actions en cours)

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| obdh.mode | 0x0300 | 0 (NOMINAL) ou mode actuel |
| eps.bat_soc | 0x0101 | Valeur actuelle (à consigner) |
| eps.bus_voltage | 0x0105 | > 28.0 V en nominal |
| eps.power_gen | 0x0107 | Valeur actuelle |
| eps.power_cons | 0x0106 | Valeur actuelle |
| eps.eclipse_flag | 0x0108 | État soleil/éclipse actuel |
| aocs.mode | 0x020F | Mode AOCS actuel |
| aocs.att_error | 0x0217 | < 0.1 deg en nominal |
| tcs.temp_battery | 0x0407 | Entre 0 et 40 °C |
| tcs.temp_fpa | 0x0408 | Valeur actuelle |
| ttc.link_status | 0x0501 | État actuel de la liaison |
| ttc.tm_data_rate | 0x0506 | Débit actif — attendu : 16000 bit/s (LOW) en opérations de routine |
| ttc.tm_tier | 0x0539 | Palier ACTIF (0=SAFE, 1=LOW, 2=HIGH) |
| ttc.tm_tier_cmd | 0x053A | Palier COMMANDÉ — doit être égal à 0x0539 à la passation |
| ttc.downlink_mode | 0x053C | 0 attendu hors vidage |
| payload.mode | 0x0600 | Mode actuel de la charge utile |
| payload.store_used | 0x0604 | Niveau actuel de la mémoire |
| obdh.reboot_count | 0x030A | Valeur actuelle |
| obdh.tc_rej_count | 0x0306 | Valeur actuelle |

## Commandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| LIST_SCHEDULE | 11 | 17 | — | Demander la synthèse du plan bord |

## Déroulement

### Étape 1 : Passer en revue l'état de tous les sous-systèmes
**Note:** Demander une collecte complète des données de servitude de tous les sous-systèmes. Les SID sont
ceux de `hk_structures.yaml` : 1 EPS, 2 AOCS, 3 TCS, 4 plateforme/OBDH, 5 charge utile,
6 TT&C. (Cette fiche les présentait auparavant sous forme d'un bloc de puces **Action:**, que
l'extracteur ne sait pas lire, et en inversant 5 et 6.)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — données de servitude EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — données de servitude AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — données de servitude TCS
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — données de servitude plateforme/OBDH
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — données de servitude de la charge utile
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — données de servitude TT&C
**Verify:** `obdh.mode` (0x0300) — consigner et annoncer le mode actuel de l'OBC
**Verify:** `eps.bat_soc` (0x0101), `eps.bus_voltage` (0x0105), `eps.power_gen` (0x0107),
`eps.power_cons` (0x0106) — consigner la synthèse du bilan de puissance
**Verify:** `aocs.mode` (0x020F), `aocs.att_error` (0x0217) — consigner l'état d'attitude
**Verify:** `tcs.temp_battery` (0x0407), `tcs.temp_obc` (0x0406) — consigner l'état thermique
**Verify:** `ttc.link_status` (0x0501) — consigner l'état de la liaison
**Verify:** `payload.mode` (0x0600), `payload.store_used` (0x0604) — consigner l'état de la charge utile
**Action:** Chaque opérateur de poste présente oralement une synthèse de l'état à l'équipe entrante :
- EPS/TCS : bilan de puissance, tendance de la batterie, état thermique, activité des réchauffeurs
- AOCS : mode d'attitude, précision de pointage, vitesses des roues, état du moment cinétique
- TT&C : état de la liaison, prochaine fenêtre de contact, état de l'échelle des débits TM — le palier ACTIF
  (0x0539), le palier COMMANDÉ (0x053A) et leur concordance. Une passation qui laisse
  le satellite commandé en HIGH avec le mode DOWNLINK verrouillé est une passation qui laisse
  une porte ouverte ; les opérations de routine se font en LOW avec `ttc.downlink_mode` (0x053C) = 0
- Charge utile : état des prises de vue, capacité de stockage, vidages en attente
- FDIR/systèmes : santé de l'OBC, nombre de redémarrages, occupation mémoire, règles FDIR actives
**GO/NO-GO:** Tous les états des sous-systèmes passés en revue et compris par l'équipe entrante — continuer.

### Étape 2 : Vérifier les alarmes et anomalies en attente
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — examiner le tampon d'alarmes via les HK OBDH — ,
ou examiner l'affichage des alarmes sur la console du MCS.
**Verify:** `obdh.alarm_buf_fill` (0x0314) — consigner le niveau
**Verify:** `obdh.tc_rej_count` (0x0306) — consigner la valeur, la comparer à la référence de début de quart
**Action:** Le FD sortant informe le FD entrant :
- de toute violation de limite ou de tout avertissement actif ;
- de toute alarme acquittée mais non encore résolue ;
- de tout paramètre surveillé en raison d'une tendance préoccupante ;
- de toute télécommande rejetée et de la suite qui lui a été donnée ;
- de toute action FDIR déclenchée pendant le quart.
**Action:** Le FD entrant confirme avoir compris tous les points en attente.
**GO/NO-GO:** Toutes les alarmes passées en revue et traitées — continuer.

### Étape 3 : Passer en revue les prochains contacts avec les stations sol
**Action:** Passer en revue le planning des contacts avec les stations sol pour les 12 prochaines heures.
**Verify:** Prochaine fenêtre de contact : station, heures d'AOS/LOS, élévation maximale
**Verify:** Activités prévues pour chaque contact (vidage HK, vidage des données, envoi de commandes)
**Verify:** Configuration de liaison requise (palier de débit TM, niveau de puissance du PA). Un passage prévu
pour un vidage de données enregistrées exige le palier HIGH, qui exige le mode DOWNLINK et une élévation
maximale d'au moins 10 deg — vérifier la géométrie du passage avant de promettre le vidage
**Action:** Si un contact exige une configuration particulière (p. ex. vidage à haut débit,
séance de mesure de distance), informer l'opérateur TT&C entrant des actions requises.
**GO/NO-GO:** Planning des contacts passé en revue et compris — continuer.

### Étape 4 : Vérifier les commandes enregistrées et le plan bord
**TC:** `LIST_SCHEDULE` (Service 11, Subtype 17) — demander la synthèse du plan bord
**Verify:** Passer en revue toutes les télécommandes datées du plan :
- confirmer que toutes les commandes programmées sont toujours valides et voulues ;
- vérifier les heures d'exécution par rapport à la prévision d'orbite mise à jour ;
- identifier les commandes à supprimer ou à modifier.
**Verify:** `obdh.hktm_buf_fill` (0x0312) — consigner l'état du tampon HK/TM
**Verify:** `obdh.event_buf_fill` (0x0313) — consigner l'état du tampon d'événements
**Action:** Si des commandes programmées doivent être modifiées, le FD entrant se coordonne avec
l'opérateur de poste concerné pour les mettre à jour.
**GO/NO-GO:** Plan bord passé en revue et confirmé — continuer.

### Étape 5 : Déclaration formelle de passation
**Action:** Le FD sortant déclare oralement :
- la synthèse des faits marquants du quart (anomalies, procédures exécutées, événements notables) ;
- les actions ouvertes et leurs responsables ;
- les contraintes ou préoccupations pour le quart à venir ;
- les activités différées et leur justification.
**Action:** Le FD entrant confirme oralement :
- sa compréhension de l'état actuel du satellite ;
- son acceptation de toutes les actions ouvertes ;
- sa connaissance des activités prévues à venir.
**Action:** Les deux FD consignent l'heure de la passation et leurs signatures dans le journal de passage.
**Verify:** Le FD entrant confirme qu'il détient l'autorité et la responsabilité.
**GO/NO-GO:** Passation terminée — le FD entrant prend la console.

## Critères de vérification
- [ ] Les six rapports HK des sous-systèmes passés en revue et consignés
- [ ] Toutes les alarmes en attente passées en revue et traitées
- [ ] Planning des contacts des 12 prochaines heures passé en revue
- [ ] Plan bord des commandes vérifié
- [ ] Déclaration formelle de passation consignée avec horodatage
- [ ] Journal de passage mis à jour et signé par les deux directeurs de vol

## Contingence
- Si une anomalie est détectée pendant la collecte HK de la passation : suspendre la passation. Le FD sortant
  conserve l'autorité et dirige le traitement de l'anomalie. La passation reprend une fois l'anomalie
  traitée ou stabilisée.
- Si une alarme critique se déclenche pendant la passation : le FD sortant conserve l'autorité jusqu'à ce que
  l'alarme soit résolue ou que la situation soit assez stable pour être transmise. Les deux FD peuvent
  se coordonner pendant cette période.
- Si la télémesure est indisponible (pas de liaison) : la passation se fait sur la base du dernier
  état de télémesure connu. Le FD entrant est informé de la lacune et du prochain contact prévu. Toutes
  les dernières valeurs connues sont clairement identifiées comme périmées.
