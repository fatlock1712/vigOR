import { db, auth } from "../Firebase/firebase.js";
import { 
  doc, 
  setDoc, 
  serverTimestamp 
} from "https://www.gstatic.com/firebasejs/12.12.0/firebase-firestore.js";

window.submitForm = async function() {

  const birthYearInput = document.getElementById('birthYear').value.trim();
  const heartRadio = document.querySelector('input[name="heart"]:checked');
  const sev = document.getElementById('severity').value;
  const allergies = [...document.querySelectorAll('input[name="allergy"]:checked')].map(c => c.value);


  if (!birthYearInput || !heartRadio) {
    alert("Please fill your information"); 
    return; 
  }


  if (birthYearInput.length < 4) {
    alert("Please enter a valid birth year (4 digits)");
    return;
  }


  if (!auth.currentUser) {
    alert('You need to login to save information.');
    return;
  }

  const uid = auth.currentUser.uid;
  const currentYear = new Date().getFullYear();
  const birthYear = parseInt(birthYearInput);
  const calculatedAge = currentYear - birthYear;

  const submitBtn = document.querySelector('.btn-submit');
  submitBtn.disabled = true;
  submitBtn.textContent = "Updating...";

  try {
    await setDoc(doc(db, "health_records", uid), {
      userId: uid,
      birthYear: birthYear,
      age: calculatedAge,
      allergies: allergies,
      severity: parseInt(sev),
      heartDisease: heartRadio.value,
      lastUpdate: serverTimestamp()
    });

    alert("Update successful!");
    window.location.assign("../index.html"); 

  } catch (error) {
    console.error("Error:", error);
    alert("Failed to save information.");
    submitBtn.disabled = false;
    submitBtn.textContent = "Xác nhận thông tin";
  }
};