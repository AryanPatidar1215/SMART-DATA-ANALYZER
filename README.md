# Smart Data Analyzer — Creative Dashboard

A beginner-friendly mini project using Python, Pandas, Streamlit, Plotly, SQLite SQL and Tableau.

## Run in VS Code on Windows
1. Extract this ZIP and open the `smart-data-analyzer` folder in VS Code.
2. Open Terminal → New Terminal.
3. Run:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. Open the local URL shown in terminal, usually `http://localhost:8501`.
5. Upload your Excel file or `sample_sales.csv`.

If PowerShell blocks activation, use Command Prompt terminal and run `.venv\Scripts\activate.bat`.

## Tableau
1. Upload a file on the website.
2. Download **Tableau-ready CSV**.
3. In Tableau Public/Desktop select **Connect → Text File** and select the CSV.
4. Build worksheets, then choose **Dashboard → New Dashboard**.
5. Tableau Public workbooks are public. Do not publish confidential data.

The website dashboard updates on upload. Tableau uses a separate workbook connection; automatically syncing every upload to a published Tableau dashboard is not included in this beginner version.
