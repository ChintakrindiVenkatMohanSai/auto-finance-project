const nodemailer = require("nodemailer");

const transporter = nodemailer.createTransport({
  service: "gmail",
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS
  }
});

async function sendOTPEmail(toEmail, otp) {
  await transporter.sendMail({
    from: process.env.EMAIL_USER,
    to: toEmail,
    subject: "Admin Password Reset OTP",
    html: `
      <h2>Sri Lakshmi Ganesh Auto Finance</h2>
      <p>Your OTP for password reset is:</p>
      <h1 style="letter-spacing:3px;">${otp}</h1>
      <p>This OTP will expire in 5 minutes.</p>
    `
  });
}

module.exports = { sendOTPEmail };
