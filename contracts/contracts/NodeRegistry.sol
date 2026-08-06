// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {INodeRegistry} from "./INodeRegistry.sol";

contract NodeRegistry is INodeRegistry {
    mapping(bytes32 => bool) private _registered;
    mapping(bytes32 => uint256) private _stakes;
    mapping(bytes32 => uint256) private _trustScores;

    function registerNode(bytes32 nodeId) external override {
        require(!_registered[nodeId], "already registered");
        _registered[nodeId] = true;
        _trustScores[nodeId] = 100;
    }

    function stake(bytes32 nodeId) external payable override {
        require(_registered[nodeId], "not registered");
        _stakes[nodeId] += msg.value;
    }

    function getTrustScore(bytes32 nodeId) external view override returns (uint256) {
        return _trustScores[nodeId];
    }

    function isRegistered(bytes32 nodeId) external view override returns (bool) {
        return _registered[nodeId];
    }
}