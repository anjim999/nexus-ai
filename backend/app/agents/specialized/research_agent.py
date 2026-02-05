# Research Agent
# Searches documents and retrieves relevant information

from typing import Dict, Any, List, Optional

from app.llm.gemini import GeminiClient
from app.rag.retriever import Retriever
from app.llm.prompts import RESEARCH_AGENT_PROMPT


class ResearchAgent:
    # Research Agent
    # Responsibilities: Search documents, extract info, summarize findings, cite sources
    
    def __init__(self, llm: GeminiClient, retriever: Retriever):
        self.llm = llm
        self.retriever = retriever
        self.system_prompt = RESEARCH_AGENT_PROMPT
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        file_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        # Search for relevant documents
        print(f"\n🔍 Research Agent Searching: '{query}'")
        # Get relevant documents
        try:
            documents = await self.retriever.retrieve(
                query=query,
                top_k=top_k,
                file_filter=file_filter
            )
        except Exception as e:
            print(f"Research Agent Retrieval Error: {e}")
            return {
                "documents": [],
                "sources": [],
                "summary": f"Search failed due to an error: {str(e)}",
                "confidence": 0.0
            }
        
        if not documents:
            return {
                "documents": [],
                "sources": [],
                "summary": "No relevant documents found in the knowledge base.",
                "confidence": 0.0
            }
        
        # Format sources
        sources = []
        for doc in documents:
            sources.append({
                "type": "document",
                "name": doc["source"],
                "page": doc.get("page"),
                "relevance": round(doc["score"], 2),
                "snippet": doc["content"][:150] + "..." if len(doc["content"]) > 150 else doc["content"]
            })
        
        # Generate summary using LLM
        context = "\n\n".join([
            f"[{doc['source']}]: {doc['content']}"
            for doc in documents
        ])
        
        summary_prompt = f"""
Based on the following document excerpts, provide a brief summary of the relevant information found.

Query: {query}

Documents:
{context}

Provide:
1. A 2-3 sentence summary of what was found
2. Key facts or data points
3. Confidence in the relevance (high/medium/low)

Keep the summary concise and factual.
"""
        
        try:
            summary = await self.llm.generate(
                prompt=summary_prompt,
                system_prompt=self.system_prompt
            )
        except Exception:
            summary = f"Found {len(documents)} relevant documents."
        
        return {
            "documents": documents,
            "sources": sources,
            "summary": summary,
            "confidence": self._calculate_confidence(documents)
        }
    
    async def extract_facts(
        self,
        query: str,
        documents: List[Dict]
    ) -> List[Dict[str, Any]]:
        # Extract specific facts from documents
        if not documents:
            return []
        
        context = "\n\n".join([
            f"[Source: {doc['source']}]\n{doc['content']}"
            for doc in documents
        ])
        
        prompt = f"""
Extract specific facts related to this query from the documents.

Query: {query}

Documents:
{context}

Return a JSON array of facts:
[
    {{"fact": "...", "source": "...", "confidence": 0.X}},
    ...
]

Only include facts directly supported by the documents.
"""
        
        try:
            result = await self.llm.generate_json(
                prompt=prompt,
                schema=[{"fact": "string", "source": "string", "confidence": "number"}]
            )
            return result if isinstance(result, list) else []
        except Exception:
            return []
    
    async def compare_documents(
        self,
        query: str,
        doc_ids: List[str]
    ) -> Dict[str, Any]:
        # Compare information across multiple documents
        # Fetch documents
        all_docs = await self.retriever.retrieve(query, top_k=20)
        
        # Filter by doc_ids
        filtered = [d for d in all_docs if d.get("doc_id") in doc_ids]
        
        if len(filtered) < 2:
            return {
                "comparison": "Need at least 2 documents to compare",
                "documents": filtered
            }
        
        context = "\n\n---\n\n".join([
            f"Document: {doc['source']}\n{doc['content']}"
            for doc in filtered
        ])
        
        prompt = f"""
Compare the following documents based on the query.

Query: {query}

{context}

Provide:
1. Key similarities
2. Key differences
3. Which document is more relevant/comprehensive
4. Any contradictions found
"""
        
        comparison = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt
        )
        
        return {
            "comparison": comparison,
            "documents": filtered
        }
    
    def _calculate_confidence(self, documents: List[Dict]) -> float:
        # Calculate overall confidence based on search results
        if not documents:
            return 0.0
        
        # Average relevance score
        avg_score = sum(d["score"] for d in documents) / len(documents)
        
        # Adjust based on number of documents
        if len(documents) >= 3:
            confidence_boost = 0.1
        elif len(documents) >= 1:
            confidence_boost = 0.05
        else:
            confidence_boost = 0.0
        
        return min(avg_score + confidence_boost, 1.0)
