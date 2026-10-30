# CTG-018 : Reprise par le chargeur d'amorçage (RETIRÉE)

**Catégorie :** Contingence
**Statut :** RETIRÉE le 2026-10-30 (décision de l'auteur Q15) --- remplacée par CTG-021
**Poste responsable :** FDIR / Systèmes

## Avis de retrait
Cette carte est retirée et ne doit pas être utilisée en vol. Elle faisait double emploi
avec CTG-021 (Reprise par le chargeur d'amorçage de l'OBC), et les deux cartes avaient
divergé. CTG-021 est la procédure de référence pour reprendre un OBC bloqué dans le
chargeur d'amorçage (`obdh.sw_image` (0x0311) = 0) : diagnostic, `OBC_BOOT_APP`,
inhibition de l'amorçage, contrôle mémoire, rechargement mémoire et remise à l'heure
après la reprise.

Utiliser **CTG-021** (`contingency/obc_bootloader_recovery.md`) à la place. Toutes les
procédures et fiches de poste qui renvoyaient à CTG-018 renvoient désormais à CTG-021.

Ce fichier est conservé pour que l'identifiant reste résolu dans l'index des procédures
et dans les anciens supports de cours. Il ne commande rien ; l'index le déclare
`advisory: true`, de sorte que le MCS ne le propose pas à l'exécution. L'ancien texte
reste disponible dans l'historique du dépôt.
