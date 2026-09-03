import json
import re

# Load contract engine data
with open('argonauts_engine_data.json', 'r', encoding='utf-8') as f:
    engine = json.load(f)

blobs = {b['index']: bytes.fromhex(b['hex']) for b in engine['blobs']}
layout = bytes.fromhex(engine['layout_hex'])

def get_blob_id(layer, idx):
    pos = 0
    for _ in range(layer):
        count = layout[pos]
        pos += 1 + count
    count = layout[pos]
    if idx >= count:
        return 0xFF
    return layout[pos + 1 + idx]

# Decode all traits into pixel grids
def decode_blob(blob_id):
    if blob_id == 0xFF or blob_id not in blobs:
        return {}
    blob = blobs[blob_id]
    p = (blob[0] << 8) | blob[1]
    off = 2
    palette = []
    for _ in range(p):
        r, g, b, a = blob[off], blob[off+1], blob[off+2], blob[off+3]
        palette.append((f'#{r:02X}{g:02X}{b:02X}', a))
        off += 4
    
    pixels = {}
    pixel = 0
    while off < len(blob):
        ci = (blob[off] << 8) | blob[off+1]
        run = blob[off+2]
        if ci != 0:
            c, a = palette[ci - 1]
            for r_i in range(run):
                px = (pixel + r_i) % 24
                py = (pixel + r_i) // 24
                pixels[(px, py)] = (c, a)
        pixel += run
        off += 3
    return pixels

# Decode Gold Bones (Layer 1, Idx 2)
gold_bones = decode_blob(get_blob_id(1, 2))
print(f"Gold Bones trait pixels: {len(gold_bones)}")

# Map gold_bones grid min/max
gb_xs = [x for x, y in gold_bones.keys()]
gb_ys = [y for x, y in gold_bones.keys()]
print(f"Gold Bones grid X: [{min(gb_xs)}..{max(gb_xs)}], Y: [{min(gb_ys)}..{max(gb_ys)}]")

# Read gold argonaut.svg
with open('gold argonaut.svg', 'r') as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)
svg_pixels = []
for d, fill, op in paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    nums = list(map(int, re.findall(r'\d+', d)))
    min_x = min(nums[0], nums[2])
    min_y = min(nums[1], nums[3])
    # x coordinate in 24px step:
    # Let's see: in gold_bones: min x is 4, max x is 19.
    # In SVG: min x is 88 (88 = 3 * 24 + 16? Or grid_x = (min_x - ...))
    svg_pixels.append((min_x, min_y, fill, op))

# Find the affine alignment: grid_x * 24 + offset_x = min_x
# Let's test offsets:
print("\nMatching SVG pixels to 24x24 trait space:")
for off_x in range(0, 24):
    for off_y in range(0, 24):
        matches = 0
        for x, y, fill, op in svg_pixels:
            if (x - off_x) % 24 == 0 and (y - off_y) % 24 == 0:
                gx = (x - off_x) // 24
                gy = (y - off_y) // 24
                if (gx, gy) in gold_bones and gold_bones[(gx, gy)][0].lower() == fill.lower():
                    matches += 1
        if matches > 50:
            print(f"Found Alignment: off_x={off_x}, off_y={off_y}, Matches with Gold Bones: {matches}/{len(gold_bones)}")

