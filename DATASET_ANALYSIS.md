# MediStock dataset comparison and analytics notes

## Final selection: `data/filtered_dataset.csv`

The project now loads this CSV in the new **Historical Analytics** page (`/analytics`). It is not merely copied into the folder: the Flask route reads its rows and computes the KPIs, filters, bar charts, monthly chart, product/distributor rankings, and medicine-class pie chart at request time.

### Comparison of the three supplied CSV files

| Dataset | Rows | Columns | What it contains | Assessment |
|---|---:|---:|---|---|
| `pharmacy_sales_data.csv` | 10 | 20 | Pharmacy/store transactions, product/batch/expiry, stock, units sold, date, store and manufacturer | Useful schema example, but only 10 records; too small for meaningful trends |
| `pharma-data.csv` | 254,082 | 18 | Multiple channels including Pharmacy and Hospital, 4 years (2017–2020), 751 customers, 29 distributors, 240 products | Largest and richest dataset, but mixes business channels and geographies |
| `filtered_dataset.csv` | 28,009 | 13 | Pharmacy channel only; Germany; Retail sub-channel; 2019–2020; 150 customers, 11 distributors, 240 products, 6 product classes | Best fit for a pharmacy-retail sales analytics module |

### Selected dataset profile

- Rows: 28,009
- Columns: 13
- Years: 2019 and 2020
- Country: Germany
- Channel/sub-channel: Pharmacy / Retail
- Distinct products: 240
- Distinct customers: 150
- Distinct distributors: 11
- Distinct product classes: 6
- Missing cells: 0
- Exact duplicate rows: 15
- Negative quantity rows: 443
- Negative sales rows: 443
- Total net sales value in source units: 1,621,568,636.28
- 2019 sales: 820,737,683.28
- 2020 sales: 800,830,953.00

Negative quantity/sales rows are retained. They may represent returns or credit adjustments; deleting them would inflate net sales. The source does not declare a currency, so the analytics page deliberately avoids adding a currency symbol or treating these values as INR.

### Key findings from the selected dataset

- 2019 sales exceed 2020 sales by approximately 2.43%.
- Analgesics have the highest aggregate sales value among the six classes (372,951,223.41 source units).
- August has the highest aggregate month-of-year sales value in the combined two-year dataset (266,433,736.00).
- The top city by aggregate sales is Butzbach (79,042,794.00).
- The dataset is historical and should not be presented as live stock or current transactions.

### Integration design

- Existing SQLite tables and pharmacy operations remain unchanged.
- Historical data is kept separate from the local SQLite demo records because the CSV has a different schema and represents a different time period/market.
- `/analytics` reads `data/filtered_dataset.csv`.
- Filters: year, product class and city.
- Visuals: annual horizontal bar chart, medicine-class pie chart, monthly sales bar chart, top products and top distributors.
- Data-quality panel reports source row count, exact duplicates, negative sales and negative quantities.
- Existing MediStock revenue cards continue to represent SQLite transactions and must not be confused with historical CSV totals.

## Important limitations

The CSV is user-supplied historical data; its independent provenance and currency are not established by this project. The 10-row sample file and 254k-row mixed-channel file were compared but are not imported into the app. This module is educational business analytics, not a live pharmacy integration or clinical decision system.
