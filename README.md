# ARGOPEPEN — On-Chain Identity Synthesizer

Live Website: **[https://argopepen.vercel.app](https://argopepen.vercel.app)**

## Overview
ARGOPEPEN dynamically transforms any on-chain Argonaut token (1..9999) from the Ethereum smart contract into a dual-head symmetrical Opepen artwork.

### Features
- **Live On-Chain Smart Contract Integration**: Queries the Ethereum mainnet Argonauts contract (`0x387C41B0B2F1128dE44dB1Bcf8baad085f26392C`) in real-time.
- **Contract-Accurate Layer Stacking**:
  - `Layer 0`: Palette (LAYER_BACKGROUND)
  - `Layer 1`: Bones (LAYER_BODY)
  - `Layer 2`: Cloak (LAYER_HOODIE)
  - `Layer 3`: Relic (LAYER_NECK)
  - `Layer 4`: Sight (LAYER_EYES)
  - `Layer 5`: Artifact (LAYER_MOUTH: Woodpipe / Vape Device & Smoke)
  - `Layer 6`: Crown (LAYER_HEAD)
- **Uncropped Artifact Traits**: Full visibility for Woodpipes, Vape (Dragon's Breath), Vape (Blueberry Kush), and vapor smoke plumes across both heads.
- **Zero-Overlap Vector Architecture**: High-contrast, pixel-perfect 560x560 SVGs with clean geometric layering and zero duplicate vector paths.
- **Export Formats**: Vector SVG, HD JPG (98 quality), HD PNG (2X scale), SVG Raw Code, and ERC-721 Metadata JSON.
