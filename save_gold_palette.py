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

# Layer 1 = Bones, index 2 = Gold
gold_bones_blob_id = get_blob_id(1, 2)
blob = blobs[gold_bones_blob_id]

p = (blob[0] << 8) | blob[1]
off = 2
contract_gold_palette = []
for i in range(p):
    r, g, b, a = blob[off], blob[off+1], blob[off+2], blob[off+3]
    contract_gold_palette.append(f'#{r:02X}{g:02X}{b:02X}')
    off += 4

print(f"Contract Gold Bones palette: {len(contract_gold_palette)} colors")
print("First 10:", contract_gold_palette[:10])
print("Last 10:", contract_gold_palette[-10:])

# Save palette to a JSON for easy reference
with open('contract_gold_bones_palette.json', 'w') as f:
    json.dump(contract_gold_palette, f, indent=2)
