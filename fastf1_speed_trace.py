"""Friday task (P4): plot the fastest qualifying lap's speed trace with real F1 data."""
import os
from pathlib import Path

import fastf1
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
cache = HERE / "f1cache"
os.makedirs(cache, exist_ok=True)              # FastF1 stores downloaded data here
fastf1.Cache.enable_cache(str(cache))

session = fastf1.get_session(2024, "Monza", "Q")  # year, track, session (Q = qualifying)
session.load()                                     # downloads timing + telemetry (first run is slow)

lap = session.laps.pick_fastest()                  # the pole lap
tel = lap.get_car_data().add_distance()            # speed, rpm, gear, throttle, brake + distance

fig, ax = plt.subplots(3, 1, sharex=True, figsize=(10, 7))
ax[0].plot(tel["Distance"], tel["Speed"]);    ax[0].set_ylabel("Speed [km/h]")
ax[1].plot(tel["Distance"], tel["Throttle"]); ax[1].set_ylabel("Throttle [%]")
ax[2].plot(tel["Distance"], tel["nGear"]);    ax[2].set_ylabel("Gear")
ax[2].set_xlabel("Distance [m]")
fig.suptitle(f"{lap['Driver']} fastest lap, Monza 2024 qualifying")
plt.savefig(HERE / "monza_fastest_lap.png", dpi=120)
plt.show()
