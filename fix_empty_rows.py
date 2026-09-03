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

# 3. Generate non-overlapping pixels ONLY for the non-empty rows:
# Rows 43-49 (inclusive: gy in [43, 44, 45, 46, 47, 48, 49]) MUST BE EMPTY!
# Rows to fill: gy in range(28, 43) [i.e. rows 28..42] and gy in range(50, 56) [i.e. rows 50..55]
# cols: gx in range(14, 42) [i.e. cols 14..41]

rng = random.Random(1337)

shuffled_colors = []
while len(shuffled_colors) < 28 * 28 + 200:
    temp = list(contract_palette)
    rng.shuffle(temp)
    shuffled_colors.extend(temp)

lower_pixel_paths = []
color_idx = 0

filled_gy_list = list(range(28, 43)) + list(range(50, 56))
print(f"Filled row indices ({len(filled_gy_list)} rows): {filled_gy_list}")
empty_gy_list = list(range(43, 50))
print(f"Empty row indices (rows 43-49, {len(empty_gy_list)} rows): {empty_gy_list}")

for gy in filled_gy_list:
    for gx in range(14, 42):
        c = shuffled_colors[color_idx]
        color_idx += 1
        x = gx * 10
        y = gy * 10
        path_d = f"M{x+10} {y}H{x}V{y+10}H{x+10}V{y}Z"
        lower_pixel_paths.append(f'<path d="{path_d}" fill="{c}"/>\n')

print(f"Generated {len(lower_pixel_paths)} lower pixel paths.")

# 4. Assemble clean SVG
new_svg_content = ''.join(upper_part_lines + lower_pixel_paths + ['</svg>\n'])

# Write to demo svg.svg and Group 12607.svg
with open('demo svg.svg', 'w', encoding='utf-8') as f:
    f.write(new_svg_content)

with open('Group 12607.svg', 'w', encoding='utf-8') as f:
    f.write(new_svg_content)

print("SUCCESS: Updated demo svg.svg and Group 12607.svg!")

# 5. Validation:
tree = ET.fromstring(new_svg_content)
print(f"XML root tag: {tree.tag}, total child elements: {len(tree)}")

# Verify rows 43-49 are 100% empty
paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"', new_svg_content)
row_pixel_counts = {}
for d, fill in paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    m = re.match(r'M(\d+)\s+(\d+)H(\d+)V(\d+)H(\d+)V(\d+)Z', d)
    if m:
        x1, y1, x2, y2, x3, y3 = map(int, m.groups())
        gx = min(x1, x2) // 10
        gy = min(y1, y2) // 10
        row_pixel_counts[gy] = row_pixel_counts.get(gy, 0) + 1

print("\nRow pixel counts around rows 40-55:")
for gy in range(40, 56):
    print(f"  Row gy={gy:02d} (y={gy*10:03d}..{gy*10+10:03d}): {row_pixel_counts.get(gy, 0)} pixels")

for gy in range(43, 50):
    assert row_pixel_counts.get(gy, 0) == 0, f"Error: Row {gy} is not empty!"

print("\nValidation PASSED: Rows 43-49 are completely empty, no overlapping pixels, all colors in contract palette!")
