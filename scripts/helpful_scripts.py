from brownie import (
    network,
    accounts,
    config,
    MockV3Aggregator,
    Contract,
    VRFCoordinatorMock,
    LinkToken,
    interface,
)


FORKED_LOCAK_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]
DECIMALS = 8
START_PRICE = 200000000000


def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAK_ENVIRONMENTS
    ):
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """
    This function will grab the contract addresses from brownie config if defined, otherwise deploye mocks version and return it

    Args:
        contract_name(string)
    returns:
        a the most recently deployed version of the contract
    """
    contract_type = contract_to_mock[contract_name]

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    return contract


def deploy_mocks(decimals=DECIMALS, initial_price=START_PRICE):
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_price, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("Mocks Deployed")


def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):  # 0.1
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    tx = link_token.transfer(contract_address, amount, {"from": account})
    # link_token_contract = interface.LinkTokenInterface(link_token.address)  # Another way of creating contracts, through interfaces
    # tx = link_token_contract.transfer(contract_address, amount, {"from": account})
    tx.wait(1)
    print("contract funded")
    return tx
