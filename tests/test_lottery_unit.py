from brownie import Lottery, accounts, config, network, exceptions
from matplotlib.pyplot import get
from web3 import Web3
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3

from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)
import pytest

"""2 types of testing:
Unit Testing: Testing small independent pieces. Testing in Development network
Integration testing: Testing big parts running across ecosystems. Tested on testnets"""


# Test all lines of the code


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act
    # 2000 usd = 1 eth, ... 50 usd = 0.025
    expectedEntrance = Web3.toWei(0.025, "ether")
    entranceFee = lottery.getEntranceFee()
    # Assert
    assert expectedEntrance == entranceFee


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    # Act
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Assert
    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Act
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    # Assert
    assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(
        lottery
    )  # The chain link node calls the fulfillRandomness function and returns random number, but in development network we have to pretend to be the node
    transaction = lottery.endLottery()
    request_id = transaction.events["RequestedRandomness"][
        "requestId"
    ]  # Here events are used.
    STATIC_RNG = 777
    # Mocking Responses for testing
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery, {"from": account}
    )
    # 777%3 = 0, account[0] will be winner
    start_bal_account = account.balance()
    lottery_bal = lottery.balance()
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == start_bal_account + lottery_bal
