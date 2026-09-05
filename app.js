/**
 * ARGOPEPEN STUDIO
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
    "Gucci", "Louis Vuitton", "Prada", "Versace", "Dior", "Balenciaga", "Chanel", "Eye Patch"
  ],
  Crown: [
    "None", "Oarsman's Band", "Bandana", "Dawn Pink Beanie", "Aegean Blue Beanie", "Purphat", "Golden Fleece", "Corsair"
  ]
};

// Canonical Underhead sight blob map when Crown == Oarsman's Band (crown_idx 1) from contract RendererV2
const CANONICAL_UNDERHEAD_MAP = {
  1: 77, // Shades
  2: 67, // Glasses
  4: 76, // Eye Patch
  5: 66, // 3D Glasses
  6: 68, // Designer
  7: 72, // Gucci
  8: 73, // Louis Vuitton
  9: 74, // Prada
  10: 75, // Versace
  11: 71, // Dior
  12: 69, // Balenciaga
  13: 70  // Chanel
};

// Offline vape flavor bitmap evaluator matching contract RendererV2.isDragonsBreath(tokenId)
let VAPE_BITMAP_BYTES = null;
function isDragonsBreath(tokenId) {
  if (!VAPE_BITMAP_BYTES && window.VAPE_FLAVOR_B64) {
    try {
      const bin = atob(window.VAPE_FLAVOR_B64);
      const b = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) b[i] = bin.charCodeAt(i);
      VAPE_BITMAP_BYTES = b;
    } catch (e) {}
  }
  if (!VAPE_BITMAP_BYTES) return false;
  const byteIdx = tokenId >> 3;
  if (byteIdx >= VAPE_BITMAP_BYTES.length) return false;
  return (VAPE_BITMAP_BYTES[byteIdx] & (0x80 >> (tokenId & 7))) !== 0;
}

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
  if (mouth_idx === 1) {
    artifactName = 'Woodpipe';
  } else if (mouth_idx === 2) {
    artifactName = isDragonsBreath(tokenId) ? "Vape (Dragon's Breath)" : "Vape (Blueberry Kush)";
  }

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

function decodeArtifactLayers(artifactName, tokenId) {
  if (!artifactName || artifactName === 'None') return { device: {}, smoke: {} };
  const nameLow = artifactName.toLowerCase();
  let device = {};
  let smoke = {};
  const isDragon = nameLow.includes('dragon') || (tokenId && isDragonsBreath(tokenId));
  if (nameLow.includes('vape') || nameLow.includes('blueberry') || nameLow.includes('thc') || nameLow.includes('kush') || nameLow.includes('breath')) {
    smoke = decodeBlob(78).pixels;
    device = isDragon ? decodeBlob(80).pixels : decodeBlob(79).pixels;
  } else if (nameLow.includes('pipe') || nameLow.includes('woodpipe')) {
    const rawPipe = decodeBlob(64).pixels;
    Object.keys(rawPipe).forEach(k => {
      const px = rawPipe[k];
      if (px.alpha < 255) {
        smoke[k] = px;
      } else {
        device[k] = px;
      }
    });
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

// Render 24x24 blob rects for on-chain Argonaut
function renderBlobRects(blob) {
  if (!blob) return '';
  const p = (blob[0] << 8) | blob[1];
  let off = 2 + p * 4;
  let pixel = 0;
  const rects = [];
  while (off < blob.length) {
    const ci = (blob[off] << 8) | blob[off + 1];
    const run = blob[off + 2];
    if (ci !== 0) {
      const e = 2 + (ci - 1) * 4;
      const r = blob[e], g = blob[e + 1], b = blob[e + 2], a = blob[e + 3];
      const hexColor = (r.toString(16).padStart(2, '0') + g.toString(16).padStart(2, '0') + b.toString(16).padStart(2, '0')).toLowerCase();
      const x = pixel % 24;
      const y = Math.floor(pixel / 24);
      let opacityStr = '';
      if (a !== 255) {
        const m = Math.floor((a * 1000) / 255);
        opacityStr = ` fill-opacity="0.${m.toString().padStart(3, '0')}"`;
      }
      rects.push(`<rect x="${x}" y="${y}" width="${run}" height="1" fill="#${hexColor}"${opacityStr}/>`);
    }
    pixel += run;
    off += 3;
  }
  return rects.join('');
}

// Generate Original On-Chain 24x24 Argonaut SVG (instant offline or live meta)
function generateOriginalTokenSVG(meta, tokenId) {
  // 1. If meta has image data URI (from RPC fetch), decode and return it
  if (meta && meta.image) {
    if (meta.image.startsWith('data:image/svg+xml;base64,')) {
      try {
        const b64 = meta.image.split('data:image/svg+xml;base64,')[1];
        return atob(b64);
      } catch (e) {}
    } else if (meta.image.startsWith('data:image/svg+xml;utf8,')) {
      return decodeURIComponent(meta.image.split('data:image/svg+xml;utf8,')[1]);
    } else if (meta.image.startsWith('<svg')) {
      return meta.image;
    }
  }

  // 2. Generate original 24x24 SVG instantly offline from indices and on-chain blobs
  const tid = tokenId || (meta && meta.name ? parseInt(meta.name.replace(/[^0-9]/g, ''), 10) : currentTokenId);
  const offline = getOfflineTokenTraits(tid);
  const indices = (meta && meta.indices) || (offline && offline.indices);
  if (!indices) return '';

  const LAYER_BACKGROUND = 0, LAYER_BODY = 1, LAYER_HOODIE = 2, LAYER_NECK = 3, LAYER_EYES = 4, LAYER_MOUTH = 5, LAYER_HEAD = 6;
  const paint = [LAYER_BACKGROUND, LAYER_BODY, LAYER_EYES, LAYER_HOODIE, LAYER_NECK, LAYER_MOUTH, LAYER_HEAD];
  const traits = [
    indices.bg_idx ?? 0,
    indices.body_idx ?? 0,
    indices.cloak_idx ?? 0,
    indices.relic_idx ?? 0,
    indices.sight_idx ?? 0,
    indices.mouth_idx ?? 0,
    indices.crown_idx ?? 0
  ];
  const isDragons = isDragonsBreath(tid) || ((meta && meta.attributes) || []).some(a => a.value && a.value.toLowerCase().includes('dragon'));
  const vaped = (traits[LAYER_MOUTH] === (window.ARGONAUTS_DATA?.vapeMouthIndex ?? 2));
  const svgBody = [];

  for (const layer of paint) {
    const idx = traits[layer];
    let blobId = 0xFF;
    if (layer === LAYER_MOUTH && vaped) {
      blobId = isDragons ? (window.ARGONAUTS_DATA?.vapeDragonsBlob ?? 80) : (window.ARGONAUTS_DATA?.vapeBlueberryBlob ?? 79);
    } else {
      blobId = getBlobId(layer, idx);
      if (layer === LAYER_EYES && blobId !== 0xFF && traits[LAYER_HEAD] === (window.ARGONAUTS_DATA?.headbandHeadIndex ?? 1)) {
        const uh = CANONICAL_UNDERHEAD_MAP[idx] || (window.UNDERHEAD_BLOB_MAP && window.UNDERHEAD_BLOB_MAP[idx]) || 0;
        if (uh !== 0) blobId = uh;
      }
    }

    if (layer === LAYER_EYES && vaped) {
      const smokeBlobId = window.ARGONAUTS_DATA?.vapeSmokeBlob ?? 78;
      if (BLOBS_MAP[smokeBlobId]) {
        svgBody.push(renderBlobRects(BLOBS_MAP[smokeBlobId]));
      }
    }

    if (blobId !== 0xFF && BLOBS_MAP[blobId]) {
      svgBody.push(renderBlobRects(BLOBS_MAP[blobId]));
    }
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" shape-rendering="crispEdges">${svgBody.join('')}</svg>`;
}

// Generate Argonaut Opepen from Token following strict contract paint order
function synthesizeOpepen(tokenId, meta) {
  const tidNum = Number(tokenId);
  const offlineMeta = getOfflineTokenTraits(tidNum);
  const resolvedMeta = meta || offlineMeta || { name: `Argonaut #${tidNum}`, attributes: [] };

  const attrMap = {};
  if (resolvedMeta && resolvedMeta.attributes) {
    resolvedMeta.attributes.forEach(a => {
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
  const ind = (resolvedMeta && resolvedMeta.indices) || (offlineMeta && offlineMeta.indices) || {};
  const bgName = attrMap['Palette'] || (ind.bg_idx !== undefined ? TRAIT_LOOKUP.Palette[ind.bg_idx] : 'Void');
  const bonesName = attrMap['Bones'] || (ind.body_idx !== undefined ? TRAIT_LOOKUP.Bones[ind.body_idx] : 'Bone');
  const cloakName = attrMap['Cloak'] || (ind.cloak_idx !== undefined ? TRAIT_LOOKUP.Cloak[ind.cloak_idx] : 'None');
  const relicName = attrMap['Relic'] || (ind.relic_idx !== undefined ? TRAIT_LOOKUP.Relic[ind.relic_idx] : 'None');
  const sightName = attrMap['Sight'] || (ind.sight_idx !== undefined ? TRAIT_LOOKUP.Sight[ind.sight_idx] : 'None');
  const crownName = attrMap['Crown'] || (ind.crown_idx !== undefined ? TRAIT_LOOKUP.Crown[ind.crown_idx] : 'None');

  let artifactName = attrMap['Artifact'];
  if (!artifactName || artifactName === 'None') {
    if (ind.mouth_idx === 1) artifactName = 'Woodpipe';
    else if (ind.mouth_idx === 2) artifactName = isDragonsBreath(tidNum) ? "Vape (Dragon's Breath)" : "Vape (Blueberry Kush)";
    else artifactName = 'None';
  }

  const bgIdx = ind.bg_idx !== undefined ? ind.bg_idx : getTraitIndex('Palette', bgName);
  const bonesIdx = ind.body_idx !== undefined ? ind.body_idx : getTraitIndex('Bones', bonesName);
  const cloakIdx = ind.cloak_idx !== undefined ? ind.cloak_idx : getTraitIndex('Cloak', cloakName);
  const relicIdx = ind.relic_idx !== undefined ? ind.relic_idx : getTraitIndex('Relic', relicName);
  const sightIdx = ind.sight_idx !== undefined ? ind.sight_idx : getTraitIndex('Sight', sightName);
  const mouthIdx = ind.mouth_idx !== undefined ? ind.mouth_idx : (artifactName.includes('Pipe') ? 1 : (artifactName.includes('Vape') ? 2 : 0));
  const crownIdx = ind.crown_idx !== undefined ? ind.crown_idx : getTraitIndex('Crown', crownName);

  // Decode layer blobs directly from on-chain layout
  const bgDecoded = decodeBlob(getBlobId(0, bgIdx));
  const bgColor = bgDecoded.palette[0] || "#141414";

  const boneDecoded = decodeBlob(getBlobId(1, bonesIdx));
  const cloakDecoded = cloakIdx > 0 ? decodeBlob(getBlobId(2, cloakIdx)) : { pixels: {} };
  const relicDecoded = relicIdx > 0 ? decodeBlob(getBlobId(3, relicIdx)) : { pixels: {} };

  let sightBlobId = sightIdx > 0 ? getBlobId(4, sightIdx) : 0xFF;
  if (crownIdx === 1 && sightIdx > 0) {
    const uh = CANONICAL_UNDERHEAD_MAP[sightIdx] || (window.UNDERHEAD_BLOB_MAP && window.UNDERHEAD_BLOB_MAP[sightIdx]) || 0;
    if (uh) sightBlobId = uh;
  }
  const sightDecoded = sightBlobId !== 0xFF ? decodeBlob(sightBlobId) : { pixels: {} };
  const { device: artifactDevicePx, smoke: artifactSmokePx } = decodeArtifactLayers(artifactName, tidNum);
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

  // Layer 5 Smoke: Vapor Smoke (rendered before eyes so it drifts behind frame)
  Object.keys(artifactSmokePx).forEach(k => {
    compositeHead[k] = artifactSmokePx[k];
  });

  // Layer 4: Sight (Eyes) - Fully visible uncropped as in original Argonaut
  Object.keys(sightDecoded.pixels).forEach(k => {
    compositeHead[k] = sightDecoded.pixels[k];
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

  // Layer 5 Device: Artifact / Mouth Device (Woodpipe, Dragon's Breath, Blueberry Kush) - Fully visible
  Object.keys(artifactDevicePx).forEach(k => {
    compositeHead[k] = artifactDevicePx[k];
  });

  // Layer 6: Crown (Head)
  Object.keys(crownDecoded.pixels).forEach(k => {
    const py = Number(k.split(',')[1]);
    if (py >= 5 && py <= 18) compositeHead[k] = crownDecoded.pixels[k];
  });

  // Build Right Head
  const headRightCells = {};

  Object.keys(compositeHead).forEach(k => {
    const [pt_x, pt_y] = k.split(',').map(Number);
    const gx_R = pt_x + 22;
    const gy_R = pt_y + 9;
    const isArtifact = Boolean(artifactDevicePx[k] || artifactSmokePx[k]);
    const isSight = Boolean(sightDecoded.pixels[k]);

    if (isArtifact || isSight) {
      // Never crop artifact or sight traits to maintain silhouette: fully visible as in original Argonaut
      if (gx_R >= 0 && gx_R < 56 && gy_R >= 0 && gy_R < 56) {
        headRightCells[`${gx_R},${gy_R}`] = Object.assign({}, compositeHead[k], {
          isArtifact: isArtifact,
          isSight: isSight
        });
      }
    } else {
      const minGy = crownDecoded.pixels[k] ? 0 : 14;
      if (gx_R >= 28 && gx_R <= 41 && gy_R >= minGy && gy_R <= 27) {
        headRightCells[`${gx_R},${gy_R}`] = compositeHead[k];
      }
    }
  });

  // Build Left Head (Anti-diagonal reflection: artifact and sight traits preserved fully without cropping, head features cropped to canonical silhouette)
  const headLeftCells = {};
  Object.keys(headRightCells).forEach(k => {
    const [gx_R, gy_R] = k.split(',').map(Number);
    const gx_L = 41 - gy_R;
    const gy_L = 55 - gx_R;
    const cell = headRightCells[k];
    if (cell.isArtifact || cell.isSight) {
      if (gx_L >= 0 && gx_L < 56 && gy_L >= 0 && gy_L < 56) {
        headLeftCells[`${gx_L},${gy_L}`] = cell;
      }
    } else {
      if (gx_L >= 14 && gx_L <= 27 && gy_L >= 14 && gy_L <= 27) {
        headLeftCells[`${gx_L},${gy_L}`] = cell;
      }
    }
  });

  // Clean merge to ensure ZERO duplicate path overlaps
  const headCombined = Object.assign({}, headLeftCells, headRightCells);

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
  const rng = seededRandom(tidNum * 31337 + 42);

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

  // Convert head cells to paths
  const headPaths = [];
  Object.keys(headCombined).forEach(k => {
    const [gx, gy] = k.split(',').map(Number);
    const { color, alpha } = headCombined[k];
    const x = gx * 10;
    const y = gy * 10;
    const opStr = alpha < 255 ? ` fill-opacity="${(alpha / 255).toFixed(3)}"` : '';
    headPaths.push(`<path d="M${x + 10} ${y}H${x}V${y + 10}H${x + 10}V${y}Z" fill="${color}"${opStr}/>`);
  });

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


function updateTraitBadgesAndInspector(tokenId, traits) {
  const badgeEl = document.getElementById('opepen-badge');
  if (badgeEl) badgeEl.textContent = `ARGOPEPEN #${tokenId.toString().padStart(4, '0')}`;
  const traitSummaryEl = document.getElementById('trait-summary-badge');
  if (traitSummaryEl) traitSummaryEl.textContent = '';

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
  const openseaLink = document.getElementById('btn-opensea');
  if (openseaLink) {
    openseaLink.href = `https://opensea.io/assets/ethereum/0x387c41b0b2f1128de44db1bcf8baad085f26392c/${tokenId}`;
    openseaLink.title = `View Argonaut #${tokenId} on OpenSea`;
  }
}

// Render Opepen to UI
async function loadToken(tokenId) {
  currentTokenId = tokenId;
  document.getElementById('token-id-input').value = tokenId;

  const btnGen = document.getElementById('btn-generate');
  const btnSpinner = btnGen ? btnGen.querySelector('.btn-spinner') : null;
  if (btnSpinner) btnSpinner.style.display = 'inline-block';

  // Update active pill
  document.querySelectorAll('.preset-pill').forEach(pill => {
    const pid = pill.dataset.id;
    if (pid && parseInt(pid) === tokenId) {
      pill.classList.add('active');
    } else {
      pill.classList.remove('active');
    }
  });

  // 1. Instantly retrieve 100% verified on-chain traits from authoritative offline table
  let meta = getOfflineTokenTraits(tokenId);
  if (!meta) {
    try {
      meta = await fetchTokenMetadata(tokenId);
    } catch (e) {}
  }
  if (!meta) {
    meta = {
      name: `Argonaut #${tokenId.toString().padStart(4, '0')}`,
      attributes: [
        { trait_type: 'Palette', value: 'Void' },
        { trait_type: 'Bones', value: 'Bone' },
        { trait_type: 'Cloak', value: 'None' },
        { trait_type: 'Relic', value: 'None' },
        { trait_type: 'Sight', value: 'None' },
        { trait_type: 'Artifact', value: 'None' },
        { trait_type: 'Crown', value: 'None' }
      ]
    };
  }
  currentMetadata = meta;

  const { svg, traits } = synthesizeOpepen(tokenId, meta);
  currentOpepenSVG = svg;

  // Render finalized Original Argonaut and Argonaut Opepen side by side with zero flicker or pixel changes
  currentOriginalSVG = generateOriginalTokenSVG(meta, tokenId);
  if (document.getElementById('orig-svg-wrapper')) {
    document.getElementById('orig-svg-wrapper').innerHTML = currentOriginalSVG;
  }
  document.getElementById('opepen-canvas-container').innerHTML = svg;

  updateTraitBadgesAndInspector(tokenId, traits);

  if (btnSpinner) btnSpinner.style.display = 'none';
}

// 15 Curated Editions State (At least 1 from all 9 Bones traits, strictly 2 Cloaks & 13 Non-Cloaks)
let defaultRandomEditions = [];
let CURATED_BONES_CACHE = null;

function getCuratedBonesCache() {
  if (CURATED_BONES_CACHE) return CURATED_BONES_CACHE;
  const allBoneNames = ['Alien', 'Radioactive', 'Gold', 'Petrified', 'Floral', 'Coral', 'Silver', 'Prehistoric', 'Bone'];
  const byBone = {};
  for (const b of allBoneNames) {
    byBone[b] = { cloak: [], nonCloak: [] };
  }

  for (let tid = 1; tid <= 9999; tid++) {
    const meta = getOfflineTokenTraits(tid);
    if (!meta || !meta.attributes) continue;
    const bAttr = meta.attributes.find(a => a.trait_type === 'Bones');
    if (!bAttr || !byBone[bAttr.value]) continue;
    const hasCloak = meta.indices ? meta.indices.cloak_idx > 0 : false;
    if (hasCloak) {
      byBone[bAttr.value].cloak.push(tid);
    } else {
      byBone[bAttr.value].nonCloak.push(tid);
    }
  }

  CURATED_BONES_CACHE = { byBone, allBoneNames };
  return CURATED_BONES_CACHE;
}

function getRandomGalleryEditions(count = 15) {
  const { byBone, allBoneNames } = getCuratedBonesCache();
  const chosen = new Set();

  // Exactly 2 tokens out of the 15 will have cloaks
  // Pick 2 distinct bone types from those with cloak variations
  const bonesWithCloaks = ['Alien', 'Radioactive', 'Gold', 'Petrified', 'Floral', 'Silver', 'Prehistoric', 'Bone'];
  const shuffledCloakBones = [...bonesWithCloaks].sort(() => Math.random() - 0.5);
  const cloakBone1 = shuffledCloakBones[0];
  const cloakBone2 = shuffledCloakBones[1];

  // 1. Guaranteed: Pick at least 1 token from each of the 9 Bones traits
  for (const b of allBoneNames) {
    let pool;
    if (b === cloakBone1 || b === cloakBone2) {
      pool = byBone[b].cloak;
    } else {
      pool = byBone[b].nonCloak;
    }
    if (pool && pool.length > 0) {
      const tid = pool[Math.floor(Math.random() * pool.length)];
      chosen.add(tid);
    }
  }

  // 2. Fill remaining slots up to count (15) with NON-CLOAK tokens across all bones
  const nonCloakPool = [];
  for (const b of allBoneNames) {
    nonCloakPool.push(...byBone[b].nonCloak);
  }

  let attempts = 0;
  while (chosen.size < count && attempts < 1000) {
    attempts++;
    const tid = nonCloakPool[Math.floor(Math.random() * nonCloakPool.length)];
    chosen.add(tid);
  }

  // 3. Shuffle so that all 9 bone archetypes and the 2 cloaks are naturally distributed
  const combined = Array.from(chosen).sort(() => Math.random() - 0.5);

  return combined.map(id => ({
    id,
    name: `ARGOPEPEN #${id.toString().padStart(4, '0')}`
  }));
}

function formatCardMeta(traits, query = '') {
  const parts = [];
  const cleanQ = query ? query.trim().toLowerCase().replace(/[,;+&]/g, ' ') : '';
  const qTerms = cleanQ ? cleanQ.split(/\s+/).filter(Boolean) : [];

  const allTraitEntries = [
    { type: 'Bones', val: traits.bones },
    { type: 'Cloak', val: traits.cloak },
    { type: 'Relic', val: traits.relic },
    { type: 'Crown', val: traits.crown },
    { type: 'Artifact', val: traits.artifact },
    { type: 'Sight', val: traits.sight },
    { type: 'Palette', val: traits.palette }
  ].filter(t => t.val && t.val !== 'None');

  // If there are search terms, prioritize all trait(s) that matched the query
  if (qTerms.length > 0) {
    for (const t of allTraitEntries) {
      const lower = t.val.toLowerCase();
      const norm = lower.replace(/s$/, '');
      if (qTerms.some(term => {
        const tNorm = term.replace(/s$/, '');
        return lower.includes(term) || (tNorm && norm.includes(tNorm));
      })) {
        if (!parts.includes(t.val)) parts.push(t.val);
      }
    }
  }

  // Fill in secondary info (up to max of 3 items for multi-trait searches or 2 default)
  const maxParts = Math.max(2, parts.length);
  for (const t of allTraitEntries) {
    if (parts.length >= maxParts) break;
    if (!parts.includes(t.val)) parts.push(t.val);
  }

  return parts.join(' • ');
}

function searchTokensByTrait(query, limit = 15) {
  if (!query || !query.trim()) return [];
  const cleanQ = query.trim().toLowerCase().replace(/[,;+&]/g, ' ');
  const qTerms = cleanQ.split(/\s+/).filter(Boolean);
  if (qTerms.length === 0) return [];

  // All valid traits on Argonaut NFTs:
  // Palette, Bones, Cloak, Relic, Sight, Artifact, Crown
  const activeTypes = new Set(['Bones', 'Cloak', 'Relic', 'Sight', 'Artifact', 'Crown', 'Palette']);
  const scoredResults = [];

  for (let tid = 1; tid <= 9999; tid++) {
    const meta = getOfflineTokenTraits(tid);
    if (!meta) continue;

    const traitEntries = [];
    const searchable = [];

    searchable.push(tid.toString(), '#' + tid.toString(), '#' + tid.toString().padStart(4, '0'));

    meta.attributes.forEach(a => {
      if (activeTypes.has(a.trait_type) && a.value && a.value !== 'None') {
        const valLower = a.value.toLowerCase();
        const typeLower = a.trait_type.toLowerCase();
        traitEntries.push({ type: a.trait_type, val: a.value, valLower, typeLower });
        searchable.push(valLower);
        searchable.push(typeLower);
        searchable.push(valLower + ' ' + typeLower);
        if (typeLower === 'bones') searchable.push(valLower + ' bone');
        if (typeLower === 'cloak') searchable.push(valLower + ' cloak');
        if (typeLower === 'relic') searchable.push(valLower + ' relic');
        if (typeLower === 'sight') searchable.push(valLower + ' sight');
        if (typeLower === 'crown') searchable.push(valLower + ' crown');
      }
    });

    let matchCount = 0;
    let score = 0;

    for (const term of qTerms) {
      const termNorm = term.replace(/s$/, '');
      let termMatched = false;

      // Check trait entries with prominence weights
      for (const entry of traitEntries) {
        const isMatch = entry.valLower.includes(term) ||
                        (termNorm.length > 2 && entry.valLower.includes(termNorm)) ||
                        entry.typeLower === term;
        if (isMatch) {
          termMatched = true;
          // Prominence weights
          if (entry.type === 'Bones') score += 120;
          else if (entry.type === 'Crown') score += 100;
          else if (entry.type === 'Cloak') score += 90;
          else if (entry.type === 'Sight') score += 80;
          else if (entry.type === 'Artifact') score += 70;
          else if (entry.type === 'Relic') score += 40;
          else if (entry.type === 'Palette') score += 30;

          if (entry.valLower === term) score += 50;
          break;
        }
      }

      // Check token ID match
      if (!termMatched && searchable.some(s => s === term || s === '#' + term)) {
        termMatched = true;
        score += 200;
      }

      if (termMatched) {
        matchCount++;
      }
    }

    if (matchCount > 0) {
      scoredResults.push({
        id: tid,
        name: `ARGOPEPEN #${tid.toString().padStart(4, '0')}`,
        meta,
        matchCount,
        score
      });
    }
  }

  // 1. Prioritize tokens matching ALL search terms (full multi-trait match)
  const fullMatches = scoredResults.filter(r => r.matchCount === qTerms.length);
  if (fullMatches.length > 0) {
    fullMatches.sort((a, b) => b.score - a.score || a.id - b.id);
    return fullMatches.slice(0, limit);
  }

  // 2. Otherwise sort by highest number of matching traits, then score
  scoredResults.sort((a, b) => b.matchCount - a.matchCount || b.score - a.score || a.id - b.id);
  return scoredResults.slice(0, limit);
}

function renderGallery(items, query = '') {
  const container = document.getElementById('gallery-grid');
  const countBadge = document.getElementById('gallery-count-badge');
  if (!container) return;

  if (query && items.length === 0) {
    if (countBadge) countBadge.textContent = '0 RESULTS';
    const escaped = query.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    container.innerHTML = `
      <div class="gallery-empty-state">
        <span class="empty-icon">🔍</span>
        <span class="empty-title">NO MATCHING ARGOPEPEN FOUND</span>
        <span class="empty-desc">No Argopepen found with trait matching "<code>${escaped}</code>". Try searching for traits like <em>Gold</em>, <em>Clergy</em>, <em>Alien</em>, <em>Woodpipe</em>, <em>3D Glasses</em>, or <em>Death</em>.</span>
      </div>
    `;
    return;
  }

  if (countBadge) {
    if (query) {
      countBadge.textContent = `${items.length} RESULTS`;
    } else {
      countBadge.textContent = '15 EDITIONS';
    }
  }

  container.innerHTML = items.map(item => {
    const meta = item.meta || getOfflineTokenTraits(item.id);
    const { svg, traits } = synthesizeOpepen(item.id, meta);
    const metaText = formatCardMeta(traits, query);
    return `
      <div class="gallery-card" data-id="${item.id}" onclick="loadGalleryToken(${item.id})">
        <div class="gallery-thumb">${svg}</div>
        <div class="gallery-info">
          <span class="gallery-title">${item.name}</span>
          <span class="gallery-meta">${metaText}</span>
        </div>
      </div>
    `;
  }).join('');
}

window.loadGalleryToken = function(tokenId) {
  loadToken(tokenId);
  window.scrollTo({ top: 0, behavior: 'smooth' });
};
window.loadToken = loadToken;

function populateGallery() {
  if (!defaultRandomEditions || defaultRandomEditions.length === 0) {
    defaultRandomEditions = getRandomGalleryEditions(15);
  }
  renderGallery(defaultRandomEditions);
}

// Toast Notification
function showToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.classList.remove('show');
  }, 2200);
}

// Download Artwork Helpers (SVG, PNG, JPG)
function getActiveOpepenSVG() {
  if (currentOpepenSVG) return currentOpepenSVG;
  const tid = currentTokenId || 20;
  const meta = getOfflineTokenTraits(tid);
  const { svg } = synthesizeOpepen(tid, meta);
  currentOpepenSVG = svg;
  return svg;
}

function downloadSVG() {
  const svgContent = getActiveOpepenSVG();
  if (!svgContent) {
    showToast('No artwork available to export');
    return;
  }
  const blob = new Blob([svgContent], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const tidStr = (currentTokenId || 20).toString().padStart(4, '0');
  a.download = `ARGOPEPEN_${tidStr}.svg`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1500);
  showToast(`Downloaded SVG (#${tidStr})`);
}

function fallbackDataUrl(canvas, ext, tidStr) {
  const mime = ext === 'jpg' ? 'image/jpeg' : 'image/png';
  const dataUrl = canvas.toDataURL(mime, 0.98);
  const a = document.createElement('a');
  a.href = dataUrl;
  a.download = `ARGOPEPEN_${tidStr}.${ext}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  showToast(`Downloaded HD ${ext.toUpperCase()} (#${tidStr})`);
}

function downloadRasterImage(format = 'png') {
  const svgContent = getActiveOpepenSVG();
  if (!svgContent) {
    showToast('No artwork available to export');
    return;
  }
  const tidStr = (currentTokenId || 20).toString().padStart(4, '0');
  const scale = 4; // 2240x2240 ultra high-definition crisp pixel art
  const size = 560 * scale;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    showToast('Canvas not supported');
    return;
  }
  ctx.imageSmoothingEnabled = false;

  const isJpg = (format === 'jpg' || format === 'jpeg');
  if (isJpg) {
    let bgFill = '#141414';
    const bgMatch = svgContent.match(/<path d="M560 0H0V560H560V0Z" fill="([^"]+)"/);
    if (bgMatch) bgFill = bgMatch[1];
    ctx.fillStyle = bgFill;
    ctx.fillRect(0, 0, size, size);
  }

  const svgDataUri = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgContent);
  const img = new Image();
  img.crossOrigin = 'anonymous';

  img.onload = () => {
    try {
      ctx.drawImage(img, 0, 0, size, size);
      const mime = isJpg ? 'image/jpeg' : 'image/png';
      const ext = isJpg ? 'jpg' : 'png';

      if (canvas.toBlob) {
        canvas.toBlob((blob) => {
          if (!blob) {
            fallbackDataUrl(canvas, ext, tidStr);
            return;
          }
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `ARGOPEPEN_${tidStr}.${ext}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          setTimeout(() => URL.revokeObjectURL(url), 1500);
          showToast(`Downloaded HD ${ext.toUpperCase()} (#${tidStr})`);
        }, mime, 0.98);
      } else {
        fallbackDataUrl(canvas, ext, tidStr);
      }
    } catch (err) {
      console.error('Raster export error:', err);
      showToast(`Error generating ${format.toUpperCase()}`);
    }
  };

  img.onerror = (e) => {
    console.error('Image load error for SVG rasterization:', e);
    showToast(`Failed to rasterize ${format.toUpperCase()}`);
  };

  img.src = svgDataUri;
}

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

  // Single Download button with dropdown
  const dropdown = document.getElementById('download-dropdown');
  const btnDownloadMain = document.getElementById('btn-download-main');

  if (btnDownloadMain && dropdown) {
    btnDownloadMain.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = dropdown.classList.toggle('open');
      btnDownloadMain.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
  }

  document.querySelectorAll('.download-option').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const fmt = btn.dataset.format;
      if (dropdown) {
        dropdown.classList.remove('open');
        if (btnDownloadMain) btnDownloadMain.setAttribute('aria-expanded', 'false');
      }
      if (fmt === 'svg') {
        downloadSVG();
      } else if (fmt === 'png') {
        downloadRasterImage('png');
      } else if (fmt === 'jpg') {
        downloadRasterImage('jpg');
      }
    });
  });

  // Close dropdown on outside click or Esc
  document.addEventListener('click', () => {
    if (dropdown && dropdown.classList.contains('open')) {
      dropdown.classList.remove('open');
      if (btnDownloadMain) btnDownloadMain.setAttribute('aria-expanded', 'false');
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && dropdown && dropdown.classList.contains('open')) {
      dropdown.classList.remove('open');
      if (btnDownloadMain) btnDownloadMain.setAttribute('aria-expanded', 'false');
    }
  });

  // Curated Editions Trait Search
  const searchInput = document.getElementById('gallery-trait-search');
  const btnClearSearch = document.getElementById('btn-clear-search');

  if (searchInput) {
    let searchDebounce = null;
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.trim();
      if (btnClearSearch) {
        btnClearSearch.style.display = q ? 'inline-flex' : 'none';
      }
      clearTimeout(searchDebounce);
      searchDebounce = setTimeout(() => {
        if (!q) {
          renderGallery(defaultRandomEditions);
        } else {
          const matches = searchTokensByTrait(q, 15);
          renderGallery(matches, q);
        }
      }, 70);
    });

    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        searchInput.value = '';
        if (btnClearSearch) btnClearSearch.style.display = 'none';
        renderGallery(defaultRandomEditions);
        searchInput.blur();
      }
    });
  }

  if (btnClearSearch && searchInput) {
    btnClearSearch.addEventListener('click', () => {
      searchInput.value = '';
      btnClearSearch.style.display = 'none';
      renderGallery(defaultRandomEditions);
      searchInput.focus();
    });
  }
}

// App Initialization
window.addEventListener('DOMContentLoaded', () => {
  initEngine();
  setupEventListeners();
  if (document.getElementById('cloaks-grid')) {
    populateCloaksShowcase();
  }
  populateGallery();
  loadToken(20); // Default to Token #20 (Clergy Cloak) so user immediately sees locked cloak design!
});
