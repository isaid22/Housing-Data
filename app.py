import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# Import the existing functions from your script
from attom_test import lookup_property_by_address, get_neighborhood_sales

# Set up the Streamlit page layout
st.set_page_config(page_title="Housing Sales Map", layout="wide")
st.title("Neighborhood Sales Dashboard 🏡")
st.markdown("Easily pull neighborhood comps to protest property taxes.")

# ----------------- SIDEBAR KNOBS AND TWEAKS -----------------
st.sidebar.header("Search Parameters")
address1 = st.sidebar.text_input("Street Address", "5203 Lakehill Blvd")
address2 = st.sidebar.text_input("City, State or Zip", "Frisco, TX 75034")

radius = st.sidebar.slider("Radius (miles)", min_value=0.1, max_value=5.0, value=0.5, step=0.1)

# Date Pickers
today = datetime.now()
default_start = today - timedelta(days=365)
start_date = st.sidebar.date_input("Start Date", default_start)
end_date = st.sidebar.date_input("End Date", today)

exclude_unknown = st.sidebar.checkbox("Exclude Unknown Prices", value=False)

st.sidebar.markdown("---")
st.sidebar.header("Map Settings")
map_style = st.sidebar.selectbox(
    "Map Provider",
    ["Google Maps", "Google Satellite", "CartoDB (Clean/Light)", "Esri Satellite", "OpenStreetMap"]
)

# Create cached wrapper functions to prevent redundant API calls
@st.cache_data(show_spinner=False)
def fetch_subject_property(addr1, addr2):
    return lookup_property_by_address(addr1, addr2)

@st.cache_data(show_spinner=False)
def fetch_sales(lat, lon, r, start_d, end_d):
    return get_neighborhood_sales(lat, lon, radius_miles=r, start_date=start_d, end_date=end_d)

# ----------------- MAIN APP LOGIC -----------------
# We use session state to remember that we clicked the button
if "search_clicked" not in st.session_state:
    st.session_state.search_clicked = False

if st.sidebar.button("Search Sales"):
    st.session_state.search_clicked = True

if st.session_state.search_clicked:
    with st.spinner("Fetching data from ATTOM API..."):
        try:
            # 1. Get Subject Property (Cached)
            my_property = fetch_subject_property(address1, address2)
            loc = my_property["property"][0]["location"]
            sub_lat = float(loc["latitude"])
            sub_lon = float(loc["longitude"])
            
            # 2. Get Comparable Sales (Cached)
            sales_data = fetch_sales(
                sub_lat, sub_lon, 
                radius, 
                start_date.strftime("%Y/%m/%d"), 
                end_date.strftime("%Y/%m/%d")
            )
            
            properties = sales_data.get("property", [])
            
            # 3. Clean and Process Data for the UI
            map_data = []
            for p in properties:
                sale_amt = p.get("sale", {}).get("amount", {}).get("saleamt", "Unknown")
                
                # Exclude logic
                if exclude_unknown and sale_amt == "Unknown":
                    continue
                    
                p_loc = p.get("location", {})
                lat = p_loc.get("latitude")
                lon = p_loc.get("longitude")
                
                # Skip properties without coordinates
                if not lat or not lon:
                    continue
                    
                addr = p.get("address", {}).get("line1", "Unknown")
                date = p.get("sale", {}).get("amount", {}).get("salerecdate", "Unknown")
                
                # Get square footage and rooms
                building = p.get("building", {})
                sqft = building.get("size", {}).get("universalsize", "Unknown")
                beds = building.get("rooms", {}).get("beds", "Unknown")
                baths = building.get("rooms", {}).get("bathstotal", "Unknown")
                
                # Format price safely for display
                fmt_price = f"${sale_amt:,}" if isinstance(sale_amt, (int, float)) else str(sale_amt)
                fmt_sqft = float(sqft) if isinstance(sqft, (int, float)) else None
                fmt_beds = str(beds) if beds != "Unknown" else "Unknown"
                fmt_baths = str(baths) if baths != "Unknown" else "Unknown"
                
                map_data.append({
                    "Address": addr,
                    "Price": fmt_price,
                    "SqFt": fmt_sqft,
                    "Beds": fmt_beds,
                    "Baths": fmt_baths,
                    "Date": date,
                    "Lat": float(lat),
                    "Lon": float(lon)
                })
            
            # ----------------- RENDER RESULTS -----------------
            st.success(f"Found {len(map_data)} sales within {radius} miles.")
            
            if not map_data:
                st.warning("No sales found! Try expanding your radius, changing your dates, or unchecking 'Exclude Unknown Prices'.")
            else:
                # Create DataFrame and add an ID for easy cross-referencing
                df = pd.DataFrame(map_data)
                df.insert(0, 'ID', range(1, 1 + len(df)))
                
                # Divide layout: Map taking 60%, Table taking 40%
                col1, col2 = st.columns([6, 4])
                
                # We render the table FIRST in code so we can capture exactly what the user selected,
                # then apply those selections to color the map markers dynamically!
                with col2:
                    st.subheader("Sales Data")
                    st.markdown("👇 **Select rows** here to highlight them on the map!")
                    
                    # Display dataframe with selection enabled
                    event = st.dataframe(
                        df.drop(columns=["Lat", "Lon"]),
                        use_container_width=True,
                        on_select="rerun",
                        selection_mode="multi-row",
                        hide_index=True
                    )
                    selected_rows = event.selection.rows

                with col1:
                    # Configure selected map tiles
                    if map_style == "OpenStreetMap":
                        m = folium.Map(location=[sub_lat, sub_lon], zoom_start=15)
                    elif map_style == "CartoDB (Clean/Light)":
                        m = folium.Map(location=[sub_lat, sub_lon], zoom_start=15, tiles="CartoDB positron")
                    elif map_style == "Google Maps":
                        m = folium.Map(location=[sub_lat, sub_lon], zoom_start=15, tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google")
                    elif map_style == "Google Satellite":
                        m = folium.Map(location=[sub_lat, sub_lon], zoom_start=15, tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google")
                    elif map_style == "Esri Satellite":
                        m = folium.Map(location=[sub_lat, sub_lon], zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
                    
                    # Add Target Property Marker (Red)
                    folium.Marker(
                        [sub_lat, sub_lon],
                        tooltip="<b>YOUR HOUSE</b><br>" + address1,
                        icon=folium.Icon(color="red", icon="home")
                    ).add_to(m)
                    
                    # Add Sales Markers
                    for idx, row in df.iterrows():
                        # If a user selected rows, highlight them in orange with a star!
                        is_selected = (len(selected_rows) > 0 and idx in selected_rows)
                        marker_color = "orange" if is_selected else "blue"
                        icon_name = "star" if is_selected else "usd"
                        
                        tooltip_html = f"<b>#{row['ID']} - {row['Address']}</b><br>Price: {row['Price']}<br>Size: {row['SqFt']}<br>Beds: {row['Beds']} | Baths: {row['Baths']}<br>Date: {row['Date']}"
                        folium.Marker(
                            [row["Lat"], row["Lon"]],
                            tooltip=tooltip_html,
                            icon=folium.Icon(color=marker_color, icon=icon_name)
                        ).add_to(m)
                        
                    # Display map in Streamlit (captures map clicks!)
                    map_res = st_folium(m, use_container_width=True, height=600)
                    
                # If the user clicks a marker on the map, show its details!
                if map_res and map_res.get("last_object_clicked"):
                    clicked_lat = map_res["last_object_clicked"]["lat"]
                    clicked_lon = map_res["last_object_clicked"]["lng"]
                    
                    # Find the property matching those coordinates
                    tol = 0.0001
                    match = df[(abs(df["Lat"] - clicked_lat) < tol) & (abs(df["Lon"] - clicked_lon) < tol)]
                    if not match.empty:
                        prop_data = match.iloc[0]
                        st.sidebar.success(
                            f"📍 **Map Clicked:**\n\n**#{prop_data['ID']} - {prop_data['Address']}**\n\n"
                            f"💰 Sold: {prop_data['Price']} on {prop_data['Date']}\n\n"
                            f"📏 Size: {prop_data['SqFt']}\n\n"
                            f"🛏️ Beds: {prop_data['Beds']} | 🛁 Baths: {prop_data['Baths']}"
                        )
                    
        except Exception as e:
            st.error(f"Error occurred: {e}")
