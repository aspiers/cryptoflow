#!/usr/bin/env python3

import csv
import dateutil.parser
import datetime
import sys

from collections import defaultdict
from dataclasses import dataclass
from pprint import pprint
# from operator import itemgetter

EXTERNAL = 'EXTERNAL'


@dataclass
class Transaction:
    date: datetime.datetime
    sender: str
    sent_amount: float
    sent_currency: str
    sent_cost_basis: str
    recipient: str
    received_amount: float
    received_currency: str
    received_cost_basis: str
    fee_amount: float
    fee_currency: str
    fee_value: float
    gain: float
    net_value: float
    tx_type: str
    tx_id: str
    tx_src: str
    tx_dest: str
    label: str
    desc: str

    def __post_init__(self):
        if not self.sender:
            self.sender = EXTERNAL
            assert (self.tx_type == "crypto_deposit" or
                    self.tx_type == "fiat_deposit"), \
                f"unexpected external deposit type {self.tx_type}"

    @property
    def short_id(self):
        return self.tx_id[0:4] + ".." + self.tx_id[-4:]

    @property
    def optional_id(self):
        return f" {self.short_id}" if self.tx_id else ""

    @property
    def is_swap(self):
        return self.sender == self.recipient

    def __str__(self):
        if self.is_swap:
            return (f"{self.date} swap: {self.sender} "
                    f"{self.sent_amount} {self.sent_currency} "
                    f"-> {self.received_amount} {self.received_currency} "
                    f"({self.tx_type}{self.optional_id})")
        else:
            return (f"{self.date} send: {self.sender} -> {self.recipient} "
                    f"{self.received_amount} {self.received_currency} "
                    f"({self.tx_type}{self.optional_id})")

    def __repr__(self):
        return f"[Tx {self}]"


class ExternalDeposit(Transaction):
    pass


class FlowAnalyser:
    def __init__(self):
        self.wallet_fundings = defaultdict(list)
        self.wallet_funding_sources = defaultdict(
            lambda: defaultdict(list))
        self.wallet_swaps = defaultdict(list)

    def add_txn(self, txn):
        if not txn.recipient or not txn.received_amount:
            return

        if txn.is_swap:
            self.add_swap(txn)
        else:
            self.add_funding(txn)

    def add_funding(self, txn):
        # txn.tx_type=crypto_deposit when sender is external
        # txn.tx_type=transfer when sender is internal
        self.wallet_fundings[txn.recipient].append(txn)
        print(txn)

        if ('deposit' not in txn.tx_type and
            (txn.received_currency != txn.sent_currency or
             txn.received_amount != txn.sent_amount)):
            print(f"!!! from {txn.sent_amount} {txn.sent_currency} !!!")

        # Track funding transitively.  Any wallet which funded
        # txt.sender is also considered a funder of txn.recipient.
        for src, txns in self.wallet_funding_sources[txn.sender].items():
            for txn in txns:
                src_src = txn.sender
                self.wallet_funding_sources[txn.recipient][src_src].append(txn)

    def add_swap(self, txn):
        wallet = txn.recipient

        if wallet not in self.wallet_swaps:
            self.wallet_swaps[wallet] = []

        self.wallet_swaps[wallet].append(txn)
        print(txn)


class KoinlyFlowAnalyser:
    def __init__(self):
        self.analyser = FlowAnalyser()
        self.dateparser = dateutil.parser

    def analyse_file(self, filename):
        with open(filename) as f:
            # Koinly adds a couple of lines before the header
            assert f.readline().startswith("Transaction report")
            assert f.readline() == "\n"

            reader = csv.DictReader(f)

            for row in reader:
                self.analyse_txn(row)

    def analyse_txn(self, row):
        date = self.dateparser.parse(row['Date'])
        txn = Transaction(
            date=date,
            sender=row['Sending Wallet'],
            sent_amount=row['Sent Amount'],
            sent_currency=row['Sent Currency'],
            sent_cost_basis=row['Sent Cost Basis'],
            recipient=row['Receiving Wallet'],
            received_amount=row['Received Amount'],
            received_currency=row['Received Currency'],
            received_cost_basis=row['Received Cost Basis'],
            tx_type=row['Type'],
            tx_id=row['TxHash'],
            tx_src=row['TxSrc'],
            tx_dest=row['TxDest'],
            label=row['Label'],
            desc=row['Description'],
        )

        # if txn.sender == txn.recipient:
        #     pprint(row)

        self.analyser.add_txn(txn)

    def report_wallet(self, wallet):
        for txn in self.analyser.wallet_fundings[wallet]:
            print(f"   {txn}")

    def report(self):
        self.report_wallet('Bitpanda')


def main():
    koinly = KoinlyFlowAnalyser()
    koinly.analyse_file(sys.argv[1])
    koinly.report()


main()
