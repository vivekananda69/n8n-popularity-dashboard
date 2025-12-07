
---

# 📊 n8n Workflow Popularity Intelligence Dashboard

*A Streamlit-based analytics system for real-time workflow popularity insights.*

---

## 🔍 Overview

This dashboard visualizes multi-platform **popularity signals** for n8n workflows collected from:

* 🎥 **YouTube** (views, likes, comments, engagement ratios)
* 💬 **n8n Community Forum** (replies, likes, contributors, views)
* 📈 **Google Trends** (search interest + % change over time)

It connects to a Django REST backend that aggregates data for **US** and **India** every 6 hours.

👉 **Live Backend API**
[https://n8n-pop-3yxb.onrender.com/api/workflows/](https://n8n-pop-3yxb.onrender.com/api/workflows/)

👉 **Purpose**
This dashboard is built as part of the **SpeakGenie AI/Data Internship Technical Assignment** by
**Bandapu Vivekananda**.

---

## 🚀 Features

### ⭐ Dashboard Highlights

* Interactive filters: platform, country, keyword search, sorting, limits
* Automated backend refresh trigger (manual + cron-based)
* Platform-wise breakdowns + score distributions
* Workflow-level evidence explorer
* Rich UI: KPI cards, tabs, charts, pills, and data tables
* Cached API calls for speed and optimized Render cold start handling

---

## 🧠 Tech Stack

### **Frontend (This Repo)**

* Streamlit
* Altair
* Pandas
* Requests

### **Backend (Separate Django Repo)**

* Django REST Framework
* CRON scheduler (6-hour interval)
* YouTube API v3
* Discourse API
* Google Trends API (pytrends)

---

## 🏗 Repository Structure

```
n8n-popularity-dashboard/
│
├── streamlit_app.py        # Main Streamlit UI
├── requirements.txt        # Dependencies
└── README.md               # Documentation
```

---

## 📦 Installation (Local Development)

Clone the repo:

```bash
git clone https://github.com/<your-username>/n8n-popularity-dashboard.git
cd n8n-popularity-dashboard
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run streamlit_app.py
```
🎉

---

## 🔗 Backend API Endpoints

| Endpoint                    | Description                    |
| --------------------------- | ------------------------------ |
| `/api/workflows/`           | Fetch workflows with filters   |
| `/api/status/`              | Get cron job health & schedule |
| `/trigger/<src>/<country>/` | Manually trigger collectors    |

---

## 🧪 API Test Script

Use this to test backend triggers:

```python
import requests

url = "https://n8n-pop-3yxb.onrender.com/trigger/youtube/US/"

resp = requests.post(
    url,
    headers={"X-Trigger-Secret": "f91b2d88219a83f0aaecc3fa4423c8d4"},
    timeout=30
)

print("STATUS:", resp.status_code)
print("RESPONSE:", resp.text)
```

---

## 📈 Example Workflow Entry (From Backend)

```json
{
  "workflow": "n8n Google Sheets Automation",
  "platform": "YouTube",
  "country": "US",
  "source_url": "https://youtube.com/watch?v=XYZ",
  "popularity_score": 563.22,
  "popularity_metrics": {
    "views": 18400,
    "likes": 920,
    "comments": 112,
    "like_to_view_ratio": 0.05,
    "comment_to_view_ratio": 0.007
  }
}
```

---

## 👨‍💻 Built By

**Bandapu Vivekananda**
AI/ML Intern Technical Assignment
SpeakGenie – December 2025

---
