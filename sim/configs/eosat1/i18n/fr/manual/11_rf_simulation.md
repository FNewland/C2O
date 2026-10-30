# Couche de simulation RF d'EOSAT-1

**Manual-Scope:** system — documentation du système de formation, ne fait pas partie du manuel des opérations de vol.

**Référence du document :** EOSAT1-UM-RFS-011
**Édition :** 1.0
**Date :** 2026-04-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Objet

Le présent document décrit le pont de simulation RF (smo-rfsim), une couche facultative qui insère
la mise en trames de transfert CCSDS et la simulation du canal RF entre le simulateur du satellite et le
système de contrôle de mission (MCS). Il permet des scénarios de formation réalistes sur le segment sol, notamment
la synchronisation de trames, la correction d'erreurs et les exercices de bilan de liaison.

## 2. Modes de fonctionnement

Le pont prend en charge trois modes de fonctionnement, sélectionnables par configuration ou par variable d'environnement :

| Mode   | Mise en trames   | RF              | Dépendances         | Latence |
|--------|------------------|-----------------|---------------------|---------|
| PACKET | Non              | Non             | Aucune (par défaut) | ~0 ms   |
| FRAME  | TF CCSDS + CLTU  | Inversion de bits selon le TEB | Python pur uniquement | <5 ms |
| RF     | TF CCSDS + CLTU  | BPSK (GR/numpy) | gnuradio (facultatif) | ~50 ms |

### 2.1 Mode PACKET

Relais TCP transparent. Le pont se contente de transmettre, sans aucun traitement, les paquets ECSS préfixés par leur longueur entre le
simulateur et le MCS. C'est le mode par défaut ; il reproduit le comportement
d'origine du système.

### 2.2 Mode FRAME

Applique le protocole complet de mise en trames de transfert CCSDS :

- **Liaison descendante (TM) :** les paquets ECSS sont placés dans des trames de transfert TM de longueur fixe
  (CCSDS 132.0-B-3), avec un marqueur de synchronisation attaché (ASM), un champ de contrôle d'erreur de trame (FECF)
  et un multiplexage par canaux virtuels. Les trames traversent un modèle de canal qui injecte des erreurs
  binaires à un taux déterminé par le réglage d'Eb/N0. Le récepteur corrèle l'ASM,
  valide le FECF et extrait les paquets.

- **Liaison montante (TC) :** les paquets TC sont codés en unités de transfert de liaison de commande (CLTU)
  conformément à CCSDS 232.0-B-4, avec des blocs de code BCH(64,56). Les CLTU traversent le modèle de canal
  et sont décodées avec correction des erreurs sur un bit.

### 2.3 Mode RF

Ajoute la modulation/démodulation BPSK à la chaîne du mode FRAME. Lorsque GNU Radio est installé,
de véritables graphes de traitement du signal assurent la modulation, la mise en forme des impulsions en racine de cosinus surélevé,
le CAG, la récupération de porteuse par boucle de Costas et la récupération d'horloge M&M. Lorsque GNU Radio n'est pas disponible,
un simulateur de canal fondé sur numpy assure l'injection de bruit AWGN et le décalage de fréquence Doppler.

## 3. Architecture

```
                    mode PACKET (contournement)
Simulateur ──TCP:8002───────────────────────────── MCS
  TM:8002                                        se connecte à
  TC:8001           mode FRAME / RF                8012/8011
     │        ┌────────────────────────────┐
     └───────>│     Pont smo-rfsim         │──TCP:8012──> MCS
              │                            │
  TC:8001<────│  TMFrameBuilder            │<──TCP:8011── MCS
              │  VCMultiplexer             │
              │  [RS Encoder]              │
              │  [Conv Encoder]            │    ┌──────────┐
              │  ChannelModel              │    │ Radio    │
              │  [Viterbi Decoder]         │───>│ UI web   │
              │  [RS Decoder]              │    │ :8094    │
              │  FrameSynchronizer         │    └──────────┘
              │  TMFrameParser             │
              │  CLTUEncoder/Decoder       │
              └────────────────────────────┘
                Interroge le WS du simulateur :8080 pour
                Eb/N0, Doppler, distance
```

Le MCS ne nécessite aucune modification de code — il se connecte aux ports 8012/8011 au lieu de 8002/8001.

## 4. Détails des trames de transfert CCSDS

### 4.1 Trames TM descendantes

- **Longueur de trame :** 1115 octets (configurable, ASM non compris)
- **ASM :** 4 octets (0x1ACFFC1D), placés en tête de chaque trame
- **En-tête primaire :** 6 octets — SCID (10 bits), VCID (3 bits), compteur de trames, pointeur de premier en-tête (First Header Pointer)
- **Zone de données :** variable (longueur de trame - 6 d'en-tête - 2 de FECF)
- **FECF :** 2 octets, CRC-16/CCITT-FALSE sur l'en-tête et la zone de données

### 4.2 Canaux virtuels

| VCID | Usage              | Priorité |
|------|--------------------|----------|
| 0    | HK en temps réel   | La plus haute |
| 1    | Relecture de la TM enregistrée | Moyenne |
| 7    | Remplissage (trames vides) | La plus basse |

### 4.3 CLTU de liaison montante TC

- **Séquence de début :** 2 octets (0xEB90)
- **Blocs de code :** 8 octets chacun (7 de données + 1 de parité BCH), BCH(64,56)
- **Séquence de fin :** 8 octets (0xC5C5C5C5C5C5C579)
- **Correction d'erreurs :** correction d'un bit par bloc de code

### 4.4 Codage de canal

- **Reed-Solomon :** RS(255,223) sur GF(2^8), correction de 16 symboles erronés
- **Convolutif :** rendement 1/2, longueur de contrainte K=7 (G1=0x79, G2=0x5B)
- **Décodeur de Viterbi :** décodeur en treillis add-compare-select en Python pur (64 états)

## 5. Synchronisation de trames

Le synchroniseur de trames met en œuvre un modèle d'acquisition à trois états :

1. **SEARCH :** balaie le flux d'octets à la recherche d'une corrélation avec l'ASM (jusqu'à 3 erreurs binaires tolérées)
2. **VERIFY :** confirme l'ASM à l'intervalle de trame attendu (configurable, 3 trames par défaut)
3. **LOCK :** extrait les trames à cadence fixe ; le volant d'inertie (flywheel) tolère jusqu'à 4 absences consécutives

## 6. Modèle de canal

Le modèle de canal applique des dégradations configurables :

| Paramètre     | Description              | Défaut   |
|---------------|--------------------------|----------|
| `eb_n0_db`    | Eb/N0 en dB              | 10.0     |
| `ber_target`  | TEB visé                 | 1e-6     |
| `path_loss_db`| Affaiblissement en espace libre | 150.0 dB |
| `doppler_hz`  | Décalage Doppler         | 0.0 Hz   |
| `delay_ms`    | Temps de propagation     | 3.0 ms   |

Le TEB est calculé à partir d'Eb/N0 au moyen de la formule théorique de la BPSK :
TEB = 0,5 × erfc(√(Eb/N0)).

Lorsque le pont est connecté au WebSocket du simulateur (port 8080), il lit les paramètres de bilan de liaison
du modèle TTC et met à jour le modèle de canal en temps réel.

## 7. Affichage du frontal radio

L'interface web Radio (port 8094) affiche en temps réel l'état de la liaison RF :

- **Indicateurs de verrouillage :** Carrier Lock, Bit Sync, Frame Sync (LED : vert/jaune/rouge)
- **Mesures RF :** RSSI, Eb/N0, TEB, marge de liaison, avec bargraphes
- **Dynamique :** Doppler, distance, débit, temps de propagation
- **Compteurs de trames :** trames valides/erronées, CLTU envoyées/acquittées, barre de taux d'erreur trame
- **Canaux virtuels :** LED d'activité VC0/1/7
- **Graphiques d'historique :** séries temporelles d'Eb/N0 et du TEB, nombre de trames par seconde

## 8. Configuration

La configuration est chargée depuis `configs/eosat1/rfsim.yaml` :

```yaml
mode: PACKET   # PACKET | FRAME | RF

ccsds:
  tm_frame_length: 1115
  scid: 1
  fecf_present: true
  rs_enabled: true
  convolutional_enabled: true

channel:
  eb_n0_db: 10.0
  doppler_hz: 0.0
  delay_ms: 3.0

network:
  sim_tm_port: 8002
  sim_tc_port: 8001
  mcs_tm_port: 8012
  mcs_tc_port: 8011
  radio_port: 8094
```

## 9. Démarrage

### 9.1 Par variable d'environnement

```bash
SMO_RF_MODE=FRAME ./start.sh
```

### 9.2 Par la ligne de commande

```bash
smo-rfsim --config configs/eosat1/rfsim.yaml --mode FRAME --radio-web
```

### 9.3 Options de la ligne de commande

| Option          | Description                          |
|-----------------|--------------------------------------|
| `--config`      | Chemin vers rfsim.yaml               |
| `--mode`        | Forcer le mode (PACKET/FRAME/RF)     |
| `--eb-n0`       | Forcer Eb/N0 en dB                   |
| `--radio-ui`   | Lancer le tableau de bord en terminal (rich) |
| `--radio-web`  | Lancer le tableau de bord web sur radio_port |
| `-v`            | Journalisation détaillée             |

## 10. Scénarios de formation

### 10.1 Exercice de dégradation du signal

1. Démarrer en mode FRAME avec Eb/N0 = 12 dB (liaison propre)
2. Réduire progressivement Eb/N0 et observer l'augmentation du TEB sur l'affichage Radio
3. Vers ~6 dB, observer l'apparition des erreurs de trame (échecs du FECF)
4. Vers ~3 dB, observer une perte de paquets importante ; le MCS affiche des données périmées

### 10.2 Perte et reprise de la synchronisation de trames

1. Partir d'une liaison propre à l'état LOCK
2. Injecter des salves d'erreurs (Eb/N0 faible pendant quelques secondes) pour provoquer le passage LOCK → SEARCH
3. Observer la transition de la LED de synchronisation de trames de Radio : vert → rouge → jaune → vert
4. Vérifier que le MCS récupère et reprend l'affichage de la télémesure

### 10.3 Erreurs sur les CLTU montantes

1. Envoyer des télécommandes à travers le pont en mode FRAME
2. Abaisser Eb/N0 pour injecter des erreurs dans les blocs de code des CLTU
3. Observer la réussite de la correction BCH d'un bit (incrémentation du compteur CLTU Ack)
4. Dégrader encore jusqu'à l'échec du décodage des CLTU (le compteur Ack cesse de s'incrémenter)

## 11. Documents associés

| Document                        | Description                    |
|---------------------------------|--------------------------------|
| EOSAT1-UM-MIS-001 (section 00) | Vue d'ensemble de la mission   |
| EOSAT1-UM-TTC-006 (section 05) | Sous-système TTC               |
| EOSAT1-UM-CMD-009 (section 09) | Référence des commandes        |
| CCSDS 132.0-B-3                 | *TM Space Data Link Protocol*  |
| CCSDS 232.0-B-4                 | *TC Space Data Link Protocol*  |
| CCSDS 131.0-B-4                 | *TM Synchronization & Coding* |
| CCSDS 401.0-B-32                | *Earth Stations and Spacecraft* |
