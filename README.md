# 🇲🇾 Malaysian Court Daily Cause List Scraper

This Python script automates the extraction of **daily hearing cause list data** from the official [Malaysian eCourt Services website](https://ecourtservices.kehakiman.gov.my/CauseList). It is designed to handle **CAPTCHA challenges**, parse structured hearing data for multiple court locations, and save the results in a clean, organized format.

---

## 📌 Features

- ✅ Automatically iterates through **all available court locations**
- 🗓️ Fetches **hearing details for the current day**
- 🔒 Bypasses **hCaptcha protection** using [AntiCaptcha](https://anti-captcha.com/)
- 📁 Saves hearing data for each court into separate **CSV files** in the `DATA/` folder
- 📜 Maintains detailed logs in the `LOGS/` folder
- 🔁 Implements **retry logic** for failed HTTP requests (status codes not in [200, 201])
- ⚙️ Uses a configurable `config.yaml` file for headers, URLs, payloads, XPath selectors, etc.

---

## 🏁 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/malaysia-court-causelist-scraper.git
cd malaysia-court-causelist-scraper
