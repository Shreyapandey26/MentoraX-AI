/*
 * biometric.js — Fingerprint Scanner Animation
 * MODULE 1: Biometric Authorization Module
 *
 * startScan() is called when the user clicks "Start Scan".
 * It:
 *   1. Validates the name field is not empty
 *   2. Plays a 3-second scanning animation
 *   3. Shows "AUTHORIZED" status
 *   4. Submits the form to /authorize/
 */

function startScan() {
    const nameInput = document.querySelector(".bio-input");
    const scanner   = document.getElementById("fpScanner");
    const status    = document.getElementById("fpStatus");
    const btn       = document.getElementById("startScanBtn");
    const form      = document.getElementById("bioForm");

    // Step 1: Make sure the name field is filled
    if (!nameInput.value.trim()) {
        // Shake the input to hint at the error
        nameInput.style.borderColor = "#ff4444";
        nameInput.style.animation   = "none";
        status.textContent = "⚠ Please enter your name first.";
        status.style.color = "#ff4444";
        nameInput.focus();
        return;
    }

    // Step 2: Disable button so user can't spam click
    btn.disabled = true;
    btn.textContent = "Scanning...";

    // Step 3: Start the scan animation (CSS class adds the moving scan line)
    scanner.classList.add("scanning");
    status.textContent = "Scanning...";
    status.style.color = "#00d4ff";

    // Step 4: After 1.5 seconds, show "Processing"
    setTimeout(function () {
        status.textContent = "Processing biometric data...";
    }, 1500);

    // Step 5: After 3 seconds, show "Authorized" then submit the form
    setTimeout(function () {
        // Remove scanning animation, add authorized glow
        scanner.classList.remove("scanning");
        scanner.classList.add("authorized");

        status.textContent = "✓ AUTHORIZED";
        status.style.color = "#00ff88";

        btn.textContent = "Access Granted — Loading...";
        btn.style.background = "linear-gradient(135deg, #00ff88, #00cc66)";

        // Submit the form after a short pause so user can see the authorized state
        setTimeout(function () {
            form.submit();
        }, 600);

    }, 3000);
}

// Also allow pressing Enter in the input to trigger the scan
document.addEventListener("DOMContentLoaded", function () {
    const nameInput = document.querySelector(".bio-input");
    if (nameInput) {
        nameInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                startScan();
            }
        });

        // Remove red border on typing after error
        nameInput.addEventListener("input", function () {
            nameInput.style.borderColor = "";
        });
    }
});
