/**
 * ARGONAUT × OPEPEN STUDIO
 * Minimalist Black & White On-Chain Synthesizer & Vector Renderer
 * Guarantees 100% full visibility for ALL Artifact traits:
 * - Vape (Dragon's Breath) (Blob 80 + Smoke Blob 78)
 * - Vape (Blueberry Kush) (Blob 79 + Smoke Blob 78)
 * - Woodpipe (Blob 64)
 */

// Trait category dictionaries
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
  Cloak: ["", "Servant", "Death", "Royalty", "Ivory", "Clergy"],
  Relic: ["", "Gold"],
  Sight: [
    "", "Shades", "Glasses", "Digital", "Eye Patch", "3D Glasses", "Designer",
    "Gucci", "Louis Vuitton", "Prada", "Versace", "Dior", "Balenciaga", "Chanel"
  ],
  Crown: [
    "", "Oarsman's Band", "Bandana", "Dawn Pink Beanie", "Aegean Blue Beanie", "Purphat", "Golden Fleece", "Corsair"
  ]
};

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

function decodeArtifactPixels(artifactName) {
  if (!artifactName || artifactName === 'None') return {};
  const nameLow = artifactName.toLowerCase();
  const pxMap = {};
  if (nameLow.includes('dragon')) {
    // Vape smoke (Blob 78) + Dragons breath device (Blob 80)
    const smoke = decodeBlob(78);
    const device = decodeBlob(80);
    Object.assign(pxMap, smoke.pixels, device.pixels);
  } else if (nameLow.includes('vape') || nameLow.includes('blueberry') || nameLow.includes('thc')) {
    // Vape smoke (Blob 78) + Blueberry device (Blob 79)
    const smoke = decodeBlob(78);
    const device = decodeBlob(79);
    Object.assign(pxMap, smoke.pixels, device.pixels);
  } else if (nameLow.includes('pipe') || nameLow.includes('woodpipe')) {
    // Woodpipe (Blob 64)
    const pipe = decodeBlob(64);
    Object.assign(pxMap, pipe.pixels);
  }
  return pxMap;
}

// Pseudo random generator seeded by Token ID
function seededRandom(seed) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return function() {
    return (s = s * 16807 % 2147483647) / 2147483647;
  };
}

// RPC Token Metadata Fetcher
async function fetchTokenMetadata(tokenId) {
  const rpcs = [
    'https://ethereum.publicnode.com',
    'https://1rpc.io/eth',
    'https://rpc.mevblocker.io'
  ];
  const mainContract = '0x387C41B0B2F1128dE44dB1Bcf8baad085f26392C';
  const tokenHex = tokenId.toString(16).padStart(64, '0');
  const data = '0xc87b56dd' + tokenHex; // tokenURI(uint256)

  for (const rpc of rpcs) {
    try {
      const resp = await fetch(rpc, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'User-Agent': 'ArgonautOpepen/1.0' },
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

// Generate Argonaut Opepen from Token
function synthesizeOpepen(tokenId, meta) {
  const attrMap = {};
  if (meta && meta.attributes) {
    meta.attributes.forEach(a => {
      attrMap[a.trait_type] = a.value;
    });
  }

  const bgName = attrMap['Palette'] || 'Void';
  const bonesName = attrMap['Bones'] || 'Bone';
  const sightName = attrMap['Sight'] || '';
  const crownName = attrMap['Crown'] || '';
  const cloakName = attrMap['Cloak'] || '';
  const relicName = attrMap['Relic'] || '';
  const artifactName = attrMap['Artifact'] || '';

  // 1. Get Trait Indices
  const bgIdx = getTraitIndex('Palette', bgName);
  const bonesIdx = getTraitIndex('Bones', bonesName);
  const sightIdx = getTraitIndex('Sight', sightName);
  const crownIdx = getTraitIndex('Crown', crownName);
  const cloakIdx = getTraitIndex('Cloak', cloakName);
  const relicIdx = getTraitIndex('Relic', relicName);

  // 2. Decode Blobs
  const bgDecoded = decodeBlob(getBlobId(0, bgIdx));
  const bgColor = bgDecoded.palette[0] || "#141414";

  const boneDecoded = decodeBlob(getBlobId(1, bonesIdx));
  const sightDecoded = sightIdx > 0 ? decodeBlob(getBlobId(4, sightIdx)) : { pixels: {} };
  const crownDecoded = crownIdx > 0 ? decodeBlob(getBlobId(6, crownIdx)) : { pixels: {} };
  const cloakDecoded = cloakIdx > 0 ? decodeBlob(getBlobId(2, cloakIdx)) : { pixels: {} };
  const relicDecoded = relicIdx > 0 ? decodeBlob(getBlobId(3, relicIdx)) : { pixels: {} };
  const artifactPixels = decodeArtifactPixels(artifactName);

  // 3. Composite upright head (bounded general traits to rows 5..18)
  const compositeHead = {};
  const generalLayers = [
    boneDecoded.pixels,
    sightDecoded.pixels,
    cloakDecoded.pixels,
    relicDecoded.pixels,
    crownDecoded.pixels
  ];

  generalLayers.forEach(pxMap => {
    Object.keys(pxMap).forEach(k => {
      const [px, py] = k.split(',').map(Number);
      if (py >= 5 && py <= 18) {
        compositeHead[`${px},${py}`] = pxMap[k];
      }
    });
  });

  // 4. Build Right Head (Bounded for general traits)
  const headRightCells = {};
  Object.keys(compositeHead).forEach(k => {
    const [pt_x, pt_y] = k.split(',').map(Number);
    const gx_R = pt_x + 22;
    const gy_R = pt_y + 9;
    if (gx_R >= 28 && gx_R <= 41 && gy_R >= 14 && gy_R <= 27) {
      headRightCells[`${gx_R},${gy_R}`] = compositeHead[k];
    }
  });

  // 5. Build Left Head (Anti-diagonal reflection for general traits)
  const headLeftCells = {};
  Object.keys(headRightCells).forEach(k => {
    const [gx_R, gy_R] = k.split(',').map(Number);
    const gx_L = 41 - gy_R;
    const gy_L = 55 - gx_R;
    if (gx_L >= 14 && gx_L <= 27 && gy_L >= 14 && gy_L <= 27) {
      headLeftCells[`${gx_L},${gy_L}`] = headRightCells[k];
    }
  });

  // 6. ARTIFACT TRAITS (Woodpipe, THC Vape Dragon's Breath, Blueberry Kush, Smoke): 100% UNCROPPED!
  Object.keys(artifactPixels).forEach(k => {
    const [pt_x, pt_y] = k.split(',').map(Number);
    // Right Head (Full uncropped placement)
    const gx_R = pt_x + 22;
    const gy_R = pt_y + 9;
    if (gx_R >= 0 && gx_R < 56 && gy_R >= 0 && gy_R < 56) {
      headRightCells[`${gx_R},${gy_R}`] = artifactPixels[k];
    }

    // Left Head (Full uncropped anti-diagonal reflection)
    const gx_L = 41 - gy_R;
    const gy_L = 55 - gx_R;
    if (gx_L >= 0 && gx_L < 56 && gy_L >= 0 && gy_L < 56) {
      headLeftCells[`${gx_L},${gy_L}`] = artifactPixels[k];
    }
  });

  // Convert cells to paths
  const headRightPaths = [];
  Object.keys(headRightCells).forEach(k => {
    const [gx, gy] = k.split(',').map(Number);
    const { color, alpha } = headRightCells[k];
    const x = gx * 10;
    const y = gy * 10;
    const opStr = alpha < 255 ? ` fill-opacity="${(alpha / 255).toFixed(3)}"` : '';
    headRightPaths.push(`<path d="M${x + 10} ${y}H${x}V${y + 10}H${x + 10}V${y}Z" fill="${color}"${opStr}/>`);
  });

  const headLeftPaths = [];
  Object.keys(headLeftCells).forEach(k => {
    const [gx, gy] = k.split(',').map(Number);
    const { color, alpha } = headLeftCells[k];
    const x = gx * 10;
    const y = gy * 10;
    const opStr = alpha < 255 ? ` fill-opacity="${(alpha / 255).toFixed(3)}"` : '';
    headLeftPaths.push(`<path d="M${x + 10} ${y}H${x}V${y + 10}H${x + 10}V${y}Z" fill="${color}"${opStr}/>`);
  });

  // 7. Body & Base Organic Sampling from on-chain bone palette
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

  const bodyPaths = [];
  CANON_BODY_TARGET.forEach(([gx, gy], i) => {
    // Avoid double-rendering if artifact overlaps
    if (headRightCells[`${gx},${gy}`] || headLeftCells[`${gx},${gy}`]) return;
    const c = shuffledPalette[i];
    const x = gx * 10;
    const y = gy * 10;
    bodyPaths.push(`<path d="M${x + 10} ${y}H${x}V${y + 10}H${x + 10}V${y}Z" fill="${c}"/>`);
  });

  const basePaths = [];
  CANON_BASE_TARGET.forEach(([gx, gy], j) => {
    if (headRightCells[`${gx},${gy}`] || headLeftCells[`${gx},${gy}`]) return;
    const c = shuffledPalette[CANON_BODY_TARGET.length + j];
    const x = gx * 10;
    y = gy * 10;
    basePaths.push(`<path d="M${x + 10} ${y}H${x}V${y + 10}H${x + 10}V${y}Z" fill="${c}"/>`);
  });

  // Assemble full 560x560 SVG
  const svg = `<svg width="560" height="560" viewBox="0 0 560 560" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M560 0H0V560H560V0Z" fill="${bgColor}"/>
${headLeftPaths.join('\n')}
${headRightPaths.join('\n')}
${bodyPaths.join('\n')}
${basePaths.join('\n')}
</svg>`;

  return {
    svg,
    traits: {
      palette: bgName,
      paletteHex: bgColor,
      bones: bonesName,
      sight: sightName || 'None',
      artifact: artifactName || 'None',
      crown: crownName || 'None',
      cloak: cloakName || 'None',
      relic: relicName || 'None'
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

  try {
    let meta = await fetchTokenMetadata(tokenId);
    if (!meta) {
      // Mock default metadata from on-chain rules if unminted or offline
      meta = {
        name: `Argonaut #${tokenId.toString().padStart(4, '0')}`,
        attributes: [
          { trait_type: 'Palette', value: 'Violet' },
          { trait_type: 'Bones', value: 'Bone' },
          { trait_type: 'Sight', value: '3D Glasses' },
          { trait_type: 'Crown', value: 'Aegean Blue Beanie' }
        ]
      };
    }
    currentMetadata = meta;

    const { svg, traits } = synthesizeOpepen(tokenId, meta);
    currentOpepenSVG = svg;
    currentOriginalSVG = generateOriginalTokenSVG(meta);

    // Update DOM Canvas
    document.getElementById('opepen-canvas-container').innerHTML = svg;
    if (currentOriginalSVG) {
      document.getElementById('orig-svg-wrapper').innerHTML = currentOriginalSVG;
    }

    // Update Header Badges
    document.getElementById('opepen-badge').textContent = `OPEPEN #${tokenId.toString().padStart(4, '0')}`;
    const artLabel = traits.artifact !== 'None' ? ` • ${traits.artifact.toUpperCase()}` : '';
    document.getElementById('trait-summary-badge').textContent = `${traits.bones} • ${traits.palette} PALETTE${artLabel}`;

    // Update Inspector Traits
    document.getElementById('meta-bones').textContent = traits.bones;
    document.getElementById('meta-palette').textContent = `${traits.palette} (${traits.paletteHex})`;
    document.getElementById('meta-sight').textContent = traits.sight;
    if (document.getElementById('meta-artifact')) {
      document.getElementById('meta-artifact').textContent = traits.artifact;
    }
    document.getElementById('meta-crown').textContent = traits.crown;
    document.getElementById('meta-cloak').textContent = traits.cloak;
    document.getElementById('meta-relic').textContent = traits.relic;

    showToast(`Synthesized Argonaut Opepen #${tokenId}`);
  } catch (err) {
    console.error(err);
    showToast(`Error synthesizing Token #${tokenId}`);
  } finally {
    btnSpinner.style.display = 'none';
  }
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
    description: `Synthesized on-chain Argonaut Opepen with uncropped Artifact traits, dual-head anti-diagonal symmetry, 380-pixel tapered torso, and zero pixel overlaps.`,
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
  const artLabel = traits.artifact !== 'None' ? ` • ${traits.artifact.toUpperCase()}` : '';
  document.getElementById('trait-summary-badge').textContent = `${traits.bones} • ${traits.palette} PALETTE${artLabel}`;

  document.getElementById('meta-bones').textContent = traits.bones;
  document.getElementById('meta-palette').textContent = `${traits.palette} (${traits.paletteHex})`;
  document.getElementById('meta-sight').textContent = traits.sight;
  if (document.getElementById('meta-artifact')) {
    document.getElementById('meta-artifact').textContent = traits.artifact;
  }
  document.getElementById('meta-crown').textContent = traits.crown;
  document.getElementById('meta-cloak').textContent = traits.cloak;
  document.getElementById('meta-relic').textContent = traits.relic;

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
  populateGallery();
  loadToken(1); // Default to Token #1
});
