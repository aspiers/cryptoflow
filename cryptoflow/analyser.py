#!/usr/bin/env python3

from collections import defaultdict
# from pprint import pprint
import sys
from typing import DefaultDict, Tuple

# type hints not yet added to sortedcontainers
# https://github.com/grantjenks/python-sortedcontainers/pull/107
from sortedcontainers import SortedSet  # type: ignore

from wallet import Wallet
from coin import Coin
from transaction import Transaction
from protocols import SupportsWrite


def create_sorted_txn_set():
    return SortedSet(key=lambda txn: txn.date)


class FlowAnalyser:
    # Dict mapping wallet -> currency -> a set of txns directly
    # *or* directly funding that wallet with that coin.  We ensure
    # the sets are chronologically sorted by setting the default
    # leaf values to be SortedSet instances which sorts by
    # txn.date.
    wallet_fundings: DefaultDict[
        Wallet,
        DefaultDict[Coin, SortedSet]
    ]

    # Dict which tracks the number of indirect fundings from
    # (wallet A, coin X) to (wallet B, coin Y) already included in
    # B's list of fundings for coin Y.
    #
    # Maps (wallet B, coin Y) -> (wallet A, coin X) -> number of
    # transactions from self.wallet_fundings[A][X] which were already
    # added to self.wallet_fundings[B][Y] as indirect fundings, or
    # skipped.
    #
    # This allows us to transitively maintain indirect funding
    # transactions in an efficient manner, avoiding duplicate funding
    # events or the need to iterate through the txn lists over and
    # over again.
    num_indirect_wallet_fundings: DefaultDict[
        Tuple[Wallet, Coin],
        DefaultDict[
            Tuple[Wallet, Coin],
            int
        ]
    ]

    output: SupportsWrite

    def __init__(self, output: SupportsWrite = sys.stdout) -> None:
        self.wallet_fundings = defaultdict(
            lambda: defaultdict(create_sorted_txn_set))

        self.num_indirect_wallet_fundings = defaultdict(
            lambda: defaultdict(lambda: 0))

        self.output = output

    def write(self, s: str) -> None:
        if self.output:
            self.output.write(s + "\n")

    def add_txn(self, txn: Transaction) -> None:
        if not txn.recipient or not txn.received_amount:
            assert 'withdrawal' in txn.tx_type
            # self.write(f"!! Skipping {txn}")
            return

        self.check_txn(txn)
        self.add_funding(txn)

    def update_wallets(self, txn: Transaction) -> None:
        src = txn.sender
        src_currency = txn.sent_currency
        src_amount = txn.sent_amount
        if (not src.is_external and src_amount is not None and
                src_currency is not None):
            src.withdraw(src_currency, src_amount)
            self.report_balance(src, src_currency, " after sending")

        dst = txn.recipient
        dst_currency = txn.received_currency
        dst_amount = txn.received_amount
        if dst_amount is not None:
            dst.deposit(dst_currency, dst_amount)
            self.report_balance(dst, dst_currency, " after receiving")

        fee_currency = txn.fee_currency
        fee_amount = txn.fee_amount
        if fee_amount is not None and fee_currency is not None:
            src.withdraw(fee_currency, fee_amount)
            self.report_balance(src, fee_currency, " after fee")

    def report_balance(self, wallet: Wallet, coin: Coin,
                       extra="") -> None:
        # Avoid balances like 0.00009062999999999433 BTC
        # which are just artifacts of floating point storage.
        # This rough approach is one decent enough option:
        #
        # balance = f"{wallet[coin]:.11f}".rstrip('0').rstrip('.')
        #
        # numpy.format_float_positional is another potential option.
        # However for now, just mimic Koinly's formatting:
        balance = f"{wallet[coin]:.8f}"
        self.write(f"   = {wallet} {coin} balance now "
                   f"{balance} {coin}{extra}")

    def check_txn(self, txn: Transaction):
        if txn.is_swap:
            assert txn.tx_type in ('buy', 'sell', 'exchange'), txn
            assert txn.sent_currency != txn.received_currency, txn
        else:
            assert txn.sent_currency == txn.received_currency, txn

    def add_funding(self, txn: Transaction) -> None:
        # txn.tx_type=crypto_deposit when sender is external
        # txn.tx_type=transfer when sender is internal
        if txn.is_swap:
            self.write(f"Swapping in {txn.sender}: "
                       f"{txn.sent_currency} -> {txn.received_currency}:")
        else:
            self.write(f"Funding {txn.recipient} with " +
                       txn.received_currency)
        self.write(f"   + {txn}")
        self.update_wallets(txn)
        self.add_direct_funding(txn)
        self.add_indirect_funding(txn)
        fundings: SortedSet[Transaction] = \
            self.wallet_fundings[txn.recipient][txn.received_currency]
        t: Transaction
        # for t in fundings:
        #     self.write(f"   . {t}")

    def add_direct_funding(self, txn: Transaction) -> None:
        self.wallet_fundings[txn.recipient][txn.received_currency].add(txn)

    def add_indirect_funding(self, txn: Transaction) -> None:
        # Track funding transitively.  Any wallet which funded
        # txn.sender is also considered an indirect funder of
        # txn.recipient.
        if txn.sender.is_external:
            self.write("   skipping transitive funding for external sources")
            return

        src = (txn.recipient, txn.received_currency)
        dst = (txn.sender, txn.sent_currency)
        count: int = self.num_indirect_wallet_fundings[src][dst]
        self.write(f"   transitively funding from funders of "
                   f"{txn.sender} with {txn.sent_currency}, "
                   f"starting at index {count}")
        fundings: SortedSet[Transaction] = \
            self.wallet_fundings[txn.sender][txn.sent_currency]
        new_indirect_txns: SortedSet[Transaction] = fundings[count:]
        for indirect_txn in new_indirect_txns:
            if (indirect_txn.sender == txn.recipient and
                    indirect_txn.sent_currency ==
                    txn.received_currency):
                self.write("      ignoring funding cycle")
                continue

            # Note: could have transactions in the same second, e.g.
            # when an exchange automatically routes a swap between
            # currencies which don't have a direct trading pair.
            assert indirect_txn.date <= txn.date

            self.wallet_fundings[txn.recipient][
                txn.received_currency].add(indirect_txn)
            # self.write(f"      > {indirect_txn}")

        new_index = \
            len(self.wallet_fundings[txn.sender][txn.sent_currency])
        self.num_indirect_wallet_fundings[src][dst] = new_index
        self.write(f"   next will start at index {new_index}")
