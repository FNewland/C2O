# CTG-002 : Reprise après anomalie SCAO
**Sous-système :** AOCS
**Phase :** CONTINGENCY
**Révision :** 1.0
**Approuvé par :** Directeur des opérations de vol

## Objet
Rétablir le SCAO après la détection d'une anomalie de contrôle d'attitude. Cette procédure
est appliquée dès que l'un des déclencheurs suivants est observé : erreur d'attitude supérieure à 5 degrés,
température d'une roue de réaction supérieure à 60 °C, ou senseur stellaire signalant un état d'éblouissement.
L'objectif est de rétablir un pointage trois axes stable en mode NOMINAL (pointage nadir) tout en préservant les
marges de sécurité du matériel.

## Prérequis
- [ ] Le satellite est en passage actif, avec une liaison descendante de télémesure valide
- [ ] La trame de télémesure SCAO (SID 2) est reçue à >= 1 Hz
- [ ] L'équipe de dynamique du vol est en console et confirme les prévisions d'orbite et d'attitude
- [ ] La procédure CTG-005 (Reprise après mode survie EPS) est disponible pour référence croisée

## Déroulement

### Étape 1 — Évaluer l'état courant du SCAO
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.mode` (0x020F) valeur reçue en moins de 5 s
**Verify:** `aocs.att_error` (0x0217) valeur reçue en moins de 5 s
**GO/NO-GO:** Télémesure reçue en direct et mode SCAO confirmé — continuer si les données sont valides

### Étape 2 — Évaluer l'état des roues de réaction
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.rw1_speed` (0x0207), `aocs.rw2_speed` (0x0208), `aocs.rw3_speed` (0x0209), `aocs.rw4_speed` (0x020A) — toutes comprises dans +/-6000 tr/min
**Verify:** `aocs.rw1_temp` (0x0218), `aocs.rw2_temp` (0x0219), `aocs.rw3_temp` (0x021A), `aocs.rw4_temp` (0x021B) — toutes < 60 °C
**GO/NO-GO:** Si la température d'une roue est >= 60 °C ou si sa vitesse oscille de plus de +/-500 tr/min/s, signaler cette roue ; l'étape 3 s'applique alors. Si toutes les roues sont nominales, l'étape 5 est la suivante (ni désactivation ni désaturation). -> GO `STEP-3` | NO-GO `STEP-5`

### Étape 3 — Désactiver la roue de réaction défaillante
**LABEL:** `STEP-3`
**TC:** `AOCS_DISABLE_WHEEL(wheel_idx=<N>)` (Service 8, Subtype 1, func_id 2)
**Verify:** La vitesse de la roue concernée (0x0207-0x020A) décroît vers 0 tr/min en moins de 30 s
**Verify:** `aocs.att_error` (0x0217) ne dépasse pas 10° pendant la transition
**GO/NO-GO:** Roue confirmée désactivée et vitesses angulaires bornées — continuer

### Étape 4 — Commander une manœuvre de désaturation
**TC:** `AOCS_DESATURATE` (Service 8, Subtype 1, func_id 1)
**Verify:** `aocs.rw1_speed` à `aocs.rw4_speed` (0x0207-0x020A) — les roues actives tendent vers 0 tr/min en moins de 120 s
**Verify:** `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) — toutes < 0.5 °/s pendant la manœuvre
**GO/NO-GO:** Moment cinétique ramené à < 20 % de la capacité sur toutes les roues actives — continuer

### Étape 5 — Vérifier la stabilité des vitesses angulaires
**LABEL:** `STEP-5`
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.rate_roll` (0x0204) < 0.1 °/s
**Verify:** `aocs.rate_pitch` (0x0205) < 0.1 °/s
**Verify:** `aocs.rate_yaw` (0x0206) < 0.1 °/s
**GO/NO-GO:** Toutes les vitesses angulaires sont inférieures à 0.1 °/s — engager le rétablissement du pointage

### Étape 6 — Rétablir le mode NOMINAL (pointage nadir)
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0)
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL) en moins de 10 s
**Verify:** `aocs.att_error` (0x0217) converge sous 1.0° en moins de 120 s
**GO/NO-GO:** Erreur d'attitude < 1.0° et stable — reprise terminée -> GO `STEP-END` | NO-GO `STEP-7`

### Étape 7 — Escalade : commander DETUMBLE en cas de panne de plusieurs roues
**LABEL:** `STEP-7`
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0)
**Verify:** `aocs.mode` (0x020F) = 2 (DETUMBLE) en moins de 5 s
**Verify:** `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) — toutes tendent vers 0 en moins de 300 s
**GO/NO-GO:** Si les vitesses angulaires ne descendent pas sous 2.0 °/s en moins de 300 s, passer à EMG-001

## Conduite à tenir hors nominal
- Si l'erreur d'attitude dépasse 15° à n'importe quelle étape : commander immédiatement `AOCS_SET_MODE(mode=2)` (DETUMBLE)
- Si deux roues de réaction ou plus sont signalées : exécuter directement l'étape 7 et informer la dynamique du vol
- Si la tension du bus EPS descend sous 27.7 V pendant la reprise : appliquer CTG-005 (Reprise après mode survie EPS)
- Si le senseur stellaire reste ébloui après DETUMBLE : appliquer CTG-007 pour évaluer les roues et prévoir une intervention du sol

## Postconditions
**LABEL:** `STEP-END`
- [ ] `aocs.mode` (0x020F) = 4 (NOMINAL), ou 2 (DETUMBLE) en cas d'escalade
- [ ] `aocs.att_error` (0x0217) < 1.0° (NOMINAL) ou vitesses angulaires < 0.5 °/s (DETUMBLE)
- [ ] Températures de toutes les roues de réaction actives < 55 °C
- [ ] Rapport d'anomalie déposé avec l'état des roues, analyse des causes racines en attente
