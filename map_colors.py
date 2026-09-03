import re

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

print("--- DETAILED COLOR MAP AROUND CHARACTER ---")
for y in range(12, 44):
    row_chars = []
    for x in range(12, 44):
        if (x, y) in cells:
            c = cells[(x, y)].upper()
            if c in ['WHITE', '#FFFFFF']:
                row_chars.append(" W ")
            elif c in ['BLACK', '#000000']:
                row_chars.append(" B ")
            else:
                # show first 2 chars of hex or indicator
                row_chars.append(f"{c[1:3]} ")
        else:
            row_chars.append(" . ")
    print(f"y={y:02d} |" + "".join(row_chars))
