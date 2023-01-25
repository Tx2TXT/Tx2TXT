// contract address: 0x5aA88d2901C68fdA244f1D0584400368d2C8e739

pragma solidity ^0.4.18;

contract MultiplicatorX3
{
    address public Owner = msg.sender;
   
    function withdraw()
    payable
    public
    {        Owner.transfer(this.balance);
    }
    
}

