# WhatsApp Observability Chatbot Setup & Usage Guide

This guide details the step-by-step process of setting up a Meta developer account, configuring a local webhook tunnel, and interacting with the dashboard chatbot on WhatsApp.

---

## 1. Create a Meta Developer App
1. Go to the **[Meta for Developers portal](https://developers.facebook.com/)** and log in with your Facebook account.
2. Complete the initial developer registration if you haven't already.
3. Go to **[My Apps](https://developers.facebook.com/apps/)** and click **Create App**.
4. Choose **Other** ➡️ **Business** as the app type.
5. Provide an app name (e.g., `Dashboard Observability Bot`) and click **Create app**.
6. On the App Dashboard, scroll down to **WhatsApp** and click **Set up**.

---

## 2. Obtain Sandbox Credentials
Under the **WhatsApp** ➡️ **API Setup** section of your Meta App Dashboard, copy the following values:
* **Temporary Access Token** (Valid for 24 hours in sandbox)
* **Phone Number ID** (e.g., `1161848187017272`)
* **Sandbox Test Phone Number** (Save this number to your contacts to chat with the bot)

---

## 3. Configure the Local Environment
Save your credentials in the backend environment file [backend/.env](file:///Users/adeelarshad/AgenticAIOPs/backend/.env):
```ini
WHATSAPP_TOKEN=EAAb09k4CAGEBRq7aa...
WHATSAPP_PHONE_NUMBER_ID=1161848187017272
WHATSAPP_VERIFY_TOKEN=sa4dst_verify_token
```
*Note: Make sure to restart the FastAPI backend server after updating `.env` to load the new values.*

---

## 4. Run a Webhook Tunnel
Since your backend runs locally on port `8000` and Meta requires a public HTTPS endpoint, expose your port using **localtunnel**:
```bash
npx localtunnel --port 8000
```
This will print a public URL, for example:
```
https://calm-cougars-find.loca.l
```

> [!NOTE]
> **Localtunnel Password Bypass:**
> When opening a `localtunnel` link for the first time, you may be greeted by a security landing page asking for a password. The password is your machine's **public IP address**. You can obtain your public IP by opening another terminal window and running:
> ```bash
> curl ipinfo.io/ip
> ```


---

## 5. Register the Webhook in Meta Dashboard
1. In the Meta App Dashboard, navigate to **WhatsApp** ➡️ **Configuration** (left menu).
2. Under **Webhook**, click **Edit** and set:
   * **Callback URL**: `https://<your-tunnel-domain>/api/whatsapp/webhook`
     *(Example: `https://calm-cougars-find.loca.l/api/whatsapp/webhook`)*
   * **Verify Token**: `sa4dst_verify_token` (matches the `WHATSAPP_VERIFY_TOKEN` in your `.env` file)
3. Click **Verify and save**.
4. Under **Webhook fields**, click **Manage** / **Subscribe** and verify you are subscribed to **`messages`**.

---

## 6. Authorize Your Recipient Phone Number
To receive responses from the sandbox:
1. In the Meta App Dashboard under **WhatsApp** ➡️ **API Setup**, find the **To** dropdown on the right side.
2. Click **Manage phone number list** and add your personal phone number.
3. Verify it by entering the OTP sent to your WhatsApp.

---

## 7. Start Chatting with the Bot
1. Send **`hi`** or **`help`** to the sandbox test number.
2. The bot will respond with an **Interactive List Menu**.
3. Open the menu list on your phone, choose any dashboard chart (e.g. *Weekly Volume*), or reply with a number (e.g. `1`).
4. The bot will launch Puppeteer, snapshot the card from `/complaint-dashboard/print` locally, and deliver the live PNG image back to you in the WhatsApp chat.
