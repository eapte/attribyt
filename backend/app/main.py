from datetime import datetime

import polars as pl
from fastapi import FastAPI, UploadFile, Form, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from attribution.service import run_analysis, AnalysisError
from attribution.file_reader import read_tabular_file, FileReadError
from app.schemas import AnalyzeResponse
from sources.models import Source, SourceType
from sources.schemas import SourceCreate, SourceResponse, SourceAnalyzeRequest
from sources.service import SourceService
from sources.testers import test_database, test_rest_api, test_webhook
from sources.sync import sync_database, sync_rest_api, SyncError
from sources.seed_test_db import seed_test_db
from sources.summary import compute_summary, SummaryError

app = FastAPI(title="Attribyt API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

seed_test_db()
source_service = SourceService()
sources_router = APIRouter(prefix="/api/sources", tags=["sources"])


# NOTE: static-path routes like /activity/recent must be declared before
# dynamic routes like /{source_id} — otherwise FastAPI would try to match
# "activity" as a source_id.

@sources_router.get("/activity/recent")
def get_recent_activity():
    """Returns a simple activity feed of recent source syncs."""
    return {"events": source_service.get_recent_activity()}


@sources_router.get("", response_model=list[SourceResponse])
def list_sources():
    """Return all connected sources."""
    return [SourceResponse(**s.to_dict()) for s in source_service.list_sources()]


@sources_router.post("", response_model=SourceResponse)
def create_source(payload: SourceCreate):
    """Register a new source and immediately test the connection."""
    source = Source(
        type=payload.type,
        name=payload.name,
        credentials=payload.credentials,
        sync_mode=payload.sync_mode,
    )

    if payload.type == SourceType.DATABASE:
        status, error = test_database(payload.credentials)
    elif payload.type == SourceType.REST_API:
        status, error = test_rest_api(payload.credentials)
    else:
        status, error = test_webhook(payload.credentials)

    source.status = status
    source.last_error = error

    source_service.create_source(source)
    return SourceResponse(**source.to_dict())


@sources_router.delete("/{source_id}")
def delete_source(source_id: str):
    """Remove a source by id."""
    if not source_service.delete_source(source_id):
        raise HTTPException(status_code=404, detail="Source not found")
    return {"ok": True}


@sources_router.post("/{source_id}/sync")
def sync_source(source_id: str):
    """Manually trigger a sync for a source and store the resulting rows.
    Supported for Database and REST API sources. Webhooks can't be pulled
    on demand — they push data to us, which isn't implemented yet."""
    source = source_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    try:
        if source.type == SourceType.DATABASE:
            rows = sync_database(source.credentials)
        elif source.type == SourceType.REST_API:
            rows = sync_rest_api(source.credentials)
        else:
            raise HTTPException(
                status_code=400,
                detail="Webhooks can't be synced on demand — they push data to Attribyt, which isn't implemented yet.",
            )
    except SyncError as e:
        raise HTTPException(status_code=422, detail=str(e))

    source_service.save_synced_rows(source_id, rows)
    now = datetime.utcnow().isoformat()
    source_service.update_last_sync(source_id, now)

    return {"synced_rows": len(rows), "last_sync": now}


@sources_router.get("/{source_id}/data")
def get_source_data(source_id: str):
    """Return the rows last synced from a source."""
    source = source_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"rows": source_service.get_synced_rows(source_id)}


@sources_router.get("/{source_id}/columns")
def get_source_columns(source_id: str):
    """Returns the real column names found in a source's last synced rows,
    so the frontend can offer a mapping step — the same way file uploads
    do — instead of assuming fixed column names."""
    source = source_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    rows = source_service.get_synced_rows(source_id)
    if not rows:
        raise HTTPException(status_code=400, detail="No synced data yet — run Sync first.")

    return {"columns": list(rows[0].keys())}


@sources_router.get("/{source_id}/flow")
def get_source_flow(source_id: str):
    """Returns simple funnel-style counts derived from a source's synced
    rows: total events, unique users, and conversions (rows with revenue > 0).
    Uses best-effort column guesses (user_id/revenue) since this endpoint
    runs before any explicit column mapping is chosen."""
    source = source_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    rows = source_service.get_synced_rows(source_id)
    if not rows:
        return {"total_rows": 0, "unique_users": 0, "conversions": 0}

    unique_users = len({r.get("user_id") for r in rows if r.get("user_id")})
    conversions = sum(1 for r in rows if float(r.get("revenue", 0) or 0) > 0)

    return {
        "total_rows": len(rows),
        "unique_users": unique_users,
        "conversions": conversions,
    }

@sources_router.get("/{source_id}/summary")
def get_source_summary(source_id: str):
    """Returns an auto-aggregated summary (revenue, orders, conversion
    rate, channel breakdown, daily timeline) using best-effort column
    guessing. Returns available=False with a clear reason if columns
    can't be confidently guessed — Home should never show fabricated
    numbers."""
    source = source_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    rows = source_service.get_synced_rows(source_id)
    try:
        data = compute_summary(rows)
    except SummaryError as e:
        return {"available": False, "reason": str(e)}

    return {"available": True, **data}


@sources_router.post("/{source_id}/analyze", response_model=AnalyzeResponse)
def analyze_source(source_id: str, mapping: SourceAnalyzeRequest):
    """Run attribution analysis on a source's last synced rows, using an
    explicit column mapping supplied by the frontend — mirrors how file
    uploads work, since a source's raw column names rarely match
    Attribyt's standard names (user_id/timestamp/channel/revenue)."""
    source = source_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    rows = source_service.get_synced_rows(source_id)
    if not rows:
        raise HTTPException(status_code=400, detail="No synced data yet — run Sync first.")

    df = pl.DataFrame(rows)

    rename_map = {
        mapping.user_col: "user_id",
        mapping.timestamp_col: "timestamp",
        mapping.channel_col: "channel",
        mapping.revenue_col: "revenue",
    }
    missing = [src for src in rename_map if src not in df.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Mapped column(s) not found in synced data: {', '.join(missing)}",
        )

    df = df.rename(rename_map)

    config = {
        "source": source.type.value,
        "model": "both",
        "user_col": "user_id",
        "timestamp_col": "timestamp",
        "channel_col": "channel",
        "revenue_col": "revenue",
        "segment_col": mapping.segment_col,
        "start_date": None,
        "end_date": None,
    }

    try:
        result = run_analysis(config, raw_df=df)
    except AnalysisError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return result


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


app.include_router(sources_router) 