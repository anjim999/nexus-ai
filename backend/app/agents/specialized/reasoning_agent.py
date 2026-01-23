"""
========================================
Reasoning Agent
========================================
Synthesizes information and draws conclusions
"""

from typing import Dict, Any, List, Optional

from app.llm.gemini import GeminiClient
from app.llm.prompts import REASONING_AGENT_PROMPT


class ReasoningAgent:
    """
    Reasoning Agent
    
    Responsibilities:
    - Synthesize information from multiple sources
    - Draw logical conclusions
    - Explain causality and correlations
    - Assess confidence levels
    - Generate actionable insights
    """
    
    def __init__(self, llm: GeminiClient):
        self.llm = llm
        self.system_prompt = REASONING_AGENT_PROMPT
    
    async def reason(
        self,
        query: str,
        documents: List[Dict] = None,
        data: List[Dict] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Reason through available information to answer query
        
        Args:
            query: User's question
            documents: Relevant documents from Research Agent
            data: Data from Analyst Agent
            context: Additional context
            
        Returns:
            Response with reasoning, confidence, and insights
        """
        # Build context from all sources
        combined_context = self._build_context(documents, data, context)
        
        # Generate reasoning chain
        reasoning = await self._generate_reasoning(query, combined_context)
        
        # Generate final response
        response = await self._generate_response(query, combined_context, reasoning)
        
        # Assess confidence
        confidence = await self._assess_confidence(query, combined_context, response)
        
        # Extract insights
        insights = await self._extract_insights(query, response, combined_context)
        
        return {
            "response": response,
            "reasoning": reasoning,
            "confidence": confidence,
            "insights": insights
        }
    
    def _build_context(
        self,
        documents: List[Dict] = None,
        data: List[Dict] = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Build combined context string"""
        parts = []
        
        # Add document context
        if documents:
            doc_text = "\n".join([
                f"- {doc.get('source', 'Unknown')}: {doc.get('content', '')[:300]}"
                for doc in documents[:5]  # Limit to top 5
            ])
            parts.append(f"**Relevant Documents:**\n{doc_text}")
        
        # Add data context
        if data:
            import json
            data_text = json.dumps(data[:10], indent=2)  # Limit and format
            parts.append(f"**Data Analysis:**\n```\n{data_text}\n```")
        
        # Add additional context
        if context:
            if "query_analysis" in context:
                qa = context["query_analysis"]
                parts.append(f"**Query Intent:** {qa.get('intent', 'Unknown')}")
        
        return "\n\n".join(parts) if parts else "No additional context available."
    
    async def _generate_reasoning(self, query: str, context: str) -> str:
        """Generate step-by-step reasoning"""
        prompt = f"""
Think through this problem step by step.

User Question: {query}

Available Information:
{context}

Provide your reasoning process:
1. What is the user really asking?
2. What relevant information do we have?
3. What can we infer or conclude?
4. What are the limitations or caveats?

Show your thinking clearly.
"""
        
        reasoning = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt
        )
        
        return reasoning
    
    async def _generate_response(
        self,
        query: str,
        context: str,
        reasoning: str
    ) -> str:
        """Generate the final response"""
        prompt = f"""
Based on your reasoning, provide a clear and helpful response to the user.

User Question: {query}

Your Reasoning:
{reasoning}

Context:
{context}

Guidelines:
- Be direct and clear
- Include specific data points when available  
- Acknowledge uncertainty if present
- Suggest next steps if appropriate
- Keep the response conversational but professional

Provide the response:
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt
        )
        
        return response
    
    async def _assess_confidence(
        self,
        query: str,
        context: str,
        response: str
    ) -> float:
        """Assess confidence in the response"""
        prompt = f"""
Assess your confidence in this response on a scale of 0.0 to 1.0.

Question: {query}

Response: {response}

Context Available: {len(context)} characters

Consider:
- Was there sufficient data to answer?
- Are there any assumptions made?
- Could the answer be verified?
- Are there contradictions in the sources?

Return only a number between 0.0 and 1.0.
"""
        
        try:
            result = await self.llm.generate(prompt=prompt)
            # Extract number from response
            import re
            numbers = re.findall(r'0\.\d+|1\.0|0|1', result)
            if numbers:
                return min(float(numbers[0]), 1.0)
            return 0.7  # Default confidence
        except Exception:
            return 0.7
    
    async def _extract_insights(
        self,
        query: str,
        response: str,
        context: str
    ) -> List[str]:
        """Extract key insights from the analysis"""
        prompt = f"""
Extract 2-3 key insights from this analysis.

Question: {query}
Response: {response}

Return as a JSON array of strings:
["insight 1", "insight 2", "insight 3"]

Focus on actionable or surprising findings.
"""
        
        try:
            result = await self.llm.generate_json(
                prompt=prompt,
                schema=["list of strings"]
            )
            return result if isinstance(result, list) else []
        except Exception:
            return []
    
    async def compare_and_contrast(
        self,
        items: List[Dict],
        criteria: List[str]
    ) -> Dict[str, Any]:
        """Compare multiple items based on criteria"""
        import json
        
        prompt = f"""
Compare these items based on the given criteria.

Items:
{json.dumps(items, indent=2)}

Criteria: {', '.join(criteria)}

Provide:
1. Comparison table (conceptually)
2. Key differences
3. Key similarities
4. Recommendation

Format as JSON:
{{
    "comparison": [...],
    "differences": [...],
    "similarities": [...],
    "recommendation": "..."
}}
"""
        
        return await self.llm.generate_json(
            prompt=prompt,
            schema={
                "comparison": "list",
                "differences": "list",
                "similarities": "list",
                "recommendation": "string"
            }
        )
    
    async def generate_hypothesis(
        self,
        observation: str,
        context: str
    ) -> Dict[str, Any]:
        """Generate hypotheses to explain an observation"""
        prompt = f"""
Given this observation, generate possible hypotheses.

Observation: {observation}

Context: {context}

For each hypothesis, provide:
1. The hypothesis
2. Supporting evidence
3. How to test/validate it
4. Likelihood (0-1)

Return as JSON:
{{
    "hypotheses": [
        {{
            "hypothesis": "...",
            "evidence": "...",
            "validation": "...",
            "likelihood": 0.X
        }}
    ]
}}
"""
        
        return await self.llm.generate_json(
            prompt=prompt,
            schema={
                "hypotheses": [{
                    "hypothesis": "string",
                    "evidence": "string",
                    "validation": "string",
                    "likelihood": "number"
                }]
            }
        )
