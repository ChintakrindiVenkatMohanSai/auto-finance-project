const express = require("express");
const router = express.Router();
const Vehicle = require("../models/vehicle");

// GET ALL
router.get("/", async (req, res) => {
  const vehicles = await Vehicle.find().sort({ createdAt: -1 });
  res.json(vehicles);
});

// ADD
router.post("/", async (req, res) => {
  try {
    const vehicle = await Vehicle.create(req.body);
    res.json(vehicle);
  } catch (err) {
    if (err.code === 11000) {
      return res.status(400).json({ message: "Vehicle number already exists" });
    }
    res.status(500).json({ message: "Server error" });
  }
});

// DELETE
router.delete("/:vehicleNumber", async (req, res) => {
  await Vehicle.deleteOne({ vehicleNumber: req.params.vehicleNumber });
  res.json({ message: "Deleted successfully" });
});

// UPDATE NOC
router.patch("/:vehicleNumber/noc", async (req, res) => {
  const { noc } = req.body;
  const updated = await Vehicle.findOneAndUpdate(
    { vehicleNumber: req.params.vehicleNumber },
    { noc },
    { new: true }
  );
  res.json(updated);
});

module.exports = router;
