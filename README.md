# 💧 Automated Lake and River Water Quality Monitoring System

A beginner-friendly **Python + Streamlit** web application that checks the quality of
lake and river water using four readings: **pH, TDS, Turbidity and Temperature**.

The app gives the water a score out of 100, labels it **GOOD / CAUTION / POOR**,
suggests **cleaning (treatment) methods**, lists **possible uses with safety warnings**,
keeps a **history with charts**, and lets you **export everything to CSV**.

---

## ⚠️ Very important: this version is software only

| Question | Answer |
| --- | --- |
| Does the app measure real water? | **No.** |
| Are there sensors, Arduino, ESP32? | **No.** |
| Is a solar panel or battery needed? | **No.** |
| Where do the numbers come from? | You **type** them in, or the app **simulates** them. |

The word *Automated* in the title refers to the **automatic analysis, classification
and recommendation** that the software performs. Automatic *measurement* from physical
probes is listed in the **Future Scope** section and is not part of this version.

> **Never use this app to decide if water is safe to drink.**
> It cannot see bacteria, viruses, nitrate, fluoride, pesticides or heavy metals.
> Always confirm with a certified laboratory.

---

## ✨ Features

1. **Dashboard** – project summary, key numbers and a quick trend chart.
2. **New Reading & Analysis** – manual sliders *or* a one-click simulator.
3. **Scoring engine** – 0–100 score per parameter plus one overall score.
4. **Classification** – GOOD, CAUTION or POOR with a safety override rule.
5. **Cleaning Recommendations** – numbered treatment steps with reasons and cost level.
6. **Potential Water Uses** – 7 uses marked SAFE / AFTER TREATMENT / NOT SAFE.
7. **History & Charts** – saved records, filters, line charts and bar charts.
8. **CSV Export** – download the full history or just the last reading.
9. **Testing Guide** – automatic tests plus a manual checklist.
10. **Future Scope** – how real sensors could be added later.

---

## 📁 Project structure

```
water-quality-monitor/
├── app.py                   # the Streamlit web app (start here)
├── requirements.txt         # Python packages
├── README.md                # this file
├── .gitignore
├── .streamlit/
│   └── config.toml          # colours and server settings
├── data/
│   ├── sample_readings.csv  # example data you can look at
│   └── history.csv          # created automatically when you save a reading
├── wq_core/                 # all the logic (no Streamlit inside)
│   ├── __init__.py
│   ├── thresholds.py        # every limit lives here
│   ├── analysis.py          # scoring + GOOD / CAUTION / POOR
│   ├── recommendations.py   # treatment methods + possible uses
│   ├── simulator.py         # fake but realistic readings
│   └── storage.py           # read / write the CSV history
└── tests/
    └── test_analysis.py     # 25+ automatic tests
```

---

## 🚀 Step 1 – Run the app on your computer

You need **Python 3.9 or newer**.

```bash
# 1. get the code
git clone https://github.com/YOUR-USERNAME/water-quality-monitor.git
cd water-quality-monitor

# 2. make a virtual environment (keeps packages tidy)
python -m venv venv

# 3. activate it
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 4. install the packages
pip install -r requirements.txt

# 5. start the app
streamlit run app.py
```

Your browser opens at **http://localhost:8501**.
If it does not open, copy that address into your browser.

To stop the app, press **Ctrl + C** in the terminal.

---

## 🧪 Step 2 – How the scoring works

Each parameter gets a score from **0 (very bad)** to **100 (perfect)**.

| Parameter | Ideal range | Why it matters |
| --- | --- | --- |
| **pH** | 6.5 – 8.5 | Acid water corrodes pipes; alkaline water tastes bitter. |
| **TDS** | 0 – 500 ppm | High dissolved salts make water taste bad and harm crops. |
| **Turbidity** | 0 – 5 NTU | Mud hides microbes and blocks disinfection. |
| **Temperature** | 10 – 25 °C | Warm water holds less oxygen and grows more algae. |

The four scores are mixed with these weights:

```
overall = 0.35 × turbidity + 0.25 × pH + 0.25 × TDS + 0.15 × temperature
```

| Overall score | Label |
| --- | --- |
| 75 – 100 (and no parameter below 60) | **GOOD** |
| 50 – 74 | **CAUTION** |
| below 50 | **POOR** |

**Safety override:** if *any single* parameter scores below **25**, the whole sample
becomes **POOR**, even when the average looks fine. One very bad parameter can make
water dangerous.

---

## 🧼 Step 3 – Treatment recommendations

The app builds a treatment plan in a sensible order:

1. **Remove solids** – settling tank, coagulation (alum / moringa), sand filter, cartridge filter.
2. **Fix the chemistry** – limestone or soda ash for acid water, CO₂ for alkaline water,
   activated carbon / ion exchange / reverse osmosis for high TDS.
3. **Control temperature** – shade, aeration, cooling pond.
4. **Disinfect last** – boiling, chlorine, UV lamp or SODIS solar bottles.
5. **Confirm** – send a sample to a laboratory when quality is CAUTION or POOR.

---

## 🚰 Step 4 – Potential uses

For each sample the app checks seven possible uses:

Drinking & cooking · Bathing & washing · Crop irrigation · Livestock drinking ·
Fish pond · Cleaning / flushing / construction · Industrial cooling

Each one is marked:

* ✅ **SAFE** – fine as it is
* ⚠️ **AFTER TREATMENT** – only after the cleaning steps above
* ⛔ **NOT SAFE** – do not use

Drinking is **never** marked plain SAFE, because raw surface water always needs
treatment and a laboratory test.

---

## ✅ Step 5 – Testing

### Automatic tests

```bash
pip install -r requirements.txt
pytest -v
```

You should see all tests pass. The tests check scoring, classification,
the safety override, treatment rules, use rules and the simulator.

### Manual test cases

| # | pH | TDS | Turbidity | Temp | Expected result |
| --- | --- | --- | --- | --- | --- |
| T1 | 7.2 | 150 | 0.8 | 18 | GOOD |
| T2 | 7.8 | 480 | 4.0 | 24 | GOOD or CAUTION |
| T3 | 6.9 | 520 | 45 | 22 | CAUTION or POOR |
| T4 | 9.3 | 600 | 20 | 30 | CAUTION |
| T5 | 4.5 | 1800 | 60 | 34 | POOR |
| T6 | 0.0 | 0 | 0 | −5 | POOR, no crash |
| T7 | 14.0 | 3000 | 200 | 60 | POOR, no crash |

### Manual checklist

- [ ] Manual sliders produce a result
- [ ] Simulate button fills the sliders
- [ ] Result banner colour changes with the label
- [ ] Treatment steps are numbered
- [ ] Each use shows SAFE / AFTER TREATMENT / NOT SAFE
- [ ] History table grows after each save
- [ ] Charts draw without errors
- [ ] Clear history empties the table
- [ ] CSV download opens in a spreadsheet
- [ ] The "no real sensors" note is visible

---

## 🐙 Step 6 – Put the project on GitHub

```bash
# inside the project folder
git init
git add .
git commit -m "Water quality monitoring system - first version"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/water-quality-monitor.git
git push -u origin main
```

If you do not have a repository yet:

1. Sign in to **github.com**.
2. Click **New repository**.
3. Name it `water-quality-monitor`, keep it **Public**, do **not** add a README
   (you already have one).
4. Click **Create repository** and run the commands above.

Later updates:

```bash
git add .
git commit -m "Describe what you changed"
git push
```

---

## ☁️ Step 7 – Deploy free on Streamlit Community Cloud

1. Make sure the repository is **public** and contains `app.py` and `requirements.txt`.
2. Go to **https://share.streamlit.io** and sign in with GitHub.
3. Click **New app**.
4. Fill the form:
   * **Repository:** `YOUR-USERNAME/water-quality-monitor`
   * **Branch:** `main`
   * **Main file path:** `app.py`
5. Click **Deploy**.
6. Wait about one minute. You get a public link like
   `https://water-quality-monitor.streamlit.app`.

**Tips**

* Every `git push` to `main` redeploys the app automatically.
* On Streamlit Cloud the file system is temporary, so `data/history.csv`
  resets when the app restarts. That is fine for a demo. For permanent
  storage, connect a database later.
* If deployment fails, open **Manage app → Logs** and read the last red lines.
  A missing package in `requirements.txt` is the most common cause.

---

## 🔭 Future scope (not in this version)

* Connect real probes (pH, TDS/EC, turbidity, temperature) to a microcontroller.
* Add an HTTP endpoint so a device can send live readings to the app.
* Solar-powered floating station for continuous monitoring.
* Machine-learning forecast of tomorrow's water quality.
* Email / SMS alerts when water becomes POOR.
* Map view with one marker per site.
* Real database instead of a CSV file.

Because all the logic is inside `wq_core/`, adding real data later only means
replacing `simulator.py` with a real data source. The rest of the app keeps working.

---

## ❓ Troubleshooting

| Problem | Fix |
| --- | --- |
| `streamlit: command not found` | Activate the virtual environment, then `pip install -r requirements.txt`. |
| `ModuleNotFoundError: wq_core` | Run `streamlit run app.py` from inside the project folder. |
| Charts are empty | Save at least two readings first. |
| Port 8501 already used | Run `streamlit run app.py --server.port 8502`. |
| History not saving | Check that the `data/` folder can be written to. |

---

## 📄 License

Released under the MIT License. Free to use for learning.
