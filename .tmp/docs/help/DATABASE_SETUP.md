# PostgreSQL Database Setup Guide

This application now uses PostgreSQL for persistent session memory storage.

## Prerequisites

- PostgreSQL 12+ installed and running
- psycopg2 driver (installed via `uv sync`)

## Setup Steps

### 1. Create Database and User

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE USER sa4dst_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE sa4dst OWNER sa4dst_user;
GRANT ALL PRIVILEGES ON DATABASE sa4dst TO sa4dst_user;

# Exit psql
\q
```

### 2. Configure Environment Variables

Create or update your `.env` file in the `backend/` directory:

```bash
DATABASE_URL=postgresql://sa4dst_user:your_secure_password@localhost:5432/sa4dst
```

> [!NOTE]
> **Default Fallback User:** If the `DATABASE_URL` environment variable is not defined, the application defaults to connecting as:
> `postgresql://adeelarshad@localhost/sa4dst` (using user `adeelarshad` to connect to database `sa4dst` on localhost without a password).

### 3. Install Dependencies

```bash
uv sync
```

### 4. Initialize Database

The database tables will be automatically created on first API startup.

Alternatively, initialize manually:

```bash
python -c "from backend.database.db import init_db; init_db()"
```

## Connecting & Querying via Command Line

### Connect to Database

* **Connect using fallback credentials (default user):**
  ```bash
  psql -d sa4dst
  ```
  *(Or explicitly: `psql -U adeelarshad -d sa4dst`)*

* **Connect using custom user:**
  ```bash
  psql -U sa4dst_user -d sa4dst
  ```

### Useful CLI Inspection Commands

Once connected to the postgres prompt (`sa4dst=#`), run:

* **List all tables:**
  ```sql
  \dt
  ```
  *(Expected tables: `chat_sessions`, `chat_messages`, `session_telemetry`, and `complaint_telemetry`)*

* **Describe table schema:**
  ```sql
  \d chat_sessions
  \d complaint_telemetry
  ```

* **Query row counts:**
  ```sql
  SELECT COUNT(*) FROM chat_sessions;
  SELECT COUNT(*) FROM chat_messages;
  SELECT COUNT(*) FROM complaint_telemetry;
  ```

* **Select latest 5 sessions:**
  ```sql
  SELECT session_id, created_at FROM chat_sessions ORDER BY created_at DESC LIMIT 5;
  ```

* **Exit PostgreSQL CLI:**
  ```sql
  \q
  ```

## Session Persistence

- Chat sessions and messages are automatically persisted to PostgreSQL
- Sessions can be resumed by passing the `session_id` in subsequent requests
- All conversation history is maintained across application restarts

## Troubleshooting

### Connection Refused
- Ensure PostgreSQL is running: `brew services start postgresql` (macOS)
- Check DATABASE_URL format in .env

### Table Already Exists
- Run migrations: `alembic upgrade head`
- Or drop and recreate: `dropdb sa4dst && createdb sa4dst`

### Migration Issues
- Initialize alembic: `alembic init alembic`
- Create migration: `alembic revision --autogenerate -m "Initial schema"`

---

## RAG Relational Database (SQLite)

Used by the **RAG Console** for structured tabular queries (SQL). Ingested Excel/CSV files are stored here as tables and queried via LLM-generated SQL.

### Location

```
backend/rag/data/rag_relational.db
```

### Connect via CLI

```bash
sqlite3 backend/rag/data/rag_relational.db
```

Once inside the SQLite prompt:

```sql
-- List all tables
.tables

-- Show schema for a table
.schema tbl_complaint_managment_dashboard_new

-- Enable column headers and pretty output
.headers on
.mode column

-- Exit
.quit
```

---

### Tables

#### `tbl_complaint_managment_dashboard_new`
> **Source file:** `Complaint_managment_dashboard_new.xlsx`
> **Active schema** (used by RAG SQL queries)
> **Rows:** 3,597

| Column | Type | Description |
|---|---|---|
| `ticket_id` | TEXT | Unique ticket identifier e.g. `TK-13323` |
| `create_date` | TEXT | Ticket creation date e.g. `2025-12-28` |
| `ticket_queue` | TEXT | NOC queue assigned: `CS`, `PS`, `IN`, `VAS`, `RAN`, `IREG`, `EI` |
| `ticket_status` | TEXT | `Resolved`, `Rejected`, `Reassigned` |
| `issue_category` | TEXT | `Roaming`, `MNP`, `Data Bundle`, `VoLTE`, `eSIM` |
| `reassignment_reason` | TEXT | Reason for reassignment (nullable) |
| `color_group` | TEXT | `BLUE` or `BROWN` classification |
| `average_time_spent_in_mins` | INTEGER | Avg handling time in minutes |
| `reassigned_to` | TEXT | Target queue if reassigned (nullable) |
| `rejection_reason` | TEXT | Reason for rejection (nullable) |
| `country` | TEXT | Customer roaming country (nullable) |

**Issue Category Distribution:**

| Category | Row Count |
|---|---|
| VoLTE | 760 |
| Roaming | 750 |
| MNP | 711 |
| Data Bundle | 695 |
| eSIM | 681 |

> [!WARNING]
> **Known Data Quality Issue — Country Name Inconsistencies**
> The `country` column has duplicate variants for the same country that cause undercounting in `GROUP BY` queries:
>
> | Canonical | Variants in Data | Combined Total (Roaming) |
> |---|---|---|
> | United States | `US` (31) + `USA` (2) | **33** |
> | Saudi Arabia | `Saudi Arabia` (26) + `KSA` (2) | **28** |
> | Singapore | `Singapore` (37) + `Singapre` (1 — typo) | **38** |
> | Pakistan | `Pak` (120) | abbreviated |
> | Australia | `AUS` (95) | abbreviated |
>
> Fix by standardising the source Excel file before re-ingesting, or use a `CASE` expression in SQL.

---

#### `tbl_operations_dashboard_data_template`
> **Source file:** `Operations_Dashboard_Data_Template.xlsx`
> **Legacy/reference table** — same schema, original mock dataset
> **Rows:** 3,597

Same 11-column schema as above. Countries in this table are fully standardised (`UAE`, `UK`, `Germany`, `US`, `Singapore`, `Saudi Arabia`).

> [!NOTE]
> This table is **not** the active RAG schema. Only `tbl_complaint_managment_dashboard_new` is registered in the docstore and used for SQL generation.

---

### Useful Diagnostic Queries

```bash
# Run any query directly from terminal (no interactive shell needed)
sqlite3 backend/rag/data/rag_relational.db "SELECT name FROM sqlite_master WHERE type='table';"
```
```
sqlite3 backend/rag/data/rag_relational.db "SELECT COUNT(*) FROM tbl_operational_data;"
```
```sql
-- Row counts for all tables
SELECT 'tbl_complaint_managment_dashboard_new' as tbl, COUNT(*) FROM tbl_complaint_managment_dashboard_new
UNION ALL
SELECT 'tbl_operations_dashboard_data_template', COUNT(*) FROM tbl_operations_dashboard_data_template;

-- Roaming complaints by country (new table, normalised)
SELECT
  CASE country
    WHEN 'USA'      THEN 'US'
    WHEN 'KSA'      THEN 'Saudi Arabia'
    WHEN 'Singapre' THEN 'Singapore'
    WHEN 'Pak'      THEN 'Pakistan'
    WHEN 'AUS'      THEN 'Australia'
    ELSE country
  END AS country_normalised,
  COUNT(*) AS total_roaming_complaints
FROM tbl_complaint_managment_dashboard_new
WHERE issue_category = 'Roaming'
GROUP BY country_normalised
ORDER BY total_roaming_complaints DESC;

-- All issue categories and their counts
SELECT issue_category, COUNT(*) AS cnt
FROM tbl_complaint_managment_dashboard_new
GROUP BY issue_category
ORDER BY cnt DESC;

-- Ticket status breakdown
SELECT ticket_status, COUNT(*) AS cnt
FROM tbl_complaint_managment_dashboard_new
GROUP BY ticket_status ORDER BY cnt DESC;

-- Queue workload distribution
SELECT ticket_queue, COUNT(*) AS cnt
FROM tbl_complaint_managment_dashboard_new
GROUP BY ticket_queue ORDER BY cnt DESC;
```

---

### Re-ingesting a New File

Upload via the RAG Console **Ingest** tab, or via API:

```bash
curl -X POST http://localhost:8000/rag/ingest \
  -F "file=@/path/to/your_file.xlsx"
```

The new table will be named from the filename (lowercased, spaces → underscores, prefixed with `tbl_`).
The old table remains in the DB unless manually dropped:

```bash
sqlite3 backend/rag/data/rag_relational.db "DROP TABLE IF EXISTS tbl_old_table_name;"
```
