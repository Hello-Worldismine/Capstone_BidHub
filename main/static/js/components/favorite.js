// 즐겨찾기 토글 함수
function toggleFavorite(caseNumber, iconElement) {
    // 로그인 확인
    if (!isUserAuthenticated()) {
        alert('로그인이 필요합니다.');
        window.location.href = getLoginUrl();
        return;
    }
    
    const heartIcon = iconElement.querySelector('.heart-icon');
    
    fetch(getToggleFavoriteUrl(), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({
            'case_number': caseNumber
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.action === 'added') {
                // 즐겨찾기 추가됨 - 빨간 속찬 하트
                heartIcon.classList.remove('far');
                heartIcon.classList.add('fas');
                // 인라인 스타일 제거 - CSS 클래스로 색상 관리
                showMessage(data.message, 'success');
            } else if (data.action === 'removed') {
                // 즐겨찾기 제거됨 - 회색 속빈 하트
                heartIcon.classList.remove('fas');
                heartIcon.classList.add('far');
                // 인라인 스타일 제거 - CSS 클래스로 색상 관리
                showMessage(data.message, 'info');
            }
        } else {
            alert('오류: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('즐겨찾기 처리 중 오류가 발생했습니다.');
    });
}

// 유틸리티 함수들
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function showMessage(message, type = 'info') {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#27ae60' : '#3498db'};
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        z-index: 10000;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        font-size: 14px;
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// 페이지별 설정 변수들 (각 템플릿에서 설정해야 함)
function isUserAuthenticated() {
    return window.USER_AUTHENTICATED || false;
}

function getLoginUrl() {
    return window.LOGIN_URL || '/accounts/login/';
}

function getToggleFavoriteUrl() {
    return window.TOGGLE_FAVORITE_URL || '/favorites/toggle/';
}