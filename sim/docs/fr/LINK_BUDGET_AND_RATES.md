# Bilan de liaison d'EOSAT-1 et échelle de débits TM

**Référence du document :** EOSAT1-OPS-LINK-001
**Édition :** 2.0 — 2026-08-12 (édition 1.0, 2026-07-29)

> **Ce qui a changé dans l'édition 2.0.** EOSAT-1 possède deux émetteurs, et non un seul.
> Le §9 est nouveau : il décrit l'émetteur de balise UHF du chargeur d'amorçage, son bilan
> de liaison, et ce qu'il conditionne ou non. Le §4 reçoit une remarque indiquant que la PIRE
> en bande S est désormais déduite de la puissance commandée du PA au lieu d'être une
> constante, de sorte que `TTC_SET_TX_POWER` fait évoluer le tableau des marges. La séquence de reprise du §6.3
> reçoit l'étape `TTC_PA_ON` qui lui avait toujours manqué.

**S'applique à :** `configs/eosat1/subsystems/ttc.yaml` (`tm_rate_tiers`), et à tout ce qui
en dépend en aval : le simulateur, la chaîne RF, le planificateur de mission, la console de
contrôle de mission, les procédures de vol et le manuel d'exploitation.

---

## 1. Pourquoi un satellite a plus d'un débit descendant

L'étudiant qui découvre une liaison satellite pose généralement la mauvaise question :
*quel est le débit ?* Les missions réelles n'en ont pas un seul. Elles disposent d'un petit ensemble fixe
et programmable de débits, et l'ingénierie intéressante réside dans **la raison pour laquelle il y en a plus
d'un et dans ce qui décide lequel est utilisé**.

Trois contraintes distinctes imposent cet éventail.

**L'acquisition réclame le débit le plus bas que l'on puisse supporter.** Juste après la séparation, personne
ne connaît la position du satellite à mieux que quelques kilomètres près, l'antenne peut être repliée,
l'attitude n'est pas contrôlée et l'émetteur fonctionne peut-être avec ce qu'il reste d'énergie dans la
batterie. Chaque bit par seconde demandé vous coûte `10·log₁₀(R)` décibels de
marge de liaison : le débit qui vous apporte votre premier paquet est donc le plus lent qui puisse
encore transporter quelque chose qui vaille la peine d'être lu.

**Les opérations courantes réclament le débit le plus bas qui suive le rythme.** Il s'agit d'une exigence de *débit*,
et non de marge, et elle relève de l'arithmétique plutôt que du jugement : le satellite
produit des données de servitude à un certain nombre de bits par seconde, et si la liaison descendante est
plus lente, l'arriéré croît sans limite. Un débit inférieur au débit de production n'est pas
« dégradé » — il est défaillant.

**La transmission en masse réclame le débit le plus élevé que l'on puisse justifier.** L'imagerie est volumineuse et le temps
de contact est rare. Mais le débit maximal coûte de la puissance, de la chaleur, de la largeur de bande occupée et de la configuration
de station sol : il n'est donc pas laissé en service en permanence. Il est *demandé*, pour une activité planifiée,
sur un passage choisi parce que sa géométrie le permet.

EOSAT-1 vole donc avec une échelle à trois échelons. Chaque échelon répond à l'une de ces trois
contraintes, et rien à bord, dans le planificateur ou sur la console ne détient sa propre
copie des valeurs — tous lisent `configs/eosat1/subsystems/ttc.yaml`.

---

## 2. L'échelle telle que livrée

| N° | Palier | Débit utile | Modulation | Codage | Gain de codage | Débit symbole | Largeur de bande occupée | Code de commande |
|---|------|------------------|------------|--------|-------------|-------------|-------------|--------------|
| 0 | `SAFE` | 1000 bit/s | BPSK | conv(7,½) + RS(255,223) | 7,5 dB | 1 kBd | 3,1 kHz | `0xFF` (non commandable) |
| 1 | `LOW` | 16 000 bit/s | BPSK | conv(7,½) + RS(255,223) | 7,5 dB | 16 kBd | 49,8 kHz | `0x00` |
| 2 | `HIGH` | 128 000 bit/s | QPSK | RS(255,223) | 6,0 dB | 64 kBd | 99,5 kHz | `0x01` |

La liaison montante de télécommande est **fixée à 4000 bit/s** et ne fait délibérément *pas* partie de l'échelle
(`tc_uplink_rate_bps`). Augmenter le débit descendant n'augmente jamais le débit montant. C'est plus important
qu'il n'y paraît : cette clé prenait autrefois par défaut le débit TM maximal, si bien qu'une modification de la liaison descendante
aurait modifié sans avertissement le délai d'accrochage de la liaison montante.

### 2.1 SAFE — 1 kbit/s, la ligne de vie (anciennement BEACON, 2026-08c)

`SAFE` (l'échelon autrefois nommé BEACON — « beacon » désigne désormais toujours l'émetteur UHF
à antenne fouet) existe pour répondre à une seule question — *l'OBC est-il vivant ?* — dans les pires conditions
que la mission connaîtra jamais. Il transporte le SID 11 : sept paramètres, un paquet de 29 octets, toutes les
30 secondes. Cela représente **7,7 bit/s de charge moyenne** : 1 kbit/s le transporte donc avec une réserve de 130×
et une salve d'émission de 0,23 s. Sa largeur de bande occupée, 3,1 kHz, est le signal le plus étroit
que le satellite puisse produire, ce qui est exactement ce que l'on souhaite lorsque la station sol
balaie ±40 kHz d'incertitude Doppler à la recherche d'une porteuse.

**Cet échelon n'est pas l'émetteur de balise.** C'est la chaîne en bande S fonctionnant à bas débit, et
elle meurt avec le PA bande S comme tout le reste de cette chaîne. La radio UHF qui transporte le
SID 11 lorsque la chaîne bande S est hors service est un boîtier distinct — voir le §9, et le §9.5 pour les trois
choses différentes que cette mission appelle « balise » (*beacon*).

On ne peut l'atteindre **qu'**à partir du chargeur d'amorçage ou du mode balise (`TTC_SET_BEACON_MODE`,
S8 fonction 70). `TTC_SET_DATA_RATE` ne le sélectionnera pas. Cette restriction est délibérée : un
opérateur capable de commander 1 kbit/s en opérations nominales commanderait un débit dont le
satellite ne peut pas vivre (§2.2), et il s'en apercevrait lentement, par un arriéré
croissant, plutôt qu'immédiatement, par une commande rejetée.

### 2.2 LOW — 16 kbit/s, là où le satellite vit réellement

**C'est le débit des opérations courantes.** C'est aussi le débit du mode survie, le repli FDIR
et le débit qui fonctionne avec l'antenne repliée. Ce n'est ni un mode dégradé ni
une situation de contingence ; un EOSAT-1 en bonne santé, au milieu d'une journée d'exploitation nominale, émet à
16 kbit/s.

16 000 bit/s est un débit calculé, et non choisi. Le fichier livré `telemetry/hk_structures.yaml` définit les
six structures de servitude périodiques :

| SID | Nom | Paramètres | Paquet | Période | Débit |
|-----|------|-----------:|-------:|---------:|-----:|
| 1 | EPS | 52 | 105 o | 1,0 s | 840,0 bit/s |
| 2 | AOCS | 75 | 152 o | 4,0 s | 304,0 bit/s |
| 3 | TCS | 17 | 49 o | 60,0 s | 6,5 bit/s |
| 4 | Plateforme | 36 | 88 o | 8,0 s | 88,0 bit/s |
| 5 | Charge utile | 29 | 75 o | 8,0 s | 75,0 bit/s |
| 6 | TT&C | 24 | 65 o | 8,0 s | 65,0 bit/s |
| | **Total** | **233** | | | **1378,5 bit/s** |

Multipliez par le facteur RS(255,223) (×255/223) et par celui de la trame de transfert TM de 1115/1107 octets, et le
flux de servitude coûte **1588 bit/s de canal** (1587,7 bit/s ; il valait 1557 bit/s avant les ajouts de la phase G à 2026-08e, et 1699,5 bit/s avant le retrait, le 2026-08-20, de tous les paramètres dérivés au sol et réservés à l'instructeur des SID HK).

Deux conclusions en découlent immédiatement, et elles constituent tout l'argument en faveur de cet échelon.

* **1000 bit/s est inférieur à 1588 bit/s.** L'ancien « débit bas » de la mission n'aurait jamais pu transmettre
  la servitude en temps réel. L'arriéré croissait de façon monotone et des paquets étaient perdus. Ce
  n'est ni une préférence ni une affaire de goût ; c'est un défaut quantifié, et c'est pourquoi
  1 kbit/s est désormais qualifié de débit de balise et verrouillé derrière le mode balise.
* **16 000 bit/s l'absorbe avec un taux d'occupation de 9,9 %** et permet encore de relire environ **0,82 orbite de
  servitude enregistrée** en un seul passage de 514 secondes. C'est la plus petite valeur ronde
  pour laquelle un satellite en mode survie ne perd pas de données et ne prend pas de retard sur une orbite.

16 kbit/s est aussi le débit TM bas en bande S de Sentinel-1 (Copernicus), et il se situe entre les
paliers de 9,6 et 19,2 kbit/s du GomSpace AX2150 — c'est donc un débit qu'une vraie radio 6U proposerait.

### 2.3 HIGH — 128 kbit/s, à mériter pour chaque vidage

`HIGH` transporte la relecture de télémesure différée et les vidages d'images, et rien d'autre. Il est conditionné
de trois façons, et chaque verrou est appliqué par **rejet**, jamais par écrêtage silencieux :

| Verrou | Clé de configuration | Télémesure | Motif du rejet |
|------|-----------|-----------|------------------|
| Antenne déployée | `requires_antenna: true` | `ttc.antenna_deployed` (0x0520) | Une antenne patch repliée a un diagramme de rayonnement inadapté à un vidage soutenu à haut débit |
| Mode DOWNLINK actif | `requires_downlink_mode: true` | `ttc.downlink_mode` (0x053C) | La transmission en masse doit être une activité délibérée et planifiée — voir le §5 |
| Élévation ≥ 10° — **politique SOL, pas de bord** | `min_elevation_deg: 10.0` (lue par le planificateur et le MCS uniquement) | géométrie du contact sol (0x050A affiché pour information) | La vitesse de poursuite, la dérive Doppler et les trajets multiples font d'un vidage QPSK à 64 kBd à faible élévation un pari risqué — appliqué par la planification et par une retenue d'armement du MCS |

Une commande qui échoue à un verrou renvoie un échec d'exécution S1.8 avec l'erreur `0x0007` et un
message nommant le verrou, p. ex. *« HIGH (128000 bps) requires DOWNLINK/dump mode »*.
Un code de palier inconnu renvoie `0x0003`. Rien n'est substitué discrètement. Un écrêtage apprendrait
à l'opérateur que le satellite l'ignore ; un rejet motivé lui apprend la
règle.

128 000 bit/s est le débit TM bande S *nominal* de Sentinel-1 et le haut de la gamme des radios TT&C
CubeSat du commerce (EnduroSat 125 kbit/s, GomSpace AX2150 96 kbit/s) : toute l'échelle est donc
accessible avec une seule radio TT&C. Aucun émetteur haut débit séparé n'est sous-entendu — ce qui est
le bon scénario matériel pour un 6U.

### 2.4 Pourquoi les paliers valent 16× et 8×

1 kbit/s × 2⁰, 2⁴, 2⁷. Les paliers valent **+12,04 dB** et **+9,03 dB**, soit exactement le terme
`−10·log₁₀(R)` du bilan de liaison. Un étudiant peut lire l'échelle directement dans le
bilan : *un changement de palier vous coûte de 9 à 12 dB de marge, et c'est la seule chose que le débit fait
à une liaison.*

---

## 3. Modulation et codage : deux leviers indépendants

La modulation et le codage changent avec le palier, et pour des raisons différentes de celle
qui fait changer le débit. Il vaut la peine de les distinguer explicitement, car la confusion entre débit,
modulation et largeur de bande est le malentendu le plus fréquent dans un premier cours de bilan
de liaison.

**Le débit fixe la largeur de bande de bruit.** `Eb/N₀ = C/N₀ − 10·log₁₀(R_b)`. Doubler le
débit utile coûte 3 dB, point final, quelle que soit la façon dont on le module.

**Le codage fixe le Eb/N₀ nécessaire.** Une BPSK ou une QPSK non codée exige 9,6 dB pour un TEB de 1e-5.
RS(255,223) apporte environ 6,0 dB ; sa concaténation avec un code convolutif de rendement ½ et K=7 apporte
environ 7,5 dB. Les deux échelons inférieurs utilisent conv+RS parce que ce sont eux qui doivent fonctionner
quand tout le reste a lâché, et parce qu'à 1–16 kbit/s le décodage de Viterbi est peu coûteux.
L'échelon supérieur utilise RS seul : il n'a pas besoin du 1,5 dB supplémentaire (§4), et le code
convolutif doublerait son débit symbole, donc sa largeur de bande occupée.

**La modulation fixe le débit symbole, donc la largeur de bande — pas le débit binaire.** C'est
le point que les étudiants comprennent le plus souvent à l'envers. La QPSK transporte deux bits par symbole :
128 kbit/s d'*information* représentent donc 64 kBd de *symboles*. Elle ne rend pas la liaison plus rapide ; elle
fait tenir la même information dans la moitié du spectre :

| Palier | Bits/symbole | Débit symbole | Largeur de bande occupée (SRRC α=0,35) | % du canal mission de 5 MHz |
|------|------------:|------------:|--------------------------:|-------------------------------:|
| SAFE | 1 (BPSK) | 1 kBd | 3,1 kHz | 0,1 % |
| LOW | 1 (BPSK) | 16 kBd | 49,8 kHz | 1,0 % |
| HIGH | 2 (QPSK) | 64 kBd | 99,5 kHz | 2,0 % |

La QPSK sur l'échelon supérieur est un choix pédagogique délibéré autant qu'un choix d'ingénierie. La
liaison n'est pas limitée en puissance (§4) et 5 MHz de canal ne sont pas une ressource rare : aucun des deux leviers n'est
donc imposé. La QPSK a été choisie parce que le changement de palier devient *visible sur la radio* — la
constellation, le diagramme de l'œil et le spectre changent tous lorsqu'on le commande, et un
étudiant peut constater par lui-même que débit et modulation sont indépendants.

Le contre-argument est réel et mérite d'être présenté aux étudiants : les radios TT&C de vol à ce débit
(AX2150, EnduroSat) utilisent une GMSK ou une GFSK à enveloppe constante, et un PA saturé préférerait
l'OQPSK. Si cette fidélité compte davantage que le changement visible de constellation, réglez
`modulation: OQPSK` sur le palier HIGH dans `ttc.yaml` — rien d'autre n'a besoin de changer.

---

## 4. Le tableau des marges

Produit par `python tools/link_budget_ladder.py`, qui pilote
`TTCBasicModel.link_margin_for` — l'objet modèle même que fait voler le simulateur — avec la
configuration livrée. L'outil et le modèle de vol ne peuvent pas diverger.

**Hypothèses** (toutes tirées de `configs/eosat1/subsystems/ttc.yaml`) : orbite à 513 km (altitude moyenne
conforme au TLE, décision d'époque et d'altitude 2026-08), liaison descendante à 2200 MHz,
PIRE de 10 dBW **au réglage NOMINAL du PA de 2 W** + antenne patch bord de 3 dBi = 13 dBW
(voir le §4.2 — la PIRE n'est plus une constante), affaiblissement atmosphérique de 0,5 dB au zénith
pondéré par cosec(ε) en dessous de 30°, polarisation 0,3 dB, implémentation 2,0 dB, G/T dégradé de
−1,5 dB en dessous de 10° et de −0,5 dB en dessous de 30°, Eb/N₀ requis de 9,6 dB sans codage diminué du
gain de codage du palier.

**Géométrie.** Distance oblique `d(ε) = R⊕·[√((r/R⊕)² − cos²ε) − sin ε]` :

| Élévation | Distance oblique | Affaiblissement en espace libre à 2200 MHz |
|-----------|------------:|-----------------:|
| 5° | 2111,7 km | 165,79 dB |
| 10° | 1726,8 km | 164,04 dB |
| 30° | 931,3 km | 158,68 dB |
| 90° | 513,0 km | 153,50 dB |

**Marge de liaison (dB) à 5° d'élévation — la pire géométrie que voie une station :**

| Station | G/T (dB/K) | SAFE | LOW | HIGH |
|---------|-----------:|-------:|----:|-----:|
| Inuvik | 22,0 | 59,0 | 47,0 | 36,5 |
| Svalbard | 21,5 | 58,5 | 46,5 | 36,0 |
| Iqaluit | 20,0 | 57,0 | 45,0 | 34,5 |
| O'Higgins | 20,0 | 57,0 | 45,0 | 34,5 |
| Troll | 18,5 | 55,5 | 43,5 | **33,0** |

**Marge de liaison (dB) à 10° d'élévation — là où s'ouvre le verrou du palier HIGH :**

| Station | SAFE | LOW | HIGH |
|---------|-------:|----:|-----:|
| Inuvik | 63,2 | 51,2 | 40,6 |
| Svalbard | 62,7 | 50,7 | 40,1 |
| Iqaluit | 61,2 | 49,2 | 38,6 |
| O'Higgins | 61,2 | 49,2 | 38,6 |
| Troll | 59,7 | 47,7 | 37,1 |

**Marge de liaison (dB) au zénith :**

| Station | SAFE | LOW | HIGH |
|---------|-------:|----:|-----:|
| Inuvik | 75,2 | 63,2 | 52,6 |
| Svalbard | 74,7 | 62,7 | 52,1 |
| Iqaluit | 73,2 | 61,2 | 50,6 |
| O'Higgins | 73,2 | 61,2 | 50,6 |
| Troll | 71,7 | 59,7 | 49,1 |

### 4.1 Lecture du tableau

**Chaque échelon boucle partout, avec des dizaines de décibels d'avance.** Le pire cas de
toute la matrice est HIGH à Troll à 5°, et il dispose encore de 33,0 dB. À 513 km d'une
parabole polaire professionnelle, une liaison en bande S de 2 W n'est pas limitée en puissance. Quiconque a
appris qu'un débit se choisit en cherchant le point où la marge s'épuise devrait s'arrêter et
examiner ce tableau, car c'est la situation réelle la plus courante, et elle enseigne une
leçon plus difficile : **le débit se choisit selon la politique d'exploitation, la largeur de bande, la puissance, le coût thermique et la planification
des passages, et non selon une falaise de puissance.**

C'est pourquoi le palier HIGH est conditionné par le mode à bord, la règle des 10° d'élévation
étant appliquée au SOL (planificateur + retenue du MCS) plutôt que par un seuil de marge.
Modéliser une fausse falaise à 10° aurait été plus facile à expliquer, et moins honnête.

**Les échelons sont séparés exactement de ce que prédit le bilan.** Lisez n'importe quelle ligne :

| Palier | Rapport de débits | Terme de débit | Changement de codage | Prédit | Mesuré (Iqaluit à 5°) |
|------|-----------:|----------:|---------------|----------:|----------------------:|
| SAFE → LOW | 16× | −12,04 dB | aucun | −12,04 dB | 57,0 − 45,0 = **−12,0 dB** |
| LOW → HIGH | 8× | −9,03 dB | conv+RS 7,5 → RS 6,0 dB | −10,53 dB | 45,0 − 34,5 = **−10,5 dB** |

Si un jeu de mesures ne montre pas ces deux paliers, le défaut est dans le modèle, et non dans la
liaison. C'est précisément cette vérification que l'étape 2a de COM-006 a pour objet d'effectuer.

**L'élévation vaut plus qu'on ne le croirait.** Passer de 5° à 10° rapporte environ 4,3 dB
— 1,85 dB d'affaiblissement en espace libre, 1,43 dB d'atmosphère et 1,0 dB de dégradation du G/T
qui disparaît. Aller jusqu'au zénith rapporte 16,6 dB. C'est pourquoi un opérateur attend un meilleur passage plutôt
qu'un meilleur débit.

### 4.2 Le tableau des marges est établi pour un seul réglage du PA

Toutes les valeurs du §4 correspondent au point de fonctionnement **NOMINAL**, 2,0 W RF. Depuis 2026-08b, la
PIRE est déduite de la puissance commandée du PA au lieu d'être une constante de configuration fixe :

```
EIRP(P) = eirp_dbw + 10·log₁₀(P / pa_ref_power_w)      pa_ref_power_w = 2.0 W
```

| Niveau `TTC_SET_TX_POWER` | Sortie RF | ΔPIRE | Échelon LOW à Iqaluit, 5° |
|---|---:|---:|---:|
| 0 `LOW` | 1,0 W | −3,01 dB | 42,0 dB |
| 1 `NOMINAL` | 2,0 W | 0,00 dB | **45,0 dB** |
| 2 `HIGH` | 5,0 W | +3,98 dB | 49,0 dB |

Retranchez 3,01 dB de toute valeur du §4 pour la lire au réglage LOW du PA, ou ajoutez
3,98 dB pour la lire au réglage HIGH.

**Pourquoi cela mérite un paragraphe.** Jusqu'à ce changement, `_eirp` était une constante que rien ne
déduisait de la puissance du PA : `TTC_SET_TX_POWER` faisait varier la télémesure `ttc.tx_fwd_power`
(0x050D) et rien d'autre — la marge, le Eb/N₀, le TEB et toute la chaîne de traitement RF
étaient identiques au bit près à 1 W et à 5 W. La reprise de niveau 1 `ttc_reduce_power` de la FDIR, dont
la seule raison d'être est d'échanger débit et puissance contre la stabilité de la liaison, était donc sans effet sur
la liaison. `ttc.eirp_dbw` (0x052C) rend désormais compte de la valeur réelle, si bien que l'effet est visible
depuis le sol.

Deux réserves sur les niveaux absolus sont consignées dans `ttc.yaml` plutôt que reportées en silence :
10 dBW à 2 W RF suppose 7 dB de gain dont un 6U ne dispose pas (la valeur honnête est une
PIRE totale de 6 dBW, c.-à-d. que chaque marge donnée ici est optimiste d'env. 7 dB), et un palier « HIGH » de 5 W RF
tiré d'une ligne continue de 11 W correspond à un rendement en puissance ajoutée (PAE) de 45 %, qu'aucun SSPA en bande S n'atteint. Les deux
corrections touchent deux fichiers, `rfsim.yaml` et la référence de commandes générée, et toutes deux sont
signalées dans `docs/plan_2026-08b/DISPLAY_REQUESTS_TTC.md`. Aucune ne modifie les conclusions
ci-dessous : la pire case de la matrice boucherait encore avec 26 dB.

### 4.3 Le plafond est réglementaire, pas physique

L'attribution 2200–2290 MHz plafonne une mission à **5,00 MHz de largeur de bande occupée**. Avec un
SRRC α = 0,35, cela représente 3,70 MBd, soit, après RS(255,223) et la trame de transfert, environ
**3,2 Mbit/s** en QPSK avec codage convolutif, ou 6,4 Mbit/s avec RS seul. La liaison elle-même
transporterait plusieurs Mbit/s avec 3 dB de marge, même avec un diagramme d'antenne patch réaliste. C'est donc
la réglementation qui limite la première, quelle que soit la géométrie — et **aucune bande X n'est nécessaire pour cette mission**.
La bande X ne se justifierait que si le volume de données de la charge utile augmentait d'environ deux ordres de
grandeur.

---

## 5. Ce que l'échelle fait à la planification de mission

C'est ici que l'échelle cesse d'être un sujet RF pour devenir un sujet d'exploitation. Le
planificateur de mission (`packages/smo-planner`) lit deux échelons dans `tm_rate_tiers` — le
`default_tier` (LOW) pour le trafic courant et l'échelon supérieur (HIGH) pour les activités
`data_dump` — et n'utilise jamais un débit unique et uniforme. Trois conséquences en découlent.

### 5.1 Une image occupe l'essentiel d'un passage

Une trame brute de 4 Mio à HIGH :

| | À HIGH (128 kbit/s) | À LOW (16 kbit/s) |
|---|---|---|
| Temps de canal brut | **262,1 s** | 2097 s |
| Avec la marge protocolaire de 20 % du planificateur | **327,7 s** | 2621 s |
| En fraction du passage moyen de 445 s | **74 %** | 589 % |

L'activité `data_dump` de `planning/activity_types.yaml` dure donc **330 secondes** —
une image, arrondie au supérieur, et rien de plus. `n` images exigent `n` vidages, et l'arithmétique
d'un plan se lit d'emblée. L'ancienne durée de 600 s avait été dimensionnée pour un débit uniforme abandonné ;
à 128 kbit/s, elle aurait réservé une capacité de 1,8 image pour une seule image à y placer.

À LOW, la même image exige plus qu'un passage entier. **C'est le compromis que l'échelle rend
visible : à LOW, l'imagerie n'est pas simplement plus lente, elle est impossible.**

### 5.2 La servitude seule occupe un tiers du réseau à bas débit

Le flux de servitude de 1588 bit/s représente 16,4 Mio par jour. Le réseau de cinq stations offre
environ 23 300 secondes de contact par jour. Transmettre une journée de servitude
consomme donc :

| Palier | Temps de contact nécessaire par jour | Part du réseau |
|------|----------------------------:|---------------------:|
| LOW (16 kbit/s) | 8573 s | **37 %** |
| HIGH (128 kbit/s) | 1072 s | **4,6 %** |

Trente-sept pour cent de l'ensemble du réseau sol, avant même la première image. Le bilan rapporte
cette valeur sous `hk_contact_fraction_percent`, par palier, calculée à partir de `hk_structures.yaml` plutôt que
supposée. C'est le chiffre qui justifie que LOW vaille 16 kbit/s et non 8, et
celui qui empêche un étudiant de considérer la servitude comme gratuite.

### 5.3 Un passage consacré au vidage n'est consacré à rien d'autre

Le bilan de données du planificateur rapporte désormais, pour chaque passage :

* `high_fraction` — la proportion de la fenêtre située au-dessus du verrou de 10°, déduite de la
  géométrie sphérique (`fraction_above_elevation`), et non d'une table de correspondance. Un passage à 30°
  passe **77 %** de sa fenêtre au-dessus de 10° ; un passage à 12°, seulement **47 %** ; un passage à 7°, **aucune partie**,
  et ne peut jamais vider à HIGH ;
* `dump_capable` / `dump_tier` — si le passage peut tenir HIGH, et à quel palier s'exécuterait réellement
  un vidage réservé sur ce passage ;
* `capacity_mb` — la capacité combinée : HIGH sur l'arc au-dessus du verrou, LOW sur les
  extrémités, moins le temps de préparation et de libération de la station ;
* `dump_contact_fraction_percent` — la part des secondes de contact utilisables de la journée que le plan
  a déjà engagée dans des vidages.

Réserver un vidage sur un passage qui ne dépasse jamais 10° lève un avertissement `DUMP_BELOW_ELEVATION_GATE`,
car le satellite refusera le palier et le passage ne transmettra qu'un huitième du
volume prévu. Le modèle livré `nominal_ops_day` évite ce cas par construction : ses
entrées `data_dump` portent `min_pass_elevation_deg: 10.0`, de sorte que le modèle ne propose que
des passages que le satellite laissera fonctionner à HIGH — 43 des 52 fenêtres d'une journée type — et
ancre chaque vidage de 330 s sur le point de plus courte distance, où toute l'activité se situe au-dessus du verrou.

Avec les statistiques de contact livrées, ce plan produit 8,6 Mo et réserve huit vidages dont les
passages transportent 44 Mo ; il boucle avec environ **80 % de marge** — et il boucle *parce qu'il* réserve
HIGH. À LOW, les mêmes huit passages transporteraient 5,5 Mo pour 8,6 Mo produits, et le
plan ne bouclerait pas.

Capacité quotidienne du réseau, pour fixer les idées :

| Scénario | Capacité |
|----------|---------:|
| Toutes les secondes de contact utilisables à HIGH | ~227 Mio/jour |
| Toutes les secondes de contact utilisables à LOW | ~28 Mio/jour |
| Combinaison réaliste (HIGH au-dessus du verrou, LOW en dessous) | **~162 Mio/jour** |

Face à environ 8–34 Mo/jour de production, la mission dispose d'une marge — mais elle ne dispose de cette marge
que parce que les vidages sont réservés sur les bons passages.

---

## 6. Exploitation de l'échelle

### 6.1 Commandes

| Commande | Service | Sous-type | Fonction | Argument |
|---------|--------:|--------:|-----:|----------|
| `TTC_SET_DATA_RATE` | 8 | 1 | **65** | un code de palier `uint8` : `0x00` = LOW, `0x01` = HIGH, `0xFF` = SAFE (non accepté par le logiciel nominal) |
| `TTC_SET_DOWNLINK_MODE` | 8 | 1 | **79** | un `uint8` : 1 = entrer dans le mode DOWNLINK/vidage, 0 = en sortir |
| `TTC_SET_BEACON_MODE` | 8 | 1 | 70 | un `uint8` : 1 = forcer l'échelon SAFE (1 kbit/s) |

**L'ancien codage est conservé tel quel.** `rate=0` a toujours signifié « le débit bas »
et `rate=1` « le débit haut ». Toutes les procédures imprimées, toutes les OBCP et l'action FDIR
`ttc_reduce_power` continuent donc de fonctionner sans changement — elles aboutissent simplement désormais à des débits
opérationnels utilisables.

Un vidage comporte toujours les quatre mêmes étapes : entrer dans le mode DOWNLINK (79), augmenter le débit (65,
rate=1), vider, puis relâcher les deux. La séquence de commandes `data_dump` de
`planning/activity_types.yaml` fait exactement cela, et NOM-011 / NOM-003 guident l'opérateur pas à pas.

### 6.2 Télémesure, et la distinction entre actif et commandé

| Paramètre | ID | Signification |
|-----------|----|---------|
| `ttc.tx_active` | 0x0525 | **La chaîne bande S rayonne-t-elle seulement ?** Le verrou que franchit chaque paquet TM. La valeur 0 alors que l'échelle de débits indique encore un palier signifie que ce palier est celui auquel vous *émettriez* si vous émettiez |
| `ttc.tx_gate_status` | 0x052B | Pourquoi 0x0525 a sa valeur, bit par bit |
| `ttc.eirp_dbw` | 0x052C | PIRE réelle à la puissance commandée du PA (§4.2) |
| `ttc.beacon_active` | 0x0527 | L'**émetteur de balise UHF**, qui est une autre radio (§9) |
| `ttc.tm_data_rate` | 0x0506 | Débit utile actif (1000 / 16000 / 128000) |
| `ttc.tm_tier` | 0x0539 | Indice du palier **ACTIF** — ce qui est à l'antenne maintenant |
| `ttc.tm_tier_cmd` | 0x053A | Indice du palier **COMMANDÉ** — ce que le sol a demandé |
| `ttc.tm_symbol_rate` | 0x053B | Débit symbole à l'antenne (16 kBd à LOW, 64 kBd à HIGH) |
| `ttc.downlink_mode` | 0x053C | Mode DOWNLINK/vidage, le verrou de HIGH |

Les verrous agissent sur le palier **actif** et n'écrasent jamais le palier **commandé**. Ainsi, lorsqu'un
passage redescend sous 10°, `tm_tier` passe de HIGH à LOW tandis que `tm_tier_cmd` reste à
HIGH, et au passage suivant au-dessus de 10° la liaison revient à HIGH sans que personne
ne la commande à nouveau.

La console affiche les deux côte à côte, avec le motif lorsqu'ils diffèrent :

```
TM Rate (active)      LOW (16 kbps, BPSK, conv+RS)
TM Rate (commanded)   HIGH (128 kbps, QPSK, RS(255,223))
Tier gate             HIGH needs elevation >= 10 deg (now 6.4 deg)
```

Cette différence est un diagnostic, pas du bruit. Une console qui n'afficherait que le débit actif
transformerait « le verrou a refusé le palier que vous avez demandé » en « pourquoi le vidage est-il lent ? ».

### 6.3 Comment changer de débit, et pourquoi un changement peut être refusé

Un palier dont les verrous ne sont pas satisfaits est **refusé, jamais écrêté en silence** : le
satellite répond à `TTC_SET_DATA_RATE` par un échec d'exécution S1.8. Depuis le défaut n° 87,
ce rapport porte, dans sa notice d'échec, les propres termes du logiciel de bord, et le
même texte apparaît sous la forme de l'événement S5 `0x030B COMMAND_REJECTED` dans le journal des événements et le journal
FDIR. Si vous recevez un `1,8`, **lisez le motif** — le code numérique ne suffit pas, car
quatre verrous différents renvoient tous `0x0007`.

**Tous les verrous de `TTC_SET_DATA_RATE` (S8.1 fonction 65) :**

| N° | Verrou | S'applique à | Code | Ce que dit la notice d'échec |
|---|------|-----------|-----:|------------------------------|
| 1 | Le code de palier doit désigner un palier existant | tous | `0x0003` | `Invalid TM rate/tier <x>. Valid: 0=LOW(16000 bps), 1=HIGH(128000 bps), …` |
| 2 | **Le mode balise impose le palier balise** | LOW, HIGH | `0x0007` | `TM rate is forced to the beacon tier in beacon mode (LOW refused)` |
| 3 | SAFE est réservé au chargeur d'amorçage | SAFE (`0xFF`) | `0x0007` | `SAFE is a bootloader-only tier (1000 bps); not selectable in nominal operations` |
| 4 | L'antenne doit être déployée | HIGH | `0x0007` | `HIGH (128000 bps) requires a deployed antenna` |
| 5 | Le mode DOWNLINK/vidage doit être actif | HIGH | `0x0007` | `HIGH (128000 bps) requires DOWNLINK/dump mode (TTC_SET_DOWNLINK_MODE)` |
| — | La ligne d'alimentation de l'émetteur TT&C doit être sous tension | tous | `0x0004` | rejet plus précoce, à l'*acceptation* : `S8 func_id 65: power line 'ttc_tx' is OFF` |

Les verrous 1–5 relèvent de `ttc_basic._tier_permission_error` ; le verrou de ligne d'alimentation est le contrôle
central du moteur au moment de l'acceptation. Les verrous 4–5 s'appliquent aussi au palier ACTIF à chaque cycle, si bien que
HIGH revient automatiquement en arrière puis reprend sans nouvelle commande (§6.2) — mais le changement *commandé*
ci-dessus est refusé d'emblée.

**Le verrou 6 (élévation ≥ 10°) n'existe plus À BORD** (2026-08c) : un satellite
ne peut pas connaître son élévation vue d'une station, si bien que la règle des 10° pour HIGH a été transférée au
SOL — `subsystems/ttc.yaml tm_rate_tiers[HIGH].min_elevation_deg` est lu par le
planificateur de mission (qui programme les vidages HIGH au-dessus de ce seuil) et par la page de commande du MCS
(qui lève une retenue d'armement lorsque HIGH est commandé en dessous, d'après la géométrie de contact
propre au sol). Le texte de refus
`HIGH ... requires elevation >= 10 deg` ne peut donc plus être produit par le
satellite ; la physique continue de dégrader honnêtement les liaisons à faible élévation par
l'affaiblissement atmosphérique en cosécante et la dégradation du G/T.

**La séquence de commandes exacte.**

*Sélectionner LOW (opérations courantes) après un démarrage ou une reprise :*

```
1. S8.1 func 19  EPS_POWER_ON, line_index = 2 (ttc_tx)   (if not already on)
2. S8.1 func 66  TTC_PA_ON                          ← the step that was missing
3. S8.1 func 70  TTC_SET_BEACON_MODE, on = 0        ← clears gate 2
4. S8.1 func 69  TTC_DEPLOY_ANTENNA                 (once, LEOP; gate 4)
5. S8.1 func 65  TTC_SET_DATA_RATE, rate = 0x00     → LOW, 16 kbps
```

**L'étape 2 est nouvelle, et son absence passait autrefois inaperçue.** Le chargeur d'amorçage laisse le
satellite avec `pa_on = False` (`engine.py:631`) et rien n'effectuait l'opération inverse :
*chaque* reprise se déroulait donc avec l'amplificateur de puissance commandé à l'arrêt. Cela ne produisait aucun symptôme
tant que rien dans la chaîne TM ne lisait l'état du PA — la télémesure passait quand même. Deux
modifications corrigent ce point :

* **Le démarrage de l'application lève l'inhibition de la bande S.** Le modèle TT&C surveille
  `obdh.sw_image` (0x0311) et réactive le PA au passage du chargeur d'amorçage → application,
  ce qui constitue la moitié manquante de l'inhibition posée par `_enter_bootloader_mode`. Un satellite qui
  redémarre sur son application revient donc avec un émetteur, ce qui est le seul
  comportement par défaut permettant de survivre : l'autre option est une réinitialisation par le chien de garde dont on ne peut se sortir
  qu'au moyen d'une commande envoyée à l'aveugle.
* **L'étape 2 reste écrite, et mérite toujours d'être envoyée.** Elle est idempotente après un
  démarrage propre, et c'est l'étape qui rétablit la liaison après qu'un opérateur ou une fiche
  FDIR a coupé le PA — `ttc_emergency_shutdown` fait exactement cela.

Si le PA *est* à l'arrêt, le symptôme est désormais sans équivoque : aucune télémesure en bande S, seulement le
SID 11 de la balise UHF toutes les 30 s, avec `ttc.pa_on` à 0 dans cette balise.

La sortie du mode balise (étape 3) remet aussi le palier **commandé** à LOW. Avant 2026-08b,
elle ne remettait à zéro que l'indicateur, si bien que la console affichait commandé = SAFE / actif = LOW
indéfiniment, et l'affichage de rétrogradation de palier ne pouvait jamais s'effacer.

*Sélectionner HIGH pour un vidage, puis le restituer :*

```
1. …LOW selectable as above (elevation ≥ 10 deg is a GROUND policy hold in the
   MCS, not an on-board gate)
2. S8.1 func 79  TTC_SET_DOWNLINK_MODE, on = 1        ← clears gate 5
3. S8.1 func 65  TTC_SET_DATA_RATE, rate = 0x01       → HIGH, 128 kbps
4. …dump (S15.9 / S13)…
5. S8.1 func 65  TTC_SET_DATA_RATE, rate = 0x00       → back to LOW
6. S8.1 func 79  TTC_SET_DOWNLINK_MODE, on = 0
```

**Le piège classique.** Démarrer l'application de l'OBC (`S8.1 func 55`,
`OBC_BOOT_APP`) ne fait **pas** sortir du mode balise. Un satellite qui a démarré sous le
chargeur d'amorçage, ou qui a été placé en mode balise par une procédure de contingence, reste en mode balise
une fois l'application en cours d'exécution — et le verrou 2 refuse *à la fois* LOW et HIGH tant que
`TTC_SET_BEACON_MODE off` n'a pas été envoyé. La question de savoir si le démarrage de l'application devrait faire sortir automatiquement du mode balise
reste une question de conception ouverte ; aujourd'hui ce n'est délibérément pas le cas, et l'étape 3
ci-dessus est donc obligatoire. LEOP-002 et CON-BOOT la détaillent.

---

## 7. Modifier les valeurs

Tout ce qui précède relève de la configuration. `configs/eosat1/subsystems/ttc.yaml` est le seul endroit
où un débit est défini ; le simulateur, la chaîne de traitement RF, le planificateur, la console, le
test des procédures et l'outil de bilan de liaison le lisent tous.

**Pour modifier un débit**, éditez le `bps` de l'échelon :

```yaml
tm_rate_tiers:
  - name: HIGH
    bps: 256000            # was 128000
    command_code: 0x01
    modulation: QPSK
    coding: RS
    coding_gain_db: 6.0
    requires_antenna: true
    requires_downlink_mode: true
    min_elevation_deg: 10.0
```

Puis exécutez, dans l'ordre :

1. `python tools/link_budget_ladder.py` — vérifier que chaque échelon boucle encore et que les échelons sont
   ceux que prédit le bilan. L'outil se termine avec un code non nul si un échelon ne boucle pas ou déborde du
   canal de 5 MHz.
2. `python -m pytest tests/test_content/test_data_rate_content.py` — ce test lit l'échelle
   et vous indique **quels documents il vous reste à modifier**. C'est le fil-piège qui détecte
   précisément le type de dérive que ce changement visait à éliminer.
3. `python -m pytest tests/test_planner tests/test_mcs tests/test_simulator` — le planificateur
   recalcule à partir de la configuration la vérification de durée de `data_dump`, la capacité quotidienne et l'arithmétique
   du verrou d'élévation : un changement de débit qui casse le plan livré échoue ici.

**Pour modifier un verrou**, éditez les champs `requires_antenna`, `requires_downlink_mode` ou
`min_elevation_deg` du palier. Le planificateur lit `min_elevation_deg` comme valeur par défaut de son
`min_dump_elevation_deg`, et `tests/test_content/test_data_rate_content.py`
vérifie que chaque station de `planning/planner.yaml` utilise la même valeur — le segment
sol ne peut donc pas planifier en fonction d'un verrou que le satellite n'applique pas.

**Pour changer l'échelon par défaut**, éditez `default_tier` (opérations courantes),
`safe_tier` (mode survie et repli FDIR) ou `beacon_tier` (chargeur d'amorçage). Ce sont des *noms*
de paliers ; un nom absent de `tm_rate_tiers` fait échouer la validation de la configuration au chargement.

**Pour ajouter un échelon**, ajoutez-le à la fin de `tm_rate_tiers`. La liste doit être strictement croissante en
`bps` et ses noms doivent être uniques — les deux conditions sont validées. Donnez-lui un `command_code` qu'aucun
autre échelon n'utilise. Rien d'autre n'est à modifier : la console construit ses libellés à partir de la liste,
le planificateur prend l'échelon supérieur comme débit de vidage et `default_tier` comme débit courant,
et `tools/link_budget_ladder.py` imprime une colonne pour lui.

**Ce qu'il ne faut pas faire**, c'est ajouter une seconde copie d'un débit où que ce soit. Les clés obsolètes
`tm_rate_lo_bps` / `tm_rate_hi_bps` existent encore dans `ttc.yaml` pour les lecteurs extérieurs
et sont déduites de l'échelle lorsqu'elles sont omises ; ce sont des alias du palier de survie et du
palier supérieur, et aucun nouveau code ne devrait les lire.

---

## 8. Pour aller plus loin

* `configs/eosat1/subsystems/ttc.yaml` — l'échelle elle-même, avec le raisonnement en commentaires
* `configs/eosat1/manual/05_ttc.md` §2.4 — le point de vue de l'opérateur
* `configs/eosat1/procedures/nominal/data_rate_change.md` (NOM-011) — changer de palier pendant
  un passage
* `configs/eosat1/procedures/commissioning/ttc_link_verification.md` (COM-006) — mesurer
  les références
* `docs/PUS_SERVICE_REFERENCE.md` — les fonctions 65 et 79 en détail
* `docs/sim_fidelity/ttc_fidelity.md` §6 — la machine d'états des débits telle que mise en œuvre
* `tools/link_budget_ladder.py` — régénérer toutes les valeurs du §4

---

## 9. L'autre émetteur — la balise UHF du chargeur d'amorçage

Tout ce qui précède le §8 décrit **une seule** radio : la chaîne principale en bande S. EOSAT-1 en emporte une
seconde, et c'est la plus intéressante des deux pour un étudiant, car elle boucle un
bilan complètement différent, avec un matériel complètement différent, pour remplir une mission que la chaîne
principale ne peut structurellement pas assurer.

### 9.1 Pourquoi une seconde radio

Relisez les §2 et §5 et remarquez ce qu'ils ont en commun : chaque échelon de l'échelle, chaque
verrou, chaque vidage et chaque paquet de servitude passe par le même PA bande S, la même
ligne d'alimentation `ttc_tx`, le même transpondeur et la même antenne patch déployable. Ce sont quatre
points de défaillance unique, en série, sur la seule chose qui puisse vous dire que le satellite
est vivant.

Un émetteur de balise n'en partage aucun. Il a son propre PA, sa propre bande, sa propre
antenne et sa propre alimentation, et c'est le boîtier qui répond à *l'OBC est-il vivant ?* lorsque
la réponse à *la chaîne bande S est-elle vivante ?* est non. C'est pourquoi le manuel de cours spécifie
« S-band prime (body-fixed patch) + UHF whip bootloader beacon » (bande S principale avec antenne patch fixée sur la structure + balise UHF du chargeur d'amorçage à antenne fouet) depuis la première édition, et
pourquoi le périmètre (d) de `UPGRADE_ROADMAP.md` demandait que les valeurs UHF soient conservées comme
liaison de la balise du chargeur d'amorçage.

Jusqu'à 2026-08b, elle n'était pas mise en œuvre. L'échelon aujourd'hui nommé `SAFE` était l'échelon 0 de l'échelle bande S — le
même PA, la même antenne, 1 kbit/s au lieu de 16 — si bien que couper le PA bande S réduisait au silence
la ligne de vie avec tout le reste. Décision R2 de Franz : construire la seconde radio.

### 9.2 Ce qu'elle est

| | Chaîne principale bande S | Émetteur de balise UHF |
|---|---|---|
| Liaison descendante | 2200 MHz | **437,5 MHz** (segment satellite amateur 435–438 MHz) |
| Sortie RF | 1 / 2 / 5 W, commandable | **1,0 W** (30 dBm), fixe |
| Antenne bord | Antenne patch déployable de 3,0 dBi | Dipôle déployable à ruban-ressort de **0 dBi** |
| Station sol | Parabole polaire de 9 m, G/T +20,0 dB/K | **Yagi croisées d'env. 16 dBic, G/T −8,0 dB/K** |
| Débits | Échelle 1 / 16 / 128 kbit/s | **1 kbit/s**, un seul débit |
| Transporte | Tout | **HK SID 11, et rien d'autre** |
| Alimentation | `ttc_tx`, commutable, 5–11 W en continu | `ttc_rx`, **non commutable**, 1,8 W en continu pendant l'émission |
| Commutée par | `TTC_PA_ON` / `TTC_PA_OFF` (66/67) | `TTC_BEACON_TX_ON` / `_OFF` (**97/98**) |
| Télémesure | `ttc.tx_active` 0x0525 | `ttc.beacon_active` 0x0527 |

Matériel dont proviennent les valeurs : **EnduroSat UHF Type II Transceiver** (435–438 MHz,
sortie jusqu'à 33 dBm, typiquement 30 dBm), **GomSpace NanoCom AX100** (430–440 MHz, jusqu'à
30 dBm), **EnduroSat UHF Antenna Type II** (dipôle déployable à ruban-ressort, env. 0 dBi,
polarisation linéaire), et le chapitre 9 de *State of the Art of Small Spacecraft Technology* de la NASA, qui
désigne l'UHF comme la bande de balise standard des CubeSat. 437,5 MHz est la fréquence où se trouvent réellement
les balises de CubeSat coordonnées par l'IARU.

### 9.3 Le bilan, et le contraste qui constitue toute la leçon

Orbite à 513 km, distance oblique tirée du même tableau de géométrie qu'au §4.

| Élévation | Distance oblique | Affaiblissement en espace libre UHF à 437,5 MHz | Eb/N₀ | **Marge de la balise** | Marge LOW bande S | Échelon SAFE bande S |
|---|---:|---:|---:|---:|---:|---:|
| 5° | 2111,7 km | 151,76 dB | 31,2 dB | **29,1 dB** | 45,0 dB | 57,0 dB |
| 10° | 1726,8 km | 150,02 dB | 34,5 dB | **32,4 dB** | 49,2 dB | 61,2 dB |
| 30° | 931,3 km | 144,65 dB | 40,7 dB | **38,6 dB** | 56,0 dB | 68,0 dB |
| 90° | 513,0 km | 139,47 dB | 45,9 dB | **43,9 dB** | 61,2 dB | 73,2 dB |

Calcul détaillé, pour la géométrie la plus défavorable (5°) :

```
EIRP           1.0 W = 0.00 dBW  +  0.0 dBi dipôle      =    0.00 dBW
FSPL           20log₁₀(2111.7 km) + 20log₁₀(437.5 MHz) − 147.55 = 151.76 dB
pertes         atmosphère 1.15 (0.2 dB au zénith × cosec 5°)
               + polarisation 3.0 + mise en œuvre 2.0   =    6.15 dB
G/T            −8.0 dB/K, déclassé de 1.5 dB sous 10°   =   −9.50 dB/K
C/N₀           0.00 − 151.76 − 6.15 − 9.50 + 228.6      =   61.19 dBHz
Eb/N₀          61.19 − 10log₁₀(1000)                    =   31.19 dB
requis         9.6 non codé − 7.5 conv(7,½)+RS          =    2.10 dB
MARGIN (marge)                                               29.09 dB
```

Placez maintenant ce résultat à côté de l'échelon `SAFE` en bande S, à la même géométrie et au même
débit utile — 57,0 dB — et expliquez l'écart de 27,9 dB. Il ne s'agit **pas** d'un seul
effet :

| Terme | UHF face à la bande S | Pourquoi |
|---|---:|---|
| Affaiblissement en espace libre | **+14,03 dB en faveur de l'UHF** | 20·log₁₀(2200/437,5) ; une longueur d'onde cinq fois plus grande |
| Puissance d'émission | −10,0 dB pour l'UHF | 1 W dans le dipôle (0 dBW) contre une PIRE en bande S de 10 dBW au réglage NOMINAL de l'amplificateur |
| Atmosphère | +1,72 dB en faveur de l'UHF | 1,15 dB contre 2,87 dB à 5° (0,2 dB contre 0,5 dB au zénith) ; l'UHF se situe bien en dessous des raies de la vapeur d'eau |
| Antenne bord | −3,0 dB pour l'UHF | dipôle omnidirectionnel de 0 dBi contre une antenne patch de 3 dBi |
| Polarisation | −2,7 dB pour l'UHF | un dipôle linéaire sur un satellite susceptible de culbuter, face à une antenne sol à polarisation circulaire, représente une désadaptation nominale de 3 dB, et non de 0,3 dB |
| G/T de la station sol | **−28,0 dB pour l'UHF** | une parabole professionnelle de 9 m est meilleure de 28 dB qu'une Yagi universitaire |
| **Bilan net** | **−27,95 dB** | |

Deux leçons qu'un étudiant devrait tirer de ce tableau. Premièrement, **le choix de la fréquence n'est pas
le terme dominant** — l'UHF gagne 14 dB d'affaiblissement de propagation, puis en rend le double en
gain de station sol, car l'ouverture que l'on peut construire évolue avec la longueur d'onde aux deux
extrémités, et c'est à l'extrémité sol que se trouve l'argent. Deuxièmement, **la balise boucle malgré tout, avec
environ 29 dB**, parce qu'elle demande 1 kbit/s au lieu de 16, et qu'elle s'adresse à une station que l'on peut construire sur
le parking d'une université. C'est une liaison délibérément modeste qui remplit une mission délibérément modeste,
et c'est ce qui lui permet de survivre.

### 9.4 Ce qu'elle conditionne, et ce qu'elle ne conditionne pas

**Uniquement la HK SID 11.** Lorsque la chaîne bande S émet (`ttc.tx_active` = 1), le propre
programmateur de servitude de l'OBC envoie le SID 11 avec tout le reste et la balise reste
silencieuse — pas de doublon. Lorsque la chaîne bande S n'émet *pas*, la balise émet le
SID 11 à son propre rythme de 30 s, et rien d'autre ne descend avec lui. La HK temps réel, la relecture,
les vidages d'images, la vérification S1 et les lectures à la demande restent toutes sur la chaîne bande S et meurent toutes
avec le PA.

Le SID 11 transporte sept paramètres : tension et SoC de la batterie, mode de l'OBC, compteur de redémarrages, image
logicielle active, OBC actif — et, depuis 2026-08b, **`ttc.pa_on`**. Ce dernier octet est
la raison d'être de tout l'exercice. Lorsque le symptôme initial observé par Franz se produit en sens inverse — aucune
télémesure lors d'un passage — le seul paquet que vous recevez encore vous indique si le PA bande S est à l'arrêt,
ce qui transforme un satellite muet en une correction à une seule commande (`TTC_PA_ON`, §6.3, étape 2).

À 1 kbit/s, un paquet SID 11 de 29 octets dure 0,23 s : le rapport cyclique d'émission de la balise est donc de
**0,75 %** et sa consommation moyenne sur l'orbite de **13 mW**. `eps.yaml` la prend déjà en compte :
`transponder_rx_power_w` = 1.5 W est documenté au §3 de `POWER_SIZING.md` comme « EnduroSat
idle/Rx 1.2 W + ~0.3 W UHF beacon Rx », ce qui couvre la veille de la balise et son émission
avec deux ordres de grandeur de réserve. **Aucune modification de l'EPS n'est nécessaire** — le calcul se trouve dans
`DISPLAY_REQUESTS_TTC.md`.

### 9.5 Trois choses appelées « beacon », et comment les distinguer

C'est le piège, et c'est la raison pour laquelle l'émetteur de balise est resté non construit pendant un an.

| Nom | Ce que c'est | Télémesure | Modifié par |
|---|---|---|---|
| **Palier `SAFE`** (ex-BEACON) | échelon 0 de l'échelle de débits TM **bande S** — 1 kbit/s, BPSK, conv+RS | `ttc.tm_tier` 0x0539 = 0 | l'entrée en mode balise ou dans le chargeur d'amorçage |
| **`beacon_mode`** | un indicateur verrouillé qui bloque l'échelle bande S sur cet échelon | `ttc.beacon_mode` 0x0521 | `TTC_SET_BEACON_MODE`, S8 fonction **70** |
| **émetteur de balise** | une **seconde radio** à 437,5 MHz transportant le SID 11 | `ttc.beacon_tx_on` 0x0526, `ttc.beacon_active` 0x0527 | `TTC_BEACON_TX_ON`/`_OFF`, S8 fonctions **97/98** |

Les deux premiers sont un même concept (un débit) sous deux noms ; le troisième est un matériel. Aucun
n'implique les autres : on peut être en mode balise avec l'émetteur UHF éteint, ou au palier HIGH
avec l'émetteur allumé, et l'état normal du satellite est une bande S capable de HIGH *plus* une
balise discrètement disponible en arrière-plan.

**Sous le chargeur d'amorçage, les trois coïncident, et c'est précisément pourquoi on les a confondus.** Le
chargeur d'amorçage règle `pa_on = False`, `antenna_deployed = False` et `beacon_mode = True` : l'échelle
bande S se trouve sur son échelon SAFE (ex-BEACON) *et* la chaîne bande S est inhibée *et* la
balise UHF est la seule chose à l'antenne. Les trois états coïncident là, et seulement là.
