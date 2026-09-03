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

gold_bones_blob_id = get_blob_id(1, 2)
blob = blobs[gold_bones_blob_id]

p = (blob[0] << 8) | blob[1]
off = 2
palette = []
for i in range(p):
    r, g, b, a = blob[off], blob[off+1], blob[off+2], blob[off+3]
    palette.append(f'#{r:02X}{g:02X}{b:02X}')
    off += 4

pixel = 0
gold_bones_grid = {}
while off < len(blob):
    ci = (blob[off] << 8) | blob[off+1]
    run = blob[off+2]
    if ci != 0:
        c = palette[ci - 1]
        for r_i in range(run):
            px = (pixel + r_i) % 24
            py = (pixel + r_i) // 24
            gold_bones_grid[(px, py)] = c
    pixel += run
    off += 3

print("Gold Bones 24x24 trait visual map:")
for y in range(24):
    row_str = f"y={y:02d}: "
    has_px = False
    for x in range(24):
        if (x, y) in gold_bones_grid:
            has_px = True
            c = gold_bones_grid[(x, y)]
            row_str += f"[{c}] "
        else:
            row_str += "    .     "
    if has_px:
        print(row_str)
