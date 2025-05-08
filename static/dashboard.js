let notifiedBookings = new Set();
let currentSlot = 0;
let isPopupVisible = false;

async function updateSlots() {
  try {
    const res = await fetch("/api/status", { cache: "no-cache" });
    if (!res.ok) {
      console.error("API status response not OK:", res.status);
      return;
    }
    const data = await res.json();
    console.log("API status response:", data);

    const slotMap = {
      "A1": { occupied: data.slot1.occupied, booked: data.slot1.booked },
      "A2": { occupied: data.slot2.occupied, booked: data.slot2.booked },
      "A3": { occupied: data.slot3.occupied, booked: data.slot3.booked },
      "A4": { occupied: data.slot4.occupied, booked: data.slot4.booked }
    };

    const bookings = data.bookings || [];
    const expiredBookings = data.expired_bookings || [];
    const currentUser = data.current_user;
    const sessionRole = data.session_role;
    const sessionUsername = data.session_username;
    const markedSlots = data.marked_slots || []; // Slot yang ditandai oleh user

    console.log("Session Role:", sessionRole, "Session Username:", sessionUsername);

    // Notification for completed bookings
    expiredBookings.forEach(expired => {
      if (expired.user_id === currentUser && !notifiedBookings.has(expired.slot_id)) {
        showToast(`Your booking time has ended. Please head to your parking slot at Slot ${expired.slot_id}!`, true);
        notifiedBookings.add(expired.slot_id);
      }
    });

    let filledCount = 0;
    let bookingCount = 0;
    let userBooking = null;

    document.querySelectorAll('.slot').forEach(slot => {
      const id = slot.dataset.id;
      slot.classList.remove("empty", "filled", "booked", "booked-own", "marked-own");
      slot.title = "";

      const slotData = slotMap[id] || { occupied: false, booked: false };
      const isBooked = bookings.find(b => b.slot_id === id);
      const isOccupied = slotData.occupied === true || slotData.occupied === "true" || slotData.occupied === 1 || slotData.occupied === "1";
      const isBookedThingsBoard = slotData.booked === true || slotData.booked === "true" || slotData.booked === 1 || slotData.booked === "1";
      const isMarked = markedSlots.includes(id); // Cek apakah slot ditandai oleh user

      if (isBooked && isBooked.user_id === currentUser) {
        slot.classList.add("booked-own");
        slot.title = `Your Booking: ${Math.floor(isBooked.duration / 60)}h ${isBooked.duration % 60}m`;
        bookingCount++;
        userBooking = isBooked;
      } else if (isBooked || isBookedThingsBoard) {
        slot.classList.add("booked");
        slot.title = `Booked${isBooked && isBooked.username ? ' by ' + isBooked.username : ''}`;
        bookingCount++;
      } else if (isOccupied) {
        if (isMarked && currentUser) {
          slot.classList.add("marked-own");
          slot.title = "Your Vehicle";
        } else {
          slot.classList.add("filled");
          slot.title = "Occupied";
        }
        filledCount++;
      } else {
        slot.classList.add("empty");
        slot.title = "Empty";
      }

      // Pop-up for booked and occupied
      if (!isPopupVisible && (isBooked || isBookedThingsBoard) && isOccupied && (!isBooked || isBooked.user_id === currentUser)) {
        currentSlot = id === "A1" ? 1 : id === "A2" ? 2 : id === "A3" ? 3 : id === "A4" ? 4 : 0;
        document.getElementById("popup").style.display = "block";
        isPopupVisible = true;
        console.log(`Pop-up shown for Slot ${id}`);
      }

      // Slot click logic
      slot.onclick = () => {
        console.log(`Clicked slot ${id} with classes:`, slot.classList);
        if (!currentUser) {
          if (slot.classList.contains("empty")) {
            showModal(`Slot ${id} is empty. Would you like to login to book it?`, (confirmLogin) => {
              if (confirmLogin) window.location.href = "/login";
            });
          }
        } else if (slot.classList.contains("empty")) {
          showBookingForm(id);
        } else if (slot.classList.contains("booked-own")) {
          showModal(`You are about to release slot ${id}. Proceed?`, (confirmUnbook) => {
            if (confirmUnbook) {
              const form = document.createElement("form");
              form.method = "POST";
              form.action = `/unbook/${id}`;
              document.body.appendChild(form);
              console.log(`Submitting unbook for slot ${id}`);
              form.submit();
            }
          });
        } else if (slot.classList.contains("booked") && sessionRole === 'admin') {
          showModal(`You are about to release slot ${id}. Proceed?`, (confirmUnbook) => {
            if (confirmUnbook) {
              const form = document.createElement("form");
              form.method = "POST";
              form.action = `/unbook/${id}`;
              document.body.appendChild(form);
              console.log(`Admin submitting unbook for slot ${id}`);
              form.submit();
            }
          });
        } else if (slot.classList.contains("filled") || slot.classList.contains("marked-own")) {
          const isCurrentlyMarked = slot.classList.contains("marked-own");
          const message = isCurrentlyMarked
            ? `Slot ${id} is marked as your vehicle. Unmark it?`
            : `Is this your vehicle at slot ${id}?`;
          showModal(message, (confirmMark) => {
            if (confirmMark) {
              const form = document.createElement("form");
              form.method = "POST";
              form.action = `/mark_vehicle/${id}`;
              form.innerHTML = `<input type="hidden" name="action" value="${isCurrentlyMarked ? 'unmark' : 'mark'}">`;
              document.body.appendChild(form);
              form.submit();
            }
          });
        }
      };
    });

    // Update summary
    const totalSlot = document.querySelectorAll('.slot').length;
    const sisaSlot = totalSlot - filledCount - bookingCount;
    document.getElementById("total-slot").textContent = totalSlot;
    document.getElementById("sisa-slot").textContent = sisaSlot;
    document.getElementById("slot-terisi").textContent = filledCount;

    // Update remaining time
    if (userBooking) {
      updateRemainingTime(userBooking);
    } else {
      document.getElementById("remainingTime").style.display = "none";
      notifiedBookings.clear();
    }

    displayActiveNotifications();
  } catch (err) {
    console.error("Failed to fetch status:", err);
  }
}

function updateRemainingTime(booking) {
  const remainingMinutes = booking.remaining_duration;
  const slotId = booking.slot_id;
  if (remainingMinutes <= 0) {
    document.getElementById("remainingTime").style.display = "none";
    if (!notifiedBookings.has(slotId)) {
      showToast(`Your booking time has ended. Please head to your parking slot at Slot ${slotId}!`, true);
      notifiedBookings.add(slotId);
      const form = document.createElement("form");
      form.method = "POST";
      form.action = `/unbook/${slotId}`;
      document.body.appendChild(form);
      form.submit();
    }
    return;
  }
  const hours = Math.floor(remainingMinutes / 60);
  const minutes = remainingMinutes % 60;
  document.getElementById("timeLeft").textContent = `${hours}h ${minutes}m`;
  document.getElementById("remainingTime").style.display = "block";
}

function showModal(message, callback) {
  const modal = document.getElementById("customModal");
  const modalText = document.getElementById("modalText");
  const yesBtn = document.getElementById("modalYes");
  const cancelBtn = document.getElementById("modalCancel");
  const bookingForm = document.getElementById("bookingForm");
  modalText.textContent = message;
  bookingForm.style.display = "none";
  modal.style.display = "flex";
  const cleanup = () => {
    modal.style.display = "none";
    yesBtn.onclick = null;
    cancelBtn.onclick = null;
  };
  yesBtn.onclick = () => { cleanup(); callback(true); };
  cancelBtn.onclick = () => { cleanup(); callback(false); };
}

function showBookingForm(slotId) {
  const modal = document.getElementById("customModal");
  const modalText = document.getElementById("modalText");
  const bookingForm = document.getElementById("bookingForm");
  const yesBtn = document.getElementById("modalYes");
  const cancelBtn = document.getElementById("modalCancel");
  const hoursInput = document.getElementById("hours-input");
  const minutesInput = document.getElementById("minutes-input");
  const totalPriceDisplay = document.getElementById("totalPrice");

  modalText.textContent = `Booking Slot ${slotId}`;
  bookingForm.style.display = "block";
  modal.style.display = "flex";
  hoursInput.value = 0;
  minutesInput.value = 0;

  function updateTotalPrice() {
    const hours = parseInt(hoursInput.value) || 0;
    const minutes = parseInt(minutesInput.value) || 0;
    const totalPrice = (hours * 5000) + (minutes * 830);
    totalPriceDisplay.textContent = `Total: Rp${totalPrice.toLocaleString('id-ID')}`;
  }

  hoursInput.oninput = updateTotalPrice;
  minutesInput.oninput = updateTotalPrice;
  updateTotalPrice();

  const cleanup = () => {
    modal.style.display = "none";
    bookingForm.style.display = "none";
    yesBtn.onclick = null;
    cancelBtn.onclick = null;
    hoursInput.oninput = null;
    minutesInput.oninput = null;
  };

  yesBtn.onclick = () => {
    const hours = parseInt(hoursInput.value) || 0;
    const minutes = parseInt(minutesInput.value) || 0;
    if (hours === 0 && minutes === 0) {
      alert("Minimum duration is 1 minute.");
      return;
    }
    if (hours > 24 || (hours == 24 && minutes > 0)) {
      alert("Maximum duration is 24 hours.");
      return;
    }
    if (minutes >= 60) {
      alert("Minutes must be less than 60.");
      return;
    }
    const form = document.createElement("form");
    form.method = "POST";
    form.action = `/book/${slotId}`;
    form.innerHTML = `
      <input type="hidden" name="hours" value="${hours}">
      <input type="hidden" name="minutes" value="${minutes}">
    `;
    document.body.appendChild(form);
    form.submit();
    cleanup();
  };

  cancelBtn.onclick = () => { cleanup(); };
}

function confirmSlot(slot, confirm) {
  fetch(`/api/confirm_slot/${slot}/${confirm}`, {
    method: 'POST'
  })
  .then(response => response.json())
  .then(data => {
    console.log(data.message);
    document.getElementById("popup").style.display = "none";
    isPopupVisible = false;
    sessionStorage.setItem('notification', `Slot ${slot} confirmation: ${confirm}`);
    showNotification();
  })
  .catch(error => console.error("Error confirming slot:", error));
}

function showToast(message, isImportant = false) {
  const notification = {
    message: message,
    isImportant: isImportant,
    timestamp: Date.now(),
    duration: isImportant ? 10000 : 5000
  };
  const slotIdMatch = message.match(/Slot (\w+)/);
  const slotId = slotIdMatch ? slotIdMatch[1] : 'general';
  sessionStorage.setItem(`notification_${slotId}`, JSON.stringify(notification));
  displayNotification(notification);
}

function displayNotification(notification) {
  const toast = document.createElement("div");
  toast.textContent = notification.message;
  toast.className = `toast-message ${notification.isImportant ? 'important' : ''}`;
  document.body.appendChild(toast);
  setTimeout(() => toast.style.opacity = 1, 100);
  setTimeout(() => {
    toast.style.opacity = 0;
    setTimeout(() => toast.remove(), 500);
  }, notification.duration);
}

function displayActiveNotifications() {
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (key.startsWith('notification_')) {
      const notification = JSON.parse(sessionStorage.getItem(key));
      const elapsed = Date.now() - notification.timestamp;
      if (elapsed >= notification.duration) {
        sessionStorage.removeItem(key);
      } else if (!document.querySelector(`.toast-message[data-message="${notification.message}"]`)) {
        displayNotification(notification);
      }
    }
  }
}

function showNotification() {
  let notification = sessionStorage.getItem('notification');
  if (notification) {
    alert(notification);
    sessionStorage.removeItem('notification');
  }
}

setInterval(updateSlots, 1000);
window.onload = updateSlots;
