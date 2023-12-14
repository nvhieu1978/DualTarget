from typing import Dict, Any
from decimal import Decimal, getcontext

from bigdecimal import sqrt

getcontext().prec = 50  # Set precision for Decimal calculations

class Big:
    def __init__(self, value):
        self.value = Decimal(value)

    def mul(self, other):
        return Big(self.value * other.value)

    def div(self, other):
        return Big(self.value / other.value)

    def __str__(self):
        return str(self.value)

def calculate_swap_exact_in(options: Dict[str, Any]) -> Dict[str, Any]:
    amount_in = options["amountIn"]
    reserve_in = options["reserveIn"]
    reserve_out = options["reserveOut"]

    amt_out_numerator = amount_in * 997 * reserve_out
    amt_out_denominator = amount_in * 997 + reserve_in * 1000

    price_impact_numerator = (
        reserve_out * amount_in * amt_out_denominator * 997 -
        amt_out_numerator * reserve_in * 1000
    )
    price_impact_denominator = reserve_out * amount_in * amt_out_denominator * 1000

    return {
        "amountOut": amt_out_numerator // amt_out_denominator,
        "priceImpact": Big(price_impact_numerator).mul(Big(100)).div(Big(price_impact_denominator)),
    }

def calculate_swap_exact_out(options: Dict[str, Any]) -> Dict[str, Any]:
    exact_amount_out = options["exactAmountOut"]
    reserve_in = options["reserveIn"]
    reserve_out = options["reserveOut"]

    amt_in_numerator = reserve_in * exact_amount_out * 1000
    amt_in_denominator = (reserve_out - exact_amount_out) * 997

    price_impact_numerator = (
        reserve_out * amt_in_numerator * 997 -
        exact_amount_out * amt_in_denominator * reserve_in * 1000
    )
    price_impact_denominator = reserve_out * amt_in_numerator * 1000

    return {
        "amountIn": amt_in_numerator // amt_in_denominator + 1,
        "priceImpact": Big(price_impact_numerator).mul(Big(100)).div(Big(price_impact_denominator)),
    }

def calculate_deposit(options: Dict[str, Any]) -> Dict[str, Any]:
    deposited_amount_a = options["depositedAmountA"]
    deposited_amount_b = options["depositedAmountB"]
    reserve_a = options["reserveA"]
    reserve_b = options["reserveB"]
    total_liquidity = options["totalLiquidity"]

    delta_liquidity_a = (deposited_amount_a * total_liquidity) // reserve_a
    delta_liquidity_b = (deposited_amount_b * total_liquidity) // reserve_b

    if delta_liquidity_a > delta_liquidity_b:
        necessary_amount_a = (deposited_amount_b * reserve_a) // reserve_b
        necessary_amount_b = deposited_amount_b
        lp_amount = delta_liquidity_b
    elif delta_liquidity_a < delta_liquidity_b:
        necessary_amount_a = deposited_amount_a
        necessary_amount_b = (deposited_amount_a * reserve_b) // reserve_a
        lp_amount = delta_liquidity_a
    else:
        necessary_amount_a = deposited_amount_a
        necessary_amount_b = deposited_amount_b
        lp_amount = delta_liquidity_a

    return {
        "necessaryAmountA": necessary_amount_a,
        "necessaryAmountB": necessary_amount_b,
        "lpAmount": lp_amount,
    }

def calculate_withdraw(options: Dict[str, Any]) -> Dict[str, Any]:
    withdrawal_lp_amount = options["withdrawalLPAmount"]
    reserve_a = options["reserveA"]
    reserve_b = options["reserveB"]
    total_liquidity = options["totalLiquidity"]

    amount_a_receive = (withdrawal_lp_amount * reserve_a) // total_liquidity
    amount_b_receive = (withdrawal_lp_amount * reserve_b) // total_liquidity

    return {
        "amountAReceive": amount_a_receive,
        "amountBReceive": amount_b_receive,
    }

def calculate_zap_in(options: Dict[str, Any]) -> int:
    amount_in = options["amountIn"]
    reserve_in = options["reserveIn"]
    reserve_out = options["reserveOut"]
    total_liquidity = options["totalLiquidity"]

    swap_amount_in = (
        (sqrt(1997 ** 2 * reserve_in ** 2 + 4 * 997 * 1000 * amount_in * reserve_in) - 1997 * reserve_in) //
        (2 * 997)
    )
    swap_to_asset_out_amount = calculate_swap_exact_in({
        "amountIn": swap_amount_in,
        "reserveIn": reserve_in,
        "reserveOut": reserve_out,
    })["amountOut"]

    return (swap_to_asset_out_amount * total_liquidity) // (reserve_out - swap_to_asset_out_amount)
