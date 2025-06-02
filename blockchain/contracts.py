
import os
import json
from web3 import Web3
from web3.exceptions import ContractLogicError
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=".env")

# Web3 설정
w3 = Web3(Web3.HTTPProvider(os.getenv("ALCHEMY_RPC")))
contract_address = Web3.to_checksum_address(os.getenv("CONTRACT_ADDRESS"))
operator_address = Web3.to_checksum_address(os.getenv("OPER_ADDRESS"))
private_key = os.getenv("PRIVATE_KEY")



abi_path = Path(__file__).resolve().parent / "contract_abi.json"
with open(abi_path, "r") as f:
    abi = json.load(f)

contract = w3.eth.contract(address=contract_address, abi=abi)

def build_and_send_tx(function_call):
    try:
        tx = function_call.build_transaction({
            'from': operator_address,
            'nonce': w3.eth.get_transaction_count(operator_address),
            'gas': 500_000,
            'gasPrice': w3.to_wei("2", "gwei")
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return {"status": "success", "tx_hash": tx_hash.hex()}

    except ContractLogicError as e:
        return {"status": "revert", "message": str(e)}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# 스마트컨트랙트 함수

def put_cryptogram(trade_num, p1, p2, p3, bidder, nonce, signature):
    return build_and_send_tx(contract.functions.putCryptogram(p1, p2, p3, trade_num, bidder, nonce, signature))

def input_decrypt(trade_num, amount, security, bidder, bid_time, due_date):
    return build_and_send_tx(contract.functions.inputDecrypt(trade_num, amount, security, bidder, bid_time, due_date))

def confirm_bid(trade_num):
    return contract.functions.confirmBid(trade_num).call()

def pay_for_award(amount, trade_num, bidder, nonce, signature):
    return build_and_send_tx(contract.functions.payForAward(amount, trade_num, bidder, nonce, signature))

def mark_additional_bid(trade_num, bidder, nonce, signature):
    return build_and_send_tx(contract.functions.markAdditionalBid(trade_num, bidder, nonce, signature))

def withdraw(amount, to_address, nonce, signature):
    return build_and_send_tx(contract.functions.Withdraw(amount, to_address, nonce, signature))

def escrow_deposit(amount_wei):
    try:
        tx = {
            'from': operator_address,
            'to': contract_address,
            'value': amount_wei,
            'nonce': w3.eth.get_transaction_count(operator_address),
            'gas': 100_000,
            'gasPrice': w3.to_wei("2", "gwei")
        }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return {"status": "success", "tx_hash": tx_hash.hex()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def escrow_refund(trade_num):
    return build_and_send_tx(contract.functions.EscrowRefund(trade_num))

def collect_proceeds():
    return build_and_send_tx(contract.functions.Collectproceeds())

def get_cryptogram(trade_num):
    return contract.functions.getCryptogram(trade_num).call()

def get_nonce(user_address, action_index):
    return contract.functions.getNonce(user_address, action_index).call()

def view_deposits(user_address):
    return contract.functions.viewMyDeposits(user_address).call()

def get_balance():
    return contract.functions.getBalance().call()
