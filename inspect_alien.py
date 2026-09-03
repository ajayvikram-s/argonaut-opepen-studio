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
    return pixels, palette

# Let's inspect Alien Bone (layer 1, idx 0)
alien_px, alien_palette = decode_blob(get_blob_id(1, 0))
print(f"Alien decoded pixels: {len(alien_px)}, palette: {len(alien_palette)}")

# Let's see Alien Head pixels (gy in 5..18)
alien_head = {k: v for k, v in alien_px.items() if 5 <= k[1] <= 18}
print(f"Alien Head pixels (pure bone): {len(alien_head)}")

# Also let's check with traits, e.g. 3D Glasses (layer 4, idx 5), Shades (layer 4, idx 1), etc.
# Crown traits: Oarsman's Band (layer 6, idx 1), Bandana (layer 6, idx 2), Golden Fleece (layer 6, idx 6)
# If user wants Alien Argonaut with 3D glasses or pure Alien Skull:
# Let's print Alien visual map:
for gy in range(5, 19):
    row_str = f"gy={gy:02d}: "
    for gx in range(6, 20):
        if (gx, gy) in alien_head:
            row_str += "#"
        else:
            row_str += "."
    print(row_str)

