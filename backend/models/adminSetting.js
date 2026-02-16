const mongoose = require("mongoose");

const AdminSettingSchema = new mongoose.Schema(
  {
    password: { type: String, default: "Vehicle@2005" }
  },
  { timestamps: true }
);

module.exports = mongoose.model("AdminSetting", AdminSettingSchema);
