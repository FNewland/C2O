# Chapitre 10 — Contrôle d'attitude et d'orbite

> **Lectures préalables conseillées.** SMAD4 chap. 11.1 (ADCS) ; Markley et Crassidis, *Fundamentals of Spacecraft Attitude Determination and Control*, chap. 1–3 ; Sidi, *Spacecraft Dynamics and Control*, chap. 4–9 ; ECSS-E-ST-60-10C (performances de contrôle). Ce chapitre utilise l'orbite du chapitre 7 ainsi que le cadre de masse, de puissance et d'interfaces du chapitre 8 ; les relations de moment cinétique des roues de réaction sont démontrées dans la partie V, §V.14.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez en mesure de :

1. expliquer la distinction entre détermination d'attitude et contrôle d'attitude, ainsi que la physique de chaque type de capteur et d'actionneur ;
2. choisir l'architecture matérielle du SCAO en fonction des exigences de pointage ;
3. calculer un bilan d'erreurs de pointage par combinaison quadratique (RSS, *root-sum-square*) ;
4. calculer les couples perturbateurs dus au gradient de gravité, à la traînée aérodynamique, à la pression de radiation solaire et au dipôle magnétique résiduel ;
5. dimensionner les actionneurs (roues de réaction, magnétocoupleurs) pour l'environnement de perturbations calculé, à l'aide d'équations détaillées ;
6. expliquer la physique du stockage du moment cinétique, de la saturation et de la désaturation ;
7. comparer actionneurs gyroscopiques (CMG) et roues de réaction, et préciser quand chacun est approprié ;
8. vérifier une conception de SCAO par rapport à son exigence de pointage.

---

## 10.1 Principes du SCAO

*[Source : SMAD, chap. 11.1 ; Markley et Crassidis, chap. 1–3]*

Le système de contrôle d'attitude et d'orbite (SCAO ; AOCS sur la console) assure deux fonctions distinctes :

| Fonction | Objet | Matériel |
|----------|---------|---------|
| **Détermination d'attitude** (AD) | Connaître l'orientation de l'engin spatial par rapport à un repère de référence | Capteurs : senseur stellaire, senseurs solaires, magnétomètre, gyroscope, senseur terrestre, récepteur GPS |
| **Contrôle d'attitude** (AC) | Modifier ou maintenir l'orientation de l'engin spatial | Actionneurs : roues de réaction, magnétocoupleurs, propulseurs, actionneurs gyroscopiques |

**L'état d'attitude :** l'attitude d'un engin spatial est son orientation dans l'espace 3D par rapport à un repère de référence (en général le repère inertiel géocentrique J2000 ou, pour les missions à pointage nadir, le repère orbital local verticale locale/horizontale locale). L'attitude est décrite par une rotation (quaternion, matrice des cosinus directeurs ou angles d'Euler) et par la vitesse angulaire $\vec{\omega}$. La dynamique est régie par l'équation d'Euler du mouvement de rotation :

$$\mathbf{I} \dot{\vec{\omega}} + \vec{\omega} \times (\mathbf{I} \vec{\omega}) = \vec{T}_{\text{external}} + \vec{T}_{\text{control}}$$

où $\mathbf{I}$ est le tenseur d'inertie de l'engin spatial, $\vec{T}_{\text{external}}$ la somme des couples perturbateurs et $\vec{T}_{\text{control}}$ le couple des actionneurs. Le terme $\vec{\omega} \times (\mathbf{I} \vec{\omega})$ représente le couplage gyroscopique : une rotation autour d'un axe peut induire un mouvement autour des autres axes si le tenseur d'inertie n'a pas une symétrie sphérique.

La boucle fermée est la même pour toutes les architectures de ce chapitre (figure 10.1) : les capteurs mesurent, un estimateur fusionne les mesures en une estimation d'attitude et de vitesse angulaire, un correcteur calcule le couple nécessaire pour ramener l'erreur à zéro et les actionneurs l'appliquent à l'engin spatial, tandis que les couples perturbateurs du §10.2 s'y opposent.

![Schéma fonctionnel de la boucle de commande du SCAO : attitude de consigne, correcteur, actionneurs, dynamique de l'engin spatial avec injection des couples perturbateurs, capteurs et estimateur à filtre de Kalman dans la boucle de retour.](../assets/figures/fig_aocs_loop.png)

**Figure 10.1** — La boucle fermée du SCAO. Le correcteur transforme l'écart entre l'attitude commandée et l'attitude estimée en demande de couple, les actionneurs l'appliquent, et l'équation d'Euler régit la réponse de l'engin spatial, avec les couples perturbateurs externes injectés au niveau du système commandé. Les capteurs mesurent l'attitude vraie avec du bruit et un biais, et un estimateur à filtre de Kalman fusionne ces mesures en une estimation d'attitude et de vitesse angulaire renvoyée au comparateur.

### 10.1.1 Capteurs d'attitude — principes de fonctionnement

Les produits commerciaux cités dans ce chapitre sont des exemples représentatifs, et non des recommandations ; les prix sont indicatifs (2026).

#### Senseurs stellaires

Le senseur stellaire est le capteur d'attitude le plus précis disponible : il fournit une connaissance absolue de l'attitude avec une précision de l'ordre de la seconde d'arc.

**Principe de fonctionnement :**

1. Un détecteur CMOS ou CCD (en général de 1024 × 1024 à 2048 × 2048 pixels) image une portion du ciel à travers un objectif grand angle (champ de vue typique de 15–25°).
2. Le processeur de bord détecte les sources ponctuelles brillantes (étoiles) dans l'image et calcule la position de leur barycentre avec une précision inférieure au pixel par ajustement gaussien.
3. Le processeur compare la configuration observée des positions d'étoiles à un catalogue stellaire embarqué (en général Hipparcos ou Tycho-2, contenant 3 000–10 000 étoiles, stockées dans un arbre k-d ou une table de hachage pour une recherche rapide).
4. L'algorithme dit « lost in space » identifie la configuration d'étoiles sans aucune connaissance préalable de l'attitude (première acquisition), en 1–5 secondes en général.
5. Une fois la configuration identifiée, le processeur calcule le quaternion de rotation du repère du catalogue (inertiel) vers le repère de la caméra (repère satellite).
6. En mode poursuite, le processeur suit d'image en image les étoiles connues et fournit des mises à jour à 1–10 Hz avec une précision de 3–10 secondes d'arc (1σ, par axe).

**Caractéristiques principales :**

| Paramètre | Senseur stellaire typique de CubeSat | Senseur stellaire de gros engin spatial |
|-----------|------------------------------|----------------------|
| Précision (1σ, axe de visée) | 5–15″ | 0,5–3″ |
| Précision (1σ, roulis) | 30–100″ | 5–20″ |
| Champ de vue | 10–15°, circulaire | 15–25°, circulaire |
| Fréquence de mise à jour | 2–5 Hz | 5–20 Hz |
| Sensibilité | Étoiles jusqu'à la magnitude 6–7 | Étoiles jusqu'à la magnitude 8–10 |
| Masse | 50–350 g | 1–5 kg |
| Puissance | 0,5–2 W | 5–15 W |
| Produits | Blue Canyon NST (350 g), Sinclair SS-411 (90 g), CubeSpace CubeStar (50 g) | Sodern Hydra, Leonardo AA-STR |

*[Source : fiches techniques de senseurs stellaires des fabricants ; ECSS-E-ST-60-20C]*

**Zones d'exclusion :** un senseur stellaire ne peut pas fonctionner lorsque des objets brillants se trouvent dans son champ de vue ou à proximité :

- **Soleil :** angle d'exclusion typique de 25–45° (la lumière solaire directe sature le détecteur et peut endommager définitivement certains types de capteurs) ;
- **Terre (limbe éclairé) :** angle d'exclusion typique de 25–35° (la luminosité de la Terre noie le signal des étoiles) ;
- **Lune :** angle d'exclusion typique de 10–15° ;
- **Lumière parasite :** les réflexions internes sur la structure voisine de l'engin spatial peuvent créer de fausses étoiles.

**Conséquence pour la conception de la mission :** pour un engin spatial à pointage nadir en LEO, la Terre se trouve toujours à moins de ~65° d'un hémisphère. Le senseur stellaire doit être monté sur une face qui n'est jamais orientée vers la Terre (en général la face zénith ou la face opposée au vecteur vitesse). Si le Soleil est proche du plan orbital (angle β voisin de 0, chapitre 7, §7.1.2), le senseur stellaire peut être périodiquement ébloui. Deux senseurs stellaires montés sur des faces différentes assurent la redondance et suppriment les lacunes dues aux zones d'exclusion d'un seul axe. Ces contraintes sont des interfaces de type O dans la matrice N² du chapitre 8.

**Pourquoi les senseurs stellaires sont les plus précis :** les autres capteurs mesurent des vecteurs dirigés vers des objets particuliers (Soleil, Terre, champ magnétique) ; chacun ne fournit que 2 des 3 degrés de liberté de l'attitude (la direction, mais pas le roulis autour de ce vecteur). Un senseur stellaire mesure simultanément plusieurs directions d'étoiles et fournit ainsi une attitude complète sur 3 axes à partir d'une seule mesure. La précision est limitée par la diffraction optique, le bruit de calcul du barycentre et la précision du catalogue, trois facteurs extrêmement bien caractérisés.

#### Senseurs solaires

Les senseurs solaires déterminent la direction du Soleil et fournissent une information d'attitude sur 2 axes (le vecteur Soleil dans le repère satellite). Ils sont simples, fiables, tolérants aux radiations et peu gourmands en énergie.

**Senseurs solaires grossiers (à photodiodes) :**
Un senseur solaire grossier se compose d'une ou plusieurs photodiodes placées derrière un masque ou une fenêtre. Le photocourant est proportionnel au cosinus de l'angle d'incidence :

$$I = I_0 \cos\theta$$

Un ensemble de 6 senseurs solaires grossiers (un par face de l'engin spatial) détermine la direction du Soleil avec une précision de 2–5° en comparant les photocourants des différentes faces. La face qui délivre le courant le plus élevé est celle qui fait face au Soleil ; le rapport entre faces adjacentes donne l'angle.

**Senseurs solaires fins (barrette linéaire ou détecteur à quadrants) :**
Un senseur solaire fin utilise un masque à fente placé au-dessus d'une barrette linéaire de photodiodes (à la manière d'un cadran solaire miniature). La lumière solaire traverse la fente et éclaire une position précise de la barrette, qui dépend proportionnellement de l'angle d'incidence. Les senseurs solaires fins atteignent une précision de 0,1–1,0°.

| Type | Précision | Champ de vue | Masse | Puissance | Produits |
|------|----------|-----|------|-------|----------|
| Grossier (photodiode) | 2–5° | ~hémisphère | 1–5 g | < 1 mW | NewSpace NCSS-SA05, Solar MEMS nanoSSOC-A60 |
| Fin (analogique, fente + barrette) | 0,1–0,5° | 60–120° | 5–30 g | 10–50 mW | NewSpace NFSS-411, Solar MEMS nanoSSOC-D60 |
| Numérique (détecteur APS + fente) | 0,01–0,05° | 60–120° | 30–50 g | 50–200 mW | Senseur solaire numérique miniature TNO |

*[Source : fiches techniques de senseurs solaires des fabricants]*

**Pourquoi tout engin spatial a besoin de senseurs solaires :** les senseurs solaires sont les seuls capteurs dont le fonctionnement est garanti quelle que soit l'attitude, quelle que soit la vitesse angulaire et quel que soit l'environnement (LEO, GEO, espace lointain). Ce sont les capteurs principaux du mode survie : lorsque l'engin spatial part en culbutage, que l'OBC redémarre ou que le senseur stellaire est ébloui, les senseurs solaires permettent de déterminer la direction du Soleil et d'orienter les générateurs solaires pour produire de la puissance. Sans senseurs solaires, un engin spatial passé en mode survie risque de ne pas retrouver d'énergie.

#### Magnétomètres

Un magnétomètre mesure le vecteur champ géomagnétique local $\vec{B}$ dans le repère satellite. En comparant le $\vec{B}$ mesuré à un modèle du champ magnétique terrestre (IGRF, *International Geomagnetic Reference Field*) à la position orbitale connue, on peut déterminer l'attitude de l'engin spatial.

**Principe de fonctionnement :**

- **Magnétomètre à vanne de flux (*fluxgate*) :** un noyau ferromagnétique est périodiquement porté à saturation par une bobine d'excitation. La présence d'un champ magnétique extérieur crée une dissymétrie dans la forme d'onde de saturation, détectée par une bobine de mesure. Trois éléments *fluxgate* orthogonaux fournissent le vecteur champ sur 3 axes. Résolution : 1–10 nT. Précision : ±200–500 nT (limitée par la contamination due au dipôle magnétique résiduel de l'engin spatial).
- **Magnétorésistif (AMR/GMR) :** capteurs magnétiques à couches minces. Plus petits et moins chers que les *fluxgates*, mais plus bruités et moins stables. Courants dans les magnétomètres COTS pour CubeSat.

**Détermination d'attitude par magnétomètre :**

- Une mesure magnétométrique unique fournit la direction du champ magnétique dans le repère satellite (2 degrés de liberté, de même qu'un senseur solaire fournit la direction du Soleil).
- La comparaison avec le modèle IGRF donne l'attitude, mais la précision est limitée par l'incertitude du modèle IGRF (~100 nT en LEO), par la contamination due au dipôle magnétique résiduel de l'engin spatial (qui peut dépasser 1000 nT à proximité de l'électronique) et par le fait que chaque mesure ne fournit que 2 degrés de liberté (pas de détermination du roulis autour du vecteur champ).
- Détermination d'attitude par magnétomètre seul : précision de ~5–10°.
- Magnétomètre + senseur solaire (combinés) : précision de ~1–3° (les deux vecteurs indépendants fournissent une solution complète sur 3 axes par la méthode TRIAD ou la méthode q).

**Contamination par le dipôle résiduel :** tout circuit électronique crée un champ magnétique. Les boucles de courant, les aimants permanents des moteurs, les éléments de structure magnétisés et les éléments de batterie contribuent tous au dipôle magnétique résiduel de l'engin spatial, qui contamine la mesure du magnétomètre. Parades : monter le magnétomètre sur un mât déployable (à 10–30 cm de la plateforme), appliquer des pratiques de conception magnétiquement propre (paires torsadées, boucles de courant équilibrées) et effectuer en orbite un étalonnage du dipôle résiduel en comparant les mesures du magnétomètre en éclipse (aucun courant du générateur solaire) et en phase éclairée.

| Paramètre | Magnétomètre typique de CubeSat |
|-----------|------------------------------|
| Plage de mesure | ±60 000 nT (suffisant en LEO : B ~20 000–50 000 nT) |
| Résolution | 10–100 nT |
| Précision (après étalonnage) | 200–1000 nT |
| Masse | 5–30 g |
| Puissance | 10–50 mW |
| Produits | NewSpace NMAG, PNI RM3100, Honeywell HMC5883L |

#### Gyroscopes (gyromètres)

Les gyroscopes mesurent la vitesse angulaire $\vec{\omega}$ et non l'attitude absolue. Ils fournissent une information de vitesse à large bande passante pour les boucles de commande et comblent l'intervalle entre deux mises à jour du senseur stellaire.

**Types utilisés sur les CubeSats :**

- **Gyroscope MEMS :** structure vibrante (diapason ou anneau) dont la force de Coriolis est proportionnelle à la vitesse de rotation. Petit, bon marché (moins de 50 € par axe, à titre indicatif), faible consommation. Dérive de biais : 1–10°/h.
- **Centrale inertielle MEMS (6 axes) :** accéléromètre 3 axes et gyroscope 3 axes combinés. Masse de 5–15 g. Très courante sur les CubeSats.
- **Gyroscope à fibre optique (FOG) :** stabilité bien meilleure (dérive de biais de 0,01–1°/h), mais plus encombrant, plus lourd (200 g et plus) et plus cher. Utilisé sur les CubeSats haut de gamme et les petits satellites.

**Pourquoi les gyroscopes dérivent :** les gyroscopes MEMS présentent un biais non nul (un décalage constant de la vitesse mesurée, même à l'arrêt) qui varie avec la température et le temps. L'intégration de la vitesse angulaire pour obtenir l'attitude ($\theta = \int \omega \, dt$) accumule linéairement cette erreur de biais. Une dérive de biais de 1°/h signifie que l'estimation d'attitude dérive de 1° par heure. Les senseurs stellaires fournissent des corrections d'attitude absolues qui annulent cette dérive : la combinaison senseur stellaire (basse fréquence, absolu) et gyroscope (haute fréquence, relatif) par un filtre de Kalman est l'approche classique pour une détermination d'attitude à hautes performances.

#### Récepteurs GPS pour la détermination d'orbite

Les récepteurs GPS déterminent la **position et la vitesse** de l'engin spatial (détermination d'orbite), et non son attitude (un GPS multi-antennes peut toutefois fournir une attitude grossière).

**Fonctionnement en LEO :**

- Les satellites GPS orbitent à ~20 200 km d'altitude ; les engins spatiaux en LEO orbitent en dessous, à 300–800 km.
- Les signaux GPS se propagent vers le bas à travers l'ionosphère jusqu'au récepteur en LEO.
- Le récepteur doit utiliser un corrélateur spécialisé capable de traiter des décalages Doppler allant jusqu'à ±40 kHz (vitesse relative en LEO ~7,5 km/s contre ~3,9 km/s pour un satellite GPS).
- Précision typique : 5–20 m en position, 0,1–0,5 m/s en vitesse (monofréquence, code C/A).
- GPS bifréquence avec mesure de phase de la porteuse : précision de position submétrique.

**Pourquoi le GPS compte pour le SCAO :** une connaissance précise de l'orbite est nécessaire pour le pointage nadir (savoir où est le « bas » exige de connaître la position), pour la poursuite de cibles au sol, pour l'évaluation du modèle IGRF (la détermination d'attitude par magnétomètre a besoin de la position en entrée) et pour la planification des manœuvres d'orbite.

| Paramètre | Récepteur GPS typique de CubeSat |
|-----------|------------------------------|
| Précision en position | 5–20 m (code C/A) |
| Précision en vitesse | 0,1–0,5 m/s |
| Précision en temps | 100 ns |
| Limite d'altitude | En général 600 km (vérifier que les limites COCOM ont été levées) |
| Masse | 15–30 g |
| Puissance | 0,5–1,0 W |
| Produits | SkyFox Labs piNAV-NG, NovAtel OEM719, Hemisphere V200 |

### 10.1.2 Choix de l'architecture du SCAO selon l'exigence de pointage

| Exigence de pointage | Architecture | Capteurs | Actionneurs | Masse | Puissance | Coût (indicatif, 2026) |
|---------------------|-------------|---------|-----------|------|-------|------|
| > 5° | Magnétique passive | Aucun (ou 1 magnétomètre) | Aimant permanent + barreaux à hystérésis | ~0,05 kg | 0 W | ~2 k€ |
| 2–5° | Amortissement B-dot + pointage magnétique | Magnétomètre 3 axes + senseurs solaires grossiers | Magnétocoupleurs 3 axes | ~0,10 kg | 0,2 W | ~8 k€ |
| 0,1–2° | Active 3 axes (RW + capteurs) | Senseurs solaires fins + magnétomètre + (gyro en option) | 3–4 RW + 3 MTQ pour la désaturation | ~0,50 kg | 2–4 W | ~35 k€ |
| < 0,1° | Pointage fin (RW + senseur stellaire) | Senseur stellaire + senseurs solaires fins + magnétomètre + gyro | 4 RW + 3 MTQ | ~0,80 kg | 3–5 W | ~55 k€ |
| < 0,01° | Pointage très fin | Deux senseurs stellaires + gyro MEMS + senseurs solaires fins + magnétomètre | 4 RW + 3 MTQ | ~1,20 kg | 4–6 W | ~80 k€ |

**Exemples de missions réelles :**

| Mission | Format | Exigence de pointage | Architecture | Masse du SCAO | Capteur clé |
|---------|------------|-------------|-------------|-----------|------------|
| **Astrocast** (3U, IoT) | 3U | ~5° | MTQ + senseurs solaires + magnétomètre | 0,1 kg | Senseurs solaires |
| **Planet SuperDove** (3U+, observation de la Terre) | 3U+ | ~0,1° | 4 RW + ST + 3 MTQ + 6 senseurs solaires | 0,8 kg | Senseur stellaire |
| **CAPSTONE** (12U, navigation cislunaire) | 12U | ~0,05° | 4 RW + ST + senseurs solaires + centrale inertielle | ~1,0 kg | Senseur stellaire + centrale inertielle |
| **ASTERIA** (6U, exoplanètes) | 6U | ~0,003° (10″) | 4 RW + ST + capteur de guidage fin | ~1,2 kg | Caméra de guidage fin spécifique |

*[Source : Pong et al., « ASTERIA: Achieving 10-arcsecond Pointing on a 6U CubeSat », SSC 2018]*

---

## 10.2 Couples perturbateurs

En LEO, quatre couples extérieurs perturbent l'attitude de l'engin spatial. Le SCAO doit les contrer en permanence. Comprendre l'origine et l'ordre de grandeur de chaque perturbation est indispensable pour dimensionner les actionneurs.

*[Source : SMAD, chap. 11.1 ; Sidi, chap. 5 ; Wertz 1999, chap. 11]*

### 10.2.1 Couple de gradient de gravité

**Physique :** un engin spatial en orbite est soumis à un champ gravitationnel non uniforme : la face la plus proche de la Terre est attirée plus fortement que la face opposée. Pour un corps allongé, cette différence d'attraction crée un couple qui tend à aligner le grand axe sur la verticale locale (direction du nadir). C'est le principe de la stabilisation par gradient de gravité.

> **Équation clé — couple de gradient de gravité**
>
> $$T_{gg} = \frac{3\mu}{2a^3} |I_z - I_x| \sin(2\theta)$$
>
> où $\mu = 3.986 \times 10^{14}$ m³/s², $a = R_E + h$ (demi-grand axe en mètres), $I_z$ et $I_x$ sont les moments d'inertie principaux autour des axes de plus grande et de plus petite inertie (kg m²), et $\theta$ est l'angle entre le grand axe et la verticale locale. Le cas le plus défavorable correspond à $\theta = 45°$, pour lequel $\sin(2\theta) = 1$.
>
> Pour un corps tel que $I_z \approx I_x$ (un cube), $T_{gg} \approx 0$ : c'est pourquoi les CubeSats 1U ne subissent qu'un couple de gradient de gravité minime.

### 10.2.2 Couple aérodynamique

**Physique :** aux altitudes LEO (200–600 km), les molécules de l'atmosphère résiduelle heurtent la surface de l'engin spatial. La force s'applique au centre de poussée (cp), qui ne coïncide généralement pas avec le centre de masse (cm). Ce décalage crée un couple.

> **Équation clé — couple aérodynamique**
>
> $$T_{\text{aero}} = \frac{1}{2} \rho v^2 C_D A_{\text{ref}} \, d_{cp-cm}$$
>
> où :
> - $\rho$ = masse volumique de l'atmosphère (kg/m³) ; elle varie de plusieurs ordres de grandeur selon l'altitude, l'activité solaire (F10.7) et l'heure locale :
>   - 300 km : $\rho \approx 2 \times 10^{-11}$ (minimum solaire) à $3 \times 10^{-10}$ (maximum solaire)
>   - 400 km : $\rho \approx 4 \times 10^{-12}$ à $1 \times 10^{-11}$
>   - 500 km : $\rho \approx 6 \times 10^{-13}$ à $5 \times 10^{-12}$
>   - 600 km : $\rho \approx 1 \times 10^{-13}$ à $8 \times 10^{-13}$
> - $v$ = vitesse orbitale (7,61 km/s à 500 km, chapitre 7)
> - $C_D \approx 2.0$–$2.3$ (coefficient de traînée en écoulement moléculaire libre ; 2,2 est la valeur usuelle pour une plaque plane)
> - $A_{\text{ref}}$ = section transversale perpendiculaire à la vitesse (m²)
> - $d_{cp-cm}$ = décalage entre le centre de poussée et le centre de masse (m) ; en général 0,5–5 cm pour un CubeSat, selon la configuration des éléments déployables

### 10.2.3 Couple de pression de radiation solaire

**Physique :** la lumière solaire transporte une quantité de mouvement. Lorsque des photons frappent une surface, ils lui transfèrent de la quantité de mouvement ($p = E/c$ en absorption, $p = 2E/c$ en réflexion spéculaire). La force résultante s'applique au centre de pression solaire, qui peut ne pas coïncider avec le cm.

> **Équation clé — couple de pression de radiation solaire (SRP)**
>
> $$T_{\text{SRP}} = \frac{S}{c} A_s (1 + q) \, d_{sp-cm}$$
>
> où $S = 1361$ W/m², $c = 3 \times 10^8$ m/s, $S/c = 4.54 \times 10^{-6}$ N/m² (pression de radiation solaire à 1 UA), $A_s$ = surface éclairée (m²), $q$ = réflectance de la surface (0 pour un absorbeur parfait, 1 pour un réflecteur spéculaire parfait) et $d_{sp-cm}$ = décalage entre le centre de pression solaire et le centre de masse (m).
>
> **Remarque :** en LEO, le couple de pression de radiation solaire est minuscule comparé aux couples aérodynamique et magnétique. Il devient la perturbation dominante en GEO et dans l'espace lointain (où il n'y a pas d'atmosphère et où le champ magnétique est faible).

### 10.2.4 Couple du dipôle magnétique résiduel

**Physique :** un engin spatial qui possède un moment dipolaire magnétique net $\vec{M}$ (dû aux boucles de courant du câblage, aux aimants permanents des moteurs de roues de réaction, aux composants ferromagnétiques magnétisés) interagit avec le champ magnétique terrestre $\vec{B}$ et subit un couple :

> **Équation clé — couple du dipôle magnétique**
>
> $$\vec{T}_{\text{mag}} = \vec{M} \times \vec{B}$$
>
> Module : $T_{\text{mag}} = M \cdot B \cdot \sin\alpha$
>
> où $M$ = moment dipolaire magnétique résiduel de l'engin spatial (A m²), $B$ = intensité du champ géomagnétique local (T) : en LEO (400–600 km), $B \approx 2$–$5 \times 10^{-5}$ T (maximal près des pôles, minimal près de l'équateur) ; en GEO, $B \approx 1 \times 10^{-7}$ T ; $\alpha$ = angle entre $\vec{M}$ et $\vec{B}$.
>
> **Moments dipolaires résiduels typiques d'un CubeSat :**
>
> | Source | Moment dipolaire (A m²) | Remarques |
> |--------|-------------------------|-------|
> | Moteur de roue de réaction | 0,005–0,02 par roue | Aimants permanents du moteur sans balais |
> | Câblage du générateur solaire | 0,001–0,01 | Boucles de courant entre le générateur solaire et l'EPS |
> | Éléments de batterie | 0,001–0,005 | Nickel du boîtier des éléments |
> | Câbles non blindés | 0,005–0,05 | Dépend du cheminement et de la longueur |
> | **Total (3U typique)** | **0,01–0,10** | Varie fortement selon la conception |
>
> **Pourquoi le couple magnétique domine sur les CubeSats :** l'électronique COTS n'est pas conçue pour la propreté magnétique. Les câblages courts forment des boucles de courant petites mais non compensées. Les moteurs des roues de réaction contiennent des aimants permanents. Il en résulte un dipôle résiduel de 0,01–0,1 A m² qui, dans un champ de 30 µT, produit de $3 \times 10^{-7}$ à $3 \times 10^{-6}$ N m, souvent davantage que les couples de gradient de gravité ou de pression de radiation solaire.

> **Exemple résolu — couples perturbateurs d'EOSat-3U à 500 km**
>
> **Caractéristiques du satellite :** 3U (100 × 100 × 340 mm), masse de 5 kg, $I_z = 0.035$ kg m² (grand axe), $I_x = 0.007$ kg m² (petit axe), $A_{\text{ref}} = 0.034$ m² (face 3U), $d_{cp-cm} = 0.02$ m (le panneau déployable décale le cm par rapport au centre géométrique). Orbite : $a = 6878.137$ km, $v = 7613$ m/s (chapitre 7, §7.2).
>
> **Gradient de gravité** (cas le plus défavorable, $\theta = 45°$) :
> $T_{gg} = \dfrac{3 \times 3.986 \times 10^{14}}{2 \times (6.878 \times 10^{6})^3} \times |0.035 - 0.007| \times 1 = \dfrac{1.196 \times 10^{15}}{6.508 \times 10^{20}} \times 0.028 = 1.84 \times 10^{-6} \times 0.028 = 5.1 \times 10^{-8}$ N m
>
> **Aérodynamique** (à 500 km, minimum solaire, $\rho \approx 6 \times 10^{-13}$ kg/m³) :
> $F_{\text{aero}} = 0.5 \times 6 \times 10^{-13} \times 7613^2 \times 2.2 \times 0.034 = 1.30 \times 10^{-6}$ N
>
> $T_{\text{aero}} = F_{\text{aero}} \times d_{cp-cm} = 1.30 \times 10^{-6} \times 0.02 = 2.6 \times 10^{-8}$ N m
>
> Remarque : au maximum solaire ($\rho \approx 5 \times 10^{-12}$), cette valeur est multipliée par ~8 et atteint $2.2 \times 10^{-7}$ N m.
>
> **Pression de radiation solaire :**
> $F_{\text{SRP}} = \dfrac{1361}{3 \times 10^8} \times 0.034 \times 1.5 = 2.31 \times 10^{-7}$ N
>
> $T_{\text{SRP}} = F_{\text{SRP}} \times d_{sp-cm} = 2.31 \times 10^{-7} \times 0.02 = 4.6 \times 10^{-9}$ N m
>
> **Dipôle magnétique résiduel** ($M = 0.05$ A m², $B = 3 \times 10^{-5}$ T) :
> $T_{\text{mag}} = 0.05 \times 3 \times 10^{-5} = 1.5 \times 10^{-6}$ N m
>
> **Synthèse :**
>
> | Source | Couple (N m) | Rang | Remarques |
> |--------|-------------|------|-------|
> | Gradient de gravité | $5.1 \times 10^{-8}$ | 3e | Faible, car un 3U est peu allongé |
> | Aérodynamique (minimum solaire) | $2.6 \times 10^{-8}$ | 4e | Multiplié par 8 au maximum solaire |
> | Pression de radiation solaire | $4.6 \times 10^{-9}$ | 5e | Négligeable en LEO |
> | Dipôle magnétique résiduel | $1.5 \times 10^{-6}$ | **1er** | **Domine d'un facteur > 10** |
> | **Total (somme, cas le plus défavorable)** | $\approx 1.6 \times 10^{-6}$ | | Estimation prudente |
> | **Total (RSS)** | $\approx 1.5 \times 10^{-6}$ | | Plus réaliste (sources non corrélées) |
>
> **Constat clé :** sur un CubeSat, le dipôle magnétique résiduel domine en raison de l'électronique COTS et des câblages courts. **La propreté magnétique compte.** Ramener le dipôle résiduel de 0,05 à 0,01 A m² (ce qui est réalisable par un cheminement soigné des câbles, des paires torsadées et une démagnétisation) diviserait la perturbation totale par 5.

---

## 10.3 Actionneurs d'attitude — physique et dimensionnement

### 10.3.1 Roues de réaction — physique du stockage du moment cinétique

Une roue de réaction est un volant d'inertie (en général un anneau en laiton ou en acier de 20–200 g sur un CubeSat) entraîné par un moteur à courant continu sans balais. D'après la troisième loi de Newton, toute variation du moment cinétique de la roue produit sur l'engin spatial un couple égal et opposé :

$$\vec{H}_{\text{total}} = \vec{H}_{\text{spacecraft}} + \vec{H}_{\text{wheels}} = \text{constante}$$

Si la roue accélère ($\Delta H_{\text{wheel}} > 0$), l'engin spatial subit une variation de moment cinétique égale et opposée ($\Delta H_{\text{SC}} = -\Delta H_{\text{wheel}}$), qui le met en rotation. Le couple de commande vaut :

$$T_{\text{control}} = \frac{dH_{\text{wheel}}}{dt} = I_{\text{wheel}} \cdot \dot{\omega}_{\text{wheel}}$$

où $I_{\text{wheel}}$ est le moment d'inertie de la roue et $\dot{\omega}_{\text{wheel}}$ son accélération angulaire.

**Stockage du moment cinétique :** le moment cinétique maximal qu'une roue peut stocker est :

$$H_{\text{max}} = I_{\text{wheel}} \times \omega_{\text{max}}$$

Pour une roue de CubeSat représentative de 10 mN m s : $I_{\text{wheel}} \approx 1.5 \times 10^{-5}$ kg m², $\omega_{\text{max}} \approx 6000$ tr/min $= 628$ rad/s, d'où $H_{\text{max}} = 0.0094$ N m s $\approx 10$ mN m s.

**Saturation :** sous l'effet des couples perturbateurs, les roues de réaction absorbent du moment cinétique. Leur vitesse augmente au fil du temps jusqu'à atteindre $\omega_{\text{max}}$ (saturation). À saturation, la roue ne peut plus absorber de moment cinétique dans ce sens et l'autorité de commande est perdue. Le temps nécessaire pour atteindre la saturation à partir d'une vitesse nulle est :

$$t_{\text{sat}} = \frac{H_{\text{max}}}{T_{\text{disturbance}}} = \frac{10 \times 10^{-3}}{1.5 \times 10^{-6}} = 6667 \text{ s} \approx 111 \text{ minutes}$$

Cela représente environ 1,2 orbite : sans désaturation, les roues satureraient donc au bout d'une orbite environ. C'est pourquoi les magnétocoupleurs sont les compagnons indispensables des roues de réaction.

**Le problème du passage par zéro :** lorsqu'une roue de réaction passe par la vitesse nulle (inversion du sens de rotation), le frottement statique des roulements crée une « zone morte » dans laquelle la roue ne peut pas produire un couple régulier et continu. Il en résulte une brève perte d'autorité de commande et une hausse des microvibrations (*jitter*). Parades :

- **Moment cinétique de biais :** faire fonctionner toutes les roues avec une vitesse de biais positive (p. ex. 500 tr/min), de sorte qu'elles ne passent jamais par zéro en fonctionnement normal ;
- **Configuration pyramidale à 4 roues :** la géométrie inclinée fait que chaque roue inverse son sens moins souvent ;
- **Lubrification :** les roulements qualifiés pour l'espace utilisent des lubrifiants solides ou déposés en phase vapeur (MoS₂, Braycote) qui minimisent le frottement statique.

**Microvibrations (*jitter*) :** le balourd d'une roue de réaction (dissymétrie de masse du volant) crée des vibrations à la fréquence de rotation et à ses harmoniques. Pour les missions d'imagerie, ces microvibrations dégradent la qualité des images. Leur amplitude dépend de la vitesse de la roue, de la masse du balourd et de la fonction de transfert structurale de l'engin spatial. Microvibrations typiques des roues de réaction de CubeSat : 5–20 secondes d'arc au niveau de la charge utile, selon l'isolation.

### 10.3.2 Configurations de roues de réaction

| Configuration | Description | Avantages | Inconvénients | Utilisation |
|--------------|------------|------|------|-----|
| **3 orthogonales** | Une roue par axe du repère satellite (X, Y, Z) | Masse minimale, commande simple | Aucune redondance ; la défaillance d'une roue entraîne la perte du contrôle sur 1 axe | Missions à bas coût et à courte durée de vie |
| **3 + 1 inclinée** | 3 roues orthogonales + 1 sur un axe incliné (p. ex. direction [1,1,1]) | Tolérance à une panne ; la roue inclinée et les 2 roues restantes assurent le contrôle sur 3 axes | Répartition de la loi de commande un peu plus complexe | **Standard pour les CubeSats** |
| **Pyramide à 4 roues** | 4 roues inclinées de ~20–30° par rapport aux axes du satellite, disposées symétriquement | Répartition optimale du couple et du moment cinétique ; tolérance à une panne ; moins de passages par zéro | Montage plus complexe, plus lourd | Missions à hautes performances, engins spatiaux agiles |

La figure 10.2 montre la géométrie de la pyramide à quatre roues : chaque axe de rotation est relevé de l'angle d'inclinaison β au-dessus du plan X–Y du satellite, et les quatre axes sont espacés de 90° en azimut, le long de ±X et ±Y.

![Pyramide de quatre roues de réaction : vue oblique du repère satellite avec les quatre axes de rotation inclinés, et vue de dessus montrant l'espacement de 90° en azimut.](../assets/figures/fig_rw_pyramid.png)

**Figure 10.2** — Géométrie de la pyramide à quatre roues, tracée pour β = 30°. À gauche : les quatre axes de rotation des roues w1–w4, chacun relevé de l'angle d'inclinaison β au-dessus du plan X–Y du satellite ; à droite : la vue selon +Z, qui montre l'espacement de 90° en azimut le long de +X, +Y, −X et −Y. Le vecteur unitaire de chaque axe de rotation dans le repère satellite est la colonne correspondante de la matrice de répartition $\mathbf{D}$ ci-dessous ; avec les quatre roues en fonctionnement, la capacité de couple vaut donc $2\cos\beta$ fois celle d'une roue seule autour de X ou de Y, et $4\sin\beta$ fois autour de Z.

La **matrice de répartition** fait correspondre les couples des roues aux couples dans le repère satellite :

$$\vec{T}_{\text{body}} = \mathbf{D} \cdot \vec{T}_{\text{wheels}}$$

Pour une pyramide à 4 roues d'angle d'inclinaison $\beta$ (il s'agit ici de l'inclinaison des roues, et non de l'angle β de l'orbite) :

$$\mathbf{D} = \begin{bmatrix} \cos\beta & 0 & -\cos\beta & 0 \\ 0 & \cos\beta & 0 & -\cos\beta \\ \sin\beta & \sin\beta & \sin\beta & \sin\beta \end{bmatrix}$$

> **Équations clés — dimensionnement des roues de réaction**
>
> **Exigence de couple** (pour contrer les perturbations et assurer la capacité de basculement) :
> $$T_{\text{RW,min}} \geq k \times T_{\text{disturbance,total}}$$
> où $k \geq 2$ est le facteur de marge de commande (en général 2–5, pour garantir une bande passante de commande et des performances de basculement suffisantes).
>
> **Exigence de stockage du moment cinétique** (accumulation entre deux cycles de désaturation) :
> $$H_{\text{required}} = T_{\text{disturbance}} \times \frac{t_{\text{desat}}}{2}$$
> où $t_{\text{desat}}$ est l'intervalle entre deux désaturations par les magnétocoupleurs (en général d'une demi-orbite à une orbite). Le facteur ½ correspond à la moyenne (des couples perturbateurs sinusoïdaux ont pour moyenne la moitié de leur valeur crête sur un quart d'orbite).
>
> **Vitesse de basculement** (missions agiles ou d'imagerie) :
> $$\dot{\theta}_{\text{max}} = \frac{H_{\text{RW,max}}}{I_{\text{axis}}}$$
>
> Pour un CubeSat 3U équipé d'une roue de 10 mN m s, avec $I_{\text{axis}} = 0.035$ kg m² :
> $\dot{\theta}_{\text{max}} = 0.010 / 0.035 = 0.286$ rad/s $= 16.4°$/s, ce qui est plus que suffisant pour basculer d'une cible à l'autre.
>
> **Durée de basculement pour un angle donné** (limitée par le couple, profil de vitesse triangulaire) :
> $$t_{\text{slew}} = 2\sqrt{\frac{\theta_{\text{slew}} \cdot I_{\text{axis}}}{T_{\text{RW}}}}$$
>
> Pour un basculement de 90° (1,57 rad) avec $T = 1.0$ mN m et $I = 0.035$ kg m² :
> $t_{\text{slew}} = 2\sqrt{\dfrac{1.57 \times 0.035}{0.001}} = 2\sqrt{54.95} = 14.8$ s
>
> Cette formule suppose que la roue n'atteint jamais sa limite de moment cinétique pendant le basculement ; si $T_{\text{RW}} \cdot t_{\text{slew}}/2 > H_{\text{max}}$, le basculement devient limité par le moment cinétique et l'engin spatial tourne sur son erre à $\dot{\theta}_{\text{max}}$ pendant la partie centrale, ce qui allonge la durée.

> **Exemple résolu — dimensionnement des roues de réaction d'EOSat-3U**
>
> **Données :** $T_{\text{disturbance}} = 1.5 \times 10^{-6}$ N m (voir le §10.2), intervalle de désaturation = 1 orbite (5677 s), exigence de pointage = 0,1°, exigence de basculement = 90° en moins de 60 s.
>
> **Exigence de couple :**
> $T_{\text{RW,min}} = 3 \times 1.5 \times 10^{-6} = 4.5 \times 10^{-6}$ N m $= 0.0045$ mN m
>
> L'exigence de couple est très faible. La plus petite roue disponible pour CubeSat (0,23 mN m) la dépasse d'un facteur 50. Le facteur dimensionnant est en réalité la vitesse de basculement et le stockage du moment cinétique, et non le couple de rejet des perturbations.
>
> **Stockage du moment cinétique :**
> $H_{\text{required}} = 1.5 \times 10^{-6} \times \dfrac{5677}{2} = 4.26 \times 10^{-3}$ N m s $= 4.26$ mN m s
>
> **Vérification de la durée de basculement avec des roues candidates** (exemples représentatifs, et non des recommandations) :
>
> | Classe de produit | Couple (mN m) | Moment cinétique (mN m s) | Masse (g) | Basculement de 90° (s) | Marge de moment cinétique |
> |---------|--------------|-------------------|----------|----------------|-----------------|
> | Micro-roue (p. ex. Hyperion RW-0.01) | 0,23 | 1,0 | 30 | ≈ 59 s (limité par le moment cinétique : la limite de 1 mN m s est atteinte après 4,3 s et le basculement se poursuit sur l'erre à 1,6°/s) | −3,26 mN m s (ÉCHEC) |
> | Petite roue (p. ex. Blue Canyon RW210) | 1,0 | 10 | 55 | 14,8 s | +5,74 mN m s (135 %) |
> | Petite roue (p. ex. CubeSpace RW3-1.0) | 1,0 | 15 | 50 | 14,8 s | +10,74 mN m s (252 %) |
> | Roue moyenne (p. ex. Blue Canyon RW400) | 4,0 | 40 | 120 | 7,4 s | +35,74 mN m s (839 %) |
>
> La micro-roue ne satisfait pas l'exigence de stockage du moment cinétique (elle saturerait bien avant une orbite) et l'exigence de basculement n'est tenue que de justesse. La petite roue de 10 mN m s offre une marge de 135 % et un basculement en 14,8 s. **Choix retenu : roue de la classe 10 mN m s.**
>
> **Configuration :** 4 roues (3 + 1 inclinée) pour la tolérance à une panne. Masse totale des roues : 4 × 55 g = 220 g.

### 10.3.3 Magnétocoupleurs — physique de la production d'un couple magnétique

Un magnétocoupleur (MTQ) n'est rien d'autre qu'une bobine de fil (ou un barreau ferromagnétique entouré de fil). Lorsqu'un courant circule dans la bobine, il crée un moment dipolaire magnétique :

$$\vec{m} = N \cdot I \cdot A \cdot \hat{n}$$

où $N$ = nombre de spires, $I$ = courant (A), $A$ = section de la bobine (m²) et $\hat{n}$ la direction normale à la bobine.

Ce dipôle magnétique interagit avec le champ géomagnétique terrestre $\vec{B}$ pour produire un couple :

$$\vec{T}_{\text{MTQ}} = \vec{m} \times \vec{B}$$

Le couple est **perpendiculaire** à la fois au moment dipolaire et au champ magnétique. Cela a une conséquence capitale : **un magnétocoupleur ne peut pas produire de couple parallèle au vecteur champ magnétique local.** À chaque instant, seuls 2 des 3 axes peuvent recevoir un couple. Sur une orbite complète, la direction du champ tournant, les 3 axes deviennent accessibles, mais jamais simultanément.

**Types de magnétocoupleurs pour CubeSat :**

| Type | Moment dipolaire | Masse | Puissance | Format | Produits |
|------|--------------|------|-------|-------------|----------|
| **Bobine à air** (piste de circuit imprimé) | 0,01–0,05 A m² | 1–5 g | 0,1–0,3 W | Circuit imprimé plat, intégré au substrat du panneau solaire | ZARM Technik MTC-1, sur mesure |
| **Barreau à air** (fil bobiné) | 0,05–0,50 A m² | 10–30 g | 0,2–0,5 W | Cylindrique, 60–100 mm de long | CubeSpace CubeMAG, NewSpace NTQS |
| **Barreau à noyau ferromagnétique** | 0,2–5,0 A m² | 20–100 g | 0,3–1,0 W | Cylindrique à noyau en mu-métal, 60–100 mm de long | ZARM Technik MTQ-1, ISIS iMTQ |

Le noyau ferromagnétique concentre le flux magnétique et fournit 5–20 fois plus de moment dipolaire par unité de courant qu'une bobine à air de même taille. En revanche, un noyau ferromagnétique peut conserver une aimantation rémanente après la mise hors tension, ce qui contribue au dipôle magnétique résiduel de l'engin spatial.

**Pourquoi les magnétocoupleurs ne permettent pas de pointer (seulement d'amortir et de désaturer) :**

Le couple $\vec{T} = \vec{m} \times \vec{B}$ est toujours perpendiculaire à $\vec{B}$. Par conséquent :

1. À un instant donné, il est impossible de produire un couple autour de la direction de $\vec{B}$.
2. La direction du couple disponible change continuellement au fil de l'orbite (car $\vec{B}$ tourne).
3. Le contrôle de pointage exige un couple dans n'importe quelle direction à tout instant, ce que les magnétocoupleurs ne peuvent pas fournir.

Les magnétocoupleurs excellent pour :

- **l'amortissement des vitesses angulaires (*detumbling*) :** la loi de commande B-dot ($\vec{m} = -k \dot{\vec{B}}$) freine la rotation de l'engin spatial en s'opposant à la variation du champ B mesuré. Elle fonctionne quelle que soit l'attitude ;
- **la désaturation :** décharger méthodiquement le moment cinétique des roues de réaction en appliquant le moment dipolaire adéquat : $\vec{m} = -k (\vec{H}_{\text{wheel}} \times \hat{B})$ ;
- **le pointage grossier** (2–10°) : possible dans la durée grâce à une commande prédictive qui planifie les commandes de dipôle sur une orbite complète en exploitant la rotation du champ, mais la précision reste limitée.

> **Équations clés — dimensionnement des magnétocoupleurs**
>
> **Couple de désaturation :**
> $$T_{\text{MTQ}} = m_{\text{dipole}} \times B \times \sin\alpha$$
>
> Couple moyen sur une orbite (compte tenu de la variation de $\alpha$) : $T_{\text{MTQ,avg}} \approx 0.7 \times m_{\text{dipole}} \times B_{\text{avg}}$
>
> **Durée de désaturation** (pour décharger une roue à partir de son moment cinétique maximal) :
> $$t_{\text{dump}} = \frac{H_{\text{wheel}}}{T_{\text{MTQ,avg}}}$$
>
> **Exigence de conception :** $t_{\text{dump}}$ doit tenir dans la portion d'orbite où la géométrie du champ est favorable et où aucune prise de vue n'est programmée, c'est-à-dire en pratique nettement moins d'une orbite.

> **Exemple résolu — dimensionnement des magnétocoupleurs d'EOSat-3U**
>
> **Données :** moment cinétique de la roue = 10 mN m s, $B_{\text{avg}} = 3 \times 10^{-5}$ T.
>
> **Option 1 : barreau à air** ($m = 0.2$ A m²) :
> $T_{\text{MTQ,avg}} = 0.7 \times 0.2 \times 3 \times 10^{-5} = 4.2 \times 10^{-6}$ N m
>
> $t_{\text{dump}} = \dfrac{10 \times 10^{-3}}{4.2 \times 10^{-6}} = 2381$ s $\approx 40$ min
>
> Cela représente environ 42 % d'une période orbitale. **Acceptable** : la désaturation peut être programmée une fois par orbite, pendant la portion sans prise de vue.
>
> **Vérification du rejet des perturbations :** le couple moyen des MTQ ($4.2 \times 10^{-6}$ N m) vaut 2,8 fois le couple perturbateur total ($1.5 \times 10^{-6}$ N m). Les MTQ peuvent décharger le moment cinétique plus vite qu'il ne s'accumule. **Conforme.**
>
> **Configuration :** 3 barreaux MTQ, un par axe du repère satellite (X, Y, Z). Cela garantit qu'un couple peut être produit autour de deux axes quelconques à tout instant. Masse totale des MTQ : 3 × 30 g = 90 g.

### 10.3.4 Actionneurs gyroscopiques et roues de réaction

Les **actionneurs gyroscopiques (CMG)** sont un autre type de dispositif d'échange de moment cinétique, utilisé sur les gros engins spatiaux agiles. Un CMG se compose d'un volant d'inertie en rotation monté sur un cardan. Au lieu de modifier la vitesse de la roue (comme une roue de réaction), le CMG modifie la direction du vecteur moment cinétique en faisant tourner le cardan. Il en résulte un couple gyroscopique :

$$T_{\text{CMG}} = H_{\text{wheel}} \times \dot{\delta}$$

où $H_{\text{wheel}}$ est le moment cinétique constant de la roue et $\dot{\delta}$ la vitesse de rotation du cardan.

**L'effet d'amplification du couple :** pour une roue de CMG tournant à grande vitesse ($H = 1$–$100$ N m s), même une rotation lente du cardan ($\dot{\delta} = 1$ rad/s) produit un couple de sortie élevé ($T = 1$–$100$ N m). C'est plusieurs ordres de grandeur de plus qu'une roue de réaction de masse comparable. Les CMG sont des « machines à couple » ; les roues de réaction sont des « machines à moment cinétique ».

| Paramètre | Roue de réaction | CMG (un cardan) |
|-----------|---------------|---------------------|
| Couple de sortie | $T = I_w \dot{\omega}_w$ (faible, 0,001–10 N m) | $T = H_w \dot{\delta}$ (élevé, 0,1–1000+ N m) |
| Complexité de la commande | Simple (consigne de vitesse) | Complexe (évitement des singularités du cardan) |
| Efficacité massique | Couple par kg plus faible | Couple par kg plus élevé (10–100 fois) |
| Mode de défaillance | Usure des roulements, panne du moteur | Blocage de cardan (singularité), usure des roulements |
| Utilisation typique | CubeSats, petits satellites, missions non agiles | Gros satellites agiles, ISS, observation de la Terre avec redépointage rapide |
| Situation pour les CubeSats | Standard (nombreux produits COTS) | Émergente (produits de micro-CMG, prototypes de recherche) |

**Quand utiliser des CMG :** engins spatiaux exigeant des basculements rapides (> 3°/s pour un gros engin spatial) ; moments d'inertie élevés pour lesquels le couple des roues de réaction est insuffisant ; missions exigeant des redépointages fréquents (vidéo depuis l'orbite, observation de la Terre à revisite rapide).

**Quand utiliser des roues de réaction :** CubeSats et petits satellites (couple suffisant, commande plus simple, offre COTS plus large) ; missions aux exigences d'agilité modestes (basculement < 10°/s pour un CubeSat) ; missions à budget contraint (les CMG sont nettement plus chers).

L'ISS utilise quatre CMG de 4600 kg, qui stockent chacun 3500 N m s de moment cinétique, pour maintenir son attitude sans consommer d'ergols. Les satellites d'observation de la Terre Pléiades Neo utilisent des CMG pour redépointer rapidement entre deux bandes de prise de vue.

---

## 10.4 Bilan d'erreurs de pointage

*[Source : ECSS-E-ST-60-10C ; SMAD, chap. 11.1]*

Le bilan d'erreurs de pointage combine toutes les sources d'erreur indépendantes par somme quadratique (RSS) pour déterminer l'incertitude de pointage totale. Il s'agit d'une combinaison statistique qui suppose des erreurs non corrélées et normalement distribuées.

**Taxonomie ECSS des performances de pointage :**

| Terme | Définition | Mesurée sur |
|------|-----------|---------------|
| **APE** (*Absolute Performance Error*, erreur de performance absolue) | Erreur totale entre le pointage réel et le pointage commandé | Une mesure unique |
| **RPE** (*Relative Performance Error*, erreur de performance relative) | Variation du pointage sur une courte durée (microvibrations/stabilité) | Fenêtre de mesure (p. ex. temps d'intégration) |
| **MPE** (*Mean Performance Error*, erreur de performance moyenne) | Biais systématique du pointage | Moyenne à long terme |

Pour la plupart des missions CubeSat, l'APE est l'exigence principale. La RPE compte pour l'imagerie à longue pose (p. ex. la stabilité de 10 secondes d'arc d'ASTERIA sur des poses de 20 minutes).

> **Équations clés — bilan d'erreurs de pointage (RSS)**
>
> $$\theta_{\text{APE}} = \sqrt{\theta_{\text{sensor}}^2 + \theta_{\text{actuator}}^2 + \theta_{\text{alignment}}^2 + \theta_{\text{thermal}}^2 + \theta_{\text{jitter}}^2 + \theta_{\text{orbit}}^2 + \theta_{\text{timing}}^2}$$
>
> Le résultat doit vérifier :
> $$\theta_{\text{APE}} \leq \theta_{\text{requirement}}$$

### 10.4.1 Sources d'erreur — définitions et physique

| Source | Description | Physique | Valeurs typiques (senseur stellaire) | Valeurs typiques (senseur solaire) |
|--------|------------|---------|------------------------------|----------------------------|
| **Précision du capteur** | Bruit de mesure intrinsèque du capteur d'attitude | Bruit de photons, erreur de calcul du barycentre, distorsion optique | 3–15″ (0,001–0,004°) | 0,5–2° |
| **Résolution des actionneurs** | Plus petit incrément de couple commandable ; bande morte de la boucle de commande | Couple de crantage du moteur, quantification de l'électronique de commande, bande passante de la commande | 2–5″ (0,001°) | Sans objet (MTQ : 1–5°) |
| **Connaissance de l'alignement** | Désalignement entre l'axe de visée du capteur et celui de la charge utile, mesuré pendant l'intégration et les essais (I&T) | Tolérances mécaniques, calage, précision du collage, incertitude de mesure | 30–60″ (0,01–0,02°) | 0,5° |
| **Distorsion thermique** | Déformation de la structure sous l'effet des variations de température ; cyclage thermique orbital | Écart de coefficients de dilatation thermique entre matériaux, gradients de température dans la structure | 10–30″ (0,003–0,01°) | 0,1° |
| **Microvibrations** | Vibrations haute fréquence dues aux roues de réaction et aux mécanismes | Forces de balourd des roues à la fréquence de rotation et à ses harmoniques, résonances de la structure | 5–20″ (0,001–0,006°) | Sans objet |
| **Connaissance de l'orbite** | Incertitude sur la position du satellite (influe sur le calcul du vecteur de pointage nadir) | Précision du GPS, erreur de propagation entre deux points GPS | 1–5″ (< 0,001°) | 0,05° |
| **Datation** | Erreur de datation entre la lecture du capteur et la commande de l'actionneur | Synchronisation des horloges, latence des interruptions, délai de communication sur le bus | 1–3″ (< 0,001°) | 0,01° |

La figure 10.3 présente un bilan de pointage sous forme de cascade : chaque contributeur y figure sous forme de barre, les contributeurs étant regroupés en termes de connaissance, de commande et d'alignement, avec les valeurs RSS de chaque groupe et la ligne d'allocation. L'exemple résolu ci-dessous construit le même type de bilan pour EOSat-3U.

![Bilan d'erreurs de pointage en cascade.](../assets/figures/fig_pointing_tree.png)

**Figure 10.3** — Bilan d'erreurs de pointage d'un petit satellite à senseur stellaire et roues de réaction, tracé sous forme de cascade de contributions à 1σ regroupées en termes de connaissance, de commande et d'alignement (valeurs en millidegrés). Les valeurs RSS des groupes et le total RSS sont comparés à l'allocation ; le groupe alignement domine, comme dans l'exemple résolu ci-dessous.

> **Exemple résolu — bilan de pointage d'EOSat-3U (senseur stellaire + roues de réaction)**
>
> | Source d'erreur | Valeur (°) | Valeur (″) | Valeur² (°²) | Remarques |
> |-------------|------------|----------------|---------------|-------|
> | Précision du senseur stellaire | 0,003 | 10,8 | $9.0 \times 10^{-6}$ | Senseur stellaire de classe CubeSat, 1σ sur l'axe de visée |
> | Résolution des roues de réaction | 0,001 | 3,6 | $1.0 \times 10^{-6}$ | Crantage du moteur + bande morte de la commande |
> | Connaissance de l'alignement | 0,020 | 72 | $4.0 \times 10^{-4}$ | **Dominant** : calage à 1 minute d'arc |
> | Distorsion thermique | 0,010 | 36 | $1.0 \times 10^{-4}$ | Structure en aluminium, excursion orbitale de 40 °C |
> | Microvibrations des RW | 0,005 | 18 | $2.5 \times 10^{-5}$ | À 3000 tr/min, sans support d'isolation |
> | Connaissance de l'orbite (GPS) | 0,001 | 3,6 | $1.0 \times 10^{-6}$ | Point GPS toutes les 10 s |
> | Erreur de datation | 0,001 | 3,6 | $1.0 \times 10^{-6}$ | Synchronisation de l'horodatage < 1 ms |
> | **Total RSS** | $\sqrt{5.37 \times 10^{-4}}$ = **0,023°** | **83″** | | |
>
> **Exigence :** 0,1° (3σ), valeur typique pour un imageur de 5 m de GSD à 500 km (où 0,1° correspond à une erreur de pointage d'environ 870 m au sol, soit ~175 pixels pour un capteur de 5 m de GSD).
>
> **Marge :** 0,1 − 0,023 = 0,077° (marge de 77 %) : **confortable**.
>
> **Idée essentielle :** la connaissance de l'alignement (0,020° = 72″) domine le bilan, avec 74 % de la variance RSS. Améliorer la précision du senseur stellaire de 10 à 3 secondes d'arc ferait passer le total RSS de 83 à 82,3 secondes d'arc : une amélioration négligeable. **Concevoir à partir du bilan** signifie investir l'effort sur le terme dominant : un meilleur étalonnage de l'alignement (p. ex. étalonnage en orbite sur des cibles au sol) aurait bien plus d'effet que le remplacement de n'importe quel capteur.
>
> Pour atteindre un pointage < 0,01° (36″), l'alignement doit être amélioré à < 0,005° (18″), ce qui exige un alignement optique de précision pendant l'intégration et les essais et/ou un étalonnage de l'alignement en orbite.

---

## 10.5 Gestion du moment cinétique et désaturation

Les couples perturbateurs font s'accumuler du moment cinétique dans les roues de réaction au fil du temps. Sans gestion, les roues saturent et l'autorité de commande est perdue. La compréhension de ce cycle est indispensable à la conception du SCAO.

**Le cycle de vie du moment cinétique :**

1. **Accumulation :** les couples perturbateurs extérieurs (gradient de gravité, aérodynamique, pression de radiation solaire, magnétique) agissent sur le corps de l'engin spatial. La boucle de commande pilote les roues de réaction pour contrer ces couples, et celles-ci absorbent le moment cinétique. La vitesse des roues augmente (ou diminue) au rythme $\dot{H} = T_{\text{disturbance}}$.

2. **Surveillance :** l'OBC surveille la vitesse des roues. Lorsqu'une roue dépasse un seuil (en général 80 % du maximum), une manœuvre de désaturation est déclenchée.

3. **Désaturation :** l'OBC active les magnétocoupleurs pour produire un couple qui s'oppose au moment cinétique stocké dans les roues. L'algorithme calcule la commande de dipôle optimale :

$$\vec{m}_{\text{cmd}} = -k_d (\vec{H}_{\text{wheel}} \times \hat{B})$$

où $k_d$ est le gain de désaturation et $\hat{B}$ le vecteur unitaire du champ magnétique. Il en résulte un couple $\vec{T} = \vec{m} \times \vec{B}$ orienté de façon à réduire $\vec{H}_{\text{wheel}}$.

4. **Achèvement :** la vitesse des roues revient près de zéro (ou à la vitesse de biais). Le cycle recommence.

La figure 10.4 montre la phase d'accumulation de ce cycle pour le cas EOSat-3U du §10.2, dont le bilan de perturbations est dominé par le dipôle magnétique résiduel plutôt que par la traînée, avec les lignes de saturation de trois tailles de roues, ainsi que le classement en ordre de grandeur des sources de perturbation.

![Accumulation du moment cinétique des roues de réaction et ordres de grandeur des couples perturbateurs.](../assets/figures/fig_rw_momentum.png)

**Figure 10.4** — À gauche : moment cinétique accumulé dans les roues en fonction du nombre d'orbites écoulées depuis la dernière désaturation, pour le cas EOSat-3U du §10.2 (perturbation totale de 1,5 µN m à 500 km), comparé à la capacité de roues de 1, 10 et 40 mN m s ; la bande grisée couvre une incertitude de 0,5 à 1,5 fois sur le dipôle résiduel. La roue de 10 mN m s sature au bout d'une orbite environ, d'où la désaturation une fois par orbite du §10.5. À droite : les couples perturbateurs du §10.2 ; le dipôle magnétique résiduel domine d'un facteur supérieur à dix, ce qui explique que le cas CubeSat soit dominé par le magnétisme plutôt que par la traînée.

**Contraintes de la désaturation :**

- Les MTQ ne peuvent produire un couple que **perpendiculairement** au vecteur champ magnétique local. Ils ne peuvent pas décharger de moment cinétique parallèlement à $\vec{B}$.
- Près de l'équateur magnétique, $\vec{B}$ est presque horizontal (orienté vers le nord). Les MTQ peuvent décharger efficacement le moment cinétique autour des axes de tangage et de roulis, mais pas de lacet.
- Près des pôles magnétiques, $\vec{B}$ est presque vertical. Les MTQ peuvent décharger le tangage et le lacet, mais pas le roulis.
- Sur une orbite complète, la direction du champ tourne suffisamment pour décharger les trois axes. Mais à chaque instant, un axe reste difficilement contrôlable.
- Une stratégie de désaturation répartie (étalant le déchargement sur une orbite complète) est plus efficace qu'un déchargement ponctuel.

**Fréquence de désaturation typique d'un CubeSat :**

- À 500 km, avec une perturbation totale de 1,5 µN m et des roues de 10 mN m s : une désaturation par orbite (toutes les ~95 minutes).
- Durée : 5–15 minutes par cycle.
- Puissance : 0,5–1,5 W pendant la désaturation (3 barreaux MTQ actifs).
- Pendant la désaturation, la précision de pointage se dégrade légèrement (les couples des MTQ perturbent l'attitude). La prise de vue doit être inhibée pendant la désaturation, règle de transition de mode qui relève du ConOps (chapitre 18).

### 10.5.1 Configurations de roues — redondance 3 + 1

La configuration standard à 4 roues assure un contrôle complet sur 3 axes avec une roue de réserve :

- **3 roues** alignées sur les axes X, Y, Z du satellite assurent le contrôle minimal ;
- **la 4e roue**, sur un axe incliné (en général [1,1,1] normalisé, ou angle d'inclinaison de 20–30° par rapport à chaque axe), apporte la redondance et une meilleure répartition du couple ;
- en cas de défaillance d'une roue, les trois restantes (dont la roue inclinée) maintiennent le contrôle sur 3 axes avec une autorité réduite mais suffisante.

**Enveloppe de couple à 4 roues :** avec 4 roues en configuration pyramidale, le couple maximal dans une direction quelconque du repère satellite vaut :

$$T_{\text{max,body}} = \sqrt{2} \cdot T_{\text{wheel}} \approx 1.41 \times T_{\text{wheel}}$$

pour la répartition optimale. C'est mieux que la configuration à 3 roues orthogonales, où $T_{\text{max,body}} = T_{\text{wheel}}$ selon chaque axe.

---

## 10.6 Exemple résolu : stabilisation magnétique passive d'UniSat-1

Retour sur UniSat-1, le démonstrateur 1U du chapitre 1, §1.7 : il ne dispose pas d'un SCAO actif. Il utilise à la place une **stabilisation magnétique passive**, la méthode de contrôle d'attitude la plus simple et la moins chère, qui ne consomme aucune puissance et n'ajoute qu'une masse minime.

**Principe de fonctionnement — physique :**

1. **Aimant permanent :** un petit aimant droit (en général AlNiCo ou NdFeB, ~10–20 g, moment dipolaire $M_p = 0.1$–$1.0$ A m²) est intégré le long d'un axe du satellite (par exemple l'axe Z). Dans le champ magnétique terrestre $\vec{B}$, l'aimant subit un couple de rappel :

$$\vec{T}_{\text{restoring}} = \vec{M}_p \times \vec{B}$$

Ce couple tend à aligner l'axe de l'aimant sur la direction locale du champ, comme l'aiguille d'une boussole s'aligne sur le nord magnétique. Le couple de rappel est maximal lorsque l'aimant est perpendiculaire au champ ($\alpha = 90°$) et nul lorsqu'il lui est aligné ($\alpha = 0$).

Pour $M_p = 0.5$ A m² et $B = 3 \times 10^{-5}$ T : $T_{\text{max}} = 0.5 \times 3 \times 10^{-5} = 1.5 \times 10^{-5}$ N m. C'est ~10 fois plus que n'importe quel couple perturbateur de l'environnement, ce qui garantit un alignement stable.

2. **Barreaux à hystérésis :** deux bandes ou plus d'un matériau magnétique doux (p. ex. Permalloy, HyMu-80, ~5–10 g chacune, dimensions ~60 × 1 × 1 mm) sont montées perpendiculairement à l'aimant permanent. Lorsque le satellite oscille autour de l'équilibre aligné sur le champ, la composante du champ extérieur le long du barreau à hystérésis s'inverse périodiquement, ce qui fait parcourir au matériau du barreau son cycle d'hystérésis B–H. L'aire du cycle d'hystérésis représente l'énergie dissipée sous forme de chaleur dans le matériau du barreau à chaque cycle. Cette dissipation prélève de l'énergie cinétique à l'oscillation du satellite et l'amortit au fil du temps.

L'énergie dissipée par cycle d'oscillation vaut :

$$E_{\text{dissipated}} = V_{\text{rod}} \times \oint H \, dB$$

où $V_{\text{rod}}$ est le volume du barreau et $\oint H \, dB$ l'aire du cycle d'hystérésis. Pour le matériau HyMu-80, la densité d'énergie typique est de ~100 J/m³ par cycle.

**Constante de temps d'amortissement :** du culbutage initial (~10°/s après déploiement) à une oscillation stabilisée (~1–5° d'amplitude), l'amortissement prend en général de quelques heures à quelques jours, selon le matériau et le volume des barreaux à hystérésis et la vitesse de culbutage initiale.

**Performances :**

| Paramètre | Magnétique passive | Active (RW + ST) |
|-----------|-----------------|------------------|
| Précision de pointage | ~10–15° (par rapport au champ B local) | < 0,1° (par rapport au repère inertiel) |
| Temps de stabilisation | Heures à jours après le déploiement | Minutes après la transition de mode |
| Vitesse de culbutage résiduelle | ~1–5°/s (amortie depuis ~10°/s initialement) | < 0,01°/s |
| Puissance | 0 W | 3–5 W |
| Masse | ~30–50 g | 500–800 g |
| Coût (indicatif, 2026) | ~2 k€ | ~55 k€ |
| Modes de défaillance | Démagnétisation (radiations, température) | Panne du moteur, usure des roulements, bogues logiciels |

**Pourquoi cette solution convient à UniSat-1 :** la charge utile, un magnétomètre MEMS, n'exige pas de pointage précis. Elle tire même parti d'un état de rotation lente, qui fournit des mesures du champ magnétique dans plusieurs directions et améliore la qualité des données scientifiques. Le magnétomètre peut mesurer le vecteur champ quelle que soit l'orientation du satellite.

**Aucun bilan de pointage nécessaire :** en l'absence d'exigence de pointage de la charge utile (rappelons que l'arbre fonctionnel d'UniSat-1 au chapitre 6 ne comporte aucune fonction « pointer »), aucun bilan d'erreurs de pointage n'est nécessaire. Cela supprime le senseur stellaire, les roues de réaction, les magnétocoupleurs (en tant qu'actionneurs), les senseurs solaires et les gyroscopes, et retire de la conception le sous-système le plus coûteux et le plus gourmand en puissance.

> **Environnement de perturbations d'un 1U à 400 km :**
>
> | Source | Couple (N m) | Calcul | Remarques |
> |--------|-------------|-------------|-------|
> | Gradient de gravité | ~$1 \times 10^{-8}$ | $\frac{3\mu}{2a^3} \Delta I$ ; $\Delta I \approx 0.001$ kg m² pour un 1U | Faible, car la forme est presque cubique ($I_z \approx I_x$) |
> | Aérodynamique | ~$3 \times 10^{-8}$ | $\frac{1}{2}\rho v^2 C_D A d$ ; $\rho(400 \text{ km}) \approx 5 \times 10^{-12}$ | $\rho$ plus élevée à 400 km qu'à 500 km |
> | Pression de radiation solaire | ~$1 \times 10^{-9}$ | $\frac{S}{c} A (1+q) d$ ; $A = 0.01$ m² | Faible surface |
> | Aimant permanent (rappel) | ~$1 \times 10^{-5}$ | $M_p \times B \times \sin\alpha$ | **Dominant** : c'est LE couple de commande |
>
> Le couple de rappel de l'aimant permanent (~$10^{-5}$ N m) est supérieur de trois ordres de grandeur à l'ensemble des perturbations réunies. Cela garantit que le satellite reste approximativement aligné sur le champ.

**Limite :** la stabilisation magnétique passive aligne le satellite sur le champ magnétique *local*, qui tourne au fil de l'orbite. Le satellite ne pointe ni vers le nadir, ni vers le Soleil, ni vers aucune direction fixe. Pour les missions exigeant un pointage Terre ou une poursuite du Soleil, un SCAO actif est obligatoire. Pour la mission magnétométrique d'UniSat-1, ce n'est pas une limite, c'est un atout.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| AD et AC | Détermination = connaître l'orientation (capteurs) ; contrôle = modifier l'orientation (actionneurs) |
| Senseurs stellaires | Reconnaissance de configurations d'étoiles par rapport à un catalogue ; précision de 3–15″ ; zones d'exclusion (Soleil 25–45°, Terre 25–35°) ; capteur le plus précis |
| Senseurs solaires | Grossiers (photodiode, 2–5°) ou fins (fente + barrette, 0,1°) ; indispensables au mode survie ; tout engin spatial en a besoin |
| Magnétomètres | Mesurent le champ $\vec{B}$ ; comparaison avec le modèle IGRF ; précision de 5–10° seuls ; la contamination par le dipôle résiduel est la principale source d'erreur |
| Récepteurs GPS | Détermination d'orbite (position/vitesse), pas d'attitude ; précision de 5–20 m en LEO ; nécessaires au calcul du pointage nadir |
| Gyroscopes | Mesurent la vitesse angulaire $\vec{\omega}$ ; dérive MEMS de 1–10°/h ; combinés au senseur stellaire par un filtre de Kalman pour une estimation à large bande passante |
| Choix de l'architecture | Dicté par l'exigence de pointage : magnétique passive pour > 5° ; MTQ pour 2–5° ; RW + ST pour < 0,1° |
| Couples perturbateurs | Gradient de gravité, aérodynamique, pression de radiation solaire, dipôle magnétique ; **le dipôle magnétique domine sur les CubeSats** |
| Physique des roues de réaction | $H = I_w \omega_w$ ; $T = dH/dt$ ; la saturation survient lorsque $\omega \rightarrow \omega_{\text{max}}$ ; microvibrations au passage par zéro |
| Dimensionnement des RW | Couple ≥ 2 fois la perturbation ; moment cinétique ≥ accumulation sur une demi-orbite ; vérifier la durée de basculement (limitée par le couple ou par le moment cinétique) |
| Physique des magnétocoupleurs | $\vec{T} = \vec{m} \times \vec{B}$ ; couple toujours perpendiculaire à $\vec{B}$ ; ne permettent pas de pointer, seulement d'amortir et de désaturer |
| Dimensionnement des MTQ | Le couple de désaturation doit dépasser le rythme d'accumulation dû aux perturbations ; durée de déchargement nettement inférieure à une orbite |
| CMG et RW | CMG : amplification du couple ($T = H \dot{\delta}$), pour les gros engins spatiaux agiles ; RW : plus simples, moins chères, standard pour les CubeSats |
| Bilan de pointage | RSS de 7 sources indépendantes ; la connaissance de l'alignement domine généralement ; améliorer le terme dominant |
| Concevoir à partir du bilan | Investir sur la plus petite source d'erreur n'a qu'un effet négligeable sur le total ; se concentrer sur le terme dominant |
| Redondance | 4 roues (3 + 1 inclinée) assurent la tolérance à une panne ; la matrice de répartition fait correspondre les couples des roues aux couples du satellite |
| Gestion du moment cinétique | Les MTQ déchargent le moment cinétique en s'appuyant sur le champ $\vec{B}$ terrestre ; ~une fois par orbite ; 5–15 min ; prise de vue inhibée pendant le déchargement |

## Exercices

1. **Choix de l'architecture.** Pour (a) un CubeSat 3U d'observation de la Terre exigeant un pointage de 0,05°, (b) un relais 6U de stockage et retransmission exigeant un pointage d'antenne de 3° et (c) UniSat-1, choisissez une architecture de SCAO dans le §10.1.2, dressez la liste des capteurs et des actionneurs, et estimez la masse, la puissance et le coût indicatif. Justifiez chaque choix en deux phrases.

2. **Couples perturbateurs.** Calculez les quatre couples perturbateurs pour un CubeSat 6U (12 kg, surface de référence de 0,06 m², $I_z = 0.10$ kg m², $I_x = 0.03$ kg m², décalage cp–cm de 3 cm, dipôle résiduel de 0,08 A m²) à 400 km (maximum solaire) et à 700 km. Classez-les dans chaque cas et déterminez l'altitude à laquelle le couple aérodynamique dépasse le couple magnétique.

3. **Propreté magnétique.** À partir de l'exemple résolu d'EOSat-3U, recalculez le couple perturbateur total, l'exigence de stockage du moment cinétique et le taux d'utilisation de la désaturation si le dipôle résiduel est ramené à 0,01 A m². De combien la roue pourrait-elle être plus petite, et quel gain de masse et de puissance en résulterait-il ?

4. **Dimensionnement des roues de réaction.** Un CubeSat 3U doit effectuer un basculement de 60° en moins de 20 s et maintenir son pointage entre des désaturations espacées d'une orbite, à 550 km. Avec $I_{\text{axis}} = 0.04$ kg m² et une perturbation totale de $2 \times 10^{-6}$ N m, calculez le couple et le moment cinétique requis, puis vérifiez les durées de basculement limitées par le couple et par le moment cinétique pour les classes de roues du §10.3.2. Quelle roue choisissez-vous ?

5. **Basculement limité par le moment cinétique.** Établissez la durée de basculement dans le cas où la roue atteint $H_{\text{max}}$ avant la mi-parcours : montrez que $t_{\text{slew}} = \theta I/H_{\text{max}} + H_{\text{max}}/T_{\text{RW}}$ et vérifiez la valeur de ≈ 59 s indiquée pour la micro-roue au §10.3.2.

6. **Dimensionnement des magnétocoupleurs.** Dimensionnez un ensemble de magnétocoupleurs capable de décharger 15 mN m s de moment cinétique des roues en moins de 25 minutes à 500 km ($B_{\text{avg}} = 3 \times 10^{-5}$ T). Quel moment dipolaire faut-il, quel type de magnétocoupleur du §10.3.3 le fournit, et quel est le coût en énergie par orbite si la désaturation a lieu une fois par orbite ?

7. **Bilan de pointage.** Construisez le bilan de pointage RSS d'un CubeSat 3U d'observation de la Terre équipé d'un senseur solaire fin et d'un magnétomètre (sans senseur stellaire) et de roues de réaction, en utilisant la colonne « senseur solaire » du §10.4.1. Le bilan satisfait-il une exigence de 0,5° ? Identifiez le terme dominant et l'amélioration unique la plus rentable.

8. **Concevoir à partir du bilan.** Dans le bilan de pointage d'EOSat-3U, le terme d'alignement vaut 0,020°. Montrez quantitativement que diviser par deux l'erreur d'alignement réduit davantage le RSS que la suppression de tous les autres termes réunis. Déterminez ensuite la connaissance de l'alignement nécessaire pour satisfaire une exigence de 0,02° (3σ), les autres termes restant inchangés.

9. **Implantation du senseur stellaire.** Un CubeSat 3U à pointage nadir, sur une orbite héliosynchrone de LTAN 10:30, monte son senseur stellaire sur la face zénith. À l'aide des angles d'exclusion du §10.1.1 et du comportement de l'angle β décrit au chapitre 7, §7.1.2, déterminez si le Soleil entre jamais dans la zone d'exclusion, et proposez une seconde face de montage qui élimine toute interruption. Consignez les entrées correspondantes dans la matrice N² du chapitre 8.

10. **Amortissement d'UniSat-1.** Estimez combien de cycles d'oscillation les barreaux à hystérésis d'UniSat-1 (deux barreaux de 60 × 1 × 1 mm, 100 J/m³ par cycle) doivent effectuer pour dissiper l'énergie cinétique de rotation d'un 1U de 1,3 kg ($I \approx 0.002$ kg m²) en culbutage à 10°/s. Si la période d'oscillation est de l'ordre d'une orbite, combien de temps dure la stabilisation, et qu'en résulte-t-il pour le début des opérations scientifiques ?

## Références

1. Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, chap. 11.1 (ADCS). https://www.space.com/smad
2. Markley, F. L. & Crassidis, J. L., *Fundamentals of Spacecraft Attitude Determination and Control*, Springer, 2014. https://link.springer.com/book/10.1007/978-1-4939-0802-8
3. Sidi, M. J., *Spacecraft Dynamics and Control*, Cambridge University Press, 1997, chap. 4–9. https://www.cambridge.org/core/books/spacecraft-dynamics-and-control/82B47C7B6E2AA53BFAADAF26C2A79F14
4. Hughes, P. C., *Spacecraft Attitude Dynamics*, Wiley, 1986 (réimpression Dover 2004). https://store.doverpublications.com
5. Wertz, J. R. & Larson, W. J. (dir.), *Space Mission Analysis and Design*, 3e éd., 1999, chap. 11 (ADCS). https://www.springer.com
6. ECSS, *ECSS-E-ST-60-10C: Control Performance*, 2008. https://ecss.nl/standard/ecss-e-st-60-10c-control-performance/
7. ECSS, *ECSS-E-ST-60-20C Rev.2: Star sensor terminology and performance specification*, 15 mai 2019. https://ecss.nl/standard/ecss-e-st-60-20c-rev-2-star-sensor-terminology-and-performance-specification-15-may-2019/
8. Pong, C. M. et al., « ASTERIA: Achieving 10-arcsecond pointing on a 6U CubeSat », Small Satellite Conference, 2018. https://digitalcommons.usu.edu/smallsat/
9. Blue Canyon Technologies, *XACT ADCS and reaction-wheel datasheets*, 2023 (exemple représentatif). https://www.bluecanyontech.com
10. CubeSpace, *ADCS Product Catalogue*, 2023 (exemple représentatif). https://www.cubespace.co.za
