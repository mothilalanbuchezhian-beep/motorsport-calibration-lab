# Week 1: CAN Bus Basics and DBC Files (19 – 25 Oct 2026)

**Goal of the week:** understand how a race car's ECU sends data on CAN, describe that data in a DBC file, and simulate a real CAN bus on your laptop.
**Files in this folder:** `engine.dbc` · `step1_decode.py` · `step2_virtual_bus.py` · `fastf1_speed_trace.py` (all tested)

## The week at a glance

| Day | Time | Task |
|---|---|---|
| Mon 19 Oct | 1 h | Theory 1: what CAN is and how a frame looks |
| Tue 20 Oct | 1.5 h | Setup: Python 3.12, project folder, GitHub repo |
| Wed 21 Oct | 1 h | Theory 2: DBC files, scaling, byte order + flashcards |
| Thu 22 Oct | 1.5 h | Run `step1_decode.py` and decode bytes by hand |
| Fri 23 Oct | 1 h | Race data: first F1 lap plot with FastF1 |
| Sat 24 Oct | 3 h | Virtual CAN bus, logging, bus-load calculation, your own changes |
| Sun 25 Oct | 1 h | README, push to GitHub, flashcards, learning log |

---

## MONDAY: Theory 1, what CAN is (1 h)

**Read:** CSS Electronics, *"CAN Bus Explained – A Simple Intro"* (search that title). Then write the notes below in your own words on one page.

### What CAN is
- **CAN = Controller Area Network.** Two wires (**CAN-H** and **CAN-L**) shared by all control units (ECU, datalogger, dash, gearbox controller, power box).
- Every unit can **send** and every unit **hears everything**. There's no "address": each message has an **ID** that says *what* it is (e.g. ID 0x100 = engine data), not *who* it's for.
- Typical race-car speed: **500 kbit/s or 1 Mbit/s**.

### How one CAN frame looks (standard 11-bit frame)

| Field | Bits | What it does |
|---|---|---|
| SOF (start of frame) | 1 | "A message starts now" |
| **ID (identifier)** | **11** | What the message is. **Lower ID = higher priority** |
| RTR | 1 | Data frame or request frame |
| IDE | 1 | 0 = standard 11-bit ID, 1 = extended 29-bit ID |
| r0 | 1 | Reserved |
| **DLC (data length code)** | **4** | How many data bytes follow (0–8) |
| **Data** | **0–64** | The actual values (rpm, temps…), 0 to 8 bytes |
| CRC | 15 + 1 | Checksum, to detect transmission errors |
| ACK | 2 | Any receiver confirms "I got it" |
| EOF | 7 | End of frame |
| IFS | 3 | Pause before the next frame |

**Total for 8 data bytes: 111 bits** (plus a few "stuff bits", see below).

### 5 ideas you must be able to explain

| Idea | Plain explanation |
|---|---|
| **Arbitration** | If two units start sending at once, they compare IDs bit by bit. A "0" (dominant) beats a "1". **The lowest ID wins** and the other unit waits. No data is lost. That's why critical messages (engine speed) get low IDs |
| **Bit stuffing** | After 5 identical bits in a row, the sender adds 1 opposite bit, so receivers stay in sync |
| **Termination** | One **120 Ω resistor at each end** of the bus. Measured between CAN-H and CAN-L with the power off, you should see **60 Ω**. Wrong termination = errors |
| **Error handling** | Units count errors. Too many → "error passive" → **"bus off"** (the unit stops sending). Very important when fault-finding at a rally |
| **CAN FD** | Newer version: up to **64 data bytes** and faster data phase. Many modern ECUs use it |

**Check yourself:** cover the tables and explain arbitration and termination out loud in 1 minute each.

---

## TUESDAY: Setup (1.5 h)

Your PC currently has **Python 3.6**, which is too old (FastF1 needs 3.9+). Install a new Python **next to it**; the old one stays untouched.

### Step 1: install Python 3.12 (15 min)
1. Go to **python.org → Downloads → Windows → Python 3.12.x (64-bit installer)**.
2. Run it. **Tick "Add python.exe to PATH"** at the bottom of the first screen, then "Install Now".
3. Open a **new** terminal (PowerShell) and check:
   ```
   py -3.12 --version
   ```
   You should see `Python 3.12.x`.

### Step 2: project folder + virtual environment (15 min)
A *virtual environment* is a private Python installation for one project, so libraries never clash.
```
cd D:\GERMAN
mkdir motorsport-calibration-lab
cd motorsport-calibration-lab
py -3.12 -m venv .venv
.venv\Scripts\activate
```
After `activate`, your prompt starts with `(.venv)`. **Do this activate step every time** you open a new terminal for this project.

If PowerShell says *"running scripts is disabled"*, run this once and answer **Y**:
```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Step 3: install the libraries (10 min)
```
pip install python-can cantools matplotlib fastf1
```

| Library | What it does |
|---|---|
| `python-can` | Sends and receives CAN frames (virtual bus now, real USB adapter later) |
| `cantools` | Reads DBC files and converts physical values ↔ raw bytes |
| `matplotlib` | Plots |
| `fastf1` | Downloads real F1 timing and telemetry |

### Step 4: copy the week-1 files (5 min)
Copy everything from `D:\GERMAN\resume_pipeline\career\week01\` into `D:\GERMAN\motorsport-calibration-lab\week01\`.

### Step 5: GitHub repo (15 min)
1. On github.com create a new **public** repo: `motorsport-calibration-lab`.
2. In your project folder:
   ```
   git init
   echo .venv/ > .gitignore
   echo f1cache/ >> .gitignore
   git add .
   git commit -m "Week 1: CAN basics setup"
   git branch -M main
   git remote add origin https://github.com/mothilalanbuchezhian-beep/motorsport-calibration-lab.git
   git push -u origin main
   ```


---

## WEDNESDAY: Theory 2, DBC files (1 h)

**Read:** CSS Electronics, *"DBC File Explained – A Simple Intro"*.

### What a DBC is
A CAN frame is just bytes, like `90 65 C8 84 3F 07 00 00`. The **DBC file** is the dictionary that says **which bits mean what**. Every logger, dash and analysis tool (CANape, MoTeC, Vector CANoe) loads a DBC.

### Read one line of our `engine.dbc`
```
BO_ 256 ENGINE_DATA_1: 8 ECU
 SG_ EngineSpeed : 0|16@1+ (0.25,0) [0|16383.75] "rpm" DASH,LOGGER
```

| Part | Meaning |
|---|---|
| `BO_ 256 ENGINE_DATA_1: 8 ECU` | Message with **ID 256** (= 0x100), name ENGINE_DATA_1, **8 bytes**, sent by the **ECU** |
| `SG_ EngineSpeed` | A signal inside it |
| `0\|16` | Starts at **bit 0**, is **16 bits** long |
| `@1` | Byte order: **1 = Intel (little-endian)**, 0 = Motorola (big-endian) |
| `+` | Unsigned (no negative raw values) |
| `(0.25,0)` | **factor 0.25, offset 0** |
| `[0\|16383.75]` | Allowed physical range |
| `"rpm"` | Unit |
| `DASH,LOGGER` | Who receives it |

### The one formula you must know
**physical value = raw value × factor + offset**
**raw value = (physical value − offset) ÷ factor**

### Practice by hand (paper, 15 min)

| Signal | Physical | Factor / offset | Raw (decimal) | Raw (hex) |
|---|---|---|---|---|
| EngineSpeed | 6500 rpm | 0.25 / 0 | 26000 | 0x6590 |
| ThrottlePos | 80 % | 0.4 / 0 | 200 | 0xC8 |
| CoolantTemp | 92 °C | 1 / −40 | 132 | 0x84 |
| MAP | 185.5 kPa | 0.1 / 0 | 1855 | 0x073F |

Cover the right two columns and redo them yourself. Then answer:
1. Why does CoolantTemp have offset −40? *(So 8 bits can show −40 °C … 215 °C.)*
2. Why does EngineSpeed use factor 0.25 instead of 1? *(Finer resolution, quarter-rpm.)*
3. What is the max rpm a 16-bit signal with factor 0.25 can show? *(65535 × 0.25 = 16383.75.)*

### Little-endian (Intel) in one picture
EngineSpeed raw = 0x**65**90 → sent **low byte first**: byte 0 = `90`, byte 1 = `65`.
So the frame starts `90 65 …`. Motorola would send `65 90`.

**Add these to your flashcards today:** physical formula · lowest ID wins · 60 Ω termination check · @1 = Intel little-endian · 111 bits per 8-byte frame.

---

## THURSDAY: Decode CAN data with Python (1.5 h)

### Step 1: run it
```
cd D:\GERMAN\motorsport-calibration-lab\week01
..\.venv\Scripts\activate
python step1_decode.py
```

### Step 2: what you should see
```
Message ENGINE_DATA_1  ID=256 (0x100)  length=8 bytes
   EngineSpeed  start= 0 len=16 factor=0.25 offset=0 unit=rpm
   ...
Physical values : {'EngineSpeed': 6500, 'ThrottlePos': 80, 'CoolantTemp': 92, 'MAP': 185.5}
Raw bytes (hex) : 90 65 C8 84 3F 07 00 00
Decoded again   : {'EngineSpeed': 6500.0, 'ThrottlePos': 80.0, 'CoolantTemp': 92, 'MAP': 185.5}
```
**Compare with your paper results from Wednesday:** `90 65` = EngineSpeed, `C8` = Throttle, `84` = Coolant, `3F 07` = MAP. They should match exactly.

### Step 3: what each part of the script does

| Line(s) | What it does |
|---|---|
| `cantools.database.load_file("engine.dbc")` | Reads the dictionary |
| `for msg in db.messages:` | Lists every message and signal, the same as a tool's "signal browser" |
| `msg.encode(values)` | Physical values → raw bytes (what the **ECU** does before sending) |
| `msg.decode(raw)` | Raw bytes → physical values (what the **logger/dash** does on receiving) |

### Step 4: your own exercises (do all 4)
1. Change `EngineSpeed` to **8250** and predict the first two bytes **before** running. *(8250 / 0.25 = 33000 = 0x80E8 → `E8 80`)*
2. Set `CoolantTemp` to **300** and run. You get an error. **Why?** *(Outside the DBC range −40…215. Good: the tool protects you from impossible values.)*
3. In `engine.dbc`, **add a signal** `OilPressure` to ENGINE_DATA_2: start bit 16, 8 bits, factor 0.05, offset 0, range 0–12.75, unit "bar". Then encode 4.5 bar. *(Raw should be 90 = 0x5A.)*
4. Change `@1` to `@0` (Motorola) for EngineSpeed and look how the bytes change. **Then change it back.**

---

## FRIDAY: First real F1 data (1 h)

```
python fastf1_speed_trace.py
```
- The first run downloads data (a few minutes), and later runs are fast (cached).
- You get 3 plots over distance: **speed, throttle, gear** for the pole lap at Monza 2024.

**Look at the plot and write 3 sentences:**
1. Where are the 3 slowest points? *(The chicanes and Parabolica.)*
2. What is the top speed, and where?
3. How long is the driver at 100 % throttle? Why is Monza "low downforce"?

**Change it:** try `session = fastf1.get_session(2024, "Monaco", "Q")` and compare. What changes in the gear plot?

---

## SATURDAY: Your own virtual CAN bus (3 h)

### Step 1: run it (15 min)
```
python step2_virtual_bus.py
```
You should see:
```
Logged 300 EngineSpeed values to engine_log.asc
Saved rpm_plot.png
```
Open **`rpm_plot.png`** (a sine-shaped rpm trace) and **`engine_log.asc`** in Notepad.

### Step 2: understand what happened (45 min)

| Part of script | Real race car equivalent |
|---|---|
| `ecu = can.Bus(interface="virtual", ...)` | The engine ECU connected to the bus |
| `logger = can.Bus(interface="virtual", ...)` | The datalogger on the same bus |
| `ecu.send(...)` every 10 ms | ECU broadcasting ENGINE_DATA_1 at **100 Hz** |
| `if step % 10 == 0:` | ENGINE_DATA_2 (lambda) only at **10 Hz**, since slow signals need less bandwidth |
| `logger.recv(...)` | Logger receiving every frame |
| `can.ASCWriter("engine_log.asc")` | Logger writing a **Vector ASC log**. CANoe/CANalyzer can open this format |
| `db.decode_message(...)` | Turning bytes into physical values for the plot |

### How to read one line of `engine_log.asc`
```
 0.027094 1  100             Rx   d 8 F2 40 84 82 12 04 00 00
```

| Part | Meaning |
|---|---|
| `0.027094` | Time in seconds |
| `1` | CAN channel 1 |
| `100` | ID in hex (0x100 = ENGINE_DATA_1) |
| `Rx` | Received |
| `d 8` | Data frame, 8 bytes |
| `F2 40 …` | The data bytes |

**Decode it by hand:** `F2 40` → 0x40F2 = 16626 × 0.25 = **4156.5 rpm**.

### Step 3: bus-load calculation (30 min, on paper)
Bus speed 500 kbit/s. One 8-byte frame ≈ 111 bits.

| Message | Rate | Bits per second |
|---|---|---|
| ENGINE_DATA_1 | 100 Hz | 100 × 111 = 11,100 |
| ENGINE_DATA_2 | 10 Hz | 10 × 111 = 1,110 |
| **Total** | | **12,210 bit/s** |

**Bus load = 12,210 ÷ 500,000 = 2.4 %.** Real cars try to stay **below ~50–60 %**.
**Exercise:** a real rally car sends 40 messages at 100 Hz. What is the bus load at 500 kbit/s, and at 1 Mbit/s? *(≈ 89 % → too high. ≈ 44 % → OK. This is why race cars use 1 Mbit/s or several buses.)*

### Step 4: make it yours (1.5 h)
1. Add your `OilPressure` signal from Thursday to the sender and plot it as well.
2. Add a **third node**, `dash = can.Bus(...)`, that prints a warning when CoolantTemp > 110 °C. Make the sender raise the temperature slowly to test it.
3. Change ENGINE_DATA_2 to 50 Hz and recalculate the bus load.

*(Note: Windows sleep timing is coarse, so the real loop runs a bit slower than 100 Hz. That's normal on a PC and irrelevant on a real ECU.)*

---

## SUNDAY: Write-up (1 h)

1. Write `week01/README.md` with: what CAN and DBC are (5 lines), the decoded-frame example, your rpm plot, the bus-load table.
2. `git add . && git commit -m "Week 1: CAN frames, DBC, virtual bus logger" && git push`
3. Review all flashcards.
4. Learning log, one line: *learned / broke / next*.

---

## Done checklist for Week 1

| Can I… | ✓ |
|---|---|
| Explain arbitration, termination (60 Ω), bit stuffing and bus-off in my own words? | [ ] |
| Read any `SG_` line in a DBC and say what every part means? | [ ] |
| Convert physical ↔ raw ↔ hex by hand (including offset and little-endian)? | [ ] |
| Run and explain `step1_decode.py` and `step2_virtual_bus.py` line by line? | [ ] |
| Read a line of an ASC log and decode it by hand? | [ ] |
| Calculate bus load? | [ ] |
| Show it all on GitHub? | [ ] |

**If something doesn't work:** copy the full error message and send it to me. I'll explain what went wrong.

## Interview line you can now say truthfully
*"I've built a DBC for an engine message set, encoded and decoded frames with cantools, simulated a multi-node CAN bus with python-can, and logged it in Vector ASC format, including bus-load budgeting."*
