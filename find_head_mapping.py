import json

with open('gold_argonaut_head_pixels.json', 'r') as f:
    orig_head_pixels = json.load(f)

# Let's inspect all elements of Head Left from analyze_transformations
import re

with open('gold argonaut opepen.svg', 'r') as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)

head_left_pixels = []
head_right_pixels = []

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
            head_left_pixels.append((gx, gy, fill, op, min_x, min_y))
        elif 28 <= gx <= 41:
            head_right_pixels.append((gx, gy, fill, op, min_x, min_y))

print(f"Head Left pixel count: {len(head_left_pixels)}")
print(f"Head Right pixel count: {len(head_right_pixels)}")

# Let's print the visual map of Head Right vs Head Left
print("\n--- VISUAL MAP OF HEAD RIGHT (Original) ---")
hr_grid = {(gx, gy): fill for gx, gy, fill, op, _, _ in head_right_pixels}
for gy in range(14, 28):
    row_str = f"gy={gy:02d}: "
    for gx in range(28, 42):
        if (gx, gy) in hr_grid:
            row_str += "#"
        else:
            row_str += "."
    print(row_str)

print("\n--- VISUAL MAP OF HEAD LEFT (Transformed) ---")
hl_grid = {(gx, gy): fill for gx, gy, fill, op, _, _ in head_left_pixels}
for gy in range(14, 28):
    row_str = f"gy={gy:02d}: "
    for gx in range(14, 28):
        if (gx, gy) in hl_grid:
            row_str += "#"
        else:
            row_str += "."
    print(row_str)

# Let's find the coordinate mapping (gx_right, gy_right) -> (gx_left, gy_left)
# Test all affine mapping: gx_left = A * gx_right + B * gy_right + C, gy_left = D * gx_right + E * gy_right + F
for A in [-1, 0, 1]:
    for B in [-1, 0, 1]:
        for D in [-1, 0, 1]:
            for E in [-1, 0, 1]:
                if A*E - B*D == 0:
                    continue # non-invertible
                for C in range(-100, 100):
                    for F in range(-100, 100):
                        matches = 0
                        for (gx_r, gy_r), fill_r in hr_grid.items():
                            gx_l = A * gx_r + B * gy_r + C
                            gy_l = D * gy_r + E * gx_r + F # check
                            if (gx_l, gy_l) in hl_grid:
                                if hl_grid[(gx_l, gy_l)].lower() == fill_r.lower():
                                    matches += 1
                        if matches > 50:
                            print(f"FOUND EXACT MAPPING: A={A}, B={B}, C={C}, D={D}, E={E}, F={F} -> Matches: {matches}")
                            break

