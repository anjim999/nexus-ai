# Vyapar360 (Nexus AI) - Deep Dive Technical Explanation

**Version:** 1.0  
**Generated For:** Project Owner (Anji)  
**Goal:** Explain *every connected piece* of the system in extreme detail.

---

# 🔗 The Connection Chain: From User Click to Database Row

We will trace the exact path of data flow. imagine a user clicking "Refresh" on the Dashboard.

## 1. The Frontend (React/TypeScript)
*Location:* `/frontend/src/`

This is where the user interaction starts.

### **A. `pages/Dashboard.tsx` (The View)**
This is the main screen file.
- **What it does:** It defines the layout (Metrics Grid, Charts, Alerts).
- **How it works:**
  - It uses a React Hook `useEffect` efficiently. This means "When the page loads, do this."
  - Inside `useEffect`, it calls `fetchDashboardData()`.
- **The Connection:** It imports `api` from `services/api`. It does *not* talk to the server directly; it uses a "service" helper.
  ```typescript
  // Actual code snippet logic
  import api from '../services/api';
  const fetchDashboardData = async () => {
      const response = await api.get('/insights/dashboard'); // <--- THE TRIGGER
  }
  ```

### **B. `services/api.ts` (The Messenger)**
This file configures `axios` (a library for making HTTP requests).
- **What it does:** It sets up the "Base URL" so we don't have to type `http://localhost:8000` every time.
- **The Connection:** It sends the request over the internet (or localhost) to port `8000`.

---

## 2. The Backend (Python/FastAPI)
*Location:* `/backend/app/`

The request hits the server.

### **C. `main.py` (The Gatekeeper)**
This is the entry point of the backend system.
- **What it does:** It creates the `FastAPI()` app.
- **The Connection:** It includes the router:
  ```python
  app.include_router(api_router, prefix="/api/v1")
  ```
  This tells the server: "If a request comes to `/api/v1/...`, send it to the `api_router`."

### **D. `api/v1/router.py` (The Traffic Cop)**
- **What it does:** It organizes all the different modules (Chat, Documents, Insights).
- **The Connection:** It routes `/insights` requests to the `insights.router`:
  ```python
  api_router.include_router(insights.router, prefix="/insights", tags=["Insights"])
  ```
  So our request `/api/v1/insights/dashboard` is finally handed over to the specific file that handles it.

### **E. `api/v1/endpoints/insights.py` (The Logic Core - WE EDITED THIS)**
This is where the magic happens.
- **What it does:** It actually logic to get the numbers.
- **The Dependency Injection (`Depends(get_db)`):**
  - Notice the function signature:
    ```python
    async def get_dashboard_data(db: AsyncSession = Depends(get_db)):
    ```
  - **Crucial Concept:** FastAPI sees `Depends(get_db)`. It pauses, calls `get_db()`, gets a fresh database session, and passes it to our function. This ensures we have a secure, open line to the database.
- **The Queries:**
  - It constructs SQL queries using SQLAlchemy style (Python code that looks like SQL).
  - *Example:* `select(func.sum(Sale.amount))` translates to `SELECT SUM(amount) FROM sales`.
  - It `await db.execute(...)` to send this passing SQL to the database.

---

## 3. The Database Layer (SQLAlchemy/Postgres)
*Location:* `/backend/app/database/`

### **F. `database/connection.py` (The Bridge)**
- **What it does:** It holds the `engine`. The engine is the heavy-lifter that maintains the connection pool to Neon (PostgreSQL).
- **The Fix We Made:** We added logic here to swap `postgresql://` to `postgresql+asyncpg://`. This tells SQLAlchemy "Use the AsyncPG driver", allowing us to handle thousands of requests without freezing.
- **`get_db` function:** This is the context manager. It opens a session → yields it to the endpoint → waits → closes it after the request is done.

### **G. `database/models.py` (The Dictionary)**
- **What it does:** It tells Python what the Database tables look like.
- **The Mapping:**
  ```python
  class Sale(Base):
      __tablename__ = "sales"
      amount: Mapped[float] = mapped_column(Float)
  ```
  This maps the Python class `Sale` to the SQL table `sales`. When we query `Sale`, SQLAlchemy knows to look at the `sales` table in Postgres.

---

## 4. The Data Origin (Seed Script)
*Location:* `/backend/seed_db.py`

How did data get there in the first place?

### **H. `seed_db.py` (The Creator)**
- **What it does:** It acts like a "God Mode" script.
- **How it works:**
  1. Activates the DB connection.
  2. Checks if data exists.
  3. If empty, it loops (e.g., `for i in range(50)`) and creates Python objects (`Customer`, `Sale`).
  4. It calls `session.commit()`.
  5. **Result:** Python objects are converted to SQL `INSERT` statements and sent to Neon.

---

## 🔍 Summary of the Flow

1. **User** loads dashboard.
2. **`Dashboard.tsx`** asks `api.ts` for data.
3. **`api.ts`** sends HTTP GET to `main.py`.
4. **`main.py`** -> `router.py` -> **`insights.py`**.
5. **`insights.py`** asks `connection.py` for a DB session.
6. **`insights.py`** runs queries defined by **`models.py`**.
7. **PostgreSQL** executes queries on data created by **`seed_db.py`**.
8. **Data** travels all the way back up the chain to the User's screen.

This architecture is **State of the Art** because it is modular. You can change the database without breaking the frontend, or change the frontend design without touching the database logic.
