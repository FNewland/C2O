# Système de contrôle d'attitude et d'orbite (AOCS) d'EOSAT-1 {#eosat-1-attitude-and-orbit-control-system-aocs}

**Référence du document :** EOSAT1-UM-AOCS-003
**Édition :** 2.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Vue d'ensemble {#1-overview}

Le système de contrôle d'attitude et d'orbite (SCAO, position AOCS sur la console) assure la détermination et le
contrôle d'attitude trois axes d'EOSAT-1. Il maintient le pointage nadir pendant les opérations nominales de prise de vue des océans,
réalise l'amortissement des vitesses angulaires après la séparation et prend en charge les manœuvres de basculement pour l'acquisition de
cibles hors nadir. L'OBC exécute le logiciel SCAO de restitution d'orbite (à l'aide du récepteur GPS
de bord). Les manœuvres d'orbite (évitement de collision, compensation limitée de la traînée, poussée de retrait de service en fin de vie) utilisent le module
propulsif 1U à monergol vert (S8, fonctions 108–118), l'AOCS maintenant l'attitude de poussée.

## 2. Configuration matérielle {#2-hardware-configuration}

### 2.1 Capteurs {#21-sensors}

| Capteur                       | Quantité | Fonction                                    |
|-------------------------------|----------|---------------------------------------------|
| Senseur stellaire (zénith)    | 1        | Référence d'attitude de haute précision (face +Z) |
| Senseur stellaire 2 (incliné) | 1        | Référence d'attitude de haute précision (face +Z, inclinée de 45° vers +Y) |
| Magnétomètre 3 axes           | 1        | Attitude grossière et champ magnétique (voie unique) |
| Gyromètres à fibre optique    | 3        | Mesure des vitesses angulaires (axes satellite) |
| Têtes de senseur solaire grossier | 6    | Direction du Soleil pour le mode survie (une par face) |
| Récepteur GPS                 | 1        | Restitution d'orbite (antenne zénith)       |

#### 2.1.1 Magnétomètre (voie unique) {#211-magnetometer-single-string}

EOSAT-1 embarque UN seul magnétomètre fluxgate 3 axes sur un mât court — comme pour les
gyromètres, il n'y a ni rechange ni commutation principal/secours. Une défaillance du magnétomètre est une
dégradation au niveau de la mission (l'amortissement B-dot et la désaturation magnétique sont aveugles
sans lui), et aucun exercice de redondance ne permet de s'en sortir — la réponse consiste à
exploiter en mode dégradé, et non à basculer :

| Paramètre       | Magnétomètre          |
|-----------------|-----------------------|
| Emplacement     | Mât déployé (extrémité) |
| Plage           | +/- 60 µT             |
| Résolution      | 10 nT                 |
| Bruit           | < 50 nT (1 sigma)     |
| Champ mesuré    | `aocs.mag_x/y/z` (0x020B-0D), norme `aocs.mag_field_total` (0x0277) |
| Validité        | `aocs.mag_enabled` (0x025C) : 0 = éteint/défaillant (B vaut 0) |
| Alimentation    | Équipement S2 0x0209 (pas de ligne EPS dédiée) |

Les valeurs mesurées sont celles qu'utilise la loi B-dot : le champ IGRF ramené dans
le repère satellite, plus le biais et le bruit du capteur. Lorsque l'équipement est hors tension, défaillant ou
que l'ensemble AOCS est éteint, les mesures sont mises à zéro — jamais figées — et 0x025C retombe
à 0. La commande MAG_SELECT n'existe plus ; une procédure périmée qui envoie la fonction S8
7 reçoit un refus explicatif (erreur 0x0007).

**En cas de défaillance du magnétomètre :** il n'y a rien sur quoi basculer. Le mode DETUMBLE
devient inefficace (la loi B-dot n'a plus d'entrée), la désaturation magnétique est refusée, et la
détermination grossière TRIAD CSS+MAG se dégrade en une propagation CSS plus gyromètres. Aucune reprise
n'est possible par l'opérateur : la mission se poursuit dans un mode d'attitude dégradé de façon permanente.

#### 2.1.2 Senseurs solaires grossiers — configuration à 6 têtes {#212-coarse-sun-sensors--6-head-configuration}

EOSAT-1 utilise 6 têtes individuelles de senseur solaire grossier (CSS), une montée sur chaque face
du satellite. Chaque tête fournit un courant à réponse en cosinus, fonction de l'angle entre le
vecteur Soleil et la normale à la face :

| Tête CSS | Face | Direction de la normale | ID param. |
|----------|------|------------------|----------|
| CSS-1    | +X   | Le long de la trace | 0x027A |
| CSS-2    | -X   | Opposée à la trace | 0x027B  |
| CSS-3    | +Y   | Transverse à la trace | 0x027C |
| CSS-4    | -Y   | Opposée à la transverse | 0x027D |
| CSS-5    | +Z   | Zénith           | 0x027E   |
| CSS-6    | -Z   | Nadir            | 0x027F   |

Le logiciel AOCS calcule le vecteur Soleil en combinant, par projection géométrique, les réponses de toutes les
têtes CSS éclairées. Au moins deux têtes éclairées sont nécessaires pour
une détermination valide du vecteur Soleil. En éclipse (toutes les têtes dans l'ombre), le vecteur Soleil est propagé
à partir de la dernière mesure valide à l'aide du modèle orbital.

#### 2.1.3 Senseurs stellaires — axes de visée et géométrie des champs de vue {#213-star-cameras--boresights-and-fov-geometry}

EOSAT-1 embarque deux senseurs stellaires, tous deux sur la face zénith (+Z), de sorte qu'aucun ne vise
la Terre en pointage nadir nominal :

| Senseur  | Face | Axe de visée | Demi-angle du FOV | Précision (3 sigma) |
|----------|------|------------|----------------|---------------------|
| ST1 (ST-Zenith) | +Z | Zénith (+Z) | Cône de 15° | 0,05°               |
| ST2 (incliné)   | +Z | À 45° de +Z vers +Y | Cône de 15° | 0,05° |

+Y est le côté opposé au Soleil sur cette orbite (bêta d'environ −21° à −31°) : l'inclinaison éloigne donc ST2
du Soleil lorsque ST1 risque l'éblouissement.

**Zones d'éblouissement :** chaque senseur stellaire est ébloui lorsque le Soleil, le limbe terrestre ou la Lune entre
dans son champ de vue (cône de 15° de demi-angle autour de l'axe de visée) :

| Senseur   | Sources d'éblouissement                                    |
|-----------|------------------------------------------------------------|
| ST1       | Soleil à moins de 15° de la direction du zénith            |
| ST2       | Soleil à moins de 15° de son axe de visée incliné ; limbe terrestre pendant les grands basculements |

En pointage nadir nominal, ST1 est la référence d'attitude principale (il vise à l'opposé de la
Terre) et ST2 sert de secours. Si les deux senseurs sont éblouis simultanément, l'attitude est
propagée à l'aide des gyromètres pendant 60 secondes au plus.

### 2.2 Actionneurs {#22-actuators}

| Actionneur           | Quantité | Fonction                                    |
|----------------------|----------|---------------------------------------------|
| Roues de réaction    | 4        | Contrôle d'attitude fin (3 + 1 redondante)  |
| Magnétocoupleurs     | 3        | Désaturation du moment cinétique et amortissement des vitesses angulaires |

Les quatre roues de réaction sont disposées en pyramide, ce qui assure un contrôle trois axes complet
avec tolérance à une panne. La plage nominale de vitesse des roues est de +/-4000 tr/min ; la limite
jaune est fixée à +/-5000 tr/min afin de conserver une marge avant qu'une désaturation ne soit nécessaire.

## 3. Modes AOCS {#3-aocs-modes}

Les codes de mode suivent le tableau de référence de `configs/eosat1/aocs/aocs_mode_codes.yaml`
(cette section comportait auparavant une numérotation contradictoire à cinq modes ; elle a été
corrigée) :

| ID de mode | Nom du mode | Description                                          |
|---------|-------------|---------------------------------------------------------|
| 0       | OFF         | Aucun contrôle d'attitude ; capteurs et actionneurs hors tension |
| 1       | SAFE_BOOT   | Stabilisation après amorçage, aucun actionnement        |
| 2       | DETUMBLE    | Amortissement des vitesses angulaires par loi B-dot à l'aide des magnétocoupleurs après la séparation |
| 3       | COARSE_SUN  | Pointage solaire à l'aide des CSS + magnétomètre + magnétocoupleurs |
| 4       | NOMINAL     | Suivi nadir LVLH : senseur stellaire + MEKF + roues     |
| 5       | FINE_POINT  | Pointage de haute précision : ST à 4 Hz, les 4 roues, soumis à conditions |
| 6       | SLEW        | Manœuvre à vitesse limitée vers un quaternion cible     |
| 7       | DESAT       | Déchargement du moment cinétique des roues par les magnétocoupleurs, attitude maintenue |
| 8       | ECLIPSE     | Maintien nadir sur la seule connaissance gyrométrique (sans mise à jour ST) |
| 9       | INERTIAL    | Maintien d'un quaternion ECI commandé (étalonnage, stéréo) |

### 3.1 Transitions de mode {#31-mode-transitions}

```
DETUMBLE --> COARSE_SUN --> NOMINAL <--> ECLIPSE
                               |
                               +--> SLEW --> NOMINAL
                               +--> DESAT --> NOMINAL
                               +--> FINE_POINT (gated) / INERTIAL
```

- **De DETUMBLE à COARSE_SUN** : autonome lorsque les vitesses angulaires restent < 0.5 deg/s pendant 30 secondes.
- **De COARSE_SUN à NOMINAL** : autonome dès que les CSS sont valides, que l'erreur d'attitude reste < 10 deg
  pendant 60 s et qu'un senseur stellaire est en TRACKING (ou sur commande sol, mode=4).
- **De NOMINAL à FINE_POINT** : sur commande sol (`AOCS_SET_MODE` mode=5). La commande
  est REFUSÉE avec TM(1,8) tant que le masque de bits de préconditions `aocs.fine_ready`
  (0x02C5) ne vaut pas 0 — utiliser d'abord `AOCS_FINE_READY_CHECK` (fonction 89).
- **De NOMINAL à SLEW** : sur commande sol via `AOCS_SLEW_TO` (fonction 10, mode=6).
- **De NOMINAL à DESAT** : sur commande sol via `AOCS_DESATURATE`, ou de façon autonome lorsque
  l'enveloppe de moment cinétique (0x02BA) dépasse 70 %.
- **De NOMINAL/FINE à ECLIPSE** : autonome à l'entrée en éclipse (anti-rebond de 5 s) ; retour
  en NOMINAL à la sortie d'éclipse.
- Tout mode revient en **COARSE_SUN** lors d'un passage en mode survie déclenché par la FDIR.

## 4. Paramètres de télémesure {#4-telemetry-parameters}

| ID param. | Nom           | Unité    | Description                              |
|----------|----------------|----------|------------------------------------------|
| 0x0200   | quat_q1        | —        | Composante q1 du quaternion d'attitude   |
| 0x0201   | quat_q2        | —        | Composante q2 du quaternion d'attitude   |
| 0x0202   | quat_q3        | —        | Composante q3 du quaternion d'attitude   |
| 0x0203   | quat_q4        | —        | Composante q4 du quaternion d'attitude (scalaire) |
| 0x0204   | rate_roll      | deg/s    | Vitesse angulaire autour de l'axe X      |
| 0x0205   | rate_pitch     | deg/s    | Vitesse angulaire autour de l'axe Y      |
| 0x0206   | rate_yaw       | deg/s    | Vitesse angulaire autour de l'axe Z      |
| 0x0207   | rw1_speed      | tr/min   | Vitesse de la roue de réaction 1         |
| 0x0208   | rw2_speed      | tr/min   | Vitesse de la roue de réaction 2         |
| 0x0209   | rw3_speed      | tr/min   | Vitesse de la roue de réaction 3         |
| 0x020A   | rw4_speed      | tr/min   | Vitesse de la roue de réaction 4         |
| 0x020B   | mag_x          | µT       | Mesure du magnétomètre sur l'axe X       |
| 0x020C   | mag_y          | µT       | Mesure du magnétomètre sur l'axe Y       |
| 0x020D   | mag_z          | µT       | Mesure du magnétomètre sur l'axe Z       |
| 0x020F   | aocs_mode      | enum     | Mode AOCS courant (voir le tableau des modes) |
| 0x0210   | sc_lat         | deg      | Latitude du point subsatellite           |
| 0x0211   | sc_lon         | deg      | Longitude du point subsatellite          |
| 0x0212   | sc_alt         | km       | Altitude orbitale                        |
| 0x0217   | att_error      | deg      | Erreur de pointage d'attitude totale     |
| 0x0218   | rw1_temp       | °C       | Température de la roue de réaction 1     |
| 0x0219   | rw2_temp       | °C       | Température de la roue de réaction 2     |
| 0x021A   | rw3_temp       | °C       | Température de la roue de réaction 3     |
| 0x021B   | rw4_temp       | °C       | Température de la roue de réaction 4     |

## 5. Définition des limites {#5-limit-definitions}

| Paramètre          | Jaune bas  | Jaune haut  | Rouge bas | Rouge haut |
|--------------------|------------|-------------|---------|----------|
| att_error (deg)    | -1         | 1           | -2      | 2        |
| rate_roll (deg/s)  | -0.5       | 0.5         | -2      | 2        |
| rate_pitch (deg/s) | -0.5       | 0.5         | -2      | 2        |
| rate_yaw (deg/s)   | -0.5       | 0.5         | -2      | 2        |
| rw_speed (tr/min)  | -5000      | 5000        | -5500   | 5500     |
| rw_temp (°C)       | 0          | 60          | -5      | 70       |

Une erreur d'attitude persistante supérieure à 1 deg déclenche une alarme jaune. Des erreurs supérieures à 5 deg en
mode NOMINAL conduisent la FDIR à commander une transition vers COARSE_SUN.

## 6. Commandes {#6-commands}

| Commande          | Service  | Paramètres             | Description                          |
|-------------------|----------|------------------------|--------------------------------------|
| AOCS_SET_MODE     | S8,S1    | mode (0–9)             | Régler le mode de fonctionnement de l'AOCS |
| AOCS_DESATURATE   | S8,S1    | —                      | Lancer la manœuvre de désaturation des roues |
| HK_REQUEST        | S3,S27   | sid=2                  | Demander le paquet de servitude AOCS |
| GET_PARAM         | S20,S3   | param_id (0x0200–021B) | Lire un paramètre AOCS individuel    |
| SET_PARAM         | S20,S1   | param_id, value        | Modifier un paramètre de configuration AOCS |

### 6.1 Procédure de désaturation {#61-desaturation-procedure}

1. Vérifier les vitesses de roue actuelles par la HK ou par `GET_PARAM` sur 0x0207–0x020A.
2. Si une roue dépasse +/-4500 tr/min, programmer une désaturation.
3. Envoyer `AOCS_DESATURATE` — l'AOCS passe en mode DESAT (mode=7).
4. Surveiller la convergence des vitesses de roue vers le biais de désaturation de ±200 tr/min (durée
   type : 5–15 min avec le dipôle de 1,6 A·m² des barreaux).
5. L'AOCS revient de manière autonome en NOMINAL à la fin de l'opération.

## 7. Remarques d'exploitation {#7-operational-notes}

1. Chaque senseur stellaire a besoin d'au moins 3 étoiles identifiées pour fournir une solution d'attitude valide.
   À la sortie d'éclipse (éblouissement par le Soleil), l'attitude est propagée à l'aide des seuls gyromètres pendant 60 s au plus.
2. L'étalonnage du biais des gyromètres est une activité commandée depuis le sol (`AOCS_GYRO_CALIBRATION`,
   S8 fonction 13). Préconditions (élément 11 de 2026-08c) : les trois gyromètres sous tension,
   le senseur stellaire sélectionné en TRACKING (>= 5 étoiles) et contribuant effectivement à
   l'estimateur (`aocs.est_source` 0x02C1 bit 0), et des vitesses à moins de 0.10 deg/s de
   la référence. Il n'exige NI le contrôle par les roues NI le mode NOMINAL — un mode
   COARSE_SUN au repos avec le senseur stellaire dans la boucle suffit, ce qui
   permet à COM-003 d'effectuer l'étalonnage avant que COM-004 n'active les roues. Codes de refus
   0x0A01-0x0A08.
3. En mode DETUMBLE, seuls les magnétocoupleurs sont actifs. Les roues de réaction ne servent pas au
   contrôle tant que le mode NOMINAL n'est pas atteint.
4. Le bilan de précision de connaissance d'attitude est de 0,05° (3 sigma) en NOMINAL lorsque le senseur
   stellaire zénith est disponible ; le système de vol atteint typiquement ~0,015° à 3 sigma
   (transmis au sol dans `aocs.knowledge_err_3sig`, 0x02A7).
5. Le magnétomètre est en voie unique (voir la section 2.1.1) ; il n'y a pas de basculement
   ni de commande MAG_SELECT.
6. Le récepteur GPS fournit la position et la vitesse pour la restitution d'orbite. Le logiciel
   SCAO utilise ces données pour la propagation d'orbite, mais n'effectue pas de contrôle d'orbite.

## 8. Séquence de recette du SCAO {#8-adcs-commissioning-sequence}

La séquence de recette du SCAO est réalisée pendant la transition de la LEOP vers les opérations
nominales. Elle suit un ordre strict, afin de vérifier chaque composant avant d'activer le suivant :

| Étape | Activité                         | Prérequis                         | GO/NO-GO |
|------|-----------------------------------|-----------------------------------|----------|
| 1    | Mise sous tension et contrôle de santé des capteurs | OBC en mode APPLICATION | Oui |
| 2    | Étalonnage du magnétomètre        | Magnétomètre sous tension, vitesses < 0.5 deg/s | Oui |
| 3    | Vérification des CSS (les 6 têtes) | Partie éclairée de l'orbite      | Oui      |
| 4    | Recette des senseurs stellaires   | Vitesses < 0.1 deg/s, hors éclipse | Oui    |
| 5    | Étalonnage du biais des gyromètres | ST en poursuite + dans la boucle de l'estimateur (est_source bit 0), vitesses < 0.1 deg/s | Oui |
| 6    | Validation de la détermination d'attitude | Tous les capteurs opérationnels | Oui |
| 7    | Mise sous tension des actionneurs | Détermination validée            | Oui      |
| 8    | Contrôle du signe des magnétocoupleurs | Région de champ magnétique connue | Oui |
| 9    | Essai de mise en rotation des roues de réaction | Magnétocoupleurs vérifiés | Oui |
| 10   | Vérification des gains de commande | Tous les actionneurs vérifiés   | Oui      |
| 11   | Essai d'amortissement des vitesses | Gains vérifiés                  | Oui      |
| 12   | Contrôle d'attitude actif         | Toutes les vérifications réussies | Oui     |

Chaque étape exige un point de contrôle GO/NO-GO. Le directeur de vol lance un tour de table de tous les
postes avant de poursuivre avec l'étape suivante. Voir `09_leop.md` pour les procédures détaillées.

---

*Fin du document — EOSAT1-UM-AOCS-003*
