# Decode one line of engine_log.asc step by step, exactly like on paper.

line = "ED 03 5A 00 00 00 00 00"        # <- paste the 8 bytes from YOUR log here

# STEP 1: split the line into 8 boxes and number them 0..7
boxes = line.split()                   # ['F2', '40', '84', ...]
for i, b in enumerate(boxes):
    print(f"byte {i} = {b}")
print()

# STEP 2: which boxes belong to which signal? (copied from engine.dbc)
#            name          start  length  factor  offset
signals = [("Lambda",       0,    16,     0.001,   0),
           ("OilPressure", 16,     8,     0.05,    0)]

for name, start, length, factor, offset in signals:
    first = start // 8                 # first box = start bit / 8
    count = length // 8                # how many boxes = length / 8
    mine = boxes[first:first + count]  # take those boxes
    print(f"{name}: start bit {start} -> box {first}, {count} box(es) -> {mine}")

    # STEP 3: Intel (@1) = first box is the LOW byte, so turn them round
    mine_high_first = list(reversed(mine))
    hex_number = "".join(mine_high_first)

    # STEP 4: hex -> decimal
    raw = int(hex_number, 16)

    # STEP 5: physical = raw * factor + offset
    physical = raw * factor + offset
    print(f"   high byte first: 0x{hex_number} = {raw}  ->  {raw} x {factor} + {offset} = {physical}")
    print()
