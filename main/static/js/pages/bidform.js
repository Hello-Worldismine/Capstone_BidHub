document.addEventListener('DOMContentLoaded', function () {
    const {
        csrfToken,
        bidder,
        tradeNum,
        auctionDate,
        currentTime
    } = window.BIDFORM_CONTEXT;

    // 사건 검색 함수
    window.searchCase = function() {
        const caseYear = document.getElementById('year-input').value;
        const caseSequence = document.getElementById('case-sequence').value;
        const court = document.getElementById('court').value;
        
        if (!caseYear || !caseSequence) {
            alert('년도와 사건번호를 모두 입력해주세요.');
            return;
        }
        
        // 현재 페이지를 검색 파라미터와 함께 리로드
        const searchParams = new URLSearchParams();
        searchParams.append('case_year', caseYear);
        searchParams.append('case_sequence', caseSequence);
        searchParams.append('court', court);
        
        window.location.href = `/bidform/?${searchParams.toString()}`;
    };

    // 입찰 시간 검증 함수
    function checkBiddingTimeWindow() {
        const auctionDateTime = new Date(auctionDate);
        const now = new Date();
        const biddingEndTime = new Date(auctionDateTime.getTime() + (60 * 60 * 1000)); // 1시간 후
        
        if (now < auctionDateTime) {
            return { 
                valid: false, 
                message: `입찰은 ${auctionDateTime.toLocaleString()}부터 시작됩니다.` 
            };
        }
        
        if (now > biddingEndTime) {
            return { 
                valid: false, 
                message: `입찰 시간이 ${biddingEndTime.toLocaleString()}에 종료되었습니다.` 
            };
        }
        
        return { valid: true, message: "" };
    }

    // 실시간 입찰 가능 시간 표시
    function updateBiddingStatus() {
        const timeCheck = checkBiddingTimeWindow();
        const statusElement = document.getElementById('bidding-status');
        
        if (!timeCheck.valid) {
            statusElement.innerHTML = `<span style="color: red;">${timeCheck.message}</span>`;
            document.querySelector('.btn-primary').disabled = true;
        } else {
            const auctionDateTime = new Date(auctionDate);
            const biddingEndTime = new Date(auctionDateTime.getTime() + (60 * 60 * 1000));
            const now = new Date();
            const remainingMinutes = Math.floor((biddingEndTime - now) / (1000 * 60));
            
            statusElement.innerHTML = `<span style="color: green;">입찰 가능 (남은 시간: ${remainingMinutes}분)</span>`;
            document.querySelector('.btn-primary').disabled = false;
        }
    }

    // 페이지 로드 시 및 1분마다 상태 업데이트
    updateBiddingStatus();
    setInterval(updateBiddingStatus, 60000);

    // ─── 헬퍼 함수 ───────────────────────────────
    function formatNumber(input) {
        input.addEventListener('input', function () {
            let value = this.value.replace(/[^0-9]/g, '');
            this.value = parseInt(value || 0);
        });
    }

    const BID_ACTION_PUTCRYPT = 0;

    async function getNonce(address) {
        const res = await fetch(`/api/get_nonce/?user=${address}&action_index=${BID_ACTION_PUTCRYPT}`);
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

    updateCourtOptions("all");    // ─── 폼 제출 처리 ──────────────────────────────
document.getElementById("bidForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    // 폼 검증
    if (!validateForm()) {
        return;
    }

    // 입찰 시간 검증
    const timeCheck = checkBiddingTimeWindow();
    if (!timeCheck.valid) {
        alert(timeCheck.message);
        return;
    }

    const bidAmount1 = document.getElementById("bidAmount1").value;
    const bidAmount2 = document.getElementById("bidAmount2").value;
    const password1 = document.getElementById("password1").value;
    const password2 = document.getElementById("password2").value;
    const deposit = document.getElementById("deposit").value;
    const bid_time = Math.floor(Date.now() / 1000);

    const KRW_PER_ETH = 10000000000;
    const krwDeposit = BigInt(deposit); // 원화 입력값 (예: "202000000")
    const weiDeposit = krwDeposit * 100000000n; // × 1e8

    // 제출 버튼 비활성화 및 로딩 상태 표시
    const submitButton = document.querySelector('.btn-primary');
    submitButton.disabled = true;
    submitButton.classList.add('loading');
    
    try {
        // 1. 암호화된 P1, P2, P3 받기
        const encRes = await fetch("/api/encrypt_bid/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                trade_num: parseInt(tradeNum),
                amount: parseInt(bidAmount1),
                security: weiDeposit.toString(),
                bidder: bidder,
                bid_time: bid_time
            })
        });

        const encData = await encRes.json();
        if (encData.status !== "success") {
            throw new Error("암호화 실패: " + encData.message);
        }

        const [p1, p2, p3] = encData.chunks;

        // 2. nonce 조회
        const nonce = await getNonce(bidder);

        // 3. 서명 (msg = keccak256(abi.encodePacked(trade_num, nonce, P1, P2, P3)))
        const bn = (v) => BigInt(v).toString();
        
        const hash = ethers.utils.solidityKeccak256(
            ["uint64", "uint256", "uint256", "uint256", "uint256"],
            [bn(tradeNum), bn(nonce), bn(p1), bn(p2), bn(p3)]
        );

        const signature = await ethereum.request({
            method: "personal_sign",
            params: [hash, bidder]
        });

        // 4. put_cryptogram 호출
        const res = await fetch("/api/put_cryptogram/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                trade_num: parseInt(tradeNum),
                p1: p1,
                p2: p2,
                p3: p3,
                bidder: bidder,
                security: weiDeposit.toString(),
                nonce: nonce,
                signature: signature
            })
        });        const result = await res.json(); 
        if (result.status === "success") {
            await fetch("/api/store_encrypted_bid/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({
                    trade_num: parseInt(tradeNum),
                    bidder: bidder,
                    bid_amount: parseInt(bidAmount1)  // or 암호화된 값
                })
            });
            
            alert("입찰 성공! TX Hash: " + result.tx_hash);
            window.location.href = "/bid_history/";
        } else if (result.status === "revert") {
            throw new Error(result.message);  // ← 여기에 require 메시지 (예: Invalid Signature)
        } else {
            throw new Error(result.message);
        }

    } catch (err) {
        console.error("입찰 처리 오류:", err);
        alert("입찰 처리 중 오류가 발생했습니다: " + err.message);
    } finally {
        // 제출 버튼 다시 활성화
        submitButton.disabled = false;
        submitButton.classList.remove('loading');
    }
});// ─── 기타 입력 처리 (포맷/유효성 등) ─────────────
    const bidAmount1Field = document.getElementById("bidAmount1");
    const bidAmount2Field = document.getElementById("bidAmount2");
    const password1Field = document.getElementById("password1");
    const password2Field = document.getElementById("password2");

    // 숫자 포맷팅 개선
    function formatNumber(input) {
        input.addEventListener('input', function () {
            let value = this.value.replace(/[^0-9]/g, '');
            this.value = value ? parseInt(value) : '';
        });
    }

    // 입찰가 실시간 검증
    bidAmount1Field.addEventListener("input", function () {
        bidAmount2Field.value = '';
        bidAmount2Field.classList.remove('error');
        
        // 최저매각가격보다 낮은 경우 경고
        const minPrice = parseInt(this.min) || 0;
        const currentValue = parseInt(this.value) || 0;
        
        if (currentValue > 0 && currentValue < minPrice) {
            this.classList.add('error');
        } else {
            this.classList.remove('error');
        }
    });

    bidAmount2Field.addEventListener("input", function () {
        const amount1 = parseInt(bidAmount1Field.value) || 0;
        const amount2 = parseInt(this.value) || 0;
        
        if (amount2 > 0 && amount1 !== amount2) {
            this.classList.add('error');
        } else {
            this.classList.remove('error');
        }
    });

    // 비밀번호 실시간 검증
    password2Field.addEventListener("input", function () {
        const password1 = password1Field.value;
        const password2 = this.value;
        
        if (password2.length > 0 && password1 !== password2) {
            this.classList.add('error');
        } else {
            this.classList.remove('error');
        }
    });

    // 폼 제출 시 추가 검증
    function validateForm() {
        let isValid = true;
        const errors = [];

        // 입찰가 검증
        const bidAmount1 = parseInt(bidAmount1Field.value) || 0;
        const bidAmount2 = parseInt(bidAmount2Field.value) || 0;
        const minPrice = parseInt(bidAmount1Field.min) || 0;

        if (bidAmount1 < minPrice) {
            errors.push("입찰가는 최저매각가격 이상이어야 합니다.");
            bidAmount1Field.classList.add('error');
            isValid = false;
        }

        if (bidAmount1 !== bidAmount2) {
            errors.push("입찰가가 일치하지 않습니다.");
            bidAmount2Field.classList.add('error');
            isValid = false;
        }

        // 비밀번호 검증
        const password1 = password1Field.value;
        const password2 = password2Field.value;

        if (password1 !== password2) {
            errors.push("비밀번호가 일치하지 않습니다.");
            password2Field.classList.add('error');
            isValid = false;
        }

        if (password1.length < 4) {
            errors.push("비밀번호는 4자리 이상이어야 합니다.");
            password1Field.classList.add('error');
            isValid = false;
        }

        if (!isValid) {
            alert(errors.join('\n'));
        }

        return isValid;
    }

    formatNumber(bidAmount1Field);
    formatNumber(bidAmount2Field);
    
    // 기존 폼 제출 핸들러에 검증 추가
    const originalSubmitHandler = document.getElementById("bidForm").onsubmit;
    document.getElementById("bidForm").addEventListener("submit", function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return false;
        }
        // 기존 로직 계속 실행
    });
});