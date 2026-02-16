const nodemailer = require("nodemailer");

async function sendOTPEmail(toEmail, otp) {
  if (!process.env.EMAIL_USER || !process.env.EMAIL_PASS) {
    throw new Error("EMAIL_USER or EMAIL_PASS missing in env");
  }

  const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS,
    },
  });

  // 🔥 This line will show the real problem in Render logs
  await transporter.verify();

  await transporter.sendMail({
    from: process.env.EMAIL_USER,
    to: toEmail,
    subject: "Admin Password Reset OTP",
    html: `
      <h2>Sri Lakshmi Ganesh Auto Finance</h2>
      <p>Your OTP for password reset is:</p>
      <h1 style="letter-spacing:3px;">${otp}</h1>
      <p>This OTP will expire in 5 minutes.</p>
    `,
  });
}

module.exports = { sendOTPEmail };
