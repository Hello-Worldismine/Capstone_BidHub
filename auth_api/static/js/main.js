// 다크모드 토글 버튼
const toggleBtn = document.getElementById('toggle-theme-btn');

function setInitialTheme() {
  const saved = localStorage.getItem('theme');
  if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.body.classList.add('dark-mode');
    toggleBtn.textContent = '☀️ 라이트모드';
  }
}

setInitialTheme();

toggleBtn.addEventListener('click', () => {
  const isDark = document.body.classList.toggle('dark-mode');
  toggleBtn.textContent = isDark ? '☀️ 라이트모드' : '🌙 다크모드';
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
});

// 연도 입력 4자리 제한
const yearInput = document.getElementById('year-input');
yearInput.addEventListener('input', () => {
  if (yearInput.value.length > 4) {
    yearInput.value = yearInput.value.slice(0, 4);
  }
});

// 네비게이션 서브메뉴 표시
const menuItems = document.querySelectorAll('.menu-item');
menuItems.forEach(item => {
  item.addEventListener('mouseenter', () => {
    const submenu = item.querySelector('.submenu');
    if (submenu) submenu.style.display = 'block';
  });

  item.addEventListener('mouseleave', () => {
    const submenu = item.querySelector('.submenu');
    if (submenu) submenu.style.display = 'none';
  });
});

// 즐겨찾기 목록 로딩
let favorites = JSON.parse(localStorage.getItem('favorites')) || [];

// 즐겨찾기 테이블 업데이트
function updateFavoritesTable() {
  const tbody = document.querySelector('#favorites-table tbody');
  tbody.innerHTML = '';
  favorites.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.caseNumber}</td>
      <td>${item.minBid}</td>
      <td>${item.deadline}</td>
    `;
    tbody.appendChild(tr);
  });
}


// 별표 아이콘 상태 초기화
function updateStarIcons() {
  document.querySelectorAll('.auction-list .favorite-btn').forEach(btn => {
    const row = btn.closest('tr');
    const caseNumber = row.children[0].textContent;
    const icon = btn.querySelector('i');
    const isFavorited = favorites.some(f => f.caseNumber === caseNumber);
    icon.classList.toggle('fa-solid', isFavorited);
    icon.classList.toggle('fa-regular', !isFavorited);
  });
}


// 기일경매목록 불러오기
function fetchAuctionList() {
  fetch('http://127.0.0.1:8000/api/cases/')
    .then(res => res.json())
    .then(data => {
      const tbody = document.querySelector('.auction-list .table tbody');
      tbody.innerHTML = '';

      data.forEach(auction => {
        const details = auction.itemdetails_set?.[0]; // 첫 번째 디테일만 사용

        if (!details) return; // 없으면 건너뜀

        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${auction.case_id}</td>
          <td>${details.min_bid}</td>
          <td>${details.auction_failures}회</td>
          <td>${details.court_date}</td>
          <td><button class="favorite-btn"><i class="fa-regular fa-star"></i></button></td>
          <td><button class="btn-secondary">입찰하기</button></td>
        `;
        tbody.appendChild(tr);
      });

      updateStarIcons();
    })
    .catch(err => {
      console.error('기일경매목록 불러오기 실패:', err);
    });
}


// 별표 버튼 클릭 시 즐겨찾기 토글
document.addEventListener('click', e => {
  if (e.target.closest('.favorite-btn')) {9
    const btn = e.target.closest('.favorite-btn');
    const icon = btn.querySelector('i');
    const row = btn.closest('tr');
    const caseNumber = row.children[0].textContent;
    const minBid = row.children[1].textContent;
    const deadline = row.children[3].textContent;

    const index = favorites.findIndex(f => f.caseNumber === caseNumber);

    if (index === -1) {
      favorites.push({ caseNumber, minBid, deadline });
      icon.classList.remove('fa-regular');
      icon.classList.add('fa-solid');
    } else {
      favorites.splice(index, 1);
      icon.classList.remove('fa-solid');
      icon.classList.add('fa-regular');
    }

    localStorage.setItem('favorites', JSON.stringify(favorites));
    updateFavoritesTable();
  }
});


// 초기 실행
fetchAuctionList();
updateFavoritesTable();

