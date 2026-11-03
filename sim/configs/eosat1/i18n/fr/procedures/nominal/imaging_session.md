# NOM-002 : Séance de prise de vue
**Sous-système :** PAYLOAD / AOCS / TCS
**Phase :** NOMINAL
**Révision :** 1.1 --- 2026-11-03 : le refroidisseur du FPA est ARRÊTÉ en STANDBY ; l'étape 2
le met en marche (préparation de la prise de vue) et l'étape 6 l'arrête.
**Approuvé par :** directeur des opérations de vol

## Objet
Exécuter une séance planifiée de prise de vue d'observation de la Terre. Cette procédure fait passer la
charge utile du mode STANDBY au mode IMAGING, surveille l'acquisition des images et ramène la
charge utile en STANDBY à la fin. Les performances de pointage fin et les conditions thermiques
du plan focal doivent être confirmées avant le début de la prise de vue.

## Prérequis
- [ ] NOM-001 Ouverture de passage achevée avec une déclaration tout GO
- [ ] Charge utile en mode STANDBY (`payload.mode` (0x0600) = 1)
- [ ] Refroidisseur du FPA mis en marche (étape 2) au moins 10 min avant la fenêtre de prise de vue.
      Le mode STANDBY ne fait plus fonctionner le refroidisseur : la mise en froid fait partie de la préparation.
- [ ] Paramètres de la scène visée envoyés à l'ordonnanceur de bord
- [ ] AOCS en FINE_POINT (`aocs.mode` (0x020F) = **5**). La condition d'acquisition de la charge utile
      exige EXACTEMENT le mode 5. Il n'existe pas de mode NOMINAL et le mode 0 est OFF —
      les codes sont 0 OFF, 1 SAFE_BOOT, 2 DETUMBLE, 3 COARSE_SUN, 4 NOMINAL,
      5 FINE_POINT, 6 SLEW, 7 DESAT, 8 ECLIPSE, 9 INERTIAL
      (`configs/eosat1/aocs/aocs_mode_codes.yaml`). Une fiche qui demandait à l'opérateur
      de confirmer le mode 0 lui demandait de confirmer que l'AOCS était éteint.
- [ ] SoC de la batterie EPS > 50 % (`eps.bat_soc` (0x0101) > 50)
- [ ] Fenêtre de prise de vue confirmée par la dynamique du vol (cible en visibilité)

## Déroulement

### Étape 1 --- Vérifier les performances de pointage fin
**TC:** `AOCS_FINE_READY_CHECK` (Service 8, Subtype 1, func_id 89) --- lire le masque des conditions préalables à FINE
**Verify:** `aocs.fine_ready == 0` (0x02C5, timeout 10 s) --- tous les bits de condition à zéro
**TC:** `AOCS_SET_MODE(mode=5)` (Service 8, Subtype 1, func_id 0) --- FINE_POINT
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- demander les données de servitude AOCS
**Verify:** `aocs.mode == 5` (0x020F, timeout 60 s) --- FINE_POINT
**Verify:** `aocs.mode_demoted == 0` (0x0298, timeout 10 s) --- le satellite est dans
le mode demandé par le sol. S'il vaut 1, `aocs.commanded_mode` (0x0297) indique
ce qui a été demandé et la description de l'événement 0x0200 indique la raison de la rétrogradation.
**Note:** `aocs.fine_degraded` (0x0299) = 1 signifie que FINE est assuré avec un jeu de TROIS
roues. C'est admis et l'acquisition se fait normalement --- la condition d'acquisition contrôle l'erreur de pointage
et la stabilité des vitesses, qui déterminent la qualité de l'image, et non le nombre de roues. Cette information est
enregistrée sur chaque produit (bit 0 de l'octet `flags` du catalogue), afin qu'une campagne
de retraitement puisse retrouver ces bandes.
**Note:** `aocs.desat_inhibit` (0x029A) est activé automatiquement tant que
`payload.mode` = 2 ; un déchargement du moment cinétique ne peut donc plus interrompre une bande. Surveiller
le bit 4 de `0x02C5` (enveloppe de moment cinétique >= 70 %) : c'est l'avertissement de planification fiable
« une désaturation approche », à consulter AVANT de s'engager dans une longue bande.
**Verify:** `aocs.att_error` (0x0217) < 0.1 deg sous 5 s
**Verify:** `aocs.rate_roll` (0x0204) < 0.01 deg/s
**Verify:** `aocs.rate_pitch` (0x0205) dans la plage [0.053, 0.073] deg/s (le suivi du nadir impose la vitesse orbitale, +0.063 deg/s sur cette console ; une vitesse de tangage nulle signifierait que le satellite NE suit PAS le nadir)
**Verify:** `aocs.rate_yaw` (0x0206) < 0.01 deg/s
**GO/NO-GO:** Si att_error >= 0.1 deg, se mettre en attente (HOLD). Attendre jusqu'à 60 s la convergence.
Si la condition n'est toujours pas remplie, interrompre la prise de vue et analyser les performances de l'AOCS.

### Étape 2 --- Préparer le plan focal (refroidisseur du FPA en marche)
**Note:** Le refroidisseur du FPA est ARRÊTÉ en STANDBY (2026-11-03). Le mettre en marche
constitue la préparation de la prise de vue : depuis l'équilibre non refroidi en STANDBY (environ +10 °C),
le détecteur a besoin d'environ 6.5 min pour atteindre `payload.fpa_ready` = 1 (dont 60 s
d'hystérésis de disponibilité). Envoyer cette étape au moins 10 min avant la fenêtre de
prise de vue, avant l'étape 1 si la fenêtre est proche ; l'activité `imaging_pass` du planificateur
lui réserve 480 s. Si `tcs.cooler_fpa` (0x040C) vaut déjà 1, ne pas envoyer la TC.
**TC:** `FPA_COOLER(on=1)` (Service 8, Subtype 1, func_id 43) --- refroidisseur du FPA en marche
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) --- demander les données de servitude TCS
**Verify:** `tcs.cooler_fpa` (0x040C) = 1 (ACTIVE) sous 10 s
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- données de servitude de la charge utile (`payload.fpa_ready`)
**Verify:** `payload.fpa_ready` (0x0610) = 1 sous 600 s
**Verify:** `tcs.temp_fpa` (0x0408) < -10.0 °C sous 5 s
**GO/NO-GO:** Si `payload.fpa_ready` vaut encore 0 après 10 min, se mettre en attente (HOLD). Lire
`payload.cooler_margin_k` (0x064B) : une valeur <= 0 signifie que la consigne est hors de portée
avec le puits thermique actuel. Si la température ne baisse pas, vérifier l'état du
refroidisseur et interrompre si nécessaire.

### Étape 3 --- Vérifier la capacité de stockage
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- demander les données de servitude de la charge utile
**Verify:** `payload.store_used` (0x0604) < 90 % sous 5 s
**Note:** Consigner `payload.product_count` (0x0648) comme référence N0 et
`payload.product_mb` (0x0647) comme volume catalogué. Ce sont les paramètres de la phase 4
qui comptent les produits RÉELS ; `payload.store_used` (0x0604) inclut aussi
le remplissage préexistant d'environ 20 % hors produits ; ce n'est donc pas un compte de produits.
**GO/NO-GO:** Si le stockage >= 90 %, interrompre la prise de vue. Programmer d'abord un vidage des données
(NOM-003) pour libérer de la mémoire avant de réessayer.

### Étape 4 --- Commander le mode prise de vue
**TC:** `PAYLOAD_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 26) --- commander IMAGING
**Verify:** `payload.mode` (0x0600) = 2 (IMAGING) sous 15 s
**Verify:** hausse de `eps.power_cons` (0x0106) observée (consommation de la charge utile)
**Note:** Le chronomètre de la séance de prise de vue démarre. Durée nominale de la séance selon le plan de passage.
**Note:** Depuis la phase 4, l'entrée en IMAGING ne produit PAS de données à elle seule.
La mémoire ne croît que pendant la lecture d'une bande commandée --- quelques secondes par
acquisition, signalée par `payload.readout_active` (0x0649) et reflétée dans
`payload.mem_used_mb` (0x060B). (Il n'existe pas de paramètres `payload.line_rate` / `payload.data_rate` ;
0x0607 et 0x0608 ne sont pas alloués dans `telemetry/parameters.yaml`.) Avant la correction, le mode IMAGING à lui seul accumulait environ
9,7 Mo/s et remplissait la mémoire de 20 Go en ~33 minutes sans aucune acquisition, ce qui explique
pourquoi une ancienne note pédagogique de cette fiche contredisait jadis le satellite.

### Étape 5 --- Déclencher la ou les acquisitions
**TC:** `PAYLOAD_CAPTURE(scene_id=N, lines=2048)` (Service 8, Subtype 1, func_id 28)  \
**Octets émis :** `1C <scene_id:uint16> 08 00` --- p. ex. scène 1042 = `1C 04 12 08 00`
**Note:** Les images n'apparaissent PAS d'elles-mêmes. Chaque acquisition est une
prise de vue commandée : `scene_id` est l'identifiant de produit attribué par le sol (0 = laisser la charge utile
l'attribuer) et `lines` est la longueur de la bande le long de la trace, 256-20000. 2048 lignes
à la fréquence ligne de 500 Hz correspondent à une acquisition de 4,10 s et, avec quatre bandes spectrales actives, à
l'image de référence de 4,0 Mo ; diviser `lines` par deux divise par deux le volume stocké. La géolocalisation est
apposée à bord à partir des éphémérides à l'ouverture de l'obturateur --- ce n'est pas un argument.
**Note:** Répéter pour chaque cible prévue dans la séance. Une acquisition est REFUSÉE
avec TM(1,8) si l'AOCS ne tient pas FINE_POINT avec une erreur totale < 0.05 deg, si
le FPA n'est pas prêt, ou si la mémoire ne peut pas contenir l'image --- l'avis d'échec
nomme la condition qui a refusé.
**Verify:** `payload.last_scene_id` (0x060C) = le `scene_id` commandé sous 10 s
**Note:** La qualité de l'image n'est pas télémesurée : elle est contrôlée au sol sur l'aperçu de chaque produit après transmission. Consigner dès maintenant les identifiants de scène pour pouvoir contrôler chaque produit à ce moment-là.

### Étape 5a --- Surveiller l'acquisition des images
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- HK charge utile, interroger toutes les 30 s
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- HK AOCS, interroger toutes les 30 s
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) --- HK TCS, interroger toutes les 30 s
**Verify:** `payload.image_count` (0x0605) en hausse (valeur courante > N0)
**Verify:** `payload.store_used` (0x0604) < 95 % pendant toute la séance
**Verify:** `aocs.att_error` (0x0217) reste < 0.1 deg pendant toute la séance
**Verify:** `tcs.temp_fpa` (0x0408) reste < -10.0 °C pendant toute la séance
**Action:** Si `payload.store_used` >= 95 %, mettre immédiatement fin à la séance (étape 6).
**Action:** Si `aocs.att_error` >= 0.5 deg, mettre immédiatement fin à la séance (étape 6).

### Étape 6 --- Mettre fin à la séance de prise de vue
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) --- commander STANDBY
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) sous 15 s
**Verify:** `tcs.cooler_fpa` (0x040C) = 0 sous 10 s --- le mode STANDBY arrête le refroidisseur du FPA
**Verify:** baisse de `eps.power_cons` (0x0106) observée (charge de prise de vue et refroidisseur de 15 W arrêtés)
**Note:** Consigner la valeur finale de `payload.image_count` (0x0605) sous le nom Nf. Images acquises = Nf - N0.

### Étape 7 --- Bilan après prise de vue
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- HK charge utile finale
**Verify:** `payload.store_used` (0x0604) < 95 %
**Verify:** `payload.image_count` (0x0605) = Nf (aucune hausse inattendue)
**Consigner :** Inscrire dans le journal de passage les images acquises, la variation de stockage et la durée de la séance.

## Conduite à tenir hors nominal
- Si `payload.mode` ne passe pas en IMAGING sous 15 s : renvoyer la commande
  une fois. Toujours sans transition : interrompre et signaler une anomalie charge utile.
- Si `payload.image_count` ne s'incrémente pas : panne possible du détecteur ou de la chaîne
  de données. Commander STANDBY et signaler l'anomalie.
- Si `aocs.att_error` dépasse 0.5 deg pendant la prise de vue : interrompre immédiatement la séance.
  Les images acquises avec une erreur élevée peuvent être inutilisables --- les signaler pour examen au sol.
- Si `tcs.temp_fpa` dépasse -5.0 °C : interrompre la prise de vue pour protéger le détecteur.
  Analyser les performances du refroidisseur.
- Si `eps.bat_soc` descend sous 40 % pendant la séance : interrompre la prise de vue afin de préserver
  la marge de puissance nécessaire à la sécurité du satellite.

## Postconditions
- [ ] Charge utile revenue en mode STANDBY, refroidisseur du FPA arrêté
- [ ] Nombre d'images et occupation de la mémoire consignés
- [ ] AOCS resté en pointage fin tout du long (att_error < 0.1 deg)
- [ ] Température du FPA restée à la consigne (<= -10.0 °C) tout du long
- [ ] Journal de passage mis à jour avec la synthèse de la séance de prise de vue
