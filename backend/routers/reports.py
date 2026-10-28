"""Reporting and Data Export Router for IRRIGATEWISE.

Provides live aggregated statistics, water consumption audits,
and dynamic CSV downloads for soil and irrigation datasets.
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Response
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from database import get_db
from services.report_generator import ReportGenerator

router = APIRouter(prefix="/reports", tags=["Reports & Export"])

@router.get("/summary")
def get_reports_summary(db: Session = Depends(get_db)):
    """Returns aggregated metrics for soil health, water conservation, and ML activity."""
    return ReportGenerator.generate_comprehensive_summary(db)

@router.get("/export/soil-csv")
def export_soil_csv(db: Session = Depends(get_db)):
    """Exports all soil records in CSV format."""
    csv_content = ReportGenerator.generate_soil_report_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=irrigatewise_soil_records.csv"}
    )

@router.get("/export/irrigation-csv")
def export_irrigation_csv(db: Session = Depends(get_db)):
    """Exports all irrigation records in CSV format."""
    csv_content = ReportGenerator.generate_irrigation_report_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=irrigatewise_irrigation_records.csv"}
    )
