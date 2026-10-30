# NOM-011 : Changement de débit

**Catégorie :** Nominal
**Poste responsable :** TT&C
**Postes associés :** opérations charge utile
**Difficulté :** Débutant

## Objectif
Faire passer la télémesure descendante d'un échelon à l'autre de l'échelle des débits TM pendant un contact avec une station
sol. L'échelle est définie dans `subsystems/ttc.yaml tm_rate_tiers` et comporte
trois échelons :

| Palier | Débit | Modulation / codage | Rôle | Conditions |
|---|---|---|---|---|
| SAFE (ex-BEACON) | 1 000 bit/s | BPSK, conv(7,1/2)+RS | Voie de secours du chargeur d'amorçage et des contingences | Non commandable — atteint par `TTC_SET_BEACON_MODE` ou par le chargeur d'amorçage. « Balise » désigne désormais toujours l'émetteur UHF distinct à antenne fouet |
| LOW | 16 000 bit/s | BPSK, conv(7,1/2)+RS | **Opérations de routine** et repli du mode survie / de la FDIR | Aucune. Fonctionne antenne repliée et à toute élévation |
| HIGH | 128 000 bit/s | QPSK, RS(255,223) | Relecture de la télémesure différée et vidages d'images UNIQUEMENT | Antenne déployée **et** mode DOWNLINK **et** élévation >= 10 deg |

Le satellite reste en **LOW** pour les opérations de routine. HIGH n'est pas un « meilleur » débit à
laisser actif : il se mérite pour un vidage et se libère ensuite. Un palier dont les conditions ne sont pas
remplies est **rejeté** avec un échec d'exécution S1.8 (erreur 0x0007) — jamais plafonné
en silence —, de sorte qu'un changement de débit en échec indique exactement quelle condition fait défaut.

Cette procédure vérifie que la marge de liaison est suffisante avant de commander un changement de débit et
confirme que le nouveau taux d'erreur binaire (TEB) reste acceptable après la transition.

## Prérequis
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Verrouillage de la porteuse établi — `ttc.carrier_lock` (0x0510) = 1
- [ ] Contact avec la station sol en cours, avec un temps de contact restant suffisant (> 2 min)
- [ ] Modem de la station sol configuré pour le débit symbole et la modulation du palier visé
- [ ] Conditions de liaison actuelles évaluées et palier visé identifié

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| ttc.link_status | 0x0501 | 2 (LOCKED) |
| ttc.link_margin | 0x0503 | > 3.0 dB pour HIGH, > 0 dB au minimum |
| ttc.tm_data_rate | 0x0506 | Débit d'information actif (1000 / 16000 / 128000 bit/s) |
| ttc.tm_tier | 0x0539 | Indice du palier ACTIF (0=SAFE, 1=LOW, 2=HIGH) |
| ttc.tm_tier_cmd | 0x053A | Indice du palier COMMANDÉ — diffère de 0x0539 lorsqu'une condition refuse le palier |
| ttc.tm_symbol_rate | 0x053B | 16000 Bd en LOW (BPSK), 64000 Bd en HIGH (QPSK) |
| ttc.downlink_mode | 0x053C | 1 requis avant que HIGH soit accepté |
| ttc.antenna_deployed | 0x0520 | 1 requis avant que HIGH soit accepté |
| ttc.ber | 0x050C | < -5 (c.-à-d. TEB < 1e-5) |
| ttc.eb_n0 | 0x0519 | > 10.0 dB pour HIGH |
| ttc.rssi | 0x0502 | Puissance du signal |
| ttc.carrier_lock | 0x0510 | 1 (verrouillé) |
| ttc.bit_sync | 0x0511 | 1 (synchronisé) |
| ttc.frame_sync | 0x0512 | 1 (synchronisé) |
| ttc.contact_elevation | 0x050A | >= 10.0 deg requis pour HIGH |

## Commandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| TTC_SET_DOWNLINK_MODE | 8 | 1 | 79 | Entrer en mode DOWNLINK ou en sortir — condition de mode pour HIGH |
| TTC_SET_DATA_RATE | 8 | 1 | 65 | Sélectionner un palier de l'échelle (0=LOW, 1=HIGH ; 255=SAFE, chargeur d'amorçage uniquement) |

## Déroulement

### Étape 1 --- Évaluer les conditions de liaison actuelles
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- demander les données de servitude TT&C
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED)
**Verify:** `ttc.carrier_lock` (0x0510) = 1
**Verify:** `ttc.bit_sync` (0x0511) = 1
**Verify:** `ttc.tm_tier` (0x0539) --- consigner le palier ACTIF
**Verify:** `ttc.tm_tier_cmd` (0x053A) --- consigner le palier COMMANDÉ
**Verify:** `ttc.link_margin` (0x0503) --- consigner la valeur actuelle
**Verify:** `ttc.ber` (0x050C) --- consigner la valeur actuelle (attendue < -5)
**Verify:** `ttc.eb_n0` (0x0519) --- consigner la valeur actuelle
**Verify:** `ttc.contact_elevation` (0x050A) --- consigner l'élévation actuelle
**Note:** Si 0x0539 et 0x053A divergent déjà, une condition refuse le palier commandé.
Régler ce point avant de commander quoi que ce soit d'autre — l'échelle n'est pas « bloquée », elle obéit à
une règle, et 0x0521 / 0x0520 / 0x053C indiquent laquelle.
**Note:** Consigner toutes les valeurs comme référence avant changement.
**GO/NO-GO:** Liaison active et stable --- continuer.

### Étape 2 --- Vérifier les conditions et la marge pour le palier visé
**Action:** Pour un passage **vers le bas, à LOW (16 kbit/s)** : aucune condition ni marge minimale.
LOW est le débit des opérations de routine et il est toujours acceptable. Le mode DOWNLINK n'est alors pas requis ; la commande de palier (étape 4) s'applique directement.
**GO/NO-GO:** Palier visé LOW -> GO `STEP-4L` | NO-GO `STEP-2H`
**LABEL:** `STEP-2H`
**Action:** Pour un passage **vers le haut, à HIGH (128 kbit/s)**, les quatre conditions doivent être remplies :
- `ttc.antenna_deployed` (0x0520) = 1
- `ttc.contact_elevation` (0x050A) >= 10.0 deg **et** restant au-dessus de 10 deg pendant la
  durée prévue du vidage (une image de 4 Mio représente 328 s de contact en HIGH)
- `ttc.link_margin` (0x0503) > 3.0 dB et `ttc.eb_n0` (0x0519) > 10.0 dB
- Modem de la station sol reconfiguré pour 64 kBd QPSK RS(255,223)
**Note:** Le saut de palier de LOW à HIGH coûte 9,03 dB au bilan de liaison
(`-10*log10(128000/16000)`). La marge en HIGH est inférieure d'environ 10,5 dB à la marge en LOW pour la même
géométrie (saut de débit de 9,03 dB plus 1,5 dB de gain de codage) — voir `docs/LINK_BUDGET_AND_RATES.md` pour le tableau par station.
**GO/NO-GO:** Si une condition fait défaut ou si la marge <= 3.0 dB, NE PAS continuer. Rester en LOW ; envisager d'attendre une élévation plus haute avant de réessayer. -> GO `STEP-3` | NO-GO `STEP-END`

### Étape 3 --- Entrer en mode DOWNLINK (HIGH uniquement)
**LABEL:** `STEP-3`
**TC:** `TTC_SET_DOWNLINK_MODE(on=1)` (Service 8, Subtype 1, func_id 79)
**Verify:** `ttc.downlink_mode` (0x053C) = 1 sous 5 s
**Note:** Le mode DOWNLINK est l'acte délibéré qui fait d'un vidage massif une activité de passage
planifiée, et non un état dans lequel le satellite glisse par inadvertance. Il ne modifie pas à lui seul
le débit.
**GO/NO-GO:** Mode DOWNLINK confirmé --- continuer.

### Étape 4 --- Commander le changement de palier
**TC:** `TTC_SET_DATA_RATE(rate=1)` (Service 8, Subtype 1, func_id 65) --- sélectionner HIGH
**BRANCH:** `ttc.tm_tier == 2` -> GO `STEP-4V` | NO-GO `STEP-4L` (timeout 10 s)
**LABEL:** `STEP-4L`
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) --- sélectionner LOW
**LABEL:** `STEP-4V`
**Note:** Envoyer UNE SEULE des deux commandes ci-dessus. L'ancien codage est conservé à l'identique :
rate=0 a toujours signifié « le débit bas » et rate=1 « le débit haut ». Ils aboutissent désormais aux
échelons LOW et HIGH de l'échelle — des débits opérationnels utilisables — plutôt qu'aux deux
débits pratiqués par cette mission avant l'introduction de l'échelle.
**Verify:** `ttc.tm_data_rate` (0x0506) reflète le nouveau débit sous 10 s :
- HIGH : 128000 bit/s
- LOW : 16000 bit/s
**Verify:** `ttc.tm_tier` (0x0539) = `ttc.tm_tier_cmd` (0x053A) --- l'actif égale le
commandé, c.-à-d. qu'aucune condition n'a rétrogradé la liaison
**Verify:** `ttc.tm_symbol_rate` (0x053B) = 64000 Bd en HIGH, 16000 Bd en LOW
**Verify:** `ttc.carrier_lock` (0x0510) = 1 (maintenu pendant la transition)
**Verify:** `ttc.bit_sync` (0x0511) = 1 (réacquis sous 5 s)
**Verify:** `ttc.frame_sync` (0x0512) = 1 (réacquis sous 10 s)
**Note:** Si la commande est rejetée avec l'erreur 0x0007, le texte d'échec S1.8 nomme la
condition non remplie. Ne pas réessayer à l'aveugle.
**GO/NO-GO:** Palier changé, actif = commandé, synchronisation confirmée --- poursuivre
par le contrôle du TEB.

### Étape 5 --- Vérifier que le nouveau TEB est acceptable
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- demander les données de servitude TT&C après
avoir laissé 30 s au TEB pour se stabiliser
**Verify:** `ttc.ber` (0x050C) < -5 (TEB meilleur que 1e-5)
**Verify:** `ttc.link_margin` (0x0503) > 1.0 dB au nouveau palier
**Verify:** `ttc.eb_n0` (0x0519) > 8.0 dB
**Action:** Si TEB >= -5, revenir immédiatement à LOW (voir Contingence).
**GO/NO-GO:** TEB acceptable au nouveau palier --- changement de débit terminé.
**BRANCH:** `ttc.downlink_mode == 1` -> GO `STEP-6` | NO-GO `STEP-END` (timeout 5 s)

### Étape 6 --- Libérer HIGH après le vidage (HIGH uniquement)
**LABEL:** `STEP-6`
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) --- retour à LOW
**TC:** `TTC_SET_DOWNLINK_MODE(on=0)` (Service 8, Subtype 1, func_id 79)
**Verify:** `ttc.tm_data_rate` (0x0506) = 16000 bit/s sous 10 s
**Verify:** `ttc.downlink_mode` (0x053C) = 0
**Note:** HIGH se libère aussi délibérément qu'il a été pris. Quitter le mode DOWNLINK
n'efface pas le palier commandé ; le palier ACTIF retombe simplement à LOW, là où se font
les opérations de routine.

## Critères de vérification
**LABEL:** `STEP-END`
- [ ] `ttc.tm_data_rate` (0x0506) correspond au débit du palier commandé
- [ ] `ttc.tm_tier` (0x0539) = `ttc.tm_tier_cmd` (0x053A)
- [ ] `ttc.tm_symbol_rate` (0x053B) correspond à la modulation du palier
- [ ] `ttc.ber` (0x050C) < -5 au nouveau palier
- [ ] `ttc.carrier_lock` (0x0510) = 1 maintenu tout du long
- [ ] `ttc.link_margin` (0x0503) > 1.0 dB au nouveau palier
- [ ] Aucune perte de synchronisation trame détectée pendant ou après la transition
- [ ] Après un vidage : retour en LOW avec `ttc.downlink_mode` (0x053C) = 0

## Contingence
- Si la commande de palier est rejetée (S1.8, erreur 0x0007) : lire le texte d'échec. Il nomme
  la condition — mode balise verrouillé, antenne repliée ou mode DOWNLINK inactif (il n'existe pas de condition
  d'élévation à bord : la règle des 10 deg est un avertissement du MCS). Remplir la condition ou accepter LOW pour ce passage.
- Si `ttc.tm_tier` (0x0539) reste inférieur à `ttc.tm_tier_cmd` (0x053A) après acceptation
  de la commande : une condition rétrograde le palier ACTIF (mode balise verrouillé, antenne repliée ou
  mode DOWNLINK inactif — 0x0521 / 0x0520 / 0x053C). Le palier commandé est conservé et HIGH
  reprend dès que la condition est levée. Ne pas renvoyer la commande.
- Si le verrouillage de la porteuse est perdu pendant le changement : attendre 15 s la réacquisition automatique.
  En l'absence de rétablissement, commander le retour à LOW : `TTC_SET_DATA_RATE(rate=0)`. Toujours sans verrouillage :
  passer à CTG-014 (analyse d'une anomalie de TEB).
- Si le TEB dépasse -5 en HIGH : revenir immédiatement à LOW avec `TTC_SET_DATA_RATE(rate=0)`.
  Vérifier que le TEB revient à des niveaux acceptables. Consigner l'anomalie et recaler le bilan
  de liaison avant le prochain passage à haut débit.
- Si la synchronisation bit/trame n'est pas acquise sous 30 s : revenir à LOW. Si la synchronisation n'est toujours pas
  acquise, vérifier que le modem sol a été reconfiguré pour le nouveau débit symbole et la nouvelle
  modulation, puis vérifier la santé du transpondeur — suivre CTG-014.
- Si le contact touche à sa fin (< 1 min restante) : NE PAS tenter de changement de débit. Attendre
  le contact suivant.
