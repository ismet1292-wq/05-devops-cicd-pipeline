const express = require("express");

const app = express();
const port = process.env.PORT || 3000;

app.get("/", (req, res) => {
  res.status(200).json({
    message: "DevOps CI/CD pipeline is working",
    environment: process.env.NODE_ENV || "development"
  });
});

app.get("/health", (req, res) => {
  res.status(200).json({
    status: "healthy"
  });
});

app.listen(port, "0.0.0.0", () => {
  console.log(`Application is running on port ${port}`);
});
