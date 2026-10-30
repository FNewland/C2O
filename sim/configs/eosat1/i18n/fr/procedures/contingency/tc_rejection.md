# CTG-030 : Rejet de télécommande et échec de vérification
**Sous-système :** OBDH / TT&C
**Phase :** TOUTES (LEOP, COMMISSIONING, NOMINAL)
**Révision :** 1.0 --- nouvelle fiche (décision de l'auteur Q22 modifiée, 2026-10-30). Elle
remplace la fiche provisoire CTG-B02 « Anomalie du taux de rejet des TC » du livre d'opérations et repose
sur la vérification du service PUS 1 que le simulateur génère réellement.
**Approuvé par :** directeur des opérations de vol

**État d'entrée :** l'un des cas suivants
- un échec d'acceptation S1.2 ou un échec d'exécution S1.8 sur une télécommande que le
  sol croit valide ;
- `obdh.tc_rej_count` (0x0306) qui s'incrémente, ou l'événement `COMMAND_REJECTED` (0x030B) ;
- une télécommande **sans aucun** compte rendu S1 (dépassement du délai de vérification dans le journal
  des commandes du MCS).

## Objet
Trouver pourquoi des télécommandes sont refusées ou ne sont pas vérifiées, supprimer la cause et
rétablir un télécommandement propre.

**Ce que le simulateur rapporte.** Toute télécommande qui atteint le logiciel de
bord reçoit un compte rendu S1, et tout refus porte un code d'échec sur 16 bits et un
texte de motif (l'avis d'échec). Le même code est mémorisé dans
`obdh.last_tc_error_code` (0x0315), et un refus à bord lève aussi l'événement
`COMMAND_REJECTED` (0x030B), dont le texte nomme la commande, l'étape et le code.
Le MCS décode les codes à partir d'un vocabulaire unique partagé (`GET /api/failure-codes`).

| Compte rendu | Étape | Codes et signification |
|--------|-------|-------------------|
| S1.2 | acceptation | 0x0001 service inconnu, 0x0002 sous-type inconnu, 0x0003 paramètre ou longueur de données invalide, 0x0004 sous-système cible non alimenté, 0x0005 liaison montante indisponible, 0x0006 hors du sous-ensemble de commandes du chargeur d'amorçage |
| S1.4 | début d'exécution | requêtes S6 mémoire : adresse illégale, zone protégée en écriture, argument erroné, longueur au-delà de la limite |
| S1.8 | exécution | 0x0005 invalide dans le mode courant, 0x0007 non autorisée dans l'état courant, et les familles par sous-système : 0x0021-0x0028 charge utile, 0x0A01-0x0A08 étalonnage gyrométrique, 0x0A20-0x0A22 entrée en mode AOCS, 0x0B01-0x0B13 propulsion, 0x0C01-0x0C04 phase de mission |

Deux cas ne sont pas des rejets :
- **0x0005 à l'acceptation sans événement `COMMAND_REJECTED`.** La liaison montante n'avait pas
  de verrouillage de la voie de commande : le logiciel de bord n'a jamais vu la télécommande.
- **Aucun compte rendu S1.** La télécommande n'a pas atteint le satellite (problème de
  liaison), ou c'est une commande à achèvement différé dont le S1.7 n'arrive qu'à la fin
  de l'action (étalonnage gyrométrique, amorçage de l'application, poussée). Déterminer
  lequel avant de renvoyer quoi que ce soit.

## Prérequis
- [ ] Liaison bande S bidirectionnelle attendue (pendant un passage prévu)
- [ ] Journal des commandes du MCS disponible avec les comptes rendus S1 et les avis d'échec

## Déroulement

### Étape 1 --- Lire les compteurs de commandes et l'état de bord
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- données de servitude OBDH
**Verify:** `obdh.tc_rx_count` (0x0304) rapporté sous 20s --- consigner
**Verify:** `obdh.tc_acc_count` (0x0305) rapporté sous 20s --- consigner
**Verify:** `obdh.tc_rej_count` (0x0306) rapporté sous 20s --- consigner
**Verify:** `obdh.last_tc_error_code` (0x0315) rapporté sous 20s --- consigner
**Verify:** `obdh.sw_image` (0x0311) rapporté sous 20s --- 0 = chargeur d'amorçage, 1 = application
**Verify:** `obdh.mode` (0x0300) rapporté sous 20s --- 0 nominal, 1 sûr, 2 urgence
**Verify:** `eps.spacecraft_phase` (0x0129) rapporté sous 20s --- consigner
**Note:** Si cette requête elle-même reste sans réponse, le problème vient de la liaison, pas des
commandes : appliquer CTG-003 (Rétablissement après perte de liaison TTC), ou CTG-019 s'il n'y a
aucune télémesure.
**GO/NO-GO:** Compteurs et état de bord consignés

### Étape 2 --- Contrôler la chaîne montante
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- données de servitude TT&C
**Verify:** `ttc.carrier_lock` (0x0510) == 1 sous 20s
**Verify:** `ttc.frame_sync` (0x0512) == 1 sous 20s
**Verify:** `ttc.cmd_rx_count` (0x0513) rapporté sous 20s --- consigner
**Verify:** `ttc.beacon_mode` (0x0521) rapporté sous 20s --- consigner
**Note:** Une télécommande sans compte rendu S1 et sans variation de `ttc.cmd_rx_count`
n'a jamais atteint le satellite. L'absence de verrouillage de porteuse ou de synchronisation de trame signale un problème
de liaison : appliquer CTG-003 (Rétablissement après perte de liaison TTC), ou CTG-019 s'il n'y a pas
non plus de télémesure.
**GO/NO-GO:** Liaison montante verrouillée et le satellite reçoit les télécommandes

### Étape 3 --- Classer le rejet
**Note:** Lire l'avis d'échec de chaque télécommande rejetée dans le journal des commandes du MCS,
ou le texte de l'événement 0x030B. Utiliser le code et l'étape :
- **0x0006 à l'acceptation** avec `obdh.sw_image` (0x0311) = 0 : l'OBC est sur le
  chargeur d'amorçage, qui n'accepte que son sous-ensemble (S17.1, S9.1, HK balise S3,
  S20.1/3 et les fonctions de maintenance S8.1). Amorcer l'application :
  LEOP-001 étape 5 au premier contact, CTG-021 (Rétablissement du chargeur d'amorçage de l'OBC) après un
  redémarrage. Dans la fenêtre CRC de 10 s qui suit OBC_BOOT_APP, l'OBC est encore sur le
  chargeur d'amorçage : attendre d'abord son S1.7.
- **0x0004 à l'acceptation :** la ligne d'alimentation du sous-système cible est coupée. Mettre la
  ligne sous tension (EPS_POWER_ON) avant de renvoyer.
- **0x0003 à l'acceptation :** la télécommande a été mal construite (nombre, type ou
  longueur des arguments). La reconstruire avec le constructeur de commandes ; ne pas modifier l'hexadécimal brut.
- **0x0001 / 0x0002 à l'acceptation :** le service ou le sous-type n'est pas implémenté.
  Contrôler la commande dans le catalogue.
- **0x0005 / 0x0007 à l'exécution :** la commande est valide mais pas autorisée maintenant.
  Le texte du motif nomme l'état (par exemple un palier de TM refusé tant que
  `ttc.beacon_mode` (0x0521) = 1 --- désactiver d'abord le mode balise avec
  TTC_SET_BEACON_MODE, comme dans LEOP-001).
- **0x0Axx, 0x0Bxx, 0x0Cxx à l'exécution :** un verrou nommé. Étalonnage gyrométrique :
  CTG-029. Armement de la propulsion : lire `prop.arm_inhibit_mask` (0x0B15), NOM-013 ou
  CTG-028. Phase de mission : gardes de `SYS_SET_MISSION_PHASE`, LEOP-003 / COM-013.
- **Commandes à exécution différée :** une commande S11 libérée par le programme est vérifiée
  à son exécution, pas à son téléchargement. Un rejet à la libération suit les
  mêmes codes.
**GO/NO-GO:** Cause identifiée pour chaque télécommande rejetée

### Étape 4 --- Tester un télécommandement propre
**TC:** `CONNECTION_TEST` (Service 17, Subtype 1) --- test de liaison et de vérification
**Verify:** S1.1 d'acceptation et S1.7 de fin d'exécution reçus sous 10s
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27)
**Verify:** `obdh.tc_acc_count` (0x0305) incrémenté sous 20s
**Verify:** `obdh.tc_rej_count` (0x0306) inchangé depuis le test de liaison sous 20s
**GO/NO-GO:** Le satellite accepte et vérifie une télécommande connue comme correcte

### Étape 5 --- Renvoyer la télécommande corrigée
**Note:** Renvoyer une seule fois la télécommande rejetée, et seulement après avoir supprimé sa cause
(étape 3). Ne jamais répéter à l'identique une télécommande refusée : elle sera
refusée de nouveau pour la même raison, et des refus répétés d'une commande critique
masquent l'état réel.
**Verify:** S1.1 et S1.7 reçus pour la télécommande renvoyée (ni S1.2 ni S1.8)
**Verify:** `obdh.last_tc_error_code` (0x0315) inchangé par la télécommande renvoyée
**GO/NO-GO:** Télécommandement rétabli --- clore l'anomalie

## Conduite à tenir hors nominal
- **CONNECTION_TEST reste sans réponse.** La liaison montante ne fonctionne pas. Appliquer CTG-003.
- **Les rejets continuent avec un code que personne ne sait expliquer.** Arrêter de télécommander, consigner
  le code, le texte du motif et la commande, et remonter au directeur de vol.
  Ne pas essayer d'autres commandes pour contourner le problème.
- **Rejets après un redémarrage de l'OBC.** L'OBC redémarre sur le chargeur d'amorçage
  (`obdh.sw_image` 0x0311 = 0) : toute commande applicative est refusée avec 0x0006 jusqu'à
  un nouvel amorçage de l'application (EMG-003, CTG-021).
- **Défaillances liées à l'horloge.** Une commande à exécution différée programmée avec une horloge
  de bord fausse s'exécute au mauvais moment au lieu d'être rejetée. Si
  `obdh.time_ref` (0x0A13) = 0 ou si `obdh.time_since_sync_s` (0x0A14) est grand,
  resynchroniser l'horloge (NOM-008) avant de télécharger un nouveau programme.

## Postconditions
- [ ] Chaque télécommande rejetée classée avec son code et sa cause
- [ ] Cause supprimée et télécommande renvoyée une fois, ou reportée avec un motif
- [ ] `CONNECTION_TEST` vérifié (S1.1 + S1.7)
- [ ] Rapport d'anomalie ouvert pour tout code inexpliqué

## État de sortie
- Télécommandement rétabli avec une vérification S1 propre
- État de bord non modifié par cette fiche (elle n'envoie que des requêtes HK et un
  test de liaison)

**PROCÉDURE SUIVANTE :** reprendre l'activité ou le plan de passage interrompu.
