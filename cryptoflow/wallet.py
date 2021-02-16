#!/usr/bin/env python3

from __future__ import annotations

from collections import defaultdict
from typing import Dict, DefaultDict

from coin import Coin
from utils import abort

_EXTERNAL = 'EXTERNAL'


class Wallet:
    wallets: Dict[str, Wallet] = {}

    name: str
    balances: DefaultDict[Coin, float]

    def __init__(self, name: str) -> None:
        assert name != ""
        self.name = name
        self.balances = defaultdict(lambda: 0.0)

    @classmethod
    def named(cls, name: str):
        if name not in cls.wallets:
            cls.wallets[name] = Wallet(name)
        return cls.wallets[name]

    def deposit(self, coin: Coin, amount: float) -> None:
        self.balances[coin] += amount

    def withdraw(self, coin: Coin, amount: float) -> None:
        if self.is_external:
            return
        balance = self.balances[coin]
        if amount > balance:
            abort(f"tried to withdraw {amount} {coin} from "
                  f"{self.name} but only {balance} {coin} present")
        self.balances[coin] -= amount

    def __str__(self) -> str:
        return self.name

    def __getitem__(self, coin: Coin) -> float:
        return self.balances[coin]

    @property
    def is_external(self):
        return self.name == _EXTERNAL


EXTERNAL = Wallet(_EXTERNAL)
