# Chapitre 4 — Besoins de la mission, parties prenantes, études de compromis et concept d'opérations

> **Lectures préalables conseillées.** NASA *Systems Engineering Handbook* §4.1, §4.4 et §6.8, annexe C (*How to Write a Good Requirement*) et annexe S (plan type d'un ConOps) ; NPR 7123.1D §3.2.1 (processus 1), §3.2.4 (processus 4) et §3.5.8 (processus 17) ; ECSS-E-ST-10C §5.1 ; SMAD4, chap. 1–3 et chap. 14. Ce chapitre s'appuie sur le cycle en V et les 17 processus du chapitre 1, ainsi que sur le contexte réglementaire et normatif des chapitres 2 et 3.

## Objectifs d'apprentissage

À l'issue de ce chapitre, vous serez capable de :

1. Rédiger un énoncé de problème clair qui définit le besoin de la mission sans prescrire de solution
2. Identifier et classer les parties prenantes de la mission à l'aide d'une matrice d'analyse structurée
3. Définir des objectifs de mission assortis de critères de réussite mesurables et en assurer la traçabilité à travers la hiérarchie MoE/MoP/TPM
4. Structurer et conduire une étude de compromis à l'aide de méthodes de notation pondérée (analyse de décision — processus 17)
5. Évaluer objectivement les solutions spatiales et non spatiales et documenter la justification de la décision
6. Concevoir un concept d'opérations (ConOps) comprenant les phases de mission, les modes opérationnels et le flux de données
7. Formaliser un concept de mission — besoin, objectifs, solutions alternatives et plan du ConOps — sous une forme exploitable par une équipe de conception concourante

---

## 4.1 L'énoncé du problème

### 4.1.1 Pourquoi commencer par le problème ?

Le NASA SEH (section 4.1.1) l'énonce ainsi : *« Clearly define the problem before solving it »* (définir clairement le problème avant de le résoudre).

Le mode de défaillance le plus courant en conception de mission n'est pas technique — c'est **résoudre le mauvais problème**. Les équipes sautent aux solutions (« il nous faut un CubeSat 6U à 500 km ») avant d'avoir formulé le besoin réel (« la surveillance agricole en Afrique subsaharienne exige une imagerie multispectrale à 10 m de résolution tous les 5 jours »). Cet engagement prématuré envers une solution :

- écarte des solutions alternatives potentiellement meilleures (achat de données commerciales, relevés aériens, capteurs au sol) ;
- introduit des contraintes inutiles qui font grimper les coûts et les risques ;
- rend impossible l'évaluation de la réussite de la mission (réussite par rapport à quoi ?) ;
- viole le principe fondamental de l'ingénierie système : **le QUOI avant le COMMENT**.

[Source : NASA SEH, section 4.1 ; NASA SEH, annexe C — « How to Write a Good Requirement »]

### 4.1.2 Structure d'un bon énoncé de problème

Un énoncé de problème rigoureux répond à quatre questions :

| Question | Contenu | Exemple |
|----------|---------|---------|
| **Quel est le problème ?** | Le manque de capacité — ce qui fait défaut ou est insuffisant | « Absence d'imagerie multispectrale disponible à temps, abordable, avec une résolution et une revisite suffisantes » |
| **Qui est concerné ?** | Les parties prenantes et les utilisateurs finaux qui pâtissent de ce manque | « Les organismes de surveillance agricole d'Afrique subsaharienne » |
| **Quel est l'impact ?** | La conséquence de l'absence de solution — quantifiée si possible | « Des évaluations des cultures tardives ou inexactes, qui affectent la répartition de l'aide alimentaire pour 300 millions de personnes » |
| **Quelles contraintes existent ?** | Limites budgétaires, calendaires, politiques, réglementaires ou techniques | « Budget : coût total de la mission < 10 M$ ; calendrier : 3 ans jusqu'aux premières données » |

### 4.1.3 Bons et mauvais énoncés de problème

**Exemple — BON :**
> « Les organismes de surveillance agricole d'Afrique subsaharienne n'ont pas accès, à temps et à un coût abordable, à une imagerie multispectrale de résolution ($\leq 10$ m) et de fréquence de revisite ($\leq 5$ jours) suffisantes pour étayer la prévision des rendements agricoles et la planification de la sécurité alimentaire. Les données actuelles de Sentinel-2 offrent une résolution de 10 m mais une revisite de 5 jours seulement à l'équateur, et la couverture nuageuse réduit les observations exploitables à environ 60 %. Il en résulte des évaluations des cultures tardives ou inexactes, qui affectent la répartition de l'aide alimentaire pour 300 millions de personnes. Contrainte budgétaire : coût total de la mission $< \$10$M ; livraison des premières données sous 3 ans. »

**Exemple — MAUVAIS :**
> « Il nous faut un CubeSat 6U avec un imageur multispectral à 500 km en SSO. »

Le mauvais exemple prescrit une solution (CubeSat 6U, SSO), fixe un paramètre de conception (500 km) et ne dit rien du problème réel. C'est un **énoncé de solution**, pas un énoncé de problème.

### 4.1.4 Le principe du QUOI et du COMMENT

Au niveau du besoin de la mission, tout doit décrire **CE QUI** est nécessaire, et non **COMMENT** l'obtenir :

| QUOI (correct à ce stade) | COMMENT (prématuré à ce stade) |
|------------------------------|-------------------------------|
| « Imagerie à 10 m de résolution » | « Utiliser un télescope de 15 cm d'ouverture » |
| « Revisite quotidienne à l'équateur » | « Déployer une constellation Walker delta de 12 satellites » |
| « Données disponibles dans les 6 heures suivant l'acquisition » | « Utiliser une liaison descendante en bande X à 150 Mbit/s vers 3 stations sol » |
| « Coût total inférieur à 10 M$ » | « Utiliser exclusivement des composants COTS » |
| « Durée de vie opérationnelle de 5 ans » | « Choisir des composants durcis aux rayonnements » |

La colonne COMMENT n'est pas fausse — ce sont toutes des décisions de conception raisonnables. Mais elles relèvent de phases ultérieures (phase A/B), pas de l'énoncé du problème. Figer le COMMENT prématurément supprime des degrés de liberté de conception et peut conduire à des solutions sous-optimales.

**Matière à réflexion.** Prenez n'importe quelle ligne de la colonne COMMENT et énumérez les options de conception qu'elle écarte implicitement. Une ouverture de 15 cm, par exemple, exclut un radar à synthèse d'ouverture, une charge utile hébergée sur une plateforme plus grande et l'achat des images à un fournisseur commercial — avant même que quiconque se soit demandé si ces solutions serviraient mieux les agriculteurs.

---

## 4.2 Identification et analyse des parties prenantes

### 4.2.1 Qu'est-ce qu'une partie prenante ?

Le NASA SEH (section 4.1.2) définit les parties prenantes comme « all parties who have a legitimate interest in the system throughout its lifecycle » (l'ensemble des acteurs ayant un intérêt légitime dans le système tout au long de son cycle de vie). Cette notion dépasse le seul utilisateur final — elle inclut tous ceux qui influent sur la mission ou qui en subissent les effets.

### 4.2.2 Catégories de parties prenantes des missions spatiales

| Catégorie | Exemples | Besoins habituels | Contraintes habituelles |
|----------|---------|---------------|-------------------|
| **Utilisateurs finaux** | Scientifiques, agriculteurs, compagnies maritimes, services d'urgence | Qualité, résolution, latence, format et accessibilité des données | Droits sur les données, formation, infrastructures |
| **Exploitants** | Centre de contrôle de mission, opérateurs de stations sol | Opérabilité, niveau d'automatisation, effectifs, formation | Budget d'exploitation, disponibilité du personnel |
| **Commanditaires / financeurs** | Agence spatiale (ASC), université, investisseur privé, MDN | Retour sur investissement, respect du calendrier, profil de risque | Plafond budgétaire, échéances politiques, obligations de rapport |
| **Autorités de réglementation** | ISDE, UIT, FCC, contrôle des exportations (AMC) | Conformité aux réglementations sur le spectre, les débris, la LSTS et les exportations | Délais de licence, obligations de notification |
| **Opérateur de lancement** | SpaceX, Rocket Lab, ISRO, Arianespace | Conformité à la CDS, limites de masse et de volume, calendrier, paiement | Exigences d'interface, fenêtre de lancement, manifeste |
| **Segment sol** | KSAT, SSC, SatNOGS, stations propres | Compatibilité des fréquences, volume de données, durée de contact | Disponibilité des stations, couverture géographique |
| **Consommateurs de données** | Archives (p. ex. EODMS), API, agences partenaires | Format des données (NetCDF, GeoTIFF), normes de métadonnées, délais | Normes de format, accords de diffusion |
| **Grand public** | Contribuables (pour les missions financées sur fonds publics) | Rapport coût-efficacité, transparence, bénéfice pour la société | Attentes politiques, engagement du public |
| **Environnement orbital** | Autres exploitants de satellites, communauté des débris | Atténuation des débris, propreté du spectre, évitement des collisions | Lignes directrices de l'IADC, ISO 24113, règle des 5 ans de la FCC |

Les noms d'entreprises cités ici sont des exemples représentatifs et non des recommandations.

### 4.2.3 Matrice d'analyse des parties prenantes

Pour chaque partie prenante, consignez cinq attributs :

| Attribut | Description | Échelle |
|-----------|-------------|-------|
| **Nom / rôle** | Qui sont-ils ? | Texte |
| **Besoins** | Qu'attendent-ils de la mission ? | Texte (précis, mesurable lorsque c'est possible) |
| **Contraintes** | Quelles limites imposent-ils ? | Texte (obligatoire ou souhaitable) |
| **Priorité** | Dans quelle mesure est-il critique de satisfaire cette partie prenante ? | Primaire (à satisfaire impérativement) / secondaire (à satisfaire de préférence) / tertiaire (souhaitable) |
| **Influence** | Quel pouvoir ont-ils sur la mission ? | Forte / moyenne / faible |

> **Pratique industrielle.** Pour la Mission de la Constellation RADARSAT (RCM), l'analyse des parties prenantes a identifié plus de 20 groupes distincts, dont le MDN (surveillance maritime), Environnement Canada (surveillance des glaces de mer), Agriculture et Agroalimentaire Canada (surveillance des cultures), Ressources naturelles Canada (foresterie), Sécurité publique Canada (intervention en cas de catastrophe) et des partenaires internationaux. Chaque partie prenante avait ses propres modes d'imagerie prioritaires, exigences de couverture et besoins de latence des données. Le défi d'ingénierie système consistait à concevoir une constellation de 3 satellites satisfaisant tous ces besoins au sein d'une architecture système unique — un exemple classique d'optimisation multipartite.

---

## 4.3 Objectifs de mission et hiérarchie MoE/MoP/TPM

### 4.3.1 Du besoin aux objectifs

Les objectifs traduisent l'énoncé du problème en buts précis et vérifiables. Chaque objectif doit comporter :

| Attribut | Description | Exemple |
|-----------|-------------|---------|
| **Texte** | Énoncé clair de ce que la mission accomplira | « Fournir une imagerie multispectrale à 10 m de GSD sur la région cible » |
| **Priorité** | Primaire (la mission échoue sans lui) ou secondaire (souhaitable) | Primaire |
| **Critère mesurable** | Comment savoir que l'objectif est atteint — une valeur assortie d'une unité | « GSD $\leq$ 10 m au nadir, 4+ bandes spectrales, revisite $\leq$ 5 jours » |
| **Type** | Catégorie de l'objectif | Observation, télécommunications, navigation, science, démonstration technologique |

### 4.3.2 Rédiger de bons objectifs

| Bon objectif | Pourquoi il est bon |
|---------------|---------------|
| « Fournir une imagerie multispectrale à 10 m de GSD, avec 4+ bandes, sur la région cible (30° S–30° N), avec une revisite $\leq$ 5 jours et une latence des données $\leq$ 24 h » | Précis (10 m, 4 bandes, emprise géographique), mesurable (tous les critères ont une valeur et une unité), pertinent pour l'agriculture, atteignable avec la technologie CubeSat |
| « Atteindre une probabilité de détection des navires par AIS de 99,5 % dans l'Atlantique Nord dans les 30 minutes suivant l'émission du navire » | Précis (AIS, Atlantique Nord), mesurable (99,5 %, 30 min), pertinent pour la sécurité maritime |

| Mauvais objectif | Pourquoi il est mauvais |
|--------------|-------------|
| « Prendre des photos depuis l'espace » | Ni précis ni mesurable, aucun critère de réussite |
| « Construire un CubeSat 3U » | C'est une solution, pas un objectif — cela ne dit rien de ce que la mission doit accomplir |
| « Démontrer une nouvelle technologie » | Quelle technologie ? Que signifie « démontrer » ? Comment savoir que c'est réussi ? |

### 4.3.3 La hiérarchie MoE / MoP / TPM

Ces trois mesures forment une chaîne qui va du besoin opérationnel au paramètre de conception suivi :

[Source : NASA SEH, sections 4.1.4, 4.2.4 et 6.7.3]

| Mesure | Ce qu'elle mesure | Qui la fixe | Exemple | Quand l'évaluer |
|---------|-----------------|-------------|---------|---------------|
| **MoE** (mesure d'efficacité) | Dans quelle mesure le système satisfait le besoin opérationnel | Utilisateurs / parties prenantes | « % des évaluations des cultures livrées dans les 5 jours suivant l'acquisition » | Phase E (exploitation) |
| **MoP** (mesure de performance) | Performances techniques du système | Ingénieur système | « GSD $\leq$ 10 m au nadir » | Phase C/D (vérification) |
| **TPM** (indicateur de performance technique) | Paramètre de conception suivi dans le temps | Équipe de conception | « Meilleure estimation actuelle de la masse de l'imageur par rapport à l'allocation (cible de 1,5 kg) » | Toutes les phases (en continu) |

La hiérarchie se lit de haut en bas, comme le montre la figure 4.1 pour l'exemple de la surveillance agricole : le besoin de la partie prenante est mesuré par une MoE, formulé en objectif de mission, mesuré par une MoP, rédigé sous forme d'exigence technique et suivi tout au long de la conception sous forme de TPM.

![Chaîne verticale allant du besoin de la partie prenante à la TPM, en passant par la MoE, l'objectif, la MoP et l'exigence, avec un exemple de surveillance agricole à chaque niveau.](../assets/figures/fig_moe_mop_tpm.png)

**Figure 4.1** — Du besoin de la partie prenante au paramètre de conception suivi. Chaque niveau de la chaîne est présenté avec son exemple de surveillance agricole, l'acteur responsable de la mesure et la phase du cycle de vie au cours de laquelle elle est évaluée : les MoE relèvent des utilisateurs et sont évaluées en exploitation, les MoP relèvent de l'ingénieur système et sont vérifiées en phase C/D, et les TPM relèvent de l'équipe de conception et sont suivies à chaque phase.

> **Équation clé.** Les mesures d'efficacité font souvent intervenir des probabilités et des durées, en lien avec les performances au niveau du système :
>
> $$MoE = P_{\text{detection}} \times P_{\text{data delivery}} \times f(T_{\text{latency}})$$
>
> Pour une mission d'observation de la Terre :
>
> $$MoE_{\text{coverage}} = \frac{A_{\text{imaged per revisit}}}{A_{\text{total target}}} \times (1 - P_{\text{cloud}})$$
>
> où $A_{\text{imaged per revisit}}$ dépend de la largeur de fauchée et de l'espacement des traces au sol, $A_{\text{total target}}$ est la surface de la zone cible et $P_{\text{cloud}}$ la probabilité de couverture nuageuse.

---

## 4.4 Du besoin à la conception : l'enchaînement

La figure 4.2 montre comment le besoin de la mission se traduit en décisions de conception sans que le besoin lui-même prescrive la conception.

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 520" style="max-width:700px; font-family: sans-serif;">
  <text x="350" y="25" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">Du besoin de la mission à la décision de conception</text>

  <!-- Level 1: Problem -->
  <rect x="50" y="45" width="600" height="45" rx="6" fill="#e8eaf6" stroke="#3949ab" stroke-width="2"/>
  <text x="70" y="63" font-size="10" font-weight="bold" fill="#1a237e">PROBLÈME</text>
  <text x="70" y="78" font-size="9" fill="#333">« Imagerie à 10 m, revisite de 5 jours, &lt; 10 M$ » — décrit CE QUI est nécessaire</text>

  <!-- Arrow -->
  <line x1="350" y1="90" x2="350" y2="110" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="105" font-size="8" fill="#888" font-style="italic">dérivation des objectifs</text>

  <!-- Level 2: Objective -->
  <rect x="50" y="115" width="600" height="45" rx="6" fill="#c5cae9" stroke="#3949ab" stroke-width="2"/>
  <text x="70" y="133" font-size="10" font-weight="bold" fill="#1a237e">OBJECTIF</text>
  <text x="70" y="148" font-size="9" fill="#333">« Fournir une imagerie multispectrale à 10 m de GSD, revisite ≤ 5 jours » — but mesurable</text>

  <!-- Arrow -->
  <line x1="350" y1="160" x2="350" y2="180" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="175" font-size="8" fill="#888" font-style="italic">compromis de mission (processus 17)</text>

  <!-- Level 3: Trade Decision -->
  <rect x="50" y="185" width="600" height="45" rx="6" fill="#fff9c4" stroke="#f9a825" stroke-width="2"/>
  <text x="70" y="203" font-size="10" font-weight="bold" fill="#e65100">DÉCISION DE COMPROMIS</text>
  <text x="70" y="218" font-size="9" fill="#333">« CubeSat dédié — aucun service existant n'offre à la fois revisite et résolution » — choix justifié</text>

  <!-- Arrow -->
  <line x1="350" y1="230" x2="350" y2="250" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="245" font-size="8" fill="#888" font-style="italic">dérivation des exigences</text>

  <!-- Level 4: Requirement -->
  <rect x="50" y="255" width="600" height="45" rx="6" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/>
  <text x="70" y="273" font-size="10" font-weight="bold" fill="#1b5e20">EXIGENCE</text>
  <text x="70" y="288" font-size="9" fill="#333">« Le système doit atteindre une GSD ≤ 10 m au nadir » — énoncé en « doit » vérifiable</text>

  <!-- Arrow -->
  <line x1="350" y1="300" x2="350" y2="320" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="315" font-size="8" fill="#888" font-style="italic">analyse de conception</text>

  <!-- Level 5: Design Choice -->
  <rect x="50" y="325" width="600" height="45" rx="6" fill="#e3f2fd" stroke="#1565c0" stroke-width="2"/>
  <text x="70" y="343" font-size="10" font-weight="bold" fill="#0d47a1">CHOIX DE CONCEPTION</text>
  <text x="70" y="358" font-size="9" fill="#333">« SSO à 500 km : GSD de 10 m avec 15 cm d'ouverture » — on précise maintenant le COMMENT</text>

  <!-- Arrow -->
  <line x1="350" y1="370" x2="350" y2="390" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="385" font-size="8" fill="#888" font-style="italic">choix des équipements</text>

  <!-- Level 6: Equipment -->
  <rect x="50" y="395" width="600" height="45" rx="6" fill="#fce4ec" stroke="#c62828" stroke-width="2"/>
  <text x="70" y="413" font-size="10" font-weight="bold" fill="#b71c1c">ÉQUIPEMENT</text>
  <text x="70" y="428" font-size="9" fill="#333">« Retenu : télescope XYZ, 15 cm d'ouverture, 1,5 kg, 8 W » — COMMENT au niveau composant</text>

  <!-- Side annotation -->
  <rect x="50" y="460" width="220" height="40" rx="4" fill="#e0e0e0" stroke="#9e9e9e" stroke-width="1"/>
  <text x="160" y="477" text-anchor="middle" font-size="9" fill="#333" font-weight="bold">À chaque niveau, l'équipe décide.</text>
  <text x="160" y="490" text-anchor="middle" font-size="8" fill="#666">L'outil de conception aide, sans imposer.</text>

  <defs>
    <marker id="arrowDown" markerWidth="8" markerHeight="6" refX="4" refY="6" orient="auto">
      <path d="M0,0 L4,6 L8,0" fill="#555"/>
    </marker>
  </defs>
</svg>

**Figure 4.2** — Du besoin de la mission à la décision de conception. Le problème et l'objectif décrivent CE QUI est nécessaire ; la décision de compromis justifie l'approche retenue ; ce n'est qu'à partir du niveau des exigences que l'équipe précise le COMMENT.

À chaque niveau de cette hiérarchie, l'équipe de conception prend des décisions éclairées par l'analyse et les études de compromis. Un outil de conception concourante accompagne ce processus par des calculs paramétriques et une vérification automatisée des contraintes, mais l'équipe conserve le pouvoir de décision.

---

## 4.5 Cadre de l'analyse de décision

### 4.5.1 Processus 17 : analyse de décision

Le processus 17 (analyse de décision) du NASA SEH fournit le cadre d'une évaluation structurée des solutions alternatives. Toute décision de conception importante devrait suivre ce processus afin que les décisions soient auditables, traçables et défendables.

[Source : NASA SEH, section 6.8, processus 17 : analyse de décision]

### 4.5.2 Les cinq éléments d'une étude de compromis rigoureuse

| Élément | Description | Écueil à éviter |
|---------|-------------|-----------------|
| **1. Énoncé de la décision** | Que décidons-nous ? Formulé sous forme de question. | Trop large (« Que devons-nous construire ? ») ou trop étroit (« Quelle roue de réaction ? ») pour la phase en cours |
| **2. Solutions alternatives** | Quelles sont les options ? Au moins 3, y compris « ne rien faire » | Solutions alternatives de façade conçues pour perdre ; omission d'options évidentes |
| **3. Critères** | Qu'est-ce qui compte ? Performances, coût, calendrier, risque, conformité | Omission d'un critère essentiel ; critères qui se recouvrent (double comptage) |
| **4. Pondérations** | Quelle est l'importance de chaque critère ? Normalisées pour que leur somme vaille 1,0 | Tous les critères pondérés à égalité (ce qui revient à dire que rien ne compte plus que le reste) ; pondérations fixées après avoir vu les notes |
| **5. Notation** | Quelle est la performance de chaque solution alternative ? | Échelle de notation incohérente ; biais d'ancrage ; conformisme de groupe |

### 4.5.3 Méthodes de pondération

| Méthode | Mode opératoire | Cas d'emploi privilégié | Limites |
|--------|-----------|-----------|------------|
| **Comparaison par paires** | Comparer les critères deux à deux ; compter les victoires. Poids = victoires / nombre total de comparaisons | Petit nombre de critères ($< 8$) | Préférences circulaires possibles ; ne rend pas compte de l'ampleur des écarts |
| **Pondération par amplitude (*swing weighting*)** | Pour chaque critère, évaluer la valeur du passage du pire au meilleur cas. Normaliser. | Critères d'unités et d'échelles différentes | Exige une compréhension claire des pires et meilleurs cas |
| **Affectation directe** | L'équipe discute et s'accorde sur les poids | Évaluation préliminaire rapide | Subjective ; dominée par les membres les plus loquaces |
| **AHP (*Analytic Hierarchy Process*)** | Comparaison par paires sur une échelle de rapports de 1–9 ; calcul du vecteur propre | Décisions complexes impliquant de nombreuses parties prenantes | Mathématiquement complexe ; contrôle de cohérence nécessaire |

> **Équation clé (comparaison par paires).** Pour $n$ critères, il y a $\frac{n(n-1)}{2}$ comparaisons par paires. Le poids brut du critère $i$ vaut
>
> $$w_i^{\text{raw}} = \sum_{j \neq i} p_{ij}$$
>
> où $p_{ij} = 1$ si le critère $i$ est préféré à $j$, 0,5 en cas d'égalité et 0 si $j$ est préféré. Le poids normalisé vaut
>
> $$w_i = \frac{w_i^{\text{raw}}}{\sum_{k=1}^{n} w_k^{\text{raw}}}$$

### 4.5.4 Méthodes de notation

| Type | Description | Exemple | Quand l'utiliser |
|------|-------------|---------|-------------|
| **Quantitative** | Valeur numérique normalisée sur 0–1 | Masse : 5 kg obtient 0,8, 10 kg obtient 0,4 | Lorsque des valeurs chiffrées fiables existent |
| **Qualitative** | Appréciation verbale convertie en nombre | « Excellent » = 1,0, « Bon » = 0,75, « Passable » = 0,5, « Médiocre » = 0,25 | Lorsque seul un jugement d'expert est disponible |
| **Seuil (GO/NO-GO)** | Critère éliminatoire appliqué avant la notation | « TRL $\geq 6$ exigé » — toute option sous le seuil est éliminée | Exigences non négociables |

### 4.5.5 Calcul du score pondéré

Pour chaque solution alternative $a$ évaluée sur $n$ critères :

> **Équation clé.**
>
> $$S(a) = \sum_{c=1}^{n} w_c \cdot s(a,c)$$
>
> où $w_c$ est le poids normalisé du critère $c$ et $s(a,c)$ la note normalisée (0–1) de la solution $a$ pour le critère $c$.
>
> Pour les critères « plus c'est élevé, mieux c'est » :
>
> $$s(a,c) = \frac{v(a,c) - v_{\min}(c)}{v_{\max}(c) - v_{\min}(c)}$$
>
> Pour les critères « plus c'est faible, mieux c'est » :
>
> $$s(a,c) = 1 - \frac{v(a,c) - v_{\min}(c)}{v_{\max}(c) - v_{\min}(c)}$$

### 4.5.6 Analyse de sensibilité

Le résultat d'une étude de compromis n'a de sens que s'il est **robuste** — c'est-à-dire si le classement ne change pas sous l'effet de petites perturbations des poids ou des notes. L'analyse de sensibilité permet de le vérifier :

| Méthode | Mode opératoire | Ce qu'elle révèle |
|--------|-----------|----------------|
| **Perturbation des poids** | Faire varier chaque poids de $\pm 20\%$, renormaliser, recalculer les scores | Les critères « pivots » susceptibles d'inverser le résultat |
| **Perturbation des notes** | Faire varier chaque note de $\pm 1$ niveau, recalculer | Les notes les plus incertaines et les plus influentes |
| **Analyse de seuil** | Pour chaque critère, déterminer le poids à partir duquel la solution classée 2e dépasse la 1re | L'ampleur de la variation des poids nécessaire pour inverser la décision |

> **Pratique industrielle.** Pour la constellation Iridium NEXT (66 satellites opérationnels + 6 de réserve en orbite), l'étude de compromis initiale sur l'architecture de la constellation a comparé des configurations Walker Delta, Walker Star et hybrides selon 12 critères, dont la couverture mondiale, le temps de revisite, la géométrie des liaisons intersatellites, le coût de lancement et le risque lié aux débris orbitaux. L'analyse de sensibilité a montré que le classement restait robuste pour toutes les perturbations de poids jusqu'à $\pm 30\%$, ce qui a donné une grande confiance dans la configuration Walker Star retenue, à 780 km d'altitude.

---

## 4.6 Solutions spatiales et non spatiales

### 4.6.1 L'étude de compromis la plus importante

Avant de s'engager dans la construction d'un satellite, les équipes doivent évaluer honnêtement si des solutions existantes répondent au besoin. C'est l'étude de compromis la plus importante du cycle de vie de la mission, car elle détermine si le projet dans son ensemble doit être poursuivi.

### 4.6.2 Catégories de solutions alternatives

| Catégorie | Exemples | Points forts | Points faibles |
|----------|---------|-----------|-----------|
| **Données gratuites existantes** | Copernicus Sentinel-2, Landsat 8/9 | Coût d'acquisition nul, qualité éprouvée, longues archives | Résolution et revisite imposées, aucune maîtrise de la programmation |
| **Achat de données commerciales** | Planet (SuperDove), Maxar (WorldView), ICEYE (radar à synthèse d'ouverture) | Haute résolution, programmation rapide, aucun risque de développement | Coût récurrent, limites des droits sur les données, dépendance au fournisseur |
| **Moyens aériens (drones/avions)** | Drones de relevé, P-3 Orion, Twin Otter | Très haute résolution ($< 1$ m), planification souple | Couverture limitée, dépendance à la météo, contraintes réglementaires |
| **Capteurs au sol** | Réseaux IoT, stations météorologiques, marégraphes | Surveillance continue, faible coût unitaire | Mesures ponctuelles uniquement, aucune couverture spatiale |
| **Satellite dédié** | Nouveau CubeSat, petit satellite ou microsatellite | Maîtrise totale, instrument sur mesure, propriété intellectuelle | Coût élevé (2–50 M$), risque de développement, calendrier de 2–5 ans |
| **Constellation** | Plusieurs satellites dédiés | Couverture mondiale, revisite courte ($< 1$ jour) | Coût bien plus élevé, complexité opérationnelle |
| **Charge utile hébergée** | Charge utile sur la plateforme d'un autre exploitant | Coût moindre, risque partagé sur la plateforme | Orbite imposée, maîtrise limitée, dépendance calendaire |

### 4.6.3 Critères de décision : quand le spatial est-il justifié ?

**Le spatial n'est probablement PAS la bonne réponse lorsque :**

- des données gratuites existantes (Sentinel-2, Landsat) satisfont les besoins de résolution et de revisite ;
- la couverture requise est locale (les drones ou les avions sont moins chers et offrent une meilleure résolution) ;
- le débit est très faible (des capteurs au sol avec une collecte par réseau cellulaire ou IoT par satellite suffisent) ;
- le budget ne permet pas d'atteindre le coût minimal d'un satellite viable (env. 2 M$ pour un CubeSat 3U de base, valeur indicative 2026) ;
- la maturité technologique est trop faible pour le calendrier disponible.

**Le spatial est probablement justifié lorsque :**

- une couverture mondiale ou étendue est nécessaire simultanément ;
- une surveillance permanente est exigée (24/7 ou revisite très fréquente $< 5$ jours) ;
- l'utilisateur a besoin de la propriété des données et de la maîtrise de la programmation des acquisitions ;
- aucun service existant ne fournit le type de mesure requis (p. ex. longueur d'onde ou polarisation particulières) ;
- des exigences réglementaires ou de souveraineté imposent un contrôle national du capteur.

### 4.6.4 Dimensionnement d'une constellation

Pour les missions qui exigent une revisite courte, le nombre de satellites détermine le coût :

> **Équation clé.** Pour une constellation Walker Delta à l'altitude $h$, avec un demi-angle de fauchée $\eta$, le nombre de plans orbitaux $P$ et de satellites par plan $S$ nécessaires pour un temps de revisite $T_{\text{rev}}$ vaut approximativement
>
> $$P \times S \geq \frac{2\pi R_E}{v_{\text{ground}} \times T_{\text{rev}} \times \tan(\eta)}$$
>
> où $v_{\text{ground}} \approx 7.1$ km/s (vitesse de la trace au sol à 500 km) et $\eta$ est lié à la largeur de fauchée $W$ de l'instrument par $\eta = W / (2 R_E)$ pour les petits angles.
>
> En pratique, le coût d'une constellation croît de façon sous-linéaire grâce aux effets d'apprentissage :
>
> $$C_{\text{total}} = C_1 \times \sum_{i=1}^{N} i^{\log_2(L)}$$
>
> où $C_1$ est le coût de la première unité, $N$ le nombre de satellites et $L$ le facteur d'apprentissage (en général 0,90–0,95 pour les petites séries, 0,85 pour les grandes séries comme les SuperDove de Planet). Le chapitre 16 approfondit la courbe d'apprentissage dans le cadre de l'estimation des coûts.

---

## 4.7 Documenter la décision de compromis

Toute étude de compromis doit produire un **dossier de décision auditable**. Le processus 17 du NASA SEH exige de documenter :

| Élément | Contenu | Finalité |
|---------|---------|---------|
| **Énoncé de la décision** | Ce qui a été décidé | Clarté |
| **Solutions alternatives examinées** | Toutes les options évaluées, y compris celles rejetées | Exhaustivité |
| **Critères et poids** | Ce qui comptait, et dans quelle mesure | Transparence |
| **Justification des notes** | Pourquoi chaque solution a obtenu sa note | Auditabilité |
| **Résultat et recommandation** | La solution retenue et son score total | Traçabilité de la décision |
| **Analyse de sensibilité** | Robustesse du résultat | Confiance |
| **Risques de l'option retenue** | Ce qui pourrait mal tourner avec la démarche choisie | Conscience des risques |
| **Responsable et date** | Qui a décidé, et quand | Responsabilisation |

> **Pratique industrielle.** Le Service hydrographique du Canada a comparé l'achat de données radar commerciales (ICEYE, Capella) à un satellite dédié pour la surveillance maritime dans l'Arctique. L'étude de compromis a documenté 8 solutions alternatives selon 11 critères, avec des poids fixés par un panel de parties prenantes comprenant le MDN, Transports Canada et la Garde côtière canadienne (GCC). La décision d'utiliser les données de la RCM complétées par des acquisitions radar commerciales programmées — plutôt que de construire un nouveau satellite — a permis d'économiser environ 100 M$ tout en satisfaisant 90 % des exigences de connaissance du domaine maritime.

---

## 4.8 Concept d'opérations

Un **concept d'opérations (ConOps)** décrit comment la mission sera exploitée pour fournir ce qu'exigent les objectifs : quels éléments existent, par quelles phases passe la mission, dans quels modes se trouve l'engin spatial et comment les données circulent de l'instrument jusqu'à l'utilisateur. Il fait le lien entre les objectifs du §4.3 et les exigences du chapitre 5, et c'est le premier document dont une équipe de conception concourante a besoin pour dimensionner quoi que ce soit. L'annexe S du NASA SEH en donne un plan complet ; cette section traite des quatre éléments qui pilotent la conception en début de projet.

### 4.8.1 Les trois segments d'une mission spatiale

Toute mission spatiale comprend trois segments qui doivent être conçus ensemble : le **segment spatial** (plateforme, charge utile et télécommunications qui les relient au sol), le **segment sol** (opérations au sol — commande, télémesure, restitution d'orbite — et centre de données de la charge utile qui reçoit, traite et archive les données) et le **segment utilisateur** (produits de données, services, portails et formation grâce auxquels les utilisateurs finaux en tirent de la valeur). Le ConOps nomme les éléments de chaque segment et les interfaces entre eux — TM/TC en bande S, données de charge utile en bande X ou Ka, métadonnées d'orbite et produits traités sur les réseaux terrestres. La décomposition détaillée des segments, leurs interfaces et le schéma fonctionnel du segment spatial font l'objet du chapitre 8, §8.1 ; le segment sol lui-même est conçu au chapitre 17. Au stade du ConOps, il suffit de tracer un schéma d'architecture comportant les segments, les systèmes externes dont ils dépendent (GNSS, satellites relais, capteurs in situ) et chaque liaison, étiquetée avec son type de données et sa bande de fréquences.

### 4.8.2 Phases de la mission

Les phases opérationnelles de la mission — distinctes des phases de développement du chapitre 1, §1.4 — sont présentées à la figure 4.3 et détaillées dans le tableau ci-dessous. Chacune a ses propres activités, sa durée et ses risques dominants, et le ConOps doit indiquer ce que font l'engin spatial et le segment sol au cours de chacune.

![Chronologie des opérations de la mission, de la LEOP au retrait de service, en passant par la recette en orbite et les opérations nominales et prolongées.](../assets/figures/fig_conops_timeline.png)

**Figure 4.3** — Chronologie des opérations d'une mission CubeSat type : LEOP, recette en orbite, opérations nominales et prolongées, et retrait de service, avec des durées indicatives.

| Phase | Durée (CubeSat type) | Activités | Principaux risques |
|-------|--------------------------|------------|-----------|
| **LEOP** | 1–3 jours | Déploiement, déploiement des antennes, premier contact, premier bilan de santé | Échec du déploiement, culbutage, absence de contact |
| **Recette en orbite** | 2–4 semaines | Vérification des sous-systèmes, étalonnage, première lumière, restitution d'orbite | Anomalies, problèmes d'étalonnage |
| **Opérations nominales** | De quelques mois à quelques années | Acquisitions de routine, liaison descendante, maintien de l'orbite | Dégradation des composants, anomalies |
| **Opérations prolongées** | Au-delà de la durée de vie nominale | Poursuite des opérations avec des performances dégradées | Dégradation du générateur solaire, épuisement des ergols |
| **Retrait de service** | De quelques jours à quelques mois | Passivation, manœuvre de désorbitation ou déclin naturel | Défaillance du dispositif de désorbitation |

### 4.8.3 Modes opérationnels

Un **mode opérationnel** est une configuration définie de l'engin spatial : quels sous-systèmes sont actifs, comment il est pointé, quelle puissance il consomme et quelles données circulent. Les modes existent parce qu'un CubeSat ne peut pas tout faire à la fois — la production de puissance est limitée à environ 7–25 W pour un 3U à panneaux déployables — et parce que les opérateurs et la logique FDIR de bord ont besoin d'un petit nombre d'états bien maîtrisés vers lesquels commander et se replier. Un mode survie à charge minimale et à pointage solaire constitue le point d'ancrage ; les modes scientifique, de liaison descendante et de manœuvre ajoutent leur charge par-dessus. Le tableau 4.1 illustre ce concept avec trois des modes de l'exemple fil rouge du CubeSat 3U d'OT ; le tableau complet des modes de l'engin, les transitions entre modes et les règles FDIR qui les déclenchent sont donnés au chapitre 18.

**Tableau 4.1** — Modes opérationnels illustratifs de l'exemple fil rouge du CubeSat 3U d'OT (tableau complet, avec le mode nominal/veille à 4 W, au chapitre 18).

| Mode | Sous-systèmes actifs | Pointage | Puissance | Flux de données |
|------|-------------------|----------|-------|-----------|
| **Survie** | EPS, OBC, TTC (balise), SCAO (grossier) | Pointage solaire | 2 W | Balise uniquement |
| **Prise de vue** | + charge utile, SCAO (pointage fin) | Nadir ou cible | 8 W | Instrument → stockage OBC |
| **Liaison descendante** | + TTC (pleine puissance d'émission) | Poursuite de la station sol | 10 W | OBC → émetteur → station sol |

### 4.8.4 Fonctionnement par intermittence

Tous les modes ne peuvent pas fonctionner simultanément, et la chronologie de l'orbite détermine ce qui peut se dérouler, et à quel moment. Pour une orbite type de 95 minutes à 500 km en SSO :

- 60 min d'éclairement, 35 min d'éclipse ;
- env. 10 min de prise de vue par orbite (rapport cyclique d'env. 10 %) ;
- env. 8 min de liaison descendante par passage (1–2 passages par jour au-dessus d'une seule station sol) ;
- env. 42 min en mode nominal/veille ;
- 35 min d'éclipse (alimentation sur batterie).

La puissance moyenne consommée sur l'orbite est la somme des puissances des modes pondérées par leurs rapports cycliques ; c'est elle — avec la durée de l'éclipse — qui dimensionne le générateur solaire et la batterie. Le ConOps doit donc indiquer le rapport cyclique de chaque mode. Les équations de dimensionnement elles-mêmes, ainsi que le bilan de puissance résolu d'UniSat-1, sont donnés au chapitre 9, §9.2–§9.3.

[Source : Wertz et al., SMAD4, chapitre 11 ; méthodologie de bilan de puissance de l'ECSS-E-ST-20C]

### 4.8.5 Flux de données

Le ConOps doit retracer le parcours des données de l'instrument jusqu'à l'utilisateur. La figure 4.4 présente la chaîne de bout en bout et le paramètre qui dimensionne chaque étape :

![Chaîne de données horizontale allant de l'instrument à la livraison aux utilisateurs, en passant par le stockage à bord, la liaison descendante, la réception au sol, le traitement L0–L2 et l'archivage.](../assets/figures/fig_data_pipeline.png)

**Figure 4.4** — La chaîne de données de bout en bout, regroupée par segment. Le segment spatial produit, stocke et transmet les données ; le segment sol les reçoit, les traite (L0 → L1 → L2) et les archive ; le segment utilisateur reçoit les produits. Le paramètre de dimensionnement clé de chaque étape est indiqué en dessous, et la chaîne n'est soutenable que si la capacité quotidienne de liaison descendante est supérieure ou égale au volume de données produit chaque jour.

| Étape | Paramètre clé | Dimensionné par |
|-------|--------------|---------|
| Production de données | Go/jour | Débit de la charge utile $\times$ rapport cyclique de prise de vue |
| Stockage à bord | Go | Doit contenir $\geq 1$ jour de données ($2\times$ pour la marge) |
| Liaison descendante par passage | Go/passage | Débit de la liaison $\times$ durée de contact par passage |
| Traitement | heures | Complexité des algorithmes, infrastructure de calcul |
| Livraison aux utilisateurs | heures | API d'archive, bande passante du réseau |

Pour que le système soit soutenable, la capacité quotidienne de liaison descendante doit être supérieure ou égale à la production quotidienne de données ; sinon, les données s'accumulent à bord et la mémoire finit par saturer. Les leviers sont le débit de la liaison, le nombre de passages, la durée de contact par passage et le volume de données produit (rapport cyclique, compression à bord, transmission sélective). Le bilan de données qui quantifie cet équilibre est développé au chapitre 11, §11.9, et le dimensionnement du stockage à bord au chapitre 12.

---

## 4.9 Retour sur UniSat-1 : pourquoi un 1U plutôt qu'un 2U ou un 3U ?

L'équipe d'UniSat-1 doit justifier le choix d'un format 1U pour sa démonstration technologique de magnétomètre MEMS. Il s'agit d'un exercice classique du processus 17 (analyse de décision).

**Énoncé de la décision :** « Quel format de CubeSat se prête le mieux à une démonstration technologique de magnétomètre MEMS dans le respect des contraintes de budget et de calendrier de l'université ? »

**Solutions alternatives** (coûts indicatifs, 2026) :

| Solution | Masse maximale | Volume interne | Coût type | Durée de développement |
|-------------|-----------|-----------------|-------------|----------|
| 1U | 1,33 kg | env. 1000 cm³ | 50–200 k€ | 6–12 mois |
| 2U | 2,66 kg | env. 2000 cm³ | 100–400 k€ | 12–18 mois |
| 3U | 4,0 kg | env. 3000 cm³ | 200–800 k€ | 18–24 mois |

**Critères et notation :**

| Critère | Poids | 1U | 2U | 3U | Justification |
|-----------|--------|-----|-----|-----|-----------|
| Coût | 0,35 | 1,0 | 0,5 | 0,2 | Le budget total de l'université est de 150 k€ |
| Calendrier | 0,25 | 1,0 | 0,6 | 0,3 | Lancement exigé sous 12 mois |
| Intégration de la charge utile | 0,20 | 0,8 | 1,0 | 1,0 | Le capteur MEMS fait 50 g et 0,2 W — il tient facilement dans un 1U |
| Simplicité de conception | 0,10 | 1,0 | 0,7 | 0,5 | Équipe plus réduite, moins de sous-systèmes |
| Retour de données | 0,10 | 0,5 | 0,7 | 1,0 | Plus de volume permet de meilleures télécommunications, mais 9600 bit/s suffisent pour une charge utile < 1 kbit/s |
| **Total pondéré** | | **0,91** | **0,67** | **0,50** | |

**Résultat :** le 1U l'emporte nettement. La charge utile magnétomètre MEMS (50 g, 0,2 W, < 1 kbit/s) n'a nul besoin du volume, de la masse ou de la puissance supplémentaires qu'offrirait un 2U ou un 3U. Le surcoût et l'allongement du calendrier d'une plateforme plus grande ne se justifient pas.

**Contrôle de sensibilité :** supposons que le commanditaire accorde beaucoup moins d'importance au coût et au calendrier que ne le pensait l'équipe, et que les poids deviennent 0,15 pour le coût, 0,15 pour le calendrier et 0,40 pour le retour de données (intégration de la charge utile et simplicité inchangées). Les totaux deviennent 0,76 (1U), 0,72 (2U) et 0,73 (3U) : le 1U reste en tête, mais l'écart passe de 0,24 à 0,03. Le retour de données est donc le *critère pivot* — la décision est robuste aux poids que l'équipe retient effectivement, mais une partie prenante qui privilégierait avant tout le volume de données pourrait raisonnablement aboutir à une autre réponse, et le dossier de décision doit le mentionner.

**Leçon clé :** ne surdimensionnez pas la plateforme pour une charge utile simple. Le format 1U impose des contraintes salutaires qui obligent l'équipe à se concentrer sur l'objectif de la mission plutôt qu'à ajouter des capacités inutiles.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Énoncé du problème | Définit CE QUI est nécessaire, et non COMMENT le résoudre ; répond aux questions quoi, qui, impact, contraintes |
| Analyse des parties prenantes | Identifier tous les acteurs ayant un intérêt légitime ; consigner besoins, contraintes, priorité, influence |
| Objectifs | Doivent être précis, mesurables et traçables jusqu'aux besoins des parties prenantes via la chaîne MoE/MoP/TPM |
| Structure d'une étude de compromis | 5 éléments : décision, solutions alternatives, critères, poids, notes ; doit inclure une analyse de sensibilité |
| Spatial ou non spatial | Des services existants répondent peut-être déjà au besoin — les évaluer honnêtement avant de s'engager à construire |
| Documentation de la décision | Chaque décision de compromis doit avoir une justification auditable conformément au processus 17 |
| ConOps | Trois segments (spatial, sol, utilisateur) ; des phases allant de la LEOP au retrait de service ; les modes opérationnels et leurs rapports cycliques déterminent le bilan de puissance (chapitre 9) |
| Chaîne de données | La capacité quotidienne de liaison descendante doit être supérieure ou égale à la production quotidienne de données (chapitre 11) |

---

## Exercices

1. **Réécrire un énoncé de solution.** La note d'un commanditaire indique : « Nous voulons un CubeSat 6U doté d'une caméra hyperspectrale en orbite héliosynchrone à 550 km pour observer les efflorescences algales des Grands Lacs. » Réécrivez-la sous forme d'énoncé de problème répondant aux quatre questions du §4.1.2, en inventant des chiffres plausibles pour l'impact et les contraintes. Énumérez ensuite trois solutions alternatives à un satellite dédié que votre énoncé laisse ouvertes et que la note avait écartées.

2. **Analyse des parties prenantes.** Pour un CubeSat 3U d'observation de la Terre fournissant chaque semaine des images NDVI des Prairies canadiennes à un ministère provincial de l'Agriculture, identifiez au moins six parties prenantes relevant d'au moins cinq des catégories du §4.2.2 et remplissez pour chacune la matrice à cinq attributs du §4.2.3. Identifiez une paire de parties prenantes dont les besoins entrent en conflit et proposez une manière de résoudre ce conflit au niveau des objectifs.

3. **Chaîne MoE/MoP/TPM.** Retracez la hiérarchie complète du §4.3.3 — besoin de la partie prenante, MoE, objectif de mission, MoP, exigence technique, TPM — pour (a) l'objectif de suivi des cultures du §4.3.2 et (b) l'objectif de détection des navires par AIS. Pour chaque TPM, indiquez la grandeur estimée au mieux à ce jour, son allocation et le poste du tableau 1.4 qui en est responsable.

4. **Pondération par paires (échauffement).** Exercez-vous à la méthode de comparaison par paires du §4.5.3 en pondérant quatre critères pour le choix d'un restaurant le midi — goût, prix, équilibre nutritionnel, rapidité — selon vos propres préférences, puis notez trois options sur une échelle de 0–1 et calculez le total pondéré. Recommencez ensuite l'exercice pour les cinq critères du §4.9 et comparez les poids obtenus à ceux que l'équipe d'UniSat-1 a fixés par affectation directe.

5. **Notation pondérée et sensibilité.** Trois charges utiles d'imagerie sont comparées pour le CubeSat 3U d'OT : A (masse 1,2 kg, puissance 6 W, GSD 8 m, TRL 8, coût 120 k€), B (0,9 kg, 4 W, 12 m, TRL 9, 60 k€) et C (1,5 kg, 9 W, 5 m, TRL 6, 200 k€). Avec les critères masse, puissance, GSD, TRL et coût, pondérés respectivement 0,15, 0,15, 0,30, 0,20 et 0,20, normalisez chaque critère à l'aide des équations du §4.5.5 (identifiez ceux pour lesquels « plus c'est élevé, mieux c'est »), calculez le score pondéré de chaque solution et classez-les. Effectuez ensuite une analyse de sensibilité par perturbation de ±20 % de chaque poids, l'un après l'autre, et indiquez si le classement change à un moment quelconque. Enfin, appliquez un critère de seuil « TRL ≥ 7 » et indiquez comment le résultat évolue.

6. **Spatial ou non ?** Un office de protection de la nature souhaite surveiller une fois par jour le niveau d'eau de 40 réservoirs répartis dans l'Ontario avec une précision de 10 cm, avec un budget de 3 M$ sur 5 ans. À l'aide du §4.6, évaluez au moins quatre catégories de solutions alternatives au regard de ce besoin, indiquez laquelle vous recommanderiez et pourquoi, et rédigez le dossier de décision du §4.7 correspondant à votre recommandation (avec au moins deux risques liés à l'option retenue).

7. **Dimensionnement d'une constellation.** À l'aide du §4.6.4, estimez le nombre de satellites nécessaires pour une revisite de 1 jour à l'équateur avec une fauchée de 50 km à 500 km d'altitude. Estimez ensuite le coût total de cette constellation si la première unité coûte \$4M et que le facteur d'apprentissage vaut 0,90, puis comparez avec un facteur de 0,85. Quelle part du total la courbe d'apprentissage permet-elle d'économiser dans chaque cas par rapport à $N \times C_1$ ?

8. **ConOps d'UniSat-1.** Rédigez un plan de ConOps d'une page pour UniSat-1 (chapitre 1, §1.7) : les trois segments et leurs liaisons, les cinq phases opérationnelles avec des durées adaptées à une mission 1U de 6 mois, et un tableau des modes au format du tableau 4.1 comportant au moins trois modes, en estimant la puissance de chaque mode à partir des valeurs des sous-systèmes données au chapitre 1, §1.7. Quels modes d'UniSat-1 le CubeSat 3U d'OT possède-t-il aussi, et de quels modes du 3U UniSat-1 n'a-t-il pas besoin ?

9. **Puissance moyenne sur l'orbite à partir des rapports cycliques.** À l'aide de la chronologie de l'orbite de 95 minutes du §4.8.4 et des puissances des modes du tableau 4.1 (en prenant 4 W pour le mode nominal/veille et 3,5 W pour la charge en éclipse, comme au chapitre 8, tableau 8.4, et au chapitre 18, tableau 18.1), calculez la puissance moyenne consommée sur l'orbite par le CubeSat 3U d'OT comme somme des puissances des modes pondérées par leurs rapports cycliques. Si le rapport cyclique de prise de vue est doublé pour atteindre 20 %, de combien la consommation moyenne sur l'orbite augmente-t-elle ? Quels deux paramètres de conception l'ingénieur puissance du tableau 1.4 devrait-il alors réexaminer (voir le chapitre 9) ?

10. **Équilibre des données.** L'imageur du CubeSat 3U d'OT produit 150 Mbit/s pendant les prises de vue, à raison de 10 minutes par orbite sur 15 orbites par jour, et la liaison descendante en bande S fournit 2 Mbit/s sur deux passages de 8 minutes par jour avec une efficacité protocolaire de 80 %. Calculez le volume de données produit chaque jour et la capacité quotidienne de liaison descendante, indiquez si le système est équilibré et — dans le cas contraire — classez les quatre leviers énumérés au §4.8.5 selon l'ampleur de la modification que chacun exigerait pour combler l'écart. Quel levier actionneriez-vous en premier, et quels autres bilans (chapitre 8) seraient touchés ?

---

## Références

1. NASA, *Systems Engineering Handbook* (SP-2016-6105 Rev 2), 2016, sections 4.1, 4.4, 6.8, annexe C et annexe S. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
2. NASA, *NPR 7123.1D — Systems Engineering Processes and Requirements*, 2020, sections 3.2.1, 3.2.4 et 3.5.8. [https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_)
3. ECSS, *ECSS-E-ST-10C — System Engineering General Requirements*, 2009, section 5.1. [https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/](https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/)
4. ECSS, *ECSS-M-ST-10C Rev.1 — Space Project Management*, 2009, section 5.3. [https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/](https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/)
5. Wertz, J.R. et al., *Space Mission Engineering : The New SMAD* (SMAD4), Microcosm Press, 2011, chapitres 1–3 et 14. [https://www.microcosminc.com/](https://www.microcosminc.com/)
6. Saaty, T.L., *The Analytic Hierarchy Process*, McGraw-Hill, 1980. [https://doi.org/10.1016/0377-2217(90)90057-I](https://doi.org/10.1016/0377-2217(90)90057-I)
