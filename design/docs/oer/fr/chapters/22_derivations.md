# Partie V — Démonstrations à partir des premiers principes

Cette partie démontre, à partir des premiers principes, les formules appliquées dans les parties I–III. Chaque démonstration est accompagnée d'un contrôle de vraisemblance détaillé par rapport à une valeur de référence publiée et — lorsque les chapitres ne le montrent pas déjà — d'un graphique de la formule en application.

L'objectif est double : (a) offrir au lecteur un endroit où trouver le *pourquoi* de toute formule qu'il applique ; (b) fournir une piste de vérification détaillée qu'un examinateur peut auditer lors d'une revue de conception. Lorsque la même équation figure dans un chapitre des parties I–III, la démonstration utilise ici exactement les symboles de ce chapitre, afin que les deux puissent être lus en parallèle.

> **Référence normative.** Les constantes et conventions utilisées dans toute cette partie suivent Vallado, *Fundamentals of Astrodynamics and Applications* (4e éd.) et les IERS Conventions 2010 — [https://www.iers.org/IERS/EN/Publications/TechnicalNotes/tn36.html](https://www.iers.org/IERS/EN/Publications/TechnicalNotes/tn36.html).

---

## V.1 — Constantes utilisées (Terre)

| Symbole | Valeur | Signification | Source |
|--------|-------|---------|--------|
| $\mu$ | 398 600,44 km³/s² | Paramètre gravitationnel terrestre | IERS Conventions 2010 |
| $R_E$ | 6378,137 km | Rayon équatorial terrestre | WGS-84 |
| $J_2$ | 1,0826 × 10⁻³ | Coefficient d'aplatissement de la Terre | Vallado §3.3 |
| $\omega_E$ | 7,292 115 × 10⁻⁵ rad/s | Vitesse de rotation de la Terre | IERS |
| $g_0$ | 9,806 65 m/s² | Pesanteur normale | ISO 80000-3 |
| $S$ | 1361 W/m² | Constante solaire à 1 ua | Kopp et Lean (2011) ; NASA SORCE |
| $\sigma$ | 5,670 374 × 10⁻⁸ W/(m²·K⁴) | Constante de Stefan-Boltzmann | CODATA 2018 |
| $k_B$ | 1,380 649 × 10⁻²³ J/K | Constante de Boltzmann | CODATA 2018 |
| $k$ | −228,6 dBW/K/Hz | Constante de Boltzmann en unités de bilan de liaison, $10\log_{10} k_B$ | calculée |
| $c$ | 2,997 924 58 × 10⁸ m/s | Vitesse de la lumière | exacte (SI) |

Ce sont les valeurs utilisées dans tous les résultats numériques des parties I–III. En particulier, toutes les grandeurs orbitales utilisent $R_E = 6378.137$ km ; les références plus anciennes qui utilisent un rayon moyen de 6371 km donnent des périodes plus courtes d'environ 0,1 min aux altitudes LEO.

---

## V.2 — Troisième loi de Kepler

### Démonstration

Pour une orbite circulaire de rayon $a$, l'accélération centripète est égale à l'attraction gravitationnelle :

$$ \frac{v^2}{a} = \frac{\mu}{a^2} $$

On substitue $v = 2\pi a / T$ et on résout en $T$ :

$$ T = 2\pi \sqrt{\frac{a^3}{\mu}} $$

Pour les orbites elliptiques, la même formule s'applique, $a$ étant le demi-grand axe. La vitesse circulaire vaut $v = \sqrt{\mu/a}$. Ce sont les formes utilisées au chapitre 7, §7.1.1.

### Vérification

La figure D.1 superpose la courbe analytique aux périodes d'orbites connues.

![Troisième loi de Kepler vérifiée sur des orbites connues.](../assets/figures/fig_kepler_proof.png)

**Figure D.1** — Courbe analytique période–altitude superposée à des orbites connues (ISS, Sentinel-2, GPS, GEO). L'accord est meilleur que 0,5 %, l'erreur résiduelle étant imputable à la correction séculaire du $J_2$, non appliquée ici. En GEO, $T = 1436$ min, contre un jour sidéral de 23,93 h × 60 = 1436 min.

**Contrôle de vraisemblance détaillé.** Pour une orbite héliosynchrone à 450 km :

$a = 6378.137 + 450 = 6828.137$ km ;
$a^3/\mu = 6828.137^3 / 398\,600.44 = 7.987 \times 10^5$ s² ; $\sqrt{\,\cdot\,} = 893.7$ s ;
$T = 2\pi \times 893.7 = 5615$ s $= 93.6$ min.

Le même calcul à 500 km donne $a = 6878.137$ km et $T = 94.6$ min, et à 400 km, 92,6 min — les valeurs utilisées dans tout le chapitre 7 et dans les chapitres consacrés aux sous-systèmes. Exprimés en mouvement moyen, 93,6 min correspondent à 15,38 révolutions par jour ; les valeurs légèrement inférieures indiquées dans les TLE de satellites réels à cette altitude (≈ 15,2–15,3 rév./jour) traduisent la perturbation de la période nodale par le $J_2$, et non une erreur de la formule.

---

## V.3 — Équation de Tsiolkovski

### Démonstration

Pour une fusée à vitesse d'éjection $v_e$ constante, la conservation de la quantité de mouvement entre les instants $t$ et $t + dt$ donne

$$ m\, dv = -v_e\, dm $$

On intègre de $m_0$ (masse totale initiale) à $m_f$ (masse sèche finale) :

$$ \Delta V = v_e \ln \frac{m_0}{m_f} = I_{sp}\, g_0\, \ln \frac{m_0}{m_f} $$

puisque $v_e = I_{sp}\, g_0$ par définition de l'impulsion spécifique. La masse d'ergols s'en déduit, $m_p = m_f\,(e^{\Delta V/(I_{sp} g_0)} - 1)$, ainsi que l'impulsion totale $I_{tot} = m_p\, I_{sp}\, g_0$. Le chapitre 12, §12.2.2, applique l'équation, et la figure 12.2 trace $\Delta V$ en fonction du rapport de masse pour des impulsions spécifiques représentatives.

### Vérification

**Contrôle de vraisemblance détaillé.** Transfert de Hohmann d'une orbite circulaire à 400 km vers l'orbite GEO (le cas tracé à la figure 7.4 du chapitre 7) :

$r_1 = 6778.137$ km, $r_2 = 42\,164$ km, $a_t = (r_1 + r_2)/2 = 24\,471$ km.

Au périgée : $v_1 = \sqrt{\mu/r_1} = 7.669$ km/s ; $v_p = \sqrt{\mu\,(2/r_1 - 1/a_t)} = 10.066$ km/s ; $\Delta V_1 = 2.397$ km/s.

À l'apogée : $v_2 = \sqrt{\mu/r_2} = 3.075$ km/s ; $v_a = \sqrt{\mu\,(2/r_2 - 1/a_t)} = 1.618$ km/s ; $\Delta V_2 = 1.456$ km/s.

Total : $\Delta V = 3.854$ km/s — conforme à la figure 7.4 (≈ 3,85 km/s) ; la somme des composantes arrondies donne 3,853 km/s. Pour le cas de désorbitation du chapitre 12, §12.2.5 (orbite circulaire à 600 km vers un périgée à 200 km), le même calcul fondé sur l'équation de la force vive donne 112 m/s.

---

## V.4 — Régression nodale due au $J_2$

### Démonstration

La principale perturbation séculaire due à l'aplatissement terrestre $J_2$ produit une vitesse de régression nodale (Vallado, éq. 9-37) :

$$ \dot{\Omega} = -\frac{3}{2}\, n\, J_2\, \left(\frac{R_E}{a(1-e^2)}\right)^2 \cos i $$

où $n = \sqrt{\mu/a^3}$ est le mouvement moyen. Le signe moins signifie que le nœud régresse pour les orbites progrades ($\cos i > 0$) et progresse pour les orbites rétrogrades ($\cos i < 0$).

### Condition d'héliosynchronisme

Pour une orbite héliosynchrone, on pose $\dot{\Omega}$ égal au mouvement moyen de la Terre autour du Soleil (360°/365,25 jours = 0,9856°/jour = 1,991 × 10⁻⁷ rad/s) :

$$ \cos i_{SSO} = -\frac{2\, \dot{\Omega}_\odot\, a^{7/2}\, (1-e^2)^2}{3\, J_2\, R_E^2\, \sqrt{\mu}} $$

C'est la condition appliquée au chapitre 7, §7.3.4.

### Vérification

La figure D.2 montre la vitesse de régression en fonction de l'inclinaison pour plusieurs altitudes.

![Vitesse de régression nodale due au J₂ en fonction de l'inclinaison pour plusieurs altitudes.](../assets/figures/fig_j2_nodal.png)

**Figure D.2** — Vitesse de régression nodale $\dot{\Omega}$ en fonction de l'inclinaison pour plusieurs altitudes. L'horizontale tiretée à 0,9856°/jour est la cible héliosynchrone ; son intersection avec chaque courbe d'altitude donne l'inclinaison héliosynchrone à cette altitude (≈ 98,2° à 700 km).

**Contrôle de vraisemblance détaillé.** Pour une orbite circulaire à 700 km ($e = 0$) :

$a = 7078.137$ km ; $n = \sqrt{398\,600.44 / 7078.137^3} = 1.060 \times 10^{-3}$ rad/s ;
$\dot{\Omega}_\odot = 2\pi/(365.25 \times 86\,400) = 1.991 \times 10^{-7}$ rad/s ;
$\cos i = -(2 \times 1.991 \times 10^{-7} \times 7078.137^{7/2}) / (3 \times 1.0826 \times 10^{-3} \times 6378.137^2 \times \sqrt{398\,600.44}) = -0.143$ ;
$i = \arccos(-0.143) = 98.2°$.

À 600 km, le même calcul donne 97,8°, et à 500 km, 97,4° — les valeurs du chapitre 7.

---

## V.5 — Fraction d'éclipse (analytique, orbite circulaire)

### Démonstration

Pour une orbite circulaire d'altitude $h$, le satellite est en éclipse lorsque la ligne de visée vers le Soleil est occultée par la Terre (approximation de l'ombre cylindrique, qui néglige la pénombre). Soit $\beta$ l'angle entre le vecteur Soleil et le plan de l'orbite. Vue depuis l'orbite, la Terre sous-tend un demi-angle $\beta^* = \arcsin\!\big(R_E/(R_E+h)\big)$ ; pour $|\beta| \ge \beta^*$, l'orbite ne traverse jamais l'ombre.

Pour $|\beta| < \beta^*$, projetons la géométrie sur le plan de l'orbite. Le cylindre d'ombre de rayon $R_E$ coupe le plan de l'orbite selon une ellipse dont le demi-petit axe (perpendiculaire à la direction du Soleil) vaut $R_E$ et dont le demi-grand axe (le long de la direction du Soleil) vaut $R_E/\cos\beta$. Le satellite, au rayon $R_E + h$, est dans l'ombre sur l'arc d'angle orbital $2\phi$ pour lequel sa distance perpendiculaire à la direction du Soleil est inférieure à $R_E$ et sa position le long de cette direction se trouve du côté opposé au Soleil ; la résolution de l'intersection avec l'ellipse donne

$$ \cos\phi = \frac{\sqrt{h^2 + 2 R_E h}}{(R_E + h)\cos\beta} $$

et donc la fraction d'éclipse de la période orbitale (Wertz, *Mission Geometry*, éq. 5-24) :

$$ f_{ecl} = \frac{1}{\pi}\, \arccos\!\left(\frac{\sqrt{h^2 + 2 R_E h}}{(R_E + h) \cos\beta}\right), \qquad |\beta| < \beta^* $$

avec $f_{ecl} = 0$ pour $|\beta| \ge \beta^*$. C'est la forme donnée au chapitre 7, §7.1.2.

**Corollaire ($\beta = 0$).** Lorsque le Soleil est dans le plan de l'orbite, l'argument devient $\sqrt{h^2 + 2R_E h}/(R_E+h) = \cos\beta^*$, d'où

$$ f_{ecl,max} = \frac{\beta^*}{\pi} = \frac{1}{\pi}\arcsin\!\left(\frac{R_E}{R_E + h}\right) $$

— le cas d'éclipse maximale utilisé pour le dimensionnement de la puissance et de la thermique (le chapitre 7 le présente comme corollaire ; le chapitre 9, §9.2–§9.3, l'utilise). La durée de l'éclipse vaut $t_{ecl} = f_{ecl}\,T$.

### Vérification

L'enveloppe annuelle de $\beta$ et les courbes de fraction d'éclipse pour une orbite de type ISS et une orbite héliosynchrone à 600 km sont tracées à la figure 7.2 du chapitre 7 : toutes deux présentent le plateau caractéristique aux faibles $|\beta|$ et la transition brutale à $\beta^*$.

**Contrôle de vraisemblance détaillé.** Orbite de type ISS, $h = 400$ km, $\beta = 0$ :

$\beta^* = \arcsin(6378.137 / 6778.137) = \arcsin(0.9410) = 70.2°$ ;
$h^2 + 2 R_E h = 160\,000 + 5\,102\,510 = 5\,262\,510$ km² ; $\sqrt{\,\cdot\,} = 2294.0$ km ;
argument $= 2294.0 / 6778.137 = 0.3384$ ; $\arccos(0.3384) = 70.2° = 1.2256$ rad ;
$f_{ecl} = 1.2256/\pi = 0.390 \approx 39\,\%$.

Ce résultat concorde avec le corollaire ($\beta^*/\pi = 70.2°/180° = 0.390$) et avec la fraction d'éclipse maximale observée pour l'ISS, d'environ 39 % (≈ 36 min sur une orbite de 92,6 min). À 500 km, le même calcul donne $f_{ecl,max} = 0.378$, $t_{ecl} = 35.8$ min — les valeurs d'EOSat-3U du chapitre 7, §7.2, et du chapitre 9.

---

## V.6 — Affaiblissement en espace libre

### Démonstration

Un radiateur isotrope de puissance $P_t$ produit à la distance $d$ une densité de flux $P_t / (4\pi d^2)$. Une antenne de réception de surface effective $A_e$ capte $A_e$ fois ce flux, et la théorie des antennes relie la surface au gain par $A_e = G_r \lambda^2 / (4\pi)$. Avec une antenne d'émission directive de gain $G_t$, la puissance reçue est donnée par l'équation de transmission de Friis :

$$ P_r = P_t\, G_t\, G_r \left(\frac{\lambda}{4 \pi d}\right)^2 $$

L'affaiblissement en espace libre est l'inverse du terme géométrique, exprimé en décibels :

$$ \text{FSPL} = 20 \log_{10}\!\left(\frac{4 \pi d}{\lambda}\right) = 20 \log_{10}\!\left(\frac{4 \pi d f}{c}\right)\ \text{dB} $$

Aucune énergie n'est absorbée : le terme en $d^2$ traduit l'étalement sphérique, et le terme en $\lambda^2$ la diminution de la surface de captation d'une antenne à gain fixe lorsque la fréquence augmente. Chaque doublement de $d$ ou de $f$ ajoute 6,02 dB. Le chapitre 11, §11.4, et la figure 11.3 tracent l'affaiblissement par bande en fonction de la distance oblique.

### Vérification

**Contrôle de vraisemblance détaillé.** Bande S (2,2 GHz) à une distance oblique de 1500 km :

$\lambda = c/f = 2.998 \times 10^8 / 2.2 \times 10^9 = 0.1363$ m ;
$\text{FSPL} = 20\log_{10}(4\pi \times 1.5 \times 10^6 / 0.1363) = 20\log_{10}(1.383 \times 10^8) = 162.8$ dB.

Pour le cas d'EOSat-3U du chapitre 11, §11.8 (2,25 GHz, distance oblique de 1695 km à 10° d'élévation), la même formule donne 164,1 dB, qui est la barre d'affaiblissement en espace libre de la cascade du bilan de liaison de la figure 11.5 du chapitre 11.

---

## V.7 — Algèbre du bilan de liaison

### Démonstration

Écrivons l'équation de Friis du V.6 en décibels et regroupons les termes d'émission dans la puissance isotrope rayonnée équivalente, $\text{PIRE} = P_{TX} + G_{TX} - L_{TX}$ (dBW). En ajoutant les pertes que l'espace libre n'inclut pas — absorption atmosphérique $L_{atm}$, dépointage de l'antenne $L_{point}$, désadaptation de polarisation $L_{pol}$ et perte de l'alimentation et de la ligne côté réception $L_{rx}$ entre l'antenne et le point auquel le bruit du système est rapporté —, la puissance de porteuse reçue vaut

$$ C = \text{PIRE} - \text{FSPL} - L_{atm} - L_{point} - L_{pol} - L_{rx} + G_{RX} \quad \text{(dBW)} $$

La densité spectrale de puissance de bruit au même point de référence vaut $N_0 = k_B T_{sys}$ (W/Hz), soit en décibels $N_0 = k + 10\log_{10} T_{sys}$ avec $k = 10\log_{10}(1.380\,649 \times 10^{-23}) = -228.6$ dBW/K/Hz. En soustrayant, et en regroupant le gain de réception et la température de bruit dans le facteur de qualité $G/T = G_{RX} - 10\log_{10} T_{sys}$ (dB/K), on obtient la forme canonique du chapitre 11, §11.2 :

$$ \frac{C}{N_0} = \text{PIRE} - \text{FSPL} - L_{atm} - L_{point} - L_{pol} - L_{rx} + G/T - k \quad \text{(dBHz)} $$

(Attention au signe : soustraire un $k$ négatif revient à ajouter 228,6 dB.) L'énergie par bit s'obtient en divisant par le débit binaire, $E_b/N_0 = C/N_0 - 10\log_{10} R_b$, et le $E_b/N_0$ requis dépend de la modulation et du codage (V.8, figure 11.4). La marge de liaison vaut

$$ \text{Marge} = (E_b/N_0)_{available} - (E_b/N_0)_{required} - L_{impl} $$

où $L_{impl}$ est la perte d'implémentation du modem. L'ECSS-E-ST-50-05C demande au moins 3 dB à partir de la phase B ; une cible de 6 dB est courante en phase A, tant que la conception reste mouvante.

### Vérification

La cascade en bande S de la figure 11.5 du chapitre 11 (émetteur de 2 W, antenne patch de 6 dBi, 2,25 GHz sur 1695 km, parabole sol de 3 m à 150 K) se lit de gauche à droite exactement comme l'équation ci-dessus : les gains s'ajoutent, les pertes se retranchent, et le $C/N_0$ reçu final s'établit à 83,4 dBHz pour 73,0 dBHz requis à 5 Mbit/s, ce qui laisse une marge de 10,4 dB. Le bilan d'EOSat-3U du chapitre 11, §11.8.1, est le même calcul ligne par ligne (PIRE de 7,5 dBW, affaiblissement en espace libre de 164,1 dB, $C/N_0 = 83.4$ dBHz, marge de 10,4 dB à 5 Mbit/s).

---

## V.8 — $E_b/N_0$ en fonction du TEB

### Démonstration

Pour la BPSK cohérente sur un canal à bruit blanc additif gaussien, la probabilité d'erreur binaire vaut

$$ P_b = \frac{1}{2}\,\mathrm{erfc}\!\left(\sqrt{\frac{E_b}{N_0}}\right) $$

Pour la QPSK avec codage de Gray, la même expression s'applique bit par bit. Pour la 8-PSK :

$$ P_b \approx \frac{2}{3}\, Q\!\left(\sqrt{2 \tfrac{E_b}{N_0}}\, \sin\!\frac{\pi}{8}\right) $$

Pour la FSK non cohérente :

$$ P_b = \frac{1}{2}\,e^{-E_b/(2 N_0)} $$

Le chapitre 11, §11.6, et la figure 11.4 tracent ces courbes avec une courbe codée représentative d'un code concaténé (convolutif + Reed–Solomon), dont le décalage horizontal par rapport à la courbe non codée à un TEB donné est le gain de codage — environ 5 dB à un TEB de $10^{-5}$ pour ce schéma, davantage pour les codes LDPC.

### Vérification

**Contrôle de vraisemblance.** BPSK à $E_b/N_0 = 9.6$ dB :

$P_b = 0.5 \times \mathrm{erfc}(\sqrt{10^{0.96}}) = 0.5 \times \mathrm{erfc}(3.02) = 0.5 \times 1.9 \times 10^{-5} \approx 9.5 \times 10^{-6}$.

La valeur classique des manuels est $10^{-5}$ à 9,6 dB ; le faible écart tient à la résolution de la grille du graphique.

---

## V.9 — Géométrie de la distance d'échantillonnage au sol

### Démonstration (limite de diffraction)

Pour une ouverture circulaire non obstruée de diamètre $D$, le premier minimum de la figure d'Airy se situe au demi-angle

$$ \theta_{Airy} = 1.22\, \frac{\lambda}{D} $$

Projeté au sol à la distance $h$ (visée au nadir depuis l'altitude $h$) :

$$ \text{GSD}_{diff} = \theta_{Airy}\, h = 1.22\, \frac{\lambda\, h}{D} $$

### Démonstration (limite pixel)

Un pixel de détecteur de pas $p$ dans le plan focal sous-tend un angle $p/f$, où $f$ est la distance focale. Projeté à la distance $h$ :

$$ \text{GSD}_{pix} = \frac{p\, h}{f} $$

La GSD atteignable est la *plus grande* des deux — le système ne peut pas résoudre mieux que ne le permet l'optique, ni mieux que n'échantillonne le détecteur. Accorder les deux (de sorte que $p/f \approx 1.22\lambda/D$, c.-à-d. un nombre d'ouverture d'environ $p/(1.22\lambda)$) est la condition de conception contre laquelle met en garde la fiche du responsable charge utile de la partie IV. Hors nadir, remplacez $h$ par la distance oblique.

### Vérification

La figure D.3 trace les deux limites en fonction du diamètre d'ouverture.

![GSD en fonction du diamètre d'ouverture — limites de diffraction et pixel.](../assets/figures/fig_gsd.png)

**Figure D.3** — Distance d'échantillonnage au sol en fonction du diamètre d'ouverture pour des imageurs dans le visible ($\lambda = 550$ nm) à quatre altitudes, avec la limite de diffraction en traits pleins et la limite pixel à 500 km (pas de 6 µm, $f/D = 5$) en tirets. Héritage Sentinel-2 à 786 km : la limite de diffraction pour une ouverture de 0,135 m vaut ≈ 3,9 m, ce qui est cohérent avec les bandes publiées à 10 m une fois pris en compte le pas du détecteur et le nombre d'ouverture.

**Contrôle de vraisemblance détaillé.** Un imageur de CubeSat 3U avec $D = 90$ mm à $h = 500$ km : $\text{GSD}_{diff} = 1.22 \times 550 \times 10^{-9} \times 5 \times 10^5 / 0.09 = 3.7$ m ; avec $p = 5.5$ µm et $f = 500$ mm, $\text{GSD}_{pix} = 5.5 \times 10^{-6} \times 5 \times 10^5 / 0.5 = 5.5$ m — limité par le pixel, la GSD atteignable est donc de 5,5 m.

---

## V.10 — Équilibre thermique radiatif

### Démonstration

Bilan énergétique d'une plaque plane en régime établi :

Puissance absorbée = puissance émise.
Puissance absorbée = $\alpha_s\, S_{eff} + \varepsilon\, \phi_{IR}$ (apport solaire au flux effectif moyen sur l'orbite $S_{eff}$, plus la contribution de l'infrarouge terrestre, absorbée à l'émittance IR en vertu de la loi de Kirchhoff).
Puissance émise = $\varepsilon\, \sigma\, T^4$ par unité de surface rayonnante.

En résolvant pour la température d'équilibre :

$$ T_{eq} = \left(\frac{\alpha_s\, S_{eff} + \varepsilon\, \phi_{IR}}{\sigma\, \varepsilon}\right)^{1/4} $$

Le rapport $\alpha_s/\varepsilon$ est le principal levier de conception. Le chapitre 9, §9.4, donne le bilan complet avec le terme d'albédo, les facteurs de forme et la dissipation interne, et la figure 9.6 trace $T_{eq}$ en fonction de $\alpha_s/\varepsilon$ en indiquant les revêtements courants.

### Vérification

**Contrôle de vraisemblance détaillé.** Un radiateur peint en blanc, $\alpha_s = 0.15$, $\varepsilon = 0.92$ ($\alpha_s/\varepsilon = 0.163$), rayonnant sur une face, en moyenne sur l'orbite à $\beta = 0$ :

solaire : $S_{eff} \approx 1361/4 = 340$ W/m², absorbé $0.15 \times 340 = 51$ W/m² ;
IR terrestre : $\phi_{IR} \approx 230/2 = 115$ W/m² vus par une plaque orientée vers le nadir en LEO, absorbé $0.92 \times 115 = 106$ W/m² ;
total absorbé = 157 W/m² ;
$T_{eq} = (157 / (0.92 \times 5.670 \times 10^{-8}))^{1/4} = (3.01 \times 10^9)^{1/4} = 234$ K $= -39$ °C.

Ce résultat correspond à la figure 9.6 pour $\alpha_s/\varepsilon \approx 0.16$. Le même bilan avec $\alpha_s/\varepsilon \approx 5$ (aluminium poli nu) donne environ +120 °C — raison pour laquelle on ne laisse jamais un métal nu face au Soleil.

---

## V.11 — Dimensionnement du générateur solaire

### Démonstration

Considérons une orbite de période $T = t_{sun} + t_{ecl}$. Le générateur ne produit que pendant l'arc éclairé $t_{sun}$ ; les charges fonctionnent en permanence. Soit $P_{sun}$ la demande maximale du mode éclairé et $P_{ecl}$ la demande en éclipse. L'énergie fournie aux charges sur l'orbite doit être apportée par le générateur, selon deux chemins de rendements différents : le chemin direct générateur–charge en phase éclairée ($\eta_{sun}$, le régulateur seul) et le chemin générateur–batterie–charge pour l'énergie d'éclipse ($\eta_{ecl} = \eta_{charge}\,\eta_{discharge}\,\eta_{regulator}$). Le bilan énergétique sur une orbite s'écrit donc

$$ P_{SA,EOL}\, t_{sun} = \frac{P_{sun}\, t_{sun}}{\eta_{sun}} + \frac{P_{ecl}\, t_{ecl}}{\eta_{ecl}} $$

et, en divisant par $t_{sun}$,

$$ P_{SA,EOL} = \frac{\dfrac{P_{sun}\, t_{sun}}{\eta_{sun}} + \dfrac{P_{ecl}\, t_{ecl}}{\eta_{ecl}}}{t_{sun}} $$

— la puissance de générateur requise en fin de vie (chapitre 9, §9.2, étape 2). Le générateur doit fournir cette puissance en fin de vie ; la puissance nominale en début de vie est donc plus élevée, du facteur de dégradation radiative $L_d = (1-\delta)^n$ et du déclassement en température $L_T = 1 + \beta_T (T_{cell} - T_{ref})$ (le coefficient de température des cellules est noté $\beta_T$ pour éviter toute confusion avec l'angle $\beta$ de l'orbite) :

$$ P_{SA,BOL} = \frac{P_{SA,EOL}}{L_d\, L_T} $$

Enfin, les cellules convertissent le flux solaire $S$ avec un rendement $\eta_{cell}$, réduit par le cosinus de l'angle d'incidence solaire $\theta$ sur le générateur, le taux de remplissage $f_{pack}$ et la transmission du verre de protection $f_{cover}$ :

$$ A_{SA} = \frac{P_{SA,BOL}}{\eta_{cell}\, S\, \cos\theta\, f_{pack}\, f_{cover}} $$

Ici, $\theta$ est l'angle entre la normale au générateur et le vecteur Soleil — nul pour un générateur orientable suivant le Soleil ; pour un panneau fixé sur la structure d'un satellite pointé au nadir, il est fixé par l'angle $\beta$ de l'orbite (un panneau dont la normale est perpendiculaire au plan de l'orbite voit en permanence $\theta = 90° - |\beta|$ ; un panneau zénith voit $\cos\theta = \cos\beta\cos\nu$ varier au long de l'arc éclairé, et l'on utilise donc sa moyenne sur cet arc). Le chapitre 9, §9.2, énonce la même chaîne et traite les valeurs d'EOSat-3U.

### Équivalence avec la formulation en fraction d'éclipse

De nombreuses références écrivent le dimensionnement en fonction de la fraction d'éclipse $f_{ecl} = t_{ecl}/T$ et de la fraction éclairée $f_{sun} = t_{sun}/T$, avec une charge moyenne unique sur l'orbite $P_{avg}$ et un facteur de dégradation unique. Posons $P_{sun} = P_{ecl} = P_{avg}$, intégrons le rendement du chemin éclairé dans la charge ($\eta_{sun} \to 1$), écrivons $\eta_{ecl} \to \eta_{dis}$, et divisons le numérateur et le dénominateur de la première équation par $T$ :

$$ P_{SA} = P_{avg}\left(1 + \frac{f_{ecl}}{f_{sun}\, \eta_{dis}}\right) $$

et, avec $L_d L_T \to (1 - D_{deg})$ et $f_{pack} f_{cover}$ intégrés dans $\eta_{cell}$,

$$ A_{SA} = \frac{P_{avg}\left(1 + \dfrac{f_{ecl}}{f_{sun}\,\eta_{dis}}\right)}{S\, \eta_{cell}\, \cos\theta\, (1 - D_{deg})} $$

Les deux formulations expriment le même bilan énergétique. La forme du chapitre 9 est préférée, car elle distingue le mode éclairé de pointe du mode éclipse (le générateur doit couvrir le mode éclairé le plus défavorable, et non la moyenne) et parce qu'elle conserve séparés les rendements des deux chemins.

### Vérification

L'abaque de dimensionnement de la figure 9.3 du chapitre 9 est tracé dans la formulation en fraction d'éclipse ($\eta_{cell} = 30$ %, dégradation EOL de 10 %, $\theta = 20°$, $\eta_{dis} = 85$ %) : un 6U avec une charge moyenne sur l'orbite de 15 W a besoin d'environ 870 cm² en fin de vie.

**Contrôle détaillé.** $P_{sun} = P_{ecl} = 15$ W, $t_{ecl}/t_{sun} = 0.35/0.65 = 0.538$, $\eta_{sun} = 1$, $\eta_{ecl} = 0.85$ :

$P_{SA} = 15 + 15 \times 0.538 / 0.85 = 15 + 9.5 = 24.5$ W pendant l'arc éclairé ;
$A_{SA} = 24.5 / (1361 \times 0.30 \times \cos 20° \times 0.90) = 24.5 / 345.0 = 0.071$ m² $= 710$ cm².

L'abaque indique environ 870 cm², car il est tracé pour une production moyennée sur l'orbite plutôt que sur l'arc éclairé, convention plus prudente ; les deux concordent à ce choix de modélisation près. Le cas d'EOSat-3U du chapitre 9, §9.2 — $P_{sun} = 10$ W, $P_{ecl} = 3.5$ W, $t_{sun} = 58.8$ min, $t_{ecl} = 35.8$ min, $\eta_{sun} = 0.90$, $\eta_{ecl} = 0.786$ — donne $P_{SA,EOL} = 13.8$ W, $P_{SA,BOL} = 16.0$ W et $A_{SA} = 0.0526$ m².

---

## V.12 — Dimensionnement de la batterie

### Démonstration

L'énergie prélevée sur la batterie pendant une éclipse vaut $E_{ecl} = P_{ecl}\, t_{ecl}$. La batterie doit la fournir par le chemin de décharge (rendement $\eta_{dis}$) en n'utilisant que la fraction DoD de sa capacité nominale, de façon à atteindre la durée de vie en cycles requise :

$$ E_{bat} = \frac{P_{ecl}\, t_{ecl}}{\text{DoD}\, \eta_{dis}} $$

— la forme du chapitre 9, §9.3. La capacité nominale en ampères-heures vaut $C = E_{bat} / V_{bus}$, et la masse découle de l'énergie massique de la chimie. Le nombre de cycles est le nombre d'éclipses sur la mission (≈ 15 par jour en LEO, soit environ 5500 par an) qui, par les courbes de durée de vie en cycles en fonction de la DoD de la figure 9.4 du chapitre 9, fixe la DoD admissible.

### Vérification

**Contrôle détaillé.** EOSat-3U, $P_{ecl} = 3.5$ W, $t_{ecl} = 35.8$ min $= 0.597$ h, DoD $= 25$ %, $\eta_{dis} = 0.95$ :

$E_{bat} = 3.5 \times 0.597 / (0.25 \times 0.95) = 2.09 / 0.2375 = 8.8$ Wh,

comme au chapitre 9, §9.3, où le besoin est arrondi par excès avec une marge et où une batterie de 20 Wh est retenue. Une mission de trois ans à 15 éclipses par jour représente environ 16 000 cycles ; la figure 9.4 montre que les éléments NCA/NMC y parviennent à 25–30 % de DoD avec marge, alors que les éléments LCO éprouvés exigent une DoD plus faible.

---

## V.13 — Marge de sécurité (structures)

La marge de sécurité structurale compare la contrainte admissible à la contrainte appliquée multipliée par le coefficient de sécurité :

$$ \text{MoS} = \frac{\sigma_{allow}}{\text{FoS} \cdot \sigma_{applied}} - 1 $$

Une marge positive est conforme ; une marge nulle se situe exactement à la contrainte admissible, coefficient appliqué ; une marge négative constitue un non-respect de l'exigence. Le chapitre 12, §12.1.6, en donne le traitement de référence (le chapitre 3, §3.3.3, et le chapitre 14 y renvoient) ainsi que les coefficients de l'ECSS-E-ST-32-10C.

**Contrôle détaillé.** Al 7075-T6, contrainte admissible à la limite élastique $\sigma_{yield} = 503$ MPa, coefficient de sécurité à la limite élastique de 1,25, contrainte appliquée de 200 MPa :

$\text{MoS} = 503 / (1.25 \times 200) - 1 = 1.012$,

soit une marge positive de 100 %. Conforme. (Pour la poutre-caisson du 3U du chapitre 12, §12.1, la première fréquence propre, $f_1 \approx 330$ Hz, est vérifiée séparément par rapport à l'exigence de 100 Hz.)

---

## V.14 — Ordre de grandeur des couples perturbateurs

### Démonstration (traînée aérodynamique)

La force de traînée sur une surface exposée $A_{ref}$ vaut $\tfrac{1}{2}\rho V^2 C_D A_{ref}$ ; elle s'applique au centre de poussée, décalé du centre de masse d'un bras de levier $\ell$, ce qui donne le couple

$$ T_{drag} = \tfrac{1}{2}\,\rho\, V^2\, C_D\, A_{ref}\, \ell $$

où $\rho$ est la masse volumique atmosphérique, $V$ la vitesse orbitale et $C_D \approx 2.2$. Le chapitre 10, §10.2, donne les expressions correspondantes pour les couples de gradient de gravité, magnétique et de pression solaire, ainsi que les valeurs d'EOSat-3U.

**Estimation détaillée.** Un CubeSat 6U à 500 km, $\rho \approx 6 \times 10^{-13}$ kg/m³ (activité solaire moyenne), $V = 7.61$ km/s, $A_{ref} = 0.06$ m², $C_D = 2.2$, $\ell = 0.02$ m :

$T_{drag} \approx 0.5 \times 6 \times 10^{-13} \times 7610^2 \times 2.2 \times 0.06 \times 0.02 \approx 4.6 \times 10^{-8}$ N m.

Avec un bras de levier de 10 cm (un panneau déployé loin du centre de masse), la valeur est cinq fois plus grande ; au cours du cycle solaire, $\rho$ à 500 km varie de plus d'un ordre de grandeur dans un sens comme dans l'autre, ce qui explique que la figure 10.4 du chapitre 10 montre une bande plutôt qu'une ligne.

### Vérification

La figure 10.4 du chapitre 10 montre le moment cinétique accumulé dans les roues en fonction du nombre d'orbites depuis la dernière désaturation, ainsi que l'ordre de grandeur des couples perturbateurs par source, pour un satellite de quelques dizaines de kilogrammes ; les valeurs d'EOSat-3U du chapitre 10, §10.2, en représentent environ un dixième, et pour un 3U à 500 km, c'est le couple magnétique, et non la traînée, qui domine. La capacité de moment cinétique des roues de réaction s'en déduit, $H \ge T_{dist}\, t_{desat}\, k_{margin}$ (chapitre 10, §10.3 et §10.5).

---

## V.15 — Bouclage du bilan de volume de données quotidien

Le contrôle de bouclage entre la production de données (charge utile) et la capacité de liaison descendante (communications) est un point de défaillance classique de la conception de mission. La charge utile produit $V_{gen} = R_{gen}\, t_{imaging}$ par jour ; le segment sol peut recevoir, avec $N_{passes}$ passages utilisables par jour de durée utilisable moyenne $t_{contact}$, au débit $R$ et avec l'efficacité protocolaire $\eta_{protocol}$ (acquittements, tramage, retransmissions) :

$$ C_{downlink} = R \cdot N_{passes} \cdot t_{contact} \cdot \eta_{protocol} $$

et la mission se boucle si

$$ V_{gen} \le C_{downlink} $$

C'est la forme du chapitre 11, §11.9. Si l'inégalité n'est pas satisfaite, les options sont une liaison descendante plus rapide (plus de bande passante ou une bande plus élevée), davantage de stations ou de passages, la compression à bord, ou moins d'images. La figure 11.6 du chapitre 11 trace la capacité quotidienne par bande en regard de volumes représentatifs de charges utiles : l'UHF ne se boucle que pour la télémesure de servitude ; la bande S convient à un imageur multispectral ; la bande X est nécessaire pour les données SAR ou hyperspectrales.

**Contrôle détaillé.** EOSat-3U à 5 Mbit/s avec cinq passages de 6 minutes par jour et $\eta_{protocol} = 0.85$ : $C = 5 \times 10^6 \times 5 \times 360 \times 0.85 / 8 = 956$ Mo/jour pour 720 Mo/jour produits — le bilan se boucle (cas du chapitre 11, §11.9, et du chapitre 17, §17.2.4). UniSat-1 à 4800 bit/s, avec cinq minutes de contact utilisable par passage vers une seule station : 0,61 Mo/jour pour 1,13 Mo/jour produits — le bilan ne se boucle pas (chapitre 11, §11.8.2 ; chapitre 17, §17.6).

---

## V.16 — Matrice de vérification croisée

Pour une revue de conception, toute affirmation quantitative devrait être vérifiée par au moins deux méthodes. La matrice suivante indique les deux méthodes attendues pour chaque grandeur démontrée dans cette partie.

| Grandeur | Méthode 1 | Méthode 2 | Démonstration |
|----------|---------|---------|--------|
| Période orbitale | Kepler (analytique) | Propagation numérique (GMAT ou équivalent) | V.2 |
| Inclinaison SSO | Condition analytique du $J_2$ | Valeurs tabulées (SMAD4, tableau 9-2) | V.4 |
| Fraction d'éclipse | Formulation analytique en β | Modèle numérique d'éclipse | V.5 |
| Affaiblissement en espace libre | $20\log_{10}(4\pi d/\lambda)$ | UIT-R P.525 | V.6 |
| Bilan de liaison | Tableur, ligne par ligne | Outil de conception concourante ou calculateur de liaison d'un fournisseur | V.7 |
| GSD (diffraction) | $1.22\,\lambda h/D$ | Tracé de rayons optique détaillé | V.9 |
| GSD (pixel) | $p\,h/f$ | Fiche technique du détecteur | V.9 |
| Équilibre thermique | Analyse en $\alpha_s/\varepsilon$ | Modèle de réseau thermique (ESATAN ou équivalent) | V.10 |
| Surface du générateur solaire | Bilan énergétique sur l'orbite | Outil de dimensionnement d'un fournisseur | V.11 |
| Capacité de la batterie | DoD et courbe de durée de vie en cycles | Données d'essais de cyclage du fournisseur | V.12 |
| Marge de sécurité | Calcul manuel | Analyse par éléments finis | V.13 |
| Couple perturbateur | Estimation à partir des premiers principes | Modèle atmosphérique (NRLMSISE-00) avec la géométrie | V.14 |
| Bilan de données | $R\,N_{passes}\,t_{contact}\,\eta$ | Simulation passage par passage avec le planning des stations | V.15 |

---

## V.17 — Références clés

- **Vallado**, *Fundamentals of Astrodynamics and Applications*, 4e éd., Microcosm Press / Springer.
- **Curtis**, *Orbital Mechanics for Engineering Students*, 3e éd., Butterworth-Heinemann.
- **Wertz**, *Mission Geometry : Orbit and Constellation Design and Management*, Microcosm Press.
- **Wertz, Everett et Puschell**, *Space Mission Engineering : The New SMAD*, 2011.
- **Larson et Wertz**, *Space Mission Analysis and Design*, 4e éd.
- **Pratt, Bostian et Allnutt**, *Satellite Communications*, 3e éd.
- **Sutton et Biblarz**, *Rocket Propulsion Elements*, 9e éd.
- **Gilmore**, *Spacecraft Thermal Control Handbook*, vol. I et II.
- **Sarafin**, *Spacecraft Structures and Mechanisms*.
- **Markley et Crassidis**, *Fundamentals of Spacecraft Attitude Determination and Control*.
- **Patel**, *Spacecraft Power Systems*.
- **Kopp et Lean**, « A new, lower value of total solar irradiance », *Geophysical Research Letters* 38, 2011.
- **NASA SEH (SP-2016-6105 Rev 2)** — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).
- **IERS Conventions 2010** — [https://www.iers.org/IERS/EN/Publications/TechnicalNotes/tn36.html](https://www.iers.org/IERS/EN/Publications/TechnicalNotes/tn36.html).
- **Constantes fondamentales CODATA 2018** — [https://physics.nist.gov/cuu/Constants/](https://physics.nist.gov/cuu/Constants/).
- **UIT-R P.525** (affaiblissement en espace libre) — [https://www.itu.int/rec/R-REC-P.525/en](https://www.itu.int/rec/R-REC-P.525/en).
- **Modèle atmosphérique NRLMSISE-00** — [https://ccmc.gsfc.nasa.gov/models/NRLMSIS~00/](https://ccmc.gsfc.nasa.gov/models/NRLMSIS~00/).
- **NASA GMAT** — [https://software.nasa.gov/software/GSC-17177-1](https://software.nasa.gov/software/GSC-17177-1).
