#!/usr/bin/env python3

import csv
import dateutil.parser
import sys
from typing import Dict, Optional

from analyser import FlowAnalyser
from wallet import Wallet
from coin import Coin
from transaction import Transaction


class KoinlyFlowAnalyser:
    def __init__(self) -> None:
        self.analyser = FlowAnalyser()
        self.dateparser = dateutil.parser

    def analyse_file(self, filename: str) -> None:
        with open(filename) as f:
            # Koinly adds a couple of lines before the header
            assert f.readline().startswith("Transaction report")
            assert f.readline() == "\n"

            reader = csv.DictReader(f)

            for row in reader:
                self.analyse_txn(row)

    def analyse_txn(self, row: Dict[str, str]) -> None:
        date = self.dateparser.parse(row['Date'])

        def safefloat(s: str) -> Optional[float]:
            return float(s) if s else None

        txn = Transaction(
            date=date,
            sender=Wallet(row['Sending Wallet']),
            sent_amount=safefloat(row['Sent Amount']),
            sent_currency=Coin(row['Sent Currency']),
            sent_cost_basis=safefloat(row['Sent Cost Basis']),
            recipient=Wallet(row['Receiving Wallet']),
            received_amount=safefloat(row['Received Amount']),
            received_currency=Coin(row['Received Currency']),
            received_cost_basis=safefloat(row['Received Cost Basis']),
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

    def report_wallet(self, wallet: Wallet) -> None:
        print(f"Fundings for {wallet}:")
        wallet_fundings = self.analyser.wallet_fundings[wallet]
        for coin, txns in wallet_fundings.items():
            print(f"   {coin}")
            for t in txns:
                print(f"      {t}")

    def report(self) -> None:
        self.report_wallet(Wallet('Bitpanda'))


def main() -> None:
    koinly = KoinlyFlowAnalyser()
    koinly.analyse_file(sys.argv[1])
    koinly.report()


main()
