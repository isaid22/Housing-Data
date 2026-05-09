import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ATTOM_API_KEY")

if not API_KEY:
    raise RuntimeError("Missing ATTOM_API_KEY in .env file")

BASE_URL = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"

headers = {
    "apikey": API_KEY,
    "accept": "application/json",
}

from datetime import datetime, timedelta

def get_neighborhood_sales(latitude: float, longitude: float, radius_miles: float = 0.5, start_date: str = None, end_date: str = None):
    """
    Search for properties sold within a specific radius in a given date range.
    """
    url = f"{BASE_URL}/sale/snapshot"
    
    if not end_date:
        end_date = datetime.now().strftime("%Y/%m/%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y/%m/%d")
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius_miles,
        "startSaleSearchDate": start_date,
        "endSaleSearchDate": end_date,
        
        # Optional: You can filter out specific property types, e.g. only SFR (Single Family Residential)
        # "propertytype": "SFR",
        "pageSize": 100 # Adjust if you have a dense neighborhood
    }

    response = requests.get(url, headers=headers, params=params, timeout=30)
    if not response.ok:
        print(f"Error {response.status_code}: {response.text}")
    response.raise_for_status()
    return response.json()

def lookup_property_by_address(address1: str, address2: str):
    """
    address1 example: '4529 Winona Ct'
    address2 example: 'Denver, CO'
    """
    url = f"{BASE_URL}/property/basicprofile"

    params = {
        "address1": address1,
        "address2": address2,
    }

    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def get_sales_history(attom_id: str):
    """
    Some ATTOM endpoints use ATTOM property id / identifier.
    Exact field name may vary by endpoint/package.
    """
    url = f"{BASE_URL}/saleshistory/snapshot"

    params = {
        "id": attom_id,
    }

    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch neighborhood sales data from ATTOM API.")
    parser.add_argument("--address1", default="4529 Winona Ct", help="Street address")
    parser.add_argument("--address2", default="Denver, CO", help="City, State, and/or Zip")
    parser.add_argument("--radius", type=float, default=0.5, help="Radius in miles (default: 0.5)")
    parser.add_argument("--start-date", type=str, help="Start date in YYYY/MM/DD format (default: 1 year ago)")
    parser.add_argument("--end-date", type=str, help="End date in YYYY/MM/DD format (default: today)")
    parser.add_argument("--exclude-unknown", action="store_true", help="Exclude sales with unknown prices")
    
    args = parser.parse_args()
    
    # Calculate dates
    now = datetime.now()
    
    # Use provided dates or default to 1 year lookback
    start_date = args.start_date if args.start_date else (now - timedelta(days=365)).strftime("%Y/%m/%d")
    end_date = args.end_date if args.end_date else now.strftime("%Y/%m/%d")

    print(f"Looking up property: {args.address1}, {args.address2}")
    my_property = lookup_property_by_address(args.address1, args.address2)
    
    location = my_property["property"][0]["location"]
    lat = location["latitude"]
    lon = location["longitude"]
    
    # Pull sales nearby
    nearby_sales = get_neighborhood_sales(lat, lon, radius_miles=args.radius, start_date=start_date, end_date=end_date)
    properties = nearby_sales.get("property", [])
    
    if args.exclude_unknown:
        properties = [
            p for p in properties 
            if p.get("sale", {}).get("amount", {}).get("saleamt", "Unknown") != "Unknown"
        ]
    
    print(f"Found {len(properties)} matching sales within {args.radius} miles from {start_date} to {end_date}.")
    
    for prop in properties:
        address = prop.get("address", {}).get("line1", "Unknown Address")
        sale_amount = prop.get("sale", {}).get("amount", {}).get("saleamt", "Unknown")
        sale_date = prop.get("sale", {}).get("amount", {}).get("salerecdate", "Unknown")
        
        loc = prop.get("location", {})
        prop_lat = loc.get("latitude", "Unknown")
        prop_lon = loc.get("longitude", "Unknown")
        
        print(f"{address} sold for ${sale_amount} on {sale_date} | Lat: {prop_lat}, Lon: {prop_lon}")