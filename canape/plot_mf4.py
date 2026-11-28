"""Read CANape MDF4 recordings (XCPsim demo) with asammdf and plot them.

1. Before vs after calibration: channel1 with ampl = 6 (first recording)
   and with ampl = 15 (second recording).
2. The KF2 map stored in the last recording, as a heat map: the spike
   you put into one cell shows up as one bright square.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from asammdf import MDF

HERE = Path(__file__).parent
BEFORE = HERE / "CANapeSplit000.MF4"   # 15:42, ampl = 6 (unchanged)
AFTER = HERE / "CANapeSplit001.MF4"    # 15:47, after ampl 6 -> 15
SPIKE = HERE / "ampl 6 to 16, period 5 to 2, KF2 spike test.MF4"

# --- 1. what is inside an MF4 file? ---------------------------------------
mdf = MDF(SPIKE)
print("Recording started:", mdf.header.start_time)
names = sorted({ch.name for group in mdf.groups for ch in group.channels})
print(len(names), "channels, for example:", [n for n in names if "[" not in n])

for name in ["channel1", "Triangle", "ampl", "period"]:
    sig = mdf.get(name)
    print(f"{name:10s} {len(sig.samples):4d} samples  "
          f"{sig.timestamps[0]:.2f}-{sig.timestamps[-1]:.2f} s  "
          f"min {sig.samples.min():.3g}  max {sig.samples.max():.3g}  unit '{sig.unit}'")

# --- 2. before vs after the ampl change ------------------------------------
before = MDF(BEFORE).get("channel1")
after = MDF(AFTER).get("channel1")

fig, ax = plt.subplots(2, 1, figsize=(10, 7))
ax[0].plot(before.timestamps, before.samples, label="before: ampl = 6")
ax[0].plot(after.timestamps, after.samples, label="after: ampl = 15")
ax[0].set_xlabel("time [s]")
ax[0].set_ylabel("channel1")
ax[0].set_title("Live calibration over XCP: effect of ampl on channel1")
ax[0].legend()
ax[0].grid(True)

# --- 3. the KF2 map with your spike ------------------------------------------
kf2 = np.array([[mdf.get(f"KF2[{i}][{j}]").samples[0] for j in range(8)] for i in range(8)])
curve1 = [int(mdf.get(f"Curve1[{i}]").samples[0]) for i in range(8)]   # x axis
curve2 = [int(mdf.get(f"Curve2[{i}]").samples[0]) for i in range(8)]   # y axis
print("KF2 map (rows = Curve2, columns = Curve1):\n", kf2)

im = ax[1].imshow(kf2, cmap="Reds", origin="lower")
ax[1].set_xticks(range(8), curve1)
ax[1].set_yticks(range(8), curve2)
ax[1].set_xlabel("Curve1 (x axis)")
ax[1].set_ylabel("Curve2 (y axis)")
ax[1].set_title("KF2 map as recorded: one spiked cell = bad calibration practice")
for i in range(8):
    for j in range(8):
        ax[1].text(j, i, kf2[i, j], ha="center", va="center", fontsize=8)
fig.colorbar(im, ax=ax[1])

fig.tight_layout()
fig.savefig(HERE / "canape_results.png", dpi=120)
print("Saved canape_results.png")
plt.show()
