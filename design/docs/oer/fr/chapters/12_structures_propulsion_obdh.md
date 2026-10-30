# Chapitre 12 — Structures, propulsion et gestion bord des données

> **Lectures préalables conseillées.** Cal Poly, *CubeSat Design Specification* Rev 14.1 ; SMAD4 chap. 11.3 (*Structures*) et chap. 17 (*Propulsion*) ; ECSS-E-ST-32C (*Structural general requirements*) et ECSS-E-ST-35C (*Propulsion general requirements*) ; Sutton et Biblarz, *Rocket Propulsion Elements*, chap. 2–4 ; Sarafin, *Spacecraft Structures and Mechanisms*, chap. 1–3. Ce chapitre clôt la séquence de conception des sous-systèmes : il utilise le ΔV de désorbitation du chapitre 7, §7.5, le bilan de masse et le barème de marges du chapitre 8, §8.4 (tableau 8.3), le bilan de puissance du chapitre 9 et le bilan de données du chapitre 11, §11.9. L'équation de Tsiolkovski et la marge de sécurité structurale sont démontrées dans la partie V, §V.3 et §V.13.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez en mesure de :

1. vérifier la conformité à la *CubeSat Design Specification* (CDS) pour les formats 1U–12U ;
2. expliquer l'environnement de charges structurales (quasi statiques, vibrations, chocs) et ses origines physiques ;
3. calculer la marge de sécurité structurale pour les charges quasi statiques au lancement ;
4. estimer l'exigence de fréquence propre fondamentale et la vérifier par rapport aux spécifications du déployeur ;
5. appliquer l'équation de Tsiolkovski pour calculer la masse d'ergols correspondant à un $\Delta V$ donné ;
6. expliquer la physique de chaque technologie de propulsion et choisir celle qui répond aux exigences de la mission ;
7. choisir l'architecture du calculateur de bord (OBC) en fonction des exigences de traitement, de tenue aux radiations et d'interfaces ;
8. dimensionner le stockage de données à bord à partir du bilan de données ;
9. établir une liste d'équipements à partir des conceptions de sous-systèmes et vérifier que chaque bilan technique boucle.

Les produits commerciaux cités dans ce chapitre sont des exemples représentatifs, et non des recommandations ; les prix sont indicatifs (2026).

---

## 12.1 Structure d'un CubeSat et conformité à la CDS

*[Source : Cal Poly CDS Rev 14.1, février 2022 ; ECSS-E-ST-32C]*

### 12.1.1 Spécifications dimensionnelles de la CDS

| Format | Dimensions (mm) | Masse max. (kg) | Volume interne (cm$^3$) | Déployeur type |
|------------|-----------------|---------------|------------------------|-----------------|
| 1U | 100 × 100 × 113,5 | 2,0 | ~1000 | ISIPOD, P-POD |
| 1,5U | 100 × 100 × 170,2 | 3,0 | ~1500 | ISIPOD |
| 2U | 100 × 100 × 227,0 | 4,0 | ~2000 | ISIPOD, P-POD |
| 3U | 100 × 100 × 340,5 | 6,0 | ~3000 | P-POD, ISIPOD, NanoRacks NRCSD |
| 6U | 100 × 226,3 × 366,0 | 12,0 | ~6000 | Déployeur 6U (Exolaunch, D-Orbit) |
| 12U | 226,3 × 226,3 × 366,0 | 24,0 | ~12000 | Déployeur 12U (Exolaunch) |

La figure 12.1 représente à l'échelle l'enveloppe d'un 3U, avec les éléments dont dépend l'interface avec le déployeur : les rails, leurs patins de contact, les interrupteurs de déploiement, l'accès à la goupille *remove-before-flight*, la tolérance de protubérance entre les rails et la limite de position du centre de gravité.

![Enveloppe d'un CubeSat 3U selon la CDS Rev 14, en vue latérale et en vue de bout, avec les rails, les patins de contact, les interrupteurs de déploiement, l'accès à la goupille RBF, l'enveloppe de protubérance et le domaine du centre de gravité.](../assets/figures/fig_cds_envelope.png)

**Figure 12.1** — Enveloppe d'un CubeSat 3U selon la *CubeSat Design Specification* Rev 14, tracée à l'échelle (cotes en mm). À gauche, vue latérale : le corps de 100 × 100 × 340,5 mm avec ses quatre rails anodisés durs, les patins de contact en bout de rail qui portent sur le déployeur, les deux interrupteurs de déploiement aux extrémités −Z des rails, l'accès à la goupille *remove-before-flight* et la limite de 2 cm autour du centre géométrique pour le centre de gravité. À droite, vue de bout : les sections de rail de 8,5 × 8,5 mm et l'enveloppe de protubérance de 6,5 mm autorisée sur les faces ±X et ±Y entre les rails en configuration repliée.

### 12.1.2 Matériaux de structure

**Matériau des rails de CubeSat : aluminium 7075-T6**

C'est l'alliage d'aluminium de structure le plus couramment spécifié pour les rails de CubeSat. La CDS impose de l'aluminium anodisé dur pour les rails (les quatre arêtes porteuses qui coulissent dans les glissières du déployeur).

| Propriété | Al 7075-T6 | Al 6061-T6 | Ti-6Al-4V | PRFC (quasi isotrope) |
|----------|-----------|-----------|-----------|----------------------|
| Masse volumique (kg/m$^3$) | 2810 | 2700 | 4430 | 1600 |
| Limite d'élasticité $\sigma_y$ (MPa) | 503 | 276 | 880 | S. O. (utiliser la résistance à la rupture) |
| Résistance à la rupture $\sigma_u$ (MPa) | 572 | 310 | 950 | 500–800 |
| Module d'Young $E$ (GPa) | 71,7 | 68,9 | 114 | 70–150 (selon la direction) |
| CTE (ppm/°C) | 23,6 | 23,1 | 8,6 | 0–2 (ajustable) |
| Conductivité thermique (W/m/K) | 130 | 167 | 6,7 | 3–10 |

*[Source : MMPDS / ASM Handbook ; fiches techniques Hexcel HexPly]*

**Pourquoi l'Al 7075-T6 pour les rails :**
- rapport résistance/masse élevé (supérieur à celui du 6061-T6) ;
- l'anodisation dure fournit un état de surface durable et à faible frottement pour le contact avec les glissières du déployeur (elle réduit le grippage et assure l'isolation électrique) ;
- bonne usinabilité ;
- héritage en vol considérable (pratiquement tous les CubeSats lancés à ce jour) ;
- CTE adapté à celui de la structure en aluminium du déployeur (évite le coincement dû à la dilatation thermique différentielle).

**Pourquoi pas d'autres matériaux pour les rails :**
- **Titane :** excellente résistance, mais faible conductivité thermique (points chauds), usinage difficile, risque de grippage contre le déployeur en aluminium.
- **PRFC :** ne peut pas être anodisé ; l'écart de CTE avec le déployeur en aluminium provoque un coincement aux températures extrêmes ; faible conductivité électrique (problèmes de mise à la masse et de métallisation).
- **Acier inoxydable :** trop lourd ; mauvaise adaptation du CTE.

**Physique de l'anodisation :** l'anodisation est un procédé électrochimique qui fait croître une couche dure d'oxyde d'aluminium ($\text{Al}_2\text{O}_3$) en surface. L'anodisation dure (type III) produit une couche d'oxyde de 25–75 µm d'épaisseur, d'une dureté de 60–70 HRC (plus dure que la plupart des aciers). Cette couche assure la résistance à l'usure au contact du déployeur, l'isolation électrique (elle évite les arcs entre le satellite et le déployeur), la résistance à la corrosion et des propriétés optiques de surface maîtrisées ($\alpha_s \approx 0.3$–$0.5$, $\varepsilon \approx 0.8$–$0.85$ pour une anodisation incolore ; $\alpha_s \approx 0.9$, $\varepsilon \approx 0.85$ pour une anodisation noire ; voir le chapitre 9, §9.4).

### 12.1.3 Principales exigences de la CDS

| Exigence | Spécification | Justification physique |
|------------|---------------|-------------------|
| Matériau des rails | Aluminium anodisé dur (7075-T6 ou 6061-T6) | Résistance à l'usure, CTE adapté au déployeur, isolation électrique |
| Section des rails | Surface de contact minimale de 8,5 × 8,5 mm | Surface d'appui suffisante pour les charges au lancement ; évite la plastification des rails sous accélération quasi statique |
| État de surface | Toutes les surfaces extérieures anodisées ou revêtues d'un revêtement à faible dégazage | Éviter la contamination des autres charges utiles du lanceur (dépôts de dégazage moléculaire sur les optiques) |
| Interrupteurs de déploiement | Au moins 1 sur chaque face de rail accessible (+X, −X) | Inhiber toute activité du satellite jusqu'à sa sortie complète du déployeur (évite un déploiement intempestif et des émissions RF sous la coiffe) |
| Goupille *remove-before-flight* (RBF) | Obligatoire ; coupe physiquement toutes les alimentations | Dernière inhibition de sécurité ; retirée sur le pas de tir après intégration ; garantit l'absence totale d'émission RF et de courant dans les actionneurs de déploiement jusqu'à son retrait volontaire |
| Protubérances | Aucune au-delà de l'enveloppe des rails en configuration repliée | Garantit une éjection franche du déployeur ; évite tout accrochage aux glissières ou à un CubeSat voisin |
| Centre de gravité | À moins de 2 cm du centre géométrique (selon l'ICD du déployeur) | Évite le balancement lors de l'éjection ; garantit des vitesses de basculement à la séparation (*tip-off*) similaires pour tous les CubeSats |
| Fréquence propre fondamentale | Premier mode > 40 Hz (exigence type des déployeurs) | Évite le couplage dynamique entre les modes structuraux du satellite et ceux du lanceur (regroupés dans la plage 10–30 Hz) |

### 12.1.4 Architecture d'empilement PC/104

La plupart des avioniques de CubeSat utilisent une architecture d'empilement compatible PC/104, héritée de la norme d'informatique embarquée industrielle et adaptée au spatial :

**Caractéristiques physiques :**
- **Taille des cartes :** 96 × 90 mm (standard) ou 90 × 96 mm.
- **Connecteur :** connecteur traversant de 104 broches (2 × 52 broches, pas de 2,54 mm) ; le brochage PC/104 d'origine transporte l'alimentation + I²C + SPI + UART + GPIO.
- **Espacement de l'empilement :** généralement 10–15 mm entre cartes (limité par la hauteur des composants et la hauteur d'accouplement des connecteurs).
- **Capacité de l'empilement :** un 1U accueille ~4 cartes ; un 3U accueille ~12 cartes (340 mm / ~28 mm par emplacement de carte).

**Ce qui prend place dans l'empilement :**
- carte EPS (gestion de la batterie, MPPT, distribution de puissance) ;
- carte OBC (processeur, mémoire, interfaces) ;
- carte de communication (radio UHF ou transpondeur en bande S) ;
- carte AOCS (si elle est intégrée : certains fournisseurs regroupent IMU, pilote de magnétocoupleurs et interface des roues de réaction sur un même circuit imprimé) ;
- carte d'interface de la charge utile (CAN, interfaces capteurs).

**Points d'attention mécaniques :**
- Les joints de brasure sont le point le plus faible ; les vibrations aléatoires provoquent des fissures de fatigue aux pattes des composants lourds (en particulier les condensateurs électrolytiques hauts, les gros connecteurs et les oscillateurs à quartz).
- Les connecteurs carte à carte doivent être correctement précontraints (trop lâches = contact intermittent ; trop serrés = montage et démontage difficiles pendant l'intégration et les essais).
- Les entretoises et colonnettes doivent être serrées au couple correct ; un frein-filet à faible résistance (p. ex. Loctite 222) est la norme.

### 12.1.5 Environnement de charges au lancement

L'environnement de lancement soumet le satellite aux charges dues à la poussée des moteurs, aux tremblements aérodynamiques, aux séparations d'étages et aux événements pyrotechniques. Le satellite doit y survivre sans rupture structurale ni dégradation fonctionnelle. Le programme d'essais qui le démontre est décrit au chapitre 14, §14.3.

| Type de charge | Source physique | Niveau type | Durée | Gamme de fréquences | Méthode de vérification |
|-----------|----------------|--------------|----------|----------------|---------------------|
| **Accélération quasi statique** | Poussée des moteurs + charges aérodynamiques | 6–12 g en axial, 2–4 g en latéral | De quelques secondes à quelques minutes | 0 (équivalent statique) | Analyse + essai de vibrations sinusoïdales |
| **Vibrations sinusoïdales** | Dynamique basse fréquence du lanceur | 0,5–3 g (5–100 Hz) | Quelques minutes | 5–100 Hz | Essai de balayage sinusoïdal (3 axes) |
| **Vibrations aléatoires** | Bruit acoustique + couche limite turbulente | 5–15 g$_{\text{rms}}$ (20–2000 Hz) | 60–120 s par axe | 20–2000 Hz | Essai de vibrations aléatoires (3 axes) |
| **Chocs** | Événements de séparation pyrotechnique (séparation d'étage, largage de coiffe, détente du ressort du déployeur) | 500–2000 g à la séparation (haute fréquence) | < 10 ms | 100–10 000 Hz | Essai de spectre de réponse au choc (SRS) |
| **Acoustique** | Pression acoustique du jet des moteurs, bruit aérodynamique | 120–140 dB (20–10 000 Hz) | Quelques minutes | 20–10 000 Hz | Généralement couvert par les vibrations aléatoires pour les CubeSats |

*[Source : ECSS-E-ST-10-03C ; NASA GEVS (GSFC-STD-7000B) ; Falcon 9 Payload User's Guide ; PSLV User's Guide]*

**Profil de DSP des vibrations aléatoires (niveau minimal de qualité de fabrication du GSFC-STD-7000B, tableau 2.4-4) :**

| Fréquence (Hz) | Niveau d'ASD (g$^2$/Hz) | Remarques |
|----------------|---------------------|-------|
| 20 | 0,01 | Début basse fréquence |
| 20–80 | +3 dB/octave | Montée |
| 80–500 | 0,04 | Palier |
| 500–2000 | −3 dB/octave | Décroissance |
| 2000 | 0,01 | Fin du profil |
| **Global** | **6,8 g$_{\text{rms}}$** | Niveau de qualité de fabrication (recette) ; le protovol est à +3 dB, soit environ 9,6 g$_{\text{rms}}$, pendant 1 min par axe (chapitre 14, §14.3.3) |

Le palier à 0,04 g$^2$/Hz entre 80 et 500 Hz est la zone où se produisent la plupart des dommages structuraux, car c'est là que sont excitées les résonances des circuits imprimés et la fatigue des joints de brasure. Les niveaux qui font foi pour un vol donné sont fixés par le manuel utilisateur du déployeur ou du lanceur ; n'utilisez ce profil que là où il les enveloppe.

**Ce qui casse pendant les essais de vibrations :**
1. **Joints de brasure :** les composants lourds (connecteurs, condensateurs hauts, transformateurs) à long bras de levier se fissurent au niveau de leurs brasures. Réduction du risque : utiliser des composants montés en surface, coller les composants hauts, appliquer un vernis de tropicalisation.
2. **Mécanismes déployables :** les charnières d'antenne, les mécanismes de gerbage des panneaux solaires et les ressorts de déploiement peuvent défaillir s'ils ne sont pas correctement maintenus. Réduction du risque : précharge suffisante des mécanismes de gerbage, essais de choc des dispositifs de libération.
3. **Composants optiques :** lentilles et miroirs peuvent se déplacer ou se fissurer s'ils ne sont pas montés avec un découplage des contraintes. Réduction du risque : enrobage RTV, montures à flexibles.
4. **Faisceau de câbles :** frottement contre les arêtes de la structure. Réduction du risque : rayons d'arête > 1 mm, attaches du faisceau tous les 50 mm, gaines de protection.

### 12.1.6 Marge de sécurité structurale

Voici l'énoncé de référence de la marge de sécurité dans cet ouvrage ; le chapitre 3, §3.3.3, l'a introduite comme exemple du niveau de détail des normes ECSS, et la partie V, §V.13, démontre la logique des facteurs de sécurité.

> **Équations clés — marge de sécurité structurale**
>
> $$\text{MoS} = \frac{\sigma_{\text{allowable}}}{\sigma_{\text{design}} \times \text{FoS}} - 1$$
>
> où :
> - $\sigma_{\text{allowable}}$ = limite d'élasticité ou résistance à la rupture du matériau (MPa)
> - $\sigma_{\text{design}}$ = contrainte calculée sous les charges de dimensionnement (MPa)
> - FoS = facteur de sécurité
>
> **Exigence :** MoS ≥ 0 pour tous les cas de charge.
>
> **Facteurs de sécurité (ECSS-E-ST-32C / ECSS-E-ST-32-10C) :**
>
> | Matériau / assemblage | FoS élasticité | FoS rupture | Justification |
> |-----------------|----------|-------------|-----------|
> | Métallique (Al 7075-T6) | 1,25 | 1,5 | Métaux de structure courants |
> | Composite (PRFC) | 1,5 | 2,0 | Plus grande variabilité des propriétés des stratifiés |
> | Assemblages collés | 1,5 | 2,0 | La résistance du collage dépend fortement du procédé |
> | Systèmes pressurisés | 1,5 | 2,0 | Risque d'éclatement pour les autres charges utiles |
> | Mécanismes (à usage unique) | — | 2,0 | Doivent fonctionner du premier coup ; aucune possibilité d'essai |
>
> **Charges de dimensionnement :** la charge de dimensionnement comprend l'accélération quasi statique (tirée du manuel utilisateur du lanceur), multipliée par un facteur d'amplification dynamique ($DAF \approx 1.25$–$1.5$) si la fréquence propre du satellite est proche d'une fréquence d'excitation du lanceur.

> **Exemple résolu — charge axiale sur un rail de CubeSat 3U (classe SuperDove)**
>
> **Données :** CubeSat 3U, masse = 5 kg, charge axiale au lancement = 9 g (valeur type Falcon 9), 4 rails (charge répartie également), section des rails = 8,5 × 8,5 mm, matériau = Al 7075-T6 ($\sigma_y = 503$ MPa, $\sigma_u = 572$ MPa).
>
> **Étape 1 — charge de dimensionnement par rail :**
> $F = \dfrac{m \times n \times g_0}{4} = \dfrac{5 \times 9 \times 9.80665}{4} = \dfrac{441.3}{4} = 110.3$ N
>
> **Étape 2 — contrainte de compression :**
> $\sigma = \dfrac{F}{A_{\text{rail}}} = \dfrac{110.3}{8.5 \times 10^{-3} \times 8.5 \times 10^{-3}} = \dfrac{110.3}{7.225 \times 10^{-5}} = 1.53$ MPa
>
> **Étape 3 — marge de sécurité (élasticité) :**
> $\text{MoS}_y = \dfrac{503}{1.53 \times 1.25} - 1 = \dfrac{503}{1.91} - 1 = 262 \gg 0$ — **Conforme** (avec une très large marge)
>
> **Étape 4 — marge de sécurité (rupture) :**
> $\text{MoS}_u = \dfrac{572}{1.53 \times 1.5} - 1 = \dfrac{572}{2.30} - 1 = 248 \gg 0$ — **Conforme**
>
> **Idée essentielle :** pour les CubeSats, la contrainte axiale quasi statique dans les rails n'est jamais le cas de charge critique. Les rails sont largement surdimensionnés en compression directe. Les véritables facteurs dimensionnants de la structure sont généralement :
> 1. **la rigidité** (fréquence propre fondamentale > 40 Hz), déterminée par la fixation des cartes et des composants internes, et non par la résistance des rails ;
> 2. **la fatigue en vibrations aléatoires** des joints de brasure des circuits imprimés, le véritable mode de défaillance ;
> 3. **la fiabilité des mécanismes de déploiement** : force des ressorts, engagement des verrous, tolérances d'alignement ;
> 4. **la position du centre de gravité**, difficile à respecter avec des charges utiles asymétriques ou des réservoirs de propulsion.

### 12.1.7 Fréquence propre fondamentale

> **Équations clés — fréquence propre fondamentale (modèle de poutre simplifié)**
>
> Pour une poutre encastrée-libre (modèle simplifié de CubeSat, encastré à l'interface avec le déployeur) :
> $$f_1 = \frac{1.875^2}{2\pi L^2} \sqrt{\frac{EI}{\rho_L}}$$
>
> où $E$ = module d'Young (Pa), $I$ = moment quadratique de la section (m$^4$), $\rho_L = \rho A_{\text{cross}}$ = masse linéique (kg/m) et $L$ = longueur (m).
>
> **Exigence :** $f_1 > 40$ Hz (selon l'ICD du déployeur). Certains déployeurs exigent $> 90$ Hz (p. ex. NanoRacks NRCSD).
>
> **Pour un CubeSat 3U modélisé comme une poutre-caisson en aluminium encastrée-libre :**
> - $L = 0.34$ m, $E = 72$ GPa, épaisseur de paroi du caisson $t = 1.5$ mm
> - $I \approx \dfrac{b^4 - (b-2t)^4}{12} = \dfrac{0.10^4 - 0.097^4}{12} = \dfrac{1.000 \times 10^{-4} - 0.885 \times 10^{-4}}{12} \approx 9.6 \times 10^{-7}$ m$^4$
> - Masse linéique : $\rho_L = m/L = 5/0.34 = 14.7$ kg/m
>
> $f_1 = \dfrac{3.516}{2\pi \times 0.34^2} \sqrt{\dfrac{72 \times 10^9 \times 9.6 \times 10^{-7}}{14.7}} = \dfrac{3.516}{0.726} \sqrt{4700} = 4.84 \times 68.6 \approx 330$ Hz
>
> **Cette valeur dépasse largement 40 Hz.** La structure elle-même est très rigide. Cependant, le premier mode réel est généralement déterminé par (a) le composant interne le plus lourd sur son support de fixation (p. ex. un senseur stellaire de 350 g en porte-à-faux sur une équerre) ou (b) un mécanisme déployable en configuration repliée (p. ex. un panneau solaire replié maintenu uniquement par une goupille de gerbage). **Ce sont ces modes locaux, et non le mode structural global, qui constituent généralement l'enjeu de conception.**

---

## 12.2 Conception du système propulsif

*[Source : SMAD, chap. 17 ; Sutton et Biblarz, chap. 2–4 ; Goebel et Katz, *Fundamentals of Electric Propulsion*, 2008]*

### 12.2.1 Quand la propulsion est nécessaire

| Besoin | $\Delta V$ typique | Scénario type | Échéance |
|------|-------------------|------------------|----------|
| **Maintien de l'orbite** (compensation de la traînée) | 5–15 m/s par an | LEO sous 400 km pendant le maximum solaire | Faible poussée continue |
| **Désorbitation** (retrait de service actif) | 50–150 m/s | Retrait de service actif depuis plus de 600 km (règle des 5 ans de la FCC, chapitre 7, §7.3.2) | Fin de mission |
| **Évitement de collision** | 1–5 m/s par événement | Évitement de conjonctions, 2–5 événements par an en LEO | À la demande, en quelques heures |
| **Phasage d'une constellation** | 10–50 m/s | Répartition des satellites sur leurs positions orbitales opérationnelles | Semaines à mois |
| **Relèvement d'orbite** | 50–200 m/s | Transfert de l'orbite d'injection vers l'orbite opérationnelle | Semaines à mois |
| **Maintien à poste** | 1–10 m/s par an | Maintien de l'altitude et de la phase orbitales | Périodique |

**Quand aucune propulsion n'est nécessaire :**

- **Orbite < 500 km :** le déclin naturel de l'orbite sous l'effet de l'atmosphère suffit à respecter la règle de désorbitation en 5 ans de la FCC (selon le coefficient balistique et l'activité solaire ; voir le chapitre 7, §7.3.3).
- **Démonstration technologique à bas coût :** durée de vie limitée acceptable, aucun maintien de l'orbite nécessaire.
- **Constellation utilisant la traînée différentielle pour le phasage** (p. ex. Planet SuperDove ajuste sa section transversale pour créer une traînée différentielle, ce qui permet des manœuvres de phasage sans ergols).
- **Missions à budget contraint**, pour lesquelles le coût, le risque et la masse de la propulsion l'emportent sur ses bénéfices.

### 12.2.2 L'équation de Tsiolkovski — physique

L'équation de Tsiolkovski est la relation fondamentale qui régit toutes les manœuvres propulsives. Elle découle de la conservation de la quantité de mouvement : la quantité de mouvement des gaz éjectés est égale à la variation de quantité de mouvement de l'engin spatial. La partie V, §V.3, en donne la démonstration ; la figure 12.2 en trace le résultat.

> **Équations clés — équation de Tsiolkovski**
>
> En partant de $F = \dot{m} v_e$ (poussée = débit massique × vitesse d'éjection) et en intégrant :
>
> $$\Delta V = v_e \ln\left(\frac{m_0}{m_f}\right) = I_{sp} \cdot g_0 \cdot \ln\left(\frac{m_0}{m_f}\right)$$
>
> Réarrangée pour la masse d'ergols :
> $$m_{\text{propellant}} = m_{\text{dry}} \times \left(e^{\Delta V / (I_{sp} \cdot g_0)} - 1\right)$$
>
> où :
> - $v_e = I_{sp} \times g_0$ = vitesse d'éjection effective (m/s)
> - $I_{sp}$ = impulsion spécifique (s), le « rendement en carburant » du propulseur. Physiquement : le nombre de secondes pendant lesquelles un propulseur peut produire 1 N de poussée à partir de 1 kg d'ergols sous la gravité normale. Plus l'$I_{sp}$ est élevée, moins il faut d'ergols.
> - $g_0 = 9.80665$ m/s$^2$ : accélération normale de la pesanteur (facteur de conversion)
> - $m_0$ = masse initiale (humide) (kg) = $m_f + m_{\text{propellant}}$
> - $m_f$ = masse finale (sèche) (kg) = masse de l'engin spatial une fois tous les ergols consommés
>
> **La tyrannie de l'équation de Tsiolkovski :** la masse d'ergols croît exponentiellement avec $\Delta V / v_e$. Pour $\Delta V = v_e$ (un $\Delta V$ égal à une vitesse d'éjection), 63 % de la masse initiale doit être constituée d'ergols. Pour $\Delta V = 2 v_e$, il en faut 86 %. C'est pourquoi les systèmes à forte $I_{sp}$ sont si précieux pour les missions à grand $\Delta V$ : ils augmentent le $v_e$ du dénominateur, ce qui réduit considérablement le rapport de masse.

![Tsiolkovski — Δv en fonction du rapport de masse pour différentes Isp.](../assets/figures/fig_tsiolkovsky.png)

**Figure 12.2** — La relation de Tsiolkovski : $\Delta V$ atteignable en fonction du rapport de masse $m_0/m_f$ pour des impulsions spécifiques représentatives, du gaz froid à la propulsion électrique. Pour les ~100 m/s d'une poussée de désorbitation de CubeSat, les courbes sont quasi linéaires et le rapport de masse est proche de 1 ; pour les kilomètres par seconde d'un transfert d'orbite, l'exponentielle l'emporte.

### 12.2.3 Technologies de propulsion pour CubeSat — physique et comparaison

La figure 12.3 situe les cinq familles de technologies comparées dans cette section sur une carte de l'impulsion spécifique en fonction de la poussée : les systèmes chimiques se placent en bas à droite (forte poussée, faible $I_{sp}$), les systèmes électriques en haut à gauche ($I_{sp}$ élevée, poussée très faible), et la puissance que chacun exige pendant la poussée détermine ceux qu'une plateforme de CubeSat peut réellement alimenter.

![Carte log–log de l'impulsion spécifique en fonction de la poussée, avec les domaines étiquetés du gaz froid, du gaz chaud, du monergol vert, de l'électronébulisation et des propulseurs à effet Hall, ainsi que les trois points de conception de l'exemple résolu.](../assets/figures/fig_propulsion_map.png)

**Figure 12.3** — Impulsion spécifique en fonction de la poussée pour les options de propulsion de CubeSat. Chaque domaine grisé couvre les plages d'$I_{sp}$ et de poussée du tableau comparatif du §12.2.5 et porte la puissance nécessaire pendant la poussée ; les propulseurs à électronébulisation tiennent dans les 20–60 W qu'un CubeSat peut fournir, alors que les propulseurs à effet Hall en demandent généralement davantage. Les étoiles sont les trois points de conception de l'exemple résolu du §12.2.5 pour une désorbitation de 112 m/s d'un engin spatial de 5 kg, à l'$I_{sp}$ utilisée dans l'exemple et pour une poussée représentative des produits cités dans cette section, annotées de la masse d'ergols requise par chacun.

#### Propulsion à gaz froid

**Physique :** un gaz comprimé (N$_2$, xénon, réfrigérant R-236fa ou autre) est stocké dans un réservoir à 1–30 MPa. Lorsqu'une vanne s'ouvre, le gaz se détend dans une tuyère et convertit son énergie thermique et de pression en énergie cinétique. Pas de combustion, pas de chauffage, pas de réaction chimique.

**Poussée :** $F = \dot{m} v_e + (p_e - p_a) A_e$. Pour une petite tuyère convergente, $v_e \approx \sqrt{2 c_p T_0}$, où $T_0$ est la température du réservoir. Pour du N$_2$ à 300 K : $v_e \approx 500$–$750$ m/s, d'où $I_{sp} \approx 50$–$75$ s.

**Avantages :** système le plus simple (pas d'allumage, pas de puissance hormis le solénoïde de la vanne), réponse rapide (ouverture de vanne de l'ordre de la milliseconde), grande fiabilité, aucun problème de contamination par le jet.

**Inconvénients :** $I_{sp}$ faible (forte masse d'ergols pour un $\Delta V$ donné), réservoir haute pression encombrant, impulsion totale limitée.

**Produits (exemples représentatifs) :** VACCO MiPS (R-236fa, $I_{sp} = 40$ s, 4 propulseurs, 0,3 kg à sec), VACCO ArgoMoon (gaz froid au Xe), gaz froid Bradford ECAPS.

**Missions utilisant le gaz froid :** MarCO (6U, JPL ; gaz froid R-236fa utilisé pour la correction de trajectoire et le contrôle d'attitude pendant le transit vers Mars), de nombreux CubeSats largués depuis l'ISS pour l'évitement de collision.

#### Résistojet / gaz chaud

**Physique :** semblable au gaz froid, mais l'ergol est chauffé électriquement avant sa détente dans la tuyère. Le chauffage élève la température du gaz $T_0$, ce qui augmente la vitesse d'éjection ($v_e \propto \sqrt{T_0}$). Ergols courants : butane (C$_4$H$_{10}$), eau (H$_2$O), ammoniac (NH$_3$).

**Propulsion au butane :** le butane est stocké sous forme liquide à sa pression de vapeur saturante (~2 atm à 20 °C). Chauffé à 200–400 °C puis détendu dans une tuyère, il atteint $I_{sp} \approx 80$–$100$ s. Le stockage liquide est bien plus dense que le gaz comprimé, ce qui permet d'emporter plus d'ergols dans un réservoir plus petit.

**Avantages :** $I_{sp}$ plus élevée que le gaz froid (~2 fois), stockage liquide dense, complexité modérée.

**Inconvénients :** nécessite de la puissance électrique pour le chauffage (5–15 W pendant la poussée), poussée inférieure à celle du gaz froid, risque d'obstruction de la tuyère si l'ergol se décompose.

**Produits (exemples représentatifs) :** Busek BGT-X5 (butane, $I_{sp} = 80$ s), NanoAvionics EPSS (butane, $I_{sp} = 85$ s), résistojet à eau Pale Blue ($I_{sp} = 70$–$80$ s).

#### Monergol vert

**Physique :** un ergol liquide est injecté dans un lit catalytique où il se décompose de façon exothermique, produisant des gaz chauds qui se détendent dans une tuyère. Les ergols « verts » sont des solutions de remplacement de l'hydrazine (N$_2$H$_4$), moins toxiques et plus faciles à manipuler.

| Ergol | Nature chimique | $I_{sp}$ (s) | Masse volumique (kg/m$^3$) | Toxicité | TRL | Héritage en vol |
|-----------|----------|-------------|-------------------|---------|-----|---------|
| **Hydrazine** (N$_2$H$_4$) | Monergol, catalyseur Shell 405 | 220–230 | 1010 | **Extrêmement toxique** (cancérogène) | 9 | Plus de 50 ans, des milliers de missions |
| **AF-M315E (ASCENT)** | Liquide ionique à base de HAN | 235–250 | 1460 | Faible toxicité | 8 | Démonstration GPIM (2019, NASA) |
| **LMP-103S** | Liquide ionique à base d'ADN | 225–235 | 1240 | Faible toxicité | 8 | Démonstration PRISMA (2010, SSC), SkySat |
| **HTP (H$_2$O$_2$ à 90 %)** | Peroxyde d'hydrogène + catalyseur à l'argent | 150–165 | 1400 | Modérée (oxydant) | 7 | Divers petits satellites |

*[Source : Masse et al., « GPIM AF-M315E Propulsion System », AIAA 2019 ; Anflo et al., « Flight Demonstration of LMP-103S », AIAA 2011]*

**Avantages :** poussée élevée (0,1–1 N pour les systèmes de CubeSat), bonne $I_{sp}$ (220 s et plus), technologie éprouvée (héritage des systèmes à hydrazine).

**Inconvénients :** préchauffage du catalyseur nécessaire (2–10 W, 10–30 min de mise en température), masse du système plus élevée (réservoir + lit catalytique + vannes + système d'alimentation), exigences de sécurité pour la manipulation des ergols (même les ergols « verts » exigent des équipements de protection), coût plus élevé (100 k\$ ou plus par unité de vol, à titre indicatif).

**Produits (exemples représentatifs) :** Aerojet MPS-130 (AF-M315E, poussée de 1 N, $I_{sp} = 235$ s, masse du système 3 kg), Bradford HPGP (LMP-103S, 1 N, $I_{sp} = 230$ s).

#### Propulsion électrique — électronébulisation (FEEP)

**Physique :** la propulsion électrique à émission de champ (FEEP, *field-emission electric propulsion*) utilise un champ électrique intense (~$10^9$ V/m) à la pointe d'une aiguille ou le long du bord d'une fente pour ioniser et extraire des atomes métalliques (en général de l'indium ou du gallium) ou des gouttelettes de liquide ionique. Les ions sont accélérés par un champ électrique jusqu'à des vitesses élevées (10–50 km/s), ce qui donne une $I_{sp}$ très élevée.

**Fonctionnement (FEEP à indium) :**
1. L'indium solide est chauffé juste au-dessus de son point de fusion (157 °C) pour former un réservoir liquide.
2. La capillarité amène l'indium liquide vers un réseau de pointes émettrices acérées.
3. Une haute tension (1–10 kV) entre les pointes émettrices et une grille d'extraction crée un champ électrique intense au sommet des pointes.
4. Le champ ionise un à un les atomes d'indium par évaporation de champ.
5. Les ions sont accélérés à travers la grille d'extraction et forment un faisceau d'ions In$^+$ à 20–40 km/s.
6. Un neutraliseur (en général à nanotubes de carbone ou à émission thermoïonique) émet des électrons pour neutraliser le faisceau et éviter la charge électrique de l'engin spatial.

**Performances :** $I_{sp} = 500$–$5000$ s (réglable par la tension d'accélération), poussée = 0,01–1 mN, puissance = 20–60 W.

**Avantages :** $I_{sp}$ extrêmement élevée (consommation d'ergols minimale), pas de réservoir sous pression, stockage compact d'un ergol solide, contrôle précis de la poussée (utile pour le vol en formation).

**Inconvénients :** poussée très faible (des mois de poussée pour un $\Delta V$ significatif), besoin de puissance important (20–60 W pour ~0,5 mN de poussée), contamination par les ions métalliques du jet (dépôt d'indium sur les surfaces), héritage en vol limité.

**Produits (exemples représentatifs) :** Enpulsion NANO R3 (FEEP à indium, 0,35 mN, $I_{sp} = 1000$–$5000$ s, masse sèche 0,9 kg, < 40 W), Accion TILE (électronébulisation de liquide ionique, 0,1 mN, $I_{sp} = 1500$ s).

**Missions utilisant la FEEP ou l'électronébulisation :** LISA Pathfinder (ESA, vol en formation de précision, propulseurs colloïdaux), SSTL NovaSAR-1 (Enpulsion NANO pour le maintien de l'orbite).

#### Propulsion électrique — propulseur à effet Hall

**Physique :** un propulseur à effet Hall utilise des champs électrique et magnétique croisés pour ioniser un gaz propulsif neutre (xénon, krypton ou iode) et accélérer les ions obtenus jusqu'à une vitesse élevée.

**Fonctionnement :**
1. Le gaz propulsif neutre (Xe ou I$_2$) est injecté dans un canal de décharge annulaire.
2. Un champ magnétique radial (produit par des aimants permanents ou des électroaimants) piège les électrons dans une boucle de courant de Hall et les empêche d'atteindre l'anode.
3. Les électrons piégés entrent en collision avec les atomes du gaz neutre et les ionisent.
4. Les ions, beaucoup plus lourds, sont peu déviés par le champ magnétique et sont accélérés axialement par le champ électrique (100–500 V) entre l'anode et la cathode.
5. Une cathode externe (cathode creuse ou cathode RF) fournit les électrons nécessaires à la neutralisation du faisceau et à l'entretien de la décharge.

**Performances :** $I_{sp} = 800$–$3000$ s, poussée = 1–50 mN pour les systèmes à l'échelle CubeSat, puissance = 50–300 W.

**Avantages :** poussée supérieure à celle de la FEEP (de l'ordre du newton pour les plus gros systèmes), excellente $I_{sp}$, technologie bien éprouvée (héritage en maintien à poste GEO : Aerojet PPS-1350, Busek BHT-200).

**Inconvénients :** besoin de puissance important (> 50 W à l'échelle CubeSat), ensemble cathode lourd, stockage du xénon dans des réservoirs haute pression (100–300 bar), érosion du canal qui limite la durée de vie.

**Produits (exemples représentatifs) :** Exotrail ExoMG-nano (40 mN, $I_{sp} = 800$ s, 1,5 kg, 60 W), Busek BHT-200 (13 mN, $I_{sp} = 1370$ s, 1,0 kg, 200 W), Enpulsion MICRO (propulseur à effet Hall, ergol iode, 1 mN, $I_{sp} = 1000$ s).

**Propulsion à l'iode :** l'iode (I$_2$) s'impose peu à peu comme alternative au xénon pour les propulseurs à effet Hall et les moteurs ioniques à grilles. L'iode est solide à température ambiante (stocké sans réservoir sous pression), a une masse volumique de 4940 kg/m$^3$ (contre ~1600 kg/m$^3$ pour le xénon à 100 bar) et une masse atomique voisine (127 contre 131). Le Busek BIT-3 (propulseur à iode) et le ThrustMe NPT30-I2 ont démontré la propulsion à l'iode en orbite.

### 12.2.4 Sans propulsion — stratégies de désorbitation passive

Pour les missions sous ~500 km qui n'ont pas besoin de propulsion pour leurs opérations, une désorbitation passive peut satisfaire les lignes directrices de la FCC (5 ans) ou de l'IADC (25 ans) :

| Méthode | Mécanisme | Masse | Volume | Efficacité | TRL |
|--------|-----------|------|--------|--------------|-----|
| **Traînée atmosphérique (naturelle)** | Sous 500 km, la traînée atmosphérique fait décroître naturellement l'orbite | 0 | 0 | Dépend du coefficient balistique et du cycle solaire | 9 |
| **Voile de traînée** | Une membrane déployable multiplie la section transversale par 10 à 100 | 0,1–0,5 kg | 0,25–1U | Très efficace au-dessus de 600 km | 7–8 |
| **Câble électrodynamique** | Un câble conducteur interagit avec le champ géomagnétique pour freiner le satellite | 0,2–0,5 kg | 0,5U | Efficacité modérée ; dépend de l'inclinaison orbitale | 6–7 |

*[Source : voile de traînée Cranfield Icarus, 0,1 kg ; NanoSail-D2, NASA ; InflateSail, SSC]*

### 12.2.5 Comparaison des systèmes propulsifs

| Paramètre | Gaz froid (N$_2$) | Gaz chaud (butane) | Monergol vert (AF-M315E) | Électronébulisation (FEEP) | Effet Hall (Xe) |
|-----------|-----------------|------------------|--------------------------|--------------------|--------------------|
| $I_{sp}$ (s) | 40–75 | 80–100 | 230–250 | 500–5000 | 800–3000 |
| Poussée | 10–100 mN | 5–50 mN | 0,1–1 N | 0,01–1 mN | 1–50 mN |
| Masse d'ergols (100 m/s, engin spatial de 5 kg à sec, à l'$I_{sp}$ indiquée) | 0,93 kg (60 s) | 0,60 kg (90 s) | 0,22 kg (235 s) | 0,042 kg | 0,055 kg |
| Masse sèche du système | 0,3 kg | 0,5 kg | 3,0 kg | 0,9 kg | 1,5 kg |
| **Masse totale du système** | **1,23 kg** | **1,10 kg** | **3,22 kg** | **0,94 kg** | **1,55 kg** |
| Durée de poussée (100 m/s) | Minutes | Minutes | Secondes | **Mois** | Jours à semaines |
| Puissance pendant la poussée | < 1 W (vanne) | 5–15 W | 2–10 W (préchauffage) | 20–60 W | 50–300 W |
| Complexité | Faible | Faible à moyenne | Élevée | Moyenne | Élevée |
| Coût (indicatif, 2026) | ~15 k€ | ~30 k€ | ~120 k€ | ~50 k€ | ~80 k€ |
| TRL | 9 | 7–8 | 7–8 | 7–8 | 6–8 (CubeSat) |

> **Exemple résolu — comparaison des masses d'ergols pour une désorbitation propulsée (cas hypothétique)**
>
> EOSat-3U n'emporte lui-même aucune propulsion : à 500 km, il compte sur le déclin naturel de son orbite, et le chapitre 7, §7.3.3, montre que sa durée de vie orbitale (≈ 5 ans) satisfait la règle de retrait de service sans poussée ; le chapitre 18 ne lui définit donc aucun mode de manœuvre. La question à laquelle répond cet exemple est par conséquent hypothétique : *si* une désorbitation propulsée était exigée pour un 3U à 600 km, que coûterait-elle en masse ?
>
> **Scénario :** CubeSat 3U, $m_{\text{dry}} = 5.0$ kg, désorbitation depuis 600 km jusqu'à un périgée de 200 km ($\Delta V = 112$ m/s, chapitre 7, §7.5).
>
> **Gaz froid** ($I_{sp} = 60$ s, $v_e = 588$ m/s) :
> $m_{\text{prop}} = 5.0 \times (e^{112/588} - 1) = 5.0 \times (e^{0.190} - 1) = 5.0 \times 0.210 =$ **1,05 kg**
>
> Système complet : 1,05 + 0,3 = 1,35 kg = **23 % de la masse limite de 6 kg du CubeSat**
>
> **Monergol vert** ($I_{sp} = 235$ s, $v_e = 2305$ m/s) :
> $m_{\text{prop}} = 5.0 \times (e^{112/2305} - 1) = 5.0 \times (e^{0.0486} - 1) = 5.0 \times 0.0498 =$ **0,249 kg**
>
> Système complet : 0,249 + 3,0 = 3,25 kg = **54 % de la masse limite** (le système est lourd, même si les ergols sont légers)
>
> **Électronébulisation (FEEP)** ($I_{sp} = 1200$ s, $v_e = 11\,768$ m/s) :
> $m_{\text{prop}} = 5.0 \times (e^{112/11768} - 1) = 5.0 \times (e^{0.00952} - 1) = 5.0 \times 0.00956 =$ **0,048 kg**
>
> Système complet : 0,048 + 0,9 = 0,95 kg = **16 % de la masse limite** (le total le plus léger, mais l'exécution prend des mois)
>
> **Synthèse du compromis :** le système à électronébulisation est le plus léger au total, car sa forte $I_{sp}$ minimise la masse d'ergols et sa masse sèche est modérée. Le gaz froid consomme le plus d'ergols mais présente la masse sèche la plus faible. Le monergol vert est pénalisé par son lourd système d'alimentation. **Le choix optimal dépend de l'échéance de la mission :** si la désorbitation doit être rapide (quelques jours), gaz froid ou monergol ; si plusieurs mois sont acceptables, la propulsion électrique l'emporte sur la masse.

---

## 12.3 Gestion bord des données

### 12.3.1 Architecture de l'OBC — choix du processeur

Le calculateur de bord (OBC) est le cerveau du satellite : il gère l'ensemble du traitement des données, la commande, la production de la télémesure et la FDIR (détection, isolation et reprise des défaillances ; chapitre 18). Le choix du processeur repose sur un compromis fondamental entre tenue aux radiations, puissance de calcul, consommation et coût.

**Processeurs à héritage en vol** (exemples représentatifs) :

| Processeur | Architecture | Horloge (MHz) | RAM | Tenue aux radiations | Puissance (W) | TRL (spatial) | Coût (indicatif, 2026) | Usage type |
|-----------|-------------|-------------|-----|---------------|-----------|------------|------|------------|
| **TI MSP430** | RISC 16 bits | 16–25 | 2–10 ko | Modérée (COTS, testé jusqu'à 30 krad) | 0,005–0,01 | 9 | < 10 € | Servitude à très basse consommation, OBC du mode survie |
| **ARM Cortex-M4** (STM32F4) | ARM 32 bits | 168 | 192 ko + ext. | Faible à modérée (COTS, 10–30 krad) | 0,05–0,20 | 8–9 | 10–20 € | **OBC standard de CubeSat**, traitement TM/TC, boucle de commande du SCAO |
| **ARM Cortex-M7** (STM32H7) | ARM 32 bits | 400–480 | 1 Mo + ext. | Faible à modérée (COTS, 10–20 krad) | 0,1–0,5 | 7–8 | 15–30 € | OBC de CubeSat plus performant, traitement d'images à bord |
| **ARM Cortex-A** (compatible Linux, p. ex. NXP i.MX6) | ARM 32/64 bits | 500–1200 | 256 Mo–1 Go DDR | Faible (COTS, < 10 krad) | 1–3 | 6–7 | 20–50 € | Traitement charge utile, inférence IA/apprentissage automatique, système Linux |
| **Xilinx Zynq** (SoC : ARM + FPGA) | ARM Cortex-A9 + FPGA Artix-7 | 667 + programmable | 512 Mo + matrice FPGA | Modérée (Zynq-7000) à élevée (Kintex durci) | 2–5 | 7–8 | 100–500 € | Traitement de données à haut débit, radio logicielle, compression d'images |
| **LEON3/4** (SPARC durci) | SPARC 32 bits | 50–250 | Externe | Élevée (100–300 krad, insensible au SEL) | 1–3 | 9 | 10–50 k€ | Missions à héritage ESA, GEO, espace lointain |
| **RAD750** (BAE Systems) | PowerPC 32 bits | 200 | 128 Mo | Très élevée (1 Mrad, insensible au SEL) | 5–10 | 9 | 200 k€ et plus | Missions phares de la NASA (MRO, Curiosity, JWST) |

*[Source : fiches techniques STM32 de STMicroelectronics ; fiche technique Xilinx Zynq-7000 ; fiche technique LEON3 de Cobham Gaisler]*

### 12.3.2 Système d'exploitation et effets des radiations

**RTOS, sans système d'exploitation ou Linux :**

| Approche | Système d'exploitation | Avantages | Inconvénients | Quand l'utiliser |
|----------|-----|------|------|------------|
| **Sans système d'exploitation** (*bare-metal*) | Aucun (boucle d'événements spécifique) | Surcharge minimale, temporisation déterministe, code le plus compact | Difficile à maintenir, pas d'isolation des tâches, pas de système de fichiers | Missions 1U très simples (MSP430) |
| **RTOS** (FreeRTOS, ChibiOS, Zephyr) | Système d'exploitation temps réel | Ordonnancement déterministe, isolation des tâches, écosystème mûr, faible empreinte (10–50 ko) | Plus complexe que sans système d'exploitation ; impose de concevoir les priorités des tâches | **Standard pour la C&DH des CubeSats** : boucle du SCAO, TM/TC, gestion des modes |
| **Linux** (Yocto, Buildroot) | Système d'exploitation complet | Écosystème riche (Python, réseau, système de fichiers, pilotes de périphériques), développement facile | Non déterministe (inadapté au temps réel dur), empreinte importante (50+ Mo), processeur gourmand en énergie | Traitement des données charge utile, IA/apprentissage automatique, analyse d'images à bord |

**Effets des radiations sur les processeurs :** l'environnement radiatif spatial (chapitre 7, §7.6) produit deux catégories d'effets :

1. **Dose ionisante totale (TID) :** dommages radiatifs cumulés dus aux protons et électrons piégés et aux particules solaires. Elle se mesure en rad(Si) ou en gray. Elle provoque des dérives de la tension de seuil des transistors CMOS, augmente le courant de fuite et finit par entraîner une défaillance fonctionnelle.
   - LEO (500 km, 51,6°) : ~1–5 krad/an derrière un blindage de 2 mm d'aluminium
   - LEO polaire/SSO (800 km) : ~5–10 krad/an
   - MEO (traversée de la ceinture de protons) : ~50–100 krad/an
   - GEO : ~10–30 krad/an

2. **Effets d'événement singulier (SEE) :** une seule particule énergétique (proton ou ion lourd) dépose dans un transistor une charge suffisante pour inverser un bit (SEU, aléa logique), verrouiller un transistor (SEL, verrouillage par ion lourd, potentiellement destructif) ou griller un composant de puissance (SEB, claquage par ion lourd).
   - **Taux de SEU en LEO :** ~1–10 inversions de bit par jour et par Go de SRAM (très variable selon l'orbite et le blindage)
   - **Réduction du risque de SEL :** résistances de limitation de courant sur les lignes d'alimentation, circuits de détection de verrouillage, réinitialisations par chien de garde
   - **Réduction du risque de SEU :** détection et correction d'erreurs (EDAC) sur la mémoire (codes de Hamming, TMR, redondance modulaire triple)

**Approche des CubeSats face aux radiations :** la plupart des CubeSats en LEO (< 600 km, mission de moins de 3 ans) utilisent des processeurs COTS avec EDAC sur la mémoire et une minuterie de chien de garde. La dose totale sur une mission de 3 ans en LEO est généralement de 3–15 krad, ce que supportent la plupart des processeurs COTS ARM Cortex-M (testés et caractérisés, à défaut d'être garantis). Pour des missions plus longues, des orbites plus hautes ou des applications critiques, des processeurs tolérants aux radiations ou durcis sont nécessaires.

### 12.3.3 Dimensionnement du stockage de données

> **Équations clés — stockage de données**
>
> $$S_{\text{required}} = V_{\text{daily}} \times N_{\text{days}} \times f_{\text{safety}}$$
>
> où $V_{\text{daily}}$ = volume de données produit chaque jour (d'après le bilan de données, chapitre 11, §11.9), $N_{\text{days}}$ = nombre de jours entre deux vidages complets vers le sol (généralement 1–3 en LEO), $f_{\text{safety}} = 2$ (pour absorber les passages manqués, les indisponibilités de station sol et les périodes en mode survie).
>
> **Technologies de stockage :**
>
> | Technologie | Capacité | Vitesse d'écriture | Tenue aux radiations | Puissance | Usage sur CubeSat |
> |-----------|----------|------------|---------------------|-------|------------|
> | Flash NOR | 4–256 Mo | 1–5 Mo/s | Modérée (10–50 krad) | Faible | Stockage du code, ROM d'amorçage, paramètres critiques |
> | Flash NAND (SLC) | 1–128 Go | 10–50 Mo/s | Faible à modérée (5–20 krad) | Faible | **Stockage principal des données** |
> | Flash NAND (MLC/TLC) | 32–512 Go | 50–200 Mo/s | Faible (< 10 krad) | Faible | Capacité maximale (utiliser EDAC et nettoyage mémoire) |
> | Carte SD (industrielle) | 4–128 Go | 10–50 Mo/s | Faible (< 5 krad) | Très faible | Missions à petit budget (risque : usure + radiations = perte de données) |
> | MRAM | 1–64 Mo | 10–50 Mo/s | Élevée (> 100 krad) | Très faible | Paramètres critiques, journal non volatil |

> **Exemple résolu — stockage du CubeSat 3U d'observation de la Terre**
>
> **Données :** génération quotidienne = 720 Mo et capacité quotidienne de la liaison descendante = 956 Mo (chapitre 11, §11.9). La capacité dépasse la génération, si bien qu'en exploitation nominale la mémoire se vide chaque jour ; le stockage doit donc couvrir le cas *anormal* de plusieurs jours sans liaison descendante réussie. On prend $N_{\text{days}} = 3$ (un long week-end d'indisponibilité de la station sol, ou une période en mode survie) et $f_{\text{safety}} = 2$ :
>
> $S_{\text{required}} = 720 \times 3 \times 2 = 4320$ Mo $\approx$ **4,3 Go**
>
> **Spécification :** stockage flash NAND ≥ 8 Go (la taille standard immédiatement supérieure). L'OBC retenu au §12.5 comporte 4 Go de flash NAND ; l'ajout d'une carte SD de 8 Go ou d'une puce NAND supplémentaire fournit une capacité suffisante. Après une interruption de trois jours, l'arriéré de 2,2 Go se résorbe en $2160/(956 - 720) \approx 9$ jours au débit nominal de la liaison descendante (chapitre 11, §11.9), ce qui explique qu'une procédure de sortie du mode survie prévoie généralement des passages supplémentaires de transmission au sol.
>
> Pour un imageur haute résolution produisant 4,5 Go/jour, le besoin de stockage est de $4500 \times 3 \times 2 = 27$ Go. Spécifier un stockage flash ≥ 32 Go.

### 12.3.4 Fonctions du logiciel de vol

| Fonction | Description | Fréquence d'exécution type | Criticité |
|----------|------------|----------------------|-------------|
| **Gestion des modes** | Transitions entre les modes Survie, Veille, Prise de vue, Liaison descendante et Éclipse selon une machine à états (chapitre 18) | Sur événement | **Critique** (transition erronée = perte de la mission) |
| **Boucle de commande du SCAO** | Lire les capteurs (senseur stellaire, gyromètre, magnétomètre), calculer l'estimation d'attitude (filtre de Kalman), commander les actionneurs (régulateur PID) | 1–10 Hz | **Critique** (perte du pointage = perte de la mission) |
| **Traitement TM/TC** | Produire les paquets de télémesure CCSDS, analyser et exécuter les télécommandes | 1 Hz (TM), sur événement (TC) | **Critique** (perte des communications = perte de la mission) |
| **Traitement des données** | Acquisition des données charge utile, compression (JPEG2000, CCSDS 122.0), mise en mémoire tampon, gestion de la file de transmission au sol | À la demande | Importante |
| **FDIR** | Détection, isolation et reprise des défaillances : minuterie de chien de garde, protection contre les surintensités, contrôles de cohérence des capteurs, déclenchement autonome du mode survie | 1–10 Hz | **Critique** (doit détecter les défauts et s'en remettre de manière autonome) |
| **Servitude** | Surveiller les températures, tensions, courants et vitesses de roue ; consigner dans une mémoire non volatile | 0,1–1 Hz | Importante |
| **Programmation** | Exécution des commandes datées : prise de vue autonome au-dessus de la cible, préparation de la transmission au sol avant le passage au-dessus de la station, programmation des désaturations | 1 Hz | Importante |
| **Contrôle thermique** | Lire les capteurs de température, commander les réchauffeurs (thermostat tout ou rien ou PID) | 0,1 Hz | Modérée (pour les missions équipées de réchauffeurs) |

---

## 12.4 Du dimensionnement aux équipements : choisir les composants

Les chapitres consacrés aux sous-systèmes (9 à 12) produisent des *dimensions* : une surface de générateur solaire, une énergie de batterie, un moment cinétique de roue, une puissance d'émission, une capacité de stockage. L'étape suivante consiste à transformer chaque dimension en un matériel. Le chapitre 13 traite en détail le choix des équipements et la nomenclature (faire, acheter ou réutiliser, TRL, contrôle des exportations) ; cette section présente les vérifications qui accompagnent le dimensionnement lui-même, car c'est au moment où de vrais composants remplacent les estimations paramétriques que les bilans changent.

**Pour chaque catégorie requise, choisissez un composant et vérifiez :**
- tient-il dans l'allocation de masse du sous-système fixée au chapitre 8, §8.4 ?
- sa consommation reste-t-elle dans le bilan de puissance des modes opérationnels où il est allumé (chapitre 8, tableau 8.4) ?
- l'interface est-elle compatible (PC/104, I²C, SPI, CAN, RS-422 ; chapitre 8, §8.3) ?
- la chaîne RF est-elle cohérente (bande du transpondeur = bande de l'antenne = bande de la station sol ; chapitre 11) ?
- le composant est-il qualifié pour l'environnement vibratoire du lancement décrit au §12.1.5 ?
- la quantité est-elle sensée (p. ex. 4 roues de réaction, 3 magnétocoupleurs ; chapitre 10) ?

**Étude de compromis sur les composants.** Pour les choix disputés (deux ou trois candidats crédibles), menez l'étude de compromis formelle sous forme de tableau du chapitre 4, §4.5 : définissez les critères (masse, puissance, coût, TRL, héritage en vol, performances), notez chaque candidat sur une échelle de 1 à 5, appliquez les pondérations, calculez les notes pondérées et documentez le candidat retenu ainsi que la justification.

**Exemple de mission réelle — choix des équipements d'Iridium NEXT.** Iridium NEXT (Thales Alenia Space, 2017–2019) constitue un exemple à grande échelle de sélection rigoureuse des équipements. Pour l'antenne réseau à commande de phase :

| Critère | Pondération | Candidat A (Thales) | Candidat B (Raytheon) |
|-----------|--------|---------------------|----------------------|
| Performances | 0,30 | 4,5 | 4,0 |
| Masse | 0,20 | 3,5 | 4,0 |
| Coût | 0,20 | 3,0 | 4,5 |
| TRL | 0,15 | 5,0 | 4,0 |
| Délais | 0,15 | 4,0 | 3,5 |
| **Note pondérée** | | **3,95** | **4,00** |

Le choix s'est finalement porté sur le candidat A (Thales) pour des raisons contractuelles extérieures à l'étude de compromis chiffrée, ce qui montre que les études de compromis éclairent les décisions sans les dicter.

---

## 12.5 Vérification du bouclage des bilans

Une fois que chaque sous-système dispose de composants réels, les bilans techniques du chapitre 8 sont recalculés à partir de la liste d'équipements plutôt qu'à partir d'estimations paramétriques, et chacun est comparé à sa limite. C'est l'aboutissement naturel de la séquence de conception des sous-systèmes et la condition d'entrée des chapitres consacrés à l'intégration et à la vérification : une conception dont un bilan est négatif n'est pas prête à être vérifiée.

### 12.5.1 Méthode

1. **Refaire le total de chaque bilan à partir de la liste d'équipements :** masse (avec le barème de marges à deux niveaux du chapitre 8, tableau 8.3), puissance par mode opérationnel, marge de liaison, bilan de données, bilan de pointage, marges structurales et coût.
2. **Comparer les estimations paramétriques aux totaux issus des équipements** et consigner l'écart ; une variation de plus de 10 % environ sur un sous-système signale qu'il faut réexaminer le modèle paramétrique, le choix d'équipement, ou les deux.
3. **Classer chaque bilan** en vert (marge nettement supérieure à l'exigence de la phase), orange (positive mais inférieure à cette exigence) ou rouge (négative).
4. **Résoudre chaque rouge avant de poursuivre,** et reporter chaque orange dans le registre des risques (chapitre 15) avec un responsable et une mesure de réduction.

### 12.5.2 Exemple résolu — liste d'équipements d'EOSat-3U

> Les colonnes de masse, de puissance et de coût sont des **totaux de ligne** (valeur unitaire × quantité) ; la valeur unitaire figure dans la description du composant lorsqu'elle diffère.
>
> | Catégorie | Composant (exemple représentatif) | Qté | Masse (kg) | Puissance (W) | Coût (k€, indicatif) | Interface |
> |----------|-----------|-----|----------|----------|-------------|-----------|
> | Carte EPS | GomSpace P31u (MPPT, rails 3,3 V/5 V/batterie) | 1 | 0,10 | 0,5 | 8 | I²C |
> | Batterie | GomSpace BP4 (2S2P, 38 Wh, Li-ion 18650) | 1 | 0,20 | — | 5 | I²C (télémesure) |
> | Panneaux solaires | MMA HaWK déployables, 2 × (0,225 kg, ~12 W en début de vie, 12,5 k€) | 2 | 0,45 | — | 25 | Directement vers l'EPS |
> | OBC | GomSpace A3200 (ARM Cortex-A, Linux, 4 Go de NAND) | 1 | 0,08 | 1,0 | 12 | I²C, SPI, UART |
> | Roues de réaction | Blue Canyon RW210, 4 × (0,055 kg, 0,6 W, 8 k€ ; 1 mN m, 10 mN m s) | 4 | 0,22 | 2,4 | 32 | SPI |
> | Magnétocoupleurs | CubeSpace CubeMAG, 3 × (0,03 kg, 0,1 W, 3 k€ ; 0,2 A m$^2$) | 3 | 0,09 | 0,3 | 9 | I²C |
> | Senseur stellaire | Blue Canyon NST (précision de 10″, mise à jour à 2 Hz) | 1 | 0,35 | 1,5 | 35 | SPI/UART |
> | Senseurs solaires | NewSpace NFSS-411, 6 × (5 g, 0,01 W, 1 k€ ; 0,5°) | 6 | 0,03 | 0,06 | 6 | Analogique/I²C |
> | Transpondeur | Endurosat bande S TX/RX (2 W RF, QPSK + LDPC, 1–5 Mbit/s) | 1 | 0,10 | 6,0 (émission) | 15 | SPI |
> | Antenne | Patch bande S Endurosat (6 dBi, RHCP) | 1 | 0,02 | — | 3 | Coaxial RF |
> | Charge utile | Télescope spécifique (multispectral, GSD de 5 m) | 1 | 1,50 | 5,0 | 150 | LVDS/SPI |
> | Structure | Structure 3U d'ISIS (Al 7075-T6, anodisé dur) | 1 | 0,30 | — | 8 | Mécanique |
> | Faisceau | Câbles spécifiques, connecteurs, empilement PC/104 | 1 | 0,15 | — | 5 | Divers |
> | **TOTAL** | | | **3,59** | **≈ 10,3 (prise de vue : charge utile + OBC + senseur stellaire + roues + EPS + magnétocoupleurs + senseurs solaires)** | **313** | |
>
> **Estimation paramétrique du chapitre 8 :** 3,68 kg (CBE). **Total des équipements :** 3,59 kg. Écart : −2 % (dans la précision attendue des modèles paramétriques).
>
> **Bilan de masse** (barème de phase A du chapitre 8, tableau 8.3, avec par simplicité une marge uniforme de 20 % pour la maturité des équipements) :
> - CBE : 3,59 kg
> - + 20 % de marge équipement : 4,31 kg
> - + 20 % de marge système : 5,17 kg (MEV)
> - Limite CDS : 6,0 kg
> - **Marge par rapport à la limite : 0,83 kg (14 %)** : orange, acceptable en phase A mais serré pour la phase B et au-delà.

### 12.5.3 Exemple résolu — tableau de bouclage d'EOSat-3U

| Bilan | Limite / exigence | Valeur issue des équipements | Marge | État | Source |
|--------|--------------------|----------------------|--------|--------|--------|
| Masse | 6,0 kg (CDS 3U) | MEV 5,17 kg (CBE 3,59 kg) | 0,83 kg (14 %) | Orange | §12.5.2, tableau 8.3 |
| Puissance — générateur | 16,0 W en début de vie requis | ~24 W en début de vie (deux panneaux déployables) | ~8 W (50 %) | Vert | Chapitre 9, §9.2 |
| Puissance — mode prise de vue | Allocation de 8,0 W | ≈ 10,3 W d'après la liste d'équipements (charge utile 5,0, senseur stellaire 1,5, 4 roues 2,4, OBC 1,0, EPS 0,5, magnétocoupleurs 0,3, senseurs solaires 0,06) | −2,3 W | **Rouge** | Chapitre 8, tableau 8.4 |
| Batterie | ≥ 11 Wh spécifiés | 38 Wh (2S2P) | 27 Wh | Vert | Chapitre 9, §9.3 |
| Marge de liaison | ≥ 3 dB à 10° d'élévation | 10,4 dB à 5 Mbit/s | 7,4 dB | Vert | Chapitre 11, §11.8.1 |
| Bilan de données | 720 Mo/jour générés | Capacité de 956 Mo/jour | 33 % | Vert | Chapitre 11, §11.9 |
| Pointage | 0,1° (3σ) | 0,023° RSS | 77 % | Vert | Chapitre 10, §10.4 |
| Structure | $f_1 > 40$ Hz ; MoS ≥ 0 | Mode global ≈ 330 Hz ; MoS ≫ 0 | Large | Vert (modes locaux à vérifier par essai) | §12.1.6–§12.1.7 |
| Coût du matériel | Plafond de 320 k€ (hypothèse de l'exemple) | 313 k€ | 7 k€ (2 %) | **Rouge** (en deçà de la réserve de coût de 10 % de la phase A) | §12.5.2 |

La ligne matériel de 313 k€ est tirée par le télescope spécifique de 150 k€ de la liste du §12.5.2 ; l'estimation de référence d'EOSat-3U du chapitre consacré aux coûts (chapitre 16, §16.1.6), qui suppose un imageur COTS, situe le matériel seul à ≈ 161–178 k€ pour un coût total de mission de ≈ 457–490 k€. Il s'agit de deux choix de charge utile différents, et non d'un désaccord arithmétique ; la comparaison du chapitre 13, §13.6, utilise les chiffres du chapitre 16.

Les deux lignes rouges sont instructives. La ligne de coût montre que le télescope spécifique consomme presque tout le plafond, avec seulement 2 % de reste, bien en deçà de la réserve de 10 % qu'une estimation de phase A devrait comporter (chapitre 16, §16.4) : c'est le premier point qu'un comité de revue contesterait. L'allocation paramétrique de 8 W pour le mode prise de vue (chapitre 8, tableau 8.4) a été établie avant tout choix de composant ; le senseur stellaire et les quatre roues retenus consomment davantage que ne le supposait l'estimation paramétrique du SCAO. La conception n'est pas compromise (le générateur fournit bien plus de 10 W en phase éclairée et la batterie est grande), mais le tableau des modes, la puissance moyenne sur l'orbite et le cas de l'éclipse du chapitre 9 doivent tous être recalculés avec les valeurs des équipements avant de pouvoir déclarer le bilan bouclé. Ce nouveau calcul, ainsi que la décision de redéfinir le référentiel d'allocation ou d'utiliser le senseur stellaire selon un rapport cyclique pendant la prise de vue, est précisément ce que la vérification du bouclage a pour objet d'imposer.

### 12.5.4 Si un bilan ne boucle pas

| Bilan | Remède courant | Incidence | Compromis type masse/puissance/coût |
|--------|-----------|--------|------------------------------|
| **Masse** (négative) | Supprimer la propulsion ; choisir des composants plus légers ; réduire la redondance ; passer à un format plus grand | Compromis risque / performances | Supprimer la propulsion économise 0,5–1,5 kg |
| **Puissance** (négative) | Ajouter un générateur solaire déployable ; réduire le rapport cyclique de la charge utile ; choisir un SCAO moins gourmand ; planifier les opérations pour éviter les charges simultanées | Compromis coût / délais | Un panneau déployable ajoute ~15 W mais coûte 0,3 kg + 25 k€ (indicatif) |
| **Liaison** (négative) | Augmenter la puissance d'émission ; utiliser une antenne à gain plus élevé ; réduire le débit ; améliorer le codage ; améliorer la station sol | Compromis masse / puissance | Les 3 dB gagnés par le codage sont « gratuits » ; 3 dB obtenus par une antenne plus grande coûtent de la masse |
| **Coût** (au-dessus du plafond) | Utiliser des COTS plutôt que des composants durcis ; supprimer la propulsion ; réduire le segment sol ; utiliser SatNOGS plutôt que des stations sol commerciales | Compromis risque / capacités | Les COTS plutôt que les composants durcis divisent le coût du processeur par 10 à 100 |
| **Pointage** (insuffisant) | Améliorer le senseur stellaire ; améliorer l'étalonnage d'alignement ; ajouter une isolation vibratoire pour les roues ; réduire les gradients thermiques | Compromis coût / complexité | L'amélioration de l'alignement est généralement la moins coûteuse |

---

## 12.6 Retour sur UniSat-1 : structure, gestion bord des données et liste d'équipements

**Conformité à la CDS pour le format 1U.** La *CubeSat Design Specification* (CDS Rev 14) définit l'enveloppe du 1U :

| Paramètre | Spécification 1U | Conception d'UniSat-1 | Conformité |
|-----------|-----------------|-----------------|------------|
| Dimensions | 100,0 × 100,0 × 113,5 mm | 100,0 × 100,0 × 113,5 mm (structure 1U d'ISIS) | **Conforme** |
| Masse maximale | 2,0 kg (CDS Rev 14, ISIPOD) | Objectif de 1,0 kg (marge de 50 % par rapport à la limite de 2 kg) | **Conforme** |
| Matériau des rails | Al 7075-T6 anodisé dur | Standard (intégré à la structure ISIS, 7075-T6, anodisation de type III) | **Conforme** |
| Section des rails | 8,5 × 8,5 mm minimum | Standard (ISIS : 8,5 × 8,5 mm) | **Conforme** |
| Interrupteurs de déploiement | Au moins 1 par face accessible | 2 interrupteurs (standard ISIS, sur les faces de rail +X/−X) | **Conforme** |
| Goupille RBF | Obligatoire | Présente (standard ISIS, sur la face −Z) | **Conforme** |
| Décalage du centre de gravité | ≤ 2 cm du centre géométrique | < 1 cm (empilement de cartes symétrique, batterie centrée) | **Conforme** |
| Protubérances | Aucune au-delà de l'enveloppe des rails (configuration repliée) | Antenne monopôle UHF repliée le long d'un rail (à ressort, dans l'enveloppe) | **Conforme** |
| Fréquence propre fondamentale | Premier mode > 40 Hz | ~600 Hz (une structure 1U en aluminium est extrêmement rigide) | **Conforme** |

**Remarque sur la limite de masse de la CDS :** la CDS Rev 14 fixe 2,0 kg comme limite du déployeur ISIPOD pour un 1U. Cependant, de nombreux fournisseurs de déployeurs (p. ex. NanoRacks, Exolaunch) spécifient 1,33 kg pour un 1U. Vérifiez toujours l'ICD du déployeur concerné. UniSat-1 vise 1,0 kg, bien en deçà de l'une ou l'autre limite.

**Pas de propulsion :** à 400 km d'altitude, la traînée atmosphérique assure une désorbitation naturelle. Le coefficient balistique d'un 1U vaut

$$B = \frac{m}{C_D \times A} = \frac{1.0}{2.2 \times 0.01} = 45.5 \text{ kg/m}^2$$

Avec la méthode du chapitre 7, §7.3.3, on obtient une durée de vie orbitale d'environ 6–18 mois selon l'activité solaire (indice F10.7). Au maximum solaire (F10.7 > 200), l'atmosphère plus dense désorbite le satellite en 6 mois environ ; au minimum solaire (F10.7 ~ 70), la durée de vie s'allonge jusqu'à près de 18 mois. Dans les deux cas, la règle des 5 ans de la FCC et la recommandation des 25 ans de l'IADC sont respectées sans aucun système de propulsion.

**Justification du choix de l'OBC :** UniSat-1 utilise une carte spécifique fondée sur un TI MSP430 (mode survie / servitude) et un STM32F4 Cortex-M4 (OBC principal). Le MSP430 exécute un micrologiciel sans système d'exploitation qui gère le chien de garde, la surveillance de l'alimentation et la reprise en mode survie. Le STM32F4 exécute FreeRTOS et gère la TM/TC, l'acquisition des données du magnétomètre et la programmation. L'architecture à deux processeurs assure une redondance : si le STM32F4 défaille (SEU, verrouillage), le MSP430 peut maintenir les opérations en mode survie et répondre aux télécommandes du sol.

**Stockage des données :** avec 1,13 Mo/jour de données magnétométriques (chapitre 11, §11.8.2) et un débit utile de 4800 bit/s en liaison descendante, le stockage à bord n'est pas un goulet d'étranglement. Une flash NOR de 4 Mo suffit (elle stocke environ 3,5 jours de données en tampon, assez pour absorber le déficit de contacts avec une seule station identifié au chapitre 11, le temps de mobiliser des stations supplémentaires). Aucune flash NAND ni carte SD n'est nécessaire.

**Liste complète des équipements du 1U :**

> | N° | Catégorie | Composant (exemple représentatif) | Masse (g) | Puissance (W) | Coût (k€, indicatif) | Qté | Interface |
> |---|----------|-----------|----------|----------|-------------|-----|-----------|
> | 1 | Structure | Structure de CubeSat 1U d'ISIS (Al 7075-T6) | 200 | — | 4,0 | 1 | Mécanique |
> | 2 | EPS | GomSpace NanoPower P31us (carte EPS + batterie Li-ion 2S, 10 Wh) | 200 | 0,3 (au repos) | 12,0 | 1 | I²C |
> | 3 | Cellules solaires | Cellules GaAs à triple jonction fixées sur la structure (5 faces) | 50 | — (produisent de la puissance) | 8,0 | 5 | Directement vers l'EPS |
> | 4 | OBC | Carte spécifique MSP430 + STM32F4 (avec flash NOR de 4 Mo) | 30 | 0,3 | 3,0 | 1 | I²C, SPI, UART |
> | 5 | Communications | Émetteur-récepteur UHF (NanoCom AX100, 0,5 W en émission, 9600 bit/s) | 60 | 0,5 (émission) / 0,1 (réception) | 8,0 | 1 | SPI |
> | 6 | Antenne | Monopôle UHF (déployable, $\lambda/4 = 17$ cm en nitinol) | 20 | — | 2,0 | 1 | Coaxial RF |
> | 7 | Charge utile | Magnétomètre MEMS (circuit imprimé spécifique, capteur PNI RM3100) | 50 | 0,2 | 5,0 | 1 | SPI |
> | 8 | SCAO (passif) | Aimant permanent (AlNiCo, 0,5 A m$^2$) + 2 barreaux à hystérésis (HyMu-80) | 30 | 0 | 1,0 | 1 | Aucune (passif) |
> | 9 | Faisceau | Câbles internes, connecteurs, connecteur d'empilement PC/104 | 50 | — | 1,0 | 1 | Divers |
> | | **TOTAL** | | **690** | **~1,3 (crête en émission)** | **~44** | | |
>
> **Bilan de masse** (chapitre 8, tableau 8.3, phase A) :
>
> | Niveau | Masse (g) |
> |-------|----------|
> | CBE (meilleure estimation actuelle) | 690 |
> | + 20 % de marge équipement | 828 |
> | + 20 % de marge système | 994 |
> | **MEV (valeur maximale attendue)** | **994** |
> | Limite du déployeur (ISIPOD) | 2000 |
> | **Marge par rapport à la limite** | **1006 g (50 %)** |
>
> **Bilan de puissance (cas le plus défavorable : mode émission en phase éclairée) :**
>
> | Charge | Puissance (W) |
> |------|----------|
> | OBC (STM32F4 + MSP430) | 0,3 |
> | EPS au repos | 0,3 |
> | Émission UHF | 0,5 |
> | Magnétomètre | 0,2 |
> | **Total en crête** | **1,3** |
> | Puissance disponible du générateur (moyenne orbitale, fin de vie ; chapitre 9, §9.5) | 2,3 |
> | **Marge** | **1,0 W (43 %)** |
>
> **Idée essentielle :** la liste complète des équipements d'UniSat-1 compte 5 composants COTS et 2 cartes spécifiques (l'OBC et le circuit imprimé du magnétomètre). Le coût total du matériel est d'environ 44 k€, soit un ordre de grandeur de moins qu'une mission 3U type. Avec la main-d'œuvre, l'intégration et les essais, le lancement et les opérations, le coût total de la mission est de 80–150 k€ (le chapitre 13, §13.6, en donne la décomposition). Cela montre qu'une mission spatiale utile peut être réalisée pour moins que le prix d'une voiture de milieu de gamme.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Conformité à la CDS | Dimensions normalisées, rails en Al 7075-T6 anodisé (8,5 mm), interrupteurs de déploiement, goupille RBF, limites de position du centre de gravité |
| Matériaux de structure | Al 7075-T6 : $\sigma_y = 503$ MPa, $E = 72$ GPa ; anodisation pour l'usure et l'isolation ; PRFC inadapté aux rails |
| Charges au lancement | 6–12 g en axial quasi statique, 6,8 g$_{\text{rms}}$ en vibrations aléatoires (20–2000 Hz ; 9,6 g$_{\text{rms}}$ en protovol), 500–2000 g en choc ; les joints de brasure des circuits imprimés sont le point faible |
| MoS structurale | $\text{MoS} = \sigma_{\text{allow}}/(\sigma_{\text{design}} \times \text{FoS}) - 1 \geq 0$ ; FoS 1,25 en élasticité / 1,5 en rupture (métaux) |
| Exigence de fréquence | Premier mode > 40 Hz ; les structures de CubeSat en aluminium le dépassent facilement (~330 Hz pour une poutre-caisson 3U) ; le risque vient des modes locaux (circuits imprimés, éléments déployables) |
| Équation de Tsiolkovski | $m_{\text{prop}} = m_{\text{dry}} \times (e^{\Delta V/(I_{sp} g_0)} - 1)$ ; croissance exponentielle avec $\Delta V / v_e$ |
| Gaz froid | $I_{sp}$ de 40–75 s ; simple, rapide, fiable ; forte pénalité de masse d'ergols pour $\Delta V > 30$ m/s |
| Monergol vert | $I_{sp}$ de 225–250 s ; poussée élevée (0,1–1 N) ; système d'alimentation lourd ; AF-M315E et LMP-103S éprouvés en vol |
| Électronébulisation (FEEP) | $I_{sp}$ de 500–5000 s ; consommation d'ergols minimale ; poussées de plusieurs mois ; puissance de 20–60 W ; indium ou liquide ionique |
| Propulseur à effet Hall | $I_{sp}$ de 800–3000 s ; poussée modérée (1–50 mN) ; 50–300 W ; l'iode s'impose comme alternative au xénon |
| Compromis propulsifs | Forte $I_{sp}$ : moins d'ergols, plus de masse sèche, poussées longues ; faible $I_{sp}$ : plus d'ergols, système plus léger, poussées rapides |
| Quand se passer de propulsion | Sous 500 km (désorbitation naturelle) ; démonstration technologique ; constellation à traînée différentielle |
| Processeurs d'OBC | MSP430 (0,01 W, mode survie), Cortex-M4 (0,2 W, CubeSat standard), Zynq (3 W, haut débit), LEON3 (durci, ESA) |
| RTOS ou Linux | FreeRTOS pour la C&DH temps réel (standard) ; Linux pour le traitement de la charge utile (gros volumes de données) |
| Effets des radiations | TID : 1–10 krad/an en LEO ; SEU : 1–10 inversions de bit/jour/Go ; réduction par EDAC, chien de garde, redondance |
| Stockage de données | $S = V_{\text{daily}} \times N_{\text{days}} \times 2$ ; flash NAND SLC pour le stockage principal ; flash NOR pour le code et les paramètres critiques |
| Choix des équipements | Chaque choix est revérifié au regard de la masse, de la puissance, des interfaces et de la compatibilité RF ; étude de compromis pour les choix disputés |
| Bouclage des bilans | Toutes les marges doivent être positives avant le début de l'intégration et de la vérification ; marge de masse > 10 % en phase A ; les totaux issus des équipements remplacent les estimations paramétriques |

---

## Exercices

1. **Contrainte dans les rails et marge de sécurité.** Un CubeSat 6U de 11 kg est lancé avec une charge axiale quasi statique de 10 g et un facteur d'amplification dynamique de 1,3. La charge est répartie entre quatre rails en Al 6061-T6 de 8,5 × 8,5 mm. Calculez la contrainte de dimensionnement ainsi que les marges de sécurité en élasticité et en rupture à l'aide des facteurs ECSS du §12.1.6. Expliquez ensuite pourquoi une MoS positive de plusieurs centaines ne signifie pas que la structure est « surdimensionnée ».

2. **Fréquence propre fondamentale.** Reprenez l'estimation par poutre-caisson du §12.1.7 pour un CubeSat 6U (section de 226 × 100 mm, $L = 0.34$ m, 11 kg) à parois de 1,0 mm, en traitant la section comme un tube rectangulaire fléchi autour de son axe de plus faible inertie. Comparez le résultat aux exigences de 40 Hz et de 90 Hz des déployeurs. Estimez ensuite le premier mode d'un senseur stellaire de 350 g monté sur une équerre en aluminium de 40 mm et de 2 mm d'épaisseur, assimilée à une poutre en porte-à-faux, et indiquez lequel des deux modes dimensionne la conception.

3. **Équation de Tsiolkovski.** Un CubeSat 3U de 5,2 kg de masse sèche doit fournir 25 m/s de ΔV d'évitement de collision sur sa durée de vie, en plus de la poussée de désorbitation de 112 m/s du §12.2.5. Calculez la masse d'ergols pour le butane ($I_{sp} = 85$ s), l'AF-M315E ($I_{sp} = 240$ s) et un propulseur à effet Hall à iode ($I_{sp} = 1000$ s), ajoutez les masses sèches du tableau comparatif et classez les options par masse totale. Laquelle choisiriez-vous si la désorbitation doit être achevée en un mois, et pourquoi ?

4. **Durée de poussée et puissance.** Pour l'option FEEP du §12.2.5 (0,35 mN, 40 W), calculez la durée totale de poussée nécessaire à la désorbitation de 112 m/s d'un engin spatial de 5 kg, ainsi que l'énergie consommée. À partir de la puissance moyenne sur l'orbite du chapitre 9, §9.2, pour le CubeSat 3U d'observation de la Terre, déterminez si le propulseur peut fonctionner en continu ou doit être utilisé selon un rapport cyclique, et estimez la durée calendaire nécessaire à la manœuvre.

5. **Désorbitation passive.** À l'aide de la méthode de durée de vie fondée sur le coefficient balistique du chapitre 7, §7.3.3, estimez la durée de vie orbitale d'EOSat-3U (5 kg, surface frontale de 0,03 m²) à 550 km, ainsi que la surface de voile de traînée nécessaire pour la ramener sous 5 ans. Comparez la masse et le volume replié de la voile (tableau du §12.2.4) avec ceux du système à gaz froid du §12.2.5, et recommandez une solution.

6. **Choix du processeur.** Un CubeSat 3U d'observation de la Terre doit exécuter une boucle de contrôle d'attitude à 10 Hz, compresser à 10:1, en temps quasi réel, 240 Mbit/s d'imagerie brute et survivre à une mission de 3 ans en SSO à 550 km. À l'aide du tableau des processeurs du §12.3.1, proposez une architecture d'OBC (un ou deux processeurs), justifiez le choix du système d'exploitation pour chacun et dressez la liste des mesures de protection contre les radiations que vous appliqueriez.

7. **Dimensionnement du stockage.** Un CubeSat 6U hyperspectral génère 60 Go/jour et transmet ses données en bande X à 150 Mbit/s, avec six passages de 8 minutes par jour et $\eta_{\text{protocol}} = 0.85$. Vérifiez si le bilan de données boucle (chapitre 11, §11.9), dimensionnez le stockage à bord pour $N_{\text{days}} = 2$ et $f_{\text{safety}} = 2$, et choisissez une technologie de stockage dans le tableau du §12.3.3 en justifiant votre choix notamment au regard des radiations.

8. **Bilans issus des équipements ou bilans paramétriques.** Au §12.5.3, la puissance du mode prise de vue issue des équipements dépasse l'allocation paramétrique. Recalculez la puissance moyenne sur l'orbite du chapitre 8, §8.4.3, avec les valeurs des équipements (prise de vue à 10 W, autres modes inchangés) et les rapports cycliques des modes du tableau 8.4, et déterminez si le générateur du chapitre 9, §9.2, permet encore de boucler. Proposez ensuite deux modifications de conception qui rétabliraient l'allocation de 8 W et indiquez ce que chacune coûte sur un autre bilan.

9. **Bouclage des bilans pour une mission modifiée.** À partir de la liste d'équipements d'EOSat-3U du §12.5.2, ajoutez un système de propulsion à gaz froid (1,35 kg, 15 k€, < 1 W) pour satisfaire une exigence de retrait de service en 5 ans. Recalculez le bilan de masse avec les marges de phase A du chapitre 8, tableau 8.3, ainsi que le coût, reclassez chaque ligne du tableau de bouclage du §12.5.3 et indiquez quel remède du §12.5.4 vous appliqueriez en premier.

10. **Changement de déployeur pour UniSat-1.** UniSat-1 est réaffecté à un déployeur imposant une limite de 1,33 kg et un premier mode à 90 Hz. Revérifiez chaque ligne du tableau de conformité du §12.6, recalculez la marge de masse et identifiez le composant dont la croissance en masse menacerait le plus rapidement la nouvelle limite.

---

## Références

1. Cal Poly, *CubeSat Design Specification (CDS) Rev 14.1*, février 2022. https://www.cubesat.org/cubesatinfo
2. Wertz, J. R., Everett, D. F. & Puschell, J. J. (dir.), *Space Mission Engineering: The New SMAD*, Microcosm Press, 2011, chap. 11.3 (*Structures*), chap. 17 (*Propulsion*). https://www.space.com/smad
3. ECSS, *ECSS-E-ST-32C Rev. 1: Structural General Requirements*, 2008. https://ecss.nl/standard/ecss-e-st-32c-rev-1-structural-general-requirements/
4. ECSS, *ECSS-E-ST-32-10C Rev. 2: Structural Factors of Safety for Spaceflight Hardware*, 2019. https://ecss.nl
5. ECSS, *ECSS-E-ST-35C: Propulsion General Requirements*, 2008. https://ecss.nl/standard/ecss-e-st-35c-propulsion-general-requirements/
6. ECSS, *ECSS-E-ST-10-03C: Testing*, 2012. https://ecss.nl/standard/ecss-e-st-10-03c-testing/
7. Sarafin, T. P. (dir.), *Spacecraft Structures and Mechanisms: From Concept to Launch*, Springer, 1995. https://www.springer.com/gp/book/9780792334767
8. Sutton, G. P. & Biblarz, O., *Rocket Propulsion Elements*, 9e éd., Wiley, 2017, chap. 2–4. https://www.wiley.com/en-us/Rocket+Propulsion+Elements
9. Goebel, D. M. & Katz, I., *Fundamentals of Electric Propulsion: Ion and Hall Thrusters*, Wiley, 2008.
10. Masse, R. K. et al., « Enabling High Performance Green Propulsion for SmallSats », *AIAA Propulsion and Energy Forum*, 2019.
11. Anflo, K. & Crowe, B., « In-Space Demonstration of an ADN-based Propulsion System », *AIAA Joint Propulsion Conference*, 2011.
12. Enpulsion, *NANO R3 Thruster Datasheet*, 2023 (exemple représentatif). https://www.enpulsion.com/nano
13. VACCO, *MiPS Propulsion System Datasheet*, 2023 (exemple représentatif). https://www.cubesat-propulsion.com
14. NASA, *General Environmental Verification Standard (GEVS)*, GSFC-STD-7000B, 2021.
15. Cobham Gaisler, *LEON3 Processor Datasheet* ; STMicroelectronics, *STM32F4 Datasheet* ; Xilinx, *Zynq-7000 SoC Datasheet* (exemples représentatifs).
