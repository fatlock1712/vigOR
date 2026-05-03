import { auth } from "../Firebase/firebase.js"; 
import { onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/11.0.0/firebase-auth.js";

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
        alert("Your login session has expired");
        window.location.assign("../Login and SignUp/login.html");
    }).catch((error) => {
        console.error("Lỗi tự động đăng xuất:", error);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            signOut(auth).then(() => {
                alert("You're sign out");
            }).catch(console.error);
        });
    }

    init(); // gọi init ở đây luôn
});


async function init() {
  await customElements.whenDefined('gmp-map');

  const map = document.querySelector('gmp-map');
  const marker = document.querySelector('gmp-advanced-marker');
  const placePicker = document.querySelector('gmpx-place-picker');
  const infowindow = new google.maps.InfoWindow();

  map.innerMap.setOptions({
    mapTypeControl: false
  });

  placePicker.addEventListener('gmpx-placechange', () => {
    const place = placePicker.value;

    if (!place.location) {
      window.alert(
        "No details available for input: '" + place.name + "'"
      );
      infowindow.close();
      marker.position = null;
      return;
    }

    if (place.viewport) {
      map.innerMap.fitBounds(place.viewport);
    } else {
      map.center = place.location;
      map.zoom = 17;
    }

    marker.position = place.location;
    infowindow.setContent(
  `<strong>${place.displayName}</strong><br>
   <span>${place.formattedAddress}</span>`
);
    infowindow.open(map.innerMap, marker);
  });
}

document.addEventListener('DOMContentLoaded', init);

