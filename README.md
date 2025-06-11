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
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Configuration

- Ensure `config.yaml` contains your `AntiCaptcha` API key and appropriate parameters.
- You can customize headers, request payloads, and XPath selectors as needed.

### 4. Run the Script

```bash
python fetch_causelist.py
```

---

## 📁 Output Structure

```
.
├── fetch_causelist.py
├── config.yaml
├── requirements.txt
├── DATA/
│   ├── court_01.csv
│   ├── court_02.csv
│   └── ...
└── LOGS/
    ├── run_2025-06-10.log
    └── ...
```

---

## ✅ Captcha Handling

This scraper uses **AntiCaptcha** service to bypass hCaptcha:

- Extracts `sitekey` and target URL from the court's cause list page
- Sends request to AntiCaptcha and retrieves a **solved token**
- Includes the token in the POST request to **successfully bypass the CAPTCHA**

> 🔐 You must have a valid AntiCaptcha API key. Enter this key in `config.yaml`.

---

## 📊 Data Coverage

- ✔️ Extracted data from the **first 50 courts**
- 📅 Covers **today's hearings**
- 📄 Each court’s data is stored separately for easy access and analysis

---

## 🧰 Requirements

- Python 3.7+
- Modules listed in `requirements.txt` including:
  - `requests`
  - `PyYAML`
  - `lxml` or `parsel`
  - any other module your script depends on

---

## 🛠️ Troubleshooting

- **Session Failures / CAPTCHA Errors:** Check if your AntiCaptcha balance is sufficient and API key is valid.
- **Incomplete Data:** Refer to the logs in the `LOGS/` folder for debugging.
- **Website Changes:** If selectors or endpoints change, update `config.yaml` accordingly.

---

## 🧑‍💻 Author

**Yashwant Jangir**  
Web Scraping Specialist | Data Engineer  
Feel free to reach out for freelance or collaboration opportunities!

---

## 📄 License

This project is licensed under the MIT License.
