// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {Ownable2Step} from "@openzeppelin/contracts/access/Ownable2Step.sol";
import {Base64} from "@openzeppelin/contracts/utils/Base64.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";
import {SSTORE2} from "./libraries/SSTORE2.sol";
import {TraitDefs} from "./libraries/TraitDefs.sol";

/// @title ArgonautsRendererV2 — the trait-fix amendment
/// @notice Same blob format and paint order as v1. Two additions: the eleven
///         corrected sprites are baked into the blobs, and the THC Vape forks
///         into two flavors — a per-token bitmap picks the device, and the
///         vapor renders on its own sub-layer beneath the eyes. The frozen
///         trait table and its commitment are untouched; the table never
///         changed, the lens did.
contract ArgonautsRendererV2 is Ownable2Step {
    using Strings for uint256;

    /// @dev SSTORE2 pointers, canonical blob order (tools/build_art_v2.py)
    address[] public blobs;

    /// @dev per layer: [count 1B][blob id 1B per table index]; 0xFF = none
    bytes public layout;
    address internal variancePtr;

    /// @dev eyes index -> underhead blob id, used when the head is the headband
    mapping(uint8 => uint8) public underheadBlob;
    uint8 public headbandHeadIndex;
    bool public locked;

    /// @dev the mouth table index the vape occupies (2 in the frozen table)
    uint8 public vapeMouthIndex;
    uint8 public vapeSmokeBlob;
    uint8 public vapeBlueberryBlob;
    uint8 public vapeDragonsBlob;
    /// @dev 1 bit per token id, big-endian within the byte; set = Dragon's Breath
    address internal vapeFlavorPtr;
    bool public vapeSet;

    constructor() Ownable(msg.sender) {}

    // ── setup (before lock) ──

    function appendBlobs(bytes[] calldata data) external onlyOwner {
        require(!locked, "locked");
        for (uint256 i = 0; i < data.length; i++) {
            blobs.push(SSTORE2.write(data[i]));
        }
    }

    function setLayout(bytes calldata l, bytes calldata underheadPairs, uint8 headbandIdx)
        external
        onlyOwner
    {
        require(!locked, "locked");
        layout = l;
        headbandHeadIndex = headbandIdx;
        for (uint256 i = 0; i < underheadPairs.length; i += 2) {
            underheadBlob[uint8(underheadPairs[i])] = uint8(underheadPairs[i + 1]);
        }
    }

    function setVariance(bytes calldata v) external onlyOwner {
        require(!locked, "locked");
        variancePtr = SSTORE2.write(v);
    }

    function setVape(uint8 mouthIdx, uint8 smokeId, uint8 blueId, uint8 greenId, bytes calldata flavors)
        external
        onlyOwner
    {
        require(!locked, "locked");
        vapeMouthIndex = mouthIdx;
        vapeSmokeBlob = smokeId;
        vapeBlueberryBlob = blueId;
        vapeDragonsBlob = greenId;
        vapeFlavorPtr = SSTORE2.write(flavors);
        vapeSet = true;
    }

    function lockRenderer() external onlyOwner {
        require(blobs.length > 0 && layout.length > 0 && vapeSet, "not configured");
        locked = true;
    }

    function blobCount() external view returns (uint256) {
        return blobs.length;
    }

    function isDragonsBreath(uint256 tokenId) public view returns (bool) {
        bytes memory f = SSTORE2.read(vapeFlavorPtr);
        uint256 byteIdx = tokenId >> 3;
        if (byteIdx >= f.length) return false;
        return uint8(f[byteIdx]) & (0x80 >> (tokenId & 7)) != 0;
    }

    // ── rendering ──

    function _blobId(uint8 layer, uint8 idx) internal view returns (uint8) {
        bytes memory l = layout;
        uint256 pos = 0;
        for (uint8 c = 0; c < layer; c++) {
            pos += 1 + uint8(l[pos]);
        }
        require(idx < uint8(l[pos]), "trait index out of range");
        return uint8(l[pos + 1 + idx]);
    }

    function render(uint8[7] memory t) public view returns (string memory) {
        return _render(t, 0, false);
    }

    function renderSeeded(uint8[7] memory t, uint256 tokenId) external view returns (string memory) {
        return _render(t, tokenId, true);
    }

    function _mb32(uint32 a) internal pure returns (uint32, uint32) {
        unchecked {
            a += 0x6D2B79F5;
            uint32 x = a;
            x = (x ^ (x >> 15)) * (x | 1);
            x = ((x + ((x ^ (x >> 7)) * (x | 61))) ^ x);
            return (a, x ^ (x >> 14));
        }
    }

    function _marks(uint256 tokenId, uint8 bodyIdx) internal view returns (bytes memory out) {
        if (variancePtr == address(0)) return out;
        bytes memory v = SSTORE2.read(variancePtr);
        uint256 off = 1;
        for (uint8 b = 0; b < bodyIdx; b++) {
            off += 1 + uint256(uint8(v[off])) * 2;
        }
        uint256 n = uint8(v[off]);
        if (n < 9) return out;
        uint256 tblOff = off + 1;
        // forge-lint: disable-next-line(unsafe-typecast)
        uint32 a = uint32(tokenId);
        uint32 r;
        uint256[3] memory picked;
        for (uint256 mk = 0; mk < 3; mk++) {
            uint256 ci;
            while (true) {
                (a, r) = _mb32(a);
                ci = (uint256(r) * n) >> 32;
                bool clash = false;
                for (uint256 j = 0; j < mk; j++) {
                    if (picked[j] == ci) { clash = true; break; }
                }
                if (!clash) break;
            }
            picked[mk] = ci;
            uint8 mx = uint8(v[tblOff + ci * 2]);
            uint8 my = uint8(v[tblOff + ci * 2 + 1]);
            out = bytes.concat(
                out,
                '<rect x="',
                bytes(uint256(mx).toString()),
                '" y="',
                bytes(uint256(my).toString()),
                mk < 2
                    ? bytes('" width="1" height="1" fill="#000000" fill-opacity="0.14"/>')
                    : bytes('" width="1" height="1" fill="#ffffff" fill-opacity="0.11"/>')
            );
        }
    }

    function _render(uint8[7] memory t, uint256 tokenId, bool seeded) internal view returns (string memory) {
        // paint order mirrors the site's drawCard: background, body, eyes
        // (underhead-swapped beneath the headband), hoodie, neck, mouth, head.
        // The vape's vapor is spliced in before the eyes so it drifts behind
        // the frame arm; the device stays seated at the mouth layer.
        uint8[7] memory paint = [
            TraitDefs.LAYER_BACKGROUND,
            TraitDefs.LAYER_BODY,
            TraitDefs.LAYER_EYES,
            TraitDefs.LAYER_HOODIE,
            TraitDefs.LAYER_NECK,
            TraitDefs.LAYER_MOUTH,
            TraitDefs.LAYER_HEAD
        ];
        bool vaped = t[TraitDefs.LAYER_MOUTH] == vapeMouthIndex;
        bytes memory body;
        for (uint256 i = 0; i < 7; i++) {
            uint8 layer = paint[i];
            uint8 idx = t[layer];
            uint8 id;
            if (layer == TraitDefs.LAYER_MOUTH && vaped) {
                id = (seeded && isDragonsBreath(tokenId)) ? vapeDragonsBlob : vapeBlueberryBlob;
            } else {
                id = _blobId(layer, idx);
                if (
                    layer == TraitDefs.LAYER_EYES && id != 0xFF
                        && t[TraitDefs.LAYER_HEAD] == headbandHeadIndex
                ) {
                    uint8 uh = underheadBlob[idx];
                    if (uh != 0) id = uh;
                }
            }
            if (layer == TraitDefs.LAYER_EYES && vaped) {
                body = bytes.concat(body, _rects(SSTORE2.read(blobs[vapeSmokeBlob])));
            }
            if (id == 0xFF) continue;
            body = bytes.concat(body, _rects(SSTORE2.read(blobs[id])));
            if (seeded && layer == TraitDefs.LAYER_BODY) {
                body = bytes.concat(body, _marks(tokenId, idx));
            }
        }
        return string(
            bytes.concat(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" shape-rendering="crispEdges">',
                body,
                "</svg>"
            )
        );
    }

    function _rects(bytes memory blob) internal pure returns (bytes memory out) {
        uint256 p = (uint256(uint8(blob[0])) << 8) | uint8(blob[1]);
        uint256 off = 2 + p * 4;
        uint256 pixel = 0;
        while (off < blob.length) {
            uint256 ci = (uint256(uint8(blob[off])) << 8) | uint8(blob[off + 1]);
            uint256 run = uint8(blob[off + 2]);
            if (ci != 0) {
                uint256 e = 2 + (ci - 1) * 4;
                out = bytes.concat(
                    out,
                    '<rect x="',
                    bytes((pixel % 24).toString()),
                    '" y="',
                    bytes((pixel / 24).toString()),
                    '" width="',
                    bytes(run.toString()),
                    '" height="1" fill="#',
                    _hex(uint8(blob[e]), uint8(blob[e + 1]), uint8(blob[e + 2])),
                    _opacity(uint8(blob[e + 3]))
                );
            }
            pixel += run;
            off += 3;
        }
    }

    function _hex(uint8 r, uint8 g, uint8 b) internal pure returns (bytes memory) {
        bytes16 sym = "0123456789abcdef";
        return bytes.concat(
            bytes1(sym[r >> 4]), bytes1(sym[r & 15]),
            bytes1(sym[g >> 4]), bytes1(sym[g & 15]),
            bytes1(sym[b >> 4]), bytes1(sym[b & 15])
        );
    }

    function _opacity(uint8 a) internal pure returns (bytes memory) {
        if (a == 255) return bytes('"/>');
        uint256 m = (uint256(a) * 1000) / 255;
        bytes memory d = bytes(m.toString());
        while (d.length < 3) d = bytes.concat("0", d);
        return bytes.concat('" fill-opacity="0.', d, '"/>');
    }

    // ── metadata ──

    function _itemName(uint8 layer, uint8 item, uint256 tokenId) internal view returns (string memory) {
        if (layer == TraitDefs.LAYER_MOUTH && item == vapeMouthIndex) {
            return isDragonsBreath(tokenId) ? "Vape (Dragon's Breath)" : "Vape (Blueberry Kush)";
        }
        return TraitDefs.itemName(layer, item);
    }

    function tokenURI(uint256 tokenId, uint8[7] memory t, bool printed) external view returns (string memory) {
        bytes memory attrs;
        for (uint8 layer = 0; layer < 7; layer++) {
            string memory v = _itemName(layer, t[layer], tokenId);
            if (bytes(v).length == 0) continue;
            attrs = bytes.concat(
                attrs,
                attrs.length == 0 ? bytes("") : bytes(","),
                '{"trait_type":"',
                bytes(TraitDefs.layerLabel(layer)),
                '","value":"',
                bytes(v),
                '"}'
            );
        }
        attrs = bytes.concat(
            attrs,
            attrs.length == 0 ? bytes("") : bytes(","),
            '{"trait_type":"Print","value":"',
            printed ? bytes("Claimed") : bytes("Unclaimed"),
            '"}'
        );
        bytes memory num = bytes(_pad4(tokenId));
        bytes memory json = bytes.concat(
            '{"name":"Argonaut #',
            num,
            '","description":"One of 9,999 signed, numbered textured prints on museum board. The digital lives here, inside the contract, forever. A Muse Facktory production.",',
            '"attributes":[',
            attrs,
            '],"image":"data:image/svg+xml;base64,',
            bytes(Base64.encode(bytes(_render(t, tokenId, true)))),
            '"}'
        );
        return string(
            bytes.concat("data:application/json;base64,", bytes(Base64.encode(json)))
        );
    }

    function _pad4(uint256 n) internal pure returns (string memory) {
        bytes memory s = bytes(n.toString());
        while (s.length < 4) s = bytes.concat("0", s);
        return string(s);
    }
}
