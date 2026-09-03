import re
import json

def parse_svg_grid(svg_path):
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tokens_paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"', content)
    cells = {}
    for d, fill in tokens_paths:
        if d == "M560 0H0V560H560V0Z":
            continue
        nums = list(map(int, re.findall(r'\d+', d)))
        min_x = min(nums[0], nums[2])
        min_y = min(nums[1], nums[3])
        gx = min_x // 10
        gy = min_y // 10
        cells[(gx, gy)] = fill
    return cells

orig_cells = parse_svg_grid('argonaut_opepens/09_Neon_Mint_Floral_Opepen.svg')
new_cells = parse_svg_grid('custom_opepens/Argonaut_0001_Bone_Violet_Opepen.svg')

print(f"Original 09 Opepen total cells: {len(orig_cells)}")
print(f"New Token 1 Opepen total cells:  {len(new_cells)}")

# Compare by region:
# 1. Head Left:  gx in 14..27, gy in 14..27
# 2. Head Right: gx in 28..41, gy in 14..27
# 3. Body:       gx in 14..41, gy in 28..41
# 4. Gap:        gy in 42..48
# 5. Base:       gx in 14..41, gy in 49..55

def get_region_cells(cells):
    regions = {
        'head_left': [pt for pt in cells.keys() if 14 <= pt[0] <= 27 and 14 <= pt[1] <= 27],
        'head_right': [pt for pt in cells.keys() if 28 <= pt[0] <= 41 and 14 <= pt[1] <= 27],
        'body': [pt for pt in cells.keys() if 14 <= pt[0] <= 41 and 28 <= pt[1] <= 41],
        'gap': [pt for pt in cells.keys() if 42 <= pt[1] <= 48],
        'base': [pt for pt in cells.keys() if 14 <= pt[0] <= 41 and 49 <= pt[1] <= 55],
    }
    return regions

orig_reg = get_region_cells(orig_cells)
new_reg = get_region_cells(new_cells)

for reg_name in orig_reg:
    print(f"\nRegion '{reg_name}':")
    print(f"  Orig count: {len(orig_reg[reg_name])}")
    print(f"  New count:  {len(new_reg[reg_name])}")
    diff_missing = set(orig_reg[reg_name]) - set(new_reg[reg_name])
    diff_extra = set(new_reg[reg_name]) - set(orig_reg[reg_name])
    if diff_missing:
        print(f"  Missing cells ({len(diff_missing)}): {sorted(list(diff_missing))[:10]}")
    if diff_extra:
        print(f"  Extra cells ({len(diff_extra)}): {sorted(list(diff_extra))[:10]}")

# Let's inspect Body and Base shape in original 09 Opepen:
print("\n--- EXACT ACTIVE CELLS IN BODY OF 09 OPEPEN ---")
for gy in range(28, 42):
    xs = sorted([x for x, y in orig_cells.keys() if y == gy])
    print(f"gy={gy:02d}: count={len(xs)}, min_x={min(xs) if xs else '-'}, max_x={max(xs) if xs else '-'}, missing={[x for x in range(14, 42) if x not in xs]}")

print("\n--- EXACT ACTIVE CELLS IN BASE OF 09 OPEPEN ---")
for gy in range(49, 56):
    xs = sorted([x for x, y in orig_cells.keys() if y == gy])
    print(f"gy={gy:02d}: count={len(xs)}, min_x={min(xs) if xs else '-'}, max_x={max(xs) if xs else '-'}")
