"""
LangGraph State Machine for the Autonomous Data Intelligence Agent.
Orchestrates:
IntentParser -> SourceDiscovery -> JevExtractor -> VectorDeduplication -> State Finalization
Provides synchronous and asynchronous streaming hooks for real-time WebSocket broadcasting.
"""
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Callable, Optional

from langgraph.graph import StateGraph, END
from ai_engine.state import WorkflowState, ExtractedRecord
from ai_engine.intent_parser import IntentParser
from ai_engine.source_discovery import SourceDiscovery
from ai_engine.jev_extractor import JevDeterministicExtractor
from ai_engine.vector_deduplication import VectorDeduplicator

logger = logging.getLogger("WorkflowGraph")

class DataIntelligenceWorkflow:
    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        confidence_threshold: float = 80.0,
        similarity_threshold: float = 0.82
    ):
        self.intent_parser = IntentParser()
        self.source_discovery = SourceDiscovery(tavily_api_key=tavily_api_key)
        self.jev_extractor = JevDeterministicExtractor(confidence_threshold=confidence_threshold)
        self.vector_deduplicator = VectorDeduplicator(similarity_threshold=similarity_threshold)
        self.app = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(WorkflowState)

        # Register nodes
        graph.add_node("intent_parser", self._node_intent_parser)
        graph.add_node("source_discovery", self._node_source_discovery)
        graph.add_node("data_extraction", self._node_data_extraction)
        graph.add_node("vector_deduplication", self._node_vector_deduplication)
        graph.add_node("human_review_evaluation", self._node_human_review)

        # Set entry point
        graph.set_entry_point("intent_parser")

        # Define standard transitions
        graph.add_edge("intent_parser", "source_discovery")
        graph.add_edge("source_discovery", "data_extraction")
        graph.add_edge("data_extraction", "vector_deduplication")
        graph.add_edge("vector_deduplication", "human_review_evaluation")

        # Conditional edge: if review items exceed threshold or all verified
        graph.add_conditional_edges(
            "human_review_evaluation",
            self._route_after_review,
            {
                "proceed_to_end": END,
                "flag_for_review": END
            }
        )

        return graph.compile()

    # --- Node Implementations ---

    def _node_intent_parser(self, state: WorkflowState) -> Dict[str, Any]:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node": "intent_parser",
            "message": f"Analyzing prompt: '{state.user_prompt}' to construct target schema"
        }
        schema = self.intent_parser.parse_intent(state.user_prompt)
        return {
            "current_node": "intent_parser",
            "target_schema": schema,
            "status": "running",
            "execution_logs": state.execution_logs + [log_entry]
        }

    async def _node_source_discovery(self, state: WorkflowState) -> Dict[str, Any]:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node": "source_discovery",
            "message": f"Querying search APIs for permitted URLs matching '{state.user_prompt}'"
        }
        sources = await self.source_discovery.search(state.user_prompt, max_results=4)
        pending_urls = [s["url"] for s in sources]

        # Fetch actual contents
        raw_documents = []
        for s in sources:
            doc = await self.source_discovery.fetch_document_content(s["url"])
            if not doc.get("text"):
                doc["text"] = s.get("content", "")
            raw_documents.append(doc)

        log_fetched = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node": "source_discovery",
            "message": f"Discovered {len(pending_urls)} verified source domains and fetched content payloads"
        }

        return {
            "current_node": "source_discovery",
            "pending_urls": pending_urls,
            "raw_documents": raw_documents,
            "execution_logs": state.execution_logs + [log_entry, log_fetched]
        }

    def _node_data_extraction(self, state: WorkflowState) -> Dict[str, Any]:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node": "data_extraction",
            "message": f"Invoking Jev deterministic extraction engine across {len(state.raw_documents)} documents"
        }

        extracted_records = []
        for doc in state.raw_documents:
            records = self.jev_extractor.extract_from_document(
                doc=doc,
                schema=state.target_schema,
                query=state.user_prompt
            )
            extracted_records.extend(records)

        log_extracted = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node": "data_extraction",
            "message": f"Jev extracted {len(extracted_records)} typed records with calibrated confidence scores"
        }

        return {
            "current_node": "data_extraction",
            "processed_data": extracted_records,
            "execution_logs": state.execution_logs + [log_entry, log_extracted]
        }

    def _node_vector_deduplication(self, state: WorkflowState) -> Dict[str, Any]:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node": "vector_deduplication",
            "message": f"Embedding entities into vector space and calculating cosine similarity matrix"
        }

        deduped_records, pruned_count = self.vector_deduplicator.deduplicate(state.processed_data)

        log_deduped = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node": "vector_deduplication",
            "message": f"Vector deduplication complete: {len(deduped_records)} unique entities retained ({pruned_count} duplicates removed)"
        }

        return {
            "current_node": "vector_deduplication",
            "deduplicated_data": deduped_records,
            "metrics": {
                **state.metrics,
                "total_extracted": len(state.processed_data),
                "total_deduplicated": len(deduped_records),
                "duplicates_pruned": pruned_count
            },
            "execution_logs": state.execution_logs + [log_entry, log_deduped]
        }

    def _node_human_review(self, state: WorkflowState) -> Dict[str, Any]:
        review_count = sum(1 for r in state.deduplicated_data if r.human_review_required)
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node": "human_review_evaluation",
            "message": f"Review evaluation: {review_count} records below {state.confidence_threshold}% confidence threshold flagged for human review"
        }

        return {
            "current_node": "human_review_evaluation",
            "status": "completed",
            "metrics": {
                **state.metrics,
                "human_review_count": review_count,
                "completed_at": datetime.now(timezone.utc).isoformat()
            },
            "execution_logs": state.execution_logs + [log_entry]
        }

    def _route_after_review(self, state: WorkflowState) -> str:
        review_count = state.metrics.get("human_review_count", 0)
        if review_count > 0:
            return "flag_for_review"
        return "proceed_to_end"

    async def run_pipeline(
        self,
        prompt: str,
        workflow_id: Optional[str] = None,
        confidence_threshold: float = 80.0,
        telemetry_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> WorkflowState:
        """
        Executes the LangGraph agent pipeline end-to-end with live step-by-step telemetry callbacks.
        """
        w_id = workflow_id or f"wf_{uuid.uuid4().hex[:10]}"
        state = WorkflowState(
            workflow_id=w_id,
            user_prompt=prompt,
            confidence_threshold=confidence_threshold,
            status="running"
        )

        async def broadcast(node_name: str, step_state: WorkflowState):
            if telemetry_callback:
                try:
                    await telemetry_callback({
                        "workflow_id": step_state.workflow_id,
                        "node": node_name,
                        "status": step_state.status,
                        "logs": step_state.execution_logs[-1] if step_state.execution_logs else None,
                        "records_count": len(step_state.deduplicated_data or step_state.processed_data),
                        "schema": step_state.target_schema.model_dump() if step_state.target_schema else None
                    })
                except Exception as e:
                    logger.error(f"Telemetry callback failed: {e}")

        # Step 1: Intent Parser
        res_intent = self._node_intent_parser(state)
        state = state.model_copy(update=res_intent)
        await broadcast("intent_parser", state)

        # Step 2: Source Discovery
        res_source = await self._node_source_discovery(state)
        state = state.model_copy(update=res_source)
        await broadcast("source_discovery", state)

        # Step 3: Data Extraction
        res_extract = self._node_data_extraction(state)
        state = state.model_copy(update=res_extract)
        await broadcast("data_extraction", state)

        # Step 4: Vector Deduplication
        res_dedup = self._node_vector_deduplication(state)
        state = state.model_copy(update=res_dedup)
        await broadcast("vector_deduplication", state)

        # Step 5: Human Review Evaluation
        res_review = self._node_human_review(state)
        state = state.model_copy(update=res_review)
        await broadcast("completed", state)

        return state
