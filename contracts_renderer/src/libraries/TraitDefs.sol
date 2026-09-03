// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title TraitDefs — trait names for the frozen table
/// @notice Index order matches the chain manifest. Retired values keep their
///         slots so indices never shift.
library TraitDefs {
    uint8 internal constant LAYER_BACKGROUND = 0;
    uint8 internal constant LAYER_BODY = 1;
    uint8 internal constant LAYER_HOODIE = 2;
    uint8 internal constant LAYER_NECK = 3;
    uint8 internal constant LAYER_EYES = 4;
    uint8 internal constant LAYER_MOUTH = 5;
    uint8 internal constant LAYER_HEAD = 6;

    function layerLabel(uint8 layer) internal pure returns (string memory) {
        if (layer == LAYER_BACKGROUND) return "Palette";
        if (layer == LAYER_BODY) return "Bones";
        if (layer == LAYER_HOODIE) return "Cloak";
        if (layer == LAYER_NECK) return "Relic";
        if (layer == LAYER_EYES) return "Sight";
        if (layer == LAYER_MOUTH) return "Artifact";
        if (layer == LAYER_HEAD) return "Crown";
        revert("bad layer");
    }

    function itemName(uint8 layer, uint8 item) internal pure returns (string memory) {
        if (layer == LAYER_BACKGROUND) return _bg(item);
        if (layer == LAYER_BODY) return _body(item);
        if (layer == LAYER_HOODIE) return _hoodie(item);
        if (layer == LAYER_NECK) return _neck(item);
        if (layer == LAYER_EYES) return _eyes(item);
        if (layer == LAYER_MOUTH) return _mouth(item);
        if (layer == LAYER_HEAD) return _head(item);
        revert("bad layer");
    }

    function _bg(uint8 i) private pure returns (string memory) {
        string[34] memory n = [
            "Bubblegum", "Yellow", "Violet", "Wine", "Sky", "Void", "MuseGreen", "Ancient",
            "Punkblue", "Blush", "Offwhite",
            "Hot Rose", "Emerald", "Bright Lilac", "Neon Mint", "Paper White",
            "Radioactive Void Charcoal", "Radioactive Deep Raspberry", "Radioactive Seafoam", "Radioactive Lavender", "Radioactive Paper White",
            "Ice Prism Pink", "Violet Pink", "Violet Cyan", "Navy Pink", "Void Pink",
            "Void Blue", "Void Cyan", "Navy Blue Vignette", "Void Teal Vignette",
            "Siren", "Seafoam", "Lavender", "Storm"
        ];
        return n[i];
    }

    function _body(uint8 i) private pure returns (string memory) {
        string[10] memory n = [
            "Alien", "Radioactive", "Gold", "Petrified", "Floral",
            "Coral", "Silver", "Prehistoric", "Bone", "Floral"
        ];
        return n[i];
    }

    function _hoodie(uint8 i) private pure returns (string memory) {
        string[6] memory n = ["", "Servant", "Death", "Royalty", "Ivory", "Clergy"];
        return n[i];
    }

    function _neck(uint8 i) private pure returns (string memory) {
        string[2] memory n = ["", "Gold"];
        return n[i];
    }

    function _eyes(uint8 i) private pure returns (string memory) {
        string[15] memory n = [
            "", "Shades", "Glasses", "Digital", "Eye Patch", "3D Glasses", "Designer",
            "Gucci", "Louis Vuitton", "Prada", "Versace", "Dior", "Balenciaga", "Chanel", "Eye Patch"
        ];
        return n[i];
    }

    function _mouth(uint8 i) private pure returns (string memory) {
        string[3] memory n = ["", "Woodpipe", "THC Vape"];
        return n[i];
    }

    function _head(uint8 i) private pure returns (string memory) {
        string[8] memory n = ["", "Oarsman's Band", "Bandana", "Dawn Pink Beanie", "Aegean Blue Beanie", "Purphat", "Golden Fleece", "Corsair"];
        return n[i];
    }
}
