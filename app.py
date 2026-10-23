"""
Automated Lake and River Water Quality Monitoring System
========================================================

A software-only Streamlit web app.

IMPORTANT
---------
This version does NOT read real water. There are no sensors, no Arduino,
no ESP32, no solar panel and no battery. You either:

  1. type the readings in yourself (Manual Entry), or
  2. let the app create realistic practice numbers (Simulation).

Run the app with:

    streamlit run app.py
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from wq_core.analysis import analyse_reading
from wq_core.recommendations import GENERAL_WARNINGS, recommend_treatments, suggest_uses
from wq_core.simulator import SCENARIOS, DEFAULT_SITES, simulate_many, simulate_reading
from wq_core.storage import (
    COLUMNS,
    append_many,
    append_reading,
    clear_history,
    history_to_csv,
    load_history,
)
from wq_core.thresholds import PARAMETERS

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Water Quality Monitoring System",
    page_icon="💧",
    layout="wide",
)

QUALITY_COLOURS = {
    "GOOD": "#16a34a",
    "CAUTION": "#d97706",
    "POOR": "#dc2626",
}

VERDICT_ICON = {
    "SAFE": "✅",
    "AFTER TREATMENT": "⚠️",
    "NOT SAFE": "⛔",
}


def load_history_df() -> pd.DataFrame:
    """Read the CSV history into a pandas DataFrame."""
    rows = load_history()
    if not rows:
        return pd.DataFrame(columns=COLUMNS)
    frame = pd.DataFrame(rows)
    for column in ["ph", "tds", "turbidity", "temperature", "overall_score",
                   "ph_score", "tds_score", "turbidity_score", "temperature_score"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    return frame


def quality_banner(analysis: dict) -> None:
    """Show the big coloured result box."""
    colour = QUALITY_COLOURS[analysis["quality"]]
    st.markdown(
        f"""
        <div style="background:{colour};color:white;padding:22px;border-radius:14px;">
            <div style="font-size:14px;opacity:.9;letter-spacing:1px;">OVERALL WATER QUALITY</div>
            <div style="font-size:44px;font-weight:800;line-height:1.1;">{analysis['quality']}</div>
            <div style="font-size:18px;margin-top:4px;">Score: {analysis['overall_score']} / 100</div>
            <div style="font-size:15px;margin-top:8px;">{analysis['meaning']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if analysis["override_reason"]:
        st.warning(analysis["override_reason"])


def show_parameter_cards(analysis: dict) -> None:
    """Show one card per parameter with value, score and status."""
    columns = st.columns(4)
    for column, key in zip(columns, ["ph", "tds", "turbidity", "temperature"]):
        detail = analysis["details"][key]
        colour = QUALITY_COLOURS[detail["status"]]
        with column:
            st.markdown(
                f"""
                <div style="border:1px solid #e2e8f0;border-left:6px solid {colour};
                            border-radius:12px;padding:14px;background:white;">
                    <div style="font-size:13px;color:#64748b;">{detail['label']} ({detail['unit'] or '-'})</div>
                    <div style="font-size:28px;font-weight:700;color:#0f172a;">{detail['value']}</div>
                    <div style="font-size:13px;color:{colour};font-weight:700;">{detail['status']} &middot; {detail['score']}/100</div>
                    <div style="font-size:12px;color:#475569;margin-top:6px;">Ideal: {detail['ideal_low']} - {detail['ideal_high']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.write("")
    for key in ["ph", "tds", "turbidity", "temperature"]:
        detail = analysis["details"][key]
        st.caption(f"**{detail['label']}** - {detail['note']}")


def show_disclaimer() -> None:
    st.info(
        "**Software-only project.** This app does not measure real water. "
        "All readings are typed in by hand or created by the built-in simulator. "
        "Real sensors are listed in the Future Scope page."
    )


# ---------------------------------------------------------------------------
# Session state (memory that survives button clicks)
# ---------------------------------------------------------------------------

if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None
if "form_values" not in st.session_state:
    st.session_state.form_values = {"ph": 7.2, "tds": 320.0, "turbidity": 3.0, "temperature": 21.0}


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.title("💧 Water Quality Monitor")
st.sidebar.caption("Software-only demonstration project")

page = st.sidebar.radio(
    "Go to page",
    [
        "🏠 Dashboard",
        "🧪 New Reading & Analysis",
        "🧼 Cleaning Recommendations",
        "🚰 Potential Water Uses",
        "📜 History & Charts",
        "⬇️ Export CSV",
        "✅ Testing Guide",
        "🔭 Future Scope",
        "ℹ️ About & Help",
    ],
)

st.sidebar.divider()
st.sidebar.warning("No sensors are connected. Readings are manual or simulated.")


# ===========================================================================
# PAGE 1 - DASHBOARD
# ===========================================================================

if page == "🏠 Dashboard":
    st.title("Automated Lake and River Water Quality Monitoring System")
    st.caption("Version 1.0 - software only - no physical hardware required")
    show_disclaimer()

    history = load_history_df()

    column1, column2, column3, column4 = st.columns(4)
    column1.metric("Saved readings", len(history))
    if len(history):
        column2.metric("Average score", f"{history['overall_score'].mean():.1f}/100")
        column3.metric("GOOD samples", int((history["quality"] == "GOOD").sum()))
        column4.metric("POOR samples", int((history["quality"] == "POOR").sum()))
    else:
        column2.metric("Average score", "-")
        column3.metric("GOOD samples", 0)
        column4.metric("POOR samples", 0)

    st.subheader("What this project does")
    st.markdown(
        """
1. You **enter** four water readings, or press a button to **simulate** them.
2. The app gives each reading a **score out of 100**.
3. The four scores are combined into one label: **GOOD**, **CAUTION** or **POOR**.
4. The app lists **cleaning (treatment) methods** that would fix the problems.
5. The app lists **possible uses** of the water with clear **safety warnings**.
6. Every reading is saved to a CSV file so you can view **history and charts**.
        """
    )

    st.subheader("The four parameters")
    table = pd.DataFrame(
        [
            {
                "Parameter": info["label"],
                "Unit": info["unit"] or "-",
                "Ideal range": f"{info['ideal_low']} - {info['ideal_high']}",
                "What it tells us": info["help"],
            }
            for info in PARAMETERS.values()
        ]
    )
    st.dataframe(table, use_container_width=True, hide_index=True)

    if len(history):
        st.subheader("Recent trend of the overall score")
        chart_data = history.tail(30).set_index("timestamp")[["overall_score"]]
        st.line_chart(chart_data)

        st.subheader("Last 5 saved readings")
        st.dataframe(
            history.tail(5)[["timestamp", "location", "ph", "tds", "turbidity",
                             "temperature", "overall_score", "quality"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No readings saved yet. Open **New Reading & Analysis** to begin.")


# ===========================================================================
# PAGE 2 - NEW READING AND ANALYSIS
# ===========================================================================

elif page == "🧪 New Reading & Analysis":
    st.title("🧪 New Reading & Analysis")
    show_disclaimer()

    mode = st.radio("How do you want to get the readings?",
                    ["✍️ Manual entry", "🎲 Simulate one reading"],
                    horizontal=True)

    if mode == "🎲 Simulate one reading":
        simulate_columns = st.columns([2, 2, 1])
        scenario = simulate_columns[0].selectbox("Choose a situation", list(SCENARIOS.keys()))
        site = simulate_columns[1].selectbox("Choose a site", DEFAULT_SITES)
        simulate_columns[2].write("")
        if simulate_columns[2].button("Generate", use_container_width=True):
            fake = simulate_reading(scenario=scenario, location=site)
            st.session_state.form_values = {
                "ph": float(fake["ph"]),
                "tds": float(fake["tds"]),
                "turbidity": float(fake["turbidity"]),
                "temperature": float(fake["temperature"]),
            }
            st.success(f"Simulated a reading for '{scenario}'. The numbers below were filled in for you.")

    with st.form("reading_form"):
        row1 = st.columns(2)
        location = row1[0].text_input("Site / location name", value="River Bridge Point")
        source_type = row1[1].selectbox("Water source type", ["Lake", "River", "Pond", "Canal", "Reservoir"])

        row2 = st.columns(2)
        ph = row2[0].slider("pH (0 - 14)", 0.0, 14.0,
                            value=st.session_state.form_values["ph"], step=0.1,
                            help=PARAMETERS["ph"]["help"])
        tds = row2[1].slider("TDS (ppm)", 0.0, 3000.0,
                             value=st.session_state.form_values["tds"], step=5.0,
                             help=PARAMETERS["tds"]["help"])

        row3 = st.columns(2)
        turbidity = row3[0].slider("Turbidity (NTU)", 0.0, 200.0,
                                   value=st.session_state.form_values["turbidity"], step=0.5,
                                   help=PARAMETERS["turbidity"]["help"])
        temperature = row3[1].slider("Temperature (C)", -5.0, 60.0,
                                     value=st.session_state.form_values["temperature"], step=0.5,
                                     help=PARAMETERS["temperature"]["help"])

        save_it = st.checkbox("Save this reading to the history file", value=True)
        submitted = st.form_submit_button("Analyse water", use_container_width=True)

    if submitted:
        analysis = analyse_reading(ph, tds, turbidity, temperature,
                                   location=location, source_type=source_type)
        st.session_state.last_analysis = analysis
        st.session_state.form_values = {"ph": ph, "tds": tds,
                                        "turbidity": turbidity, "temperature": temperature}
        if save_it:
            append_reading(analysis, entry_mode="Manual" if mode.startswith("✍️") else "Simulated")
            st.toast("Reading saved to history.csv")

    analysis = st.session_state.last_analysis
    if analysis:
        st.divider()
        quality_banner(analysis)
        st.write("")
        show_parameter_cards(analysis)

        st.subheader("Score of each parameter")
        score_frame = pd.DataFrame(
            {"Parameter": [analysis["details"][k]["label"] for k in analysis["scores"]],
             "Score": list(analysis["scores"].values())}
        ).set_index("Parameter")
        st.bar_chart(score_frame)

        st.success("Next: open **Cleaning Recommendations** and **Potential Water Uses** in the sidebar.")
    else:
        st.info("Fill the form above and press **Analyse water**.")


# ===========================================================================
# PAGE 3 - CLEANING RECOMMENDATIONS
# ===========================================================================

elif page == "🧼 Cleaning Recommendations":
    st.title("🧼 Cleaning / Treatment Recommendations")
    analysis = st.session_state.last_analysis

    if not analysis:
        st.warning("Please analyse a reading first on the **New Reading & Analysis** page.")
    else:
        quality_banner(analysis)
        st.write("")
        st.subheader("Suggested treatment steps, in order")

        steps = recommend_treatments(analysis)
        for step in steps:
            with st.container(border=True):
                st.markdown(f"**Step {step['step']}: {step['method']}**")
                st.caption(step["reason"])
                st.markdown(f"Estimated cost level: `{step['cost']}`")

        st.subheader("Summary table")
        st.dataframe(
            pd.DataFrame(steps)[["step", "method", "cost", "reason"]]
            .rename(columns={"step": "Step", "method": "Method",
                             "cost": "Cost", "reason": "Why"}),
            use_container_width=True, hide_index=True,
        )

        st.error(
            "**Safety note:** treatment advice here is educational. "
            "Always confirm with a certified laboratory before anyone drinks the water."
        )


# ===========================================================================
# PAGE 4 - POTENTIAL WATER USES
# ===========================================================================

elif page == "🚰 Potential Water Uses":
    st.title("🚰 Potential Uses of This Water")
    analysis = st.session_state.last_analysis

    if not analysis:
        st.warning("Please analyse a reading first on the **New Reading & Analysis** page.")
    else:
        quality_banner(analysis)
        st.write("")

        uses = suggest_uses(analysis)
        left, right = st.columns(2)
        for index, item in enumerate(uses):
            target = left if index % 2 == 0 else right
            with target:
                with st.container(border=True):
                    st.markdown(f"### {VERDICT_ICON[item['verdict']]} {item['use']}")
                    st.markdown(f"**{item['verdict']}**")
                    st.caption(item["reason"])

        st.subheader("Summary table")
        st.dataframe(
            pd.DataFrame(uses).rename(columns={"use": "Possible use",
                                               "verdict": "Verdict",
                                               "reason": "Reason"}),
            use_container_width=True, hide_index=True,
        )

        st.subheader("⚠️ Safety warnings you must read")
        for warning in GENERAL_WARNINGS:
            st.markdown(f"- {warning}")


# ===========================================================================
# PAGE 5 - HISTORY AND CHARTS
# ===========================================================================

elif page == "📜 History & Charts":
    st.title("📜 Historical Records & Charts")

    tools = st.columns([2, 2, 2, 2])
    bulk_scenario = tools[0].selectbox("Scenario for bulk simulation", ["Mixed"] + list(SCENARIOS.keys()))
    bulk_count = tools[1].number_input("How many readings?", 1, 200, 20)
    if tools[2].button("🎲 Simulate & save", use_container_width=True):
        chosen = None if bulk_scenario == "Mixed" else bulk_scenario
        fake_rows = simulate_many(int(bulk_count), scenario=chosen)
        analyses = [
            analyse_reading(row["ph"], row["tds"], row["turbidity"], row["temperature"],
                            location=row["location"], source_type=row["source_type"],
                            timestamp=row["timestamp"])
            for row in fake_rows
        ]
        append_many(analyses, entry_mode="Simulated")
        st.success(f"Added {bulk_count} simulated readings.")
        st.rerun()

    if tools[3].button("🗑️ Clear history", use_container_width=True):
        clear_history()
        st.success("History cleared.")
        st.rerun()

    history = load_history_df()

    if history.empty:
        st.info("No records yet. Add readings manually or press **Simulate & save**.")
    else:
        filter_columns = st.columns(2)
        sites = ["All sites"] + sorted(history["location"].dropna().unique().tolist())
        chosen_site = filter_columns[0].selectbox("Filter by site", sites)
        labels = ["All"] + ["GOOD", "CAUTION", "POOR"]
        chosen_label = filter_columns[1].selectbox("Filter by quality", labels)

        view = history.copy()
        if chosen_site != "All sites":
            view = view[view["location"] == chosen_site]
        if chosen_label != "All":
            view = view[view["quality"] == chosen_label]

        st.metric("Rows shown", len(view))

        tab1, tab2, tab3 = st.tabs(["📈 Trends", "📊 Distribution", "📋 Table"])

        with tab1:
            if len(view):
                indexed = view.set_index("timestamp")
                st.markdown("**Overall score over time**")
                st.line_chart(indexed[["overall_score"]])
                st.markdown("**pH and temperature over time**")
                st.line_chart(indexed[["ph", "temperature"]])
                st.markdown("**TDS and turbidity over time**")
                st.line_chart(indexed[["tds", "turbidity"]])

        with tab2:
            if len(view):
                counts = view["quality"].value_counts().reindex(["GOOD", "CAUTION", "POOR"]).fillna(0)
                st.markdown("**How many samples of each class**")
                st.bar_chart(counts)
                st.markdown("**Average score at each site**")
                st.bar_chart(view.groupby("location")["overall_score"].mean())

        with tab3:
            st.dataframe(view.sort_values("timestamp", ascending=False),
                         use_container_width=True, hide_index=True)


# ===========================================================================
# PAGE 6 - EXPORT CSV
# ===========================================================================

elif page == "⬇️ Export CSV":
    st.title("⬇️ Export Data as CSV")
    history = load_history_df()
    st.write(f"There are **{len(history)}** saved readings.")

    csv_text = history_to_csv()
    st.download_button(
        "Download history.csv",
        data=csv_text,
        file_name=f"water_quality_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if st.session_state.last_analysis:
        single = pd.DataFrame([{
            "timestamp": st.session_state.last_analysis["timestamp"],
            "location": st.session_state.last_analysis["location"],
            **st.session_state.last_analysis["values"],
            "overall_score": st.session_state.last_analysis["overall_score"],
            "quality": st.session_state.last_analysis["quality"],
        }])
        st.download_button(
            "Download only the last analysed reading",
            data=single.to_csv(index=False),
            file_name="last_reading.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.subheader("Column meanings")
    st.markdown(
        """
| Column | Meaning |
| --- | --- |
| timestamp | Date and time of the reading |
| location | Site name you typed or picked |
| source_type | Lake, River, Pond, Canal or Reservoir |
| ph / tds / turbidity / temperature | The four raw readings |
| *_score | 0-100 score for that parameter |
| overall_score | Weighted average of the four scores |
| quality | GOOD, CAUTION or POOR |
| entry_mode | Manual or Simulated |
        """
    )
    if not history.empty:
        st.dataframe(history.tail(10), use_container_width=True, hide_index=True)


# ===========================================================================
# PAGE 7 - TESTING GUIDE
# ===========================================================================

elif page == "✅ Testing Guide":
    st.title("✅ How to Test This Project")

    st.subheader("1. Automatic tests")
    st.code("pip install -r requirements.txt\npytest -v", language="bash")
    st.caption("All tests live in the `tests/` folder and check the scoring rules.")

    st.subheader("2. Manual test cases")
    cases = pd.DataFrame([
        {"Test": "T1 Clean lake", "pH": 7.2, "TDS": 150, "Turbidity": 0.8,
         "Temp": 18, "Expected": "GOOD"},
        {"Test": "T2 Normal river", "pH": 7.8, "TDS": 480, "Turbidity": 4.0,
         "Temp": 24, "Expected": "GOOD or CAUTION"},
        {"Test": "T3 After rain", "pH": 6.9, "TDS": 520, "Turbidity": 45,
         "Temp": 22, "Expected": "CAUTION or POOR"},
        {"Test": "T4 Algae bloom", "pH": 9.3, "TDS": 600, "Turbidity": 20,
         "Temp": 30, "Expected": "CAUTION"},
        {"Test": "T5 Acid discharge", "pH": 4.5, "TDS": 1800, "Turbidity": 30,
         "Temp": 34, "Expected": "POOR"},
        {"Test": "T6 Edge low", "pH": 0.0, "TDS": 0, "Turbidity": 0,
         "Temp": -5, "Expected": "POOR (no crash)"},
        {"Test": "T7 Edge high", "pH": 14.0, "TDS": 3000, "Turbidity": 200,
         "Temp": 60, "Expected": "POOR (no crash)"},
    ])
    st.dataframe(cases, use_container_width=True, hide_index=True)

    st.subheader("3. Feature checklist")
    checklist = [
        "Manual entry form accepts values and shows a result",
        "Simulate button fills the form with realistic numbers",
        "Result banner changes colour for GOOD / CAUTION / POOR",
        "Cleaning page lists numbered treatment steps",
        "Uses page shows SAFE / AFTER TREATMENT / NOT SAFE for each use",
        "History page shows saved rows and three charts",
        "Clear history empties the table",
        "CSV download opens correctly in a spreadsheet program",
        "Every page shows the 'no real sensors' note",
    ]
    for item in checklist:
        st.checkbox(item, key=f"check_{item}")


# ===========================================================================
# PAGE 8 - FUTURE SCOPE
# ===========================================================================

elif page == "🔭 Future Scope":
    st.title("🔭 Future Scope")
    st.markdown(
        """
The current version is **100% software**. Nothing is measured automatically.
These ideas are for a possible later version, and are **not part of this project**.
        """
    )
    st.subheader("Planned hardware (future only)")
    st.dataframe(pd.DataFrame([
        {"Idea": "pH probe", "Purpose": "Read pH automatically"},
        {"Idea": "TDS / EC probe", "Purpose": "Read dissolved solids automatically"},
        {"Idea": "Optical turbidity sensor", "Purpose": "Read cloudiness automatically"},
        {"Idea": "Waterproof temperature probe", "Purpose": "Read water temperature"},
        {"Idea": "Microcontroller + Wi-Fi", "Purpose": "Send readings to this app"},
        {"Idea": "Solar panel + battery", "Purpose": "Power a floating station"},
    ]), use_container_width=True, hide_index=True)

    st.subheader("Planned software features (future only)")
    st.markdown(
        """
- A `/api/reading` endpoint so a real device can POST live data.
- Machine-learning prediction of tomorrow's water quality.
- Email or SMS alerts when quality becomes POOR.
- A map view with one marker per monitoring site.
- Multi-user login and role-based access.
- A proper database (SQLite or PostgreSQL) instead of a CSV file.
        """
    )
    st.info("Because the code is split into `wq_core` modules, adding a real "
            "data source later only means replacing the simulator.")


# ===========================================================================
# PAGE 9 - ABOUT AND HELP
# ===========================================================================

else:
    st.title("ℹ️ About & Help")
    show_disclaimer()

    st.subheader("How the score is calculated")
    st.markdown(
        """
1. Each parameter gets a score from 0 (very bad) to 100 (perfect).
2. The scores are mixed using these weights:
   **turbidity 35%, pH 25%, TDS 25%, temperature 15%**.
3. The result is one overall score out of 100.
4. The overall score becomes a label:

| Overall score | Label |
| --- | --- |
| 75 and above (and no weak parameter) | **GOOD** |
| 50 to 74 | **CAUTION** |
| below 50 | **POOR** |

5. Safety override: if **any single parameter scores below 25**, the whole
   sample is marked **POOR**, even when the average looks fine.
        """
    )

    st.subheader("Folder structure")
    st.code(
        """water-quality-monitor/
├── app.py                  # the Streamlit web app (this file)
├── requirements.txt
├── README.md
├── data/
│   └── history.csv         # created automatically
├── wq_core/
│   ├── __init__.py
│   ├── thresholds.py       # all limits
│   ├── analysis.py         # scoring + GOOD/CAUTION/POOR
│   ├── recommendations.py  # treatment + uses
│   ├── simulator.py        # fake readings
│   └── storage.py          # CSV read/write
└── tests/
    └── test_analysis.py""",
        language="text",
    )

    st.subheader("Run it on your computer")
    st.code(
        """git clone https://github.com/YOUR-USERNAME/water-quality-monitor.git
cd water-quality-monitor
python -m venv venv
source venv/bin/activate      # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py""",
        language="bash",
    )

    st.subheader("Put it on Streamlit Community Cloud")
    st.markdown(
        """
1. Push the folder to a **public GitHub repository**.
2. Go to **share.streamlit.io** and sign in with GitHub.
3. Click **New app**, pick your repository and branch `main`.
4. Set **Main file path** to `app.py`.
5. Click **Deploy**. Your app gets a public link in about a minute.
        """
    )

    st.error(
        "**Final warning:** this is a learning project. Do not use it to decide "
        "whether water is safe to drink. Always use a certified laboratory."
    )
