import json

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

def extract_colors_from_blob(blob):
    if not blob:
        return []
    p = (blob[0] << 8) | blob[1]
    off = 2
    colors = []
    for ci in range(p):
        r, g, b, a = blob[off], blob[off+1], blob[off+2], blob[off+3]
        hex_c = f"#{r:02X}{g:02X}{b:02X}"
        colors.append((hex_c, r, g, b, a))
        off += 4
    return colors

print("--- GOLD BONES (Layer 1, Idx 2) ---")
gold_bones_blob_id = get_blob_id(1, 2)
gold_bones_colors = extract_colors_from_blob(blobs[gold_bones_blob_id])
for c in gold_bones_colors:
    print(" ", c)

print("\n--- GOLD RELIC (Layer 3, Idx 1) ---")
gold_relic_blob_id = get_blob_id(3, 1)
gold_relic_colors = extract_colors_from_blob(blobs[gold_relic_blob_id])
for c in gold_relic_colors:
    print(" ", c)

print("\n--- GOLDEN FLEECE (Layer 6, Idx 6) ---")
golden_fleece_blob_id = get_blob_id(6, 6)
golden_fleece_colors = extract_colors_from_blob(blobs[golden_fleece_blob_id])
for c in golden_fleece_colors:
    print(" ", c)

print("\n--- YELLOW / GOLD PALETTE (Layer 0, Idx 1) ---")
yellow_palette_blob_id = get_blob_id(0, 1)
yellow_colors = extract_colors_from_blob(blobs[yellow_palette_blob_id])
for c in yellow_colors:
    print(" ", c)

# Collect ALL official gold colors from the smart contract engine
all_gold_colors = set([c[0] for c in gold_bones_colors + gold_relic_colors + golden_fleece_colors])
print("\n--- ALL UNIQUE ON-CHAIN GOLD TRAIT COLORS ---")
print(f"Total: {len(all_gold_colors)}")
for c in sorted(list(all_gold_colors)):
    print(f"  {c}")
