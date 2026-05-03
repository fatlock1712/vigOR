
import { auth, db, googleProvider } from "../Firebase/firebase.js";

import {
  signInWithEmailAndPassword,
  signInWithPopup,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/12.12.0/firebase-auth.js";

import {
  collection,
  query,
  where,
  getDocs,
  doc,
  setDoc,
  serverTimestamp
} from "https://www.gstatic.com/firebasejs/12.12.0/firebase-firestore.js";

const loginForm = document.getElementById("loginForm");
const googleLoginBtn = document.getElementById("googleLoginBtn");

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const submitBtn = loginForm.querySelector('input[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.value = "Logging in...";

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  try {

    const q = query(collection(db, "users"), where("email", "==", email));
    const snapshot = await getDocs(q);

    if (snapshot.empty) {
      alert("Account not found. Please sign up to proceed!");
      return;
    }
    
    await signInWithEmailAndPassword(auth, email, password);
    
    alert("Login successfully!");
    window.location.assign("./asthma-form.html");
  } catch (error) {
    console.error("Login error:", error);

    if (error.code === "auth/invalid-credential") {
      alert("Email or password not match. Try again");
    } else {
      alert(`Code: ${error.code}\nMessage: ${error.message}`);
    }
  } finally {
    submitBtn.disabled = false;
    submitBtn.value = "Submit";
  }
});



googleLoginBtn.addEventListener("click", async () => {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;

    await setDoc(
      doc(db, "users", user.uid),
      {
        uid: user.uid,
        firstname: user.displayName || "",
        lastname: "",
        fullName: user.displayName || "",
        phonenumber: "",
        email: user.email || "",
        photoURL: user.photoURL || "",
        provider: "google",
        createdAt: serverTimestamp()
      },
      { merge: true }
    );

    window.location.assign("./asthma-form.html");
  } catch (error) {
    console.error("Google login error:", error);
    alert("Google login failed: " + error.message);
  }
});