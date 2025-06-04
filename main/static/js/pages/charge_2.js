// ✅ 필요한 상수들 먼저 정의
const contractAddress = "0xb06D2548C61486c1BF1f216d36984A7b253576C8";
const contractABI = [
  "function EscrowDeposit(uint256 amount) external payable",
  "function viewMyDeposits() external view returns (uint256)",
];

async function depositETH(event) {
  console.log("🚀 charge_2.js 최신 버전 실행됨");
  event.preventDefault();

  const krwInput = document.getElementById("ethAmount").value.trim();
  const status = document.getElementById("status");
  const btn = document.querySelector(".btn-primary");

  if (!krwInput || isNaN(krwInput)) {
    alert("금액을 숫자로 입력하세요");
    return;
  }

  try {
    if (!window.ethereum) {
      alert("메타마스크가 설치되어 있지 않습니다.");
      return;
    }

    btn.disabled = true;
    status.innerText = "⏳ 트랜잭션 전송 중...";

    const provider = new ethers.providers.Web3Provider(window.ethereum);
    const signer = provider.getSigner();
    const contract = new ethers.Contract(contractAddress, contractABI, signer);

    const KRW_PER_ETH = 10000000000; // 1 ETH = 100억 원
    const krw = parseFloat(krwInput);
    const ethAmount = krw / KRW_PER_ETH;
    const ethAmountStr = ethAmount.toFixed(18);
    const weiAmount = ethers.utils.parseUnits(ethAmountStr, "ether");

    console.log("KRW 입력:", krwInput);
    console.log("ETH 계산:", ethAmountStr);
    console.log("Wei:", weiAmount.toString());

    const timeout = setTimeout(() => {
      status.innerText = "⚠️ 응답 지연 중입니다. 지갑을 다시 확인하세요.";
    }, 60000);

    const tx = await contract.EscrowDeposit(weiAmount, {
      value: weiAmount,
      gasLimit: 300000
    });

    await tx.wait();
    clearTimeout(timeout);
    status.innerText = `✅ 입금 완료! Tx Hash: ${tx.hash}`;
  } catch (err) {
    console.error(err);
    let errorMsg = "❌ 트랜잭션 실패";

    if (err?.error?.message) {
      errorMsg = err.error.message;
    } else if (err?.data?.message) {
      errorMsg = err.data.message;
    } else if (err?.message) {
      errorMsg = err.message;
    }

    if (errorMsg.includes("execution reverted: ")) {
      errorMsg = errorMsg.split("execution reverted: ")[1];
    }

    status.innerText = "❌ 오류: " + errorMsg;
  } finally {
    btn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const userAddress = document.body.dataset.wallet;  // 템플릿에서 바디에 넣음
  if (!userAddress) return;

  try {
    const res = await fetch(`/api/view_deposits/?user=${userAddress}`);
    const data = await res.json();
    const krw = Number(data.deposits_krw).toLocaleString();
    document.getElementById("wallet-display").innerHTML =
      `<i class="fa-solid fa-won-sign"></i> 예치금 ${krw}원`;
  } catch (err) {
    console.error("예치금 조회 실패", err);
  }
});
