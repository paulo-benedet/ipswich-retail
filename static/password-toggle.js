"use strict";
const password = document.getElementById("id_password");
const toggle = document.getElementById("password-toggle");
if (password && toggle) {
  toggle.hidden = false;
  const conceal = () => {
    password.type = "password";
    toggle.textContent = "Show";
    toggle.setAttribute("aria-label", "Show password");
  };
  toggle.addEventListener("click", () => {
    if (password.type === "password") {
      password.type = "text";
      toggle.textContent = "Hide";
      toggle.setAttribute("aria-label", "Hide password");
    } else {
      conceal();
    }
  });
  window.addEventListener("pageshow", conceal);
  password.form.addEventListener("submit", conceal);
}
