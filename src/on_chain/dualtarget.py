from opshin.ledger.interval import *
from opshin.ledger.api_v2 import *



@dataclass()
class Asset_dual(PlutusData):
    """
    A Asset, consisting of a PolicyId and TokenName
    """
    policy_id: PolicyId
    token_name: TokenName

@dataclass()
class VestingParams(PlutusData):
    beneficiary: PubKeyHash
    deadline: POSIXTime

@dataclass()
class DaultargetParams(PlutusData):
    odSender: PubKeyHash #Address
    odReceiver: PubKeyHash # Address
    assetIn: Asset_dual #ADA
    amountIn: int
    assetOut: Asset_dual #poolDatum.assetB
    minimumAmountOut: int
    minimumAmountOutProfit: int   
    unit_price: int
    odPrice: int
    odstrategy: bytes
    BatcherFee: int
    OutputADA: int
    fee_address: bytes
    validator_address: bytes
    deadline: POSIXTime
    

@dataclass()
class ClaimRedeemer(PlutusData):
    CONSTR_ID= 0
    pass

@dataclass()
class RefundRedeemer(PlutusData):
    CONSTR_ID= 1
    pass

@dataclass()
class TradingRedeemer(PlutusData):
    CONSTR_ID= 2
    pass

@dataclass()
class BuyAdaRedeemer(PlutusData):
    CONSTR_ID= 3
    pass

@dataclass()
class SellAdaRedeemer(PlutusData):
    CONSTR_ID= 4
    pass

@dataclass()
class TrueRedeemer(PlutusData):
    CONSTR_ID= 5
    pass
    

def signed_by_odSender(params: DaultargetParams, context: ScriptContext) -> bool:
    return params.odSender in context.tx_info.signatories

def signed_by_odReceiver(params: DaultargetParams, context: ScriptContext) -> bool:
    return params.odReceiver in context.tx_info.signatories

def is_after(deadline: POSIXTime, valid_range: POSIXTimeRange) -> bool:
    # To ensure that the `valid_range` occurs after the `deadline`,
    # we construct an interval from `deadline` to infinity
    # then check whether that interval contains the `valid_range` interval.
    from_interval: POSIXTimeRange = make_from(deadline)
    return contains(from_interval, valid_range)


def deadline_reached(params: DaultargetParams, context: ScriptContext) -> bool:
    # The current transaction can only execute in `valid_range`,
    # so the current execution time is always within `valid_range`.
    # Therefore, to make all possible execution times occur after the deadline,
    # we need to make sure the whole `valid_range` interval occurs after the `deadline`.
    return is_after(params.deadline, context.tx_info.valid_range)


# def trading_reached(params: DaultargetParams, context: ScriptContext) -> bool:
#     pass

def is_Buy_ADA(params: DaultargetParams, context: ScriptContext) -> bool:
    ff = False  # fee address found
    fp = False  # fee paid
    vf = False  # validator address found
    vpo = False  # validator paid UTxO Order

    for item in context.tx_info.outputs:
        """
        check if the fee has been paid to the fee address
        """
        if params.fee_address == item.address.payment_credential.credential_hash: # fee_address: Có thể chuyển địa chỉ này thành tham số hóa
            ff = True
            if item.value.get(b"", {b"": 0}).get(b"", 0) >= params.BatcherFee:
                fp = True
        """
        check if the minimumAmountOut has been paid to the validator_address
        """       
        if params.validator_address == item.address.payment_credential.credential_hash: # validator_address: 
            vf = True
            if item.value.get(b"", {b"": 0}).get(b"", 0) >= params.minimumAmountOut:    #UTxO Order
                vpo = True


    return ff and fp and vf and vpo 

def is_Sell_ADA(params: DaultargetParams, context: ScriptContext) -> bool:
    ff = False  # fee address found
    fp = False  # fee paid
    vf = False  # validator address found
    vpo = False  # validator paid  Order UTxO
    vpp = False  # validator paid UTxO Profit
    vpd = False  #check OutputDatum
    for item in context.tx_info.outputs:
        """
        check if the fee has been paid to the fee address
        """
        if params.fee_address == item.address.payment_credential.credential_hash: # fee_address: Có thể chuyển địa chỉ này thành tham số hóa
            ff = True
            if item.value.get(b"", {b"": 0}).get(b"", 0) >= params.BatcherFee:
                fp = True
        """
        check if the minimumAmountOut has been paid to the validator_address
        """       
        if params.validator_address == item.address.payment_credential.credential_hash: # validator_address: 
            vf = True
            if item.value.get(b"params.assetIn.policy_id", {b"params.assetIn.token_name": 0}).get(b"params.assetIn.token_name", 0) >= params.minimumAmountOut:    #UTxO Order
                vpo = True
            elif item.value.get(b"params.assetIn.policy_id", {b"params.assetIn.token_name": 0}).get(b"params.assetIn.token_name", 0) >= params.minimumAmountOutProfit:    #UTxO Profit
                vpp = True  
            """
            check if the datum.info from the reference input is greater than the datum.limit from the claimed UtxO
            """
            #check OutputDatum
            rid = item.datum
            if isinstance(rid, SomeOutputDatum):
                oi: DaultargetParams = rid.datum  # oracle info
                if oi.odSender == params.odSender:
                    vpd = True

    return ff and fp #and vf and vpo and vpp and vpd
   

def validator(datum: DaultargetParams, redeemer: Union[ClaimRedeemer, RefundRedeemer, TradingRedeemer, BuyAdaRedeemer, SellAdaRedeemer, TrueRedeemer], context: ScriptContext) -> None:
    if isinstance(redeemer, ClaimRedeemer): #Vesting 
        assert signed_by_odReceiver(datum, context), "1" #"odReceiver's signature missing"
        assert deadline_reached(datum, context), "2" #"deadline not reached"
    elif isinstance(redeemer, RefundRedeemer): #ReFund
        assert signed_by_odSender(datum, context), "3" #"odSender's signature missing"

    elif isinstance(redeemer, BuyAdaRedeemer): #Buy ADA
        assert is_Buy_ADA(datum, context), "4" #"output ADA False"

    elif isinstance(redeemer, SellAdaRedeemer): #Sell ADA
        assert is_Sell_ADA(datum, context), "5" #"Sell ADA False"   

    elif isinstance(redeemer, TrueRedeemer):
        assert True, "away True redeemer"       

    else:
        assert False, "Invalid redeemer"
