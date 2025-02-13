from flask import Flask, render_template_string, send_file
import pandas as pd
import io
import requests
from fpdf import FPDF

app = Flask(__name__)

# 🔗 קישור לגוגל שיטס
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1udZCCmDPq-RXW1jdNnHLrH_at-4hMUbvpZ0IUQZxIRg/gviz/tq?tqx=out:csv"

def fetch_data():
    response = requests.get(GOOGLE_SHEETS_URL)
    if response.status_code != 200:
        return None
    df = pd.read_csv(io.StringIO(response.text), encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    return df

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

    return render_template_string("""
    <h2>🔍 נתוני משתמש {{ user_id }}</h2>
    <p>✅ הצביעו: {{ voted_yes }}</p>
    <p>❌ לא הצביעו: {{ voted_no }}</p>

    <h3>📋 רשימת המשתמשים שטרם הצביעו</h3>
    {{ table|safe }}

    <a href="/download/excel/{{ user_id }}" class="btn btn-success">⬇️ הורד כ-Excel</a>
    <a href="/download/pdf/{{ user_id }}" class="btn btn-danger">⬇️ הורד כ-PDF</a>
    """, table=filtered_df.to_html(index=False), user_id=user_id, voted_yes=voted_yes, voted_no=voted_no)

@app.route('/download/excel/<user_id>')
def download_excel(user_id):
    df = fetch_data()
    if df is None:
        return "⚠️ שגיאה בטעינת הנתונים.", 500

    filtered_df = df[(df['user_id'].astype(str) == user_id) & (df['Vote'].str.strip().str.lower() == "no")]
    filtered_df = filtered_df[['ID', 'Last_Name', 'First_Name', 'Phone', 'City', 'Branch']]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name="Users")

    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"user_{user_id}_data.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/download/pdf/<user_id>')
def download_pdf(user_id):
    df = fetch_data()
    if df is None:
        return "⚠️ שגיאה בטעינת הנתונים.", 500

    filtered_df = df[(df['user_id'].astype(str) == user_id) & (df['Vote'].str.strip().str.lower() == "no")]
    filtered_df = filtered_df[['ID', 'Last_Name', 'First_Name', 'Phone', 'City', 'Branch']]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"רשימת משתמשים שטרם הצביעו ({user_id})", ln=True, align='C')
    
    pdf.ln(10)
    for col in filtered_df.columns:
        pdf.cell(35, 10, col, border=1)
    pdf.ln()

    for _, row in filtered_df.iterrows():
        for col in filtered_df.columns:
            pdf.cell(35, 10, str(row[col]), border=1)
        pdf.ln()

    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"user_{user_id}_data.pdf", mimetype="application/pdf")

if __name__ == '__main__':
    app.run(debug=True)