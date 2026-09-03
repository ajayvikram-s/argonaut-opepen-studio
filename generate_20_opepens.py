import os
import json
import re
import random
import xml.etree.ElementTree as ET

# Load contract data
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
        return {}, []
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
    return pixels, [c[0] for c in palette]

def parse_d_box(d):
    tokens = re.findall(r'([A-Za-z]|-?\d+(?:\.\d+)?)', d)
    curr_x, curr_y = 0, 0
    xs, ys = [], []
    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        if cmd == 'M':
            curr_x = float(tokens[i+1])
            curr_y = float(tokens[i+2])
            xs.append(curr_x)
            ys.append(curr_y)
            i += 3
        elif cmd == 'H':
            curr_x = float(tokens[i+1])
            xs.append(curr_x)
            i += 2
        elif cmd == 'V':
            curr_y = float(tokens[i+1])
            ys.append(curr_y)
            i += 2
        elif cmd in ['Z', 'z']:
            i += 1
        else:
            i += 1
    if not xs or not ys:
        return None
    return int(min(xs)), int(min(ys))

# Extract standard target silhouette cells from gold opepen
with open('gold argonaut opepen.svg', 'r') as f:
    orig_opepen = f.read()

orig_paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"', orig_opepen)
body_cells_target = []
base_cells_target = []

for d, _ in orig_paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    box = parse_d_box(d)
    if not box:
        continue
    gx = box[0] // 10
    gy = box[1] // 10
    if 28 <= gy <= 41:
        if (gx, gy) not in body_cells_target:
            body_cells_target.append((gx, gy))
    elif 49 <= gy <= 55:
        if (gx, gy) not in base_cells_target:
            base_cells_target.append((gx, gy))

body_cells_target.sort(key=lambda pt: (pt[1], pt[0]))
base_cells_target.sort(key=lambda pt: (pt[1], pt[0]))

# Create output folder
out_dir = os.path.join(os.getcwd(), 'argonaut_opepens')
os.makedirs(out_dir, exist_ok=True)

# Define 20 curated, visually stunning Argonaut trait combinations
# [bg_idx, body_idx, hoodie_idx, relic_idx, eyes_idx, mouth_idx, head_idx, name]
combinations = [
    # 1. Cyberpunk Alien
    (5, 0, 0, 0, 5, 0, 6, "01_Cyber_Alien_Opepen", "Void", "Alien", "3D Glasses", "Golden Fleece"),
    # 2. Radioactive Toxic Glow
    (16, 1, 0, 0, 1, 0, 1, "02_Radioactive_Void_Opepen", "Radioactive Void Charcoal", "Radioactive", "Shades", "Oarsman's Band"),
    # 3. Celestial Gold
    (2, 2, 0, 1, 5, 0, 6, "03_Celestial_Gold_Opepen", "Violet", "Gold", "3D Glasses", "Golden Fleece"),
    # 4. Platinum Silver Knight
    (5, 6, 0, 0, 3, 0, 0, "04_Liquid_Silver_Opepen", "Void", "Silver", "Digital", "None"),
    # 5. Oceanic Deep Coral
    (8, 5, 0, 1, 2, 0, 7, "05_Abyssal_Coral_Opepen", "Punkblue", "Coral", "Glasses", "Corsair"),
    # 6. Ancient Petrified Relic
    (33, 3, 0, 1, 4, 0, 2, "06_Ancient_Petrified_Opepen", "Storm", "Petrified", "Eye Patch", "Bandana"),
    # 7. Volcanic Prehistoric
    (3, 7, 0, 0, 1, 0, 0, "07_Volcanic_Prehistoric_Opepen", "Wine", "Prehistoric", "Shades", "None"),
    # 8. Sacred Temple Bone
    (7, 8, 5, 1, 0, 0, 0, "08_Clergy_Bone_Opepen", "Ancient", "Bone", "None", "None"),
    # 9. Neo Mint Floral
    (14, 4, 0, 0, 6, 0, 3, "09_Neon_Mint_Floral_Opepen", "Neon Mint", "Floral", "Designer", "Dawn Pink Beanie"),
    # 10. Hot Rose Cyber Alien
    (11, 0, 0, 0, 7, 0, 4, "10_Hot_Rose_Alien_Opepen", "Hot Rose", "Alien", "Gucci", "Aegean Blue Beanie"),
    # 11. Radioactive Deep Raspberry
    (17, 1, 0, 0, 10, 0, 5, "11_Deep_Raspberry_Radioactive_Opepen", "Radioactive Deep Raspberry", "Radioactive", "Versace", "Purphat"),
    # 12. Emerald Forest Gold
    (12, 2, 0, 0, 8, 0, 2, "12_Emerald_Gold_Opepen", "Emerald", "Gold", "Louis Vuitton", "Bandana"),
    # 13. Bubblegum Silver Punk
    (0, 6, 0, 0, 11, 0, 1, "13_Bubblegum_Silver_Opepen", "Bubblegum", "Silver", "Dior", "Oarsman's Band"),
    # 14. Bright Lilac Coral
    (13, 5, 0, 0, 9, 0, 3, "14_Bright_Lilac_Coral_Opepen", "Bright Lilac", "Coral", "Prada", "Dawn Pink Beanie"),
    # 15. Radioactive Seafoam Alien
    (18, 0, 0, 0, 5, 0, 6, "15_Radioactive_Seafoam_Alien_Opepen", "Radioactive Seafoam", "Alien", "3D Glasses", "Golden Fleece"),
    # 16. Wine Red Petrified
    (3, 3, 0, 0, 1, 0, 7, "16_Wine_Petrified_Opepen", "Wine", "Petrified", "Shades", "Corsair"),
    # 17. Siren Prehistoric Corsair
    (30, 7, 0, 0, 4, 0, 7, "17_Siren_Prehistoric_Opepen", "Siren", "Prehistoric", "Eye Patch", "Corsair"),
    # 18. Storm Silver Cyber
    (33, 6, 0, 0, 3, 0, 5, "18_Storm_Silver_Opepen", "Storm", "Silver", "Digital", "Purphat"),
    # 19. Void Cyan Bone
    (27, 8, 0, 0, 5, 0, 6, "19_Void_Cyan_Bone_Opepen", "Void Cyan", "Bone", "3D Glasses", "Golden Fleece"),
    # 20. Ancient Floral Royalty
    (7, 4, 3, 0, 6, 0, 6, "20_Ancient_Floral_Royalty_Opepen", "Ancient", "Floral", "Designer", "Golden Fleece")
]

print(f"Generating {len(combinations)} distinct Argonaut Opepens...")

results = []

for idx, item in enumerate(combinations):
    bg_idx, body_idx, hoodie_idx, relic_idx, eyes_idx, mouth_idx, head_idx, filename_base, bg_name, body_name, eyes_name, head_name = item
    
    # 1. Background color
    bg_blob_id = get_blob_id(0, bg_idx)
    _, bg_pal = decode_blob(bg_blob_id)
    bg_color = bg_pal[0] if bg_pal else "#141414"
    
    # 2. Decode Trait Blobs
    bone_px, bone_pal = decode_blob(get_blob_id(1, body_idx))
    hoodie_px, _ = decode_blob(get_blob_id(2, hoodie_idx)) if hoodie_idx > 0 else ({}, [])
    relic_px, _ = decode_blob(get_blob_id(3, relic_idx)) if relic_idx > 0 else ({}, [])
    eyes_px, _ = decode_blob(get_blob_id(4, eyes_idx)) if eyes_idx > 0 else ({}, [])
    mouth_px, _ = decode_blob(get_blob_id(5, mouth_idx)) if mouth_idx > 0 else ({}, [])
    crown_px, _ = decode_blob(get_blob_id(6, head_idx)) if head_idx > 0 else ({}, [])
    
    # Composite upright head (rows 5..18)
    # Paint order: Bones -> Eyes -> Hoodie -> Relic -> Mouth -> Crown
    composite_head = {}
    for pt, (c, a) in bone_px.items():
        if 5 <= pt[1] <= 18:
            composite_head[pt] = (c, a)
    for pt, (c, a) in eyes_px.items():
        if 5 <= pt[1] <= 18:
            composite_head[pt] = (c, a)
    for pt, (c, a) in hoodie_px.items():
        if 5 <= pt[1] <= 18:
            composite_head[pt] = (c, a)
    for pt, (c, a) in relic_px.items():
        if 5 <= pt[1] <= 18:
            composite_head[pt] = (c, a)
    for pt, (c, a) in mouth_px.items():
        if 5 <= pt[1] <= 18:
            composite_head[pt] = (c, a)
    for pt, (c, a) in crown_px.items():
        if 5 <= pt[1] <= 18:
            composite_head[pt] = (c, a)
            
    # Right Head (bounded strictly to 14x14 box: gx in 28..41, gy in 14..27)
    head_right_paths = []
    head_right_cells = {}
    for (pt_x, pt_y), (c, a) in composite_head.items():
        gx_R = pt_x + 22
        gy_R = pt_y + 9
        if 28 <= gx_R <= 41 and 14 <= gy_R <= 27:
            head_right_cells[(gx_R, gy_R)] = (c, a)
            x = gx_R * 10
            y = gy_R * 10
            path_d = f"M{x+10} {y}H{x}V{y+10}H{x+10}V{y}Z"
            op_str = f' fill-opacity="{a/255.0:.3f}"' if a < 255 else ''
            head_right_paths.append(f'<path d="{path_d}" fill="{c}"{op_str}/>\n')
            
    # Left Head (Anti-diagonal reflection: gx_L = 41 - gy_R, gy_L = 55 - gx_R)
    head_left_paths = []
    for (gx_R, gy_R), (c, a) in head_right_cells.items():
        gx_L = 41 - gy_R
        gy_L = 55 - gx_R
        if 14 <= gx_L <= 27 and 14 <= gy_L <= 27:
            x = gx_L * 10
            y = gy_L * 10
            path_d = f"M{x+10} {y}H{x}V{y+10}H{x+10}V{y}Z"
            op_str = f' fill-opacity="{a/255.0:.3f}"' if a < 255 else ''
            head_left_paths.append(f'<path d="{path_d}" fill="{c}"{op_str}/>\n')
            
    # Body & Base from on-chain bone palette
    rng = random.Random(idx * 100 + 42)
    shuffled_palette = []
    while len(shuffled_palette) < len(body_cells_target) + len(base_cells_target) + 200:
        tmp = list(bone_pal)
        rng.shuffle(tmp)
        shuffled_palette.extend(tmp)
        
    body_paths = []
    c_idx = 0
    for gx, gy in body_cells_target:
        c = shuffled_palette[c_idx]
        c_idx += 1
        x = gx * 10
        y = gy * 10
        path_d = f"M{x+10} {y}H{x}V{y+10}H{x+10}V{y}Z"
        body_paths.append(f'<path d="{path_d}" fill="{c}"/>\n')
        
    base_paths = []
    for gx, gy in base_cells_target:
        c = shuffled_palette[c_idx]
        c_idx += 1
        x = gx * 10
        y = gy * 10
        path_d = f"M{x+10} {y}H{x}V{y+10}H{x+10}V{y}Z"
        base_paths.append(f'<path d="{path_d}" fill="{c}"/>\n')
        
    bg_path = f'<path d="M560 0H0V560H560V0Z" fill="{bg_color}"/>\n'
    
    svg_str = (
        '<svg width="560" height="560" viewBox="0 0 560 560" fill="none" xmlns="http://www.w3.org/2000/svg">\n'
        + bg_path
        + ''.join(head_left_paths)
        + ''.join(head_right_paths)
        + ''.join(body_paths)
        + ''.join(base_paths)
        + '</svg>\n'
    )
    
    svg_filename = f"{filename_base}.svg"
    svg_filepath = os.path.join(out_dir, svg_filename)
    
    with open(svg_filepath, 'w', encoding='utf-8') as f:
        f.write(svg_str)
        
    # Validate
    parsed = re.findall(r'<path d="([^"]+)" fill="([^"]+)"', svg_str)
    cells = {}
    overlaps = 0
    for d, fill in parsed:
        if d == "M560 0H0V560H560V0Z":
            continue
        box = parse_d_box(d)
        if not box:
            continue
        gx = box[0] // 10
        gy = box[1] // 10
        if (gx, gy) in cells:
            overlaps += 1
        cells[(gx, gy)] = fill
        
    assert overlaps == 0, f"Overlaps detected in {svg_filename}"
    
    meta = {
        'id': idx + 1,
        'name': filename_base.replace('_', ' '),
        'file': svg_filename,
        'palette': bg_name,
        'background_color': bg_color,
        'bones': body_name,
        'sight': eyes_name,
        'crown': head_name,
        'total_paths': len(parsed),
        'unique_cells': len(cells),
        'overlaps': overlaps
    }
    results.append(meta)
    print(f"[{idx+1:02d}/20] Created {svg_filename} -> Bones: {body_name}, BG: {bg_name} ({bg_color}), Overlaps: {overlaps}")

# Save collection metadata index
with open(os.path.join(out_dir, 'collection_index.json'), 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print("\nSUCCESS: All 20 Argonaut Opepens generated and validated in argonaut_opepens/")
