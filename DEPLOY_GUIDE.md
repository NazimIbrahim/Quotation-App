# 🚀 Real-Time Cloud & Android Synchronization Guide
## AMA Ceramics Quotation Management System (v2.0)

This system allows seamless real-time synchronization between your **Windows Desktop App** and **Android Mobile Phones**. Any quotation created, edited, or marked won on either device is immediately synchronized to the other.

---

## 🌟 Choose Your Sync Setup

| Method | Where it works | Setup Time | Cost |
| :--- | :--- | :--- | :--- |
| **Option 1: Showroom Local Wi-Fi** | Anywhere in showroom on Wi-Fi | 30 Seconds | **100% Free, No Signup** |
| **Option 2: Cloud 24/7 Sync** | Anywhere in the world (4G/5G/Home) | 5 Minutes | **100% Free Tier (Supabase + Render)** |

---

## 📶 Option 1: Showroom Local Wi-Fi (Instant 30-Second Setup)

If your desktop PC and Android phone are connected to the same showroom Wi-Fi network:

1. **Start the API Server on your PC**:
   Double click `start_server.bat` or run in terminal:
   ```bash
   python server/main.py
   ```
2. **Find Your Showroom Wi-Fi Link**:
   - Open your desktop Quotation App.
   - Go to **⚙️ Company Settings** -> **☁️ Cloud & Mobile Sync** tab.
   - You will see your local showroom address, for example:
     `http://192.168.1.15:8000/mobile/`
3. **Open on Android Phone**:
   - Open Chrome or any browser on your Android phone and navigate to that address.
   - Tap **"Add to Home Screen"** or **"Install App"**.
   - You now have a standalone touch quotation app on your phone that reads and writes to your PC database instantly!

---

## 🌐 Option 2: 24/7 Cloud Sync (Anywhere in the World over 4G/5G)

To keep PC and phones synced wherever you go:

### Step 1: Free Cloud Database (Supabase)
1. Go to [supabase.com](https://supabase.com) and click **Start your project** (Free).
2. Create a new project (e.g. `ama-ceramics`).
3. Under **Project Settings** -> **Database** -> **Connection string**, copy the `URI`:
   ```text
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

### Step 2: Free Backend API Deployment (Render)
1. Go to [render.com](https://render.com) and sign up with your GitHub account.
2. Click **New +** -> **Web Service**.
3. Select your repository: `Quotation-App`.
4. Configure:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   - Key: `DATABASE_URL`
   - Value: Paste your Supabase URI from Step 1.
6. Click **Deploy Web Service**.
7. Render gives you a free HTTPS link (e.g. `https://ama-quotation.onrender.com`).

### Step 3: Connect Desktop App
1. In your desktop app, open **⚙️ Company Settings** -> **☁️ Cloud & Mobile Sync** tab.
2. Paste:
   - **Cloud Database URL**: Your Supabase PostgreSQL URI.
   - **Cloud API Server URL**: Your Render URL (`https://ama-quotation.onrender.com`).
3. Click **⚡ Test Cloud Connection**, then **💾 Save Sync Settings**.
4. Restart your desktop app. It will now connect directly to the cloud database!

### Step 4: Connect Android Phone
- **Web PWA Method**: Open `https://ama-quotation.onrender.com/mobile/` on your Android phone and tap **Add to Home Screen**.
- **Native APK Method**:
  1. Go to your GitHub repository -> **Actions** tab -> **Build Android APK**.
  2. Download `AMA_Ceramics_Quotation_v2.0.apk` from the latest run.
  3. Install the APK on your Android phone.
  4. In the app settings screen, enter `https://ama-quotation.onrender.com` and tap **Save & Apply**.

---

## 📱 Mobile App Features Included

- **⚡ Real-Time Quotation Builder**: Create quotations on the showroom floor directly in front of clients.
- **📦 Multi-Unit Support**: Choose **Box**, **Sqft**, **Pieces**, **Bags**, or **Nos** for every item with automatic rate & quantity calculations.
- **🏷️ CERA Discount Protection**: Automatically distributes overall quotation discounts across non-CERA items while protecting CERA items at 0% discount.
- **🤝 Assisted Deal Sharing**: Assign lead and secondary salespersons with percentage or fixed amount splits.
- **🔒 Encrypted Quotations (-AMA)**: Export customer-safe PDFs with masked product codes (e.g. `HSDS-AMA`) and hidden brand names with 1 tap.
- **💬 1-Tap WhatsApp Sharing**: Send formal quote PDFs directly to customer's WhatsApp chat with pre-filled greeting.
- **👥 Customer Phone Lookup**: Instant customer search by mobile number with historical quotation records.
- **📊 Live Performance Dashboard**: Track monthly targets, won deals, open pipeline, and conversion rates.
