# Reports Generator Service
# Aggregates business data and compiles beautiful PDFs using WeasyPrint

from datetime import datetime, timedelta
import io
import os
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from weasyprint import HTML

from app.config import settings


async def generate_pdf_report(
    title: str,
    report_type: str,
    time_range_days: int,
    include_ai_analysis: bool,
    db: AsyncSession
) -> bytes:
    # 1. Determine Date Range
    now = datetime.utcnow()
    start_date = now - timedelta(days=time_range_days)
    prev_start_date = now - timedelta(days=time_range_days * 2)

    # 2. Fetch Metrics from Database
    # Revenue
    revenue_query = text("SELECT SUM(amount) FROM sales WHERE date >= :start_date")
    revenue_result = await db.execute(revenue_query, {"start_date": start_date})
    current_revenue = revenue_result.scalar() or 0.0

    prev_revenue_query = text("SELECT SUM(amount) FROM sales WHERE date >= :prev_start_date AND date < :start_date")
    prev_revenue_result = await db.execute(prev_revenue_query, {"prev_start_date": prev_start_date, "start_date": start_date})
    prev_revenue = prev_revenue_result.scalar() or 0.0

    revenue_change = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0.0

    # Customers
    total_customers_query = text("SELECT COUNT(id) FROM customers")
    total_customers_result = await db.execute(total_customers_query)
    total_customers = total_customers_result.scalar() or 0

    new_customers_query = text("SELECT COUNT(id) FROM customers WHERE created_at >= :start_date")
    new_customers_result = await db.execute(new_customers_query, {"start_date": start_date})
    new_customers = new_customers_result.scalar() or 0

    prev_customers_query = text("SELECT COUNT(id) FROM customers WHERE created_at >= :prev_start_date AND created_at < :start_date")
    prev_customers_result = await db.execute(prev_customers_query, {"prev_start_date": prev_start_date, "start_date": start_date})
    prev_customers = prev_customers_result.scalar() or 0
    customers_change = ((new_customers - prev_customers) / prev_customers * 100) if prev_customers > 0 else 0.0

    # Support Tickets
    total_tickets_query = text("SELECT COUNT(id) FROM support_tickets WHERE created_at >= :start_date")
    total_tickets_result = await db.execute(total_tickets_query, {"start_date": start_date})
    total_tickets = total_tickets_result.scalar() or 0

    open_tickets_query = text("SELECT COUNT(id) FROM support_tickets WHERE created_at >= :start_date AND status = 'open'")
    open_tickets_result = await db.execute(open_tickets_query, {"start_date": start_date})
    open_tickets = open_tickets_result.scalar() or 0

    resolved_tickets_query = text("SELECT COUNT(id) FROM support_tickets WHERE created_at >= :start_date AND status = 'resolved'")
    resolved_tickets_result = await db.execute(resolved_tickets_query, {"start_date": start_date})
    resolved_tickets = resolved_tickets_result.scalar() or 0

    high_priority_query = text("SELECT COUNT(id) FROM support_tickets WHERE created_at >= :start_date AND priority IN ('high', 'critical')")
    high_priority_result = await db.execute(high_priority_query, {"start_date": start_date})
    high_priority_tickets = high_priority_result.scalar() or 0

    # Recent Sales Table (limit to 10)
    sales_query = text("""
        SELECT s.date, s.quantity, s.amount, c.name AS customer_name, p.name AS product_name, p.category AS product_category
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        LEFT JOIN products p ON s.product_id = p.id
        WHERE s.date >= :start_date
        ORDER BY s.date DESC
        LIMIT 10
    """)
    sales_result = await db.execute(sales_query, {"start_date": start_date})
    recent_sales = sales_result.all()

    # AI Insights
    insights_query = text("SELECT title, summary, priority, created_at FROM insights ORDER BY created_at DESC LIMIT 5")
    insights_result = await db.execute(insights_query)
    insights = insights_result.all()

    # 3. Generate AI Summary using Gemini if requested
    ai_summary = ""
    if include_ai_analysis:
        try:
            from app.dependencies import get_llm_client
            llm = get_llm_client()
            insights_summary = "\n".join([f"- {i.title}: {i.summary}" for i in insights])
            prompt = f"""
            Analyze these business metrics and provide a professional, concise executive summary (2 paragraphs max) for a business performance report.
            
            Report Title: {title}
            Time Range: Last {time_range_days} days
            
            Metrics:
            - Total Sales Revenue: ₹{current_revenue:,.2f} (period change: {revenue_change:+.1f}%)
            - Total Customers: {total_customers} (new this period: {new_customers}, change: {customers_change:+.1f}%)
            - Support Tickets Created: {total_tickets} ({open_tickets} open, {resolved_tickets} resolved, {high_priority_tickets} high priority)
            
            Latest Database Insights:
            {insights_summary}
            
            Write the output directly in paragraphs without any markdown headers. Keep the tone executive, objective, and analytical.
            """
            ai_summary = await llm.generate(prompt=prompt, system_prompt="You are an expert Business Intelligence Analyst.")
        except Exception as e:
            print(f"AI report summary generation failed: {e}")
            ai_summary = "AI analysis was requested but could not be completed due to rate limits or API connectivity. Please review database metrics below."

    # 4. Generate HTML String with Beautiful Styling
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 20mm;
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 8pt;
                    font-family: 'Inter', Helvetica, Arial, sans-serif;
                    color: #94a3b8;
                }}
                @bottom-left {{
                    content: "Vyapar360 AI Ops Report";
                    font-size: 8pt;
                    font-family: 'Inter', Helvetica, Arial, sans-serif;
                    color: #94a3b8;
                }}
            }}
            body {{
                font-family: 'Inter', Helvetica, Arial, sans-serif;
                color: #1e293b;
                line-height: 1.5;
                font-size: 10pt;
                background-color: #ffffff;
                margin: 0;
                padding: 0;
            }}
            .header {{
                background-color: #1e293b;
                color: #ffffff;
                padding: 20px;
                margin-bottom: 25px;
                border-radius: 6px;
            }}
            .header-title {{
                font-size: 18pt;
                font-weight: 700;
                margin: 0 0 5px 0;
                color: #f8fafc;
            }}
            .header-meta {{
                font-size: 9pt;
                color: #94a3b8;
                margin: 0;
            }}
            .grid {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 25px;
            }}
            .card {{
                flex: 1;
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 15px;
                margin-right: 15px;
            }}
            .card:last-child {{
                margin-right: 0;
            }}
            .card-title {{
                font-size: 8pt;
                font-weight: 600;
                color: #64748b;
                text-transform: uppercase;
                margin: 0 0 5px 0;
            }}
            .card-value {{
                font-size: 16pt;
                font-weight: 700;
                color: #0f172a;
                margin: 0 0 5px 0;
            }}
            .badge {{
                display: inline-block;
                padding: 2px 6px;
                font-size: 8pt;
                font-weight: 600;
                border-radius: 4px;
            }}
            .badge-success {{
                background-color: #dcfce7;
                color: #15803d;
            }}
            .badge-danger {{
                background-color: #fee2e2;
                color: #b91c1c;
            }}
            .badge-info {{
                background-color: #e0f2fe;
                color: #0369a1;
            }}
            .section {{
                margin-bottom: 30px;
            }}
            .section-title {{
                font-size: 12pt;
                font-weight: 700;
                color: #1e293b;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 5px;
                margin-top: 0;
                margin-bottom: 15px;
            }}
            .ai-box {{
                background-color: #eef2ff;
                border-left: 4px solid #4f46ed;
                padding: 15px;
                border-radius: 0 6px 6px 0;
                font-size: 9.5pt;
                color: #312e81;
                margin-bottom: 25px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
            }}
            th {{
                background-color: #f8fafc;
                color: #64748b;
                font-weight: 600;
                font-size: 8.5pt;
                text-align: left;
                padding: 10px;
                border-bottom: 1px solid #e2e8f0;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #f1f5f9;
                font-size: 9pt;
            }}
            .text-right {{
                text-align: right;
            }}
            .insight-item {{
                margin-bottom: 15px;
                padding: 12px;
                background-color: #f8fafc;
                border-radius: 6px;
                border-left: 3px solid #64748b;
            }}
            .insight-header {{
                display: flex;
                justify-content: space-between;
                font-weight: 600;
                font-size: 9.5pt;
                margin-bottom: 5px;
            }}
            .insight-desc {{
                font-size: 9pt;
                color: #475569;
                margin: 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="header-title">{title}</h1>
            <p class="header-meta">Generated: {datetime.now().strftime('%B %d, %Y %H:%M')} | Report Type: {report_type.replace('_', ' ').title()} | Period: Last {time_range_days} Days</p>
        </div>

        <div class="grid">
            <div class="card">
                <p class="card-title">Total Sales Revenue</p>
                <p class="card-value">₹{current_revenue:,.2f}</p>
                <span class="badge {'badge-success' if revenue_change >= 0 else 'badge-danger'}">
                    {revenue_change:+.1f}% vs last period
                </span>
            </div>
            <div class="card">
                <p class="card-title">Total Customers</p>
                <p class="card-value">{total_customers}</p>
                <span class="badge {'badge-success' if customers_change >= 0 else 'badge-danger'}">
                    {new_customers:+} new ({customers_change:+.1f}%)
                </span>
            </div>
            <div class="card">
                <p class="card-title">Support Operations</p>
                <p class="card-value">{total_tickets} Tickets</p>
                <span class="badge badge-info">
                    {resolved_tickets} resolved / {open_tickets} open
                </span>
            </div>
        </div>
    """

    if include_ai_analysis and ai_summary:
        formatted_summary = ai_summary.replace("\n", "</p><p>")
        html_content += f"""
        <div class="section">
            <h2 class="section-title">AI Executive Summary</h2>
            <div class="ai-box">
                <p>{formatted_summary}</p>
            </div>
        </div>
        """

    # Add Recent Sales Section
    sales_rows = ""
    for sale in recent_sales:
        sales_rows += f"""
        <tr>
            <td>{sale.date.strftime('%Y-%m-%d %H:%M') if hasattr(sale.date, 'strftime') else str(sale.date)}</td>
            <td>{sale.customer_name if sale.customer_name else 'N/A'}</td>
            <td>{sale.product_name if sale.product_name else 'N/A'}</td>
            <td>{sale.product_category if sale.product_category else 'N/A'}</td>
            <td class="text-right">{sale.quantity}</td>
            <td class="text-right">₹{sale.amount:,.2f}</td>
        </tr>
        """

    html_content += f"""
        <div class="section">
            <h2 class="section-title">Recent Transactions</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Customer</th>
                        <th>Product</th>
                        <th>Category</th>
                        <th class="text-right">Qty</th>
                        <th class="text-right">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {sales_rows if sales_rows else '<tr><td colspan="6" style="text-align: center;">No transactions found in this period.</td></tr>'}
                </tbody>
            </table>
        </div>
    """

    # Add AI Insights Section
    insight_items = ""
    for insight in insights:
        priority_badge = ""
        if insight.priority == "critical":
            priority_badge = '<span class="badge badge-danger">Critical</span>'
        elif insight.priority == "high":
            priority_badge = '<span class="badge badge-danger">High</span>'
        else:
            priority_badge = f'<span class="badge badge-info">{insight.priority.title()}</span>'
            
        insight_items += f"""
        <div class="insight-item">
            <div class="insight-header">
                <span>{insight.title}</span>
                {priority_badge}
            </div>
            <p class="insight-desc">{insight.summary}</p>
        </div>
        """

    html_content += f"""
        <div class="section">
            <h2 class="section-title">Key System Insights</h2>
            {insight_items if insight_items else '<p>No system insights generated recently.</p>'}
        </div>
    </body>
    </html>
    """

    # 5. Compile HTML to PDF using WeasyPrint
    pdf_buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    return pdf_buffer.getvalue()
