from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import analyzer

app = FastAPI(title="RepoSense AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    repo_path: str

@app.post("/api/scan")
def scan_repository(payload: ScanRequest):
    path = payload.repo_path.strip()
    try:
        # 1. Scan directory for files
        files = analyzer.scan_directory(path)
        
        # 2. Get language breakdown
        lang_data = analyzer.language_breakdown(files)
        
        # 3. Check onboarding files
        onboarding_data = analyzer.check_onboarding_files(path)
        
        # 4. Security & Quality scan
        security_data = analyzer.security_quality_scan(files)
        
        # Convert DataFrames to dict/json serializable format if needed
        # (Handling summary_df and findings_df so FastAPI can send them as JSON)
        summary_df = lang_data.get("summary")
        lang_summary = summary_df.to_dict(orient="records") if hasattr(summary_df, "to_dict") else []
        
        findings_df = security_data.get("findings")
        findings_list = findings_df.to_dict(orient="records") if hasattr(findings_df, "to_dict") else []

        return {
            "status": "success",
            "data": {
                "totals": lang_data.get("totals", {}),
                "language_summary": lang_summary,
                "onboarding": onboarding_data,
                "security_stats": security_data.get("stats", {}),
                "security_findings": findings_list
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        