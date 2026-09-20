import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")
plt.style.use("seaborn-v0_8-darkgrid")
sns.set_palette("husl")


def parse_date_safe(date_str: str | float | int | None):
    if pd.isna(date_str):
        return None
    text = str(date_str).strip()
    formats = ["%d-%m-%Y", "%m-%d-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
    for fmt in formats:
        try:
            return pd.to_datetime(text, format=fmt)
        except Exception:
            continue
    try:
        return pd.to_datetime(text)
    except Exception:
        return None


def standardize_pincode(pincode: str | float | int | None):
    if pd.isna(pincode):
        return None
    return str(int(float(pincode))).zfill(6)


def load_base_data(prefix: str):
    enrolment = pd.read_csv(prefix + "combined enrolment.csv")
    demographic = pd.read_csv(prefix + "combined demographic.csv")
    biometric = pd.read_csv(prefix + "combined biometrics.csv")
    geo_data = gpd.read_file(prefix + "All_India_pincode.geojson")
    census = pd.read_csv(prefix + "consolidated_pincode_census.csv")
    return enrolment, demographic, biometric, geo_data, census


def clean_enrolment(df: pd.DataFrame):
    df = df.copy()
    df["date"] = df["date"].apply(parse_date_safe)
    df = df.dropna(subset=["date"])
    df["pincode"] = df["pincode"].apply(standardize_pincode)
    df = df.dropna(subset=["pincode"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["year_month"] = df["date"].dt.to_period("M")
    for col in ["age_0_5", "age_5_17", "age_18_greater"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def clean_demographic(df: pd.DataFrame):
    df = df.copy()
    df["date"] = df["date"].apply(parse_date_safe)
    df = df.dropna(subset=["date"])
    df["pincode"] = df["pincode"].apply(standardize_pincode)
    df = df.dropna(subset=["pincode"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["year_month"] = df["date"].dt.to_period("M")
    for col in ["demo_age_5_17", "demo_age_17_"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def clean_biometric(df: pd.DataFrame):
    df = df.copy()
    df["date"] = df["date"].apply(parse_date_safe)
    df = df.dropna(subset=["date"])
    df["pincode"] = df["pincode"].apply(standardize_pincode)
    df = df.dropna(subset=["pincode"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["year_month"] = df["date"].dt.to_period("M")
    for col in ["bio_age_5_17", "bio_age_17_"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def clean_census(df: pd.DataFrame):
    df = df.copy()
    df["pincode"] = df["pincode"].apply(standardize_pincode)
    df = df.dropna(subset=["pincode"])
    if "Persons" in df.columns:
        df["population"] = pd.to_numeric(df["Persons"], errors="coerce")
    else:
        pop_col = [c for c in df.columns if "person" in c.lower() or "population" in c.lower()]
        if pop_col:
            df["population"] = pd.to_numeric(df[pop_col[0]], errors="coerce")
    if "X5...14.years" in df.columns:
        df["child_population"] = pd.to_numeric(df["X5...14.years"], errors="coerce")
    return df


def aggregate_data(enrolment, demographic, biometric, census):
    enrol_agg = enrolment.groupby(["pincode", "year_month"]).agg(
        age_0_5=("age_0_5", "sum"),
        age_5_17=("age_5_17", "sum"),
        age_18_greater=("age_18_greater", "sum"),
        state=("state", "first"),
        district=("district", "first"),
        month=("month", "first"),
        year=("year", "first"),
    ).reset_index()
    enrol_agg["total_enrolment"] = enrol_agg[["age_0_5", "age_5_17", "age_18_greater"]].sum(axis=1)

    demo_agg = demographic.groupby(["pincode", "year_month"]).agg(
        demo_age_5_17=("demo_age_5_17", "sum"),
        demo_age_17_=("demo_age_17_", "sum"),
        month_demo=("month", "first"),
        year_demo=("year", "first"),
    ).reset_index()
    demo_agg["total_demographic"] = demo_agg[["demo_age_5_17", "demo_age_17_"]].sum(axis=1)

    bio_agg = biometric.groupby(["pincode", "year_month"]).agg(
        bio_age_5_17=("bio_age_5_17", "sum"),
        bio_age_17_=("bio_age_17_", "sum"),
        month_bio=("month", "first"),
        year_bio=("year", "first"),
    ).reset_index()
    bio_agg["total_biometric"] = bio_agg[["bio_age_5_17", "bio_age_17_"]].sum(axis=1)

    combined = enrol_agg.merge(demo_agg, on=["pincode", "year_month"], how="outer")
    combined = combined.merge(bio_agg, on=["pincode", "year_month"], how="outer")
    combined = combined.merge(census[["pincode", "population", "child_population"]], on="pincode", how="left")
    combined["month"] = combined["month"].fillna(combined["month_demo"]).fillna(combined["month_bio"])
    combined["year"] = combined["year"].fillna(combined["year_demo"]).fillna(combined["year_bio"])
    count_cols = [
        "age_0_5",
        "age_5_17",
        "age_18_greater",
        "total_enrolment",
        "demo_age_5_17",
        "demo_age_17_",
        "total_demographic",
        "bio_age_5_17",
        "bio_age_17_",
        "total_biometric",
    ]
    for col in count_cols:
        if col in combined.columns:
            combined[col] = combined[col].fillna(0)
    return combined


def add_metrics(combined):
    combined = combined.copy()
    combined["enrol_per_10k"] = combined["total_enrolment"] / combined["population"] * 10000
    combined["demo_per_10k"] = combined["total_demographic"] / combined["population"] * 10000
    combined["bio_per_10k"] = combined["total_biometric"] / combined["population"] * 10000
    combined.replace([np.inf, -np.inf], np.nan, inplace=True)
    combined["is_oct_dec"] = combined["month"].isin([10, 11, 12])
    return combined


def compute_suii(combined):
    suii_calc = (
        combined.groupby("pincode")
        .apply(
            lambda x: pd.Series(
                {
                    "demo_oct_dec_avg": x[x["is_oct_dec"]]["total_demographic"].mean(),
                    "demo_other_avg": x[~x["is_oct_dec"]]["total_demographic"].mean(),
                    "bio_oct_dec_avg": x[x["is_oct_dec"]]["total_biometric"].mean(),
                    "bio_other_avg": x[~x["is_oct_dec"]]["total_biometric"].mean(),
                    "state": x["state"].iloc[0] if "state" in x.columns and len(x) else None,
                    "district": x["district"].iloc[0] if "district" in x.columns and len(x) else None,
                }
            )
        )
        .reset_index()
    )
    suii_calc["demo_SUII"] = suii_calc["demo_oct_dec_avg"] / suii_calc["demo_other_avg"]
    suii_calc["bio_SUII"] = suii_calc["bio_oct_dec_avg"] / suii_calc["bio_other_avg"]
    suii_calc.replace([np.inf, -np.inf], np.nan, inplace=True)
    return suii_calc


def compute_yur(combined):
    oct_dec_data = (
        combined[combined["is_oct_dec"]]
        .groupby("pincode")
        .agg(
            demo_age_5_17=("demo_age_5_17", "sum"),
            total_demographic=("total_demographic", "sum"),
            bio_age_5_17=("bio_age_5_17", "sum"),
            total_biometric=("total_biometric", "sum"),
        )
        .reset_index()
    )
    oct_dec_data["demo_YUR"] = oct_dec_data["demo_age_5_17"] / oct_dec_data["total_demographic"] * 100
    oct_dec_data["bio_YUR"] = oct_dec_data["bio_age_5_17"] / oct_dec_data["total_biometric"] * 100
    oct_dec_data.replace([np.inf, -np.inf], np.nan, inplace=True)
    return oct_dec_data


def compute_biometric_risk(combined):
    bio_risk = (
        combined.groupby("pincode")
        .agg(
            child_population=("child_population", "first"),
            total_biometric=("total_biometric", "sum"),
            population=("population", "first"),
            state=("state", "first"),
            district=("district", "first"),
        )
        .reset_index()
    )
    bio_risk["bio_per_capita"] = bio_risk["total_biometric"] / bio_risk["population"]
    bio_risk["biometric_risk_score"] = bio_risk["child_population"] / (
        bio_risk["bio_per_capita"] * bio_risk["population"] + 1
    )
    bio_risk.replace([np.inf, -np.inf], np.nan, inplace=True)
    return bio_risk


def plot_monthly_trends(combined):
    monthly_trends = (
        combined.groupby("year_month")
        .agg(total_demographic=("total_demographic", "sum"), total_biometric=("total_biometric", "sum"), total_enrolment=("total_enrolment", "sum"), month=("month", "first"))
        .reset_index()
        .sort_values("year_month")
    )
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    ax1.plot(range(len(monthly_trends)), monthly_trends["total_demographic"], marker="o", linewidth=2, markersize=6, color="steelblue", label="Demographic")
    ax1.set_title("Monthly Demographic Updates Trend", fontsize=14, fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    for i, row in monthly_trends.iterrows():
        if row["month"] in [10, 11, 12]:
            ax1.axvspan(i - 0.5, i + 0.5, alpha=0.2, color="orange")
    ax2.plot(range(len(monthly_trends)), monthly_trends["total_biometric"], marker="s", linewidth=2, markersize=6, color="darkgreen", label="Biometric")
    ax2.set_title("Monthly Biometric Updates Trend", fontsize=14, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    for i, row in monthly_trends.iterrows():
        if row["month"] in [10, 11, 12]:
            ax2.axvspan(i - 0.5, i + 0.5, alpha=0.2, color="orange")
    plt.tight_layout()
    plt.show()


def plot_top_seasonal(suii_calc):
    top_seasonal = suii_calc.nlargest(20, "demo_SUII")
    plt.figure(figsize=(12, 8))
    plt.barh(range(len(top_seasonal)), top_seasonal["demo_SUII"], color="coral")
    plt.yticks(range(len(top_seasonal)), top_seasonal["pincode"])
    plt.xlabel("Seasonal Intensity Index")
    plt.title("Top 20 Pincodes with Strongest Oct-Dec Spike", fontsize=14, fontweight="bold")
    plt.axvline(x=1.0, color="red", linestyle="--", linewidth=2, label="No seasonal effect")
    plt.legend()
    plt.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.show()


def plot_population_scatter(combined):
    scatter_data = (
        combined.groupby("pincode")
        .agg(population=("population", "first"), demo_per_10k=("demo_per_10k", "mean"), bio_per_10k=("bio_per_10k", "mean"))
        .reset_index()
        .dropna()
    )
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    ax1.scatter(scatter_data["population"], scatter_data["demo_per_10k"], alpha=0.5, s=50, color="steelblue")
    ax1.set_xscale("log")
    ax1.set_xlabel("Population")
    ax1.set_ylabel("Demographic Updates per 10,000")
    ax1.set_title("Population vs Demographic Update Rate", fontsize=14, fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax2.scatter(scatter_data["population"], scatter_data["bio_per_10k"], alpha=0.5, s=50, color="darkgreen")
    ax2.set_xscale("log")
    ax2.set_xlabel("Population")
    ax2.set_ylabel("Biometric Updates per 10,000")
    ax2.set_title("Population vs Biometric Update Rate", fontsize=14, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def plot_geo_risk(geo_data, bio_risk):
    top_risk = bio_risk.nlargest(100, "biometric_risk_score")
    risk_map = geo_data.merge(top_risk, on="pincode", how="inner")
    if not len(risk_map):
        print("No geographic matches found for risk map")
        return
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    risk_map.plot(column="biometric_risk_score", cmap="YlOrRd", legend=True, ax=ax, legend_kwds={"label": "Biometric Risk Score"})
    ax.set_title("Top 100 High-Risk Pincodes for Biometric Updates", fontsize=16, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    plt.show()


def plot_youth_pies(combined):
    oct_dec_summary = combined[combined["is_oct_dec"]].agg(
        demo_age_5_17=("demo_age_5_17", "sum"),
        demo_age_17_=("demo_age_17_", "sum"),
        bio_age_5_17=("bio_age_5_17", "sum"),
        bio_age_17_=("bio_age_17_", "sum"),
    )
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    ax1.pie([oct_dec_summary["demo_age_5_17"], oct_dec_summary["demo_age_17_"]], labels=["Youth (5-17)", "Adults (17+)"], autopct="%1.1f%%", colors=["#ff9999", "#66b3ff"], startangle=90)
    ax1.set_title("Demographic Updates in Oct-Dec", fontsize=14, fontweight="bold")
    ax2.pie([oct_dec_summary["bio_age_5_17"], oct_dec_summary["bio_age_17_"]], labels=["Youth (5-17)", "Adults (17+)"], autopct="%1.1f%%", colors=["#99ff99", "#ffcc99"], startangle=90)
    ax2.set_title("Biometric Updates in Oct-Dec", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.show()


def detect_anomalies(combined):
    combined_sorted = combined.sort_values(["pincode", "year_month"])
    combined_sorted["demo_pct_change"] = combined_sorted.groupby("pincode")["total_demographic"].pct_change() * 100
    combined_sorted["bio_pct_change"] = combined_sorted.groupby("pincode")["total_biometric"].pct_change() * 100
    anomalies_pct = combined_sorted[
        (combined_sorted["demo_pct_change"].abs() > 100) | (combined_sorted["bio_pct_change"].abs() > 100)
    ].copy()
    combined_sorted["demo_zscore"] = combined_sorted.groupby("pincode")["total_demographic"].transform(lambda x: np.abs(stats.zscore(x, nan_policy="omit")))
    combined_sorted["bio_zscore"] = combined_sorted.groupby("pincode")["total_biometric"].transform(lambda x: np.abs(stats.zscore(x, nan_policy="omit")))
    anomalies_z = combined_sorted[(combined_sorted["demo_zscore"] > 3) | (combined_sorted["bio_zscore"] > 3)].copy()
    return combined_sorted, anomalies_pct, anomalies_z


def plot_anomaly_sample(combined_sorted, anomalies_z):
    if not len(anomalies_z):
        print("No anomalies to plot")
        return
    sample_pincode = anomalies_z.groupby("pincode").size().idxmax()
    sample_data = combined_sorted[combined_sorted["pincode"] == sample_pincode].sort_values("year_month")
    plt.figure(figsize=(14, 6))
    plt.plot(range(len(sample_data)), sample_data["total_demographic"], marker="o", linewidth=2, label="Demographic", color="steelblue")
    anomaly_points = sample_data[sample_data["demo_zscore"] > 3]
    anomaly_indices = [sample_data.index.get_loc(idx) for idx in anomaly_points.index]
    plt.scatter(anomaly_indices, anomaly_points["total_demographic"], color="red", s=200, marker="X", zorder=5, label="Anomalies")
    plt.title(f"Demographic Updates Over Time - Pincode {sample_pincode}", fontsize=14, fontweight="bold")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def education_correlation(suii_calc, oct_dec_data):
    education_analysis = suii_calc.merge(oct_dec_data, on="pincode")
    if len(education_analysis) <= 10:
        return None
    correlation = education_analysis[["demo_SUII", "demo_YUR"]].corr().iloc[0, 1]
    plt.figure(figsize=(10, 6))
    plt.scatter(education_analysis["demo_YUR"], education_analysis["demo_SUII"], alpha=0.5, s=50, color="purple")
    plt.xlabel("Youth Update Ratio (%)")
    plt.ylabel("Seasonal Intensity Index")
    plt.title("Youth Activity vs Seasonal Spikes", fontsize=14, fontweight="bold")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    return correlation


def rural_urban_comparison(combined, census):
    if "Rural" not in census.columns or "Urban" not in census.columns:
        return None
    rural_urban = (
        combined.groupby("pincode")
        .agg(demo_per_10k=("demo_per_10k", "mean"), bio_per_10k=("bio_per_10k", "mean"))
        .reset_index()
    )
    rural_urban = rural_urban.merge(census[["pincode", "Rural", "Urban"]], on="pincode")
    rural_urban[["Rural", "Urban"]] = rural_urban[["Rural", "Urban"]].apply(pd.to_numeric, errors="coerce").fillna(0)
    rural_urban["type"] = rural_urban.apply(lambda x: "Rural" if x["Rural"] > x["Urban"] else "Urban", axis=1)
    comparison = rural_urban.groupby("type").agg(demo_per_10k=("demo_per_10k", "mean"), bio_per_10k=("bio_per_10k", "mean"))
    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    comparison["demo_per_10k"].plot(kind="bar", ax=ax[0], color=["green", "orange"])
    ax[0].set_title("Demographic Updates: Rural vs Urban", fontsize=14, fontweight="bold")
    comparison["bio_per_10k"].plot(kind="bar", ax=ax[1], color=["green", "orange"])
    ax[1].set_title("Biometric Updates: Rural vs Urban", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.show()
    return comparison


def migration_bar(combined):
    monthly_demographic = combined.groupby("month").agg(total_demographic=("total_demographic", "sum"), total_biometric=("total_biometric", "sum")).reset_index()
    plt.figure(figsize=(12, 6))
    plt.bar(monthly_demographic["month"], monthly_demographic["total_demographic"], color=["orange" if m in [10, 11, 12] else "steelblue" for m in monthly_demographic["month"]])
    plt.xlabel("Month")
    plt.ylabel("Total Demographic Updates")
    plt.title("Demographic Updates by Month (Orange = Oct-Dec)", fontsize=14, fontweight="bold")
    plt.xticks(range(1, 13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()


def recommendations(suii_calc, bio_risk, oct_dec_data, anomalies_z):
    priority_seasonal = suii_calc.nlargest(20, "demo_SUII")[["pincode", "state", "district", "demo_SUII"]]
    priority_biometric = bio_risk.nlargest(20, "biometric_risk_score")[["pincode", "state", "district", "biometric_risk_score", "child_population"]]
    priority_youth = oct_dec_data.nlargest(20, "demo_YUR")[["pincode", "demo_YUR", "bio_YUR"]]
    resource_matrix = suii_calc.merge(bio_risk[["pincode", "biometric_risk_score"]], on="pincode").merge(oct_dec_data[["pincode", "demo_YUR"]], on="pincode")
    resource_matrix["priority"] = "Low"
    resource_matrix.loc[
        (resource_matrix["demo_SUII"] > 2.0)
        | (resource_matrix["biometric_risk_score"] > resource_matrix["biometric_risk_score"].quantile(0.75)),
        "priority",
    ] = "Medium"
    resource_matrix.loc[
        (resource_matrix["demo_SUII"] > 2.5)
        & (resource_matrix["biometric_risk_score"] > resource_matrix["biometric_risk_score"].quantile(0.85)),
        "priority",
    ] = "High"
    priority_counts = resource_matrix["priority"].value_counts()
    print("Priority Pincodes for Oct-Dec Capacity:\n", priority_seasonal.head(20).to_string(index=False))
    print("\nPriority Pincodes for Mobile Biometric Units:\n", priority_biometric.head(20).to_string(index=False))
    print("\nPriority Pincodes for School Partnerships:\n", priority_youth.head(20).to_string(index=False))
    if len(anomalies_z):
        top_anomalies = anomalies_z.nlargest(15, "demo_zscore")[
            ["pincode", "year_month", "total_demographic", "demo_zscore", "state", "district"]
        ]
        print("\nPriority Anomalies for Investigation:\n", top_anomalies.to_string(index=False))
    print("\nResource Allocation Summary:")
    print(f"High Priority: {priority_counts.get('High', 0)}")
    print(f"Medium Priority: {priority_counts.get('Medium', 0)}")
    print(f"Low Priority: {priority_counts.get('Low', 0)}")


def main():
    file_path_prefix = "/content/"
    enrolment, demographic, biometric, geo_data, census = load_base_data(file_path_prefix)
    enrolment = clean_enrolment(enrolment)
    demographic = clean_demographic(demographic)
    biometric = clean_biometric(biometric)
    census = clean_census(census)
    combined = aggregate_data(enrolment, demographic, biometric, census)
    combined = add_metrics(combined)
    suii_calc = compute_suii(combined)
    oct_dec_data = compute_yur(combined)
    bio_risk = compute_biometric_risk(combined)
    print(f"Combined records: {len(combined)} | Pincodes: {combined['pincode'].nunique()}")
    print(f"Median Demographic SUII: {suii_calc['demo_SUII'].median():.2f}")
    print(f"Median Biometric SUII: {suii_calc['bio_SUII'].median():.2f}")
    print(f"Median Demographic YUR: {oct_dec_data['demo_YUR'].median():.1f}%")
    print(f"Median Biometric YUR: {oct_dec_data['bio_YUR'].median():.1f}%")
    print(f"Median Risk Score: {bio_risk['biometric_risk_score'].median():.2f}")
    plot_monthly_trends(combined)
    plot_top_seasonal(suii_calc)
    plot_population_scatter(combined)
    plot_geo_risk(geo_data, bio_risk)
    plot_youth_pies(combined)
    combined_sorted, anomalies_pct, anomalies_z = detect_anomalies(combined)
    print(f"Anomalies (pct change >100): {len(anomalies_pct)} | Anomalies (z-score>3): {len(anomalies_z)}")
    plot_anomaly_sample(combined_sorted, anomalies_z)
    correlation = education_correlation(suii_calc, oct_dec_data)
    if correlation is not None:
        print(f"Youth-seasonality correlation: {correlation:.3f}")
    comparison = rural_urban_comparison(combined, census)
    if comparison is not None:
        print("Rural vs Urban Comparison:\n", comparison)
    migration_bar(combined)
    recommendations(suii_calc, bio_risk, oct_dec_data, anomalies_z)
    print("Analysis complete")


if __name__ == "__main__":
    main()