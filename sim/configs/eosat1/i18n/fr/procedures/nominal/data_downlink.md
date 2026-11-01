# NOM-003 : Transmission des données au sol
**Sous-système :** PAYLOAD / TTC
**Phase :** NOMINAL
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Transmettre au sol les images scientifiques et les données annexes enregistrées dans la mémoire de masse
de bord, vers la station sol pendant une fenêtre d'AOS. Cette procédure fait monter l'échelle des débits
TM jusqu'à HIGH, ouvre un transfert de grands volumes de données S13 sur un produit image CATALOGUÉ,
descend les segments un à un, clôt le transfert et ramène la liaison à
LOW avant le LOS.

> **Réécrite en 2026-08b.** La révision précédente commandait
> `PAYLOAD_SET_MODE(mode=3)` en l'appelant « PLAYBACK ». Il n'a jamais existé de
> mode PLAYBACK : la plage de `PAYLOAD_SET_MODE` était 0-2 (le mode 3 est désormais CALIBRATION,
> ajouté en phase 4) ; la commande était donc REJETÉE et tout le vidage
> dépendait d'une transition impossible. La véritable voie de transfert de masse est le
> **Service 13**, et depuis la phase 4 elle porte sur les octets réels de l'image, avec un
> CRC-32 que le sol peut contrôler.

## Prérequis
- [ ] NOM-001 Ouverture de passage achevée avec une déclaration tout GO
- [ ] Liaison TTC établie : `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Marge de liaison confirmée : `ttc.link_margin` (0x0503) > 3.0 dB
- [ ] Charge utile en mode STANDBY : `payload.mode` (0x0600) = 1
- [ ] La mémoire de bord contient des PRODUITS : `payload.product_count` (0x0648) > 0.
      `payload.store_used` (0x0604) n'est pas le bon critère — la mémoire est livrée remplie à environ 20 %
      de données de remplissage hors produits ; elle est donc > 0 % sur un satellite vide.
- [ ] Enregistreur de données de la station sol armé et en réception

## Déroulement

### Étape 1 --- Confirmer la qualité de la liaison
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- demander les données de servitude TT&C
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) sous 5 s
**Verify:** page TT&C (sol) : `ttc.rssi` (0x0502) > -126 dBm sous 5 s
**Verify:** page TT&C (sol) : `ttc.link_margin` (0x0503) > 3.0 dB sous 5 s
**GO/NO-GO:** Si la marge de liaison <= 3.0 dB, se mettre en attente (HOLD). Si la marge ne s'améliore pas sous
30 s, tenter `TTC_SWITCH_REDUNDANT`. Si elle reste insuffisante, reporter le vidage.

### Étape 2 --- Consigner l'état initial de la mémoire
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- demander les données de servitude de la charge utile
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) sous 5 s
**Note:** Consigner `payload.product_mb` (0x0647) sous le nom V0 et `payload.product_count`
(0x0648) sous le nom N0. Ces paramètres comptent les produits CATALOGUÉS ; `payload.store_used` (0x0604)
inclut aussi le remplissage initial de la mémoire et varie pour des raisons sans rapport avec les images.
**TC:** `PAYLOAD_GET_IMAGE_CATALOG` (Service 8, Subtype 1, func_id 32) — catalogue de bord
**Note:** Depuis la phase 4, la réponse est un rapport de catalogue TM(8,2) : un en-tête
shown(u16) held(u16) product_mb_x100(u32) free_mb_x100(u32), puis un enregistrement de 20 octets
par produit — scene_id(u16), lat_x1e4(i32), lon_x1e4(i32), size_kb(u32),
lines(u16), quality_pct(u8), status(u8), flags(u8), segment(u8). Y choisir le
`scene_id` à transmettre. `status` 0 = OK, 1 = PARTIAL, 2 = CORRUPT ;
`flags` bit 0 = la bande a été acquise avec un jeu FINE dégradé (3 roues).

### Étape 3 --- Monter la liaison en HIGH
**TC:** `TTC_SET_DOWNLINK_MODE(on=1)` (Service 8, Subtype 1, func_id 79) --- entrer en
mode DOWNLINK/vidage, condition d'accès au palier HIGH
**TC:** `TTC_SET_DATA_RATE(rate=1)` (Service 8, Subtype 1, func_id 65) --- monter l'échelle
des débits TM à HIGH (128 kbit/s QPSK RS(255,223)). Les conditions BORD sont exactement :
antenne déployée + mode DOWNLINK actif + verrou du mode balise levé (chaque condition non remplie
donne un S1.8 avec l'erreur 0x0007 qui la nomme). Il n'y a PAS de condition d'élévation à bord
(2026-08c) : la règle des 10 deg pour HIGH est une politique SOL de confirmation explicite --- le MCS
avertit, d'après sa propre géométrie de contact, lorsque HIGH est commandé sous 10 deg, et
l'opérateur doit confirmer explicitement en passant outre l'avertissement ; le planificateur programme
les vidages HIGH au-dessus
**Verify:** `ttc.tm_data_rate` (0x0506) = 128000 bit/s et `ttc.tm_tier` (0x0539) =
`ttc.tm_tier_cmd` (0x053A) = 2 sous 10 s
**Note:** Ordre pratiqué en vol (2026-08c) : contrôle de liaison HK(6) -> catalogue -> mode DOWNLINK
+ HIGH (avec la confirmation sol ci-dessus) -> ouverture S13.1 (blocs + CRC)
-> segments -> état -> fin -> retour à LOW. Ce sont les étapes 1-6 de cette fiche.
**Note:** NE PAS commander de mode de charge utile ici. Il n'existe pas de mode PLAYBACK, et
`PAYLOAD_SET_MODE(mode=3)` correspond à CALIBRATION depuis la phase 4 — l'envoyer lancerait
un étalonnage en plein passage de vidage. La charge utile reste en STANDBY pendant
toute la session ; le S13 lit dans la mémoire, et non selon un mode de l'instrument.
**GO/NO-GO:** Palier HIGH actif, mode DOWNLINK actif, charge utile en STANDBY

### Étape 3a --- Ouvrir le transfert S13
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- données de servitude TT&C
**TC:** `S13_CREATE_TRANSFER(scene_id=N, size_mb=0)` (Service 13, Subtype 1) --- ouvrir un
transfert de grands volumes de données pour la scène choisie dans le catalogue à l'étape 2
**Note:** La réponse TM(13,2) porte l'identifiant du transfert suivi de
`total_blocks(u32) + crc32(u32)`. Consigner LES DEUX : le nombre de blocs dimensionne la session
et le CRC-32 est la valeur à laquelle le sol compare le produit réassemblé.
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- données de servitude de la charge utile
**Verify:** `payload.transfer_active == 1` (0x062D, timeout 15 s)
**GO/NO-GO:** Transfert ouvert, nombre de blocs et CRC-32 consignés

### Étape 4 --- Descendre les segments et suivre l'avancement
**TC:** `S13_DOWNLOAD_SEGMENT(transfer_id=T, segment_num=K)` (Service 13, Subtype 3) --- demander
le bloc suivant ; répéter pour K = 0 .. total_blocks-1
**TC:** `S13_REPORT_STATUS(transfer_id=T)` (Service 13, Subtype 9) --- état du transfert, toutes les 60 s
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- interroger toutes les 60 s
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- interroger toutes les 60 s
**Verify:** `payload.transfer_progress` (0x062E) croissant d'une interrogation à l'autre
**Verify:** `ttc.link_status == 2` (0x0501, timeout 60 s) --- LOCKED maintenu
**Verify:** page TT&C (sol) : `ttc.link_margin` (0x0503) > 2.0 dB pendant toute la session
**Verify:** page TT&C (sol) : `ttc.rssi` (0x0502) > -126 dBm pendant toute la session
**Note:** Depuis la phase 4, le moteur de transfert de bord s'écoule au débit
d'information ACTIF `ttc.tm_data_rate` (0x0506) et se BLOQUE lorsque `ttc.link_status`
(0x0501) quitte LOCKED, puis reprend à son retour. Un
`payload.transfer_progress` figé signifie donc que la liaison descendante est coupée — le plus souvent
à cause du PA, puisque `ttc.tx_active` (0x0525) est désormais une vraie condition. Auparavant, il vidait un
compteur à un débit codé en dur de 10 Mbit/s, indépendamment du contact, du PA ou de l'échelle ; ainsi
un « vidage » pouvait s'achever en éclipse, émetteur éteint.
**Note:** Si `ttc.link_margin` descend sous 2.0 dB, cesser de demander des segments ;
la clôture de session de l'étape 6 s'applique alors, et le transfert pourra reprendre à l'AOS suivant avec le même
`transfer_id`.
**BRANCH:** `ttc.link_margin < 2.0` -> GO `STEP-6` | NO-GO `STEP-5` (timeout 5 s)

### Étape 5a --- Vérifier la somme de contrôle du produit
**LABEL:** `STEP-5`
**Action:** Calculer au sol le CRC-32 du produit réassemblé et le comparer à la
valeur indiquée par la TM(13,2) à l'étape 3a.
**Note:** C'est un vrai contrôle, pas une formalité. Un produit soumis à l'injection `image_corrupt`
fournit des octets ENDOMMAGÉS face à la somme de contrôle SAINE calculée par l'instrument
à l'acquisition ; une image corrompue échoue donc réellement à la vérification au lieu
d'être identique octet pour octet à une image saine.
**GO/NO-GO:** CHECKSUM OK --- le produit a été transmis intact

### Étape 5 --- Vérifier la réception au sol
**Action:** Confirmer auprès de l'opérateur de la station sol que les trames sont reçues
et archivées sans erreur.
**Verify:** Taux d'erreur trame de la station sol < 1.0E-6
**Note:** Si la station sol signale une perte de synchronisation trame, faire une pause et réévaluer
les conditions de liaison avant de continuer.

### Étape 6 --- Clore la session de vidage et libérer le palier HIGH
**LABEL:** `STEP-6`
**TC:** `S13_END_TRANSFER(transfer_id=T)` (Service 13, Subtype 5) --- clore la session
**Note:** Clore une session ENTIÈREMENT vidée SUPPRIME le produit et libère sa
place en mémoire ; une session partielle laisse le produit à bord pour le passage suivant.
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- données de servitude TT&C
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- données de servitude de la charge utile
**Verify:** `payload.transfer_active == 0` (0x062D, timeout 15 s)
**Verify:** `payload.mode == 1` (0x0600, timeout 15 s) --- STANDBY tout du long
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) --- retour à LOW
**TC:** `TTC_SET_DOWNLINK_MODE(on=0)` (Service 8, Subtype 1, func_id 79)
**Verify:** `ttc.tm_data_rate` (0x0506) = 16000 bit/s sous 10 s
**Verify:** `ttc.downlink_mode` (0x053C) = 0
**Note:** HIGH se libère aussi délibérément qu'il a été pris. Laisser le satellite
commandé en HIGH avec le mode DOWNLINK verrouillé, c'est laisser une porte ouverte — les opérations
de routine se font en LOW.
**Note:** Consigner la valeur finale de `payload.product_mb` (0x0647) sous le nom Vf et
`payload.product_count` (0x0648) sous le nom Nf.
**Note:** Volume de données libéré = V0 - Vf Mo, produits libérés = N0 - Nf.

### Étape 7 --- Bilan après vidage
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- état final TT&C
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- état final de la charge utile
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED)
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY confirmé)
**Consigner :** Inscrire dans le journal de passage la durée du vidage, le volume de données transféré, la marge de liaison moyenne
et toute interruption de synchronisation trame.

## Conduite à tenir hors nominal
- Si `S13_CREATE_TRANSFER` est refusée : le `scene_id` ne figure pas au catalogue.
  Relancer `PAYLOAD_GET_IMAGE_CATALOG` (func 32) et choisir une scène qui y figure.
- Si `payload.transfer_progress` (0x062E) est figé : la liaison descendante
  n'émet pas. Vérifier `ttc.tx_active` (0x0525) et, s'il vaut 0,
  `ttc.tx_gate_status` (0x052B) pour identifier l'autorisation manquante — bit0 PA,
  bit1 ligne `ttc_tx`, bit2 station en visibilité, bit6 antenne. Le transfert reprend
  de lui-même dès que la liaison revient.
- Si le produit réassemblé échoue au contrôle CRC-32 : le produit est corrompu à bord,
  et non pendant la transmission — la somme de contrôle a été calculée à l'acquisition. Consigner le
  `scene_id`, NE PAS envoyer `S13_END_TRANSFER` (qui le supprimerait), et déclarer une
  anomalie charge utile.
- Si `ttc.link_status` tombe à 0 (NO_LINK) ou 1 (ACQUIRING) pendant le transfert : tenter
  `TTC_SWITCH_REDUNDANT`. Si la liaison est rétablie, reprendre au point courant.
  Sinon, attendre et réessayer à l'AOS suivant.
- Si `ttc.link_margin` < 2.0 dB de façon prolongée : redescendre l'échelle jusqu'à LOW par
  `TTC_SET_DATA_RATE(rate=0)` (func_id 65) et quitter le mode DOWNLINK avec
  `TTC_SET_DOWNLINK_MODE(on=0)` (func_id 79). En LOW, le reste du produit exige
  huit fois plus de temps de contact ; replanifier donc le vidage sur un passage plus élevé plutôt que
  de l'égrener à 16 kbit/s.
- Si le LOS approche (< 2 min restantes) : clore proprement le vidage. Les données
  restantes seront programmées sur le prochain passage disponible.

## Postconditions
- [ ] Charge utile revenue en mode STANDBY
- [ ] Volume catalogué réduit (Vf < V0)
- [ ] La station sol confirme l'archivage des données sans corruption
- [ ] Liaison TTC maintenue tout du long (ou rétablie proprement)
- [ ] Journal de passage mis à jour avec la synthèse de la session de vidage
