import json
from generate_artworks import decode_blob_to_pixel_grid, BLOBS, get_blob_id, TRAIT_NAMES, UNDERHEAD_MAP, HEADBAND_HEAD_IDX, VAPE_MOUTH_IDX, VAPE_SMOKE_BLOB, VAPE_BLUE_BLOB

LAYER_BACKGROUND = 0
LAYER_BODY = 1
LAYER_HOODIE = 2
LAYER_NECK = 3
LAYER_EYES = 4
LAYER_MOUTH = 5
LAYER_HEAD = 6

# Traits: Golden Royal Argonaut with 3D Glasses
traits = [25, 2, 3, 1, 5, 0, 6]

layer_names = {
    LAYER_BACKGROUND: 'Background_Canvas_60x60',
    LAYER_BODY: 'Bones_Gold',
    LAYER_EYES: 'Sight_3D_Glasses',
    LAYER_HOODIE: 'Cloak_Royalty',
    LAYER_NECK: 'Relic_Gold',
    LAYER_MOUTH: 'Artifact_None',
    LAYER_HEAD: 'Crown_Golden_Fleece'
}

paint_order = [LAYER_BACKGROUND, LAYER_BODY, LAYER_EYES, LAYER_HOODIE, LAYER_NECK, LAYER_MOUTH, LAYER_HEAD]

CANVAS_SIZE = 60
full_grid_60 = [[None for _ in range(CANVAS_SIZE)] for _ in range(CANVAS_SIZE)]
layer_grids = {l: [[None for _ in range(CANVAS_SIZE)] for _ in range(CANVAS_SIZE)] for l in paint_order}

# 1. Background layer (60x60 Canvas) - Void Dark Base (#0d0b16)
BG_COLOR = (13, 11, 22, 255) # Sleek Void Dark Canvas fill
for y in range(CANVAS_SIZE):
    for x in range(CANVAS_SIZE):
        layer_grids[LAYER_BACKGROUND][y][x] = BG_COLOR
        full_grid_60[y][x] = BG_COLOR

# 2. Decode Argonaut layers (placed at original (0,0) coordinates, size 24x24 inside 60x60 canvas)
for l in paint_order:
    if l == LAYER_BACKGROUND:
        continue
    idx = traits[l]
    blob_id = 0xFF
    if l == LAYER_MOUTH and idx == VAPE_MOUTH_IDX:
        blob_id = VAPE_BLUE_BLOB
    else:
        blob_id = get_blob_id(l, idx)
        if l == LAYER_EYES and blob_id != 0xFF and traits[LAYER_HEAD] == HEADBAND_HEAD_IDX:
            uh = UNDERHEAD_MAP.get(idx, 0)
            if uh != 0:
                blob_id = uh
    
    if l == LAYER_EYES and idx == VAPE_MOUTH_IDX:
        decode_blob_to_pixel_grid(BLOBS[VAPE_SMOKE_BLOB], full_grid_60, offset_x=0, offset_y=0)
        decode_blob_to_pixel_grid(BLOBS[VAPE_SMOKE_BLOB], layer_grids[l], offset_x=0, offset_y=0)
        
    if blob_id != 0xFF and blob_id in BLOBS:
        decode_blob_to_pixel_grid(BLOBS[blob_id], full_grid_60, offset_x=0, offset_y=0)
        decode_blob_to_pixel_grid(BLOBS[blob_id], layer_grids[l], offset_x=0, offset_y=0)

# Build Figma-ready 60x60 SVG with crisp 1x1 vector rects and clean layer groupings
svg_lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_SIZE} {CANVAS_SIZE}" width="{CANVAS_SIZE * 10}" height="{CANVAS_SIZE * 10}" shape-rendering="crispEdges">'
]

# Layer 0: Background 60x60 canvas
svg_lines.append(f'  <g id="Background_Canvas_60x60">')
svg_lines.append(f'    <rect id="bg_canvas_base" x="0" y="0" width="{CANVAS_SIZE}" height="{CANVAS_SIZE}" fill="#0d0b16"/>')
svg_lines.append('  </g>')

# Other Argonaut layers
for l in paint_order[1:]:
    g_id = layer_names[l]
    has_pixels = any(layer_grids[l][y][x] is not None for y in range(CANVAS_SIZE) for x in range(CANVAS_SIZE))
    if not has_pixels:
        continue
    svg_lines.append(f'  <g id="{g_id}">')
    for y in range(CANVAS_SIZE):
        for x in range(CANVAS_SIZE):
            px = layer_grids[l][y][x]
            if px is not None and px[3] > 0:
                hex_c = f"#{px[0]:02x}{px[1]:02x}{px[2]:02x}"
                op = f' fill-opacity="{px[3]/255:.3f}"' if px[3] != 255 else ''
                svg_lines.append(f'    <rect id="{g_id}_px_{x}_{y}" x="{x}" y="{y}" width="1" height="1" fill="{hex_c}"{op}/>')
    svg_lines.append('  </g>')

svg_lines.append('</svg>')

svg_content = '\n'.join(svg_lines)
with open('argonaut_60x60_figma.svg', 'w', encoding='utf-8') as f:
    f.write(svg_content)

# Export Full Pixel Manifest (3,600 pixels)
all_pixels = []
argonaut_pixel_count = 0
for y in range(CANVAS_SIZE):
    for x in range(CANVAS_SIZE):
        px = full_grid_60[y][x]
        hex_c = f"#{px[0]:02x}{px[1]:02x}{px[2]:02x}"
        is_argo = (0 <= x < 24 and 0 <= y < 24 and any(layer_grids[l][y][x] is not None for l in paint_order[1:]))
        if is_argo:
            argonaut_pixel_count += 1
        all_pixels.append({
            "x": x,
            "y": y,
            "index_60x60": y * CANVAS_SIZE + x,
            "is_argonaut_character": is_argo,
            "hex": hex_c,
            "rgba": list(px)
        })

with open('argonaut_60x60_pixel_data.json', 'w', encoding='utf-8') as f:
    json.dump({
        "canvas_size": {"width": 60, "height": 60, "total_pixels": 3600},
        "character_placement": {"x_min": 0, "x_max": 23, "y_min": 0, "y_max": 23},
        "argonaut_character_pixels": argonaut_pixel_count,
        "background_pixels": 3600 - argonaut_pixel_count,
        "traits": {
            "Palette": "Void Pink (Expanded 60x60 Void Base)",
            "Bones": TRAIT_NAMES[1][traits[1]],
            "Cloak": TRAIT_NAMES[2][traits[2]],
            "Relic": TRAIT_NAMES[3][traits[3]],
            "Sight": TRAIT_NAMES[4][traits[4]],
            "Artifact": TRAIT_NAMES[5][traits[5]],
            "Crown": TRAIT_NAMES[6][traits[6]],
        },
        "pixels": all_pixels
    }, f, indent=2)

print(f"DONE: Canvas 60x60 generated. Total pixels: 3600, Character pixels: {argonaut_pixel_count}")
