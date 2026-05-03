// /firebase/firebase.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.12.0/firebase-app.js";
import { getAuth, GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/12.12.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/12.12.0/firebase-firestore.js";
import { getStorage } from "https://www.gstatic.com/firebasejs/12.12.0/firebase-storage.js";

const firebaseConfig = {
  apiKey: "AIzaSyDoQolmXT7Ds56NVQCp7ZQI7iLxtosHOVw",
  authDomain: "vigor-f58b1.firebaseapp.com",
  projectId: "vigor-f58b1",
  storageBucket: "vigor-f58b1.firebasestorage.app",
  messagingSenderId: "626875686827",
  appId: "1:626875686827:web:8545c8de43f1c074787cee",
  measurementId: "G-0Z8QLCVRSX"
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const db = getFirestore(app);
export const storage = getStorage(app);
export const googleProvider = new GoogleAuthProvider();