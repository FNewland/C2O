# CTG-006 : Anomalie charge utile
**Sous-système :** Charge utile / TCS
**Phase :** CONTINGENCY
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Traiter une anomalie thermique du plan focal (FPA) de la charge utile, lorsque la température du FPA
dépasse la limite opérationnelle de -15 °C ou augmente à une vitesse inattendue (> 0.5 °C
par minute alors que le refroidisseur est actif). La procédure met la charge utile sur OFF, vérifie
l'état du refroidisseur, attend la stabilisation thermique et redémarre la charge utile si les conditions le permettent.
Une hausse non maîtrisée de la température du FPA peut dégrader les performances du détecteur et risque de l'endommager
de façon permanente au-delà de +25 °C.

## Prérequis
- [ ] La télémesure de la charge utile (SID 5) est reçue à >= 0.5 Hz
- [ ] La télémesure TCS (SID 3) est reçue et confirme la validité des capteurs thermiques
- [ ] `payload.mode` (0x0600) vaut actuellement 1 (STANDBY) ou 2 (IMAGING)
- [ ] Le bilan de puissance de l'EPS offre une marge suffisante pour le fonctionnement du refroidisseur — `eps.bat_soc` (0x0101) > 30 %

## Déroulement

### Étape 1 — Confirmer le dépassement de température du FPA
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — Télémesure de servitude TCS
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Télémesure de servitude charge utile
**Verify:** `payload.fpa_temp` (0x0601) — consigner la valeur courante
**Verify:** `tcs.temp_fpa` (0x0408) — recouper avec le capteur TCS (les valeurs doivent concorder à 2 °C près)
**GO/NO-GO:** Si la température du FPA est > -15 °C ou augmente de > 0.5 °C/min, confirmer l'anomalie et continuer

### Étape 2 — Mettre la charge utile sur OFF
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1)
**Verify:** `payload.mode` (0x0600) = 0 (OFF) en 10 s
**Verify:** `eps.power_cons` (0x0106) diminue de >= 15 W (électronique de la charge utile hors tension)
**GO/NO-GO:** Charge utile confirmée sur OFF — passer à l'évaluation du refroidisseur

### Étape 3 — Vérifier l'état et l'alimentation du refroidisseur
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Télémesure de servitude EPS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — Télémesure de servitude TCS
**Verify:** `tcs.cooler_fpa` (0x040C) = 1 (actif) — si 0, le refroidisseur est défaillant ou a été arrêté par commande
**Verify:** `eps.power_gen` (0x0107) comparé à `eps.power_cons` (0x0106) — confirmer une marge de puissance positive >= 10 W pour le refroidisseur
**GO/NO-GO:** Si le refroidisseur est inactif, commander `FPA_COOLER(on=1)` (Service 8, Subtype 1, func_id 43) et vérifier son activation en 15 s. Si le refroidisseur ne peut pas être activé, faire remonter au sol pour une investigation matérielle.

### Étape 4 — Surveiller la phase de refroidissement
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Télémesure de servitude charge utile ; répéter toutes les 60 s pendant 20 minutes au plus
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Télémesure de servitude EPS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — Télémesure de servitude TCS
**Verify:** `payload.fpa_temp` (0x0601) en baisse à >= 0.3 °C/min
**Verify:** `tcs.temp_fpa` (0x0408) cohérent avec le capteur de la charge utile
**Verify:** `eps.bat_soc` (0x0101) reste > 25 % pendant le fonctionnement du refroidisseur
**GO/NO-GO:** La température du FPA doit descendre sous -20 °C et se stabiliser (vitesse < 0.05 °C/min) avant de continuer

### Étape 5 — Redémarrer la charge utile en STANDBY
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1)
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) en 15 s
**Verify:** `payload.fpa_temp` (0x0601) reste < -18 °C après la remise sous tension de l'électronique de la charge utile
**Verify:** hausse de `eps.power_cons` (0x0106) cohérente avec la consommation en STANDBY (~8 W)
**GO/NO-GO:** Température du FPA stable et charge utile en STANDBY — passer au contrôle d'aptitude à la prise de vue

### Étape 6 — Valider l'aptitude à la prise de vue
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Télémesure de servitude charge utile ; attendre 120 s après l'entrée en STANDBY
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — Télémesure de servitude TCS
**Verify:** `payload.fpa_temp` (0x0601) < -20 °C et stable
**Verify:** `tcs.cooler_fpa` (0x040C) = 1 (actif, consommation de courant nominale)
**GO/NO-GO:** Si la température du FPA est stable sous -20 °C, la charge utile peut être commandée en IMAGING pour la prochaine acquisition programmée. Si la température augmente encore, la maintenir en STANDBY et faire remonter au sol.

## Conduite à tenir hors nominal
- Si la température du FPA dépasse +10 °C à n'importe quelle étape : commander immédiatement `PAYLOAD_SET_MODE(mode=0)` et signaler pour une revue matérielle — ne pas retenter de redémarrage sans autorisation du sol
- Si le refroidisseur ne s'active pas à l'étape 3 : maintenir la charge utile sur OFF, exécuter CTG-004 (dépassement thermique) pour l'évaluation des zones
- Si le SoC de l'EPS descend sous 20 % pendant le refroidissement : exécuter CTG-005 (mode survie EPS) — l'alimentation du refroidisseur risque d'être interrompue
- Si les capteurs FPA de la charge utile et du TCS divergent de plus de 5 °C : suspecter une défaillance de capteur et retenir la valeur la plus basse pour les décisions de sécurité

## Postconditions
- [ ] `payload.fpa_temp` (0x0601) < -20 °C et stable
- [ ] `payload.mode` (0x0600) >= 1 (STANDBY ou IMAGING)
- [ ] `tcs.cooler_fpa` (0x040C) = 1 (actif)
- [ ] Rapport d'anomalie établi avec les données de tendance thermique et l'analyse de cause première
- [ ] Prochaine opportunité de prise de vue confirmée ou reportée dans l'attente de la revue thermique

## Chemin de reprise — remise sous tension des charges délestées
Une fois le bus stabilisé par cette procédure et la cause première comprise, **tout sous-système dont les lignes d'alimentation ont été mises hors tension lors du délestage doit être remis en service dans l'ordre maîtrisé défini par LEOP-007 (mise sous tension séquentielle)**. Ne **pas** se contenter de réactiver les lignes au coup par coup : LEOP-007 impose le bon enchaînement sous-système→ligne→mode, l'espacement des courants d'appel, le préconditionnement thermique des réchauffeurs OBC/batterie et les exemptions set_mode AOCS/charge utile au verrou d'alimentation à deux niveaux des TC. Référence croisée : `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
