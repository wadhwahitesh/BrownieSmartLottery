// SPDX-License-Identifier: MIT

pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

contract Lottery is VRFConsumerBase, Ownable {
    address payable[] public players;
    uint256 usdEntryFee;
    AggregatorV3Interface internal ethToUsdPriceFeed;
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    } //This is actually 0, 1 and 2 respectively

    LOTTERY_STATE public lottery_state;
    uint256 public fee;
    bytes32 public keyhash;
    address payable public recentWinner;
    uint256 public randomness;
    event RequestedRandomness(bytes32 requestId);

    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyhash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntryFee = 50 * (10**18);
        ethToUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED; //or lottery_state = 1
        fee = _fee;
        keyhash = _keyhash;
    }

    function enter() public payable {
        //require(condition);
        require(lottery_state == LOTTERY_STATE.OPEN); //or lottery_state=LOTTER..open
        require(msg.value >= getEntranceFee(), "Not Enough ETH!");
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethToUsdPriceFeed.latestRoundData();
        uint256 adjustedPrice = uint256(price) * (10**10);
        //50$, 2000$ Eth Price
        //so 50/2000 ETH = 50$, but decimals dont work in solidity

        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice;
        //USE SAFEMATH HERE
        return costToEnter;

        //Test this early
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Can't start a new lottery yet"
        );

        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        //Picking a lottery can't be simply random because all the nodes cannot output the same random number,
        //Should take care of picking random numbers from the global variables such block.difficulty or msg.sender etc because they can be predicted
        //This makes the lottery hackable.
        //So we get the random number from outside, which is CHAINLINK ofc. Chainlink VRF(verifiably randomized fucniton)

        require(lottery_state == LOTTERY_STATE.OPEN);
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;

        bytes32 requestId = requestRandomness(keyhash, fee);
        emit RequestedRandomness(requestId);
    }

    function fulfillRandomness(bytes32 requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "You aren't there yet"
        );
        require(_randomness > 0, "Random not found");
        uint256 indexOfWiner = _randomness % players.length;
        recentWinner = players[indexOfWiner];

        recentWinner.transfer(address(this).balance);

        players = new address payable[](0);

        lottery_state = LOTTERY_STATE.CLOSED;

        randomness = _randomness;
    }
}
