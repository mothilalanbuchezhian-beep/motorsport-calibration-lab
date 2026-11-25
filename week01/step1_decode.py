import cantools
from pathlib import Path

HERE = Path(__file__).parent   # folder this script is in, so it works from anywhere

db = cantools.database.load_file(HERE / "engine.dbc")

for msg in db.messages:
    print(f"Message {msg.name}  ID={msg.frame_id} (0x{msg.frame_id:X})  length={msg.length} bytes")
    for sig in msg.signals:
        print(f"   {sig.name:12s} start={sig.start:2d} len={sig.length:2d} "
              f"factor={sig.scale} offset={sig.offset} unit={sig.unit}")

msg = db.get_message_by_name("ENGINE_DATA_1")
values = {"EngineSpeed": 8250, "ThrottlePos": 80, "CoolantTemp": 92, "MAP": 185.5}
raw = msg.encode(values)
print("\nPhysical values :", values)
print("Raw bytes (hex) :", " ".join(f"{b:02X}" for b in raw))
print("Decoded again   :", msg.decode(raw))

msg2 = db.get_message_by_name("ENGINE_DATA_2")
raw2 = msg2.encode({"Lambda": 1.0, "OilPressure": 4.5})
print("\nENGINE_DATA_2 hex :", " ".join(f"{b:02X}" for b in raw2))
print("Decoded again     :", msg2.decode(raw2))
