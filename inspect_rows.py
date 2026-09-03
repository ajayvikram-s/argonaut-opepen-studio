import re

with open('demo svg.svg', 'r', encoding='utf-8') as f:
    content = f.read()

raw_paths = re.findall(r'<path\s+([^>]+)/>', content)

cells = {}
bg_fill = "#0D0B16"

for p in raw_paths:
    d_m = re.search(r'd="([^"]+)"', p)
    fill_m = re.search(r'fill="([^"]+)"', p)
    if not d_m or not fill_m:
        continue
    d = d_m.group(1)
    fill = fill_m.group(1)
    
    if "560" in d:
        bg_fill = fill
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

print(f"Background Fill: {bg_fill}")
print(f"Total Character Cells: {len(cells)}")

# Check every row where cells exist
y_list = sorted(list(set(y for x, y in cells.keys())))
for y in y_list:
    row_cells = [(x, cells[(x, y)]) for x in range(56) if (x, y) in cells]
    print(f"Row y={y:02d} (count={len(row_cells)}): min_x={min(x for x, c in row_cells)}, max_x={max(x for x, c in row_cells)}")
    for x, c in row_cells:
        if c.lower() in ['white', '#ffffff', '#fff']:
            print(f"   --> WHITE PIXEL at ({x}, {y})")
