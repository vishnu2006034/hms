# Hospital Management System (HMS)

A dynamic Hospital Management System built using Flask and the HOGC EAV CRUD Engine. The system allows staff to manage patients, hospital visits, inventory, prescriptions, and laboratory tests seamlessly.

## Prerequisites

- **Python 3.8+**
- **PostgreSQL** (running locally or accessible via network)

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
   pip install -r requirements.txt
   ```
   *(Note: Ensure that the `hogc` engine is installed in your environment if it is a local or custom package).*

## Configuration

1. Create a `.env` file in the root directory (`hms/.env`).
2. Add your PostgreSQL database connection string to the `.env` file. For example:
   ```env
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/hms
   
   # Optional: Configure HOGC Tenant
   HOGC_TENANT_ID=hms
   HOGC_ORG_ID=default
   ```
   *(Make sure to create an empty database named `hms` in PostgreSQL before proceeding).*

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
