import re
from collections import defaultdict

with open('demo svg.svg', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
print(f'Total lines in demo svg.svg: {len(lines)}')

# Parse all paths and rects
paths = []
for idx, line in enumerate(lines):
    pm = re.search(r'<path\s+([^>]+)/>', line)
    if pm:
        dm = re.search(r'd="([^"]+)"', line)
        fm = re.search(r'fill="([^"]+)"', line)
        if dm and fm:
            paths.append(('path', idx, line, dm.group(1), fm.group(1)))

print(f'Total parsed elements: {len(paths)}')

cell_elements = defaultdict(list)
for item in paths:
    _, idx, line, d, fill = item
    if d == 'M560 0H0V560H560V0Z':
        continue
    m = re.match(r'M(\d+)\s+(\d+)H(\d+)V(\d+)H(\d+)V(\d+)Z', d)
    if m:
        x1, y1, x2, y2, x3, y3 = map(int, m.groups())
        gx = min(x1, x2) // 10
        gy = min(y1, y2) // 10
        cell_elements[(gx, gy)].append((idx, line, fill))
    else:
        m2 = re.findall(r'\d+', d)
        if len(m2) >= 2:
            xs = [int(m2[k]) for k in range(0, len(m2), 2)]
            ys = [int(m2[k]) for k in range(1, len(m2), 2)]
            gx = min(xs) // 10
            gy = min(ys) // 10
            cell_elements[(gx, gy)].append((idx, line, fill))

overlapping = {k: v for k, v in cell_elements.items() if len(v) > 1}
print(f'Total occupied unique grid cells: {len(cell_elements)}')
print(f'Total cells with multiple elements (overlapping): {len(overlapping)}')
print(f'Total paths in overlapping cells: {sum(len(v) for v in overlapping.values())}')

print('\nSample overlapping cells:')
for (gx, gy), elist in sorted(overlapping.items())[:25]:
    print(f'Cell ({gx:02d}, {gy:02d}) [lines {[e[0] for e in elist]}]: {[e[2] for e in elist]}')
