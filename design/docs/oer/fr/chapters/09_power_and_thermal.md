# Partie II — Conception des sous-systèmes

# Chapitre 9 — Alimentation électrique et contrôle thermique

> **Lectures préalables conseillées.** SMAD4 chap. 11.4 (puissance) et 11.5 (thermique) ; ECSS-E-ST-20C §5 (électrique) ; ECSS-E-ST-31C (contrôle thermique) ; Patel, *Spacecraft Power Systems*, chap. 3–4 ; Gilmore, *Spacecraft Thermal Control Handbook*, vol. 1, chap. 1–4. Ce chapitre utilise l'orbite du chapitre 7 (période, fraction d'éclipse) et le bilan de puissance par mode du chapitre 8, §8.4.3 ; les équations de dimensionnement sont démontrées à partir des premiers principes dans la partie V (§V.10–§V.12).

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez en mesure de :

1. dimensionner un générateur solaire à partir de la demande de puissance de la mission, du profil d'éclipse et de la dégradation ;
2. dimensionner une batterie à partir de la demande d'énergie en éclipse, de la profondeur de décharge et des exigences de durée de vie en cycles ;
3. calculer la puissance moyenne sur l'orbite par une analyse des rapports cycliques ;
4. expliquer l'architecture de l'EPS (DET ou PPT, MPPT, régulation du bus) et exposer la physique de chaque solution ;
5. effectuer une analyse de bilan thermique de premier ordre (cas chaud et cas froid) avec la démonstration radiative complète ;
6. choisir les moyens de contrôle thermique et appliquer les marges thermiques de l'ECSS ;
7. expliquer la constitution d'un MLI, le fonctionnement d'un caloduc et le dimensionnement des réchauffeurs ;
8. vérifier le bouclage d'une conception électrique et thermique dans chaque mode opérationnel.

---

## 9.1 Architecture du sous-système d'alimentation électrique

*[Source : SMAD, chap. 11.4 ; ECSS-E-ST-20C ; Patel, chap. 3]*

L'EPS est le « fournisseur d'électricité » du satellite. Il doit alimenter en continu tous les sous-systèmes en puissance régulée, dans tous les modes opérationnels, y compris pendant l'éclipse. Contrairement aux réseaux électriques terrestres, l'EPS d'un engin spatial ne peut puiser dans aucun réseau — le générateur solaire, la batterie et l'électronique de conditionnement de puissance doivent former un système énergétique entièrement autonome, sans aucune maintenance pendant toute la durée de la mission. La figure 9.1 présente l'architecture de référence.

<svg viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg" style="max-width:700px; font-family: sans-serif; font-size: 11px;">
  <!-- Solar Array -->
  <rect x="30" y="100" width="120" height="60" rx="4" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="90" y="125" text-anchor="middle" fill="#92400e" font-weight="bold">Générateur solaire</text>
  <text x="90" y="142" text-anchor="middle" fill="#92400e" font-size="10">GaAs 29,5 %</text>
  <text x="90" y="155" text-anchor="middle" fill="#92400e" font-size="9">1361 W/m²</text>
  <!-- MPPT -->
  <rect x="200" y="100" width="100" height="60" rx="4" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
  <text x="250" y="125" text-anchor="middle" fill="#3730a3" font-weight="bold">MPPT</text>
  <text x="250" y="142" text-anchor="middle" fill="#3730a3" font-size="10">Régulateur</text>
  <line x1="150" y1="130" x2="200" y2="130" stroke="#64748b" stroke-width="2" marker-end="url(#arr9)"/>
  <!-- Bus -->
  <line x1="300" y1="130" x2="480" y2="130" stroke="#dc2626" stroke-width="3"/>
  <text x="390" y="120" text-anchor="middle" fill="#dc2626" font-weight="bold">Bus régulé (3,3 V / 5 V / batt.)</text>
  <!-- Battery -->
  <rect x="330" y="200" width="120" height="55" rx="4" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="390" y="222" text-anchor="middle" fill="#166534" font-weight="bold">Batterie</text>
  <text x="390" y="239" text-anchor="middle" fill="#166534" font-size="10">Li-ion, DoD 30 %</text>
  <line x1="390" y1="200" x2="390" y2="133" stroke="#16a34a" stroke-width="2"/>
  <text x="408" y="175" fill="#16a34a" font-size="9">charge/décharge</text>
  <!-- Loads -->
  <rect x="520" y="40" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="62" text-anchor="middle" fill="#1e40af" font-size="10">Charge utile (C)</text>
  <rect x="520" y="85" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="107" text-anchor="middle" fill="#1e40af" font-size="10">SCAO (C)</text>
  <rect x="520" y="130" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="152" text-anchor="middle" fill="#1e40af" font-size="10">Émetteur (C)</text>
  <rect x="520" y="175" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="197" text-anchor="middle" fill="#1e40af" font-size="10">OBC (permanent)</text>
  <rect x="520" y="220" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="242" text-anchor="middle" fill="#1e40af" font-size="10">Réchauffeurs (thermo.)</text>
  <!-- Switch lines -->
  <line x1="480" y1="57" x2="520" y2="57" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="102" x2="520" y2="102" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="147" x2="520" y2="147" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="192" x2="520" y2="192" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="237" x2="520" y2="237" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="57" x2="480" y2="237" stroke="#64748b" stroke-width="1.5"/>
  <text x="490" y="30" fill="#64748b" font-size="10">Lignes commutées</text>
  <text x="490" y="42" fill="#64748b" font-size="9">(C = commutable)</text>
  <defs><marker id="arr9" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/></marker></defs>
</svg>

**Figure 9.1** — EPS de référence d'un CubeSat : générateur solaire, dispositif de recherche du point de puissance maximale, bus régulé, batterie et lignes de charge commutées.

### 9.1.1 Physique de la cellule solaire

Une cellule photovoltaïque convertit l'énergie des photons en énergie électrique par effet photovoltaïque. Lorsqu'un photon d'énergie $E = h\nu \geq E_g$ (où $E_g$ est la largeur de bande interdite du semi-conducteur) frappe la cellule, il fait passer un électron de la bande de valence à la bande de conduction, créant une paire électron-trou. Le champ électrique interne de la jonction p-n entraîne les porteurs vers des bornes opposées, ce qui produit une tension ($V_{oc}$) et un courant ($I_{sc}$).

**Cellules à simple jonction et cellules multijonctions :**

Une cellule à simple jonction (p. ex. en silicium, $E_g = 1.12$ eV) ne peut absorber que les photons tels que $E \geq E_g$. Les photons tels que $E < E_g$ la traversent sans être absorbés ; les photons tels que $E \gg E_g$ perdent leur énergie excédentaire sous forme de chaleur (pertes par thermalisation). Le rendement maximal théorique d'une cellule à simple jonction sous éclairement AM0 (spatial) est d'environ 31 % (limite de Shockley-Queisser).

Les cellules multijonctions (MJ) empilent deux ou trois jonctions p-n de matériaux semi-conducteurs différents, chacune étant accordée pour absorber une partie différente du spectre solaire :

| Technologie de cellule | Structure | Bandes interdites (eV) | Rendement AM0 | Coefficient de température | Héritage en vol |
|----------------|-----------|---------------|----------------|------------------|-----------------|
| **Si monocristallin** | Simple jonction | 1,12 | 16–18 % | −0,45 %/°C | Très étendu (ISS, nombreux satellites LEO) |
| **GaAs simple jonction** | Simple jonction | 1,42 | 22–24 % | −0,21 %/°C | Modéré |
| **InGaP/GaAs double jonction** | 2 jonctions | 1,86 / 1,42 | 26–28 % | −0,20 %/°C | Modéré |
| **InGaP/GaAs/Ge triple jonction** | 3 jonctions (à accord de maille) | 1,86 / 1,42 / 0,67 | 28–30 % | −0,19 %/°C | Très étendu (> 90 % des engins spatiaux modernes) |
| **InGaP/GaAs/InGaAs IMM** | 3 jonctions (métamorphique inversée) | 1,86 / 1,42 / 1,0 | 32–33 % | −0,18 %/°C | En progression |

*[Source : fiches techniques de fabricants de cellules triple jonction ; Green et al., « Solar Cell Efficiency Tables », Progress in Photovoltaics, version 62, 2023. Les produits de fabricants cités dans ce chapitre sont des exemples représentatifs, et non des recommandations.]*

**Pourquoi le GaAs triple jonction domine dans l'espace :** le spectre solaire AM0 (au-dessus de l'atmosphère) est plus riche en photons UV et bleus que le spectre terrestre AM1.5. Les cellules triple jonction captent cette énergie sur trois bandes interdites. La cellule supérieure (InGaP, $E_g = 1.86$ eV) absorbe le bleu et l'UV, la cellule intermédiaire (GaAs, $E_g = 1.42$ eV) le visible, et la cellule inférieure (Ge, $E_g = 0.67$ eV) le proche infrarouge. Chaque jonction apporte sa tension en série, tandis que le courant est limité par la jonction qui débite le moins (contrainte d'égalité des courants).

**Effets de la température :** en orbite, les cellules solaires fonctionnent entre 40 et 80 °C selon leur montage et l'orbite. Le rendement des cellules diminue lorsque la température augmente, en raison de l'accroissement de la concentration intrinsèque de porteurs (qui réduit $V_{oc}$). Le coefficient de température du GaAs triple jonction est d'environ −0,19 %/°C en relatif — autrement dit, une cellule donnée pour 29,5 % à 28 °C tombe à environ 28,5 % à 80 °C. Il faut en tenir compte dans les calculs du bilan de puissance :

$$\eta_{\text{cell}}(T) = \eta_{\text{ref}} \times [1 + \beta_T (T - T_{\text{ref}})]$$

où $\beta_T \approx -0.0019$ /°C pour le GaAs triple jonction et $T_{\text{ref}} = 28$ °C (conditions d'essai normalisées). (L'indice distingue ce coefficient de l'angle bêta de l'orbite du chapitre 7.)

**Mécanismes de dégradation :** en orbite, les cellules solaires se dégradent sous l'effet :

- **des dommages dus aux rayonnements :** les protons et électrons énergétiques (piégés dans les ceintures de Van Allen ou issus des éruptions solaires à particules) déplacent des atomes du réseau cristallin et créent des centres de recombinaison qui réduisent la durée de vie des porteurs minoritaires, donc le courant. La dégradation est exprimée en fluence équivalente d'électrons de 1 MeV. Taux typiques : 2–3 %/an en LEO, 5–8 %/an en MEO (traversée de la ceinture de protons), 1–2 %/an en GEO ;
- **du noircissement sous UV :** le rayonnement ultraviolet noircit progressivement l'adhésif du verre de protection, ce qui réduit la transmission ;
- **de l'érosion par les micrométéoroïdes :** le piquage progressif du verre de protection réduit la transmission optique ;
- **des décharges électrostatiques (ESD) :** en GEO ou en orbite polaire, la charge différentielle peut provoquer des arcs entre cellules et endommager définitivement les interconnexions.

Le verre de protection (généralement en borosilicate dopé au cérium, de 100 à 150 µm d'épaisseur) atténue les effets des rayonnements et des UV. Le facteur de dégradation combiné s'écrit :

$$L_d = (1 - \delta)^n$$

où $\delta = 0.025$ (2,5 %/an pour le GaAs triple jonction en LEO avec un verre de protection standard) et $n$ = durée de la mission en années.

### 9.1.2 Générateurs solaires fixés sur la structure ou déployables

Les **cellules fixées sur la structure** sont collées directement sur les panneaux extérieurs du satellite. C'est la solution la plus simple et la plus fiable (ni mécanisme de déploiement, ni charnières, ni moteurs d'entraînement), mais sa surface est fortement limitée.

| Montage | Avantages | Inconvénients | Puissance typique |
|----------|-----------|---------------|--------------|
| **Fixé sur la structure** | Aucun risque lié à un mécanisme, aucune puissance consommée pour l'orientation, masse faible, coût faible | Surface limitée (surface du satellite seulement), géométrie d'éclairement défavorable pour un satellite pointé au nadir, température des cellules élevée | 1U : ~2 W, 3U : ~7 W, 6U : ~12 W |
| **Déployable fixe** | Surface 2–4× plus grande, meilleur angle solaire, cellules moins chaudes (refroidissement radiatif par la face arrière) | Mécanisme de déploiement (point de défaillance unique), augmentation de la traînée aérodynamique, dynamique structurale | 3U : ~15–25 W, 6U : ~30–48 W |
| **Déployable orientable** | Incidence solaire optimale ($\cos\theta \approx 1$), puissance maximale | Le SADM (mécanisme d'entraînement du générateur solaire) ajoute masse, coût et complexité, et le moteur consomme en permanence | Grands engins spatiaux : 100+ W |

**Exemples de missions réelles :**

- **Planet SuperDove (3U+) :** cellules fixées sur la structure + deux ailes déployables fixes. ~25 W en BOL. Les panneaux déployables, à charnières à ressort, sont repliés contre le corps 3U pendant le lancement et se déploient après l'éjection du distributeur.
- **ASTERIA (6U, JPL) :** deux générateurs déployables, 48 W en BOL, cellules GaAs triple jonction sur des panneaux déployables commerciaux.
- **CubeSats 1U déployés depuis l'ISS :** cellules fixées sur la structure uniquement, 2–3 W. Suffisant pour des missions simples de capteurs à faible rapport cyclique.

### 9.1.3 Types d'architectures

| Architecture | Principe de fonctionnement (physique) | Rendement | Complexité | Usage typique |
|-------------|----------------------|-----------|-----------|------------|
| **DET** (transfert direct d'énergie, *Direct Energy Transfer*) | Le générateur solaire est relié directement au bus ; un régulateur shunt dérive l'excédent de courant vers un banc de résistances (dissipé sous forme de chaleur) lorsque la production du générateur dépasse la charge. Aucun régulateur série entre le générateur et le bus. La tension varie avec l'éclairement. | 80–85 % (pertes shunt) | Faible | Engins spatiaux GEO éprouvés, certains CubeSats |
| **PPT / MPPT** (recherche du point de puissance maximale) | Un convertisseur continu-continu (généralement élévateur ou abaisseur-élévateur) placé entre le générateur et le bus ajuste en permanence son impédance d'entrée pour faire fonctionner le générateur à son point de puissance maximale (MPP). Utilise un algorithme de perturbation et observation ou de conductance incrémentale. Extrait 10–15 % de puissance de plus qu'une architecture DET, surtout aux températures hors nominal et en fin de vie. | 90–95 % | Moyenne | La plupart des CubeSats modernes |
| **Bus non régulé** | La batterie est reliée directement au bus d'alimentation par de simples transistors FET de protection. La tension du bus est égale à celle de la batterie (de 3,0 V à vide à 4,2 V en pleine charge par élément, soit 6,0–8,4 V en configuration 2S). Les sous-systèmes doivent tolérer les variations de tension. | La plus élevée (aucune perte de régulateur) | La plus faible | CubeSats très simples, missions 1U |
| **Bus régulé** | Des convertisseurs continu-continu créent des rails de tension fixes (3,3 V, 5 V, 12 V) à partir de la batterie ou du générateur. Les sous-systèmes voient une tension constante quel que soit l'état de la batterie. Ajoute ~5–10 % de pertes dans les régulateurs, mais simplifie grandement la conception des sous-systèmes. | Bon (85–90 % au global) | Moyenne | La plupart des cartes EPS COTS pour CubeSat |

**Physique du MPPT :** la caractéristique I-V d'une cellule solaire présente un « coude » marqué où la puissance extraite ($P = I \times V$) est maximale. En circuit ouvert ($I = 0$), la tension est maximale mais la puissance est nulle. En court-circuit ($V = 0$), le courant est maximal mais la puissance est nulle. Le MPP se situe à environ 75–80 % de $V_{oc}$ et 90–95 % de $I_{sc}$. La température déplace la caractéristique I-V (une température $T$ plus élevée décale $V_{oc}$ vers la gauche), donc le MPP se déplace. Un contrôleur MPPT suit ce point de façon dynamique, avec une mise à jour typiquement toutes les 0,1 à 1 s. Les convertisseurs MPPT courants pour CubeSat atteignent un rendement de suivi de 95–97 %.

**Régulation de la charge de la batterie :** l'EPS doit empêcher la surcharge (qui provoque un dépôt de lithium métallique, un dégagement gazeux et un emballement thermique dans les éléments Li-ion) et la décharge profonde (qui provoque la dissolution du cuivre du collecteur de courant négatif et endommage définitivement l'élément). Les cartes EPS modernes pour CubeSat mettent en œuvre :

- **la charge CC-CV :** charge à courant constant jusqu'à ce que la tension de l'élément atteigne 4,2 V, puis charge à tension constante avec décroissance du courant jusqu'à ce qu'il passe sous C/20 ;
- **la coupure sur sous-tension :** déconnexion du bus lorsque la tension de l'élément descend sous 3,0 V (ou 2,8 V en urgence) ;
- **l'équilibrage des éléments :** pour les configurations à plusieurs éléments en série (2S ou plus), des circuits d'équilibrage passifs ou actifs maintiennent les éléments à moins de 50 mV les uns des autres ;
- **les seuils de coupure en température :** charge inhibée en dessous de 0 °C et au-dessus de 45 °C (charger un élément Li-ion sous 0 °C provoque un dépôt de lithium métallique).

**Standard CubeSat :** la plupart des cartes EPS commerciales associent MPPT et bus régulé avec des rails de 3,3 V et 5 V, plus un rail batterie non régulé (6,0–8,4 V pour du Li-ion 2S).

---

## 9.2 Dimensionnement du générateur solaire

La chaîne de dimensionnement ci-dessous est la forme de référence utilisée dans tout le manuel ; la partie V, §V.11, la démontre à partir du bilan énergétique sur l'orbite et montre son équivalence avec la forme fondée sur la fraction d'éclipse que l'on trouve dans certains ouvrages.

> **Équations clés — dimensionnement du générateur solaire**
>
> **Étape 1 : demande de puissance moyenne sur l'orbite** (chapitre 8, §8.4.4) :
> $$P_{\text{avg}} = \sum_{\text{modes}} P_{\text{mode}} \times f_{\text{duty,mode}}$$
>
> **Étape 2 : puissance requise du générateur en fin de vie.** Pendant l'arc éclairé ($t_{\text{sun}}$), le générateur doit fournir la charge de la phase éclairée par la chaîne diurne et, dans le même temps, restituer à la batterie l'énergie que la charge en éclipse ($P_{\text{ecl}}$ pendant $t_{\text{ecl}}$) y a puisée, par la chaîne charge-stockage-décharge :
> $$P_{\text{SA,EOL}} = \frac{\dfrac{P_{\text{sun}}\, t_{\text{sun}}}{\eta_{\text{sun}}} + \dfrac{P_{\text{ecl}}\, t_{\text{ecl}}}{\eta_{\text{ecl}}}}{t_{\text{sun}}}$$
> où $P_{\text{sun}}$ est la demande du mode éclairé de pointe (le générateur doit couvrir le mode éclairé le plus défavorable, et non la moyenne), $\eta_{\text{sun}}$ est le rendement de la chaîne générateur-charge en phase éclairée (régulateur seul, ≈ 0,90) et $\eta_{\text{ecl}} = \eta_{\text{charge}} \times \eta_{\text{discharge}} \times \eta_{\text{regulator}}$ est le rendement de la chaîne générateur-batterie-charge (≈ 0,92 × 0,95 × 0,90 ≈ 0,79 pour un EPS de CubeSat typique). Utiliser un rendement global $\eta_{\text{ecl}} \approx 0.90$ est courant dans les manuels, mais légèrement optimiste.
>
> **Étape 3 : puissance en début de vie, compte tenu de la dégradation et de la température :**
> $$P_{\text{SA,BOL}} = \frac{P_{\text{SA,EOL}}}{L_d \times L_T}$$
> où $L_d = (1 - \delta)^n$ est le facteur de dégradation due aux rayonnements ($\delta = 0.025$/an pour le GaAs triple jonction en LEO) et $L_T = 1 + \beta_T (T_{\text{cell}} - T_{\text{ref}})$ est le facteur de déclassement en température ($\beta_T = -0.0019$/°C, $T_{\text{ref}} = 28$ °C, $T_{\text{cell}}$ typiquement 60–80 °C en LEO). Pour une cellule fonctionnant à 65 °C : $L_T = 1 + (-0.0019)(65 - 28) = 0.930$ (7 % de perte de puissance due à la température).
>
> **Étape 4 : surface du générateur :**
> $$A_{\text{SA}} = \frac{P_{\text{SA,BOL}}}{\eta_{\text{cell}} \times S \times \cos\theta \times f_{\text{pack}} \times f_{\text{cover}}}$$
> où :
> - $\eta_{\text{cell}} = 0.295$ (rendement du GaAs triple jonction sous AM0, à 28 °C — valeur nominale STC) ;
> - $S = 1361$ W/m² (constante solaire à 1 UA, Kopp & Lean 2011) ;
> - $\theta$ = **angle d'incidence solaire sur le générateur** (angle entre la normale au générateur et la direction du Soleil). Il vaut 0° pour un générateur orienté vers le Soleil. Pour un panneau fixe sur un satellite pointé au nadir, il est fixé par l'angle bêta de l'orbite du chapitre 7 : un panneau dont la normale est perpendiculaire au plan orbital voit un angle constant $\theta = 90° - |\beta|$, tandis qu'un panneau dont la normale est dans le plan orbital (la face zénith) voit $\cos\theta = \cos\beta\cos\nu$ varier le long de l'arc éclairé, si bien que l'on retient sa moyenne sur l'arc éclairé. Une aile déployable inclinée vers le Soleil sur une orbite héliosynchrone atteint typiquement un $\theta$ effectif moyen sur l'orbite de 20 à 25° ;
> - $f_{\text{pack}} = 0.85$–$0.90$ (taux de remplissage — fraction de la surface du panneau couverte de cellules ; des espaces sont nécessaires pour les interconnexions, les dégagements en bordure et le passage du harnais) ;
> - $f_{\text{cover}} = 0.97$ (pertes de transmission du verre de protection, typiquement 2 à 4 %).
>
> **Étape 5 : masse du générateur :**
> $$m_{\text{SA}} = A_{\text{SA}} \times \sigma_{\text{SA}} + m_{\text{mechanism}}$$
> où $\sigma_{\text{SA}}$ est la masse surfacique du panneau : fixé sur la structure (cellules sur substrat Al) ≈ 2,0–2,5 kg/m² ; déployable rigide (nid d'abeilles Al/CFRP) ≈ 1,5–2,0 kg/m² ; déployable souple ≈ 0,8–1,2 kg/m² ; $m_{\text{mechanism}}$ (charnière, ressort, mécanisme de gerbage) vaut typiquement 0,1–0,3 kg par panneau pour les CubeSats.

La figure 9.2 montre ce que l'équation de dimensionnement met en balance : la production est une impulsion quasi rectangulaire sur l'arc éclairé, tandis que la charge est un empilement de la puissance permanente du bus, de la puissance des réchauffeurs et des pointes brèves de prise de vue et de liaison descendante — dont certaines tombent en éclipse et doivent être fournies par la batterie.

![Production de puissance et profil de charge empilé sur une orbite.](../assets/figures/fig_power_modes.png)

**Figure 9.2** — En haut : production du générateur solaire au cours d'une orbite (arc éclairé et éclipse). En bas : profil de charge empilé illustratif par sous-système, avec les pointes de prise de vue et de liaison descendante superposées aux charges permanentes du bus et des réchauffeurs. Le générateur doit fournir la charge de la phase éclairée et recharger l'énergie de l'éclipse pendant l'arc éclairé.

> **Exemple résolu — générateur solaire d'EOSat-3U**
>
> **Données** (chapitre 7, §7.2, et chapitre 8, tableau 8.4) : orbite héliosynchrone à 500 km, $T = 94.6$ min, $t_{\text{sun}} = 58.8$ min, $t_{\text{ecl}} = 35.8$ min ; demande de pointe en phase éclairée $P_{\text{sun}} = 10.0$ W (mode liaison descendante), $P_{\text{ecl}} = 3.5$ W ; durée de la mission 3 ans ; température des cellules 65 °C ; un panneau déployable avec un angle effectif moyen sur l'orbite $\theta = 23°$ ; $\eta_{\text{sun}} = 0.90$, $\eta_{\text{ecl}} = 0.92 \times 0.95 \times 0.90 = 0.786$.
>
> **Étape 2 — Puissance du générateur en EOL :**
> $\dfrac{P_{\text{sun}}}{\eta_{\text{sun}}} = \dfrac{10.0}{0.90} = 11.11$ W $\qquad \dfrac{P_{\text{ecl}}\, t_{\text{ecl}}}{\eta_{\text{ecl}}\, t_{\text{sun}}} = \dfrac{3.5 \times 35.8}{0.786 \times 58.8} = \dfrac{125.3}{46.2} = 2.71$ W
>
> $P_{\text{SA,EOL}} = 11.11 + 2.71 = 13.82$ W
>
> **Étape 3 — Puissance en BOL, avec 3 ans de dégradation et la température :**
> $L_d = (1 - 0.025)^3 = 0.9269$ ; $\quad L_T = 1 + (-0.0019)(65 - 28) = 0.930$
>
> $P_{\text{SA,BOL}} = \dfrac{13.82}{0.9269 \times 0.930} = \dfrac{13.82}{0.862} = 16.0$ W
>
> **Étape 4 — Surface du générateur :**
> $A_{\text{SA}} = \dfrac{16.0}{0.295 \times 1361 \times \cos 23° \times 0.85 \times 0.97} = \dfrac{16.0}{0.295 \times 1361 \times 0.9205 \times 0.85 \times 0.97} = \dfrac{16.0}{304.7} = 0.0526$ m²
>
> Cela correspond à environ 23 cm × 23 cm — réalisable avec un seul panneau déployable sur un CubeSat 3U (les ailes déployables commerciales pour 3U offrent jusqu'à ~0,06 m² chacune).
>
> **Étape 5 — Masse du générateur (déployable, rigide) :**
> $m_{\text{SA}} = 0.0526 \times 1.8 + 0.15 = 0.095 + 0.15 = 0.25$ kg (panneau + mécanisme)
>
> **Comparaison avec Planet SuperDove :** le SuperDove réel utilise des cellules fixées sur la structure plus deux ailes déployables, et atteint ~25 W en BOL. Les 16 W en BOL calculés ici pour un seul panneau sont cohérents — la puissance plus élevée du SuperDove lui permet d'assurer simultanément la prise de vue en continu et la liaison descendante en bande S.
>
> **Mise en garde sur les données d'entrée.** Le chapitre 12, §12.5.3, montre que la charge de prise de vue calculée au niveau des équipements atteint ≈ 10 W ; le dimensionnement ci-dessus utilise l'allocation paramétrique de 8 W du tableau 8.4 (et la pointe de 10 W en liaison descendante) et devra être refait une fois les équipements choisis — une itération typique du CDF.

La figure 9.3 généralise le calcul sous forme d'abaque : pour un rendement de cellule, une dégradation, un angle solaire et un rendement de chaîne donnés, la surface du générateur requise en EOL se lit directement à partir de la charge moyenne sur l'orbite et de la fraction d'éclipse.

![Abaque de dimensionnement du générateur solaire.](../assets/figures/fig_solar_array.png)

**Figure 9.3** — Abaque de dimensionnement du générateur solaire suivant la chaîne du §9.2. À gauche : puissance du générateur en BOL en fonction de la charge moyenne sur l'orbite pour trois fractions d'éclipse (étapes 2–3, avec $\eta_{\text{sun}} = 0.90$, $\eta_{\text{ecl}} = 0.79$ et $L_d L_T = 0.86$) ; la fraction d'éclipse accroît le besoin, car l'énergie de l'éclipse doit être rechargée pendant l'arc éclairé. À droite : surface du générateur obtenue à l'étape 4, $A = P_{\text{BOL}}/(\eta_{\text{cell}} S \cos\theta f_{\text{pack}} f_{\text{cover}})$, pour trois angles solaires, avec le point d'EOSat-3U (16,0 W en BOL → 0,053 m² à θ = 23°) repéré.

### 9.2.1 Puissance des générateurs solaires de CubeSats : valeurs de référence

| Configuration | 1U | 3U | 6U | 12U |
|--------------|-----|-----|-----|------|
| Fixé sur la structure uniquement | ~2 W | ~7 W | ~12 W | ~20 W |
| Un panneau déployable | ~4 W | ~15 W | ~30 W | ~55 W |
| Deux panneaux déployables | — | ~25 W | ~48 W | ~100 W |
| Quatre panneaux déployables | — | — | ~80 W | ~180 W |

*[Source : fiches techniques de fournisseurs ; ASTERIA 6U : 48 W en BOL confirmés ; Dove/SuperDove : ~25 W confirmés]*

---

## 9.3 Dimensionnement de la batterie

### 9.3.1 Chimie et physique de l'élément Li-ion

Toutes les batteries modernes d'engins spatiaux utilisent la chimie lithium-ion (Li-ion). Pendant la décharge, les ions lithium migrent de l'anode en graphite (électrode négative), à travers un électrolyte organique et un séparateur polymère, vers la cathode en oxyde métallique lithié (électrode positive), tandis que les électrons circulent dans le circuit extérieur en fournissant un travail. Pendant la charge, le processus s'inverse.

**Chimies de cathode couramment employées dans l'espace :**

| Chimie | Cathode | Tension nominale | Énergie massique | Durée de vie en cycles (DoD de 30 %) | Stabilité thermique | Héritage spatial |
|-----------|---------|----------------|---------------|----------------------|-------------------|----------------|
| **LCO** (LiCoO₂) | Oxyde de cobalt | 3,7 V | 150–200 Wh/kg | ~10 000 | Modérée | ISS, nombreux CubeSats (éléments 18650) |
| **NMC** (LiNiMnCoO₂) | Nickel-manganèse-cobalt | 3,7 V | 170–250 Wh/kg | ~5000 | Modérée | Héritage en progression |
| **LFP** (LiFePO₄) | Phosphate de fer | 3,2 V | 90–120 Wh/kg | ~50 000 | Excellente | Marginal (lorsque la durée de vie en cycles prime) |
| **NCA** (LiNiCoAlO₂) | Nickel-cobalt-aluminium | 3,6 V | 200–260 Wh/kg | ~3000 | Plus faible | Héritage spatial limité |

*[Source : Ratnakumar et al., NASA JPL ; fiches techniques d'éléments qualifiés pour l'espace ; spécifications d'éléments 18650 commerciaux]*

**Formats d'éléments :**

- **Cylindrique 18650 :** 18 mm de diamètre, 65 mm de long. Le cheval de bataille des missions CubeSat, de 2500 à 3350 mAh par élément selon le type ; énergie de 9 à 12 Wh par élément.
- **Éléments souples (*pouch*) :** dimensions sur mesure, énergie massique plus élevée (~250 Wh/kg), mais nécessitent un support structural externe. Utilisés sur certaines missions 6U+ et sur tous les grands engins spatiaux.
- **Éléments prismatiques :** boîtier rigide, intermédiaires entre les formats cylindrique et souple. Utilisés dans certaines conceptions propres à une mission.

**Configuration des éléments :**

Les éléments sont montés en série (S) pour augmenter la tension et en parallèle (P) pour augmenter la capacité :

- **1S (un seul élément) :** bus de 3,0–4,2 V. Utilisé pour les CubeSats 1U très simples.
- **2S (deux en série) :** bus de 6,0–8,4 V. Standard pour la plupart des CubeSats.
- **2S2P (deux en série, deux en parallèle) :** bus de 6,0–8,4 V, capacité doublée (~38 Wh avec quatre éléments 18650). Utilisé pour les missions plus énergivores.

**Circuits de protection :** tout pack de batterie de vol comporte :

- **la surveillance de la tension des éléments :** mesure de la tension de chaque élément pour détecter les surtensions et sous-tensions ;
- **la protection contre les surintensités :** résistances de mesure de courant + interrupteurs MOSFET pour déconnecter en cas de surintensité (prévient l'emballement thermique par court-circuit) ;
- **la surveillance de la température :** thermistances sur chaque élément ; charge inhibée en dessous de 0 °C et au-dessus de 45 °C ;
- **le circuit de réchauffage :** réchauffeur Kapton sur le pack de batterie, régulé par thermostat, pour maintenir les éléments au-dessus de la température minimale de charge pendant l'éclipse.

**Modèle de perte de capacité :** les éléments Li-ion perdent de la capacité au fil du temps en raison de la croissance de l'interphase électrolyte solide (SEI) sur l'anode. Un modèle simplifié de perte calendaire et de perte par cyclage :

$$C(t, N) = C_0 \times (1 - \alpha \sqrt{t}) \times (1 - \beta_c \cdot N \cdot \text{DoD}^{\gamma})$$

où $C_0$ = capacité initiale, $t$ = temps (années), $N$ = nombre de cycles, $\alpha \approx 0.02$ (perte calendaire), $\beta_c \approx 3 \times 10^{-6}$, $\gamma \approx 2.1$ (perte par cyclage). En LEO avec une DoD de 30 %, on obtient une perte de capacité d'environ 5 à 8 % par an — valeur cohérente avec les données de vol issues des remplacements de batteries de l'ISS et de la télémesure des flottes de CubeSats.

### 9.3.2 Équations de dimensionnement

> **Équations clés — dimensionnement de la batterie**
>
> **Énergie requise de la batterie :**
> $$E_{\text{bat}} = \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{\text{DoD} \times \eta_{\text{dis}}}$$
> où DoD est la profondeur de décharge maximale, $\eta_{\text{dis}} = 0.95$ (rendement de décharge, qui tient compte des pertes $I^2R$ dans la résistance interne) et $t_{\text{ecl}}$ est exprimé en heures.
>
> **Masse de la batterie :**
> $$m_{\text{bat}} = \frac{E_{\text{bat}}}{e_{\text{specific}}}$$
> où $e_{\text{specific}} = 150$–$200$ Wh/kg pour des éléments Li-ion 18650 intégrés en pack (l'énergie massique au niveau de l'élément est plus élevée, mais l'intégration ajoute ~30 % de masse).
>
> **Relation entre durée de vie en cycles et DoD** (Li-ion 18650, chimie LCO) :
>
> | DoD | Durée de vie en cycles typique | Durée de mission compatible | Éclipses annuelles (LEO, 15/jour) |
> |-----|-------------------|--------------------------|-------------------------------|
> | 80 % | ~500 cycles | < 1 mois | 450 |
> | 50 % | ~2000 cycles | < 4 mois | 1800 |
> | 30 % | ~10 000 cycles | 1–2 ans | 5475 |
> | 20 % | ~30 000 cycles | 3–5 ans | 10 950 |
> | 10 % | ~100 000 cycles | > 7 ans | 38 325 |
>
> **Règle empirique de conception :** pour une mission LEO de plusieurs années, partez d'une DoD de 20 à 30 %. Pour une courte démonstration technologique (< 6 mois), une DoD de 40 à 50 % est acceptable et réduit nettement la taille, la masse et le coût de la batterie.

La figure 9.4 montre les courbes de durée de vie en cycles qui sous-tendent ce tableau pour trois familles Li-ion, avec les nombres de cycles en LEO correspondant à 1, 5 et 10 ans.

![Durée de vie en cycles de la batterie en fonction de la profondeur de décharge.](../assets/figures/fig_battery_dod.png)

**Figure 9.4** — Nombre de cycles jusqu'à la fin de vie en fonction de la profondeur de décharge pour des éléments LCO éprouvés, NCA/NMC aérospatiaux et LFP. Les droites horizontales repèrent les nombres de cycles de missions LEO de 1, 5 et 10 ans à ~15 éclipses par jour ; le point de conception à 30 % de DoD est typique d'une mission de plusieurs années.

> **Exemple résolu — batterie d'EOSat-3U**
>
> **Données :** $P_{\text{ecl}} = 3.5$ W, $t_{\text{ecl}} = 35.8$ min $= 0.597$ h, DoD $= 0.25$ (valeur prudente pour une mission de 3 ans), $\eta_{\text{dis}} = 0.95$.
>
> **Étape 1 — Énergie requise de la batterie :**
> $E_{\text{bat}} = \dfrac{3.5 \times 0.597}{0.25 \times 0.95} = \dfrac{2.09}{0.2375} = 8.8$ Wh
>
> **Étape 2 — Application de la marge système de phase A (20 %, tableau 8.3) :**
> $E_{\text{bat,spec}} \geq 8.8 \times 1.20 = 10.6$ Wh. Spécifiez **11 Wh au minimum**, idéalement **20 Wh** pour disposer de souplesse opérationnelle.
>
> **Étape 3 — Vérification de la durée de vie en cycles :**
> Une mission de 3 ans à $1440/94.6 = 15.2$ orbites/jour donne $3 \times 365 \times 15.2 \approx 16\,650$ éclipses. Avec une DoD de 25 %, les éléments Li-ion 18650 assurent ~20 000 cycles. **Marge ≈ 20 %. Conforme.**
>
> En tenant compte de la perte de capacité : après 3 ans, ~15–20 % de perte de capacité due au vieillissement calendaire et au cyclage. La DoD effective passe à $0.25/0.82 = 0.30$ — ce qui reste dans le régime des 10 000 cycles. **Acceptable sous surveillance.**
>
> **Étape 4 — Masse de la batterie :**
> $m_{\text{bat}} = \dfrac{20}{170} = 0.12$ kg (avec 170 Wh/kg pour des éléments 18650 intégrés en pack)
>
> **Étape 5 — Volume de la batterie :**
> Deux éléments 18650 en 2S1P : environ 34 mL, ce qui tient facilement dans un empilement 3U.
>
> **Comparaison avec Planet SuperDove :** le SuperDove emporte environ 20 Wh en configuration 2S2P (4 éléments), ce qui est cohérent avec ce dimensionnement. La DoD réelle en exploitation est estimée à 10–15 % par éclipse, ce qui laisse une marge de durée de vie en cycles confortable au regard de la cadence de renouvellement pluriannuelle de la constellation.

**Modes de défaillance à surveiller :**

- **Emballement thermique :** si un élément est surchargé, endommagé mécaniquement ou subit un court-circuit interne, la décomposition exothermique du matériau de cathode peut conduire à un emballement thermique (auto-échauffement > dissipation de chaleur), avec des températures pouvant dépasser 600 °C. Parades : fusibles au niveau des éléments, surveillance de la tension de chaque élément, coupures thermiques.
- **Dépôt de lithium métallique :** une charge en dessous de 0 °C provoque le dépôt de lithium métallique à la surface de l'anode au lieu de son insertion dans le graphite. Ce phénomène est irréversible, réduit la capacité et peut provoquer des courts-circuits internes. Parades : réchauffeur de batterie + thermostat + verrouillage logiciel.
- **Déséquilibre de capacité :** dans les configurations en série, l'élément le plus faible limite le pack. Si les éléments vieillissent à des rythmes différents, l'élément le plus faible atteint le seuil de coupure sur sous-tension alors que les autres disposent encore de capacité. Parades : circuits d'équilibrage des éléments, éléments appariés issus d'un même lot.

---

## 9.4 Sous-système de contrôle thermique

*[Source : ECSS-E-ST-31C ; Gilmore, chap. 1–4 ; SMAD, chap. 11.5]*

La figure 9.5 résume le bilan énergétique développé dans cette section : quatre apports de chaleur (flux solaire direct, albédo terrestre, infrarouge terrestre et dissipation électrique propre du satellite) et une seule sortie, le rayonnement vers l'espace profond, avec les conditions de cas chaud et de cas froid qui encadrent la conception.

![Schéma du bilan énergétique thermique d'un CubeSat en LEO avec les apports solaire, d'albédo, d'infrarouge terrestre et interne, le rayonnement vers l'espace et les annotations de cas chaud et de cas froid.](../assets/figures/fig_thermal_schematic.png)

**Figure 9.5** — Bilan énergétique thermique d'un CubeSat en LEO. Le flux solaire direct, l'albédo terrestre et l'infrarouge terrestre sont absorbés selon les propriétés du revêtement $\alpha_s$ et $\varepsilon$ et selon les facteurs de forme ; la dissipation interne ajoute la puissance électrique convertie en chaleur ; la seule sortie est le rayonnement vers l'espace profond, $\varepsilon \sigma A_{\text{rad}} T^4$. Le cas chaud combine Soleil au périhélie, dissipation maximale, revêtements en fin de vie et albédo maximal ; le cas froid correspond à l'éclipse en mode survie avec des revêtements en début de vie et un infrarouge terrestre minimal (§9.4.5).

### 9.4.1 La physique du contrôle thermique d'un engin spatial

Le contrôle thermique d'un engin spatial diffère fondamentalement de la thermique terrestre, car **il n'y a pas de convection dans le vide**. Les seuls modes de transfert de chaleur sont :

1. **la conduction :** flux de chaleur à travers un matériau solide, régi par la loi de Fourier : $\dot{Q} = -kA \dfrac{dT}{dx}$. Elle est déterminante au sein de la structure du satellite et entre les composants et leurs surfaces de montage ;
2. **le rayonnement :** transfert de chaleur par rayonnement électromagnétique, régi par la loi de Stefan-Boltzmann : $\dot{Q} = \varepsilon \sigma A T^4$. C'est le **seul** mécanisme permettant de rejeter de la chaleur vers l'environnement.

Il n'existe aucun refroidissement par convection. Un composant qui surchauffe ne peut pas être refroidi par un ventilateur. Toute la chaleur dissipée doit être conduite jusqu'à une surface rayonnante, puis rayonnée vers l'espace. C'est la contrainte centrale de la conception thermique d'un engin spatial.

### 9.4.2 Environnement thermique en LEO

Un engin spatial en LEO reçoit quatre apports thermiques et dispose d'un puits thermique :

| Source | Flux | Direction | Variabilité |
|--------|------|-----------|-------------|
| **Flux solaire direct** | $S = 1361 \pm 1$ W/m² (à 1 UA) | Faces orientées vers le Soleil uniquement | Saisonnière (±3,3 % du fait de l'excentricité de l'orbite terrestre : $S_{\text{perihelion}} = 1414$ W/m² en janvier, $S_{\text{aphelion}} = 1322$ W/m² en juillet) |
| **Albédo terrestre** | $\alpha_E \times S \approx 0.30 \times 1361 \approx 408$ W/m² | Faces orientées vers la Terre (nadir) | Varie selon la couverture nuageuse et le type de surface (0,06 pour l'océan à 0,80 pour la neige fraîche) ; plage moyenne sur l'orbite 0,25–0,35 |
| **Infrarouge terrestre** | $q_{\text{IR}} \approx 240$ W/m² (moyenne sur l'orbite) | Faces orientées vers la Terre (nadir) | Plage de 200–270 W/m² selon la latitude, la saison et la couverture nuageuse |
| **Dissipation interne** | $Q_{\text{int}} = P_{\text{dissipated}}$ | Chaleur dissipée par l'électronique | Varie selon le mode opérationnel ; la quasi-totalité de la puissance électrique finit en chaleur |
| **Espace profond** (puits) | $T_{\text{space}} \approx 2.7$ K (CMB) | Surfaces radiatives orientées vers le zénith | Pratiquement 0 K pour l'ingénieur |

### 9.4.3 Facteurs de forme

La fraction de la « vue » radiative d'une surface qui voit chaque source thermique est déterminante pour la précision de la modélisation thermique. Pour une surface plane orientée vers le nadir en LEO :

$$F_{\text{Earth}} = \frac{1}{1 + (h/R_E)^2 + 2(h/R_E)} = \left(\frac{R_E}{R_E + h}\right)^2$$

où $h$ est l'altitude et $R_E = 6378.137$ km. Pour une orbite à 500 km : $F_{\text{Earth}} = (6378.137/6878.137)^2 = 0.860$. La face nadir voit 86 % de Terre et 14 % d'espace profond. La face zénith voit 100 % d'espace profond (en l'absence d'ombre portée du satellite sur lui-même). Les faces latérales voient un mélange des deux.

Aux altitudes plus élevées, $F_{\text{Earth}}$ diminue : il vaut 0,79 à 800 km et seulement 0,023 à 35 786 km (GEO) — c'est pourquoi la conception thermique en GEO est dominée par le flux solaire et la dissipation interne, et non par l'infrarouge terrestre ou l'albédo.

### 9.4.4 Équation du bilan thermique

> **Équations clés — équilibre thermique** (partie V, §V.10)
>
> En régime permanent, la chaleur absorbée est égale à la chaleur rayonnée :
> $$Q_{\text{in}} = Q_{\text{out}}$$
>
> **Chaleur absorbée (forme développée) :**
> $$Q_{\text{in}} = \underbrace{\alpha_s \cdot A_{\text{sun}} \cdot S}_{\text{flux solaire direct}} + \underbrace{\alpha_s \cdot A_{\text{alb}} \cdot F_{\text{alb}} \cdot \alpha_E \cdot S}_{\text{albédo terrestre}} + \underbrace{\varepsilon \cdot A_{\text{IR}} \cdot F_{\text{IR}} \cdot q_{\text{IR}}}_{\text{IR terrestre}} + \underbrace{Q_{\text{int}}}_{\text{dissipation interne}}$$
>
> **Chaleur rayonnée :**
> $$Q_{\text{out}} = \varepsilon \cdot \sigma \cdot A_{\text{rad}} \cdot T^4$$
>
> où :
> - $\alpha_s$ = absorptivité solaire du revêtement de surface (sans dimension, 0–1) ;
> - $\varepsilon$ = émissivité infrarouge du revêtement de surface (sans dimension, 0–1) ;
> - $\sigma = 5.670 \times 10^{-8}$ W/m²/K⁴ (constante de Stefan-Boltzmann) ;
> - $A_{\text{sun}}$, $A_{\text{alb}}$, $A_{\text{IR}}$, $A_{\text{rad}}$ = surfaces projetées pour chaque flux (m²) ;
> - $F_{\text{alb}}$, $F_{\text{IR}}$ = facteurs de forme vers la Terre des surfaces exposées à l'albédo et à l'infrarouge ;
> - $T$ = température d'équilibre (K).
>
> **Remarque sur $\alpha_s$ et $\varepsilon$ :** l'absorptivité solaire ($\alpha_s$) se mesure sur le spectre solaire (0,2–2,5 µm, maximum à 0,5 µm dans le visible). L'émissivité infrarouge ($\varepsilon$) se mesure sur le spectre de l'infrarouge thermique (3–50 µm, maximum vers ~10 µm pour des objets à température ambiante). Ce sont des **domaines spectraux différents** ; on a donc $\alpha_s \neq \varepsilon$ pour la plupart des surfaces réelles. Ce découplage est le fondement de tout contrôle thermique passif : en choisissant le rapport $\alpha_s/\varepsilon$, le concepteur maîtrise la température d'équilibre.
>
> **Résolution pour la température d'équilibre :**
> $$T = \left(\frac{Q_{\text{absorbed}} + Q_{\text{internal}}}{\varepsilon \sigma A_{\text{rad}}}\right)^{1/4}$$
>
> Cette équation n'est valable que pour un nœud isotherme unique (modèle à paramètres localisés). Pour les modèles thermiques à plusieurs nœuds (indispensables pour tout engin spatial réel), le bilan thermique est résolu simultanément pour tous les nœuds à l'aide d'un logiciel numérique d'analyse thermique.

### 9.4.5 Cas chaud et cas froid

| Cas | Conditions | Préoccupation de conception |
|------|-----------|----------------|
| **Cas chaud** | Exposition solaire maximale ($S = 1414$ W/m², périhélie), tous les sous-systèmes actifs ($Q_{\text{int}}$ maximal), angle solaire le plus défavorable ($A_{\text{sun}}$ maximale), revêtements en EOL ($\alpha_s$ accrue par le noircissement sous UV), albédo maximal (0,35) | Des composants dépassent leur température maximale de fonctionnement |
| **Cas froid** | Éclipse (pas de flux solaire), dissipation minimale (mode survie, $Q_{\text{int}}$ minimal), revêtements en BOL ($\alpha_s$ à son minimum), infrarouge terrestre minimal (200 W/m²), vue sur l'espace profond | Des composants descendent sous leur température minimale de fonctionnement |

**Philosophie de conception :** l'ingénieur thermicien conçoit le système de façon à maintenir tous les composants dans leur plage de température qualifiée, aussi bien dans le cas chaud que dans le cas froid les plus défavorables, en appliquant les marges imposées par l'ECSS.

### 9.4.6 Revêtements de surface — la boîte à outils du contrôle thermique passif

| Revêtement | $\alpha_s$ (BOL) | $\alpha_s$ (EOL, 5 ans en LEO) | $\varepsilon$ | $\alpha_s/\varepsilon$ (BOL) | Cas d'emploi |
|---------|-----------|---------------------------|--------------|------------------------|----------|
| Peinture blanche (AZ-93, S13G-LO) | 0,14–0,20 | 0,25–0,35 | 0,89–0,92 | 0,16–0,22 | Surfaces de radiateurs (restent froides : faible absorption solaire, forte émission infrarouge) |
| Peinture noire (Aeroglaze Z306) | 0,95 | 0,95 | 0,89 | 1,07 | Surfaces internes (maximiser les échanges radiatifs entre composants) |
| Ruban doré (Kapton 2 mil + VDA) | 0,22–0,25 | 0,25–0,30 | 0,03–0,05 | 5,0–7,5 | Couche externe du MLI, isolation thermique |
| Aluminium nu (poli) | 0,10–0,15 | 0,15–0,20 | 0,03–0,05 | 2,5–4,0 | Surfaces réfléchissantes, faible émissivité |
| Alodine (conversion chromatée sur Al) | 0,35–0,40 | 0,40–0,50 | 0,12–0,16 | 2,5–3,0 | Contrôle thermique modéré, surfaces structurales |
| Aluminium anodisé (incolore ou noir) | 0,30–0,50 | 0,35–0,55 | 0,75–0,86 | 0,4–0,65 | Structure externe des CubeSats (finition standard selon le CDS) |
| Couverture MLI (valeur effective) | 0,05–0,15 | 0,10–0,20 | 0,02–0,05 | ~3 | Isolation thermique des composants sensibles |
| Cellules solaires (avec verre de protection) | 0,75–0,92 | 0,78–0,92 | 0,80–0,85 | ~1,0 | Surfaces du générateur solaire (forte absorption inévitable ; les cellules chauffent) |
| OSR (réflecteur solaire optique) | 0,05–0,08 | 0,08–0,12 | 0,78–0,80 | 0,06–0,10 | Radiateurs à hautes performances (grands engins spatiaux, GEO) |

**Idée essentielle pour la conception :** une surface à faible rapport $\alpha_s/\varepsilon$ (p. ex. peinture blanche : 0,2) reste froide, car elle réfléchit l'essentiel de l'énergie solaire tout en rayonnant efficacement dans l'infrarouge thermique. Une surface à rapport $\alpha_s/\varepsilon$ élevé (p. ex. ruban doré : 6,0) reste chaude, car elle absorbe l'énergie solaire mais ne rayonne presque pas. C'est pourquoi la peinture blanche est employée sur les radiateurs et l'or ou le MLI pour l'isolation. La figure 9.6 trace la température d'équilibre d'une plaque plane en LEO en fonction de ce rapport.

![Équilibre thermique radiatif en fonction de α/ε.](../assets/figures/fig_thermal_balance.png)

**Figure 9.6** — Température d'équilibre moyenne sur l'orbite d'une plaque plane en LEO en fonction de $\alpha_s/\varepsilon$, avec les revêtements courants repérés. La peinture blanche se situe bien en dessous de la plage de fonctionnement de l'électronique, la peinture noire près de sa limite supérieure ; la ligne tiretée indique la température en éclipse seule (sans Soleil).

**Dégradation des revêtements :** le rayonnement UV noircit progressivement la plupart des peintures blanches, ce qui augmente $\alpha_s$ en laissant $\varepsilon$ presque inchangée. Le rapport $\alpha_s/\varepsilon$ augmente donc, et la surface est plus chaude en EOL. La conséquence pour l'analyse des cas les plus défavorables est facile à inverser par erreur : en BOL, la peinture blanche a l'$\alpha_s$ la *plus faible* ; le **cas froid est donc le plus conservatif avec les propriétés en BOL**, tandis que le **cas chaud est le plus conservatif avec les propriétés en EOL**, une fois que $\alpha_s$ a augmenté. Chaque cas doit être évalué avec les propriétés qui le rendent le plus défavorable.

### 9.4.7 MLI (isolant multicouche) — constitution et physique

Les couvertures MLI sont l'isolant thermique le plus répandu sur les engins spatiaux. Elles agissent en réduisant au minimum les transferts de chaleur par rayonnement et par conduction grâce à de multiples couches réfléchissantes séparées par des intercalaires peu conducteurs.

**Constitution (couverture MLI typique) :**

1. **Enveloppe externe :** Kapton aluminisé de 1 mil (25 µm) (VDA — aluminium déposé sous vide sur une face). Assure la protection mécanique et une faible absorptivité solaire.
2. **Couches réfléchissantes internes :** 10 à 20 couches de Mylar doublement aluminisé (DAM) de 0,25 mil (6 µm). Chaque couche réfléchit le rayonnement infrarouge, et les espaces sous vide entre les couches ne donnent lieu à aucune convection.
3. **Intercalaires :** filet de Dacron ou de Nomex entre chaque couche de DAM, qui empêche tout contact conductif entre feuilles réfléchissantes adjacentes.
4. **Enveloppe interne :** Kapton aluminisé de 1 mil, qui protège les couches internes.

**Émissivité effective :** une couverture MLI idéale comportant $N$ couches réfléchissantes a une émissivité effective de :

$$\varepsilon_{\text{eff}} = \frac{1}{2/\varepsilon_{\text{inner}} + (N-1)(2/\varepsilon_{\text{layer}} - 1)}$$

Pour 20 couches de DAM ($\varepsilon_{\text{layer}} = 0.03$) : $\varepsilon_{\text{eff}} \approx 0.002$. En pratique, un MLI réel atteint $\varepsilon_{\text{eff}} = 0.01$–$0.03$ en raison des coutures, des traversées (harnais, fixations) et des effets de bord. Les performances réelles sont typiquement 2 à 5 fois moins bonnes que les performances théoriques.

**Difficultés du MLI sur CubeSat :** les CubeSats disposent d'une surface limitée et de nombreuses traversées (connecteurs, antennes, capteurs, cellules solaires), ce qui rend difficile l'obtention de bonnes performances du MLI. La plupart des CubeSats en LEO n'utilisent pas de MLI — ils s'appuient sur l'environnement thermique modéré (l'infrarouge terrestre fournit un « plancher chaud ») et sur les revêtements de surface. Le MLI devient indispensable pour les CubeSats d'exploration lointaine (p. ex. MarCO, CAPSTONE) ou pour les missions à charge utile sensible (détecteurs infrarouges, systèmes laser).

### 9.4.8 Dimensionnement des réchauffeurs

Lorsque le contrôle thermique passif ne peut empêcher un composant de descendre sous sa température minimale (typiquement pendant l'éclipse ou en mode survie), des réchauffeurs électriques sont nécessaires.

> **Équations clés — dimensionnement des réchauffeurs**
>
> **Puissance de réchauffage requise** (pour maintenir la température minimale dans le cas froid le plus défavorable) :
> $$P_{\text{heater}} = \varepsilon \sigma A_{\text{rad}} T_{\text{min}}^4 - Q_{\text{environment,cold}} - Q_{\text{internal,cold}}$$
> où $T_{\text{min}}$ est la température minimale admissible du composant (en kelvins).
>
> **Types de réchauffeurs pour CubeSat :**
> - **Réchauffeurs souples en Kapton :** éléments résistifs en feuille gravée, laminés entre des feuilles de Kapton. Souples, minces (0,2–0,5 mm), légers (2–10 g chacun). Puissance typique : 0,5–5 W par réchauffeur. Collés directement sur la surface du composant avec un adhésif sensible à la pression.
> - **Réchauffeurs à cartouche :** cylindriques, insérés dans des alésages. Densité de puissance plus élevée, mais plus lourds et moins courants sur les CubeSats.
>
> **Régulation par thermostat :** de simples thermostats bimétalliques mettent les réchauffeurs en marche et à l'arrêt à des températures de consigne (p. ex. marche à −5 °C, arrêt à +5 °C). Masse : ~2 g chacun. Pour une plus grande fiabilité, les CubeSats modernes privilégient des réchauffeurs pilotés par logiciel à partir des capteurs de température et des interrupteurs de l'EPS — mais cela suppose que l'OBC fonctionne, ce qui peut ne pas être le cas en mode survie.

### 9.4.9 Caloducs et tresses thermiques

Les **caloducs** sont des dispositifs passifs de transfert de chaleur diphasiques, capables de transporter de grandes quantités d'énergie thermique avec de très faibles écarts de température. Largement employés sur les engins spatiaux de plus grande taille, ils commencent à apparaître sur les CubeSats 6U+.

**Fonctionnement d'un caloduc :**

1. le fluide de travail (ammoniac, méthanol ou eau) s'évapore à l'extrémité chaude (évaporateur) en absorbant de la chaleur latente ;
2. la vapeur circule dans le cœur creux du tube jusqu'à l'extrémité froide (condenseur) ;
3. au condenseur, la vapeur restitue sa chaleur latente et se condense en liquide ;
4. le liquide revient à l'évaporateur par capillarité dans une structure capillaire (métal fritté, rainures axiales ou toile tissée) ;
5. le processus est continu et passif (aucune pièce mobile, aucune puissance consommée) et permet de transporter 10 à 100 W sur 20 à 50 cm avec un écart de température < 5 °C.

**Conductance thermique d'un caloduc :** sa conductivité thermique effective est de 10 000 à 100 000 W/m/K (contre 400 W/m/K pour le cuivre et 237 W/m/K pour l'aluminium). Un caloduc à ammoniac de 6 mm de diamètre peut transporter ~30 W sur 30 cm avec un gradient < 3 °C.

Les **tresses thermiques** sont des liaisons conductrices souples (cuivre tressé, fibres de graphite ou feuille de graphite pyrolytique) qui conduisent la chaleur entre des composants ne pouvant pas être reliés rigidement (p. ex. au travers d'une charnière, ou entre une charge utile isolée des vibrations et la plateforme). Conductance typique : 0,5–5 W/K.

| Moyen de transport de la chaleur | Conductance | Masse | Puissance | Sensibilité à l'orientation | Emploi sur CubeSat |
|----------------------|-------------|------|-------|------------------------|------------|
| Conduction dans l'aluminium | ~0,5–2 W/K par chemin | Fait partie de la structure | 0 W | Aucune | Toujours (intrinsèque) |
| Tresse thermique en cuivre | 1–5 W/K | 10–50 g | 0 W | Aucune | Occasionnel (6U+) |
| Caloduc (ammoniac) | 5–50 W/K | 20–100 g | 0 W | Dépend de la gravité (à essayer dans l'orientation représentative) | Rare (6U+, quelques 3U) |
| Boucle fluide pompée | 50–500 W/K | 500+ g | 5–20 W | Aucune | Grands engins spatiaux uniquement |

### 9.4.10 Synthèse des moyens de contrôle thermique

| Moyen | Type | Incidence sur la masse | Emploi typique | Paramètre de conception clé |
|--------|------|-------------|------------|---------------------|
| **Revêtements de surface** | Passif | Négligeable | Toujours — choisir le rapport $\alpha_s/\varepsilon$ de chaque face | Rapport $\alpha_s/\varepsilon$ |
| **Couvertures MLI** | Passif | 0,5–2,0 kg/m² | Isoler les composants sensibles de l'environnement | Nombre de couches, $\varepsilon_{\text{eff}}$ |
| **Radiateurs** | Passif | Fait partie de la structure | Rejeter la chaleur dissipée vers l'espace profond | Surface du radiateur, $\varepsilon$, vue sur l'espace |
| **Réchauffeurs** | Actif | 0,005–0,02 kg chacun | Maintenir la température minimale pendant l'éclipse ou en mode survie | Puissance, consigne du thermostat |
| **Caloducs** | Passif | 0,02–0,10 kg chacun | Transporter la chaleur de la source vers le radiateur | Fluide de travail, $Q_{\text{max}}$, orientation |
| **Tresses thermiques** | Passif | 0,01–0,05 kg chacune | Liaison conductrice souple au travers des jonctions et charnières | Conductance (W/K) |
| **Persiennes** | Actif | 0,1–0,5 kg | Radiateurs à conductance variable (rares sur les CubeSats) | Plage de températures d'ouverture/fermeture |

### 9.4.11 Marges thermiques de l'ECSS

*[Source : convention pédagogique propre à ce manuel ; les normes sont commentées sous le tableau]*

| Niveau | Marge chaude (au-dessus du maximum prédit) | Marge froide (en dessous du minimum prédit) |
|-------|----------------------------------|-----------------------------------|
| **Qualification** | Prédiction + 15 °C | Prédiction − 15 °C |
| **Recette** | Prédiction + 10 °C | Prédiction − 10 °C |
| **Fonctionnement** | Prédiction + 5 °C | Prédiction − 5 °C |

Ces marges garantissent que les incertitudes du modèle thermique (typiquement ±5 à 10 °C pour les modèles simplifiés, ±2 à 5 °C pour les modèles détaillés corrélés) ne provoquent pas de dépassements de température en orbite.

**Lien avec les normes.** L'ECSS-E-ST-31C ne tabule pas ces valeurs. Sa figure 3-1 définit l'enchaînement qui va de la température prédite, en passant par l'incertitude, aux températures de recette et de qualification ; elle laisse les marges à l'autorité système et précise qu'on n'applique normalement pas d'incertitude inférieure à 10 K avant un essai d'équilibre thermique. L'ECSS-E-ST-10-03C (tableaux 5-2 et 5-4) ajoute à cette plage une marge de recette de 5 °C et une marge de qualification de 5 °C, et le GSFC-STD-7000B §2.6 essaie une unité de protovol aux températures maximale et minimale prédites ± 10 °C, pendant au moins 4 cycles. Le niveau de vide thermique en protovol du chapitre 14, §14.3.4 (prévision ± 10 °C), suit ces normes.

> **Exemple résolu — analyse thermique à un nœud d'EOSat-3U**
>
> **Cas chaud (phase éclairée, mode de pointe, périhélie, revêtements en EOL) :**
>
> Modèle simplifié à un seul nœud. CubeSat 3U, pointé au nadir.
>
> - Surface exposée au Soleil (+Z, panneau 3U orienté vers le zénith) : $A_{\text{sun}} = 0.034$ m²
> - Surfaces du générateur solaire (exposées au Soleil) : $\alpha_s = 0.85$, $\varepsilon = 0.82$ (propriétés des cellules solaires)
> - Face nadir (−Z) : $A_{\text{nadir}} = 0.034$ m², Al anodisé ($\alpha_s = 0.45$ en EOL, $\varepsilon = 0.82$)
> - Faces latérales (4×) : $A_{\text{side}} = 4 \times 0.01$ m² $= 0.04$ m², Al anodisé
> - Dissipation interne (mode de pointe, liaison descendante à 10 W — tableau 8.4) : $Q_{\text{int}} = 10.0$ W. La quasi-totalité de la puissance électrique consommée par les charges finit en chaleur à l'intérieur du satellite ; la puissance RF effectivement rayonnée par l'antenne (un ou deux watts) est la seule exception, et elle est ici négligée par prudence.
>
> $Q_{\text{solar}} = 0.85 \times 0.034 \times 1414 = 40.9$ W — mais une bonne partie de cette énergie est convertie en électricité par les cellules ; l'apport thermique net par le générateur est donc $Q_{\text{solar,thermal}} = \alpha_s A S (1 - \eta_{\text{cell}}) = 0.85 \times 0.034 \times 1414 \times 0.705 = 28.8$ W
>
> $Q_{\text{albedo}} = 0.45 \times 0.034 \times 0.35 \times 1414 = 7.6$ W
>
> $Q_{\text{Earth IR}} = 0.82 \times 0.034 \times 270 = 7.5$ W (face nadir, infrarouge terrestre du cas chaud)
>
> Au total, $Q_{\text{in}} \approx 28.8 + 7.6 + 7.5 + 10.0 = 53.9$ W
>
> Surface rayonnante totale (les six faces, moins la surface du générateur, qui absorbe plus qu'elle ne rayonne, et compte tenu du masquage partiel de la face nadir par la Terre) : $A_{\text{rad}} \approx 0.066$ m² ; émissivité moyenne $\varepsilon_{\text{avg}} \approx 0.82$
>
> $T_{\text{hot}} = \left(\dfrac{53.9}{0.82 \times 5.67 \times 10^{-8} \times 0.066}\right)^{1/4} = \left(\dfrac{53.9}{3.07 \times 10^{-9}}\right)^{1/4} = (1.756 \times 10^{10})^{1/4} = 364$ K $= +91$ °C
>
> **Cette valeur dépasse les limites de la plupart des composants !** Ce calcul simplifié surestime toutefois la température, car il traite le satellite comme un nœud isotherme unique et y intègre l'absorption des cellules solaires de la face zénith. En pratique :
> - la face zénith (cellules solaires) est plus chaude que la plateforme ;
> - les composants internes sont couplés par conduction à toutes les faces, y compris à la face nadir, plus froide ;
> - un modèle à plusieurs nœuds prédit typiquement des températures internes maximales de +40 à +55 °C pour ce scénario.
>
> **Réponse de l'ingénieur thermicien :** si le calcul à un nœud dépasse 60 °C, un modèle thermique détaillé à plusieurs nœuds est nécessaire. Le calcul simplifié est un outil de tri, pas un outil de conception.
>
> **Cas froid (éclipse, mode survie, aphélie, revêtements en BOL) :**
>
> - Ni flux solaire ni albédo
> - Infrarouge terrestre seul : $Q_{\text{Earth IR}} = 0.82 \times 0.034 \times 200 = 5.58$ W (cas froid : 200 W/m²)
> - Dissipation interne (mode survie, tableau 8.4) : $Q_{\text{int}} = 2.0$ W
> - Au total, $Q_{\text{in}} = 5.58 + 2.0 = 7.58$ W
>
> $T_{\text{cold}} = \left(\dfrac{7.58}{0.82 \times 5.67 \times 10^{-8} \times 0.070}\right)^{1/4} = \left(\dfrac{7.58}{3.25 \times 10^{-9}}\right)^{1/4} = (2.33 \times 10^{9})^{1/4} = 220$ K $= -53$ °C
>
> **C'est trop froid** pour les batteries Li-ion (−20 °C minimum en fonctionnement, 0 °C minimum en charge) et pour la plupart des électroniques COTS (−40 °C minimum) — *si* le satellite avait le temps d'atteindre le régime permanent.
>
> **Vérification du réchauffeur en régime permanent.** Maintenir l'ensemble du satellite à $T_{\text{min}} = -10$ °C $= 263$ K exigerait
> $Q_{\text{heater}} = \varepsilon \sigma A_{\text{rad}} T_{\text{min}}^4 - Q_{\text{in}} = 3.25 \times 10^{-9} \times 263^4 - 7.58 = 15.6 - 7.58 = 8.0$ W
>
> Un réchauffeur de 8 W en éclipse dépasserait la capacité de la batterie. Mais il s'agit d'un calcul isotherme sur l'ensemble du satellite : en réalité, la batterie se trouve à l'intérieur de la plateforme, partiellement isolée par la structure et les cartes qui l'entourent, et un réchauffeur ciblé de 0,5 à 1,0 W placé sur le pack de batterie, avec un enveloppement MLI, suffit généralement. Surtout, l'éclipse ne dure que 36 minutes, et l'inertie thermique de la structure empêche le satellite de s'approcher, si peu que ce soit, du régime permanent.
>
> **Vérification en transitoire.** En éclipse, la vitesse de refroidissement nette est $Q_{\text{out}} - Q_{\text{in}}$. À l'entrée en éclipse, $T = 293$ K (+20 °C) :
>
> $Q_{\text{out}} = 0.82 \times 5.67 \times 10^{-8} \times 0.070 \times 293^4 = 3.25 \times 10^{-9} \times 7.37 \times 10^{9} = 24.0$ W
>
> $Q_{\text{net cooling}} = 24.0 - 7.58 = 16.4$ W
>
> Pour un satellite de 5 kg dont l'inertie thermique est dominée par l'aluminium ($c_p \approx 900$ J/kg/K) :
> $\Delta T = \dfrac{Q_{\text{net}} \times t}{m \times c_p} = \dfrac{16.4 \times 2150}{5.0 \times 900} = \dfrac{35\,260}{4500} = 7.8$ °C de baisse en 36 minutes
>
> Partant de +20 °C, le satellite se refroidit donc jusqu'à environ +12 °C après une éclipse — largement dans les limites (et l'estimation linéaire est elle-même prudente, puisque $Q_{\text{out}}$ diminue en $T^4$ à mesure que le satellite se refroidit). **Aucun réchauffeur n'est nécessaire pour la plateforme ; un réchauffeur de batterie seulement si la batterie est thermiquement isolée de la plateforme.**
>
> **Vérification des marges ECSS — détecteur de la charge utile :**
> Température maximale prédite du détecteur de la charge utile = 42 °C.
> - Limite de fonctionnement = 50 °C. Marge = 50 − 42 = 8 °C > 5 °C. **Conforme.**
> - Essai de qualification : à réaliser à 42 + 15 = 57 °C. Si la limite de qualification est de 60 °C : **conforme.**
>
> Température minimale prédite de la batterie = −8 °C pendant l'éclipse la plus défavorable.
> - Limite de fonctionnement = −10 °C. Marge = −8 − (−10) = 2 °C < 5 °C. **Non conforme — marge insuffisante.**
> - **Action :** ajouter un réchauffeur de survie de 0,5 W avec thermostat réglé à −5 °C, ou envelopper le pack de batterie de MLI.

---

## 9.5 Exemple résolu : puissance et thermique d'UniSat-1

Retour sur UniSat-1, le démonstrateur 1U du chapitre 1, §1.7, sur l'orbite de l'ISS à 400 km du chapitre 7, §7.7 (période de 92,6 min, 56,5 min d'ensoleillement, 36 min d'éclipse).

**Dimensionnement de la puissance : cellules fixées sur la structure uniquement.** UniSat-1 utilise des cellules solaires fixées sur les cinq faces exposées au Soleil (la sixième face porte l'interface de l'interrupteur de déploiement). En l'absence de panneaux déployables, le sous-système d'alimentation est plus simple, plus léger et moins cher — mais sa puissance est fortement limitée.

> **Exemple résolu — générateur solaire d'UniSat-1**
>
> **Données :** cellules fixées sur 5 faces d'un 1U (100 × 100 mm chacune). $P_{\text{ecl}} = 0.5$ W (OBC seul), $P_{\text{sun}} = 1.2$ W (chevauchement science + liaison descendante évité par la programmation). Durée de la mission : 6 mois. Température des cellules : 55 °C (sur un 1U, les cellules fixées sur la structure sont moins chaudes grâce à un bon couplage thermique avec la masse de la plateforme).
>
> **Étape 1 — Surface éclairée effective :**
> Avec une attitude magnétique passive (culbutage lent d'environ 1°/s), seules ~1,5 face sont en moyenne bien éclairées à un instant donné. Surface moyenne effective :
> $A_{\text{eff}} \approx 1.5 \times (0.10 \times 0.10) = 0.015$ m²
>
> **Étape 2 — Puissance du générateur en BOL (avec déclassement en température) :**
> $L_T = 1 + (-0.0019)(55 - 28) = 0.949$
>
> $P_{\text{SA,BOL}} = \eta_{\text{cell}} \times L_T \times S \times A_{\text{eff}} \times f_{\text{pack}} = 0.295 \times 0.949 \times 1361 \times 0.015 \times 0.80 = 4.57$ W (crête en éclairement)
>
> **Étape 3 — Puissance moyenne disponible sur l'orbite :**
> $P_{\text{avg,avail}} = P_{\text{SA,BOL}} \times \dfrac{t_{\text{sun}}}{T} \times \eta_{\text{EPS}} = 4.57 \times \dfrac{56.5}{92.6} \times 0.85 = 2.37$ W
>
> Après 6 mois de dégradation ($(1 - 0.025)^{0.5} = 0.987$) : $P_{\text{avg,EOL}} = 2.37 \times 0.987 = 2.34$ W
>
> **Étape 4 — Demande de puissance (moyenne sur l'orbite) :** d'après le chapitre 8, §8.5 : $P_{\text{avg,demand}} = 0.68$ W.
>
> **Marge de puissance :** $2.34 - 0.68 = 1.66$ W (**marge de 71 %**). Même avec des hypothèses géométriques prudentes, le bilan se boucle confortablement.
>
> **Remarque sur les générateurs fixés sur la structure et le culbutage :** la principale incertitude sur la puissance d'un 1U à cellules fixées sur la structure est l'attitude. Avec une stabilisation magnétique passive, le satellite s'aligne approximativement sur le champ magnétique terrestre, ce qui rend l'éclairement plus prévisible qu'un culbutage aléatoire ; la surface effective varie toutefois sensiblement le long de l'orbite, car la direction du champ change avec la latitude. La moyenne de 1,5 face est prudente — une simulation de Monte-Carlo de la géométrie d'éclairement sur de nombreuses orbites donne typiquement une moyenne plus optimiste de 1,7 à 1,9 face effective.

> **Exemple résolu — batterie d'UniSat-1**
>
> **Données :** $P_{\text{ecl}} = 0.5$ W, $t_{\text{ecl}} = 36$ min $= 0.60$ h, DoD $= 0.50$ (acceptable pour une mission de 6 mois : ~2740 cycles), $\eta_{\text{dis}} = 0.95$.
>
> $E_{\text{bat}} = \dfrac{0.5 \times 0.60}{0.50 \times 0.95} = \dfrac{0.30}{0.475} = 0.63$ Wh
>
> Avec marge : spécifiez **10 Wh** au minimum — la plus petite batterie COTS pour CubeSat bénéficiant d'un héritage en vol.
>
> **Vérification du nombre de cycles :** 6 mois à 15,5 orbites/jour ≈ 2800 éclipses. Avec une DoD de 50 %, les éléments Li-ion supportent sans difficulté > 2000 cycles. **Conforme.**
>
> **DoD réelle en exploitation :** avec une batterie de 10 Wh et 0,63 Wh par éclipse, la DoD réelle = 0,63/10 = **6,3 %** par éclipse. À cette DoD, la durée de vie dépasse 100 000 cycles. **La dégradation de la batterie est négligeable** sur la mission de 6 mois.
>
> **Idée essentielle :** la batterie de 10 Wh est très largement surdimensionnée par rapport à la demande réelle en éclipse. C'est fréquent sur les missions 1U — la plus petite batterie COTS disponible offre bien plus de capacité que nécessaire. Cette capacité excédentaire procure une excellente marge et permet de se remettre d'anomalies (plusieurs périodes éclairées manquées).

**Thermique : contrôle passif uniquement.** UniSat-1 n'utilise ni réchauffeurs, ni MLI, ni contrôle thermique actif. Trois facteurs le justifient :

1. **Basse altitude (400 km) :** le fort flux infrarouge terrestre (~240 W/m²) fournit un plancher chaud qui évite les cas froids extrêmes ;
2. **Mission courte (6 mois) :** aucune dégradation à long terme des revêtements n'est à craindre ;
3. **Composants tolérants :** l'électronique COTS fonctionne typiquement de −20 °C à +60 °C ; l'environnement thermique LEO à 400 km reste compris entre −10 °C et +45 °C pour un 1U à surfaces standard en aluminium nu ou anodisé.

> **Vérification thermique rapide — cas froid d'UniSat-1 (transitoire)**
>
> Éclipse la plus défavorable, tous les sous-systèmes éteints sauf l'OBC (0,5 W de dissipation interne) :
> - infrarouge terrestre absorbé : $\varepsilon \times A_{\text{nadir}} \times q_{\text{IR}} = 0.85 \times 0.01 \times 240 = 2.04$ W ;
> - dissipation interne : 0,5 W ;
> - chaleur entrante totale : 2,54 W.
>
> Température en régime permanent (si l'éclipse durait indéfiniment) :
> $T_{\text{steady}} = \left(2.54 / (0.85 \times 5.67 \times 10^{-8} \times 0.045)\right)^{1/4} = 195$ K $= -78$ °C
>
> **Cela semble alarmant** — mais l'éclipse ne dure que 36 minutes, et l'inertie thermique empêche le satellite d'atteindre le régime permanent.
>
> **Analyse transitoire :** en partant de $T_0 = +20$ °C (293 K) à l'entrée en éclipse :
>
> $Q_{\text{rad,out}} = 0.85 \times 5.67 \times 10^{-8} \times 0.045 \times 293^4 = 2.17 \times 10^{-9} \times 7.37 \times 10^{9} = 16.0$ W
>
> Refroidissement net : $16.0 - 2.54 = 13.5$ W
>
> Estimation linéaire : $\Delta T = \dfrac{Q_{\text{net}} \times t}{m \times c_p} = \dfrac{13.5 \times 36 \times 60}{1.0 \times 900} = \dfrac{29\,160}{900} = 32$ °C
>
> L'estimation linéaire est prudente — à mesure que le satellite se refroidit, la puissance rayonnée diminue en $T^4$, si bien que le refroidissement réel ralentit. Une estimation plus précise donne $\Delta T \approx 20$–$25$ °C, soit une température minimale d'environ −5 à −10 °C.
>
> **Conclusion :** le 1U à 400 km atteint environ −5 à −10 °C pendant l'éclipse la plus défavorable, en partant d'une entrée chaude depuis la phase éclairée. Ces valeurs restent dans les limites de fonctionnement des COTS (−20 °C à +60 °C pour la plupart des composants) et dans la plage de décharge de la batterie. **Aucun réchauffeur n'est nécessaire.** La brièveté de l'éclipse et le fort flux infrarouge terrestre à 400 km rendent le contrôle thermique passif viable pour une mission 1U.

---

## 9.6 Exemples de missions réelles

### 9.6.1 EPS de Planet SuperDove

| Paramètre | Valeur | Justification de conception |
|-----------|-------|-----------------|
| Format | 3U+, ~5 kg | Constellation Flock ; compatible avec le distributeur |
| Configuration du générateur solaire | Cellules fixées sur la structure + deux ailes déployables | ~25 W en BOL nécessaires pour la prise de vue en continu + la liaison descendante en bande S |
| Cellules du générateur | GaAs triple jonction | Qualité spatiale standard, 29,5 % sous AM0 |
| Batterie | Li-ion, ~20 Wh (2S2P 18650) | Assure une charge en éclipse de ~3,5 W pendant 35 min avec une DoD < 20 % |
| Tension du bus | Non régulée 7,2–8,4 V (2S) + régulée 3,3 V, 5 V | Architecture EPS standard des CubeSats |
| Demande de pointe | ~18 W (mode prise de vue) | Imageur multispectral + senseur stellaire + roues de réaction + OBC |
| Orbite | SSO à 475 km, période de ~94 min | Héliosynchrone pour un éclairement constant |
| Éclipse | ~35 min au maximum, ~3 W de demande | OBC + SCAO seulement pendant l'éclipse ; ni prise de vue ni liaison descendante |
| Thermique | Panneaux radiateurs fixés sur la structure + réchauffeur de batterie | Contrôle thermique passif ; réchauffeur de batterie pour la marge de charge en éclipse |

*[Source : présentations de Planet Labs en conférence ; Salas et al., « SuperDove Constellation », SSC 2021]*

### 9.6.2 Conception thermique de CAPSTONE

CAPSTONE, de la NASA (12U, 25 kg), évolue sur une orbite de halo quasi rectiligne (NRHO) autour de la Lune, avec des cycles thermiques extrêmes :

- périlune : fort rayonnement infrarouge de la Terre et de la Lune + flux solaire ;
- apolune : froid de l'espace profond, longues périodes d'ombre (jusqu'à plus de 12 heures) ;
- contrôle thermique : enveloppement MLI (couvertures de DAM à 10 couches), réchauffeurs sur les lignes de propulsion (pour empêcher le gel de l'ergol), panneaux radiateurs passifs peints en blanc (AZ-93) ;
- réchauffeurs de batterie : 5 W au total, régulés par thermostat, indispensables à la survie pendant les longues éclipses ;
- plage de température de fonctionnement : −20 °C à +50 °C pour l'électronique ; lignes de propulsion maintenues au-dessus de +5 °C.

*[Source : Advanced Space, « CAPSTONE Design Overview », SmallSat Conference 2022]*

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Physique des cellules solaires | Le GaAs triple jonction (InGaP/GaAs/Ge) atteint 28–30 % sous AM0 ; l'empilement multijonction capte une partie plus large du spectre solaire |
| Effets de la température | Les cellules perdent ~0,19 %/°C (en relatif) ; fonctionner à 65 °C coûte ~7 % de puissance par rapport aux STC |
| Dégradation | Dommages dus aux rayonnements : $(1-\delta)^n$, $\delta \approx 2.5$ %/an en LEO ; le verre de protection atténue les dommages dus aux protons et aux électrons |
| Architecture de l'EPS | MPPT + bus régulé est le standard CubeSat ; le MPPT extrait 10–15 % de puissance de plus que le DET |
| Dimensionnement du générateur | $P_{\text{SA,EOL}} = (P_{\text{sun}} t_{\text{sun}}/\eta_{\text{sun}} + P_{\text{ecl}} t_{\text{ecl}}/\eta_{\text{ecl}})/t_{\text{sun}}$ ; déclassement pour la dégradation $L_d$ et la température $L_T$ |
| Surface du générateur | $A = P_{\text{BOL}} / (\eta_{\text{cell}} \cdot S \cdot \cos\theta \cdot f_{\text{pack}} \cdot f_{\text{cover}})$ ; θ découle de la géométrie du générateur et de l'angle bêta de l'orbite |
| Chimie de la batterie | Li-ion (LCO/NMC) : 150–200 Wh/kg intégré en pack ; 3,0–4,2 V par élément ; charge CC-CV |
| Dimensionnement de la batterie | $E = P_{\text{ecl}} \cdot t_{\text{ecl}} / (\text{DoD} \cdot \eta_{\text{dis}})$ ; DoD de 20–30 % pour une mission LEO de plusieurs années |
| Modes de défaillance de la batterie | Emballement thermique (surcharge), dépôt de lithium métallique (charge à froid), déséquilibre de capacité (éléments en série) |
| Puissance des générateurs : valeurs de référence | Fixé sur la structure : 2–20 W ; un panneau déployable : 4–55 W ; deux panneaux déployables : 25–100 W (1U–12U, §9.2.1) |
| Physique thermique | Pas de convection dans le vide ; le rayonnement ($\varepsilon \sigma T^4$) est le seul mécanisme de rejet de la chaleur |
| Bilan thermique | $Q_{\text{in}} = Q_{\text{out}}$ ; résoudre $T = (Q/\varepsilon\sigma A)^{1/4}$ (nœud unique) ; modèle à plusieurs nœuds pour la conception réelle |
| Rapport $\alpha_s/\varepsilon$ | Rapport faible = surface froide (radiateur) ; rapport élevé = surface chaude (isolation) |
| Constitution du MLI | Enveloppe externe en Kapton VDA + 10–20 couches de DAM + intercalaires en Dacron ; $\varepsilon_{\text{eff}} = 0.01$–$0.03$ |
| Dimensionnement des réchauffeurs | $P_{\text{heater}} = \varepsilon\sigma A T_{\text{min}}^4 - Q_{\text{env}} - Q_{\text{int}}$ ; réchauffeurs souples en Kapton, régulation par thermostat |
| Marges thermiques | Convention du manuel : ±5 °C en fonctionnement, ±10 °C en recette, ±15 °C en qualification ; TVAC de protovol à la prévision ±10 °C (GSFC-STD-7000B §2.6) |
| Effets transitoires | L'inertie thermique ($mc_p$) empêche d'atteindre le régime permanent pendant les éclipses courtes ; un 1U à 400 km se refroidit de ~20–25 °C pendant une éclipse de 36 min |

## Exercices

1. **Dimensionnement du générateur.** Un CubeSat 3U d'observation de la Terre sur une orbite héliosynchrone à 550 km (calculez $T$, $t_{\text{sun}}$ et $t_{\text{ecl}}$ pour β = 0 à l'aide du chapitre 7) présente une demande de pointe en phase éclairée de 12 W et une charge en éclipse de 4 W. Dimensionnez le générateur solaire pour une mission de 4 ans avec des cellules à 70 °C et un angle solaire effectif de 25°, en détaillant les cinq étapes. Quelles surface et masse du générateur obtenez-vous ?

2. **Sensibilité au rendement de chaîne.** Reprenez l'exemple résolu d'EOSat-3U du §9.2 avec le rendement global $\eta_{\text{ecl}} = 0.90$ au lieu de 0,786, puis avec $\eta_{\text{sun}} = 1$ (aucune perte de régulateur en phase éclairée). De quel pourcentage la puissance requise en BOL varie-t-elle dans chaque cas ? Quelle hypothèse accepteriez-vous en phase A, et pourquoi ?

3. **Angle solaire et β.** Pour l'orbite d'EOSat-3U (LTAN 10 h 30 ; supposez β compris entre 20° et 30° au cours de l'année), comparez la valeur moyenne de $\cos\theta$ sur l'orbite (a) d'un panneau latéral dont la normale est perpendiculaire au plan orbital et (b) de la face zénith. Quel montage fournit le plus d'énergie par orbite, et comment la réponse change-t-elle pour une orbite aube-crépuscule (β ≈ 85°) ?

4. **Dimensionnement de la batterie et durée de vie en cycles.** Dimensionnez la batterie du satellite de l'exercice 1 pour une DoD de 20 % et de 35 %. Pour chacune, calculez le nombre de cycles d'éclipse sur 4 ans et comparez-le au tableau de durée de vie en cycles. Quelle DoD retiendriez-vous, et quelle masse de batterie implique-t-elle à 170 Wh/kg ?

5. **Bouclage sur l'orbite.** À l'aide du tableau des modes du chapitre 8 (tableau 8.4) et des rapports cycliques du §8.4.4, confirmez la demande moyenne sur l'orbite de 4,63 W. Calculez ensuite la puissance moyenne sur l'orbite effectivement fournie par le générateur du §9.2 (puissance en BOL × fraction éclairée × $\eta_{\text{sun}}$) et montrez si le bilan énergétique sur l'orbite se boucle en BOL et en EOL.

6. **Tri du cas chaud.** Refaites le calcul à un nœud du cas chaud du §9.4.11 pour un satellite dont la face zénith est une structure peinte en blanc ($\alpha_s = 0.30$ en EOL, $\varepsilon = 0.90$) au lieu de cellules solaires, le générateur étant reporté sur une aile déployable thermiquement découplée de la plateforme. Quelle température à un nœud obtenez-vous, et que vous apprend la comparaison sur l'emplacement du générateur du point de vue thermique ?

7. **Refroidissement transitoire.** Intégrez numériquement le refroidissement en éclipse du §9.4.11 (pas de temps de 2 minutes, en recalculant $Q_{\text{out}}$ à chaque pas) et comparez le résultat à l'estimation linéaire de 7,8 °C. Recommencez pour le cas du 1U UniSat-1 et comparez avec les 20–25 °C indiqués au §9.5.

8. **Dimensionnement d'un réchauffeur.** Un pack de batterie de 0,15 kg (chaleur massique effective $c_p = 1000$ J/kg/K) est enveloppé de MLI avec $\varepsilon_{\text{eff}} = 0.03$ et une surface rayonnante de 0,01 m², et il entre en éclipse à +15 °C. Estimez son refroidissement sur 36 minutes sans réchauffeur, et dimensionnez un réchauffeur régulé par thermostat qui le maintient au-dessus de 0 °C. Quelle fraction du bilan d'énergie en éclipse du §9.3 le réchauffeur consomme-t-il ?

9. **Marges de l'ECSS.** La plage de température prédite d'un senseur stellaire va de −18 °C à +48 °C et ses limites de fonctionnement de −30 °C à +60 °C. Vérifiez la marge de fonctionnement, indiquez les températures d'essai de recette et de qualification, et décidez si la conception est conforme. Si la limite de qualification de l'équipement est de +60 °C, que faut-il modifier ?

10. **Compromis pour UniSat-1.** Supposons qu'UniSat-1 ajoute un unique panneau déployable 1U (0,01 m², $\theta$ ≈ 30° en moyenne). Recalculez la puissance moyenne disponible sur l'orbite et la marge. Énumérez ensuite les trois nouvelles interfaces (chapitre 8, §8.3) et le nouveau mode de défaillance qu'introduit le panneau, et discutez de l'intérêt de ce 1 W supplémentaire pour une mission magnétométrique.

## Références

1. Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, chap. 11.4 (EPS), chap. 11.5 (thermique). https://www.space.com/smad
2. ECSS, *ECSS-E-ST-20C Rev.1: Electrical and Electronic*, 2019. https://ecss.nl/standard/ecss-e-st-20c-electrical-and-electronic/
3. ECSS, *ECSS-E-ST-31C: Thermal Control*, 2008 (réédition 2020). https://ecss.nl/standard/ecss-e-st-31c-thermal-control/
4. Patel, M. R., *Spacecraft Power Systems*, CRC Press, 2005, chap. 3–8. https://www.taylorfrancis.com/books/mono/10.1201/9781420038217/spacecraft-power-systems-mukund-patel
5. Gilmore, D. G. (dir.), *Spacecraft Thermal Control Handbook, Vol. 1: Fundamental Technologies*, 2e éd., Aerospace Press, 2002. https://arc.aiaa.org/doi/book/10.2514/4.104503
6. Gilmore, D. G. (dir.), *Spacecraft Thermal Control Handbook, Vol. 2: Cryogenics*, 2003. https://arc.aiaa.org/doi/book/10.2514/4.104515
7. Ratnakumar, B. V. et al., *Lithium-Ion Batteries for Space*, NASA JPL, 2003. https://trs.jpl.nasa.gov
8. Kopp, G. & Lean, J. L., « A new, lower value of total solar irradiance », *Geophys. Res. Lett.* 38, 2011. https://doi.org/10.1029/2010GL045777
9. Green, M. A. et al., « Solar cell efficiency tables (version 62) », *Progress in Photovoltaics* 31, 2023. https://doi.org/10.1002/pip.3726
10. Salas, J. et al., « SuperDove constellation », Small Satellite Conference, 2021. https://digitalcommons.usu.edu/smallsat/
11. Advanced Space, « CAPSTONE design overview », Small Satellite Conference, 2022. https://digitalcommons.usu.edu/smallsat/
