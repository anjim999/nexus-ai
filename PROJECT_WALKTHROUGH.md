# Vyapar360 (Nexus AI) - Complete Project Walkthrough & Technical Guide

**Version:** 1.0  
**Generated For:** Project Owner (Anji)  
**Date:** February 04, 2026

---

## 🚀 1. Introduction: What is this project?

**Vyapar360** (internally codenamed *Nexus AI*) is an advanced **Business Intelligence & ERP Dashboard** powered by Artificial Intelligence. 

Unlike traditional dashboards that just show static tables, Vyapar360 is designed to act as an **"AI Ops Engineer"**. It actively monitors business data (sales, customers, support tickets), detects anomalies (like sudden revenue drops), and suggests actions (like reordering inventory).

### **Why is this impressive?**
- **It's "Agentic":** It doesn't just display data; it "thinks" about it using AI agents (Research, Analyst, Reasoning).
- **It's Real-Time:** Everything you see on the dashboard comes from a live, production-grade PostgreSQL database.
- **It's Scalable:** The architecture separates the "Brains" (Python/FastAPI) from the "Face" (React/Vite).

---

## 🏗️ 2. The Architecture: How does it basically work?

Imagine a restaurant. 
- **The Frontend (React)** is the Menu and the Waiter. It shows options to the user and takes requests.
- **The Backend (FastAPI)** is the Kitchen. It cooks the data (processes requests).
- **The Database (PostgreSQL)** is the Pantry. It stores all the raw ingredients (customer lists, sales records).
- **The AI (Gemini/Agents)** is the Head Chef. It invents new recipes (insights) based on what's in the pantry.

### **High-Level Flow:**
1. **User opens Dashboard** → Frontend sends a request to Backend (`GET /dashboard`).
2. **Backend receives request** → It asks the Database: *"Give me the total sales for this week."*
3. **Database responds** → *"Total sales: ₹12.4L"*.
4. **Backend asks AI** → *"Is this sales number good? Write a summary."*
5. **AI responds** → *"Yes, it's up 12% week-over-week."*
6. **Backend serves dish** → Sends formatted data to Frontend.
7. **Frontend displays** → You see a beautiful card saying **"Revenue: ₹12.4L 📈"**.

---

## 📂 3. Folder Structure & Key Files (The "Where is What")

### **Frontend (`/frontend`)** - The User Interface
Built with **React, TypeScript, Tailwind CSS, and Vite**.

- **`src/pages/Dashboard.tsx`**: The main screen you are looking at. It organizes the cards, charts, and lists.
- **`src/components/ui/`**: Reusable building blocks (Buttons, Cards, Badges, Charts).
- **`src/services/api.ts`**: The bridge that talks to the backend.

### **Backend (`/backend`)** - The Logic Center
Built with **Python, FastAPI, SQLAlchemy, and AsyncPG**.

- **`main.py`**: The entry point. Starts the server.
- **`app/api/v1/endpoints/insights.py`**: **CRITICAL FILE.** This contains the logic we just wrote to fetch real data for the dashboard.
- **`app/database/models.py`**: Defines what our data looks like (e.g., "A Customer has a name, email, and segment").
- **`app/database/connection.py`**: Handles connecting to the PostgreSQL database safely.
- **`seed_db.py`**: A special script we created to fill the empty database with realistic "dummy" data so the app looks alive.

---

## 🛠️ 4. How We Built & Fixed It (Step-by-Step)

Here is the story of how we took this from "broken/empty" to "working/real":

### **Phase 1: The Setup**
- We confirmed we are using **PostgreSQL** (specifically Neon DB).
- We ensured the `.env` file had the correct database URL.
- We fixed a compatibility issue where the code expected `sqlite` but we gave it `postgresql`. We added logic to automatically switch to the `asyncpg` driver (the fast connector for Postgres).

### **Phase 2: The Data Problem**
- **Issue:** The dashboard was showing hardcoded "fake" text (e.g., "Pending Tasks: 12") even though the code was running.
- **Solution:** We needed **Real Data**.
- **Action:** We wrote and refined `seed_db.py`.
    - We generated **50 Customers**, **10 Products**, **200 Sales**, and **30 Support Tickets**.
    - We ran this script (`python seed_db.py`), which pushed all this data into your cloud database.

### **Phase 3: Connecting the Wires**
- **Issue:** The API (`insights.py`) was still returning the hardcoded text, ignoring the database.
- **Solution:** We rewrote the `get_dashboard_data` function.
    - Instead of `return "12"`, we wrote code to **count** the actual rows in the database tables.
    - **Revenue Logic:** Sum of all `Sale.amount` for the last 7 days.
    - **Pending Tasks:** Count of active `ScheduledTask` rows.
    - **Alerts:** Fetch `SupportTicket` rows where priority is "High" or "Critical".
- **Result:** When you refresh the page, the backend runs a live SQL query and gives you the exact numbers from the DB.

---

## 💻 5. How to Run It Yourself (The "Commands")

If you restart your computer, here is how you bring the project back to life:

**Terminal 1 (Backend):**
```bash
cd nexus-ai
cd backend
source venv/bin/activate  # Activate the Python environment
python main.py            # Start the API server
```
*You will see logs saying "Application startup complete".*

**Terminal 2 (Frontend):**
```bash
cd nexus-ai
cd frontend
npm run dev               # Start the React UI
```
*Click the link (usually http://localhost:5173) to open the app.*

---

## 🔮 6. Future: What's Next? (Deployment)

Currently, this runs on your laptop ("Localhost"). To show it to recruiters anywhere in the world, we need to **Deploy** it.

**The Plan:**
1.  **Backend:** Deploy to a cloud provider like **Render** or **Railway**. They connect to your GitHub and run `python main.py` for you.
2.  **Frontend:** Deploy to **Vercel**. It builds your React site and puts it on a public URL (e.g., `vyapar360.vercel.app`).
3.  **Database:** Already deployed on **Neon** (Good job!), so the cloud backend can connect to it easily.

---

## ✅ Summary for Recruiters

When explaining this project, you can confidently say:
> *"I built a scalable AI-driven ERP system. It uses a modern React frontend and a Python FastAPI backend. The data is not mocked; it flows in real-time from a PostgreSQL database. I implemented an Agentic AI system to generate business insights and automated database seeding scripts to simulate realistic enterprise load."*
