# Chapitre 3 — Normes internationales pour les systèmes spatiaux

> **Lectures préalables conseillées.** ECSS-S-ST-00C (description du système ECSS) ; NASA *Systems Engineering Handbook* §6.5 ; la *CubeSat Design Specification* Rev 14 ; les *IADC Space Debris Mitigation Guidelines*. Ce chapitre s'appuie sur le cadre d'ingénierie système du chapitre 1 et sur le contexte réglementaire canadien du chapitre 2.

## Objectifs d'apprentissage

À l'issue de ce chapitre, vous serez capable de :

1. Décrire le système de normes ECSS et sa structure hiérarchique (management, ingénierie, assurance produit, durabilité)
2. Comparer les normes ECSS et NASA et en identifier les équivalences
3. Expliquer la norme d'interface CDS Rev 14 et son rôle dans l'intégration au lanceur
4. Appliquer à la conception de mission les lignes directrices relatives à l'atténuation des débris spatiaux (IADC, ISO 24113, règle des 5 ans de la FCC)
5. Décrire le rôle du CUPEEA et le cadre du Traité sur l'espace extra-atmosphérique
6. Mettre en place le suivi de la conformité d'une mission de petit engin spatial et identifier les vérifications qui peuvent être automatisées

---

## 3.1 Pourquoi les normes sont importantes en ingénierie spatiale

### 3.1.1 Le coût de la non-conformité

Les missions spatiales se déroulent dans un environnement où les défaillances sont catastrophiques, où la réparation est impossible et où les conséquences des brouillages ou des débris touchent tous les utilisateurs de l'espace. Les normes existent pour :

1. **Garantir la sécurité et la fiabilité des missions** — en codifiant le retour d'expérience de plusieurs décennies d'opérations spatiales
2. **Permettre l'interopérabilité** — en définissant des interfaces, des formats de données et des protocoles communs
3. **Réduire les coûts** — en fournissant des démarches de conception éprouvées au lieu de réinventer des solutions
4. **Satisfaire aux exigences réglementaires** — en démontrant le respect des obligations nationales et internationales
5. **Faciliter le transfert de technologie** — en établissant un langage d'ingénierie commun

> **Pratique industrielle.** La perte de Mars Climate Orbiter (1999) est l'exemple canonique de ce qui arrive en l'absence de normes d'interface rigoureuses. Le logiciel sol de Lockheed Martin produisait des données de poussée des propulseurs en livres-force seconde, alors que le logiciel de navigation de la NASA attendait des newtons-seconde. La sonde est entrée dans l'atmosphère martienne à 57 km d'altitude au lieu des 226 km prévus et a été détruite. Perte totale : 327,6 M$. Cet échec a directement conduit la NASA à renforcer le processus 12 (gestion des interfaces) de la NPR 7123.1D. La leçon : les normes et la maîtrise des interfaces ne sont pas une surcharge bureaucratique — elles sont critiques pour la mission.

### 3.1.2 Les grands systèmes de normes

Trois grands systèmes de normes encadrent les activités spatiales dans le monde :

| Système | Périmètre | Utilisateurs types | Nombre de documents |
|-----------|-------|----------------|---------------|
| **ECSS** (European Cooperation for Space Standardization) | Cycle de vie complet, toutes disciplines | ESA, industrie européenne, ASC (en partie) | 144 normes + 56 manuels |
| **Normes techniques de la NASA** | Programmes et projets de la NASA | Centres de la NASA, maîtres d'œuvre américains | Séries NPR/NPD/NASA-STD |
| **ISO TC 20/SC 14** | Systèmes et opérations spatiaux | International (norme de référence) | env. 40 normes |

Ces systèmes ne s'excluent pas mutuellement. De nombreuses missions (y compris canadiennes) adoptent une combinaison adaptée : ECSS pour l'ingénierie système et l'assurance produit, normes NASA pour certains domaines techniques précis et ISO pour l'atténuation des débris.

---

## 3.2 Hiérarchie des normes ECSS

### 3.2.1 Structure

Le système ECSS organise les normes en quatre branches, chacune comportant trois niveaux. La figure 3.1 présente cette hiérarchie et les principales normes de chaque branche.

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" style="max-width:800px; font-family: sans-serif;">
  <!-- Title -->
  <text x="400" y="28" text-anchor="middle" font-size="15" font-weight="bold" fill="#1a1a2e">Hiérarchie des normes ECSS</text>

  <!-- Top level: ECSS-S (System) -->
  <rect x="300" y="45" width="200" height="40" rx="6" fill="#37474f" stroke="#263238" stroke-width="2"/>
  <text x="400" y="70" text-anchor="middle" font-size="12" fill="white" font-weight="bold">ECSS-S : niveau système</text>

  <!-- Branch boxes -->
  <rect x="30" y="130" width="160" height="40" rx="6" fill="#1565c0" stroke="#0d47a1" stroke-width="2"/>
  <text x="110" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">M : management</text>

  <rect x="220" y="130" width="160" height="40" rx="6" fill="#2e7d32" stroke="#1b5e20" stroke-width="2"/>
  <text x="300" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">E : ingénierie</text>

  <rect x="410" y="130" width="160" height="40" rx="6" fill="#e65100" stroke="#bf360c" stroke-width="2"/>
  <text x="490" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Q : assurance produit</text>

  <rect x="600" y="130" width="160" height="40" rx="6" fill="#6a1b9a" stroke="#4a148c" stroke-width="2"/>
  <text x="680" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">U : durabilité</text>

  <!-- Connecting lines from S to branches -->
  <line x1="350" y1="85" x2="110" y2="130" stroke="#555" stroke-width="1.5"/>
  <line x1="380" y1="85" x2="300" y2="130" stroke="#555" stroke-width="1.5"/>
  <line x1="420" y1="85" x2="490" y2="130" stroke="#555" stroke-width="1.5"/>
  <line x1="450" y1="85" x2="680" y2="130" stroke="#555" stroke-width="1.5"/>

  <!-- Level descriptions for M branch -->
  <rect x="10" y="195" width="180" height="30" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="1"/>
  <text x="100" y="215" text-anchor="middle" font-size="9" fill="#0d47a1">ST : norme (« shall »)</text>

  <rect x="10" y="235" width="180" height="30" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="1"/>
  <text x="100" y="255" text-anchor="middle" font-size="9" fill="#0d47a1">HB : manuel (recommandations)</text>

  <rect x="10" y="275" width="180" height="30" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="1"/>
  <text x="100" y="295" text-anchor="middle" font-size="9" fill="#0d47a1">TM : note technique</text>

  <!-- Key M standards -->
  <text x="20" y="325" font-size="9" fill="#333" font-weight="bold">Principales normes M :</text>
  <text x="20" y="340" font-size="8" fill="#555">ECSS-M-ST-10C : management de projet</text>
  <text x="20" y="353" font-size="8" fill="#555">ECSS-M-ST-40C : gestion de configuration</text>
  <text x="20" y="366" font-size="8" fill="#555">ECSS-M-ST-80C : gestion des risques</text>

  <!-- Level descriptions for E branch -->
  <rect x="205" y="195" width="190" height="30" rx="4" fill="#e8f5e9" stroke="#2e7d32" stroke-width="1"/>
  <text x="300" y="215" text-anchor="middle" font-size="9" fill="#1b5e20">ST : norme (« shall »)</text>

  <rect x="205" y="235" width="190" height="30" rx="4" fill="#e8f5e9" stroke="#2e7d32" stroke-width="1"/>
  <text x="300" y="255" text-anchor="middle" font-size="9" fill="#1b5e20">HB : manuel (recommandations)</text>

  <!-- Key E standards -->
  <text x="210" y="290" font-size="9" fill="#333" font-weight="bold">Principales normes E :</text>
  <text x="210" y="305" font-size="8" fill="#555">ECSS-E-ST-10C : IS, généralités</text>
  <text x="210" y="318" font-size="8" fill="#555">ECSS-E-ST-20C : électricité et électronique</text>
  <text x="210" y="331" font-size="8" fill="#555">ECSS-E-ST-31C : contrôle thermique</text>
  <text x="210" y="344" font-size="8" fill="#555">ECSS-E-ST-32C : structures</text>
  <text x="210" y="357" font-size="8" fill="#555">ECSS-E-ST-33-01C : mécanismes</text>
  <text x="210" y="370" font-size="8" fill="#555">ECSS-E-ST-35C : propulsion</text>
  <text x="210" y="383" font-size="8" fill="#555">ECSS-E-ST-40C : logiciel</text>
  <text x="210" y="396" font-size="8" fill="#555">ECSS-E-ST-50C : communications</text>
  <text x="210" y="409" font-size="8" fill="#555">ECSS-E-ST-60C : contrôle-commande</text>
  <text x="210" y="422" font-size="8" fill="#555">ECSS-E-ST-70C : systèmes sol</text>

  <!-- Key Q standards -->
  <text x="415" y="195" font-size="9" fill="#333" font-weight="bold">Principales normes Q :</text>
  <text x="415" y="210" font-size="8" fill="#555">ECSS-Q-ST-10C : management de l'AP</text>
  <text x="415" y="223" font-size="8" fill="#555">ECSS-Q-ST-20C : assurance qualité</text>
  <text x="415" y="236" font-size="8" fill="#555">ECSS-Q-ST-30C : sûreté de fonctionnement</text>
  <text x="415" y="249" font-size="8" fill="#555">ECSS-Q-ST-40C : sécurité</text>
  <text x="415" y="262" font-size="8" fill="#555">ECSS-Q-ST-60C : composants EEE</text>
  <text x="415" y="275" font-size="8" fill="#555">ECSS-Q-ST-70C : matériaux et procédés</text>

  <!-- Key U standards -->
  <text x="605" y="195" font-size="9" fill="#333" font-weight="bold">Principales normes U :</text>
  <text x="605" y="210" font-size="8" fill="#555">ECSS-U-AS-10C : avis d'adoption</text>
  <text x="605" y="223" font-size="8" fill="#555">de l'ISO 24113 (atténuation des débris)</text>
  <text x="605" y="248" font-size="8" fill="#555">ECSS-U-AS-10C Rev.2 :</text>
  <text x="605" y="261" font-size="8" fill="#555">exigences de durabilité spatiale</text>

  <!-- Legend -->
  <rect x="500" y="380" width="280" height="55" rx="4" fill="#fff9c4" stroke="#f9a825" stroke-width="1"/>
  <text x="510" y="397" font-size="9" fill="#333" font-weight="bold">Règle de dénomination :</text>
  <text x="510" y="412" font-size="8" fill="#555">ECSS-[Branche]-[Type]-[Numéro][Niveau]</text>
  <text x="510" y="425" font-size="8" fill="#555">Ex. : ECSS-E-ST-10C = Ingénierie-Norme-10-Niveau C</text>
</svg>

**Figure 3.1** — La hiérarchie des normes ECSS : les documents ECSS-S de niveau système, les quatre branches (M, E, Q, U), les trois types de documents (ST, HB, TM) et les principales normes de chaque branche.

### 3.2.2 Les quatre branches

| Branche | Code | Périmètre | Exemple de norme |
|--------|------|-------|-----------------|
| **Management** | M | Management de projet, planification, revues, gestion de configuration, gestion des risques | ECSS-M-ST-10C Rev.1 (*Space Project Management*) |
| **Ingénierie** | E | Disciplines techniques : système, structures, thermique, EPS, télécommunications, SCAO, logiciel, sol | ECSS-E-ST-10C (*Systems Engineering General Requirements*) |
| **Assurance produit** | Q | Qualité, fiabilité, sécurité, composants EEE, matériaux, contamination | ECSS-Q-ST-10C (*Product Assurance Management*) |
| **Durabilité** | U | Atténuation des débris spatiaux, retrait de service en fin de vie, protection de l'environnement spatial | ECSS-U-AS-10C Rev.2 (adoption de l'ISO 24113) |

### 3.2.3 Types de documents

| Type | Code | Signification | Obligation |
|------|------|---------|-----------|
| **Norme** | ST | Contient des exigences en « shall » (« doit ») — obligatoires lorsqu'elle est rendue applicable | Conformité obligatoire ou demande formelle de dérogation |
| **Manuel** | HB | Contient des recommandations, des bonnes pratiques, des exemples résolus | Consultatif — non obligatoire mais fortement recommandé |
| **Note technique** | TM | Contient des informations de contexte, l'état de l'art | Purement informatif |

### 3.2.4 Adaptation

Une notion essentielle du système ECSS (et de tous les systèmes de normes) est l'**adaptation** (*tailoring*) — le processus qui consiste à sélectionner les normes, et les exigences au sein de ces normes, applicables à un projet donné.

L'ECSS-S-ST-00C définit trois niveaux d'adaptation :

| Niveau d'adaptation | Description | Application habituelle |
|----------------|-------------|-------------------|
| **Application complète** | Toutes les exigences de la norme rendue applicable s'appliquent | Grandes missions de l'ESA (Sentinel, JUICE) |
| **Application partielle** | Certaines clauses s'appliquent ; les autres sont écartées avec justification | Missions moyennes, projets de l'ASC |
| **Non applicable** | La norme n'est pas rendue applicable au projet | Missions CubeSat, démonstrateurs technologiques |

La justification de l'adaptation est documentée dans le **plan d'assurance produit et de sécurité (PASP)** et dans le **plan de management de l'ingénierie système (SEMP)**.

> **Équation clé.** Le coût de la conformité aux normes croît de façon non linéaire avec la classe de mission. Relation approximative observée dans des études de l'ESA :
>
> $$C_{\text{compliance}} \approx k \cdot M_{SC}^{0.7} \cdot N_{\text{standards}}^{0.3}$$
>
> où $M_{SC}$ est la masse sèche de l'engin spatial (kg), $N_{\text{standards}}$ le nombre de normes rendues applicables et $k$ une constante qui dépend de la maturité de l'organisation. Pour un CubeSat de 10 kg auquel 5 normes sont applicables, les coûts de conformité représentent environ 5–10 % du coût de la mission. Pour un satellite de 1000 kg auquel 40 normes sont applicables, ils peuvent atteindre 15–20 %.

---

## 3.3 Principales normes d'ingénierie ECSS

### 3.3.1 Ingénierie système (ECSS-E-ST-10C)

Il s'agit de la norme d'ingénierie maîtresse, équivalente à la NPR 7123.1D de la NASA. Elle définit :

- les processus et activités d'ingénierie système ;
- l'ingénierie des exigences (rédaction, vérification, traçabilité) ;
- l'analyse et la décomposition fonctionnelles ;
- la gestion des interfaces ;
- la gestion de configuration (aspects techniques).

| Notion ECSS-E-ST-10C | Équivalent NASA | Différence principale |
|----------------------|----------------|----------------|
| Spécification des exigences système | Référentiel des exigences techniques | L'ECSS exige un document formel de spécification des exigences (RSD) |
| Analyse fonctionnelle | Décomposition logique (processus 3) | Périmètre similaire |
| Matrice de vérification | Matrice de vérification des exigences | L'ECSS utilise une DRD formelle (définition des exigences documentaires) |
| Dossier de justification de la conception | Référentiel de la solution de conception | L'ECSS exige un DJF qui assure la traçabilité de chaque décision de conception |

### 3.3.2 Principales normes de sous-systèmes

| Norme | Discipline | Exigences principales | Équivalent NASA |
|----------|-----------|-----------------|----------------|
| ECSS-E-ST-20C | Électricité et électronique | Conception de l'EPS, mise à la masse, CEM, harnais | NASA-STD-4003A (EEE), NASA-HDBK-4001 |
| ECSS-E-ST-31C | Contrôle thermique | Conception, analyse et essais thermiques | NASA-STD-5001B (*Structural Design*) |
| ECSS-E-ST-32C | Structures | Conception structurale, facteurs de sécurité, essais | NASA-STD-5001B, GEVS (GSFC-STD-7000A) |
| ECSS-E-ST-33-01C | Mécanismes | Conception, essais et lubrification des mécanismes | NASA-STD-5017 |
| ECSS-E-ST-35C | Propulsion | Conception et essais du système propulsif | — |
| ECSS-E-ST-40C | Logiciel | Développement et vérification du logiciel, FDIR | NASA-STD-8739.8 |
| ECSS-E-ST-50C | Communications | Conception du système de télécommunications, bilan de liaison, protocoles | Normes CCSDS |
| ECSS-E-ST-60C | Contrôle-commande | Conception du SCAO, pointage, navigation | — |
| ECSS-E-ST-70C | Systèmes sol | Conception du segment sol, opérations | Normes CCSDS |

### 3.3.3 Exigences de conception structurale (exemple)

Pour illustrer le niveau de détail des normes ECSS, considérons les exigences de conception structurale de l'ECSS-E-ST-32C :

| Exigence | Valeur | Justification |
|-------------|-------|-----------|
| Facteur de sécurité (FoS) — limite élastique | $\geq 1.25$ | Éviter toute déformation permanente sous les charges limites |
| Facteur de sécurité — rupture | $\geq 1.5$ | Éviter la ruine de la structure sous les charges extrêmes |
| Charges de qualification | $1.25 \times$ charges limites | Démontrer une marge au-delà de l'environnement attendu |
| Première fréquence propre (axiale) | $> 25$ Hz en général (selon le lanceur) | Éviter le couplage avec les modes du lanceur |
| Première fréquence propre (latérale) | $> 10$ Hz en général (selon le lanceur) | Éviter le couplage avec les modes du lanceur |

> **Équation clé.** La marge de sécurité (MoS) est définie par
>
> $$MoS = \frac{\sigma_{\text{allowable}}}{FoS \times \sigma_{\text{applied}}} - 1$$
>
> Une MoS positive ($MoS > 0$) indique que la structure satisfait l'exigence. Une MoS de 0,0 signifie que la structure satisfait exactement l'exigence, sans aucune marge.
>
> Exemple : si la contrainte admissible vaut 280 MPa, la contrainte appliquée 150 MPa et le FoS 1,5 :
>
> $$MoS = \frac{280}{1.5 \times 150} - 1 = \frac{280}{225} - 1 = 0.244$$
>
> L'emploi de cette marge en dimensionnement structural, ainsi que sa démonstration, sont développés au chapitre 12, §12.1.6, et dans la partie V, §V.13.

---

## 3.4 Comparaison avec les normes de la NASA

### 3.4.1 Architecture des normes techniques de la NASA

Les normes de la NASA sont organisées différemment des normes ECSS. Principaux types de documents :

| Type | Code | Exemple | Obligation |
|------|------|---------|-----------|
| **Directive de politique de la NASA** | NPD | NPD 8700.1 (*Safety and Mission Assurance*) | Obligatoire pour tous les programmes de la NASA |
| **Exigence procédurale de la NASA** | NPR | NPR 7123.1D (*SE Processes*) | Obligatoire ; définit des processus et des exigences |
| **Norme technique de la NASA** | NASA-STD | NASA-STD-5001B (*Structural Design*) | Obligatoire lorsqu'elle est rendue applicable |
| **Manuel de la NASA** | NASA-HDBK | NASA-HDBK-4001 (*EEE Parts*) | Recommandations à titre consultatif |
| **Publication spéciale** | SP | SP-2016-6105 (SEH) | Ouvrage de référence |

### 3.4.2 Tableau de correspondance

| Domaine | Norme ECSS | Norme NASA | Norme ISO |
|--------|--------------|--------------|-------------|
| Ingénierie système | ECSS-E-ST-10C | NPR 7123.1D, SP-2016-6105 | ISO 15288 |
| Management de projet | ECSS-M-ST-10C | NPR 7120.5F | ISO 21500 |
| Gestion de configuration | ECSS-M-ST-40C | NPR 7120.5F, chap. 4 | ISO 10007 |
| Gestion des risques | ECSS-M-ST-80C | NPR 8000.4B | ISO 31000 |
| Conception structurale | ECSS-E-ST-32C | NASA-STD-5001B | — |
| Atténuation des débris | ECSS-U-AS-10C | NASA-STD-8719.14A | ISO 24113 |
| Propreté | ECSS-Q-ST-70-01C | NASA-SN-C-0005 | ISO 14644 |
| Logiciel | ECSS-E-ST-40C | NASA-STD-8739.8 | ISO 12207 |

---

## 3.5 CDS Rev 14 — norme d'interface avec le lanceur

### 3.5.1 Qu'est-ce que la CDS ?

La **CubeSat Design Specification (CDS)**, tenue à jour par la California Polytechnic State University (Cal Poly) et révisée par la communauté CubeSat, définit les interfaces mécaniques, électriques et opérationnelles entre les CubeSats et leurs systèmes de déploiement (P-POD, ISIPOD, etc.).

[Source : CDS Rev 14, 2022, disponible auprès du Cal Poly CubeSat Program]

### 3.5.2 Principales exigences de la CDS

| Paramètre | Exigence de la CDS Rev 14 | Justification |
|-----------|----------------------|-----------|
| **Dimensions d'une unité** | $100 \times 100 \times 113.5$ mm par U | Écartement standard des rails du déployeur |
| **Masse par U** | $\leq 2.0$ kg (avec dérogation jusqu'à 2,66 kg pour certains déployeurs) | Limites du mécanisme à ressort du déployeur |
| **Matériau des rails** | Aluminium anodisé dur (7075 ou 6061-T6) | Compatibilité avec les surfaces de contact du déployeur |
| **Centre de gravité** | À moins de 2 cm du centre géométrique | Dynamique de déploiement, maîtrise de la vitesse de culbutage |
| **Éléments déployables** | Doivent être maintenus pendant le lancement ; aucune saillie hors de l'enveloppe du CubeSat | Protéger les charges utiles voisines dans le déployeur |
| **Ressorts de séparation** | Interdits sur le CubeSat (fournis par le déployeur) | Mécanisme de déploiement standardisé |
| **Silence RF** | Aucune émission RF avant 30 minutes après le déploiement | Éviter les brouillages avec le lanceur |
| **Interrupteurs de déploiement** | Au moins 1 par élément déployable ; 2 pour la redondance | Empêcher un déploiement prématuré |
| **État de charge de la batterie** | Pleine charge (recommandé) ; recharge par le déployeur impossible | Aucune interface électrique avec le déployeur |
| **Propulsion** | Le cas échéant : doit être bloquée par 3 inhibitions indépendantes ; aucun ergol toxique | Sécurité de la charge utile principale et du déployeur |

### 3.5.3 Formats

| Format | Dimensions (mm) | Masse maximale | Applications habituelles |
|------------|-----------------|------------|---------------------|
| 1U | 100 × 100 × 113,5 | 2,0 kg | Démonstrateurs technologiques, nœuds IoT |
| 1,5U | 100 × 100 × 170,2 | 3,0 kg | Démonstrateurs technologiques avancés |
| 2U | 100 × 100 × 227,0 | 4,0 kg | Instruments simples, stockage et retransmission |
| 3U | 100 × 100 × 340,5 | 6,0 kg | Missions standard d'observation de la Terre et scientifiques |
| 6U | 100 × 226,3 × 366,0 | 12,0 kg | Observation de la Terre avancée, télécommunications |
| 12U | 226,3 × 226,3 × 366,0 | 24,0 kg | Missions à hautes performances |
| 16U | 226,3 × 226,3 × 454,0 | 32,0 kg | Capacités proches d'un microsatellite |

### 3.5.4 Interfaces de lancement partagé

Pour les petits satellites qui ne sont pas des CubeSats (microsatellites de 10–200 kg), la norme d'interface dépend du lanceur (exemples représentatifs, et non des recommandations) :

| Opérateur de lancement | Norme d'interface | Type d'adaptateur | Document de référence |
|----------------|-------------------|-------------|-------------|
| SpaceX (Rideshare) | Classe ESPA | Port ESPA de 15" ou 24" | SpaceX Rideshare User's Guide |
| Rocket Lab (Electron) | Système de séparation spécifique | Fourni par Rocket Lab | Electron Payload User's Guide |
| Arianespace (Vega-C) | ASAP-S | Adaptateur multicharge | Vega-C User Manual |
| ISRO (PSLV) | Adaptateur spécifique | Fourni par l'ISRO | PSLV User Manual |

> **Pratique industrielle.** La constellation SuperDove de Planet Labs (plus de 150 satellites) utilise un format 3U étendu, conforme à la CDS, qui complète la norme par un agencement de déployeur spécifique permettant un déploiement par lots. Chaque satellite SuperDove (masse env. 5,8 kg) emporte un imageur multispectral à 8 bandes avec une GSD d'env. 3 m. La standardisation de la plateforme a permis une cadence de fabrication de plus de 2 satellites par semaine — ce qui n'est possible que parce que la CDS fournit un référentiel d'interface stable.

---

## 3.6 Atténuation des débris spatiaux

### 3.6.1 Le problème des débris

En 2025, on dénombre approximativement :

- **plus de 36 500** objets suivis de plus de 10 cm en orbite terrestre ;
- **plus de 1 000 000** d'objets estimés de 1–10 cm (non suivis, mortels pour un engin spatial) ;
- **plus de 130 000 000** d'objets estimés de 1 mm–1 cm (susceptibles d'endommager des composants).

La population de débris augmente sous l'effet des collisions (syndrome de Kessler), des essais antisatellites (p. ex. l'ASAT chinois de 2007 : plus de 3500 fragments suivis) et de la croissance rapide des mégaconstellations.

[Source : ESA Space Debris Office, rapport annuel 2024 ; NASA ODPO, *Orbital Debris Quarterly News*]

### 3.6.2 Hiérarchie des textes relatifs à l'atténuation des débris

| Niveau | Document | Périmètre | Statut |
|-------|----------|-------|--------|
| **International volontaire** | IADC Space Debris Mitigation Guidelines (Rev 3, 2021) | Bonnes pratiques mondiales | Consultatif ; adopté par le CUPEEA |
| **Norme internationale** | ISO 24113:2023 | Exigences relatives à l'atténuation des débris | Norme ; rendue applicable par de nombreuses agences |
| **Norme européenne** | ECSS-U-AS-10C Rev.2 | Avis d'adoption ECSS de l'ISO 24113 | Obligatoire pour les missions de l'ESA |
| **Réglementation américaine** | FCC 47 CFR 25.114(d)(14) | Retrait de service des satellites sous licence américaine | Juridiquement contraignant pour les titulaires de licence FCC |
| **Norme NASA** | NASA-STD-8719.14A | Processus de la NASA pour limiter les débris orbitaux | Obligatoire pour les missions de la NASA |
| **Exigence ESA** | ESA/ADMIN/IPOL(2023)2 | Exigences Clean Space | Obligatoire pour les missions de l'ESA (à partir de 2023) |

### 3.6.3 Principales exigences d'atténuation des débris

| Exigence | Source | Valeur | Remarques |
|-------------|--------|-------|-------|
| **Retrait de service** | IADC, ISO 24113 | $\leq 25$ ans | Ligne directrice volontaire ; en cours de durcissement |
| **Retrait de service** | FCC (à partir de 2024) | $\leq 5$ ans | Juridiquement contraignant pour les satellites sous licence FCC |
| **Probabilité de réussite du retrait de service** | ISO 24113 | $\geq 0.9$ | La fiabilité du dispositif de désorbitation doit être démontrée |
| **Risque de victimes lors de la rentrée** | NASA-STD-8719.14A | $\leq 1:10{,}000$ par événement | Oriente le choix des matériaux et la conception pour la désintégration |
| **Probabilité de collision** | IADC | $< 10^{-4}$ par an (cumulée) | Oriente le choix de l'orbite et la capacité de manœuvre |
| **Passivation** | ISO 24113, ECSS-U-AS-10C | Toutes les sources d'énergie stockée vidées en fin de vie | Batteries, réservoirs sous pression, roues, RF |

### 3.6.4 Options de retrait de service

| Méthode | Orbite concernée | Mécanisme | Délai avant rentrée |
|--------|-----------------|-----------|------------------|
| **Traînée atmosphérique (naturelle)** | LEO < 600 km | Déclin d'orbite naturel | De quelques mois à quelques années |
| **Traînée atmosphérique (augmentée)** | LEO < 700 km | Voile de traînée, câble de traînée | De quelques semaines à quelques années |
| **Désorbitation propulsive** | LEO | Les propulseurs abaissent le périgée à env. 200 km | Quelques jours |
| **Orbite cimetière** | GEO | Relèvement de l'orbite d'env. 300 km au-dessus de la GEO | Indéfini (pas de rentrée) |
| **Retrait de service héliocentrique** | Au-delà de la GEO | Échappement à l'orbite terrestre | Sans objet |

Le paramètre déterminant est la durée de vie orbitale. La figure 3.2 montre comment la durée de vie varie avec l'altitude pour des coefficients balistiques représentatifs, ainsi que les limites de 25 ans de l'IADC et de 5 ans de la FCC ; les équations ci-dessous en donnent une première estimation, et le chapitre 7 traite en détail l'environnement de traînée atmosphérique.

![Durée de vie orbitale en fonction de l'altitude pour des coefficients balistiques représentatifs, avec les limites de 5 ans de la FCC et de 25 ans de l'IADC.](../assets/figures/fig_orbital_lifetime.png)

**Figure 3.2** — Durée de vie orbitale en fonction de l'altitude circulaire initiale pour des coefficients balistiques représentatifs. Les lignes horizontales indiquent les limites de retrait de service de 5 ans de la FCC et de 25 ans de l'IADC ; l'altitude à laquelle la courbe d'un engin spatial donné croise chaque ligne est l'orbite la plus haute qu'il peut occuper sans capacité de désorbitation active.

> **Équation clé.** La durée de vie orbitale d'un satellite en LEO due à la traînée atmosphérique vaut approximativement
>
> $$\tau \approx \frac{C_D \cdot A \cdot \rho \cdot a^2}{2m} \cdot \text{(intégrale complexe)}$$
>
> Règle empirique plus simple pour les orbites circulaires :
>
> $$\tau_{\text{years}} \approx \frac{h - 200}{30} \cdot \frac{m / A}{50}$$
>
> où $h$ est l'altitude en km, $m$ la masse en kg et $A$ la section transversale en m². Cette relation est très approximative ; la durée de vie réelle dépend de l'activité solaire (qui module la densité atmosphérique aux altitudes élevées), du coefficient de traînée et de l'excentricité de l'orbite. Utilisez le logiciel DAS (*Debris Assessment Software*) de la NASA ou l'outil DRAMA de l'ESA pour des prévisions précises.
>
> Plus précisément, le coefficient balistique vaut
>
> $$B = \frac{m}{C_D \cdot A}$$
>
> Plus $B$ est faible (masse plus faible, surface plus grande), plus la rentrée est rapide. Un CubeSat 3U ($m \approx 4$ kg, $A \approx 0.03$ m², $C_D \approx 2.2$) à 400 km a un $B \approx 61$ kg/m² et rentrera dans l'atmosphère en env. 1–3 ans selon le cycle solaire.

### 3.6.5 Conséquences pratiques pour la conception de mission

| Décision de conception | Conséquence pour l'atténuation des débris |
|----------------|--------------------------|
| Choix de l'altitude de l'orbite | Les altitudes > 600 km exigent une désorbitation active ; > 700 km est fortement déconseillé pour un engin spatial non manœuvrant |
| Système propulsif | Exigé pour les altitudes > 500–600 km afin de respecter la règle des 25 ans (ou celle des 5 ans de la FCC) |
| Conception de la passivation | Il faut concevoir les circuits de déconnexion de la batterie, de dépressurisation et d'arrêt des roues |
| Choix des matériaux | Structures en aluminium privilégiées pour la conception pour la désintégration ; le titane et la fibre de carbone survivent à la rentrée |
| Évitement des collisions | Capacité de manœuvre ou service d'analyse de conjonctions (p. ex. 18th SDS, SSA de l'ESA) nécessaire |

> **Pratique industrielle.** OneWeb (648 satellites à 1200 km) embarque une propulsion sur chaque satellite, spécifiquement pour la désorbitation en fin de vie, car le déclin naturel depuis 1200 km prendrait des siècles. Chaque satellite emporte assez d'ergols pour plusieurs manœuvres d'évitement de collision, plus une poussée de désorbitation complète pour abaisser le périgée sous 300 km. L'opération de désorbitation dure environ 3 mois par satellite.

---

## 3.7 Droit international de l'espace et CUPEEA

### 3.7.1 Les traités des Nations unies sur l'espace

Le cadre juridique des activités spatiales est établi par cinq traités des Nations unies négociés au sein du Comité des utilisations pacifiques de l'espace extra-atmosphérique (CUPEEA) :

| Traité | Année | Principales dispositions | Ratification |
|--------|------|----------------|-------------|
| **Traité sur l'espace extra-atmosphérique (OST)** | 1967 | L'exploration de l'espace est libre ; aucune appropriation nationale ; les États sont responsables de leurs activités nationales ; responsabilité pour les dommages | 114 États parties (dont le Canada) |
| **Accord sur le sauvetage** | 1968 | Restitution des astronautes et des objets spatiaux | 99 États parties |
| **Convention sur la responsabilité** | 1972 | L'État de lancement est responsable des dommages causés sur Terre (responsabilité absolue) et dans l'espace (responsabilité pour faute) | 98 États parties |
| **Convention sur l'immatriculation** | 1976 | Les États doivent immatriculer leurs objets spatiaux auprès des Nations unies | 72 États parties |
| **Accord sur la Lune** | 1979 | La Lune et les corps célestes sont le « patrimoine commun de l'humanité » | 18 États parties (NI les États-Unis, NI la Russie, NI la Chine) |

### 3.7.2 Principes juridiques clés pour la conception de mission

| Principe | Source | Conséquence |
|-----------|--------|------------|
| **Responsabilité de l'État** | OST, art. VI | Le gouvernement du Canada porte la responsabilité internationale de toutes les activités spatiales canadiennes, y compris les missions privées et universitaires |
| **Autorisation et surveillance** | OST, art. VI | Le Canada doit autoriser et surveiller en permanence toutes les activités spatiales non gouvernementales (d'où l'existence de la LSTS — chapitre 2, §2.6) |
| **Responsabilité pour les dommages** | Convention sur la responsabilité | Le Canada (en tant qu'État de lancement) est responsable des dommages causés par les satellites canadiens ; responsabilité absolue sur Terre, pour faute dans l'espace |
| **Immatriculation** | Convention sur l'immatriculation | Le Canada doit immatriculer tous ses objets spatiaux auprès des Nations unies ; l'ASC tient le registre canadien |
| **Non-contamination** | OST, art. IX | Éviter toute contamination nuisible de l'espace et des corps célestes (protection planétaire) |
| **Prise en compte des intérêts d'autrui** | OST, art. IX | Mener les activités en tenant dûment compte des intérêts des autres États (atténuation des débris) |

### 3.7.3 Lignes directrices du CUPEEA sur la viabilité à long terme (2019)

En 2019, le CUPEEA a adopté 21 lignes directrices aux fins de la viabilité à long terme des activités spatiales. Elles sont volontaires mais politiquement importantes :

| Catégorie de lignes directrices | Nombre | Points clés |
|--------------------|----|------------|
| Cadre politique et réglementaire | 7 | Adopter des cadres réglementaires nationaux, immatriculer les objets spatiaux, partager les données de surveillance de l'espace (SSA) |
| Sécurité des opérations | 4 | Analyse de conjonctions, évitement des collisions, évaluation du risque à la rentrée |
| Coopération internationale | 4 | Partager les bonnes pratiques d'atténuation des débris, coordonner l'utilisation du spectre |
| Recherche scientifique et technique | 6 | Améliorer les modèles de débris, développer des technologies de retrait, étudier les effets de la météorologie de l'espace |

[Source : A/74/20, rapport du CUPEEA, 2019, annexe II]

---

## 3.8 Suivi de la conformité dans une étude de conception concourante

Dans une équipe de conception concourante, le poste d'**ingénieur conformité** (chapitre 1, tableau 1.4 ; partie IV) est responsable de l'état de la conception au regard des normes, des licences et du contrôle des exportations. Ce poste tient un registre de conformité qui comprend au minimum les éléments du tableau 3.1. Certaines de ces vérifications peuvent être calculées directement à partir du modèle paramétrique partagé — durée de vie orbitale à partir de l'altitude, de la masse et de la surface ; limites de masse, de dimensions et de centre de gravité de la CDS —, et un outil de conception concourante peut les signaler automatiquement dès qu'un paramètre change. D'autres sont par nature manuelles : les dépôts de licences, les classifications au titre du contrôle des exportations et l'applicabilité d'une norme relèvent du jugement et de démarches administratives que le registre consigne mais ne peut trancher.

**Tableau 3.1** — Éléments d'un registre de conformité de mission et degré d'automatisation possible de chacun.

| Élément | Objet du suivi | Niveau d'automatisation |
|---------|---------------|-----------------|
| **Matrice d'applicabilité des normes** | Normes ECSS/NASA/ISO applicables à la mission, et niveau d'adaptation retenu | Semi-automatisé (proposé selon le type de mission ; confirmé par jugement) |
| **Conformité en matière de débris** | Durée de vie après la mission, plan de passivation, risque de victimes | Automatisé (calculé à partir de l'orbite et de la masse) |
| **Liste de vérification LSTS** | Exigences de licence pour les missions canadiennes de télédétection | Manuel (liste de vérification avec conseils) |
| **État des notifications de spectre** | Avancement des démarches auprès d'ISDE et de l'UIT | Manuel (suivi d'état) |
| **Classification au titre du contrôle des exportations** | Classification ECCN/USML des composants clés | Manuel (par composant) |
| **Conformité à la CDS** | Conformité des interfaces mécaniques et électriques à la CDS Rev 14 | Semi-automatisé (vérifie masse, dimensions, centre de gravité) |

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Système ECSS | Quatre branches (M, E, Q, U) ; trois types de documents (ST, HB, TM) ; l'adaptation est indispensable |
| Normes NASA | Organisées en NPD/NPR/NASA-STD/NASA-HDBK ; globalement équivalentes aux normes ECSS |
| CDS Rev 14 | Définit les interfaces mécaniques, électriques et opérationnelles des CubeSats ; la conformité est exigée pour un lancement partagé |
| Atténuation des débris | Règle des 25 ans de l'IADC ; règle des 5 ans de la FCC (à partir de 2024) ; passivation exigée ; oriente la conception de l'orbite et de la propulsion |
| Droit international | L'OST établit la responsabilité des États ; le Canada est responsable de toutes les activités spatiales canadiennes |
| CUPEEA | 21 lignes directrices sur la viabilité (2019) ; volontaires mais de plus en plus influentes |
| Suivi de la conformité | Relève du poste d'ingénieur conformité ; automatisé lorsque la vérification est numérique, manuel lorsqu'il s'agit d'un dépôt ou d'un jugement |

---

## Exercices

1. **Les interfaces et Mars Climate Orbiter.** Identifiez lesquels des 17 processus techniques communs du chapitre 1, §1.3, ont failli lors de la perte de Mars Climate Orbiter, et rédigez l'exigence d'interface (sous la forme en « doit » du chapitre 5) qui, si elle avait figuré dans le document de contrôle d'interface et avait été vérifiée, aurait évité la perte. Quelle méthode de vérification (ATIR(D)) lui attribueriez-vous ?

2. **Adapter un ensemble de normes.** Pour un CubeSat 3U d'observation de la Terre construit par une équipe universitaire disposant d'un budget modeste, sélectionnez cinq normes ECSS de la figure 3.1 à rendre applicables. Pour chacune, indiquez le niveau d'adaptation (complète, partielle, non applicable), donnez une justification en une phrase et nommez le document (PASP ou SEMP) dans lequel cette justification serait consignée. Identifiez une norme que vous avez délibérément choisi de *ne pas* rendre applicable et expliquez le risque que vous acceptez en l'omettant.

3. **Évolution du coût de la conformité.** À l'aide de la relation du §3.2.4, calculez le rapport entre le coût de conformité d'un satellite de 1000 kg auquel 40 normes sont applicables et celui d'un CubeSat de 10 kg auquel 5 normes sont applicables, en supposant le même $k$. Si le coût d'une mission évolue approximativement comme $M_{SC}^{0.9}$, la hausse annoncée du coût de conformité, de 5–10 % à 15–20 % du coût de la mission, est-elle cohérente avec l'équation ? Commentez ce que les exposants impliquent quant à l'endroit où concentrer l'effort de conformité pour les petites missions.

4. **Marge de sécurité.** Un rail de CubeSat est usiné dans de l'aluminium 7075-T6 (contrainte admissible à la limite élastique de 503 MPa, contrainte admissible à rupture de 572 MPa). L'analyse donne une contrainte appliquée de 310 MPa sous charge limite. Calculez la marge de sécurité vis-à-vis de la limite élastique (FoS 1,25) et vis-à-vis de la rupture (FoS 1,5) à l'aide du §3.3.3. Quel cas est dimensionnant ? Quelle contrainte appliquée ramènerait la marge dimensionnante à zéro, et à quelle charge de qualification (en multiples de la charge limite) la structure devrait-elle alors résister ?

5. **Audit de conformité à la CDS.** Retour sur UniSat-1 (chapitre 1, §1.7) : la conception a une masse de 1,0 kg, un centre de gravité situé à 1,5 cm du centre géométrique selon le grand axe, une antenne UHF déployable en ruban et un émetteur qui doit rester silencieux après le déploiement. Confrontez la conception à chaque ligne du §3.5.2 et indiquez si elle est conforme, non conforme, ou si une caractéristique de conception doit être ajoutée. Recommencez pour un CubeSat 3U d'OT de 4,2 kg doté de panneaux solaires déployables et d'un module de propulsion à gaz froid.

6. **Durée de vie orbitale et règle des 5 ans.** (a) À l'aide de la règle empirique du §3.6.4, estimez la durée de vie orbitale d'un CubeSat 3U ($m = 4$ kg, $A = 0.03$ m²) à 400, 500 et 600 km, ainsi que celle d'UniSat-1 ($m = 1$ kg, $A = 0.01$ m²) à 400 km. (b) Comparez votre résultat à 400 km avec l'affirmation de la même section fondée sur le coefficient balistique (« env. 1–3 ans ») et avec la figure 3.2. Les estimations divergent ; expliquez pourquoi une règle empirique qui ignore l'activité solaire et la densité atmosphérique peut se tromper d'un facteur important, et indiquez sur quelle source vous vous appuieriez lors d'une revue de conception (le calcul physique du chapitre 7, §7.3.3, donne ≈ 9 mois à 400 km et ≈ 5 ans à 500 km pour le cas 3U). (c) Estimez, à partir de la figure 3.2, l'altitude circulaire la plus élevée à laquelle le CubeSat 3U pourrait être exploité sans propulsion tout en respectant la règle des 5 ans de la FCC.

7. **Passivation.** Énumérez toutes les sources d'énergie stockée d'un CubeSat 3U d'OT qui emporte une batterie lithium-ion, trois roues de réaction, un module de propulsion à gaz froid et un émetteur en bande S. Pour chacune, indiquez l'action de passivation exigée par l'ISO 24113 en fin de vie et la caractéristique de conception (circuit, vanne, commande) qui la permet. Lesquelles de ces actions doivent encore fonctionner après la défaillance du calculateur de vol principal ?

8. **État de lancement et responsabilité.** Un CubeSat universitaire canadien est lancé par un PSLV indien dans le cadre d'un contrat négocié par une société néerlandaise et, trois ans plus tard, entre en collision avec un étage supérieur russe hors d'usage. À l'aide du §3.7, identifiez les États qui sont des « États de lancement » au sens de la Convention sur la responsabilité, indiquez si c'est la responsabilité absolue ou la responsabilité pour faute qui s'applique, et quel État doit avoir immatriculé le CubeSat. Qu'implique l'article VI de l'OST quant aux obligations de l'université envers le gouvernement du Canada avant le lancement ?

9. **Constituer un registre de conformité.** Pour le CubeSat 3U d'OT, constituez un registre de conformité au format du tableau 3.1 comportant au moins huit lignes et couvrant l'applicabilité des normes, l'atténuation des débris, la LSTS, le spectre, le contrôle des exportations et la CDS. Pour chaque ligne, indiquez le ou les paramètres du modèle de conception partagé dont elle dépend, si la vérification peut être automatisée, et la phase du cycle de vie (chapitre 1, §1.4) à laquelle elle doit être close.

---

## Références

1. ECSS, *ECSS-S-ST-00C — Space Standardization : Policy and Organisation*, 2020. [https://ecss.nl/standard/ecss-s-st-00c-space-standardization-policy-and-organisation/](https://ecss.nl/standard/ecss-s-st-00c-space-standardization-policy-and-organisation/)
2. ECSS, *ECSS-E-ST-10C — System Engineering General Requirements*, 2009. [https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/](https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/)
3. ECSS, *ECSS-E-ST-32C Rev.1 — Structural General Requirements*, 2008. [https://ecss.nl/standard/ecss-e-st-32c-rev-1-structural-general-requirements/](https://ecss.nl/standard/ecss-e-st-32c-rev-1-structural-general-requirements/)
4. ECSS, *ECSS-U-AS-10C Rev.2 — Adoption Notice of ISO 24113*, 2023. [https://ecss.nl/standard/ecss-u-as-10c-rev-2/](https://ecss.nl/standard/ecss-u-as-10c-rev-2/)
5. ISO, *ISO 24113:2023 — Space Systems : Space Debris Mitigation Requirements*, 2023. [https://www.iso.org/standard/82450.html](https://www.iso.org/standard/82450.html)
6. IADC, *IADC-02-01 Rev 3 — Space Debris Mitigation Guidelines*, 2021. [https://www.iadc-home.org/documents_public/](https://www.iadc-home.org/documents_public/)
7. Cal Poly, *CubeSat Design Specification (CDS) Rev 14*, 2022. [https://www.cubesat.org/cubesatinfo](https://www.cubesat.org/cubesatinfo)
8. NASA, *Systems Engineering Handbook* (SP-2016-6105 Rev 2), 2016. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
9. NASA, *NASA-STD-8719.14A — Process for Limiting Orbital Debris*, 2019. [https://standards.nasa.gov/standard/oce/nasa-std-871914](https://standards.nasa.gov/standard/oce/nasa-std-871914)
10. UNOOSA, *A/74/20 — Report of COPUOS*, 2019. [https://www.unoosa.org/oosa/en/ourwork/copuos/2019/index.html](https://www.unoosa.org/oosa/en/ourwork/copuos/2019/index.html)
11. UNOOSA, *Outer Space Treaty*, 1967. [https://www.unoosa.org/oosa/en/ourwork/spacelaw/treaties/outerspacetreaty.html](https://www.unoosa.org/oosa/en/ourwork/spacelaw/treaties/outerspacetreaty.html)
12. UNOOSA, *COPUOS Guidelines for the Long-term Sustainability of Outer Space Activities*, 2019. [https://www.unoosa.org/oosa/en/ourwork/topics/long-term-sustainability-of-outer-space-activities.html](https://www.unoosa.org/oosa/en/ourwork/topics/long-term-sustainability-of-outer-space-activities.html)
13. ESA, *Space Debris Mitigation Compliance Verification Guidelines* (ESSB-HB-U-002), 2023. [https://technology.esa.int/upload/media/47ypgb5qwq.pdf](https://technology.esa.int/upload/media/47ypgb5qwq.pdf)
14. FCC, *47 CFR 25.114 — Satellite Applications*. [https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-25](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-25)
