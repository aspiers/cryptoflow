#!/usr/bin/env python3

import csv
import dateutil.parser
import sys

from pprint import pprint
from operator import itemgetter


class FlowAnalyser:
    def __init__(self):
        self.fundings_by_wallet = {}

    def add_txn(self, date,
                sender, sent_amount, sent_currency,
                recipient, received_amount, received_currency,
                txtype, txid):
        if not sender:
            sender = "EXTERNAL"
            assert (txtype == "crypto_deposit" or
                    txtype == "fiat_deposit"), \
                f"unexpected external deposit type f{txtype}"

        if not recipient or not received_amount:
            return

        if sender == recipient:
            self.add_swap(
                date,
                sender, sent_amount, sent_currency,
                received_amount, received_currency,
                txtype, txid)
        else:
            self.add_funding(
                date,
                sender, received_amount, received_currency,
                recipient, received_amount, received_currency,
                txtype, txid)

    def add_funding(self, date,
                    sender, sent_amount, sent_currency,
                    recipient, received_amount, received_currency,
                    txtype, txid):
        # txtype=crypto_deposit when sender is external
        # txtype=transfer when sender is internal
        if recipient not in self.fundings_by_wallet:
            self.fundings_by_wallet[recipient] = []

        self.fundings_by_wallet[recipient].append(
            [date, sender,
             recipient, received_amount, received_currency]
        )
        print(f"{date} {sender} sent {recipient} "
              f"{received_amount} {received_currency} "
              f"({txtype}{optional_txid(txid)})")

        if (received_currency != sent_currency or
                received_amount != sent_amount):
            print(f"!!! from {sent_amount} {sent_currency} !!!")

    def add_swap(self, date,
                 wallet, sent_amount, sent_currency,
                 received_amount, received_currency,
                 txtype, txid):
        # print(f"{date} {wallet}: swapped "
        #       f"{sent_amount} {sent_currency} "
        #       f"for {received_amount} {received_currency} "
        #       f"({txtype}{optional_txid(txid)})")
        pass


def short_txid(txid):
    return txid[0:4] + ".." + txid[-4:]


def optional_txid(txid):
    return f" {short_txid(txid)}" if txid else ""


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
        (sender, sent_amount, sent_currency,
         recipient, received_amount, received_currency,
         txid, txtype) = itemgetter(
            'Sending Wallet',
            'Sent Amount',
            'Sent Currency',
            'Receiving Wallet',
            'Received Amount',
            'Received Currency',
            'TxHash',
            'Type'
        )(row)

        # if sender == recipient:
        #     pprint(row)

        self.analyser.add_txn(
            date,
            sender, sent_amount, sent_currency,
            recipient, received_amount, received_currency,
            txtype, txid)


def main():
    koinly = KoinlyFlowAnalyser()
    koinly.analyse_file(sys.argv[1])


main()
