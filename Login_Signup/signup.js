import { auth, db, googleProvider } from "../Firebase/firebase.js";
import {
  createUserWithEmailAndPassword,
  updateProfile,
  signInWithPopup
} from "https://www.gstatic.com/firebasejs/12.12.0/firebase-auth.js";

import {
  doc,
  setDoc,
  serverTimestamp
} from "https://www.gstatic.com/firebasejs/12.12.0/firebase-firestore.js";

// Hàm băm mật khẩu
async function hashPassword(password) {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

const signupForm = document.getElementById("signupForm");
const googleSignUpBtn = document.getElementById("googleSignUpBtn");

// Xử lý đăng ký bằng Email/Password
signupForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const submitBtn = signupForm.querySelector('input[type="submit"]');
  const originalBtnText = submitBtn.value;
  
  // Disable nút để tránh submit nhiều lần
  submitBtn.disabled = true;
  submitBtn.value = "PROVISIONING...";

  const lastname = document.getElementById("lastname").value.trim();
  const firstname = document.getElementById("firstname").value.trim();
  const phonenumber = document.getElementById("phonenumber").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  try {
    // 1. Tạo user trên Firebase Auth
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;

    // 2. Cập nhật Display Name
    await updateProfile(user, {
      displayName: `${firstname} ${lastname}`
    });

    // 3. Băm mật khẩu để bảo mật trước khi lưu Firestore
    const passwordHash = await hashPassword(password);

    // 4. Lưu thông tin vào Firestore
    await setDoc(doc(db, "users", user.uid), {
      uid: user.uid,
      firstname,
      lastname,
      fullName: `${firstname} ${lastname}`,
      phonenumber,
      email,
      photoURL: user.photoURL || "",
      provider: "email",
      passwordHash, // CHỈ lưu hash, không lưu pass thô
      createdAt: serverTimestamp()
    });

    alert("Account Initialized Successfully!");
    // Chuyển hướng về trang login (đảm bảo đường dẫn đúng với Live Server của bạn)
    window.location.href = "./login.html";

  } catch (error) {
    console.error("Signup error:", error);
    if (error.code === "auth/email-already-in-use") {
      alert("Email này đã được đăng ký hệ thống.");
    } else if (error.code === "auth/weak-password") {
      alert("Mật khẩu quá yếu (yêu cầu ít nhất 6 ký tự).");
    } else {
      alert(`Lỗi hệ thống: ${error.message}`);
    }
  } finally {
    submitBtn.disabled = false;
    submitBtn.value = originalBtnText;
  }
});

// Xử lý đăng ký bằng Google
googleSignUpBtn.addEventListener("click", async () => {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;

    // Tách tên từ displayName nếu có thể
    const nameParts = user.displayName ? user.displayName.split(" ") : ["", ""];
    const fName = nameParts[0];
    const lName = nameParts.slice(1).join(" ");

    await setDoc(
      doc(db, "users", user.uid),
      {
        uid: user.uid,
        firstname: fName || "User",
        lastname: lName || "",
        fullName: user.displayName || "New Subject",
        email: user.email || "",
        photoURL: user.photoURL || "",
        provider: "google",
        updatedAt: serverTimestamp()
      },
      { merge: true }
    );

    window.location.href = "./login.html";
  } catch (error) {
    console.error(error);
    alert("Google Initialization failed: " + error.message);
  }
});