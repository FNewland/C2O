# OER edition working directory

- `oer_edit_spec.md` — binding editorial specification (numbering, notation, cuts, template).
- `oer_inventory.md` — line-level inventory of the source book that the spec was derived from.
- `chapters/NN_<slug>.md` — per-chapter OER sources; the build concatenates them in numeric order.
- `XREF_NOTES.md` — cross-chapter change requests for the integrator.
- `build_oer.py` — builds `../pdf/Concurrent_Spacecraft_Design_OER.pdf` (neutral brand, CC BY cover).

Source of the conversion: `../course/facilitator_book_expanded.md` (unchanged).

Build: `make deps` once, then `make` (or `make docker` for a clean container build). See Makefile.
