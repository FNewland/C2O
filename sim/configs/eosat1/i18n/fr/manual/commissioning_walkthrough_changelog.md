# Déroulé de la recette en orbite — journal des modifications de développement

**Manual-Scope:** system — relevé des défauts trouvés et corrigés pendant la construction du système de formation. Ne fait pas partie du manuel d'opérations de vol.

Retiré de `commissioning_sequence_walkthrough.md` le 2026-08-21 : un manuel d'opérations décrit le satellite, et non l'historique de l'outil qui sert à s'y exercer.

---

## Problèmes connus du simulateur

Tous les problèmes signalés précédemment ont été résolus :

**Résolus (séance 1) :**
- ~~Déploiement de l'antenne en mode chargeur d'amorçage~~ — func_id 69 ajouté à la liste d'autorisation du chargeur d'amorçage
- ~~Références aux propulseurs sur l'écran TCS~~ — supprimées de `index.html`, `displays.yaml`, `tcs.yaml` et `hk_structures.yaml`
- **Contournement de la condition d'alimentation en mode chargeur d'amorçage** — la lecture/l'écriture de paramètres S20 et les commandes S8 ignorent désormais la condition sur l'état d'alimentation EPS pendant la phase chargeur d'amorçage
- **Séparation RX/TX du TTC** — couper le PA n'empêche plus l'acquisition du verrouillage en liaison montante ; les chaînes RX et TX sont indépendantes
- **link_status à trois états** — 0x0501 indique désormais 0 (NO_LINK), 1 (ACQUIRING) ou 2 (LOCKED)
- **image_count de la charge utile** — initialisé à 0 (valait à tort 12) ; le refroidisseur du FPA demande une mise en froid d'environ 200 s

**Résolus (séance 2 — affichage et architecture du MCS) :**
- **Correspondance des noms de champs** — `_UI_KEY_MAP` dans `server.py` traduit les short_keys YAML en noms de champs de l'interface (p. ex. `bat_soc` → `soc_pct`, `rssi` → `rssi_dbm`)
- **Libellé de l'antenne** — le synoptique TTC affiche « VHF/UHF » (au lieu de « PATCH »)
- **TM à la demande « antenne déployée »** — le paramètre 0x0520 est désormais marqué `on_demand: true` pour les requêtes S3
- **Conflit d'ID d'événement** — 0x050E n'est plus réutilisé pour la reprise de l'antenne ; un nouvel événement 0x0512 (ANTENNA_DEPLOY_READY_RECOVERED) a été créé
- **État des équipements AOCS** — les indicateurs d'activation du magnétomètre (0x025C), du gyroscope (0x025D) et du magnétocoupleur (0x025E) figurent désormais dans le SID HK 2 ; l'interface les affiche en gris/éteint lorsqu'ils ne sont pas alimentés (ils étaient codés en dur en vert)
- **Architecture du MCS** — le MCS n'interroge pas le simulateur ; orbite issue de la propagation des TLE, temps sol configurable via `--sim-epoch`

**Résolus (séance 3 — corrections du déroulé de recette en orbite) :**
- **Horloge SC TIME** — lit désormais la télémesure de temps CUC de l'OBC (0x0309) au lieu de l'horloge sol ; affiche « NOT SET » avant S9.1, se met à jour après SET_TIME
- **Temps OBC dans les HK** — paramètre 0x0309 (obc_time) ajouté à parameters.yaml et au SID HK 4
- **Asservissement du réchauffeur de batterie à l'EPS** — le thermostat ne fonctionne que si la ligne d'alimentation EPS 5 (`htr_bat`, 0x0115) est sur ON
- **Données YPR en AOCS OFF** — les vitesses angulaires et l'erreur d'attitude valent désormais 0 lorsque le mode AOCS est OFF (l'état interne fuyait auparavant)
- **Mise à jour des roues en mode OFF** — les roues de réaction sont désormais mises à jour dans tous les modes (frottement, décroissance), même en mode AOCS OFF, ce qui permet de vérifier leur santé avant DETUMBLE
- **Synchronisation temporelle GPS** — la nouvelle commande `OBC_GPS_TIME_SYNC` (func_id 80) synchronise l'horloge de bord sur le GPS ; un saut de temps > 5 s déclenche une transition AOCS en SAFE_BOOT
- **Interface de réglage libre du temps** — le panneau TIME CORRELATION comporte désormais une saisie libre de l'heure avec aperçu de la conversion CUC
- **Tracés de la TM différée** — le visualiseur de TM différée intègre désormais des courbes temporelles interactives Chart.js avec zoom et défilement
- **Outils TLE/orbite** — le nouvel outil `tools/orbit_tools.py` convertit un TLE ou un vecteur d'état au format hexadécimal de commande S20.1 (CLI + interface web sur le port 8093)

---
