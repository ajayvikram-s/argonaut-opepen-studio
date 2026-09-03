import re
import json

log_path = r"C:\Users\avsin\.gemini\antigravity-ide\brain\6e2e0c2a-e2ed-43fc-852a-9e642ba2725d\.system_generated\logs\transcript_full.jsonl"

color_map_text = ""
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('step_index') == 61:
            color_map_text = obj.get('content', '')
            break

orig_cells_map = {}
for out_line in color_map_text.split('\n'):
    m = re.match(r'y=(\d+)\s*\|(.*)', out_line)
    if m:
        y_val = int(m.group(1))
        row_str = m.group(2)
        col_count = len(row_str) // 3
        for col_idx in range(col_count):
            token = row_str[col_idx*3 : col_idx*3 + 3].strip()
            gx_val = 12 + col_idx
            if token != '.':
                orig_cells_map[(gx_val, y_val)] = token

# Argonauts Gold Skeleton palette shades
GOLD_PALETTE = [
    "#F7EEC2", # Bright Gold
    "#F3E7B4", # Soft Gold highlight
    "#DCC67E", # Primary Gold bone
    "#C6AE6E", # Warm Gold
    "#C3AC6B", # Golden bone
    "#C3A759", # Deep Gold
    "#AC924C", # Amber Gold
    "#9C844F", # Mid Gold
    "#8E7539", # Classic Gold
    "#8A7439", # Shaded Gold
    "#6F5829", # Contour Gold
    "#574217", # Shadow Gold
    "#3A2A0B", # Deep cavity Gold
]

# Start with user's original cells
final_cells = {}
with open('demo_svg_filled.svg', 'r', encoding='utf-8') as f:
    filled_content = f.read()

for (gx, gy) in orig_cells_map.keys():
    match = re.search(r'<path id="px_' + str(gx) + r'_' + str(gy) + r'" d="[^"]+" fill="([^"]+)"/>', filled_content)
    c = match.group(1) if match else "#DCC67E"
    if (gx, gy) == (33, 18):
        c = "#8A7439"
    elif (gx, gy) == (18, 22):
        c = "#DCC67E"
    final_cells[(gx, gy)] = c

# Now let's fill the empty/white spaces within the character envelope with Gold Skeleton palette colors!
# 1. Fill rows 28 and 29 (neck & spine connection between skulls and body)
spine_28 = {
    17: "#574217", 18: "#6F5829", 19: "#8E7539", 20: "#DCC67E", 21: "#8E7539", 22: "#6F5829", 23: "#574217",
    27: "#574217", 28: "#6F5829", 29: "#8E7539", 30: "#DCC67E", 31: "#8E7539", 32: "#6F5829", 33: "#574217"
}
spine_29 = {
    17: "#3A2A0B", 18: "#574217", 19: "#6F5829", 20: "#C3AC6B", 21: "#6F5829", 22: "#574217", 23: "#3A2A0B",
    27: "#3A2A0B", 28: "#574217", 29: "#6F5829", 30: "#C3AC6B", 31: "#6F5829", 32: "#574217", 33: "#3A2A0B"
}
for x, c in spine_28.items():
    final_cells[(x, 28)] = c
for x, c in spine_29.items():
    final_cells[(x, 29)] = c

# 2. Fill the internal empty spaces inside the ribcage / torso (rows 30..41)
for y in range(30, 42):
    row_xs = [x for (x, cy) in final_cells.keys() if cy == y]
    if not row_xs:
        continue
    min_x, max_x = min(row_xs), max(row_xs)
    for x in range(min_x, max_x + 1):
        if (x, y) not in final_cells:
            # Alternating authentic gold bone shades across the ribcage
            gold_color = GOLD_PALETTE[(x * 3 + y * 7) % len(GOLD_PALETTE)]
            final_cells[(x, y)] = gold_color

# 3. Fill the gap between the two skulls in rows 15..27
for y in range(15, 28):
    for x in range(21, 29):
        if (x, y) not in final_cells:
            gold_color = GOLD_PALETTE[(x * 2 + y * 5) % (len(GOLD_PALETTE) - 2) + 2]
            final_cells[(x, y)] = gold_color

# Construct SVG with explicit Gold Skeleton Pixel paths and transparent or toggleable background layer
svg_lines = [
    '<svg width="560" height="560" viewBox="0 0 560 560" fill="none" xmlns="http://www.w3.org/2000/svg">',
    '  <!-- Background Canvas Layer -->',
    '  <g id="Background_Canvas">',
    '    <rect width="560" height="560" fill="#0D0B16"/>',
    '  </g>',
    '  <!-- Gold Skeleton Artwork & Infill Pixels -->',
    '  <g id="Gold_Skeleton_Pixels">'
]

for (gx, gy) in sorted(final_cells.keys(), key=lambda pt: (pt[1], pt[0])):
    x1 = gx * 10
    y1 = gy * 10
    path_d = f"M{x1+10} {y1}H{x1}V{y1+10}H{x1+10}V{y1}Z"
    c = final_cells[(gx, gy)]
    svg_lines.append(f'    <path id="px_{gx}_{gy}" d="{path_d}" fill="{c}"/>')

svg_lines.append('  </g>')
svg_lines.append('</svg>')

svg_str = '\n'.join(svg_lines)

with open('demo svg.svg', 'w', encoding='utf-8') as f:
    f.write(svg_str)

print(f"Updated demo svg.svg with {len(final_cells)} golden/character pixel cells!")
