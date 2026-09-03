import json
import random
import re
import xml.etree.ElementTree as ET

# 1. Load official contract Gold Skeleton palette
with open('contract_gold_bones_palette.json', 'r') as f:
    contract_palette = json.load(f)

contract_palette_set = set(contract_palette)

# 2. Load upper part lines (1..396) from demo svg.svg
with open('demo svg.svg', 'r', encoding='utf-8') as f:
    all_lines = f.readlines()

upper_part_lines = all_lines[:396]

# 3. Generate 784 non-overlapping pixels for gx in 14..41, gy in 28..55
rng = random.Random(1337) # High quality organic distribution seed

shuffled_colors = []
while len(shuffled_colors) < 28 * 28 + 200:
    temp = list(contract_palette)
    rng.shuffle(temp)
    shuffled_colors.extend(temp)

lower_pixel_paths = []
color_idx = 0

for gy in range(28, 56):
    for gx in range(14, 42):
        c = shuffled_colors[color_idx]
        color_idx += 1
        x = gx * 10
        y = gy * 10
        path_d = f"M{x+10} {y}H{x}V{y+10}H{x+10}V{y}Z"
        lower_pixel_paths.append(f'<path d="{path_d}" fill="{c}"/>\n')

# 4. Assemble the complete clean SVG
new_svg_content = ''.join(upper_part_lines + lower_pixel_paths + ['</svg>\n'])

# Write to demo svg.svg
with open('demo svg.svg', 'w', encoding='utf-8') as f:
    f.write(new_svg_content)

# Also write to Group 12607.svg so both stay in sync
with open('Group 12607.svg', 'w', encoding='utf-8') as f:
    f.write(new_svg_content)

print("SUCCESS: Updated demo svg.svg and Group 12607.svg!")

# 5. Comprehensive validation:
# Valid XML check
tree = ET.fromstring(new_svg_content)
print(f"XML root tag: {tree.tag}, child count: {len(tree)}")

# Overlap check across the entire lower part
paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"', new_svg_content)
print(f"Total path elements: {len(paths)}")

lower_cells = {}
lower_overlap_count = 0
for d, fill in paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    m = re.match(r'M(\d+)\s+(\d+)H(\d+)V(\d+)H(\d+)V(\d+)Z', d)
    if m:
        x1, y1, x2, y2, x3, y3 = map(int, m.groups())
        gx = min(x1, x2) // 10
        gy = min(y1, y2) // 10
        if gy >= 28:
            if (gx, gy) in lower_cells:
                lower_overlap_count += 1
            lower_cells[(gx, gy)] = fill

print(f"Total lower part cells: {len(lower_cells)} / 784")
print(f"Total lower part overlapping pixels: {lower_overlap_count}")
print(f"All 160 contract colors used: {len(set(lower_cells.values())) == 160}")
print(f"Any non-contract color used: {any(c not in contract_palette_set for c in lower_cells.values())}")
