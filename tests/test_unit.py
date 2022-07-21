from brownie import (
    CryptoGuardian,
    Token,
    NFT,
    accounts,
    config,
    network,
    exceptions,
    convert,
)
from web3 import Web3
from scripts.deploy import deploy_new_contracts
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account
import pytest
import eth_abi
import time

initial_fee = 0.01 * 10**18


def test_transfer_all():
    account = get_account()
    account1 = get_account(index=1)
    crypto_guardian, token, nft = deploy_new_contracts(account, initial_fee)
    print("Contracts deployed!!")

    # minting token and nft
    token_amount = 1000 * 10**18
    token_mint_tx = token.mint(token_amount, {"from": account})
    token_mint_tx.wait(1)
    assert token.balanceOf(account) == token_amount
    nft_amount = 3
    nft_mint_tx = nft.mint(nft_amount, {"from": account})
    nft_mint_tx.wait(1)
    assert nft.balanceOf(account) == nft_amount
    print("Tokens and NFTs minted!!")

    # grant approvals
    max_number = 2**256 - 1
    token_approval = token.approve(
        crypto_guardian.address, max_number, {"from": account}
    )
    token_approval.wait(1)
    nft_approval = nft.setApprovalForAll(
        crypto_guardian.address, True, {"from": account}
    )
    nft_approval.wait(1)
    nft.isApprovedForAll(account, crypto_guardian.address)
    print("Approvals granted!!")

    # adding erc20 and erc721
    crypto_guardian.addERC20(token.address, {"from": account, "value": 0.01 * 10**18})
    crypto_guardian.addERC721(nft.address, {"from": account, "value": 0.01 * 10**18})
    assert crypto_guardian.addressToListing(account.address)["erc20Count"] == 1
    assert crypto_guardian.addressToListing(account.address)["erc721Count"] == 1
    print("Token and NFT addresses added to contract!!")

    # adding emergency contact
    crypto_guardian.setEmergencyAddress(account1.address, {"from": account})
    assert (
        crypto_guardian.addressToListing(account.address)["emergencyAddress"]
        == account1.address
    )
    print("Emergency address added!!")

    # transfer all
    with pytest.raises(exceptions.VirtualMachineError):
        # transfer from non owner account
        crypto_guardian.transferAllTokens({"from": account1})
    # transfer from owner account
    transfer_tx = crypto_guardian.transferAllTokens({"from": account})
    transfer_tx.wait(1)
    assert token.balanceOf(account1) == token_amount
    assert nft.balanceOf(account1) == nft_amount


def test_eth_deposit_withdraw():
    account = get_account()
    beneficiary_address = get_account(index=1)
    crypto_guardian, token, nft = deploy_new_contracts(account, initial_fee)
    print("Contracts deployed!!")

    # deposit ether
    ether_amount = 1 * 10**18
    deposit_tx = crypto_guardian.depositEther({"from": account, "value": ether_amount})
    deposit_tx.wait(1)
    assert (
        crypto_guardian.addressToListing(account.address)["ethDeposit"] == ether_amount
    )
    assert crypto_guardian.totalEthDeposits() == ether_amount

    # withdraw ether
    with pytest.raises(exceptions.VirtualMachineError):
        # withdrawing more than deposit
        crypto_guardian.withdrawEther(ether_amount + 1, {"from": account})
    withdraw_tx = crypto_guardian.withdrawEther(ether_amount, {"from": account})
    withdraw_tx.wait(1)
    assert crypto_guardian.addressToListing(account.address)["ethDeposit"] == 0
    assert crypto_guardian.totalEthDeposits() == 0


def test_owner_withdraw():
    owner = get_account()
    user = get_account(index=1)
    crypto_guardian, token, nft = deploy_new_contracts(owner, initial_fee)
    print("Contracts deployed!!")

    # deposit ether
    ether_amount = 1 * 10**18
    deposit_tx = crypto_guardian.depositEther({"from": user, "value": ether_amount})
    deposit_tx.wait(1)
    assert crypto_guardian.addressToListing(user.address)["ethDeposit"] == ether_amount
    assert crypto_guardian.totalEthDeposits() == ether_amount

    # adding ERC20 and ERC721
    crypto_guardian.addERC20(token.address, {"from": user, "value": 0.01 * 10**18})
    crypto_guardian.addERC721(nft.address, {"from": user, "value": 0.01 * 10**18})

    # withdraw ether
    with pytest.raises(exceptions.VirtualMachineError):
        crypto_guardian.ownerWithdraw({"from": user})
    ori_owner_balance = owner.balance()
    owner_withdraw_tx = crypto_guardian.ownerWithdraw({"from": owner})
    owner_withdraw_tx.wait(1)
    new_owner_balance = owner.balance()
    assert new_owner_balance - ori_owner_balance == 0.02 * 10**18
    withdraw_tx = crypto_guardian.withdrawEther(ether_amount, {"from": user})
    withdraw_tx.wait(1)
    assert crypto_guardian.addressToListing(user.address)["ethDeposit"] == 0
    assert crypto_guardian.totalEthDeposits() == 0


def test_beneficiary_withdraw():
    account = get_account()
    beneficiary_address = get_account(index=1)
    non_beneficiary_address = get_account(index=2)
    crypto_guardian, token, nft = deploy_new_contracts(account, initial_fee)
    print("Contracts deployed!!")

    # minting token and nft
    token_amount = 1000 * 10**18
    token_mint_tx = token.mint(token_amount, {"from": account})
    token_mint_tx.wait(1)
    assert token.balanceOf(account) == token_amount
    nft_amount = 3
    nft_mint_tx = nft.mint(nft_amount, {"from": account})
    nft_mint_tx.wait(1)
    assert nft.balanceOf(account) == nft_amount
    print("Tokens and NFTs minted!!")

    # deposit ether
    ether_amount = 1 * 10**18
    deposit_tx = crypto_guardian.depositEther({"from": account, "value": ether_amount})
    deposit_tx.wait(1)
    assert (
        crypto_guardian.addressToListing(account.address)["ethDeposit"] == ether_amount
    )
    assert crypto_guardian.totalEthDeposits() == ether_amount

    # grant approvals
    max_number = 2**256 - 1
    token_approval = token.approve(
        crypto_guardian.address, max_number, {"from": account}
    )
    token_approval.wait(1)
    nft_approval = nft.setApprovalForAll(
        crypto_guardian.address, True, {"from": account}
    )
    nft_approval.wait(1)
    nft.isApprovedForAll(account, crypto_guardian.address)
    print("Approvals granted!!")

    # adding erc20 and erc721
    crypto_guardian.addERC20(token.address, {"from": account, "value": 0.01 * 10**18})
    crypto_guardian.addERC721(nft.address, {"from": account, "value": 0.01 * 10**18})
    assert crypto_guardian.addressToListing(account.address)["erc20Count"] == 1
    assert crypto_guardian.addressToListing(account.address)["erc721Count"] == 1
    print("Token and NFT addresses added to contract!!")

    # adding emergency contact
    crypto_guardian.setBeneficiaryAddress(
        beneficiary_address.address, {"from": account}
    )
    assert (
        crypto_guardian.addressToListing(account.address)["beneficiaryAddress"]
        == beneficiary_address.address
    )
    print("Beneficiary address added!!")

    # withdraw
    ori_eth_balance = beneficiary_address.balance()
    with pytest.raises(exceptions.VirtualMachineError):
        # attempted withdrawal before expiry
        crypto_guardian.withdraw(account.address, {"from": beneficiary_address})
    time.sleep(360)  # sleep for 6 minutes so that we'd be past expiry
    with pytest.raises(exceptions.VirtualMachineError):
        # attempted withdrawal by non emergency address
        crypto_guardian.withdraw(account.address, {"from": non_beneficiary_address})
    withdraw_tx = crypto_guardian.withdraw(
        account.address, {"from": beneficiary_address}
    )
    withdraw_tx.wait(1)
    new_eth_balance = beneficiary_address.balance()
    assert token.balanceOf(beneficiary_address) == token_amount
    assert nft.balanceOf(beneficiary_address) == nft_amount
    assert new_eth_balance - ori_eth_balance == ether_amount
    assert crypto_guardian.totalEthDeposits() == 0
