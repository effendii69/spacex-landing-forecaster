# backend/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import joblib
import pandas as pd
from pathlib import Path
import backend.live_api as live_api

app = FastAPI(title="SpaceX Falcon 9 Landing Forecaster")

backend_dir = Path(__file__).resolve().parent
base_dir = backend_dir.parent

# Load model and data with absolute paths to avoid CWD issues
model_path = backend_dir / "landing_model.pkl"
data_dir = base_dir / "data"
raw_data_path = data_dir / "spacex_landing_dataset.csv"
processed_data_path = data_dir / "spacex_processed.csv"


def load_history_dataframe() -> pd.DataFrame:
    """
    Load the processed dataset that contains the 'success' column.
    If the processed file is missing, fall back to the raw dataset,
    add the 'success' column from 'Class', save the processed file,
    and return a DataFrame guaranteed to have the needed columns.
    """
    df_local = None

    if processed_data_path.exists():
        try:
            df_local = pd.read_csv(processed_data_path)
        except Exception:
            df_local = None

    if df_local is None:
        if raw_data_path.exists():
            raw_df = pd.read_csv(raw_data_path)
            if "success" not in raw_df.columns:
                if "Class" in raw_df.columns:
                    raw_df = raw_df.copy()
                    raw_df["success"] = raw_df["Class"]
                else:
                    raw_df = raw_df.copy()
                    raw_df["success"] = None
            raw_df.to_csv(processed_data_path, index=False)
            df_local = raw_df
        else:
            df_local = pd.DataFrame()

    required_cols = ["FlightNumber", "Date", "PayloadMass", "Outcome", "success"]
    for col in required_cols:
        if col not in df_local.columns:
            df_local[col] = None

    return df_local


df = load_history_dataframe()
model = joblib.load(model_path)

frontend_dir = base_dir / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
async def root():
    return FileResponse(frontend_dir / "index.html")

@app.get("/api/history")
async def get_history():
    return df[['FlightNumber', 'Date', 'PayloadMass', 'Outcome', 'success']].to_dict(orient="records")

@app.get("/api/next")
async def next_prediction():
    return live_api.get_live_next_launch(model)

@app.get("/health")
async def health():
    return {"status": "nominal"}
