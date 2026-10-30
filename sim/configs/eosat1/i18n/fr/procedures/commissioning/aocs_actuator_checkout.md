# COM-004 : Vérification des actionneurs SCAO
**Sous-système :** AOCS
**Phase :** COMMISSIONING
**Révision :** 2.1 --- 2026-10-30 (décision de l'auteur Q16) : cette fiche s'exécute désormais
juste après COM-002, AVANT COM-003, depuis le maintien COARSE_SUN de la LEOP sans aucun
senseur stellaire en service. Sans senseur, rien ne fait sortir l'AOCS de ce maintien ;
la fiche active donc les roues puis COMMANDE NOMINAL (étape 1b) ; COM-003
étalonne ensuite les gyromètres dans ce NOMINAL contrôlé par les roues. La révision 2.0
(2026-08c) a rendu explicite la règle d'ordonnancement : les roues sont ACTIVÉES (étape 1)
avant toute « vérification de leur fonctionnement ». Aucune fiche en amont ne lit plus la télémesure des roues ; l'ancienne
étape de LEOP-002 « vérifier que les quatre roues répondent », qui s'exécutait avant même
que les roues soient alimentées, a été supprimée.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-002 --- satellite dans le maintien COARSE_SUN laissé
par la LEOP (`aocs.mode` 0x020F = 3), roues DÉSACTIVÉES (`aocs.wheels_enabled`
0x0260 = 0), senseurs stellaires et gyromètres sur OFF, SID 2 transmis, phase de
mission 5.

## Objet
Recetter individuellement les quatre roues de réaction. Effectuer des essais contrôlés de montée et
de descente en vitesse sur chaque roue, vérifier la précision de la régulation de vitesse, mesurer les
températures des roues et valider la capacité de gestion du moment cinétique (désaturation) au moyen des
magnétocoupleurs.

## Prérequis
- [ ] COM-001 et COM-002 terminées. COM-003 n'est PAS un prérequis : elle s'exécute
      après cette fiche (décision Q16)
- [ ] AOCS dans le maintien COARSE_SUN de la LEOP (`aocs.mode` 0x020F = 3, ou 8 en
      éclipse). Sans senseur stellaire en service, il ne se promeut pas de lui-même ; l'étape 1b
      commande NOMINAL
- [ ] Vitesses angulaires < 0.5 deg/s par axe. Le maintien par magnétocoupleurs seuls oscille entre
      0.1 et 0.4 deg/s ; les roues le stabilisent
- [ ] `eps.pl_aocs_wheels` (0x0117) == 1 — la ligne d'alimentation de l'ensemble est sur ON (LEOP-007).
      Les roues elles-mêmes sont encore DÉSACTIVÉES à ce stade ; l'étape 1 les active,
      et ce n'est QU'ALORS qu'une étape lit ou sollicite la télémesure des roues.
- [ ] `eps.bat_soc` (0x0101) > 65 %
- [ ] Liaison bidirectionnelle en bande S active
- [ ] Au moins 20 minutes de passage station sol restantes

## Déroulement

### Étape 1 — Activer les quatre roues de réaction
**Action:** Les roues de réaction sortent du chargeur d'amorçage DÉSACTIVÉES et le restent jusqu'à ce que la fonction d'activation ci-dessous soit commandée, une fois par roue. Alimenter la ligne EPS `aocs_wheels` met sous tension l'électronique de commande mais n'active PAS les roues — cette séparation est délibérée, afin qu'une commutation de ligne d'alimentation ne puisse jamais rendre silencieusement l'autorité d'attitude à la boucle de contrôle.
**TC:** `AOCS_ENABLE_WHEEL(wheel_idx=0)` (Service 8, Subtype 1, func_id 3)
**TC:** `AOCS_ENABLE_WHEEL(wheel_idx=1)` (Service 8, Subtype 1, func_id 3)
**TC:** `AOCS_ENABLE_WHEEL(wheel_idx=2)` (Service 8, Subtype 1, func_id 3)
**TC:** `AOCS_ENABLE_WHEEL(wheel_idx=3)` (Service 8, Subtype 1, func_id 3)
**Verify:** `aocs.wheels_enabled` (0x0260) == 4 sous 10s
**Verify:** `aocs.rw1_enabled` (0x0254) == 1 sous 10s
**Verify:** `aocs.rw2_enabled` (0x0255) == 1 sous 10s
**Verify:** `aocs.rw3_enabled` (0x0256) == 1 sous 10s
**Verify:** `aocs.rw4_enabled` (0x0257) == 1 sous 10s
**Action:** Avec moins de trois des quatre roues activées, le satellite ne dispose d'aucun actionnement trois axes, et avec moins de deux, la règle FDIR de bord sur `aocs.wheels_enabled` fera passer l'AOCS en mode sûr dès que la phase de mission atteindra NOMINAL. Ne pas quitter cette fiche avec moins de trois roues activées.
**GO/NO-GO:** Les quatre roues signalées activées

### Étape 1b — Commander NOMINAL contrôlé par les roues
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0) --- NOMINAL
**Note:** Le simulateur accepte NOMINAL sans senseur stellaire ; la connaissance d'attitude
reste sur la voie grossière Soleil/magnétomètre jusqu'à ce que COM-003 intègre le
senseur dans l'estimateur. Cette commande mémorise aussi `aocs.commanded_mode`
(0x0297) = 4.
**Verify:** `aocs.mode` (0x020F) dans {4, 8} sous 300s --- 8 (ECLIPSE) est le
passage de relais côté ombre du même état commandé
**Verify:** `aocs.commanded_mode` (0x0297) = 4 sous 10s
**GO/NO-GO:** AOCS en NOMINAL sur les roues

### Étape 2 — Consigner les vitesses de référence des roues
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.rw1_speed` (0x0207) rapportée sous 10s — consigner la valeur
**Verify:** `aocs.rw2_speed` (0x0208) rapportée sous 10s — consigner la valeur
**Verify:** `aocs.rw3_speed` (0x0209) rapportée sous 10s — consigner la valeur
**Verify:** `aocs.rw4_speed` (0x020A) rapportée sous 10s — consigner la valeur
**Action:** Les roues nouvellement activées en NOMINAL reprennent immédiatement la charge de contrôle et peuvent présenter des vitesses non nulles. Les consigner comme référence.
**GO/NO-GO:** Les quatre roues répondent avec des lectures de vitesse valides

### Étape 3 — Essai de montée en vitesse de la roue de réaction 1
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=0, bias_rpm=2000.0)` (Service 8, Subtype 1, func_id 8) — biais de +2000 tr/min sur RW1
**Note:** `RW_SET_SPEED_BIAS` applique un biais *ajouté à la vitesse actuelle de la roue* ; la référence de l'étape 2 sert de base à tous les contrôles ci-dessous. Les vitesses des roues (0x0207-0x020A) sont une télémesure en LECTURE SEULE et ne peuvent pas être commandées avec `SET_PARAM`.
**Verify:** `aocs.rw1_speed` (0x0207) atteint référence +1800 à +2200 tr/min sous 60s
**Action:** Surveiller la perturbation d'attitude — les autres roues doivent compenser.
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg sous 60s
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=0, bias_rpm=-4000.0)` (Service 8, Subtype 1, func_id 8) — faire passer RW1 par zéro jusqu'à référence -2000 tr/min
**Verify:** `aocs.rw1_speed` (0x0207) atteint référence -2200 à -1800 tr/min sous 120s
**TC:** `AOCS_RW_RAMP_DOWN(wheel_idx=0, target_rpm=0.0)` (Service 8, Subtype 1, func_id 14) — ramener RW1 à zéro
**Verify:** `aocs.rw1_speed` (0x0207) revient à < 100 tr/min sous 60s
**GO/NO-GO:** Régulation de vitesse de RW1 vérifiée dans les deux sens

### Étape 4 — Essai de montée en vitesse de la roue de réaction 2
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=1, bias_rpm=2000.0)` (Service 8, Subtype 1, func_id 8) — biais de +2000 tr/min sur RW2
**Verify:** `aocs.rw2_speed` (0x0208) atteint référence +1800 à +2200 tr/min sous 60s
**Action:** Surveiller la perturbation d'attitude — les autres roues doivent compenser.
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg sous 60s
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=1, bias_rpm=-4000.0)` (Service 8, Subtype 1, func_id 8) — faire passer RW2 par zéro jusqu'à référence -2000 tr/min
**Verify:** `aocs.rw2_speed` (0x0208) atteint référence -2200 à -1800 tr/min sous 120s
**TC:** `AOCS_RW_RAMP_DOWN(wheel_idx=1, target_rpm=0.0)` (Service 8, Subtype 1, func_id 14) — ramener RW2 à zéro
**Verify:** `aocs.rw2_speed` (0x0208) revient à < 100 tr/min sous 60s
**GO/NO-GO:** Régulation de vitesse de RW2 vérifiée dans les deux sens

### Étape 5 — Essai de montée en vitesse de la roue de réaction 3
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=2, bias_rpm=2000.0)` (Service 8, Subtype 1, func_id 8) — biais de +2000 tr/min sur RW3
**Verify:** `aocs.rw3_speed` (0x0209) atteint référence +1800 à +2200 tr/min sous 60s
**Action:** Surveiller la perturbation d'attitude — les autres roues doivent compenser.
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg sous 60s
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=2, bias_rpm=-4000.0)` (Service 8, Subtype 1, func_id 8) — faire passer RW3 par zéro jusqu'à référence -2000 tr/min
**Verify:** `aocs.rw3_speed` (0x0209) atteint référence -2200 à -1800 tr/min sous 120s
**TC:** `AOCS_RW_RAMP_DOWN(wheel_idx=2, target_rpm=0.0)` (Service 8, Subtype 1, func_id 14) — ramener RW3 à zéro
**Verify:** `aocs.rw3_speed` (0x0209) revient à < 100 tr/min sous 60s
**GO/NO-GO:** Régulation de vitesse de RW3 vérifiée dans les deux sens

### Étape 6 — Essai de montée en vitesse de la roue de réaction 4
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=3, bias_rpm=2000.0)` (Service 8, Subtype 1, func_id 8) — biais de +2000 tr/min sur RW4
**Verify:** `aocs.rw4_speed` (0x020A) atteint référence +1800 à +2200 tr/min sous 60s
**Action:** Surveiller la perturbation d'attitude — les autres roues doivent compenser.
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg sous 60s
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=3, bias_rpm=-4000.0)` (Service 8, Subtype 1, func_id 8) — faire passer RW4 par zéro jusqu'à référence -2000 tr/min
**Verify:** `aocs.rw4_speed` (0x020A) atteint référence -2200 à -1800 tr/min sous 120s
**TC:** `AOCS_RW_RAMP_DOWN(wheel_idx=3, target_rpm=0.0)` (Service 8, Subtype 1, func_id 14) — ramener RW4 à zéro
**Verify:** `aocs.rw4_speed` (0x020A) revient à < 100 tr/min sous 60s
**GO/NO-GO:** Régulation de vitesse de RW4 vérifiée dans les deux sens

### Étape 7 — Contrôler les températures des roues
**TC:** `GET_PARAM(param_id=0x0218)` (Service 20, Subtype 3) — `aocs.rw1_temp`
**TC:** `GET_PARAM(param_id=0x0219)` (Service 20, Subtype 3) — `aocs.rw2_temp`
**TC:** `GET_PARAM(param_id=0x021A)` (Service 20, Subtype 3) — `aocs.rw3_temp`
**TC:** `GET_PARAM(param_id=0x021B)` (Service 20, Subtype 3) — `aocs.rw4_temp`
**Verify:** Toutes les températures des roues dans la plage [-10C, +55C] sous 10s
**Note:** 0x028A-0x028D sont des pourcentages d'état de santé des têtes CSS (`aocs.css_head_health_py/my/pz/mz`),
et non des températures de roues.
**Action:** Les températures après essai peuvent être légèrement élevées. Les consigner pour le suivi de tendance.
**GO/NO-GO:** Toutes les températures des roues dans les limites opérationnelles

### Étape 8 — Essai de désaturation du moment cinétique
**Action:** Commander la désaturation pour décharger le moment cinétique accumulé au moyen des magnétocoupleurs.
**TC:** `AOCS_DESATURATE` (Service 8, Subtype 1, func_id 1)
**Verify:** `aocs.rw1_speed` (0x0207) tendant vers 0 tr/min sous 300s
**Verify:** `aocs.rw2_speed` (0x0208) tendant vers 0 tr/min sous 300s
**Verify:** `aocs.rw3_speed` (0x0209) tendant vers 0 tr/min sous 300s
**Verify:** `aocs.rw4_speed` (0x020A) tendant vers 0 tr/min sous 300s
**Action:** La désaturation peut prendre 5-10 minutes selon le niveau de moment cinétique et l'intensité du champ magnétique. Surveiller la stabilité de l'attitude pendant la désaturation.
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg pendant la désaturation
**GO/NO-GO:** Désaturation efficace — vitesses des roues tendant vers zéro

### Étape 9 — Établir le rapport de recette des roues
**Action:** Consigner, pour chaque roue, les temps de réponse en montée et descente en vitesse, la précision de régulation de vitesse, les températures et les performances de désaturation. Les comparer à la spécification. Documenter toute anomalie.
**GO/NO-GO:** Recette des quatre roues de réaction réussie

## Conduite à tenir hors nominal
- Si une roue n'atteint pas la vitesse commandée en 90s : réduire le biais commandé à +1000 tr/min à titre de diagnostic. Si elle ne répond toujours pas, vérifier que la ligne des roues est alimentée via `GET_PARAM(param_id=0x0117)` (`eps.pl_aocs_wheels`) et sa consommation via `GET_PARAM(param_id=0x011F)` (`eps.line_current_7`). Si l'alimentation est nominale mais que la roue ne répond pas, la déclarer défaillante. L'AOCS peut fonctionner sur trois roues.
- Si la température d'une roue dépasse +55C pendant les essais : interrompre les essais sur cette roue. Laisser refroidir pendant 10 minutes. Recontrôler la température avant de continuer. Si la température reste élevée, réduire le biais d'essai à +1000 tr/min.
- Si l'erreur d'attitude dépasse 10 deg pendant un essai de roue : interrompre immédiatement l'essai via `AOCS_RW_RAMP_DOWN(wheel_idx=255, target_rpm=0.0)` (Service 8, Subtype 1, func_id 14 — 255 = toutes les roues). Vérifier que l'AOCS contrôle toujours. Vérifier si plusieurs roues sont sollicitées simultanément (ce qui ne devrait pas être le cas). Poursuivre les essais une fois l'attitude rétablie.
- Si la désaturation ne réduit pas les vitesses des roues : vérifier le fonctionnement des magnétocoupleurs via `GET_PARAM(param_id=0x025E)` (`aocs.mtq_enabled`). Contrôler la position orbitale actuelle au regard de l'intensité du champ magnétique (désaturation moins efficace près de l'équateur). Réessayer lors du passage au-dessus des pôles.
- Si une roue présente une réponse sensiblement différente des autres : consigner une anomalie. Usure possible des roulements ou problème d'électronique de commande. Poursuivre la recette avec les autres roues. Programmer une investigation détaillée.

## État de sortie
- Les quatre roues ACTIVÉES et sollicitées, moment cinétique déchargé (étape 8), AOCS dans
  la famille NOMINAL commandée, maintenant le pointage nadir sur roues
- Senseurs stellaires et gyromètres toujours sur OFF (COM-003 les met en service)
- Aucun état de ligne d'alimentation, de charge utile ni de TTC touché par cette fiche

## Postconditions
- [ ] Les quatre roues de réaction activées — `aocs.wheels_enabled` (0x0260) == 4
- [ ] Montée/descente en vitesse de RW1 vérifiée dans les deux sens
- [ ] Montée/descente en vitesse de RW2 vérifiée dans les deux sens
- [ ] Montée/descente en vitesse de RW3 vérifiée dans les deux sens
- [ ] Montée/descente en vitesse de RW4 vérifiée dans les deux sens
- [ ] Toutes les températures des roues dans les limites opérationnelles
- [ ] Désaturation du moment cinétique par magnétocoupleurs vérifiée
- [ ] Rapport de recette des roues établi

**PROCÉDURE SUIVANTE :** COM-003 (Étalonnage des capteurs SCAO --- étalonnage des gyromètres en NOMINAL contrôlé par les roues)
