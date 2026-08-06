// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface INodeRegistry {
    function registerNode(bytes32 nodeId) external;
    function stake(bytes32 nodeId) external payable;
    function getTrustScore(bytes32 nodeId) external view returns (uint256);
    function isRegistered(bytes32 nodeId) external view returns (bool);
}