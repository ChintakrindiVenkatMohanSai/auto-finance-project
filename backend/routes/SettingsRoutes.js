const express = require("express");
const router = express.Router();
const AdminSetting = require("../models/adminSetting");
const OTP = require("../models/OTP");

// GET ADMIN PASSWORD
router.get("/admin-password", async (req, res) => {
  try {
    let setting = await AdminSetting.findOne();
    if (!setting) setting = await AdminSetting.create({ password: "Vehicle@2005" });

    res.json({ password: setting.password });
  } catch (err) {
    res.status(500).json({ message: "Server error" });
  }
});

// UPDATE ADMIN PASSWORD (Only after OTP Verified)
router.patch("/admin-password", async (req, res) => {
  try {
    const { email, otp, newPassword } = req.body;

    if (!email || !otp || !newPassword) {
      return res.status(400).json({ message: "Email, OTP, newPassword required" });
    }

    // Check OTP exists and valid
    const record = await OTP.findOne({ email, otp });
    if (!record) return res.status(400).json({ message: "OTP not verified" });

    if (new Date() > record.expiresAt) {
      await OTP.deleteMany({ email });
      return res.status(400).json({ message: "OTP expired" });
    }

    let setting = await AdminSetting.findOne();
    if (!setting) setting = await AdminSetting.create({ password: newPassword });
    else setting.password = newPassword;

    await setting.save();

    // Remove OTP after password reset
    await OTP.deleteMany({ email });

    res.json({ message: "Password updated successfully", password: newPassword });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Server error" });
  }
});

module.exports = router;
