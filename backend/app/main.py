import polars as pl
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from attribution.service import run_analysis, AnalysisError
from attribution.file_reader import read_tabular_file, FileReadError
from app.schemas import AnalyzeResponse

app = FastAPI(title="Attribyt API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


async def _read_upload(file: UploadFile) -> pl.DataFrame:
    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 100MB).")
    try:
        return read_tabular_file(raw_bytes, file.filename or "")
    except FileReadError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/preview")
async def preview(file: UploadFile):
    df = await _read_upload(file)
    return {"headers": df.columns}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile,
    model: str = Form("both"),
    user_col: str = Form("user_id"),
    timestamp_col: str = Form("timestamp"),
    channel_col: str = Form("channel"),
    revenue_col: str = Form("revenue"),
    segment_col: str | None = Form(None),
    start_date: str | None = Form(None),
    end_date: str | None = Form(None),
):
    df = await _read_upload(file)

    config = {
        "source": "csv",
        "model": model,
        "user_col": user_col,
        "timestamp_col": timestamp_col,
        "channel_col": channel_col,
        "revenue_col": revenue_col,
        "segment_col": segment_col or None,
        "start_date": start_date,
        "end_date": end_date,
    }

    try:
        result = run_analysis(config, raw_df=df)
    except AnalysisError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return result 