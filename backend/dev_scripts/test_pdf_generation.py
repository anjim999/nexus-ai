import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add backend directory to sys path
sys.path.append(os.getcwd())

from app.database.connection import get_db_session
from app.core.reports_generator import generate_pdf_report
from app.config import settings

async def test_pdf():
    print("Initializing report generation test...")
    print(f"Database URL: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print(f"Reports folder: {settings.REPORTS_DIR}")
    
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    
    async with get_db_session() as db:
        title = "Automated Test Performance Report"
        report_type = "weekly_analysis"
        time_range_days = 7
        include_ai_analysis = True
        
        print(f"Generating PDF for '{title}' (pacing includes AI call if active)...")
        try:
            pdf_bytes = await generate_pdf_report(
                title=title,
                report_type=report_type,
                time_range_days=time_range_days,
                include_ai_analysis=include_ai_analysis,
                db=db
            )
            
            output_path = os.path.join(settings.REPORTS_DIR, "test_run.pdf")
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
                
            print(f"SUCCESS: PDF Report generated successfully!")
            print(f"- Destination: {output_path}")
            print(f"- File size: {len(pdf_bytes) / 1024:.2f} KB")
            
        except Exception as e:
            print(f"FAILURE: PDF Report generation failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pdf())
