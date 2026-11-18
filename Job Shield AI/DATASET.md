# 📊 Job Shield AI - Dataset Documentation

This project utilizes a structured job listing dataset designed for training and evaluating machine learning algorithms on fraudulent versus legitimate job offers.

---

## 1. Included Dataset: `sample_data.csv`
A curated dataset of 66 verified benchmark job postings representing genuine corporate openings as well as prevalent recruitment scam patterns.

### Schema:
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `title` | Text | Job title / designation (e.g., *Data Analyst Intern*, *Customer Support*) |
| `company_profile` | Text | Brief background of the hiring entity or agency |
| `description` | Text | Detailed roles, duties, work arrangement, and financial promises |
| `requirements` | Text | Required qualifications, degrees, skills, and tools |
| `fraudulent` | Integer (`0` or `1`) | Target label: `0` for Legitimate, `1` for Fraudulent / Scam |

### Sample Scam Indicators in Dataset:
* Demands for upfront "security deposit", "laptop dispatch fee", or "training certificate fee".
* Payouts promised via untraceable channels (Cryptocurrency, Telegram transfers, Gift cards).
* Directing applicants away from legitimate platforms to private Telegram channels or WhatsApp chats.
* Unrealistic compensation promises with zero qualification requirements.

---

## 2. External Benchmark Dataset Link
For extended training and large-scale benchmarking, this project is modeled around the **EMSCAD (Employment Scam Aegean Dataset)**:

* 🌐 **Kaggle Dataset Link:** [Real / Fake Job Posting Prediction (EMSCAD) on Kaggle](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction)
* **Dataset Size:** ~18,000 real job descriptions with metadata (telecommuting, company logo, salary range, employment type, requirements).
* **Research Reference:** Aegean University Laboratory of Information & Communication Systems Security (ICCS).
