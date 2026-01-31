import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
import numpy as np
import io
import streamlit.components.v1 as components

# 1. Page Config
st.set_page_config(layout="wide", page_title="Health Intelligence", page_icon="📊")

# 2. UI Enhancement (Fixed Sidebar & Modern Theme)
st.markdown("""
    <style>
    /* --- Layout & Fix for Sidebar Toggle --- */
    html, body, [data-testid="stAppViewContainer"] {
        margin: 0 !important;
        padding: 0 !important;
        height: 100vh !important;
        overflow: hidden !important;
    }

    /* Keep the main block container clear for the fixed iframe */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Fixed Map Iframe */
    iframe {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw !important;
        height: 100vh !important;
        border: none !important;
        z-index: 1;
    }

    /* Ensure Sidebar and Header (Toggle Button) are reachable */
    [data-testid="stSidebar"], [data-testid="stHeader"] {
        z-index: 1000 !important;
        visibility: visible !important;
    }

    /* --- Sidebar Visual Improvements --- */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 2px solid #e2e8f0;
    }

    /* Sidebar Cards: Makes sliders and inputs stand out */
    .stSelectbox, .stSlider, .stFileUploader, div[data-testid="stMetric"] {
        background-color: white !important;
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        margin-bottom: 15px !important;
        border: 1px solid #edf2f7 !important;
    }

    /* Professional Metric Styling */
    [data-testid="stMetricValue"] {
        color: #e11d48 !important; /* Clinic Red color */
        font-family: 'Inter', sans-serif !important;
    }

    /* Professional Action Button */
    .stButton>button {
        background: linear-gradient(135deg, #e11d48 0%, #9f1239 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        transition: 0.3s all ease !important;
    }

    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(225, 29, 72, 0.3) !important;
    }
    </style>

    <script>
    /* Animation for Sidebar elements */
    const sidebarElements = window.parent.document.querySelectorAll('[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div');
    sidebarElements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transition = `opacity 0.5s ease ${index * 0.1}s`;
        setTimeout(() => el.style.opacity = '1', 100);
    });
    </script>
    """, unsafe_allow_html=True)

# 3. Helper: Haversine Formula
def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8 # Earth radius in miles
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi, dlambda = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1-a))

# Clinic Locations
hosp_data = {
    'Name': ['Downtown Clinic', 'East Hub', 'West Medical', 'South Center', 'North Health'],
    'Latitude': [38.2527, 38.2450, 38.2600, 38.1800, 38.3200],
    'Longitude': [-85.7585, -85.6000, -85.8500, -85.7500, -85.7000]
}
hosp = pd.DataFrame(hosp_data)

# 4. Sidebar Logic
with st.sidebar:
    st.title("🏥 Health Intelligence")
    uploaded_file = st.file_uploader("Upload Patient Data", type=['xlsx', 'csv'])
    st.divider()
    radius = st.select_slider("Service Radius (Miles)", options=[1, 2, 3, 5, 8, 10, 15, 20], value=5)
    map_style = st.selectbox("Map Theme", ["CartoDB dark_matter", "CartoDB positron", "OpenStreetMap"])
    
    df = None
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        # Calculate minimum distance to nearest clinic
        df['Min_Dist'] = df.apply(lambda row: min([haversine(row['Latitude'], row['Longitude'], h_lat, h_lon) 
                                                 for h_lat, h_lon in zip(hosp['Latitude'], hosp['Longitude'])]), axis=1)
        
        st.subheader("📊 Strategic Analysis")
        total_pts = len(df)
        covered_pts = len(df[df['Min_Dist'] <= radius])
        coverage_pct = (covered_pts / total_pts) * 100
        
        # Primary Coverage Metric
        st.metric("Total Coverage Score", f"{coverage_pct:.1f}%")
        
        # Patient Segmentation by Distance (Strategic Insights)
        bins = [0, radius, radius+5, radius+10, 100]
        labels = ['In Radius', '+5 Miles Gap', '+10 Miles Gap', 'Critical Gap']
        df['Bracket'] = pd.cut(df['Min_Dist'], bins=bins, labels=labels)
        bracket_counts = df['Bracket'].value_counts().reindex(labels)
        
        st.write("### 📍 Patient Segmentation")
        for label, count in bracket_counts.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(label)
            with col2:
                st.write(f"**{count}**")
        
        # Prepare Multi-sheet Excel Report
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            report_df = df.copy().sort_values(by='Min_Dist', ascending=False)
            report_df.to_excel(writer, sheet_name='Detailed_Patient_Data', index=False)
            bracket_counts.reset_index().to_excel(writer, sheet_name='Executive_Summary', index=False)
            
        st.download_button(
            label="📊 Download Strategic Report",
            data=output.getvalue(),
            file_name=f"Health_Coverage_Report_{radius}mi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.divider()
        intensity = st.slider("Heat Intensity", 0.1, 1.0, 0.5)
        heat_mode = st.radio("Heatmap Coverage", ["All Patients", "Only Uncovered"])

# 5. Map Construction
m = folium.Map(location=[38.2527, -85.7585], zoom_start=11, tiles=map_style)

# Add Clinic Layers
hosp_layer = folium.FeatureGroup(name="🏥 Clinics").add_to(m)
for _, h in hosp.iterrows():
    folium.Marker([h['Latitude'], h['Longitude']], icon=folium.Icon(color='red', icon='hospital', prefix='fa')).add_to(hosp_layer)
    folium.Circle([h['Latitude'], h['Longitude']], radius=radius * 1609.34, color='#00EAFF', weight=2, fill=True, fill_opacity=0.1).add_to(hosp_layer)

if df is not None:
    # Heatmap Layer
    h_df = df[df['Min_Dist'] > radius] if heat_mode == "Only Uncovered" else df
    HeatMap([[r['Latitude'], r['Longitude'], intensity] for _, r in h_df.iterrows()],
            radius=20, blur=15, gradient={0.2: '#00EAFF', 0.4: '#00FF41', 0.7: '#FFF000', 1: '#FF0000'}, 
            name="🔥 Heatmap").add_to(m)

    # Individual Patient Markers
    patient_layer = folium.FeatureGroup(name="👥 Patients").add_to(m)
    for _, row in df.iterrows():
        p_color = "#00FFFF" if row['Min_Dist'] > radius else "#888888"
        
        # Create professional popup text
        popup_text = f"Distance to Clinic: {row['Min_Dist']:.2f} miles"
        
        folium.CircleMarker(
            [row['Latitude'], row['Longitude']], 
            radius=2.5, 
            color="#444444", 
            weight=0.6, 
            fill=True, 
            fill_color=p_color, 
            fill_opacity=0.8,
            popup=folium.Popup(popup_text, max_width=200) # Added Popup
        ).add_to(patient_layer)

folium.LayerControl(collapsed=False).add_to(m)

# 6. Final Render
map_html = m._repr_html_()
components.html(map_html, height=2000)

# --- FLOATING LEGEND (Bottom-Right) ---
st.markdown(f"""
    <div style="
        position: fixed; 
        bottom: 40px; 
        right: 20px; 
        width: 190px; 
        background-color: rgba(255, 255, 255, 0.95); 
        border: 2px solid #333; 
        z-index: 999999; 
        padding: 12px; 
        border-radius: 10px; 
        box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
        font-family: 'Helvetica Neue', Arial, sans-serif;
    ">
        <b style="font-size: 14px; display: block; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 5px;">📊 Legend</b>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="width: 20px; text-align: center; margin-right: 10px;">🏥</span> Clinic
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="color: #00EAFF; font-size: 20px; margin-right: 10px; line-height: 0;">●</span> Radius ({radius} mi)
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="color: #00FFFF; font-size: 20px; margin-right: 10px; line-height: 0;">●</span> Uncovered
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="color: #888888; font-size: 20px; margin-right: 10px; line-height: 0;">●</span> Covered
        </div>
        <div style="margin-top: 10px; border-top: 1px solid #eee; padding-top: 8px;">
            <div style="background: linear-gradient(to right, #00EAFF, #00FF41, #FFF000, #FF0000); height: 8px; border-radius: 4px;"></div>
            <div style="display: flex; justify-content: space-between; font-size: 10px; margin-top: 3px; color: #444;">
                <span>Low Density</span><span>High</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)