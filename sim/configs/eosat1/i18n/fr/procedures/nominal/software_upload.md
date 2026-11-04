# NOM-006 : Chargement de logiciel
**Sous-système :** OBDH / gestion mémoire
**Phase :** NOMINAL
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Envoyer un nouveau correctif logiciel ou une nouvelle image applicative dans la mémoire de l'OBC, vérifier son intégrité par
comparaison de sommes de contrôle et, le cas échéant, activer la nouvelle image. C'est une procédure à haut risque
qui exige l'autorisation du directeur de vol et une exécution pas à pas avec des jalons GO/NO-GO
explicites. Un chargement raté ou une image corrompue pourrait rendre l'OBC inopérant ; plusieurs
contrôles d'intégrité sont donc effectués. La procédure couvre à la fois les correctifs partiels (appliqués à
l'image en cours d'exécution) et les remplacements complets de l'image applicative (chargée à la place de
l'image applicative et amorcée avec `OBC_BOOT_APP`). L'OBC n'a qu'une seule image applicative et aucune sélection
de banc d'amorçage : l'image précédente n'est pas conservée à bord, et revenir en arrière signifie la recharger.

## Prérequis
- [ ] Liaison TTC établie avec une marge > 6 dB : `ttc.link_margin` (0x0503) > 6.0
- [ ] Aucune séance de prise de vue active : `payload.mode` (0x0600) != 2
- [ ] OBC en mode NOMINAL : `obdh.mode` (0x0300) = 0
- [ ] OBC actif identifié : `obdh.active_obc` (0x030C) consigné (0=A, 1=B)
- [ ] Version logicielle actuelle consignée : `obdh.sw_version` (0x030B)
- [ ] Fichier de correctif vérifié au sol : somme de contrôle CRC-32 calculée et consignée
- [ ] Taille du fichier de correctif confirmée compatible avec la mémoire disponible : `obdh.mmm_used` (0x0303) < 70 %
- [ ] Le directeur de vol a autorisé le chargement (autorisation signée dans le journal de console)
- [ ] Opérateur FDIR/systèmes à la console
- [ ] SoC de la batterie > 60 % : `eps.bat_soc` (0x0101) > 60
- [ ] Aucune entrée en éclipse prévue pendant la fenêtre de chargement (durée de contact suffisante)

## Déroulement

### Étape 1 --- Évaluation de santé avant chargement
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- demander les données de servitude OBDH
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL)
**Verify:** `obdh.cpu_load` (0x0302) < 50 % (marge pour le traitement du chargement)
**Verify:** `obdh.mmm_used` (0x0303) < 70 % (mémoire libre suffisante pour l'image)
**Verify:** `obdh.mem_errors` (0x031E) sans augmentation --- la consigner comme référence de cette fiche. Le compteur inclut les perturbations corrigées par l'EDAC, qui s'accumulent en orbite (2 après ~3 h le 2026-11-02), donc 0 n'est pas la valeur saine ; une AUGMENTATION pendant le chargement est la panne
**Verify:** `obdh.heap_usage` (0x031D) < 60 % (tas suffisant pour la tâche de chargement)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- demander les données de servitude EPS
**Verify:** `eps.bat_soc` (0x0101) > 60 %
**Verify:** `eps.bus_voltage` (0x0105) > 32.1 V
**GO/NO-GO:** Le directeur de vol confirme le GO pour le chargement. Si un paramètre est limite, se mettre en attente (HOLD).

### Étape 2 --- Suspendre les tâches de bord non critiques
**TC:** `DISABLE_SCHEDULE` (Service 11, Subtype 9) --- suspendre l'ordonnancement de bord
**Note:** Était `FUNC_PERFORM func_id=10`. La fonction S8 10 est `AOCS_SLEW_TO` — un
basculement d'attitude. Il n'existe pas de commande générique FUNC_PERFORM ; la suspension du
plan des télécommandes datées est le sous-type 9 du S11.
**Verify:** acceptation de la commande sous 5 s
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1) --- charge utile OFF (si ce n'est pas déjà le cas)
**Verify:** `payload.mode` (0x0600) = 0 (OFF) sous 10 s
**Action:** Confirmer qu'aucune séquence de télécommandes datées ne reste dans la file d'exécution.
**Note:** La suspension de l'ordonnanceur empêche toute autonomie de bord d'interférer avec
le processus de chargement. Il sera rétabli à l'étape 8.
**GO/NO-GO:** Tâches non critiques suspendues. Ressources de l'OBC disponibles pour le chargement.

### Étape 3 --- Ouvrir la session de chargement mémoire
**TC:** `MEM_LOAD(memory_id=1, address=ADDR, data=BLOCK)` (Service 6, Subtype 2) --- premier bloc (le S6.2 n'a pas de session de chargement : chaque MEM_LOAD écrit un bloc)
**Action:** Indiquer l'adresse de base de la mémoire cible pour le correctif (fournie par l'ingénieur OBDH).
**Action:** Indiquer la longueur totale en octets du fichier de correctif.
**Verify:** acceptation de la commande sous 5 s
**Verify:** aucun rejet (Service 1, Subtype 2) --- vérifier l'absence de violation de plage d'adresses
**Note:** Le service de gestion de la mémoire de bord prépare la zone cible et signale
qu'il est prêt. Si la zone cible est protégée en écriture, le chargement est rejeté.
**GO/NO-GO:** Session de chargement mémoire initialisée. OBC prêt à recevoir les segments de données.

### Étape 4 --- Envoyer les segments de données
**TC:** `MEM_LOAD(memory_id=1, address=ADDR, data=BLOCK)` (Service 6, Subtype 2) --- envoyer un segment
**Note:** Était `MEM_LOAD_DATA ... (Service 6, Subtype 9)`. La commande est
`MEM_LOAD` et correspond au sous-type **2** du S6 ; le sous-type 9 est `MEM_CHECK` : l'étape d'envoi
était donc adressée au service de somme de contrôle.
**Action:** Transmettre le fichier de correctif en segments successifs de 256 octets chacun.
**Action:** Pour chaque segment, attendre l'acquittement avant d'envoyer le suivant.
**Verify:** acquittement reçu pour chaque segment sous 10 s
**Surveiller :** `obdh.cpu_load` (0x0302) --- doit rester < 70 % pendant le chargement
**Surveiller :** `ttc.link_margin` (0x0503) --- interrompre si la marge descend sous 3.0 dB
**Surveiller :** `obdh.hktm_buf_fill` (0x0312) --- interrompre si le remplissage du tampon > 90 %
**Avancement :** Suivre segment_id par rapport au nombre total de segments. Consigner l'avancement tous les 10 %.
**Attention :** Si un segment n'est pas acquitté sous 30 s, le retransmettre
une fois. S'il n'est toujours pas acquitté, se mettre en attente (HOLD) et analyser.
**GO/NO-GO:** Tous les segments envoyés et acquittés individuellement.

### Étape 5 --- Vérifier l'intégrité par somme de contrôle
**TC:** `MEM_CHECK(memory_id=1, address=ADDR, length=LEN)` (Service 6, Subtype 9) --- demander la somme de contrôle
**Note:** Était annoté Subtype 5, qui est `MEM_DUMP` — la fiche demandait un
VIDAGE mémoire, puis vérifiait une somme de contrôle qui n'avait jamais été calculée.
**Verify:** rapport de somme de contrôle reçu sous 15 s
**Action:** Comparer le CRC-32 de bord rapporté au CRC-32 calculé au sol.
**Verify:** les sommes de contrôle concordent exactement (bit à bit)
**Critique :** Si les sommes de contrôle NE concordent PAS, le chargement est CORROMPU. NE PAS procéder à
l'activation. Exécuter l'action de reprise 1 (recharger ; ne pas démarrer l'image).
**GO/NO-GO:** Somme de contrôle vérifiée --- intégrité de l'image chargée confirmée.

### Étape 6 --- Activer la nouvelle image logicielle (en cas de remplacement complet de l'image)
**Note:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55) amorce l'image applicative nouvellement chargée, mais PAS à cette étape : tant que l'application tourne, elle est refusée par un S1.8 « Already in application » (mesuré le 2026-11-02). Elle est envoyée à l'étape 7, une fois que le redémarrage a fait passer l'OBC sur le chargeur d'amorçage.
**Note:** Était `FUNC_PERFORM func_id=20`. La fonction S8 20 est `EPS_POWER_OFF` — cette
étape aurait DÉLESTÉ UNE LIGNE D'ALIMENTATION (indice de ligne tiré de l'octet
suivant, quel qu'il soit) en plein chargement de logiciel. Il n'existe pas de fonction
distincte de « sélection de la source d'amorçage » : `OBC_BOOT_APP` vérifie le CRC de l'application
pendant 10 s et fait passer `obdh.sw_image` (0x0311) à 1.
**Note:** Il n'existe ni registre de source d'amorçage ni second banc d'image : l'image chargée
EST l'image applicative, et `OBC_BOOT_APP` l'amorce après le contrôle de son CRC.
**Note:** Pour les correctifs appliqués à l'image en cours d'exécution, cette étape peut être remplacée par une
commande d'application directe du correctif. Consulter l'ingénieur OBDH pour l'activation propre au correctif.
**Verify:** `obdh.sw_image` (0x0311) toujours = 1 (application) --- aucun redémarrage intempestif à ce stade
**GO/NO-GO:** Somme de contrôle de l'image chargée vérifiée (étape 5). Prêt pour un redémarrage maîtrisé.

### Étape 7 --- Confirmer l'amorçage sur le nouveau logiciel
**TC:** `OBC_REBOOT` (Service 8, Subtype 1, func_id 52) --- commander un redémarrage maîtrisé de l'OBC
**Note:** Était `FUNC_PERFORM func_id=30`, qui correspond à `PAYLOAD_DELETE_IMAGE`.
**Action:** Attendre la séquence d'amorçage --- l'OBC ne répond plus pendant environ 60 s.
**Verify:** `obdh.mode` (0x0300) répond dans les 90 s qui suivent la commande de redémarrage
**Verify:** `obdh.sw_image` (0x0311) = 0 (BOOTLOADER) sur la balise (SID 11) sous 90 s. Un `OBC_REBOOT` commandé aboutit sur le chargeur d'amorçage et, lors de l'essai du 2026-11-02, y est RESTÉ jusqu'à `OBC_BOOT_APP` (pas d'amorçage automatique après 45 s), et le chargeur d'amorçage n'émet que le SID 11 — un 1 lu avant la balise suivante est la valeur d'avant le redémarrage
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55) --- amorcer la nouvelle image applicative (fenêtre de CRC de 10 s ; attendre son S1.7)
**Verify:** `obdh.sw_image` (0x0311) = 1 (application, et non chargeur d'amorçage) sous 45 s
**TC:** `HK_ENABLE(sid=4)` (Service 3, Subtype 5) --- l'amorçage de l'application réapplique `default_enabled_sids: [1, 11]` ; réactiver tous les autres SID utilisés pendant le passage (2, 3, 5, 6, 7, 12 comme dans LEOP-001 / LEOP-007 / COM-009)
**TC:** `OBC_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 50) --- rendre NOMINAL explicite : le redémarrage met l'OBC en SAFE (`obdh.mode` = 1) dans le chargeur d'amorçage et un amorçage applicatif réussi rétablit normalement 0 ; l'étape 8 le vérifie
**Note:** Le redémarrage remet aussi l'horloge de l'OBC à J2000 (resynchroniser avec NOM-008) et la phase du satellite vaut 4 après l'amorçage, et non 6 : le directeur de vol la redéclare avec `SYS_SET_MISSION_PHASE(phase=6)` (func 120) avant de rendre la main aux opérations courantes.
**TC:** `GET_PARAM(param_id=0x0316)` (Service 20, Subtype 3) — `obdh.last_reboot_cause` (à la demande : aucun SID HK ne le transporte)
**Verify:** `obdh.last_reboot_cause` (0x0316) = 1 (commandé)
**Verify:** `obdh.active_obc` (0x030C) inchangé (même unité OBC qu'avant)
**Critique :** Si l'OBC ne répond pas sous 120 s, ou s'il démarre sur le chargeur d'amorçage (sw_image=0),
la nouvelle image a peut-être échoué à la validation d'amorçage. Exécuter l'action de reprise 2.
**GO/NO-GO:** Fonctionnement de l'OBC sur la nouvelle version logicielle confirmé.

### Étape 8 --- Vérification après chargement et reprise des opérations
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- contrôle de santé OBDH complet
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL)
**Verify:** `obdh.cpu_load` (0x0302) < 50 %
**Verify:** `obdh.mem_errors` (0x031E) = la référence de l'étape 1 (aucune nouvelle erreur pendant le chargement)
**Verify:** `obdh.bus_a_status` (0x030F) = 0 (OK) --- communication par bus CAN rétablie
**TC:** `ENABLE_SCHEDULE` (Service 11, Subtype 13) --- reprendre l'ordonnancement de bord
**Note:** Était `FUNC_PERFORM func_id=11`, qui correspond à `AOCS_CHECK_MOMENTUM`.
**Verify:** acceptation de la commande sous 5 s
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- vérifier la communication avec le sous-système EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- vérifier la communication avec le sous-système AOCS
**Verify:** réponses HK de tous les sous-systèmes reçues avec des valeurs plausibles sous 15 s
**Action:** Consigner la fin du chargement : ancienne version, nouvelle version, durée du chargement, nombre de segments,
somme de contrôle, anomalies éventuellement observées.
**GO/NO-GO:** Tous les sous-systèmes communiquent normalement. Procédure de chargement terminée.

## Actions de reprise

### Action de reprise 1 --- Sommes de contrôle discordantes (chargement corrompu)
1. NE PAS activer l'image chargée.
2. **Note:** Il n'existe AUCUNE commande d'interruption. `MEM_LOAD_ABORT` ne figure pas dans
   `tc_catalog.yaml`, et le sous-type 3 du S6 n'est pas un sous-type que cette suite
   traite (le S6 met en œuvre 2 chargement, 5 vidage, 9 contrôle). Il suffit de ne pas amorcer
   l'image : `obdh.sw_image` (0x0311) reste à 0 tant que `OBC_BOOT_APP`
   (func 55) n'a pas réussi, et cette commande vérifie le CRC de l'application sur
   une fenêtre de 10 s avant d'effectuer la transition. Une zone corrompue est
   écrasée par le `MEM_LOAD` suivant, et non effacée par une commande distincte.
3. Ne pas attendre que la zone soit effacée : elle reste en l'état jusqu'à ce que le `MEM_LOAD` suivant l'écrase.
4. Rechercher la cause : dégradation de la liaison pendant le chargement ? Débordement de tampon ? Segments réordonnés ?
5. Si la cause est identifiée et corrigible : recommencer le chargement à partir de la session de chargement mémoire (étape 3), dans de meilleures conditions.
6. Si la cause est inconnue : interrompre la procédure. Le logiciel existant reste actif et n'est pas affecté.

### Action de reprise 2 --- Échec d'amorçage (OBC sur le chargeur d'amorçage)
1. Si `obdh.sw_image` (0x0311) = 0 (chargeur d'amorçage), la nouvelle image a échoué à la validation d'amorçage.
2. **Note:** Pour revenir à l'image précédente, la recharger avec `MEM_LOAD`
   (S6.2) et l'amorcer avec `OBC_BOOT_APP` (func 55). Il n'existe AUCUNE commande de « retour à la source
   d'amorçage précédente » — l'ancienne fiche envoyait `FUNC_PERFORM func_id=21`, qui correspond à
   `EPS_RESET_OC_FLAG`. Si l'OBC ne quitte pas le chargeur d'amorçage, utiliser
   `OBC_BOOT_INHIBIT(inhibit=0)` (func 56) puis `OBC_REBOOT` (func 52), et
   suivre CTG-021 Reprise par le chargeur d'amorçage de l'OBC.
3. Recharger l'image précédente (réputée saine) depuis l'archive sol avec `MEM_LOAD`,
   en répétant les étapes 3-5 de cette fiche avec les segments et le CRC-32 de cette image.
4. L'amorcer avec `OBC_BOOT_APP` (func 55) et attendre la fenêtre de contrôle CRC de 10 s.
5. Vérifier que `obdh.sw_image` (0x0311) = 1 et que la somme de contrôle de l'étape 5 correspond à l'image précédente.
6. Si l'OBC se rétablit : consigner l'échec, rechercher la cause racine au sol.
7. Si l'OBC reste sur le chargeur d'amorçage : faire remonter au directeur de vol. Envisager un basculement de redondance
   de l'OBC vers l'unité de secours si elle est disponible (`obdh.obc_b_status` (0x030D) = 1 STANDBY).

### Action de reprise 3 --- Perte de liaison pendant le chargement
1. Si `ttc.link_status` (0x0501) != 2 (pas LOCKED) pendant le chargement : le chargement est incomplet.
2. À l'AOS suivant, vérifier `obdh.mode` (0x0300) --- l'OBC doit toujours exécuter le logiciel précédent.
3. Les données partiellement chargées restent en mémoire mais ne sont pas activées.
4. Poursuivre à partir du dernier segment_id acquitté, ou effacer et recommencer le chargement à partir de la session de chargement mémoire (étape 3).

## Conduite à tenir hors nominal
- Si `obdh.cpu_load` dépasse 70 % pendant le chargement : suspendre la transmission des segments pendant 30 s pour
  laisser l'OBC traiter les données en tampon. Reprendre à cadence réduite (un segment toutes les 2 s).
- Si la retransmission d'un même segment échoue deux fois : interrompre le chargement, effacer la zone cible et
  retenter lors d'un passage ultérieur offrant de meilleures conditions de liaison.
- Si `eps.bat_soc` descend sous 50 % pendant le chargement : interrompre proprement le chargement et rétablir
  l'ordonnancement de bord. Le logiciel existant n'est pas affecté.
- Si l'OBC redémarre de façon inattendue pendant le chargement (`obdh.reboot_count` s'incrémente) : le chargement
  est caduc. Attendre que l'OBC se stabilise, vérifier qu'il exécute le logiciel précédent, et
  ne retenter qu'après l'analyse de la cause racine du redémarrage.

## Postconditions
- [ ] OBC exécutant l'image applicative chargée : `obdh.sw_image` (0x0311) = 1 après `OBC_BOOT_APP`, la somme de contrôle de l'étape 5 étant vérifiée
- [ ] `obdh.mode` (0x0300) = NOMINAL (0)
- [ ] Tous les sous-systèmes communiquant normalement par le bus CAN
- [ ] Ordonnancement de bord rétabli et opérationnel
- [ ] `obdh.mem_errors` (0x031E) pas plus élevé que la référence de l'étape 1
- [ ] Somme de contrôle de l'image chargée vérifiée correcte
- [ ] Journal de chargement complété avec numéros de version, sommes de contrôle et durée
- [ ] Image précédente et son CRC-32 archivés au sol (revenir en arrière signifie la recharger)
- [ ] Le directeur de vol a validé la réussite du chargement

---
*AIG --- contenu généré par l'intelligence artificielle*
*Référence : https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/*
