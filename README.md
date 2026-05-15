# Housing Data Dashboard

## Introduction
The Housing Data Dashboard is an interactive web application built with Streamlit and Folium that allows users to visualize and analyze recent property sales data. By hooking into the ATTOM API, the application pulls property selling data over the past year for a specific geographical radius and displays the properties on a dynamic, interactive map alongside a detailed data table.

## Features
* **ATTOM API Integration:** Fetches real-time geographical property and sales records.
* **Interactive Mapping:** Plots property sales on a map using Folium.
* **Cross-Referenced UI:** Selecting a property row in the data table synchronizes with the map, highlighting the selected property's pin (turns orange).
* **Map Customization:** Toggle between multiple map providers, such as CartoDB, Google Satellite, and Esri.
* **Filter Options:** Parameter toggling for customizing the date range and radius of the searched sales.

## Getting Started

### Prerequisites
Make sure you have Python installed, along with the required libraries. Typically you'd install:
```bash
pip install streamlit pandas folium streamlit-folium requests python-dotenv
```

### Configuration
You will need an ATTOM API key to fetch the housing data. 
1. Create a `.env` file in the root directory of the project (`Housing-Data/.env`).
2. Add your ATTOM API key to the file like this:
```env
ATTOM_API_KEY=your_api_key_here
```
*(Note: The `.env` file is ignored by Git to keep your API key secure.)*

## How to Run the Project
Navigate to the project directory in your terminal and start the Streamlit server:
```bash
streamlit run app.py
```
This will open a new tab in your default web browser displaying the interactive UI.

## How to Play with the UI
1. **Explore the Map:** Use your mouse to drag the map around and scroll to zoom in and out.
2. **Change Map Style:** Use the styling dropdown in the side panel or main view to switch between map providers (e.g., Satellite view vs. standard maps) to better understand the neighborhood layout.
3. **Data Table Syncing:** Scroll through the property table. When you click or select a specific row, the corresponding location pin on the map will turn orange, allowing you to instantly locate exactly where that house is.
