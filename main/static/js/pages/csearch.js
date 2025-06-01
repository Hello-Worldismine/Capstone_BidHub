// 전역 변수
let minPrice = null;
let maxPrice = null;
let priceButtonsClicked = [];
<<<<<<< Updated upstream

// DOM 로드 완료 시 초기화
document.addEventListener("DOMContentLoaded", function () {
=======
let searchTimeout = null;

// DOM 로드 완료 시 초기화
document.addEventListener("DOMContentLoaded", function () {
    console.log('조건검색 페이지 로드 완료');
    
>>>>>>> Stashed changes
    // 기본적으로 물건종류 탭 활성화
    const typeButton = document.querySelector('button[onclick="toggleFilter(\'type\')"]');
    if (typeButton) {
        typeButton.classList.add('active');
    }
    
    // 물건종류 필터 그룹 보이기
    const typeGroup = document.getElementById('filter-type');
    if (typeGroup) {
        typeGroup.classList.remove('hidden');
    }
    
    // 다른 필터 그룹들은 숨기기
    const priceGroup = document.getElementById('filter-price');
    const failGroup = document.getElementById('filter-fail');
    
    if (priceGroup) priceGroup.classList.add('hidden');
    if (failGroup) failGroup.classList.add('hidden');
<<<<<<< Updated upstream
=======
    
    // 초기 로드 시 전체 목록 표시
    setTimeout(() => {
        executeSearch();
    }, 500);
>>>>>>> Stashed changes
});

// 필터 탭 토글 함수
function toggleFilter(id) {
    try {
        // 모든 필터 그룹 숨기기
        document.querySelectorAll('.filter-group').forEach(group => {
            group.classList.add('hidden');
        });
        
        // 모든 탭 버튼 비활성화
        document.querySelectorAll('.filter-toggle').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // 선택된 필터 그룹 보이기
        const targetGroup = document.getElementById('filter-' + id);
        const targetButton = event.target; // 클릭된 버튼
        
        if (targetGroup) {
            // 이미 활성화된 탭을 다시 클릭하면 숨기기
            if (targetButton.classList.contains('active')) {
                targetGroup.classList.add('hidden');
                targetButton.classList.remove('active');
            } else {
                // 새로운 탭 활성화
                targetGroup.classList.remove('hidden');
                targetButton.classList.add('active');
            }
        }
        
    } catch (error) {
        console.error('Error toggling filter:', error);
    }
}

// 일반 필터 선택 함수
function selectFilter(btn) {
    if (btn) {
<<<<<<< Updated upstream
        btn.classList.toggle('selected');
        // 필터 변경 시 자동으로 검색 실행
        executeSearch();
=======
        // 토글 방식으로 선택/해제
        if (btn.classList.contains('selected')) {
            btn.classList.remove('selected');
        } else {
            btn.classList.add('selected');
        }
        
        // 디바운스를 이용한 검색 실행
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        searchTimeout = setTimeout(() => {
            executeSearch();
        }, 500); // 0.5초 후 실행
>>>>>>> Stashed changes
    }
}

// 모든 필터 초기화 함수
function resetFilters() {
    try {
        // 모든 필터 버튼의 스타일 초기화
        document.querySelectorAll('.filter-group button').forEach(b => {
            b.classList.remove('selected', 'selected-min', 'selected-max');
        });

        // 입찰금 관련 상태값 초기화
        minPrice = null;
        maxPrice = null;
        priceButtonsClicked = [];

        // UI에 표시된 금액 초기화
        const minPriceLabel = document.getElementById("minPriceLabel");
        const maxPriceLabel = document.getElementById("maxPriceLabel");
        
        if (minPriceLabel) minPriceLabel.innerText = "최소";
        if (maxPriceLabel) maxPriceLabel.innerText = "최대";
        
<<<<<<< Updated upstream
        // AJAX로 전체 목록 가져오기
        fetch('/csearch/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newResults = doc.querySelector('.search-results');
            
            if (newResults) {
                const currentResults = document.querySelector('.search-results');
                if (currentResults) {
                    currentResults.innerHTML = newResults.innerHTML;
                }
            }
        })
        .catch(error => {
            console.error('Error resetting filters:', error);
        });
=======
        // 전체 목록으로 리셋
        console.log('Resetting filters');
        executeSearch();
>>>>>>> Stashed changes
        
    } catch (error) {
        console.error('Error resetting filters:', error);
    }
}

// 가격 텍스트를 숫자로 변환하는 함수
function parsePriceToNumber(priceText) {
    if (!priceText || typeof priceText !== 'string') return 0;
    
    try {
        if (priceText.includes("천")) {
            return parseInt(priceText.replace("천", "")) * 10000000;  // 5천 → 50,000,000
        } else if (priceText.includes("억")) {
            if (priceText === "18억~") {
                return 1800000001;
            }
            return parseInt(priceText.replace("억", "")) * 100000000;
        }
        return 0;
    } catch (error) {
        console.error('Error parsing price:', error);
        return 0;
    }
}

<<<<<<< Updated upstream
// 가격 버튼 선택 함수 - 자동 검색 추가
=======
// 가격 버튼 선택 함수
>>>>>>> Stashed changes
function selectPrice(button) {
    if (!button) return;
    
    try {
        // 모든 버튼에서 기존 클래스 제거
        document.querySelectorAll('.price-button').forEach(b => {
            b.classList.remove('selected', 'selected-min', 'selected-max');
        });

        // 클릭 기록 저장 (최대 2개)
        priceButtonsClicked.push(button);
        if (priceButtonsClicked.length > 2) {
            priceButtonsClicked.shift();
        }

        if (priceButtonsClicked.length === 1) {
            // 하나만 클릭했을 경우: 기본 selected 표시
            priceButtonsClicked[0].classList.add("selected");
            const val = parsePriceToNumber(priceButtonsClicked[0].innerText);
            minPrice = val;
            maxPrice = null;
            updatePriceLabels();
        } else if (priceButtonsClicked.length === 2) {
            const [btn1, btn2] = priceButtonsClicked;
            const val1 = parsePriceToNumber(btn1.innerText);
            const val2 = parsePriceToNumber(btn2.innerText);

            let minBtn, maxBtn;
            if (val1 <= val2) {
                minBtn = btn1;
                maxBtn = btn2;
                minPrice = val1;
                maxPrice = val2;
            } else {
                minBtn = btn2;
                maxBtn = btn1;
                minPrice = val2;
                maxPrice = val1;
            }

            minBtn.classList.add("selected-min");
            maxBtn.classList.add("selected-max");
            updatePriceLabels();
        }
        
<<<<<<< Updated upstream
        // 가격 필터 변경 시 자동으로 검색 실행
        executeSearch();
=======
        // 디바운스를 이용한 검색 실행
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        searchTimeout = setTimeout(() => {
            executeSearch();
        }, 500); // 0.5초 후 실행
>>>>>>> Stashed changes
        
    } catch (error) {
        console.error('Error selecting price:', error);
    }
}

// 가격 라벨 업데이트 함수
function updatePriceLabels() {
    const minPriceLabel = document.getElementById("minPriceLabel");
    const maxPriceLabel = document.getElementById("maxPriceLabel");
    
    if (minPriceLabel) {
        minPriceLabel.innerText = minPrice !== null ? formatKoreanPrice(minPrice) : "최소";
    }
    if (maxPriceLabel) {
        maxPriceLabel.innerText = maxPrice !== null ? formatKoreanPrice(maxPrice) : "최대";
    }
}

// 한국식 가격 포맷 함수
function formatKoreanPrice(num) {
    if (num === null || num === undefined) return "0";
    
    try {
        if (num === 0) {
            return "0";
        } else if (num >= 1800000000) {
            return "18억~";
        } else if (num >= 100000000) {
            return (num / 100000000) + "억";
        } else if (num >= 10000000) {
            return (num / 10000000) + "천";
        } else {
            return Math.floor(num / 10000) + "만";
        }
    } catch (error) {
        console.error('Error formatting price:', error);
        return "0";
    }
}

<<<<<<< Updated upstream
// 가격 조정 함수 - 자동 검색 추가
=======
// 가격 조정 함수
>>>>>>> Stashed changes
function adjustPrice(type, direction) {
    if (type !== "min" && type !== "max") return;
    if (direction !== "up" && direction !== "down") return;
    
    try {
        let price = (type === "min") ? minPrice : maxPrice;

        if (price === null) {
            // 가격이 설정되지 않은 경우 기본값 설정
            price = (type === "min") ? 0 : 50000000;
        }

        if (direction === "up") {
            price += 50000000;
            if (price > 1800000000) price = 1800000000;  // 상한선 고정
        } else if (direction === "down") {
            price -= 50000000;
            if (price < 0) price = 0;
        }

        if (type === "min") {
            minPrice = price;
        } else {
            maxPrice = price;
        }

        // 최소값이 최대값보다 클 경우 초기화
        if (minPrice !== null && maxPrice !== null && minPrice > maxPrice) {
            alert("최소 금액이 최대 금액보다 클 수 없습니다.");
            resetPriceSelection();
            return;
        }

        updatePriceLabels();
        updatePriceButtonStyles();
        
<<<<<<< Updated upstream
        // 가격 조정 시 자동으로 검색 실행
        executeSearch();
=======
        // 디바운스를 이용한 검색 실행
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        searchTimeout = setTimeout(() => {
            executeSearch();
        }, 500); // 0.5초 후 실행
>>>>>>> Stashed changes
        
    } catch (error) {
        console.error('Error adjusting price:', error);
    }
}

// 가격 선택 초기화 함수
function resetPriceSelection() {
    try {
        minPrice = null;
        maxPrice = null;
        priceButtonsClicked = [];
        
        // 모든 가격 버튼 스타일 초기화
        document.querySelectorAll('.price-button').forEach(b => {
            b.classList.remove('selected', 'selected-min', 'selected-max');
        });
        
        updatePriceLabels();
    } catch (error) {
        console.error('Error resetting price selection:', error);
    }
}

// 가격 버튼 스타일 업데이트 함수
function updatePriceButtonStyles() {
    try {
        // 모든 버튼 초기화
        document.querySelectorAll('.price-button').forEach(b => {
            b.classList.remove('selected', 'selected-min', 'selected-max');
        });
        
        // 현재 설정된 가격에 맞는 버튼 찾기 및 스타일 적용
        document.querySelectorAll('.price-button').forEach(button => {
            const buttonValue = parsePriceToNumber(button.innerText);
            
            if (minPrice !== null && buttonValue === minPrice) {
                if (maxPrice !== null && maxPrice !== minPrice) {
                    button.classList.add('selected-min');
                } else {
                    button.classList.add('selected');
                }
            }
            
            if (maxPrice !== null && buttonValue === maxPrice && maxPrice !== minPrice) {
                button.classList.add('selected-max');
            }
        });
    } catch (error) {
        console.error('Error updating price button styles:', error);
    }
}

<<<<<<< Updated upstream
// 디바운스 함수 추가 (너무 빈번한 요청 방지)
let searchTimeout = null;

// 검색 실행 함수 - AJAX로 변경
function executeSearch() {
    try {
        // 이전 타이머 취소
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        // 300ms 후에 검색 실행 (디바운스)
        searchTimeout = setTimeout(() => {
            const params = new URLSearchParams();
            
            // 선택된 물건종류 수집
            const selectedTypes = [];
            document.querySelectorAll('#filter-type .selected').forEach(btn => {
                selectedTypes.push(btn.innerText.trim());
            });
            
            selectedTypes.forEach(type => {
                params.append('item_types', type);
            });
            
            // 가격 필터 추가
            if (minPrice !== null) {
                params.append('min_price', minPrice);
            }
            if (maxPrice !== null) {
                params.append('max_price', maxPrice);
            }
            
            // 유찰횟수 필터 추가
            const selectedFailure = document.querySelector('#filter-fail .selected');
            if (selectedFailure) {
                params.append('failure_count', selectedFailure.innerText.trim());
            }
            
            // 디버깅용 콘솔 로그
            console.log('Search parameters:', {
                minPrice: minPrice,
                maxPrice: maxPrice,
                selectedTypes: selectedTypes,
                selectedFailure: selectedFailure?.innerText?.trim(),
                queryString: params.toString()
            });
            
            // AJAX 요청으로 검색 결과 가져오기
            fetch(`/csearch/?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                console.log('Search response received');
                // HTML 파싱하여 검색 결과 영역만 추출
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newResults = doc.querySelector('.search-results');
                
                if (newResults) {
                    // 기존 검색 결과를 새로운 결과로 교체
                    const currentResults = document.querySelector('.search-results');
                    if (currentResults) {
                        currentResults.innerHTML = newResults.innerHTML;
                        console.log('Search results updated');
                    }
                } else {
                    console.log('No search results found in response');
                }
            })
            .catch(error => {
                console.error('Error fetching search results:', error);
            });
            
        }, 300);
=======
// 로딩 상태 표시 함수
function showLoading() {
    const resultList = document.querySelector('.result-list');
    if (resultList) {
        resultList.innerHTML = `
            <div class="loading-message" style="text-align: center; padding: 50px;">
                <p>검색 중...</p>
                <div style="margin: 20px 0;">
                    <div style="display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                </div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
    }
}

// 페이지 이동 함수 - AJAX 방식으로 수정
function goToPage(pageNumber) {
    executeSearch(pageNumber);
}

// 검색 실행 함수 - 페이지 번호 매개변수 추가
function executeSearch(page = 1) {
    try {
        const params = new URLSearchParams();
        
        // 페이지 번호 추가
        if (page > 1) {
            params.append('page', page);
        }
        
        // 선택된 물건종류 수집
        const selectedTypes = [];
        document.querySelectorAll('#filter-type .selected').forEach(btn => {
            selectedTypes.push(btn.innerText.trim());
        });
        
        selectedTypes.forEach(type => {
            params.append('item_types', type);
        });
        
        // 가격 필터 추가
        if (minPrice !== null) {
            params.append('min_price', minPrice);
        }
        if (maxPrice !== null) {
            params.append('max_price', maxPrice);
        }
        
        // 유찰횟수 필터 추가
        const selectedFailure = document.querySelector('#filter-fail .selected');
        if (selectedFailure) {
            params.append('failure_count', selectedFailure.innerText.trim());
        }
        
        // 디버깅용 콘솔 로그
        console.log('Search parameters:', {
            page: page,
            minPrice: minPrice,
            maxPrice: maxPrice,
            selectedTypes: selectedTypes,
            selectedFailure: selectedFailure?.innerText?.trim(),
            queryString: params.toString()
        });
        
        // 로딩 상태 표시
        showLoading();
        
        // AJAX 요청으로 검색 결과 가져오기
        fetch(`/csearch/?${params.toString()}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            console.log('Search response received');
            
            // HTML 파싱하여 검색 결과 영역만 추출
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newResults = doc.querySelector('.result-list');
            
            if (newResults) {
                // 기존 검색 결과를 새로운 결과로 교체
                const currentResults = document.querySelector('.result-list');
                if (currentResults) {
                    currentResults.innerHTML = newResults.innerHTML;
                    console.log('Search results updated successfully');
                    
                    // URL 업데이트 (브라우저 히스토리 관리)
                    const newUrl = `/csearch/?${params.toString()}`;
                    window.history.pushState(null, '', newUrl);
                }
            } else {
                console.log('No search results found in response');
                const currentResults = document.querySelector('.result-list');
                if (currentResults) {
                    currentResults.innerHTML = '<p class="no-result" style="text-align: center; padding: 50px;">검색 조건에 맞는 결과가 없습니다.</p>';
                }
            }
        })
        .catch(error => {
            console.error('Error fetching search results:', error);
            const currentResults = document.querySelector('.result-list');
            if (currentResults) {
                currentResults.innerHTML = `
                    <div class="error-message" style="text-align: center; padding: 50px; color: #e74c3c;">
                        <p>검색 중 오류가 발생했습니다.</p>
                        <p><small>잠시 후 다시 시도해주세요.</small></p>
                    </div>
                `;
            }
        });
>>>>>>> Stashed changes
        
    } catch (error) {
        console.error('Error executing search:', error);
    }
<<<<<<< Updated upstream
}
=======
}
>>>>>>> Stashed changes
