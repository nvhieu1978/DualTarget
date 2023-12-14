import time

import click
from pycardano import (
    OgmiosChainContext,
    TransactionBuilder,
    TransactionOutput,
    Address,
    UTxO,
    Redeemer,
    VerificationKeyHash,
    DeserializeException, Network,
)

from src.on_chain.dualtarget import ClaimRedeemer, RefundRedeemer, SellAdaRedeemer, BuyAdaRedeemer, DaultargetParams 
from src.utils import get_signing_info, get_address, network, get_chain_context
from src.utils.contracts import get_contract


@click.command()
@click.argument("name")

def main(name: str):
    # Load chain context
    #context = OgmiosChainContext(ogmios_url, network=network, kupo_url=kupo_url)
    context = get_chain_context()

    script_cbor, script_hash, script_address = get_contract("dualtarget")

    # Get payment address
    payment_address = get_address(name)


    #Thay đổi ==================================================================
    # Find a script UTxO
    script_utxos = context.utxos(str(script_address))
    sc_utxo = ""
    claimable_utxos = []
    utxo_to_spend = None

    for item in context.utxos(str(script_address)): #script_utxos:
        if item.output.datum:
            try:
                params = DaultargetParams.from_cbor(item.output.datum.cbor)
            except DeserializeException:
                continue
            if (
                params.odSender == bytes(payment_address.payment_part)
                
            ):
                fee_address1 = Address(
                    VerificationKeyHash.from_primitive(params.fee_address),
                    network=network,
                )
                """
                TODO: also check if the deadline has passed and if the oracle datum info is greater than the datum limit
                """
                claimable_utxos.append(
                    {"utxo": item, 
                    "BatcherFee_addr": str(fee_address1), "fee": params.BatcherFee, 
                    "minimumAmountOut": params.minimumAmountOut,
                    "minimumAmountOutProfit": params.minimumAmountOutProfit,
                    }
                )
                utxo_to_spend = item
# thay đổ khi dùng ref_scripts để refund 1 lần được tất cả
                break 
    assert isinstance(utxo_to_spend, UTxO), "No script UTxOs found!"

    # Find a collateral UTxO
    non_nft_utxo = None
    for utxo in context.utxos(str(payment_address)):
        # multi_asset should be empty for collateral utxo
        if not utxo.output.amount.multi_asset and utxo.output.amount.coin >= 5000000:
            non_nft_utxo = utxo
            break
    assert isinstance(non_nft_utxo, UTxO), "No collateral UTxOs found!"
    # Make redeemer
    redeemer = Redeemer(RefundRedeemer())

    # Build the transaction
    builder = TransactionBuilder(context)

    #Thay đổi==============================================
    #builder.add_script_input(utxo_to_spend, script=script_cbor, redeemer=redeemer)
    
    builder.add_input_address(payment_address)
    for utxo_to_spend in claimable_utxos:
        builder.add_script_input(utxo_to_spend["utxo"], script=script_cbor , redeemer=redeemer) # thay đổ khi dùng ref_scripts để refund 1 lần được tất cả

        # output for BatcherFee
        builder.add_output(
            TransactionOutput(
                utxo_to_spend["BatcherFee_addr"], 
                utxo_to_spend["fee"],

            )
        )
     #==============================================
    builder.add_output(
        TransactionOutput(address=payment_address, amount=int(5000000))
    )
    builder.collaterals.append(non_nft_utxo)
    # This tells pycardano to add vkey_hash to the witness set when calculating the transaction cost
    vkey_hash: VerificationKeyHash = payment_address.payment_part
    builder.required_signers = [vkey_hash]
    # we must specify at least the start of the tx valid range in slots
    builder.validity_start = context.last_block_slot
    # This specifies the end of tx valid range in slots
    builder.ttl = builder.validity_start + 1000

    # Sign the transaction
    payment_vkey, payment_skey, payment_address = get_signing_info(name)
    signed_tx = builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=payment_address,
    )

    # Submit the transaction
    context.submit_tx(signed_tx.to_cbor())

    # context.submit_tx(signed_tx.to_cbor())
    print(f"transaction id: {signed_tx.id}")
    if network == Network.TESTNET:
        print(f"Cexplorer: https://preprod.cexplorer.io/tx/{signed_tx.id}")
    else:
        print(f"Cexplorer: https://cexplorer.io/tx/{signed_tx.id}")


if __name__ == "__main__":
    main()
