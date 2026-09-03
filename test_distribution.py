import json
from collections import Counter
import random

with open('contract_gold_bones_palette.json', 'r') as f:
    palette = json.load(f)

print(f"Total palette colors: {len(palette)}")
print(f"Set size: {len(set(palette))}")

# Also get the exact pixel colors from the decoded trait blob
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

gold_bones_blob_id = get_blob_id(1, 2)
blob = blobs[gold_bones_blob_id]
off = 2 + len(palette) * 4

pixel = 0
trait_colors = []
while off < len(blob):
    ci = (blob[off] << 8) | blob[off+1]
    run = blob[off+2]
    if ci != 0:
        c = palette[ci - 1]
        for r_i in range(run):
            trait_colors.append(c)
    pixel += run
    off += 3

print(f"Total trait pixels: {len(trait_colors)}")
c_counts = Counter(trait_colors)
print(f"Unique colors in trait: {len(c_counts)}")

# Let's inspect how colors are distributed by luminance:
# In Argonauts gold skeleton:
# Gold highlights, warm gold bones, amber marrow, deep shadow gold, cavity outlines
print("Sample of colors used across the skeleton:")
for c, cnt in c_counts.most_common(20):
    print(f"  {c}: {cnt}")
