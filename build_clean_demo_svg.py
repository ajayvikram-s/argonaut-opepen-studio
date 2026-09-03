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
        # Each cell is 3 characters: " xx" or " . "
        col_count = len(row_str) // 3
        for col_idx in range(col_count):
            token = row_str[col_idx*3 : col_idx*3 + 3].strip()
            gx_val = 12 + col_idx
            if token != '.':
                orig_cells_map[(gx_val, y_val)] = token

print(f"Extracted original cells count: {len(orig_cells_map)}")

with open('demo_svg_filled.svg', 'r', encoding='utf-8') as f:
    filled_content = f.read()

# Build clean SVG with only original paths, and white replaced with gold skeleton palette
svg_lines = [
    '<svg width="560" height="560" viewBox="0 0 560 560" fill="none" xmlns="http://www.w3.org/2000/svg">',
    '<path d="M560 0H0V560H560V0Z" fill="#0D0B16"/>'
]

replaced_white_count = 0
for (gx, gy) in sorted(orig_cells_map.keys(), key=lambda pt: (pt[1], pt[0])):
    x1 = gx * 10
    y1 = gy * 10
    path_d = f"M{x1+10} {y1}H{x1}V{y1+10}H{x1+10}V{y1}Z"
    
    # Check matching path in filled_content
    match = re.search(r'<path id="px_' + str(gx) + r'_' + str(gy) + r'" d="[^"]+" fill="([^"]+)"/>', filled_content)
    fill = match.group(1) if match else "#DCC67E"
    
    # White replacements with Gold Skeleton palette colors
    if (gx, gy) == (33, 18):
        fill = "#8A7439" # Gold shadow / socket tone
        replaced_white_count += 1
    elif (gx, gy) == (18, 22):
        fill = "#DCC67E" # Primary Gold bone highlight tone
        replaced_white_count += 1
        
    svg_lines.append(f'<path d="{path_d}" fill="{fill}"/>')

svg_lines.append('</svg>')

clean_svg = '\n'.join(svg_lines)

with open('demo svg.svg', 'w', encoding='utf-8') as f:
    f.write(clean_svg)

print(f"SUCCESS: Wrote demo svg.svg with {len(orig_cells_map)} character paths + background. Replaced {replaced_white_count} white pixels.")
