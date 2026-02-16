const mongoose = require("mongoose");

const VehicleSchema = new mongoose.Schema(
  {
    surname: String,
    firstName: String,
    phone: String,
    address: String,
    vehicleNumber: { type: String, unique: true },
    loanAg: String,
    loanDate: String,
    guarantor: String,
    maker: String,
    classification: String,
    model: String,
    chassis: String,
    engine: String,
    rto: String,
    noc: { type: String, default: null }
  },
  { timestamps: true }
);

module.exports = mongoose.model("Vehicle", VehicleSchema);
