import json
import random
import re
from collections import defaultdict

# 1. Load the official contract Gold Skeleton palette
with open('contract_gold_bones_palette.json', 'r') as f:
    contract_palette = json.load(f)

print(f"Loaded {len(contract_palette)} official contract gold skeleton colors.")
contract_palette_set = set(contract_palette)

# 2. Read existing demo svg.svg to get lines 1..396 (the upper part)
with open('demo svg.svg', 'r', encoding='utf-8') as f:
    all_lines = f.readlines()

upper_part_lines = all_lines[:396]
print(f"Upper part has {len(upper_part_lines)} lines.")
print("Line 1:", upper_part_lines[0].strip())
print("Line 2 (Background):", upper_part_lines[1].strip())
print("Line 396:", upper_part_lines[395].strip())

# 3. Build the 28x28 grid for the recently changed #FFFFFF space (gx in 14..41, gy in 28..55)
# Use random seed for reproducible beautiful organic distribution
rng = random.Random(42)

# Weight distribution based on authentic Argonauts Gold Skeleton:
# highlights (5%), mid-gold/bright gold (25%), warm amber (35%), deep shadow (25%), dark cavity/contour (10%)
# Let's shuffle and cycle through all 160 contract colors with randomized permutations so all 160 colors get used naturally without repetition patterns!

shuffled_colors = []
while len(shuffled_colors) < 28 * 28 + 200:
    temp = list(contract_palette)
    rng.shuffle(temp)
    shuffled_colors.extend(temp)

# Create 28x28 non-overlapping paths
lower_pixel_paths = []
color_idx = 0

for gy in range(28, 56): # rows 28 to 55
    for gx in range(14, 42): # cols 14 to 41
        c = shuffled_colors[color_idx]
        color_idx += 1
        
        # Verify color is strictly in contract palette
        assert c in contract_palette_set, f"Color {c} not in contract palette!"
        
        x = gx * 10
        y = gy * 10
        path_d = f"M{x+10} {y}H{x}V{y+10}H{x+10}V{y}Z"
        lower_pixel_paths.append(f'<path d="{path_d}" fill="{c}"/>\n')

print(f"Generated {len(lower_pixel_paths)} non-overlapping lower pixel paths.")

# 4. Assemble the complete new SVG
new_svg_lines = upper_part_lines + lower_pixel_paths + ['</svg>\n']

output_svg = ''.join(new_svg_lines)

# 5. Verify the complete SVG:
# - No overlapping pixels in lower part
# - All lower part colors are in contract palette
# - Total unique colors used
# - Upper part unchanged
parsed_paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"', output_svg)
print(f"Total paths in new SVG: {len(parsed_paths)}")

lower_cells = defaultdict(list)
for d, fill in parsed_paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    m = re.match(r'M(\d+)\s+(\d+)H(\d+)V(\d+)H(\d+)V(\d+)Z', d)
    if m:
        x1, y1, x2, y2, x3, y3 = map(int, m.groups())
        gx = min(x1, x2) // 10
        gy = min(y1, y2) // 10
        if gy >= 28:
            lower_cells[(gx, gy)].append(fill)

print(f"Total lower unique cells: {len(lower_cells)}")
overlaps_lower = [k for k, v in lower_cells.items() if len(v) > 1]
print(f"Overlapping cells in lower part: {len(overlaps_lower)}")
assert len(overlaps_lower) == 0, "Error: Overlaps found in lower part!"
assert len(lower_cells) == 28 * 28, f"Expected 784 cells, got {len(lower_cells)}"

# Check colors in lower part
all_lower_fills = [v[0] for v in lower_cells.values()]
invalid_colors = [c for c in all_lower_fills if c not in contract_palette_set]
print(f"Invalid colors in lower part: {len(invalid_colors)}")
assert len(invalid_colors) == 0, "Error: Invalid colors found!"

print(f"Unique colors used in lower part: {len(set(all_lower_fills))} out of {len(contract_palette_set)}")
from collections import Counter
counts = Counter(all_lower_fills)
print("Max occurrences of any single color in lower part:", max(counts.values()))
print("Min occurrences of any single color in lower part:", min(counts.values()))
