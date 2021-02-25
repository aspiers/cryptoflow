#!/usr/bin/env python3

import datetime
from dataclasses import dataclass
from typing import Optional
import uuid

from wallet import Wallet, EXTERNAL
from coin import Coin


@dataclass
class Transaction:
    date: datetime.datetime
    sender: Wallet
    sent_amount: Optional[float]
    sent_currency: Coin
    sent_cost_basis: Optional[float]
    recipient: Wallet
    received_amount: Optional[float]
    received_currency: Coin
    received_cost_basis: Optional[float]
    tx_type: str
    tx_id: str
    tx_src: str
    tx_dest: str
    label: str
    desc: str
    fee_amount: Optional[float] = None
    fee_currency: Optional[Coin] = None
    fee_value: Optional[float] = None
    gain: Optional[float] = None
    net_value: Optional[float] = None

    def __post_init__(self) -> None:
        if self.sender == EXTERNAL:
            assert (self.tx_type == "crypto_deposit" or
                    self.tx_type == "fiat_deposit"), \
                f"unexpected external deposit type {self.tx_type}"
            assert not self.sent_currency
            assert self.received_currency
            self.sent_currency = self.received_currency

        if not self.tx_id:
            self.tx_id = str(uuid.uuid4())

    @property
    def short_id(self) -> str:
        tx_id = self.tx_id
        if tx_id.startswith('0x'):
            tx_id = tx_id[2:]
        if len(tx_id) in (24, 36, 64):
            return tx_id[0:4] + ".." + tx_id[-4:]
        return tx_id

    @property
    def optional_id(self) -> str:
        return f" {self.short_id}" if self.tx_id else ""

    @property
    def is_swap(self) -> bool:
        return self.sender == self.recipient

    @property
    def date_ms(self) -> str:
        # return self.date.isoformat(timespec='milliseconds')
        return self.date.strftime('%Y-%m-%dT%H:%M:%S.%f')[0:-3]

    def __str__(self) -> str:
        if self.is_swap:
            return (f"{self.date_ms} swap[{self.sender}] "
                    f"{self.sent_amount} {self.sent_currency} "
                    f"-> {self.received_amount} {self.received_currency} "
                    f"({self.tx_type}{self.optional_id})")
        else:
            return (f"{self.date_ms} send[{self.sender} -> {self.recipient}] "
                    f"{self.received_amount} {self.received_currency} "
                    f"({self.tx_type}{self.optional_id})")

    def __repr__(self) -> str:
        return f"[Tx {self}]"

    def __lt__(self, other) -> int:
        return self.date < other.date

    def __eq__(self, other) -> bool:
        return self.tx_id == other.tx_id

    def __hash__(self) -> int:
        return hash(self.tx_id)


class ExternalDeposit(Transaction):
    pass
