# Chapitre 7 — Choix de l'orbite et environnement spatial

> **Lectures préalables conseillées.** SMAD4 chap. 5–7 (géométrie de l'orbite et de la mission) ; Vallado, *Fundamentals of Astrodynamics and Applications*, chap. 2 et 9 ; ECSS-E-ST-10-04C (environnement spatial) ; ECSS-U-AS-10C Rev.2 (atténuation des débris). Les démonstrations de la troisième loi de Kepler, de la régression nodale due au J₂ et de la fraction d'éclipse figurent dans la partie V (§V.2, §V.4, §V.5) ; ce chapitre en utilise les résultats.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez en mesure de :

1. définir les six éléments orbitaux képlériens et les réduire aux trois qui comptent pour la conception d'une orbite LEO circulaire ;
2. calculer la période orbitale, la vitesse et la fraction d'éclipse d'orbites circulaires, y compris leur dépendance à l'angle bêta solaire ;
3. calculer l'inclinaison héliosynchrone à partir de la précession nodale due au J₂ ;
4. évaluer les compromis d'orbite en fonction de l'altitude, de la couverture, de la durée de vie, des rayonnements et de la conformité aux règles sur les débris, et estimer la durée de vie orbitale à partir des premiers principes ;
5. appliquer les équations de ΔV du transfert de Hohmann au relèvement d'orbite et à la désorbitation ;
6. noter des orbites candidates selon des critères adaptés à la mission et justifier le choix retenu.

---

## 7.1 Éléments orbitaux képlériens

Six paramètres (les *éléments orbitaux classiques*) décrivent entièrement la taille, la forme et l'orientation d'une orbite, ainsi que la position du satellite sur celle-ci.

*[Source : Vallado, chap. 2 ; Curtis, chap. 2]*

| Élément | Symbole | Signification physique | Plage typique |
|---------|--------|-----------------|---------------|
| Demi-grand axe | $a$ | Taille de l'orbite | 6578–42 164 km (de LEO à GEO) |
| Excentricité | $e$ | Forme (0 = cercle, 0 < e < 1 = ellipse) | 0–0,001 pour une orbite LEO circulaire |
| Inclinaison | $i$ | Inclinaison du plan orbital par rapport au plan équatorial | 0–180° |
| RAAN | $\Omega$ | Orientation du nœud ascendant dans le plan équatorial | 0–360° |
| Argument du périgée | $\omega$ | Orientation du périgée dans le plan orbital | 0–360° |
| Anomalie vraie | $\nu$ | Position du satellite sur l'orbite | 0–360° |

Pour les missions en **orbite LEO circulaire** (le type d'orbite le plus courant pour les CubeSats), les paramètres de conception essentiels se réduisent à trois : l'**altitude** ($h$), l'**inclinaison** ($i$) et la **LTAN** (heure locale du nœud ascendant, pour les orbites héliosynchrones). La figure 7.1 en esquisse la géométrie.

<svg viewBox="0 0 500 400" xmlns="http://www.w3.org/2000/svg" style="max-width:450px; font-family: sans-serif; font-size: 11px;">
  <!-- Earth -->
  <circle cx="250" cy="200" r="80" fill="#bfdbfe" stroke="#2563eb" stroke-width="2"/>
  <text x="250" y="205" text-anchor="middle" fill="#1e3a5f" font-size="12">Terre</text>
  <!-- Equatorial plane -->
  <ellipse cx="250" cy="200" rx="160" ry="30" fill="none" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="420" y="195" fill="#94a3b8" font-size="10">Plan équatorial</text>
  <!-- Orbit ellipse (tilted) -->
  <ellipse cx="250" cy="185" rx="160" ry="120" fill="none" stroke="#dc2626" stroke-width="2" transform="rotate(-15, 250, 185)"/>
  <!-- Ascending node -->
  <circle cx="405" cy="195" r="5" fill="#dc2626"/>
  <text x="415" y="200" fill="#dc2626" font-weight="bold">AN</text>
  <!-- Labels -->
  <text x="250" y="50" text-anchor="middle" fill="#dc2626" font-weight="bold">Plan orbital (incliné)</text>
  <line x1="250" y1="200" x2="250" y2="100" stroke="#16a34a" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="260" y="145" fill="#16a34a" font-size="10">i (inclinaison)</text>
  <!-- RAAN arrow -->
  <path d="M 330 200 A 80 15 0 0 1 370 195" fill="none" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="345" y="220" fill="#7c3aed" font-size="10">Ω (RAAN)</text>
  <!-- Satellite -->
  <rect x="310" y="88" width="12" height="8" fill="#f59e0b" stroke="#92400e"/>
  <text x="330" y="95" fill="#92400e" font-size="10">Satellite</text>
</svg>

**Figure 7.1** — Géométrie de l'orbite : le plan orbital incliné, le plan équatorial, le nœud ascendant (AN), l'inclinaison $i$ et l'ascension droite du nœud ascendant $\Omega$.

### 7.1.1 Équations clés

Dans tout ce manuel, les constantes terrestres sont $R_E = 6378.137$ km (rayon équatorial WGS-84), $\mu = 398\,600.44$ km³/s² $= 3.986\,00 \times 10^{14}$ m³/s² et $J_2 = 1.0826 \times 10^{-3}$ (partie V, §V.1).

> **Équations clés — fondamentaux de mécanique spatiale**
>
> **Période orbitale** (orbite circulaire ; partie V, §V.2) :
> $$T = 2\pi \sqrt{\frac{a^3}{\mu}}$$
> où $a = R_E + h$ est le demi-grand axe.
>
> **Vitesse orbitale** (orbite circulaire) :
> $$v = \sqrt{\frac{\mu}{a}}$$
>
> **Inclinaison héliosynchrone** (précession de la RAAN due au $J_2$ de 360° par an ; partie V, §V.4) :
> $$\cos i = -\frac{2 \dot{\Omega}_{\text{req}} \, a^{7/2}}{3 R_E^2 \, J_2 \, \sqrt{\mu}}$$
> où $\dot{\Omega}_{\text{req}} = \dfrac{2\pi}{365.25 \times 86\,400} = 1.991 \times 10^{-7}$ rad/s.

### 7.1.2 Fraction d'éclipse et angle bêta

Qu'une orbite circulaire traverse l'ombre de la Terre, et pendant combien de temps, dépend de l'**angle bêta solaire** : l'angle entre la direction du Soleil et le plan orbital. On l'obtient à partir de l'orientation de l'orbite et de la position du Soleil (ascension droite $\alpha_\odot$, déclinaison $\delta_\odot$) :

$$\sin\beta = \cos\delta_\odot \sin i \sin(\Omega - \alpha_\odot) + \sin\delta_\odot \cos i$$

Comme $\Omega$ précesse et que le Soleil se déplace le long de l'écliptique, β varie au cours de l'année. Sur une orbite héliosynchrone, la précession suit le Soleil, si bien que β reste dans une bande étroite fixée par la LTAN (une orbite aube-crépuscule a un $|\beta|$ voisin de 90° et n'est presque jamais éclipsée ; une orbite à LTAN 10 h 30 a un $|\beta|$ de l'ordre de 20 à 30°). Sur une orbite de type ISS, β balaie une large plage et peut atteindre la condition d'éclairement permanent pendant quelques jours d'affilée.

> **Équation clé — fraction d'éclipse (orbite circulaire, ombre cylindrique ; partie V, §V.5)**
>
> On définit le demi-angle de l'ombre vu depuis l'orbite, $\beta^* = \arcsin\!\left(\dfrac{R_E}{R_E + h}\right)$. Pour $|\beta| < \beta^*$,
> $$f_{\text{ecl}} = \frac{1}{\pi} \arccos\left(\frac{\sqrt{h^2 + 2 R_E h}}{(R_E + h)\cos\beta}\right)$$
> et pour $|\beta| \geq \beta^*$, l'orbite est entièrement éclairée ($f_{\text{ecl}} = 0$).
>
> **Corollaire — cas le plus défavorable, β = 0** (Soleil dans le plan orbital). Comme $\sqrt{h^2 + 2R_E h}/(R_E + h) = \sqrt{1 - (R_E/(R_E+h))^2} = \cos\beta^*$, la fraction d'éclipse maximale vaut simplement
> $$f_{\text{ecl,max}} = \frac{\beta^*}{\pi} = \frac{1}{\pi}\arcsin\!\left(\frac{R_E}{R_E + h}\right)$$
> C'est la valeur retenue pour le dimensionnement de la puissance au chapitre 9, sauf si l'on sait que l'historique de l'angle bêta de la mission exclut β = 0.

La figure 7.2 montre les deux volets de ce comportement : l'enveloppe annuelle de l'angle bêta pour une orbite de type ISS et pour une orbite héliosynchrone à LTAN 10 h 30 (à gauche), et la fraction d'éclipse en fonction de β, avec son plateau autour de β = 0 et sa chute brutale à zéro en $\beta^*$ (à droite).

![Enveloppe de l'angle β sur une année et fraction d'éclipse en fonction de β.](../assets/figures/fig_beta_eclipse.png)

**Figure 7.2** — À gauche : enveloppe annuelle de l'angle β pour une orbite de type ISS (51,6°, 400 km) et une orbite héliosynchrone à LTAN 10 h 30 (98°, 600 km). À droite : fraction d'éclipse en fonction de β pour ces deux mêmes orbites ; le plateau aux faibles |β| correspond à la valeur la plus défavorable retenue pour le dimensionnement de la puissance, et l'orbite est entièrement éclairée au-delà de $\beta^*$ (≈ 70° à 400 km, ≈ 66° à 600 km).

---

## 7.2 Exemples résolus : calculs orbitaux

> **Exemple résolu — orbite LEO circulaire à 500 km**
>
> **Données :** $h = 500$ km, orbite circulaire.
>
> **Étape 1 — Demi-grand axe :**
> $a = 6378.137 + 500 = 6878.137$ km $= 6.878 \times 10^6$ m
>
> **Étape 2 — Période orbitale :**
> $a^3 = 6878.137^3 = 3.254 \times 10^{11}$ km³ ; $\quad a^3/\mu = 3.254 \times 10^{11} / 398\,600.44 = 8.163 \times 10^{5}$ s²
>
> $T = 2\pi \sqrt{8.163 \times 10^{5}} = 2\pi \times 903.5 = 5677$ s $\approx$ **94,6 min**
>
> **Étape 3 — Vitesse orbitale :**
> $v = \sqrt{\dfrac{398\,600.44}{6878.137}} = \sqrt{57.95} =$ **7,613 km/s**
>
> **Étape 4 — Demi-angle de l'ombre et fraction d'éclipse maximale (β = 0) :**
> $\beta^* = \arcsin\!\left(\dfrac{6378.137}{6878.137}\right) = \arcsin(0.9273) = 68.0°$
>
> Vérification par la forme générale : $\sqrt{h^2 + 2R_E h} = \sqrt{500^2 + 2 \times 6378.137 \times 500} = \sqrt{6\,628\,137} = 2574.5$ km ; $\;2574.5/6878.137 = 0.3743$ ; $\;\arccos(0.3743) = 68.0°$ ✓
>
> $f_{\text{ecl,max}} = 68.0/180 =$ **0,378** (37,8 %)
>
> **Étape 5 — Durées d'éclipse et d'ensoleillement :**
> $t_{\text{ecl}} = 94.6 \times 0.378 =$ **35,8 min** ; $\quad t_{\text{sun}} = 94.6 - 35.8 =$ **58,8 min**
>
> **Étape 6 — Inclinaison héliosynchrone :**
> $a^{7/2} = a^3 \sqrt{a} = 3.254 \times 10^{20} \times 2622.6 = 8.534 \times 10^{23}$ (unités SI)
>
> Numérateur : $2 \times 1.991 \times 10^{-7} \times 8.534 \times 10^{23} = 3.398 \times 10^{17}$
>
> Dénominateur : $3 \times (6.378137 \times 10^6)^2 \times 1.0826 \times 10^{-3} \times \sqrt{3.986 \times 10^{14}} = 3 \times 4.068 \times 10^{13} \times 1.0826 \times 10^{-3} \times 1.9965 \times 10^{7} = 2.638 \times 10^{18}$
>
> $\cos i = -\dfrac{3.398 \times 10^{17}}{2.638 \times 10^{18}} = -0.1288 \Rightarrow i \approx$ **97,4°**

> **Vérification — orbite héliosynchrone à 450 km** (l'altitude retenue pour la vérification de la partie V, §V.2) :
> $a = 6828.137$ km ; $a^3/\mu = 3.1835 \times 10^{11}/398\,600.44 = 7.987 \times 10^{5}$ s² ; $\sqrt{\cdot} = 893.7$ s ; $T = 2\pi \times 893.7 = 5615$ s $\approx$ **93,6 min**. L'ancienne valeur $R_E = 6371$ km donne 93,5 min ; l'écart est inférieur à 0,2 %, mais tous les nombres de ce manuel utilisent 6378,137 km afin que les chapitres concordent.

---

## 7.3 Compromis pour le choix de l'orbite

L'orbite est la décision de conception initiale qui a le plus de conséquences. Elle se répercute sur tous les sous-systèmes.

*[Source : SMAD, chap. 7 ; Wertz et al., « Reducing Space Mission Cost », chap. 3]*

| Paramètre | Altitude basse (300–400 km) | Altitude haute (600–800 km) |
|-----------|------------------------------|-------------------------------|
| **GSD** | Meilleure (distance à la cible plus courte) | Moins bonne (distance plus longue) |
| **Durée de vie orbitale** | Courte (de quelques mois à quelques années, déclin naturel) | Longue (25–100+ ans) |
| **Conformité débris** | Facile (règle des 5 ans de la FCC respectée naturellement) | Peut exiger une propulsion de désorbitation active |
| **Rayonnements (TID)** | Plus faibles (2–5 krad/an) | Plus élevés (10–20 krad/an au-dessus de 700 km) |
| **Coût de lancement** | ΔV de mise en orbite plus faible | Légèrement plus élevé |
| **Bilan de liaison** | Meilleur (distance oblique plus courte) | Moins bon (affaiblissement de propagation plus grand) |
| **Couverture/fauchée** | Plus étroite par passage | Plus large par passage |
| **Traînée atmosphérique** | Importante (limite la durée de vie) | Négligeable au-dessus de ~700 km |
| **Fraction d'éclipse (β = 0)** | ~38–39 % | ~35–37 % |

### 7.3.1 Types d'orbites et applications

| Orbite | Altitude | Inclinaison | Adaptée à | Exemple réel |
|-------|----------|-------------|----------|-------------|
| **LEO (hors SSO)** | 300–600 km | Quelconque | Démonstrateurs technologiques, déploiement depuis l'ISS | De nombreux CubeSats |
| **SSO** | 400–800 km | 97–99° | Observation de la Terre (éclairement solaire constant) | Planet SuperDove (475 km) |
| **Orbite de l'ISS** | ~410 km | 51,6° | CubeSats déployés depuis l'ISS | Déploiements NanoRacks |
| **MEO** | 2000–20 200 km | Variable | Navigation | GPS (20 200 km) |
| **GEO** | 35 786 km | 0° | Télécommunications, météorologie | Anik F2 (Telesat) |
| **HEO (Molniya)** | 500–40 000 km | 63,4° | Couverture des hautes latitudes | Meridian (Russie) |
| **NRHO lunaire** | 1500–70 000 km | Lunaire | Opérations cislunaires | CAPSTONE (NASA/Advanced Space) |

### 7.3.2 Règles relatives aux débris

| Règle | Exigence | S'applique à |
|------|------------|-----------|
| **Ligne directrice de l'IADC** (2021) | Retrait de service dans les 25 ans | International (volontaire mais attendu) |
| **Règle de la FCC** (2024+) | Retrait de service dans les **5 ans** | Tous les satellites LEO sous licence de la FCC |
| **ECSS-U-AS-10C Rev.2** | Conformité aux règles de l'IADC et à la Charte Zéro Débris de l'ESA | Missions de l'ESA |
| **ISDE (Canada)** | Règle des 25 ans à ce jour ; durcissement à l'étude | Satellites sous licence canadienne |

**Altitudes charnières pour la conformité à la règle des 5 ans de la FCC** (coefficients balistiques typiques des CubeSats, activité solaire moyenne) :

| Altitude | Durée de vie naturelle | Conforme FCC ? | Action requise |
|----------|-----------------|---------------|---------------|
| < 450 km | < 5 ans | Oui | Aucune (déclin naturel) |
| 450–550 km | 5–20 ans | Limite | Une augmentation de traînée peut suffire |
| 550–650 km | 20–50 ans | **Non** | Désorbitation active (propulsion ou voile de traînée) |
| > 700 km | > 100 ans | **Non** | Propulsion obligatoire ; zone Zéro Débris de l'ESA |

*[Source : IADC-02-01 Rev 3, sect. 5.3.2 ; FCC 22-74 ; ECSS-U-AS-10C Rev.2]*

### 7.3.3 Durée de vie orbitale à partir des premiers principes

Le chapitre 3, §3.6.4, a présenté le coefficient balistique $B = m/(C_D A)$, l'abaque durée de vie/altitude (figure 3.2) et une règle empirique rapide. Cette règle empirique est un ajustement de courbe valable pour des engins spatiaux d'altitude moyenne et de $B$ modéré, et elle surestime fortement la durée de vie au-dessous d'environ 500 km (elle donne ~18 ans à 400 km pour un CubeSat 3U de 4 kg et 0,03 m², ce qui est faux de plus d'un ordre de grandeur). L'estimation fondée sur la physique est courte et mérite d'être faite correctement.

Pour une orbite circulaire, la traînée fait décroître le demi-grand axe au rythme

$$\frac{da}{dt} = -\sqrt{\mu a}\,\frac{\rho}{B}, \qquad B = \frac{m}{C_D A}$$

(ce résultat découle de la décroissance par orbite $\Delta a = -2\pi\,\rho\,a^2/B$ divisée par la période). Comme la masse volumique atmosphérique décroît à peu près exponentiellement avec l'altitude, $\rho \propto e^{-h/H}$ avec une hauteur d'échelle $H$, la quasi-totalité de la durée de vie restante s'écoule dans la première hauteur d'échelle sous l'altitude initiale, d'où

$$\tau \approx \frac{H}{|da/dt|_{h_0}} = \frac{H\,B}{\rho(h_0)\sqrt{\mu a}}$$

> **Exemple résolu — durée de vie d'un CubeSat 3U à 400 km et à 500 km**
>
> **Données :** $m = 4$ kg, surface moyenne en culbutage $A = 0.03$ m², $C_D = 2.2$, d'où $B = 4/(2.2 \times 0.03) = 60.6$ kg/m².
>
> **400 km, activité solaire moyenne :** $\rho \approx 2.8 \times 10^{-12}$ kg/m³, $H \approx 58$ km.
> $\sqrt{\mu a} = \sqrt{3.986 \times 10^{14} \times 6.778 \times 10^{6}} = 5.20 \times 10^{10}$ m²/s
> $|da/dt| = 5.20 \times 10^{10} \times 2.8 \times 10^{-12} / 60.6 = 2.4 \times 10^{-3}$ m/s $= 207$ m/jour $= 76$ km/an
> $\tau \approx 58 / 76 \approx 0.76$ an $\approx$ **9 mois**
>
> Sur le cycle solaire, la masse volumique à 400 km varie d'un facteur 8 environ ($\sim 1 \times 10^{-12}$ au minimum solaire à $\sim 8 \times 10^{-12}$ au maximum solaire), si bien que la durée de vie va d'environ **3 mois (maximum solaire) à environ 2 ans (minimum solaire)**.
>
> **500 km, activité solaire moyenne :** $\rho \approx 5 \times 10^{-13}$ kg/m³, $H \approx 65$ km, $\sqrt{\mu a} = 5.24 \times 10^{10}$ m²/s.
> $|da/dt| = 5.24 \times 10^{10} \times 5 \times 10^{-13} / 60.6 = 4.3 \times 10^{-4}$ m/s $= 13.6$ km/an ; $\quad \tau \approx 65/13.6 \approx$ **5 ans** (environ 2 à 12 ans sur le cycle).
>
> **Lecture du résultat.** À 400 km, un CubeSat 3U rentre naturellement dans l'atmosphère en un an environ et n'a besoin d'aucun dispositif de désorbitation ; à 500 km, la conception se situe à la limite des 5 ans de la FCC et la réponse dépend de la date de lancement dans le cycle solaire. Pour obtenir une valeur précise, utilisez un modèle de masse volumique (NRLMSISE-00 ou JB2008) et une propagation numérique — mais l'estimation ci-dessus est exacte à un facteur deux près, ce qui suffit pour décider si un sous-système de désorbitation est nécessaire.

### 7.3.4 Effets des perturbations

| Perturbation | Cause | Effet sur l'orbite | Incidence sur la conception |
|-------------|-------|----------------|---------------|
| **$J_2$ (aplatissement terrestre)** | Renflement équatorial | Précession de la RAAN, dérive de l'argument du périgée | Rend possible l'orbite héliosynchrone ; orbites gelées à $\omega = 90°$ |
| **Traînée atmosphérique** | Atmosphère résiduelle | Déclin du demi-grand axe, rentrée à terme | Limite la durée de vie sous ~600 km ; impose un besoin de propulsion |
| **Pression de radiation solaire** | Quantité de mouvement des photons | Oscillations de l'excentricité, perturbation de l'orbite | Importante pour un rapport A/m élevé (voiles de traînée, grands générateurs solaires) |
| **Troisième corps (Lune/Soleil)** | Attraction gravitationnelle | Oscillations à longue période de $e$, $i$ | Importante en GEO et HEO ; négligeable en LEO |
| **Champ magnétique** | Force de Lorentz sur l'engin spatial chargé | Effet très faible, analogue à une traînée | Négligeable pour la plupart des missions |

---

## 7.4 Couverture au sol et revisite

> **Équations clés — couverture au sol**
>
> **Largeur de fauchée** (capteur pointé au nadir, de demi-angle au sommet $\theta$) :
> $$W_{\text{swath}} = 2h \tan\theta$$
>
> **Écart entre traces au sol** (satellite unique en LEO). La Terre tourne sous l'orbite de $\omega_E T$ à chaque révolution ; pour $T = 94.6$ min,
> $$\Delta_{\text{lon}} = \frac{360°}{86\,164 \text{ s}} \times 5677 \text{ s} \approx 23.7° \approx 2640 \text{ km à l'équateur}$$
> (pour une orbite héliosynchrone, la précession nodale ajoute environ 0,07° par orbite en sens inverse — négligeable ici).
>
> **Temps de revisite** (approximatif, satellite unique, fauchée plus étroite que l'écart entre traces) :
> $$t_{\text{revisit}} \approx \frac{\Delta_{\text{lon}}}{W_{\text{swath}}} \times T_{\text{orbit}}$$
>
> **Revisite d'une constellation** ($N$ satellites identiques, régulièrement phasés) :
> $$t_{\text{revisit,constellation}} \approx \frac{t_{\text{revisit,single}}}{N}$$

**Exemple — constellation SuperDove :** Planet exploite environ 200 satellites SuperDove. Avec une fauchée d'environ 24 km à 475 km d'altitude, la revisite d'un satellite unique à l'équateur serait de $(2640/24) \times 94.6$ min $\approx 110$ orbites $\approx 7$ jours ; grâce à plusieurs plans orbitaux, la constellation assure une revisite quotidienne de l'ensemble du globe.

La figure 7.3 montre une révolution et demie de la trace au sol d'une orbite héliosynchrone à 600 km. Chaque passage successif au nœud ascendant est décalé vers l'ouest de $\Delta_{\text{lon}}$, la trace atteint la latitude $\pm(180° - i) \approx \pm 82°$, et un site de latitude moyenne comme Ottawa n'est survolé que lors d'une fraction des passages quotidiens — c'est pourquoi la fauchée, et non l'orbite seule, fixe la revisite.

![Trace au sol d'une orbite héliosynchrone à 600 km.](../assets/figures/fig_ground_track.png)

**Figure 7.3** — Trace au sol d'une orbite héliosynchrone à 600 km ($i = 97.79°$) sur une révolution et demie. Les traces successives se décalent vers l'ouest de la rotation de la Terre pendant une orbite (≈ 24°) ; la latitude maximale atteinte est $180° - i$.

### 7.4.1 Géométrie des contacts avec la station sol

La durée d'un passage dépend de l'élévation minimale $\varepsilon_{\min}$ à laquelle la station peut assurer la poursuite (typiquement 5 à 10°). L'angle au centre de la Terre entre la station et le satellite à cette élévation vaut

$$\lambda_{\max} = \arccos\!\left(\frac{R_E}{R_E + h}\cos\varepsilon_{\min}\right) - \varepsilon_{\min}$$

et le passage le plus long (au zénith) dure environ

$$t_{\text{contact,max}} \approx \frac{T}{\pi}\,\lambda_{\max} \quad (\lambda_{\max} \text{ en radians})$$

> **Exemple — 500 km, $\varepsilon_{\min} = 10°$ :** $\dfrac{R_E}{R_E+h}\cos 10° = 0.9273 \times 0.9848 = 0.9132$ ; $\arccos(0.9132) = 24.0°$ ; $\lambda_{\max} = 24.0° - 10° = 14.0° = 0.245$ rad ; $t_{\text{contact,max}} = (5677/\pi) \times 0.245 \approx 442$ s $\approx$ **7,4 min**. Avec un masque de 5°, la même orbite donne $\lambda_{\max} = 17.5°$ et environ 9,2 min.

**Règles empiriques** pour une orbite LEO à 500 km avec un masque de 10° : passage maximal ≈ 7 à 8 min (au zénith), passage moyen ≈ 5 min, et 4 à 6 passages exploitables par jour depuis une station de latitude moyenne. Le chapitre 17 développe la géométrie complète des passages (distance oblique, Doppler et profil d'élévation) pour la conception du segment sol.

---

## 7.5 Transfert de Hohmann et désorbitation

> **Équations clés — transfert de Hohmann** (la partie V, §V.3, donne la vérification de vraisemblance LEO → GEO)
>
> Le transfert biimpulsionnel à énergie minimale entre deux orbites circulaires coplanaires de rayons $r_1$ et $r_2$ :
>
> $$\Delta V_1 = \sqrt{\frac{\mu}{r_1}} \left(\sqrt{\frac{2r_2}{r_1 + r_2}} - 1\right)$$
>
> $$\Delta V_2 = \sqrt{\frac{\mu}{r_2}} \left(1 - \sqrt{\frac{2r_1}{r_1 + r_2}}\right)$$
>
> $$\Delta V_{\text{total}} = |\Delta V_1| + |\Delta V_2|$$

La figure 7.4 illustre la géométrie dans le cas classique LEO-GEO : une poussée au périgée élève l'apogée jusqu'au rayon visé, et une seconde poussée à l'apogée circularise l'orbite. Les mêmes équations, avec $r_2 < r_1$, décrivent une poussée de désorbitation.

![Transfert de Hohmann d'une orbite LEO à 400 km vers l'orbite GEO.](../assets/figures/fig_hohmann.png)

**Figure 7.4** — Transfert de Hohmann d'une orbite circulaire à 400 km vers l'orbite GEO : $\Delta V_1 \approx 2.40$ km/s au périgée, $\Delta V_2 \approx 1.46$ km/s à l'apogée, total ≈ 3,85 km/s, durée du transfert ≈ 5,3 h. La partie V, §V.3, retrouve ces valeurs.

> **Exemple résolu — désorbitation de 600 km vers un périgée de rentrée à 200 km**
>
> $r_1 = 6378.137 + 600 = 6978.137$ km, $\quad r_2 = 6378.137 + 200 = 6578.137$ km
>
> $\sqrt{\mu/r_1} = \sqrt{398\,600.44/6978.137} = \sqrt{57.12} = 7.558$ km/s
>
> $\sqrt{\dfrac{2r_2}{r_1 + r_2}} = \sqrt{\dfrac{13\,156.27}{13\,556.27}} = \sqrt{0.9705} = 0.9851$
>
> $\Delta V_1 = 7.558 \times (0.9851 - 1) = 7.558 \times (-0.0149) = -0.112$ km/s
>
> $\Delta V_{\text{deorbit}} \approx$ **112 m/s** (seule la première poussée est nécessaire — une fois le périgée situé dans l'atmosphère dense, la traînée achève le travail)

Ce ΔV de désorbitation est une donnée d'entrée essentielle du dimensionnement de la propulsion au chapitre 12 et de la décision de conformité aux règles sur les débris du §7.3.2.

---

## 7.6 Environnement radiatif

*[Source : ECSS-E-ST-10-04C Rev.1 ; SMAD, chap. 8.1]*

### 7.6.1 Dose ionisante totale (TID) selon l'orbite

La dose qu'accumule un engin spatial en LEO est dominée par les protons piégés de la ceinture de Van Allen intérieure, qu'il traverse dans l'anomalie de l'Atlantique Sud (§7.6.2) ; elle croît fortement avec l'altitude et décroît avec l'épaisseur du blindage. La figure 7.5 montre cette tendance pour les trois épaisseurs de blindage entre lesquelles le concepteur d'un CubeSat peut réalistement choisir, et le tableau qui suit donne les valeurs par orbite derrière 2 mm d'aluminium.

![Dose ionisante totale annuelle en fonction de l'altitude pour des blindages de 1, 2 et 4 mm d'aluminium, avec les plages du tableau repérées.](../assets/figures/fig_tid_altitude.png)

**Figure 7.5** — Dose ionisante totale due aux protons piégés en fonction de l'altitude pour 1, 2 et 4 mm de blindage en aluminium. La courbe à 2 mm est un ajustement illustratif passant par les plages du tableau ci-dessous (barres grises) ; diviser le blindage par deux multiplie à peu près la dose par deux ou trois, le doubler la divise à peu près par deux. Au-dessous d'environ 600 km, l'électronique commerciale survit à des missions de plusieurs années avec un blindage modeste ; au-dessus, les rayonnements deviennent un facteur dimensionnant.

| Orbite | TID (krad/an derrière 2 mm d'Al) | Classe d'électronique |
|-------|-------------------------------|-------------------|
| ISS (410 km, 51,6°) | 2–5 | COTS commerciaux acceptables |
| SSO 500 km | 5–10 | Commerciale / tolérante aux rayonnements |
| SSO 800 km | 10–20 | Tolérante aux rayonnements recommandée |
| MEO 2000 km | 50–100 | Durcie aux rayonnements obligatoire |
| GEO 35 786 km | 10–20 | Durcie aux rayonnements obligatoire |

**Règle empirique :** en LEO sous 600 km, une électronique commerciale COTS peut survivre à des missions de 3 ans avec un blindage modeste (2–3 mm d'équivalent Al). Au-dessus de 600 km, les rayonnements deviennent un facteur dimensionnant important et le coût des composants augmente fortement.

### 7.6.2 Anomalie de l'Atlantique Sud (SAA)

Entre 200 et 600 km d'altitude au-dessus de l'Amérique du Sud, les protons piégés de la ceinture de Van Allen intérieure descendent à des altitudes plus basses. La SAA provoque :

- des aléas logiques (SEU) dans les mémoires ;
- des verrouillages par ion lourd (SEL) dans les circuits CMOS ;
- une augmentation du bruit de fond dans les détecteurs optiques.

Parades : mémoire à correction d'erreurs (EDAC), temporisateurs chien de garde, circuits de protection contre le verrouillage (*latch-up*).

---

## 7.7 Exemple résolu : choix de l'orbite d'UniSat-1

Retour sur UniSat-1, le démonstrateur 1U du chapitre 1, §1.7 : il retient l'orbite de l'ISS (400 km, 51,6°) non par optimisation, mais pour des raisons d'**accès**. Le déploiement depuis l'ISS au moyen d'un déployeur commercial constitue l'occasion de lancement la moins chère et la plus accessible pour un CubeSat 1U universitaire.

> **Exemple résolu — paramètres orbitaux à 400 km, 51,6°**
>
> **Étape 1 — Demi-grand axe :**
> $a = 6378.137 + 400 = 6778.137$ km $= 6.778 \times 10^6$ m
>
> **Étape 2 — Période orbitale :**
> $a^3/\mu = 3.114 \times 10^{11}/398\,600.44 = 7.813 \times 10^{5}$ s² ; $\quad T = 2\pi \times 883.9 = 5554$ s $\approx$ **92,6 min**
>
> **Étape 3 — Vitesse orbitale :**
> $v = \sqrt{398\,600.44/6778.137} = \sqrt{58.81} =$ **7,669 km/s**
>
> **Étape 4 — Fraction d'éclipse maximale (β = 0) :**
> $\beta^* = \arcsin(6378.137/6778.137) = \arcsin(0.9410) = 70.2°$ ; $\quad f_{\text{ecl,max}} = 70.2/180 \approx$ **0,390** (39,0 %)
>
> **Étape 5 — Durées d'éclipse et d'ensoleillement :**
> $t_{\text{ecl}} = 92.6 \times 0.390 \approx$ **36 min** ; $\quad t_{\text{sun}} = 92.6 - 36 \approx$ **56,5 min**
>
> **Étape 6 — Durée de vie** (§7.3.3) : $m = 1.3$ kg, $A = 0.01$ m², $B = 1.3/(2.2 \times 0.01) = 59$ kg/m² — presque le même coefficient balistique que dans le cas 3U, donc la même réponse : **environ 9 mois en activité solaire moyenne, de 3 mois à 2 ans sur le cycle.**

**Pourquoi cette orbite convient à UniSat-1 :**

| Critère | 400 km / 51,6° | Incidence pour UniSat-1 |
|--------|-------------------|-------------------|
| Coût de lancement | Le plus bas (lancement partagé avec le ravitaillement de l'ISS) | Compatible avec un budget universitaire |
| Durée de vie orbitale | ~9 mois en activité moyenne (déclin naturel) | Couvre la mission de 6 mois en activité solaire moyenne ou faible ; conforme à la règle des 5 ans de la FCC sans propulsion |
| Rayonnements | Faibles (~2–3 krad/an derrière 2 mm d'Al) | Électronique COTS sûre pour une mission de 6 mois |
| Inclinaison | 51,6° | Couverture en latitude suffisante pour la science de la météorologie de l'espace |
| Éclipse | ~36 min (~39 % de l'orbite) | Gérable avec une batterie de 10 Wh |
| Contacts sol | Stations aux latitudes moyennes : ~4–6 passages/jour | Suffisant pour une liaison descendante UHF à 9600 bit/s |

**Ce que cette orbite N'offre PAS :**

- un éclairement héliosynchrone (inutile — le magnétomètre n'est pas un instrument optique) ;
- une couverture polaire (acceptable — 51,6° couvrent l'essentiel des variations du champ magnétique) ;
- une longue durée de vie (acceptable — la durée de vie nominale de 6 mois reste inférieure à la durée de vie naturelle en activité solaire moyenne, mais voir ci-dessous).

**Pas de compromis sur la propulsion :** à 400 km, la traînée atmosphérique provoque une rentrée naturelle en un an environ. UniSat-1 n'a donc besoin d'aucun système propulsif, ni pour le maintien d'orbite ni pour la conformité aux règles sur les débris. Un sous-système entier disparaît — une simplification majeure pour une mission 1U. Le seul risque que révèle l'estimation de la durée de vie tient à la **date de lancement** : déployé au maximum solaire, un 1U à 400 km peut rentrer dans l'atmosphère en trois mois environ, soit moins que la mission de 6 mois. Le plan de mission doit alors soit accepter une mission écourtée, soit demander une altitude de déploiement un peu plus élevée.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Éléments képlériens | Six paramètres définissent l'orbite ; en LEO : altitude + inclinaison + LTAN |
| Formules clés | $T = 2\pi\sqrt{a^3/\mu}$ ; $v = \sqrt{\mu/a}$ ; fraction d'éclipse déduite de la géométrie et de l'angle bêta |
| Éclipse | $f_{\text{ecl}}$ dépend de β ; le cas le plus défavorable, β = 0, donne $\beta^*/\pi$ (≈ 38 % à 500 km, 39 % à 400 km) |
| Héliosynchrone | Exige une inclinaison précise (~97,4° à 500 km) grâce à la précession due au $J_2$ |
| Perturbations | Le $J_2$ rend possible l'orbite SSO ; la traînée limite la durée de vie ; la pression de radiation solaire affecte les satellites à rapport A/m élevé |
| Compromis | Altitude plus basse = meilleure GSD et meilleure liaison, mais durée de vie plus courte et traînée plus forte |
| Durée de vie | $\tau \approx H B/(\rho \sqrt{\mu a})$ : ~9 mois à 400 km, ~5 ans à 500 km pour un CubeSat ; forte dépendance au cycle solaire |
| Règles sur les débris | FCC : 5 ans ; IADC : 25 ans ; au-dessus de ~550 km, désorbitation active requise |
| Transfert de Hohmann | $\Delta V_{\text{deorbit}} \approx 110$ m/s depuis 600 km ; donnée d'entrée essentielle pour la propulsion |
| Rayonnements | Sous 600 km : COTS acceptables ; au-dessus : composants tolérants/durcis nécessaires ; la SAA provoque des SEU |
| Effet en cascade | Le choix de l'orbite affecte tous les sous-systèmes — c'est la décision de conception au plus fort effet de levier |

## Exercices

1. **Bases de l'orbite.** Pour des orbites circulaires à 350, 550 et 700 km, calculez la période, la vitesse, le demi-angle de l'ombre $\beta^*$ et la fraction d'éclipse la plus défavorable. Présentez les résultats sous forme de tableau et commentez la faible dépendance de la fraction d'éclipse à l'altitude, comparée à celle de la durée de vie.

2. **Angle bêta et puissance.** Un CubeSat 3U d'observation de la Terre évolue sur une orbite héliosynchrone à 550 km de LTAN 10 h 30 ; on suppose que son angle bêta reste compris entre 15° et 35° au cours de l'année. Calculez la fraction d'éclipse pour β = 15°, 25° et 35° et comparez-la au corollaire β = 0. De quel pourcentage la batterie dimensionnée au chapitre 9 serait-elle surdimensionnée si l'on utilisait la valeur β = 0 ?

3. **Inclinaison héliosynchrone.** Calculez l'inclinaison héliosynchrone à 400, 600 et 800 km. Tracez (ou présentez sous forme de tableau) $i$ en fonction de l'altitude et expliquez, à l'aide de la dépendance en $a^{7/2}$, pourquoi les orbites plus hautes exigent une inclinaison plus rétrograde.

4. **Durée de vie et cycle solaire.** Un CubeSat 6U ($m = 10$ kg, surface moyenne en culbutage 0,06 m², $C_D = 2.2$) doit être déployé à 500 km. En appliquant la méthode du §7.3.3 avec des masses volumiques de $2 \times 10^{-13}$, $5 \times 10^{-13}$ et $2 \times 10^{-12}$ kg/m³ (minimum, moyenne et maximum solaires), estimez la durée de vie dans chaque cas. La mission respecte-t-elle la règle des 5 ans de la FCC sans dispositif de désorbitation ? Que recommanderiez-vous ?

5. **Règle empirique contre physique.** Appliquez la règle empirique du chapitre 3, §3.6.4, au cas à 400 km, 4 kg et 0,03 m², et comparez le résultat à celui du §7.3.3. Sur quelle plage d'altitudes les deux concordent-ils à un facteur deux près, et pourquoi la règle échoue-t-elle à basse altitude ?

6. **ΔV de désorbitation.** Calculez le ΔV de désorbitation en une seule poussée depuis 500 km et depuis 700 km vers un périgée de 200 km. Si l'engin spatial emporte plutôt une voile de traînée qui fait passer sa surface de 0,03 m² à 1,0 m², estimez la nouvelle durée de vie à 700 km (prenez $\rho \approx 2 \times 10^{-14}$ kg/m³ et $H \approx 90$ km) et comparez les deux stratégies de désorbitation en termes de masse et de risque.

7. **Couverture.** Un satellite unique à 500 km emporte un imageur de demi-angle au sommet 3°. Calculez la fauchée, l'écart entre traces au sol et le temps de revisite approximatif à l'équateur. Combien de satellites régulièrement phasés faudrait-il pour une revisite de deux jours ?

8. **Durée de contact.** Pour une orbite à 400 km et une station dotée d'un masque d'élévation de 5°, calculez la durée maximale d'un passage. Si le passage moyen dure environ 60 % du maximum et que la station voit cinq passages par jour, de combien de minutes de contact dispose-t-on chaque jour, et (en anticipant le chapitre 11) quel débit faudrait-il pour transmettre au sol 500 Mo par jour ?

9. **Notation des orbites.** Définissez un barème de notation pondéré (pondérations de somme 1) portant sur la GSD, la revisite, la durée de vie/conformité aux règles sur les débris, les rayonnements et le coût de lancement, et notez trois orbites candidates (400 km ISS, 500 km SSO, 700 km SSO) pour (a) une mission optique d'observation de la Terre et (b) une mission scientifique magnétométrique comme UniSat-1. Expliquez pourquoi l'orbite gagnante diffère, et ce que devient le classement si l'on double la pondération de la durée de vie.

## Références

1. Vallado, D., *Fundamentals of Astrodynamics and Applications*, 4e éd., 2013, chap. 2–6, 9. https://celestrak.org/software/vallado-sw.php
2. Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, chap. 5–7. https://www.space.com/smad
3. Curtis, H., *Orbital Mechanics for Engineering Students*, 4e éd., 2020, chap. 2–4. https://www.elsevier.com/books/orbital-mechanics-for-engineering-students/curtis/978-0-08-102133-0
4. NASA, *Systems Engineering Handbook*, 2016, §4.4 (Process 4: Design Solution Definition). https://www.nasa.gov/reference/systems-engineering-handbook/
5. ECSS, *ECSS-E-ST-10-04C Rev.1: Space Environment*, 2020. https://ecss.nl/standard/ecss-e-st-10-04c-rev-1-space-environment-15-june-2020/
6. ECSS, *ECSS-U-AS-10C Rev.2: Space Debris Mitigation Requirements*, 2023. https://ecss.nl/standard/ecss-u-as-10c-rev-2-space-debris-mitigation-requirements/
7. IADC, *Space Debris Mitigation Guidelines*, IADC-02-01 Rev 3, 2021. https://www.iadc-home.org/documents_public/
8. FCC, *Report and Order FCC 22-74: Space Innovation (5-year rule)*, 2022. https://www.fcc.gov/document/fcc-adopts-new-5-year-rule-deorbiting-satellites
9. Wertz, J. R., *Mission Geometry: Orbit and Constellation Design and Management*, 2001 (géométrie des éclipses, éq. 5.24). https://www.springer.com
10. Picone, Hedin, Drob & Aikin, « NRLMSISE-00 empirical model of the atmosphere », *J. Geophys. Res.* 107, 2002. https://doi.org/10.1029/2002JA009430
