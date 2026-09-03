import json
from generate_artworks import decode_blob_to_pixel_grid, BLOBS, get_blob_id, TRAIT_NAMES, UNDERHEAD_MAP, HEADBAND_HEAD_IDX, VAPE_MOUTH_IDX, VAPE_SMOKE_BLOB, VAPE_BLUE_BLOB, VAPE_DRAGONS_BLOB

LAYER_BACKGROUND = 0
LAYER_BODY = 1
LAYER_HOODIE = 2
LAYER_NECK = 3
LAYER_EYES = 4
LAYER_MOUTH = 5
LAYER_HEAD = 6

# Traits: Golden Royal Argonaut with 3D Glasses
# Palette: Void Pink (25)
# Bones: Gold (2)
# Cloak: Royalty (3)
# Relic: Gold (1)
# Sight: 3D Glasses (5)
# Artifact: None (0)
# Crown: Golden Fleece (6)
traits = [25, 2, 3, 1, 5, 0, 6]

layer_names = {
    LAYER_BACKGROUND: 'Background_Void_Pink',
    LAYER_BODY: 'Bones_Gold',
    LAYER_EYES: 'Sight_3D_Glasses',
    LAYER_HOODIE: 'Cloak_Royalty',
    LAYER_NECK: 'Relic_Gold',
    LAYER_MOUTH: 'Artifact_None',
    LAYER_HEAD: 'Crown_Golden_Fleece'
}

paint_order = [LAYER_BACKGROUND, LAYER_BODY, LAYER_EYES, LAYER_HOODIE, LAYER_NECK, LAYER_MOUTH, LAYER_HEAD]

full_grid = [[None for _ in range(24)] for _ in range(24)]
layer_grids = {}

for l in paint_order:
    l_grid = [[None for _ in range(24)] for _ in range(24)]
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
        decode_blob_to_pixel_grid(BLOBS[VAPE_SMOKE_BLOB], full_grid)
        decode_blob_to_pixel_grid(BLOBS[VAPE_SMOKE_BLOB], l_grid)
        
    if blob_id != 0xFF and blob_id in BLOBS:
        decode_blob_to_pixel_grid(BLOBS[blob_id], full_grid)
        decode_blob_to_pixel_grid(BLOBS[blob_id], l_grid)
        
    layer_grids[l] = l_grid

# Build Figma SVG with individual 1x1 pixel rects inside grouped layers
svg_lines = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="576" height="576" shape-rendering="crispEdges">'
]

# We output grouped by layer for clean Figma layer tree
for l in paint_order:
    g_id = layer_names[l]
    # Check if there are any pixels in this layer
    has_pixels = any(layer_grids[l][y][x] is not None for y in range(24) for x in range(24))
    if not has_pixels:
        continue
    svg_lines.append(f'  <g id="{g_id}">')
    for y in range(24):
        for x in range(24):
            px = layer_grids[l][y][x]
            if px is not None and px[3] > 0:
                hex_c = f"#{px[0]:02x}{px[1]:02x}{px[2]:02x}"
                op = f' fill-opacity="{px[3]/255:.3f}"' if px[3] != 255 else ''
                svg_lines.append(f'    <rect id="{g_id}_px_{x}_{y}" x="{x}" y="{y}" width="1" height="1" fill="{hex_c}"{op}/>')
    svg_lines.append('  </g>')

svg_lines.append('</svg>')

svg_content = '\n'.join(svg_lines)
with open('argonaut_figma.svg', 'w', encoding='utf-8') as f:
    f.write(svg_content)

# Dump full pixel map for the final combined 24x24 canvas
pixel_manifest = []
for y in range(24):
    row_pixels = []
    for x in range(24):
        px = full_grid[y][x]
        if px is not None:
            hex_c = f"#{px[0]:02x}{px[1]:02x}{px[2]:02x}"
            row_pixels.append({
                "x": x,
                "y": y,
                "index": y * 24 + x,
                "hex": hex_c,
                "rgba": list(px)
            })
    pixel_manifest.append(row_pixels)

with open('argonaut_pixel_data.json', 'w', encoding='utf-8') as f:
    json.dump({
        "traits": {
            "Palette": TRAIT_NAMES[0][traits[0]],
            "Bones": TRAIT_NAMES[1][traits[1]],
            "Cloak": TRAIT_NAMES[2][traits[2]],
            "Relic": TRAIT_NAMES[3][traits[3]],
            "Sight": TRAIT_NAMES[4][traits[4]],
            "Artifact": TRAIT_NAMES[5][traits[5]],
            "Crown": TRAIT_NAMES[6][traits[6]],
        },
        "trait_indices": traits,
        "dimensions": {"width": 24, "height": 24, "total_pixels": 576},
        "pixels": [px for row in pixel_manifest for px in row]
    }, f, indent=2)

print("SUCCESS")
