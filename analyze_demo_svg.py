import re
import xml.etree.ElementTree as ET

with open('demo svg.svg', 'r', encoding='utf-8') as f:
    content = f.read()

print("SVG Length:", len(content))

# Look at all path elements
lines = content.split('\n')
print(f"Total lines: {len(lines)}")
for i in range(min(15, len(lines))):
    print(f"{i+1}: {lines[i]}")

# Extract all path descriptions
paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"', content)
print(f"Total path elements: {len(paths)}")

grid_pixels = {}
for d, fill in paths:
    # check if background rect
    if d == "M560 0H0V560H560V0Z":
        print(f"Found background path: fill={fill}")
        continue
    # e.g. M320 140H310V150H320V140Z -> x from 310 to 320, y from 140 to 150
    m = re.match(r'M(\d+)\s+(\d+)H(\d+)V(\d+)H(\d+)V(\d+)Z', d)
    if m:
        x1, y1, x2, y2, x3, y3 = map(int, m.groups())
        gx = min(x1, x2) // 10
        gy = min(y1, y2) // 10
        grid_pixels[(gx, gy)] = fill.upper()
    else:
        print(f"Unmatched path format: d={d} fill={fill}")

print(f"Total parsed grid pixels: {len(grid_pixels)}")

# Print bounds of character
xs = [x for x, y in grid_pixels.keys()]
ys = [y for x, y in grid_pixels.keys()]
print(f"X range: {min(xs)} to {max(xs)}")
print(f"Y range: {min(ys)} to {max(ys)}")

# Check colors
color_freq = {}
for c in grid_pixels.values():
    color_freq[c] = color_freq.get(c, 0) + 1

print("\nColor frequencies:")
for c, count in sorted(color_freq.items(), key=lambda x: x[1], reverse=True):
    print(f"  {c}: {count}")

# Print ASCII visual of character in grid
print("\nCharacter Grid Map (56x56):")
for y in range(min(ys), max(ys)+1):
    row_str = f"y={y:02d}: "
    for x in range(min(xs), max(xs)+1):
        if (x, y) in grid_pixels:
            row_str += "#"
        else:
            row_str += "."
    print(row_str)
