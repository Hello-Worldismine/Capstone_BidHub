document.addEventListener('DOMContentLoaded', function () {
    const {
        csrfToken,
        bidder,
        tradeNum
    } = window.BIDFORM_CONTEXT;

    // ─── 헬퍼 함수 ───────────────────────────────
    function formatNumber(input) {
        input.addEventListener('input', function () {
            let value = this.value.replace(/[^0-9]/g, '');
            this.value = parseInt(value || 0);
        });
    }

    const BID_ACTION_PUTSEC = 0;

    async function getNonce(address) {
        const res = await fetch(`/api/get_nonce/?user=${address}&action_index=${BID_ACTION_PUTSEC}`);
        const data = await res.json();
        return data.nonce;
    }
    
    async function signBidData(trade_num, amount, security, bid_time, nonce) {
        const message = `${trade_num}${amount}${security}${bid_time}${nonce}`;
        const from = ethereum.selectedAddress;
        const signature = await ethereum.request({
            method: 'personal_sign',
            params: [message, from],
        });
        return signature;
    }


    // ─── 초기 로딩 시 법원 select 동기화 ───────────
    const courtOptions = {
        all: [
            "서울중앙지방법원",
            "서울동부지방법원",
            "서울남부지방법원",
            "서울서부지방법원",
            "수원지방법원"
        ],
        seoul: [
            "서울중앙지방법원",
            "서울동부지방법원",
            "서울남부지방법원",
            "서울서부지방법원"
        ],
        gyeonggi: [
            "수원지방법원"
        ]
    };

    function updateCourtOptions(region) {
        const courtSelect = document.getElementById("court");
        courtSelect.innerHTML = "";
        courtOptions[region].forEach(court => {
            const option = document.createElement("option");
            option.value = court;
            option.textContent = court;
            courtSelect.appendChild(option);
        });
    }

    document.getElementById("region").addEventListener("change", function () {
        updateCourtOptions(this.value);
    });

    updateCourtOptions("all");

    // ─── 폼 제출 처리 ──────────────────────────────


    document.getElementById("bidForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const bidAmount1 = document.getElementById("bidAmount1").value;
    const bidAmount2 = document.getElementById("bidAmount2").value;
    const password1 = document.getElementById("password1").value;
    const password2 = document.getElementById("password2").value;
    const deposit = document.getElementById("deposit").value;
    const bid_time = Math.floor(Date.now() / 1000);

    const KRW_PER_ETH = 10000000000;
    const krwDeposit = BigInt(deposit);
    const weiDeposit = krwDeposit * 100000000n;

    if (bidAmount1 !== bidAmount2) {
        alert("입찰가가 일치하지 않습니다.");
        return;
    }

    if (password1 !== password2) {
        alert("비밀번호가 일치하지 않습니다.");
        return;
    }

    try {
        // 1. nonce 조회
        const nonce = await getNonce(bidder);

        // 2. 서명 (msg = keccak256(abi.encodePacked(trade_num, nonce, security)))
        const bn = (v) => BigInt(v).toString();
        const hash = ethers.utils.solidityKeccak256(
            ["uint64", "uint256", "uint80"],
            [bn(tradeNum), bn(nonce), bn(weiDeposit)]
        );

        const signature = await ethereum.request({
            method: "personal_sign",
            params: [hash, bidder]
        });

        // 3. putSec 호출
        const res = await fetch("/api/put_sec/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                trade_num: parseInt(tradeNum),
                bidder: bidder,
                security: weiDeposit.toString(),
                amount: bidAmount1,
                nonce: nonce,
                signature: signature,
                bid_time: bid_time 
            })
        });

        const result = await res.json();
        if (result.status === "success") {
            alert("입찰 성공! TX Hash: " + result.tx_hash);
            window.location.href = "/bid_history/";
        } else {
            alert("실패: " + result.message);
        }
    } catch (err) {
        alert("요청 실패: " + err);
    }
});


    // ─── 기타 입력 처리 (포맷/유효성 등) ─────────────
    const bidAmount1Field = document.getElementById("bidAmount1");
    const bidAmount2Field = document.getElementById("bidAmount2");

    bidAmount1Field.addEventListener("input", function () {
        bidAmount2Field.value = '';
    });

    bidAmount2Field.addEventListener("input", function () {
        this.style.borderColor = this.value !== bidAmount1Field.value ? "#e74c3c" : "";
    });

    document.getElementById("password2").addEventListener("input", function () {
        const p1 = document.getElementById("password1").value;
        this.style.borderColor = this.value !== p1 ? "#e74c3c" : "";
    });

    formatNumber(bidAmount1Field);
    formatNumber(bidAmount2Field);
});
