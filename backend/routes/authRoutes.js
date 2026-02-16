const express = require("express");
const router = express.Router();
const OTP = require("../models/OTP");
const { sendOTPEmail } = require("../utils/mailer");

function generateOTP() {
  return Math.floor(100000 + Math.random() * 900000).toString(); // 6 digit
}

// SEND OTP
router.post("/send-otp", async (req, res) => {
  try {
    const { email } = req.body;

    if (!email) return res.status(400).json({ message: "Email required" });

    // Only allow admin email
    if (email.toLowerCase() !== process.env.ADMIN_EMAIL.toLowerCase()) {
      return res.status(403).json({ message: "This email is not authorized." });
    }

    const otp = generateOTP();
    const expiresAt = new Date(Date.now() + 5 * 60 * 1000); // 5 minutes

    // Delete old OTP
    await OTP.deleteMany({ email });

    await OTP.create({ email, otp, expiresAt });

    await sendOTPEmail(email, otp);

    res.json({ message: "OTP sent successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Server error sending OTP" });
  }
});

// VERIFY OTP
router.post("/verify-otp", async (req, res) => {
  try {
    const { email, otp } = req.body;

    if (!email || !otp)
      return res.status(400).json({ message: "Email and OTP required" });

    const record = await OTP.findOne({ email, otp });

    if (!record) return res.status(400).json({ message: "Invalid OTP" });

    if (new Date() > record.expiresAt) {
      await OTP.deleteMany({ email });
      return res.status(400).json({ message: "OTP expired" });
    }

    res.json({ message: "OTP verified successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Server error verifying OTP" });
  }
});

module.exports = router;
