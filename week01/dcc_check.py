import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
root = ET.parse(HERE / "sensor_dcc.xml").getroot()
tol = 0.5  # kPa: allowed error

for p in root.iter("point"):
    ref = float(p.get("ref"))
    meas = float(p.get("measured"))
    u = float(p.get("uncertainty"))
    err = meas - ref
    ok = round(abs(err) + u, 6) <= tol      # rule: |error| + uncertainty <= tolerance
    print(f"{ref:6.1f} kPa  error {err:+.2f}  +/-{u}  {'PASS' if ok else 'FAIL'}")