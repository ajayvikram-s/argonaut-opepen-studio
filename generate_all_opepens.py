import json
import re
import random

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

def create_argonaut_opepen(body_idx, bone_name, bg_color, filename, sight_idx=5, crown_idx=6, seed=42):
    bone_px, bone_palette = decode_blob(get_blob_id(1, body_idx))
    glasses_px, _ = decode_blob(get_blob_id(4, sight_idx))
    crown_px, _ = decode_blob(get_blob_id(6, crown_idx))
    
    # Flatten head in 24x24 trait box (rows 5..18)
    composite_head = {}
    for pt, (c, a) in bone_px.items():
        if 5 <= pt[1] <= 18:
            composite_head[pt] = (c, a)
    for pt, (c, a) in glasses_px.items():
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
        
    # Body & Base
    rng = random.Random(seed)
    shuffled_palette = []
    while len(shuffled_palette) < len(body_cells_target) + len(base_cells_target) + 200:
        tmp = list(bone_palette)
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
    
    with open(filename, 'w', encoding='utf-8') as f:
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
        
    print(f"Created {filename} ({bone_name}): Total paths={len(parsed)}, Unique cells={len(cells)}, Overlaps={overlaps}")
    assert overlaps == 0, f"Overlaps in {filename}"
    return filename

# Generate all remaining bone types with perfect zero-overlap validation!
create_argonaut_opepen(1, "Radioactive", "#1C1C20", "radioactive argonaut opepen.svg")
create_argonaut_opepen(6, "Silver", "#141414", "silver argonaut opepen.svg")
create_argonaut_opepen(5, "Coral", "#2D6581", "coral argonaut opepen.svg")
create_argonaut_opepen(3, "Petrified", "#7C8088", "petrified argonaut opepen.svg")
create_argonaut_opepen(7, "Prehistoric", "#141414", "prehistoric argonaut opepen.svg")
create_argonaut_opepen(8, "Bone", "#141414", "bone argonaut opepen.svg")
