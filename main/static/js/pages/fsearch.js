
document.addEventListener('DOMContentLoaded', function() {
    // DOM 요소들 가져오기
    const searchForm = document.querySelector('.search-box form');
    const courtSelect = document.getElementById('court');
    const yearInput = document.querySelector('input[name="year"]');
    const numberInput = document.querySelector('input[name="number"]');
    const searchBtn = document.querySelector('.search-btn');
    const resultList = document.querySelector('.result-list');

    // 폼 유효성 검사 - 법원 필수만
    function validateForm() {
        const court = courtSelect.value.trim();
        const year = yearInput.value.trim();
        const number = numberInput.value.trim();

        // 법원 선택 필수
        if (!court) {
            alert('법원을 선택해주세요.');
            courtSelect.focus();
            return false;
        }

        // 연도가 입력된 경우에만 유효성 검사
        if (year) {
            if (year.length !== 4 || !/^\d{4}$/.test(year)) {
                alert('연도는 4자리 숫자로 입력해주세요.');
                yearInput.focus();
                return false;
            }

            const currentYear = new Date().getFullYear();
            const inputYear = parseInt(year);
            if (inputYear < 2000 || inputYear > currentYear + 1) {
                alert(`연도는 2000년부터 ${currentYear + 1}년 사이로 입력해주세요.`);
                yearInput.focus();
                return false;
            }
        }

        // 사건번호가 입력된 경우에만 유효성 검사
        if (number) {
            if (!/^\d+$/.test(number)) {
                alert('사건번호는 숫자만 입력해주세요.');
                numberInput.focus();
                return false;
            }

            if (number.length > 6) {
                alert('사건번호는 최대 6자리까지 입력 가능합니다.');
                numberInput.focus();
                return false;
            }
        }

        return true;
    }

    // 입력 필드 실시간 유효성 검사
    yearInput.addEventListener('input', function(e) {
        this.value = this.value.replace(/[^0-9]/g, '');
        if (this.value.length > 4) {
            this.value = this.value.slice(0, 4);
        }
    });

    numberInput.addEventListener('input', function(e) {
        this.value = this.value.replace(/[^0-9]/g, '');
        if (this.value.length > 6) {
            this.value = this.value.slice(0, 6);
        }
    });

    // Enter 키 검색
    yearInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });

    numberInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });

    // 폼 제출 이벤트 처리
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        performSearch();
    });

    // 검색 수행 함수
    function performSearch() {
        if (!validateForm()) {
            return;
        }

        showLoading();
        
        const court = courtSelect.value.trim();
        const year = yearInput.value.trim();
        const number = numberInput.value.trim();
        
        const searchParams = new URLSearchParams();
        
        // 법원은 항상 포함 (필수)
        searchParams.append('court', court);
        
        // 입력된 파라미터만 추가
        if (year) searchParams.append('year', year);
        if (number) searchParams.append('number', number);

        // AJAX 검색
        fetch(`/api/search-cases/?${searchParams.toString()}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => {
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`HTTP ${response.status}: ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Search results:', data);
            hideLoading();
            displayResults(data.results || []);
        })
        .catch(error => {
            hideLoading();
            console.error('검색 오류:', error);
            displayError(`검색 중 오류가 발생했습니다: ${error.message}`);
        });
    }

    function showLoading() {
        searchBtn.disabled = true;
        searchBtn.textContent = '검색 중...';
        resultList.innerHTML = `
            <div class="loading-message">
                <p>⏳ 검색 중입니다...</p>
            </div>
        `;
    }

    function hideLoading() {
        searchBtn.disabled = false;
        searchBtn.textContent = '검색';
    }

    function getCsrfToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                         '';
        return csrfToken;
    }

    function displayResults(results) {
        if (!results || results.length === 0) {
            resultList.innerHTML = `<p class="no-result">검색 결과가 없습니다.</p>`;
            return;
        }

        let html = '';
        results.forEach(caseItem => {
            html += createResultCard(caseItem);
        });
        
        resultList.innerHTML = html;
        addResultCardListeners();
    }

    function createResultCard(caseItem) {
        const auctionItem = caseItem.auctionitem_set?.[0] || {};
        const schedules = caseItem.schedules || [];
        
        const valuationAmount = formatCurrency(auctionItem.valuation_amount);
        
        // 현재 매각 스케줄 찾기
        let currentSchedule = null;
        const now = new Date();
        
        for (const schedule of schedules) {
            if (schedule.schedule_type === '매각기일' && schedule.auction_date) {
                const auctionDate = new Date(schedule.auction_date);
                const daysDiff = (auctionDate.getTime() - now.getTime()) / (1000 * 3600 * 24);
                
                // 가장 가까운 미래 매각기일 선택
                if (daysDiff >= -1) {
                    currentSchedule = schedule;
                    break;
                }
            }
        }
        
        return `
            <div class="result-card" data-case-id="${caseItem.case_number}">
                <div class="thumbnail">
                    <img src="/static/img/bidhub-logo.png" 
                         alt="물건 이미지" 
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                    <div class="no-image" style="display: none;">이미지 없음</div>
                </div>
                <div class="card-info">
                    <h3 class="case-number" data-case-id="${caseItem.case_number}">
                        ${caseItem.case_number}
                    </h3>
                    <p><strong>법원:</strong> ${caseItem.court}</p>
                    <p><strong>사건명:</strong> ${caseItem.case_name || '정보없음'}</p>
                    <p><strong>감정평가액:</strong> ${valuationAmount}</p>
                    <p><strong>유찰횟수:</strong> ${auctionItem.auction_failures || 0}회</p>
                    <p><strong>물건용도:</strong> ${auctionItem.item_purpose || '정보없음'}</p>
                    <p><strong>주소:</strong> ${auctionItem.item_note || '주소 정보 없음'}</p>
                    ${currentSchedule ? `
                        <p><strong>매각기일:</strong> ${formatDate(currentSchedule.auction_date)}</p>
                        <p><strong>최저가격:</strong> ${formatCurrency(currentSchedule.minimum_price)}</p>
                    ` : auctionItem.auction_date ? `
                        <p><strong>매각기일:</strong> ${formatDate(auctionItem.auction_date)}</p>
                    ` : ''}
                    <button class="favorite-btn" data-case-number="${caseItem.case_number}">
                        <i class="fa-regular fa-star"></i> 즐겨찾기
                    </button>
                </div>
            </div>
        `;
    }

    function displayError(message) {
        resultList.innerHTML = `
            <div class="error-message">
                <p>${message}</p>
            </div>
        `;
    }

    function addResultCardListeners() {
        document.querySelectorAll('.case-number').forEach(element => {
            element.addEventListener('click', function() {
                const caseId = this.dataset.caseId;
                window.location.href = `/tender/${encodeURIComponent(caseId)}/`;
            });
        });

        // 즐겨찾기 버튼 처리
        document.querySelectorAll('.favorite-btn').forEach(button => {
            button.addEventListener('click', function() {
                const caseNumber = this.dataset.caseNumber;
                toggleFavorite(caseNumber, this);
            });
        });
    }

    function toggleFavorite(caseNumber, button) {
        let favorites = JSON.parse(localStorage.getItem('favorites')) || [];
        const existingIndex = favorites.findIndex(f => f.caseNumber === caseNumber);
        const icon = button.querySelector('i');
        
        if (existingIndex === -1) {
            // 즐겨찾기 추가
            favorites.push({
                caseNumber: caseNumber,
                addedDate: new Date().toISOString()
            });
            
            icon.classList.remove('fa-regular');
            icon.classList.add('fa-solid');
            button.innerHTML = '<i class="fa-solid fa-star"></i> 즐겨찾기 해제';
        } else {
            // 즐겨찾기 제거
            favorites.splice(existingIndex, 1);
            icon.classList.remove('fa-solid');
            icon.classList.add('fa-regular');
            button.innerHTML = '<i class="fa-regular fa-star"></i> 즐겨찾기';
        }
        
        localStorage.setItem('favorites', JSON.stringify(favorites));
    }

    function formatCurrency(amount) {
        if (!amount) return '정보없음';
        const numAmount = typeof amount === 'string' ? 
            parseInt(amount.replace(/[^0-9]/g, '')) : amount;
        return formatWithComma(numAmount) + '원';
    }

    function formatWithComma(num) {
        if (!num) return '0';
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    function formatDate(dateString) {
        if (!dateString) return '정보없음';
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR') + ' ' + 
               date.toLocaleTimeString('ko-KR', {
                   hour: '2-digit',
                   minute: '2-digit'
               });
    }

    // 페이지 로드 시 URL 파라미터 확인하여 자동 검색
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('court')) {
        // URL에서 파라미터 읽어와서 폼 채우기
        courtSelect.value = urlParams.get('court') || '';
        yearInput.value = urlParams.get('year') || '';
        numberInput.value = urlParams.get('number') || '';
        
        // 자동 검색 실행
        setTimeout(() => {
            performSearch();
        }, 100);
    }
});