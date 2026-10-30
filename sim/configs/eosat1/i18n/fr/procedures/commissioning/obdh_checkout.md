# COM-007 : Vérification de l'OBDH
**Sous-système :** OBDH
**Phase :** COMMISSIONING
**Révision :** 2.0 --- 2026-08c : codages de `OBC_SET_MODE` corrigés dans toute la fiche
(0 = NOMINAL, 1 = SAFE, 2 = EMERGENCY --- l'ancienne fiche les avait INVERSÉS et
sa dernière étape laissait l'OBC en SAFE en croyant avoir rétabli NOMINAL),
et la fiche se termine désormais en rétablissant explicitement `obdh.mode` = 0.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-006 --- AOCS en NOMINAL commandé, liaison descendante en
LOW avec l'antenne déployée, OBC en NOMINAL (`obdh.mode` 0x0300 = 0).

## Objet
Vérifier le système de gestion bord des données. Confirmer le mode de fonctionnement de l'OBC, la charge
du processeur, l'intégrité de la mémoire, les compteurs de paquets TC/TM et le fonctionnement du chien de garde.
Valider les transitions de mode entre SAFE et NOMINAL et confirmer la génération autonome des
données de servitude.

## Prérequis
- [ ] COM-001 à COM-006 terminées
- [ ] AOCS dans la famille NOMINAL (`aocs.mode` 0x020F dans {4, 8})
- [ ] `obdh.mode` (0x0300) = 0 (NOMINAL) ou 1 (SAFE)
- [ ] Liaison bidirectionnelle en bande S active
- [ ] `eps.bat_soc` (0x0101) > 60 %

## Déroulement

### Étape 1 — Vérifier le mode actuel de l'OBC
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27)
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) sous 10s — le codage est
0 = NOMINAL, 1 = SAFE, 2 = EMERGENCY (identique à `OBC_SET_MODE` func 50)
**Action:** Consigner le mode actuel. NOMINAL est l'état attendu ; une lecture SAFE
ici signifie qu'une fiche précédente a laissé une excursion non rétablie — l'examiner avant
de continuer.
**GO/NO-GO:** OBC répondant en NOMINAL

### Étape 2 — Contrôler la charge du processeur
**TC:** `GET_PARAM(param_id=0x0302)` (Service 20, Subtype 3) — charge du processeur
**Verify:** `obdh.cpu_load` (0x0302) dans la plage [10 %, 50 %] sous 10s
**Action:** Consigner la charge processeur de référence. La charge nominale au repos est d'environ 15-25 %. Des valeurs plus élevées indiquent l'exécution de tâches de fond.
**GO/NO-GO:** Charge processeur dans la plage acceptable

### Étape 3 — Vérifier l'état de la mémoire
**TC:** `GET_PARAM(param_id=0x0303)` (Service 20, Subtype 3) — pourcentage d'utilisation de la RAM
**TC:** `GET_PARAM(param_id=0x0304)` (Service 20, Subtype 3) — nombre d'erreurs EDAC
**Verify:** Utilisation de la RAM < 70 % sous 10s
**Verify:** Nombre d'erreurs EDAC sur un bit rapporté (consigner la valeur) sous 10s
**Verify:** Nombre d'erreurs EDAC multibits = 0 sous 10s
**GO/NO-GO:** Mémoire saine, sans erreur non corrigible

### Étape 4 — Contrôler les compteurs de paquets TC/TM
**TC:** `GET_PARAM(param_id=0x0304)` (Service 20, Subtype 3) — compteur de TC reçues (`obdh.tc_rx_count`)
**TC:** `GET_PARAM(param_id=0x0306)` (Service 20, Subtype 3) — compteur de TC rejetées (`obdh.tc_rej_count`)
**TC:** `GET_PARAM(param_id=0x0307)` (Service 20, Subtype 3) — compteur de TM générées (`obdh.tm_pkt_count`)
**Verify:** Compteur de TC reçues > 0 (doit correspondre au journal sol) sous 10s
**Verify:** Compteur de TC rejetées = 0 (aucune commande invalide envoyée) sous 10s
**Verify:** Compteur de TM générées > 0 et en progression sous 10s
**GO/NO-GO:** Compteurs TC/TM cohérents avec les opérations menées à ce jour

### Étape 5 — Confirmer les services du mode NOMINAL
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) sous 10s
**Verify:** `obdh.cpu_load` (0x0302) reste < 60 % sous 30s
**Action:** Le mode NOMINAL assure l'ensemble des données de servitude autonomes, la surveillance FDIR
et l'exécution des commandes datées — ce que confirme l'étape 6 sans aucune commande de
mode (l'OBC est déjà en NOMINAL ; commander le mode dans lequel on se trouve ne prouve
rien).
**GO/NO-GO:** Services du mode NOMINAL confirmés

### Étape 6 — Vérifier la génération autonome des HK
**Action:** En mode NOMINAL, l'OBC doit générer de façon autonome des paquets HK périodiques. Attendre 60 secondes et vérifier la progression du compteur de TM sans demande du sol.
**TC:** `GET_PARAM(param_id=0x0312)` (Service 20, Subtype 3) — compteur de TM avant
**Action:** Attendre 60 secondes. N'envoyer aucune TC.
**TC:** `GET_PARAM(param_id=0x0312)` (Service 20, Subtype 3) — compteur de TM après
**Verify:** Le compteur de TM a progressé (HK autonomes actives) sous 10s
**GO/NO-GO:** Génération autonome des données de servitude confirmée

### Étape 7 — Vérifier le chien de garde
**TC:** `GET_PARAM(param_id=0x0305)` (Service 20, Subtype 3) — état du chien de garde
**TC:** `GET_PARAM(param_id=0x0316)` (Service 20, Subtype 3) — cause du dernier redémarrage (`obdh.last_reboot_cause`)
**Verify:** État du chien de garde = ENABLED (valeur 1) sous 10s
**Verify:** Cause du dernier redémarrage = 0 (aucune) — aucune réinitialisation inattendue sous 10s
**GO/NO-GO:** Chien de garde actif, aucune réinitialisation anormale enregistrée

### Étape 8 — Essayer une excursion de mode de l'OBC (NOMINAL -> SAFE -> NOMINAL)
**TC:** `OBC_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 50) — SAFE (codage : 1 = SAFE)
**Verify:** `obdh.mode` (0x0300) = 1 (SAFE) sous 15s
**Action:** Confirmer que tous les sous-systèmes restent stables pendant l'excursion. Le bandeau
de contingence du MCS (M8) s'affiche tant que `obdh.mode` != 0 — c'est attendu.
**TC:** `OBC_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 50) — RÉTABLIR NOMINAL (codage : 0 = NOMINAL)
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) sous 15s — LA FICHE NE DOIT PAS
SE TERMINER AVEC L'OBC EN SAFE. La révision antérieure à 2026-08c se terminait sur `mode=1`
en le croyant NOMINAL, et transmettait un OBC en SAFE à toutes les fiches suivantes.
**GO/NO-GO:** Excursion propre dans les deux sens, OBC rétabli en NOMINAL

### Étape 9 — Consigner la référence de l'OBDH
**Action:** Rassembler la charge processeur, l'utilisation mémoire, les compteurs EDAC, les statistiques TC/TM et l'état du chien de garde dans le rapport de vérification de l'OBDH. Ces valeurs constituent la référence pour la détection d'anomalies en opérations nominales.
**GO/NO-GO:** Vérification de l'OBDH terminée — tous les paramètres nominaux

## Conduite à tenir hors nominal
- Si `obdh.cpu_load` > 60 % : examiner les tâches en cours via `GET_PARAM(param_id=0x0307)` (liste des tâches). Si une tâche inattendue consomme des ressources, envisager l'arrêt ciblé de cette tâche après accord du directeur de vol. Ne pas redémarrer sauf si la charge processeur dépasse 90 %.
- Si des erreurs EDAC multibits > 0 : corruption mémoire détectée. Tenter un nettoyage mémoire avec `OBC_MEMORY_SCRUB` (Service 8, Subtype 1, func_id 51). Si les erreurs persistent, identifier la zone mémoire affectée. Un repli sur l'OBC redondant peut être nécessaire.
- Si une transition de mode de l'OBC échoue : renvoyer la commande une fois. En cas de nouvel échec, contrôler l'état d'acceptation de la TC. Vérifier l'authentification de la commande. Si le mode NOMINAL est inaccessible, poursuivre la recette en orbite en mode SAFE avec des demandes de HK manuelles.
- Si l'état du chien de garde = DISABLED : le réactiver via `SET_PARAM(param_id=0x0305, value=1)`. Rechercher pourquoi le chien de garde était désactivé — cela peut indiquer un rétablissement après une panne antérieure.
- Si le compteur de TC rejetées > 0 : examiner le journal des commandes sol à la recherche de séquences invalides. Après investigation, consigner la valeur du compteur comme nouvelle référence (il n'existe pas de commande de remise à zéro du compteur ; ne jamais écrire 0x0311, qui est `obdh.sw_image`).
- Si la cause de la dernière réinitialisation != POWER_ON : examiner le code de cause de réinitialisation. Si une réinitialisation par sous-tension ou par chien de garde s'est produite pendant la LEOP, examiner la chronologie de télémesure correspondante. La documenter dans le journal des anomalies.

## État de sortie
- OBC en NOMINAL (`obdh.mode` 0x0300 = 0) — revérifié positivement après
  l'excursion de l'étape 8 ; chien de garde activé ; rien d'autre modifié par cette fiche

## Postconditions
- [ ] OBC fonctionnant en mode NOMINAL (`obdh.mode` = 0)
- [ ] Charge processeur de référence établie (15-25 % au repos attendus)
- [ ] Mémoire saine — aucune erreur EDAC non corrigible
- [ ] Compteurs TC/TM cohérents avec l'historique des opérations
- [ ] Génération autonome des données de servitude confirmée
- [ ] Chien de garde activé et fonctionnel
- [ ] Transitions de mode (SAFE <-> NOMINAL) vérifiées
- [ ] Rapport de vérification de l'OBDH établi

**PROCÉDURE SUIVANTE :** COM-008 (Configuration de la FDIR et fonctions de protection)
