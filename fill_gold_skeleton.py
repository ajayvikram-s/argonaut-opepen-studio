import re
import json

with open('demo svg.svg', 'r', encoding='utf-8') as f:
    content = f.read()

raw_paths = re.findall(r'<path\s+([^>]+)/>', content)
cells = {}

for p in raw_paths:
    d_m = re.search(r'd="([^"]+)"', p)
    fill_m = re.search(r'fill="([^"]+)"', p)
    if not d_m or not fill_m:
        continue
    d = d_m.group(1)
    fill = fill_m.group(1)
    if "560" in d:
        continue
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
    min_x, min_y = min(path_xs), min(path_ys)
    gx = min_x // 10
    gy = min_y // 10
    cells[(gx, gy)] = fill

BG_COLOR = "#0D0B16"

# 1. Replace white pixels with gold skeleton colors
# (33, 18) -> surrounded by #362508, #080502, #372C14, #615025 -> Gold Bone highlight #C3AC6B or #8A7439
# (18, 22) -> surrounded by #574217, #B5B8BE, #59451D -> Gold Bone highlight #DCC67E
if (33, 18) in cells:
    cells[(33, 18)] = "#8A7439"
if (18, 22) in cells:
    cells[(18, 22)] = "#DCC67E"

# 2. Bridge the neck connection at rows 28 and 29 with gold vertebrae / spine
# Left skull chin is at x in [17..23], right skull chin is at x in [26..33]
# Neck column 1 (left spine): x in [19, 20, 21, 22]
# Neck column 2 (right spine): x in [28, 29, 30, 31]
spine_colors_28 = {
    18: "#3F3223", 19: "#574217", 20: "#6F5829", 21: "#5C4111", 22: "#3A2A0B",
    27: "#3F3223", 28: "#574217", 29: "#6F5829", 30: "#5C4111", 31: "#3A2A0B"
}
spine_colors_29 = {
    18: "#3A2A0B", 19: "#6F5829", 20: "#8E7539", 21: "#6F5829", 22: "#261E0D",
    27: "#3A2A0B", 28: "#6F5829", 29: "#8E7539", 30: "#6F5829", 31: "#261E0D"
}

for x, c in spine_colors_28.items():
    cells[(x, 28)] = c
for x, c in spine_colors_29.items():
    cells[(x, 29)] = c

# 3. Fill the intercostal / ribcage and skeleton hollow spaces in rows 33 to 41
# In row 33 to 41, fill internal bone spaces between ribs with deep bone shadow / marrow tones
# For rows 33..41, for each row, find leftmost and rightmost character pixel, fill the gaps with skeleton cavity/marrow colors
for y in range(30, 42):
    row_xs = [x for x, cy in cells.keys() if cy == y]
    if not row_xs:
        continue
    min_x, max_x = min(row_xs), max(row_xs)
    for x in range(min_x, max_x + 1):
        if (x, y) not in cells:
            # Check surrounding pixels
            # Fill with gold bone marrow / deep skeletal shadow
            if x % 2 == 0:
                cells[(x, y)] = "#3A2A0B"
            else:
                cells[(x, y)] = "#261E0D"

# Also bridge gap between left and right head in rows 16 to 27 where skulls touch
for y in range(16, 27):
    # If gap between x=22 and x=28
    for x in range(22, 28):
        if (x, y) not in cells:
            # Fill seam with dark gold shadow bone
            cells[(x, y)] = "#362A12" if (x + y) % 2 == 0 else "#2B2310"

# 4. Now construct complete 56x56 grid (all 3,136 cells)
full_grid = {}
for gy in range(56):
    for gx in range(56):
        if (gx, gy) in cells:
            full_grid[(gx, gy)] = cells[(gx, gy)]
        else:
            full_grid[(gx, gy)] = BG_COLOR

# 5. Generate pristine Figma-ready SVG (viewBox 0 0 560 560)
svg_lines = [
    '<svg width="560" height="560" viewBox="0 0 560 560" fill="none" xmlns="http://www.w3.org/2000/svg">',
    '  <!-- Base Canvas Layer: 56x56 cells (no white space) -->',
    '  <g id="Background_Canvas">',
    '    <rect width="560" height="560" fill="#0D0B16"/>',
    '  </g>',
    '  <!-- Character & Skeleton Layer with Gold Bone Palette -->',
    '  <g id="Gold_Skeleton_Character">'
]

for gy in range(56):
    for gx in range(56):
        c = full_grid[(gx, gy)]
        if c != BG_COLOR:
            x1 = gx * 10
            y1 = gy * 10
            # Standard Figma path format: M(x+10) (y)H(x)V(y+10)H(x+10)V(y)Z
            path_d = f"M{x1+10} {y1}H{x1}V{y1+10}H{x1+10}V{y1}Z"
            svg_lines.append(f'    <path id="px_{gx}_{gy}" d="{path_d}" fill="{c}"/>')

svg_lines.append('  </g>')
svg_lines.append('</svg>')

svg_str = "\n".join(svg_lines)

# Overwrite demo svg.svg and create demo_svg_filled.svg
with open('demo svg.svg', 'w', encoding='utf-8') as f:
    f.write(svg_str)

with open('demo_svg_filled.svg', 'w', encoding='utf-8') as f:
    f.write(svg_str)

# Save pixel data
char_px_count = sum(1 for c in full_grid.values() if c != BG_COLOR)
print(f"Successfully updated demo svg.svg! Total Character Pixels: {char_px_count}, Total Canvas Pixels: {len(full_grid)}")
