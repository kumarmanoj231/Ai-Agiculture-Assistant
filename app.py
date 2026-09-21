from datetime import datetime
from io import BytesIO
from pathlib import Path
import textwrap

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from agricultural_util import GreenCureAI
from crop_recommendation import predict_crop
from weather import show_weather


BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "images" / "crop_banner.jpg"


class GreenCureManager:
    def __init__(self):
        self.recommendations = []
        self.diagnoses = []
        self.soil_analyses = []
        self.weather_advisories = []
        self.market_analyses = []

    def _add(self, collection, data):
        collection.append({**data, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    def add_recommendation(self, data):
        self._add(self.recommendations, data)

    def add_diagnosis(self, data):
        self._add(self.diagnoses, data)

    def add_soil_analysis(self, data):
        self._add(self.soil_analyses, data)

    def add_weather_advisory(self, data):
        self._add(self.weather_advisories, data)

    def add_market_analysis(self, data):
        self._add(self.market_analyses, data)


@st.cache_resource(show_spinner=False)
def create_ai_assistant(key_name):
    return GreenCureAI(key_name)


def get_manager():
    if "green_cure_manager" not in st.session_state:
        st.session_state.green_cure_manager = GreenCureManager()
    return st.session_state.green_cure_manager


def page_header(title, subtitle=None):
    st.markdown(f'<h1 class="main-header">{title}</h1>', unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)


def render_ai_selector():
    available = GreenCureAI.available_keys()
    if not available:
        st.sidebar.warning("No Groq API keys configured.")
        st.sidebar.caption("Add GROQ_API_KEY_1..4 in Streamlit Secrets.")
        return None

    selected = st.sidebar.selectbox("AI Model / API Key", available, key="selected_groq_key")
    try:
        assistant = create_ai_assistant(selected)
        st.sidebar.success(f"{selected} ready")
        return assistant
    except Exception as exc:
        st.sidebar.error(f"AI setup failed: {exc}")
        return None


def generate_pdf(manager: GreenCureManager) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40

    def line(text="", bold=False, size=10, gap=15):
        nonlocal y
        if y < 55:
            pdf.showPage()
            y = height - 40
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        for wrapped in textwrap.wrap(str(text), width=95) or [""]:
            if y < 55:
                pdf.showPage()
                y = height - 40
            pdf.drawString(40, y, wrapped)
            y -= gap

    line("GreenCure AI - Comprehensive Agricultural Report", True, 16, 22)
    line(f"Generated on: {datetime.now():%Y-%m-%d %H:%M:%S}", size=10, gap=20)

    sections = [
        ("CROP RECOMMENDATIONS", manager.recommendations, ["crop_name", "location", "season", "expected_yield"]),
        ("DISEASE DIAGNOSES", manager.diagnoses, ["disease_name", "crop_type", "severity", "region"]),
        ("SOIL ANALYSES", manager.soil_analyses, ["soil_type", "region", "ph_analysis"]),
        ("WEATHER ADVISORIES", manager.weather_advisories, ["location", "crop_stage", "conditions"]),
        ("MARKET ANALYSES", manager.market_analyses, ["crop_type", "location", "current_price", "demand_status"]),
    ]

    for title, records, fields in sections:
        if not records:
            continue
        line(title, True, 13, 18)
        for index, record in enumerate(records[-5:], 1):
            line(f"Entry {index}", True, 10, 14)
            for field in fields:
                label = field.replace("_", " ").title()
                line(f"{label}: {record.get(field, 'N/A')}", gap=13)
            line("-" * 80, gap=10)

    pdf.save()
    return buffer.getvalue()


def main():
    st.set_page_config(
        page_title="GreenCure AI | Agriculture Assistant",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <style>
    .main-header { font-size: 2.6rem; color: #2E7D32; text-align: center; margin-bottom: .75rem; }
    .metric-card { background: #f0f8f0; padding: 1rem; border-radius: .75rem; border-left: 4px solid #2E7D32; }
    div.stButton > button { border-radius: .5rem; }
    </style>
    """, unsafe_allow_html=True)

    manager = get_manager()

    st.sidebar.title("🌱 GreenCure AI")
    st.sidebar.caption("AI-powered agriculture assistant")
    st.sidebar.divider()

    menu_options = [
        "Dashboard",
        "Crop Recommendations",
        "Disease Diagnosis",
        "Soil Analysis",
        "Weather Advisory",
        "Market Analysis",
        "Farm Analytics",
        "Reports",
    ]
    selected_option = st.sidebar.selectbox("Choose Service", menu_options)

    st.sidebar.divider()
    needs_ai = selected_option in {
        "Crop Recommendations",
        "Disease Diagnosis",
        "Soil Analysis",
        "Weather Advisory",
        "Market Analysis",
    }
    ai_assistant = render_ai_selector() if needs_ai else None

    if selected_option == "Dashboard":
        display_dashboard()
    elif selected_option == "Crop Recommendations":
        display_crop_page(ai_assistant, manager)
    elif selected_option == "Disease Diagnosis":
        display_disease_diagnosis(ai_assistant, manager)
    elif selected_option == "Soil Analysis":
        display_soil_analysis(ai_assistant, manager)
    elif selected_option == "Weather Advisory":
        display_weather_advisory(ai_assistant, manager)
    elif selected_option == "Market Analysis":
        display_market_analysis(ai_assistant, manager)
    elif selected_option == "Farm Analytics":
        display_farm_analytics(manager)
    elif selected_option == "Reports":
        display_reports(manager)


def display_dashboard():
    page_header(
        "🌾 Welcome to GreenCure AI",
        "Machine learning, weather data and AI-powered agricultural insights in one place.",
    )

    if IMAGE_PATH.exists():
        st.image(str(IMAGE_PATH), caption="Helping farmers make smarter agricultural decisions.", use_container_width=True)
    else:
        st.info("Crop banner image is not available. Add images/crop_banner.jpg to the repository.")

    st.markdown("### 🌦️ Seven-Day Weather Forecast")
    show_weather()


def require_ai(ai_assistant):
    if ai_assistant is None:
        st.warning("AI features are unavailable. Configure at least one Groq API key in Streamlit Secrets.")
        return False
    return True


def display_crop_page(ai_assistant, manager):
    page_header("Smart Crop Recommendations", "Combine ML crop prediction with AI farming guidance.")

    st.subheader("🌱 Traditional ML Crop Prediction")
    with st.form("ml_crop_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            nitrogen = st.number_input("Nitrogen (N)", min_value=0.0, value=50.0)
        with c2:
            phosphorus = st.number_input("Phosphorus (P)", min_value=0.0, value=50.0)
        with c3:
            potassium = st.number_input("Potassium (K)", min_value=0.0, value=50.0)
        c4, c5, c6, c7 = st.columns(4)
        with c4:
            temperature = st.number_input("Temperature (°C)", value=25.0)
        with c5:
            humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=70.0)
        with c6:
            ph = st.number_input("pH", min_value=0.0, max_value=14.0, value=6.5)
        with c7:
            rainfall = st.number_input("Rainfall (mm)", min_value=0.0, value=100.0)
        predict_submitted = st.form_submit_button("Predict Crop", type="primary", use_container_width=True)

    if predict_submitted:
        try:
            result = predict_crop(nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall)
            st.success(f"🌾 Recommended Crop: **{result.title()}**")
        except Exception as exc:
            st.error(f"Crop model failed: {exc}")

    st.divider()
    st.subheader("🤖 AI Crop Recommendation")
    if not require_ai(ai_assistant):
        return

    with st.form("crop_ai_form"):
        c1, c2 = st.columns(2)
        with c1:
            location = st.text_input("Location / District", placeholder="e.g. Guna, Madhya Pradesh")
            soil_type = st.selectbox("Soil Type", [
                "Black Soil (Regur)", "Red Soil", "Alluvial Soil", "Laterite Soil",
                "Desert Soil", "Mountain Soil", "Clay", "Sandy", "Loamy"
            ])
        with c2:
            season = st.selectbox("Season", ["Kharif (Monsoon)", "Rabi (Winter)", "Zaid (Summer)"])
            farm_size = st.selectbox("Farm Size", [
                "Marginal (< 1 hectare)", "Small (1-2 hectares)",
                "Semi-medium (2-4 hectares)", "Medium (4-10 hectares)", "Large (> 10 hectares)"
            ])
        submitted = st.form_submit_button("Get AI Recommendation", type="primary", use_container_width=True)

    if not submitted:
        return
    if not location.strip():
        st.error("Please enter your location.")
        return

    with st.spinner("AI is analyzing your farming conditions..."):
        try:
            recommendation = ai_assistant.get_crop_recommendation(location, soil_type, season, farm_size)
        except Exception as exc:
            st.error(f"AI recommendation failed: {exc}")
            return

    manager.add_recommendation({
        "location": location,
        "soil_type": soil_type,
        "season": season,
        "farm_size": farm_size,
        "crop_name": recommendation.crop_name,
        "planting_season": recommendation.planting_season,
        "expected_yield": recommendation.expected_yield,
        "market_value": recommendation.market_value,
        "care_instructions": recommendation.care_instructions,
    })

    st.success("Recommendation generated successfully!")
    left, right = st.columns([2, 1])
    with left:
        st.markdown(f"### Recommended Crop: **{recommendation.crop_name}**")
        st.info(f"**Best planting season:** {recommendation.planting_season}")
        st.info(f"**Expected yield:** {recommendation.expected_yield}")
        st.success(f"**Market information:** {recommendation.market_value}")
        st.markdown("#### Care Instructions")
        for i, instruction in enumerate(recommendation.care_instructions, 1):
            st.markdown(f"**{i}.** {instruction}")
    with right:
        st.markdown("### Farm Summary")
        st.write(f"**Location:** {location}")
        st.write(f"**Soil:** {soil_type}")
        st.write(f"**Season:** {season}")
        st.write(f"**Farm size:** {farm_size}")

    report = f"""GREEN CURE - CROP RECOMMENDATION REPORT

Location: {location}
Soil Type: {soil_type}
Season: {season}
Farm Size: {farm_size}
Generated: {datetime.now():%Y-%m-%d %H:%M:%S}

Crop: {recommendation.crop_name}
Planting Season: {recommendation.planting_season}
Expected Yield: {recommendation.expected_yield}
Market Information: {recommendation.market_value}

CARE INSTRUCTIONS:
""" + "\n".join(f"{i}. {x}" for i, x in enumerate(recommendation.care_instructions, 1))
    st.download_button("Download Recommendation", report, f"crop_recommendation_{datetime.now():%Y%m%d_%H%M%S}.txt", "text/plain")


def display_disease_diagnosis(ai_assistant, manager):
    page_header("Smart Disease Diagnosis", "Use symptoms and crop information to get AI-assisted guidance.")
    if not require_ai(ai_assistant):
        return

    with st.form("disease_form"):
        c1, c2 = st.columns(2)
        with c1:
            crop_type = st.selectbox("Crop Type", [
                "Wheat", "Rice", "Cotton", "Sugarcane", "Soybean", "Maize", "Bajra", "Jowar",
                "Potato", "Tomato", "Onion", "Garlic", "Chilli", "Other"
            ])
            region = st.text_input("Region / State", placeholder="e.g. Madhya Pradesh")
        with c2:
            symptoms = st.text_area("Describe Symptoms", placeholder="Yellow spots, wilting, brown patches, insect damage...", height=120)
        submitted = st.form_submit_button("Diagnose Disease", type="primary", use_container_width=True)

    if not submitted:
        return
    if not symptoms.strip():
        st.error("Please describe the symptoms.")
        return

    with st.spinner("AI is analyzing the symptoms..."):
        try:
            diagnosis = ai_assistant.diagnose_crop_disease(crop_type, symptoms, region)
        except Exception as exc:
            st.error(f"Disease diagnosis failed: {exc}")
            return

    manager.add_diagnosis({
        "crop_type": crop_type, "region": region, "symptoms_described": symptoms,
        "disease_name": diagnosis.disease_name, "severity": diagnosis.severity,
        "symptoms": diagnosis.symptoms, "treatment": diagnosis.treatment, "prevention": diagnosis.prevention,
    })

    st.success("Disease analysis complete.")
    st.markdown(f"### Diagnosis: **{diagnosis.disease_name}**")
    st.markdown(f"### Severity: **{diagnosis.severity}**")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Identified Symptoms")
        for item in diagnosis.symptoms:
            st.markdown(f"- {item}")
        st.markdown("#### Treatment Recommendations")
        for i, item in enumerate(diagnosis.treatment, 1):
            st.markdown(f"**{i}.** {item}")
    with c2:
        st.markdown("#### Prevention")
        for i, item in enumerate(diagnosis.prevention, 1):
            st.markdown(f"**{i}.** {item}")

    report = f"""GREEN CURE - DISEASE DIAGNOSIS REPORT

Crop: {crop_type}
Region: {region}
Symptoms: {symptoms}
Disease: {diagnosis.disease_name}
Severity: {diagnosis.severity}

IDENTIFIED SYMPTOMS:
""" + "\n".join(f"- {x}" for x in diagnosis.symptoms) + "\n\nTREATMENT:\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(diagnosis.treatment, 1)) + "\n\nPREVENTION:\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(diagnosis.prevention, 1))
    st.download_button("Download Diagnosis Report", report, f"disease_diagnosis_{datetime.now():%Y%m%d_%H%M%S}.txt", "text/plain")


def display_soil_analysis(ai_assistant, manager):
    page_header("Smart Soil Analysis", "Analyze pH, organic matter and drainage conditions.")
    if not require_ai(ai_assistant):
        return

    with st.form("soil_form"):
        c1, c2 = st.columns(2)
        with c1:
            ph_level = st.slider("Soil pH Level", 1.0, 14.0, 7.0, 0.1)
            organic_matter = st.selectbox("Organic Matter", ["Very Low (< 0.5%)", "Low (0.5-1.0%)", "Medium (1.0-3.0%)", "Good (3.0-5.0%)", "High (> 5.0%)"])
        with c2:
            drainage = st.selectbox("Drainage Quality", ["Very Poor", "Poor", "Fair", "Good", "Excellent"])
            region = st.text_input("Region / District", placeholder="e.g. Guna, Madhya Pradesh")
        submitted = st.form_submit_button("Analyze Soil", type="primary", use_container_width=True)

    if not submitted:
        return
    if not region.strip():
        st.error("Please enter your region.")
        return

    with st.spinner("AI is analyzing soil conditions..."):
        try:
            analysis = ai_assistant.analyze_soil_conditions(ph_level, organic_matter, drainage, region)
        except Exception as exc:
            st.error(f"Soil analysis failed: {exc}")
            return

    manager.add_soil_analysis({
        "region": region, "ph_level_input": ph_level, "organic_matter": organic_matter,
        "drainage": drainage, "soil_type": analysis.soil_type, "ph_analysis": analysis.ph_level,
        "nutrient_status": analysis.nutrient_status, "recommendations": analysis.recommendations,
        "suitable_crops": analysis.suitable_crops,
    })

    st.success("Soil analysis complete.")
    c1, c2 = st.columns([1, 2])
    with c1:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=ph_level, title={"text": "Soil pH"}, gauge={"axis": {"range": [0, 14]}}))
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"Organic matter: {organic_matter}")
        st.info(f"Drainage: {drainage}")
    with c2:
        st.markdown(f"### Soil Type: **{analysis.soil_type}**")
        st.write(f"**pH Analysis:** {analysis.ph_level}")
        st.markdown("#### Nutrient Status")
        for item in analysis.nutrient_status:
            st.markdown(f"- {item}")
        st.markdown("#### Improvement Recommendations")
        for i, item in enumerate(analysis.recommendations, 1):
            st.markdown(f"**{i}.** {item}")
        st.markdown("#### Suitable Crops")
        for item in analysis.suitable_crops:
            st.success(item)


def display_weather_advisory(ai_assistant, manager):
    page_header("Weather-Based Farming Advisory", "Turn current conditions and crop stage into practical guidance.")
    if not require_ai(ai_assistant):
        return

    with st.form("weather_advisory_form"):
        location = st.text_input("Location", placeholder="e.g. Guna, Madhya Pradesh")
        current_weather = st.text_area("Current Weather Conditions", placeholder="Temperature, humidity, rainfall, wind, etc.", height=100)
        crop_stage = st.selectbox("Current Crop Stage", [
            "Land Preparation", "Sowing/Planting", "Germination", "Vegetative Growth",
            "Flowering/Pollination", "Fruit Development", "Maturity", "Harvesting"
        ])
        submitted = st.form_submit_button("Get Weather Advisory", type="primary", use_container_width=True)

    if not submitted:
        return
    if not location.strip() or not current_weather.strip():
        st.error("Please fill in the location and current weather.")
        return

    with st.spinner("AI is generating weather advice..."):
        try:
            advisory = ai_assistant.get_weather_advisory(location, current_weather, crop_stage)
        except Exception as exc:
            st.error(f"Weather advisory failed: {exc}")
            return

    manager.add_weather_advisory({
        "location": location, "current_weather": current_weather, "crop_stage": crop_stage,
        "conditions": advisory.current_conditions, "farming_impact": advisory.farming_impact,
        "recommendations": advisory.recommendations, "alerts": advisory.alerts,
    })

    st.success("Weather advisory generated.")
    st.info(advisory.current_conditions)
    st.warning(advisory.farming_impact)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Recommendations")
        for i, item in enumerate(advisory.recommendations, 1):
            st.markdown(f"**{i}.** {item}")
    with c2:
        st.markdown("### Alerts")
        if advisory.alerts:
            for item in advisory.alerts:
                st.error(item)
        else:
            st.success("No critical alerts reported.")


def display_market_analysis(ai_assistant, manager):
    page_header("Market Intelligence & Analysis", "AI-assisted market guidance. Verify live prices with official/local mandi sources.")
    if not require_ai(ai_assistant):
        return

    with st.form("market_form"):
        c1, c2 = st.columns(2)
        with c1:
            crop_type = st.selectbox("Crop Type", ["Wheat", "Rice", "Cotton", "Sugarcane", "Soybean", "Maize", "Bajra", "Jowar", "Potato", "Tomato", "Coriander", "Onion", "Garlic", "Chilli", "Groundnut", "Other"])
            location = st.text_input("Market Location", placeholder="e.g. Guna Mandi, Madhya Pradesh")
        with c2:
            quantity = st.selectbox("Expected Quantity", ["Small (< 10 quintals)", "Medium (10-50 quintals)", "Large (50-200 quintals)", "Bulk (> 200 quintals)"])
        submitted = st.form_submit_button("Get Market Analysis", type="primary", use_container_width=True)

    if not submitted:
        return
    if not location.strip():
        st.error("Please enter the market location.")
        return

    with st.spinner("AI is analyzing market conditions..."):
        try:
            analysis = ai_assistant.analyze_market_conditions(crop_type, location, quantity)
        except Exception as exc:
            st.error(f"Market analysis failed: {exc}")
            return

    manager.add_market_analysis({
        "crop_type": crop_type, "location": location, "quantity": quantity,
        "current_price": analysis.current_price, "price_trend": analysis.price_trend,
        "demand_status": analysis.demand_status, "selling_tips": analysis.selling_tips,
    })

    st.success("Market analysis complete.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Current Pricing")
        st.info(analysis.current_price)
        st.markdown("### Price Trend")
        st.info(analysis.price_trend)
    with c2:
        st.markdown("### Demand")
        st.warning(analysis.demand_status)
        st.markdown("### Selling Tips")
        for i, item in enumerate(analysis.selling_tips, 1):
            st.markdown(f"**{i}.** {item}")


def display_farm_analytics(manager):
    page_header("Farm Analytics & Insights", "Session-level usage analytics for this app session.")

    counts = {
        "Recommendations": len(manager.recommendations),
        "Diagnoses": len(manager.diagnoses),
        "Soil Analyses": len(manager.soil_analyses),
        "Weather Advisories": len(manager.weather_advisories),
        "Market Analyses": len(manager.market_analyses),
    }

    cols = st.columns(5)
    for col, (label, value) in zip(cols, counts.items()):
        with col:
            st.metric(label, value)

    usage_df = pd.DataFrame({"Service": list(counts), "Usage Count": list(counts.values())})
    if usage_df["Usage Count"].sum() > 0:
        st.plotly_chart(px.pie(usage_df, values="Usage Count", names="Service", title="Service Usage"), use_container_width=True)
    else:
        st.info("Use the services to populate analytics.")

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    yield_df = pd.DataFrame({"Month": months, "Expected Yield": [120, 140, 160, 180, 200, 220]})
    revenue_df = pd.DataFrame({"Month": months, "Projected Revenue": [50000, 60000, 70000, 80000, 90000, 100000]})
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.line(yield_df, x="Month", y="Expected Yield", title="Expected Crop Yield Trend"), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(revenue_df, x="Month", y="Projected Revenue", title="Projected Monthly Revenue (₹)"), use_container_width=True)


def display_reports(manager):
    page_header("Reports & Documentation", "Generate downloadable summaries without requiring persistent server storage.")

    report_type = st.selectbox("Select Report Type", [
        "Comprehensive Farm Report", "Crop Recommendations Summary", "Disease Diagnosis History",
        "Soil Analysis Summary", "Weather Advisory Log", "Market Analysis Report"
    ])

    if st.button("Generate Report", type="primary", use_container_width=True):
        if report_type == "Comprehensive Farm Report":
            pdf_bytes = generate_pdf(manager)
            st.success("PDF report generated.")
            st.download_button("Download PDF Report", pdf_bytes, f"green_cure_report_{datetime.now():%Y%m%d_%H%M%S}.pdf", "application/pdf")
        else:
            content = generate_specific_report(manager, report_type)
            st.success("Report generated.")
            st.text_area("Report Preview", content, height=350)
            st.download_button("Download Report", content, f"{report_type.lower().replace(' ', '_')}_{datetime.now():%Y%m%d_%H%M%S}.txt", "text/plain")


def generate_specific_report(manager, report_type):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if report_type == "Crop Recommendations Summary":
        records = manager.recommendations
    elif report_type == "Disease Diagnosis History":
        records = manager.diagnoses
    elif report_type == "Soil Analysis Summary":
        records = manager.soil_analyses
    elif report_type == "Weather Advisory Log":
        records = manager.weather_advisories
    else:
        records = manager.market_analyses

    lines = [f"GREEN CURE - {report_type.upper()}", "=" * 50, f"Generated on: {timestamp}", f"Total entries: {len(records)}", ""]
    for index, record in enumerate(records, 1):
        lines.append(f"Entry {index}:")
        for key, value in record.items():
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        lines.append("-" * 50)
    if not records:
        lines.append("No data recorded in this session.")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
