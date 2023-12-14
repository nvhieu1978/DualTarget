import time

import click
from pycardano import *
from src.utils import get_chain_context, get_signing_info, get_address, network
from src.on_chain import dualtarget
from src.utils.contracts import get_contract


@click.command()
@click.argument("name")
@click.argument("beneficiary")
@click.option(
    "--amount",
    type=int,
    default=5000000,
    help="Amount of lovelace to send to the script address.",
)
@click.option(
    "--wait_time",
    type=int,
    default=0,
    help="Time until the vesting contract deadline from current time",
)



def main(name: str, beneficiary: str, amount: int, wait_time: int):
    # Load chain context
    #context = OgmiosChainContext(ogmios_url, network=network, kupo_url=kupo_url)
    context = get_chain_context()

    # Get payment address
    payment_vkey, payment_skey, payment_address = get_signing_info(name)
    vkey_owner_hash: VerificationKeyHash = payment_address.payment_part
    

    # Get the beneficiary VerificationKeyHash (PubKeyHash)
    beneficiary_address = get_address(beneficiary)
    vkey_hash: VerificationKeyHash = beneficiary_address.payment_part
    print(f"beneficiary_address: {beneficiary_address}")
  
    # Build the transaction
    builder = TransactionBuilder(context)
    builder.add_input_address(payment_address)
    # builder.add_output(
    #     TransactionOutput(address=script_address, amount=amount, datum=datum)
    # )

    # Send 1.5 ADA and a native asset (CHOC) in quantity of 2000 to an address.
    builder.add_output(
        TransactionOutput(
            beneficiary_address,
            Value.from_primitive(
                [
                    1800000,
                    {
                        bytes.fromhex(
                            "e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72"  # Policy ID
                        ): {
                            b"MIN": 1100  # Asset name and amount
                        }
                    },
                ]
            ),
        )
    )
    # Sign the transaction

    signed_tx = builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=payment_address,
    )

    # Submit the transaction
    context.submit_tx(signed_tx.to_cbor())

    print(f"transaction id: {signed_tx.id}")
    if network == Network.TESTNET:
        print(f"Cexplorer: https://preprod.cexplorer.io/tx/{signed_tx.id}")
    else:
        print(f"Cexplorer: https://cexplorer.io/tx/{signed_tx.id}")


if __name__ == "__main__":
    main()

















# import time

# import click
# from pycardano import *

# @click.command()
# @click.argument("name")
# @click.argument("beneficiary")
# @click.option(
#     "--amount",
#     type=int,
#     default=5000000,
#     help="Amount of lovelace to send to the script address.",
# )
# @click.option(
#     "--wait_time",
#     type=int,
#     default=0,
#     help="Time until the vesting contract deadline from current time",
# )



# def main(name: str, beneficiary: str, amount: int, wait_time: int):
#     network = Network.TESTNET
#     #context = BlockFrostChainContext("preview0zkKyyt1OgyY2PweIYbbSXlUEKQHta2D", base_url="https://cardano-preview.blockfrost.io/api/")
#     context = BlockFrostChainContext("preprod2EkL4jB7Awsl1ugTeMg1oOID9gHLi6pd", base_url="https://cardano-preprod.blockfrost.io/api/")


#     # address_from = input('Enter source address: ')
#     # sk_path = input('Enter the name of the file with the signing key: ')
#     # address_to = input('Enter destination address: ')


#     # tx_builder = TransactionBuilder(context)

#     # tx_builder.add_input_address(address_from)
#     # tx_builder.add_output(TransactionOutput.from_primitive([address_to, 10000000]))

#     # payment_signing_key = PaymentSigningKey.load(sk_path)

#     # signed_tx = tx_builder.build_and_sign([payment_signing_key], change_address=Address.from_primitive(address_from))

#     # context.submit_tx(signed_tx.to_cbor())

#     #===============================================

#     # Read keys to memory
#     # Assume there is a payment.skey file sitting in current directory
#     psk = PaymentSigningKey.load("keys/wallet1.skey")
#     # Assume there is a stake.skey file sitting in current directory
#     #ssk = StakeSigningKey.load("stake.skey")

#     pvk = PaymentVerificationKey.from_signing_key(psk)
#     #svk = StakeVerificationKey.from_signing_key(ssk)

#     # Derive an address from payment verification key and stake verification key
#     address = Address.from_primitive("addr_test1vzzfhwyzkzvel68wuvvs65apm3r06urugxze7jtn4myyesqyrms82") #(pvk.hash(), network)
#     address = Address(pvk.hash(), network=network)
#     print(f'address: {address}')

#     # Create a transaction builder
#     builder = TransactionBuilder(context)

#     # Tell the builder that transaction input will come from a specific address, assuming that there are some ADA and native
#     # assets sitting at this address. "add_input_address" could be called multiple times with different address.
#     builder.add_input_address(address)

#     # Get all UTxOs currently sitting at this address
#     utxos = context.utxos(address)

#     # We can also tell the builder to include a specific UTxO in the transaction.
#     # Similarly, "add_input" could be called multiple times.
#     #builder.add_input(utxos[0])

#     # Send 1.5 ADA and a native asset (CHOC) in quantity of 2000 to an address.
#     builder.add_output(
#         TransactionOutput(
#             Address.from_primitive(
#                 "addr_test1qrsatwqzdh6w0ucekezvlrhe3cs76mpp7pup3eddkmq4ax8n0l9jsm5npkmszc2jeet7w6wwp5a94aqadlueuzk4sjdsd3dq4j"
#             ),
#             Value.from_primitive(
#                 [
#                     1700000,
#                     {
#                         bytes.fromhex(
#                             "e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72"  # Policy ID
#                         ): {
#                             b"tDJED": 1000  # Asset name and amount
#                         }
#                     },
#                 ]
#             ),
#         )
#     )

#     # We can add multiple outputs, similar to what we can do with inputs.
#     # Send 2 ADA and a native asset (CHOC) in quantity of 200 to ourselves
#     builder.add_output(
#         TransactionOutput(
#             address,
#             Value.from_primitive(
#                 [
#                     2600000,
#                     {
#                         bytes.fromhex(
#                             "e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72"  # Policy ID
#                         ): {
#                             b"tDJED": 2000  # Asset name and amount
#                         }
#                     },
#                 ]
#             ),
#         )
#     )

#     # Create final signed transaction
#     signed_tx = builder.build_and_sign([psk], change_address=address)
#     #signed_tx = builder.build_and_sign([payment_signing_key], change_address=address)

#     # Submit signed transaction to the network
#     context.submit_tx(signed_tx)

#     print('transaction submitted')
# if __name__ == "__main__":
#     main()