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

body_names = [
    "Alien", "Radioactive", "Gold", "Petrified", "Floral",
    "Coral", "Silver", "Prehistoric", "Bone", "Floral-2"
]

print("=== ALL BONE / BODY TYPES IN ARGONAUTS CONTRACT ===")
body_traits_data = {}

for idx, name in enumerate(body_names):
    bid = get_blob_id(1, idx)
    if bid == 0xFF or bid not in blobs:
        print(f"Index {idx} ({name}): No blob")
        continue
    blob = blobs[bid]
    p = (blob[0] << 8) | blob[1]
    off = 2
    palette = []
    for _ in range(p):
        r, g, b, a = blob[off], blob[off+1], blob[off+2], blob[off+3]
        palette.append(f'#{r:02X}{g:02X}{b:02X}')
        off += 4
    
    # decode pixels
    pixel = 0
    pixels = {}
    while off < len(blob):
        ci = (blob[off] << 8) | blob[off+1]
        run = blob[off+2]
        if ci != 0:
            c = palette[ci - 1]
            for r_i in range(run):
                px = (pixel + r_i) % 24
                py = (pixel + r_i) // 24
                pixels[(px, py)] = c
        pixel += run
        off += 3
    
    body_traits_data[name] = {
        'idx': idx,
        'blob_id': bid,
        'palette_size': len(palette),
        'unique_colors': len(set(palette)),
        'sample_colors': list(set(palette))[:8],
        'pixel_count': len(pixels),
        'pixels': pixels,
        'palette': palette
    }
    print(f"\nIndex {idx}: {name}")
    print(f"  Blob ID: {bid}, Palette size: {len(palette)}, Decoded Pixels: {len(pixels)}")
    print(f"  Key Colors: {list(set(palette))[:8]}")

# Also let's inspect available Background Palettes (Layer 0)
bg_names = [
    "Bubblegum", "Yellow", "Violet", "Wine", "Sky", "Void", "MuseGreen", "Ancient",
    "Punkblue", "Blush", "Offwhite",
    "Hot Rose", "Emerald", "Bright Lilac", "Neon Mint", "Paper White",
    "Radioactive Void Charcoal", "Radioactive Deep Raspberry", "Radioactive Seafoam", "Radioactive Lavender", "Radioactive Paper White",
    "Ice Prism Pink", "Violet Pink", "Violet Cyan", "Navy Pink", "Void Pink",
    "Void Blue", "Void Cyan", "Navy Blue Vignette", "Void Teal Vignette",
    "Siren", "Seafoam", "Lavender", "Storm"
]
print("\n=== BACKGROUND PALETTES ===")
bg_colors = {}
for idx, name in enumerate(bg_names):
    bid = get_blob_id(0, idx)
    if bid in blobs:
        blob = blobs[bid]
        p = (blob[0] << 8) | blob[1]
        off = 2
        palette = []
        for _ in range(p):
            r, g, b, a = blob[off], blob[off+1], blob[off+2], blob[off+3]
            palette.append(f'#{r:02X}{g:02X}{b:02X}')
            off += 4
        bg_colors[name] = palette
        print(f"  {idx}: {name} -> {palette}")
