import json
import re

# Let's inspect each row of gold argonaut.svg in the 24x24 standard grid
# and also in canvas pixel coordinates (step=24, offset: x = gx*24 - 8, y = gy*24 - 16)

with open('gold argonaut.svg', 'r') as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)

cells_by_gy = {}
all_cells = {}
for d, fill, op in paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    nums = list(map(int, re.findall(r'\d+', d)))
    min_x = min(nums[0], nums[2])
    min_y = min(nums[1], nums[3])
    gx = (min_x + 8) // 24
    gy = (min_y + 16) // 24
    if gy not in cells_by_gy:
        cells_by_gy[gy] = {}
    cells_by_gy[gy][gx] = (fill, op, min_x, min_y, d)
    all_cells[(gx, gy)] = (fill, op, min_x, min_y, d)

print("=== COMPLETE ROW-BY-ROW BREAKDOWN OF GOLD ARGONAUT ===")
for gy in sorted(cells_by_gy.keys()):
    row_cells = cells_by_gy[gy]
    min_gx = min(row_cells.keys())
    max_gx = max(row_cells.keys())
    y_canvas = gy * 24 - 16
    print(f"\nRow gy={gy:02d} (Canvas Y={y_canvas:03d}..{y_canvas+24:03d}), X=[{min_gx}..{max_gx}], Count={len(row_cells)}:")
    for gx in sorted(row_cells.keys()):
        fill, op, min_x, min_y, d = row_cells[gx]
        op_str = f" op={op}" if op else ""
        print(f"  (gx={gx:02d}, gy={gy:02d}) [x={min_x:03d}, y={min_y:03d}]: {fill}{op_str}")

# In Argonauts anatomy on 24x24 grid:
# - Head / Crown / Sight / Skull / Face / Jaw: Rows gy = 5 to 18 (Canvas Y = 104 to 416)
#   - Rows 5..9 (Y=104..224): Crown / Cranium / Top of Skull
#   - Rows 10..14 (Y=224..344): Eyes / 3D Glasses / Nose Cavity / Skull Face
#   - Rows 15..18 (Y=344..440): Jaw / Teeth / Chin / Clavicle base
# - Body / Neck / Clavicle / Ribs / Spine: Rows gy = 19 to 23 (Canvas Y = 440 to 560)
#   - Row 19 (Y=440..464): Neck / Spine / Clavicle top
#   - Row 20 (Y=464..488): Clavicle / Upper Ribcage
#   - Row 21 (Y=488..512): Ribcage / Golden Relic
#   - Row 22 (Y=512..536): Lower Ribcage / Relic / Spine
#   - Row 23 (Y=536..560): Base of Ribcage / Lumbar Spine

head_pixels = {k: v for k, v in all_cells.items() if k[1] <= 18}
body_pixels = {k: v for k, v in all_cells.items() if k[1] >= 19}

print(f"\nTotal Head Pixels (gy <= 18): {len(head_pixels)}")
print(f"Total Body Pixels (gy >= 19): {len(body_pixels)}")

# Save head pixels as reusable JSON reference
head_data = []
for (gx, gy), (fill, op, min_x, min_y, d) in sorted(head_pixels.items(), key=lambda pt: (pt[0][1], pt[0][0])):
    head_data.append({
        'grid_x': gx,
        'grid_y': gy,
        'canvas_x': min_x,
        'canvas_y': min_y,
        'fill': fill,
        'opacity': op if op else "1.0",
        'path_d': d
    })

with open('gold_argonaut_head_pixels.json', 'w') as f:
    json.dump(head_data, f, indent=2)

print("Saved gold_argonaut_head_pixels.json successfully!")
