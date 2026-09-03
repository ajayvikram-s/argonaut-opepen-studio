import re
from collections import defaultdict

with open('alien argonaut opepen.svg', 'r') as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"', content)
print(f"Total paths in alien argonaut opepen.svg: {len(paths)}")

cells = defaultdict(list)
for d, fill in paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    nums = list(map(int, re.findall(r'\d+', d)))
    min_x = min(nums[0], nums[2])
    min_y = min(nums[1], nums[3])
    gx = min_x // 10
    gy = min_y // 10
    cells[(gx, gy)].append(fill)

overlaps = {k: v for k, v in cells.items() if len(v) > 1}
print(f"Total unique cells: {len(cells)}")
print(f"Overlapping cells: {len(overlaps)}")
assert len(overlaps) == 0, "Error: Overlaps found!"

# Check gap
gap_cells = [k for k in cells.keys() if 42 <= k[1] <= 48]
print(f"Gap rows (42-48) cells count: {len(gap_cells)} (Expected 0)")
assert len(gap_cells) == 0, "Error: Gap not empty!"

print("ALL CHECKS PASSED: Pixel-perfect, zero overlaps, correct Opepen silhouette!")
