# C2O design tokens

`c2o.tokens.json` is the single source of truth for colour, type, spacing,
radius and motion across the SMO consoles (`sim/`) and SpaceCDF (`design/`).
It uses the W3C Design Tokens (DTCG) format: every token has a `$value` and
a `$type`, and there are two themes, `theme.dark` (control room, the default
on the consoles) and `theme.light` (design work, the default in SpaceCDF).

## Change a token

1. Edit `c2o.tokens.json`.
2. Run `python3 shared/ui-tokens/build.py` (stdlib only). It writes:
   - the block between `/* tokens:begin */` and `/* tokens:end */` in
     `sim/packages/smo-common/src/smo_common/ui/design-system.css`, plus the
     contrast table in that file's header (everything else there is
     hand-written);
   - `design/frontend/src/theme/tokens.css` and `tokens.ts` (whole files).
3. `python3 shared/ui-tokens/build.py --check` exits 1 if an output is out of
   date or a contrast floor is missed (dark text 7:1, light text 4.5:1,
   graphics 3:1). `sim/tests/test_common/test_ui_tokens.py` runs it.
   `--contrast` prints the table.

Never edit a hex value in a generated file; the test will fail.

## Names

Output names are listed per target under `$extensions["org.c2o.outputs"]`.
The consoles keep their short names (`--bg --s1 --s2 --s3 --line --line-2
--val --tx --tx2 --tx3 --tx-off --accent --ok --warn --alarm --shelf --stale
--fill`, washes, `--fs-* --sp-* --radius* --motion --ease --font-*`).
SpaceCDF keeps its semantic names (`--surface-0 … --interactive
--status-caution …`); new names may be added, existing ones are never
removed.

The visual reference for every component and state is
`sim/packages/smo-common/src/smo_common/ui/gallery.html`, served by any SMO
server at `/static/shared/gallery.html`.

## Fonts

IBM Plex Sans (400, 400 italic, 500, 600) and IBM Plex Mono (400, 400 italic,
500), latin and latin-ext, are self-hosted in `smo_common/ui/fonts/` under the
SIL OFL 1.1 (`fonts/OFL.txt`). SpaceCDF loads the same faces from
`@fontsource`. Mono has no 600: never set mono heavier than 500.
