# À propos de ce manuel

*Concurrent Spacecraft Design* (*Conception concourante d'engins spatiaux*) est un manuel ouvert consacré à la conception de petits engins spatiaux selon la méthode de l'ingénierie concourante. Il conduit une mission d'un besoin exprimé, en passant par les exigences, le choix de l'orbite, l'architecture et le dimensionnement des sous-systèmes, jusqu'à la vérification, aux coûts, à la revue de conception, au segment sol et aux opérations, avec deux exemples fil rouge de CubeSats — un engin 3U d'observation de la Terre (EOSat-3U) et un démonstrateur 1U à magnétomètre (UniSat-1) — suivis dans chaque chapitre. La partie IV présente une fiche pour chaque poste d'ingénierie d'une table de conception concourante ; la partie V démontre les équations à partir des premiers principes.

Il s'adresse aux étudiantes et étudiants de dernière année de premier cycle et des cycles supérieurs ainsi qu'aux jeunes ingénieures et ingénieurs qui possèdent une formation d'ingénieur mais aucune expérience préalable de la conception d'engins spatiaux, et aux ingénieures et ingénieurs en activité qui souhaitent un exposé compact, adossé aux normes, de la manière dont les composantes d'une mission se contraignent mutuellement. Chaque chapitre comporte des objectifs d'apprentissage, une synthèse, des exercices et des références ; les exercices ne nécessitent aucun logiciel au-delà d'une calculatrice ou d'un tableur.

**Figures reproductibles.** Toutes les figures tracées de ce manuel sont générées de façon procédurale par un court script conservé avec les sources du manuel, à partir de données numériques reproductibles. Aucune courbe n'est dessinée à la main : une figure peut être régénérée lorsque les chiffres sous-jacents changent, et le lecteur qui veut voir comment une courbe a été calculée peut lire le script qui l'a tracée. Les schémas sont dessinés sous forme de graphiques vectoriels dans les sources.

**Exemples calculés avec l'outil.** Chaque exemple numérique résolu — les bilans d'EOSat-3U et d'UniSat-1, les durées orbitales, les bouclages de liaison, les cas thermiques, les cumuls de coûts — a été calculé avec l'outil libre SpaceCDF décrit à l'annexe A, à partir de descripteurs de mission publiés avec lui, puis vérifié à la main à l'aide des équations données dans le texte et démontrées dans la partie V. Lorsque les éditeurs de cette édition ont relevé une erreur de calcul dans une version antérieure, la valeur corrigée est utilisée de façon cohérente dans chaque chapitre qui la cite, et la démonstration de la partie V présente le calcul corrigé. Le lecteur qui veut reproduire un exemple peut exécuter le descripteur publié ; celui qui veut en contester un peut suivre la démonstration.

**Normes.** Les normes ECSS, les manuels de la NASA et les ouvrages SMAD sont cités là où ils sont utilisés. Lorsque la formulation d'une norme et la pratique courante diffèrent — les méthodes de vérification du chapitre 14 en sont un exemple —, le manuel indique ce qui relève de l'une et de l'autre.

**Corrections et contributions.** Ce document est vivant. Les corrections, les exercices améliorés et les nouvelles figures sont les bienvenus par l'intermédiaire du dépôt indiqué à l'annexe A ; les contributeurs et contributrices sont remerciés dans l'édition suivante.

---

# Licence

*Concurrent Spacecraft Design : An Open Textbook*, Franz Newland et collaborateurs, est mis à disposition selon les termes de la licence Creative Commons Attribution 4.0 International (CC BY 4.0).

**Attribution.** En cas de réutilisation ou d'adaptation de cette œuvre, merci de l'attribuer comme suit :

> *Concurrent Spacecraft Design : An Open Textbook*, Franz Newland et collaborateurs, CC BY 4.0.

**Vous êtes autorisé à :**

- **Partager** — copier, distribuer et communiquer le matériel par tous moyens et sous tous formats ;
- **Adapter** — remixer, transformer et créer à partir du matériel pour toute utilisation, y compris commerciale.

L'Offrant ne peut retirer les autorisations concédées par la licence tant que vous appliquez les termes de cette licence.

**Selon les conditions suivantes :**

- **Attribution** — Vous devez créditer l'œuvre, intégrer un lien vers la licence et indiquer si des modifications ont été effectuées. Vous devez indiquer ces informations par tous les moyens raisonnables, sans toutefois suggérer que l'Offrant vous soutient ou soutient la façon dont vous avez utilisé son œuvre.
- **Pas de restrictions complémentaires** — Vous n'êtes pas autorisé à appliquer des conditions légales ou des mesures techniques qui restreindraient légalement autrui à utiliser l'œuvre dans les conditions décrites par la licence.

Vous n'êtes pas tenu de vous conformer aux conditions de la licence pour des éléments du matériel appartenant au domaine public ou dans le cas où l'utilisation que vous souhaitez faire est couverte par une exception ou une limitation applicable. Aucune garantie n'est donnée. Il se peut que la licence ne vous donne pas toutes les permissions nécessaires pour l'utilisation que vous prévoyez ; par exemple, d'autres droits, tels que le droit à l'image, le droit au respect de la vie privée ou les droits moraux, peuvent limiter votre utilisation du matériel.

Le texte intégral de la licence est disponible à l'adresse [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/).

**Matériel de tiers.** Les normes, manuels et articles cités ou résumés dans ce manuel restent la propriété de leurs éditeurs et sont cités là où ils sont utilisés. Les produits de fournisseurs nommés dans les exemples résolus sont des exemples représentatifs et non des recommandations, et leurs marques appartiennent à leurs propriétaires. Le logo AIG (assisté par l'IA générative) utilisé dans la déclaration ci-dessous est publié selon ses propres conditions CC BY-NC-SA 4.0, qui régissent sa réutilisation indépendamment de la licence CC BY 4.0 de ce manuel.

---

# Déclaration — IA générative

Ce manuel a été produit avec l'assistance de l'IA générative. La structure des chapitres, la conversion de documents antérieurs en texte de manuel, la rédaction des exercices, les scripts de génération des figures et la mise en forme des documents ont été préparés avec l'assistance de l'IA, guidée tout au long du travail par les normes ECSS, le *Systems Engineering Handbook* de la NASA et les références SMAD citées dans le texte. Les exemples numériques ont été calculés par l'outil SpaceCDF (annexe A) et vérifiés à la main. Le cadrage éditorial, les exemples résolus, le choix de ce qui est inclus ou omis et la responsabilité de chaque affirmation du manuel restent du ressort des auteurs humains.

L'attribution suit le cadre AIG (assisté par l'IA générative) — Peters (2023), *Logos IA-EN*, CC BY-NC-SA 4.0 — [https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/](https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/). Le logo AIG est utilisé selon ses propres conditions de licence, qui diffèrent de la licence de ce manuel (voir la page Licence ci-dessus).

Les personnes qui adaptent ce manuel sont invitées à conserver la même pratique : indiquer où et comment l'IA générative a été utilisée. Refuser d'utiliser l'IA est tout à fait acceptable ; l'utiliser sans le dire ne l'est pas.

---

# Colophon

Le manuel est rédigé en Markdown, à raison d'un fichier par chapitre, avec les mathématiques en notation LaTeX ; les figures tracées sont générées par des scripts matplotlib conservés avec les sources, et les schémas sont en SVG intégré. Les chapitres sont concaténés dans l'ordre, convertis en HTML, puis rendus en PDF par WeasyPrint. Les polices sont les familles sans empattement et à empattement par défaut du moteur de rendu ; la couleur d'accentuation utilisée dans les figures et les titres est un bleu neutre.
