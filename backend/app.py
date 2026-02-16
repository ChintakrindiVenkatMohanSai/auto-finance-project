import os
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


# =========================
# Load ENV
# =========================
load_dotenv()

PORT = int(os.getenv("PORT", 5000))
MONGO_URI = os.getenv("MONGO_URI")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")


# =========================
# Flask Setup
# =========================
app = Flask(__name__)
CORS(app)


# =========================
# MongoDB Setup
# =========================
if not MONGO_URI:
    raise Exception("MONGO_URI missing in .env")

client = MongoClient(MONGO_URI)
db = client["auto_finance"]

vehicles_col = db["vehicles"]
otp_col = db["otp_requests"]
settings_col = db["settings"]

# Create unique index for vehicleNumber
try:
    vehicles_col.create_index("vehicleNumber", unique=True)
except Exception:
    pass


# =========================
# Helpers
# =========================
def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(to_email, otp):
    if not EMAIL_USER or not EMAIL_PASS:
        raise Exception("EMAIL_USER or EMAIL_PASS missing in .env")

    subject = "Admin Password Reset OTP"
    html_body = f"""
    <h2>Sri Lakshmi Ganesh Auto Finance</h2>
    <p>Your OTP for password reset is:</p>
    <h1 style="letter-spacing:3px;">{otp}</h1>
    <p>This OTP will expire in 5 minutes.</p>
    """

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)


def clean_vehicle_doc(doc):
    """Convert MongoDB doc to JSON safe dict"""
    doc["_id"] = str(doc["_id"])
    return doc


def get_admin_password_plain():
    """
    Your frontend expects password in plain text (because you compare it directly).
    So we store it plain in DB.
    """
    doc = settings_col.find_one({"key": "admin_password"})
    if not doc:
        default_pass = "Vehicle@2005"
        settings_col.insert_one({"key": "admin_password", "password": default_pass})
        return default_pass
    return doc.get("password", "Vehicle@2005")


def set_admin_password_plain(new_password):
    settings_col.update_one(
        {"key": "admin_password"},
        {"$set": {"password": new_password}},
        upsert=True
    )


def otp_is_valid(email, otp):
    record = otp_col.find_one({"email": email, "otp": otp})
    if not record:
        return False, "Invalid OTP"

    if datetime.utcnow() > record["expiresAt"]:
        otp_col.delete_many({"email": email})
        return False, "OTP expired"

    return True, "OTP valid"


# =========================
# Routes
# =========================

@app.get("/")
def home():
    return "Auto Finance Flask API Running"


# -------------------------
# SETTINGS: GET PASSWORD
# -------------------------
@app.get("/api/settings/admin-password")
def get_admin_password():
    password = get_admin_password_plain()
    return jsonify({"password": password})


# -------------------------
# SETTINGS: RESET PASSWORD (OTP REQUIRED)
# -------------------------
@app.patch("/api/settings/admin-password")
def reset_admin_password():
    data = request.get_json(force=True)

    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()
    new_password = (data.get("newPassword") or "").strip()

    if not email or not otp or not new_password:
        return jsonify({"message": "Email, OTP and newPassword required"}), 400

    if not ADMIN_EMAIL:
        return jsonify({"message": "ADMIN_EMAIL missing in server env"}), 500

    if email != ADMIN_EMAIL.lower():
        return jsonify({"message": "This email is not authorized."}), 403

    if len(new_password) < 4:
        return jsonify({"message": "Password too short"}), 400

    ok, msg = otp_is_valid(email, otp)
    if not ok:
        return jsonify({"message": msg}), 400

    set_admin_password_plain(new_password)

    # delete OTP after successful reset
    otp_col.delete_many({"email": email})

    return jsonify({"message": "Admin password updated successfully"})


# -------------------------
# AUTH: SEND OTP
# -------------------------
@app.post("/api/auth/send-otp")
def send_otp():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"message": "Email required"}), 400

    if not ADMIN_EMAIL:
        return jsonify({"message": "ADMIN_EMAIL missing in server env"}), 500

    # Only allow admin email
    if email != ADMIN_EMAIL.lower():
        return jsonify({"message": "This email is not authorized."}), 403

    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    # delete old OTPs
    otp_col.delete_many({"email": email})

    otp_col.insert_one({
        "email": email,
        "otp": otp,
        "expiresAt": expires_at
    })

    try:
        send_otp_email(email, otp)
        return jsonify({"message": "OTP sent successfully"})
    except Exception as e:
        print("MAIL ERROR:", str(e))
        return jsonify({"message": "OTP sending failed", "error": str(e)}), 500


# -------------------------
# AUTH: VERIFY OTP
# -------------------------
@app.post("/api/auth/verify-otp")
def verify_otp():
    data = request.get_json(force=True)

    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()

    if not email or not otp:
        return jsonify({"message": "Email and OTP required"}), 400

    ok, msg = otp_is_valid(email, otp)
    if not ok:
        return jsonify({"message": msg}), 400

    return jsonify({"message": "OTP verified successfully"})


# -------------------------
# VEHICLES: GET ALL
# -------------------------
@app.get("/api/vehicles")
def get_all_vehicles():
    all_docs = list(vehicles_col.find({}).sort("vehicleNumber", 1))
    all_docs = [clean_vehicle_doc(d) for d in all_docs]
    return jsonify(all_docs)


# -------------------------
# VEHICLES: ADD NEW
# -------------------------
@app.post("/api/vehicles")
def add_vehicle():
    data = request.get_json(force=True)

    required_fields = [
        "surname", "firstName", "phone", "address",
        "vehicleNumber", "loanAg", "loanDate",
        "guarantor", "maker", "classification",
        "model", "chassis", "engine", "rto"
    ]

    for f in required_fields:
        if f not in data:
            return jsonify({"message": f"Missing field: {f}"}), 400

    vehicle_number = data["vehicleNumber"].strip().upper()

    new_vehicle = {
        "surname": data["surname"].strip().upper(),
        "firstName": data["firstName"].strip().upper(),
        "phone": data["phone"].strip(),
        "address": data["address"].strip().upper(),
        "vehicleNumber": vehicle_number,
        "loanAg": data["loanAg"].strip().upper(),
        "loanDate": data["loanDate"].strip(),
        "guarantor": (data.get("guarantor") or "N/A").strip().upper(),
        "maker": data["maker"].strip().upper(),
        "classification": data["classification"].strip().upper(),
        "model": data["model"].strip().upper(),
        "chassis": data["chassis"].strip().upper(),
        "engine": data["engine"].strip().upper(),
        "rto": data["rto"].strip().upper(),
        "noc": data.get("noc") or None
    }

    try:
        vehicles_col.insert_one(new_vehicle)
        return jsonify({"message": "Vehicle added successfully"}), 201
    except DuplicateKeyError:
        return jsonify({"message": "Vehicle number already exists"}), 400
    except Exception as e:
        print("ADD VEHICLE ERROR:", str(e))
        return jsonify({"message": "Server error adding vehicle"}), 500


# -------------------------
# VEHICLES: DELETE
# -------------------------
@app.delete("/api/vehicles/<vehicleNumber>")
def delete_vehicle(vehicleNumber):
    vehicleNumber = vehicleNumber.strip().upper()

    result = vehicles_col.delete_one({"vehicleNumber": vehicleNumber})
    if result.deleted_count == 0:
        return jsonify({"message": "Vehicle not found"}), 404

    return jsonify({"message": "Vehicle deleted successfully"})


# -------------------------
# VEHICLES: UPDATE NOC
# -------------------------
@app.patch("/api/vehicles/<vehicleNumber>/noc")
def update_vehicle_noc(vehicleNumber):
    vehicleNumber = vehicleNumber.strip().upper()
    data = request.get_json(force=True)

    noc = (data.get("noc") or "").strip()
    if not noc:
        return jsonify({"message": "noc is required"}), 400

    result = vehicles_col.update_one(
        {"vehicleNumber": vehicleNumber},
        {"$set": {"noc": noc}}
    )

    if result.matched_count == 0:
        return jsonify({"message": "Vehicle not found"}), 404

    return jsonify({"message": "NOC updated successfully", "noc": noc})


# =========================
# Run
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
