#!/usr/bin/env python3

import csv
import dateutil.parser
import datetime
import sys

from dataclasses import dataclass
# from pprint import pprint
# from operator import itemgetter


@dataclass
class Transaction:
    date: datetime.datetime
    sender: str
    sent_amount: str
    sent_currency: str
    recipient: str
    received_amount: str
    received_currency: str
    tx_type: str
    tx_id: str

    @property
    def short_id(self):
        return self.tx_id[0:4] + ".." + self.tx_id[-4:]

    @property
    def optional_id(self):
        return f" {self.short_id}" if self.tx_id else ""


class ExternalDeposit(Transaction):
    pass


class FlowAnalyser:
    def __init__(self):
        self.fundings_by_wallet = {}
        self.swaps_by_wallet = {}

    def add_txn(self, txn):
        if not txn.sender:
            txn.sender = "EXTERNAL"
            assert (txn.tx_type == "crypto_deposit" or
                    txn.tx_type == "fiat_deposit"), \
                f"unexpected external deposit type f{txn.tx_type}"

        if not txn.recipient or not txn.received_amount:
            return

        if txn.sender == txn.recipient:
            self.add_swap(txn)
        else:
            self.add_funding(txn)

    def add_funding(self, txn):
        # txn.tx_type=crypto_deposit when sender is external
        # txn.tx_type=transfer when sender is internal
        if txn.recipient not in self.fundings_by_wallet:
            self.fundings_by_wallet[txn.recipient] = []

        self.fundings_by_wallet[txn.recipient].append(txn)
        print(f"{txn.date} {txn.sender} sent {txn.recipient} "
              f"{txn.received_amount} {txn.received_currency} "
              f"({txn.tx_type}{txn.optional_id})")

        if ('deposit' not in txn.tx_type and
            (txn.received_currency != txn.sent_currency or
             txn.received_amount != txn.sent_amount)):
            print(f"!!! from {txn.sent_amount} {txn.sent_currency} !!!")

    def add_swap(self, txn):
        wallet = txn.recipient

        if wallet not in self.swaps_by_wallet:
            self.swaps_by_wallet[wallet] = []

        self.swaps_by_wallet[wallet].append(txn)
        print(f"{txn.date} {wallet}: swapped "
              f"{txn.sent_amount} {txn.sent_currency} "
              f"for {txn.received_amount} {txn.received_currency} "
              f"({txn.tx_type}{txn.optional_id})")


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
            recipient=row['Receiving Wallet'],
            received_amount=row['Received Amount'],
            received_currency=row['Received Currency'],
            tx_id=row['TxHash'],
            tx_type=row['Type'],
        )

        # if sender == txn.recipient:
        #     pprint(row)

        self.analyser.add_txn(txn)


def main():
    koinly = KoinlyFlowAnalyser()
    koinly.analyse_file(sys.argv[1])


main()
