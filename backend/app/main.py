import io
import polars as pl
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from attribution.service import run_analysis, AnalysisError
from app.schemas import AnalyzeRequest, AnalyzeResponse

app = FastAPI(title="Attribyt API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile,
    model: str = Form("both"),
    user_col: str = Form("user_id"),
    timestamp_col: str = Form("timestamp"),
    channel_col: str = Form("channel"),
    event_col: str = Form("event_type"),
    revenue_col: str = Form("revenue"),
    start_date: str | None = Form(None),
    end_date: str | None = Form(None),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported right now.")

    raw_bytes = await file.read()
    max_size = 50 * 1024 * 1024  # 50MB guard against accidental huge uploads
    if len(raw_bytes) > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 50MB).")

    try:
        df = pl.read_csv(io.BytesIO(raw_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    config = {
        "source": "csv",
        "model": model,
        "user_col": user_col,
        "timestamp_col": timestamp_col,
        "channel_col": channel_col,
        "event_col": event_col,
        "revenue_col": revenue_col,
        "start_date": start_date,
        "end_date": end_date,
    }

    try:
        result = run_analysis(config, raw_df=df)
    except AnalysisError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return result
