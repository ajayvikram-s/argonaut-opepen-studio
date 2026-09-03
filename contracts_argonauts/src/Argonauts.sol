// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @artist ack.eth
/// @developer yungwknd.eth

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {Ownable2Step} from "@openzeppelin/contracts/access/Ownable2Step.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {MessageHashUtils} from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";
import {Base64} from "@openzeppelin/contracts/utils/Base64.sol";
import {SSTORE2} from "./libraries/SSTORE2.sol";

interface IRenderer {
    function tokenURI(uint256 tokenId, uint8[7] memory traits, bool printed)
        external
        view
        returns (string memory);
}

interface ISite {
    function siteHTML() external view returns (string memory);
}

/////////////////////////////////////////////////////////////////////////////////////////
//                                                                                     //
//    The Argonauts                                                                    //
//                                                    Developed by the Muse Facktory   //
//                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////
contract Argonauts is ERC721, Ownable2Step {
    // ═══════════════════════════════════════
    // CONSTANTS
    // ═══════════════════════════════════════

    uint256 public constant MAX_ID = 9999;
    /// @dev #0 is the site, not a card
    uint256 public constant SITE_TOKEN_ID = 0;
    /// @dev tokens per table chunk: 3400 * 7 = 23,800 bytes < SSTORE2 max
    uint256 public constant CHUNK_TOKENS = 3400;
    /// @dev alphacentaurikid.eth — the artist; every sale pays here
    address public constant ARTIST = 0x03ee832367E29a5CD001f65093283eabB5382B62;

    /// @dev a hand of ten at most, per transaction
    uint256 public constant MAX_PER_TX = 10;

    /// @dev voucher kind byte, so a claim digest can never pass as a sale digest
    uint8 public constant VOUCHER_CLAIM = 1;
    uint8 public constant VOUCHER_SALE = 2;

    // ═══════════════════════════════════════
    // CONFIG (owner-settable)
    // ═══════════════════════════════════════

    /// @dev id-indexed trait table, 7 bytes per id, 0xFF lead byte = not living
    address[3] public traitChunks;
    /// @dev the artist's personal reserve — never sold, never claimable
    mapping(uint256 => bool) public ownerReserved;
    /// @dev the drawable ids, big-endian uint16 each, shuffled before upload
    address public poolPointer;
    uint32 public poolTotal;
    /// @dev the deck as a bitmap, written once by setPool
    mapping(uint256 => uint256) private pooledBits;

    address public facktorySigner;
    /// @dev sale-gate hot key; address(0) = ungated
    address public saleSigner;
    /// @dev one per buyer, so each sale voucher spends exactly once
    mapping(address => uint256) public saleNonce;
    IRenderer public renderer;
    /// @dev the page, in bytecode. Serves `tokenURI(0)`.
    ISite public site;
    /// @dev #0's name and description
    string public siteName;
    string public siteDescription;
    /// @dev the official marketplace, by the artist's word; address(0) = none
    address public marketplace;
    bool public claimOpen;
    bool public saleOpen;

    /// @dev price of one Argonaut
    uint256 public price = 0.12 ether;

    // ═══════════════════════════════════════
    // SALE STATE
    // ═══════════════════════════════════════

    uint32 public poolDrawn;
    uint32 public poolPending;
    /// @dev sparse Fisher-Yates: virtual index -> (slot + 1)
    mapping(uint256 => uint256) private poolSwap;

    /// @dev one storage slot; count <= MAX_PER_TX, done = minted so far
    struct Pending {
        address to;
        uint64 blockNum;
        uint16 count;
        uint16 done;
    }

    Pending[] private queue;
    uint256 public queueHead;

    // ═══════════════════════════════════════
    // EVENTS / ERRORS
    // ═══════════════════════════════════════

    event Claimed(address indexed to, uint256 indexed tokenId);
    event SiteTokenMinted(address indexed to);
    event SiteNameSet(string name);
    event SiteDescriptionSet(string description);
    event AssignmentRequested(address indexed to, uint256 indexed requestId, uint16 count);
    event Assigned(address indexed to, uint256 indexed tokenId, uint256 indexed requestId);
    /// @dev a stale request was re-armed to a fresh seed block
    event AssignmentRearmed(uint256 indexed requestId, uint64 newBlock);
    /// @dev a bought-and-named id: part of a purchase, chosen not drawn
    event Picked(address indexed to, uint256 indexed tokenId);
    event MarketplaceSet(address indexed marketplace);
    /// @dev a pooled id already existed at draw time: a partition violation
    event DrawSkipped(uint256 indexed tokenId);
    /// @dev a paid-for token the deck could not deal; the shop owes the buyer
    event AssignmentUnfilled(address indexed to, uint256 indexed requestId, uint256 index);
    event ArtistSigned(address indexed artist, string signature);

    // ERC-4906
    event MetadataUpdate(uint256 _tokenId);
    event BatchMetadataUpdate(uint256 _fromTokenId, uint256 _toTokenId);

    error ClaimsClosed();
    error SaleClosed();
    error NotLivingToken();
    error BadVoucher();
    error OwnerReservedToken();
    error NotOwnerReserved();
    error NotTheArtist();
    error AlreadySigned();
    error SiteNotSet();
    error BadMetadataString();
    error WrongPayment();
    error BadCount();
    error PoolExhausted();
    error PaymentFailed();
    error BadSaleVoucher();
    error SaleVoucherExpired();
    error TableNotSet();
    error TableFrozen();
    error PoolAlreadySet();
    error PoolNotSet();
    /// @dev the deck was refused: an id is 0, out of range, retired or repeated
    error BadPool(uint256 id);
    /// @dev the partition, enforced: only the draw may mint a pooled id
    error PooledToken();
    error NotMinted();

    constructor() ERC721("Argonauts", "ARGO") Ownable(msg.sender) {
        siteName = "Argonauts: The Site";
        siteDescription = "The complete Argonauts page, stored in bytecode and served with no server"
            " anywhere. Token 0 is not an Argonaut: it is the shop, the wall, and the generator"
            " that shows them.";
    }

    // ═══════════════════════════════════════
    // SETUP (owner)
    // ═══════════════════════════════════════
    // No config lock. The table and the deck freeze each other at setPool.

    function setTraitChunk(uint256 index, bytes calldata data) external onlyOwner {
        if (poolPointer != address(0)) revert TableFrozen();
        traitChunks[index] = SSTORE2.write(data);
    }

    function setPool(bytes calldata ids) external onlyOwner {
        if (poolPointer != address(0)) revert PoolAlreadySet();
        if (traitChunks[0] == address(0) || traitChunks[1] == address(0) || traitChunks[2] == address(0)) {
            revert TableNotSet();
        }
        require(ids.length % 2 == 0, "odd pool bytes");
        require(ids.length >= 2, "empty pool");
        uint256[40] memory bits = _validatePool(ids);
        for (uint256 w = 0; w < 40; w++) {
            if (bits[w] != 0) pooledBits[w] = bits[w];
        }
        poolPointer = SSTORE2.write(ids);
        poolTotal = uint32(ids.length / 2);
    }

    function _validatePool(bytes calldata ids) internal view virtual returns (uint256[40] memory bits) {
        bytes memory table = bytes.concat(
            SSTORE2.read(traitChunks[0]), SSTORE2.read(traitChunks[1]), SSTORE2.read(traitChunks[2])
        );
        uint256 bad;
        bool fail;
        assembly ("memory-safe") {
            let n := ids.length
            let tlen := mload(table)
            let tp := add(table, 0x20)
            for { let i := 0 } lt(i, n) { i := add(i, 2) } {
                // big-endian uint16 at ids[i..i+2)
                let id := shr(240, calldataload(add(ids.offset, i)))
                if or(iszero(id), gt(id, 9999)) {
                    fail := 1
                    bad := id
                    break
                }
                // living: lead byte of the id's 7-byte row is not 0xFF, and
                // the row exists at all
                let row := mul(sub(id, 1), 7)
                if or(iszero(lt(row, tlen)), eq(byte(0, mload(add(tp, row))), 0xff)) {
                    fail := 1
                    bad := id
                    break
                }
                // once: set the bit, refuse if it was already set
                let wp := add(bits, shl(5, shr(8, id)))
                let m := shl(and(id, 0xff), 1)
                let cur := mload(wp)
                if and(cur, m) {
                    fail := 1
                    bad := id
                    break
                }
                mstore(wp, or(cur, m))
            }
        }
        if (fail) revert BadPool(bad);
    }

    function isPooled(uint256 tokenId) public view returns (bool) {
        if (tokenId > MAX_ID) return false;
        return pooledBits[tokenId >> 8] & (1 << (tokenId & 255)) != 0;
    }

    function _requireNotPooled(uint256 tokenId) internal view virtual {
        if (poolPointer == address(0)) revert PoolNotSet();
        if (isPooled(tokenId)) revert PooledToken();
    }

    function reserveOwner(uint256[] calldata ids) external onlyOwner {
        for (uint256 i = 0; i < ids.length; i++) {
            _requireNotPooled(ids[i]);
            ownerReserved[ids[i]] = true;
        }
    }

    function setSaleSigner(address s) external onlyOwner {
        saleSigner = s;
    }

    function setFacktorySigner(address s) external onlyOwner {
        facktorySigner = s;
    }

    function setRenderer(address r) external onlyOwner {
        renderer = IRenderer(r);
        emit BatchMetadataUpdate(1, MAX_ID);
    }

    function setSite(address s) external onlyOwner {
        site = ISite(s);
        emit MetadataUpdate(SITE_TOKEN_ID);
    }

    function setMarketplace(address m) external onlyOwner {
        marketplace = m;
        emit MarketplaceSet(m);
    }

    function setPrice(uint256 p) external onlyOwner {
        price = p;
    }

    function setClaimOpen(bool open) external onlyOwner {
        claimOpen = open;
    }

    function setSaleOpen(bool open) external onlyOwner {
        saleOpen = open;
    }

    // ═══════════════════════════════════════
    // THE TABLE
    // ═══════════════════════════════════════

    function traitsOf(uint256 tokenId) public view returns (uint8[7] memory t) {
        if (tokenId == 0 || tokenId > MAX_ID) revert NotLivingToken();
        uint256 index = tokenId - 1;
        uint256 chunk = index / CHUNK_TOKENS;
        uint256 offset = (index % CHUNK_TOKENS) * 7;
        bytes memory b = SSTORE2.read(traitChunks[chunk], offset, offset + 7);
        if (uint8(b[0]) == 0xFF) revert NotLivingToken();
        for (uint256 i = 0; i < 7; i++) {
            t[i] = uint8(b[i]);
        }
    }

    function isLiving(uint256 tokenId) public view returns (bool) {
        if (tokenId == 0 || tokenId > MAX_ID) return false;
        uint256 index = tokenId - 1;
        uint256 chunk = index / CHUNK_TOKENS;
        uint256 offset = (index % CHUNK_TOKENS) * 7;
        bytes memory b = SSTORE2.read(traitChunks[chunk], offset, offset + 1);
        return uint8(b[0]) != 0xFF;
    }

    // ═══════════════════════════════════════
    // THE CLAIM — the voucher door
    // ═══════════════════════════════════════

    function claim(uint256 tokenId, address to, bytes calldata sig) external {
        if (!claimOpen) revert ClaimsClosed();
        if (ownerReserved[tokenId]) revert OwnerReservedToken();
        _requireNotPooled(tokenId); // a pooled id is the sale's, whatever was signed
        bytes32 digest = MessageHashUtils.toEthSignedMessageHash(
            keccak256(
                abi.encodePacked("ARGONAUTS", VOUCHER_CLAIM, block.chainid, address(this), tokenId, to)
            )
        );
        if (ECDSA.recover(digest, sig) != facktorySigner) revert BadVoucher();
        _mint(to, tokenId); // reverts unless tokenId is unminted; traitsOf reverts below if not living
        traitsOf(tokenId); // a retired number can never be claimed, even with a signature
        emit Claimed(to, tokenId);
    }

    // ═══════════════════════════════════════
    // THE PUBLIC SALE — the pool door
    // ═══════════════════════════════════════

    function mintPublic(uint256 count, uint256 deadline, bytes calldata sig) external payable {
        _buy(count, new uint256[](0), deadline, sig);
    }

    function mintPublic(uint256 count, uint256[] calldata picks, uint256 deadline, bytes calldata sig)
        external
        payable
    {
        _buy(count, picks, deadline, sig);
    }

    function _buy(uint256 count, uint256[] memory picks, uint256 deadline, bytes calldata sig) internal {
        if (!saleOpen) revert SaleClosed();
        uint256 total = count + picks.length;
        if (total == 0 || total > MAX_PER_TX) revert BadCount();
        if (msg.value != total * price) revert WrongPayment();
        _spendSaleVoucher(count, picks, deadline, sig);
        // reveal up to `total` earlier tokens first; the frontend supplies
        // base + total * PER_MINT as the gas limit
        _reveal(total);
        if (count > 0) {
            // forge-lint: disable-next-line(unsafe-typecast)
            _requestAssignment(msg.sender, uint16(count));
        }
        for (uint256 i = 0; i < picks.length; i++) {
            uint256 id = picks[i];
            if (ownerReserved[id]) revert OwnerReservedToken();
            _requireNotPooled(id);
            _mint(msg.sender, id); // reverts if already minted
            traitsOf(id); // a retired number cannot be picked, even signed
            emit Picked(msg.sender, id);
        }
        // straight to the artist, after every state change
        (bool ok,) = ARTIST.call{value: msg.value}("");
        if (!ok) revert PaymentFailed();
    }

    function _spendSaleVoucher(uint256 count, uint256[] memory picks, uint256 deadline, bytes calldata sig)
        internal
    {
        address gate = saleSigner;
        if (gate == address(0)) {
            if (picks.length != 0) revert BadSaleVoucher();
            return;
        }
        if (block.timestamp > deadline) revert SaleVoucherExpired();
        uint256 nonce = saleNonce[msg.sender];
        bytes32 digest = MessageHashUtils.toEthSignedMessageHash(
            keccak256(
                abi.encodePacked(
                    "ARGONAUTS",
                    VOUCHER_SALE,
                    block.chainid,
                    address(this),
                    msg.sender,
                    count,
                    keccak256(abi.encodePacked(picks)),
                    nonce,
                    deadline
                )
            )
        );
        // tryRecover: a malformed signature is BadSaleVoucher, not a panic
        (address signed, ECDSA.RecoverError err,) = ECDSA.tryRecover(digest, sig);
        if (err != ECDSA.RecoverError.NoError || signed != gate) revert BadSaleVoucher();
        saleNonce[msg.sender] = nonce + 1;
    }

    function _requestAssignment(address to, uint16 count) internal {
        if (poolDrawn + poolPending + count > poolTotal) revert PoolExhausted();
        poolPending += count;
        queue.push(Pending({to: to, blockNum: uint64(block.number), count: count, done: 0}));
        emit AssignmentRequested(to, queue.length - 1, count);
    }

    function finalize(uint256 maxTokens) external {
        _reveal(maxTokens);
    }

    function _reveal(uint256 budget) internal {
        uint256 head = queueHead;
        uint256 len = queue.length;
        uint256 processed;
        while (head < len && processed < budget) {
            Pending storage p = queue[head];
            if (p.blockNum >= block.number) break;
            bytes32 bh = blockhash(p.blockNum);
            if (bh == bytes32(0)) {
                // stale: seed block out of the 256-block window. Re-arm to a
                // fresh block rather than let the finalizer pick the seed.
                p.blockNum = uint64(block.number);
                emit AssignmentRearmed(head, uint64(block.number));
                break;
            }
            bytes32 base = keccak256(abi.encodePacked(bh, head));
            uint256 i = p.done;
            uint256 count = p.count;
            while (i < count && processed < budget) {
                uint256 seed = uint256(keccak256(abi.encodePacked(base, i)));
                uint256 id = _drawMintableId(seed);
                if (id == 0) {
                    // nothing left to deal: close the token rather than revert,
                    // which would be permanent at this queue head
                    emit AssignmentUnfilled(p.to, head, i);
                } else {
                    // _mint, not _safeMint: a reverting receiver must not brick the queue
                    _mint(p.to, id);
                    emit Assigned(p.to, id, head);
                }
                i++;
                processed++;
            }
            // forge-lint: disable-next-line(unsafe-typecast)
            p.done = uint16(i);
            if (i == count) {
                // forge-lint: disable-next-line(unsafe-typecast)
                poolPending -= uint32(count);
                head++;
            }
        }
        queueHead = head;
    }

    function pendingRequests() external view returns (uint256) {
        return queue.length - queueHead;
    }

    function _drawMintableId(uint256 seed) internal returns (uint256 id) {
        for (uint256 tries = 0; tries < 8; tries++) {
            if (poolDrawn >= poolTotal) return 0;
            id = _drawId(seed);
            if (_ownerOf(id) == address(0) && isLiving(id)) return id;
            emit DrawSkipped(id);
            seed = uint256(keccak256(abi.encodePacked(seed, tries)));
        }
        return 0;
    }

    function _drawId(uint256 seed) internal returns (uint256) {
        uint256 remaining = poolTotal - poolDrawn;
        uint256 j = seed % remaining;
        uint256 slot = poolSwap[j] == 0 ? j : poolSwap[j] - 1;
        uint256 last = remaining - 1;
        uint256 lastSlot = poolSwap[last] == 0 ? last : poolSwap[last] - 1;
        poolSwap[j] = lastSlot + 1;
        delete poolSwap[last];
        poolDrawn++;
        return _poolIdAt(slot);
    }

    function _poolIdAt(uint256 slot) internal view returns (uint256) {
        bytes memory b = SSTORE2.read(poolPointer, slot * 2, slot * 2 + 2);
        return (uint256(uint8(b[0])) << 8) | uint256(uint8(b[1]));
    }

    // ═══════════════════════════════════════
    // THE ARTIST'S SIGNATURE
    // ═══════════════════════════════════════
    // signed once, from the artist's own wallet

    string public artistSignature;

    function signAsArtist(string calldata message) external {
        if (msg.sender != ARTIST) revert NotTheArtist();
        if (bytes(artistSignature).length != 0) revert AlreadySigned();
        artistSignature = message;
        emit ArtistSigned(msg.sender, message);
    }

    // ═══════════════════════════════════════
    // THE PRINT REGISTRY
    // ═══════════════════════════════════════
    // opt-in, one-way, at most one print per card

    mapping(uint256 => bool) public printExists;

    event Printed(uint256 indexed tokenId);

    function markPrinted(uint256[] calldata ids) external onlyOwner {
        for (uint256 i = 0; i < ids.length; i++) {
            uint256 id = ids[i];
            if (id == SITE_TOKEN_ID || _ownerOf(id) == address(0)) revert NotMinted();
            if (!printExists[id]) {
                printExists[id] = true;
                emit Printed(id);
                emit MetadataUpdate(id);
            }
        }
    }

    // ═══════════════════════════════════════
    // OWNER RESERVE
    // ═══════════════════════════════════════

    function ownerMint(uint256[] calldata ids, address to) external onlyOwner {
        for (uint256 i = 0; i < ids.length; i++) {
            if (!ownerReserved[ids[i]]) revert NotOwnerReserved();
            _mint(to, ids[i]);
            traitsOf(ids[i]);
        }
    }

    // ═══════════════════════════════════════
    // #0 — THE SITE
    // ═══════════════════════════════════════
    // #0 is the page itself, read from the site contract; minted once

    function mintSiteToken(address to) external onlyOwner {
        if (address(site) == address(0)) revert SiteNotSet();
        _mint(to, SITE_TOKEN_ID);
        emit SiteTokenMinted(to);
    }

    function setSiteName(string calldata n) external onlyOwner {
        _requireJsonSafe(bytes(n));
        siteName = n;
        emit SiteNameSet(n);
        emit MetadataUpdate(SITE_TOKEN_ID);
    }

    function setSiteDescription(string calldata d) external onlyOwner {
        _requireJsonSafe(bytes(d));
        siteDescription = d;
        emit SiteDescriptionSet(d);
        emit MetadataUpdate(SITE_TOKEN_ID);
    }

    function _requireJsonSafe(bytes memory b) internal pure {
        for (uint256 i = 0; i < b.length; i++) {
            uint8 c = uint8(b[i]);
            if (c == 0x22 || c == 0x5C || c < 0x20) revert BadMetadataString(); // " \ and controls
        }
    }

    function _siteTokenURI() internal view returns (string memory) {
        return string.concat(
            'data:application/json;utf8,{"name":"',
            siteName,
            '","description":"',
            siteDescription,
            '","animation_url":"data:text/html;base64,',
            Base64.encode(bytes(site.siteHTML())),
            '"}'
        );
    }

    // ═══════════════════════════════════════
    // METADATA
    // ═══════════════════════════════════════

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        _requireOwned(tokenId);
        if (tokenId == SITE_TOKEN_ID) return _siteTokenURI();
        return renderer.tokenURI(tokenId, traitsOf(tokenId), printExists[tokenId]);
    }

    function supportsInterface(bytes4 interfaceId) public view override returns (bool) {
        return interfaceId == 0x49064906 || super.supportsInterface(interfaceId);
    }
}
