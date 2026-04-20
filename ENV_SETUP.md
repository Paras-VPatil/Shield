# Shield Environment Configuration Guide

This guide provides the exact values required to configure the **Shield (RequiMind AI)** project on Vercel.

## Dashboard Setup (Manual)

To set these up in the Vercel Dashboard:
1. Go to your **Project Settings** on Vercel.
2. Select **Environment Variables**.
3. Add the following keys and values:

| Key | Value (Copy-Paste) | Type | Note |
| :--- | :--- | :--- | :--- |
| `LLM_MODE` | `gemini` | Plaintext | Switches to cloud analysis. |
| `SHIELD_DB_MODE` | `mongodb` | Plaintext | Switches to MongoDB storage. |
| `MONGODB_DB_NAME` | `the_shield` | Plaintext | Default database name. |
| `MONGODB_URI` | *[Your Atlas String]* | Secret | e.g. `mongodb+srv://...` |
| `GEMINI_API_KEY` | *[Your API Key]* | Secret | From Google AI Studio. |

---

## CLI Setup (Fastest)

If you have the [Vercel CLI](https://vercel.com/download) installed, follow these steps:

1. **Login**:
   ```bash
   vercel login
   ```

2. **Link Project**:
   ```bash
   vercel link
   ```

3. **Run Setup Script**:
   We've provided a script to automate this for you. Run it in your terminal:
   ```powershell
   .\setup_vercel_env.ps1
   ```

## Next Steps

Once the variables are set, you can deploy by simply running:
```bash
vercel --prod
```
