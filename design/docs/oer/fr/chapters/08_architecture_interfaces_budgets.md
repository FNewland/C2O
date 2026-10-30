# Chapitre 8 — Architecture de mission : segments, interfaces et bilans d'ingénierie

> **Lectures préalables conseillées.** NASA *Systems Engineering Handbook* §4.4 (*Design Solution Definition*) et §6.3 (*Interface Management*) ; ECSS-E-ST-10-24C (gestion des interfaces) ; ECSS-E-HB-10-02A §5.2 et ECSS-E-ST-10-02C (philosophie des marges) ; SMAD4 chap. 10–11. Ce chapitre suppose que les exigences (chapitre 5), les fonctions (chapitre 6) et une orbite (chapitre 7) ont été définies.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez en mesure de :

1. décomposer une mission spatiale en ses segments constitutifs (spatial, sol, lancement, utilisateur) ;
2. construire un schéma fonctionnel de l'architecture du système faisant apparaître les frontières des sous-systèmes ;
3. identifier et classer toutes les interfaces entre sous-systèmes à l'aide d'une matrice N², et détecter les conflits d'interface ;
4. rédiger des exigences d'interface formelles pour les paires de sous-systèmes critiques ;
5. construire un bilan de masse selon la politique de marges à deux niveaux de l'ECSS, ainsi qu'un bilan de puissance par mode ;
6. interpréter un ensemble d'indicateurs de bilan (marge par bilan, marge par mode) et décider si une conception est bouclée.

---

## 8.1 Décomposition de la mission en segments

*[Source : NASA SEH sect. 4.4 ; ECSS-E-ST-10C sect. 5.4 ; SMAD, chap. 1]*

Toute mission spatiale se décompose en segments, chacun doté de fonctions et d'interfaces propres. Le chapitre 4, §4.8.1, a présenté les segments au niveau du ConOps ; la présente section en constitue le traitement de référence. La figure 8.1 montre les quatre segments et les liens qui les relient.

<svg viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg" style="max-width:700px; font-family: sans-serif; font-size: 12px;">
  <!-- Space Segment -->
  <rect x="50" y="20" width="200" height="110" rx="8" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="150" y="45" text-anchor="middle" fill="#1e40af" font-weight="bold" font-size="14">Segment spatial</text>
  <text x="150" y="65" text-anchor="middle" fill="#1e40af" font-size="10">Plateforme</text>
  <text x="150" y="80" text-anchor="middle" fill="#1e40af" font-size="10">Instrument(s) de charge utile</text>
  <text x="150" y="95" text-anchor="middle" fill="#1e40af" font-size="10">Sous-systèmes (EPS, SCAO, TTC…)</text>
  <text x="150" y="110" text-anchor="middle" fill="#1e40af" font-size="10">Logiciel de vol</text>
  <!-- Ground Segment -->
  <rect x="300" y="170" width="200" height="110" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="400" y="195" text-anchor="middle" fill="#166534" font-weight="bold" font-size="14">Segment sol</text>
  <text x="400" y="215" text-anchor="middle" fill="#166534" font-size="10">Station(s) sol</text>
  <text x="400" y="230" text-anchor="middle" fill="#166534" font-size="10">Centre de contrôle de mission</text>
  <text x="400" y="245" text-anchor="middle" fill="#166534" font-size="10">Chaîne de traitement des données</text>
  <text x="400" y="260" text-anchor="middle" fill="#166534" font-size="10">Équipe d'opérations</text>
  <!-- Launch Segment -->
  <rect x="550" y="20" width="200" height="80" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="650" y="45" text-anchor="middle" fill="#92400e" font-weight="bold" font-size="14">Segment lancement</text>
  <text x="650" y="65" text-anchor="middle" fill="#92400e" font-size="10">Lanceur</text>
  <text x="650" y="80" text-anchor="middle" fill="#92400e" font-size="10">Déployeur (p. ex. ISIPOD)</text>
  <!-- User Segment -->
  <rect x="550" y="170" width="200" height="80" rx="8" fill="#fce7f3" stroke="#db2777" stroke-width="2"/>
  <text x="650" y="195" text-anchor="middle" fill="#9d174d" font-weight="bold" font-size="14">Segment utilisateur</text>
  <text x="650" y="215" text-anchor="middle" fill="#9d174d" font-size="10">Utilisateurs finaux</text>
  <text x="650" y="235" text-anchor="middle" fill="#9d174d" font-size="10">Produits de données / applications</text>
  <!-- RF link between space and ground -->
  <line x1="250" y1="100" x2="300" y2="200" stroke="#64748b" stroke-width="2" stroke-dasharray="6,3"/>
  <text x="260" y="155" fill="#64748b" font-size="10" transform="rotate(-35, 260, 155)">Liaison RF (TTC + données)</text>
  <!-- Launch to space -->
  <line x1="550" y1="60" x2="250" y2="60" stroke="#d97706" stroke-width="2"/>
  <text x="400" y="52" text-anchor="middle" fill="#d97706" font-size="10">Déploiement</text>
  <!-- Ground to user -->
  <line x1="500" y1="230" x2="550" y2="210" stroke="#64748b" stroke-width="1.5"/>
  <text x="530" y="215" fill="#64748b" font-size="10">Données</text>
</svg>

**Figure 8.1** — Les quatre segments de la mission et leurs principaux liens : le segment lancement déploie le segment spatial ; les segments spatial et sol échangent télémesures, télécommandes et données par liaison RF ; le segment sol livre les produits de données au segment utilisateur.

| Segment | Éléments | Interfaces principales |
|---------|----------|---------------|
| **Spatial** | Plateforme, charge utile, logiciel de vol | Vers le sol (RF), vers le lancement (mécanique/électrique) |
| **Sol** | Station sol, CCM, traitement des données | Vers l'espace (RF), vers l'utilisateur (réseau) |
| **Lancement** | Lanceur, déployeur, adaptateur | Vers l'espace (mécanique, inhibitions électriques) |
| **Utilisateur** | Utilisateurs finaux, applications, consommateurs de données | Vers le sol (produits de données) |

Le segment sol est conçu au chapitre 17 et exploité au chapitre 18 ; l'interface avec le lancement (déployeur, inhibitions, *CubeSat Design Specification*) est traitée avec la structure au chapitre 12.

---

## 8.2 Schéma fonctionnel de l'architecture du système

Le schéma fonctionnel du système montre l'architecture interne du segment spatial — tous les sous-systèmes et leurs liaisons de données, d'alimentation et mécaniques. La figure 8.2 présente l'architecture CubeSat de référence utilisée pour l'exemple fil rouge du CubeSat 3U d'observation de la Terre (EOSat-3U) tout au long des chapitres 9 à 12.

<svg viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" style="max-width:750px; font-family: sans-serif; font-size: 11px;">
  <!-- Central bus -->
  <rect x="300" y="200" width="200" height="60" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="400" y="225" text-anchor="middle" fill="#92400e" font-weight="bold">OBC / gestion des données</text>
  <text x="400" y="245" text-anchor="middle" fill="#92400e" font-size="10">Bus I2C / SPI / CAN</text>
  <!-- EPS -->
  <rect x="50" y="30" width="160" height="55" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="130" y="52" text-anchor="middle" fill="#1e40af" font-weight="bold">EPS</text>
  <text x="130" y="70" text-anchor="middle" fill="#1e40af" font-size="10">Gén. sol. + batt. + régul.</text>
  <!-- Power bus lines -->
  <line x1="130" y1="85" x2="130" y2="160" stroke="#dc2626" stroke-width="2"/>
  <line x1="50" y1="160" x2="750" y2="160" stroke="#dc2626" stroke-width="2"/>
  <text x="400" y="153" text-anchor="middle" fill="#dc2626" font-size="10" font-weight="bold">Bus d'alimentation (3,3 V / 5 V / batterie)</text>
  <!-- AOCS -->
  <rect x="50" y="310" width="160" height="55" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="130" y="332" text-anchor="middle" fill="#166534" font-weight="bold">SCAO</text>
  <text x="130" y="350" text-anchor="middle" fill="#166534" font-size="10">RW + MTQ + ST + SS</text>
  <line x1="210" y1="335" x2="300" y2="230" stroke="#64748b" stroke-width="1.5"/>
  <!-- Comms -->
  <rect x="590" y="310" width="160" height="55" rx="6" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
  <text x="670" y="332" text-anchor="middle" fill="#3730a3" font-weight="bold">Télécom (TTC)</text>
  <text x="670" y="350" text-anchor="middle" fill="#3730a3" font-size="10">Émetteur + récepteur + antenne</text>
  <line x1="590" y1="335" x2="500" y2="230" stroke="#64748b" stroke-width="1.5"/>
  <!-- Payload -->
  <rect x="590" y="30" width="160" height="55" rx="6" fill="#fce7f3" stroke="#db2777" stroke-width="2"/>
  <text x="670" y="52" text-anchor="middle" fill="#9d174d" font-weight="bold">Charge utile</text>
  <text x="670" y="70" text-anchor="middle" fill="#9d174d" font-size="10">Télescope / capteur</text>
  <line x1="590" y1="60" x2="500" y2="220" stroke="#64748b" stroke-width="1.5"/>
  <!-- Thermal -->
  <rect x="300" y="400" width="200" height="45" rx="6" fill="#fef9c3" stroke="#ca8a04" stroke-width="2"/>
  <text x="400" y="420" text-anchor="middle" fill="#854d0e" font-weight="bold">Thermique</text>
  <text x="400" y="437" text-anchor="middle" fill="#854d0e" font-size="10">Réchauffeurs + MLI + radiateurs</text>
  <line x1="400" y1="400" x2="400" y2="260" stroke="#64748b" stroke-width="1" stroke-dasharray="4,3"/>
  <!-- Structure (background) -->
  <rect x="30" y="10" width="740" height="470" rx="10" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="8,4"/>
  <text x="400" y="490" text-anchor="middle" fill="#94a3b8" font-size="12">Structure (primaire + secondaire)</text>
  <!-- Power taps -->
  <line x1="130" y1="160" x2="130" y2="310" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="670" y1="160" x2="670" y2="310" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="670" y1="85" x2="670" y2="160" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="400" y1="160" x2="400" y2="200" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
</svg>

**Figure 8.2** — Schéma fonctionnel du système d'un CubeSat de référence : l'OBC au centre du bus de données, l'EPS qui alimente chaque sous-système par un bus d'alimentation régulé, et la structure qui les enveloppe tous.

### 8.2.1 Rôle des sous-systèmes (référence CubeSat)

| Sous-système | Abréviation | Fonction principale | Fraction de masse typique |
|-----------|-------------|-----------------|----------------------|
| **Charge utile** | PL | Détection ou communication propre à la mission | 25–40 % |
| **Sous-système d'alimentation électrique** | EPS | Produire, stocker et distribuer l'énergie électrique | 15–25 % |
| **Contrôle d'attitude et d'orbite** | AOCS | Déterminer et contrôler l'attitude ; connaissance de l'orbite | 8–15 % |
| **Télécommunications (TTC)** | LINK / TTC | Liaison descendante de télémesure, liaison montante de télécommande, liaison descendante des données | 5–10 % |
| **Calculateur de bord** | OBC / C&DH | Exécution des commandes, gestion des données, logiciel de vol | 2–5 % |
| **Contrôle thermique** | TCS | Maintenir tous les composants dans leurs limites de température | 1–5 % |
| **Structure** | STR | Soutien mécanique, cheminement des charges du lancement, conformité au CDS | 15–25 % |
| **Propulsion** | PROP | Manœuvres orbitales, désorbitation (si nécessaire) | 0–15 % |
| **Harnais** | HAR | Interconnexions électriques | 3–7 % |

---

## 8.3 La matrice d'interfaces N²

*[Source : NASA SEH sect. 6.3 — Process 12: Interface Management ; ECSS-E-ST-10-24C]*

Les problèmes d'interface sont la première cause d'échec à l'intégration. Selon le NASA SEH, « la plupart des défaillances des systèmes trouvent leur origine dans des problèmes d'interface ». La matrice N², popularisée par la pratique de la conception concourante à la NASA et à l'ESA, est l'outil de référence pour débusquer chaque interface avant qu'elle ne vous prenne au dépourvu. Cette section constitue le traitement de référence du manuel ; le chapitre 15 revient sur les interfaces en tant que source de risque.

### 8.3.1 Structure de la matrice N²

Pour un système de $N$ sous-systèmes, la matrice N² est une grille $N \times N$ dans laquelle :

- les **cellules diagonales** contiennent les noms des sous-systèmes (EPS, SCAO, télécom, thermique, structure, propulsion, OBC, charge utile) ;
- les **cellules hors diagonale** contiennent les interfaces entre sous-systèmes ;
- la **cellule $(i, j)$** = ce que le sous-système $i$ fournit AU sous-système $j$ (lecture en ligne) ;
- la **cellule $(j, i)$** = ce que le sous-système $j$ fournit AU sous-système $i$ (lecture en colonne).

Pour 8 sous-systèmes, on compte $8 \times 7 / 2 = 28$ paires d'interfaces potentielles (56 cellules orientées). Un CubeSat typique compte 18 à 22 paires actives.

### 8.3.2 Un exemple à six sous-systèmes

Le tableau ci-dessous est une matrice N² complète pour un CubeSat à six sous-systèmes. Chaque cellule se lit « ce que le sous-système de la ligne fournit au sous-système de la colonne ».

| DE ↓ / VERS → | EPS | OBC | SCAO | TTC | Charge utile | Structure |
|---|---|---|---|---|---|---|
| **EPS** | *[EPS]* | Bus 28 V ; 5 V régulé ; HK I²C | Bus 28 V ; 5 V régulé ; HK I²C | Bus 28 V ; 5 V régulé ; HK I²C | Bus 28 V ; 5 V régulé ; HK I²C | Boulons de fixation |
| **OBC** | Commandes d'alimentation ; télémesure | *[OBC]* | Commandes (I²C/SPI) | Données TC (UART) | Commandes (SPI/UART) | — |
| **SCAO** | Demande d'alimentation | Données d'attitude ; HK du SCAO | *[SCAO]* | Attitude pour le pointage de l'antenne | Données d'attitude pour le pointage | Fixation ; vibrations |
| **TTC** | Demande d'alimentation | Données reçues ; transfert des commandes | — | *[TTC]* | — | Fixation de l'antenne |
| **Charge utile** | Demande d'alimentation | Données scientifiques ; HK de la charge utile | Demande de pointage | — | *[Charge utile]* | Dégagement du champ de vue |
| **Structure** | — | — | Fixation des capteurs | Fixation de l'antenne | Fixation de la charge utile | *[Structure]* |

**Tableau 8.1** — Matrice N² d'un CubeSat à six sous-systèmes. Ligne = source, colonne = destination.

### 8.3.3 Types d'interfaces

Chaque entrée de la matrice est étiquetée par un ou plusieurs types d'interfaces. Les codes à une lettre ci-dessous sont utilisés dans tout le manuel (le chapitre 15 emploie les mêmes codes dans le registre des risques d'interface).

| Type | Code | Description | Exemples |
|------|------|-------------|----------|
| **Mécanique** | M | Fixation physique, charges, tolérances d'alignement, tresses thermiques, pions d'alignement | Fixation de la charge utile sur une face de la structure |
| **Électrique / alimentation** | E | Connexions d'alimentation, tension du bus, lignes commutées | Bus 28 V, 5 V régulé, lignes commutées vers tous les sous-systèmes |
| **Thermique** | T | Chemins de transfert de chaleur, couplages conductif et radiatif | Chaleur dissipée par le transpondeur vers le panneau radiateur |
| **Données** | D | Bus numérique (I²C, SPI, UART, CAN, RS-422) | Commandes de l'OBC vers le contrôleur SCAO |
| **RF** | R | Chemins RF intentionnels (câble coaxial, guide d'ondes) et couplage électromagnétique | Couplage des émissions de l'émetteur dans le récepteur de la charge utile |
| **Optique** | O | Chemins lumineux, dégagement du champ de vue, lumière parasite | Dégagement du champ de vue du senseur stellaire par rapport au générateur solaire |
| **Logiciel** | S | Interfaces de commande, définitions des paquets de télémesure, transitions de mode | Dictionnaire des commandes OBC-SCAO |

**Tableau 8.2** — Codes des types d'interfaces utilisés dans tout le manuel.

La figure 8.3 montre une matrice N² en couleurs pour un CubeSat 6U à huit sous-systèmes utilisant ces codes. On remarque que la ligne Alimentation est presque entièrement de type E (chaque sous-système consomme de la puissance), que la ligne et la colonne Données/OBC sont majoritairement de type D, et que les rares entrées M, T, R et O sont celles que l'on risque le plus d'oublier.

![Matrice d'interfaces N² d'un CubeSat 6U.](../assets/figures/fig_n2_matrix.png)

**Figure 8.3** — Matrice d'interfaces N² illustrative d'un CubeSat 6U à huit sous-systèmes, colorée selon le type d'interface (M mécanique, E électrique, T thermique, D données, R RF, O optique, S logiciel — tableau 8.2). Les cellules diagonales nomment les sous-systèmes ; les cellules hors diagonale se lisent ligne → colonne.

### 8.3.4 Préoccupations courantes aux interfaces d'un CubeSat

| Paire d'interfaces | Types | Préoccupation principale |
|----------------|-------|-------------|
| EPS ↔ SCAO | E | Compatibilité de la tension du bus ; appel de puissance crête des roues de réaction |
| EPS ↔ télécom | E | Demande de puissance crête de l'émetteur (~6–10 W) ; affectation des lignes commutées |
| EPS ↔ thermique | E, T | Couplage thermique du générateur solaire ; concurrence entre surfaces de radiateur et de générateur solaire sur les faces externes |
| EPS ↔ charge utile | E | Commutation de la puissance crête ; coordination des rapports cycliques |
| Structure ↔ SCAO | M | Alignement du montage des roues de réaction et du senseur stellaire ; isolation vibratoire |
| Structure ↔ charge utile | M, O | Stabilité d'alignement de la charge utile ; dégagement du champ de vue optique |
| OBC ↔ SCAO | D, S | Données d'attitude pour le pointage de la charge utile ; commandes de transition de mode |
| OBC ↔ télécom | D, S | Routage des paquets de télémesure ; distribution des télécommandes |
| OBC ↔ charge utile | D, S | Déclenchement de l'acquisition des données scientifiques ; commande de l'instrument |
| Télécom ↔ charge utile | R | **CEM :** émissions conduites/rayonnées de l'émetteur face à la sensibilité du récepteur de la charge utile |
| Télécom ↔ SCAO | R, O | Diagramme de rayonnement de l'antenne face au champ de vue du senseur stellaire ; coordination du pointage de l'antenne |
| Thermique ↔ charge utile | T | Besoin de refroidissement du détecteur ; limites de température de fonctionnement |
| SCAO ↔ charge utile | M | Microvibrations des roues de réaction face à la stabilité de pointage de la charge utile (gigue) |

### 8.3.5 Détection et résolution des conflits

Un **conflit d'interface** existe lorsque deux sous-systèmes ont des attentes incompatibles à leur frontière commune. Cas typiques :

- le sous-système A s'attend à fournir du 28 V, mais le sous-système B n'accepte que du 5 V (E) ;
- le sous-système A utilise l'I²C, mais le sous-système B ne dispose que du SPI ou du RS-422 (D) ;
- le sous-système A émet en bande S, mais l'antenne du sous-système B est en bande X (R) ;
- le sous-système A se monte sur la face +Z, mais la structure ne prévoit aucune fixation sur +Z (M).

Nombre de ces vérifications sont mécaniques — comparer les deux côtés de chaque cellule en tension, protocole, bande et emplacement — et un outil de conception concourante doté d'un moteur de contraintes les signale automatiquement à mesure que les équipements sont choisis. Les autres relèvent du jugement de l'ingénieur, et c'est là que la classification par gravité est utile.

**Classification par gravité :**

| Gravité | Description | Exemple | Action requise |
|----------|-------------|---------|----------------|
| **Critique** | La conception ne peut pas être bouclée sans résolution | CEM : le rayonnement de l'émetteur empêche le fonctionnement de la charge utile | À résoudre avant la PDR |
| **Majeur** | Incidence notable sur les marges de conception | La surface de radiateur entre en concurrence avec celle du générateur solaire | Plan de réduction exigé à la PDR |
| **Mineur** | Gérable par un ajustement mineur | Champ de vue du senseur stellaire partiellement masqué par l'antenne repliée | Analyse d'aménagement |

**Options de résolution :**

1. **Déplacer :** déplacer un composant pour éviter le conflit (p. ex. placer le senseur stellaire sur une autre face) ;
2. **Blinder/isoler :** ajouter un blindage CEM, des isolateurs de vibrations, une isolation thermique ;
3. **Partager dans le temps :** programmer les activités en conflit pour éviter leur simultanéité (p. ex. pas d'émission pendant la prise de vue) ;
4. **Accepter le risque :** consigner le risque résiduel et son incidence sur les marges dans le registre des risques (chapitre 15).

> **Exemple résolu — détection d'un conflit de protocole de données**
>
> *Problème :* l'OBC envoie ses commandes aux roues de réaction par I²C. L'ensemble de roues de réaction retenu (un Blue Canyon RWP100 — exemple représentatif, et non une recommandation) utilise le RS-422. La cellule (OBC → SCAO) de la matrice N² indique donc « commandes, I²C » d'un côté de la frontière et « commandes, RS-422 » de l'autre : c'est un conflit d'interface de type D.
>
> *Options de résolution :*
> 1. choisir une autre roue de réaction compatible I²C ;
> 2. ajouter un pont I²C/RS-422 (composant supplémentaire, avec sa masse, son coût et son point de défaillance) ;
> 3. choisir un autre OBC compatible RS-422.
>
> *Gravité :* majeure — la conception peut être bouclée avec l'option 2, mais au prix de la masse, du harnais et de la fiabilité. Le conflit est consigné dans le registre des interfaces avec sa résolution et son responsable, et la résolution devient une exigence d'interface (voir ci-dessous). Dans un outil de conception concourante disposant des données de protocole au niveau des équipements, ce conflit apparaît sous forme d'avertissement dès que la roue est sélectionnée.

### 8.3.6 Rédaction des exigences d'interface

Pour chaque interface importante, rédigez des exigences formelles sous la forme « doit » du chapitre 5 :

**Exemple — EPS ↔ tous les sous-systèmes :**
```
IR-PWR-001 : « L'EPS doit fournir à tous les sous-systèmes des tensions de bus
              régulées de 3.3 V ± 0.1 V et 5.0 V ± 0.25 V. »
IR-PWR-002 : « Aucun sous-système ne doit dépasser la puissance qui lui est
              allouée sans coordination avec l'EPS. »
```

**Exemple — télécom ↔ charge utile (CEM) :**
```
IR-EMC-001 : « Les émissions conduites de l'émetteur (TX) doivent rester sous −60 dBm
              dans la bande du récepteur charge utile (1.5–1.6 GHz) en mode prise de vue. »
IR-EMC-002 : « L'émission (TX) et l'acquisition charge utile ne doivent pas fonctionner
              simultanément, sauf si IR-EMC-001 est vérifiée par essai. »
```

**Exemple — OBC ↔ SCAO (données), tiré de l'exemple résolu :**
```
IR-DAT-003 : « L'OBC doit commander l'ensemble de roues de réaction par une liaison
              RS-422 à 115.2 kbit/s via le pont I²C/RS-422 ; le pont doit être
              alimenté par la ligne commutée AOCS. »
```

---

## 8.4 Bilans d'ingénierie : masse et puissance

*[Source : ECSS-E-HB-10-02A sect. 5.2 ; ECSS-E-ST-10-02C ; SMAD, chap. 10–11]*

Les bilans d'ingénierie constituent l'ossature quantitative de la conception. Ils répondent à la question : **« Cette conception est-elle bouclée ? »**

### 8.4.1 Bilan de masse

> **Équations clés — bilan de masse**
>
> **Marge de masse :**
> $$\text{Marge}_{\%} = \frac{M_{\text{allocation}} - M_{\text{MEV}}}{M_{\text{allocation}}} \times 100\,\%$$
>
> où MEV = valeur maximale attendue (*Maximum Expected Value*) = CBE + marges de maturité (au niveau des équipements), à laquelle s'ajoute la marge au niveau système avant comparaison avec l'allocation.
>
> **Seuils d'état :** vert : > 20 % | orange : 10–20 % | rouge : < 10 % | dépassement : < 0 %

| Terme | Définition |
|------|-----------|
| **CBE** (meilleure estimation actuelle, *Current Best Estimate*) | Meilleure estimation de la masse réelle compte tenu des connaissances actuelles |
| **MEV** (valeur maximale attendue, *Maximum Expected Value*) | CBE + marge de maturité des équipements = masse attendue dans le cas le plus défavorable |
| **Marge de maturité des équipements** | Appliquée composant par composant selon la maturité de la conception (TRL / héritage en vol) |
| **Marge système** | Appliquée au niveau système, à titre de réserve de gestion, et décroissante au fil des phases du projet |

### 8.4.2 La politique de marges de l'ECSS — deux niveaux

La philosophie des marges de l'ECSS comporte **deux niveaux**, qui doivent tous deux être appliqués. D'abord, chaque équipement porte une **marge de maturité** qui dépend du degré de connaissance de sa masse ; ensuite, le projet porte une **marge au niveau système** sur la somme des MEV, qui dépend de la phase du cycle de vie (chapitre 1, §1.4). Le tableau 8.3 est l'énoncé unique de la politique utilisée dans tout le manuel ; la partie IV et les chapitres suivants y renvoient plutôt que de répéter les valeurs.

| Niveau | Base | Marge |
|-------|-------|--------|
| **Maturité des équipements** | Sur étagère, ayant volé, sans modification | 5 % |
| | Sur étagère avec modification mineure | 10 % |
| | Nouvelle conception ou modification majeure | 20 % |
| **Niveau système, par phase** | Phase 0 / A (concept, faisabilité) | 20 % |
| | Phase B (définition préliminaire) | 15 % |
| | Phase C (définition détaillée) | 10 % |
| | Phase D (qualification et production) | 5 % |

**Tableau 8.3** — Barème de référence des marges de masse de l'ECSS : marges de maturité des équipements (appliquées article par article pour obtenir la MEV) plus une marge au niveau système selon la phase (appliquée à la somme des MEV). Source : ECSS-E-HB-10-02A §5.2 et philosophie des marges de l'ECSS-E-ST-10-02C.

Les deux niveaux se cumulent. Pour une conception de phase A dans laquelle la plupart des équipements sont nouveaux (marge de maturité de 20 %), la provision totale au-dessus de la CBE est de $1.20 \times 1.20 - 1 \approx 44\,\%$ ; en phase C, avec des équipements en grande partie éprouvés en vol, elle tombe à environ $1.05 \times 1.10 - 1 \approx 16\,\%$, et en phase D, lorsque les masses sont mesurées, à environ 5 %. La figure 8.4 montre cette enveloppe qui se resserre, à côté d'une répartition typique de la masse à sec.

![Répartition de la masse et politique de marges de l'ECSS par phase.](../assets/figures/fig_mass_budget.png)

**Figure 8.4** — À gauche : répartition typique de la masse à sec d'un engin spatial de la classe CubeSat de 8,5 kg (la structure, l'alimentation et la charge utile dominent). À droite : l'enveloppe des marges cumulées équipement + système selon la phase, qui montre comment la provision au-dessus de la CBE se réduit à mesure que la conception mûrit (tableau 8.3).

> **Exemple résolu — bilan de masse d'EOSat-3U (phase A)**
>
> Tous les équipements sont traités comme de nouvelles conceptions (marge de maturité de 20 %) ; marge système de 20 % (phase A).
>
> | Sous-système | CBE (kg) | Marge équip. (20 %) | MEV (kg) |
> |-----------|---------|---------------------|---------|
> | Charge utile | 1,50 | 0,30 | 1,80 |
> | EPS | 0,75 | 0,15 | 0,90 |
> | SCAO | 0,55 | 0,11 | 0,66 |
> | Télécom (TTC) | 0,25 | 0,05 | 0,30 |
> | OBC | 0,08 | 0,02 | 0,10 |
> | Thermique | 0,05 | 0,01 | 0,06 |
> | Structure | 0,35 | 0,07 | 0,42 |
> | Harnais | 0,15 | 0,03 | 0,18 |
> | **Total à sec** | **3,68** | | **4,42** |
> | Marge système (20 %) | | | **0,88** |
> | **MEV à sec + marge système** | | | **5,30** |
> | Ergols | | | 0,00 |
> | **Masse humide** | | | **5,30** |
> | **Allocation lanceur** | | | **6,00** (limite 3U) |
> | **Marge de masse** | | | **0,70 kg (11,7 %)** — orange |
>
> La CBE de 3,68 kg est l'estimation paramétrique que le chapitre 12 remplacera par une liste d'équipements ascendante.

### 8.4.3 Bilan de puissance par mode

Le bilan de puissance est calculé **mode opérationnel par mode opérationnel**, car tous les sous-systèmes ne consomment pas simultanément. Les modes sont ceux du ConOps (chapitre 4, §4.8.3 ; le tableau complet des modes, avec leurs transitions et les déclencheurs FDIR, figure au chapitre 18). Le tableau ci-dessous détaille la consommation par sous-système d'EOSat-3U ; ses totaux (survie 2 W, nominal 4 W, prise de vue 8 W, liaison descendante 10 W) sont les valeurs utilisées aux chapitres 4, 9 et 18.

| Sous-système | Survie (W) | Nominal (W) | Prise de vue (W) | Liaison descendante (W) | Éclipse (W) |
|-----------|---------|---------|-------------|-------------|-------------|
| OBC | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| SCAO | 0,3 | 1,5 | 2,5 | 2,0 | 1,5 |
| Charge utile | 0 | 0 | 3,5 | 0 | 0 |
| Télécom (récepteur toujours actif ; émetteur en liaison descendante) | 0,2 | 0,5 | 0,5 | 6,0 | 0,5 |
| Thermique (réchauffeurs) | 0,5 | 1,0 | 0,5 | 1,0 | 0,5 |
| **Total** | **2,0** | **4,0** | **8,0** | **10,0** | **3,5** |

**Tableau 8.4** — Bilan de puissance par mode d'EOSat-3U. La colonne éclipse correspond au mode nominal avec les charges thermiques et SCAO de l'arc d'éclipse ; c'est la $P_{\text{ecl}}$ utilisée pour le dimensionnement de la batterie au chapitre 9.

### 8.4.4 Puissance moyenne sur l'orbite

> **Équation clé — puissance moyenne sur l'orbite**
>
> $$P_{\text{avg}} = \sum_{\text{modes}} \left(P_{\text{mode}} \times \text{duty}_{\text{mode}}\right)$$
>
> **Exemple pour l'orbite de 94,6 min à 500 km du chapitre 7 (58,8 min d'ensoleillement, 35,8 min d'éclipse) :**
>
> | Mode | Puissance (W) | Rapport cyclique (%) | Contribution (W) |
> |------|----------|----------|-------------------|
> | Nominal (phase éclairée) | 4,0 | 45 % | 1,80 |
> | Prise de vue | 8,0 | 10 % | 0,80 |
> | Liaison descendante | 10,0 | 7 % | 0,70 |
> | Éclipse | 3,5 | 38 % | 1,33 |
> | **Total** | | **100 %** | **4,63 W** |

La demande moyenne sur l'orbite est ce que le générateur solaire doit fournir en moyenne ; le mode éclairé de pointe (10 W) et la charge en éclipse (3,5 W) dimensionnent respectivement le générateur et la batterie (chapitre 9, §9.2–§9.3).

### 8.4.5 Autres types de bilans (aperçu)

Chacun des bilans restants est développé dans son propre chapitre :

| Bilan | Équation clé | Chapitre |
|--------|-------------|---------|
| **Liaison** | $\text{Marge} = \text{PIRE} - \text{FSPL} + G/T - k - 10\log_{10}(R_b) - E_b/N_0$ | 11 |
| **Pointage** | $\theta_{\text{total}} = \sqrt{\sum \theta_i^2}$ (somme quadratique, RSS) | 10 |
| **ΔV** | $\Delta V = I_{sp} \cdot g_0 \cdot \ln(m_0/m_f)$ (Tsiolkovski) | 12 |
| **Données** | Capacité de transmission quotidienne vers le sol ≥ volume produit quotidien | 11 |

---

## 8.5 Exemple résolu : architecture d'UniSat-1

Retour sur UniSat-1, le démonstrateur 1U du chapitre 1, §1.7 : il montre qu'un CubeSat 1U peut être réalisé avec une architecture radicalement simplifiée par rapport à la mission 3U d'observation de la Terre. Plusieurs sous-systèmes disparaissent entièrement.

| Sous-système | EOSat-3U | UniSat-1 (1U) | Justification de la suppression |
|-----------|--------------|---------------|--------------------------|
| **EPS** | Nécessaire | **Nécessaire** | Toujours indispensable |
| **OBC** | Nécessaire | **Nécessaire** | Toujours indispensable (minimal : classe MSP430 ou ARM Cortex-M) |
| **Télécom** | Bande S + bande X | **UHF seule** | 9600 bit/s suffisent pour des données de charge utile < 1 kbit/s |
| **Structure** | Nécessaire | **Nécessaire** | Toujours indispensable (cadre 1U COTS) |
| **Charge utile** | Télescope (complexe) | **Magnétomètre MEMS** (simple : 50 g, 0,2 W) | — |
| **SCAO** | Senseur stellaire + roues de réaction + magnétocoupleurs | **Supprimé** | Stabilisation magnétique passive uniquement (aimant permanent + barreaux d'hystérésis, traités comme de la structure et non comme un sous-système) |
| **Thermique** | MLI + réchauffeurs | **Supprimé** | Revêtements passifs uniquement ; l'environnement thermique LEO à 400 km est clément pour une mission de 6 mois |
| **Propulsion** | Parfois nécessaire | **Supprimée** | L'orbite à 400 km décroît naturellement en moins d'un an (chapitre 7, §7.7) ; aucun maintien d'orbite nécessaire |
| **Harnais** | Important | **Minimal** | Seulement 3–4 connexions carte à carte via l'empilement PC/104 |

**Matrice N² — considérablement réduite :** pour UniSat-1, la matrice d'interfaces passe de 28 paires potentielles (8 sous-systèmes) à seulement 10 paires (5 sous-systèmes). Les interfaces actives sont :

| Paire d'interfaces | Types | Préoccupation principale |
|----------------|-------|-------------|
| EPS ↔ OBC | E, D | Régulation de puissance, télémesure de servitude |
| EPS ↔ télécom | E | Puissance crête de l'émetteur (~0,5 W — faible au regard du bilan) |
| EPS ↔ charge utile | E | Commutation de la charge utile (0,2 W — négligeable) |
| OBC ↔ télécom | D, S | Routage des paquets TM/TC |
| OBC ↔ charge utile | D | Acquisition des données du magnétomètre (I²C ou SPI) |
| Structure ↔ tous | M | Fixation, conformité des rails au CDS |

**Bilan de masse (phase A) :**

| Sous-système | CBE (g) | Marge équip. (20 %) | MEV (g) |
|-----------|---------|---------------------|---------|
| Charge utile (magnétomètre MEMS) | 50 | 10 | 60 |
| EPS (carte + batterie + cellules fixées sur la structure) | 250 | 50 | 300 |
| OBC (carte MSP430/Cortex-M) | 30 | 6 | 36 |
| Télécom (émetteur-récepteur UHF + antenne) | 80 | 16 | 96 |
| Structure (cadre 1U) | 200 | 40 | 240 |
| SCAO magnétique passif (aimant + barreaux) | 30 | 6 | 36 |
| Harnais | 50 | 10 | 60 |
| **Total à sec** | **690** | | **828** |
| Marge système (20 %) | | | **166** |
| **MEV à sec + marge système** | | | **994** |
| **Allocation CDS** | | | **1330** |
| **Marge de masse** | | | **336 g (25,3 %)** — vert |

**Bilan de puissance (tous les modes utilisent le même rapport cyclique simple) :**

| Mode | Puissance (W) | Rapport cyclique (%) | Contribution (W) |
|------|----------|----------|-------------------|
| Veille (OBC + balise) | 0,7 | 50 % | 0,35 |
| Science (+ magnétomètre) | 0,9 | 10 % | 0,09 |
| Liaison descendante (+ émetteur UHF) | 1,2 | 5 % | 0,06 |
| Éclipse (OBC seul) | 0,5 | 35 % | 0,18 |
| **Moyenne sur l'orbite** | | **100 %** | **0,68 W** |

Avec ~2 W disponibles grâce aux cellules fixées sur la structure, la marge de puissance est confortable (~1,3 W, soit 66 %). C'est l'un des luxes que permet une charge utile simple sur une plateforme 1U.

**Idée essentielle sur l'architecture :** l'architecture d'UniSat-1 est si simple qu'une petite équipe (3 à 5 personnes) peut la concevoir, la construire, l'essayer et l'exploiter. Elle est donc idéale pour un programme universitaire ou pédagogique. Le processus de conception concourante s'applique toujours — mais les boucles de conception sont plus courtes et l'espace des compromis plus restreint.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Segments de la mission | Spatial, sol, lancement, utilisateur — chacun avec des interfaces définies |
| Architecture du système | Le schéma fonctionnel montre les sous-systèmes, les bus de données et la distribution de puissance |
| Matrice N² | Recense les 28 paires d'interfaces potentielles ; 7 types (M, E, T, D, R, O, S) ; lecture ligne → colonne |
| Conflits d'interface | Détectés en comparant les deux côtés de chaque cellule ; gravité (critique/majeur/mineur) ; 4 options de résolution |
| Exigences d'interface | Accords formels aux frontières ; doivent être vérifiables |
| Bilan de masse | CBE + marge de maturité des équipements = MEV ; + marge système ; comparaison avec l'allocation |
| Marges de l'ECSS | Deux niveaux : équipements 5/10/20 % selon la maturité ; système 20/15/10/5 % selon la phase (tableau 8.3) |
| Bilan de puissance | Par mode ; les rapports cycliques donnent la moyenne sur l'orbite ; le générateur solaire doit couvrir la pointe + la recharge |
| Bouclage des bilans | Marge négative = conception non bouclée ; réduire la demande ou augmenter l'allocation |

## Exercices

1. **Segments et interfaces.** Pour un CubeSat 3U d'observation de la Terre qui livre des images à des utilisateurs agricoles par l'intermédiaire d'un réseau commercial de stations sol, énumérez chaque segment, les éléments de chacun et l'interface entre chaque paire de segments avec son code de type (tableau 8.2). Quelle interface entre segments est régie par un document que l'équipe de mission ne maîtrise pas ?

2. **Construire une matrice N².** Construisez la matrice N² complète 8 × 8 de l'architecture de référence de la figure 8.2 (charge utile, EPS, SCAO, télécom, OBC, thermique, structure, harnais). Renseignez chaque cellule active avec l'élément fourni et son ou ses codes de type. Comptez les paires actives et comparez-les à la plage typique de 18 à 22.

3. **Détection des conflits.** Dans votre matrice de l'exercice 2, introduisez trois conflits : une incompatibilité de tension, une incompatibilité de protocole et une obstruction de champ de vue. Pour chacun, classez la gravité, choisissez une option de résolution et rédigez l'exigence d'interface qui consigne la résolution.

4. **Interface CEM.** L'émetteur télécom rayonne 2 W à 2,2 GHz et la charge utile comporte un récepteur GNSS à 1,575 GHz. Expliquez pourquoi il s'agit d'un conflit de type R bien que les fréquences diffèrent, proposez deux options de résolution tirées du §8.3.5 et rédigez une exigence d'interface vérifiable pour celle que vous retenez.

5. **Bilan de masse par phase.** Reprenez les valeurs de CBE d'EOSat-3U du §8.4.2 et recalculez la marge de masse par rapport à une allocation de 6,0 kg pour la phase B (en supposant que la charge utile et le SCAO sont désormais des produits sur étagère avec modification mineure, et le reste de nouvelles conceptions) et pour la phase C (tous les équipements sur étagère, sans modification). À quelle phase le bilan passe-t-il au vert ?

6. **Sensibilité à l'allocation.** Le fournisseur de lancement réduit l'allocation 3U de 6,0 kg à 5,5 kg. À partir du bilan de phase A du §8.4.2, calculez la nouvelle marge et l'état correspondant. Identifiez les deux sous-systèmes dont la réduction de CBE rétablirait le plus rapidement une marge de 10 %, et indiquez la masse que chacun doit perdre.

7. **Puissance par mode.** À l'aide du tableau 8.4, calculez la puissance moyenne sur l'orbite pour une orbite de type ISS de 92,6 min (36 min d'éclipse) dans laquelle la prise de vue occupe 15 % et la liaison descendante 5 % de l'orbite. Refaites ensuite le calcul pour une orbite héliosynchrone aube-crépuscule sans éclipse. De combien la demande moyenne varie-t-elle, et quelles lignes de sous-systèmes sont concernées ?

8. **Interfaces d'UniSat-1.** Rédigez la matrice N² complète 5 × 5 d'UniSat-1 (§8.5), y compris la ligne et la colonne Structure, et étiquetez chaque cellule avec ses codes de type. Identifiez l'unique interface que vous vérifieriez par essai plutôt que par inspection, et justifiez votre choix.

9. **Tension des bilans.** Une conception présente une marge de masse de 12 %, une marge de puissance en mode prise de vue de 4 %, une marge de liaison de 6 dB et une marge de pointage de 60 %. Quel bilan est le plus tendu, quelle modification de conception unique l'améliorerait le plus, et quels autres bilans cette modification affecterait-elle (suivez le couplage à travers la matrice N²) ?

## Références

1. NASA, *Systems Engineering Handbook* (NASA/SP-2016-6105 Rev 2), 2016, §4.4 (Process 4) et §6.3 (Process 12: Interface Management). https://www.nasa.gov/reference/systems-engineering-handbook/
2. ECSS, *ECSS-E-ST-10-24C: Interface Management*, 2015. https://ecss.nl/standard/ecss-e-st-10-24c-interface-management/
3. ECSS, *ECSS-E-HB-10-02A: Verification Guidelines*, 2010, §5.2 (Mass Margins). https://ecss.nl/hbstms/ecss-e-hb-10-02a-verification-guidelines/
4. ECSS, *ECSS-E-ST-10-02C Rev.1: Verification*, 2018. https://ecss.nl/standard/ecss-e-st-10-02c-rev-1-verification-1-february-2018/
5. Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, chap. 10–11. https://www.space.com/smad
6. ECSS, *ECSS-E-ST-20C Rev.1: Electrical and Electronic*, 2019 (bilans de puissance). https://ecss.nl/standard/ecss-e-st-20c-electrical-and-electronic/
7. ECSS, *ECSS-E-ST-10C Rev.1: System Engineering General Requirements*, 2017, §5.4. https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/
