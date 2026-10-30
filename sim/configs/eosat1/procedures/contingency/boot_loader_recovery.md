# CTG-018: Boot Loader Recovery (RETIRED)

**Category:** Contingency
**Status:** RETIRED 2026-10-30 (author ruling Q15) --- superseded by CTG-021
**Position Lead:** FDIR / Systems

## Retirement notice
This card is retired and must not be flown. It duplicated CTG-021 (OBC
Bootloader Recovery), and the two cards had drifted apart. CTG-021 is the
canonical procedure for recovering an OBC that is stuck in the bootloader
(`obdh.sw_image` (0x0311) = 0): diagnosis, `OBC_BOOT_APP`, boot inhibit, memory
check, memory reload, and the time re-set after recovery.

Use **CTG-021** (`contingency/obc_bootloader_recovery.md`) instead. Every
procedure and role card that pointed at CTG-018 now points at CTG-021.

This file is kept so that the identifier still resolves in the procedure index
and in older course material. It commands nothing; the index declares it
`advisory: true`, so the MCS does not offer it for execution. The former text
remains in the repository history.
