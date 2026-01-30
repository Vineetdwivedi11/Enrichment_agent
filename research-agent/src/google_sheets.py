"""Google Sheets exporter for research data."""

from typing import Optional
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from .config import settings
from .models import ProspectResearch


class GoogleSheetsExporter:
    """Export research data to Google Sheets."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self):
        if not settings.GOOGLE_CREDENTIALS_PATH or not settings.GOOGLE_CREDENTIALS_PATH.exists():
            raise ValueError("Google credentials file not found")
        
        self.credentials = Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_PATH,
            scopes=self.SCOPES
        )
        self.client = gspread.authorize(self.credentials)
    
    def export_research(
        self, 
        research: ProspectResearch,
        sheet_name: Optional[str] = None
    ) -> str:
        """
        Export research data to Google Sheets.
        
        Args:
            research: ProspectResearch object
            sheet_name: Name for the spreadsheet (optional)
            
        Returns:
            URL of created spreadsheet
        """
        if not sheet_name:
            sheet_name = f"Research - {research.company_name} - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Create new spreadsheet
        spreadsheet = self.client.create(sheet_name)
        
        # Overview worksheet
        worksheet = spreadsheet.sheet1
        worksheet.update_title("Overview")
        
        # Prepare data rows
        rows = [
            ["Research Report", "", ""],
            ["Company Name", research.company_name, ""],
            ["Research Date", research.timestamp.strftime("%Y-%m-%d %H:%M:%S"), ""],
            ["", "", ""],
        ]
        
        if research.website_url:
            rows.append(["Website", research.website_url, ""])
        
        if research.linkedin_url:
            rows.append(["LinkedIn", research.linkedin_url, ""])
        
        rows.append(["", "", ""])
        
        # Website Data Section
        if research.website_data:
            rows.extend([
                ["WEBSITE DATA", "", ""],
                ["Title", research.website_data.title or "N/A", ""],
                ["Description", research.website_data.description or "N/A", ""],
                ["Content Preview", (research.website_data.content or "")[:500], ""],
                ["", "", ""]
            ])
        
        # LinkedIn Company Data Section
        if research.linkedin_company_data:
            company = research.linkedin_company_data
            rows.extend([
                ["LINKEDIN COMPANY DATA", "", ""],
                ["Company Name", company.name or "N/A", ""],
                ["Industry", company.industry or "N/A", ""],
                ["Company Size", company.company_size or "N/A", ""],
                ["Headquarters", company.headquarters or "N/A", ""],
                ["Founded", company.founded or "N/A", ""],
                ["Website", company.website or "N/A", ""],
                ["Employee Count", str(company.employee_count) if company.employee_count else "N/A", ""],
                ["Description", company.description or "N/A", ""],
                ["Specialties", ", ".join(company.specialties) if company.specialties else "N/A", ""],
                ["", "", ""]
            ])
        
        # Update worksheet with data
        worksheet.update("A1", rows)
        
        # LinkedIn Posts worksheet
        if research.linkedin_posts:
            posts_ws = spreadsheet.add_worksheet("LinkedIn Posts", rows=len(research.linkedin_posts) + 10, cols=5)
            
            post_rows = [
                ["Author", "Content Preview", "Likes", "Comments", "Published"]
            ]
            
            for post in research.linkedin_posts:
                post_rows.append([
                    post.author or "N/A",
                    (post.content or "")[:200],
                    post.engagement.get("likes", 0),
                    post.engagement.get("comments", 0),
                    post.published_at.strftime("%Y-%m-%d") if post.published_at else "N/A"
                ])
            
            posts_ws.update("A1", post_rows)
        
        # Format the sheet
        self._format_sheet(worksheet)
        
        return spreadsheet.url
    
    def _format_sheet(self, worksheet):
        """Apply basic formatting to worksheet."""
        # Format header row
        worksheet.format("A1:C1", {
            "backgroundColor": {
                "red": 0.2,
                "green": 0.5,
                "blue": 0.8
            },
            "textFormat": {
                "bold": True,
                "fontSize": 14
            }
        })
        
        # Auto-resize columns
        worksheet.columns_auto_resize(0, 2)
