# CTG-007 : Anomalie de roue de réaction
**Sous-système :** AOCS
**Phase :** CONTINGENCY
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Traiter l'anomalie d'une roue de réaction caractérisée par une oscillation de vitesse
(gigue > +/-500 tr/min sur 10 s), une divergence de vitesse inattendue ou une surchauffe du roulement de la roue
(> 60 °C). EOSAT-1 emporte quatre roues de réaction en configuration pyramidale ; les opérations
nominales en exigent au moins trois. Cette procédure isole la roue défaillante, passe
en mode de contrôle à trois roues, désature les roues restantes et établit un
plan pour une éventuelle reprise de la roue.

## Prérequis
- [ ] La télémesure AOCS (SID 2) est reçue à >= 1 Hz
- [ ] Au moins trois roues de réaction étaient confirmées fonctionnelles avant l'anomalie
- [ ] La dynamique du vol dispose d'une estimation à jour de l'état du moment cinétique
- [ ] La procédure CTG-002 (reprise après anomalie SCAO) a été passée en revue pour les voies d'escalade

## Déroulement

### Étape 1 — Identifier la roue de réaction concernée
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.rw1_speed` (0x0207) — consigner la valeur et sa vitesse de variation
**Verify:** `aocs.rw2_speed` (0x0208) — consigner la valeur et sa vitesse de variation
**Verify:** `aocs.rw3_speed` (0x0209) — consigner la valeur et sa vitesse de variation
**Verify:** `aocs.rw4_speed` (0x020A) — consigner la valeur et sa vitesse de variation
**Verify:** `aocs.rw1_temp` (0x0218), `aocs.rw2_temp` (0x0219), `aocs.rw3_temp` (0x021A), `aocs.rw4_temp` (0x021B)
**Action:** Signaler toute roue présentant : une oscillation de vitesse > +/-500 tr/min/10 s, une vitesse > 6500 tr/min ou une température > 60 °C
**GO/NO-GO:** Une seule roue est anormale — continuer. Si plusieurs roues sont anormales, passer à CTG-002 (étape 7).

### Étape 2 — Désactiver la roue anormale
**TC:** `AOCS_DISABLE_WHEEL(wheel_idx=N)` (Service 8, Subtype 1, func_id 2)
**Verify:** La vitesse de la roue concernée (0x0207-0x020A) commence à décroître en 10 s
**Verify:** `aocs.att_error` (0x0217) — surveiller une hausse transitoire (acceptable jusqu'à 5° pendant la transition)
**Verify:** `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) — les vitesses angulaires restent < 1.0°/s
**GO/NO-GO:** Roue désactivée et vitesses angulaires du satellite bornées — continuer

### Étape 3 — Commander le mode de contrôle à trois roues
**Note:** Il n'existe ni commande distincte de mode à trois roues ni paramètre `aocs.wheel_config` :
`AOCS_DISABLE_WHEEL` à l'étape 2 constitue à lui seul la reconfiguration à 3 roues sur 4 (comme dans CTG-026).
**Verify:** La boucle de contrôle du SCAO se reconfigure en 15 s (mise à jour d'un indicateur de mode interne)
**Verify:** `aocs.att_error` (0x0217) commence à reconverger sous 2.0° en 60 s
**Verify:** Les vitesses des trois roues restantes redistribuent correctement le moment cinétique
**GO/NO-GO:** Mode trois roues actif et attitude en convergence — continuer

### Étape 4 — Désaturer les roues restantes
**TC:** `AOCS_DESATURATE` (Service 8, Subtype 1, func_id 1)
**Verify:** Vitesses des roues actives (les trois restantes) tendant vers 0 tr/min en 120 s
**Verify:** `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) — toutes < 0.5°/s pendant la manœuvre
**Verify:** Aucune roue ne dépasse 5000 tr/min pendant la redistribution
**GO/NO-GO:** Moment cinétique déchargé — toutes les roues actives < 2000 tr/min et vitesses angulaires < 0.2°/s

### Étape 5 — Vérifier la stabilité du pointage en mode trois roues
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — échantillonner toutes les 60 s pendant 5 minutes
**Verify:** `aocs.att_error` (0x0217) < 1.5° (relâché par rapport à la valeur nominale de 1.0° pour l'exploitation à trois roues)
**Verify:** `aocs.rate_roll` (0x0204) < 0.1°/s
**Verify:** `aocs.rate_pitch` (0x0205) < 0.1°/s
**Verify:** `aocs.rate_yaw` (0x0206) < 0.1°/s
**Verify:** Températures des roues actives toutes < 55 °C
**GO/NO-GO:** Performances de pointage acceptables pour les opérations de mission — continuer

### Étape 6 — Confirmer la compatibilité avec le mode NOMINAL (nadir)
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0)
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL) en 15 s
**Verify:** `aocs.att_error` (0x0217) converge sous 1.5° en 120 s
**GO/NO-GO:** NOMINAL (nadir) atteint en mode trois roues — passer à la planification de la reprise de la roue

### Étape 7 — Évaluer la faisabilité de la reprise de la roue
**Action:** Si l'anomalie était une surchauffe : surveiller passivement `aocs.rw<N>_temp` pendant 2 orbites — si la température descend sous 45 °C, la roue est peut-être récupérable
**Action:** Si l'anomalie était une oscillation de vitesse : signaler pour une analyse de dégradation du roulement — la reprise de la roue exige l'autorisation du sol
**Action:** Si l'anomalie était une divergence de vitesse : suspecter l'électronique de commande — ne pas réactiver sans correctif logiciel ou mise à jour de paramètres par le sol
**GO/NO-GO:** Le sol a autorisé une tentative de reprise de la roue désactivée -> GO `STEP-7R` | NO-GO `STEP-END`
**LABEL:** `STEP-7R`
**TC:** `AOCS_ENABLE_WHEEL(wheel_idx=<N>)` (Service 8, Subtype 1, func_id 3) — tentative de reprise, sur autorisation du sol uniquement
**Verify:** La roue monte régulièrement à la vitesse commandée en 30 s, sans oscillation
**GO/NO-GO:** Si la reprise réussit, le contrôle à quatre roues est rétabli (`aocs.rw<N>_enabled` = 1 ; `AOCS_ENABLE_WHEEL` suffit, il n'existe pas de paramètre de configuration des roues). Si elle échoue, maintenir l'exploitation à trois roues.

## Conduite à tenir hors nominal
- Si une deuxième roue tombe en panne pendant cette procédure : commander immédiatement `AOCS_SET_MODE(mode=2)` pour passer en DETUMBLE et exécuter l'étape 7 de CTG-002
- Si l'erreur d'attitude dépasse 10° pendant la désactivation de la roue : commander `AOCS_SET_MODE(mode=2)` pour passer en DETUMBLE jusqu'à stabilisation des vitesses angulaires
- Si la désaturation est inefficace (roues toujours > 4000 tr/min) : planifier une désaturation prolongée par magnétocoupleurs sur les 3 orbites suivantes
- Si l'erreur de pointage à trois roues dépasse 3° : réduire les exigences de prise de vue et informer la planification de mission

## Postconditions
**LABEL:** `STEP-END`
- [ ] Roue anormale identifiée et documentée (RW1/2/3/4)
- [ ] Mode de contrôle à trois roues confirmé stable
- [ ] `aocs.att_error` (0x0217) < 1.5° en NOMINAL (nadir)
- [ ] Températures de toutes les roues actives < 55 °C et vitesses < 4000 tr/min
- [ ] Plan de reprise de la roue établi, avec le calendrier de décision de l'équipe sol
