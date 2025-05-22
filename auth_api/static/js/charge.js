const contractAddress = "0xacF4DF2C9C3deb0f4fb8e632421d16e3D22b5a93";
const contractABI = [
  "function EscrowDeposit(uint256 amount) external payable",
  "function viewMyDeposits() external view returns (uint256)",
];

async function depositETH(event) {
  event.preventDefault();

  const amount = document.getElementById("ethAmount").value;
  const status = document.getElementById("status");
  const btn = document.querySelector(".btn-primary");

  if (!amount) return alert("금액 입력하세요");

  try {
    if (!window.ethereum) {
      alert("메타마스크 설치 필요!");
      return;
    }

    btn.disabled = true;
    status.innerText = "⏳ 트랜잭션 전송 중...";

    const provider = new ethers.providers.Web3Provider(window.ethereum);
    const signer = provider.getSigner();
    const contract = new ethers.Contract(contractAddress, contractABI, signer);
    const weiAmount = ethers.utils.parseEther(amount);

    const timeout = setTimeout(() => {
      status.innerText = "⚠️ 응답 지연 중입니다. 지갑을 다시 확인하세요.";
    }, 60000); // 60초 타임아웃

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
  }
finally {
    btn.disabled = false;
  }
}