# CTG-015 : Reprise après image corrompue

**Catégorie :** Contingence
**Poste responsable :** Opérations charge utile
**Postes associés :** Puissance et thermique (EPS/TCS)
**Difficulté :** Intermédiaire

## Objectif
Analyser et traiter des données d'image corrompues, détectées par des erreurs de somme de contrôle à bord.
Cette procédure détermine si la corruption provient des conditions thermiques du plan focal (FPA),
de la défaillance d'un segment mémoire ou d'un événement transitoire, et engage les actions
correctives, y compris l'interruption de la prise de vue si nécessaire et une nouvelle acquisition de la scène.

## Prérequis
- [ ] Erreurs de somme de contrôle détectées — `payload.checksum_errors` (0x0609) a augmenté
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Charge utile en mode STANDBY ou IMAGING — `payload.mode` (0x0600) >= 1
- [ ] Opérateur charge utile en console

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| payload.checksum_errors | 0x0609 | En hausse par rapport à la référence (déclencheur de l'anomalie) |
| payload.fpa_temp | 0x0601 | < -25.0 °C pour la qualité d'image |
| payload.fpa_ready | 0x0610 | 1 (FPA dans la plage) |
| payload.imager_temp | 0x0603 | < 30 °C |
| payload.mem_segments_bad | 0x0612 | 0 en nominal ; > 0 indique un problème mémoire |
| payload.store_used | 0x0604 | Niveau de stockage courant |
| payload.image_count | 0x0605 | Nombre d'images courant |
| payload.last_scene_id | 0x060C | Dernière scène acquise |
| payload.last_scene_quality | 0x060D | Indicateur de qualité de la dernière image |
| payload.mode | 0x0600 | Mode courant de la charge utile |
| tcs.temp_fpa | 0x0408 | < -25.0 °C (recouper avec le capteur de la charge utile) |
| tcs.cooler_fpa | 0x040C | 1 (refroidisseur actif) |

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| PAYLOAD_SET_MODE | 8 | 1 | 26 | Régler le mode de la charge utile |
| PAYLOAD_CAPTURE | 8 | 1 | 28 | Relancer une acquisition d'image |
| PAYLOAD_DELETE_IMAGE | 8 | 1 | 30 | Supprimer l'image corrompue |
| FPA_COOLER | 8 | 1 | 43 | Commander le refroidisseur du FPA |
| PAYLOAD_MARK_BAD_SEGMENT | 8 | 1 | 31 | Déclarer un segment mémoire inutilisable |

## Déroulement

### Étape 1 : Détecter et quantifier les erreurs de somme de contrôle
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Demander les données de servitude de la charge utile
**Verify:** `payload.checksum_errors` (0x0609) — consigner la valeur courante et la comparer à la
référence précédente. Calculer l'écart (nombre de nouvelles erreurs).
**Verify:** `payload.last_scene_id` (0x060C) — consigner la scène potentiellement touchée
**Verify:** `payload.last_scene_quality` (0x060D) — consigner l'indicateur de qualité
**Verify:** `payload.image_count` (0x0605) — consigner le nombre courant
**Note:** Une erreur de somme de contrôle isolée peut être un événement transitoire (SEU). Plusieurs erreurs sur la
même scène laissent penser à un problème systématique.
**GO/NO-GO:** Erreurs de somme de contrôle confirmées — engager la recherche de la cause racine.

### Étape 2 : Contrôler la température du FPA
**Note:** Demander les données de servitude de la charge utile et du TCS :
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — HK charge utile
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — HK TCS
**Verify:** `payload.fpa_temp` (0x0601) — consigner la valeur
**Verify:** `tcs.temp_fpa` (0x0408) — recouper avec le capteur TCS
**Verify:** `payload.fpa_ready` (0x0610) — vérifier si le FPA est dans sa plage opérationnelle
**Verify:** `tcs.cooler_fpa` (0x040C) — confirmer que le refroidisseur est actif
**Action:** Évaluer l'état thermique du FPA :
- Si `payload.fpa_temp` > -20.0 °C : le FPA est trop chaud pour une imagerie de qualité. L'étape 3
  (interruption de la prise de vue, attente du refroidissement) s'applique.
- Si `payload.fpa_temp` < -25.0 °C et `payload.fpa_ready` = 1 : le FPA est nominal.
  L'étape 4 (contrôle de la mémoire) s'applique.
**GO/NO-GO:** Évaluation du FPA terminée — suivre la branche appropriée.
**BRANCH:** `payload.fpa_ready == 1` -> GO `STEP-4` | NO-GO `STEP-3` (timeout 10 s)

### Étape 3 : FPA trop chaud — interrompre la prise de vue et refroidir
**LABEL:** `STEP-3`
**Note:** Uniquement si `payload.mode` (0x0600) = 2 (IMAGING). Le mode 3 est CALIBRATION
et s'interrompt avec la même commande ; le mode 1 est déjà STANDBY et ne demande aucune action.
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) — interruption vers STANDBY
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) en moins de 10 s
**Note:** Vérifier que le refroidisseur est actif : si `tcs.cooler_fpa` (0x040C) = 0, l'activer :
**TC:** `FPA_COOLER(on=1)` (Service 8, Subtype 1, func_id 43)
**Verify:** `tcs.cooler_fpa` (0x040C) = 1 en moins de 5 s
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Données de servitude charge utile ; surveiller la mise en froid du FPA toutes les 60 s
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — Données de servitude TCS
**Verify:** `payload.fpa_temp` (0x0601) en baisse vers la cible (consigne du refroidisseur à -5 °C,
seuil opérationnel à -25 °C)
**Note:** La mise en froid depuis l'ambiante (~5 °C) jusqu'à la température opérationnelle (< -25 °C) dure environ
100-150 s selon le modèle thermique (tau ~100 s).
**Action:** Attendre que `payload.fpa_temp` < -25.0 °C et `payload.fpa_ready` = 1
**GO/NO-GO:** FPA refroidi à sa température opérationnelle — l'étape 5 (nouvelle acquisition) s'applique.
**BRANCH:** `payload.fpa_ready == 1` -> GO `STEP-5` | NO-GO `STEP-END` (timeout 300 s)

### Étape 4 : Contrôler les segments mémoire
**LABEL:** `STEP-4`
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Demander les données de servitude de la charge utile
**Verify:** `payload.mem_segments_bad` (0x0612) — consigner la valeur courante
**Verify:** `payload.store_used` (0x0604) — consigner l'occupation du stockage
**Action:** Si `payload.mem_segments_bad` > 0 :
- la défaillance d'un segment mémoire est une cause possible de la corruption ;
- appliquer CTG-016 (Défaillance d'un segment mémoire) pour identifier et déclarer le segment
  défectueux avant de poursuivre.
**Action:** Si `payload.mem_segments_bad` = 0 et que le FPA est froid :
- la corruption est probablement due à un événement transitoire (événement singulier, impact de particule) ;
- l'étape 5 (nouvelle acquisition) s'applique.
**GO/NO-GO:** Évaluation de la mémoire terminée — engager la nouvelle acquisition si elle est appropriée.

### Étape 5 : Supprimer l'image corrompue et acquérir à nouveau la scène
**LABEL:** `STEP-5`
**TC:** `PAYLOAD_DELETE_IMAGE(scene_id=N)` (Service 8, Subtype 1, func_id 30) — Supprimer l'image corrompue
N étant l'identifiant de la scène touchée relevé à l'étape 1.
**Verify:** `payload.store_used` (0x0604) diminue (stockage libéré)
**Verify:** `payload.image_count` (0x0605) diminue de 1
**Action:** Si la fenêtre de prise de vue est encore disponible et que toutes les conditions sont réunies :
- `payload.fpa_temp` (0x0601) < -25.0 °C
- `payload.fpa_ready` (0x0610) = 1
- `payload.mem_segments_bad` (0x0612) = 0 (ou segments défectueux déclarés)
- `aocs.att_error` (0x0217) < 0.1°
**TC:** `PAYLOAD_CAPTURE(scene_id=N, lines=L)` (Service 8, Subtype 1, func_id 28) — Acquérir à nouveau la scène
**Octets émis :** `1C <scene_id:uint16> <lines:uint16>` — p. ex. scène 1042, 2048 lignes = `1C 04 12 08 00`.
`scene_id` 0 laisse la charge utile attribuer automatiquement le prochain identifiant libre ; `lines` est le nombre de lignes du
détecteur le long de la trace, de 256 à 20000 (2048 = l'image de référence 4 bandes de 4,0 Mo). La géolocalisation n'est PAS un argument —
elle est horodatée à bord à partir du point sous-satellite propagé à l'ouverture de l'obturateur.
**Verify:** `payload.image_count` (0x0605) augmente de 1
**Verify:** `payload.checksum_errors` (0x0609) n'augmente PAS
**Verify:** `payload.last_scene_quality` (0x060D) — consigner l'indicateur de qualité de la nouvelle image
**GO/NO-GO:** Nouvelle acquisition réussie sans nouvelle erreur — procédure terminée.

### Étape 6 : Vérification après acquisition
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Demander les dernières données de servitude de la charge utile
**Verify:** `payload.checksum_errors` (0x0609) — aucune nouvelle hausse
**Verify:** `payload.last_scene_quality` (0x060D) — qualité acceptable
**Verify:** `payload.store_used` (0x0604) — dans les limites de capacité
**Action:** Consigner l'incident : identifiant de la scène d'origine, nombre d'erreurs, cause racine retenue
(thermique / mémoire / transitoire) et résultat de la nouvelle acquisition.

## Critères de vérification
**LABEL:** `STEP-END`
- [ ] Cause racine identifiée (thermique du FPA, segment mémoire ou transitoire)
- [ ] Image corrompue supprimée du stockage
- [ ] Image acquise à nouveau (si la fenêtre le permet) sans erreur de somme de contrôle
- [ ] `payload.fpa_temp` (0x0601) < -25.0 °C confirmée
- [ ] `payload.fpa_ready` (0x0610) = 1
- [ ] `payload.mem_segments_bad` (0x0612) traité (segment déclaré défectueux ou valeur 0 confirmée)
- [ ] Rapport d'anomalie déposé

## Contingence
- Si les erreurs de somme de contrôle persistent après la nouvelle acquisition, avec un FPA froid et sans segment défectueux :
  problème possible de l'électronique de l'imageur. Passer la charge utile en STANDBY. Effectuer un cycle d'alimentation de la charge utile :
  `PAYLOAD_SET_MODE(mode=0)`, attendre 30 s, `PAYLOAD_SET_MODE(mode=1)`. Si les erreurs persistent,
  faire remonter à l'équipe d'ingénierie.
- Si le refroidisseur ne parvient pas à refroidir le FPA sous -25 °C : le refroidisseur est peut-être dégradé. Contrôler
  `payload.cooler_pwr` (0x0602) pour vérifier la puissance absorbée attendue. Si la puissance du refroidisseur est nulle (0) alors que
  le refroidisseur est commandé sur ON, suspecter une panne matérielle du refroidisseur. Faire remonter l'anomalie.
- Si plusieurs images sont corrompues : vérifier si toutes les images corrompues correspondent à la même zone
  mémoire. Si c'est le cas, il s'agit probablement d'une défaillance mémoire localisée — déclarer le segment défectueux selon
  CTG-016.
- Si la fenêtre de prise de vue est passée et qu'une nouvelle acquisition est impossible : consigner la scène perdue.
  Se coordonner avec la planification de mission pour programmer une nouvelle acquisition lors d'un passage ultérieur.
