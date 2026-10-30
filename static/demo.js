"use strict";
const demoButton = document.getElementById("use-demo");
const demoData = document.getElementById("demo-details");
if (demoButton && demoData) {
  demoButton.hidden = false;
  demoButton.addEventListener("click", () => {
    const details = JSON.parse(demoData.textContent);
    document.getElementById("id_username").value = details.email;
    const field = document.getElementById("id_password");
    field.value = details.password;
    field.type = "password";
    const toggle = document.getElementById("password-toggle");
    toggle.textContent = "Show";
    toggle.setAttribute("aria-label", "Show password");
    document.getElementById("demo-status").textContent = "Demo details filled. Select Sign in to continue.";
    document.querySelector("button[type=submit]").focus();
  });
}
