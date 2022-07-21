from brownie import CryptoGuardian, config, network, interface, Token, NFT
from scripts.helpful_scripts import (
    get_account,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    FORKED_BLOCKCHAIN,
)

initial_fee = 0.01 * 10**18


def main():
    account = get_account()
    if (
        network.show_active() in FORKED_BLOCKCHAIN
        or network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
    ):
        crypto_guardian, token, nft = deploy_new_contracts(account, initial_fee)
    else:
        crypto_guardian = deploy_new_contracts(account, initial_fee)
    # crypto_guardian = deploy_contract(account, initial_fee)


# def deploy_contract(account, initial_fee):
#     if len(CryptoGuardian) > 0:
#         crypto_guardian = CryptoGuardian[-1]
#     else:
#         crypto_guardian = CryptoGuardian.deploy(
#             initial_fee,
#             {"from": account},
#             publish_source=True,
#         )
#     return crypto_guardian


def deploy_new_contracts(account, initial_fee):
    account = get_account()
    print()
    if (
        network.show_active() in FORKED_BLOCKCHAIN
        or network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
    ):
        crypto_guardian = CryptoGuardian.deploy(
            initial_fee,
            {"from": account},
            # publish_source=True,
        )
        token = Token.deploy({"from": account})
        nft = NFT.deploy({"from": account})
        return crypto_guardian, token, nft
    else:
        crypto_guardian = CryptoGuardian.deploy(
            initial_fee,
            {"from": account},
            publish_source=True,
        )
        return crypto_guardian
