require("dotenv").config();

const express = require("express");
const cors = require("cors");

const connectDB = require("./config/db");

const vehicleRoutes = require("./routes/VehicleRoutes");
const settingsRoutes = require("./routes/SettingsRoutes");
const authRoutes = require("./routes/authRoutes");

const app = express();

app.use(cors());
app.use(express.json());

// DEBUG (temporary)
console.log("EMAIL_USER:", process.env.EMAIL_USER);
console.log("ADMIN_EMAIL:", process.env.ADMIN_EMAIL);

connectDB();

app.use("/api/vehicles", vehicleRoutes);
app.use("/api/settings", settingsRoutes);
app.use("/api/auth", authRoutes);

app.get("/", (req, res) => {
  res.send("Auto Finance API Running");
});


console.log("EMAIL_USER =", process.env.EMAIL_USER);
console.log("EMAIL_PASS =", process.env.EMAIL_PASS ? "LOADED" : "MISSING");
console.log("ADMIN_EMAIL =", process.env.ADMIN_EMAIL);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log("Server running on port " + PORT));
