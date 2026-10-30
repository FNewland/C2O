# 136 — `gfsk_mod_index` and `gmsk_bt` never reached the transmitter

**Status:** Fixed

## Summary

`configs/eosat1/rfsim.yaml` has `pipeline.gmsk_bt` and
`pipeline.gfsk_mod_index`, and `RFSimConfig` validates both (`0.1..1.0`,
`>0..2`). Neither reached the downlink modulator. `PipelineCoordinator` built
`SpacecraftTX` without them, and `SpacecraftTX` built its `Modulator` with
defaults. Only the receiver got `gmsk_bt`. Changing either value in the
config did nothing on the air.

The recorder had the same gap for the GFSK index: `RecorderConfig` had no
field for it, and `smo-rfsim-record` had no option.

## Fix

* `SpacecraftTX(gmsk_bt=…, gfsk_mod_index=…)`, passed from `pc.gmsk_bt` and
  `pc.gfsk_mod_index` by the coordinator.
* `RecorderConfig.gfsk_mod_index`, written to the sidecar, plus
  `smo-rfsim-record --gfsk-h`.

## Regression tests

`tests/test_rfsim/test_modulation_roundtrip.py::TestCPMConfigReachesTheTransmitter`.
