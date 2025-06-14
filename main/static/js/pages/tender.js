document.addEventListener("DOMContentLoaded", function () {
    // 전역 변수
    let currentIndex = 0;
    let imagePaths = [];
    
    // DOM 요소
    const mainImage = document.getElementById("mainImage");
    const modal = document.getElementById("imageModal");
    const modalImage = document.getElementById("modalImage");
    const closeBtn = document.querySelector(".close");
    const modalPrev = document.getElementById("modalPrev");
    const modalNext = document.getElementById("modalNext");

    // 이미지 관련 함수들
    function updateMainImage() {
        if (imagePaths.length > 0 && mainImage) {
            mainImage.src = imagePaths[currentIndex];
            const counter = document.getElementById("image-counter");
            if (counter) {
                counter.textContent = `${currentIndex + 1} / ${imagePaths.length}`;
            }
        }
    }

    function openModal(index) {
        currentIndex = index;
        if (modalImage && imagePaths.length > 0) {
            modalImage.src = imagePaths[currentIndex];
            modal.style.display = "block";
        }
    }

    function closeModal() {
        if (modal) {
            modal.style.display = "none";
        }
    }

    function showNextImage() {
        if (imagePaths.length > 0) {
            currentIndex = (currentIndex + 1) % imagePaths.length;
            if (modalImage) {
                modalImage.src = imagePaths[currentIndex];
            }
        }
    }

    function showPrevImage() {
        if (imagePaths.length > 0) {
            currentIndex = (currentIndex - 1 + imagePaths.length) % imagePaths.length;
            if (modalImage) {
                modalImage.src = imagePaths[currentIndex];
            }
        }
    }

    // 이벤트 리스너 설정
    function setupImageEventListeners() {
        if (mainImage) {
            mainImage.addEventListener("click", () => openModal(currentIndex));
        }

        document.querySelectorAll(".thumb").forEach((thumb, index) => {
            thumb.addEventListener("click", () => {
                currentIndex = index;
                updateMainImage();
            });
            thumb.addEventListener("dblclick", () => openModal(index));
        });

        if (closeBtn) {
            closeBtn.addEventListener("click", closeModal);
        }
        if (modalPrev) {
            modalPrev.addEventListener("click", showPrevImage);
        }
        if (modalNext) {
            modalNext.addEventListener("click", showNextImage);
        }

        if (modal) {
            modal.addEventListener("click", (e) => {
                if (e.target === modal) closeModal();
            });
        }
    }

    // 가격 포맷팅 함수들
    function formatToKorean(price) {
        const oku = Math.floor(price / 100000000);
        const man = Math.floor((price % 100000000) / 10000);
        let result = "";
        if (oku > 0) result += oku + "억 ";
        if (man > 0) result += man + "만원";
        return result.trim();
    }

    function parseNumber(str) {
        return parseInt(str.replaceAll(",", "").replace(/[^0-9]/g, ""), 10) || 0;
    }

    function formatWithComma(num) {
        return num.toLocaleString("ko-KR");
    }

    // 가격 및 입찰 검증 설정
    function setupPriceValidation() {
        const priceBlock = document.querySelector(".price");
        const bidInput = document.getElementById("bid-price");
        const submitBtn = document.querySelector(".submit-btn");

        if (priceBlock) {
            const fullText = priceBlock.textContent.trim();
            const match = fullText.match(/[0-9,]+/);

            if (match) {
                const price = parseNumber(match[0]);
                const formatted = formatToKorean(price);

                // 가격 블럭 표기 변경 (510,000,000 → 5억 100만원)
                priceBlock.innerHTML = priceBlock.innerHTML.replace(match[0], formatted);

                // 입력 필드 이벤트 처리
                if (bidInput && submitBtn) {
                    bidInput.addEventListener("input", function () {
                        let raw = parseNumber(bidInput.value);
                        bidInput.value = formatWithComma(raw);

                        if (raw < price) {
                            submitBtn.disabled = true;
                            submitBtn.style.backgroundColor = "#ccc";
                            submitBtn.style.cursor = "not-allowed";
                            submitBtn.style.pointerEvents = "none";
                            submitBtn.innerText = `입찰 금액은 ${formatted} 이상이어야 합니다`;
                        } else {
                            submitBtn.disabled = false;
                            submitBtn.style.backgroundColor = "#3B82F6";
                            submitBtn.style.cursor = "pointer";
                            submitBtn.style.pointerEvents = "auto";
                            submitBtn.innerText = "입찰표 작성하기";
                        }
                    });
                }

                // 보증금 계산 (최저매각가격의 10%)
                const depositAmount = Math.floor(price * 0.1);
                const depositElement = document.getElementById('deposit-amount');
                if (depositElement) {
                    depositElement.textContent = formatWithComma(depositAmount) + '원';
                }
            }
        }
    }

    // 카운트다운 설정
    function setupCountdown(auctionDateStr) {
        if (auctionDateStr && auctionDateStr !== "None") {
            const targetDate = new Date(auctionDateStr);
            const now = new Date();
            const diffTime = targetDate - now;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            const countdownElement = document.getElementById('countdown-timer');
            if (countdownElement) {
                if (diffDays > 0) {
                    countdownElement.textContent = `D-${diffDays}`;
                    countdownElement.style.color = '#e74c3c';
                } else if (diffDays === 0) {
                    countdownElement.textContent = 'D-Day';
                    countdownElement.style.color = '#e74c3c';
                    countdownElement.style.fontWeight = 'bold';
                } else {
                    countdownElement.textContent = '마감';
                    countdownElement.style.color = '#95a5a6';
                }
            }
        }
    }

    // 외부에서 호출 가능한 함수들
    window.setMainImage = function (index) {
        currentIndex = index;
        updateMainImage();
    };

    window.prevImage = function () {
        currentIndex = (currentIndex - 1 + imagePaths.length) % imagePaths.length;
        updateMainImage();
    };

    window.nextImage = function () {
        currentIndex = (currentIndex + 1) % imagePaths.length;
        updateMainImage();
    };

    // 즐겨찾기 함수
    window.addToFavorites = function (caseNumber, minBid, auctionDate) {
        let favorites = JSON.parse(localStorage.getItem('favorites')) || [];
        
        const exists = favorites.some(fav => fav.caseNumber === caseNumber);
        
        if (!exists) {
            favorites.push({
                caseNumber: caseNumber,
                minBid: minBid,
                deadline: auctionDate
            });
            
            localStorage.setItem('favorites', JSON.stringify(favorites));
            alert('관심 목록에 추가되었습니다.');
        } else {
            alert('이미 관심 목록에 있는 물건입니다.');
        }
    };

    // 이미지 경로 설정 함수 (템플릿에서 호출)
    window.setImagePaths = function (paths) {
        imagePaths = paths;
        updateMainImage();
    };

    // 초기화
    setupImageEventListeners();
    setupPriceValidation();
    
    // 전역 설정 함수 (템플릿에서 호출)
    window.initializePage = function (auctionDate) {
        setupCountdown(auctionDate);
    };
});