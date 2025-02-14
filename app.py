from flask import Flask, Response, send_file, render_template_string
import pandas as pd
import io
import requests
from fpdf import FPDF
from typing import Optional
import logging
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1udZCCmDPq-RXW1jdNnHLrH_at-4hMUbvpZ0IUQZxIRg/gviz/tq?tqx=out:csv"
CACHE_DURATION = 300  # 5 minutes cache

# Global variables
_data_cache = None
_last_fetch_time = None

def fetch_data() -> Optional[pd.DataFrame]:
    """
    Fetch data from Google Sheets with Hebrew encoding and caching
    
    Returns:
        Optional[pd.DataFrame]: DataFrame containing the data or None if fetch fails
    """
    global _data_cache, _last_fetch_time
    
    # Check cache
    if _data_cache is not None and _last_fetch_time is not None:
        if (datetime.now() - _last_fetch_time).seconds < CACHE_DURATION:
            return _data_cache

    try:
        response = requests.get(GOOGLE_SHEETS_URL, timeout=10)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text), encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        
        # Update cache
        _data_cache = df
        _last_fetch_time = datetime.now()
        
        logger.info("Data fetched successfully")
        return df
    
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return None

def create_html_response(content: str) -> Response:
    """Create an HTML response with proper Hebrew encoding"""
    return Response(content, content_type="text/html; charset=utf-8")

@app.route('/')
def home():
    """Home page route"""
    html_content = """<!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>מערכת הצבעות</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                text-align: right;
            }
            .button {
                display: inline-block;
                padding: 10px 20px;
                margin: 10px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
            }
            .button:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <h1>✅ מערכת ההצבעות פעילה!</h1>
        <div>
            <a href="/stats" class="button">צפייה בסטטיסטיקות</a>
            <a href="/stats-ma" class="button">צפייה בסטטיסטיקות מפורטות</a>
        </div>
    </body>
    </html>"""
    return create_html_response(html_content)

@app.route('/user/<user_id>')
def user_data(user_id: str):
    """User data route showing voting statistics for a specific user"""
    df = fetch_data()
    if df is None:
        return create_html_response("⚠️ שגיאה בטעינת הנתונים."), 500

    user_df = df[df['user_id'].astype(str) == user_id]
    if user_df.empty:
        return create_html_response("⚠️ לא נמצאו נתונים למשתמש זה."), 404

    # Calculate statistics
    voted_yes = (user_df['Vote'].str.strip().str.lower() == "yes").sum()
    voted_no = (user_df['Vote'].str.strip().str.lower() == "no").sum()
    
    # Get non-voters data
    non_voters = user_df[
        (user_df['Vote'].str.strip().str.lower() == "no")
    ][['ID', 'Last_Name', 'First_Name', 'Phone', 'City', 'Branch']]

    html_content = f"""<!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>נתוני משתמש {user_id}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                text-align: right;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: right;
            }}
            th {{
                background-color: #f5f5f5;
            }}
            .stats {{
                display: flex;
                gap: 20px;
                margin: 20px 0;
            }}
            .stat-box {{
                padding: 15px;
                border-radius: 5px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }}
            .back-link {{
                display: inline-block;
                margin-top: 20px;
                color: #007bff;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <h2>🔍 נתוני משתמש {user_id}</h2>
        <div class="stats">
            <div class="stat-box">
                <h3>✅ הצביעו</h3>
                <p>{voted_yes}</p>
            </div>
            <div class="stat-box">
                <h3>❌ לא הצביעו</h3>
                <p>{voted_no}</p>
            </div>
        </div>
        <h3>📋 רשימת המשתמשים שטרם הצביעו</h3>
        {non_voters.to_html(index=False)}
        <a href="/" class="back-link">← חזרה לדף הבית</a>
    </body>
    </html>"""
    
    return create_html_response(html_content)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return create_html_response("⚠️ הדף המבוקש לא נמצא."), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return create_html_response("⚠️ שגיאת שרת פנימית."), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=False)