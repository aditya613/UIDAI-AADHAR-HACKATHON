import json
import os
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENROL_FILE = os.path.join(SCRIPT_DIR, "combined enrolment.csv")
DEMO_FILE = os.path.join(SCRIPT_DIR, "combined demographic.csv")
BIO_FILE = os.path.join(SCRIPT_DIR, "combined biometrics.csv")
POP_FILE = os.path.join(SCRIPT_DIR, "consolidated_pincode_census.csv")
OUT_JSON = os.path.join(SCRIPT_DIR, "stats.json")

DATE_COL = "date"


def standardize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def ensure_pincode_str(x):
    s = str(int(float(x))) if (pd.notna(x) and str(x).replace('.0','').isdigit()) else str(x).strip()
    return s.zfill(6) if len(s) <= 6 else s


def load_csv(path: str, parse_dates: bool = False) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    kwargs = {}
    if parse_dates:
        kwargs["parse_dates"] = [DATE_COL]
        kwargs["dayfirst"] = True
    df = pd.read_csv(path, **kwargs)
    return standardize_cols(df)


def build_master():
    df_bio = load_csv(BIO_FILE, parse_dates=True)
    df_demo = load_csv(DEMO_FILE, parse_dates=True)
    df_enrol = load_csv(ENROL_FILE, parse_dates=True)

    # Ensure common keys exist
    for df in (df_bio, df_demo, df_enrol):
        for col in ("state", "district", "pincode"):
            if col not in df.columns:
                df[col] = np.nan
        df["pincode"] = df["pincode"].astype(str).map(ensure_pincode_str)

    merge_keys = [DATE_COL, "state", "district", "pincode"]
    master = pd.merge(df_bio, df_demo, on=merge_keys, how="outer")
    master = pd.merge(master, df_enrol, on=merge_keys, how="outer")
    master = master.fillna(0)

    # total enrolment
    a0 = master.get("age_0_5", 0)
    a1 = master.get("age_5_17", 0)
    a2 = master.get("age_18_greater", 0)
    master["total_enrolment"] = a0 + a1 + a2

    return master


def build_population():
    if not os.path.exists(POP_FILE):
        return pd.DataFrame()
    pop_df = pd.read_csv(POP_FILE, dtype=str, low_memory=False)
    pop_df = standardize_cols(pop_df)
    # detect pincode column candidate
    pin_col = None
    for c in pop_df.columns:
        if "pinc" in c:
            pin_col = c
            break
    if pin_col is None:
        pin_col = "pincode" if "pincode" in pop_df.columns else pop_df.columns[1]
    pop_df["pincode"] = pop_df[pin_col].map(ensure_pincode_str)
    # detect population column
    pop_col = None
    for c in pop_df.columns:
        if ("pop" in c) or ("population" in c):
            pop_col = c
            break
    if pop_col is None:
        pop_col = pop_df.columns[-1]
    pop_df["population"] = pd.to_numeric(pop_df[pop_col], errors="coerce").fillna(0)
    return pop_df[["pincode", "population"]]


def compute_summaries(master: pd.DataFrame, pop_df: pd.DataFrame):
    # Map pincode -> district to aggregate population by district
    pincode_district = master[["pincode", "district", "state"]].drop_duplicates()
    if not pop_df.empty:
        pop_with_dist = pd.merge(pop_df, pincode_district, on="pincode", how="left")
        district_pop = pop_with_dist.groupby(["state", "district"]).agg({"population": "sum"}).reset_index()
    else:
        district_pop = pd.DataFrame(columns=["state", "district", "population"])

    # District summary
    agg_dict = {
        "total_enrolment": "sum",
        "age_0_5": "sum",
        "age_5_17": "sum",
        "age_18_greater": "sum",
    }
    # Add optional columns
    if "bio_age_5_17" in master.columns:
        agg_dict["bio_age_5_17"] = "sum"
    if "demo_age_5_17" in master.columns:
        agg_dict["demo_age_5_17"] = "sum"
    if "demo_age_17_" in master.columns:
        agg_dict["demo_age_17_"] = "sum"
    
    district_summary = master.groupby(["state", "district"]).agg(agg_dict).reset_index()

    # Merge population
    summary = pd.merge(district_summary, district_pop, on=["state", "district"], how="left")

    # Saturation
    summary["population"] = pd.to_numeric(summary.get("population", 0), errors="coerce").fillna(0)
    summary["saturation"] = np.where(summary["population"] > 0,
                                     (summary["total_enrolment"] / summary["population"]),
                                     np.nan)

    # Build pincode-level data for map
    pincode_agg = master.groupby(["state", "district", "pincode"]).agg({
        "total_enrolment": "sum",
        "age_0_5": "sum",
        "age_5_17": "sum",
        "age_18_greater": "sum"
    }).reset_index()
    
    # Merge population at pincode level
    if not pop_df.empty:
        pincode_agg = pd.merge(pincode_agg, pop_df, on="pincode", how="left")
        pincode_agg["population"] = pincode_agg["population"].fillna(0)
    else:
        pincode_agg["population"] = 0

    # National metrics
    total_bio = master.get("bio_age_5_17", pd.Series(dtype=float)).sum() if "bio_age_5_17" in master.columns else 0
    total_demo = master.get("demo_age_17_", pd.Series(dtype=float)).sum() if "demo_age_17_" in master.columns else 0
    
    national = {
        "states": int(master["state"].nunique()),
        "districts": int(master["district"].nunique()),
        "pincodes": int(master["pincode"].nunique()),
        "total_enrolments": float(master["total_enrolment"].sum()),
        "biometric_updates": float(total_bio),
        "demographic_updates": float(total_demo),
        "age_0_5": float(master["age_0_5"].sum()),
        "age_5_17": float(master["age_5_17"].sum()),
        "age_18_greater": float(master["age_18_greater"].sum()),
    }

    # Build per-state payload
    states_payload = {}
    for state, g in summary.groupby("state"):
        state_pincodes = pincode_agg[pincode_agg["state"] == state]
        
        # KPIs
        st_total_ops = float(g["total_enrolment"].sum())
        if "demo_age_17_" in g.columns:
            st_total_ops += float(g["demo_age_17_"].sum())
        
        st_population = float(g["population"].sum()) if "population" in g.columns else 0.0
        
        # Safe average saturation
        if "saturation" in g.columns:
            sat_vals = pd.to_numeric(g["saturation"], errors="coerce").dropna()
            st_avg_sat = float(sat_vals.mean()) if len(sat_vals) > 0 else None
        else:
            st_avg_sat = None
        
        # Risk districts calculation
        if "bio_age_5_17" in g.columns and "demo_age_5_17" in g.columns:
            st_risk = int((g["bio_age_5_17"] < g["demo_age_5_17"]).sum())
        else:
            st_risk = 0

        # Top saturation districts
        top_sat = (
            g.sort_values("saturation", ascending=False)
             .head(10)[["district", "saturation"]]
             .dropna()
             .to_dict(orient="records")
        )
        
        # Compliance gap
        comp_cols = ["district"]
        if "demo_age_5_17" in g.columns:
            comp_cols.append("demo_age_5_17")
        if "bio_age_5_17" in g.columns:
            comp_cols.append("bio_age_5_17")
        
        if len(comp_cols) > 1:
            comp = (
                g.sort_values("bio_age_5_17" if "bio_age_5_17" in g.columns else "total_enrolment", ascending=True)
                 .head(10)[comp_cols]
                 .fillna(0)
                 .to_dict(orient="records")
            )
        else:
            comp = []
        
        # Pincode level data for this state (limit to avoid huge JSON)
        pincode_data = state_pincodes.head(500).to_dict(orient="records")

        states_payload[state] = {
            "metrics": {
                "total_ops": st_total_ops,
                "avg_saturation": st_avg_sat,
                "risk_districts": st_risk,
                "age_0_5": float(g["age_0_5"].sum()),
                "youth": float(g["age_5_17"].sum()),
                "adults": float(g["age_18_greater"].sum()),
                "bio_updates": float(g["bio_age_5_17"].sum()) if "bio_age_5_17" in g.columns else 0.0,
                "demo_updates": float(g["demo_age_5_17"].sum()) if "demo_age_5_17" in g.columns else 0.0,
                "districts": int(g["district"].nunique()),
                "pincodes": int(master[master["state"] == state]["pincode"].nunique()),
                "population": st_population,
            },
            "top_saturation": top_sat,
            "compliance": comp,
            "pincode_data": pincode_data,
        }

    return {"national": national, "states": states_payload}


def main():
    master = build_master()
    pop_df = build_population()
    payload = compute_summaries(master, pop_df)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Wrote stats to {OUT_JSON}")
    print(f"National: {payload['national']}")
    print(f"States: {len(payload['states'])} states processed")


if __name__ == "__main__":
    main()
