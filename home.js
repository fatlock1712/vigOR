import { auth } from "../Firebase/firebase.js"; 
import { onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/12.12.0/firebase-auth.js";

// Đặt thời gian hết hạn là 20 phút
const SESSION_TIMEOUT_MS = 20 * 60 * 1000; 
let logoutTimer; 

onAuthStateChanged(auth, (user) => {
    // Đổi JS để tìm nút Sign In mới
    const signInBtn = document.getElementById('sign-in-btn');
    const emailDisplay = document.getElementById('user-email-display');
    const userProfile = document.getElementById('user-profile');
    
    if (user) {
        // --- 1. TRẠNG THÁI ĐÃ ĐĂNG NHẬP ---
        if (signInBtn) signInBtn.style.setProperty('display', 'none', 'important');
        if (emailDisplay) emailDisplay.style.setProperty('display', 'inline-block', 'important');
        if (userProfile) userProfile.style.setProperty('display', 'block', 'important');

        const userEmail = user.email;
        if (emailDisplay) {
            emailDisplay.textContent = userEmail;
        }
        console.log("Đã đăng nhập:", userEmail);

        // --- 2. LOGIC KIỂM TRA THỜI GIAN ---
        let sessionStartTime = localStorage.getItem('sessionStartTime');
        if (!sessionStartTime) {
            sessionStartTime = Date.now();
            localStorage.setItem('sessionStartTime', sessionStartTime);
        }

        const elapsedTime = Date.now() - parseInt(sessionStartTime);
        const remainingTime = SESSION_TIMEOUT_MS - elapsedTime;

        if (remainingTime <= 0) {
            forceLogout();
        } else {
            if (logoutTimer) clearTimeout(logoutTimer);
            logoutTimer = setTimeout(() => {
                forceLogout();
            }, remainingTime);
            
            console.log(`Phiên đăng nhập còn lại: ${Math.floor(remainingTime / 60000)} phút.`);
        }

    } else {
        // --- 3. TRẠNG THÁI CHƯA ĐĂNG NHẬP (HOẶC ĐÃ ĐĂNG XUẤT) ---
        // Hiện lại nút Sign In
        if (signInBtn) signInBtn.style.setProperty('display', 'inline-block', 'important');
        if (emailDisplay) emailDisplay.style.setProperty('display', 'none', 'important');
        if (userProfile) userProfile.style.setProperty('display', 'none', 'important');

        localStorage.removeItem('sessionStartTime');
        if (logoutTimer) clearTimeout(logoutTimer);
    }
});

function forceLogout() {
    signOut(auth).then(() => {
        alert("Phiên đăng nhập đã hết hạn sau 20 phút. Vui lòng đăng nhập lại!");
        window.location.assign("../Login and SignUp/login.html");
    }).catch((error) => {
        console.error("Lỗi tự động đăng xuất:", error);
    });
}

// Xử lý nút Logout thủ công khi click vào Menu Dropdown
const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        signOut(auth).then(() => {
            console.log("Đã đăng xuất thành công");
            alert("Bạn đã đăng xuất!");
            // Nếu muốn chuyển hướng sau khi đăng xuất thì bật dòng dưới lên:
            // window.location.assign("../Login and SignUp/login.html");
        }).catch((error) => {
            console.error("Lỗi khi đăng xuất:", error);
        });
    });
}