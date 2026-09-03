import re
from collections import defaultdict
import json

with open('gold argonaut.svg', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
print(f"Total lines: {len(lines)}")

# Check background
bg_m = re.search(r'<path d="M560 0H0V560H560V0Z" fill="([^"]+)"/>', content)
if bg_m:
    print(f"Background color: {bg_m.group(1)}")

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)
print(f"Total paths: {len(paths)}")

# Notice coordinates: e.g. M208 440H184V464... width = 24, height = 24!
# 560 x 560 canvas? No wait: 24px per pixel?
# Let's check: 24 * 24 = 576, or what is the grid step?
# Let's check step between consecutive coordinates: 208 - 184 = 24px!
# 464 - 440 = 24px!
# Let's find min/max coordinates:
all_xs = []
all_ys = []
pixel_list = []

for d, fill, op in paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    nums = list(map(int, re.findall(r'\d+', d)))
    if len(nums) >= 2:
        xs = [nums[k] for k in range(0, len(nums), 2)]
        ys = [nums[k] for k in range(1, len(nums), 2)]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w = max_x - min_x
        h = max_y - min_y
        all_xs.extend([min_x, max_x])
        all_ys.extend([min_y, max_y])
        pixel_list.append({
            'd': d,
            'fill': fill,
            'op': op,
            'x': min_x,
            'y': min_y,
            'w': w,
            'h': h
        })

print(f"Pixel step size / width: {set(p['w'] for p in pixel_list)}, height: {set(p['h'] for p in pixel_list)}")
print(f"X bounds: {min(all_xs)} to {max(all_xs)}")
print(f"Y bounds: {min(all_ys)} to {max(all_ys)}")

# Grid coordinates: gx = x // 24 (or relative to origin)
# Let's see: min_x = 88, 88 % 24 = 16? 88 = 3 * 24 + 16? Or what is the offset?
xs_mod = set(p['x'] % 24 for p in pixel_list)
ys_mod = set(p['y'] % 24 for p in pixel_list)
print(f"X mod 24: {xs_mod}")
print(f"Y mod 24: {ys_mod}")

# Notice 88 % 24 = 16.
# 104 % 24 = 8.
# 128 % 24 = 8.
# Let's check distinct x and y coordinates!
distinct_xs = sorted(list(set(p['x'] for p in pixel_list)))
distinct_ys = sorted(list(set(p['y'] for p in pixel_list)))
print("Distinct X coordinates:", distinct_xs)
print("Distinct Y coordinates:", distinct_ys)
