import asyncio
import os
import sys
from datetime import datetime, timedelta
import random

from dotenv import load_dotenv

# Load env vars
load_dotenv()

sys.path.append(os.getcwd())

from app.database.connection import init_database, get_db_session, close_database
from app.database.models import Customer, Product, Sale, SupportTicket, ScheduledTask, TaskFrequency, Insight, InsightPriority

async def seed_data():
    print("Initializing database...")
    await init_database()
    
    async with get_db_session() as session:
        # Check if data exists
        from sqlalchemy import select
        result = await session.execute(select(Customer))
        customer_exists = result.scalars().first() is not None
        
        if not customer_exists:
            print("Seeding base business data (Customers, Products, Sales)...")
            
            # 1. Create Customers
            customers = []
            segments = ["Enterprise", "SMB", "Startup"]
            for i in range(50):
                c = Customer(
                    name=f"Customer {i+1}",
                    email=f"contact@customer{i+1}.com",
                    segment=random.choice(segments),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
                )
                customers.append(c)
            session.add_all(customers)
            await session.flush() # flush to get IDs
            
            # 2. Create Products
            products = []
            categories = ["Software", "Hardware", "Services"]
            for i in range(10):
                p = Product(
                    name=f"Product {i+1}",
                    category=random.choice(categories),
                    price=round(random.uniform(100, 5000), 2),
                    cost=round(random.uniform(50, 2000), 2),
                    inventory=random.randint(0, 100)
                )
                products.append(p)
            session.add_all(products)
            await session.flush()
            
            # 3. Create Sales
            sales = []
            regions = ["North America", "Europe", "Asia", "South America"]
            for i in range(200):
                p = random.choice(products)
                s = Sale(
                    customer_id=random.choice(customers).id,
                    product_id=p.id,
                    amount=p.price * random.randint(1, 5),
                    quantity=random.randint(1, 5),
                    region=random.choice(regions),
                    date=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                )
                sales.append(s)
            session.add_all(sales)
            
            # 4. Create Support Tickets
            tickets = []
            statuses = ["open", "resolved", "pending"]
            priorities = ["low", "medium", "high"]
            for i in range(30):
                t = SupportTicket(
                    customer_id=random.choice(customers).id,
                    subject=f"Issue with {random.choice(products).name}",
                    status=random.choice(statuses),
                    priority=random.choice(priorities),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, 10))
                )
                tickets.append(t)
            session.add_all(tickets)
            await session.commit()
            print("Base business data seeded!")
        else:
            print("Base business data already exists. Skipping.")

        # 5. Check and Seed Scheduled Tasks (Pending Tasks)
        result_tasks = await session.execute(select(ScheduledTask))
        if not result_tasks.scalars().first():
            print("Seeding scheduled tasks...")
            from uuid import uuid4
            tasks = []
            task_types = ["report_generation", "data_sync", "email_campaign", "system_maintenance"]
            # Frequencies
            freqs = [TaskFrequency.DAILY, TaskFrequency.WEEKLY, TaskFrequency.MONTHLY]
            
            for i in range(15):
                t = ScheduledTask(
                    id=str(uuid4()),
                    name=f"Task {i+1}: {random.choice(['Daily Backup', 'Weekly Report', 'Sync CRM', 'Email Blast', 'Update Inventory'])}",
                    task_type=random.choice(task_types),
                    frequency=random.choice(freqs),
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                )
                tasks.append(t)
            session.add_all(tasks)
            await session.commit()
            print("Scheduled tasks seeded!")
            
        # 6. Check and Seed AI Insights
        result_insights = await session.execute(select(Insight))
        if not result_insights.scalars().first():
            print("Seeding AI insights...")
            from uuid import uuid4
            insights = []
            
            # Sample insight templates
            insight_templates = [
                {
                    "title": "Churn Risk Detected",
                    "category": "Customer Retention",
                    "priority": InsightPriority.HIGH,
                    "summary": "3 enterprise customers showing low engagement in the last 14 days.",
                    "confidence": 0.89
                },
                {
                    "title": "Inventory Optimization",
                    "category": "Operations",
                    "priority": InsightPriority.MEDIUM,
                    "summary": "Product 4 inventory levels are critical. Recommend reordering 50 units.",
                    "confidence": 0.95
                },
                {
                    "title": "Revenue Forecast",
                    "category": "Financial",
                    "priority": InsightPriority.MEDIUM,
                    "summary": "Expected 15% revenue growth next month based on current pipeline velocity.",
                    "confidence": 0.82
                },
                {
                    "title": "Anomalous Spending",
                    "category": "Financial",
                    "priority": InsightPriority.CRITICAL,
                    "summary": "Detected unusual spike in cloud infrastructure costs (+40%) yesterday.",
                    "confidence": 0.98
                },
                {
                    "title": "Sales Opportunity",
                    "category": "Sales",
                    "priority": InsightPriority.LOW,
                    "summary": "SMB segment showing higher conversion rates. Recommend targeting with new campaign.",
                    "confidence": 0.75
                }
            ]
            
            for template in insight_templates:
                insight = Insight(
                    id=str(uuid4()),
                    title=template["title"],
                    summary=template["summary"],
                    details=f"Detailed analysis for {template['title']}: {template['summary']} Based on data from the last 30 days.",
                    category=template["category"],
                    priority=template["priority"],
                    confidence=template["confidence"],
                    created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
                    is_read=False,
                    is_dismissed=False
                )
                insights.append(insight)
            
            session.add_all(insights)
            await session.commit()
            print("AI insights seeded!")

async def main():
    try:
        await seed_data()
    finally:
        await close_database()

if __name__ == "__main__":
    asyncio.run(main())
