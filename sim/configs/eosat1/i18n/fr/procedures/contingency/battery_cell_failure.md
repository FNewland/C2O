# CTG-013 : Défaillance d'un élément de batterie

**Catégorie :** Contingence
**Poste responsable :** Puissance et thermique (EPS/TCS)
**Postes associés :** (directeur de vol pour information)
**Difficulté :** Avancé

## Objectif
Traiter une défaillance présumée d'un élément de batterie, signalée par une chute de tension anormale, et
évaluer si la capacité restante de la batterie suffit à maintenir les opérations du satellite
pendant les éclipses. Cette procédure surveille les paramètres de santé de la batterie,
réduit les charges électriques si nécessaire pour les adapter à la capacité de stockage réduite, et vérifie que le satellite
peut traverser une éclipse en sécurité avec la batterie dégradée.

## Prérequis
- [ ] Anomalie de tension batterie détectée — `eps.bat_voltage` (0x0100) inférieure à la valeur attendue
  pour l'état de charge courant, ou chute de tension brutale observée
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Directeur de vol informé de l'anomalie batterie
- [ ] Prévision d'orbite courante disponible (durée et horaires des éclipses)

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| eps.bat_voltage | 0x0100 | Anormale — inférieure à la valeur attendue pour le SoC courant |
| eps.bat_soc | 0x0101 | Consigner la valeur courante et la tendance |
| eps.bat_temp | 0x0102 | Entre 0 et 40 °C (critique — surchauffe = danger) |
| eps.bat_current | 0x0109 | Consigner le courant de charge/décharge |
| eps.bat_capacity_wh | 0x010A | Réduite par rapport à la valeur nominale de 120 Wh |
| eps.bus_voltage | 0x0105 | Surveiller — peut chuter sous charge |
| eps.power_cons | 0x0106 | Consommation totale courante |
| eps.power_gen | 0x0107 | Puissance générée courante |
| eps.eclipse_flag | 0x0108 | État éclairé/éclipse courant |
| tcs.temp_battery | 0x0407 | Recouper avec la température batterie EPS |
| tcs.htr_battery | 0x040A | État du réchauffeur de batterie |

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| PAYLOAD_SET_MODE | 8 | 1 | 26 | Réduire la charge de la charge utile |
| FPA_COOLER | 8 | 1 | 43 | Arrêter le refroidisseur du FPA |
| TTC_PA_OFF | 8 | 1 | 67 | Arrêter le PA si nécessaire |
| HEATER_BATTERY | 8 | 1 | 40 | Commander le réchauffeur de batterie |
| HEATER_SET_SETPOINT | 8 | 1 | 44 | Ajuster les consignes du réchauffeur de batterie |
| EPS_POWER_OFF | 8 | 1 | 20 | Délester des lignes d'alimentation si nécessaire |

## Déroulement

### Étape 1 : Détecter et caractériser l'anomalie de tension batterie
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander les données de servitude EPS
**Verify:** `eps.bat_voltage` (0x0100) — consigner la valeur courante
**Verify:** `eps.bat_soc` (0x0101) — consigner la valeur courante
**Verify:** `eps.bat_capacity_wh` (0x010A) — consigner la valeur (nominale = 120 Wh)
**Verify:** `eps.bat_current` (0x0109) — consigner le courant (positif = charge, négatif = décharge)
**Action:** Calculer la tension attendue pour le SoC courant :
- un SoC de 100 % correspond à ~29.2 V, un SoC de 0 % à ~21.5 V (d'après le modèle de batterie) ;
- tension attendue = 21.5 + (SoC/100) * (29.2 - 21.5) = 21.5 + SoC * 0.077.
**Action:** Comparer la tension mesurée à la tension attendue :
- si la tension mesurée est inférieure de plus de 1.0 V à la valeur attendue : défaillance d'élément possible ;
- si la tension mesurée est à moins de 0.5 V de la valeur attendue : il peut s'agir d'une variation normale.
**Note:** La défaillance d'un seul élément dans une chaîne série réduit la tension totale de la
tension d'un élément (~3.6 V nominale pour le Li-ion).
**GO/NO-GO:** Anomalie de tension confirmée (écart > 1.0 V) — engager l'évaluation thermique.

### Étape 2 : Contrôler la température de la batterie
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — Demander les données de servitude TCS
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Données de servitude EPS
**Verify:** `eps.bat_temp` (0x0102) — consigner la valeur
**Verify:** `tcs.temp_battery` (0x0407) — recouper avec le capteur TCS
**Note:** Évaluer l'état thermique de la batterie :
**Note:** - Si la température de la batterie est > 40 °C : échauffement anormal. Court-circuit interne possible dans
**Note:** l'élément défaillant. Situation DANGEREUSE — risque d'emballement thermique.
**Note:** - Réduire immédiatement le courant de charge/décharge en délestant des charges.
**TC:** `HEATER_BATTERY(on=0)` (Service 8, Subtype 1, func_id 40) — Arrêter le réchauffeur de batterie
**Note:** - Surveiller étroitement la température (toutes les 30 s).
**Note:** - Si la température dépasse 50 °C, passer en mode EMERGENCY selon EMG-006.
**Note:** - Si la température de la batterie est comprise entre 0 et 35 °C : l'état thermique est actuellement sûr.
**Note:** Poursuivre avec l'évaluation de la capacité.
**Verify:** `tcs.htr_battery` (0x040A) — si le réchauffeur est sur ON et la batterie chaude, l'arrêter
pour éviter un échauffement inutile.
**GO/NO-GO:** Température de la batterie sûre — continuer. En cas de surchauffe, traiter d'abord le
problème thermique avant de poursuivre.

### Étape 3 : Évaluer la capacité restante de la batterie
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander les données de servitude EPS
**Verify:** `eps.bat_capacity_wh` (0x010A) — consigner la capacité rapportée
**Action:** Si la capacité est rapportée, utiliser cette valeur. Sinon,
estimer la capacité restante :
- capacité nominale : 120 Wh ;
- si un élément est défaillant en circuit ouvert : la capacité peut tomber à ~0 (chaîne série interrompue),
  sauf si le système de gestion de la batterie peut court-circuiter l'élément ;
- si un élément est défaillant en court-circuit : capacité réduite d'environ 15-20 % (un élément d'une
  chaîne multi-éléments ; tension réduite mais capacité partiellement conservée).
**Action:** Calculer le bilan de survie en éclipse :
- durée maximale d'éclipse (d'après la prévision d'orbite) : typiquement ~35 min en LEO ;
- puissance requise pendant l'éclipse : valeur courante de `eps.power_cons` (0x0106) ;
- énergie requise = puissance * eclipse_duration / 60 (en Wh) ;
- énergie disponible = bat_capacity_wh * (current_SoC/100 - 0.20)
  (en conservant 20 % de SoC comme minimum) ;
- marge = énergie disponible - énergie requise.
**GO/NO-GO:** Si la marge est > 0 : la batterie peut tenir l'éclipse à la charge actuelle. Si la marge est < 0 : réduction de charge nécessaire. L'étape 4 s'applique. -> GO `STEP-5` | NO-GO `STEP-4`

### Étape 4 : Réduire les charges si nécessaire
**LABEL:** `STEP-4`
**Note:** Si la marge de survie en éclipse est négative, réduire les charges par ordre de priorité :
1. Charge utile sur OFF (gain de ~8-45 W) :
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) — Charge utile sur OFF
   **Verify:** `payload.mode` (0x0600) = 0 en moins de 10 s
2. Refroidisseur du FPA sur OFF (gain de ~15 W) : `FPA_COOLER(on=0)` (func_id 43)
   **Verify:** `tcs.cooler_fpa` (0x040C) = 0 en moins de 5 s
3. Émetteur sur OFF (gain de ~20 W) — uniquement si l'éclipse est imminente et que le bilan de charge reste négatif :
   `TTC_PA_OFF` (func_id 67)
   **Verify:** `ttc.pa_on` (0x0516) = 0 en moins de 5 s
**Action:** Après chaque délestage, recalculer la marge de survie en éclipse.
**Verify:** `eps.power_cons` (0x0106) — confirmer la baisse de consommation
**Note:** Ajuster les consignes du réchauffeur de batterie pour réduire son rapport cyclique pendant l'éclipse :
**TC:** `HEATER_SET_SETPOINT(circuit=0, on_temp=-2.0, off_temp=2.0)` (Service 8, Subtype 1, func_id 44)
**Note:** La batterie peut ainsi se refroidir légèrement pendant l'éclipse pour économiser l'énergie,
tout en restant protégée contre des températures dangereusement basses.
**GO/NO-GO:** La marge de survie en éclipse est désormais positive — engager la surveillance.

### Étape 5 : Surveiller la batterie pendant l'éclipse (le cas échéant)
**LABEL:** `STEP-5`
**Note:** Si une éclipse approche ou est en cours, surveiller la batterie toutes les 60 s :
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.bat_voltage` (0x0100) — ne descend PAS sous 24.0 V
**Verify:** `eps.bat_soc` (0x0101) — ne descend PAS sous 20 %
**Verify:** `eps.bat_temp` (0x0102) — reste entre 0 et 40 °C
**Verify:** `eps.bus_voltage` (0x0105) — reste > 26.5 V
**Action:** Si `eps.bus_voltage` descend sous 26.5 V pendant l'éclipse : effectuer un
délestage supplémentaire selon CTG-001 (Délestage sur sous-tension).
**Action:** Après la sortie d'éclipse, vérifier :
- `eps.power_gen` (0x0107) > 25 W (reprise de la charge) ;
- `eps.bat_soc` (0x0101) en hausse ;
- `eps.bat_temp` (0x0102) stable.
**GO/NO-GO:** La batterie a tenu l'éclipse — engager l'évaluation à long terme.

### Étape 6 : Vérification de la capacité à long terme
**Action:** Au cours des 2-3 orbites suivantes, surveiller le comportement en charge/décharge de la batterie :
**Verify:** `eps.bat_soc` (0x0101) — le SoC remonte-t-il entièrement à > 90 % pendant la phase éclairée ?
**Verify:** `eps.bat_voltage` (0x0100) — la tension atteint-elle > 28.5 V en pleine charge ?
**Verify:** `eps.bat_capacity_wh` (0x010A) — la capacité rapportée a-t-elle changé ?
**Action:** Évaluer l'impact à long terme :
- si la capacité est réduite mais suffisante pour les opérations nominales avec marge : poursuivre
  les opérations avec un bilan de puissance ajusté ;
- si la capacité tombe en deçà du niveau nécessaire aux opérations nominales : réduire le rapport cyclique
  de la charge utile, limiter la prise de vue aux phases éclairées ou réduire le volume de données descendues.
**Action:** Documenter les constats dans le rapport d'anomalie :
- tension mesurée et tension attendue pour plusieurs valeurs de SoC ;
- perte de capacité estimée ;
- marges de survie en éclipse à la charge actuelle et à charge réduite ;
- contraintes opérationnelles recommandées.
**Action:** Informer le directeur de vol et l'équipe de planification de mission de toute contrainte opérationnelle.

## Critères de vérification
- [ ] Anomalie de tension batterie caractérisée (type de défaillance d'élément évalué)
- [ ] Température de la batterie dans les limites sûres (0 à 40 °C)
- [ ] Capacité restante suffisante pour la survie en éclipse (avec une marge > 10 %)
- [ ] Charges réduites si nécessaire pour s'adapter à la capacité dégradée de la batterie
- [ ] Batterie ayant traversé au moins une éclipse à capacité réduite
- [ ] Contraintes opérationnelles à long terme documentées
- [ ] Rapport d'anomalie déposé

## Contingence
- Si la température de la batterie dépasse 45 °C à un moment quelconque : risque d'emballement thermique. Arrêter
  immédiatement le réchauffeur de batterie. Délester toutes les charges non essentielles. Si la température dépasse
  50 °C, commander `OBC_SET_MODE(mode=2)` (EMERGENCY). Appliquer EMG-006.
- Si la tension de la batterie descend sous 22.0 V : risque de décharge profonde et de dommage permanent.
  Délester immédiatement toutes les charges sauf l'OBC et le récepteur TTC. Commander le mode EMERGENCY.
- Si le SoC de la batterie ne peut être maintenu au-dessus de 20 % sur une orbite complète : la
  dégradation de la batterie est trop importante pour les opérations actuelles. Exploiter le satellite dans un mode fortement
  réduit (charges minimales, opérations en phase éclairée uniquement). Consulter l'équipe d'ingénierie.
- Si la batterie présente des signes de courts-circuits intermittents (fluctuations de tension) : surveiller
  étroitement. Des courts-circuits intermittents peuvent évoluer en courts-circuits permanents ou en événements thermiques.
  Envisager une réduction préventive des charges même si les marges actuelles semblent suffisantes.
- En cas de défaillance d'un deuxième élément : la capacité de la batterie peut être réduite de façon critique. Évaluer
  immédiatement si le satellite peut survivre à l'éclipse. Sinon, demander la programmation de contacts
  d'urgence pour un soutien continu depuis le sol.
