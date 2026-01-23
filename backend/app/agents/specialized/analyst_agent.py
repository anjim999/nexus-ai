"""
========================================
Analyst Agent
========================================
Analyzes data, generates SQL, detects patterns
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.llm.gemini import GeminiClient
from app.llm.prompts import ANALYST_AGENT_PROMPT


class AnalystAgent:
    """
    Analyst Agent
    
    Responsibilities:
    - Query databases using natural language to SQL
    - Perform calculations and aggregations
    - Detect trends and patterns
    - Identify anomalies
    - Generate chart data
    """
    
    def __init__(self, llm: GeminiClient):
        self.llm = llm
        self.system_prompt = ANALYST_AGENT_PROMPT
        
        # Sample database schema (would be loaded from actual DB)
        self.schema = """
        Tables:
        - sales (id, product_id, customer_id, amount, quantity, date, region)
        - customers (id, name, email, segment, created_at, last_purchase)
        - products (id, name, category, price, cost, inventory)
        - support_tickets (id, customer_id, subject, status, priority, created_at, resolved_at)
        - metrics (id, metric_name, value, recorded_at)
        """
    
    async def analyze(
        self,
        query: str,
        context: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze data based on query
        
        Args:
            query: Analysis request
            context: Additional context from documents
            
        Returns:
            Analysis results with data and summary
        """
        # Determine what kind of analysis is needed
        analysis_type = await self._determine_analysis_type(query)
        
        # Generate SQL if database query needed
        if analysis_type.get("needs_sql"):
            sql_query = await self._generate_sql(query)
            data = await self._execute_query(sql_query)
        else:
            data = self._get_sample_data(query)
        
        # Detect patterns
        patterns = await self._detect_patterns(data, query)
        
        # Generate chart if visualization would help
        chart = None
        if analysis_type.get("needs_visualization"):
            chart = await self._generate_chart_config(data, query)
        
        # Generate summary
        summary = await self._summarize_analysis(query, data, patterns)
        
        return {
            "data": data,
            "patterns": patterns,
            "chart": chart,
            "summary": summary,
            "action": f"Analyzed {len(data)} data points",
            "sql_query": analysis_type.get("sql_query")
        }
    
    async def _determine_analysis_type(self, query: str) -> Dict[str, Any]:
        """Determine what kind of analysis is needed"""
        prompt = f"""
Analyze this query and determine the type of data analysis needed.

Query: {query}

Return JSON:
{{
    "needs_sql": true/false,
    "needs_visualization": true/false,
    "metrics": ["list of metrics to analyze"],
    "time_range": "today/week/month/quarter/year/all",
    "aggregation": "sum/avg/count/max/min/none",
    "grouping": "field name or null"
}}
"""
        
        try:
            return await self.llm.generate_json(
                prompt=prompt,
                schema={
                    "needs_sql": "boolean",
                    "needs_visualization": "boolean",
                    "metrics": ["list"],
                    "time_range": "string",
                    "aggregation": "string",
                    "grouping": "string or null"
                }
            )
        except Exception:
            return {
                "needs_sql": False,
                "needs_visualization": True,
                "metrics": ["general"],
                "time_range": "week"
            }
    
    async def _generate_sql(self, query: str) -> str:
        """Generate SQL query from natural language"""
        prompt = f"""
Generate a SQL query for the following request.

Database Schema:
{self.schema}

User Request: {query}

Rules:
- Use standard SQL syntax
- Include appropriate WHERE clauses
- Use aggregations when asking for totals/averages
- Limit results to 1000 rows
- Add ORDER BY for meaningful ordering

Return only the SQL query, no explanation.
"""
        
        sql = await self.llm.generate(prompt=prompt)
        
        # Clean SQL
        sql = sql.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        
        return sql.strip()
    
    async def _execute_query(self, sql: str) -> List[Dict]:
        """
        Execute SQL query (returns sample data for now)
        In production, this would connect to actual database
        """
        # Return sample data based on query type
        if "sales" in sql.lower():
            return self._generate_sales_data()
        elif "ticket" in sql.lower():
            return self._generate_ticket_data()
        elif "customer" in sql.lower():
            return self._generate_customer_data()
        else:
            return self._generate_generic_data()
    
    async def _detect_patterns(
        self,
        data: List[Dict],
        query: str
    ) -> List[Dict[str, Any]]:
        """Detect patterns in data"""
        if not data:
            return []
        
        patterns = []
        
        # Look for trends
        if len(data) > 1:
            values = [d.get("value", d.get("amount", 0)) for d in data]
            
            if values[-1] > values[0]:
                change = ((values[-1] - values[0]) / values[0]) * 100 if values[0] else 0
                patterns.append({
                    "type": "trend",
                    "direction": "increasing",
                    "change_percent": round(change, 1),
                    "description": f"Values increased by {round(change, 1)}%"
                })
            elif values[-1] < values[0]:
                change = ((values[0] - values[-1]) / values[0]) * 100 if values[0] else 0
                patterns.append({
                    "type": "trend",
                    "direction": "decreasing",
                    "change_percent": round(-change, 1),
                    "description": f"Values decreased by {round(change, 1)}%"
                })
        
        # Look for anomalies
        if len(data) > 3:
            values = [d.get("value", d.get("amount", 0)) for d in data]
            avg = sum(values) / len(values)
            
            for i, v in enumerate(values):
                if abs(v - avg) > avg * 0.5:  # 50% deviation
                    patterns.append({
                        "type": "anomaly",
                        "index": i,
                        "value": v,
                        "expected": round(avg, 2),
                        "description": f"Unusual value detected: {v} (expected ~{round(avg, 2)})"
                    })
                    break  # Report first anomaly
        
        return patterns
    
    async def _generate_chart_config(
        self,
        data: List[Dict],
        query: str
    ) -> Dict[str, Any]:
        """Generate chart configuration"""
        if not data:
            return None
        
        # Determine best chart type
        chart_type = "line"  # default
        if "compare" in query.lower() or "breakdown" in query.lower():
            chart_type = "bar"
        elif "distribution" in query.lower() or "share" in query.lower():
            chart_type = "pie"
        
        # Extract x and y axes
        sample = data[0]
        x_key = None
        y_key = None
        
        for key in ["date", "month", "week", "name", "category"]:
            if key in sample:
                x_key = key
                break
        
        for key in ["value", "amount", "count", "total"]:
            if key in sample:
                y_key = key
                break
        
        if not x_key:
            x_key = list(sample.keys())[0]
        if not y_key:
            y_key = list(sample.keys())[-1]
        
        return {
            "chart_type": chart_type,
            "title": f"Analysis: {query[:50]}",
            "data": data,
            "x_axis": x_key,
            "y_axis": y_key
        }
    
    async def _summarize_analysis(
        self,
        query: str,
        data: List[Dict],
        patterns: List[Dict]
    ) -> str:
        """Generate analysis summary"""
        if not data:
            return "No data available for analysis."
        
        pattern_text = "\n".join([p["description"] for p in patterns]) if patterns else "No significant patterns detected."
        
        prompt = f"""
Summarize this data analysis in 2-3 sentences.

Query: {query}
Data Points: {len(data)}
Patterns Found: {pattern_text}

Sample Data:
{data[:3]}

Keep the summary concise and actionable.
"""
        
        return await self.llm.generate(prompt=prompt)
    
    # ========================================
    # Sample Data Generators
    # ========================================
    def _generate_sales_data(self) -> List[Dict]:
        """Generate sample sales data"""
        base_date = datetime.now() - timedelta(days=7)
        return [
            {"date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
             "amount": 10000 + (i * 1000) + ((-1) ** i * 2000),
             "orders": 50 + i * 5}
            for i in range(7)
        ]
    
    def _generate_ticket_data(self) -> List[Dict]:
        """Generate sample ticket data"""
        return [
            {"date": "2024-01-23", "open": 47, "resolved": 32, "new": 15},
            {"date": "2024-01-22", "open": 64, "resolved": 28, "new": 42},
            {"date": "2024-01-21", "open": 50, "resolved": 35, "new": 22},
        ]
    
    def _generate_customer_data(self) -> List[Dict]:
        """Generate sample customer data"""
        return [
            {"segment": "Enterprise", "count": 45, "revenue": 450000},
            {"segment": "SMB", "count": 320, "revenue": 280000},
            {"segment": "Startup", "count": 890, "revenue": 120000},
        ]
    
    def _generate_generic_data(self) -> List[Dict]:
        """Generate generic sample data"""
        return [
            {"category": "A", "value": 100},
            {"category": "B", "value": 150},
            {"category": "C", "value": 80},
        ]
    
    def _get_sample_data(self, query: str) -> List[Dict]:
        """Get sample data based on query keywords"""
        query_lower = query.lower()
        
        if "sales" in query_lower or "revenue" in query_lower:
            return self._generate_sales_data()
        elif "ticket" in query_lower or "support" in query_lower:
            return self._generate_ticket_data()
        elif "customer" in query_lower:
            return self._generate_customer_data()
        else:
            return self._generate_generic_data()
