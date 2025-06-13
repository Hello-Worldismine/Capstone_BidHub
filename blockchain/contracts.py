
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
        # ✅ 먼저 시뮬레이션 (revert 사유 추출)
        try:
            function_call.call({'from': operator_address})
        except ContractLogicError as e:
            msg = e.args[0] if len(e.args) > 0 else str(e)
            if "execution reverted:" in msg:
                revert_reason = msg.split("execution reverted:")[1].split("(")[0].strip()
            else:
                revert_reason = "Unknown revert reason"
            return {
                "status": "revert",
                "message": revert_reason
            }


        # ✅ 트랜잭션 실제 실행
        tx = function_call.build_transaction({
            'from': operator_address,
            'nonce': w3.eth.get_transaction_count(operator_address),
            'gas': 500_000,
            'gasPrice': w3.to_wei("2", "gwei")
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 1:
            return {"status": "success", "tx_hash": tx_hash.hex()}
        else:
            return {
                "status": "revert",
                "message": "Transaction reverted without explicit reason",
                "tx_hash": tx_hash.hex()
            }

    except ContractLogicError as e:
        msg = e.args[0] if len(e.args) > 0 else str(e)
        if "execution reverted:" in msg:
            revert_reason = msg.split("execution reverted:")[1].split("(")[0].strip()
        else:
            revert_reason = "Unknown revert reason"
        return {
            "status": "revert",
            "message": revert_reason
        }

    except Exception as e:
        # ✅ 여기서도 바이트 스트링 날리는 걸 제거
        return {"status": "error", "message": str(e).split(",")[0].strip()}

def inputbid(trade_num: int, amount: int, security: int, bidder: str, bid_time: int) -> dict:
    bidder = Web3.to_checksum_address(bidder)
    bid_time_utc = bid_time - 9 * 60 * 60

    return build_and_send_tx(
        contract.functions.inputBid(trade_num, amount, security, bidder, bid_time_utc)
    )
    
    
def putsec(trade_num, bidder, security, nonce, signature):
    bidder = Web3.to_checksum_address(bidder)
    return build_and_send_tx(contract.functions.putSec(trade_num, bidder, security, nonce, signature))


def confirm_bid(trade_num: int, due_date: int) -> dict:
    due_date_utc = due_date - 9 * 60 * 60  # == due_date - 9 hours in seconds
    return build_and_send_tx(
        contract.functions.confirmBid(trade_num, due_date_utc)
    )

def pay_for_award(amount, trade_num, bidder, nonce, signature):
    bidder = Web3.to_checksum_address(bidder)
    return build_and_send_tx(contract.functions.payForAward(amount, trade_num, bidder, nonce, signature))

def mark_additional_bid(trade_num, bidder, nonce, signature):
    bidder = Web3.to_checksum_address(bidder)
    return build_and_send_tx(contract.functions.markAdditionalBid(trade_num, bidder, nonce, signature))

def withdraw(amount, to_address, nonce, signature):
    to_address = Web3.to_checksum_address(to_address)
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
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return {"status": "success", "tx_hash": tx_hash.hex()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def escrow_refund(trade_num):
    return build_and_send_tx(contract.functions.EscrowRefund(trade_num))

def collect_proceeds():
    return build_and_send_tx(contract.functions.Collectproceeds())

def get_nonce(user_address, action_index):
    checksum_address = Web3.to_checksum_address(user_address)  # ✅ 체크섬 주소로 변환
    return contract.functions.getNonce(checksum_address, action_index).call()


def view_deposits(user_address):
    checksum_address = Web3.to_checksum_address(user_address)
    return contract.functions.viewMyDeposits(checksum_address).call()

def get_balance():
    return contract.functions.getBalance().call()
