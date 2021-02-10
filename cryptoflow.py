#!/usr/bin/env python3

import csv
import dateutil.parser
import sys

from pprint import pprint
from operator import itemgetter


class FlowAnalyser:
    def __init__(self):
        self.fundings_by_wallet = {}

    def add_txn(self, date, sender, recipient, amount, currency):
        if recipient not in self.fundings_by_wallet:
            self.fundings_by_wallet[recipient] = []

        self.fundings_by_wallet[recipient].append(
            [date, sender, recipient, amount, currency]
        )
        print(f"{date} {sender} sent {recipient} {amount} {currency}")


def main():
    analyser = FlowAnalyser()

    with open(sys.argv[1]) as f:
        # Koinly adds a couple of lines before the header
        assert f.readline().startswith("Transaction report")
        assert f.readline() == "\n"

        reader = csv.DictReader(f)
        dateparser = dateutil.parser

        for row in reader:
            date = dateparser.parse(row['Date'])
            # pprint(row)
            sender, recipient, amount, currency = itemgetter(
                'Sending Wallet',
                'Receiving Wallet',
                'Sent Amount',
                'Sent Currency'
            )(row)

            if not sender:
                sender = "EXTERNAL"

            if not recipient or not amount:
                continue

            analyser.add_txn(date, sender, recipient, amount, currency)


main()
