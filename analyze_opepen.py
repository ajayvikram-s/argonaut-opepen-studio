import re
import xml.etree.ElementTree as ET
from collections import defaultdict
import json

with open('gold argonaut opepen.svg', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File size: {len(content)} bytes")
lines = content.split('\n')
print(f"Total lines: {len(lines)}")

# Parse SVG header
svg_tag = re.search(r'<svg[^>]+>', content)
if svg_tag:
    print("SVG Tag:", svg_tag.group(0))

# Find background
bg_paths = re.findall(r'<path d="M560 0H0V560H560V0Z"[^>]*>', content)
print("Background paths:", bg_paths)

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)
rects = re.findall(r'<rect ([^>]+)/>', content)
print(f"Total path elements: {len(paths)}, rect elements: {len(rects)}")

# Parse all coordinates
parsed_pixels = []
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
        parsed_pixels.append({
            'd': d,
            'fill': fill,
            'op': op,
            'x': min_x,
            'y': min_y,
            'w': w,
            'h': h
        })

print(f"Total parsed pixel paths: {len(parsed_pixels)}")
widths = set(p['w'] for p in parsed_pixels)
heights = set(p['h'] for p in parsed_pixels)
print(f"Pixel widths: {widths}, heights: {heights}")

all_xs = [p['x'] for p in parsed_pixels]
all_ys = [p['y'] for p in parsed_pixels]
print(f"X bounds: {min(all_xs)} to {max(all_xs)} (span = {max(all_xs)-min(all_xs)+10}px)")
print(f"Y bounds: {min(all_ys)} to {max(all_ys)} (span = {max(all_ys)-min(all_ys)+10}px)")

distinct_xs = sorted(list(set(all_xs)))
distinct_ys = sorted(list(set(all_ys)))
print(f"Distinct X count: {len(distinct_xs)}, values: {distinct_xs}")
print(f"Distinct Y count: {len(distinct_ys)}, values: {distinct_ys}")

# Let's check grid step:
x_diffs = set(distinct_xs[i+1] - distinct_xs[i] for i in range(len(distinct_xs)-1))
y_diffs = set(distinct_ys[i+1] - distinct_ys[i] for i in range(len(distinct_ys)-1))
print("X step diffs:", x_diffs)
print("Y step diffs:", y_diffs)
