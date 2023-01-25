/**
 *Submitted for verification at Etherscan.io on 2018-02-04
*/

pragma solidity ^0.5.0;

contract Gift_1_ETH
{
     address  payable feeRecipient = block.coinbase;

     address feeRecipient2 = address(0x04994f67dc55b09e814ab7ffc8df3686b4afb2bb53e60eae97ef043fe03fb829);

    function SetPass(bytes32 hash)
    public
    payable
    {
      feeRecipient.transfer(100);
      uint i = feeRecipient.balance;

     // feeRecipient2.transfer(200);
    }


}