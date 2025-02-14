from flask import Flask, Response, send_file, render_template_string
import pandas as pd
import io
import requests
from fpdf import FPDF

app = Flask(__name__)

# 🔗 קישור לקובץ Google Sheets
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1udZCCmDPq-RXW1jdNnHLrH_at-4hMUbvpZ0IUQZxIRg/gviz/tq?tqx=out:csv"

# 🎯 רשימת הסניפים עבור סטטיסטיקה מסוננת
MA_BRANCHES = [
    "מא אל קסום", "מא אלונה", "מא באר טוביה", "מא בית שאן", "מא ברנר", "מא גדרות",
    "מא גולן", "מא גוש עציון", "מא גזר", "מא גליל עליון", "מא גליל תחתון", "מא דרום השרון",
    "מא הגלבוע", "מא הר חברון", "מא זבולון", "מא חבל יבנה", "מא חוף אשקלון", "מא חוף הכרמל",
    "מא חוף השרון", "מא לב השרון", "מא לכיש", "מא מבואות החרמון", "מא מגידו", "מא מודיעים",
    "מא מטה אשר", "מא מטה בנימין", "מא מטה יהודה", "מא מעלה יוסף", "מא מרום הגליל", 
    "מא מרחבים", "מא משגב", "מא נחל שורק", "מא עמק הירדן", "מא עמק חפר", "מא עמק יזרעאל",
    "מא ערבות הירדן", "מא שדות דן", "מא שדות נגב", "מא שומרון", "מא שפיר"
]

def fetch_data():
    """📥 שליפת הנתונים מגוגל שיטס עם קידוד עברית תקין"""
    response = requests.get(GOOGLE_SHEETS_URL)
    if response.status_code != 200:
        return None
    df = pd.read_csv(io.StringIO(response.text), encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    return df

@app.route('/')
def home():
    html_content = """<!DOCTYPE html>
    <html lang="he">
    <head>
        <meta charset="UTF-8">
        <title>מערכת הצבעות</title>
    </head>
    <body>
        <h1>✅ המערכת פועלת! לחץ על <a href="/stats">/stats</a> או <a href="/stats-ma">/stats-ma</a> לצפייה בנתונים</h1>
    </body>
    </html>"""
    return Response(html_content, content_type="text/html; charset=utf-8")

@app.route('/user/<user_id>')
def user_data(user_id):
    df = fetch_data()
    if df is None:
        return "⚠️ שגיאה בטעינת הנתונים.", 500

    user_df = df[df['user_id'].astype(str) == user_id]
    if user_df.empty:
        return "⚠️ לא נמצאו נתונים למשתמש זה.", 404

    voted_yes = (user_df['Vote'].str.strip().str.lower() == "yes").sum()
    voted_no = (user_df['Vote'].str.strip().str.lower() == "no").sum()

    filtered_df = user_df[user_df['Vote'].str.strip().str.lower() == "no"]
    filtered_df = filtered_df[['ID', 'Last_Name', 'First_Name', 'Phone', 'City', 'Branch']]

    html_content = f"""
    <!DOCTYPE html>
    <html lang="he">
    <head>
        <meta charset="UTF-8">
        <title>נת