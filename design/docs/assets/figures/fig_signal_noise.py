"""Eb/N0 vs BER for common modulations (AWGN, theoretical) and a coded curve."""
from math import erfc
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

erfc_v = np.vectorize(erfc)


def Q(x):
    return 0.5 * erfc_v(x / np.sqrt(2))


EbN0_dB = np.linspace(0, 14, 400)
EbN0 = 10 ** (EbN0_dB / 10)

ber_bpsk = Q(np.sqrt(2 * EbN0))                                  # BPSK / Gray QPSK
M = 8
ber_8psk = (2 / np.log2(M)) * Q(np.sqrt(2 * np.log2(M) * EbN0) * np.sin(np.pi / M))
ber_fsk = 0.5 * np.exp(-EbN0 / 2)                                 # non-coherent FSK
ber_cc = Q(np.sqrt(2 * 10 ** ((EbN0_dB + 5) / 10)))               # ≈5 dB coding gain

ax.semilogy(EbN0_dB, ber_bpsk, lw=2.0, color=COLORS["accent"], label="BPSK / QPSK, uncoded")
ax.semilogy(EbN0_dB, ber_8psk, lw=2.0, color=COLORS["accent_2"], label="8-PSK, uncoded")
ax.semilogy(EbN0_dB, ber_fsk, lw=2.0, color=COLORS["grey"], label="Non-coherent FSK")
ax.semilogy(EbN0_dB, ber_cc, lw=2.0, color=COLORS["accent_3"], ls="--",
            label="BPSK + conv. + RS(255,223) (≈ 5 dB gain)")

for ber, lab in [(1e-5, "BER = 10⁻⁵"), (1e-7, "BER = 10⁻⁷")]:
    ax.axhline(ber, color=COLORS["grey"], lw=0.9, ls=":")
    ax.text(13.8, ber * 1.3, lab, fontsize=8.5, color=COLORS["grey"], ha="right", clip_on=True)

# Coding-gain arrow at BER 1e-5
x_unc = EbN0_dB[np.argmin(np.abs(ber_bpsk - 1e-5))]
x_cod = EbN0_dB[np.argmin(np.abs(ber_cc - 1e-5))]
ax.annotate("", xy=(x_cod, 1e-5), xytext=(x_unc, 1e-5),
            arrowprops=dict(arrowstyle="<->", color=COLORS["accent_3"], lw=1.2))
ax.text((x_unc + x_cod) / 2, 2.2e-6, f"coding gain ≈ {x_unc - x_cod:.0f} dB",
        ha="center", va="top", fontsize=8.5, color=COLORS["accent_3"], clip_on=True)

ax.set_xlabel("Eb/N₀ (dB)")
ax.set_ylabel("Bit error rate")
ax.set_title("Eb/N₀ → BER for common modulations (theoretical, AWGN channel)")
ax.set_xlim(0, 14)
ax.set_ylim(1e-9, 0.5)
ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="lower left", fontsize=9)
save(fig, Path(__file__).stem)
