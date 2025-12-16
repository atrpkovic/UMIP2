"""
UMIP 2.0 Mock Data Generator
Generates realistic tire industry data and uploads to Snowflake.

Usage:
    1. Fill in your Snowflake credentials below
    2. Run: python generate_mock_data.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas


def ts_now():
    """Return current timestamp as string for Snowflake compatibility."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def date_today():
    """Return today's date as string for Snowflake compatibility."""
    return datetime.now().strftime('%Y-%m-%d')


# =============================================================================
# SNOWFLAKE CREDENTIALS - FILL THESE IN
# =============================================================================
SF_CONFIG = {
    "account": "umc92597.us-east-1",
    "user": "ALEKSA.TRPKOVIC",
    "password": "jrcysS)$.fMi3K6",
    "warehouse": "GSHOPPING_WH",
    "database": "PRIORITY_TIRE_DATA",
    "schema": "UMIP_MOCK",
}

# =============================================================================
# REALISTIC TIRE INDUSTRY DATA
# =============================================================================

TIRE_SIZES = [
    "205/55R16", "215/55R17", "225/45R17", "225/65R17", "235/55R18",
    "235/65R18", "245/45R18", "255/55R19", "265/70R17", "275/55R20",
    "275/60R20", "285/45R22", "285/70R17", "265/75R16", "235/75R15",
    "245/75R16", "31X10.50R15", "33X12.50R20", "35X12.50R20", "275/65R18",
    "275/70R18", "255/70R18", "265/60R18", "245/60R18", "235/70R16",
    "215/60R16", "195/65R15", "185/65R15", "205/65R15", "225/60R16",
    "235/45R18", "245/40R18", "255/35R19", "275/40R20", "295/45R20",
    "225/55R17", "235/50R18", "245/50R20", "255/50R19", "265/50R20",
]

TIRE_BRANDS = [
    "Michelin", "Goodyear", "Bridgestone", "Continental", "Pirelli",
    "BFGoodrich", "Firestone", "Yokohama", "Toyo", "Falken",
    "Hankook", "Kumho", "Nexen", "Cooper", "General",
    "Dunlop", "Nitto", "Sumitomo", "Federal", "Achilles",
]

TIRE_MODELS = {
    "Michelin": ["Pilot Sport 4S", "Defender LTX", "CrossClimate 2", "Primacy Tour"],
    "Goodyear": ["Eagle F1", "Wrangler AT", "Assurance WeatherReady", "Eagle Sport"],
    "Bridgestone": ["Potenza Sport", "Dueler AT", "Turanza QuietTrack", "Blizzak WS90"],
    "Continental": ["ExtremeContact DWS06", "TerrainContact AT", "PureContact LS"],
    "Pirelli": ["P Zero", "Scorpion Verde", "Cinturato P7", "Winter Sottozero"],
    "BFGoodrich": ["All-Terrain T/A KO2", "Mud-Terrain T/A KM3", "Advantage T/A Sport"],
    "Cooper": ["Discoverer AT3", "CS5 Ultra Touring", "Zeon RS3-G1"],
    "Toyo": ["Open Country AT3", "Proxes Sport", "Celsius II"],
    "Yokohama": ["Geolandar AT", "ADVAN Sport", "BluEarth GT"],
    "Hankook": ["Ventus S1 evo3", "Dynapro AT2", "Kinergy GT"],
}

CAMPAIGN_TYPES = ["Search", "Shopping", "Performance Max"]
CAMPAIGN_NAMES = [
    "Brand - Core", "Brand - Competitor Conquest", "Non-Brand - Tire Sizes",
    "Non-Brand - Tire Brands", "Shopping - All Products", "Shopping - Top Sellers",
    "PMax - New Customer Acquisition", "PMax - Remarketing", "Search - Winter Tires",
    "Search - All-Season Tires", "Search - Truck Tires", "Search - Performance Tires",
]

TREND_CLASSIFICATIONS = ["growing", "stable", "declining", "seasonal"]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

# Seasonal patterns for different tire types
SEASONAL_PATTERNS = {
    "winter": [85, 90, 70, 40, 20, 15, 15, 25, 50, 75, 95, 100],  # Peak Nov-Dec
    "all_season": [60, 65, 80, 90, 85, 70, 65, 70, 85, 95, 75, 55],  # Peak spring/fall
    "summer": [40, 50, 70, 85, 95, 100, 95, 90, 75, 55, 35, 30],  # Peak summer
    "truck": [70, 75, 80, 85, 80, 75, 70, 75, 85, 90, 80, 70],  # Relatively stable
}


def get_seasonal_pattern(keyword):
    """Assign a seasonal pattern based on keyword."""
    kw_lower = keyword.lower()
    if any(w in kw_lower for w in ["winter", "snow", "blizzak", "ice"]):
        return "winter"
    elif any(w in kw_lower for w in ["summer", "sport", "pilot", "potenza"]):
        return "summer"
    elif any(w in kw_lower for w in ["truck", "wrangler", "terrain", "ko2", "discoverer"]):
        return "truck"
    else:
        return "all_season"


def add_noise(values, noise_pct=0.15):
    """Add random noise to a list of values."""
    return [max(0, v + random.uniform(-v * noise_pct, v * noise_pct)) for v in values]


# =============================================================================
# DATA GENERATION FUNCTIONS
# =============================================================================

def generate_keywords():
    """Generate master keyword list."""
    keywords = []
    
    # Tire sizes
    for size in TIRE_SIZES:
        keywords.append({"keyword": size, "category": "tire size"})
        keywords.append({"keyword": f"{size} tires", "category": "tire size"})
    
    # Brands
    for brand in TIRE_BRANDS:
        keywords.append({"keyword": f"{brand} tires", "category": "brand"})
    
    # Brand + Model combinations
    for brand, models in TIRE_MODELS.items():
        for model in models:
            keywords.append({"keyword": f"{brand} {model}", "category": "brand+model"})
    
    # Some long-tail keywords
    long_tail = [
        "best tires for snow", "quiet highway tires", "best truck tires",
        "longest lasting tires", "best tires for rain", "cheap tires near me",
        "tire installation cost", "tire rotation service", "wheel alignment cost",
        "best all season tires 2024", "run flat tires", "low profile tires",
    ]
    for kw in long_tail:
        keywords.append({"keyword": kw, "category": "long-tail"})
    
    df = pd.DataFrame(keywords)
    df["IS_ACTIVE"] = True
    df["ADDED_AT"] = (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d %H:%M:%S')
    df.columns = ["KEYWORD", "CATEGORY", "IS_ACTIVE", "ADDED_AT"]
    
    return df


def generate_ahrefs_keywords(keywords_df):
    """Generate Ahrefs ranking data."""
    records = []
    
    for _, row in keywords_df.iterrows():
        keyword = row["KEYWORD"]
        category = row["CATEGORY"]
        
        # Volume based on category
        if category == "tire size":
            volume = random.randint(1000, 50000)
        elif category == "brand":
            volume = random.randint(5000, 100000)
        elif category == "brand+model":
            volume = random.randint(500, 20000)
        else:
            volume = random.randint(200, 10000)
        
        # Generate page path
        slug = keyword.lower().replace(" ", "-").replace("/", "-")
        page_path = f"/tires/{slug}/"
        
        records.append({
            "KEYWORD": keyword,
            "CURRENT_URL": f"https://www.prioritytire.com{page_path}",
            "PAGE_PATH": page_path,
            "VOLUME": volume,
            "CURRENT_POSITION": random.randint(1, 100),
            "CURRENT_TRAFFIC": int(volume * random.uniform(0.01, 0.3)),
            "KEYWORD_DIFFICULTY": random.randint(10, 85),
            "CPC": round(random.uniform(0.5, 4.5), 2),
            "LOADED_AT": ts_now(),
        })
    
    return pd.DataFrame(records)


def generate_ga4_metrics(ahrefs_df):
    """Generate GA4 page metrics."""
    # Get unique page paths
    page_paths = ahrefs_df["PAGE_PATH"].unique()
    
    records = []
    for path in page_paths:
        # Get traffic estimate from Ahrefs data
        ahrefs_row = ahrefs_df[ahrefs_df["PAGE_PATH"] == path].iloc[0]
        base_users = ahrefs_row["CURRENT_TRAFFIC"]
        
        records.append({
            "PAGE_PATH": path,
            "TOTAL_USERS": int(base_users * random.uniform(0.8, 1.5)),
            "USER_KEY_EVENT_RATE": round(random.uniform(0.01, 0.08), 4),
            "TOTAL_REVENUE": round(base_users * random.uniform(0.5, 5.0), 2),
            "LOADED_AT": ts_now(),
        })
    
    return pd.DataFrame(records)


def generate_trends_timeseries(keywords_df):
    """Generate Google Trends time series data."""
    records = []
    
    # Generate 2 years of weekly data
    start_date = datetime.now() - timedelta(weeks=104)
    dates = [start_date + timedelta(weeks=w) for w in range(104)]
    
    for _, row in keywords_df.iterrows():
        keyword = row["KEYWORD"]
        pattern_type = get_seasonal_pattern(keyword)
        base_pattern = SEASONAL_PATTERNS[pattern_type]
        
        for date in dates:
            month_idx = date.month - 1
            week_num = date.isocalendar()[1]
            
            # Get base value from seasonal pattern and add noise
            base_value = base_pattern[month_idx]
            interest = int(max(0, min(100, base_value + random.uniform(-15, 15))))
            
            records.append({
                "KEYWORD": keyword,
                "TREND_DATE": date.strftime('%Y-%m-%d'),
                "INTEREST": interest,
                "WEEK_NUM": week_num,
                "FETCHED_AT": ts_now(),
            })
    
    return pd.DataFrame(records)


def generate_seasonality_monthly(keywords_df):
    """Generate monthly seasonality data."""
    records = []
    
    for _, row in keywords_df.iterrows():
        keyword = row["KEYWORD"]
        pattern_type = get_seasonal_pattern(keyword)
        base_pattern = SEASONAL_PATTERNS[pattern_type]
        noisy_pattern = add_noise(base_pattern, 0.1)
        
        record = {
            "KEYWORD": keyword,
            "ANALYSIS_DATE": date_today(),
            "PEAK_CONSISTENCY": round(random.uniform(0.6, 0.95), 3),
            "CREATED_AT": ts_now(),
        }
        
        # Add monthly averages
        for i, month in enumerate(MONTHS):
            record[f"{month}_AVG"] = round(noisy_pattern[i], 2)
        
        # Determine peak month
        peak_idx = noisy_pattern.index(max(noisy_pattern))
        record["PEAK_MONTH"] = MONTHS[peak_idx]
        
        records.append(record)
    
    return pd.DataFrame(records)


def generate_seasonality_quarterly(keywords_df):
    """Generate quarterly seasonality data."""
    records = []
    
    for _, row in keywords_df.iterrows():
        keyword = row["KEYWORD"]
        pattern_type = get_seasonal_pattern(keyword)
        base_pattern = SEASONAL_PATTERNS[pattern_type]
        
        # Calculate quarterly averages
        q1_avg = sum(base_pattern[0:3]) / 3
        q2_avg = sum(base_pattern[3:6]) / 3
        q3_avg = sum(base_pattern[6:9]) / 3
        q4_avg = sum(base_pattern[9:12]) / 3
        
        q_avgs = [q1_avg, q2_avg, q3_avg, q4_avg]
        q_avgs = add_noise(q_avgs, 0.1)
        
        peak_idx = q_avgs.index(max(q_avgs))
        
        records.append({
            "KEYWORD": keyword,
            "ANALYSIS_DATE": date_today(),
            "Q1_AVG": round(q_avgs[0], 2),
            "Q2_AVG": round(q_avgs[1], 2),
            "Q3_AVG": round(q_avgs[2], 2),
            "Q4_AVG": round(q_avgs[3], 2),
            "PEAK_QUARTER": QUARTERS[peak_idx],
            "CREATED_AT": ts_now(),
        })
    
    return pd.DataFrame(records)


def generate_trend_analysis(keywords_df):
    """Generate trend analysis data."""
    records = []
    
    for _, row in keywords_df.iterrows():
        keyword = row["KEYWORD"]
        
        # Random trend classification weighted toward stable
        classification = random.choices(
            TREND_CLASSIFICATIONS,
            weights=[0.2, 0.5, 0.15, 0.15]
        )[0]
        
        if classification == "growing":
            slope = random.uniform(0.1, 0.5)
            annual_growth = random.uniform(5, 25)
        elif classification == "declining":
            slope = random.uniform(-0.5, -0.1)
            annual_growth = random.uniform(-25, -5)
        elif classification == "seasonal":
            slope = random.uniform(-0.05, 0.05)
            annual_growth = random.uniform(-3, 3)
        else:  # stable
            slope = random.uniform(-0.1, 0.1)
            annual_growth = random.uniform(-5, 5)
        
        records.append({
            "KEYWORD": keyword,
            "ANALYSIS_DATE": date_today(),
            "SLOPE": round(slope, 4),
            "P_VALUE": round(random.uniform(0.001, 0.1), 4),
            "ANNUAL_GROWTH": round(annual_growth, 2),
            "TREND_CLASSIFICATION": classification,
            "DATA_POINTS": random.randint(80, 104),
            "CREATED_AT": ts_now(),
        })
    
    return pd.DataFrame(records)


def generate_keyword_analysis(keywords_df, ahrefs_df, ga4_df, seasonality_monthly_df, trend_df):
    """Generate comprehensive keyword analysis by joining data."""
    records = []
    
    for _, kw_row in keywords_df.iterrows():
        keyword = kw_row["KEYWORD"]
        
        # Get Ahrefs data
        ahrefs_match = ahrefs_df[ahrefs_df["KEYWORD"] == keyword]
        if ahrefs_match.empty:
            continue
        ahrefs_row = ahrefs_match.iloc[0]
        
        # Get GA4 data
        page_path = ahrefs_row["PAGE_PATH"]
        ga4_match = ga4_df[ga4_df["PAGE_PATH"] == page_path]
        ga4_row = ga4_match.iloc[0] if not ga4_match.empty else None
        
        # Get seasonality data
        season_match = seasonality_monthly_df[seasonality_monthly_df["KEYWORD"] == keyword]
        season_row = season_match.iloc[0] if not season_match.empty else None
        
        # Get trend data
        trend_match = trend_df[trend_df["KEYWORD"] == keyword]
        trend_row = trend_match.iloc[0] if not trend_match.empty else None
        
        record = {
            "KEYWORD": keyword,
            "PAGE_PATH": page_path,
            "SEARCH_VOLUME": ahrefs_row["VOLUME"],
            "CURRENT_POSITION": ahrefs_row["CURRENT_POSITION"],
            "CURRENT_TRAFFIC": ahrefs_row["CURRENT_TRAFFIC"],
            "KEYWORD_DIFFICULTY": ahrefs_row["KEYWORD_DIFFICULTY"],
            "TOTAL_USERS": ga4_row["TOTAL_USERS"] if ga4_row is not None else None,
            "USER_KEY_EVENT_RATE": ga4_row["USER_KEY_EVENT_RATE"] if ga4_row is not None else None,
            "TOTAL_REVENUE": ga4_row["TOTAL_REVENUE"] if ga4_row is not None else None,
        }
        
        if trend_row is not None:
            record["SLOPE"] = trend_row["SLOPE"]
            record["P_VALUE"] = trend_row["P_VALUE"]
            record["ANNUAL_GROWTH"] = trend_row["ANNUAL_GROWTH"]
            record["TREND_CLASSIFICATION"] = trend_row["TREND_CLASSIFICATION"]
        
        if season_row is not None:
            for month in MONTHS:
                record[f"{month}_AVG"] = season_row[f"{month}_AVG"]
            record["PEAK_MONTH"] = season_row["PEAK_MONTH"]
            record["PEAK_CONSISTENCY"] = season_row["PEAK_CONSISTENCY"]
            
            # Calculate quarterly averages
            record["Q1_AVG"] = round((season_row["JAN_AVG"] + season_row["FEB_AVG"] + season_row["MAR_AVG"]) / 3, 2)
            record["Q2_AVG"] = round((season_row["APR_AVG"] + season_row["MAY_AVG"] + season_row["JUN_AVG"]) / 3, 2)
            record["Q3_AVG"] = round((season_row["JUL_AVG"] + season_row["AUG_AVG"] + season_row["SEP_AVG"]) / 3, 2)
            record["Q4_AVG"] = round((season_row["OCT_AVG"] + season_row["NOV_AVG"] + season_row["DEC_AVG"]) / 3, 2)
            
            q_avgs = [record["Q1_AVG"], record["Q2_AVG"], record["Q3_AVG"], record["Q4_AVG"]]
            record["PEAK_QUARTER"] = QUARTERS[q_avgs.index(max(q_avgs))]
        
        records.append(record)
    
    return pd.DataFrame(records)


def generate_google_ads(days=90):
    """Generate Google Ads campaign data."""
    records = []
    
    start_date = datetime.now() - timedelta(days=days)
    
    for day_offset in range(days):
        date = start_date + timedelta(days=day_offset)
        
        for campaign_name in CAMPAIGN_NAMES:
            # Determine campaign type from name
            if "Shopping" in campaign_name:
                campaign_type = "Shopping"
            elif "PMax" in campaign_name:
                campaign_type = "Performance Max"
            else:
                campaign_type = "Search"
            
            # Base metrics vary by campaign type
            if campaign_type == "Shopping":
                base_impressions = random.randint(5000, 50000)
                ctr = random.uniform(0.01, 0.03)
                cpc = random.uniform(0.3, 1.2)
                conv_rate = random.uniform(0.02, 0.05)
            elif campaign_type == "Performance Max":
                base_impressions = random.randint(10000, 100000)
                ctr = random.uniform(0.005, 0.02)
                cpc = random.uniform(0.5, 2.0)
                conv_rate = random.uniform(0.01, 0.04)
            else:  # Search
                base_impressions = random.randint(1000, 20000)
                ctr = random.uniform(0.02, 0.08)
                cpc = random.uniform(0.8, 3.5)
                conv_rate = random.uniform(0.03, 0.08)
            
            clicks = int(base_impressions * ctr)
            cost = round(clicks * cpc, 2)
            conversions = round(clicks * conv_rate, 2)
            aov = random.uniform(150, 400)  # Average order value for tires
            conversion_value = round(conversions * aov, 2)
            
            records.append({
                "DATE": date.strftime('%Y-%m-%d'),
                "CAMPAIGN_NAME": campaign_name,
                "CAMPAIGN_TYPE": campaign_type,
                "IMPRESSIONS": base_impressions,
                "CLICKS": clicks,
                "COST": cost,
                "CONVERSIONS": conversions,
                "CONVERSION_VALUE": conversion_value,
            })
    
    return pd.DataFrame(records)


def generate_netsuite_inventory():
    """Generate NetSuite inventory data."""
    records = []
    
    for brand in TIRE_BRANDS:
        models = TIRE_MODELS.get(brand, ["Standard", "Premium"])
        
        for model in models:
            for size in random.sample(TIRE_SIZES, k=min(10, len(TIRE_SIZES))):
                sku = f"{brand[:3].upper()}-{model[:3].upper()}-{size.replace('/', '-')}"
                
                # Price based on brand tier
                if brand in ["Michelin", "Pirelli", "Continental"]:
                    unit_cost = random.uniform(80, 200)
                elif brand in ["Goodyear", "Bridgestone", "BFGoodrich"]:
                    unit_cost = random.uniform(60, 150)
                else:
                    unit_cost = random.uniform(40, 100)
                
                list_price = round(unit_cost * random.uniform(1.3, 1.6), 2)
                qty_on_hand = random.randint(0, 200)
                qty_reserved = random.randint(0, min(20, qty_on_hand))
                
                records.append({
                    "SKU": sku,
                    "PRODUCT_NAME": f"{brand} {model} {size}",
                    "BRAND": brand,
                    "SIZE": size,
                    "QUANTITY_ON_HAND": qty_on_hand,
                    "QUANTITY_AVAILABLE": qty_on_hand - qty_reserved,
                    "UNIT_COST": round(unit_cost, 2),
                    "LIST_PRICE": list_price,
                    "LAST_UPDATED": ts_now(),
                })
    
    return pd.DataFrame(records)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def upload_to_snowflake(df, table_name, conn):
    """Upload a DataFrame to Snowflake, replacing existing data."""
    print(f"  Uploading {len(df)} rows to {table_name}...")
    
    # Drop existing table data
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM {table_name}")
        print(f"    Cleared existing data")
    except:
        print(f"    Table may not exist, will create")
    finally:
        cursor.close()
    
    # Upload new data
    success, num_chunks, num_rows, _ = write_pandas(
        conn, df, table_name, auto_create_table=True, overwrite=False
    )
    
    if success:
        print(f"    Success: {num_rows} rows uploaded")
    else:
        print(f"    Failed to upload")
    
    return success


def main():
    print("=" * 60)
    print("UMIP 2.0 Mock Data Generator")
    print("=" * 60)
    
    # Generate all data
    print("\n[1/10] Generating keywords master list...")
    keywords_df = generate_keywords()
    print(f"  Generated {len(keywords_df)} keywords")
    
    print("\n[2/10] Generating Ahrefs keyword data...")
    ahrefs_df = generate_ahrefs_keywords(keywords_df)
    print(f"  Generated {len(ahrefs_df)} Ahrefs records")
    
    print("\n[3/10] Generating GA4 page metrics...")
    ga4_df = generate_ga4_metrics(ahrefs_df)
    print(f"  Generated {len(ga4_df)} GA4 records")
    
    print("\n[4/10] Generating Google Trends timeseries...")
    trends_df = generate_trends_timeseries(keywords_df)
    print(f"  Generated {len(trends_df)} trend data points")
    
    print("\n[5/10] Generating monthly seasonality...")
    seasonality_monthly_df = generate_seasonality_monthly(keywords_df)
    print(f"  Generated {len(seasonality_monthly_df)} monthly records")
    
    print("\n[6/10] Generating quarterly seasonality...")
    seasonality_quarterly_df = generate_seasonality_quarterly(keywords_df)
    print(f"  Generated {len(seasonality_quarterly_df)} quarterly records")
    
    print("\n[7/10] Generating trend analysis...")
    trend_df = generate_trend_analysis(keywords_df)
    print(f"  Generated {len(trend_df)} trend analysis records")
    
    print("\n[8/10] Generating keyword analysis (combined)...")
    keyword_analysis_df = generate_keyword_analysis(
        keywords_df, ahrefs_df, ga4_df, seasonality_monthly_df, trend_df
    )
    print(f"  Generated {len(keyword_analysis_df)} keyword analysis records")
    
    print("\n[9/10] Generating Google Ads campaign data...")
    google_ads_df = generate_google_ads(days=90)
    print(f"  Generated {len(google_ads_df)} Google Ads records")
    
    print("\n[10/10] Generating NetSuite inventory...")
    netsuite_df = generate_netsuite_inventory()
    print(f"  Generated {len(netsuite_df)} inventory records")
    
    # Connect to Snowflake
    print("\n" + "=" * 60)
    print("Connecting to Snowflake...")
    print("=" * 60)
    
    conn = snowflake.connector.connect(**SF_CONFIG)
    print("Connected!")
    
    # Upload all tables
    print("\nUploading to Snowflake...")
    
    upload_to_snowflake(keywords_df, "KEYWORDS_MASTER", conn)
    upload_to_snowflake(ahrefs_df, "AHREFS_KEYWORDS", conn)
    upload_to_snowflake(ga4_df, "GA4_PAGE_METRICS", conn)
    upload_to_snowflake(trends_df, "GOOGLE_TRENDS_TIMESERIES", conn)
    upload_to_snowflake(seasonality_monthly_df, "SEASONALITY_MONTHLY", conn)
    upload_to_snowflake(seasonality_quarterly_df, "SEASONALITY_QUARTERLY", conn)
    upload_to_snowflake(trend_df, "TREND_ANALYSIS", conn)
    upload_to_snowflake(keyword_analysis_df, "KEYWORD_ANALYSIS", conn)
    upload_to_snowflake(google_ads_df, "GOOGLE_ADS_CAMPAIGNS", conn)
    upload_to_snowflake(netsuite_df, "NETSUITE_INVENTORY", conn)
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("DONE! Mock data uploaded successfully.")
    print("=" * 60)
    print("\nYou can now test UMIP 2.0 with questions like:")
    print('  - "Which keywords should I push in Q1?"')
    print('  - "What are our top performing campaigns by ROAS?"')
    print('  - "Show me keywords with high volume but low ranking"')
    print('  - "What inventory do we have for Michelin tires?"')


if __name__ == "__main__":
    main()