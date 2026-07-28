# Hospital Management System (HMS)

A dynamic Hospital Management System built using Flask and the HOGC EAV CRUD Engine. The system allows staff to manage patients, hospital visits, inventory, prescriptions, and laboratory tests seamlessly.

## Prerequisites

- **Python 3.12+**
- **PostgreSQL 14+** (running locally or accessible via network)
- **Git**

---

## PostgreSQL Installation Guide

> If you already have PostgreSQL installed and running, skip to [Installation & Setup](#installation--setup).

### Windows

1. **Download** the installer from the official site:
   [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)
2. Run the installer and follow the setup wizard:
   - Choose a **password** for the `postgres` superuser — **remember this password**, you'll need it for the `.env` file.
   - Keep the default **port** as `5432`.
   - Leave everything else as default and finish the installation.
3. The installer includes **pgAdmin** (a GUI tool) and adds `psql` to your PATH.
4. **Verify** the installation by opening a terminal:
   ```bash
   psql --version
   ```
   > If `psql` is not recognized, add `C:\Program Files\PostgreSQL\<version>\bin` to your system PATH.

### macOS

1. **Install via Homebrew** (recommended):
   ```bash
   brew install postgresql@16
   brew services start postgresql@16
   ```
2. **Verify** installation:
   ```bash
   psql --version
   ```

### Linux (Ubuntu / Debian)

1. **Install via apt**:
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```
2. **Start the service**:
   ```bash
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```
3. **Set a password** for the `postgres` user:
   ```bash
   sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'yourpassword';"
   ```

---

### Creating the `hms` Database

After PostgreSQL is installed and running, create the database that the app will use:

**Option A — Using the `psql` command line:**
```bash
# Connect as the postgres superuser
psql -U postgres

# Inside the psql prompt, run:
CREATE DATABASE hms;

# Exit
\q
```

**Option B — Using pgAdmin (GUI):**
1. Open **pgAdmin** and connect to your local server.
2. Right-click **Databases** → **Create** → **Database…**
3. Enter `hms` as the database name and click **Save**.

---

## Installation & Setup

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/vishnu2006034/hms.git
   cd hms
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   uv pip install .
   ```


## Configuration

1. Create a `.env` file in the root directory (`hms/.env`).
2. Add the following environment variables, replacing `yourpassword` with the password you set during PostgreSQL installation:
   ```env
   FLASK_APP=run.py
   FLASK_ENV=development
   FLASK_SECRET_KEY=change-this-to-a-random-secret-key
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/hms
   ```
   > Make sure you have already created the `hms` database — see [Creating the hms Database](#creating-the-hms-database) above.

## Initializing the Database

The application comes with an automatic seeding mechanism that populates the database with default modules, configurations, and dummy data.

If you ever need to reset the database and start fresh:
```bash
python reset_db.py
```
*(Warning: This will delete existing records from the database).*

## Running the Application

To start the Flask development server, run:
```bash
python run.py
```

On the first run (or after running `reset_db.py`), the app will automatically seed the database with the required module schemas and default data. This may take a few seconds.

## Usage

1. Open your web browser and navigate to:
   [http://127.0.0.1:5000](http://127.0.0.1:5000)
2. Log in using the default administrator credentials:
   - **Username:** `admin`
   - **Password:** `admin123`
3. Use the navigation bar to access different modules:
   - **Users:** Manage hospital staff and roles.
   - **Patients:** Manage patient records and demographics.
   - **Visits:** Log and track patient appointments and visits.
   - **Inventory:** Keep track of hospital supplies and medications.
   - **Prescriptions:** Issue and view medical prescriptions.
   - **Laboratory:** Order and record lab tests and results.
