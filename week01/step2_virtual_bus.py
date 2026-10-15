import math
import time

import can
import cantools
from pathlib import Path

HERE = Path(__file__).parent   # folder this script is in, so it works from anywhere

db = cantools.database.load_file(HERE / "engine.dbc")
msg1 = db.get_message_by_name("ENGINE_DATA_1")
msg2 = db.get_message_by_name("ENGINE_DATA_2")

# Two "nodes" on the same virtual CAN bus
ecu = can.Bus(interface="virtual", channel="vcan0")
logger = can.Bus(interface="virtual", channel="vcan0")

log_file = can.ASCWriter(str(HERE / "engine_log.asc"))
rpm_trace = []

t0 = time.time()
for step in range(300):                      # 300 steps x 10 ms = 3 seconds
    t = time.time() - t0
    rpm = 4000 + 3000 * math.sin(2 * t)
    data1 = msg1.encode({
        "EngineSpeed": rpm,
        "ThrottlePos": 50 + 50 * math.sin(2 * t),
        "CoolantTemp": 90,
        "MAP": 100 + 80 * math.sin(2 * t),
    })
    ecu.send(can.Message(arbitration_id=msg1.frame_id, data=data1, is_extended_id=False))

    if step % 10 == 0:                       # ENGINE_DATA_2 only every 100 ms
        data2 = msg2.encode({"Lambda": 1.0 + 0.05 * math.sin(t)})
        ecu.send(can.Message(arbitration_id=msg2.frame_id, data=data2, is_extended_id=False))

    # the logger node reads everything waiting on the bus
    frame = logger.recv(timeout=0.01)
    while frame is not None:
        log_file.on_message_received(frame)
        decoded = db.decode_message(frame.arbitration_id, frame.data)
        if "EngineSpeed" in decoded:
            rpm_trace.append((t, decoded["EngineSpeed"]))
        frame = logger.recv(timeout=0)

    time.sleep(0.01)

log_file.stop()
ecu.shutdown()
logger.shutdown()
print(f"Logged {len(rpm_trace)} EngineSpeed values to engine_log.asc")
print("Last value:", rpm_trace[-1])

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ts, rpms = zip(*rpm_trace)
plt.plot(ts, rpms)
plt.xlabel("time [s]")
plt.ylabel("EngineSpeed [rpm]")
plt.title("EngineSpeed received on the virtual CAN bus")
plt.savefig(HERE / "rpm_plot.png", dpi=120)
print("Saved rpm_plot.png")
