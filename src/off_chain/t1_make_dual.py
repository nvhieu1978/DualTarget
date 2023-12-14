import time

import click
from pycardano import *
# from pycardano import (
#     OgmiosChainContext,
#     TransactionBuilder,
#     TransactionOutput,
#     VerificationKeyHash, Network,
# )

#from opshin.ledger.api_v2 import *
from src.on_chain import dualtarget
from src.utils import get_signing_info, get_address, network, get_chain_context
from src.utils.contracts import get_contract


@click.command()
@click.argument("name")
@click.argument("beneficiary")
@click.option(
    "--amount",
    type=int,
    default=15000000,
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
    payment_address = get_address(name)
    vkey_owner_hash: VerificationKeyHash = payment_address.payment_part
    

    # Get the beneficiary VerificationKeyHash (PubKeyHash)
    beneficiary_address = get_address(beneficiary)
    vkey_hash: VerificationKeyHash = beneficiary_address.payment_part

    ADA = dualtarget.Asset_dual(policy_id=b"", token_name=b"")
    MIN = dualtarget.Asset_dual(policy_id=b"e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72", token_name=b"4d494e")
    DJED = dualtarget.Asset_dual(policy_id=b"e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72", token_name=b"74444a4544")

    _, _, fee_address = get_signing_info(beneficiary)
    fee_address=fee_address.payment_part.to_primitive() #đưa vào datum


    # beneficiary_address_skey = "keys/beneficiary1.skey"
    # beneficiary_skey = PaymentSigningKey.load(beneficiary_address_skey)
    # beneficiary_vkey = PaymentVerificationKey.from_signing_key(beneficiary_skey)               
    # beneficiary_address = Address(beneficiary_vkey.hash(), network=network) #addr_test1vzth8xrfjwzveqkst9qt4x6j4ghg47wjpyyuxwfancptghc2w6dcw
    # fee_address1=beneficiary_address.payment_part.to_primitive() #đưa vào datum

    _, _, script_address = get_contract("dualtarget")
    validator_address=script_address.payment_part.to_primitive() #đưa vào datum
    print(f"validator_address {validator_address}")

    #Tính số  ADA và số token 
    BatcherFee=int(1500000)
    OutputADA=int(6000000)
    unit_price=int(1000000)
    step=int(10)
    price= int(1100000)
    amountIn=amount
    minimumAmountOut=int((100-step)/100*price*amountIn/unit_price)
    minimumAmountOutProfit=int((step)/100*price*amountIn/unit_price)
    amount_send=amount+BatcherFee+OutputADA
    print(f"amount_send: {amount_send}")
    # if minimumAmountOut<OutputADA or minimumAmountOutProfit<OutputADA:
    #     print("ADA nhỏ")
    #     exit()


    # Create the Dualtarget datum
    params = dualtarget.DaultargetParams(
        odSender= bytes(vkey_owner_hash), #Address
        odReceiver= bytes(vkey_hash), # Address
        assetIn= ADA, #ADA
        amountIn= amount_send,
        assetOut= MIN, #b"ADA", #poolDatum.assetB
        minimumAmountOut= minimumAmountOut, 
        minimumAmountOutProfit= minimumAmountOutProfit,  
        unit_price= unit_price,
        odPrice= price,
        odstrategy= b"ADADJED",
        BatcherFee= BatcherFee,
        OutputADA= OutputADA,
        fee_address= fee_address,
        validator_address= validator_address, 
        deadline=int(time.time() + wait_time) * 1000,  # must be in milliseconds
    )

    
    multi_assets = MultiAsset()

    # The utxo contains Multi-asset
    # data = bytes.fromhex("e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed724d494e") 
    # policy_id = ScriptHash(data[:SCRIPT_HASH_SIZE])
    # asset_name = AssetName(data[SCRIPT_HASH_SIZE:])

    # if policy_id not in multi_assets:
    #     multi_assets[policy_id] = Asset()
    # multi_assets[policy_id][asset_name] = int(111)
    # print(f"Asset: {multi_assets}")    
    # lovelace_amount=int(19000000)

    # Make datum
    datum = params

    # Build the transaction
    builder = TransactionBuilder(context)
    builder.add_input_address(payment_address)
    builder.add_output(
        TransactionOutput(address=script_address, amount=amount_send, datum=datum)
    )
    # builder.add_output(
    #     TransactionOutput(address=script_address, amount=Value(lovelace_amount, multi_assets), datum=datum)
    # )

    # Sign the transaction
    payment_vkey, payment_skey, payment_address = get_signing_info(name)
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
