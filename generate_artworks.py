"""
Argonauts Art Generator & Pixel Transform Engine CLI
Generates new unique artworks and ERC-721 metadata matching the official Argonauts on-chain smart contracts.
Includes programmatic pixel transforms: Crop, Rotate, Flip, Scale, and Resize.
"""

import os
import json
import random
import argparse
import xml.etree.ElementTree as ET

with open('argonauts_engine_data.json', 'r', encoding='utf-8') as f:
    ENGINE = json.load(f)

BLOBS = {b['index']: bytes.fromhex(b['hex']) for b in ENGINE['blobs']}
LAYOUT = bytes.fromhex(ENGINE['layout_hex'])
HEADBAND_HEAD_IDX = ENGINE['headbandHeadIndex']
VAPE_MOUTH_IDX = ENGINE['vapeMouthIndex']
VAPE_SMOKE_BLOB = ENGINE['vapeSmokeBlob']
VAPE_BLUE_BLOB = ENGINE['vapeBlueberryBlob']
VAPE_DRAGONS_BLOB = ENGINE['vapeDragonsBlob']
UNDERHEAD_MAP = {int(k): v for k, v in ENGINE['underheadBlob'].items()}

TRAIT_NAMES = {
    0: [
        "Bubblegum", "Yellow", "Violet", "Wine", "Sky", "Void", "MuseGreen", "Ancient",
        "Punkblue", "Blush", "Offwhite",
        "Hot Rose", "Emerald", "Bright Lilac", "Neon Mint", "Paper White",
        "Radioactive Void Charcoal", "Radioactive Deep Raspberry", "Radioactive Seafoam", "Radioactive Lavender", "Radioactive Paper White",
        "Ice Prism Pink", "Violet Pink", "Violet Cyan", "Navy Pink", "Void Pink",
        "Void Blue", "Void Cyan", "Navy Blue Vignette", "Void Teal Vignette",
        "Siren", "Seafoam", "Lavender", "Storm"
    ],
    1: [
        "Alien", "Radioactive", "Gold", "Petrified", "Floral",
        "Coral", "Silver", "Prehistoric", "Bone", "Floral II"
    ],
    2: ["None", "Servant", "Death", "Royalty", "Ivory", "Clergy"],
    3: ["None", "Gold"],
    4: [
        "None", "Shades", "Glasses", "Digital", "Eye Patch", "3D Glasses", "Designer",
        "Gucci", "Louis Vuitton", "Prada", "Versace", "Dior", "Balenciaga", "Chanel", "Eye Patch II"
    ],
    5: ["None", "Woodpipe", "THC Vape"],
    6: ["None", "Oarsman's Band", "Bandana", "Dawn Pink Beanie", "Aegean Blue Beanie", "Purphat", "Golden Fleece", "Corsair"]
}

LAYER_LABELS = ["Palette", "Bones", "Cloak", "Relic", "Sight", "Artifact", "Crown"]

def get_blob_id(layer, idx):
    pos = 0
    for _ in range(layer):
        count = LAYOUT[pos]
        pos += 1 + count
    count = LAYOUT[pos]
    if idx >= count:
        return 0xFF
    return LAYOUT[pos + 1 + idx]

def decode_blob_to_pixel_grid(blob, grid, offset_x=0, offset_y=0):
    if not blob:
        return
    p = (blob[0] << 8) | blob[1]
    off = 2 + p * 4
    pixel = 0
    w = len(grid[0])
    h = len(grid)
    while off < len(blob):
        ci = (blob[off] << 8) | blob[off + 1]
        run = blob[off + 2]
        if ci != 0:
            e = 2 + (ci - 1) * 4
            r, g, b, a = blob[e], blob[e+1], blob[e+2], blob[e+3]
            for r_i in range(run):
                px = (pixel + r_i) % 24 + offset_x
                py = (pixel + r_i) // 24 + offset_y
                if 0 <= px < w and 0 <= py < h:
                    grid[py][px] = (r, g, b, a)
        pixel += run
        off += 3

def render_pixel_grid_to_svg(grid):
    h = len(grid)
    w = len(grid[0])
    rects = []
    for y in range(h):
        x = 0
        while x < w:
            px = grid[y][x]
            if px is None or px[3] == 0:
                x += 1
                continue
            run = 1
            while x + run < w and grid[y][x + run] == px:
                run += 1
            hex_color = f"{px[0]:02x}{px[1]:02x}{px[2]:02x}"
            op_str = ""
            if px[3] != 255:
                m = (px[3] * 1000) // 255
                op_str = f' fill-opacity="0.{m:03d}"'
            rects.append(f'<rect x="{x}" y="{y}" width="{run}" height="1" fill="#{hex_color}"{op_str}/>')
            x += run
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" shape-rendering="crispEdges">{"".join(rects)}</svg>'

def render_argonaut_grid(traits, is_dragons=False, size=24):
    grid = [[None for _ in range(size)] for _ in range(size)]
    paint_order = [0, 1, 4, 2, 3, 5, 6]
    vaped = (traits[5] == VAPE_MOUTH_IDX)
    
    for layer in paint_order:
        idx = traits[layer]
        blob_id = 0xFF
        if layer == 5 and vaped:
            blob_id = VAPE_DRAGONS_BLOB if is_dragons else VAPE_BLUE_BLOB
        else:
            blob_id = get_blob_id(layer, idx)
            if layer == 4 and blob_id != 0xFF and traits[6] == HEADBAND_HEAD_IDX:
                uh = UNDERHEAD_MAP.get(idx, 0)
                if uh != 0:
                    blob_id = uh
                    
        if layer == 4 and vaped:
            decode_blob_to_pixel_grid(BLOBS[VAPE_SMOKE_BLOB], grid)
            
        if blob_id != 0xFF and blob_id in BLOBS:
            decode_blob_to_pixel_grid(BLOBS[blob_id], grid)
            
    return grid

# Transform Functions
def rotate_grid(grid, angle=90):
    """Rotates grid by 90, 180, or 270 degrees clockwise"""
    h = len(grid)
    w = len(grid[0])
    if angle == 90:
        return [[grid[h - 1 - x][y] for x in range(h)] for y in range(w)]
    elif angle == 180:
        return [[grid[h - 1 - y][w - 1 - x] for x in range(w)] for y in range(h)]
    elif angle == 270:
        return [[grid[x][w - 1 - y] for x in range(h)] for y in range(w)]
    return grid

def flip_grid(grid, horizontal=True):
    """Flips grid horizontally or vertically"""
    if horizontal:
        return [row[::-1] for row in grid]
    else:
        return grid[::-1]

def crop_grid(grid, x1, y1, x2, y2):
    """Crops grid to bounding box [x1..x2, y1..y2]"""
    return [row[x1:x2+1] for row in grid[y1:y2+1]]

def scale_grid(grid, factor=2):
    """Nearest-neighbor integer scale"""
    new_grid = []
    for row in grid:
        scaled_row = []
        for px in row:
            scaled_row.extend([px] * factor)
        for _ in range(factor):
            new_grid.append(list(scaled_row))
    return new_grid

def generate_random_traits():
    bg = random.randint(0, len(TRAIT_NAMES[0]) - 1)
    body = random.randint(0, len(TRAIT_NAMES[1]) - 1)
    hoodie = 0 if random.random() < 0.6 else random.randint(1, len(TRAIT_NAMES[2]) - 1)
    neck = 1 if random.random() < 0.2 else 0
    eyes = 0 if random.random() < 0.3 else random.randint(1, len(TRAIT_NAMES[4]) - 1)
    mouth = 0 if random.random() < 0.75 else random.randint(1, len(TRAIT_NAMES[5]) - 1)
    head = 0 if random.random() < 0.4 else random.randint(1, len(TRAIT_NAMES[6]) - 1)
    return [bg, body, hoodie, neck, eyes, mouth, head]

def generate_metadata(token_id, traits, is_dragons=False, transforms=""):
    attributes = []
    for layer in range(7):
        val_name = TRAIT_NAMES[layer][traits[layer]]
        if layer == 5 and traits[5] == VAPE_MOUTH_IDX:
            val_name = "Vape (Dragon's Breath)" if is_dragons else "Vape (Blueberry Kush)"
        if val_name != "None":
            attributes.append({
                "trait_type": LAYER_LABELS[layer],
                "value": val_name
            })
    attributes.append({"trait_type": "Print", "value": "Unclaimed"})
    if transforms:
        attributes.append({"trait_type": "Transforms", "value": transforms})
    
    return {
        "name": f"Argonaut #{token_id:04d}",
        "description": "One of signed, numbered textured prints on museum board. The digital lives inside the contract. A Muse Facktory production.",
        "attributes": attributes,
        "traits_indices": traits
    }

def main():
    parser = argparse.ArgumentParser(description="Generate and edit Argonauts artworks")
    parser.add_argument("--count", type=int, default=5, help="Number of artworks to generate")
    parser.add_argument("--outdir", type=str, default="generated_output", help="Output directory")
    parser.add_argument("--rotate", type=int, choices=[0, 90, 180, 270], default=0, help="Rotate degrees clockwise")
    parser.add_argument("--flip", type=str, choices=["none", "h", "v"], default="none", help="Flip direction")
    parser.add_argument("--scale", type=int, default=1, help="Scale factor (e.g. 2 for 48x48)")
    parser.add_argument("--crop", type=str, default="", help="Crop box 'x1,y1,x2,y2' (e.g. 4,4,20,20)")
    args = parser.parse_args()
    
    os.makedirs(args.outdir, exist_ok=True)
    os.makedirs(os.path.join(args.outdir, "svg"), exist_ok=True)
    os.makedirs(os.path.join(args.outdir, "metadata"), exist_ok=True)
    
    transforms_desc = []
    if args.rotate: transforms_desc.append(f"Rotate {args.rotate}°")
    if args.flip != "none": transforms_desc.append(f"Flip {args.flip.upper()}")
    if args.scale > 1: transforms_desc.append(f"Scale {args.scale}x")
    if args.crop: transforms_desc.append(f"Crop [{args.crop}]")
    trans_str = ", ".join(transforms_desc)
    
    print(f"Generating {args.count} artworks (Transforms: {trans_str or 'None'})...")
    token_id = 10001
    
    for i in range(args.count):
        traits = generate_random_traits()
        is_drag = random.random() < 0.5
        grid = render_argonaut_grid(traits, is_drag)
        
        # Apply transforms
        if args.rotate:
            grid = rotate_grid(grid, args.rotate)
        if args.flip == "h":
            grid = flip_grid(grid, horizontal=True)
        elif args.flip == "v":
            grid = flip_grid(grid, horizontal=False)
        if args.crop:
            x1, y1, x2, y2 = map(int, args.crop.split(","))
            grid = crop_grid(grid, x1, y1, x2, y2)
        if args.scale > 1:
            grid = scale_grid(grid, args.scale)
            
        svg = render_pixel_grid_to_svg(grid)
        meta = generate_metadata(token_id, traits, is_drag, trans_str)
        
        svg_path = os.path.join(args.outdir, "svg", f"{token_id}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
            
        meta_path = os.path.join(args.outdir, "metadata", f"{token_id}.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            
        token_id += 1

    print(f"Successfully generated {args.count} transformed artworks in '{args.outdir}'!")

if __name__ == "__main__":
    main()
