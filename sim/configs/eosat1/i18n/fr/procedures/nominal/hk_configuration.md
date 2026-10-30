# NOM-005 : Configuration HK
**Sous-système :** OBDH / Housekeeping
**Phase :** NOMINAL
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Configurer les intervalles de collecte de la télémesure de servitude et les jeux de paramètres pour la phase de mission
en cours. Ajuster les cadences de compte rendu HK selon les besoins opérationnels : cadence élevée
pendant les contacts avec la station sol pour la surveillance en temps réel, et cadence basse pendant
l'éclipse ou les périodes d'attente pour économiser l'espace tampon de bord et la puissance. Cette procédure
active ou désactive aussi des identifiants de structure (SID) particuliers afin d'adapter le flux de télémesure aux
sous-systèmes concernés par le calendrier d'opérations en cours.

## Prérequis
- [ ] OBDH en mode NOMINAL : `obdh.mode` (0x0300) = 0
- [ ] Liaison TTC établie : `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] `ttc.link_margin` (0x0503) > 3.0 dB (marge suffisante pour le débit TM)
- [ ] Configuration HK actuelle documentée dans le journal d'exploitation
- [ ] Aucune séquence critique d'autonomie bord dépendant des intervalles HK actuels
- [ ] Opérateur FDIR/systèmes à la console

## Déroulement

### Étape 1 --- Lire la configuration HK actuelle
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- rapport HK EPS ponctuel
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- rapport HK AOCS ponctuel
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) --- rapport HK TCS ponctuel
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- rapport HK OBDH ponctuel
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- rapport HK ponctuel de la charge utile
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- rapport HK TT&C ponctuel
**Verify:** rapports HK reçus pour les 6 SID sous 15 s (S3.27 est une lecture ponctuelle ; S3.5 `HK_ENABLE` activerait le compte rendu périodique, et il n'existe pas de sous-type de rapport de structure)
**Note:** La table des SID est fixée par `telemetry/hk_structures.yaml` : **1 EPS, 2 AOCS, 3 TCS,
4 OBDH/plateforme, 5 charge utile, 6 TT&C, 7 détermination AOCS, 8 EPS étendu, 9 PROP,
11 balise.** Seuls les SID **1 et 11** sont activés à la mise sous tension
(`simulation.yaml` `default_enabled_sids: [1, 11]`, réappliqué à l'amorçage de l'application) ;
tout autre SID doit être activé par commande avec `HK_ENABLE` (S3.5).
**Action:** Consigner les valeurs interval_s actuelles de chaque SID. Les intervalles de
`hk_structures.yaml` à la livraison sont :
  - SID 1 (EPS) : 1.0 s
  - SID 2 (AOCS) : 4.0 s
  - SID 3 (TCS) : 60.0 s
  - SID 4 (OBDH/plateforme) : 8.0 s
  - SID 5 (charge utile) : 8.0 s
  - SID 6 (TT&C) : 8.0 s
**GO/NO-GO:** Configurations de tous les SID récupérées et consignées avec succès.

### Étape 2 --- Modifier les intervalles de collecte HK
**TC:** `HK_SET_INTERVAL(sid=1, interval_s=N)` (Service 3, Subtype 31) --- régler l'intervalle EPS
**TC:** `HK_SET_INTERVAL(sid=2, interval_s=N)` (Service 3, Subtype 31) --- régler l'intervalle AOCS
**TC:** `HK_SET_INTERVAL(sid=3, interval_s=N)` (Service 3, Subtype 31) --- régler l'intervalle TCS
**TC:** `HK_SET_INTERVAL(sid=4, interval_s=N)` (Service 3, Subtype 31) --- régler l'intervalle OBDH
**TC:** `HK_SET_INTERVAL(sid=5, interval_s=N)` (Service 3, Subtype 31) --- régler l'intervalle de la charge utile
**TC:** `HK_SET_INTERVAL(sid=6, interval_s=N)` (Service 3, Subtype 31) --- régler l'intervalle TT&C
**Action:** Régler les intervalles sur le profil de cadence approprié (SID5 = charge utile, SID6 = TT&C) :
  - **Profil contact :** SID1=1s, SID2=4s, SID3=10s, SID4=5s, SID5=5s, SID6=2s
  - **Profil attente :** SID1=10s, SID2=30s, SID3=60s, SID4=30s, SID5=60s, SID6=10s
  - **Profil éclipse :** SID1=5s, SID2=10s, SID3=30s, SID4=10s, SID5=OFF, SID6=5s
**Verify:** acceptation de chaque SET_INTERVAL sous 5 s
**Note:** Les intervalles doivent être >= 1 s et multiples du top d'ordonnancement de bord (1 s).
**GO/NO-GO:** Toutes les commandes d'intervalle acceptées.

### Étape 3 --- Activer les SID HK requis
**TC:** `HK_ENABLE(sid=1)` (Service 3, Subtype 5) --- activer le compte rendu périodique EPS
**TC:** `HK_ENABLE(sid=2)` (Service 3, Subtype 5) --- activer le compte rendu périodique AOCS
**TC:** `HK_ENABLE(sid=4)` (Service 3, Subtype 5) --- activer le compte rendu périodique OBDH
**TC:** `HK_ENABLE(sid=6)` (Service 3, Subtype 5) --- activer le compte rendu périodique TT&C
**Verify:** acceptation de chaque ENABLE sous 5 s
**Note:** Les SID 1 (EPS), 2 (AOCS), 4 (OBDH) et 6 (TT&C) forment le socle maintenu actif
pendant les opérations nominales. Seuls les SID 1 et 11 (balise) restent actifs après un redémarrage — les autres doivent être
commandés de nouveau après chaque amorçage de l'application.
**GO/NO-GO:** SID du socle activés et émettant leurs comptes rendus.

### Étape 4 --- Activer ou désactiver les SID optionnels selon la phase
**Note:** Selon le contexte opérationnel en cours, activer ou désactiver les SID optionnels :
**TC:** `HK_ENABLE(sid=5)` (Service 3, Subtype 5) — **Si une prise de vue est prévue :**  --- HK charge utile ON
**TC:** `HK_DISABLE(sid=5)` (Service 3, Subtype 6) — **Si aucune opération charge utile :**  --- HK charge utile OFF
**TC:** `HK_ENABLE(sid=3)` (Service 3, Subtype 5) — **En cas de préoccupation thermique :**  --- HK TCS ON à cadence élevée
**Note:** **Si le thermique est nominal :** régler SID=3 à cadence basse selon le profil attente de l'étape 2
**Verify:** acceptation sous 5 s de chaque activation ou désactivation
**Verify:** `obdh.hktm_buf_fill` (0x0312) < 50 % --- le tampon ne déborde pas avec la nouvelle configuration
**Note:** Activer simultanément tous les SID à cadence élevée peut dépasser la capacité du tampon de bord
pendant les longues périodes hors contact. Surveiller le taux de remplissage du tampon.
**GO/NO-GO:** SID optionnels configurés selon le plan d'opérations en cours.

### Étape 5 --- Vérifier que la nouvelle configuration est active
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- rapport HK EPS ponctuel
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- rapport HK AOCS ponctuel
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- rapport HK OBDH ponctuel (compteurs TM, remplissage du tampon)
**Action:** Vérifier que l'espacement des paquets périodiques correspond aux intervalles commandés pour tous les SID modifiés.
**Verify:** paquets HK périodiques arrivant aux cadences attendues (observer le compteur de paquets TM
`obdh.tm_pkt_count` (0x0307) s'incrémenter à la cadence globale attendue).
**Verify:** `obdh.hktm_buf_fill` (0x0312) stable ou en baisse (pas d'arriéré qui s'accumule).
**GO/NO-GO:** Nouvelle configuration HK confirmée active et stable.

### Étape 6 --- Confirmer l'arrivée des comptes rendus périodiques
**Action:** Surveiller le flux de télémesure pendant 60 s pour confirmer que les comptes rendus périodiques de tous
les SID activés arrivent aux intervalles configurés.
**Verify:** paquets SID 1 (EPS) reçus à la cadence configurée +/- 1 s
**Verify:** paquets SID 2 (AOCS) reçus à la cadence configurée +/- 1 s
**Verify:** paquets SID 4 (OBDH) reçus à la cadence configurée +/- 1 s
**Verify:** paquets SID 6 (TT&C) reçus à la cadence configurée +/- 1 s
**Verify:** paquets SID 5 (charge utile) reçus à la cadence configurée (s'il est activé)
**Verify:** tous les paramètres HK reçus contiennent des valeurs plausibles (ni données périmées ni remplissage à zéro)
**Note:** Consigner la nouvelle configuration dans le journal d'exploitation avec l'heure d'effet et la justification.

## Conduite à tenir hors nominal
- Si la commande HK_SET_INTERVAL est rejetée : vérifier que la valeur d'intervalle est dans la plage valide
  (1--3600 s). Vérifier que le SID existe dans la définition des structures HK de bord. Renvoyer
  avec une valeur corrigée.
- Si les paquets HK n'arrivent pas après ENABLE : vérifier que `obdh.mode` (0x0300) est toujours NOMINAL.
  Le service HK peut être inhibé si l'OBC est en mode SAFE. Vérifier que le SID n'a pas été
  désactivé par inadvertance par un autre opérateur.
- Si `obdh.hktm_buf_fill` (0x0312) > 80 % : la nouvelle configuration produit plus de données
  que la liaison descendante ne peut en écouler. Réduire immédiatement les cadences ou désactiver les SID non critiques pour
  éviter le débordement du tampon et la perte de données.
- Si les paquets HK contiennent des données périmées (valeurs figées) : le sous-système source du paramètre est peut-être
  éteint ou ne répond pas. Vérifier le mode et l'état d'alimentation du sous-système. Ne pas confondre un paramètre
  stable avec un paramètre périmé --- vérifier par une demande ponctuelle (Service 3, Subtype 27).
- Si la configuration revient à l'état antérieur après un redémarrage de l'OBC : la configuration HK n'est pas conservée et le
  catalogue ne comporte aucune commande d'enregistrement de configuration. Réappliquer cette procédure après chaque
  amorçage de l'application.

## Postconditions
- [ ] Intervalles de collecte HK réglés sur le profil visé (contact/attente/éclipse)
- [ ] Tous les SID requis activés et produisant des comptes rendus périodiques
- [ ] SID optionnels configurés selon le plan d'opérations en cours
- [ ] `obdh.hktm_buf_fill` (0x0312) stable et < 50 %
- [ ] Comptes rendus périodiques confirmés arrivant au sol aux cadences attendues
- [ ] Nouvelle configuration HK documentée dans le journal d'exploitation
- [ ] OBDH toujours en mode NOMINAL : `obdh.mode` (0x0300) = 0

---
*AIG --- contenu généré par l'intelligence artificielle*
*Référence : https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/*
