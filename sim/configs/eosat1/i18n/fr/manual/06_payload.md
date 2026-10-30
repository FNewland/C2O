# Charge utile d'EOSAT-1 — imageur multispectral

**Référence du document :** EOSAT1-UM-PLD-007
**Édition :** 2.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Vue d'ensemble

La charge utile d'EOSAT-1 est un imageur multispectral à balayage par barrette (pushbroom), monté au nadir et optimisé pour l'observation
de la couleur de l'océan et la surveillance des courants. Il fournit des images de moyenne résolution dans quatre
bandes spectrales du visible et du proche infrarouge (VNIR), choisies spécifiquement pour
la science de la couleur de l'océan (absorption de la chlorophylle, luminance émergente de l'eau, détection des sédiments
en suspension). Il dispose d'un plan focal (FPA) refroidi pour un rapport signal sur bruit
optimal et d'une compression bord des données adaptée à la scène.

## 2. Caractéristiques de l'instrument

| Paramètre              | Valeur                         |
|------------------------|--------------------------------|
| Type d'instrument      | Imageur multispectral à barrette (pushbroom) |
| Domaine spectral       | 443–865 nm (VNIR)             |
| Nombre de bandes       | 4 (bleu, vert, rouge, NIR)    |
| Distance d'échantillonnage au sol (GSD) | ~33 m (à l'altitude moyenne de 513 km) |
| Largeur de fauchée     | ~273 km (à l'altitude moyenne de 513 km) |
| Type de détecteur      | Barrette linéaire CCD          |
| Température de fonctionnement du FPA | -15 °C (nominale) |
| Débit (brut)           | ~40 Mbit/s                     |
| Taux de compression    | 2:1 à 8:1 (selon la scène)    |
| Débit effectif         | ~5–20 Mbit/s (compressé)      |
| Montage                | Face nadir (+Z), axe de visée selon +Z |

### 2.1 Bandes spectrales — configuration couleur de l'océan

Les bandes spectrales sont choisies spécifiquement pour la science de la couleur de l'océan et la surveillance des courants :

| Bande | Nom  | Longueur d'onde centrale | Largeur de bande | Application principale            |
|------|-------|-------------------|-----------|----------------------------------------|
| 1    | Bleu  | 443 nm            | 20 nm     | Absorption de la chlorophylle, couleur de l'océan |
| 2    | Vert  | 560 nm            | 35 nm     | Luminance émergente de l'eau, turbidité |
| 3    | Rouge | 665 nm            | 30 nm     | Sédiments en suspension, éléments côtiers |
| 4    | NIR   | 865 nm            | 40 nm     | Correction atmosphérique, masque terre-mer |

**Application à la couleur de l'océan :** la bande bleue à 443 nm est centrée sur le pic d'absorption de la chlorophylle a,
ce qui en fait le canal principal pour détecter les efflorescences de phytoplancton et les
variations de couleur de l'océan associées aux limites des courants. La bande verte capte la
luminance émergente de l'eau pour la cartographie de la turbidité. Les bandes rouge et NIR assurent la
correction atmosphérique et la discrimination terre/mer.

### 2.2 Géométrie en fonction de l'altitude

La géométrie de prise de vue varie avec l'altitude orbitale et découle du champ de vue total de 29,856°
de l'optique (8192 px x 5,5 µm sur un télescope de 84,5 mm). Le segment
sol calcule les deux grandeurs à partir de la solution d'orbite courante ; sur l'orbite de 503–530 km
(moyenne de 513 km, décision 2026-08 sur l'époque et l'altitude) :

| Paramètre              | À 513 km (moyenne) | À 450 km (valeur déclarée abandonnée) | Loi de variation |
|------------------------|------------------|---------------------------------|--------------------|
| GSD | ~33,4 m         | ~29,3 m                         | Proportionnelle à l'altitude |
| Largeur de fauchée     | ~273 km          | ~240 km                         | Proportionnelle à l'altitude |

L'altitude réelle plus élevée élargit la fauchée et dégrade la GSD d'environ 14 % par rapport aux
valeurs citées historiquement à 450 km.

### 2.3 Compression adaptée à la scène

L'algorithme de compression bord adapte son taux au contenu de la scène :

| Type de scène      | Taux type     | Remarques                                  |
|--------------------|---------------|--------------------------------------------|
| Océan ouvert (uniforme) | 6:1 à 8:1 | Faible complexité spatiale, forte compressibilité |
| Côtier/mixte       | 3:1 à 5:1    | Complexité moyenne                         |
| Terre (urbaine/variée) | 2:1 à 3:1 | Forte complexité spatiale                 |
| Couverture nuageuse | 4:1 à 6:1   | Complexité moyenne, faible valeur scientifique |

Le taux de compression est indiqué dans la télémesure et influe sur le bilan de volume de données utilisé pour
la planification des transmissions au sol.

### 2.4 Couplage entre attitude et qualité d'image

La qualité d'image est directement liée à la stabilité d'attitude du satellite pendant l'acquisition :

| Erreur d'attitude | Impact sur la qualité d'image                          |
|------------------|---------------------------------------------------------|
| < 0.1 deg        | Qualité complète — GSD et FTM nominales                 |
| 0.1 – 0.5 deg   | Acceptable — léger filé, exploitable scientifiquement   |
| 0.5 – 1.0 deg   | Dégradée — filé important, résolution spatiale réduite  |
| > 1.0 deg        | Inexploitable — ne pas tenter de prise de vue           |

Le paramètre AOCS `att_error` (0x0217) doit être surveillé avant et pendant la prise de vue. Si
l'erreur d'attitude dépasse 0.5 deg pendant l'acquisition, la qualité d'image est fortement dégradée
et les données peuvent ne pas satisfaire aux exigences scientifiques de détection des courants océaniques. La règle FDIR
PLD-02 interrompt la prise de vue si `att_error` dépasse 1 deg.

## 3. Modes de la charge utile

| ID de mode | Nom du mode | Description                                        |
|---------|------------|-------------------------------------------------------|
| 0       | OFF        | Charge utile hors tension, aucun contrôle thermique   |
| 1       | STANDBY    | Électronique sous tension, refroidisseur du FPA actif, pas de prise de vue |
| 2       | IMAGING    | Acquisition d'images active et traitement bord        |
| 3       | CALIBRATION | Étalonnage radiométrique (obturateur fermé, image d'obscurité / champ plat) |

**Remarque :** une fonction PLAYBACK est gérée par le sous-système de mémoire de masse de l'OBDH et ne
nécessite pas de mode dédié de la charge utile. Les données d'image enregistrées sont transmises au sol par le sous-système TTC
pendant les contacts sol.

### 3.1 Transitions de mode

```
OFF --> STANDBY --> IMAGING --> STANDBY --> OFF
```

- **De OFF à STANDBY** : sur commande sol via `PAYLOAD_SET_MODE` (mode=1). Le refroidisseur du FPA commence
  la mise en froid. La boucle atteint la bande de consigne en 10 minutes environ depuis l'équilibre
  non refroidi, et `fpa_ready` (0x0610) est positionné après 60 s supplémentaires d'hystérésis.
- **De STANDBY à IMAGING** : sur commande sol via `PAYLOAD_SET_MODE` (mode=2). Le FPA doit
  être prêt thermiquement — `fpa_ready` (0x0610) = 1. Cet indicateur constitue la condition ; il signifie que la boucle
  s'est stabilisée autour de la consigne **active** du refroidisseur (-1 K / +5 K) *et* que `fpa_temp` est à
  **-3.0 °C** ou en dessous. Avec la consigne par défaut de -15 °C, cela correspond à
  **-16.0 … -10.0 °C**. Ne vous fiez pas à une valeur mémorisée : la consigne est commandable
  sur -20…0 °C, si bien que tout seuil fixe est faux sur la majeure partie de l'enveloppe.
- **De IMAGING à STANDBY** : sur commande sol ou de façon autonome à la fin de la fenêtre de prise de vue.
- **De STANDBY à OFF** : sur commande sol via `PAYLOAD_SET_MODE` (mode=0).

### 3.2 Contraintes de prise de vue

| Contrainte                   | Valeur / condition                   |
|------------------------------|--------------------------------------|
| Condition thermique du FPA   | `fpa_ready` (0x0610) = 1 — stabilisé autour de la consigne active (-1 K/+5 K) **et** à -3.0 °C ou en dessous |
| Prise de vue continue max.   | 10 min (limitée par la thermique et la puissance) |
| SoC min. de la batterie      | 40 % (pour l'activation de la prise de vue) |
| Mode AOCS requis             | NOMINAL (4) ou FINE_POINT (5)        |
| Erreur d'attitude requise    | < 0.5 deg                            |

## 4. Stockage et gestion des données

Les images acquises sont stockées dans la mémoire de masse de l'OBDH. Chaque bande d'image reçoit un
numéro de séquence et une somme de contrôle CRC pour la vérification de l'intégrité des données.

| Paramètre           | Valeur                         |
|---------------------|--------------------------------|
| Mémoire d'images de la charge utile | 20 000 Mo (`total_storage_mb`) |
| Octets par image    | Image brute de 4 Mo (1,0–2,7 Mo stockés après compression) |
| Nombre max. d'images stockées | ~5 000 images brutes |
| Algorithme de somme de contrôle | CRC-32             |

Le paramètre `store_used` (0x0604) indique le pourcentage de la mémoire de masse occupé
par les données de la charge utile. `image_count` (0x0605) comptabilise le nombre de fichiers image stockés.
Le paramètre `checksum_errors` (0x0609) compte les défauts d'intégrité des données.

## 5. Paramètres de télémesure

| ID param. | Nom            | Unité  | Description                          |
|----------|-----------------|--------|--------------------------------------|
| 0x0600   | pld_mode        | enum   | Mode courant de la charge utile (0/1/2/3) |
| 0x0601   | fpa_temp        | °C     | Température du plan focal            |
| 0x0602   | cooler_pwr      | W      | Consommation du refroidisseur du FPA |
| 0x0604   | store_used      | %      | Taux d'occupation du stockage des données de la charge utile |
| 0x0605   | image_count     | nombre | Nombre d'images stockées             |
| 0x0609   | checksum_errors | nombre | Nombre cumulé d'erreurs de somme de contrôle |

## 6. Définition des limites

| Paramètre       | Jaune bas  | Jaune haut  | Rouge bas | Rouge haut |
|-----------------|------------|-------------|---------|----------|
| fpa_temp (°C)     | -22.5      | 13.5        | -26.0   | 17.0     |
| detector_temp (°C) | -22.0     | 14.0        | -25.5   | 17.5     |

Dérivées de `subsystems/tcs.yaml: fpa_envelope` (DECISIONS §3) — les bandes du nœud
FPA du TCS (03_tcs.md §6) décalées le long de la chaîne thermique de la charge utile :

| Mesure | Param. | Position |
|---|---|---|
| Support du FPA (nœud de régulation TCS) | 0x0408 | la consigne régulée |
| Doigt froid | 0x0601 `fpa_temp` | support **-0,5 K** |
| Puce du détecteur | 0x0617 `detector_temp` | doigt froid **+0,5 K** (autoéchauffement) |

### 6.1 Interprétation de la température du FPA

Les limites répondent à la question « le matériel est-il sain ? ». La disponibilité répond à la question « puis-je prendre des images ? ».
Ce sont deux questions différentes, et elles figuraient autrefois dans le même tableau, ce qui explique pourquoi
cinq fichiers se contredisaient.

- **En dessous de -22.5 °C** : plus froid que ce que le refroidisseur peut commander. La boucle a perdu le
  contrôle — il s'agit d'un défaut, et non d'un refroidisseur trop performant.
- **À l'intérieur de la bande commandée** (consigne active -1 K / +5 K) **et à -3.0 °C
  ou en dessous** : plage de prise de vue. `fpa_ready` = 1.
- **Au-dessus de -3.0 °C** : `FPA_OVERTEMP` (0x0604). Le courant d'obscurité rend le
  produit inexploitable. Situation légitime en STANDBY ; aucune prise de vue ne doit être lancée.
- **Autour de +11,5 °C** : état de repos normal, non refroidi, refroidisseur
  éteint. Ce n'est pas une alarme.
- **Au-dessus de +13.5 °C** : jaune. Au-dessus de **+17.0 °C** : rouge — le chemin thermique vers le radiateur
  a été perdu, ou un étuvage de décontamination est en cours (0x0418).

## 7. Commandes

| Commande          | Service  | Paramètres    | Description                          |
|-------------------|----------|---------------|--------------------------------------|
| PAYLOAD_SET_MODE  | S8,S1    | mode (0/1/2/3) | Régler le mode de fonctionnement de la charge utile |
| HK_REQUEST        | S3,S27   | sid=6         | Demander le paquet de servitude de la charge utile |
| GET_PARAM         | S20,S3   | param_id      | Lire un paramètre individuel de la charge utile |
| SET_PARAM         | S20,S1   | param_id, val | Modifier un paramètre de configuration de la charge utile |

### 7.1 Séquence de prise de vue type

1. Vérifier que le satellite est en mode AOCS NOMINAL (4) avec `att_error` < 0.5 deg.
2. Vérifier que le SoC de la batterie est > 40 % et que la mémoire de masse disponible est suffisante.
3. Envoyer `PAYLOAD_SET_MODE` (mode=1) pour passer en STANDBY. Surveiller `fpa_temp` (0x0601).
4. Attendre la mise en froid du FPA : `fpa_ready` (0x0610) = 1 — environ 10 minutes depuis l'équilibre
   non refroidi, plus 60 s d'hystérésis de disponibilité.
   Avec la consigne par défaut de -15 °C, cela correspond à `fpa_temp` dans -16.0 … -10.0 °C.
5. Au début de la fenêtre de prise de vue, envoyer `PAYLOAD_SET_MODE` (mode=2).
6. Surveiller l'incrémentation de `image_count` (0x0605) pendant l'acquisition.
7. À la fin de la fenêtre de prise de vue, envoyer `PAYLOAD_SET_MODE` (mode=1) pour revenir en STANDBY.
8. Si aucune autre prise de vue n'est prévue, envoyer `PAYLOAD_SET_MODE` (mode=0).

## 8. Remarques d'exploitation

1. Le refroidisseur du FPA consomme 15 W. Le bilan de puissance total de la charge utile en mode IMAGING est
   d'environ 20,5 W (15 W pour le refroidisseur + 5,5 W pour l'imageur ; voir 01_eps.md).
2. La prise de vue pendant l'éclipse est possible, mais produit des images d'obscurité (utiles pour l'étalonnage).
3. Si `checksum_errors` (0x0609) s'incrémente, l'image la plus récente est peut-être corrompue.
   Il convient d'envisager une nouvelle prise de vue de la cible.
4. La transmission au sol des données de la charge utile s'effectue sur le palier HIGH de l'échelle de débits TM (128 kbit/s, QPSK,
   RS(255,223), voir `manual/05_ttc.md` §2.4). Une image brute de 4 Mio représente 262 s de canal,
   ou 328 s une fois appliquée la provision protocolaire de 20 % du planificateur de mission — soit environ
   les trois quarts du passage moyen de 445 s des statistiques de contact à cinq stations de cette mission.
   100 Mo de produit compressé représentent donc environ 2,3 heures de temps de
   contact, soit l'essentiel du réseau utilisable en une journée. La programmation des transmissions au sol doit tenir compte du
   temps de contact disponible sur l'ensemble des cinq stations, et le palier HIGH n'est disponible
   que sur les passages atteignant 10° d'élévation, avec le mode DOWNLINK commandé.
5. La charge utile ne devrait pas rester en STANDBY plus de 4 heures d'affilée, afin de
   préserver la durée de vie du refroidisseur.
6. Pour la surveillance des courants océaniques, donner la priorité aux prises de vue au-dessus des régions où les limites des courants
   sont connues (p. ex. Gulf Stream, Kuroshio, courant circumpolaire antarctique). La bande bleue à
   443 nm offre la plus grande sensibilité aux gradients de chlorophylle a aux limites
   des courants.
7. Du fait des taux de compression adaptés à la scène, les images d'océan ouvert occupent moins d'espace de stockage
   que les images côtières ou terrestres. Le planificateur de mission devrait en tenir compte lors de l'estimation
   des bilans de volume de données.
8. La stabilité d'attitude est essentielle pour les mesures de couleur de l'océan. Vérifier que `att_error` < 0.5 deg
   avant de commander le mode IMAGING. Une attitude dégradée produit des images floues,
   inexploitables pour l'estimation de la vitesse des courants océaniques.

---

*Fin du document — EOSAT1-UM-PLD-007*

---

## Réglages commandables

Tous les réglages de la charge utile accessibles par liaison, avec leur codage.

<!-- BEGIN GENERATED: payload commandable settings -->
<!-- Generated by tools/gen_command_reference.py — do not edit by hand. -->

| Réglage | Commande | func_id | Forme transmise | Plage physique | Défaut | Relecture |
|---|---|---|---|---|---|---|
| Régler le mode de la charge utile. | `PAYLOAD_SET_MODE` | 26 (0x1A) | mode:uint8 | 0 … 3 | 0 | payload.mode (0x0600) |
| OBSOLÈTE — prérégler l'identifiant de la prochaine scène. | `PAYLOAD_SET_SCENE` | 27 (0x1B) | scene_id:uint16 | 0 … 65535 | 0 | payload.scene_id (0x0606) |
| Déclencher une acquisition d'image. | `PAYLOAD_CAPTURE` | 28 (0x1C) | scene_id:uint16, lines:uint16 | 0 … 65535; 256 … 20000 | 0; 2048 | payload.last_scene_id (0x060C) |
| Rapporter un produit image stocké. | `PAYLOAD_DOWNLOAD_IMAGE` | 29 (0x1D) | scene_id:uint16 | 0 … 65535 | 0 | — |
| Supprimer une image donnée de la mémoire de la charge utile | `PAYLOAD_DELETE_IMAGE` | 30 (0x1E) | scene_id:uint16 | 0 … 65535 | 0 | — |
| Marquer un segment mémoire comme inutilisable | `PAYLOAD_MARK_BAD_SEGMENT` | 31 (0x1F) | segment_id:uint8 | 0 … 7 | 0 | payload.mem_segments_bad (0x0612) |
| Demander le catalogue des images stockées. | `PAYLOAD_GET_IMAGE_CATALOG` | 32 (0x20) | aucun argument | — | — | — |
| Régler le masque d'activation des bandes spectrales | `PAYLOAD_SET_BAND_CONFIG` | 33 (0x21) | mask:uint8 | 1 … 15 | 15 | payload.band_enable_mask (0x0625) |
| Régler les temps d'intégration du détecteur par bande. | `PAYLOAD_SET_INTEGRATION_TIME` | 34 (0x22) | blue_ms:uint16 x0.01, green_ms:uint16 x0.01, red_ms:uint16 x0.01, nir_ms:uint16 x0.01 | 0.1 … 655.35; 0.1 … 655.35; 0.1 … 655.35; 0.1 … 655.35 | 2.0; 2.0; 2.0; 2.0 | payload.integration_ms (moyenne) (0x0635) |
| Régler le gain du détecteur. | `PAYLOAD_SET_GAIN` | 35 (0x23) | gain:uint16 x0.001 | 0.1 … 10.0 | 1.0 | payload.gain_code (0x0636) |
| Régler la consigne de régulation du refroidisseur thermoélectrique du FPA … | `PAYLOAD_COOLER_SETPOINT` | 36 (0x24) | setpoint:uint16 x0.01 | -20.0 … 0.0 | -15.0 | payload.fpa_setpoint (0x0631) |
| Lancer une séquence d'étalonnage radiométrique (image d'obscurité / champ plat … | `PAYLOAD_START_CALIBRATION` | 37 (0x25) | mode:uint8 | — | 2 | payload.cal_active (0x062A) |
| Abandonner la séquence d'étalonnage | `PAYLOAD_STOP_CALIBRATION` | 38 (0x26) | aucun argument | — | — | — |
| Sélectionner l'algorithme de compression et forcer le taux (auparavant un seul … | `PAYLOAD_SET_COMPRESSION` | 39 (0x27) | algorithm:uint8, ratio:uint8 x0.1 | —; 0.0 … 4.0 | 3; 0.0 | payload.compression_ratio (0x0614) |
| Faire tourner la roue à filtres jusqu'à une position (2 s par pas de 90 deg) | `PAYLOAD_SELECT_FILTER` | 92 (0x5C) | position:uint8 | — | 0 | payload.filter_pos (0x063D) |
| Exécuter un EXERCICE du mécanisme d'obturateur. | `PAYLOAD_CYCLE_SHUTTER` | 93 (0x5D) | cycles:uint8 | 1 … 100 | 1 | payload.shutter_pos (0x063C) |
| Lancer le moteur de transfert d'images de bord pour une scène stockée — le lien … | `PAYLOAD_INITIATE_TRANSFER` | 94 (0x5E) | scene_id:uint16 | 1 … 65535 | 1 | payload.transfer_active (0x062D) |
| Lampe d'étalonnage marche/arrêt (aussi accessible comme équipement S2 0x0602) | `PAYLOAD_CAL_LAMP` | 95 (0x5F) | on:uint8 | — | 0 | payload.cal_lamp_on (0x0615) |

<!-- END GENERATED: payload commandable settings -->
