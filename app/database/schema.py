"""
Schema definitions for the SQL agent.

This file is CRITICAL for the agent's effectiveness. The more detailed
and accurate these descriptions are, the better the generated SQL will be.

Update this file whenever you add new tables to your warehouse.
"""

from dataclasses import dataclass


@dataclass
class Column:
    """Column definition with semantic information."""
    name: str
    data_type: str
    description: str
    example_values: str = ""


@dataclass
class Table:
    """Table definition for the agent's knowledge."""
    name: str  # Fully qualified: database.schema.table
    description: str
    columns: list[Column]
    notes: str = ""  # Additional context for the agent


# =============================================================================
# PRIORITY TIRE DATA WAREHOUSE TABLES
# =============================================================================

TABLES = [
    # -------------------------------------------------------------------------
    # Google Shopping Scraper Data (Competitor Pricing)
    # -------------------------------------------------------------------------
    Table(
        name="PRIORITY_TIRE_DATA.UMIP_MOCK.GOOGLE_SHOPPING_SCRAPER",
        description="Competitor pricing data scraped from Google Shopping. Contains ~422K rows of tire listings from various sellers.",
        columns=[
            Column("SCRAPED_AT", "NUMBER", "Unix timestamp when data was scraped"),
            Column("SCRAPE_TYPE", "TEXT", "Type of scrape performed", "sizes, brands, brand model size"),
            Column("KEYWORD", "TEXT", "Search keyword used (typically tire size)", "275/60R20, 225/65R17"),
            Column("LOCATION", "TEXT", "Geographic location for search", "Florida, United States"),
            Column("POSITION", "NUMBER", "Position in Google Shopping results (1 = top)"),
            Column("PRODUCT_TITLE", "TEXT", "Full product listing title"),
            Column("PRICE", "FLOAT", "Current listed price in USD"),
            Column("OLD_PRICE", "FLOAT", "Previous/strikethrough price if on sale (often NULL)"),
            Column("RATING", "FLOAT", "Product rating (0-5 scale, can be NULL)"),
            Column("REVIEWS", "FLOAT", "Number of reviews (can be NULL)"),
            Column("SELLER", "TEXT", "Merchant/retailer name", "Walmart, Giga Tires, Tire Rack, Priority Tire, Tires Easy"),
            Column("URL", "TEXT", "Product page URL (often NULL)"),
            Column("BRAND", "TEXT", "Tire brand extracted from listing", "Michelin, Goodyear, Bridgestone"),
            Column("MATCHED_SELLER", "TEXT", "Normalized seller name for matching", "walmart, giga tires, tire rack"),
        ],
        notes="Primary source for competitive pricing analysis. Join on KEYWORD (tire size) to compare prices across sellers. Priority Tire appears as both 'Priority Tire' and 'Walmart - Priority Tire'."
    ),

    # -------------------------------------------------------------------------
    # Ahrefs SEO Data
    # -------------------------------------------------------------------------
    Table(
        name="PRIORITY_TIRE_DATA.UMIP_MOCK.AHREFS_KEYWORDS",
        description="Organic keyword rankings from Ahrefs for Priority Tire website.",
        columns=[
            Column("KEYWORD", "TEXT", "Search keyword/phrase"),
            Column("CURRENT_URL", "TEXT", "Full URL currently ranking for this keyword"),
            Column("PAGE_PATH", "TEXT", "URL path portion (without domain)"),
            Column("VOLUME", "NUMBER", "Monthly search volume"),
            Column("CURRENT_POSITION", "NUMBER", "Current SERP position (1-100)"),
            Column("CURRENT_TRAFFIC", "NUMBER", "Estimated monthly organic traffic"),
            Column("KEYWORD_DIFFICULTY", "NUMBER", "Ahrefs KD score (0-100, higher = harder to rank)"),
            Column("CPC", "FLOAT", "Cost per click for paid ads on this keyword"),
            Column("LOADED_AT", "TIMESTAMP_NTZ", "When this data was imported"),
        ],
        notes="Lower CURRENT_POSITION = better ranking. Use for SEO opportunity analysis."
    ),

    # -------------------------------------------------------------------------
    # GA4 Analytics
    # -------------------------------------------------------------------------
    Table(
        name="PRIORITY_TIRE_DATA.UMIP_MOCK.GA4_PAGE_METRICS",
        description="Google Analytics 4 page-level performance metrics.",
        columns=[
            Column("PAGE_PATH", "TEXT", "URL path of the page"),
            Column("TOTAL_USERS", "NUMBER", "Total unique users who viewed this page"),
            Column("USER_KEY_EVENT_RATE", "FLOAT", "Conversion rate (key events / users)"),
            Column("TOTAL_REVENUE", "FLOAT", "Total revenue attributed to this page"),
            Column("LOADED_AT", "TIMESTAMP_NTZ", "When this data was imported"),
        ],
        notes="Join with AHREFS_KEYWORDS on PAGE_PATH to connect SEO rankings with conversion data."
    ),

    # -------------------------------------------------------------------------
    # Google Trends
    # -------------------------------------------------------------------------
    Table(
        name="PRIORITY_TIRE_DATA.UMIP_MOCK.GOOGLE_TRENDS_TIMESERIES",
        description="Historical Google Trends interest data for tire-related keywords.",
        columns=[
            Column("KEYWORD", "TEXT", "Search term tracked"),
            Column("TREND_DATE", "DATE", "Date of the data point"),
            Column("INTEREST", "NUMBER", "Relative interest score (0-100)"),
            Column("WEEK_NUM", "NUMBER", "Week number of the year (1-52)"),
            Column("FETCHED_AT", "TIMESTAMP_NTZ", "When this data was fetched"),
        ],
        notes="Interest scores are relative within each keyword (100 = peak popularity for that term). Use for seasonality analysis."
    ),

    # -------------------------------------------------------------------------
    # Keywords Master List
    # -------------------------------------------------------------------------
    Table(
        name="PRIORITY_TIRE_DATA.UMIP_MOCK.KEYWORDS_MASTER",
        description="Master list of tracked keywords with categorization.",
        columns=[
            Column("KEYWORD", "TEXT", "The keyword/search term"),
            Column("CATEGORY", "TEXT", "Keyword category", "tire size, brand, brand+model"),
            Column("IS_ACTIVE", "BOOLEAN", "Whether keyword is actively tracked"),
            Column("ADDED_AT", "TIMESTAMP_NTZ", "When keyword was added to tracking"),
        ],
        notes="Reference table for keyword management."
    ),

    # -------------------------------------------------------------------------
    # Keyword Analysis (Aggregated View)
    # -------------------------------------------------------------------------
    Table(
        name="PRIORITY_TIRE_DATA.UMIP_MOCK.KEYWORD_ANALYSIS",
        description="Comprehensive keyword analysis combining SEO, GA4, and trend data with seasonality metrics.",
        columns=[
            Column("KEYWORD", "TEXT", "The analyzed keyword"),
            Column("PAGE_PATH", "TEXT", "Ranking page path"),
            Column("SEARCH_VOLUME", "NUMBER", "Monthly search volume"),
            Column("CURRENT_POSITION", "NUMBER", "Current SERP position"),
            Column("CURRENT_TRAFFIC", "NUMBER", "Estimated organic traffic"),
            Column("KEYWORD_DIFFICULTY", "NUMBER", "Ahrefs KD score"),
            Column("TOTAL_USERS", "NUMBER", "GA4 users for ranking page"),
            Column("USER_KEY_EVENT_RATE", "FLOAT", "Conversion rate"),
            Column("TOTAL_REVENUE", "FLOAT", "Revenue from ranking page"),
            Column("SLOPE", "FLOAT", "Trend line slope (positive = growing)"),
            Column("P_VALUE", "FLOAT", "Statistical significance of trend"),
            Column("ANNUAL_GROWTH", "FLOAT", "Year-over-year growth rate"),
            Column("TREND_CLASSIFICATION", "TEXT", "Trend category", "growing, declining, stable, seasonal"),
            Column("Q1_AVG", "FLOAT", "Average interest Q1 (Jan-Mar)"),
            Column("Q2_AVG", "FLOAT", "Average interest Q2 (Apr-Jun)"),
            Column("Q3_AVG", "FLOAT", "Average interest Q3 (Jul-Sep)"),
            Column("Q4_AVG", "FLOAT", "Average interest Q4 (Oct-Dec)"),
            Column("PEAK_QUARTER", "TEXT", "Quarter with highest average interest", "Q1, Q2, Q3, Q4"),
            Column("JAN_AVG", "FLOAT", "Average January interest"),
            Column("FEB_AVG", "FLOAT", "Average February interest"),
            Column("MAR_AVG", "FLOAT", "Average March interest"),
            Column("APR_AVG", "FLOAT", "Average April interest"),
            Column("MAY_AVG", "FLOAT", "Average May interest"),
            Column("JUN_AVG", "FLOAT", "Average June interest"),
            Column("JUL_AVG", "FLOAT", "Average July interest"),
            Column("AUG_AVG", "FLOAT", "Average August interest"),
            Column("SEP_AVG", "FLOAT", "Average September interest"),
            Column("OCT_AVG", "FLOAT", "Average October interest"),
            Column("NOV_AVG", "FLOAT", "Average November interest"),
            Column("DEC_AVG", "FLOAT", "Average December interest"),
            Column("PEAK_MONTH", "TEXT", "Month with highest average interest"),
            Column("PEAK_CONSISTENCY", "FLOAT", "How consistent the peak month is across years (0-1)"),
        ],
        notes="Pre-computed analysis table. Best for quick lookups. Use this for questions about keyword performance, seasonality, and opportunities."
    ),

    # -------------------------------------------------------------------------
    # Seasonality Tables
    # -------------------------------------------------------------------------
    Table(
        name="PRIORITY_TIRE_DATA.UMIP_MOCK.SEASONALITY_MONTHLY",
        description="Monthly seasonality patterns for keywords.",
        columns=[
            Column("KEYWORD", "TEXT", "The keyword"),
            Column("ANALYSIS_DATE", "DATE", "When analysis was performed"),
            Column("JAN_AVG", "FLOAT", "Average January interest"),
            Column("FEB_AVG", "FLOAT", "Average February interest"),
            Column("MAR_AVG", "FLOAT", "Average March interest"),
            Column("APR_AVG", "FLOAT", "Average April interest"),
            Column("MAY_AVG", "FLOAT", "Average May interest"),
            Column("JUN_AVG", "FLOAT", "Average June interest"),
            Column("JUL_AVG", "FLOAT", "Average July interest"),
            Column("AUG_AVG", "FLOAT", "Average August interest"),
            Column("SEP_AVG", "FLOAT", "Average September interest"),
            Column("OCT_AVG", "FLOAT", "Average October interest"),
            Column("NOV_AVG", "FLOAT", "Average November interest"),
            Column("DEC_AVG", "FLOAT", "Average December interest"),
            Column("PEAK_MONTH", "TEXT", "Month with highest interest"),
            Column("PEAK_CONSISTENCY", "FLOAT", "Consistency score (0-1)"),
            Column("CREATED_AT", "TIMESTAMP_NTZ", "Record creation timestamp"),
        ],
        notes="Use for monthly seasonality patterns and planning ad spend timing."
    ),

    Table(
        name="PRIORITY_TIRE_DATA.UMIP_MOCK.SEASONALITY_QUARTERLY",
        description="Quarterly seasonality patterns for keywords.",
        columns=[
            Column("KEYWORD", "TEXT", "The keyword"),
            Column("ANALYSIS_DATE", "DATE", "When analysis was performed"),
            Column("Q1_AVG", "FLOAT", "Average Q1 interest (Jan-Mar)"),
            Column("Q2_AVG", "FLOAT", "Average Q2 interest (Apr-Jun)"),
            Column("Q3_AVG", "FLOAT", "Average Q3 interest (Jul-Sep)"),
            Column("Q4_AVG", "FLOAT", "Average Q4 interest (Oct-Dec)"),
            Column("PEAK_QUARTER", "TEXT", "Quarter with highest interest"),
            Column("CREATED_AT", "TIMESTAMP_NTZ", "Record creation timestamp"),
        ],
        notes="Use for quarterly planning and budget allocation."
    ),

    # -------------------------------------------------------------------------
    # Trend Analysis
    # -------------------------------------------------------------------------
    Table(
        name="PRIORITY_TIRE_DATA.UMIP_MOCK.TREND_ANALYSIS",
        description="Long-term trend analysis for keywords.",
        columns=[
            Column("KEYWORD", "TEXT", "The keyword"),
            Column("ANALYSIS_DATE", "DATE", "When analysis was performed"),
            Column("SLOPE", "FLOAT", "Trend line slope (positive = growing interest)"),
            Column("P_VALUE", "FLOAT", "Statistical significance (< 0.05 = significant)"),
            Column("ANNUAL_GROWTH", "FLOAT", "Estimated annual growth rate"),
            Column("TREND_CLASSIFICATION", "TEXT", "Category", "growing, declining, stable"),
            Column("DATA_POINTS", "NUMBER", "Number of data points in analysis"),
            Column("CREATED_AT", "TIMESTAMP_NTZ", "Record creation timestamp"),
        ],
        notes="Use for identifying growing vs declining keyword opportunities."
    ),

    # -------------------------------------------------------------------------
    # PLACEHOLDER: Google Ads (Future - API import via N8N)
    # -------------------------------------------------------------------------
    Table(
        name="PRIORITY_TIRE_DATA.UMIP_MOCK.GOOGLE_ADS_CAMPAIGNS",
        description="[PLACEHOLDER - Coming Soon] Google Ads campaign performance data.",
        columns=[
            Column("DATE", "DATE", "Report date"),
            Column("CAMPAIGN_NAME", "TEXT", "Campaign name"),
            Column("CAMPAIGN_TYPE", "TEXT", "Campaign type", "Search, Shopping, Performance Max"),
            Column("IMPRESSIONS", "NUMBER", "Ad impressions"),
            Column("CLICKS", "NUMBER", "Ad clicks"),
            Column("COST", "FLOAT", "Ad spend in USD"),
            Column("CONVERSIONS", "FLOAT", "Conversion count"),
            Column("CONVERSION_VALUE", "FLOAT", "Total conversion value in USD"),
        ],
        notes="PLACEHOLDER TABLE - Not yet populated. Will be imported via Google Ads API through N8N."
    ),

    # -------------------------------------------------------------------------
    # PLACEHOLDER: NetSuite Inventory (Future - API import via N8N)
    # -------------------------------------------------------------------------
    Table(
        name="PRIORITY_TIRE_DATA.UMIP_MOCK.NETSUITE_INVENTORY",
        description="[PLACEHOLDER - Coming Soon] Inventory levels and pricing from NetSuite.",
        columns=[
            Column("SKU", "TEXT", "Product SKU"),
            Column("PRODUCT_NAME", "TEXT", "Product display name"),
            Column("BRAND", "TEXT", "Tire brand"),
            Column("SIZE", "TEXT", "Tire size", "225/65R17"),
            Column("QUANTITY_ON_HAND", "NUMBER", "Current stock level"),
            Column("QUANTITY_AVAILABLE", "NUMBER", "Available to sell"),
            Column("UNIT_COST", "FLOAT", "Our cost per unit"),
            Column("LIST_PRICE", "FLOAT", "Current selling price"),
            Column("LAST_UPDATED", "TIMESTAMP_NTZ", "Last sync timestamp"),
        ],
        notes="PLACEHOLDER TABLE - Not yet populated. Will be imported via NetSuite API through N8N."
    ),
]


def get_schema_documentation() -> str:
    """
    Generate formatted schema documentation for the LLM prompt.
    
    Returns:
        Formatted string describing all tables and columns
    """
    lines = []
    
    for table in TABLES:
        lines.append(f"### {table.name}")
        lines.append(f"{table.description}")
        lines.append("")
        lines.append("Columns:")
        
        for col in table.columns:
            example = f" (e.g., {col.example_values})" if col.example_values else ""
            lines.append(f"  - {col.name} ({col.data_type}): {col.description}{example}")
        
        if table.notes:
            lines.append(f"\nNotes: {table.notes}")
        
        lines.append("")
    
    return "\n".join(lines)


def get_table_names() -> list[str]:
    """Return list of all table names."""
    return [table.name for table in TABLES]