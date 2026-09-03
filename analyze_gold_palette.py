import json
from collections import Counter

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

# Layer 1 = Bones, index 2 = Gold
gold_bones_blob_id = get_blob_id(1, 2)
blob = blobs[gold_bones_blob_id]

p = (blob[0] << 8) | blob[1]
off = 2
palette = []
for i in range(p):
    r, g, b, a = blob[off], blob[off+1], blob[off+2], blob[off+3]
    palette.append(f'#{r:02X}{g:02X}{b:02X}')
    off += 4

print(f"Contract Gold Skeleton Palette size: {len(palette)}")
print(f"Unique colors in Gold Skeleton trait: {len(set(palette))}")

# Decode pixels
pixel = 0
decoded_pixels = []
while off < len(blob):
    ci = (blob[off] << 8) | blob[off+1]
    run = blob[off+2]
    if ci != 0:
        c = palette[ci - 1]
        for r_i in range(run):
            px = (pixel + r_i) % 24
            py = (pixel + r_i) // 24
            decoded_pixels.append((px, py, c))
    pixel += run
    off += 3

print(f"Decoded trait pixel count: {len(decoded_pixels)}")

# Color frequency distribution in authentic Gold Skeleton
color_counts = Counter([c for _, _, c in decoded_pixels])
print("\nTop 30 colors in official Argonauts Gold Skeleton trait:")
for c, cnt in color_counts.most_common(30):
    print(f"  {c}: {cnt}")

print("\nColor brightness / category analysis:")
# Categorize into Highlights, Midtones, Warm Golds, Deep Gold/Bronze, Shadow/Cavity, Dark Contours
categories = {
    'highlight': [], # Bright golden highlights
    'mid_gold': [],  # Rich golden bone midtones
    'deep_amber': [],# Warm amber/deep gold
    'shadow': [],    # Bone shadows / contours
    'cavity': []     # Deep dark cavities / outlines
}

for hex_c in set(palette):
    r = int(hex_c[1:3], 16)
    g = int(hex_c[3:5], 16)
    b = int(hex_c[5:7], 16)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    if lum > 180:
        categories['highlight'].append((hex_c, lum))
    elif lum > 110:
        categories['mid_gold'].append((hex_c, lum))
    elif lum > 70:
        categories['deep_amber'].append((hex_c, lum))
    elif lum > 35:
        categories['shadow'].append((hex_c, lum))
    else:
        categories['cavity'].append((hex_c, lum))

for cat, items in categories.items():
    print(f"Category '{cat}': {len(items)} colors (e.g. {[c[0] for c in items[:5]]})")
