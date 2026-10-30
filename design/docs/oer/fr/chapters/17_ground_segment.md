# Chapitre 17 — Architecture du segment sol

> **Lectures préalables conseillées.** ECSS-E-ST-70C (*Ground systems and operations*) ; CCSDS 131.0-B (*TM synchronisation and channel coding*), CCSDS 231.0-B (*TC synchronisation and channel coding*) et CCSDS 133.0-B (*Space Packet Protocol*) ; NASA *DSN Telecommunications Link Design Handbook* (810-005) pour le haut de l'échelle des grandes antennes. Ce chapitre s'appuie sur le bilan de liaison et les types de stations sol du chapitre 11 (§11.7–§11.9), sur la géométrie des passages du chapitre 7, §7.4.1, et sur les fonctions du segment sol F-G01…F-G04 allouées au chapitre 6, §6.2.4 ; les phases du cycle de vie dans lesquelles il s'inscrit sont celles de la figure 1.4 du chapitre 1.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez capable de :

1. Décrire les composants d'une architecture de segment sol (réseau de stations sol, système de contrôle de mission, dynamique du vol, planification de mission, traitement des données)
2. Calculer le temps de contact avec une station sol et le volume de données par passage pour une orbite et un masque d'élévation donnés
3. Expliquer la pile de protocoles CCSDS des communications spatiales et choisir un schéma de correction d'erreurs directe
4. Concevoir un réseau de stations sol pour une orbite et un besoin quotidien de liaison descendante donnés
5. Construire une chronologie des opérations de mission du lancement à la fin de vie, avec les effectifs par phase

Les produits et logiciels de fournisseurs cités dans ce chapitre sont des exemples représentatifs et non des recommandations ; les prix sont indicatifs (2026).

---

## 17.1 Architecture du segment sol

Le segment sol regroupe tout ce qui, au sol, soutient la mission spatiale. Il est souvent sous-estimé au début de la conception de la mission, alors qu'il représente 5–15 % du coût total de la mission (le chapitre 16, §16.2.1, alloue 5 % au segment sol et 5 % de plus aux opérations) et qu'il est essentiel à sa réussite : un satellite que l'on ne peut pas commander, ou dont on ne peut pas recevoir les données, n'a pas de mission.

*[Source : ECSS-E-ST-70C (*Ground Systems and Operations*)]*
*[URL : https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/]*

### 17.1.1 Composants du segment sol

La figure 17.1 montre les cinq blocs fonctionnels et le réseau de données qui les relie ; la liaison RF avec le segment spatial entre par le réseau de stations sol, et les produits de la mission sortent du bloc de traitement des données vers le segment utilisateur. Ces cinq blocs fonctionnels se retrouvent dans tout segment sol, si petit soit-il ; dans un projet universitaire de CubeSat, ils peuvent tous tourner sur un seul ordinateur dans une seule pièce, mais ils restent cinq fonctions distinctes, avec des interfaces distinctes.

![Schéma fonctionnel du segment sol](../assets/figures/fig_ground_segment.png)

**Figure 17.1** — Schéma fonctionnel du segment sol. Le réseau de stations sol, le système de contrôle de mission, le système de dynamique du vol, le système de planification de mission et le traitement et l'archivage des données sont reliés par un réseau de données ; l'interface RF avec le segment spatial entre par le réseau de stations sol et les produits de la mission quittent le bloc de traitement des données vers le segment utilisateur.

### 17.1.2 Composants d'une station sol

| Composant | Fonction | Spécification typique |
|-----------|----------|---------------------|
| **Antenne** | Émettre les commandes en liaison montante, recevoir la télémesure en liaison descendante | Parabole de 3–13 m (bandes S/X) ; Yagi/tourniquet (UHF) |
| **Frontal RF** | Amplificateur faible bruit (LNA), amplificateur de puissance, filtres | Facteur de bruit du LNA < 1 dB ; amplificateur de puissance de 50–500 W |
| **Modem/bande de base** | Modulation/démodulation, codage/décodage | Conforme CCSDS ; BPSK/QPSK/8PSK |
| **Système de poursuite** | Pointage de l'antenne, poursuite Doppler, mesure de distance (ranging) | Poursuite automatique ou programmée |
| **Acquisition des données** | Enregistrer les données brutes de bande de base pour post-traitement | Baie de disques à haut débit |
| **Référence de temps** | Oscillateur asservi au GPS pour la synchronisation temporelle | Précision < 1 µs |

Les types de stations sol accessibles à une mission CubeSat — réseaux bénévoles, paraboles universitaires, réseaux commerciaux et (pour l'espace lointain) le DSN —, avec leur $G/T$ et des prix indicatifs, sont présentés en tableau au chapitre 11, §11.7.1, et ne sont pas repris ici.

### 17.1.3 Système de contrôle de mission (MCS)

| Fonction | Description | Outils (représentatifs) |
|----------|------------|-------|
| **Traitement de la télémesure** | Décoder, décommuter, afficher et archiver les paquets TM | COSMOS, YAMCS, EGOS (ESA) |
| **Génération des télécommandes** | Créer, valider, coder et envoyer les paquets TC | Mêmes outils MCS |
| **Programmation des passages** | Programmer le temps d'antenne, planifier les fenêtres de visibilité | STK, GMAT, programmateurs sur mesure |
| **Surveillance et contrôle** | Surveillance de santé en temps réel, contrôle de limites, gestion des alarmes | Tableaux de bord du MCS |
| **Gestion des anomalies** | Détecter, diagnostiquer et résoudre les anomalies | Procédures + jugement d'expert (chapitre 18, §18.5) |

### 17.1.4 Système de dynamique du vol (FDS)

| Fonction | Description | Entrées |
|----------|------------|--------|
| **Restitution d'orbite** | Calculer l'orbite actuelle à partir des données de poursuite | Distance, Doppler, GPS (si embarqué) |
| **Prévision d'orbite** | Propager l'orbite pour la planification des passages | Vecteur d'état actuel, modèles de perturbations (chapitre 7) |
| **Planification des manœuvres** | Calculer le ΔV nécessaire au maintien d'orbite | Orbite cible, modèle de propulsion (chapitre 12, §12.2) |
| **Évaluation des conjonctions** | Prévoir les rapprochements avec des débris ou d'autres objets | Catalogue de TLE, orbite propre |
| **Planification de fin de vie** | Calculer la manœuvre de désorbitation ou le plan de passivation | Ergols restants, orbite cible (chapitre 3, §3.6) |

Pour un CubeSat sans propulsion, le FDS se réduit à la restitution et à la prévision d'orbite — en général à partir des TLE publiés, affinés par le GPS embarqué s'il existe —, mais l'évaluation des conjonctions demeure : un CubeSat incapable de manœuvrer doit tout de même savoir quand il est exposé à un risque, ne serait-ce que pour prévenir l'autre exploitant.

---

## 17.2 Analyse des contacts avec les stations sol

Savoir quelle quantité de données peut être transférée par passage est fondamental pour la conception de la mission. Le bilan de données dépend de la géométrie du contact, du débit et de la durée du passage.

### 17.2.1 Géométrie du contact

Pour une orbite LEO circulaire, la visibilité d'une station sol est déterminée par l'angle d'élévation minimal $\varepsilon_{\min}$ auquel la liaison est utilisable (typiquement 5–10°). La distance oblique à cette élévation, qui fixe l'affaiblissement en espace libre le plus défavorable dans le bilan de liaison (chapitre 11, §11.4.1), vaut

$$\rho = R_E \left[\sqrt{\left(\frac{R_E + h}{R_E}\right)^2 - \cos^2\varepsilon_{\min}} - \sin\varepsilon_{\min}\right]$$

avec $R_E = 6378.137$ km et $h$ l'altitude de l'orbite.

> **Exemple résolu — distance oblique maximale.** Pour $h = 500$ km et $\varepsilon_{\min} = 5°$ :
>
> $(R_E + h)/R_E = 6878.137/6378.137 = 1.0784$, au carré $= 1.1629$ ; $\cos^2 5° = 0.9924$ ; différence $= 0.1705$, racine carrée $= 0.4129$ ; moins $\sin 5° = 0.0872$ donne $0.3258$ ;
>
> $\rho = 6378.137 \times 0.3258 \approx 2\,080$ km.
>
> Avec un masque de 10°, la même orbite donne 1695 km — la valeur utilisée dans le bilan de liaison d'EOSat-3U au chapitre 11, §11.8.1.

La durée du passage découle de l'angle au centre de la Terre sous-tendu par le cercle de visibilité. Le chapitre 7, §7.4.1, donne

$$\lambda_{\max} = \arccos\!\left(\frac{R_E}{R_E + h}\cos\varepsilon_{\min}\right) - \varepsilon_{\min}, \qquad t_{\text{contact,max}} \approx \frac{T}{\pi}\,\lambda_{\max}$$

où $T$ est la période orbitale et $\lambda_{\max}$ est exprimé en radians. C'est la durée d'un passage *à la verticale* ; un passage dont l'élévation maximale est plus faible est plus court.

> **Exemple résolu — durée maximale de passage.** Pour l'orbite à 500 km ($T = 94.6$ min, chapitre 7, §7.7) :
>
> pour $\varepsilon_{\min} = 10°$ : $\lambda_{\max} = \arccos(0.9273 \times 0.9848) - 10° = 24.0° - 10° = 14.0° = 0.245$ rad, d'où $t_{\max} \approx (94.6/\pi) \times 0.245 \approx 7.4$ min ;
>
> pour $\varepsilon_{\min} = 5°$ : $\lambda_{\max} = 22.5° - 5° = 17.5° = 0.306$ rad, d'où $t_{\max} \approx 9.2$ min.
>
> *Durée moyenne utilisable typique d'un passage (tous les passages ne sont pas à la verticale, et les 30–60 premières et dernières secondes servent à acquérir la liaison) : ≈ 6 min.*

La figure 17.2 montre le profil d'élévation en fonction du temps d'un passage. Trois instants comptent sur le plan opérationnel : l'**AOS** (acquisition du signal, lorsque le satellite passe au-dessus du masque), le **TCA** (instant de plus courte distance, élévation maximale et distance oblique minimale) et la **LOS** (perte du signal). La partie du passage réservée au haut débit, là où la marge de liaison est la plus grande, est la fenêtre centrale au-dessus d'environ 30° d'élévation ; un passage dont l'élévation maximale n'atteint jamais 30° peut n'être utilisable que pour la télémesure de servitude. La trace au sol correspondante — qui survole quelles stations — figure au chapitre 7 (figure 7.3).

![Profil d'élévation d'un passage pour un contact en bande S](../assets/figures/fig_pass_geometry.png)

**Figure 17.2** — Profil d'élévation en fonction du temps d'un passage en bande S au-dessus d'une station de haute latitude (Iqaluit, 63,7° N) pour une orbite héliosynchrone à 450 km, à titre d'illustration : AOS et LOS au masque de 5°, TCA à l'élévation maximale, et la fenêtre ≥ 30° dans laquelle est programmée la liaison descendante à haut débit.

### 17.2.2 Volume de données par passage

$$V_{\text{pass}} = R \; t_{\text{contact}} \; \eta_{\text{protocol}}$$

où $R$ est le débit de la liaison descendante (bit/s), $t_{\text{contact}}$ la durée de contact utilisable (s) et $\eta_{\text{protocol}}$ l'efficacité protocolaire (typiquement 0,85–0,95 pour le tramage CCSDS ; le chapitre 11, §11.9, retient 0,80–0,90 pour inclure l'établissement de la liaison et les retransmissions).

> **Exemple :** $R = 2$ Mbit/s, $t = 360$ s (moyenne de 6 min), $\eta = 0.9$ :
> $V_{\text{pass}} = 2 \times 10^6 \times 360 \times 0.9 = 648$ Mbit $= 81$ Mo par passage.

Sommé sur les passages utilisables d'une journée, ce volume donne la capacité quotidienne de liaison descendante $C_{\text{downlink}} = R\,N_{\text{passes}}\,t_{\text{contact}}\,\eta_{\text{protocol}}$ du chapitre 11, §11.9.

### 17.2.3 Fréquence des contacts

| Orbite | Latitude de la station | Passages par jour | Durée moyenne utilisable | Volume quotidien à 2 Mbit/s |
|-------|-------------|----------------|-------------|---------------------------|
| SSO à 500 km | 52° N (p. ex. sud de l'Ontario) | 3–5 | 6 min | 243–405 Mo |
| SSO à 500 km | 69° N (p. ex. Kiruna) | 6–8 | 7 min | 567–756 Mo |
| 500 km, 51,6° (orbite de l'ISS) | 52° N | 2–4 | 5 min | 135–270 Mo |
| SSO à 500 km | Réseau bénévole (mondial, UHF) | 10–15 | 5 min | 3,2–4,9 Mo (à 9,6 kbit/s en UHF) |

*[Source : simulations de propagation d'orbite ; validées par les journaux d'observation de réseaux bénévoles. Volumes recalculés d'après le §17.2.2 avec η = 0,9.]*

On retrouve le schéma décrit au chapitre 11, §11.7.2 : un satellite polaire ou héliosynchrone est vu par une station de haute latitude à presque chaque orbite, mais par une station de moyenne latitude seulement lors des trois à cinq orbites par jour dont la trace au sol passe à l'intérieur du cercle de visibilité.

### 17.2.4 Exemple résolu : bouclage du bilan de données

*Problème :* une mission d'observation de la Terre produit 500 Mo/jour d'images. Une seule station sol à 52° N suffit-elle avec une liaison descendante en bande S à 2 Mbit/s ?

*Calcul :*
- Passages par jour : ≈ 4 (SSO à 500 km, depuis 52° N)
- Passage utilisable moyen : 6 min = 360 s
- Données par passage : $2 \times 10^6 \times 360 \times 0.9 / 8 = 81$ Mo
- Capacité quotidienne : $4 \times 81 = 324$ Mo
- Besoin : 500 Mo/jour
- **Déficit : 176 Mo/jour — le bilan n'est pas bouclé.**

*Solutions :*
1. Ajouter une seconde station sol à haute latitude (p. ex. Kiruna → +6 passages → +567 Mo)
2. Augmenter le débit (bande X à 10 Mbit/s → 405 Mo/passage → largement suffisant ; voir l'exercice 4 du chapitre 11 pour le côté bilan de liaison)
3. Réduire la production de données (rapport cyclique plus faible ou résolution d'image réduite)
4. Ajouter une compression des données à bord (2:1 sans perte → besoin de 250 Mo/jour)
5. Utiliser un réseau UHF bénévole pour des passages supplémentaires (télémesure de servitude uniquement — le débit est trop faible pour les images)

Chaque option déplace un bilan différent : (1) déplace le coût, (2) la puissance et la notification réglementaire, (3) l'exigence de mission, (4) le traitement à bord et le risque. Le bilan de données d'EOSat-3U du chapitre 11, §11.9, se boucle à 5 Mbit/s avec 5 passages/jour (capacité de 956 Mo/jour pour 720 Mo/jour produits) — l'option 2 appliquée en restant en bande S.

---

## 17.3 Pile de protocoles CCSDS

Le Comité consultatif pour les systèmes de données spatiales (CCSDS) définit les protocoles normalisés des communications spatiales, de façon analogue à TCP/IP pour les réseaux terrestres. Leur emploi n'est pas obligatoire pour un CubeSat, mais c'est grâce à eux qu'une station sol commerciale ou d'agence peut dialoguer avec le satellite sans logiciel sur mesure.

*[Source : CCSDS 131.0-B-4 (*TM Synchronization and Channel Coding*) ; CCSDS 231.0-B-4 (*TC Synchronization and Channel Coding*) ; CCSDS 133.0-B-2 (*Space Packet Protocol*)]*
*[URL : https://public.ccsds.org/Pubs/131x0b4.pdf (en libre accès)]*

### 17.3.1 Couches protocolaires

| Couche | Norme CCSDS | Fonction | Équivalent au sol |
|-------|---------------|----------|----------------|
| **Application** | CCSDS 133.0 (*Space Packet*) | Paquets de données de mission et de servitude | HTTP/données applicatives |
| **Réseau** | CCSDS 732.0 (AOS) ou 132.0 (TM) | Canaux virtuels, multiplexage | Routage IP |
| **Liaison de données** | CCSDS 131.0 (codage TM) / 231.0 (codage TC) | FEC, synchronisation trame, CRC | Ethernet |
| **Physique** | CCSDS 401.0 (RF et modulation) | Modulation, fréquence, puissance | Couche physique |

### 17.3.2 Structure d'une trame de télémesure (TM)

```
+--------+------------------+----+
| En-tête| Champ de données | EC |
| 6 oct. | 1–1019 octets    | 2 o|
+--------+------------------+----+
  |
  +-- Identifiant du satellite (10 bits)
  +-- Identifiant de canal virtuel (3 bits)
  +-- Compteur de trames (8 bits)
  +-- Longueur de trame
```

C'est le compteur de trames qui permet au sol de détecter une trame manquante et d'en demander la retransmission ; c'est l'identifiant de canal virtuel qui permet aux données de servitude et aux données de charge utile de partager une même liaison RF tout en étant acheminées vers des destinataires différents au sol.

### 17.3.3 Options de correction d'erreurs directe (FEC)

| Code | Rendement | Gain de codage (dB) | Cas d'usage |
|------|------|------------------|----------|
| Convolutif (7, 1/2) | 1/2 | 5,5 | CubeSats anciens |
| Reed–Solomon (255, 223) | 0,87 | 3,5 | Associé au code convolutif |
| Turbocode (rendement 1/2) | 1/2 | 7,5 | CubeSats à hautes performances |
| LDPC (rendement 7/8) | 7/8 | 6,0 | Haut débit, bonne efficacité spectrale |

*Les CubeSats modernes utilisent généralement un codage LDPC pour la liaison descendante (haut débit) et un code convolutif + Reed–Solomon pour la liaison montante (priorité à la robustesse).* Le gain de codage intervient dans le bilan de liaison comme une réduction du $E_b/N_0$ requis (chapitre 11, §11.6) ; le rendement de code réduit le débit d'information utile pour un débit de canal donné, ce qui explique que les calculs de bilan de données du §17.2 utilisent le débit *d'information* $R$.

---

## 17.4 Construction de la chronologie des opérations

La chronologie des opérations définit toutes les activités majeures du lancement à la fin de vie. Elle fait partie du ConOps (chapitre 4, §4.8, pour le concept ; chapitre 18 pour le détail opérationnel) et dimensionne le segment sol : le nombre de stations, les effectifs et le niveau d'automatisation en découlent.

### 17.4.1 Phases de la mission du point de vue des opérations

| Phase | Durée | Activités clés | Effectifs |
|-------|----------|---------------|---------|
| **LEOP** | 0–72 heures | Séparation, acquisition de la balise, déploiement de l'antenne et du générateur solaire, bilan de santé initial | 24/7 (3 quarts) |
| **Recette en orbite** | 1–4 semaines | Vérification des sous-systèmes, étalonnage du SCAO, première lumière de la charge utile | 16/7 (2 quarts) |
| **Premières opérations** | 1–3 mois | Caractérisation des performances, affinement des procédures | 8/5 (1 quart) |
| **Opérations nominales** | Durée de vie de la mission | Science ou service de routine, maintien d'orbite | 8/5 ou automatisé |
| **Opérations prolongées** | Si approuvées | Opérations en mode dégradé, données réduites | Temps partiel |
| **Fin de vie** | 1–4 semaines | Passivation, manœuvre de désorbitation, dernière télémesure | 8/5 |

### 17.4.2 Chronologie des opérations (style Gantt)

La figure 17.3 dispose les phases du §17.4.1 sur le calendrier, avec le niveau d'effectifs au-dessous.

![Chronologie des opérations de la première année](../assets/figures/fig_ops_timeline.png)

**Figure 17.3** — Chronologie des opérations de style Gantt pour la première année d'une mission CubeSat : la LEOP occupe les 72 premières heures, la recette en orbite se poursuit jusqu'à la semaine 4, les premières opérations jusqu'au mois 3, puis viennent les opérations nominales. Le profil d'effectifs au-dessous passe de 24/7 (trois quarts) pendant la LEOP à 16/7 (deux quarts) pendant la recette en orbite, puis à 8/5 — un seul quart, ou des passages automatisés — à partir des premières opérations.

Le coût des effectifs chute fortement après la recette en orbite (figure 17.3). La ligne « opérations » du WBS (chapitre 16, §16.2.1, 5 %) suppose ce profil ; une mission qui reste à 16/7 parce que ses procédures n'ont jamais été automatisées la dépassera en quelques mois.

### 17.4.3 Détail de la chronologie LEOP

| Temps (après la séparation) | Activité | Critère de succès |
|------------------------|----------|-------------------|
| T+0 s | Séparation du déployeur | Interrupteurs de déploiement libérés |
| T+0 à T+30 min | Décompte de la minuterie de déploiement (pas de RF) | La minuterie tourne ; toutes les inhibitions sont levées |
| T+30 min | Déploiement de l'antenne | Balise détectée par la station sol |
| T+30 à T+60 min | Acquisition de la balise | Verrouillage de la porteuse ; balise décodée |
| T+1 h | Première liaison descendante de télémesure | Données de servitude reçues et validées |
| T+1 à T+6 h | Évaluation initiale de la santé | Tous les sous-systèmes transmettent des données de servitude nominales |
| T+6 à T+12 h | Déploiement du générateur solaire (s'il est séparé) | Production de puissance confirmée |
| T+12 à T+24 h | Initialisation du SCAO | Détermination d'attitude active |
| T+24 à T+48 h | Étalonnage du SCAO (magnétomètre, senseur solaire) | Pointage dans la spécification grossière |
| T+48 à T+72 h | Validation de la chaîne de communication (duplex intégral) | Liaisons montante et descendante au débit opérationnel |

Le silence RF de 30 minutes après le déploiement est une exigence du fournisseur de lancement (chapitre 3, §3.5.2), et non un choix de conception ; le premier passage peut donc survenir avant que le satellite ne soit autorisé à émettre, et le plan LEOP doit préciser ce que fait l'équipe d'un premier passage silencieux. Le chapitre 19 répète exactement ce cas.

---

## 17.5 Dimensionnement du segment sol

Trois questions dimensionnent le segment sol d'un CubeSat, dans cet ordre :

1. **Le bilan de données se boucle-t-il avec une seule station ?** (§17.2.4 ; chapitre 11, §11.9.) Sinon, il faut choisir entre une seconde station, un débit plus élevé et moins de données — et la seconde station s'achète en général plutôt qu'elle ne se construit : un réseau commercial vend des passages à la minute (chapitre 11, §11.7.1), ce qui transforme un coût d'investissement en coût d'exploitation proportionnel à la mission.
2. **Quel est l'effectif minimal qui maintient le satellite en sécurité ?** Un satellite dont la FDIR (chapitre 18, §18.3) peut le maintenir indéfiniment en mode survie n'a besoin de l'attention du sol que le jour ouvré suivant ; celui qui ne le peut pas exige une astreinte 24/7 dès la LEOP, qui coûte plus cher que n'importe quelle antenne.
3. **Qui d'autre doit pouvoir dialoguer avec lui ?** Un satellite qui utilise le tramage CCSDS (§17.3) peut être pris en charge par n'importe quelle station conforme en cas d'urgence ; un satellite doté d'un protocole propriétaire dépend du bon fonctionnement de sa propre station.

Un bilan représentatif de segment sol pour une mission 3U — une station dédiée en bande S (≈ 50–200 k€ à construire, chapitre 11, §11.7.1), un réseau UHF bénévole pour la télémesure de servitude, un logiciel MCS libre et 0,5 ETP d'opérations — correspond à la paire « Sol 8 k€ + Opérations 40 k€ » de la colonne ascendante du chapitre 16, §16.1.6, qui suppose que la station existe déjà.

---

## 17.6 Retour sur UniSat-1 : un segment sol minimal

Le segment sol d'UniSat-1 se compose d'une seule station UHF à antenne Yagi à l'université et du réseau bénévole (le chapitre 13, §13.6, l'évalue à 5 k€). Le chapitre 11, §11.8.2, a montré ce que cela permet : à 400 km avec un masque de 10°, le contact utilisable est d'environ 5 min par passage (6,2 min au maximum, chapitre 7, §7.4.1), soit 153 ko par passage et **0,61 Mo/jour pour 1,13 Mo/jour produits** — le bilan de données ne se boucle pas avec une seule station.

Application du §17.5 à UniSat-1 :

1. *Seconde station ou débit plus élevé ?* La liaison UHF est limitée en puissance et utilise déjà une FEC (chapitre 11, §11.8.2) : le débit ne peut donc guère augmenter ; le réseau bénévole ajoute des passages sans coût, mais sans garantie de disponibilité. La solution réaliste se situe du côté de la production — un mode de moyennage à bord, ou une fréquence d'échantillonnage du magnétomètre plus faible hors des régions d'intérêt scientifique —, ce qui relève d'une modification des exigences (chapitre 5, §5.6.2) et non du segment sol. C'est le risque R-02 du registre des risques d'UniSat-1 au chapitre 15, §15.5, et sa réduction est exactement cette paire de mesures : s'inscrire auprès du réseau bénévole et réduire de moitié le débit de données à bord.
2. *Effectif minimal ?* UniSat-1 a un contrôle d'attitude passif et un mode survie limité à la balise dont le bilan de puissance est positif (chapitre 9, §9.5) ; il peut donc attendre plusieurs jours qu'on s'occupe de lui : des opérateurs étudiants à 0,2 ETP suffisent.
3. *Qui d'autre peut dialoguer avec lui ?* Le tramage de type AX.25 courant sur les réseaux bénévoles n'est pas du CCSDS : aucune station d'agence ne peut donc aider en cas d'urgence ; la mission l'accepte, et cette acceptation devrait être consignée dans le registre comme un risque à part entière.

Pour UniSat-1, la chronologie LEOP du §17.4.3 se réduit aux cinq premières lignes : il n'y a ni générateur solaire à déployer ni SCAO à étalonner, si bien que la recette en orbite est terminée dès que le magnétomètre renvoie des valeurs de champ plausibles, le deuxième jour.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Segment sol | Réseau de stations sol + MCS + FDS + planification de mission + traitement des données (§17.1.1) |
| Analyse des contacts | La distance oblique au masque d'élévation fixe l'affaiblissement en espace libre le plus défavorable ; $t_{\max} \approx (T/\pi)\lambda_{\max}$ ≈ 7,4 min à 500 km / 10° ; moyenne utilisable ≈ 6 min |
| Volume de données | $V_{\text{pass}} = R\,t_{\text{contact}}\,\eta_{\text{protocol}}$ ; 2 Mbit/s × 6 min × 0,9 ≈ 81 Mo par passage |
| Bilan de données | Doit être bouclé : production quotidienne ≤ capacité quotidienne de liaison descendante ; ajouter une station, augmenter le débit, compresser ou produire moins |
| CCSDS | Pile normalisée : paquet spatial, trames AOS/TM, codage FEC, modulation RF ; le gain de codage réduit le $E_b/N_0$ requis |
| Chronologie des opérations | LEOP (24/7) → recette en orbite (16/7) → nominal (8/5 ou automatisé) ; les effectifs déterminent le coût des opérations |
| LEOP | Les 72 premières heures sont critiques : déploiement de l'antenne, acquisition de la balise, bilan de santé, étalonnage du SCAO |
| UniSat-1 | Une seule station UHF ne boucle pas le bilan de données ; la solution se situe du côté de la production |

---

## Exercices

1. **Distance oblique et durée de passage.** Pour une orbite circulaire à 550 km, calculez la distance oblique à 5°, 10° et 20° d'élévation ainsi que la durée maximale de passage pour chaque masque (prenez $R_E = 6378.137$ km et $\mu = 398\,600.44$ km³/s²). Commentez le compromis entre un masque bas (passages plus longs) et la pénalité d'affaiblissement en espace libre qu'il introduit dans le bilan de liaison du chapitre 11.

2. **Volume de données par passage.** Un CubeSat 3U d'observation de la Terre transmet en liaison descendante à 5 Mbit/s avec un codage LDPC de rendement 7/8 et une efficacité protocolaire CCSDS de 0,85. Pour un passage utilisable moyen de 6 min, calculez les données utiles par passage. Combien de passages par jour faut-il pour écouler 1,2 Go/jour d'images, et depuis quelle latitude de station du §17.2.3 cela est-il réalisable avec une seule station ?

3. **Conception d'un réseau de stations sol.** Une mission SSO à 500 km doit transmettre 2 Go/jour en liaison descendante. Concevez un réseau de stations — emplacements, tailles d'antenne, débits — à partir des types de stations du chapitre 11, §11.7.1, et des nombres de passages du §17.2.3, pour (a) un coût d'investissement minimal et (b) un coût d'exploitation minimal sur trois ans. Donnez le coût annuel de chacune des solutions et le point où leurs coûts se croisent.

4. **Chronologie LEOP.** Construisez une chronologie LEOP heure par heure pour les 72 premières heures d'un CubeSat 3U déployé depuis l'orbite de l'ISS (51,6°, 400 km) avec une seule station à 45° N. Repérez chaque passage (vous pouvez supposer quatre passages par jour de 5 min chacun, regroupés en deux séries), indiquez quelle activité du §17.4.3 est tentée à chacun d'eux, et identifiez le plus long intervalle pendant lequel le satellite n'est pas observé.

5. **Premier passage silencieux.** Le premier passage après le déploiement survient 20 minutes après la séparation, alors que la minuterie d'inhibition RF tourne encore. Rédigez l'arbre de décision que suit l'équipe des opérations pour les trois passages suivants si (a) une balise est reçue au passage 2, (b) rien n'est reçu aux passages 2 et 3, et (c) une porteuse est reçue mais aucune trame n'est décodée. Pour chaque branche, nommez le composant du segment sol ou le sous-système du satellite soupçonné en premier et l'essai qui permet de trancher.

6. **Chronologie des opérations et effectifs.** Établissez une chronologie des opérations à la semaine pour une mission d'observation de la Terre de 12 mois en suivant le §17.4.2, puis chiffrez les effectifs à 60 k€ par ETP-année pour le profil 24/7 → 16/7 → 8/5. Refaites le calcul si la recette en orbite glisse de 4 à 10 semaines. Quel investissement d'automatisation unique réduit le plus la sensibilité à ce glissement ?

7. **Choix de la FEC.** Une liaison descendante UHF se boucle avec 2,8 dB de marge sans codage (chapitre 11, §11.8.2) pour une exigence de 3 dB. À l'aide des gains de codage du §17.3.3, choisissez un code qui satisfait l'exigence avec la plus faible perte de débit d'information, et calculez le volume de données quotidien qui en résulte pour 4 passages de 5 min. Refaites ensuite ce choix pour une liaison en bande S limitée en bande passante plutôt qu'en puissance, et expliquez pourquoi la réponse diffère.

8. **Segment sol minimal.** Spécifiez le segment sol minimal capable de soutenir la mission UniSat-1 du §17.6 — matériel, logiciel, effectifs et adhésion à un réseau — et estimez son coût. Énumérez ensuite ce que ce segment minimal *ne peut pas* faire (mesure de distance, réponse à une conjonction, reprise à haut débit) et attribuez à chaque lacune une cote de risque sur la matrice 5×5 du chapitre 15.

9. **Mode survie pendant un week-end.** Un satellite 3U passe en mode survie à 03:00 un samedi ; le prochain contact avec du personnel est le lundi à 09:00. À l'aide de la puissance en mode survie du tableau 18.1 du chapitre 18 (2 W) et de la batterie du chapitre 9, §9.3 (20 Wh, à la limite de profondeur de décharge qui y est retenue), déterminez si le satellite survit à 54 heures d'éclipses sans intervention du sol, et quelle astreinte minimale, le cas échéant, le segment sol doit assurer.

---

## Références

1. ECSS, *ECSS-E-ST-70C : Ground Systems and Operations*, 2008. https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/
2. CCSDS, *TM Synchronization and Channel Coding*, CCSDS 131.0-B-4, 2022. https://public.ccsds.org/Pubs/131x0b4.pdf
3. CCSDS, *Space Packet Protocol*, CCSDS 133.0-B-2, 2020. https://public.ccsds.org/Pubs/133x0b2.pdf
4. CCSDS, *TC Synchronization and Channel Coding*, CCSDS 231.0-B-4, 2021. https://public.ccsds.org/Pubs/231x0b4.pdf
5. SatNOGS, *Global Network of Satellite Ground Stations*. https://network.satnogs.org/
6. NASA JPL, *DSN Telecommunications Link Design Handbook*, 810-005. https://deepspace.jpl.nasa.gov/dsndocs/810-005/
7. Space Applications Services, *Yamcs Mission Control Software* (logiciel libre). https://yamcs.org/
8. Wertz, J. R., Everett, D. F. et Puschell, J. J. (dir.), *Space Mission Engineering : The New SMAD*, Microcosm Press, 2011, chapitres 28–29 (segment sol ; opérations de mission).
