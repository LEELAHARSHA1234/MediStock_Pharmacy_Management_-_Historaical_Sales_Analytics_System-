# MediStock – Pharmacy Inventory & Sales Management System

A professional, responsive Flask web application inspired by the MediStock dashboard reference image.

## Features
- Dashboard with revenue, low-stock, expiring-soon and today's sales KPI cards.
- Sales chart, stock-by-category visualization, low-stock/expiry table and recent transactions.
- Medicine inventory: add, edit, delete and search medicines.
- Sales entry: records a sale and automatically reduces stock.
- Purchases: records incoming stock and automatically increases stock.
- Supplier directory.
- Date-filtered sales reports and CSV exports.
- Expiry and reorder-level alerts.
- Local SQLite database; sample data is created automatically on first run.

## Technology
Python, Flask, SQLite, HTML, CSS and built-in Python CSV support. No Pandas, PyArrow, Streamlit or Matplotlib dependency.

## Windows 11 setup (VS Code / PowerShell)
1. Extract `MediStock_Pharmacy_System.zip`.
2. Open the extracted `MediStock_Pharmacy_System` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:
   ```powershell
   py -3.11 -m venv .venv
   ```
   If Python 3.11 is not installed, use an approved Python version available on your laptop, for example `py -3 -m venv .venv`.
5. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
6. Install Flask:
   ```powershell
   python -m pip install -r requirements.txt
   ```
7. Run:
   ```powershell
   python app.py
   ```
8. Open `http://127.0.0.1:5000` in your browser.

If PowerShell blocks virtual-environment activation, use:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Historical analytics dataset
- The `data/filtered_dataset.csv` file is the selected 28,009-row Pharmacy/Retail historical dataset supplied for this project.
- Open **Historical Analytics** in the sidebar to view interactive year, medicine-class and city filters, annual/monthly sales charts, a medicine-class pie chart, top products/distributors and data-quality checks.
- Historical CSV analytics are kept separate from live/demo SQLite inventory and sales records. The source currency is unspecified, so analytics values are shown without a currency symbol.
- See `DATASET_ANALYSIS.md` for the comparison of all three supplied CSV datasets and the reasons for selecting this one.

## Data
On first run, the app creates `data/medistock.db` and inserts fictional demonstration records. The database persists between runs. Keep a backup before deleting it. CSV downloads are available from Inventory and Sales/Reports.

## Important limitations
- The included records are fictional sample data for a college demonstration.
- This is an educational inventory and sales demo, not a validated pharmacy, prescription, clinical, tax or accounting system.
- Expiry alerts use the entered expiry date; always verify actual batch information.
- There is no login/authentication. Do not expose this local demo to the public internet or store real customer/patient information.
- Dashboard sample chart uses recorded transactions; the purchases list is available in the Purchases section.
