// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title SSTORE2 — data as contract bytecode
/// @notice After 0xsequence/sstore2 and solady. Runtime is 0x00 (STOP) ++ data.
library SSTORE2 {
    // ──────────────────────── errors ────────────────────────
    error DeploymentFailed();
    error DataTooLarge();
    error ReadOutOfBounds();

    /// @dev EIP-170 (24,576) less the STOP byte
    uint256 internal constant MAX_DATA = 24_575;

    // ──────────── write (deploy data as contract) ──────────
    function write(bytes memory data) internal returns (address pointer) {
        if (data.length > MAX_DATA) revert DataTooLarge();
        // Prepend 0x00 (STOP opcode) so the contract can't be called.
        // Constructor (10 bytes at offsets 0x00–0x09):
        //   PUSH2 codeSize   (61 XXXX)  — codeSize = data.length + 1
        //   DUP1             (80)
        //   PUSH1 0x0a       (60 0a)    — offset where runtime starts
        //   RETURNDATASIZE   (3d)       — pushes 0 (cheaper than PUSH1 0)
        //   CODECOPY          (39)       — copy runtime to memory
        //   RETURNDATASIZE   (3d)       — pushes 0
        //   RETURN            (f3)       — return runtime from memory
        // Runtime (starts at 0x0a):
        //   0x00 (STOP) followed by the raw data
        bytes memory code = abi.encodePacked(
            hex"61",
            uint16(data.length + 1),
            hex"80600a3d393df3",
            hex"00",
            data
        );

        assembly {
            pointer := create(0, add(code, 0x20), mload(code))
        }
        if (pointer == address(0)) revert DeploymentFailed();
    }

    // ──────────── read (extcodecopy) ──────────
    function read(address pointer) internal view returns (bytes memory data) {
        return read(pointer, 0, codeSize(pointer));
    }

    function read(address pointer, uint256 start, uint256 end) internal view returns (bytes memory data) {
        // +1 to skip the STOP byte prefix
        start += 1;
        end += 1;

        uint256 size = end - start;
        if (end > pointer.code.length) revert ReadOutOfBounds();

        data = new bytes(size);
        assembly {
            extcodecopy(pointer, add(data, 0x20), start, size)
        }
    }

    function codeSize(address pointer) internal view returns (uint256 size) {
        size = pointer.code.length - 1;
    }
}
