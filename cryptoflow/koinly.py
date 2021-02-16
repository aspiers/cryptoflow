#!/usr/bin/env python3

import csv
import dateutil.parser
import datetime
import sys
from typing import Dict, Optional

from analyser import FlowAnalyser
from wallet import Wallet, EXTERNAL
from coin import Coin
from transaction import Transaction


class KoinlyFlowAnalyser:
    def __init__(self) -> None:
        self.analyser = FlowAnalyser()
        self.dateparser = dateutil.parser
        self.last_date: Optional[datetime.datetime] = None

    def analyse_file(self, filename: str) -> None:
        with open(filename) as f:
            # Koinly adds a couple of lines before the header
            assert f.readline().startswith("Transaction report")
            assert f.readline() == "\n"

            reader = csv.DictReader(f)

            for row in reader:
                self.analyse_txn(row)
            print("\n")

    def analyse_txn(self, row: Dict[str, str]) -> None:
        date = self.dateparser.parse(row['Date'])

        # Preserve file ordering even when timestamps are identical
        if date == self.last_date:
            date += datetime.timedelta(milliseconds=1)
            # print("   >> shifted to " +
            #       date.isoformat(timespec='milliseconds'))
        self.last_date = date

        def safefloat(s: str) -> Optional[float]:
            return float(s) if s else None

        def safewallet(s: str) -> Wallet:
            return Wallet.named(s) if s else EXTERNAL

        txn = Transaction(
            date=date,
            sender=safewallet(row['Sending Wallet']),
            sent_amount=safefloat(row['Sent Amount']),
            sent_currency=Coin(row['Sent Currency']),
            sent_cost_basis=safefloat(row['Sent Cost Basis']),
            recipient=safewallet(row['Receiving Wallet']),
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
            balance = wallet[coin]
            print(f"   {balance} {coin}")
            for t in txns:
                print(f"      {t}")

    def report(self) -> None:
        self.report_wallet(Wallet.named('Bitpanda'))


def main() -> None:
    koinly = KoinlyFlowAnalyser()
    koinly.analyse_file(sys.argv[1])
    koinly.report()


main()
