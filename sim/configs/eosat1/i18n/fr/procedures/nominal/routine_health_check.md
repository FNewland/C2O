# NOM-009 : Bilan de santé de routine
**Sous-système :** ALL
**Phase :** NOMINAL
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Réaliser une évaluation complète de la santé de tous les sous-systèmes du satellite en
collectant et en évaluant la télémesure de servitude des six identifiants de service HK.
Cette procédure est une activité de surveillance passive --- aucune commande n'est envoyée
sauf détection d'une anomalie. Elle est exécutée au moins une fois par contact sol
et constitue le principal outil de détection précoce des anomalies et d'analyse de tendance.

## Prérequis
- [ ] Liaison TTC établie : `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Base de données du contrôle de limites du MCS chargée avec les jeux de limites en vigueur
- [ ] Référence HK du passage précédent disponible pour la comparaison de tendance
- [ ] L'opérateur a accès à l'affichage des tendances et au journal des anomalies

## Déroulement

### Étape 1 --- Demander tous les paquets de servitude
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- données de servitude EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- données de servitude AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) --- données de servitude TCS
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- données de servitude OBDH
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- données de servitude de la charge utile
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- données de servitude TT&C
**Verify:** les 6 paquets HK sont reçus sous 30 s
**Action:** Si un paquet manque, le redemander une fois après un délai de 15 s.

### Étape 2 --- Évaluation de la santé de l'EPS
**Verify:** `eps.bat_soc` (0x0101) > 40 % --- plage NOMINAL 40-100 %
**Verify:** `eps.bus_voltage` (0x0105) dans la plage 30.9 - 34.0 V
**Verify:** `eps.power_gen` (0x0107) > 0 W (au Soleil ; 0 W acceptable en éclipse)
**Verify:** `eps.power_cons` (0x0106) < 350 W (bilan nominal du bus)
**Verify:** Marge de puissance : `eps.power_gen` - `eps.power_cons` > -50 W
**Tendance :** Comparer le SoC au passage précédent --- variation attendue < 10 % par orbite.
**Signaler :** Si le SoC tend à baisser sur plusieurs passages, analyser l'équilibre de puissance.

### Étape 3 --- Évaluation de la santé de l'AOCS
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL)
**Verify:** `aocs.att_error` (0x0217) < 1.0 deg
**Verify:** `aocs.rate_roll` (0x0204) < 0.05 deg/s
**Verify:** `aocs.rate_pitch` (0x0205) dans la plage [0.043, 0.083] deg/s (le suivi du nadir impose la vitesse orbitale, +0.063 deg/s sur cette console ; une vitesse de tangage nulle signifierait que le satellite NE suit PAS le nadir)
**Verify:** `aocs.rate_yaw` (0x0206) < 0.05 deg/s
**Verify:** |`aocs.rw1_speed`| (0x0207) < 5000 tr/min
**Verify:** |`aocs.rw2_speed`| (0x0208) < 5000 tr/min
**Verify:** |`aocs.rw3_speed`| (0x0209) < 5000 tr/min
**Verify:** |`aocs.rw4_speed`| (0x020A) < 5000 tr/min
**Tendance :** Comparer les vitesses des roues au passage précédent. Une hausse monotone indique
  une désaturation insuffisante --- programmer NOM-007 (Gestion du moment cinétique).
**Signaler :** Si une roue > 4500 tr/min, recommander une désaturation immédiate.

### Étape 4 --- Évaluation de la santé du TCS
**Verify:** `tcs.temp_obc` (0x0406) dans la plage -10.0 à +50.0 °C
**Verify:** `tcs.temp_battery` (0x0407) dans la plage +5.0 à +35.0 °C
**Verify:** `tcs.temp_fpa` (0x0408) < 0.0 °C (si le refroidisseur est actif, s'attendre à < -25 °C)
**Verify:** `tcs.htr_battery` (0x040A) = état attendu (thermostat : ON à <= +5 °C, OFF à >= +10 °C ; entre les consignes, l'état précédent se maintient)
**Verify:** `tcs.cooler_fpa` (0x040C) = état attendu (ON si la charge utile n'est pas OFF)
**Tendance :** Comparer la température de la batterie à la position orbitale --- elle doit suivre
  un schéma éclipse/soleil prévisible.
**Signaler :** Si la température de la batterie sort de +5 à +35 °C, analyser le réchauffeur et le chemin thermique.

### Étape 5 --- Évaluation de la santé de l'OBDH
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL)
**Verify:** `obdh.cpu_load` (0x0302) < 80 %
**Verify:** `obdh.uptime` (0x0308) cohérent avec la valeur attendue (aucun redémarrage
  inattendu --- l'uptime doit croître de façon monotone depuis la dernière réinitialisation connue)
**Tendance :** La charge CPU doit être stable. Une tendance à la hausse peut indiquer une fuite mémoire
  ou une tâche emballée.
**Signaler :** Si l'uptime est anormalement bas, une réinitialisation de l'OBC s'est produite --- en rechercher
  la cause dans le journal des événements.

### Étape 6 --- Évaluation de la santé du TTC
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED)
**Verify:** page TT&C (sol) : `ttc.rssi` (0x0502) > -126 dBm
**Verify:** page TT&C (sol) : `ttc.link_margin` (0x0503) > 2.0 dB
**Tendance :** Le RSSI doit suivre le profil de passage attendu (hausse jusqu'au TCA, baisse
  ensuite). Un RSSI durablement faible peut indiquer une dégradation de l'antenne.
**Signaler :** Si la marge de liaison < 2.0 dB à haute élévation, analyser la chaîne RF.

### Étape 7 --- Évaluation de la santé de la charge utile
**Verify:** `payload.mode` (0x0600) = état attendu (0=OFF, 1=STANDBY, 2=IMAGING)
**Verify:** `payload.fpa_temp` (0x0601) dans la plage attendue pour le mode actuel
**Verify:** `payload.store_used` (0x0604) < 95 % (seuil d'alerte)
**Verify:** `payload.image_count` (0x0605) correspond au nombre attendu d'après le plan de passage
**Tendance :** L'occupation de la mémoire doit baisser après les passages de vidage et augmenter après les
  passages de prise de vue. Des variations inattendues indiquent une anomalie.
**Signaler :** Si le stockage > 90 %, donner la priorité au vidage au prochain passage disponible.

### Étape 8 --- Synthèse et consignation des anomalies
**Action:** Établir la synthèse de l'évaluation de santé :
  - EPS : SoC=___%, bus=___V, marge=___W --- NOMINAL / CAUTION / WARNING
  - AOCS : mode=___, att_err=___deg, max_rw=___RPM --- NOMINAL / CAUTION / WARNING
  - TCS : OBC=___C, batterie=___C, FPA=___C --- NOMINAL / CAUTION / WARNING
  - OBDH : mode=___, CPU=___%, uptime=___s --- NOMINAL / CAUTION / WARNING
  - TTC : RSSI=___dBm, marge=___dB --- NOMINAL / CAUTION / WARNING
  - Charge utile : mode=___, mémoire=___%, images=___ --- NOMINAL / CAUTION / WARNING
**Consigner :** Inscrire toutes les valeurs de paramètres et tous les signalements dans le journal de santé du passage.
**Action:** Si un paramètre est signalé CAUTION ou WARNING, informer le directeur de vol
  et indiquer la procédure de contingence ou la procédure corrective nominale appropriée.

## Conduite à tenir hors nominal
- Si un paquet HK n'est pas reçu après deux demandes : signaler une anomalie de communication
  du sous-système. Vérifier le routage des paquets par l'OBDH et l'intégrité de la liaison TTC.
- Si un paramètre atteint une limite WARNING (rouge) : informer immédiatement le directeur de vol.
  Exécuter la procédure de contingence correspondante sans attendre la fin de l'évaluation.
- Si plusieurs sous-systèmes sont simultanément en CAUTION : cela peut indiquer un problème
  systémique (puissance, thermique ou OBC). Corréler les paramètres avant d'agir.
- Aucune commande n'est envoyée dans cette procédure, sauf détection d'une anomalie de niveau WARNING
  exigeant une réponse immédiate.

## Postconditions
- [ ] Les 6 paquets HK collectés et archivés
- [ ] Tous les paramètres contrôlés par rapport aux limites nominales
- [ ] Comparaison de tendance avec le passage précédent effectuée
- [ ] Journal des anomalies mis à jour (entrées ajoutées en cas de signalement)
- [ ] Directeur de vol informé de l'état de santé global du satellite
- [ ] Actions correctives programmées en cas de signalement CAUTION
