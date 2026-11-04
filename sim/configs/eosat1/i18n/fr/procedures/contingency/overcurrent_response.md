# CTG-012 : Traitement d'une surintensité

**Catégorie :** Contingence
**Poste responsable :** Puissance et thermique (EPS/TCS)
**Postes associés :** poste du sous-système concerné (AOCS, TT&C, charge utile ou FDIR/Systèmes)
**Difficulté :** Intermédiaire

## Objectif
Traiter un déclenchement sur surintensité d'une ou plusieurs lignes d'alimentation de l'EPS. Cette procédure
identifie la ou les lignes déclenchées, évalue le courant de chaque ligne pour déterminer si le défaut
est transitoire ou persistant, isole le défaut, réinitialise l'indicateur de surintensité, réactive
la ligne d'alimentation concernée et vérifie le fonctionnement nominal du sous-système alimenté en aval.

## Prérequis
- [ ] Événement de surintensité détecté par la télémesure ou par une alarme
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Opérateur EPS en console ou directeur de vol informé
- [ ] Le satellite n'est pas en mode EMERGENCY — `obdh.mode` (0x0300) != 2

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| eps.oc_trip_flags | 0x010D | Un masque binaire non nul indique la ou les lignes déclenchées |
| eps.line_current_0 | 0x0118 | Courant de la ligne OBC |
| eps.line_current_1 | 0x0119 | Courant de la ligne TTC RX |
| eps.line_current_2 | 0x011A | Courant de la ligne TTC TX |
| eps.line_current_3 | 0x011B | Courant de la ligne charge utile |
| eps.line_current_4 | 0x011C | Courant de la ligne refroidisseur du FPA |
| eps.line_current_5 | 0x011D | Courant de la ligne réchauffeur batterie |
| eps.line_current_6 | 0x011E | Courant de la ligne réchauffeur OBC |
| eps.line_current_7 | 0x011F | Courant de la ligne roues AOCS |
| eps.pl_obc | 0x0110 | État de la ligne d'alimentation OBC |
| eps.pl_ttc_tx | 0x0112 | État de la ligne d'alimentation TTC TX |
| eps.pl_payload | 0x0113 | État de la ligne d'alimentation charge utile |
| eps.pl_fpa_cooler | 0x0114 | État de la ligne d'alimentation refroidisseur du FPA |
| eps.pl_aocs_wheels | 0x0117 | État de la ligne d'alimentation roues AOCS |
| eps.bus_voltage | 0x0105 | > 30.9 V |
| eps.bat_soc | 0x0101 | Consigner la valeur courante |

## Télécommandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| EPS_RESET_OC_FLAG | 8 | 1 | 21 | Réinitialiser l'indicateur de déclenchement sur surintensité et réactiver la ligne |
| EPS_POWER_ON | 8 | 1 | 19 | Mettre une ligne d'alimentation sur ON |
| EPS_POWER_OFF | 8 | 1 | 20 | Mettre une ligne d'alimentation sur OFF |

## Déroulement

### Étape 1 : Identifier la ou les lignes d'alimentation déclenchées
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander la télémesure de servitude EPS
**Verify:** `eps.oc_trip_flags` (0x010D) — décoder le masque binaire pour identifier la ou les lignes déclenchées :
- Bit 0 : OBC (ligne 0) — non commutable, critique
- Bit 1 : TTC RX (ligne 1) — non commutable, critique
- Bit 2 : TTC TX (ligne 2)
- Bit 3 : charge utile (ligne 3)
- Bit 4 : refroidisseur du FPA (ligne 4)
- Bit 5 : réchauffeur batterie (ligne 5)
- Bit 6 : réchauffeur OBC (ligne 6)
- Bit 7 : roues AOCS (ligne 7)
**Note:** Consigner la ou les lignes déclenchées et l'heure de détection.
**GO/NO-GO:** Ligne(s) déclenchée(s) identifiée(s) — passer à l'évaluation des courants.

### Étape 2 : Contrôler le courant de chaque ligne pour évaluer le défaut
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander la télémesure de servitude EPS
**Verify:** Contrôler le courant de la ligne déclenchée (0x0118 à 0x011F) :
- Si le courant est proche de 0 A : la ligne a été déconnectée par le LCL (attendu après un déclenchement).
- Si le courant reste élevé : défaut persistant — NE PAS réactiver la ligne. L'isoler et
  analyser la cause.
**Verify:** Contrôler les registres d'état des lignes d'alimentation (0x0110 à 0x0117) pour confirmer que la ligne
est sur OFF après le déclenchement.
**Verify:** `eps.bus_voltage` (0x0105) > 30.9 V — le bus est stable sans la charge déclenchée.
**Action:** Consigner tous les courants de ligne pour le rapport d'anomalie.
**GO/NO-GO:** En cas de surintensité persistante détectée sur la ligne, NE PAS procéder à la réinitialisation.
Faire remonter à l'équipe d'ingénierie. Si le courant est nominal (proche de 0), continuer.

### Étape 3 : Isoler le défaut — se coordonner avec le sous-système concerné
**Action:** Informer l'opérateur du poste responsable du sous-système concerné :
- Ligne 2 (TTC TX) : informer l'opérateur TT&C
- Ligne 3 (charge utile) : informer l'opérateur charge utile
- Ligne 4 (refroidisseur du FPA) : informer l'opérateur charge utile / EPS-TCS
- Ligne 5 (réchauffeur batterie) : traitée directement par l'opérateur EPS/TCS
- Ligne 6 (réchauffeur OBC) : traitée directement par l'opérateur EPS/TCS
- Ligne 7 (roues AOCS) : informer l'opérateur AOCS
**Action:** L'opérateur du sous-système concerné confirme que le sous-système était dans un état connu
avant le déclenchement et qu'aucun indice ne signale de dommage matériel.
**Verify:** Si le déclenchement s'est produit pendant une transition de mode ou une mise sous tension, évaluer
si un courant d'appel a pu provoquer un déclenchement transitoire.
**GO/NO-GO:** Défaut jugé probablement transitoire — procéder à la réinitialisation. En cas de suspicion de dommage
matériel, HOLD et faire remonter l'anomalie.

### Étape 4 : Réinitialiser l'indicateur de surintensité
**Note:** Réinitialiser l'indicateur de déclenchement sur surintensité de la ligne concernée :
**TC:** `EPS_RESET_OC_FLAG(line_index=N)` (Service 8, Subtype 1, func_id 21) — où N est l'indice de la ligne déclenchée (0 à 7).
**Verify:** `eps.oc_trip_flags` (0x010D) — confirmer que le bit de la ligne concernée est retombé.
**Verify:** Attendre 5 s et contrôler de nouveau `eps.oc_trip_flags` pour confirmer que l'indicateur reste retombé.
**GO/NO-GO:** Indicateur OC retombé — procéder à la réactivation.

### Étape 5 : Réactiver la ligne d'alimentation
**Note:** N est la ligne qui a déclenché : 2 ttc_tx, 3 payload, 4 fpa_cooler,
5 htr_bat, 6 htr_obc, 7 aocs_wheels. Les lignes 0 (obc) et 1 (ttc_rx) ne sont
pas commutables et ne peuvent pas déclencher de cette façon.
**TC:** `EPS_POWER_ON(line_index=3)` (Service 8, Subtype 1, func_id 19) — exemple : la ligne charge utile
**Verify:** Registre d'état de la ligne d'alimentation (0x0110 + N) = 1 (ON) en 5 s
**Verify:** Le courant de la ligne (0x0118 + N) revient à la valeur nominale attendue
**Verify:** `eps.oc_trip_flags` (0x010D) reste à zéro (pas de nouveau déclenchement)
**Action:** Attendre 30 s pour confirmer la stabilité de la ligne.
**GO/NO-GO:** Ligne réactivée et stable — passer à la vérification.

### Étape 6 : Vérifier la reprise du sous-système aval
**Note:** Demander la télémesure de servitude du sous-système concerné :
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Roues AOCS : vérifier `aocs.mode` (0x020F) et les vitesses des roues
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Charge utile : vérifier `payload.mode` (0x0600)
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TTC TX : vérifier `ttc.link_status` (0x0501) = 2 (LOCKED).
  Le SID 6 est la structure TT&C ; le SID 5 est celle de la charge utile.
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — Réchauffeurs : vérifier l'état des réchauffeurs et les températures
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Télémesure de servitude EPS
**Verify:** Le sous-système aval fonctionne nominalement.
**Verify:** `eps.power_cons` (0x0106) reflète la charge réintroduite.
**Verify:** `eps.bus_voltage` (0x0105) > 30.9 V avec la charge rétablie.
**GO/NO-GO:** Sous-système nominal et bilan de puissance stable — procédure terminée.

## Critères de vérification
- [ ] `eps.oc_trip_flags` (0x010D) = 0 (tous les indicateurs retombés)
- [ ] État de la ligne d'alimentation concernée = ON
- [ ] Courant de la ligne dans la plage nominale attendue
- [ ] Sous-système aval en fonctionnement nominal
- [ ] Tension du bus stable > 30.9 V
- [ ] Aucun nouveau déclenchement dans les 5 minutes suivant la réactivation

## Cas de contingence
- Si l'indicateur de surintensité déclenche de nouveau aussitôt après la réinitialisation : NE PAS tenter de troisième réinitialisation.
  Le défaut est persistant. Commander `EPS_POWER_OFF(line_index=N)` pour isoler la ligne.
  Faire remonter à l'équipe d'ingénierie pour une évaluation matérielle.
- Si un nouveau déclenchement survient dans les 5 minutes suivant la réactivation : défaut intermittent possible. Commander
  `EPS_POWER_OFF(line_index=N)`. Attendre le contact suivant pour un nouvel essai. Si le déclenchement se répète,
  traiter le défaut comme persistant.
- Si la ligne déclenchée est celle de l'OBC (ligne 0) ou du TTC RX (ligne 1) : ce sont des lignes critiques
  non commutables. Un déclenchement OC sur ces lignes signale une anomalie grave. Faire remonter
  immédiatement au directeur de vol et l'équipe d'ingénierie.
- Si la tension du bus chute après la réactivation de la ligne : la charge absorbe peut-être un courant
  excessif. Commander immédiatement `EPS_POWER_OFF(line_index=N)` et analyser la cause.
- Si plusieurs lignes ont déclenché simultanément : suspecter un défaut au niveau du bus plutôt qu'un
  problème d'une seule ligne. Contrôler `eps.bus_voltage`, `eps.bat_voltage` et `eps.bat_current`.
  Faire remonter au directeur de vol.

## Chemin de reprise — remise sous tension des charges délestées
Une fois le bus stabilisé par cette procédure et la cause première comprise, **tout sous-système dont les lignes d'alimentation ont été mises hors tension lors du délestage doit être remis en service dans l'ordre maîtrisé défini par LEOP-007 (mise sous tension séquentielle)**. Ne **pas** se contenter de réactiver les lignes au coup par coup : LEOP-007 impose le bon enchaînement sous-système→ligne→mode, l'espacement des courants d'appel, le préconditionnement thermique des réchauffeurs OBC/batterie et les exemptions set_mode AOCS/charge utile au verrou d'alimentation à deux niveaux des TC. Référence croisée : `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
