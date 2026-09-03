import json, re

with open('contract_gold_bones_palette.json', 'r') as f:
    palette = set(json.load(f))

with open('demo svg.svg', 'r', encoding='utf-8') as f:
    lines = f.readlines()

lower_paths = lines[984:1107]
print(f"Total lower paths: {len(lower_paths)}")

valid_lower_cells = {}
for idx, l in enumerate(lower_paths):
    d_m = re.search(r'd="([^"]+)"', l)
    f_m = re.search(r'fill="([^"]+)"', l)
    op_m = re.search(r'fill-opacity="([^"]+)"', l)
    if not (d_m and f_m):
        continue
    d = d_m.group(1)
    f = f_m.group(1).upper()
    nums = list(map(int, re.findall(r'\d+', d)))
    if len(nums) >= 2:
        xs = [nums[k] for k in range(0, len(nums), 2)]
        ys = [nums[k] for k in range(1, len(nums), 2)]
        min_x = min(xs)
        min_y = min(ys)
        # Snap to nearest 10
        gx = round(min_x / 10.0)
        gy = round(min_y / 10.0)
        is_gold = f in palette
        print(f"Line {idx+985}: ({min_x}, {min_y}) -> gx={gx}, gy={gy}, fill={f}, is_gold={is_gold}")
        valid_lower_cells[(gx, gy)] = (f if is_gold else None, l)

print(f"Unique snapped grid cells in lower paths: {len(valid_lower_cells)}")
