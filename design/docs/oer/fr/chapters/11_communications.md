# Chapitre 11 — Télécommunications et bilans de liaison

> **Lectures préalables conseillées.** SMAD4 chap. 13 (*Communications*) ; ECSS-E-ST-50-05C (*Radio frequency and modulation*) ; CCSDS 131.0-B-4 (*TM synchronisation and channel coding*) ; Pratt, Bostian et Allnutt, *Satellite Communications*, chap. 4 ; Maral et Bousquet, *Satellite Communications Systems*, chap. 5. Ce chapitre utilise l'orbite et la géométrie des contacts du chapitre 7, les fonctions du segment sol du chapitre 6, la capacité de pointage du chapitre 10 et le cadre réglementaire du chapitre 2 ; l'affaiblissement en espace libre et l'algèbre du bilan de liaison sont démontrés à partir des premiers principes dans la partie V, §V.6–V.8.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez en mesure de :

1. établir un bilan de liaison complet à partir des premiers principes (en décibels) ;
2. calculer l'affaiblissement en espace libre pour toute fréquence et toute distance oblique ;
3. choisir une bande de fréquences appropriée en fonction du débit, des licences et de la disponibilité des équipements ;
4. expliquer la physique de chaque type d'antenne et calculer le gain et l'ouverture du faisceau d'une antenne ;
5. choisir le schéma de modulation et de codage en fonction du $E_b/N_0$ requis et de l'efficacité spectrale ;
6. expliquer le fondement physique du gain de codage et pourquoi le codage correcteur d'erreurs (FEC) est indispensable aux liaisons spatiales ;
7. dimensionner une antenne (gain, ouverture du faisceau, masse) pour la fréquence choisie ;
8. déterminer le débit utile et vérifier que le bilan de données boucle ;
9. identifier les options de stations sol et calculer la géométrie des contacts ;
10. calculer un bilan de liaison à la main et le confronter à un outil de conception concourante ou à un tableur.

Les produits commerciaux cités dans ce chapitre sont des exemples représentatifs, et non des recommandations ; les prix et redevances de licence sont indicatifs (2026).

---

## 11.1 Le concept de bilan de liaison

*[Source : SMAD, chap. 13 ; ECSS-E-ST-50-05C ; Roddy, chap. 4]*

Le bilan de liaison est le relevé comptable de la liaison de télécommunications. Chaque gain et chaque perte entre l'émetteur et le récepteur sont totalisés en **décibels (dB)** pour déterminer si la liaison « boucle », c'est-à-dire si le signal reçu est assez fort pour être décodé avec un taux d'erreur acceptable.

La question fondamentale : **le signal reçu a-t-il assez d'énergie par bit, par rapport au bruit, pour atteindre le taux d'erreur binaire (TEB) exigé ?** Cette grandeur est quantifiée par $E_b/N_0$, le rapport entre l'énergie par bit d'information et la densité spectrale de bruit.

### 11.1.1 Enchaînement du bilan de liaison

La figure 11.1 montre la chaîne : la puissance de l'émetteur, le gain d'antenne et les pertes de ligne se combinent en une puissance isotrope rayonnée équivalente (PIRE) ; le canal retranche les pertes de propagation, atmosphériques et de dépointage ; le gain d'antenne et la température de bruit du récepteur fixent son facteur de qualité $G/T$ ; enfin, le démodulateur compare le $E_b/N_0$ disponible à celui qu'exigent la modulation et le codage choisis. Ce qui reste constitue la marge.

<svg viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg" style="max-width:750px; font-family: sans-serif; font-size: 11px;">
  <!-- TX -->
  <rect x="20" y="60" width="100" height="80" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="70" y="85" text-anchor="middle" fill="#1e40af" font-weight="bold">Émetteur</text>
  <text x="70" y="100" text-anchor="middle" fill="#1e40af" font-size="9">P_TX (dBW)</text>
  <text x="70" y="115" text-anchor="middle" fill="#1e40af" font-size="9">G_TX (dBi)</text>
  <text x="70" y="130" text-anchor="middle" fill="#1e40af" font-size="9">L_TX (dB)</text>
  <!-- EIRP label -->
  <rect x="145" y="80" width="70" height="30" rx="4" fill="#fef3c7" stroke="#d97706"/>
  <text x="180" y="100" text-anchor="middle" fill="#92400e" font-weight="bold" font-size="10">PIRE</text>
  <line x1="120" y1="100" x2="145" y2="95" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- Path -->
  <rect x="240" y="60" width="120" height="80" rx="6" fill="#fee2e2" stroke="#dc2626" stroke-width="2"/>
  <text x="300" y="85" text-anchor="middle" fill="#991b1b" font-weight="bold">Pertes du canal</text>
  <text x="300" y="100" text-anchor="middle" fill="#991b1b" font-size="9">Affaibl. esp. libre (dB)</text>
  <text x="300" y="115" text-anchor="middle" fill="#991b1b" font-size="9">Atmosphérique (dB)</text>
  <text x="300" y="130" text-anchor="middle" fill="#991b1b" font-size="9">Dépointage, polar. (dB)</text>
  <line x1="215" y1="100" x2="240" y2="100" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- RX -->
  <rect x="390" y="60" width="110" height="80" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="445" y="85" text-anchor="middle" fill="#166534" font-weight="bold">Récepteur</text>
  <text x="445" y="100" text-anchor="middle" fill="#166534" font-size="9">G_RX (dBi)</text>
  <text x="445" y="115" text-anchor="middle" fill="#166534" font-size="9">T_sys (K)</text>
  <text x="445" y="130" text-anchor="middle" fill="#166534" font-size="9">G/T (dB/K)</text>
  <line x1="360" y1="100" x2="390" y2="100" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- Result -->
  <rect x="530" y="60" width="120" height="80" rx="6" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
  <text x="590" y="85" text-anchor="middle" fill="#3730a3" font-weight="bold">Démodulateur</text>
  <text x="590" y="100" text-anchor="middle" fill="#3730a3" font-size="9">Eb/N0 disponible (dB)</text>
  <text x="590" y="115" text-anchor="middle" fill="#3730a3" font-size="9">Eb/N0 requis (dB)</text>
  <text x="590" y="130" text-anchor="middle" fill="#3730a3" font-size="9">Perte d'implém. (dB)</text>
  <line x1="500" y1="100" x2="530" y2="100" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- Margin -->
  <rect x="680" y="70" width="90" height="55" rx="6" fill="#d1fae5" stroke="#059669" stroke-width="3"/>
  <text x="725" y="93" text-anchor="middle" fill="#065f46" font-weight="bold" font-size="13">MARGE</text>
  <text x="725" y="112" text-anchor="middle" fill="#065f46" font-size="11">≥ 3 dB</text>
  <line x1="650" y1="100" x2="680" y2="97" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <defs><marker id="a3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#64748b"/></marker></defs>
</svg>

**Figure 11.1** — La chaîne de liaison, de l'émetteur au démodulateur. Chaque bloc apporte des gains (positifs) ou des pertes (négatives) en décibels ; la marge est ce qui reste une fois satisfaite l'exigence du démodulateur.

### 11.1.2 Rappels sur les décibels

Tous les termes du bilan de liaison sont exprimés en décibels, ce qui transforme les multiplications et divisions en additions et soustractions :

| Conversion | Formule | Exemple |
|-----------|---------|---------|
| Watts en dBW | $P_{\text{dBW}} = 10 \log_{10}(P_W)$ | 2 W = +3,0 dBW |
| Milliwatts en dBm | $P_{\text{dBm}} = 10 \log_{10}(P_{mW})$ | 1 W = +30 dBm |
| dBW en watts | $P_W = 10^{P_{\text{dBW}}/10}$ | −3 dBW = 0,5 W |
| Rapport en dB | $G_{\text{dB}} = 10 \log_{10}(G)$ | Gain de 100 = 20 dB |
| dBW et dBm | dBm = dBW + 30 | 0 dBW = 30 dBm |

**Valeurs de puissance courantes :**

| Puissance | dBW | dBm |
|-------|-----|-----|
| 0,1 W | −10,0 | +20,0 |
| 0,5 W | −3,0 | +27,0 |
| 1 W | 0,0 | +30,0 |
| 2 W | +3,0 | +33,0 |
| 5 W | +7,0 | +37,0 |
| 10 W | +10,0 | +40,0 |

---

## 11.2 L'équation complète du bilan de liaison

> **Équations clés — bilan de liaison (en dB)**
>
> **PIRE** (puissance isotrope rayonnée équivalente) :
> $$\text{PIRE} = P_{TX} + G_{TX} - L_{TX} \quad \text{(dBW)}$$
>
> La PIRE représente la puissance qu'une antenne isotrope devrait rayonner pour produire la même intensité de signal dans la direction de gain maximal de l'antenne. Elle combine la puissance de l'émetteur, le gain de l'antenne (directivité) et les pertes dans les câbles et filtres.
>
> **Affaiblissement en espace libre :**
> $$\text{FSPL} = 20\log_{10}\left(\frac{4\pi d}{\lambda}\right) = 20\log_{10}\left(\frac{4\pi d f}{c}\right) \quad \text{(dB)}$$
> où $d$ = distance oblique (m), $f$ = fréquence (Hz), $c = 3 \times 10^8$ m/s.
>
> **Interprétation physique :** l'affaiblissement en espace libre n'est pas une « absorption d'énergie » : aucune énergie n'est perdue. Il traduit l'étalement géométrique de la puissance rayonnée sur une sphère de rayon $d$. Une antenne isotrope rayonne de façon égale dans toutes les directions, si bien que la puissance par unité de surface à la distance $d$ vaut $P/(4\pi d^2)$. La dépendance en $\lambda^2$ vient de ce que l'ouverture effective d'une antenne de réception varie comme $A_{\text{eff}} = G\lambda^2/(4\pi)$ : aux fréquences plus élevées, l'antenne de réception « capte » une moindre part du flux disponible (à moins d'être physiquement plus grande). La partie V, §V.6, démontre ce résultat à partir de l'équation de transmission de Friis.
>
> **Facteur de qualité du récepteur :**
> $$G/T = G_{RX} - 10\log_{10}(T_{sys}) \quad \text{(dB/K)}$$
>
> Le facteur de qualité $G/T$ est le paramètre le plus important de toute station de réception. Il combine le gain d'antenne (captation du signal) et la température de bruit du système (plancher de bruit). Un $G/T$ élevé signifie une bonne sensibilité.
>
> La **température de bruit du système** $T_{sys}$ comprend :
> - la température de bruit d'antenne $T_A$ (elle dépend de ce que « voit » l'antenne : ciel ~10–50 K au zénith, ~150–300 K en visant la Terre ou le sol) ;
> - les pertes de la source et des câbles : $T_{\text{feed}} = T_{\text{physical}} (L-1)$, où $L$ = facteur de perte ;
> - la température de bruit du LNA : $T_{\text{LNA}} = T_0 (F-1)$, où $F$ = facteur de bruit, $T_0 = 290$ K ;
> - les étages suivants (atténués par le gain du LNA).
>
> Règle empirique : $T_{sys} \approx 100$–$200$ K pour une station sol professionnelle équipée d'un LNA cryogénique ou à faible bruit ; $T_{sys} \approx 400$–$800$ K pour une station amateur équipée d'un LNA COTS.
>
> **Rapport porteuse sur densité de bruit** (forme canonique utilisée dans tout cet ouvrage, y compris dans la partie IV et dans la partie V, §V.7) :
> $$C/N_0 = \text{PIRE} - \text{FSPL} - L_{\text{atm}} - L_{\text{point}} - L_{\text{pol}} - L_{\text{rx}} + G/T - k \quad \text{(dBHz)}$$
> où $k = -228.6$ dBW/K/Hz (constante de Boltzmann, $k = 1.381 \times 10^{-23}$ J/K, exprimée en dB) et $L_{\text{rx}}$ est la perte de source et de ligne côté réception entre l'antenne et le point auquel $T_{sys}$ est rapportée (souvent intégrée au $G/T$, auquel cas elle vaut 0 dB dans le tableau ligne par ligne).
>
> **Énergie par bit sur densité de bruit :**
> $$E_b/N_0 = C/N_0 - 10\log_{10}(R_b) \quad \text{(dB)}$$
> où $R_b$ = débit (bit/s). C'est la mesure de qualité fondamentale : chaque bit a besoin d'une certaine quantité d'énergie ($E_b$) par rapport au plancher de bruit ($N_0$) pour être correctement démodulé.
>
> **Marge de liaison :**
> $$\text{Marge} = E_b/N_{0,\text{available}} - E_b/N_{0,\text{required}} - L_{\text{implementation}} \quad \text{(dB)}$$
>
> **Exigence :** marge ≥ 3 dB à partir de la phase B (selon ECSS-E-ST-50-05C ; un objectif de 6 dB est courant en phase A, tant que la conception reste mouvante). Cette marge de 3 dB couvre :
> - les variations de la puissance d'émission (vieillissement, température) ;
> - les incertitudes sur les gains d'antenne ;
> - la scintillation atmosphérique ;
> - les variations de l'erreur de pointage ;
> - les variations des performances de la station sol.

### 11.2.1 Tableau complet du bilan de liaison

| Ligne | Paramètre | Formule / valeur typique | Unité | Signification physique |
|------|-----------|------------------------|------|-----------------|
| 1 | Puissance d'émission | $P_{TX}$ (p. ex. 2 W = +3,0) | dBW | Puissance RF en sortie d'amplificateur |
| 2 | Gain de l'antenne d'émission | $G_{TX}$ (p. ex. +6,0 pour une antenne patch) | dBi | Directivité par rapport à l'antenne isotrope |
| 3 | Pertes de ligne à l'émission | $L_{TX}$ (câbles, filtres : −1,5) | dB | Pertes ohmiques dans les câbles et connecteurs RF |
| 4 | **PIRE** | $= P_{TX} + G_{TX} - L_{TX}$ | dBW | Puissance rayonnée équivalente |
| 5 | Affaiblissement en espace libre | $\text{FSPL} = 20\log_{10}(4\pi d f/c)$ | dB | Étalement géométrique + effet d'ouverture |
| 6 | Affaiblissement atmosphérique | $L_{\text{atm}}$ (−0,3 à −3,0) | dB | Absorption moléculaire (O$_2$, H$_2$O) |
| 7 | Perte de dépointage | $L_{\text{point}}$ (−0,5 à −3,0) | dB | Baisse du signal due au dépointage de l'antenne |
| 8 | Perte de polarisation | $L_{\text{pol}}$ (−0,1 à −3,0) | dB | Désadaptation entre les polarisations d'émission et de réception |
| 9 | Gain de l'antenne de réception | $G_{RX}$ (p. ex. +35 pour une parabole de 3 m) | dBi | Directivité de l'antenne sol |
| 10 | Température de bruit du système | $T_{sys}$ (p. ex. 150 K = 21,8 dBK) | dBK | Température de bruit totale de la chaîne de réception |
| 11 | **G/T** | $= G_{RX} - 10\log_{10}(T_{sys})$ | dB/K | Facteur de qualité du récepteur |
| 12 | Constante de Boltzmann | $k = -228.6$ | dBW/K/Hz | Densité spectrale de puissance du bruit thermique |
| 13 | **C/N$_0$** | $= \text{PIRE} - \text{FSPL} - L_{\text{atm}} - L_{\text{point}} - L_{\text{pol}} - L_{\text{rx}} + G/T - k$ | dBHz | Rapport signal sur densité de bruit |
| 14 | Débit | $10\log_{10}(R_b)$ | dB(bit/s) | Débit d'information |
| 15 | **$E_b/N_0$ disponible** | $= C/N_0 - 10\log_{10}(R_b)$ | dB | Énergie disponible par bit |
| 16 | $E_b/N_0$ requis | Selon le choix de modulation et de codage | dB | Minimum nécessaire pour le TEB visé |
| 17 | Perte d'implémentation | En général 1,5–2,5 dB | dB | Performances réelles du démodulateur par rapport aux performances idéales |
| 18 | **MARGE DE LIAISON** | $= E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}}$ | dB | Doit être ≥ 3 dB |

---

## 11.3 Types d'antennes — physique et choix

*[Source : SMAD, chap. 13 ; Balanis, *Antenna Theory: Analysis and Design*, 4e éd., 2016]*

L'antenne convertit l'énergie RF guidée (dans les câbles ou les guides d'ondes) en ondes électromagnétiques rayonnées (et inversement en réception). Ses principaux paramètres de performance sont :

- **Gain** ($G$) : le surcroît de signal que l'antenne concentre dans la direction de son faisceau par rapport à un radiateur isotrope. Gain plus élevé = faisceau plus étroit = plus de signal, mais pointage plus précis nécessaire.
- **Ouverture du faisceau** ($\theta_{3\text{dB}}$) : la largeur angulaire du lobe principal entre les points à −3 dB (mi-puissance).
- **Polarisation :** linéaire (verticale/horizontale), circulaire (RHCP/LHCP) ou elliptique.

**Compromis fondamental :** $G \propto 1/\theta_{3\text{dB}}^2$. Une antenne à gain plus élevé a un faisceau plus étroit et exige un pointage plus précis. Pour un engin spatial sans pointage précis, une antenne omnidirectionnelle à faible gain est obligatoire. Pour un engin spatial pointé à 0,1° (chapitre 10), une antenne directive à grand gain devient envisageable. La figure 11.2 met en regard les deux extrêmes.

![Diagrammes de rayonnement : parabole à grand gain et antenne patch.](../assets/figures/fig_antenna_pattern.png)

**Figure 11.2** — Diagrammes de gain à 2,25 GHz d'une parabole de 3 m (35 dBi ; lobe principal étroit de 3°, lobes secondaires marqués) et d'une antenne patch en bande S (6 dBi ; lobe large, quasi hémisphérique). La parabole exige un pointage par le SCAO à une fraction de son ouverture de faisceau près ; l'antenne patch tolère des dépointages de plusieurs dizaines de degrés, au prix d'environ 25–30 dB de gain.

### 11.3.1 Types d'antennes pour engin spatial

| Type d'antenne | Gain (dBi) | Ouverture du faisceau | Pointage nécessaire ? | Masse (CubeSat) | Physique |
|-------------|-----------|-----------|-------------------|----------------|---------|
| **Monopôle/dipôle** | 0–2 | ~omnidirectionnelle (diagramme torique) | Non | 5–20 g (fil déployable) | La distribution de courant sur un fil rayonne ; monopôle $\lambda/4$ sur plan de masse ou dipôle $\lambda/2$ |
| **Tourniquet** | 0–3 | Hémisphérique | Non | 10–30 g | Deux dipôles croisés alimentés en quadrature (90°) ; produit une polarisation circulaire |
| **Patch (microruban)** | 5–8 | 60–90° | Peu exigeant (~10°) | 10–50 g | Élément conducteur résonant sur substrat diélectrique au-dessus d'un plan de masse ; patch $\lambda/2$ à la résonance |
| **Réseau de patchs (2×2, 4×4)** | 10–18 | 15–40° | Modéré (~5°) | 50–200 g | Plusieurs éléments patch avec réseau d'alimentation arborescent ; gain = $G_{\text{element}} + 10\log_{10}(N)$ |
| **Cornet** | 15–25 | 10–25° | Oui (~2°) | 100–500 g | Guide d'ondes évasé ; l'éclairement régulier de l'ouverture donne des lobes secondaires faibles |
| **Réflecteur parabolique** | 25–45 | 1–5° | Oui (< 1°) | 500 g – 5 kg | Une source au foyer éclaire la parabole ; $G = \eta_a (\pi D/\lambda)^2$ |
| **Antenne réseau à commande de phase** | 15–35 | Dépointage électronique, 1–30° | Électronique (pas de mécanisme) | 200 g – 2 kg | Réseau d'éléments munis chacun d'un déphaseur ; faisceau orienté par réglage des phases relatives ; aucune pièce mobile |

**Physique du monopôle et du dipôle :** le monopôle quart d'onde ($L = \lambda/4$) est l'antenne la plus simple. À 437 MHz (UHF), $\lambda = 0.686$ m, si bien qu'un monopôle mesure 17,2 cm, ce qui se déploie facilement depuis un CubeSat au moyen d'un ruban de mètre ressort ou d'un fil en nitinol. Le diagramme de rayonnement est omnidirectionnel dans le plan azimutal (perpendiculaire au fil) et nul selon l'axe du fil. Le gain est d'environ 0–2 dBi selon la taille du plan de masse.

**Physique de l'antenne patch :** une antenne patch microruban se compose d'un élément conducteur (en général rectangulaire, $L \approx \lambda/2$ à la fréquence visée) imprimé sur un substrat diélectrique (p. ex. Rogers RT/duroid, $\varepsilon_r = 2.2$–$10.2$, épaisseur 1–3 mm) au-dessus d'un plan de masse. Le patch résonne à la fréquence pour laquelle sa longueur vaut $\lambda_{eff}/2$ (où $\lambda_{eff} = \lambda_0/\sqrt{\varepsilon_r}$). En bande S (2,25 GHz), un patch mesure environ 40 × 40 mm, assez petit pour être monté sur une face de CubeSat. Le gain est généralement de 5–8 dBi avec un diagramme hémisphérique. La polarisation circulaire s'obtient en alimentant deux modes orthogonaux en quadrature (90°) (double alimentation ou patch à coins tronqués).

**Physique du réflecteur parabolique :** une parabole concentre les ondes planes incidentes en son foyer (en réception) ou transforme les ondes sphériques issues d'une source placée au foyer en un faisceau parallèle (en émission). Le gain dépend du diamètre de la parabole $D$ et de la longueur d'onde $\lambda$ :

> **Équations clés — antennes**
>
> **Gain d'une antenne parabolique :**
> $$G = \eta_a \left(\frac{\pi D}{\lambda}\right)^2$$
>
> En dBi : $G_{\text{dBi}} = 10\log_{10}\left[\eta_a \left(\frac{\pi D}{\lambda}\right)^2\right]$
>
> où $\eta_a \approx 0.55$–$0.65$ (rendement d'ouverture, qui tient compte de la loi d'éclairement, du débordement, du masquage et des défauts de surface), $D$ = diamètre de l'antenne (m), $\lambda = c/f$.
>
> **Ouverture du faisceau à mi-puissance (HPBW) :**
> $$\theta_{3\text{dB}} \approx \frac{70\lambda}{D} \quad \text{(degrés)}$$
>
> **Gain d'une antenne patch** (élément unique) : en général 5–8 dBi, ouverture du faisceau ~60–90°
>
> **Gain d'un réseau de patchs** ($N$ éléments) : $G_{\text{array}} = G_{\text{element}} + 10\log_{10}(N)$
>
> **Perte de dépointage** (antenne dépointée d'un angle $\Delta\theta$) :
> $$L_{\text{point}} \approx -12 \left(\frac{\Delta\theta}{\theta_{3\text{dB}}}\right)^2 \quad \text{(dB)}$$
>
> On voit qu'un faisceau plus étroit (plus petit $\theta_{3\text{dB}}$) est plus sensible aux erreurs de pointage.

**Exemple résolu — gain d'une parabole de 30 cm dans différentes bandes** ($\eta_a = 0.55$) :

| Bande | Fréquence | $\lambda$ (mm) | $D/\lambda$ | Gain (dBi) | HPBW (°) | Pointage requis |
|------|-----------|----------------|-------------|-----------|-----------|-------------|
| Bande S | 2,25 GHz | 133 | 2,25 | 14,4 | 31 | ~5° |
| Bande X | 8,4 GHz | 35,7 | 8,4 | 25,8 | 8,3 | ~1° |
| Bande Ka | 26 GHz | 11,5 | 26,1 | 35,7 | 2,7 | ~0,3° |

Ce tableau illustre le lien fondamental entre fréquence, taille d'antenne, gain et exigence de pointage. En bande Ka, même une petite parabole offre un gain élevé, mais l'ouverture du faisceau est si étroite qu'une précision de pointage inférieure au degré devient indispensable. C'est pourquoi les liaisons en bande Ka des CubeSats exigent un SCAO à senseur stellaire et roues de réaction (chapitre 10, §10.1).

**Physique des antennes réseau à commande de phase :** une antenne réseau à commande de phase se compose de plusieurs éléments rayonnants (patchs, dipôles ou fentes) disposés selon une grille. Chaque élément dispose de son propre déphaseur (et parfois d'un réglage d'amplitude). En ajustant la phase relative entre éléments, on peut orienter électroniquement le faisceau sans déplacer l'antenne. La direction du faisceau $\theta_s$ pour un espacement des éléments $d$ et un incrément de phase $\Delta\phi$ vaut

$$\sin(\theta_s) = \frac{\Delta\phi \cdot \lambda}{2\pi d}$$

Avantages : aucune pièce mobile, dépointage rapide du faisceau (quelques microsecondes), possibilité de plusieurs faisceaux simultanés. Inconvénients : complexité, coût, forte consommation pour les réseaux actifs, perte de balayage aux grands angles (facteur $\cos\theta_s$). Les antennes réseau à commande de phase équipent les satellites Starlink (bande Ka) et Iridium NEXT (bande L), et apparaissent sur les CubeSats en bande Ka.

---

## 11.4 Affaiblissement en espace libre par bande

L'affaiblissement en espace libre augmente avec la fréquence et avec la distance. À distance oblique fixe, les bandes de fréquences plus élevées perdent davantage de signal, mais cette perte est compensée par la possibilité d'utiliser, aux fréquences élevées, des antennes plus petites et à plus grand gain.

> **Équations clés — affaiblissement en espace libre (forme développée)**
>
> $$\text{FSPL (dB)} = 20\log_{10}(4\pi) + 20\log_{10}(d) + 20\log_{10}(f) - 20\log_{10}(c)$$
> $$= 21.98 + 20\log_{10}(d_m) + 20\log_{10}(f_{Hz}) - 169.54$$
>
> **Forme pratique (en km et GHz) :**
> $$\text{FSPL (dB)} = 92.45 + 20\log_{10}(d_{km}) + 20\log_{10}(f_{GHz})$$

La figure 11.3 trace cette relation pour cinq bandes sur la plage de distances obliques utiles, de quelques centaines de kilomètres (LEO à la verticale) jusqu'à la distance géostationnaire.

![Affaiblissement en espace libre en fonction de la distance oblique, pour différentes bandes.](../assets/figures/fig_fspl.png)

**Figure 11.3** — Affaiblissement en espace libre en fonction de la distance oblique (échelle logarithmique) pour les bandes VHF, UHF, S, X et Ka. Chaque doublement de la distance ou de la fréquence ajoute 6 dB ; les repères verticaux indiquent une distance oblique LEO de 1000 km, un passage polaire à faible élévation et la distance directe en GEO.

### 11.4.1 Géométrie de la distance oblique

La distance oblique $d$ entre un engin spatial en LEO et une station sol dépend de l'altitude de l'orbite $h$ et de l'angle d'élévation $\varepsilon$ au-dessus de l'horizon :

$$d = R_E \left[\sqrt{\left(\frac{R_E + h}{R_E}\right)^2 - \cos^2(\varepsilon)} - \sin(\varepsilon)\right]$$

Avec $R_E = 6378.137$ km, les orbites LEO typiques donnent :

| Altitude | Élévation 90° (nadir) | Élévation 30° | Élévation 10° | Élévation 5° |
|----------|------------------------|-------------------|-------------------|-------------------|
| 400 km | 400 km | 740 km | 1440 km | 1800 km |
| 500 km | 500 km | 910 km | 1695 km | 2080 km |
| 600 km | 600 km | 1075 km | 1930 km | 2330 km |

**Règle de conception :** calculez toujours le bilan de liaison à l'**angle d'élévation minimal** (cas le plus défavorable), en général 5–10°. En dessous de 5°, les pertes atmosphériques augmentent fortement, les échos du sol entrent dans les lobes secondaires de l'antenne et la liaison est généralement inutilisable.

### 11.4.2 Affaiblissement en espace libre par bande et par géométrie

| Bande | Fréquence centrale | Affaiblissement à 500 km (nadir) | Affaiblissement à 1695 km (10° d'élévation) | Différence |
|------|-----------------|----------------------|-------------------------------|------------|
| **VHF** | 146 MHz | 129,7 dB | 140,3 dB | 10,6 dB |
| **UHF** | 437 MHz | 139,2 dB | 149,8 dB | 10,6 dB |
| **Bande S** | 2250 MHz | 153,5 dB | 164,1 dB | 10,6 dB |
| **Bande X** | 8200 MHz | 164,7 dB | 175,3 dB | 10,6 dB |
| **Bande Ka** | 26 GHz | 174,7 dB | 185,3 dB | 10,6 dB |

**La pénalité de l'angle d'élévation :** à 500 km, passer du nadir à 10° d'élévation augmente l'affaiblissement en espace libre d'environ 10,6 dB (la distance est multipliée par 3,4 ; l'affaiblissement varie comme $20\log_{10}(3.4) = 10.6$ dB). C'est une perte importante, et c'est pourquoi le temps de contact à forte élévation vaut bien plus que le temps de contact à faible élévation.

---

## 11.5 Choix de la bande de fréquences et licences

*[Source : Règlement des radiocommunications de l'UIT, articles 5 et 22 ; ISDE CNR-SAT (RSS-SAT) ; FCC Part 25 ; coordination des fréquences satellite de l'IARU]*

Le choix de la bande est une **contrainte de conception** qui influe sur le débit, la taille des antennes, les pertes atmosphériques, la disponibilité des équipements, le coût des licences et la politique de données. C'est l'une des décisions les plus précoces et les plus lourdes de conséquences de la conception d'une mission. La procédure réglementaire elle-même est décrite au chapitre 2, §2.7 ; cette section se concentre sur les conséquences techniques.

### 11.5.1 Tableau comparatif des bandes

| Bande | Plage de fréquences | Attribution | Largeur de bande max. | Débit pratique | Perte atmosphérique (10°) | Évanouissement dû à la pluie | Licences (indicatif, 2026) | Disponibilité des équipements |
|------|----------------|-----------|--------|--------------------|--------------------------|-----------|-----------|-----------------------|
| **VHF** | 144–146 MHz | Amateur | 15 kHz | < 9,6 kbit/s | 0,1 dB | Aucun | Coordination IARU (gratuite, 3–6 mois) | Nombreux COTS, faible coût |
| **UHF** | 435–438 MHz | Amateur | 20 kHz | < 19,2 kbit/s | 0,2 dB | Négligeable | Coordination IARU (gratuite, 3–6 mois) | Nombreux COTS, faible coût |
| **Bande S** | 2200–2290 MHz | Recherche spatiale / SETS | 5 MHz | 0,1–10 Mbit/s | 0,5 dB | < 0,5 dB | ISDE/FCC (30–45 k\$, 6–12 mois) | Nombreux COTS |
| **Bande X** | 8025–8400 MHz | SETS | 375 MHz | 10–400 Mbit/s | 1,0 dB | 1–3 dB | ISDE/FCC + UIT (50–80 k\$, 12 mois et plus) | Offre COTS croissante |
| **Bande Ka** | 25,5–27,0 GHz | SETS/SFS | 1,5 GHz | 100–2000+ Mbit/s | 2–5 dB | 3–15 dB (selon le site) | UIT, complexe (100 k\$ et plus, 18 mois et plus) | COTS émergents |

*SETS = service d'exploration de la Terre par satellite (EES) ; SFS = service fixe par satellite (FSS)*

**Physique de l'atténuation atmosphérique :** l'atmosphère absorbe et diffuse l'énergie RF. L'oxygène moléculaire présente une forte raie d'absorption à 60 GHz (utilisée pour les liaisons intersatellites, qui n'ont pas besoin de traverser l'atmosphère). La vapeur d'eau absorbe à 22,2 GHz (près de la bande Ka). En bande S et en dessous, les pertes atmosphériques sont minimes (< 1 dB). En bande Ka, des pertes de 2–5 dB sont typiques à 10° d'élévation, et l'évanouissement dû à la pluie peut ajouter 3–15 dB dans les régions tropicales.

**Évanouissement dû à la pluie :** les gouttes de pluie diffusent et absorbent l'énergie RF. L'effet varie approximativement comme $f^2$ : négligeable sous 4 GHz, significatif au-dessus de 10 GHz et sévère au-dessus de 20 GHz. L'évanouissement dû à la pluie se caractérise par l'intensité de pluie (mm/h) et la longueur du trajet dans la pluie. Dans les régions tropicales, des intensités de pluie de 50 mm/h et plus peuvent causer une perte supplémentaire de 10 dB et plus en bande Ka. Parades : débit adaptatif (réduire le débit pendant la pluie), diversité de sites (plusieurs stations sol), contrôle de puissance (augmenter la puissance d'émission pendant l'évanouissement). Pour les liaisons en bande Ka, on prévoit généralement une marge d'évanouissement dû à la pluie de 5–10 dB.

**Réglementation des bandes amateurs (IARU) :**
- usage non commercial, éducatif et expérimental uniquement ;
- politique de données ouvertes : toutes les transmissions doivent être non chiffrées et le protocole doit être publié ;
- aucune transmission au sol de données ou d'images commerciales ;
- coordination par l'IARU (Union internationale des radioamateurs) : gratuite, mais elle prend 3–6 mois ;
- très prisé pour les CubeSats universitaires (faible coût, pas de redevance de licence, la vaste communauté des radioamateurs fournit gratuitement un soutien de stations sol via le réseau SatNOGS).

**Licences pour les bandes commerciales :**
- dépôt national obligatoire (FCC aux États-Unis, ISDE au Canada, Ofcom au Royaume-Uni, CNES/ANFR en France) + coordination UIT pour les fréquences supérieures à 1 GHz ;
- coûts (indicatifs, 2026) : 50–80 k\$ pour la bande X, 30–45 k\$ pour la bande S (cas typique), plus de 100 k\$ pour la bande Ka ;
- délais : 6–12 mois pour la bande S, 12–18 mois pour la bande X, 18 mois et plus pour la bande Ka ;
- les données commerciales peuvent être chiffrées et propriétaires ;
- l'attribution de largeur de bande peut être limitée par l'autorité nationale.

### 11.5.2 Arbre de décision pour le choix de la bande

```
Débit de données requis ?
  ≤ 9.6 kbit/s AND usage non commercial/éducatif → VHF/UHF amateur (IARU, gratuit, 3–6 mois)
  ≤ 10 Mbit/s                                    → bande S commerciale (ISED/FCC, 30–45 k$, 6–12 mois)
  ≤ 400 Mbit/s                                   → bande X (ISED/FCC + ITU, 50–80 k$, 12+ mois)
  > 400 Mbit/s                                   → bande Ka (ITU complexe, 100+ k$, 18+ mois, évanouissements dus à la pluie)
```

---

## 11.6 Modulation et codage — physique et choix

*[Source : CCSDS 131.0-B-4 ; Sklar, chap. 7–8 ; Haykin, chap. 10 ; norme DVB-S2]*

### 11.6.1 Modulation — comment l'information devient un signal RF

La modulation inscrit des données numériques sur une porteuse RF en faisant varier l'amplitude, la fréquence ou la phase de la porteuse.

**Modulation par déplacement de phase (PSK) :** c'est la famille de modulations la plus courante dans les télécommunications spatiales. La phase de la porteuse est décalée de valeurs discrètes pour représenter les différentes combinaisons de bits :

- **BPSK (PSK binaire) :** 2 états de phase (0° et 180°). Chaque symbole transporte 1 bit. Efficacité spectrale : 1 bit/s/Hz. La plus robuste au bruit.
- **QPSK (PSK en quadrature) :** 4 états de phase (0°, 90°, 180°, 270°). Chaque symbole transporte 2 bits. Efficacité spectrale : 2 bit/s/Hz. Exige le même $E_b/N_0$ que la BPSK, mais double le débit pour une même largeur de bande. **Le choix standard pour la plupart des liaisons spatiales.**
- **8PSK :** 8 états de phase, 3 bits/symbole, efficacité spectrale de 3 bit/s/Hz. Exige ~3,5 dB de $E_b/N_0$ de plus que la QPSK pour le même TEB.
- **16APSK :** 16 états (amplitude + phase), 4 bits/symbole, efficacité spectrale de 4 bit/s/Hz. Exige ~7 dB de $E_b/N_0$ de plus que la QPSK.

**Modulation par déplacement de fréquence (FSK) :** la fréquence de la porteuse bascule entre des valeurs discrètes. Moins efficace spectralement que la PSK, mais plus tolérante à la non-linéarité des amplificateurs. Variantes :
- **FSK :** simple commutation de fréquence.
- **GFSK (FSK gaussienne) :** un filtre gaussien adoucit les transitions de fréquence et réduit l'étalement spectral. Utilisée par de nombreuses radios UHF de CubeSat (protocole AX.25 à 9600 bit/s).
- **MSK (*minimum shift keying*) :** cas particulier de la FSK avec l'écart de fréquence minimal qui permet encore une détection cohérente. Enveloppe constante (importante pour les amplificateurs non linéaires). Efficacité spectrale ~1 bit/s/Hz.

**Pourquoi préférer la QPSK à la BPSK pour les liaisons spatiales :** la QPSK transmet 2 bits par symbole tout en exigeant la même énergie par bit que la BPSK. La QPSK atteint donc un débit double pour la même largeur de bande et les mêmes performances en $E_b/N_0$. La seule complexité supplémentaire est que le récepteur doit distinguer 4 états de phase au lieu de 2, ce qui est trivial pour les récepteurs numériques modernes.

La figure 11.4 montre les courbes de taux d'erreur binaire qui sous-tendent les valeurs de $E_b/N_0$ requis utilisées dans la suite de ce chapitre ; la partie V, §V.8, donne les expressions analytiques correspondantes.

![Eb/N0 en fonction du TEB pour les modulations courantes.](../assets/figures/fig_signal_noise.png)

**Figure 11.4** — Taux d'erreur binaire en fonction de $E_b/N_0$ pour la BPSK/QPSK, la 8-PSK et la FSK non cohérente, avec une courbe codée représentative (codage concaténé convolutif + Reed–Solomon). L'écart horizontal entre les courbes non codée et codée à un TEB donné est le gain de codage : environ 5 dB à un TEB de $10^{-5}$ pour ce schéma, et davantage pour les codes LDPC.

### 11.6.2 Codage correcteur d'erreurs (FEC) — gain de codage

Le codage correcteur d'erreurs (FEC, *forward error correction*) ajoute des bits redondants au flux de données avant la transmission. Le récepteur utilise ces bits redondants pour détecter et corriger les erreurs binaires sans retransmission. L'amélioration de l'$E_b/N_0$ requis (par rapport à une transmission non codée) s'appelle le **gain de codage**.

**Pourquoi le codage est indispensable aux liaisons spatiales :** les liaisons spatiales fonctionnent avec une puissance de signal reçue très faible (du femtowatt au picowatt). Sans codage, l'$E_b/N_0$ requis pour un TEB de $10^{-6}$ est de 10,5 dB. Avec un codage LDPC, il tombe à 2,0 dB, soit un gain de codage de 8,5 dB. Cela équivaut à multiplier la puissance d'émission par 7, ou le diamètre de l'antenne par 2,7, ou à diviser le débit par 7. Le codage procure le même bénéfice au prix de quelques watts seulement de puissance de traitement numérique.

**Types de codes utilisés dans les télécommunications spatiales :**

| Type de code | Rendement de code | Gain de codage à un TEB de $10^{-6}$ | Complexité de décodage | Norme | Utilisation |
|-----------|-----------|-------------------------------|---------------------|----------|-----|
| **Convolutif** (K = 7) | 1/2 | ~5,5 dB | Faible (décodeur de Viterbi, matériel) | CCSDS | Télécommande historique, AX.25 |
| **Convolutif + RS** (concaténé) | ~0,44 | ~7,5 dB | Moyenne | CCSDS | Télémesure CCSDS standard (nombreuses missions à héritage en vol) |
| **Turbocode** | 1/2 à 1/6 | ~8–10 dB | Élevée (décodeur itératif) | CCSDS | Liaisons d'espace lointain (Mars, Jupiter) |
| **LDPC** (*low-density parity check*) | 1/2 | ~8,5 dB | Moyenne à élevée (décodeur itératif BP) | CCSDS, DVB-S2 | Liaisons descendantes spatiales modernes, **recommandé pour les CubeSats** |
| **LDPC** | 3/4 | ~6,5 dB | Moyenne à élevée | CCSDS, DVB-S2 | Équilibre entre performances et débit |
| **LDPC** | 7/8 | ~5,0 dB | Moyenne à élevée | DVB-S2 | Débit maximal, signal fort |

*[Source : CCSDS 131.0-B-4 ; DVB-S2 ETSI EN 302 307]*

**Rendement de code $r$ :** le rapport entre les bits d'information et le nombre total de bits transmis. Un code de rendement 1/2 transmet 1 bit d'information pour 2 bits transmis (surdébit de 50 %). Le débit sur le canal doit donc être $R_{\text{channel}} = R_{\text{info}} / r$ : un code de rendement 1/2 exige une largeur de bande de canal double pour un débit d'information donné.

### 11.6.3 Tableau complet modulation et codage

| Modulation + codage | $E_b/N_0$ requis (TEB $10^{-6}$) | Efficacité spectrale (bit/s/Hz) | Utilisation typique | Mise en œuvre |
|--------------------|------------------------------------|-------------------------------|------------|----------------|
| GMSK non codée | 10,5 dB | ~1,0 | AX.25 amateur, historique | Circuit intégré radio simple |
| BPSK non codée | 10,5 dB | 1,0 | Télécommande historique | Simple |
| QPSK non codée | 10,5 dB | 2,0 | Télémesure simple | Modérée |
| QPSK + conv. (r = 1/2, K = 7) | 5,0 dB | 1,0 | TM CCSDS standard | Viterbi matériel |
| QPSK + conv. + RS (concaténé) | 3,0 dB | 0,88 | CCSDS à héritage en vol | Matérielle |
| QPSK + LDPC (r = 1/2) | 2,0 dB | 1,0 | Liaison descendante à haut rendement | Sur FPGA |
| QPSK + LDPC (r = 3/4) | 4,0 dB | 1,5 | **Équilibrée — recommandée** | Sur FPGA |
| QPSK + LDPC (r = 7/8) | 5,5 dB | 1,75 | Limitée par la largeur de bande | Sur FPGA |
| 8PSK + LDPC (r = 3/4) | 6,5 dB | 2,25 | Liaison descendante à haut débit | Sur FPGA |
| 16APSK + LDPC (r = 3/4) | 8,5 dB | 3,0 | Débit maximal | Sur FPGA |

**Recommandations de conception pour les CubeSats :**
- **UHF amateur :** GMSK ou AFSK (protocole AX.25) à un débit canal de 1,2–9,6 kbit/s. Ajouter un codage convolutif si la marge de liaison est serrée.
- **Bande S :** QPSK + LDPC (r = 1/2 ou r = 3/4). C'est le meilleur compromis : 5,5–8,5 dB de gain de codage pour une complexité maîtrisable. La plupart des émetteurs COTS en bande S pour CubeSat (Endurosat, NanoAvionics, AAC Clyde, à titre d'exemples représentatifs) prennent en charge nativement le LDPC DVB-S2 ou CCSDS.
- **Bande X / bande Ka :** 8PSK ou 16APSK + LDPC pour une efficacité spectrale maximale lorsque la largeur de bande est limitée.

---

## 11.7 Stations sol

La station sol constitue la moitié de la liaison de télécommunications. Ses performances ($G/T$) déterminent directement le débit atteignable. Améliorer la station sol est souvent le moyen le moins coûteux d'améliorer les performances de la liaison (comparé à l'amélioration de l'émetteur ou de l'antenne du satellite). L'architecture du segment sol dans son ensemble (stations, réseaux, contrôle de mission et systèmes de données) fait l'objet du chapitre 17.

### 11.7.1 Types de stations sol

| Type | Antenne | G/T (bande S) | Coût (indicatif, 2026) | Disponibilité | Exemples |
|------|---------|-------------|------|-------------|---------|
| **Amateur (SatNOGS)** | Yagi de 10–15 dBi | −15 à −10 dB/K | Gratuit (exploitation bénévole) | Réseau mondial, plus de 200 stations | Réseau SatNOGS |
| **Universitaire** | Parabole de 2–3 m | +10 à +15 dB/K | 50–200 k\$ (construction) | Disponibilité limitée | De nombreuses universités disposent de stations en bande S |
| **Commerciale (petite)** | Parabole de 3–5 m | +15 à +25 dB/K | 5–20 k\$ par mois ou 500 \$ par passage | KSAT Lite, AWS Ground Station | KSAT, Amazon, Leaf Space |
| **Commerciale (grande)** | Parabole de 5–13 m | +25 à +35 dB/K | 20–50 k\$ par mois ou 1000 \$ par passage | SSC, KSAT, ATLAS | SSC (Esrange), KSAT (Svalbard), ATLAS (Fairbanks) |
| **Deep Space Network** | Parabole de 34–70 m | +45 à +60 dB/K | Financement NASA uniquement | DSN (3 sites dans le monde) | Goldstone, Canberra, Madrid |

*[Source : tarifs KSAT Lite 2024 ; tarifs AWS Ground Station ; segment sol SSC SmallSat]*

### 11.7.2 Géométrie des contacts et durée des passages

Un satellite en LEO n'est visible d'une station sol que pendant un temps limité à chaque orbite. La durée du passage dépend de l'altitude de l'orbite et de l'angle d'élévation minimal utilisable. Le chapitre 7, §7.4.1, en donne la géométrie : l'angle au centre de la Terre entre la station et le satellite au masque d'élévation vaut

$$\lambda_{\max} = \arccos\!\left(\frac{R_E}{R_E + h}\cos\varepsilon_{\min}\right) - \varepsilon_{\min}$$

et le passage le plus long (à la verticale) dure environ $t_{\text{contact,max}} \approx (T/\pi)\,\lambda_{\max}$, où $T$ est la période orbitale. Les passages qui ne passent pas à la verticale sont plus courts ; le profil complet de l'élévation en fonction du temps au cours d'un passage est présenté au chapitre 17 (voir la figure 17.2).

| Altitude | Élévation min. | Durée maximale du passage | Durée utile typique | Passages par jour (latitude moyenne) |
|----------|--------------|-------------------|------------------------|--------------------------|
| 400 km | 10° | ~6 min | ~5 min | 3–4 |
| 500 km | 10° | ~7,4 min | ~6 min | 4–5 |
| 600 km | 10° | ~8,5 min | ~7 min | 4–5 |
| 800 km | 10° | ~10,5 min | ~9 min | 5–6 |

La « durée utile » est plus courte que le passage complet, car la liaison ne boucle qu'au-dessus de l'angle d'élévation minimal et les 30–60 premières et dernières secondes servent à l'acquisition du signal et à l'établissement de la liaison.

**Critères de choix d'une station sol :**
- **Emplacement :** les stations polaires (Svalbard à 78° N, McMurdo à 78° S) voient chaque orbite d'un satellite en orbite polaire ou SSO, soit 12 contacts par jour ou plus. Les stations de latitude moyenne ne voient que 3–5 passages. Les stations équatoriales voient encore moins de passages des satellites polaires.
- **G/T :** il détermine le débit atteignable. Une amélioration de 3 dB du G/T permet de doubler le débit.
- **Licences :** la station doit être compatible avec l'attribution de fréquences du satellite.
- **Coût :** de gratuit (SatNOGS, universités) à plus de 1000 \$ par passage (stations commerciales).
- **Fiabilité :** SLA (accord de niveau de service) pour les stations commerciales ; les stations universitaires peuvent avoir une disponibilité d'opérateurs limitée.

**PIRE (émission de la station sol, pour la liaison montante) :** pour la liaison montante de télécommande, c'est la station sol qui émet vers le satellite. La PIRE d'une station sol commerciale est généralement de 40–60 dBW, ce qui suffit à des liaisons de commande robustes, même avec des antennes de réception bord à faible gain.

---

## 11.8 Exemples résolus : bilans de liaison complets

### 11.8.1 EOSat-3U — liaison descendante en bande S

> **Exemple résolu — liaison descendante en bande S du CubeSat 3U d'observation de la Terre (classe SuperDove)**
>
> **Scénario :** SSO à 500 km, bande S (2250 MHz), liaison descendante à 1 Mbit/s, élévation minimale de 10° (distance oblique de 1695 km, §11.4.1), station sol à parabole de 3 m ($T_{sys} = 150$ K, $G_{RX} = 35$ dBi en bande S).
>
> | Ligne | Paramètre | Valeur | Unité | Calcul / source |
> |------|-----------|-------|------|--------------------|
> | 1 | Puissance d'émission (2 W) | +3,0 | dBW | Émetteur COTS en bande S |
> | 2 | Gain de l'antenne d'émission (patch) | +6,0 | dBi | Patch en bande S à élément unique |
> | 3 | Pertes de ligne à l'émission | −1,5 | dB | Câble de 15 cm + connecteur |
> | 4 | **PIRE** | **+7,5** | dBW | $3.0 + 6.0 - 1.5$ |
> | 5 | Affaiblissement en espace libre (2250 MHz, 1695 km) | −164,1 | dB | $92.45 + 20\log_{10}(1695) + 20\log_{10}(2.25)$ |
> | 6 | Affaiblissement atmosphérique | −0,5 | dB | Bande S, 10° d'élévation |
> | 7 | Perte de dépointage | −1,0 | dB | Dépointage de 5°, patch d'ouverture 80° |
> | 8 | Perte de polarisation (RHCP–RHCP) | −0,3 | dB | Léger écart de rapport axial |
> | 9 | Gain de l'antenne de réception (parabole de 3 m) | +35,0 | dBi | $10\log_{10}(0.6 \times (\pi \times 3.0 / 0.133)^2)$ |
> | 10 | Température de bruit du système (150 K) | 21,8 | dBK | LNA professionnel + température du ciel (perte de ligne en réception incluse) |
> | 11 | **G/T** | **+13,2** | dB/K | $35.0 - 21.8$ |
> | 12 | Constante de Boltzmann | +228,6 | dBW/K/Hz | $-k$ dans l'équation de liaison |
> | 13 | **C/N$_0$** | **+83,4** | dBHz | $7.5 - 164.1 - 0.5 - 1.0 - 0.3 + 13.2 + 228.6$ |
> | 14 | Débit (1 Mbit/s) | 60,0 | dB(bit/s) | $10\log_{10}(10^6)$ |
> | 15 | **$E_b/N_0$ disponible** | **+23,4** | dB | $83.4 - 60.0$ |
> | 16 | $E_b/N_0$ requis (QPSK + LDPC r = 3/4) | 4,0 | dB | D'après le tableau modulation/codage |
> | 17 | Perte d'implémentation | 2,0 | dB | Démodulateur réel par rapport à l'idéal |
> | 18 | **MARGE DE LIAISON** | **+17,4** | dB | $23.4 - 4.0 - 2.0$ |
>
> **Résultat :** la liaison boucle avec une marge de 17,4 dB (exigence : ≥ 3 dB). **Conforme.**
>
> **Enseignement pour la conception :** la marge confortable montre que la liaison dispose d'un large excédent de puissance à 1 Mbit/s. Le débit pourrait être nettement augmenté :
>
> Débit maximal pour une marge de 3 dB : $E_b/N_0$ disponible au débit maximal $= 4.0 + 2.0 + 3.0 = 9.0$ dB ; avec $C/N_0 = 83.4$ dBHz, on obtient $R_{b,\max} = 10^{(83.4 - 9.0)/10} = 10^{7.44} \approx$ **27 Mbit/s** du seul point de vue de la puissance.
>
> En pratique, c'est l'attribution en bande S, et non la puissance, qui limite : un canal de 5 MHz à 1,5 bit/s/Hz (QPSK + LDPC r = 3/4) transporte au plus 7,5 Mbit/s environ. À 5 Mbit/s ($10\log_{10}(5 \times 10^6) = 67.0$ dB(bit/s)) : $E_b/N_0 = 83.4 - 67.0 = 16.4$ dB ; marge $= 16.4 - 4.0 - 2.0 = 10.4$ dB. **Conforme.** Les 7 dB restants au-delà de l'exigence méritent d'être conservés comme marge de conception à ce stade, ou pourront être échangés plus tard contre un émetteur moins puissant (0,5 W au lieu de 2 W coûte 6 dB et la liaison boucle encore avec 4,4 dB) ou contre une parabole sol plus petite. Le cas à 5 Mbit/s est celui qui est repris dans le bilan de données du §11.9.

La figure 11.5 présente ce bilan sous forme de cascade. En la lisant de gauche à droite, les gains font monter le $C/N_0$ cumulé et les pertes le font baisser ; la valeur finale est comparée à ce qu'exigent la modulation, le codage et le débit choisis.

![Bilan de liaison en cascade de la liaison descendante en bande S.](../assets/figures/fig_link_budget.png)

**Figure 11.5** — Bilan de liaison en cascade de la liaison descendante en bande S du §11.8.1 (émetteur de 2 W, antenne patch de 6 dBi, 2,25 GHz sur une distance oblique de 1695 km à 10° d'élévation, parabole sol de 3 m à 150 K). Les barres vertes sont des gains, les barres orange des pertes ; la ligne tiretée indique le $C/N_0$ reçu de 83,4 dBHz et la ligne pointillée les 73,0 dBHz requis à 5 Mbit/s (QPSK + LDPC r = 3/4, plus 2 dB de perte d'implémentation). L'écart entre les deux correspond à la marge de liaison de 10,4 dB.

### 11.8.2 Retour sur UniSat-1 : bilan de liaison UHF à 437 MHz et 9600 bit/s

UniSat-1 utilise la bande UHF amateur à 437 MHz avec une station sol équipée d'une antenne Yagi de 10 dBi. C'est l'architecture de télécommunications la moins coûteuse et la plus simple dont disposent les missions CubeSat.

> **Exemple résolu — bilan de liaison descendante UHF d'UniSat-1**
>
> **Scénario :** orbite à 400 km, UHF (437 MHz), liaison descendante à 9600 bit/s (GMSK), angle d'élévation minimal de 10°, station sol amateur équipée d'une antenne Yagi de 10 dBi, $T_{sys} = 600$ K (LNA COTS, pertes du câble coaxial, bruit du ciel près de l'horizon).
>
> **Distance oblique à 10° d'élévation :** depuis une altitude de 400 km, la distance oblique la plus défavorable à 10° d'élévation est de 1440 km (§11.4.1).
>
> | Ligne | Paramètre | Valeur | Unité | Remarques |
> |------|-----------|-------|------|-------|
> | 1 | Puissance d'émission (0,5 W) | −3,0 | dBW | Radio UHF standard de CubeSat |
> | 2 | Gain de l'antenne d'émission (monopôle) | 0,0 | dBi | Monopôle quart d'onde, ~omnidirectionnel |
> | 3 | Pertes de ligne à l'émission | −0,5 | dB | Câble court jusqu'à l'antenne |
> | 4 | **PIRE** | **−3,5** | dBW | La faible PIRE est la difficulté fondamentale en UHF |
> | 5 | Affaiblissement en espace libre (437 MHz, 1440 km) | −148,4 | dB | $92.45 + 20\log_{10}(1440) + 20\log_{10}(0.437)$ ; ~16 dB de moins qu'en bande S |
> | 6 | Affaiblissement atmosphérique | −0,3 | dB | L'affaiblissement atmosphérique est minime en UHF |
> | 7 | Perte de dépointage (antenne omnidirectionnelle) | −0,5 | dB | Diagramme omnidirectionnel : négligeable |
> | 8 | Perte de polarisation (linéaire–linéaire) | −3,0 | dB | **Perte majeure** : la rotation de Faraday dans l'ionosphère fait tourner la polarisation de façon aléatoire |
> | 9 | Gain de l'antenne de réception (Yagi de 10 dBi) | +10,0 | dBi | Yagi à 5 éléments, poursuite manuelle |
> | 10 | Température de bruit du système (600 K) | 27,8 | dBK | Station amateur : LNA non refroidi + pertes de câble |
> | 11 | **G/T** | **−17,8** | dB/K | Le faible G/T est la limite de la station sol |
> | 12 | Constante de Boltzmann | +228,6 | dBW/K/Hz | |
> | 13 | **C/N$_0$** | **+55,1** | dBHz | $-3.5 - 148.4 - 0.3 - 0.5 - 3.0 - 17.8 + 228.6$ |
> | 14 | Débit (9600 bit/s) | 39,8 | dB(bit/s) | |
> | 15 | **$E_b/N_0$ disponible** | **+15,3** | dB | |
> | 16 | $E_b/N_0$ requis (GMSK non codée) | 10,5 | dB | |
> | 17 | Perte d'implémentation | 2,0 | dB | |
>
> **Marge = 15,3 − 10,5 − 2,0 = +2,8 dB. Inférieure à l'exigence de 3 dB : la liaison ne satisfait pas la spécification**, et la ligne de perte de polarisation de −3,0 dB n'est qu'une moyenne : lorsque le plan tourné par l'effet Faraday est presque orthogonal à la Yagi, la perte peut atteindre 20 dB ou plus, et la liaison décroche complètement.
>
> **Parade 1 : ajouter une FEC.** Codage convolutif (r = 1/2, K = 7) :
> - l'$E_b/N_0$ requis tombe à **5,0 dB** (gain de codage de 5,5 dB) ;
> - le débit canal reste de 9600 bit/s, mais le débit utile est de 4800 bit/s (la moitié est de la redondance) ;
> - **marge** = 15,3 − 5,0 − 2,0 = **+8,3 dB** : l'exigence est satisfaite, mais les évanouissements dus à l'effet Faraday subsistent.
>
> **Parade 2 : remplacer l'antenne sol par une Yagi croisée (13 dBi) à polarisation circulaire :**
> - gain de réception : +13,0 dBi (contre +10,0) → amélioration de +3,0 dB ;
> - perte de polarisation : −0,5 dB (contre −3,0 dB, désormais RHCP vers RHCP) → amélioration de +2,5 dB, et les évanouissements profonds disparaissent ;
> - amélioration nette : +5,5 dB ;
> - nouveau C/N$_0$ : 60,6 dBHz ;
> - nouvel $E_b/N_0$ disponible : 60,6 − 39,8 = 20,8 dB ;
> - **marge** (avec FEC) = 20,8 − 5,0 − 2,0 = **+13,8 dB** : **validé** ; même sans codage, la marge serait de 8,3 dB.
>
> **Physique de la perte de polarisation :** en UHF (437 MHz), l'ionosphère provoque une rotation de Faraday des signaux polarisés linéairement. L'angle de rotation dépend du contenu électronique total (TEC) le long du trajet et varie selon l'heure, l'activité solaire et le trajet du signal. Si le satellite émet en polarisation linéaire et que la station sol reçoit en polarisation linéaire, les plans de polarisation peuvent être orthogonaux par moments, ce qui peut aller jusqu'à la perte complète du signal (perte théoriquement infinie, évanouissements de 20 dB et plus en pratique). L'utilisation d'une polarisation circulaire à au moins une extrémité (de préférence aux deux) élimine la perte due à la rotation de Faraday et la ramène à ~0,3–0,5 dB d'écart de rapport axial. **C'est pourquoi la polarisation circulaire est obligatoire pour des liaisons satellite UHF fiables.**
>
> **Synthèse du bilan de liaison final (avec FEC + Yagi croisée) :** le codage est conservé bien que la liaison en polarisation circulaire boucle sans codage, car la température de bruit de la station amateur, les zéros du diagramme du monopôle et la poursuite assurée par la station sont tous moins certains que ne le suppose le bilan. La marge de 13,8 dB absorbe ces incertitudes ; le prix à payer est la moitié du débit.
>
> | Paramètre | Valeur |
> |-----------|-------|
> | Puissance d'émission | 0,5 W |
> | Antenne d'émission | Monopôle (0 dBi) |
> | Fréquence | 437 MHz |
> | Débit canal | 9600 bit/s |
> | Débit utile | 4800 bit/s (avec FEC r = 1/2) |
> | Antenne sol | Yagi croisée de 13 dBi, RHCP |
> | Marge de liaison | **+13,8 dB** |

**Débit de données d'UniSat-1 :** avec un débit utile de 4800 bit/s, un passage offrant 5 minutes de contact utile (§11.7.2, 400 km) fournit :
$V_{\text{pass}} = 4800 \times 300 \times 0.85 = 1.22$ Mbit $= 153$ ko par passage.

Le facteur 0,85 tient compte du surdébit protocolaire (en-têtes de paquets, acquittements, retransmissions, temps d'établissement de la liaison).

Avec 4 passages par jour : $V_{\text{daily}} = 612$ ko/jour $\approx$ **0,6 Mo/jour**. Le magnétomètre génère $< 1$ kbit/s $\times$ 600 s/orbite $\times$ 15 orbites $= 9$ Mbit/jour $= 1.13$ Mo/jour. **Le bilan de données ne boucle pas avec une seule station sol** : il faut environ huit passages par jour. La solution la moins coûteuse consiste à augmenter le temps de contact : le réseau SatNOGS (plus de 200 stations bénévoles dans le monde) peut fournir gratuitement plus de 10 contacts supplémentaires par jour, puisque le protocole amateur ouvert permet à n'importe quelle station de recevoir les données. Les autres options consistent à réduire le volume de données (fréquence d'échantillonnage plus basse ou moyennage à bord) ou à renoncer à la FEC en acceptant une marge plus faible.

**Leçon clé du bilan de liaison d'UniSat-1 :** les liaisons UHF manquent de puissance par rapport aux liaisons en bande S ou X. L'affaiblissement en espace libre plus faible à 437 MHz (~16 dB de moins qu'en bande S à élévation comparable) ne compense pas la faible puissance d'émission (0,5 W contre 2 W, soit 6 dB de moins), le faible gain d'antenne (0 dBi contre 6 dBi, soit 6 dB de moins) et la température de bruit système plus élevée des stations amateurs (600 K contre 150 K, soit 6 dB de plus). Le codage FEC et la polarisation circulaire sont indispensables pour faire boucler une liaison UHF de CubeSat.

---

## 11.9 Bilan de données

Le bilan de données détermine si le système de télécommunications peut acheminer au sol toutes les données de la mission. Même si le bilan de liaison boucle, la mission échoue si le volume total de données dépasse la capacité de la liaison descendante. Le chapitre 4, §4.8.5, a introduit cette notion dans le cadre du flux de données du ConOps ; cette section la quantifie, et le chapitre 12, §12.3.3, dimensionne le stockage à bord qui absorbe l'écart.

> **Équations clés — bilan de données**
>
> **Volume de données généré par jour :**
> $$V_{\text{gen}} = R_{\text{payload}} \times t_{\text{imaging}} \times N_{\text{orbits}} \times f_{\text{compression}}$$
>
> **Capacité quotidienne de la liaison descendante** (forme canonique utilisée dans tout cet ouvrage) :
> $$C_{\text{downlink}} = R \cdot N_{\text{passes}} \cdot t_{\text{contact}} \cdot \eta_{\text{protocol}}$$
>
> où $R$ est le débit utile (d'information), $N_{\text{passes}}$ le nombre de passages utilisables par jour, $t_{\text{contact}}$ le temps de contact utile par passage, et $\eta_{\text{protocol}} = 0.80$–$0.90$ tient compte du surdébit des paquets, des retransmissions, du temps d'établissement de la liaison et des échanges de protocole. (Certains ouvrages notent cette capacité $V_{\text{DL}}$ ; il s'agit de la même grandeur.)
>
> **Bouclage du bilan de données :**
> $$C_{\text{downlink}} \geq V_{\text{gen}} \quad \text{(le bilan de données boucle)}$$
>
> **Temps de résorption de l'arriéré :** si un excédent temporaire $V_{\text{stored}}$ s'est accumulé dans le stockage à bord (après une interruption, par exemple) et que $C_{\text{downlink}} > V_{\text{gen}}$, l'arriéré se résorbe en
> $$t_{\text{clear}} = \frac{V_{\text{stored}}}{C_{\text{downlink}} - V_{\text{gen}}}$$
> Si $C_{\text{downlink}} < V_{\text{gen}}$ de façon durable, l'arriéré croît sans limite : la mission ne peut pas soutenir son rythme de génération de données.

> **Exemple résolu — bilan de données du CubeSat 3U d'observation de la Terre**
>
> **Première estimation de la génération :** 240 Mbit/s de données d'imagerie brutes × 5 min/orbite × 15 orbites/jour × 0,25 (compression JPEG2000 4:1)
> $= 240 \times 300 \times 15 \times 0.25 = 270\,000$ Mbit/jour = **33,75 Go/jour**
>
> C'est bien au-delà de toute liaison descendante en bande S, et c'est de surcroît irréaliste : toutes les orbites ne comportent pas de cible. En supposant 4 passages de prise de vue de 5 minutes chacun par jour :
>
> $V_{\text{gen}} = 240 \times 10^6 \times 300 \times 4 \times 0.25 = 72\,000$ Mbit $= 9.0$ Go/jour
>
> C'est encore trop. Les SuperDove de Planet effectuent leurs prises de vue pendant environ 1–2 minutes par orbite au-dessus de cibles prioritaires, compressent fortement (10:1 ou plus) et transmettent au sol de façon sélective.
>
> **Génération révisée :** 240 Mbit/s × 1 min/passage × 4 passages/jour × 0,10 (compression 10:1) $= 240 \times 60 \times 4 \times 0.10 = 5\,760$ Mbit = **720 Mo/jour**
>
> **Capacité de la liaison descendante (bande S à 5 Mbit/s, §11.8.1) :**
> $C_{\text{downlink}} = 5 \times 10^6 \times 5 \times 360 \times 0.85 = 7\,650$ Mbit $= 956$ Mo/jour
>
> **Résultat :** 956 Mo/jour > 720 Mo/jour. **Le bilan de données boucle** avec une marge de 33 %.
>
> **Sensibilité :** si le rapport cyclique d'imagerie double (2 min/passage), la génération passe à 1440 Mo/jour > 956 Mo/jour. Options : (a) bande X pour un débit plus élevé, (b) stations sol supplémentaires, (c) compression plus agressive, (d) hiérarchisation et sélection des données à bord.

La figure 11.6 replace ces chiffres dans leur contexte : capacité quotidienne de la liaison descendante par bande pour une seule station sol polaire, comparée à la production quotidienne de charges utiles représentatives. Une liaison UHF ne peut même pas acheminer la télémesure de servitude d'une mission d'imagerie ; la bande S transporte sans difficulté un imageur monobande à 1–4 Mbit/s ; les charges utiles radar à synthèse d'ouverture (SAR) et hyperspectrales exigent la bande X ou mieux.

![Capacité quotidienne de la liaison descendante par bande — vérification du bouclage du bilan de données.](../assets/figures/fig_data_volume.png)

**Figure 11.6** — Capacité quotidienne de la liaison descendante (Go/jour, échelle logarithmique) pour cinq combinaisons de bande et de débit, chacune supposant quatre passages de 8 minutes par jour au-dessus d'une seule station sol polaire, sans surdébit protocolaire. Les lignes verticales marquent la production quotidienne de données de charges utiles représentatives, de la seule télémesure de servitude (5 Mo) à un SAR à données compressées (30 Go). Une ligne de charge utile située à droite d'une barre signifie que cette configuration ne peut pas faire boucler le bilan de données.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Bilan de liaison | $\text{Marge} = E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}} \geq 3$ dB |
| PIRE | $\text{PIRE} = P_{TX} + G_{TX} - L_{TX}$ : puissance effective de l'émetteur dans la direction du faisceau |
| Physique de l'affaiblissement en espace libre | Étalement géométrique ($1/d^2$) + variation de l'ouverture ($\lambda^2$) ; pas d'absorption d'énergie |
| Formule de l'affaiblissement en espace libre | $92.45 + 20\log_{10}(d_{km}) + 20\log_{10}(f_{GHz})$ ; augmente de 6 dB à chaque doublement de la fréquence ou de la distance |
| Distance oblique | 1440 km à 400 km / 10° d'élévation ; 1695 km à 500 km / 10° ; passer du nadir à 10° coûte ~10,6 dB |
| G/T | Facteur de qualité du récepteur : gain d'antenne moins température de bruit ; paramètre le plus important d'une station sol |
| Types d'antennes | Du monopôle (0 dBi, omnidirectionnel) au réflecteur parabolique (25–45 dBi, faisceau étroit) ; compromis entre gain et pointage |
| Gain d'antenne | $G = \eta_a (\pi D/\lambda)^2$ ; patch ~6 dBi ; parabole de 3 m : 35 dBi en bande S ; parabole de 30 cm : 14 dBi en bande S, 26 dBi en bande X |
| Perte de dépointage | $-12(\Delta\theta/\theta_{3\text{dB}})^2$ dB ; faisceau plus étroit = plus sensible aux erreurs de pointage |
| Modulation | QPSK : 2 bits/symbole, même $E_b/N_0$ que la BPSK mais efficacité spectrale multipliée par 2 ; **choix standard** |
| Codage FEC | LDPC (r = 3/4) : $E_b/N_0 = 4.0$ dB, gain de codage ~6,5 dB ; **indispensable aux liaisons spatiales** |
| Gain de codage | Amélioration de 5–10 dB presque gratuite (simple traitement numérique) ; équivaut à multiplier la puissance par 3 à 10 |
| Difficultés de l'UHF | Faible PIRE, rotation de Faraday (utiliser la polarisation circulaire), bruit élevé des stations sol ; FEC obligatoire |
| Choix de la bande | UHF pour < 9,6 kbit/s (gratuite, amateur) ; bande S pour < 10 Mbit/s ; bande X pour < 400 Mbit/s ; bande Ka pour > 400 Mbit/s |
| Évanouissement dû à la pluie | Négligeable sous 4 GHz ; 1–3 dB en bande X ; 3–15 dB en bande Ka ; ajouter de la marge ou un débit adaptatif |
| Stations sol | G/T : amateur −15 dB/K, universitaire +12 dB/K, commerciale +25 dB/K ; les stations polaires voient chaque orbite |
| Bilan de données | $C_{\text{downlink}} = R \cdot N_{\text{passes}} \cdot t_{\text{contact}} \cdot \eta_{\text{protocol}}$ doit dépasser la génération quotidienne ; le taux de compression est un levier essentiel |
| Licences | Amateur (gratuite, IARU, 3–6 mois) ; bande X (12 mois et plus, 50–80 k\$) ; bande S (6–12 mois, 30–45 k\$), à titre indicatif (2026) |

---

## Exercices

1. **Calcul en décibels.** Convertissez dans les unités demandées : 4 W en dBW et en dBm ; −7 dBW en watts ; un rapport de gain de 2500 en dB ; 27 dBm en watts. Montrez ensuite, à l'aide de la forme en dB de l'équation de liaison, pourquoi doubler le débit réduit la marge de liaison d'exactement 3 dB.

2. **Affaiblissement en espace libre.** Calculez l'affaiblissement en espace libre pour (a) 437 MHz à 1440 km, (b) 2250 MHz à 1695 km et (c) 8,2 GHz à 2330 km, et comparez (b) à la figure 11.3. Calculez ensuite la distance oblique depuis une orbite à 550 km pour des élévations de 5°, 10° et 30° à l'aide de la formule du §11.4.1, et indiquez la pénalité d'affaiblissement, en dB, d'une conception avec un masque de 5° plutôt que de 10° en bande S.

3. **Dimensionnement d'antenne.** Une station sol doit utiliser une parabole de 1,2 m avec $\eta_a = 0.6$. Calculez son gain et son ouverture de faisceau à mi-puissance en bande S (2,25 GHz) et en bande X (8,2 GHz). Si l'erreur de poursuite de la station est de 0,5° (1σ), calculez la perte de dépointage dans chaque bande et indiquez si la parabole est utilisable en bande X sans monture améliorée.

4. **Bilan de liaison en bande X.** Reprenez l'exemple résolu du §11.8.1 pour une liaison descendante en bande X : 8,2 GHz, émetteur de 2 W, réseau de patchs de 12 dBi sur le satellite (ouverture de faisceau de 30°, dépointage de 3°), distance oblique de 1695 km, affaiblissement atmosphérique de 1,0 dB, perte de polarisation de 0,3 dB, parabole sol de 3 m avec $T_{sys} = 200$ K, 8PSK + LDPC r = 3/4 et perte d'implémentation de 2 dB. Déterminez le débit maximal pour une marge de 3 dB et comparez-le au résultat en bande S. La limite est-elle fixée par la puissance ou par la largeur de bande attribuée ?

5. **Puissance d'émission minimale.** Pour la liaison d'UniSat-1 du §11.8.2 dans sa configuration finale (Yagi croisée, RHCP, code convolutif de rendement 1/2), déterminez la puissance d'émission la plus faible qui donne encore une marge de 3 dB. Déterminez ensuite la puissance la plus faible qui permet de boucler sans codage au débit plein de 9600 bit/s. Indiquez, en une phrase pour chaque point, ce qui change par ailleurs sur le satellite lorsque la puissance d'émission diminue (chapitre 9) et pourquoi l'option sans codage est plus risquée que ne le laissent penser les chiffres.

6. **Rotation de Faraday.** Expliquez, en vous référant au contenu électronique total de l'ionosphère, pourquoi une liaison UHF à polarisation linéaire subit une perte de polarisation aléatoire alors qu'une liaison en bande S ne nécessite pas le même traitement (l'angle de rotation varie comme $1/f^2$). Si le monopôle d'UniSat-1 était remplacé par une antenne tourniquet rayonnant en RHCP, quelle ligne du bilan de liaison changerait, et de combien ?

7. **Bouclage du bilan de données.** Un CubeSat 3U d'observation de la Terre génère 1,2 Go/jour après compression. À l'aide de $C_{\text{downlink}} = R \cdot N_{\text{passes}} \cdot t_{\text{contact}} \cdot \eta_{\text{protocol}}$, avec $\eta_{\text{protocol}} = 0.85$ et 6 minutes de contact utile par passage, déterminez le nombre de passages en bande S à 5 Mbit/s nécessaires chaque jour pour faire boucler le bilan. Si seuls cinq passages sont disponibles, quel débit minimal faut-il, et quelle bande du §11.5.1 choisiriez-vous ? Enfin, après une interruption de la station sol pendant trois jours, combien de temps faut-il pour résorber l'arriéré à 5 Mbit/s avec sept passages par jour ?

8. **Choix de la bande.** Une jeune entreprise propose un imageur multispectral 6U produisant 25 Go/jour et souhaite disposer des données au sol dans les 6 heures suivant l'acquisition. À l'aide du tableau comparatif des bandes, de l'arbre de décision du §11.5.2 et de la figure 11.6, choisissez une bande, estimez le coût et le délai d'obtention de la licence (à titre indicatif), et identifiez les deux sous-systèmes du satellite les plus touchés par ce choix (chapitres 9 et 10).

9. **Comparaison de stations sol.** Comparez deux options pour la mission EOSat-3U : (a) une station universitaire de 2,5 m avec $G/T = +12$ dB/K voyant quatre passages par jour, et (b) une station polaire commerciale avec $G/T = +25$ dB/K voyant douze passages par jour, à un tarif indicatif (en \$) de 500 par passage. Pour chacune, calculez le débit maximal pour une marge de 3 dB (à l'aide du bilan du §11.8.1 avec le nouveau $G/T$) et la capacité quotidienne. Quelle option achemine le plus de données par an, et à quel coût par gigaoctet ?

10. **Codage ou matériel.** Montrez que le remplacement d'une liaison QPSK non codée par une liaison QPSK + LDPC r = 1/2 au même débit *d'information* équivaut, en marge de liaison, à multiplier la puissance d'émission par 7, et indiquez le prix payé en largeur de bande de canal. Pour une liaison en bande S limitée à 5 MHz, quel schéma du tableau du §11.6.3 maximise le débit d'information tout en maintenant la marge d'EOSat-3U du §11.8.1 au-dessus de 3 dB ?

---

## Références

1. Wertz, J. R., Everett, D. F. & Puschell, J. J. (dir.), *Space Mission Engineering: The New SMAD*, Microcosm Press, 2011, chap. 13 (*Communications*). https://www.space.com/smad
2. ECSS, *ECSS-E-ST-50-05C Rev. 2: Radio Frequency and Modulation*, 2011. https://ecss.nl/standard/ecss-e-st-50-05c-radio-frequency-and-modulation/
3. CCSDS, *131.0-B-4: TM Synchronization and Channel Coding*, 2023. https://public.ccsds.org/Pubs/131x0b4.pdf
4. UIT, *Radio Regulations* (Règlement des radiocommunications), 2020 (articles 5 et 22). https://www.itu.int/en/publications/ITU-R/pages/default.aspx
5. Maral, G. & Bousquet, M., *Satellite Communications Systems*, 6e éd., Wiley, 2020, chap. 5. https://www.wiley.com/en-us/Satellite+Communications+Systems
6. Roddy, D., *Satellite Communications*, 4e éd., McGraw-Hill, 2006, chap. 4–6. https://www.mhprofessional.com
7. Haykin, S., *Communication Systems*, 5e éd., Wiley, 2009. https://www.wiley.com
8. Sklar, B., *Digital Communications: Fundamentals and Applications*, 2e éd., Prentice Hall, 2001. https://www.pearson.com
9. IARU, *Amateur Satellite Frequency Coordination*, 2023. https://www.iaru.org/satellite/
10. Balanis, C. A., *Antenna Theory: Analysis and Design*, 4e éd., Wiley, 2016.
11. ETSI, *EN 302 307: Digital Video Broadcasting (DVB) ; Second generation framing structure, channel coding and modulation systems (DVB-S2)*, 2014. https://www.etsi.org
12. Pratt, T., Bostian, C. & Allnutt, J., *Satellite Communications*, 3e éd., Wiley, 2019.
