"""
========================================
Analyst Agent
========================================
Analyzes data, generates SQL, detects patterns
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import text

from app.llm.gemini import GeminiClient
from app.llm.prompts import ANALYST_AGENT_PROMPT
from app.database.connection import get_db_session

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
        
        # Real database schema (matches models.py)
        self.schema = """
        Tables:
        - sales (id, customer_id, product_id, amount, quantity, region, date)
        - customers (id, name, email, segment, created_at, last_purchase)
        - products (id, name, category, price, cost, inventory)
        - support_tickets (id, customer_id, subject, status, priority, created_at, resolved_at)
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
        
        sql_query = None
        # Generate SQL if database query needed
        if analysis_type.get("needs_sql"):
            sql_query = await self._generate_sql(query)
            try:
                data = await self._execute_query(sql_query)
            except Exception as e:
                print(f"SQL Execution Error: {e}")
                # Fallback to empty list or simple error message in data
                data = []
        else:
            # If no SQL needed, maybe just visualization of derived data?
            # For now, default to empty or specific logic
            data = []
        
        # Detect patterns
        patterns = await self._detect_patterns(data, query)
        
        # Generate chart if visualization would help
        chart = None
        if analysis_type.get("needs_visualization") and data:
            chart = await self._generate_chart_config(data, query)
        
        # Generate summary
        summary = await self._summarize_analysis(query, data, patterns)
        
        return {
            "data": data,
            "patterns": patterns,
            "chart": chart,
            "summary": summary,
            "action": f"Analyzed {len(data)} data points",
            "sql_query": sql_query
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
                "needs_sql": True, # Default to try SQL
                "needs_visualization": True,
                "metrics": ["general"],
                "time_range": "all"
            }
    
    async def _generate_sql(self, query: str) -> str:
        """Generate SQL query from natural language"""
        prompt = f"""
Generate a SQL query for the following request.

Database Schema:
{self.schema}

User Request: {query}

Rules:
- Use standard SQL syntax (SQLite compatible)
- Include appropriate WHERE clauses
- Use aggregations when asking for totals/averages
- Limit results to 100 rows
- Add ORDER BY for meaningful ordering
- Return dates as strings if needed

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
        Execute SQL query against the real database
        """
        print(f"📊 Executing SQL: {sql}")
        async with get_db_session() as session:
            result = await session.execute(text(sql))
            
            # Convert rows to list of dicts
            columns = result.keys()
            rows = []
            for row in result.all():
                row_dict = {}
                for i, column in enumerate(columns):
                    val = row[i]
                    # Handle datetime serialization if needed
                    if isinstance(val, datetime):
                        val = val.isoformat()
                    row_dict[column] = val
                rows.append(row_dict)
            
            return rows

    async def _detect_patterns(
        self,
        data: List[Dict],
        query: str
    ) -> List[Dict[str, Any]]:
        """Detect patterns in data"""
        if not data:
            return []
        
        patterns = []
        
        # Look for trends (simple logic for now)
        if len(data) > 1:
            # Try to find a numerical column
            value_key = None
            for key in data[0].keys():
                if isinstance(data[0][key], (int, float)) and key not in ["id", "product_id", "customer_id"]:
                    value_key = key
                    break
            
            if value_key:
                values = [d[value_key] for d in data]
                if values[-1] > values[0]:
                    change = ((values[-1] - values[0]) / values[0]) * 100 if values[0] else 0
                    patterns.append({
                        "type": "trend",
                        "direction": "increasing",
                        "change_percent": round(change, 1),
                        "description": f"{value_key} increased by {round(change, 1)}%"
                    })
                elif values[-1] < values[0]:
                    change = ((values[0] - values[-1]) / values[0]) * 100 if values[0] else 0
                    patterns.append({
                        "type": "trend",
                        "direction": "decreasing",
                        "change_percent": round(-change, 1),
                        "description": f"{value_key} decreased by {round(change, 1)}%"
                    })
        
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
        
        # Heuristics for axes
        for key in sample.keys():
            if key in ["date", "month", "week", "name", "category", "region"]:
                x_key = key
                break
        
        for key in sample.keys():
            if isinstance(sample[key], (int, float)) and key not in ["id", "customer_id", "product_id"]:
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
            return "No data available for analysis. The query returned no results."
        
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
