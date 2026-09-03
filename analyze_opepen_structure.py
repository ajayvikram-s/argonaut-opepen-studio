import re
import json

with open('gold argonaut opepen.svg', 'r', encoding='utf-8') as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)

head_left = {}
head_right = {}
body = {}
base = {}

for d, fill, op in paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    nums = list(map(int, re.findall(r'\d+', d)))
    min_x = min(nums[0], nums[2])
    min_y = min(nums[1], nums[3])
    gx = min_x // 10
    gy = min_y // 10
    
    if 14 <= gy <= 27:
        if 14 <= gx <= 27:
            head_left[(gx, gy)] = (fill, op, d)
        elif 28 <= gx <= 41:
            head_right[(gx, gy)] = (fill, op, d)
    elif 28 <= gy <= 41:
        body[(gx, gy)] = (fill, op, d)
    elif 49 <= gy <= 55:
        base[(gx, gy)] = (fill, op, d)

print(f"Head Left cells:  {len(head_left)}")
print(f"Head Right cells: {len(head_right)}")
print(f"Body cells:       {len(body)}")
print(f"Base cells:       {len(base)}")

# Let's inspect Head Right (gx_r in 28..41, gy_r in 14..27)
# and Head Left (gx_l in 14..27, gy_l in 14..27)
# Let local coordinates in each 14x14 box be:
# u_r = gx_r - 28 (0..13), v_r = gy_r - 14 (0..13)
# u_l = gx_l - 14 (0..13), v_l = gy_l - 14 (0..13)

# Test the 8 standard 2D isometries (D4 group):
transforms = {
    "Identity": lambda u, v: (u, v),
    "Rotate 90 CW": lambda u, v: (13 - v, u),
    "Rotate 180": lambda u, v: (13 - u, 13 - v),
    "Rotate 270 CW (90 CCW)": lambda u, v: (v, 13 - u),
    "Flip Horizontal (Mirror X)": lambda u, v: (13 - u, v),
    "Flip Vertical (Mirror Y)": lambda u, v: (u, 13 - v),
    "Transpose (Flip Main Diagonal / Rot 90 + Flip H)": lambda u, v: (v, u),
    "Anti-transpose (Flip Anti-Diagonal / Rot 90 + Flip V)": lambda u, v: (13 - v, 13 - u),
}

print("\n--- ISOMETRY MATCHING BETWEEN HEAD RIGHT AND HEAD LEFT ---")
for name, func in transforms.items():
    matches = 0
    total = 0
    for (gx_r, gy_r), (fill_r, op_r, _) in head_right.items():
        u_r = gx_r - 28
        v_r = gy_r - 14
        u_l, v_l = func(u_r, v_r)
        gx_l = u_l + 14
        gy_l = v_l + 14
        total += 1
        if (gx_l, gy_l) in head_left:
            fill_l, op_l, _ = head_left[(gx_l, gy_l)]
            if fill_l.lower() == fill_r.lower():
                matches += 1
    print(f"  {name:50s}: {matches}/{total} matching pixels")

# Also check what the Body and Base are made of:
print("\n--- BODY ANALYSIS (Rows gy=28..41, gx=14..41) ---")
# Count unique colors in Body
from collections import Counter
body_colors = Counter([v[0] for v in body.values()])
print(f"Body unique colors count: {len(body_colors)}, total pixels: {len(body)}")
print("Sample body colors:", body_colors.most_common(10))

print("\n--- BASE ANALYSIS (Rows gy=49..55, gx=14..41) ---")
base_colors = Counter([v[0] for v in base.values()])
print(f"Base unique colors count: {len(base_colors)}, total pixels: {len(base)}")
print("Sample base colors:", base_colors.most_common(10))

# Check gap rows
with open('gold argonaut opepen.svg', 'r') as f:
    content = f.read()

print("\n--- GAP ANALYSIS (Rows gy=42..48) ---")
gap_pixels = [d for d in paths if any(f" {y} " in f" {d} " or f"H{y}" in d or f"V{y}" in d for y in range(420, 490, 10))]
print(f"Pixels in gap Y=[420..490]: {len(gap_pixels)} (Completely Empty Gap!)")

