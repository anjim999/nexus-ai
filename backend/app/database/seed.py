import asyncio
import logging
import random
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import select, func

from app.database.connection import get_db_session
from app.database.models import (
    Customer, Product, Sale, SupportTicket, 
    ScheduledTask, TaskFrequency, Insight, InsightPriority
)

logger = logging.getLogger(__name__)

async def seed_database_if_empty():
    """
    Check if the database is empty and seed it with initial data if needed.
    Idempotent: Safe to run multiple times.
    """
    async with get_db_session() as session:
        # Check if customers exist
        result = await session.execute(select(Customer).limit(1))
        if result.scalars().first():
            logger.info("📦 Database already contains data. Skipping auto-seed.")
            return

        logger.info("🌱 Database is empty. Starting automatic seeding...")
        
        try:
            # 1. Create Customers
            segments = ["Enterprise", "SMB", "Startup"]
            customers = [
                Customer(
                    name=f"Customer {i+1}",
                    email=f"contact@customer{i+1}.com",
                    segment=random.choice(segments),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
                ) for i in range(50)
            ]
            session.add_all(customers)
            await session.flush()
            
            # 2. Create Products
            categories = ["Software", "Hardware", "Services"]
            products = [
                Product(
                    name=f"Product {i+1}",
                    category=random.choice(categories),
                    price=round(random.uniform(100, 5000), 2),
                    cost=round(random.uniform(50, 2000), 2),
                    inventory=random.randint(0, 100)
                ) for i in range(10)
            ]
            session.add_all(products)
            await session.flush()
            
            # 3. Create Sales
            regions = ["North America", "Europe", "Asia", "South America"]
            sales = [
                Sale(
                    customer_id=random.choice(customers).id,
                    product_id=random.choice(products).id,
                    amount=random.choice(products).price * random.randint(1, 5),
                    quantity=random.randint(1, 5),
                    region=random.choice(regions),
                    date=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                ) for i in range(200)
            ]
            session.add_all(sales)
            
            # 4. Create Support Tickets
            statuses = ["open", "resolved", "pending"]
            priorities = ["low", "medium", "high", "critical"]
            tickets = [
                SupportTicket(
                    customer_id=random.choice(customers).id,
                    subject=f"Issue with {random.choice(products).name}",
                    status=random.choice(statuses),
                    priority=random.choice(priorities),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, 10))
                ) for i in range(30)
            ]
            session.add_all(tickets)
            
            # 5. Create Scheduled Tasks
            task_types = ["report_generation", "data_sync", "email_campaign", "system_maintenance"]
            freqs = [TaskFrequency.DAILY, TaskFrequency.WEEKLY, TaskFrequency.MONTHLY]
            tasks = [
                ScheduledTask(
                    id=str(uuid4()),
                    name=f"Task {i+1}: {random.choice(['Daily Backup', 'Weekly Report', 'Sync CRM', 'Email Blast', 'Update Inventory'])}",
                    task_type=random.choice(task_types),
                    frequency=random.choice(freqs),
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                ) for i in range(15)
            ]
            session.add_all(tasks)
            
            # 6. Create AI Insights
            insight_templates = [
                {"title": "Churn Risk Detected", "category": "Customer Retention", "priority": InsightPriority.HIGH, "summary": "3 enterprise customers showing low engagement in the last 14 days.", "confidence": 0.89},
                {"title": "Inventory Optimization", "category": "Operations", "priority": InsightPriority.MEDIUM, "summary": "Product 4 inventory levels are critical. Recommend reordering 50 units.", "confidence": 0.95},
                {"title": "Revenue Forecast", "category": "Financial", "priority": InsightPriority.MEDIUM, "summary": "Expected 15% revenue growth next month based on current pipeline velocity.", "confidence": 0.82},
                {"title": "Anomalous Spending", "category": "Financial", "priority": InsightPriority.CRITICAL, "summary": "Detected unusual spike in cloud infrastructure costs (+40%) yesterday.", "confidence": 0.98},
                {"title": "Sales Opportunity", "category": "Sales", "priority": InsightPriority.LOW, "summary": "SMB segment showing higher conversion rates. Recommend targeting with new campaign.", "confidence": 0.75}
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
                session.add(insight)
            
            await session.commit()
            logger.info("✅ Database seeded successfully!")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Auto-seeding failed: {str(e)}")
            # Don't raise, allowing the app to start even if seed fails
