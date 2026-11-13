from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3, csv, io
from pathlib import Path
from datetime import date, datetime, timedelta

BASE = Path(__file__).resolve().parent
DB = BASE / "data" / "medistock.db"
HISTORICAL_CSV = BASE / "data" / "filtered_dataset.csv"
app = Flask(__name__)
app.secret_key = "change-this-development-secret"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    DB.parent.mkdir(exist_ok=True)
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS medicines(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT NOT NULL,
          batch TEXT, expiry TEXT, quantity INTEGER NOT NULL DEFAULT 0,
          reorder_level INTEGER NOT NULL DEFAULT 10, cost REAL NOT NULL DEFAULT 0,
          price REAL NOT NULL DEFAULT 0, supplier TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS sales(
          id INTEGER PRIMARY KEY AUTOINCREMENT, medicine_id INTEGER, medicine_name TEXT NOT NULL,
          quantity INTEGER NOT NULL, unit_price REAL NOT NULL, total REAL NOT NULL,
          payment TEXT NOT NULL, sold_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS purchases(
          id INTEGER PRIMARY KEY AUTOINCREMENT, medicine_id INTEGER, medicine_name TEXT NOT NULL,
          quantity INTEGER NOT NULL, unit_cost REAL NOT NULL, total REAL NOT NULL,
          supplier TEXT, purchased_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS suppliers(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT, email TEXT
        );
        """)
        if con.execute("SELECT COUNT(*) FROM medicines").fetchone()[0] == 0:
            today = date.today()
            samples = [
             ("Amoxicillin 250mg","Antibiotics","AMX2401",(today+timedelta(days=180)).isoformat(),6,20,8.5,14,"HealthPlus"),
             ("Ibuprofen 400mg","Analgesics","IBU2402",(today+timedelta(days=240)).isoformat(),42,15,3.2,7,"MedSupply"),
             ("Paracetamol 500mg","Analgesics","PCM2403",(today+timedelta(days=310)).isoformat(),18,20,1.8,4,"HealthPlus"),
             ("ORS Sachets","Rehydration","ORS2404",(today+timedelta(days=25)).isoformat(),8,15,4,8,"CareSource"),
             ("Metformin 500mg","Antidiabetics","MET2405",(today+timedelta(days=420)).isoformat(),22,12,5,10,"MedSupply"),
             ("Vitamin D3 60K","Vitamins","VIT2406",(today+timedelta(days=12)).isoformat(),31,10,18,32,"WellnessCo"),
             ("Cetirizine 10mg","Antiallergics","CET2407",(today+timedelta(days=280)).isoformat(),55,15,2.5,6,"CareSource"),
             ("Azithromycin 500mg","Antibiotics","AZI2408",(today+timedelta(days=150)).isoformat(),14,10,12,22,"HealthPlus"),
             ("Cough Syrup 100ml","Cold & Cough","CSY2409",(today+timedelta(days=330)).isoformat(),26,10,22,38,"WellnessCo"),
             ("Calcium Tablets","Vitamins","CAL2410",(today+timedelta(days=500)).isoformat(),4,12,6,12,"MedSupply"),
             ("Pantoprazole 40mg","Gastro","PAN2411",(today+timedelta(days=210)).isoformat(),19,10,7,13,"CareSource"),
             ("Antiseptic Cream","First Aid","ANT2412",(today+timedelta(days=90)).isoformat(),13,8,15,27,"WellnessCo")]
            con.executemany("""INSERT INTO medicines(name,category,batch,expiry,quantity,reorder_level,cost,price,supplier)
                              VALUES(?,?,?,?,?,?,?,?,?)""", samples)
            con.executemany("INSERT INTO suppliers(name,phone,email) VALUES(?,?,?)", [
                ("HealthPlus","9876501234","orders@healthplus.example"),
                ("MedSupply","9876502345","sales@medsupply.example"),
                ("CareSource","9876503456","support@caresource.example"),
                ("WellnessCo","9876504567","hello@wellnessco.example")])
            meds = con.execute("SELECT id,name,price FROM medicines").fetchall()
            for i in range(18):
                m = meds[i % len(meds)]
                qty = (i % 4) + 1
                sold = (date.today() - timedelta(days=(17-i))).isoformat()
                con.execute("INSERT INTO sales(medicine_id,medicine_name,quantity,unit_price,total,payment,sold_at) VALUES(?,?,?,?,?,?,?)",
                            (m["id"],m["name"],qty,m["price"],qty*m["price"],["UPI","Cash","Card"][i%3],sold))
            for i in range(6):
                m = meds[i]
                con.execute("INSERT INTO purchases(medicine_id,medicine_name,quantity,unit_cost,total,supplier,purchased_at) VALUES(?,?,?,?,?,?,?)",
                            (m["id"],m["name"],20,8+i,20*(8+i),["HealthPlus","MedSupply","CareSource"][i%3],(date.today()-timedelta(days=20-i*2)).isoformat()))

def money(value):
    return "₹{:,.0f}".format(value or 0)

@app.context_processor
def inject_globals():
    return {"money": money, "today": date.today().isoformat()}

@app.route("/")
def dashboard():
    with db() as con:
        today = date.today().isoformat()
        month_start = date.today().replace(day=1).isoformat()
        total_rev = con.execute("SELECT COALESCE(SUM(total),0) FROM sales").fetchone()[0]
        today_rev = con.execute("SELECT COALESCE(SUM(total),0) FROM sales WHERE sold_at=?", (today,)).fetchone()[0]
        txns = con.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        low = con.execute("SELECT COUNT(*) FROM medicines WHERE quantity <= reorder_level").fetchone()[0]
        expiry = con.execute("SELECT COUNT(*) FROM medicines WHERE expiry BETWEEN ? AND ?",(today,(date.today()+timedelta(days=30)).isoformat())).fetchone()[0]
        stock_count = con.execute("SELECT COALESCE(SUM(quantity),0) FROM medicines").fetchone()[0]
        sales_days = con.execute("SELECT sold_at, SUM(total) total FROM sales WHERE sold_at >= ? GROUP BY sold_at ORDER BY sold_at",( (date.today()-timedelta(days=6)).isoformat(),)).fetchall()
        categories = con.execute("SELECT category, SUM(quantity) qty FROM medicines GROUP BY category ORDER BY qty DESC").fetchall()
        alerts = con.execute("""SELECT * FROM medicines WHERE quantity <= reorder_level OR expiry <= ?
                                ORDER BY CASE WHEN quantity <= reorder_level THEN 0 ELSE 1 END, expiry LIMIT 8""",
                             ((date.today()+timedelta(days=30)).isoformat(),)).fetchall()
        recent = con.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 6").fetchall()
        top = con.execute("SELECT medicine_name,SUM(quantity) qty FROM sales GROUP BY medicine_name ORDER BY qty DESC LIMIT 5").fetchall()
    max_sale = max([r["total"] for r in sales_days], default=1) or 1
    chart = [{"day": datetime.strptime(r["sold_at"],"%Y-%m-%d").strftime("%a"),"value":r["total"],"height":max(8,int(r["total"]/max_sale*100))} for r in sales_days]
    return render_template("dashboard.html", active="dashboard", total_rev=total_rev, today_rev=today_rev,
        txns=txns, low=low, expiry=expiry, stock_count=stock_count, chart=chart, categories=categories,
        alerts=alerts, recent=recent, top=top)

@app.route("/inventory", methods=["GET","POST"])
def inventory():
    if request.method == "POST":
        f=request.form
        try:
            vals=(f["name"].strip(),f["category"],f.get("batch",""),f.get("expiry",""),int(f["quantity"]),
                  int(f["reorder_level"]),float(f["cost"]),float(f["price"]),f.get("supplier",""))
            with db() as con:
                if f.get("id"):
                    con.execute("""UPDATE medicines SET name=?,category=?,batch=?,expiry=?,quantity=?,reorder_level=?,cost=?,price=?,supplier=? WHERE id=?""", vals+(int(f["id"]),))
                    flash("Medicine details updated.","success")
                else:
                    con.execute("""INSERT INTO medicines(name,category,batch,expiry,quantity,reorder_level,cost,price,supplier) VALUES(?,?,?,?,?,?,?,?,?)""", vals)
                    flash("Medicine added to inventory.","success")
        except (ValueError,KeyError):
            flash("Please check the medicine details and try again.","error")
        return redirect(url_for("inventory"))
    q=request.args.get("q","").strip()
    with db() as con:
        rows=con.execute("SELECT * FROM medicines WHERE name LIKE ? OR category LIKE ? OR batch LIKE ? ORDER BY name",
                         (f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
    return render_template("inventory.html",active="inventory",medicines=rows,q=q)

@app.route("/medicine/delete/<int:mid>", methods=["POST"])
def delete_medicine(mid):
    with db() as con: con.execute("DELETE FROM medicines WHERE id=?",(mid,))
    flash("Medicine removed.","success")
    return redirect(url_for("inventory"))

@app.route("/sales", methods=["GET","POST"])
def sales():
    if request.method=="POST":
        f=request.form
        try:
            mid=int(f["medicine_id"]); qty=int(f["quantity"])
            with db() as con:
                m=con.execute("SELECT * FROM medicines WHERE id=?",(mid,)).fetchone()
                if not m or qty<1: raise ValueError()
                if qty>m["quantity"]:
                    flash("Not enough stock available for this sale.","error")
                else:
                    total=qty*m["price"]
                    con.execute("INSERT INTO sales(medicine_id,medicine_name,quantity,unit_price,total,payment,sold_at) VALUES(?,?,?,?,?,?,?)",
                                (mid,m["name"],qty,m["price"],total,f["payment"],date.today().isoformat()))
                    con.execute("UPDATE medicines SET quantity=quantity-? WHERE id=?",(qty,mid))
                    flash("Sale recorded and inventory updated.","success")
        except (ValueError,KeyError):
            flash("Please select a medicine and enter a valid quantity.","error")
        return redirect(url_for("sales"))
    with db() as con:
        meds=con.execute("SELECT * FROM medicines WHERE quantity>0 ORDER BY name").fetchall()
        rows=con.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 50").fetchall()
    return render_template("sales.html",active="sales",medicines=meds,sales=rows)

@app.route("/purchases", methods=["GET","POST"])
def purchases():
    if request.method=="POST":
        f=request.form
        try:
            mid=int(f["medicine_id"]); qty=int(f["quantity"]); cost=float(f["unit_cost"])
            with db() as con:
                m=con.execute("SELECT * FROM medicines WHERE id=?",(mid,)).fetchone()
                if not m or qty<1 or cost<0: raise ValueError()
                con.execute("INSERT INTO purchases(medicine_id,medicine_name,quantity,unit_cost,total,supplier,purchased_at) VALUES(?,?,?,?,?,?,?)",
                            (mid,m["name"],qty,cost,qty*cost,f.get("supplier",""),date.today().isoformat()))
                con.execute("UPDATE medicines SET quantity=quantity+?,cost=? WHERE id=?",(qty,cost,mid))
            flash("Purchase recorded and stock increased.","success")
        except (ValueError,KeyError):
            flash("Enter valid purchase details.","error")
        return redirect(url_for("purchases"))
    with db() as con:
        meds=con.execute("SELECT * FROM medicines ORDER BY name").fetchall()
        rows=con.execute("SELECT * FROM purchases ORDER BY id DESC LIMIT 50").fetchall()
        suppliers=con.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    return render_template("purchases.html",active="purchases",medicines=meds,purchases=rows,suppliers=suppliers)

@app.route("/suppliers", methods=["GET","POST"])
def suppliers():
    if request.method=="POST":
        f=request.form
        if f.get("name","").strip():
            with db() as con: con.execute("INSERT INTO suppliers(name,phone,email) VALUES(?,?,?)",(f["name"].strip(),f.get("phone",""),f.get("email","")))
            flash("Supplier added.","success")
        return redirect(url_for("suppliers"))
    with db() as con: rows=con.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    return render_template("suppliers.html",active="suppliers",suppliers=rows)

@app.route("/reports")
def reports():
    start=request.args.get("start",(date.today()-timedelta(days=30)).isoformat())
    end=request.args.get("end",date.today().isoformat())
    with db() as con:
        sales_rows=con.execute("SELECT * FROM sales WHERE sold_at BETWEEN ? AND ? ORDER BY sold_at DESC",(start,end)).fetchall()
        rev=sum(r["total"] for r in sales_rows)
        qty=sum(r["quantity"] for r in sales_rows)
        pay=con.execute("SELECT payment,SUM(total) total FROM sales WHERE sold_at BETWEEN ? AND ? GROUP BY payment",(start,end)).fetchall()
    return render_template("reports.html",active="reports",rows=sales_rows,start=start,end=end,rev=rev,qty=qty,pay=pay)

@app.route("/export/<kind>.csv")
def export_csv(kind):
    with db() as con:
        if kind=="inventory":
            rows=con.execute("SELECT id,name,category,batch,expiry,quantity,reorder_level,cost,price,supplier FROM medicines").fetchall()
            headers=["ID","Medicine","Category","Batch","Expiry","Quantity","Reorder level","Cost","Price","Supplier"]
        else:
            rows=con.execute("SELECT id,medicine_name,quantity,unit_price,total,payment,sold_at FROM sales ORDER BY sold_at DESC").fetchall()
            headers=["ID","Medicine","Quantity","Unit price","Total","Payment","Date"]
    out=io.StringIO(); writer=csv.writer(out); writer.writerow(headers)
    for r in rows: writer.writerow(list(r))
    return Response("\\ufeff"+out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":f"attachment; filename=medistock_{kind}.csv"})


def load_historical_rows():
    """Load the selected real-world historical pharmacy-retail dataset."""
    rows = []
    if not HISTORICAL_CSV.exists():
        return rows
    with HISTORICAL_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                row["Quantity"] = float(row.get("Quantity") or 0)
                row["Price"] = float(row.get("Price") or 0)
                row["Sales"] = float(row.get("Sales") or 0)
                row["Year"] = int(float(row.get("Year") or 0))
            except (TypeError, ValueError):
                continue
            rows.append(row)
    return rows

def compact_number(value):
    value = float(value or 0)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f}K"
    return f"{value:,.0f}"

@app.route("/analytics")
def analytics():
    all_rows = load_historical_rows()
    years = sorted({r["Year"] for r in all_rows})
    classes = sorted({r.get("Product Class", "Unknown") for r in all_rows})
    cities = sorted({r.get("City", "Unknown") for r in all_rows})
    selected_year = request.args.get("year", "all")
    selected_class = request.args.get("product_class", "all")
    selected_city = request.args.get("city", "all")

    rows = [r for r in all_rows
            if (selected_year == "all" or str(r["Year"]) == selected_year)
            and (selected_class == "all" or r.get("Product Class") == selected_class)
            and (selected_city == "all" or r.get("City") == selected_city)]

    total_sales = sum(r["Sales"] for r in rows)
    total_units = sum(r["Quantity"] for r in rows)
    transactions = len(rows)
    avg_sale = total_sales / transactions if transactions else 0

    def aggregate(key):
        result = {}
        for r in rows:
            label = r.get(key) or "Unknown"
            result[label] = result.get(label, 0) + r["Sales"]
        return result

    class_totals = sorted(aggregate("Product Class").items(), key=lambda x: x[1], reverse=True)
    year_totals = sorted(aggregate("Year").items(), key=lambda x: int(x[0]))
    month_order = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]
    month_map = aggregate("Month")
    month_totals = [(m, month_map.get(m, 0)) for m in month_order if m in month_map]
    product_totals = sorted(aggregate("Product Name").items(), key=lambda x: x[1], reverse=True)[:8]
    distributor_totals = sorted(aggregate("Distributor").items(), key=lambda x: x[1], reverse=True)[:8]

    palette = ["#2563eb","#14b8a6","#f59e0b","#8b5cf6","#ef4444","#64748b"]
    pie_parts, cumulative = [], 0.0
    for i, (label, value) in enumerate(class_totals):
        pct = (value / total_sales * 100) if total_sales else 0
        end = cumulative + max(0, pct)
        pie_parts.append(f"{palette[i % len(palette)]} {cumulative:.3f}% {end:.3f}%")
        cumulative = end
    pie_gradient = "conic-gradient(" + ", ".join(pie_parts) + ")" if pie_parts else "conic-gradient(#e5e7eb 0 100%)"

    max_year = max([v for _, v in year_totals], default=1) or 1
    year_chart = [{"label": str(k), "value": v, "width": max(2, v/max_year*100)} for k,v in year_totals]
    max_month = max([v for _, v in month_totals], default=1) or 1
    month_chart = [{"label": k[:3], "value": v, "height": max(3, v/max_month*100)} for k,v in month_totals]
    max_product = max([v for _,v in product_totals], default=1) or 1
    product_chart = [{"label":k, "value":v, "width":max(2,v/max_product*100)} for k,v in product_totals]

    # Data-quality indicators are calculated from the source file, not just filtered rows.
    source_rows = all_rows
    negative_sales = sum(1 for r in source_rows if r["Sales"] < 0)
    negative_qty = sum(1 for r in source_rows if r["Quantity"] < 0)
    with HISTORICAL_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        raw = list(csv.DictReader(handle))
    duplicate_rows = len(raw) - len({tuple(sorted(x.items())) for x in raw})

    return render_template("analytics.html", active="analytics", years=years, classes=classes,
        cities=cities, selected_year=selected_year, selected_class=selected_class,
        selected_city=selected_city, total_sales=total_sales, total_units=total_units,
        transactions=transactions, avg_sale=avg_sale, class_totals=class_totals,
        pie_gradient=pie_gradient, year_chart=year_chart, month_chart=month_chart,
        product_chart=product_chart, distributor_totals=distributor_totals,
        compact_number=compact_number, negative_sales=negative_sales,
        negative_qty=negative_qty, duplicate_rows=duplicate_rows, source_count=len(all_rows))

@app.route("/settings")
def settings():
    return render_template("settings.html",active="settings")

if __name__ == "__main__":
    init_db()
    print("MediStock is running at http://127.0.0.1:5000")
    app.run(debug=True)
