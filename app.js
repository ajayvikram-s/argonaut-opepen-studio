/**
 * ARGONAUT × OPEPEN STUDIO
 * Minimalist Black & White On-Chain Synthesizer & Vector Renderer
 * Layer definitions, naming, and paint sequence are strictly identical to the Argonauts smart contract:
 * - Layer 0: Palette (LAYER_BACKGROUND)
 * - Layer 1: Bones (LAYER_BODY)
 * - Layer 2: Cloak (LAYER_HOODIE)
 * - Layer 3: Relic (LAYER_NECK)
 * - Layer 4: Sight (LAYER_EYES)
 * - Layer 5: Artifact (LAYER_MOUTH)
 * - Layer 6: Crown (LAYER_HEAD)
 *
 * Paint Stacking Order (from RendererV2.sol):
 * 1. Palette -> 2. Bones -> 3. Vapor Smoke -> 4. Sight -> 5. Cloak -> 6. Relic -> 7. Artifact Device -> 8. Crown
 */

// Trait category dictionaries matching on-chain frozen table indices
const TRAIT_LOOKUP = {
  Palette: [
    "Bubblegum", "Yellow", "Violet", "Wine", "Sky", "Void", "MuseGreen", "Ancient",
    "Punkblue", "Blush", "Offwhite",
    "Hot Rose", "Emerald", "Bright Lilac", "Neon Mint", "Paper White",
    "Radioactive Void Charcoal", "Radioactive Deep Raspberry", "Radioactive Seafoam", "Radioactive Lavender", "Radioactive Paper White",
    "Ice Prism Pink", "Violet Pink", "Violet Cyan", "Navy Pink", "Void Pink",
    "Void Blue", "Void Cyan", "Navy Blue Vignette", "Void Teal Vignette",
    "Siren", "Seafoam", "Lavender", "Storm"
  ],
  Bones: [
    "Alien", "Radioactive", "Gold", "Petrified", "Floral",
    "Coral", "Silver", "Prehistoric", "Bone", "Floral"
  ],
  Cloak: ["None", "Servant", "Death", "Royalty", "Ivory", "Clergy"],
  Relic: ["None", "Gold"],
  Sight: [
    "None", "Shades", "Glasses", "Digital", "Eye Patch", "3D Glasses", "Designer",
    "Gucci", "Louis Vuitton", "Prada", "Versace", "Dior", "Balenciaga", "Chanel"
  ],
  Crown: [
    "None", "Oarsman's Band", "Bandana", "Dawn Pink Beanie", "Aegean Blue Beanie", "Purphat", "Golden Fleece", "Corsair"
  ]
};

// Offline token traits cache for all 9,999 living Argonauts
let TOKEN_TRAITS_BYTES = null;

function getOfflineTokenTraits(tokenId) {
  if (!window.ARGONAUTS_TRAITS_B64) return null;
  if (!TOKEN_TRAITS_BYTES) {
    const binaryStr = atob(window.ARGONAUTS_TRAITS_B64);
    const len = binaryStr.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryStr.charCodeAt(i);
    }
    TOKEN_TRAITS_BYTES = bytes;
  }
  const idx = tokenId - 1;
  if (idx < 0 || idx >= 9999) return null;
  const off = idx * 7;
  const bg_idx = TOKEN_TRAITS_BYTES[off];
  const body_idx = TOKEN_TRAITS_BYTES[off + 1];
  const cloak_idx = TOKEN_TRAITS_BYTES[off + 2];
  const relic_idx = TOKEN_TRAITS_BYTES[off + 3];
  const sight_idx = TOKEN_TRAITS_BYTES[off + 4];
  const mouth_idx = TOKEN_TRAITS_BYTES[off + 5];
  const crown_idx = TOKEN_TRAITS_BYTES[off + 6];

  const palName = TRAIT_LOOKUP.Palette[bg_idx] || 'Void';
  const bonesName = TRAIT_LOOKUP.Bones[body_idx] || 'Bone';
  const cloakName = TRAIT_LOOKUP.Cloak[cloak_idx] || 'None';
  const relicName = TRAIT_LOOKUP.Relic[relic_idx] || 'None';
  const sightName = TRAIT_LOOKUP.Sight[sight_idx] || 'None';
  const crownName = TRAIT_LOOKUP.Crown[crown_idx] || 'None';

  let artifactName = 'None';
  if (mouth_idx === 1) artifactName = 'Woodpipe';
  else if (mouth_idx === 2) artifactName = 'THC Vape';

  return {
    name: `Argonaut #${tokenId.toString().padStart(4, '0')}`,
    attributes: [
      { trait_type: 'Palette', value: palName },
      { trait_type: 'Bones', value: bonesName },
      { trait_type: 'Cloak', value: cloakName },
      { trait_type: 'Relic', value: relicName },
      { trait_type: 'Sight', value: sightName },
      { trait_type: 'Artifact', value: artifactName },
      { trait_type: 'Crown', value: crownName }
    ],
    indices: { bg_idx, body_idx, cloak_idx, relic_idx, sight_idx, mouth_idx, crown_idx }
  };
}

// Canonical Tapered Silhouette Cells
const CANON_BODY_TARGET = [];
for (let gy = 28; gy <= 41; gy++) {
  for (let gx = 14; gx <= 41; gx++) {
    if (gy === 39 && (gx === 14 || gx === 41)) continue;
    if (gy === 40 && (gx <= 15 || gx >= 40)) continue;
    if (gy === 41 && (gx <= 16 || gx >= 39)) continue;
    CANON_BODY_TARGET.push([gx, gy]);
  }
}

const CANON_BASE_TARGET = [];
for (let gy = 49; gy <= 55; gy++) {
  for (let gx = 14; gx <= 41; gx++) {
    if (gy === 49 && (gx <= 16 || gx >= 39)) continue;
    if (gy === 50 && (gx <= 15 || gx >= 40)) continue;
    if (gy === 51 && (gx === 14 || gx === 41)) continue;
    CANON_BASE_TARGET.push([gx, gy]);
  }
}

// Global state
let currentTokenId = 1;
let currentMetadata = null;
let currentOpepenSVG = "";
let currentOriginalSVG = "";
let isGridVisible = false;
let isSplitVisible = false;

// Engine blob cache
let BLOBS_MAP = {};
let LAYOUT_BYTES = [];

function initEngine() {
  if (!window.ARGONAUTS_DATA) return;
  const data = window.ARGONAUTS_DATA;
  if (data.blobs) {
    data.blobs.forEach(b => {
      BLOBS_MAP[b.index] = hexToBytes(b.hex);
    });
  }
  if (data.layout_hex) {
    LAYOUT_BYTES = hexToBytes(data.layout_hex);
  }
}

function hexToBytes(hex) {
  const bytes = [];
  for (let c = 0; c < hex.length; c += 2) {
    bytes.push(parseInt(hex.substr(c, 2), 16));
  }
  return bytes;
}

function getBlobId(layer, idx) {
  if (!LAYOUT_BYTES.length) return 0xFF;
  let pos = 0;
  for (let i = 0; i < layer; i++) {
    const count = LAYOUT_BYTES[pos];
    pos += 1 + count;
  }
  const count = LAYOUT_BYTES[pos];
  if (idx >= count) return 0xFF;
  return LAYOUT_BYTES[pos + 1 + idx];
}

function decodeBlob(blobId) {
  if (blobId === 0xFF || !BLOBS_MAP[blobId]) return { pixels: {}, palette: [] };
  const blob = BLOBS_MAP[blobId];
  const p = (blob[0] << 8) | blob[1];
  let off = 2;
  const palette = [];
  for (let i = 0; i < p; i++) {
    const r = blob[off], g = blob[off + 1], b = blob[off + 2], a = blob[off + 3];
    const hex = "#" + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase();
    palette.push({ hex, alpha: a });
    off += 4;
  }

  const pixels = {};
  let pixel = 0;
  while (off < blob.length) {
    const ci = (blob[off] << 8) | blob[off + 1];
    const run = blob[off + 2];
    if (ci !== 0 && ci - 1 < palette.length) {
      const col = palette[ci - 1];
      for (let r_i = 0; r_i < run; r_i++) {
        const px = (pixel + r_i) % 24;
        const py = Math.floor((pixel + r_i) / 24);
        pixels[`${px},${py}`] = { color: col.hex, alpha: col.alpha };
      }
    }
    pixel += run;
    off += 3;
  }
  return { pixels, palette: palette.map(x => x.hex) };
}

function getTraitIndex(category, name) {
  if (!name) return 0;
  const list = TRAIT_LOOKUP[category] || [];
  const idx = list.findIndex(item => item.toLowerCase() === name.toLowerCase());
  return idx >= 0 ? idx : 0;
}

function decodeArtifactLayers(artifactName) {
  if (!artifactName || artifactName === 'None') return { device: {}, smoke: {} };
  const nameLow = artifactName.toLowerCase();
  let device = {};
  let smoke = {};
  if (nameLow.includes('dragon')) {
    smoke = decodeBlob(78).pixels;
    device = decodeBlob(80).pixels;
  } else if (nameLow.includes('vape') || nameLow.includes('blueberry') || nameLow.includes('thc')) {
    smoke = decodeBlob(78).pixels;
    device = decodeBlob(79).pixels;
  } else if (nameLow.includes('pipe') || nameLow.includes('woodpipe')) {
    device = decodeBlob(64).pixels;
  }
  return { device, smoke };
}

// Pseudo random generator seeded by Token ID
function seededRandom(seed) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return function() {
    return (s = s * 16807 % 2147483647) / 2147483647;
  };
}

// RPC Token Metadata Fetcher (optional online enhancement)
async function fetchTokenMetadata(tokenId) {
  const rpcs = [
    'https://1rpc.io/eth',
    'https://rpc.mevblocker.io',
    'https://ethereum.publicnode.com'
  ];
  const mainContract = '0x387C41B0B2F1128dE44dB1Bcf8baad085f26392C';
  const tokenHex = tokenId.toString(16).padStart(64, '0');
  const data = '0xc87b56dd' + tokenHex; // tokenURI(uint256)

  for (const rpc of rpcs) {
    try {
      const resp = await fetch(rpc, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 1,
          method: 'eth_call',
          params: [{ to: mainContract, data: data }, 'latest']
        })
      });
      const resJson = await resp.json();
      if (resJson && resJson.result && resJson.result !== '0x') {
        const rawHex = resJson.result.slice(2);
        const offBytes = parseInt(rawHex.substr(0, 64), 16);
        const lenBytes = parseInt(rawHex.substr(offBytes * 2, 64), 16);
        const hexStr = rawHex.substr((offBytes + 32) * 2, lenBytes * 2);
        let str = "";
        for (let i = 0; i < hexStr.length; i += 2) {
          str += String.fromCharCode(parseInt(hexStr.substr(i, 2), 16));
        }
        if (str.startsWith('data:application/json;base64,')) {
          const b64 = str.split('data:application/json;base64,')[1];
          return JSON.parse(atob(b64));
        } else if (str.startsWith('data:application/json;utf8,')) {
          return JSON.parse(str.split('data:application/json;utf8,')[1]);
        }
      }
    } catch (e) {
      continue;
    }
  }
  return null;
}

// Generate Argonaut Opepen from Token following strict contract paint order
function synthesizeOpepen(tokenId, meta) {
  // If this token is one of the 5 canonical Smart Contract Cloak master archetypes, return the exact master SVG
  const tidNum = Number(tokenId);
  if (window.CLOAK_MASTER_SVGS && window.CLOAK_MASTER_SVGS[tidNum]) {
    const rawSvg = window.CLOAK_MASTER_SVGS[tidNum];
    const bgMatch = rawSvg.match(/fill="([^"]+)"/);
    const bgColor = bgMatch ? bgMatch[1] : "#141414";
    const resolvedMeta = meta || getOfflineTokenTraits(tidNum) || { name: `Argonaut #${tidNum}`, attributes: [] };
    const palAttr = resolvedMeta.attributes ? resolvedMeta.attributes.find(a => a.trait_type === 'Palette') : null;
    return {
      svg: rawSvg,
      metadata: resolvedMeta,
      bgColor: bgColor,
      paletteName: palAttr ? palAttr.value : 'Custom'
    };
  }

  const attrMap = {};
  if (meta && meta.attributes) {
    meta.attributes.forEach(a => {
      attrMap[a.trait_type] = a.value;
    });
  }

  // Canonical Contract Layer Indices:
  // Layer 0: Palette
  // Layer 1: Bones
  // Layer 2: Cloak
  // Layer 3: Relic
  // Layer 4: Sight
  // Layer 5: Artifact
  // Layer 6: Crown
  const bgName = attrMap['Palette'] || 'Void';
  const bonesName = attrMap['Bones'] || 'Bone';
  const cloakName = attrMap['Cloak'] || 'None';
  const relicName = attrMap['Relic'] || 'None';
  const sightName = attrMap['Sight'] || 'None';
  const artifactName = attrMap['Artifact'] || 'None';
  const crownName = attrMap['Crown'] || 'None';

  const bgIdx = meta && meta.indices ? meta.indices.bg_idx : getTraitIndex('Palette', bgName);
  const bonesIdx = meta && meta.indices ? meta.indices.body_idx : getTraitIndex('Bones', bonesName);
  const cloakIdx = meta && meta.indices ? meta.indices.cloak_idx : getTraitIndex('Cloak', cloakName);
  const relicIdx = meta && meta.indices ? meta.indices.relic_idx : getTraitIndex('Relic', relicName);
  const sightIdx = meta && meta.indices ? meta.indices.sight_idx : getTraitIndex('Sight', sightName);
  const crownIdx = meta && meta.indices ? meta.indices.crown_idx : getTraitIndex('Crown', crownName);

  // Decode layer blobs
  const bgDecoded = decodeBlob(getBlobId(0, bgIdx));
  const bgColor = bgDecoded.palette[0] || "#141414";

  const boneDecoded = decodeBlob(getBlobId(1, bonesIdx));
  const cloakDecoded = cloakIdx > 0 ? decodeBlob(getBlobId(2, cloakIdx)) : { pixels: {} };
  const relicDecoded = relicIdx > 0 ? decodeBlob(getBlobId(3, relicIdx)) : { pixels: {} };
  const sightDecoded = sightIdx > 0 ? decodeBlob(getBlobId(4, sightIdx)) : { pixels: {} };
  const { device: artifactDevicePx, smoke: artifactSmokePx } = decodeArtifactLayers(artifactName);
  const crownDecoded = crownIdx > 0 ? decodeBlob(getBlobId(6, crownIdx)) : { pixels: {} };

  // Strict Paint Stacking Sequence from RendererV2.sol:
  // 1. Bones (Body)
  // 2. Vapor Smoke
  // 3. Sight (Eyes)
  // 4. Cloak (Hoodie)
  // 5. Relic (Neck)
  // 6. Artifact Device (Mouth)
  // 7. Crown (Head)
  const compositeHead = {};

  // Layer 1: Bones (bounded to head rows 5..18)
  Object.keys(boneDecoded.pixels).forEach(k => {
    const py = Number(k.split(',')[1]);
    if (py >= 5 && py <= 18) compositeHead[k] = boneDecoded.pixels[k];
  });

  // Layer 5 Smoke: Vapor Smoke
  Object.keys(artifactSmokePx).forEach(k => {
    compositeHead[k] = artifactSmokePx[k];
  });

  // Layer 4: Sight (Eyes)
  Object.keys(sightDecoded.pixels).forEach(k => {
    const py = Number(k.split(',')[1]);
    if (py >= 5 && py <= 18) compositeHead[k] = sightDecoded.pixels[k];
  });

  // Layer 2: Cloak (Hoodie)
  Object.keys(cloakDecoded.pixels).forEach(k => {
    const py = Number(k.split(',')[1]);
    if (py >= 5 && py <= 18) compositeHead[k] = cloakDecoded.pixels[k];
  });

  // Layer 3: Relic (Neck)
  Object.keys(relicDecoded.pixels).forEach(k => {
    const py = Number(k.split(',')[1]);
    if (py >= 5 && py <= 18) compositeHead[k] = relicDecoded.pixels[k];
  });

  // Layer 5 Device: Artifact / Mouth Device
  Object.keys(artifactDevicePx).forEach(k => {
    compositeHead[k] = artifactDevicePx[k];
  });

  // Layer 6: Crown (Head)
  Object.keys(crownDecoded.pixels).forEach(k => {
    const py = Number(k.split(',')[1]);
    if (py >= 5 && py <= 18) compositeHead[k] = crownDecoded.pixels[k];
  });

  // Build Right Head (with full collar drape when cloak is present)
  const headRightCells = {};
  const maxGy = cloakIdx > 0 ? 32 : 27;
  const minGx = cloakIdx > 0 ? 14 : 28;
  const minGy = cloakIdx > 0 ? 9 : 14;

  Object.keys(compositeHead).forEach(k => {
    const [pt_x, pt_y] = k.split(',').map(Number);
    const gx_R = pt_x + 22;
    const gy_R = pt_y + 9;
    const isArtifactPixel = artifactDevicePx[k] || artifactSmokePx[k];
    if (isArtifactPixel) {
      if (gx_R >= 0 && gx_R < 56 && gy_R >= 0 && gy_R < 56) {
        headRightCells[`${gx_R},${gy_R}`] = compositeHead[k];
      }
    } else {
      if (gx_R >= minGx && gx_R <= 41 && gy_R >= minGy && gy_R <= maxGy) {
        headRightCells[`${gx_R},${gy_R}`] = compositeHead[k];
      }
    }
  });

  // Build Left Head (Anti-diagonal reflection: strictly cropped to canonical silhouette gx >= 14)
  const headLeftCells = {};
  Object.keys(headRightCells).forEach(k => {
    const [gx_R, gy_R] = k.split(',').map(Number);
    const gx_L = 41 - gy_R;
    const gy_L = 55 - gx_R;
    if (gx_L >= 14 && gx_L <= 41 && gy_L >= 14 && gy_L <= 55) {
      headLeftCells[`${gx_L},${gy_L}`] = headRightCells[k];
    }
  });

  // Clean merge to ensure ZERO duplicate path overlaps
  const headCombined = Object.assign({}, headLeftCells, headRightCells);

  const headPaths = [];
  Object.keys(headCombined).forEach(k => {
    const [gx, gy] = k.split(',').map(Number);
    const { color, alpha } = headCombined[k];
    const x = gx * 10;
    const y = gy * 10;
    const opStr = alpha < 255 ? ` fill-opacity="${(alpha / 255).toFixed(3)}"` : '';
    headPaths.push(`<path d="M${x + 10} ${y}H${x}V${y + 10}H${x + 10}V${y}Z" fill="${color}"${opStr}/>`);
  });

  // Volumetric Clean-Cloth Drapery Palettes with Option 3 Dual-Wing Sweep Accents
  const CLOAK_PALETTES = {
    1: { name: "Servant", SPEC_HI: "#FFFFFF", SOFT_HI: "#E6E6E6", ROSE_HI: "#DDDDDD", MID_TONE: "#D6D3D1", BERRY_MID: "#C8C4C0", ROSE_MID: "#B8B4B0", DEEP_ROSE: "#A9A9A9", PLUM_SHD: "#979797" },
    2: { name: "Death", SPEC_HI: "#2E2F38", SOFT_HI: "#24252C", ROSE_HI: "#1E1F24", MID_TONE: "#1A1B20", BERRY_MID: "#17171B", ROSE_MID: "#131316", DEEP_ROSE: "#0D0D10", PLUM_SHD: "#09090B" },
    3: { name: "Royalty", SPEC_HI: "#5A3686", SOFT_HI: "#4A2C6E", ROSE_HI: "#432864", MID_TONE: "#3C2358", BERRY_MID: "#351E4E", ROSE_MID: "#2D1842", DEEP_ROSE: "#29173C", PLUM_SHD: "#241334" },
    4: { name: "Ivory", SPEC_HI: "#FFF9EB", SOFT_HI: "#E8E2D2", ROSE_HI: "#DDD7C7", MID_TONE: "#D1CBBB", BERRY_MID: "#C4BEAE", ROSE_MID: "#B8B2A2", DEEP_ROSE: "#B2AC9D", PLUM_SHD: "#A39D8E" },
    5: { name: "Clergy", SPEC_HI: "#A7344E", SOFT_HI: "#992F47", ROSE_HI: "#9D3049", MID_TONE: "#8C2A40", BERRY_MID: "#8F2B42", ROSE_MID: "#88283E", DEEP_ROSE: "#7E2439", PLUM_SHD: "#691C2E" }
  };

  function getVolumetricClothColor(gx, gy, cIdx) {
    const pal = CLOAK_PALETTES[cIdx] || CLOAK_PALETTES[5];

    // Option 3: Dual-Wing Drapery Sweep Accents
    if ((gy === 29 || gy === 30) && (gx === 17 || gx === 18)) return pal.SOFT_HI;
    if ((gy === 32 || gy === 33) && (gx === 18 || gx === 19)) return pal.SOFT_HI;
    if ((gy === 34 || gy === 35) && (gx === 19 || gx === 20)) return pal.SOFT_HI;
    if ((gy === 32 || gy === 33) && (gx === 27 || gx === 28)) return pal.ROSE_MID;
    if ((gy === 34 || gy === 35) && (gx === 26 || gx === 27)) return pal.ROSE_MID;

    const dist = Math.abs(gx - 13.5);
    if (gy >= 28 && gy <= 41) {
      if (gy <= 30) {
        if (dist > 9.5) return pal.PLUM_SHD;
        if (dist > 7.0) return pal.SPEC_HI;
        if (dist > 4.5) return pal.SOFT_HI;
        if (dist > 1.5) return pal.MID_TONE;
        return pal.ROSE_MID;
      } else if (gy <= 33) {
        if (dist > 11.5) return pal.PLUM_SHD;
        if (dist > 9.5) return pal.DEEP_ROSE;
        if (dist > 8.0) return pal.ROSE_MID;
        if (dist > 5.5) return pal.SOFT_HI;
        if (dist > 2.0) return pal.MID_TONE;
        return pal.BERRY_MID;
      } else if (gy <= 38) {
        if (dist > 11.5) return pal.PLUM_SHD;
        if (dist > 9.0) return pal.DEEP_ROSE;
        if (dist > 7.5) return pal.ROSE_MID;
        if (dist > 4.5) {
          if ((gy === 36 || gy === 37) && dist >= 5.5 && dist <= 7.0) return pal.SOFT_HI;
          return pal.MID_TONE;
        }
        if (dist > 1.5) return pal.MID_TONE;
        return pal.BERRY_MID;
      } else if (gy === 39) {
        if (dist > 10.5) return pal.DEEP_ROSE;
        if (dist > 8.5) return pal.ROSE_MID;
        if (dist > 1.5) return pal.MID_TONE;
        return pal.BERRY_MID;
      } else if (gy === 40) {
        if (dist > 9.5) return pal.PLUM_SHD;
        if (dist > 7.5) return pal.DEEP_ROSE;
        if (dist > 5.5) return pal.ROSE_MID;
        return pal.MID_TONE;
      } else if (gy === 41) {
        if (dist > 6.0) return pal.PLUM_SHD;
        if (dist > 3.0) return pal.DEEP_ROSE;
        return pal.ROSE_MID;
      }
    } else if (gy >= 49 && gy <= 55) {
      if (gy === 49) {
        if (dist > 7.5) return pal.DEEP_ROSE;
        if (dist > 5.0) return pal.SOFT_HI;
        if (dist > 1.5) return pal.MID_TONE;
        return pal.SOFT_HI;
      } else if (gy === 50) {
        if (dist > 9.0) return pal.DEEP_ROSE;
        if (dist > 6.5) return pal.SOFT_HI;
        return pal.MID_TONE;
      } else if (gy <= 54) {
        if (dist > 11.0) return pal.PLUM_SHD;
        if (dist > 9.0) return pal.DEEP_ROSE;
        if (dist > 7.0) return pal.ROSE_MID;
        return pal.MID_TONE;
      } else if (gy === 55) {
        if (dist > 8.0) return pal.PLUM_SHD;
        if (dist > 4.0) return pal.DEEP_ROSE;
        return pal.ROSE_MID;
      }
    }
    return pal.MID_TONE;
  }

  // Body & Base Organic Sampling from on-chain bone palette (or Volumetric Cloth when Cloak present)
  const bonePalette = boneDecoded.palette.length ? boneDecoded.palette : ["#DCD4D0", "#BDB9B8", "#8D8B8A", "#6A6866"];
  const rng = seededRandom(tokenId * 31337 + 42);

  const shuffledPalette = [];
  while (shuffledPalette.length < CANON_BODY_TARGET.length + CANON_BASE_TARGET.length + 100) {
    const tmp = [...bonePalette];
    for (let i = tmp.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [tmp[i], tmp[j]] = [tmp[j], tmp[i]];
    }
    shuffledPalette.push(...tmp);
  }

  const cloakBodyMap = (window.CLOAK_BODY_MAPS && window.CLOAK_BODY_MAPS[cloakIdx]) || null;
  const cloakNeckMap = (window.CLOAK_NECK_MAPS && window.CLOAK_NECK_MAPS[cloakIdx]) || null;

  if (cloakIdx > 0 && cloakNeckMap) {
    Object.keys(cloakNeckMap).forEach(k => {
      if (!headCombined[k]) {
        headCombined[k] = { color: cloakNeckMap[k], alpha: 255 };
      }
    });
  }

  const bodyPaths = [];
  let cIdx = 0;
  CANON_BODY_TARGET.forEach(([gx, gy]) => {
    if (headCombined[`${gx},${gy}`]) return; // Avoid duplicate overlapping pixels
    const coordKey = `${gx},${gy}`;
    const c = (cloakIdx > 0 && cloakBodyMap && cloakBodyMap[coordKey])
      ? cloakBodyMap[coordKey]
      : (cloakIdx > 0 ? getVolumetricClothColor(gx, gy, cloakIdx) : shuffledPalette[cIdx++]);
    const x = gx * 10;
    const y = gy * 10;
    bodyPaths.push(`<path d="M${x + 10} ${y}H${x}V${y + 10}H${x + 10}V${y}Z" fill="${c}"/>`);
  });

  const basePaths = [];
  CANON_BASE_TARGET.forEach(([gx, gy]) => {
    if (headCombined[`${gx},${gy}`]) return; // Avoid duplicate overlapping pixels
    const coordKey = `${gx},${gy}`;
    const c = (cloakIdx > 0 && cloakBodyMap && cloakBodyMap[coordKey])
      ? cloakBodyMap[coordKey]
      : (cloakIdx > 0 ? getVolumetricClothColor(gx, gy, cloakIdx) : shuffledPalette[cIdx++]);
    const x = gx * 10;
    const y = gy * 10;
    basePaths.push(`<path d="M${x + 10} ${y}H${x}V${y + 10}H${x + 10}V${y}Z" fill="${c}"/>`);
  });

  // Assemble full 560x560 SVG with zero overlaps
  const svg = `<svg width="560" height="560" viewBox="0 0 560 560" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M560 0H0V560H560V0Z" fill="${bgColor}"/>
${headPaths.join('\n')}
${bodyPaths.join('\n')}
${basePaths.join('\n')}
</svg>`;

  return {
    svg,
    traits: {
      palette: bgName,
      paletteHex: bgColor,
      bones: bonesName,
      cloak: cloakName || 'None',
      relic: relicName || 'None',
      sight: sightName || 'None',
      artifact: artifactName || 'None',
      crown: crownName || 'None'
    }
  };
}

// Generate Original 24x24 Token SVG
function generateOriginalTokenSVG(meta) {
  if (meta && meta.image && meta.image.startsWith('data:image/svg+xml;base64,')) {
    return atob(meta.image.split('data:image/svg+xml;base64,')[1]);
  }
  return "";
}

// Render Opepen to UI
async function loadToken(tokenId) {
  currentTokenId = tokenId;
  document.getElementById('token-id-input').value = tokenId;

  const btnGen = document.getElementById('btn-generate');
  const btnSpinner = btnGen.querySelector('.btn-spinner');
  btnSpinner.style.display = 'inline-block';

  // Update active pill
  document.querySelectorAll('.preset-pill').forEach(pill => {
    const pid = pill.dataset.id;
    if (pid && parseInt(pid) === tokenId) {
      pill.classList.add('active');
    } else {
      pill.classList.remove('active');
    }
  });

  // 1. Instantly retrieve 100% verified on-chain traits from offline table
  let meta = getOfflineTokenTraits(tokenId);
  if (!meta) {
    meta = {
      name: `Argonaut #${tokenId.toString().padStart(4, '0')}`,
      attributes: [
        { trait_type: 'Palette', value: 'Violet' },
        { trait_type: 'Bones', value: 'Bone' },
        { trait_type: 'Cloak', value: 'None' },
        { trait_type: 'Sight', value: '3D Glasses' },
        { trait_type: 'Crown', value: 'Aegean Blue Beanie' }
      ]
    };
  }
  currentMetadata = meta;

  const { svg, traits } = synthesizeOpepen(tokenId, meta);
  currentOpepenSVG = svg;

  // Render immediately to DOM
  document.getElementById('opepen-canvas-container').innerHTML = svg;

  // Update Header Badges
  document.getElementById('opepen-badge').textContent = `OPEPEN #${tokenId.toString().padStart(4, '0')}`;
  const cloakLabel = traits.cloak !== 'None' ? ` • ${traits.cloak.toUpperCase()} CLOAK` : '';
  const artLabel = traits.artifact !== 'None' ? ` • ${traits.artifact.toUpperCase()}` : '';
  document.getElementById('trait-summary-badge').textContent = `${traits.bones} • ${traits.palette} PALETTE${cloakLabel}${artLabel}`;

  // Update Inspector Traits in Canonical Contract Layer Order (0..6):
  document.getElementById('meta-palette').textContent = `${traits.palette} (${traits.paletteHex})`;
  document.getElementById('meta-bones').textContent = traits.bones;
  document.getElementById('meta-cloak').textContent = traits.cloak;
  document.getElementById('meta-relic').textContent = traits.relic;
  document.getElementById('meta-sight').textContent = traits.sight;
  if (document.getElementById('meta-artifact')) {
    document.getElementById('meta-artifact').textContent = traits.artifact;
  }
  document.getElementById('meta-crown').textContent = traits.crown;

  showToast(`Synthesized Argonaut Opepen #${tokenId}`);

  // Background fetch to load original token SVG for comparison view
  fetchTokenMetadata(tokenId).then(liveMeta => {
    if (liveMeta) {
      currentOriginalSVG = generateOriginalTokenSVG(liveMeta);
      if (currentOriginalSVG && document.getElementById('orig-svg-wrapper')) {
        document.getElementById('orig-svg-wrapper').innerHTML = currentOriginalSVG;
      }
    }
  }).catch(() => {}).finally(() => {
    btnSpinner.style.display = 'none';
  });
}

// Toast notification helper
function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 2500);
}

// Export actions
function downloadSVG() {
  if (!currentOpepenSVG) return;
  const blob = new Blob([currentOpepenSVG], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Argonaut_${currentTokenId.toString().padStart(4, '0')}_Opepen.svg`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Downloaded Vector SVG');
}

function downloadImage(type = 'jpeg', scale = 2) {
  if (!currentOpepenSVG) return;
  const canvas = document.createElement('canvas');
  const size = 560 * scale;
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;

  const img = new Image();
  const svgBlob = new Blob([currentOpepenSVG], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(svgBlob);

  img.onload = () => {
    ctx.drawImage(img, 0, 0, size, size);
    URL.revokeObjectURL(url);
    const imgUrl = canvas.toDataURL(`image/${type}`, 0.98);
    const a = document.createElement('a');
    a.href = imgUrl;
    a.download = `Argonaut_${currentTokenId.toString().padStart(4, '0')}_Opepen.${type === 'jpeg' ? 'jpg' : 'png'}`;
    a.click();
    showToast(`Downloaded HD ${type.toUpperCase()}`);
  };
  img.src = url;
}

function copySVGCode() {
  if (!currentOpepenSVG) return;
  navigator.clipboard.writeText(currentOpepenSVG).then(() => {
    showToast('Copied SVG code to clipboard!');
  });
}

function exportJSON() {
  if (!currentMetadata) return;
  const opepenMeta = {
    name: `Argonaut Opepen #${currentTokenId.toString().padStart(4, '0')}`,
    description: `Synthesized on-chain Argonaut Opepen with contract-accurate layer stacking, uncropped Artifact traits, dual-head anti-diagonal symmetry, 380-pixel tapered torso, and zero pixel overlaps.`,
    attributes: [
      ...(currentMetadata.attributes || []),
      { trait_type: "Style", value: "Argonaut Opepen" },
      { trait_type: "Silhouette", value: "Canonical Tapered (Uncropped Artifacts)" },
      { trait_type: "Dimensions", value: "560x560" }
    ]
  };
  const blob = new Blob([JSON.stringify(opepenMeta, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Argonaut_${currentTokenId.toString().padStart(4, '0')}_Opepen_metadata.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Exported Metadata JSON');
}

// 5 Smart Contract Cloaks Master Suite (Exact Canonical Master Archetypes)
const SMART_CONTRACT_CLOAKS = [
  {
    id: 125,
    name: "Servant Argonaut Opepen",
    cloak: "Servant",
    cloakIdx: 1,
    material: "Silver Grey & Charcoal Velvet",
    drape: "Authentic Master Contract Servant Cloak (564 px drape)",
    traits: { Palette: "Bubblegum", Bones: "Bone", Cloak: "Servant", Sight: "Chanel", Artifact: "THC Vape" }
  },
  {
    id: 28,
    name: "Death Argonaut Opepen",
    cloak: "Death",
    cloakIdx: 2,
    material: "Obsidian Void Velvet",
    drape: "Authentic Master Contract Death Cloak (564 px drape)",
    traits: { Palette: "Punkblue", Bones: "Floral II", Cloak: "Death", Sight: "3D Glasses", Artifact: "THC Vape" }
  },
  {
    id: 107,
    name: "Royalty Argonaut Opepen",
    cloak: "Royalty",
    cloakIdx: 3,
    material: "Imperial Tyrian Purple Velvet",
    drape: "Authentic Master Contract Royalty Cloak (564 px drape)",
    traits: { Palette: "Offwhite", Bones: "Bone", Cloak: "Royalty", Relic: "Gold", Sight: "Louis Vuitton", Artifact: "Woodpipe" }
  },
  {
    id: 18,
    name: "Ivory Argonaut Opepen",
    cloak: "Ivory",
    cloakIdx: 4,
    material: "Alabaster Silk & Ermine Weave",
    drape: "Authentic Master Contract Ivory Cloak (564 px drape)",
    traits: { Palette: "Blush", Bones: "Bone", Cloak: "Ivory", Sight: "Shades" }
  },
  {
    id: 20,
    name: "Clergy Argonaut Opepen",
    cloak: "Clergy",
    cloakIdx: 5,
    material: "Crimson Wine Velvet",
    drape: "Authentic Master Contract Clergy Cloak (cloak svg.svg)",
    traits: { Palette: "Punkblue", Bones: "Bone", Cloak: "Clergy", Relic: "Gold", Sight: "Eye Patch" }
  }
];

function populateCloaksShowcase() {
  const container = document.getElementById('cloaks-grid');
  if (!container) return;

  container.innerHTML = SMART_CONTRACT_CLOAKS.map(item => {
    const mockMeta = {
      name: item.name,
      attributes: Object.entries(item.traits).map(([k, v]) => ({ trait_type: k, value: v }))
    };
    const { svg } = synthesizeOpepen(item.id, mockMeta);
    return `
      <div class="cloak-card" data-id="${item.id}" onclick="loadCloak(${item.id})">
        <div class="cloak-card-badge">CLOAK ARCHETYPE</div>
        <div class="cloak-thumb">${svg}</div>
        <div class="cloak-info">
          <div class="cloak-header">
            <span class="cloak-name">${item.cloak}</span>
            <span class="cloak-token-tag">#${item.id}</span>
          </div>
          <span class="cloak-material">${item.material}</span>
          <span class="cloak-drape-note">${item.drape}</span>
          <button class="cloak-load-btn" onclick="event.stopPropagation(); loadCloak(${item.id});">
            <span>SYNTHESIZE ARCHETYPE</span> →
          </button>
        </div>
      </div>
    `;
  }).join('');
}

window.loadCloak = function(tokenId) {
  loadToken(tokenId);
  const stage = document.querySelector('.stage-section');
  if (stage) {
    stage.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};

// 20 Curated Editions Catalog
const CURATED_EDITIONS = [
  { id: 1, name: "Cyber Alien Opepen", bone: "Alien", pal: "Void", traits: { Palette: "Void", Bones: "Alien", Sight: "3D Glasses" } },
  { id: 2, name: "Radioactive Void Opepen", bone: "Radioactive", pal: "Charcoal", traits: { Palette: "Radioactive Void Charcoal", Bones: "Radioactive", Sight: "Digital", Artifact: "Vape (Dragon's Breath)" } },
  { id: 3, name: "Celestial Gold Opepen", bone: "Gold", pal: "Violet", traits: { Palette: "Violet", Bones: "Gold", Sight: "3D Glasses", Crown: "Golden Fleece", Artifact: "Woodpipe" } },
  { id: 4, name: "Liquid Silver Opepen", bone: "Silver", pal: "Void", traits: { Palette: "Void", Bones: "Silver", Sight: "Shades" } },
  { id: 5, name: "Abyssal Coral Opepen", bone: "Coral", pal: "Punkblue", traits: { Palette: "Punkblue", Bones: "Coral", Sight: "Designer", Artifact: "Woodpipe" } },
  { id: 6, name: "Ancient Petrified Opepen", bone: "Petrified", pal: "Storm", traits: { Palette: "Storm", Bones: "Petrified", Crown: "Purphat" } },
  { id: 7, name: "Volcanic Prehistoric", bone: "Prehistoric", pal: "Wine", traits: { Palette: "Wine", Bones: "Prehistoric", Sight: "Eye Patch", Artifact: "Vape (Dragon's Breath)" } },
  { id: 8, name: "Clergy Bone Opepen", bone: "Bone", pal: "Ancient", traits: { Palette: "Ancient", Bones: "Bone", Cloak: "Clergy", Artifact: "Vape (Blueberry Kush)" } },
  { id: 9, name: "Neon Mint Floral", bone: "Floral", pal: "Neon Mint", traits: { Palette: "Neon Mint", Bones: "Floral", Sight: "3D Glasses", Artifact: "Vape (Dragon's Breath)" } },
  { id: 10, name: "Hot Rose Alien", bone: "Alien", pal: "Hot Rose", traits: { Palette: "Hot Rose", Bones: "Alien", Sight: "Shades" } },
  { id: 11, name: "Deep Raspberry Radio", bone: "Radioactive", pal: "Raspberry", traits: { Palette: "Radioactive Deep Raspberry", Bones: "Radioactive", Sight: "Designer", Artifact: "Woodpipe" } },
  { id: 12, name: "Emerald Gold Opepen", bone: "Gold", pal: "Emerald", traits: { Palette: "Emerald", Bones: "Gold", Sight: "3D Glasses", Artifact: "Woodpipe" } },
  { id: 13, name: "Bubblegum Silver", bone: "Silver", pal: "Bubblegum", traits: { Palette: "Bubblegum", Bones: "Silver", Sight: "Glasses", Artifact: "Woodpipe" } },
  { id: 14, name: "Bright Lilac Coral", bone: "Coral", pal: "Bright Lilac", traits: { Palette: "Bright Lilac", Bones: "Coral", Crown: "Aegean Blue Beanie", Artifact: "Woodpipe" } },
  { id: 15, name: "Seafoam Alien Opepen", bone: "Alien", pal: "Seafoam", traits: { Palette: "Radioactive Seafoam", Bones: "Alien", Sight: "3D Glasses" } },
  { id: 16, name: "Wine Petrified Opepen", bone: "Petrified", pal: "Wine", traits: { Palette: "Wine", Bones: "Petrified", Sight: "Shades", Artifact: "Woodpipe" } },
  { id: 17, name: "Siren Prehistoric", bone: "Prehistoric", pal: "Siren", traits: { Palette: "Siren", Bones: "Prehistoric", Sight: "Eye Patch" } },
  { id: 18, name: "Storm Silver Opepen", bone: "Silver", pal: "Storm", traits: { Palette: "Storm", Bones: "Silver", Sight: "3D Glasses" } },
  { id: 19, name: "Void Cyan Bone", bone: "Bone", pal: "Void Cyan", traits: { Palette: "Void Cyan", Bones: "Bone", Sight: "3D Glasses" } },
  { id: 20, name: "Ancient Floral Royalty", bone: "Floral", pal: "Ancient", traits: { Palette: "Ancient", Bones: "Floral", Cloak: "Royalty" } }
];

function populateGallery() {
  const container = document.getElementById('gallery-grid');
  if (!container) return;

  container.innerHTML = CURATED_EDITIONS.map(item => {
    const mockMeta = {
      name: item.name,
      attributes: Object.entries(item.traits).map(([k, v]) => ({ trait_type: k, value: v }))
    };
    const { svg } = synthesizeOpepen(item.id, mockMeta);
    return `
      <div class="gallery-card" data-id="${item.id}" onclick="loadCurated(${item.id})">
        <div class="gallery-thumb">${svg}</div>
        <div class="gallery-info">
          <span class="gallery-title">${item.name}</span>
          <span class="gallery-meta">${item.bone} • ${item.pal}</span>
        </div>
      </div>
    `;
  }).join('');
}

window.loadCurated = function(idx) {
  const item = CURATED_EDITIONS.find(x => x.id === idx);
  if (!item) return;
  const mockMeta = {
    name: item.name,
    attributes: Object.entries(item.traits).map(([k, v]) => ({ trait_type: k, value: v }))
  };
  currentMetadata = mockMeta;
  currentTokenId = item.id;
  document.getElementById('token-id-input').value = item.id;

  const { svg, traits } = synthesizeOpepen(item.id, mockMeta);
  currentOpepenSVG = svg;

  document.getElementById('opepen-canvas-container').innerHTML = svg;
  document.getElementById('opepen-badge').textContent = `OPEPEN #${item.id.toString().padStart(4, '0')}`;
  const cloakLabel = traits.cloak !== 'None' ? ` • ${traits.cloak.toUpperCase()} CLOAK` : '';
  const artLabel = traits.artifact !== 'None' ? ` • ${traits.artifact.toUpperCase()}` : '';
  document.getElementById('trait-summary-badge').textContent = `${traits.bones} • ${traits.palette} PALETTE${cloakLabel}${artLabel}`;

  document.getElementById('meta-palette').textContent = `${traits.palette} (${traits.paletteHex})`;
  document.getElementById('meta-bones').textContent = traits.bones;
  document.getElementById('meta-cloak').textContent = traits.cloak;
  document.getElementById('meta-relic').textContent = traits.relic;
  document.getElementById('meta-sight').textContent = traits.sight;
  if (document.getElementById('meta-artifact')) {
    document.getElementById('meta-artifact').textContent = traits.artifact;
  }
  document.getElementById('meta-crown').textContent = traits.crown;

  showToast(`Loaded ${item.name}`);
};

// Event Listeners setup
function setupEventListeners() {
  document.getElementById('btn-generate').addEventListener('click', () => {
    const val = parseInt(document.getElementById('token-id-input').value, 10);
    if (!isNaN(val) && val >= 1 && val <= 9999) {
      loadToken(val);
    } else {
      showToast('Please enter a valid Token ID (1-9999)');
    }
  });

  document.getElementById('token-id-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const val = parseInt(e.target.value, 10);
      if (!isNaN(val) && val >= 1 && val <= 9999) {
        loadToken(val);
      }
    }
  });

  document.querySelectorAll('.preset-pill[data-id]').forEach(pill => {
    pill.addEventListener('click', () => {
      const id = parseInt(pill.dataset.id, 10);
      loadToken(id);
    });
  });

  document.getElementById('btn-random').addEventListener('click', () => {
    const randId = Math.floor(Math.random() * 9999) + 1;
    loadToken(randId);
  });

  document.getElementById('toggle-grid-btn').addEventListener('click', function() {
    isGridVisible = !isGridVisible;
    this.classList.toggle('active', isGridVisible);
    document.getElementById('viewport').classList.toggle('show-grid', isGridVisible);
    showToast(isGridVisible ? '10px Grid Enabled' : 'Grid Disabled');
  });

  document.getElementById('toggle-split-btn').addEventListener('click', function() {
    isSplitVisible = !isSplitVisible;
    this.classList.toggle('active', isSplitVisible);
    document.getElementById('original-token-container').style.display = isSplitVisible ? 'block' : 'none';
  });

  document.getElementById('btn-download-svg').addEventListener('click', downloadSVG);
  document.getElementById('btn-download-jpg').addEventListener('click', () => downloadImage('jpeg', 2));
  document.getElementById('btn-download-png').addEventListener('click', () => downloadImage('png', 2));
  document.getElementById('btn-copy-svg').addEventListener('click', copySVGCode);
  document.getElementById('btn-export-json').addEventListener('click', exportJSON);
}

// App Initialization
window.addEventListener('DOMContentLoaded', () => {
  initEngine();
  setupEventListeners();
  populateCloaksShowcase();
  populateGallery();
  loadToken(20); // Default to Token #20 (Clergy Cloak) so user immediately sees locked cloak design!
});
