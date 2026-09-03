import re

with open('demo svg.svg', 'r', encoding='utf-8') as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)
print(f'Total paths found: {len(paths)}')

# Check non-multiple of 10 coordinates
non_grid_paths = []
for d, fill, op in paths:
    coords = list(map(int, re.findall(r'\d+', d)))
    if any(c % 10 != 0 for c in coords):
        non_grid_paths.append((d, fill, op, coords))

print(f'Non-multiple of 10 paths count: {len(non_grid_paths)}')
for d, fill, op, coords in non_grid_paths:
    print(f'  d="{d}" fill="{fill}" coords={coords}')
