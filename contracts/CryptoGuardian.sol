// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "@openzeppelin/contracts/interfaces/IERC20.sol";
import "@openzeppelin/contracts/interfaces/IERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract CryptoGuardian is Ownable {
    uint256 public listingFee;

    uint256[] public tokenIdList;

    uint256 public timeOut = 4 weeks;

    uint256 public totalEthDeposits;

    struct listing {
        address[] erc20List;
        address[] erc721List;
        address emergencyAddress;
        address beneficiaryAddress;
        uint256 erc20Count;
        uint256 erc721Count;
        uint256 ethDeposit;
        uint256 expiry;
    }

    mapping(address => listing) public addressToListing;

    constructor(
        uint256 _listingFee // , uint256 _timeOut
    ) {
        listingFee = _listingFee;
        // timeOut = _timeOut;
    }

    function updateListingFee(uint256 _newListingFee) external onlyOwner {
        listingFee = _newListingFee;
    }

    function updateTimeOut(uint256 _newTimeOut) external onlyOwner {
        timeOut = _newTimeOut;
    }

    function addERC20(address _tokenAddress) external payable {
        require(msg.value == listingFee, "INSUFFICIENT_FUNDS");
        addressToListing[msg.sender].erc20List.push(_tokenAddress);
        addressToListing[msg.sender].erc20Count += 1;
        addressToListing[msg.sender].expiry = block.timestamp + timeOut;
    }

    function addERC721(address _nftAddress) external payable {
        require(msg.value == listingFee, "INSUFFICIENT_FUNDS");
        addressToListing[msg.sender].erc721List.push(_nftAddress);
        addressToListing[msg.sender].erc721Count += 1;
        addressToListing[msg.sender].expiry = block.timestamp + timeOut;
    }

    function depositEther() external payable {
        require(msg.value > 0, "NOTHING_TO_DEPOSIT");
        addressToListing[msg.sender].ethDeposit += msg.value;
        totalEthDeposits += msg.value;
        addressToListing[msg.sender].expiry = block.timestamp + timeOut;
    }

    function withdrawEther(uint256 _amount) external {
        require(
            addressToListing[msg.sender].ethDeposit >= _amount,
            "INSUFFICIENT_FUNDS"
        );
        addressToListing[msg.sender].ethDeposit -= _amount;
        totalEthDeposits -= _amount;
        (bool sent, ) = msg.sender.call{value: _amount}("");
        require(sent, "FAILED_TO_SEND");
        addressToListing[msg.sender].expiry = block.timestamp + timeOut;
    }

    function setEmergencyAddress(address _emergencyAddress) external {
        addressToListing[msg.sender].emergencyAddress = _emergencyAddress;
        addressToListing[msg.sender].expiry = block.timestamp + timeOut;
    }

    function setBeneficiaryAddress(address _beneficiaryAddress) external {
        addressToListing[msg.sender].beneficiaryAddress = _beneficiaryAddress;
        addressToListing[msg.sender].expiry = block.timestamp + timeOut;
    }

    function stillAlive() external {
        addressToListing[msg.sender].expiry = block.timestamp + timeOut;
    }

    function withdraw(address _address) external {
        address beneficiaryAddress = addressToListing[_address]
            .beneficiaryAddress;
        require(beneficiaryAddress == msg.sender, "NOTHING_TO_WITHDRAW");
        require(
            block.timestamp > addressToListing[_address].expiry,
            "NOT_EXPIRED"
        );
        uint256 tokenCount = addressToListing[_address].erc20Count;
        uint256 nftCount = addressToListing[_address].erc721Count;
        uint256 ethDeposit = addressToListing[_address].ethDeposit;
        require(
            tokenCount > 0 || nftCount > 0 || ethDeposit > 0,
            "NOTHING_TO_TRANSFER"
        );
        if (tokenCount > 0) {
            address[] memory erc20 = addressToListing[_address].erc20List;
            for (uint256 i = 0; i < tokenCount; i++) {
                address tokenAddress = erc20[i];
                IERC20 tokenContract = IERC20(tokenAddress);
                uint256 tokenBalance = tokenContract.balanceOf(_address);
                if (tokenBalance > 0) {
                    tokenContract.transferFrom(
                        _address,
                        beneficiaryAddress,
                        tokenBalance
                    );
                }
            }
        }
        if (nftCount > 0) {
            address[] memory erc721 = addressToListing[_address].erc721List;
            for (uint256 i = 0; i < nftCount; i++) {
                address nftAddress = erc721[i];
                IERC721Enumerable nftContract = IERC721Enumerable(nftAddress);
                uint256 nftBalance = nftContract.balanceOf(_address);
                if (nftBalance > 0) {
                    for (uint256 j = nftBalance; j > 0; j--) {
                        uint256 tokenId = nftContract.tokenOfOwnerByIndex(
                            _address,
                            j - 1
                        );
                        nftContract.transferFrom(
                            _address,
                            beneficiaryAddress,
                            tokenId
                        );
                    }
                }
            }
        }
        if (ethDeposit > 0) {
            addressToListing[_address].ethDeposit = 0;
            totalEthDeposits -= ethDeposit;
            (bool sent, ) = msg.sender.call{value: ethDeposit}("");
            require(sent, "FAILED_TO_SEND");
        }
        delete addressToListing[_address];
    }

    function transferAllTokens() external {
        address emergencyAddress = addressToListing[msg.sender]
            .emergencyAddress;
        require(emergencyAddress != address(0), "NO_EMERGENCY_ADDRESS");
        uint256 tokenCount = addressToListing[msg.sender].erc20Count;
        uint256 nftCount = addressToListing[msg.sender].erc721Count;
        require(tokenCount > 0 || nftCount > 0, "NOTHING_TO_TRANSFER");
        if (tokenCount > 0) {
            address[] memory erc20 = addressToListing[msg.sender].erc20List;
            for (uint256 i = 0; i < tokenCount; i++) {
                address tokenAddress = erc20[i];
                IERC20 tokenContract = IERC20(tokenAddress);
                uint256 tokenBalance = tokenContract.balanceOf(msg.sender);
                if (tokenBalance > 0) {
                    tokenContract.transferFrom(
                        msg.sender,
                        emergencyAddress,
                        tokenBalance
                    );
                }
            }
        }
        if (nftCount > 0) {
            address[] memory erc721 = addressToListing[msg.sender].erc721List;
            for (uint256 i = 0; i < nftCount; i++) {
                address nftAddress = erc721[i];
                IERC721Enumerable nftContract = IERC721Enumerable(nftAddress);
                uint256 nftBalance = nftContract.balanceOf(msg.sender);
                if (nftBalance > 0) {
                    for (uint256 j = nftBalance; j > 0; j--) {
                        uint256 tokenId = nftContract.tokenOfOwnerByIndex(
                            msg.sender,
                            j - 1
                        );
                        nftContract.transferFrom(
                            msg.sender,
                            emergencyAddress,
                            tokenId
                        );
                    }
                }
            }
        }
    }

    function ownerWithdraw() external onlyOwner {
        uint256 amount = address(this).balance - totalEthDeposits;
        (bool sent, ) = msg.sender.call{value: amount}("");
        require(sent, "FAILED_TO_SEND");
    }

    // Function to receive Ether. msg.data must be empty
    receive() external payable {}

    // Fallback function is called when msg.data is not empty
    fallback() external payable {}
}
