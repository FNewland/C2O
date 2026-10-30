# CTG-016 : Défaillance d'un segment mémoire

**Catégorie :** Contingence
**Poste responsable :** Opérations charge utile
**Postes associés :** (aucun — procédure interne à la charge utile)
**Difficulté :** Intermédiaire

## Objectif
Détecter, identifier et isoler un segment défaillant de la mémoire de masse de la charge utile. Cette
procédure déclare le segment défectueux inutilisable, vérifie que la capacité restante est
suffisante pour poursuivre les opérations et ajuste le plan de prise de vue pour tenir compte de la capacité
de stockage réduite.

## Prérequis
- [ ] Hausse du nombre de segments mémoire défectueux détectée — `payload.mem_segments_bad` (0x0612) > 0
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Charge utile en mode STANDBY — `payload.mode` (0x0600) = 1
- [ ] Aucune séance de prise de vue active (interrompre la prise de vue avant d'exécuter cette procédure)

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| payload.mem_segments_bad | 0x0612 | > 0 (en hausse par rapport à la dernière valeur connue) |
| payload.mem_total_mb | 0x060A | Capacité mémoire totale |
| payload.mem_used_mb | 0x060B | Mémoire actuellement occupée |
| payload.store_used | 0x0604 | Taux d'occupation du stockage (%) |
| payload.image_count | 0x0605 | Nombre d'images actuellement stockées |
| payload.checksum_errors | 0x0609 | Peut être élevé en cas de corruption |
| payload.mode | 0x0600 | 1 (STANDBY) |

## Télécommandes requises
| Télécommande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| PAYLOAD_MARK_BAD_SEGMENT | 8 | 1 | 31 | Déclarer un segment mémoire inutilisable |
| PAYLOAD_GET_IMAGE_CATALOG | 8 | 1 | 32 | Demander le catalogue des images stockées |
| PAYLOAD_DELETE_IMAGE | 8 | 1 | 30 | Supprimer une image du segment touché |
| MEM_CHECK | 6 | 9 | — | Contrôle CRC de la mémoire |

## Déroulement

### Étape 1 : Détecter la défaillance d'un segment mémoire
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Demander les données de servitude de la charge utile
**Verify:** `payload.mem_segments_bad` (0x0612) — consigner la valeur courante et la comparer à la
dernière valeur connue. Calculer le nombre de segments nouvellement défaillants.
**Verify:** `payload.mem_total_mb` (0x060A) — consigner la capacité totale
**Verify:** `payload.mem_used_mb` (0x060B) — consigner la capacité occupée
**Verify:** `payload.store_used` (0x0604) — consigner le pourcentage
**Verify:** `payload.checksum_errors` (0x0609) — consigner la valeur (peut être corrélée à la défaillance du segment)
**Note:** Chaque segment mémoire représente environ 2 500 Mo (total de 20 000 Mo / 8 segments).
Un seul segment défectueux réduit la capacité de 12,5 %.
**GO/NO-GO:** Défaillance de segment confirmée — engager l'identification.

### Étape 2 : Identifier le segment défaillant
**Note:** Demander le catalogue des images pour déterminer le ou les segments potentiellement touchés :
**TC:** `PAYLOAD_GET_IMAGE_CATALOG` (Service 8, Subtype 1, func_id 32)
**Action:** Rechercher dans le catalogue les images ayant signalé des erreurs de somme de contrôle. Le segment
qui héberge l'image corrompue est probablement le segment défaillant.
**Note:** Si le segment défaillant ne peut être déterminé à partir du catalogue, effectuer un
**TC:** `MEM_CHECK(memory_id=0, address=SEGMENT_START, length=SEGMENT_SIZE)` (Service 6, Subtype 9) — contrôle CRC de la mémoire
**Note:** (Service 6, Subtype 9) pour chaque segment suspect.
**Verify:** Résultat du contrôle CRC — les segments dont le CRC ne correspond pas sont confirmés défectueux.
**Note:** L'indice de segment va de 0 à 7. Si l'indice précis du segment est connu
grâce aux diagnostics de bord, le contrôle CRC manuel est inutile.
**GO/NO-GO:** Segment(s) défaillant(s) identifié(s) — engager la déclaration.

### Étape 3 : Déclarer le segment défectueux
**Note:** Déclarer le segment défaillant inutilisable :
**TC:** `PAYLOAD_MARK_BAD_SEGMENT(segment_id=N)` (Service 8, Subtype 1, func_id 31) — N étant l'indice du segment (**0-7** ;
**Note:** `num_memory_segments: 8` dans `subsystems/payload.yaml` — le modèle REJETTE tout indice >= 8. L'ancienne
**Note:** plage « 0-79 » n'a jamais été exécutable).
**Octets émis :** `1F 0N` — p. ex. segment 3 = `1F 03`
**Verify:** Demander les données de servitude de la charge utile : `HK_REQUEST(sid=5)` (Service 3, Subtype 27)
**Verify:** `payload.mem_segments_bad` (0x0612) — confirmer que le compteur intègre le segment nouvellement déclaré
**Note:** Si plusieurs segments sont défectueux, répéter cette étape pour chaque segment identifié.
**Note:** Si des images étaient stockées dans le segment défectueux, les supprimer :
**TC:** `PAYLOAD_DELETE_IMAGE(scene_id=X)` (Service 8, Subtype 1, func_id 30) — pour chaque scène touchée.
**GO/NO-GO:** Segment(s) défectueux déclaré(s) et images touchées supprimées — continuer.

### Étape 4 : Vérifier la capacité réduite
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Demander les données de servitude de la charge utile
**Verify:** `payload.mem_total_mb` (0x060A) — confirmer que la capacité totale rapportée tient compte de la
réduction (baisse attendue d'environ 2 500 Mo par segment défectueux)
**Verify:** `payload.store_used` (0x0604) — recalculer le pourcentage sur la base de la nouvelle capacité totale
**Verify:** `payload.mem_used_mb` (0x060B) — confirmer que la mémoire occupée est exacte
**Action:** Calculer la capacité utilisable restante :
- capacité utilisable = capacité totale - (segments défectueux x 2 500 Mo) - stockage occupé ;
- images restantes = capacité utilisable / 4 Mo par image brute (`payload.yaml image_size_mb` ;
  1-2,7 Mo après passage du compresseur CCSDS-123 de bord).
**Note:** Consigner les valeurs de capacité mises à jour dans le journal des opérations.
**GO/NO-GO:** Capacité réduite vérifiée et documentée — engager l'ajustement du plan.

### Étape 5 : Ajuster le plan de prise de vue
**Action:** Évaluer l'impact sur le plan de prise de vue en cours :
- si la capacité restante permet toutes les prises de vue prévues : aucune modification du plan n'est nécessaire ;
- si la capacité restante est insuffisante : hiérarchiser les cibles de prise de vue. Envisager de
  programmer des transmissions de données au sol entre les séances de prise de vue pour libérer du stockage ;
- si plus d'un segment est défectueux (> 1 sur 8, plus de 12,5 % de la capacité) : faire remonter à l'équipe de planification
  de mission pour une évaluation de la capacité à long terme. Envisager de réduire la résolution des images ou
  d'ajuster les paramètres de compression pour réduire le stockage par image.
**Action:** Informer le directeur de vol de la capacité mise à jour et de toute modification du plan de prise de vue.
**Action:** Mettre à jour le journal des opérations avec :
- le ou les indices des segments défectueux ;
- le nombre total de segments défectueux ;
- la capacité utilisable restante ;
- l'évaluation de l'impact sur le plan de prise de vue.
**GO/NO-GO:** Plan de prise de vue ajusté — procédure terminée.

## Critères de vérification
- [ ] Segment(s) défaillant(s) identifié(s) et déclaré(s) au moyen de `PAYLOAD_MARK_BAD_SEGMENT`
- [ ] `payload.mem_segments_bad` (0x0612) reflète exactement le nombre total de segments défectueux
- [ ] Toutes les images corrompues des segments défectueux ont été supprimées
- [ ] Capacité utilisable restante calculée et documentée
- [ ] Plan de prise de vue ajusté si la réduction de capacité affecte les opérations
- [ ] Rapport d'anomalie déposé avec le détail de la défaillance de segment

## Contingence
- Si le nombre de segments défectueux augmente rapidement (plusieurs nouvelles défaillances en peu de temps) :
  suspecter un verrouillage (latch-up) induit par les radiations ou une défaillance mémoire systématique. Passer la charge utile
  sur OFF : `PAYLOAD_SET_MODE(mode=0)` (func_id 26). Effectuer un cycle d'alimentation de la charge utile après 60 s.
  Si les défaillances persistent après le cycle d'alimentation, faire remonter à l'équipe d'ingénierie.
- Si plus de deux segments sont défectueux (> 2 sur 8, plus de 25 % de la capacité) : la mémoire de la charge utile est fortement
  dégradée. Évaluer si l'imageur peut encore produire des données scientifiques utiles. Envisager
  un fonctionnement à capacité réduite, avec transmission au sol immédiate après chaque acquisition.
- Si la déclaration d'un segment échoue (commande rejetée) : renvoyer la commande. Si elle est toujours rejetée,
  le segment est peut-être déjà déclaré ou l'indice est invalide. Vérifier l'indice du segment
  et réessayer. Si le problème persiste, faire remonter l'anomalie.
- Si les images stockées ne peuvent pas être récupérées dans un segment nouvellement défaillant : les images sont
  perdues. Consigner les identifiants des scènes perdues et se coordonner avec la planification de mission pour une nouvelle acquisition.
