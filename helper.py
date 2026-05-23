import pandas as pd
import matplotlib.pyplot as plt  
import seaborn as sns  
import matplotlib.patches as mpatches

def load_data(file_path="nepal-earthquake-severity-index-latest.csv"):
    """Loads the earthquake dataset and cleans basic issues."""
    df = pd.read_csv(file_path)
    # Drop duplicates if any exist
    df = df.drop_duplicates()
    return df

def get_kpis(df):
    """Calculates overall metrics for the homepage."""
    kpis = {
        "total_vdcs": df["P_CODE"].nunique(),
        "total_districts": df["DISTRICT"].nunique(),
        "total_regions": df["REGION"].nunique(),
        "avg_severity": df["Severity"].mean(),
        "max_severity": df["Severity"].max()
    }
    return kpis

def filter_data(df, region=None, severity_cat=None):
    """Filters data dynamic based on user selection in Streamlit."""
    filtered_df = df.copy()
    
    if region and region != "All":
        filtered_df = filtered_df[filtered_df["REGION"] == region]
        
    if severity_cat and severity_cat != "All":
        filtered_df = filtered_df[filtered_df["Severity category"] == severity_cat]
        
    return filtered_df

def get_region_summary(df):
    """Aggregates all key risk metrics across regions."""
    region_summary = df.groupby("REGION").agg({
        "Severity": "mean",
        "Hazard (Intensity)": "mean",
        "Exposure": "mean",
        "Vulnerability": "mean",
        "P_CODE": "count"
    }).rename(columns={"P_CODE": "Total Areas"}).sort_values("Severity", ascending=False)
    
    return region_summary.reset_index()

def get_top_risky_districts(df, top_n=10):
    """Returns the top N risky districts based on average severity."""
    district_risk = df.groupby("DISTRICT")["Severity"].mean().sort_values(ascending=False).head(top_n).reset_index()
    return district_risk



def get_district_profile_data(df, target_district):
    """
    Takes the main dataset and pulls out the clean metrics 
    and a sorted table for ONE chosen district.
    """
    # Step 1: Filter down to rows belonging ONLY to the selected district
    district_df = df[df["DISTRICT"] == target_district]
    
    # Step 2: Calculate the 4 averages for our Summary Cards
    avg_severity = district_df["Severity"].mean()
    avg_hazard = district_df["Hazard (Intensity)"].mean()
    avg_housing = district_df["Housing"].mean()
    total_local_units = district_df["VDC_NAME"].nunique()
    
    # Step 3: Streamline the table columns and rename for professional display
    important_cols = [
        "VDC_NAME", "REGION", "Hazard (Intensity)", 
        "Exposure", "Housing", "Poverty", "Severity", "Severity category"
    ]
    
    # Slice the dataframe and rename the column title beautifully
    clean_table = district_df[important_cols].rename(
        columns={"VDC_NAME": "Local Unit (Municipality/VDC)"}
    )
    
    # Step 4: Sort strictly by Severity Score from Highest to Lowest
    clean_table_sorted = clean_table.sort_values(by="Severity", ascending=False)
    
    # Return all 5 pieces of information back to app.py
    return avg_severity, avg_hazard, avg_housing, total_local_units, clean_table_sorted


def generate_district_chart(sorted_df, district_name):
    """
    Takes the sorted table and draws the horizontal bar chart
    showing the gap between top and bottom local units.
    """
    # Clear the current figure canvas state to prevent visual cross-page bleeding
    plt.clf()
    
    # 1. Grab top 5 worst-hit and bottom 5 safest areas
    top_5 = sorted_df.head(5)
    bottom_5 = sorted_df.tail(5)
    
    # Combine them into a plotting dataframe (and remove duplicates if the district has fewer than 10 units total)
    plot_df = pd.concat([top_5, bottom_5]).drop_duplicates()
    
    # 2. Initialize a blank Matplotlib figure canvas
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # 3. Create our custom color list
    colors = ['#d9534f'] * len(top_5) + ['#5bc0de'] * len(bottom_5)
    colors = colors[:len(plot_df)] # Adjust length to fit exact data size
    
    # 4. Draw the actual bar chart onto our axis (ax=ax keeps it safe inside the figure)
    sns.barplot(
        data=plot_df, 
        x="Severity", 
        y="Local Unit (Municipality/VDC)", 
        palette=colors,
        ax=ax
    )
    
    # 5. Add custom legend at the bottom right using the mpatches namespace
    red_patch = mpatches.Patch(color='#d9534f', label='Top 5 Highest Severity Areas')
    blue_patch = mpatches.Patch(color='#5bc0de', label='Top 5 Lowest Severity Areas')
    ax.legend(handles=[red_patch, blue_patch], loc='lower right', frameon=True)
    
    # 6. Dress up the titles and labels
    ax.set_title(f"Severity Range: Top & Bottom Impacted Local Units in {district_name}", fontsize=12, fontweight='bold')
    ax.set_xlabel("Severity Score")
    ax.set_ylabel("")
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    
    # Return the entire completed figure object back to app.py
    return fig