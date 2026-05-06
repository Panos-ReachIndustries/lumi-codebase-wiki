// Copy this file to app/config.js and paste your Gemini API key.
// app/config.js is gitignored so the real key doesn't get committed.
//
// Get a key: https://aistudio.google.com/apikey
// Models:    https://ai.google.dev/gemini-api/docs/models
window.LUMI_GEMINI = {
  apiKey: "PASTE_YOUR_GEMINI_API_KEY_HERE",
  model:  "gemini-2.5-flash",          // "gemini-2.5-pro" for heavier reasoning
  temperature: 0.4,                    // lower = more grounded; raise for creativity
  maxOutputTokens: 4096,
};
