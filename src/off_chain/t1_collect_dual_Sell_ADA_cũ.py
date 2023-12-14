import time

import click
from pycardano import *
from src.utils import get_chain_context, get_signing_info, get_address, network
from src.utils.contracts import get_contract
from src.on_chain.dualtarget import ClaimRedeemer, RefundRedeemer, Coin2AdaRedeemer, Ada2CoinRedeemer, DaultargetParams, Asset_dual

@click.command()
@click.argument("name")
@click.argument("beneficiary")
@click.option(
    "--amount",
    type=int,
    default=1500000,
    help="Amount of lovelace to send to the script address.",
)
@click.option(
    "--wait_time",
    type=int,
    default=0,
    help="Time until the vesting contract deadline from current time",
)

# def send_asset(name: str, beneficiary: str, amount: int, wait_time: int):
#     # Load chain context
#     #context = OgmiosChainContext(ogmios_url, network=network, kupo_url=kupo_url)
#     context = get_chain_context()

#     # Get payment address
#     payment_vkey, payment_skey, payment_address = get_signing_info(name)
#     vkey_owner_hash: VerificationKeyHash = payment_address.payment_part
    

#     # Get the beneficiary VerificationKeyHash (PubKeyHash)
#     beneficiary_address = get_address(beneficiary)
#     vkey_hash: VerificationKeyHash = beneficiary_address.payment_part

  
#     # Build the transaction
#     builder = TransactionBuilder(context)
#     builder.add_input_address(payment_address)
#     # builder.add_output(
#     #     TransactionOutput(address=script_address, amount=amount, datum=datum)
#     # )

#     # Send 1.5 ADA and a native asset (CHOC) in quantity of 2000 to an address.
#     builder.add_output(
#         TransactionOutput(
#             # Address.from_primitive(
#             #     "addr_test1qrsatwqzdh6w0ucekezvlrhe3cs76mpp7pup3eddkmq4ax8n0l9jsm5npkmszc2jeet7w6wwp5a94aqadlueuzk4sjdsd3dq4j"
#             # ),
#             beneficiary_address,
#             Value.from_primitive(
#                 [
#                     1800000,
#                     {
#                         bytes.fromhex(
#                             "e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72"  # Policy ID
#                         ): {
#                             b"MIN": 1100000  # Asset name and amount
#                         }
#                     },
#                 ]
#             ),
#         )
#     )
#     # Sign the transaction

#     signed_tx = builder.build_and_sign(
#         signing_keys=[payment_skey],
#         change_address=payment_address,
#     )

#     # Submit the transaction
#     context.submit_tx(signed_tx.to_cbor())

#     print(f"transaction id: {signed_tx.id}")
#     if network == Network.TESTNET:
#         print(f"Cexplorer: https://preprod.cexplorer.io/tx/{signed_tx.id}")
#     else:
#         print(f"Cexplorer: https://cexplorer.io/tx/{signed_tx.id}")

def main(name: str, beneficiary: str, amount: int, wait_time: int):
    # Load chain context
    #context = OgmiosChainContext(ogmios_url, network=network, kupo_url=kupo_url)
    context = get_chain_context()

    # Get validator address
    script_cbor, script_hash, script_address = get_contract("dualtarget")
    validator_address_hash=script_address.payment_part.to_primitive() #đưa vào datum
    validator_address1 = Address(
        VerificationKeyHash.from_primitive(validator_address_hash),
        network=network,
    )

    # Get payment address
    payment_vkey, payment_skey, payment_address = get_signing_info(name)
    vkey_owner_hash=payment_address.payment_part.to_primitive() #đưa vào datum
    

     # Get the beneficiary VerificationKeyHash (PubKeyHash)
    beneficiary_address = get_address(beneficiary)
    vkey_hash: VerificationKeyHash = beneficiary_address.payment_part # phần payment để ghep Franken
    fee_address_hash=beneficiary_address.payment_part.to_primitive() #đưa vào datum
    fee_address1 = Address(
        VerificationKeyHash.from_primitive(fee_address_hash),
        network=network,
    ) 


    print(f"beneficiary_address {beneficiary_address} -> {vkey_hash} : {fee_address_hash} -> {fee_address1}" )
    print(f"validator_address_hash {script_address} -> {validator_address_hash} -> {validator_address1}" )   


    ADA = Asset_dual(policy_id=b"", token_name=b"")
    MIN = Asset_dual(policy_id=b"e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72", token_name=b"4d494e")
    DJED = Asset_dual(policy_id=b"e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72", token_name=b"74444a4544")

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
                params.assetIn == ADA
                and params.odSender == vkey_owner_hash  # POSIXTime is in ms!
            ):

            # if str(datum_obj.odSender.hex()) == bytes(payment_address.payment_part):
            #     beneficiary = Address(
            #         VerificationKeyHash.from_primitive(datum_obj.beneficiary),
            #         network=network,
            #     )

                validator_address1 = Address(
                    VerificationKeyHash.from_primitive(params.validator_address),
                    network=network,
                )
                fee_address1 = Address(
                    VerificationKeyHash.from_primitive(params.fee_address),
                    network=network,
                )                
                """
                TODO: also check if the deadline has passed and if the oracle datum info is greater than the datum limit
                """
                # claimable_utxos.append(
                #     {"fee_address": str(fee_address), "fee": datum_obj.fee, "utxo": item}
                # )
                claimable_utxos.append(
                    {"utxo": item, 
                    "BatcherFee_addr": str(fee_address1), "fee": params.BatcherFee, 
                    "script_addr1": str(validator_address1), "minimumAmountOut": params.minimumAmountOut,
                    "script_addr2": str(validator_address1), "minimumAmountOutProfit": params.minimumAmountOutProfit,
                    }
                )
                utxo_to_spend = item
                datum=params
                break
            else: 
                print(f"không đúng điều kiện: {params.odSender} == {vkey_owner_hash }")
                break

    assert isinstance(utxo_to_spend, UTxO), "No script UTxOs found!"


    # Find a collateral UTxO
    non_nft_utxo = None
    for utxo in context.utxos(str(payment_address)):
        # multi_asset should be empty for collateral utxo
        if not utxo.output.amount.multi_asset and utxo.output.amount.coin > 5000000:
            non_nft_utxo = utxo
            break
    assert isinstance(non_nft_utxo, UTxO), "No collateral UTxOs found!"




    #========================================================

    #========================================================
    # # Create the Dualtarget datum
    # params = DaultargetParams(
    #     odSender= bytes(vkey_owner_hash), #Address
    #     odReceiver= bytes(vkey_hash), # Address
    #     assetIn= ADA, #ADA
    #     amountIn= int(5000000),
    #     assetOut= MIN, #b"ADA", #poolDatum.assetB
    #     minimumAmountOut= int(10000000), 
    #     minimumAmountOutProfit= int(0),  
    #     odPrice= int(2000000),
    #     odstrategy= b"ADADJED",
    #     BatcherFee= int(2000000),
    #     OutputADA= int(2000000),
    #     fee_address= fee_address_hash,#b"a24dbfcdb549b0657990105579af8eb560d78c481f0524318cef2e8a"
    #     validator_address= validator_address_hash, #b"006a563c1553ed9a153b34c5719b603a1c9e78f506640330512020bf",
    #     deadline=int(time.time() + wait_time) * 1000,  # must be in milliseconds
    # )

    

    # # Make datum
    # datum = params

    # Make redeemer
    redeemer = Redeemer(RefundRedeemer())



#     #Thay đổi==============================================
#     #builder.add_script_input(utxo_to_spend, script=script_cbor, redeemer=redeemer)
#  # Build the transaction
#     builder = TransactionBuilder(context)

#     for utxo_to_spend in claimable_utxos:
#         # builder.add_input_address(payment_address)
#         builder.add_script_input(utxo_to_spend["utxo"], script=script_cbor , redeemer=redeemer)

#         builder.add_output(
#             TransactionOutput(
#                 utxo_to_spend["BatcherFee_addr"], 
#                 utxo_to_spend["fee"],

#             )
#         )

#         # builder.add_output(
#         #     TransactionOutput(
#         #         #utxo_to_spend["script_addr1"], 
#         #         script_address,
#         #         utxo_to_spend["minimumAmountOut"],
#         #         datum,

#         #     )
#         # )
#     builder.add_output(
#         TransactionOutput(address=script_address, amount=amount, datum=datum)
#     )
#         # builder.add_output(
#         #     TransactionOutput(address=script_address, amount=multi_assets, datum=datum)
#         # )       

#         # Send 1.5 ADA and a native asset (CHOC) in quantity of 2000 to an address.
#         # builder.add_output(
#         #     TransactionOutput(
#         #         # Address.from_primitive(
#         #         #     "addr_test1qrsatwqzdh6w0ucekezvlrhe3cs76mpp7pup3eddkmq4ax8n0l9jsm5npkmszc2jeet7w6wwp5a94aqadlueuzk4sjdsd3dq4j"
#         #         # ),
#         #         address=script_address,
#         #         # amount=Value.from_primitive(
#         #         #     [
#         #         #         1500000,
#         #         #         {
#         #         #             bytes.fromhex(
#         #         #                 "e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72"  # Policy ID
#         #         #             ): {
#         #         #                 b"MIN": 20001  # Asset name and amount
#         #         #             }
#         #         #         },
#         #         #     ]
#         #         # ),
#         #         amount=100,
#         #         datum=datum,
#         #     )
#         # )

#         # builder.add_output(
#         #     TransactionOutput.from_primitive(
#         #         [utxo_to_spend["fee_address1"], utxo_to_spend["fee"]]
#         #     )
#         # )
#      #==============================================
#     builder.collaterals.append(non_nft_utxo)
#     # This tells pycardano to add vkey_hash to the witness set when calculating the transaction cost
#     vkey_hash: VerificationKeyHash = payment_address.payment_part
#     builder.required_signers = [vkey_hash]
#     # we must specify at least the start of the tx valid range in slots
#     builder.validity_start = context.last_block_slot
#     # This specifies the end of tx valid range in slots
#     builder.ttl = builder.validity_start + 1000




#     # Sign the transaction
#     payment_vkey, payment_skey, payment_address = get_signing_info(name)
#     signed_tx = builder.build_and_sign(
#         signing_keys=[payment_skey],
#         change_address=payment_address,
#     )

#     # Submit the transaction
#     context.submit_tx(signed_tx.to_cbor())

    
#     print(f"transaction id: {signed_tx.id}")
#     if network == Network.TESTNET:
#         print(f"Cexplorer: https://preprod.cexplorer.io/tx/{signed_tx.id}")
#     else:
#         print(f"Cexplorer: https://cexplorer.io/tx/{signed_tx.id}")

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

    # Create the Dualtarget datum
    params = DaultargetParams(
        odSender= bytes(vkey_owner_hash), #Address
        odReceiver= bytes(vkey_hash), # Address
        assetIn= ADA, #ADA
        amountIn= int(5000000),
        assetOut= MIN, #b"ADA", #poolDatum.assetB
        minimumAmountOut= int(10000000), 
        minimumAmountOutProfit= int(0),  
        odPrice= int(2000000),
        odstrategy= b"ADADJED",
        BatcherFee= int(2000000),
        OutputADA= int(2000000),
        fee_address= fee_address,#b"a24dbfcdb549b0657990105579af8eb560d78c481f0524318cef2e8a"
        validator_address= validator_address, #b"006a563c1553ed9a153b34c5719b603a1c9e78f506640330512020bf",
        deadline=int(time.time() + wait_time) * 1000,  # must be in milliseconds
    )

    

    # Make datum
    datum = params

    # Build the transaction
    builder = TransactionBuilder(context)
    builder.add_script_input(utxo_to_spend, script=script_cbor , redeemer=redeemer)
    builder.add_input_address(payment_address)
    builder.add_output(
        TransactionOutput(address=script_address, amount=amount, datum=datum)
    )

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
