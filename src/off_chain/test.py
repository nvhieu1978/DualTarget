from opshin.ledger.interval import *
from opshin.ledger.api_v2 import *
ID: PolicyId
Tokenname: TokenName
fee: Value
ID="123"
Tokenname="432"
fee=[ID, [Tokenname, 100]]

from typing import Dict, Any

@dataclass()
class Asset(PlutusData):
    """
    A Asset, consisting of a PolicyId and TokenName
    """
    policy_id: PolicyId
    token_name: TokenName

# ADA asset instance
ADA = Asset(policy_id="", token_name="")
# ADA asset instance
DJED = Asset(policy_id="123", token_name="456")

# Assume you have a Value instance
value: Value = {
    b"": {b"": 10},
    b"policy_id_2": {b"token_name_3": 30},
}

value: Value ={
        ScriptHash(hex='e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72'): {AssetName(b'MIN'): 739}
        }

bytes.fromhex(    "e16c2dc8ae937e8d3790c7fd7168d7b994621ba14ca11415f39fed72"  ): { b"MIN": 11  }

print(f"DJED policy_id {DJED.policy_id}  token_name {DJED.token_name}")
print(value.get(b"policy_id_2", {b"token_name_3": 0}).get(b"token_name_3", 0))
# Accessing each element in the nested dictionary
# for policy_id, token_dict in value.items():
#     for token_name, amount in token_dict.items():
#         print(f"Policy ID: {policy_id}, Token Name: {token_name}, Amount: {amount}")

policy_id, token_dict = value
token_name, amount = token_dict.items(1)
print(f"Policy ID: {policy_id}, Token Name: {token_name}, Amount: {amount}")