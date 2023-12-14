import time

import click
from pycardano import *
# from pycardano import (
#     OgmiosChainContext,
#     TransactionBuilder,
#     TransactionOutput,
#     VerificationKeyHash, Network,
# )

from opshin.ledger.api_v2 import *
from src.on_chain import dualtarget
from src.utils import get_signing_info, get_address, network, get_chain_context
from src.utils.contracts import get_contract


@click.command()
@click.argument("name")



def main(name: str):
    # Load chain context
    #context = OgmiosChainContext(ogmios_url, network=network, kupo_url=kupo_url)
    context = get_chain_context()

    # Get payment address
    payment_address = get_address(name)
    vkey_owner_hash: VerificationKeyHash = payment_address.payment_part
    # get utxo to spend
    utxos = context.utxos(payment_address)

    print(utxos)
    



if __name__ == "__main__":
    main()
