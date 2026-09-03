import json
import re

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

# Read gold argonaut.svg
with open('gold argonaut.svg', 'r') as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)

# Map SVG paths to (gx, gy) in standard 24x24 trait grid
# gx = (min_x + 8) // 24
# gy = (min_y + 16) // 24
svg_grid = {}
all_svg_items = []
for d, fill, op in paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    nums = list(map(int, re.findall(r'\d+', d)))
    min_x = min(nums[0], nums[2])
    min_y = min(nums[1], nums[3])
    gx = (min_x + 8) // 24
    gy = (min_y + 16) // 24
    svg_grid[(gx, gy)] = (fill, op, d)
    all_svg_items.append((gx, gy, fill, op, d))

print(f"Total SVG items: {len(all_svg_items)}")
print(f"Total unique (gx, gy) cells: {len(svg_grid)}")

# Check which traits make up this Argonaut:
# Layer 0: Palette (Background = #75459C -> let's see which palette this is)
# Layer 1: Body (Bones = Gold)
# Layer 2: Cloak (Hoodie)
# Layer 3: Relic (Neck)
# Layer 4: Sight (Eyes)
# Layer 5: Artifact (Mouth)
# Layer 6: Crown (Head)

# Let's decode all layers & items and find the exact combination
layer_names = ["Palette", "Bones", "Cloak", "Relic", "Sight", "Artifact", "Crown"]
matched_traits = {}

for layer_id in range(7):
    # count for this layer
    pos = 0
    for _ in range(layer_id):
        pos += 1 + layout[pos]
    count = layout[pos]
    for item_id in range(count):
        bid = get_blob_id(layer_id, item_id)
        if bid == 0xFF:
            continue
        trait_px = decode_blob(bid)
        # check overlap with svg
        matches = 0
        for pt, (c, a) in trait_px.items():
            if pt in svg_grid and svg_grid[pt][0].lower() == c.lower():
                matches += 1
        if matches > 0:
            print(f"Layer {layer_id} ({layer_names[layer_id]}), Item {item_id}: Matches = {matches}/{len(trait_px)}")

