import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import helper  # Safe import for helper.py

# Set page layout to wide
st.set_page_config(page_title="Nepal Earthquake Risk Dashboard", layout="wide")

# 1. LOAD DATA
df = helper.load_data()

# 2. CLEAN IT IMMEDIATELY (Drop the null district rows right here!)
df = df.dropna(subset=["DISTRICT"])
df = df.drop_duplicates()

# ==========================================
# 2. SIDEBAR NAVIGATION & DYNAMIC FILTERS
# ==========================================
st.sidebar.title("Navigation")

# This creates your clean menu links in the sidebar with zero extra spaces
app_mode = st.sidebar.radio(
    "Go To:",
    ["Overview & KPIs", "Region filter", "District Profiles", "Risk Factor Relationships & conclusion"]
)

# Initialize variables to avoid NameError when navigating between different pages
selected_region = "All"
selected_severity = "All"
filtered_df = df.copy()

# Only process and show filter configurations if the user is explicitly on the filter page
if app_mode == "Region filter":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Controls")
    
    region_options = ["All"] + list(df["REGION"].unique())
    severity_options = ["All"] + list(df["Severity category"].unique())

    selected_region = st.sidebar.selectbox("Select Region:", region_options)
    selected_severity = st.sidebar.selectbox("Select Severity Category:", severity_options)

    # Process filtered data exclusively for this view
    filtered_df = helper.filter_data(df, selected_region, selected_severity)


# ==========================================
# 3. RENDER THE SECTIONS BASED ON SELECTION
# ==========================================

#  PAGE 1: OVERVIEW & KPIS
if app_mode == "Overview & KPIs":
    st.title("🇳🇵 Nepal Earthquake Overall Statistics")
    st.markdown("Master view of total country risk indicators.")
    
    kpis = helper.get_kpis(df)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Regions", kpis["total_regions"])
    col2.metric("Total Districts Involved", kpis["total_districts"])
    col3.metric("Average Severity Index", f"{kpis['avg_severity']:.2f}")
    col4.metric("Maximum Severity Recorded", f"{kpis['max_severity']:.2f}")
    
    st.markdown("---")
  # ======================================================================
   # ======================================================================
    #  FIXED: 6-CATEGORY EXPLICIT REGIONAL BREAKDOWN (Manual Mapping)
    # ======================================================================
    st.subheader(" Macro-Regional Crisis Breakdown")
    st.markdown("This chart showcases how earthquake severity categories were distributed across different macro-geographic regions.")
    
    # 1. Prepare the stacked data matrix
    region_counts = df.groupby("REGION")["Severity category"].value_counts().unstack().fillna(0)
    
    # 2. DEFINED MANUALLY: Map your exact 6 categories from lowest risk to absolute highest risk
    #  EDIT THESE STRINGS BELOW TO MATCH YOUR EXACT DATAFRAME VALUE SPELLINGS
    manual_order_and_colors = {
        "Lowest": "#2ca02c",  # Green (Lowest Risk)
        "Low": "#dbdb8d",  # Soft Yellow
        "Medium-Low": "#ffbb78",  # Light Orange
        "Medium-High": "#ff7f0e",  # True Orange
        "High": "#ff4d4d",  # Light Red (High Risk)
        "Highest": "#660000"   # Dark Red / Dark Burgundy (Highest Risk)
    }
    
    # 3. Align the dataframe columns to your exact structural order
    # This filters out errors if a specific category isn't present in a region
    ordered_categories = [cat for cat in manual_order_and_colors.keys() if cat in region_counts.columns]
    region_counts = region_counts.reindex(columns=ordered_categories, fill_value=0)
    
    # Extract the exact matching custom colors for the columns present
    color_list = [manual_order_and_colors[cat] for cat in region_counts.columns]
    
    # 4. Build the chart using a clean theme
    sns.set_theme(style="whitegrid")
    fig_regional, ax_regional = plt.subplots(figsize=(10, 5))
    
    # Explicit float conversion stops internal data type plotting failures
    region_counts.astype(float).plot(kind="bar", stacked=True, ax=ax_regional, color=color_list)
    
    # 5. Clean up the labels and layout for a web browser view
    ax_regional.set_title("Distribution of Severity Categories by Region", fontsize=13, fontweight='bold', pad=12)
    ax_regional.set_xlabel("Geographic Region", fontsize=10)
    ax_regional.set_ylabel("Count of Local Units / Villages", fontsize=10)
    
    plt.xticks(rotation=15, ha='right', fontsize=9)
    ax_regional.legend(title="Severity Category", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
    plt.tight_layout()
    
    st.pyplot(fig_regional)
    # ======================================================================
   # ======================================================================
    # 📊 NEW CHART: DISTRICTS PER SEVERITY CATEGORY (Stacked Directly Below)
    # ======================================================================
    st.subheader("📊 National District Severity Summary")
    st.markdown("This chart counts the number of individual districts across Nepal assigned to each severity level, calculated by taking the most common (mode) severity category reported across all local units inside that district.")

        # 1. Clean data aggregation (1 row per district using mode)
    try:
        district_df = df.groupby("DISTRICT", as_index=False)["Severity category"].agg(lambda x: x.mode()[0] if not x.mode().empty else None)
    except Exception:
        district_df = df.groupby("DISTRICT", as_index=False)["Severity category"].first()

    # 2. Match your manual color theme ordering for the X-axis
    available_order = [cat for cat in manual_order_and_colors.keys() if cat in district_df["Severity category"].unique()]
    countplot_colors = [manual_order_and_colors[cat] for cat in available_order]

    # 3. Build the minimalist Countplot
    fig_count, ax_count = plt.subplots(figsize=(10, 5))
    sns.countplot(
        data=district_df, 
        x="Severity category", 
        order=available_order, 
        palette=countplot_colors, 
        ax=ax_count
    )

    # 4. FIX: Loop through ALL containers to apply counts on top of every single bar
    for container in ax_count.containers:
        ax_count.bar_label(container, fontweight='bold', padding=3)

    # 5. Style the plot beautifully for the web screen
    ax_count.set_title("Total Districts per Severity Category", fontsize=13, fontweight='bold', pad=12)
    ax_count.set_xlabel("Severity Category", fontsize=10)
    ax_count.set_ylabel("Number of Districts", fontsize=10)
    plt.xticks(rotation=15, ha='right', fontsize=9)
    plt.tight_layout()

    st.pyplot(fig_count)
    # ======================================================================
    # ======================================================================
    
    st.markdown("---") # Visual separator before your existing columns start
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Top 10 Most Risky Districts (Overall)")
        top_10 = helper.get_top_risky_districts(df, top_n=10)
        
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(data=top_10, x="Severity", y="DISTRICT", ax=ax, palette="Reds_r")
        ax.set_title("Average Severity Score by District")
        st.pyplot(fig)
        
    with col_right:
        st.subheader("Severity Category Breakdown")
        fig, ax = plt.subplots(figsize=(5, 5))
        df["Severity category"].value_counts().plot(kind="pie", autopct="%1.1f%%", ax=ax, colors=["#ff9999","#66b3ff","#99ff99"])
        ax.set_ylabel("") 
        st.pyplot(fig)

#  PAGE 2: FILTER EXPLORATION
elif app_mode == "Region filter":
    st.title("Dynamic Filter Exploration acc to Provinces")
    st.markdown(f"Currently filtering for Region: **{selected_region}** | Severity: **{selected_severity}**")
    st.caption(f"Showing **{len(filtered_df)}** areas matching your sidebar selections.")
    
    display_cols = ["VDC_NAME", "DISTRICT", "REGION", "Hazard (Intensity)", "Exposure", "Vulnerability", "Severity", "Severity category"]
    st.dataframe(filtered_df[display_cols], use_container_width=True)
    
    st.markdown("---")
    
    if not filtered_df.empty:
        st.subheader("Regional Risk Breakdown Table (Filtered View)")
        reg_summary = helper.get_region_summary(filtered_df)
        st.dataframe(reg_summary, use_container_width=True)
    else:
        st.warning("No data matches this specific filter combination.")

# PAGE 3: DISTRICT PROFILES
elif app_mode == "District Profiles":
    st.title("Local District Profile Deep-Dive")
    st.markdown("Select an individual district to view its localized summaries, range graphs, and ranked municipal impact lists.")
    st.write("---")

    # 1. Generate the Clean Dropdown List (Sorted Alphabetically)
    available_districts = sorted(df["DISTRICT"].unique())
    
    selected_district = st.selectbox(
        "Select District to Generate Local Profile:", 
        options=available_districts
    )

    # 2. Extract calculations and tables from helper.py
    avg_sev, avg_haz, avg_hou, total_units, sorted_table = helper.get_district_profile_data(df, selected_district)

    # 3. Render the 4 Summary Cards horizontally side-by-side
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Avg Severity Score", value=f"{avg_sev:.2f} / 10")
    with col2:
        st.metric(label="Avg Shaking Hazard", value=f"{avg_haz:.2f}")
    with col3:
        st.metric(label="Avg Housing Vulnerability", value=f"{avg_hou:.2f}")
    with col4:
        st.metric(label="Total Local Units", value=f"{total_units} VDCs/Muns")

    st.write("---")

    # 4. Generate and display the horizontal range bar chart
    st.subheader(f"Severity Contrast Chart for {selected_district}")
    st.markdown("Visualizing the internal disparity: Top 5 most impacted vs. Top 5 least impacted areas within the district.")
    
    # We call our helper function which builds and returns the complete plt object
    district_fig = helper.generate_district_chart(sorted_table, selected_district)
    st.pyplot(district_fig)

    st.write("---")

    # 5. Display the Dataframe Table spanning the full page width
    st.subheader(f"Ranked Municipal Impact Data (Highest to Lowest)")
    st.markdown("This list contains your important columns, automatically sorted by the continuous severity calculation value.")
    
    st.dataframe(sorted_table, use_container_width=True)

#  PAGE 4: Risk Factor Relationships & conclusion
elif app_mode == "Risk Factor Relationships & conclusion":
    st.title("What Drives Earthquake Severity?")
    st.markdown("Analyzing how different factors impact Severity.")
    
    # 1. ADD THIS LINE BACK: This splits your app layout into two columns
    col_chart, col_corr = st.columns([3, 2])
    
    # Put the scatter plot in the left column
    with col_chart:
        factor = st.radio("Select Factor to Compare with Severity:", 
                          ["Hazard (Intensity)", "Exposure", "Vulnerability"])
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(df[factor], df["Severity"], alpha=0.6, color='blue')
        
        ax.set_xlabel(factor)
        ax.set_ylabel("Severity Score")
        ax.set_title(f"{factor} vs Severity")
        ax.grid(True, linestyle='--', alpha=0.3)
        
        st.pyplot(fig)
        
    # Put the heatmap in the right column
    with col_corr:
        st.subheader("Risk Factor Correlations")
        cols = ["Hazard (Intensity)", "Exposure", "Vulnerability", "Severity", "Housing", "Poverty"]
        corr_matrix = df[cols].corr()
        
        fig, ax = plt.subplots(figsize=(5, 4.5))
        sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", ax=ax, cbar=False)
        ax.set_title("Correlation Heatmap Matrix")
        
        st.pyplot(fig)

    