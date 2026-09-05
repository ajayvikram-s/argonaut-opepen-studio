#!/usr/bin/env python3
"""
Argonaut to Opepen Converter Tool
Fetches any Argonaut token directly from the Ethereum smart contract (1..9999),
extracts its exact on-chain traits, composite head, and colors, and generates
the corresponding pixel-perfect Argonaut Opepen artwork in both SVG and JPG formats!

Layering & Paint Stacking strictly follows the Argonauts smart contract:
- Layer 0: Palette (LAYER_BACKGROUND)
- Layer 1: Bones (LAYER_BODY)
- Layer 2: Cloak (LAYER_HOODIE)
- Layer 3: Relic (LAYER_NECK)
- Layer 4: Sight (LAYER_EYES)
- Layer 5: Artifact (LAYER_MOUTH)
- Layer 6: Crown (LAYER_HEAD)
"""

import os
import sys
import json
import base64
import random
import re
import argparse
import urllib.request
import ssl
from PIL import Image, ImageDraw

RPC_ENDPOINTS = [
    'https://ethereum.publicnode.com',
    'https://1rpc.io/eth',
    'https://rpc.mevblocker.io',
    'https://eth-mainnet.public.blastapi.io'
]

MAIN_CONTRACT = '0x387C41B0B2F1128dE44dB1Bcf8baad085f26392C'
ctx = ssl._create_unverified_context()

# Load local engine data
with open('argonauts_engine_data.json', 'r', encoding='utf-8') as f:
    ENGINE_DATA = json.load(f)

BLOBS = {b['index']: bytes.fromhex(b['hex']) for b in ENGINE_DATA.get('blobs', [])}
LAYOUT = bytes.fromhex(ENGINE_DATA.get('layout_hex', ''))

def get_blob_id(layer, idx):
    pos = 0
    for _ in range(layer):
        count = LAYOUT[pos]
        pos += 1 + count
    count = LAYOUT[pos]
    if idx >= count:
        return 0xFF
    return LAYOUT[pos + 1 + idx]

def decode_blob(blob_id):
    if blob_id == 0xFF or blob_id not in BLOBS:
        return {}, []
    blob = BLOBS[blob_id]
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

TRAIT_LOOKUP = {
    'Palette': [
        "Bubblegum", "Yellow", "Violet", "Wine", "Sky", "Void", "MuseGreen", "Ancient",
        "Punkblue", "Blush", "Offwhite",
        "Hot Rose", "Emerald", "Bright Lilac", "Neon Mint", "Paper White",
        "Radioactive Void Charcoal", "Radioactive Deep Raspberry", "Radioactive Seafoam", "Radioactive Lavender", "Radioactive Paper White",
        "Ice Prism Pink", "Violet Pink", "Violet Cyan", "Navy Pink", "Void Pink",
        "Void Blue", "Void Cyan", "Navy Blue Vignette", "Void Teal Vignette",
        "Siren", "Seafoam", "Lavender", "Storm"
    ],
    'Bones': [
        "Alien", "Radioactive", "Gold", "Petrified", "Floral",
        "Coral", "Silver", "Prehistoric", "Bone", "Floral"
    ],
    'Cloak': ["", "Servant", "Death", "Royalty", "Ivory", "Clergy"],
    'Relic': ["", "Gold"],
    'Sight': [
        "", "Shades", "Glasses", "Digital", "Eye Patch", "3D Glasses", "Designer",
        "Gucci", "Louis Vuitton", "Prada", "Versace", "Dior", "Balenciaga", "Chanel"
    ],
    'Crown': [
        "", "Oarsman's Band", "Bandana", "Dawn Pink Beanie", "Aegean Blue Beanie", "Purphat", "Golden Fleece", "Corsair"
    ]
}

def get_trait_index(category, name):
    if not name:
        return 0
    names = TRAIT_LOOKUP.get(category, [])
    for idx, n in enumerate(names):
        if n.lower() == name.lower():
            return idx
    return 0

def decode_artifact_layers(artifact_name):
    if not artifact_name or artifact_name == 'None':
        return {}, {}
    name_low = artifact_name.lower()
    device = {}
    smoke = {}
    if 'dragon' in name_low:
        smoke, _ = decode_blob(78)
        device, _ = decode_blob(80)
    elif 'vape' in name_low or 'blueberry' in name_low or 'thc' in name_low:
        smoke, _ = decode_blob(78)
        device, _ = decode_blob(79)
    elif 'pipe' in name_low or 'woodpipe' in name_low:
        raw_pipe, _ = decode_blob(64)
        for k, (c, a) in raw_pipe.items():
            if a < 255:
                smoke[k] = (c, a)
            else:
                device[k] = (c, a)
    return device, smoke

# Canonical Tapered Silhouette Cells
CANON_BODY_TARGET = []
for gy in range(28, 42):
    for gx in range(14, 42):
        if gy == 39 and (gx == 14 or gx == 41):
            continue
        if gy == 40 and (gx <= 15 or gx >= 40):
            continue
        if gy == 41 and (gx <= 16 or gx >= 39):
            continue
        CANON_BODY_TARGET.append((gx, gy))

CANON_BASE_TARGET = []
for gy in range(49, 56):
    for gx in range(14, 42):
        if gy == 49 and (gx <= 16 or gx >= 39):
            continue
        if gy == 50 and (gx <= 15 or gx >= 40):
            continue
        if gy == 51 and (gx == 14 or gx == 41):
            continue
        CANON_BASE_TARGET.append((gx, gy))

def fetch_token_metadata(token_id):
    payload = json.dumps({
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'eth_call',
        'params': [{'to': MAIN_CONTRACT, 'data': '0xc87b56dd' + hex(token_id)[2:].zfill(64)}, 'latest']
    }).encode('utf-8')
    
    for ep in RPC_ENDPOINTS:
        try:
            req = urllib.request.Request(
                ep,
                headers={'Content-Type': 'application/json', 'User-Agent': 'ArgonautOpepen/1.0'},
                data=payload
            )
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                result = data.get('result')
                if not result or result == '0x':
                    continue
                raw_bytes = bytes.fromhex(result[2:])
                offset = int.from_bytes(raw_bytes[:32], 'big')
                str_len = int.from_bytes(raw_bytes[offset:offset+32], 'big')
                uri = raw_bytes[offset+32:offset+32+str_len].decode('utf-8', errors='ignore')
                
                if uri.startswith('data:application/json;base64,'):
                    b64_json = uri.split('data:application/json;base64,')[1]
                    return json.loads(base64.b64decode(b64_json).decode('utf-8'))
                elif uri.startswith('data:application/json;utf8,'):
                    return json.loads(uri.split('data:application/json;utf8,')[1])
        except Exception:
            continue
    return None

CLOAK_PALETTES = {
    1: {"name": "Servant", "SPEC_HI": "#FFFFFF", "SOFT_HI": "#E6E6E6", "ROSE_HI": "#DDDDDD", "MID_TONE": "#D6D3D1", "BERRY_MID": "#C8C4C0", "ROSE_MID": "#B8B4B0", "DEEP_ROSE": "#A9A9A9", "PLUM_SHD": "#979797"},
    2: {"name": "Death", "SPEC_HI": "#2E2F38", "SOFT_HI": "#24252C", "ROSE_HI": "#1E1F24", "MID_TONE": "#1A1B20", "BERRY_MID": "#17171B", "ROSE_MID": "#131316", "DEEP_ROSE": "#0D0D10", "PLUM_SHD": "#09090B"},
    3: {"name": "Royalty", "SPEC_HI": "#5A3686", "SOFT_HI": "#4A2C6E", "ROSE_HI": "#432864", "MID_TONE": "#3C2358", "BERRY_MID": "#351E4E", "ROSE_MID": "#2D1842", "DEEP_ROSE": "#29173C", "PLUM_SHD": "#241334"},
    4: {"name": "Ivory", "SPEC_HI": "#FFF9EB", "SOFT_HI": "#E8E2D2", "ROSE_HI": "#DDD7C7", "MID_TONE": "#D1CBBB", "BERRY_MID": "#C4BEAE", "ROSE_MID": "#B8B2A2", "DEEP_ROSE": "#B2AC9D", "PLUM_SHD": "#A39D8E"},
    5: {"name": "Clergy", "SPEC_HI": "#A7344E", "SOFT_HI": "#992F47", "ROSE_HI": "#9D3049", "MID_TONE": "#8C2A40", "BERRY_MID": "#8F2B42", "ROSE_MID": "#88283E", "DEEP_ROSE": "#7E2439", "PLUM_SHD": "#691C2E"}
}

def get_volumetric_cloth_color(gx, gy, c_idx):
    pal = CLOAK_PALETTES.get(c_idx, CLOAK_PALETTES[5])
    # Option 3: Dual-Wing Drapery Sweep Accents
    if (gy in (29, 30)) and (gx in (17, 18)): return pal["SOFT_HI"]
    if (gy in (32, 33)) and (gx in (18, 19)): return pal["SOFT_HI"]
    if (gy in (34, 35)) and (gx in (19, 20)): return pal["SOFT_HI"]
    if (gy in (32, 33)) and (gx in (27, 28)): return pal["ROSE_MID"]
    if (gy in (34, 35)) and (gx in (26, 27)): return pal["ROSE_MID"]

    dist = abs(gx - 13.5)
    if 28 <= gy <= 41:
        if gy <= 30:
            if dist > 9.5: return pal["PLUM_SHD"]
            if dist > 7.0: return pal["SPEC_HI"]
            if dist > 4.5: return pal["SOFT_HI"]
            if dist > 1.5: return pal["MID_TONE"]
            return pal["ROSE_MID"]
        elif gy <= 33:
            if dist > 11.5: return pal["PLUM_SHD"]
            if dist > 9.5: return pal["DEEP_ROSE"]
            if dist > 8.0: return pal["ROSE_MID"]
            if dist > 5.5: return pal["SOFT_HI"]
            if dist > 2.0: return pal["MID_TONE"]
            return pal["BERRY_MID"]
        elif gy <= 38:
            if dist > 11.5: return pal["PLUM_SHD"]
            if dist > 9.0: return pal["DEEP_ROSE"]
            if dist > 7.5: return pal["ROSE_MID"]
            if dist > 4.5:
                if gy in (36, 37) and 5.5 <= dist <= 7.0: return pal["SOFT_HI"]
                return pal["MID_TONE"]
            if dist > 1.5: return pal["MID_TONE"]
            return pal["BERRY_MID"]
        elif gy == 39:
            if dist > 10.5: return pal["DEEP_ROSE"]
            if dist > 8.5: return pal["ROSE_MID"]
            if dist > 1.5: return pal["MID_TONE"]
            return pal["BERRY_MID"]
        elif gy == 40:
            if dist > 9.5: return pal["PLUM_SHD"]
            if dist > 7.5: return pal["DEEP_ROSE"]
            if dist > 5.5: return pal["ROSE_MID"]
            return pal["MID_TONE"]
        elif gy == 41:
            if dist > 6.0: return pal["PLUM_SHD"]
            if dist > 3.0: return pal["DEEP_ROSE"]
            return pal["ROSE_MID"]
    elif 49 <= gy <= 55:
        if gy == 49:
            if dist > 7.5: return pal["DEEP_ROSE"]
            if dist > 5.0: return pal["SOFT_HI"]
            if dist > 1.5: return pal["MID_TONE"]
            return pal["SOFT_HI"]
        elif gy == 50:
            if dist > 9.0: return pal["DEEP_ROSE"]
            if dist > 6.5: return pal["SOFT_HI"]
            return pal["MID_TONE"]
        elif gy <= 54:
            if dist > 11.0: return pal["PLUM_SHD"]
            if dist > 9.0: return pal["DEEP_ROSE"]
            if dist > 7.0: return pal["ROSE_MID"]
            return pal["MID_TONE"]
        elif gy == 55:
            if dist > 8.0: return pal["PLUM_SHD"]
            if dist > 4.0: return pal["DEEP_ROSE"]
            return pal["ROSE_MID"]
    return pal["MID_TONE"]

CLOAK_BODY_MAPS = {}
try:
    _maps_path = os.path.join(os.path.dirname(__file__), 'extracted_cloak_maps.json')
    if os.path.exists(_maps_path):
        with open(_maps_path, 'r', encoding='utf-8') as _f:
            CLOAK_BODY_MAPS = json.load(_f).get('body', {})
except Exception:
    pass

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c*2 for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def generate_opepen_for_token(token_id, output_dir=None):
    print(f"\n[+] Fetching Argonaut #{token_id:04d} from smart contract...")
    meta = fetch_token_metadata(token_id)
    if not meta:
        print(f"[-] Error: Could not fetch metadata for Token #{token_id}.")
        return None

    name = meta.get('name', f'Argonaut #{token_id:04d}')
    attributes = meta.get('attributes', [])
    attr_dict = {a.get('trait_type'): a.get('value') for a in attributes if isinstance(a, dict)}
    
    # Contract layer mappings:
    bg_name = attr_dict.get('Palette', 'Void')      # Layer 0
    bones_name = attr_dict.get('Bones', 'Bone')     # Layer 1
    cloak_name = attr_dict.get('Cloak', '')         # Layer 2
    relic_name = attr_dict.get('Relic', '')         # Layer 3
    sight_name = attr_dict.get('Sight', '')         # Layer 4
    artifact_name = attr_dict.get('Artifact', '')   # Layer 5
    crown_name = attr_dict.get('Crown', '')         # Layer 6
    
    print(f"    Name: {name}")
    print(f"    Layer 0 (Palette):  {bg_name}")
    print(f"    Layer 1 (Bones):    {bones_name}")
    print(f"    Layer 2 (Cloak):    {cloak_name or 'None'}")
    print(f"    Layer 3 (Relic):    {relic_name or 'None'}")
    print(f"    Layer 4 (Sight):    {sight_name or 'None'}")
    print(f"    Layer 5 (Artifact): {artifact_name or 'None'}")
    print(f"    Layer 6 (Crown):    {crown_name or 'None'}")

    bg_idx = get_trait_index('Palette', bg_name)
    body_idx = get_trait_index('Bones', bones_name)
    cloak_idx = get_trait_index('Cloak', cloak_name)
    relic_idx = get_trait_index('Relic', relic_name)
    sight_idx = get_trait_index('Sight', sight_name)
    crown_idx = get_trait_index('Crown', crown_name)

    # 1. Background color
    _, bg_pal = decode_blob(get_blob_id(0, bg_idx))
    bg_color = bg_pal[0] if bg_pal else "#141414"

    # 2. Decode Blobs
    bone_px, bone_palette = decode_blob(get_blob_id(1, body_idx))
    cloak_px, _ = decode_blob(get_blob_id(2, cloak_idx)) if cloak_idx > 0 else ({}, [])
    relic_px, _ = decode_blob(get_blob_id(3, relic_idx)) if relic_idx > 0 else ({}, [])
    sight_px, _ = decode_blob(get_blob_id(4, sight_idx)) if sight_idx > 0 else ({}, [])
    crown_px, _ = decode_blob(get_blob_id(6, crown_idx)) if crown_idx > 0 else ({}, [])
    artifact_device_px, artifact_smoke_px = decode_artifact_layers(artifact_name)

    # 3. Strict Paint Stacking Sequence from RendererV2.sol:
    # 1. Bones -> 2. Vapor Smoke -> 3. Sight -> 4. Cloak -> 5. Relic -> 6. Artifact Device -> 7. Crown
    composite_head = {}

    # Layer 1: Bones
    for pt, (c, a) in bone_px.items():
        if 5 <= pt[1] <= 18:
            composite_head[pt] = (c, a)

    # Layer 5 Smoke: Vapor Smoke (rendered before eyes so it drifts behind frame)
    for pt, (c, a) in artifact_smoke_px.items():
        composite_head[pt] = (c, a)

    # Layer 4: Sight (Eyes) - Fully visible uncropped as in original Argonaut
    for pt, (c, a) in sight_px.items():
        composite_head[pt] = (c, a)

    # Layer 2: Cloak (Hoodie)
    for pt, (c, a) in cloak_px.items():
        if 5 <= pt[1] <= 18:
            composite_head[pt] = (c, a)

    # Layer 3: Relic (Neck)
    for pt, (c, a) in relic_px.items():
        if 5 <= pt[1] <= 18:
            composite_head[pt] = (c, a)

    # Layer 5 Device: Artifact / Mouth Device - Fully visible
    for pt, (c, a) in artifact_device_px.items():
        composite_head[pt] = (c, a)

    # Layer 6: Crown (Head)
    for pt, (c, a) in crown_px.items():
        if 5 <= pt[1] <= 18:
            composite_head[pt] = (c, a)

    # 4. Right Head construction
    head_right_cells = {}
    for (pt_x, pt_y), (c, a) in composite_head.items():
        gx_R = pt_x + 22
        gy_R = pt_y + 9
        is_artifact_pixel = (pt_x, pt_y) in artifact_device_px or (pt_x, pt_y) in artifact_smoke_px
        is_sight_pixel = (pt_x, pt_y) in sight_px
        if is_artifact_pixel or is_sight_pixel:
            if 0 <= gx_R < 56 and 0 <= gy_R < 56:
                head_right_cells[(gx_R, gy_R)] = (c, a, is_artifact_pixel or is_sight_pixel)
        else:
            min_gy = 0 if (pt_x, pt_y) in crown_px else 14
            if 28 <= gx_R <= 41 and min_gy <= gy_R <= 27:
                head_right_cells[(gx_R, gy_R)] = (c, a, False)

    # 5. Left Head construction (Anti-diagonal reflection)
    head_left_cells = {}
    for (gx_R, gy_R), (c, a, is_exempt) in head_right_cells.items():
        gx_L = 41 - gy_R
        gy_L = 55 - gx_R
        if is_exempt:
            if 0 <= gx_L < 56 and 0 <= gy_L < 56:
                head_left_cells[(gx_L, gy_L)] = (c, a)
        else:
            if 14 <= gx_L <= 27 and 14 <= gy_L <= 27:
                head_left_cells[(gx_L, gy_L)] = (c, a)

    # Convert cells to paths
    head_right_paths = []
    for (gx, gy), (c, a) in head_right_cells.items():
        x = gx * 10
        y = gy * 10
        path_d = f"M{x+10} {y}H{x}V{y+10}H{x+10}V{y}Z"
        op_str = f' fill-opacity="{a/255.0:.3f}"' if a < 255 else ''
        head_right_paths.append(f'<path d="{path_d}" fill="{c}"{op_str}/>\n')

    head_left_paths = []
    for (gx, gy), (c, a) in head_left_cells.items():
        x = gx * 10
        y = gy * 10
        path_d = f"M{x+10} {y}H{x}V{y+10}H{x+10}V{y}Z"
        op_str = f' fill-opacity="{a/255.0:.3f}"' if a < 255 else ''
        head_left_paths.append(f'<path d="{path_d}" fill="{c}"{op_str}/>\n')

    # Body & Base using exact canonical silhouette targets
    rng = random.Random(token_id * 31337 + 42)
    shuffled_palette = []
    while len(shuffled_palette) < len(CANON_BODY_TARGET) + len(CANON_BASE_TARGET) + 200:
        tmp = list(bone_palette)
        rng.shuffle(tmp)
        shuffled_palette.extend(tmp)

    body_paths = []
    c_idx = 0
    cloak_map = CLOAK_BODY_MAPS.get(str(cloak_idx)) if cloak_idx > 0 else None
    for gx, gy in CANON_BODY_TARGET:
        if (gx, gy) in head_right_cells or (gx, gy) in head_left_cells:
            continue
        coord_key = f"{gx},{gy}"
        if cloak_idx > 0 and cloak_map and coord_key in cloak_map:
            c = cloak_map[coord_key]
        elif cloak_idx > 0:
            c = get_volumetric_cloth_color(gx, gy, cloak_idx)
        else:
            c = shuffled_palette[c_idx]
            c_idx += 1
        x = gx * 10
        y = gy * 10
        path_d = f"M{x+10} {y}H{x}V{y+10}H{x+10}V{y}Z"
        body_paths.append(f'<path d="{path_d}" fill="{c}"/>\n')

    base_paths = []
    for gx, gy in CANON_BASE_TARGET:
        if (gx, gy) in head_right_cells or (gx, gy) in head_left_cells:
            continue
        coord_key = f"{gx},{gy}"
        if cloak_idx > 0 and cloak_map and coord_key in cloak_map:
            c = cloak_map[coord_key]
        elif cloak_idx > 0:
            c = get_volumetric_cloth_color(gx, gy, cloak_idx)
        else:
            c = shuffled_palette[c_idx]
            c_idx += 1
        x = gx * 10
        y = gy * 10
        path_d = f"M{x+10} {y}H{x}V{y+10}H{x+10}V{y}Z"
        base_paths.append(f'<path d="{path_d}" fill="{c}"/>\n')

    bg_path = f'<path d="M560 0H0V560H560V0Z" fill="{bg_color}"/>\n'

    # Assemble complete SVG
    svg_content = (
        '<svg width="560" height="560" viewBox="0 0 560 560" fill="none" xmlns="http://www.w3.org/2000/svg">\n'
        + bg_path
        + ''.join(head_left_paths)
        + ''.join(head_right_paths)
        + ''.join(body_paths)
        + ''.join(base_paths)
        + '</svg>\n'
    )

    if not output_dir:
        output_dir = os.path.join(os.getcwd(), 'custom_opepens')
    os.makedirs(output_dir, exist_ok=True)

    clean_title = re.sub(r'[^a-zA-Z0-9_]', '_', f"Argonaut_{token_id:04d}_{bones_name}_{bg_name}_Opepen")
    svg_filename = f"{clean_title}.svg"
    jpg_filename = f"{clean_title}.jpg"
    
    svg_path = os.path.join(output_dir, svg_filename)
    jpg_path = os.path.join(output_dir, jpg_filename)

    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    # Render directly to high-res JPG using Pillow
    img = Image.new('RGBA', (560, 560), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    
    # Background
    bg_rgb = hex_to_rgb(bg_color)
    draw.rectangle([0, 0, 560, 560], fill=(*bg_rgb, 255))

    # Draw body & base
    for i, (gx, gy) in enumerate(CANON_BODY_TARGET):
        if (gx, gy) in head_right_cells or (gx, gy) in head_left_cells:
            continue
        c = shuffled_palette[i]
        x, y = gx * 10, gy * 10
        r, g, b = hex_to_rgb(c)
        draw.rectangle([x, y, x + 10, y + 10], fill=(r, g, b, 255))

    for j, (gx, gy) in enumerate(CANON_BASE_TARGET):
        if (gx, gy) in head_right_cells or (gx, gy) in head_left_cells:
            continue
        c = shuffled_palette[len(CANON_BODY_TARGET) + j]
        x, y = gx * 10, gy * 10
        r, g, b = hex_to_rgb(c)
        draw.rectangle([x, y, x + 10, y + 10], fill=(r, g, b, 255))

    # Draw heads with exact layer stack
    for (gx, gy), (fill, a) in head_left_cells.items():
        x, y = gx * 10, gy * 10
        r, g, b = hex_to_rgb(fill)
        draw.rectangle([x, y, x + 10, y + 10], fill=(r, g, b, a))

    for (gx, gy), (fill, a) in head_right_cells.items():
        x, y = gx * 10, gy * 10
        r, g, b = hex_to_rgb(fill)
        draw.rectangle([x, y, x + 10, y + 10], fill=(r, g, b, a))

    rgb_img = img.convert('RGB')
    rgb_img.save(jpg_path, 'JPEG', quality=98)

    print(f"[+] SUCCESS: Created Argonaut Opepen for Token #{token_id}:")
    print(f"    SVG: {svg_path}")
    print(f"    JPG: {jpg_path}")
    return svg_path, jpg_path

def main():
    parser = argparse.ArgumentParser(description="Convert any on-chain Argonaut token into an Argonaut Opepen.")
    parser.add_argument('tokens', nargs='*', type=int, help="Token ID(s) to convert (e.g. 1 2 3 5 42 777 1458 9999)")
    parser.add_argument('--out', type=str, default="custom_opepens", help="Output directory for generated files")
    args = parser.parse_args()

    token_list = args.tokens
    if not token_list:
        print("--- Argonaut to Opepen Interactive CLI ---")
        val = input("Enter Argonaut Token ID (1..9999) or multiple IDs separated by space: ").strip()
        if not val:
            print("No token ID provided. Exiting.")
            sys.exit(0)
        token_list = [int(x) for x in re.findall(r'\d+', val)]

    for tid in token_list:
        generate_opepen_for_token(tid, output_dir=args.out)

if __name__ == '__main__':
    main()
