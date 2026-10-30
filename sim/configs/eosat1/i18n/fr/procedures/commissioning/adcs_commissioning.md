# COM-013 : Clôture de la recette du SCAO et déclaration NOMINAL

**Sous-système :** AOCS / Tous
**Phase :** COMMISSIONING
**Révision :** 2.0 --- dédoublonnage 2026-08c. La révision 1.0 refaisait des travaux relevant d'autres
fiches (contrôles du magnétomètre = LEOP-007/COM-003, senseurs stellaires et étalonnage des
gyromètres = COM-003, contrôles de signe des roues et des magnétocoupleurs = COM-004, amortissement
et transitions de modes = LEOP-005/COM-005) et faisait référence à du matériel non
installé : il n'y a qu'UN magnétomètre (le bloc de TM à deux unités 0x0223-0x0229 et
la commande MAG_SELECT sont retirés --- la func 7 est REFUSÉE à bord). Cette
révision est la fiche de CLÔTURE : elle suppose acquis l'état de sortie de chaque fiche précédente,
relit l'état final consolidé sans rien réessayer, et effectue
la seule déclaration qui met fin à la recette en orbite.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-011 (ordre définitif … COM-010, COM-012
première lumière, COM-011 étalonnage, COM-013) --- recette de la charge utile effectuée : première
lumière acquise et vidée par le S13, données d'étalonnage radiométrique recueillies ;
AOCS en NOMINAL commandé avec les roues activées et les gyromètres étalonnés ; liaison descendante
revenue en LOW ; OBC en NOMINAL ; phase de mission 5.

## Objet
Clore la recette en orbite : vérifier l'état final consolidé du satellite par rapport à
l'état de sortie déclaré de chaque fiche, faire le tour de table de toutes les positions, et déclarer la phase de mission
6 (NOMINAL) --- l'unique transition commandée qui déverrouille le mode satellite dérivé
NOMINAL, arme les règles FDIR conditionnées par la phase et le verrouillage de la propulsion.
Rien à bord ne fait avancer la phase à votre place ; la déclaration est
la télécommande propre à cette fiche et aucune autre fiche ne la contient.

## Prérequis
- [ ] COM-001 à COM-012 terminées, avec leurs états de sortie vérifiés
- [ ] `eps.bat_soc` (0x0101) > 60 %
- [ ] Liaison bidirectionnelle en bande S active sur un passage programmé
- [ ] Briefing du directeur de vol tenu ; liste de contrôle de pré-transition du manuel
      LEOP (§9.1) passée en revue

## Déroulement

### Étape 1 --- Relecture consolidée de l'état final de l'AOCS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.mode` (0x020F) dans {4, 5, 8} --- famille opérationnelle
**Verify:** `aocs.commanded_mode` (0x0297) = 4 et `aocs.mode_demoted` (0x0298) = 0
**Verify:** `aocs.wheels_enabled` (0x0260) = 4 (état de sortie de COM-004)
**Verify:** `aocs.gyro_units_mask` (0x02D1) = 7 (état de sortie de COM-003)
**Verify:** `aocs.st1_status` (0x0240) = 2 avec `aocs.st1_num_stars` (0x0241) >= 5
**Verify:** `aocs.mag_enabled` (0x025C) = 1 et `aocs.mag_field_total` (0x0277)
dans [5000, 70000] nT --- l'unique magnétomètre (il n'existe pas d'unité B ; rien à
sélectionner)
**Verify:** `aocs.att_error` (0x0217) < 1.0 deg (côté éclairé)
**GO/NO-GO:** L'état final de l'AOCS correspond à la somme de ses fiches

### Étape 2 --- Relecture consolidée de l'état final de la plateforme
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27)
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27)
**Verify:** `obdh.mode` (0x0300) = 0 --- NOMINAL (COM-007 l'a rétabli ; un
satellite sur le point de déclarer NOMINAL ne doit pas porter un OBC en SAFE)
**Verify:** `ttc.tm_tier` (0x0539) = 1 (LOW) et `ttc.downlink_mode` (0x053C) = 0
--- aucune fiche n'a laissé le verrou HIGH ouvert (états de sortie de COM-006/COM-012)
**Verify:** `eps.load_shed_stage` (0x0134) = 0 --- aucun verrou de délestage laissé positionné (COM-008)
**Verify:** `eps.bus_voltage` (0x0105) dans [26.5, 29.5] V ; `eps.bat_soc`
(0x0101) > 60 %
**Verify:** `obdh.time_ref` (0x0A13) != 0 --- horloge référencée (LEOP-006)
**GO/NO-GO:** État final de la plateforme propre --- rien de laissé armé, délesté ou levé

### Étape 3 --- Relecture consolidée de l'état final de la charge utile
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27)
**Verify:** `payload.mode` (0x0600) = 1 --- STANDBY (jamais laissée en IMAGING)
**Verify:** `payload.fpa_ready` (0x0610) = 1 --- refroidisseur en régulation (COM-010)
**Verify:** `payload.transfer_active` (0x062D) = 0 --- aucune session S13 laissée ouverte
**GO/NO-GO:** Recette de la charge utile effectuée, charge utile au repos

### Étape 4 --- Déclarer les opérations NOMINAL (phase 6)
**Action:** Le FD fait le tour de table de toutes les positions. Dérouler la liste de contrôle de pré-transition :
modes de l'OBC et de l'AOCS, erreur d'attitude soutenue, SoC de la batterie et marge de puissance,
capteurs et actionneurs répondant, liaison stable, point GPS valide, zones thermiques dans
leurs limites, surveillance S12 et événements-actions S19 activés.
**Note:** C'est la déclaration de NOMINAL (6) qui déverrouille réellement les opérations nominales.
En deçà de la phase 6, le mode satellite dérivé (`sat.mode` 0x0001, ainsi que l'en-tête de la
console) est figé sur SAFE quel que soit l'état de santé du satellite ; le modèle avancé de
propagation des pannes et les règles FDIR conditionnées par la phase sont désarmés ; et le
verrouillage de la propulsion refuse d'armer une poussée (`prop.yaml min_phase: 6`).
**TC:** `SYS_SET_MISSION_PHASE(phase=6, flags=0)` (Service 8, Subtype 1, func_id 120)
**Verify:** `eps.spacecraft_phase` (0x0129) = 6 sous 5s
**Verify:** `sat.mode` (0x0001) = 1 sous 10s --- NOMINAL dérivé
**Action:** Confirmer que l'événement `MISSION_PHASE_CHANGED` (0x0055) apparaît dans le
journal des événements avec `5 (COMMISSIONING) -> 6 (NOMINAL)`, et consigner
l'heure de la transition dans le journal de mission.
**Note:** Le retour en arrière est refusé sauf si l'indicateur FORCE est positionné (bit 0 de flags = 1)
--- un ralentisseur délibéré. Si une déclaration a été prématurée, la renvoyer avec
l'indicateur et en consigner la raison.
**GO/NO-GO:** Phase = NOMINAL, satellite déclaré opérationnel

### Étape 5 --- Maintenir et passer la main
**Action:** Maintenir pendant au moins un cycle d'éclipse complet, les règles FDIR désormais armées
étant évaluées. Confirmer dans l'archive que `sat.mode` (0x0001) reste à 1
et que `aocs.mode` (0x020F) reste dans {4, 5, 8} tout du long.
**Action:** Diffuser le rapport de clôture de la recette en orbite et passer la console
à l'équipe des opérations nominales (NOM-001 et suivantes).
**GO/NO-GO:** NOMINAL maintenu sur une orbite --- recette en orbite CLOSE

## Conduite à tenir hors nominal
- Si l'une des relectures des étapes 1-3 échoue : NE PAS déclarer la phase 6. Se reporter à la section hors nominal de la fiche responsable (les lignes de vérification ci-dessus la nomment) et rétablir d'abord son état de sortie.
- Si `SYS_SET_MISSION_PHASE` est refusée : 0x0C03 = OBC dans le chargeur d'amorçage (un redémarrage a eu lieu --- exécuter de nouveau LEOP-001, étape 5, puis LEOP-006) ; 0x0C04 = retour en arrière sans FORCE.
- Si `sat.mode` ne dérive pas 1 après la déclaration : une contingence FDIR est verrouillée --- lire le journal FDIR, supprimer la cause, et le mode dérivé se rétablit de lui-même. Aucune TC ne positionne directement sat.mode.
- Si l'AOCS rétrograde pendant le maintien de l'étape 5 : la règle FDIR `aocs.att_error` désormais armée commande COARSE_SUN sur une excursion réelle ; l'échelle de reprise automatique s'applique. Analyser l'excursion avant de redéclarer quoi que ce soit.

## État de sortie
- Phase de mission 6, `sat.mode` = 1 (NOMINAL) ; FDIR entièrement armée
- AOCS en NOMINAL commandé ; charge utile en STANDBY avec le FPA en régulation ; liaison descendante en LOW ;
  OBC en NOMINAL ; aucun verrouillage, aucune session ni aucun verrou laissé ouvert
- Le satellite constitue la référence des opérations nominales que suppose NOM-001

## Postconditions
- [ ] État de sortie de chaque fiche de recette en orbite revérifié en consolidation
- [ ] Phase 6 déclarée (événement 0x0055 journalisé), `sat.mode` = 1
- [ ] NOMINAL maintenu pendant un cycle d'éclipse complet
- [ ] Rapport de clôture de la recette en orbite diffusé

**PROCÉDURE SUIVANTE :** Opérations nominales (NOM-001 Ouverture de passage). La recette en orbite est close.
