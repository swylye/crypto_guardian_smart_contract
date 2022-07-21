// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";

contract NFT is ERC721Enumerable {
    uint256 public nextTokenId = 1;

    constructor() ERC721("NFT", "NFT") {}

    function mint(uint256 _amount) external {
        for (uint256 i = 0; i < _amount; i++) {
            _safeMint(msg.sender, nextTokenId);
            nextTokenId += 1;
        }
    }
}
