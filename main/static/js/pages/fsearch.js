document.addEventListener('DOMContentLoaded', function() {
    // DOM 요소들 가져오기
    const courtSelect = document.getElementById('court');
    const yearInput = document.querySelector('input[name="year"]');
    const numberInput = document.querySelector('input[name="number"]');
    const searchForm = document.querySelector('.search-box form');
    
    // 입력 필드 실시간 유효성 검사
    if (yearInput) {
        yearInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 4) {
                this.value = this.value.slice(0, 4);
            }
        });
    }

    if (numberInput) {
        numberInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 6) {
                this.value = this.value.slice(0, 6);
            }
        });
    }

    // 폼 제출 시 유효성 검사
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            if (!courtSelect || !courtSelect.value) {
                e.preventDefault();
                alert('법원을 선택해주세요.');
                if (courtSelect) courtSelect.focus();
                return false;
            }

            // 연도 유효성 검사
            if (yearInput && yearInput.value) {
                const year = yearInput.value.trim();
                if (year.length !== 4 || !/^\d{4}$/.test(year)) {
                    e.preventDefault();
                    alert('연도는 4자리 숫자로 입력해주세요.');
                    yearInput.focus();
                    return false;
                }

                const currentYear = new Date().getFullYear();
                const inputYear = parseInt(year);
                if (inputYear < 2000 || inputYear > currentYear + 1) {
                    e.preventDefault();
                    alert(`연도는 2000년부터 ${currentYear + 1}년 사이로 입력해주세요.`);
                    yearInput.focus();
                    return false;
                }
            }

            // 사건번호 유효성 검사
            if (numberInput && numberInput.value) {
                const number = numberInput.value.trim();
                if (!/^\d+$/.test(number)) {
                    e.preventDefault();
                    alert('사건번호는 숫자만 입력해주세요.');
                    numberInput.focus();
                    return false;
                }
            }
        });
    }

    // Enter 키 이벤트 처리
    if (yearInput) {
        yearInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (searchForm) {
                    searchForm.submit();
                }
            }
        });
    }

    if (numberInput) {
        numberInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (searchForm) {
                    searchForm.submit();
                }
            }
        });
    }
});

// 검색 결과 카드 호버 효과
function addCardHoverEffects() {
    const cards = document.querySelectorAll('.fav-card, .result-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'transform 0.2s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// 페이지 로드 완료 후 호버 효과 적용
window.addEventListener('load', function() {
    addCardHoverEffects();
});

// 통화 포맷팅 함수 (필요시)
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