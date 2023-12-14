import time
import json
import click
from pycardano import (
    OgmiosChainContext,
    TransactionBuilder,
    TransactionOutput,
    UTxO,
    Redeemer,
    VerificationKeyHash,
    DeserializeException, Network,
    Value, Address,
    MultiAsset,
    AssetName,
    Asset,

)
from pycardano.hash import SCRIPT_HASH_SIZE, DatumHash, ScriptHash

from src.on_chain.dualtarget import ClaimRedeemer, RefundRedeemer, BuyAdaRedeemer, SellAdaRedeemer, TrueRedeemer, DaultargetParams, Asset_dual 
from src.utils import get_signing_info, get_address, network, get_chain_context
from src.utils.contracts import get_contract
from src.on_chain import dualtarget


@click.command()
@click.argument("name")
@click.argument("beneficiary")
@click.option(
    "--price",
    type=int,
    default=1000000,
    help="price current ADA/DJED.",
)
@click.option(
    "--wait_time",
    type=int,
    default=0,
    help="Time until the vesting contract deadline from current time",
)

def main(name: str, beneficiary: str, price: int, wait_time: int):
    # Load chain context
    #context = OgmiosChainContext(ogmios_url, network=network, kupo_url=kupo_url)
    context = get_chain_context()

    #key=========================================================================================================================== 
    # Get payment address
    payment_vkey, payment_skey, payment_address = get_signing_info(name)
    vkey_owner_hash: VerificationKeyHash = payment_address.payment_part

    # Get the beneficiary VerificationKeyHash (PubKeyHash)
    beneficiary_address = get_address(beneficiary)
    vkey_hash: VerificationKeyHash = beneficiary_address.payment_part

    #get address fee BatcherFee
    _, _, fee_address = get_signing_info(beneficiary)
    fee_address=fee_address.payment_part.to_primitive() #đưa vào datum

    # get address smart contract
    script_cbor, script_hash, script_address = get_contract("dualtarget")
    validator_address=script_address.payment_part.to_primitive() #đưa vào datum


    ADA = dualtarget.Asset_dual(policy_id=b"", token_name=b"")
    MIN = dualtarget.Asset_dual(policy_id=b"e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72", token_name=b"4d494e")
    DJED = dualtarget.Asset_dual(policy_id=b"e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72", token_name=b"74444a4544")
    price_current=price

    #key===========================================================================================================================    

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
                params.unit_price>= price_current 
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
                    "amountIn": params.amountIn,
                    "minimumAmountOut": params.minimumAmountOut,
                    "minimumAmountOutProfit": params.minimumAmountOutProfit,
                    "params":DaultargetParams.from_cbor(item.output.datum.cbor),
                    }
                )

                utxo_to_spend = item
                break

    assert isinstance(utxo_to_spend, UTxO), "No script UTxOs found!"

    # Find a collateral UTxO
    nft_utxo = []
    non_nft_utxo = None
    # Get all UTxOs currently sitting at this address
    utxos = context.utxos(payment_address)
    for utxo in utxos:
        # multi_asset should be empty for collateral utxo
        if not utxo.output.amount.multi_asset and utxo.output.amount.coin > 5000000:
            non_nft_utxo = utxo
        else:
            nft_utxo.append(
                {"utxo":utxo,
                }
            )     
            
    assert isinstance(non_nft_utxo, UTxO), "No collateral UTxOs found!"




    lovelace_amount=int(3000000)


    # Make redeemer
    redeemer = Redeemer(BuyAdaRedeemer())

    # Build the transaction==========================================================================================================
    builder = TransactionBuilder(context)
    builder.add_input_address(payment_address)
    # We can also tell the builder to include a specific UTxO in the transaction.
    # Similarly, "add_input" could be called multiple times.

    # builder.add_input(utxos[0])
    # builder.add_input(utxos[2])
    for utxo_to_input in nft_utxo:
        builder.add_input(utxo_to_input["utxo"])

    for utxo_to_spend in claimable_utxos:
        builder.add_script_input(utxo_to_spend["utxo"], script=script_cbor , redeemer=redeemer)
        builder.add_output(
            TransactionOutput(address=script_address, amount=utxo_to_spend["amountIn"], datum=utxo_to_spend["params"]) #gửi ADA vào SC
        )

        # output for BatcherFee
        builder.add_output(
            TransactionOutput(
                utxo_to_spend["BatcherFee_addr"], 
                utxo_to_spend["fee"],

            )
        )
        # builder.add_output(
        #     TransactionOutput(address=beneficiary_address, amount=Value(lovelace_amount, multi_assets))
        # )


    builder.collaterals.append(non_nft_utxo)
    # This tells pycardano to add vkey_hash to the witness set when calculating the transaction cost
    builder.required_signers = [vkey_owner_hash]
    # we must specify at least the start of the tx valid range in slots
    builder.validity_start = context.last_block_slot
    # This specifies the end of tx valid range in slots
    builder.ttl = builder.validity_start + 1000

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


  