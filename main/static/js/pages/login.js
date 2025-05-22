// login.js

document.querySelector(".login-form").addEventListener("submit", function(e) {
    e.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
  
    if (!username || !password) {
      alert("아이디와 비밀번호를 모두 입력해주세요.");
      return;
    }
  
    // 여기에 실제 로그인 코드 추가해주면 될듯!
    alert(`로그인 시도: ${username}`);
  });
  