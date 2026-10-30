# Guide de la propulsion d'EO-Sat-1 (phase D)

**Décision de périmètre (directeur de vol) :** la propulsion sert aux **manœuvres d'évitement
de débris** et à un **maintien d'orbite limité** (compensation de la traînée / décalage volontaire
du demi-grand axe). Elle est délibérément minimale. Il n'existe **aucune capacité de désorbitation
en fin de vie, et aucune n'est nécessaire** : le déclin naturel depuis 450 km avec
B = 77,9 kg/m² prend 1,7 an à activité solaire moyenne (4,8 ans au minimum solaire, 0,2 an
avec les ailes orientées face à la vitesse, traînée maximale) — conforme à la règle des 5 ans de la FCC quelle que soit
l'activité solaire. Une désorbitation propulsée coûterait plus de 42,6 m/s, soit un second
système propulsif complet.

> **Mise en garde 2026-08 :** les durées de déclin ci-dessus ont été calculées pour l'altitude
> déclarée de 450 km, désormais abandonnée. L'altitude moyenne réelle d'après le TLE est d'environ 513 km
> (orbit.yaml, décision 2026-08 sur l'époque et l'altitude), où la densité atmosphérique est
> environ deux fois plus faible et le déclin naturel plusieurs fois plus lent — le cas du minimum solaire
> dépasse très probablement la règle des 5 ans de la FCC. L'analyse du déclin, et avec elle
> la décision en vigueur « aucune capacité de désorbitation », doivent être refaites à 513 km.
> Décision du responsable en attente ; non recalculé lors de la revue de configuration 2026-08.

## Matériel

Module à monergol vert (classe LMP-103S/ADN) de 1U en mode blowdown (pressurisation non régulée), avec un
propulseur unique sur la face −X poussant selon **+X satellite** — dans le sens du mouvement en
attitude nominale nadir ; une poussée rétrograde exige un basculement délibéré de 180° en lacet
(maintien INERTIAL). Ce couplage avec l'AOCS est voulu : c'est le point pédagogique.

| Paramètre | Valeur |
|---|---|
| Poussée | 0,33 N (22 bar en BOL) → 0,14 N (9,33 bar en EOL), F ∝ P |
| Isp | 220 s en BOL → 196 s en EOL (208 s en moyenne) |
| Ergol | 0,400 kg, ρ = 1240 kg/m³, réservoir de 560 cm³, blowdown N₂ 2,36:1 |
| Lit catalytique | préchauffage ≥ 180 °C, 12 W × ~20 min (4 Wh) via `HEATER_THRUSTER` (fonction S8 42) |
| Système humide | 1,55 kg (12,9 % de la plateforme de 12 kg) |
| **ΔV total** | **66,9 m/s** |

**Bilan de ΔV (phase active de 2 ans, hypothèse évitement de débris + compensation de traînée) :**
compensation de traînée 42,6 + décalage SMA/LTAN 3,0 + manœuvres d'évitement de collision, CAM (6 événements × 0,1) 0,6 +
recette en orbite/étalonnage 1,0 + contrôle de l'excentricité 1,5 + marges 7,3 =
**56,0 m/s nécessaires** pour une capacité de 66,9 (**+19,5 %**). L'enveloppe
restante (`prop.dv_remaining`, 0x0B0C) constitue d'abord une **réserve d'évitement
de collision** : en dessous d'environ 1 m/s, le satellite a de fait perdu sa capacité de CAM
et la conduite à tenir face aux conjonctions change.

Poussées types : CAM de 0,20 m/s ≈ 7,5 s ; compensation de traînée bimensuelle de 0,85 m/s ≈
32 s (BOL) ; toutes tiennent dans un passage. Une poussée prograde de 1,0 m/s relève le SMA de
1,79 km et décale les heures de passage d'environ 34 s/jour (mesuré dans le simulateur : −33,5 s/jour,
valeur analytique −33,9).

## Automate d'états et verrouillages

`SAFED(0) → ARMED(1) → FIRING(2)`, plus l'état verrouillé `INHIBIT(3)` après une deuxième
interruption (levé uniquement par `PROP_INHIBIT_CLR`). Armement en deux temps : `PROP_SET_BURN`
doit précéder `PROP_ARM` (code 0xA5C3) de 300 s au plus. Les huit verrouillages d'armement
(lit catalytique ≥ 180 °C, réservoir 6–24 bar, ergol > 5 g, mode AOCS ∈ {4,5,9},
att_error < 2°, SoC > 45 %, phase NOMINAL, hors éclipse, une branche de vanne à verrouillage
ouverte, aucune inhibition) renvoient des **codes S1(8) distincts** et positionnent leur bit dans
`prop.arm_inhibit_mask` (0x0B15) — le paramètre le plus utile de tous pour les stagiaires.

Interruptions de poussée à bord (att_error > 2°, alimentation < 4 bar, lit catalytique > 350 °C,
chien de garde, perte de vanne, délestage de la ligne EPS `prop`), plus l'autonomie S19 : règles
8001–8006 (interruption sur violation S12 de 0x0217, pression réservoir, surchauffe du lit catalytique,
isolation sur fuite, désarmement sur passage en mode survie, interruption sur SoC critique). Le **ΔV partiel
d'une poussée interrompue perturbe tout de même l'orbite** — la restitution d'orbite après poussée est obligatoire.

## Intégration orbitale (ce qui la rend réaliste)

Une poussée finie est intégrée par sous-pas de 1 s au plus ; le ΔV résultant
(composante le long de la trace × cos θ + composante latérale × sin θ, θ = att_error) est appliqué au SGP4 sous la forme
d'**une impulsion unique au milieu de la poussée**, au moyen d'une correction différentielle du TLE à 6 paramètres
(paramétrisation équinoxiale ; 3 à 6 itérations, résidu inférieur au millimètre ;
divergence → événement 0x0812, orbite inchangée). Chaque poussée appliquée incrémente
`epoch_version` (0x0B19, `/api/state`) : le planificateur et le MCS la traitent comme un saut
de temps, purgent leurs caches de contacts et de trace au sol et adoptent le nouveau TLE. Les points de reprise
sérialisent le jeu d'éléments (`orbit_elset`) — « le SGP4 est sans état pour un temps
UTC donné » a cessé d'être vrai le jour où la propulsion est arrivée.

En état FIRING, le moteur **limite l'accélération du temps à 10× au plus** (événement
0x0811 `PROP_SPEED_CLAMPED`) afin que les poussées et les interruptions restent observables.

## Puissance et thermique

Ligne EPS 8 `prop` (OFF par défaut, **dernière** dans l'ordre de délestage — la délester
en cours de poussée déclenche l'interruption). La consommation suit l'état des actionneurs, et non celui de
l'interrupteur de ligne : 0 W au repos, 2 W pour les circuits de commande des vannes en ARMED/FIRING, +12 W lorsque le
réchauffeur du lit catalytique fonctionne. Le lit catalytique correspond au circuit TCS `thruster`
(`tcs.temp_thruster` 0x0409, état du réchauffeur 0x041B) : commande manuelle via la fonction 42,
régulation thermostatique 190/230 °C via `HEATER_AUTO_MODE circuit=2`. Une manœuvre est
une **activité de puissance** : les 4 Wh de préchauffage plus la poussée doivent tenir dans le bilan
de la phase éclairée.

## Interfaces

- **Commandes :** fonctions S8 **108–118** (`PROP_ARM` 108, `PROP_DISARM` 109,
  `PROP_SET_BURN` 110, `PROP_EXECUTE` 111, `PROP_ABORT` 112,
  `PROP_ISO_OPEN/CLOSE` 113/114, `PROP_SET_LIMITS` 115,
  `PROP_INHIBIT_SET/CLR` 116/117, `PROP_GET_STATUS` 118) + fonction 42 pour le réchauffeur.
  *(Le brief 03 prévoyait 85–95 ; le bloc de pointage AOCS de la phase C a pris 85–91, si bien que
  108–118 est le bloc attribué.)*
- **Télémesure :** bloc **0x0B00–0x0B1B** ; **SID HK 9** à 8 s (désactivé à la
  mise sous tension, `HK_ENABLE sid=9`). *(Le brief prévoyait le SID 7 ; la phase C l'a pris pour
  l'AOCS.)* Paramètres de ligne EPS 0x014A/0x014B ; TCS 0x0409/0x041B.
- **Événements :** **0x0800–0x0812**. **S12 :** plage de pression réservoir + **moniteur de variation
  et de taux** (le détecteur de fuite), lit catalytique, ergol, poussée faible, enveloppe de
  ΔV. **S19 :** ea_id 8001–8006.
- **Procédures :** **NOM-004** (planification, occupe l'indice laissé libre),
  **NOM-013** (exécution ; la NOM-005 du manuel — la NOM-005 du simulateur était déjà la Configuration
  HK), **CTG-028** (anomalie ; la CTG-006 du manuel — la CTG-006 du simulateur était
  déjà l'Anomalie charge utile ; et « SID 5/propulsion » correspond ici au SID 9). L'OBCP 4
  (`obcp/04_orbit_manoeuvre.yaml`) constitue la séquence minutée à bord. Activité du planificateur :
  `orbit_manoeuvre`.
- **Scénarios de formation :** `prop_valve_stuck_open`, `prop_slow_leak`,
  `prop_underperformance`, `prop_burn_eclipse_power`,
  `prop_attitude_loss_mid_burn`.

## Limites du modèle (enseignées, non simulées)

Un propulseur, un axe — pas d'orientation de la poussée (TVC), pas de désaturation par propulseurs (NOM-007 reste
réalisée uniquement aux magnétocoupleurs). Pas de retrait de service propulsé, de changement de plan, de relèvement d'orbite,
de phasage, de rendez-vous, de contrôle d'orbite en boucle fermée ni de véritable criblage des
conjonctions (la CAM est une entrée de scénario scriptée). Pas de transitoires de combustion ou d'alimentation,
de blowdown non isotherme, de ballottement ou de migration du centre de gravité, ni de couplage avec le tenseur d'inertie
(la masse n'est qu'une télémesure). Deux *branches* de vannes à verrou, un propulseur. Le déclin dû
à la traînée est celui que donne le B* du SGP4 — le bilan de ΔV ci-dessus est un calcul de dimensionnement
hors ligne, non une boucle de rétroaction en temps réel.
