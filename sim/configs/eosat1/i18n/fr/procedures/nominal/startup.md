# NOM-001 : Ouverture de passage
**Sous-système :** ALL
**Phase :** NOMINAL
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Établir des communications sol-bord complètes à l'AOS et vérifier que tous les
sous-systèmes sont dans un état nominal sain avant d'engager les activités du passage
(prise de vue, vidage des données ou maintenance). Cette procédure est exécutée au début de
chaque contact sol programmé.

## Prérequis
- [ ] Antenne de la station sol en acquisition et en poursuite d'EOSAT-1
- [ ] Plan de passage revu et envoyé au MCS
- [ ] Prévision de trajectoire de la dynamique du vol à jour (datant de < 4 h)
- [ ] Directeur de vol à la console et boucle de communication confirmée

## Déroulement

### Étape 1 --- Vérifier l'état de l'OBC
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- demander les données de servitude OBDH
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) sous 10 s
**Verify:** `obdh.cpu_load` (0x0302) < 80 % sous 10 s
**Verify:** `obdh.uptime` (0x0308) cohérent avec la dernière valeur connue
**GO/NO-GO:** Si `obdh.mode` != 0, interrompre le passage et exécuter CTG-010 Reprise de l'OBC.

### Étape 2 --- Vérifier la santé de l'EPS
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- demander les données de servitude EPS
**Verify:** `eps.bat_soc` (0x0101) > 50 % sous 10 s
**Verify:** `eps.bus_voltage` (0x0105) > 27.0 V sous 10 s
**Verify:** `eps.power_gen` (0x0107) > `eps.power_cons` (0x0106) (marge de puissance positive)
**GO/NO-GO:** Si SoC < 50 % ou tension du bus < 27 V, exécuter la procédure CTG-005 Mode survie
EPS. NE PAS poursuivre les opérations de charge utile.

### Étape 3 --- Vérifier le pointage AOCS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- demander les données de servitude AOCS
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL, suivi du nadir) sous 10 s
**Verify:** `aocs.att_error` (0x0217) < 1.0 deg sous 10 s si la convergence est déjà acquise ;
admettre jusqu'à 400 s de reconvergence après une perturbation (phase C : stabilisation réelle,
4/(ζωn) ≈ 140 s plus l'arc d'acquisition à vitesse limitée)
**Verify:** |`aocs.rate_roll`| (0x0204) < 0.05 deg/s
**Verify:** `aocs.rate_pitch` (0x0205) = -0.063 ± 0.02 deg/s (le suivi du nadir
impose la vitesse orbitale autour de l'axe -Y satellite — une vitesse de tangage nulle signifierait ici que
le satellite NE suit PAS le nadir)
**Verify:** |`aocs.rate_yaw`| (0x0206) < 0.05 deg/s
**GO/NO-GO:** Si l'erreur d'attitude > 1 deg ou si une vitesse > 0.1 deg/s, se mettre en attente et
évaluer. Envisager d'exécuter NOM-007 Gestion du moment cinétique avant de continuer.

### Étape 4 --- Établir la liaison TTC
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1) --- activer le transpondeur principal
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) sous 15 s
**Verify:** page TT&C (sol) : `ttc.rssi` (0x0502) > -126 dBm sous 15 s
**Verify:** page TT&C (sol) : `ttc.link_margin` (0x0503) > 3.0 dB sous 15 s
**GO/NO-GO:** Si la liaison n'est pas établie sous 15 s, commander `TTC_SWITCH_REDUNDANT`
et répéter la vérification. Si le transpondeur redondant échoue aussi, déclarer une anomalie TTC.

### Étape 5 --- Collecte complète des données de servitude
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) --- TCS
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- OBDH
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- TTC
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- charge utile
**Verify:** les 6 paquets HK sont reçus sous 30 s
**Verify:** aucun paramètre hors limites signalé par le contrôle de limites du MCS

### Étape 6 --- Préparation de la charge utile (si une prise de vue ou un vidage est prévu)
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1) --- commander STANDBY
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) sous 20 s
**Verify:** `tcs.temp_fpa` (0x0408) en baisse (refroidisseur actif)
**Verify:** `payload.store_used` (0x0604) < 90 % (stockage suffisant)
**Note:** NE PAS commander IMAGING tant que la température du FPA n'est pas < -10 °C (voir NOM-002).

### Étape 7 --- Déclaration de disponibilité pour le passage
**Jalon GO/NO-GO --- Tour de table du directeur de vol :**
- EPS : SoC > 50 %, tension du bus > 27 V, marge de puissance positive --- GO / NO-GO
- AOCS : NOMINAL, att_error < 1 deg, vitesses < 0.05 deg/s --- GO / NO-GO
- TTC : liaison UP, RSSI > -100 dBm, marge > 3 dB --- GO / NO-GO
- TCS : toutes les températures dans les limites nominales --- GO / NO-GO
- OBDH : NOMINAL, CPU < 80 % --- GO / NO-GO
- Charge utile : STANDBY (si requis), stockage < 90 % --- GO / NO-GO

**Décision :** Si tout est GO, engager les activités prévues du passage. Si un poste est NO-GO,
exécuter la procédure hors nominal correspondante avant de continuer.

## Conduite à tenir hors nominal
- Si `eps.bat_soc` < 30 % : exécuter immédiatement CTG-005 Reprise après mode survie EPS.
- Si `aocs.mode` = 2 (SAFE) : exécuter CTG-002 Reprise après anomalie SCAO.
- Si les voies TTC principale et redondante échouent toutes deux : déclarer la perte de communication ; attendre le passage suivant.
- Si `obdh.cpu_load` > 90 % : rechercher un processus emballé ; envisager une réinitialisation de l'OBC.
- Si un paquet HK n'est pas reçu : le redemander une fois ; s'il manque toujours, signaler le sous-système.

## Postconditions
- [ ] Tous les sous-systèmes confirmés NOMINAL
- [ ] Liaison TTC établie avec une marge > 3 dB
- [ ] Jeu complet de données de servitude collecté et archivé
- [ ] Charge utile en STANDBY (si des opérations sont prévues)
- [ ] Le directeur de vol a déclaré le passage GO
