import re
import json
from collections import defaultdict

with open('gold argonaut opepen.svg', 'r', encoding='utf-8') as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)

# Load head pixels from gold_argonaut_head_pixels.json
with open('gold_argonaut_head_pixels.json', 'r') as f:
    orig_head_pixels = json.load(f)

print(f"Original head pixel count: {len(orig_head_pixels)}")

# Extract all pixels in the SVG
# Map into 4 quadrants / zones:
# Zone 1 (Top-Left):   gx in [14..27], gy in [14..27] -> 14x14 grid (Head A)
# Zone 2 (Top-Right):  gx in [28..41], gy in [14..27] -> 14x14 grid (Head B)
# Zone 3 (Mid Torso):  gx in [14..41], gy in [28..41] -> 28x14 grid (Body)
# Zone 4 (Empty Gap):  gy in [42..48] -> empty
# Zone 5 (Base):       gx in [14..41], gy in [49..55] -> 28x7 grid (Base)

zones = {
    'head_left': [],
    'head_right': [],
    'body': [],
    'gap': [],
    'base': []
}

for d, fill, op in paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    nums = list(map(int, re.findall(r'\d+', d)))
    min_x = min(nums[0], nums[2])
    min_y = min(nums[1], nums[3])
    max_x = max(nums[0], nums[2])
    max_y = max(nums[1], nums[3])
    w = max_x - min_x
    h = max_y - min_y
    gx = min_x // 10
    gy = min_y // 10
    
    item = {'d': d, 'fill': fill, 'op': op, 'x': min_x, 'y': min_y, 'w': w, 'h': h, 'gx': gx, 'gy': gy}
    
    if 14 <= gy <= 27:
        if 14 <= gx <= 27:
            zones['head_left'].append(item)
        elif 28 <= gx <= 41:
            zones['head_right'].append(item)
    elif 28 <= gy <= 41:
        zones['body'].append(item)
    elif 42 <= gy <= 48:
        zones['gap'].append(item)
    elif 49 <= gy <= 55:
        zones['base'].append(item)

print(f"Zone counts:")
print(f"  Head Left  (gx: 14..27, gy: 14..27): {len(zones['head_left'])} elements")
print(f"  Head Right (gx: 28..41, gy: 14..27): {len(zones['head_right'])} elements")
print(f"  Body       (gx: 14..41, gy: 28..41): {len(zones['body'])} elements")
print(f"  Gap        (gy: 42..48):             {len(zones['gap'])} elements")
print(f"  Base       (gx: 14..41, gy: 49..55): {len(zones['base'])} elements")

# Now let's analyze Head Left vs Head Right:
# Which one is the original head, and which one is the rotated/flipped copy?
# Let's compare coordinates and colors with orig_head_pixels!
# In orig_head_pixels:
# grid_x in [6..19] (span=14), grid_y in [5..18] (span=14)
# That is exactly a 14x14 bounding box! (gx - 6 in 0..13, gy - 5 in 0..13)

# Let's test standard orientations:
# 1. Direct placement at Top-Left: target_gx = (gx - 6) + 14 = gx + 8, target_gy = (gy - 5) + 14 = gy + 9
# 2. Direct placement at Top-Right: target_gx = (gx - 6) + 28 = gx + 22, target_gy = (gy - 5) + 14 = gy + 9

print("\n--- COMPARING ORIG HEAD WITH HEAD RIGHT ---")
matches_right = 0
for p in orig_head_pixels:
    tgx = p['grid_x'] + 22
    tgy = p['grid_y'] + 9
    # find in head_right
    found = any(it['gx'] == tgx and it['gy'] == tgy and it['fill'].lower() == p['fill'].lower() for it in zones['head_right'])
    if found:
        matches_right += 1
print(f"Direct match with Head Right: {matches_right} / {len(orig_head_pixels)}")

print("\n--- COMPARING ORIG HEAD WITH HEAD LEFT ---")
matches_left = 0
for p in orig_head_pixels:
    tgx = p['grid_x'] + 8
    tgy = p['grid_y'] + 9
    found = any(it['gx'] == tgx and it['gy'] == tgy and it['fill'].lower() == p['fill'].lower() for it in zones['head_left'])
    if found:
        matches_left += 1
print(f"Direct match with Head Left: {matches_left} / {len(orig_head_pixels)}")

# Now test transformations for the other head:
# Transformations of a 14x14 box (local x in 0..13, local y in 0..13):
# Transformations:
# Rotations: 0, 90, 180, 270 deg
# Flips: Horizontal flip (x' = 13 - x), Vertical flip (y' = 13 - y), Transpose, Anti-transpose
# Let's test all 8 dihedral transformations D4!
print("\n--- TESTING ALL 8 TRANSFORMATIONS ON HEAD LEFT ---")
for rot in [0, 90, 180, 270]:
    for flip_h in [False, True]:
        for flip_v in [False, True]:
            match_cnt = 0
            for p in orig_head_pixels:
                lx = p['grid_x'] - 6 # 0..13
                ly = p['grid_y'] - 5 # 0..13
                
                # apply rot
                if rot == 0:
                    rx, ry = lx, ly
                elif rot == 90:
                    rx, ry = 13 - ly, lx
                elif rot == 180:
                    rx, ry = 13 - lx, 13 - ly
                elif rot == 270:
                    rx, ry = ly, 13 - lx
                
                if flip_h:
                    rx = 13 - rx
                if flip_v:
                    ry = 13 - ry
                
                tgx = rx + 14
                tgy = ry + 14
                found = any(it['gx'] == tgx and it['gy'] == tgy and it['fill'].lower() == p['fill'].lower() for it in zones['head_left'])
                if found:
                    match_cnt += 1
            if match_cnt > 30:
                print(f"Transformation match: rot={rot}deg, flip_h={flip_h}, flip_v={flip_v} -> Matches: {match_cnt}/{len(orig_head_pixels)}")

