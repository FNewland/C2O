"""Eb/N0 vs BER for common modulation/coding schemes — required link margin."""
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import erfc
from uottawa_brand import apply_style, COLORS, SERIES, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

EbN0_dB = np.linspace(0, 14, 200)
EbN0 = 10**(EbN0_dB/10)

# BPSK uncoded:  BER = 0.5 * erfc(sqrt(EbN0))
ber_bpsk = 0.5 * erfc(np.sqrt(EbN0))
# QPSK: same Eb/N0 vs BER as BPSK (gray-coded)
ber_qpsk = ber_bpsk
# 8PSK: BER ≈ (2/3) * Q(sqrt(2 EbN0) sin(pi/8))
def Q(x): return 0.5 * erfc(x/np.sqrt(2))
ber_8psk = (2/3) * Q(np.sqrt(2 * EbN0) * np.sin(np.pi/8))

# Uncoded GFSK ~ similar to FSK noncoherent
ber_fsk = 0.5 * np.exp(-EbN0/2)

# Concatenated coding (RS+conv) gain typically -5 dB at 1e-5
EbN0_dB_cc = EbN0_dB + 5
ber_cc = 0.5 * erfc(np.sqrt(10**(EbN0_dB_cc/10)))   # shift left

ax.semilogy(EbN0_dB, ber_bpsk, lw=2.0, color=COLORS["garnet"], label="BPSK / QPSK uncoded")
ax.semilogy(EbN0_dB, ber_8psk, lw=2.0, color=COLORS["blue"], label="8-PSK uncoded")
ax.semilogy(EbN0_dB, ber_fsk,  lw=2.0, color=COLORS["warm_grey"], label="Non-coherent FSK")
ax.semilogy(EbN0_dB, ber_cc,   lw=2.0, color=COLORS["green"], ls="--",
            label="BPSK + RS(255,223)+conv (~5 dB gain)")

# Common BER targets
ax.axhline(1e-5, color=COLORS["polar"], lw=0.8)
ax.text(0.3, 1.4e-5, "BER = 10⁻⁵", fontsize=8.5, color=COLORS["warm_grey"])
ax.axhline(1e-7, color=COLORS["polar"], lw=0.8)
ax.text(0.3, 1.4e-7, "BER = 10⁻⁷", fontsize=8.5, color=COLORS["warm_grey"])

ax.set_xlabel("Eb/N₀ (dB)")
ax.set_ylabel("Bit Error Rate")
ax.set_title("Eb/N₀ → BER for common modulations  (theoretical, AWGN channel)")
ax.set_xlim(0, 14)
ax.set_ylim(1e-9, 0.5)
ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="upper right", frameon=False, fontsize=9)
add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_signal_noise.png")
print("OK signal noise")
