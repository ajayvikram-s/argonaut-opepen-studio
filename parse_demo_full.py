import re

with open('demo svg.svg', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's parse all path elements properly
# Find all <path ... />
raw_paths = re.findall(r'<path\s+([^>]+)/>', content)
print(f"Total raw paths: {len(raw_paths)}")

all_cells = {}
background_paths = []

for idx, p in enumerate(raw_paths):
    d_m = re.search(r'd="([^"]+)"', p)
    fill_m = re.search(r'fill="([^"]+)"', p)
    if not d_m or not fill_m:
        continue
    d = d_m.group(1)
    fill = fill_m.group(1)
    
    # Extract all numbers from d
    nums = [int(n) for n in re.findall(r'\d+', d)]
    if len(nums) == 4 and d == "M560 0H0V560H560V0Z":
        background_paths.append((d, fill))
        continue
    
    # For a 10x10 rect path, let's find min/max x and y
    # The coords in path: e.g. M320 140H310V150... or M190 140V150H200...
    xs = nums[0::2] if len(nums) >= 4 else []
    # Actually nums contains alternating x,y or single dimensions
    # Let's parse tokens in d:
    tokens = re.findall(r'([MmVvHhZz]|\d+)', d)
    curr_x, curr_y = 0, 0
    path_xs, path_ys = [], []
    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        if cmd == 'M':
            curr_x = int(tokens[i+1])
            curr_y = int(tokens[i+2])
            path_xs.append(curr_x)
            path_ys.append(curr_y)
            i += 3
        elif cmd == 'H':
            curr_x = int(tokens[i+1])
            path_xs.append(curr_x)
            i += 2
        elif cmd == 'V':
            curr_y = int(tokens[i+1])
            path_ys.append(curr_y)
            i += 2
        elif cmd in ['Z', 'z']:
            i += 1
        else:
            i += 1
            
    min_x, max_x = min(path_xs), max(path_xs)
    min_y, max_y = min(path_ys), max(path_ys)
    gx = min_x // 10
    gy = min_y // 10
    all_cells[(gx, gy)] = fill

print(f"Total cells parsed: {len(all_cells)}")
print("Background paths:", background_paths)

# Check all fills
white_cells = []
for (gx, gy), fill in all_cells.items():
    if fill.lower() in ['white', '#ffffff', '#fff']:
        white_cells.append((gx, gy, fill))

print("White cells found in cells:", white_cells)

# Also check non-background empty spaces or gaps in the 56x56 grid
# What is the full canvas dimension? viewBox="0 0 560 560" -> 56x56 grid!
print(f"Total possible cells on 56x56: {56*56} = 3136")
print(f"Occupied cells: {len(all_cells)}")

# Print character min/max
min_gx = min(x for x, y in all_cells.keys())
max_gx = max(x for x, y in all_cells.keys())
min_gy = min(y for x, y in all_cells.keys())
max_gy = max(y for x, y in all_cells.keys())
print(f"Character bounding box: X=[{min_gx}..{max_gx}], Y=[{min_gy}..{max_gy}]")

# Let's see the character grid in detail
print("\nCharacter Visual Map (with gaps):")
for y in range(min_gy, max_gy + 1):
    row_str = f"y={y:02d}: "
    for x in range(min_gx, max_gx + 1):
        if (x, y) in all_cells:
            f = all_cells[(x, y)]
            if f.lower() in ['white', '#ffffff']:
                row_str += "W"
            else:
                row_str += "#"
        else:
            row_str += " "
    print(row_str)
