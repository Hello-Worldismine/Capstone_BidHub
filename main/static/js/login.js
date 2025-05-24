// login.js

document.addEventListener('DOMContentLoaded', function() {
  const loginForm = document.querySelector(".login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", function(e) {
      e.preventDefault(); // Prevent default form submission
      const usernameInput = document.getElementById("username");
      const passwordInput = document.getElementById("password");
      const username = usernameInput.value;
      const password = passwordInput.value;
    
      if (!username || !password) {
        alert("아이디와 비밀번호를 모두 입력해주세요.");
        return;
      }
    
      // Send credentials to the backend API
      fetch('/api/token/', { // Correct JWT token endpoint
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Note: CSRF token is typically not needed for stateless JWT endpoints
        },
        body: JSON.stringify({ username: username, password: password })
      })
      .then(response => {
        if (response.ok) {
          return response.json(); // Parse JSON body on success
        } else {
          // Handle login errors (e.g., 401 Unauthorized)
          return response.json().then(data => {
            // Try to get a specific error message, otherwise use a generic one
            let errorMessage = "로그인 실패. 아이디 또는 비밀번호를 확인하세요.";
            if (data && data.detail) {
                errorMessage = data.detail;
            }
            throw new Error(errorMessage);
          });
        }
      })
      .then(data => {
        // Login successful, store tokens
        localStorage.setItem('accessToken', data.access);
        localStorage.setItem('refreshToken', data.refresh);
        
        // Redirect to the homepage or dashboard
        window.location.href = '/'; 
      })
      .catch(error => {
        console.error('Login error:', error);
        alert(error.message); // Show error message to the user
        passwordInput.value = ""; // Clear password field on error
      });
    });
  }
});
  