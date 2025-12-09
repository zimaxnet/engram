"""
Agent Workflow

The main Temporal workflow for agent execution.
This is the "Spine" of the Brain + Spine architecture.

The workflow provides:
- Durable execution (survives crashes)
- Automatic retries with backoff
- Human-in-the-loop signals
- Time-travel debugging
- Long-running support (can wait days for approval)
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities (with sandbox warning suppression)
with workflow.unsafe.imports_passed_through():
    from backend.workflows.activities import (
        MemoryEnrichInput,
        MemoryPersistInput,
        ReasoningInput,
        agent_reasoning_activity,
        enrich_memory_activity,
        initialize_context_activity,
        persist_memory_activity,
        send_notification_activity,
        validate_response_activity,
    )


logger = logging.getLogger(__name__)


# =============================================================================
# Workflow Input/Output
# =============================================================================


@dataclass
class AgentWorkflowInput:
    """Input to start an agent workflow"""

    user_id: str
    tenant_id: str
    session_id: str
    agent_id: str
    user_message: str


@dataclass
class AgentWorkflowOutput:
    """Output from agent workflow"""

    response: str
    agent_id: str
    session_id: str
    tokens_used: int
    success: bool
    error: Optional[str] = None
    context_json: Optional[str] = None


@dataclass
class ConversationTurn:
    """A single turn in a conversation"""

    user_message: str
    agent_response: str
    agent_id: str
    tokens_used: int


# =============================================================================
# Retry Policies
# =============================================================================

# Policy for LLM calls - more retries, exponential backoff
LLM_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=5,
)

# Policy for memory operations - fewer retries
MEMORY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=3,
)

# Policy for notifications - fire and forget
NOTIFICATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_attempts=2,
)


# =============================================================================
# Signals for Human-in-the-Loop
# =============================================================================


@dataclass
class ApprovalSignal:
    """Signal to approve or reject a pending action"""

    approved: bool
    feedback: Optional[str] = None
    approver_id: Optional[str] = None


@dataclass
class UserInputSignal:
    """Signal with additional user input"""

    content: str


# =============================================================================
# Agent Workflow
# =============================================================================


@workflow.defn
class AgentWorkflow:
    """
    Main workflow for agent execution.

    This workflow:
    1. Initializes the context (Security layer)
    2. Enriches with memory (Episodic + Semantic layers)
    3. Runs agent reasoning (Brain)
    4. Validates the response
    5. Persists to memory
    6. Returns the response

    Supports human-in-the-loop via signals for:
    - Approval of sensitive actions
    - Additional input requests
    """

    def __init__(self):
        self._pending_approval: Optional[ApprovalSignal] = None
        self._additional_input: Optional[str] = None
        self._context_json: Optional[str] = None

    # -------------------------------------------------------------------------
    # Signal Handlers
    # -------------------------------------------------------------------------

    @workflow.signal
    async def approve(self, signal: ApprovalSignal):
        """Receive approval/rejection signal"""
        workflow.logger.info(f"Received approval signal: approved={signal.approved}")
        self._pending_approval = signal

    @workflow.signal
    async def provide_input(self, signal: UserInputSignal):
        """Receive additional user input"""
        workflow.logger.info("Received additional input")
        self._additional_input = signal.content

    # -------------------------------------------------------------------------
    # Query Handlers
    # -------------------------------------------------------------------------

    @workflow.query
    def get_status(self) -> str:
        """Query current workflow status"""
        if self._pending_approval is not None:
            return "awaiting_approval"
        if self._additional_input is not None:
            return "received_input"
        return "processing"

    @workflow.query
    def get_context(self) -> Optional[str]:
        """Query current context state"""
        return self._context_json

    # -------------------------------------------------------------------------
    # Main Workflow
    # -------------------------------------------------------------------------

    @workflow.run
    async def run(self, input: AgentWorkflowInput) -> AgentWorkflowOutput:
        """
        Execute the agent workflow.

        This is the durable execution path for processing a user message.
        """
        workflow.logger.info(
            f"Starting agent workflow: session={input.session_id}, "
            f"agent={input.agent_id}"
        )

        try:
            # Step 1: Initialize Context
            self._context_json = await workflow.execute_activity(
                initialize_context_activity,
                args=[input.user_id, input.tenant_id, input.session_id, input.agent_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=MEMORY_RETRY_POLICY,
            )

            # Step 2: Enrich with Memory
            enrich_result = await workflow.execute_activity(
                enrich_memory_activity,
                MemoryEnrichInput(
                    context_json=self._context_json, query=input.user_message
                ),
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=MEMORY_RETRY_POLICY,
            )

            if enrich_result.success:
                self._context_json = enrich_result.context_json
                workflow.logger.info(
                    f"Memory enriched: {enrich_result.facts_retrieved} facts, "
                    f"{enrich_result.entities_retrieved} entities"
                )
            else:
                workflow.logger.warning(
                    f"Memory enrichment failed: {enrich_result.error}"
                )

            # Step 3: Agent Reasoning (the Brain)
            reasoning_result = await workflow.execute_activity(
                agent_reasoning_activity,
                ReasoningInput(
                    context_json=self._context_json,
                    user_message=input.user_message,
                    agent_id=input.agent_id,
                ),
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=LLM_RETRY_POLICY,
            )

            if not reasoning_result.success:
                workflow.logger.error(
                    f"Agent reasoning failed: {reasoning_result.error}"
                )
                return AgentWorkflowOutput(
                    response=reasoning_result.response,
                    agent_id=input.agent_id,
                    session_id=input.session_id,
                    tokens_used=0,
                    success=False,
                    error=reasoning_result.error,
                )

            self._context_json = reasoning_result.context_json
            response = reasoning_result.response

            # Step 4: Validate Response
            is_valid, validation_error = await workflow.execute_activity(
                validate_response_activity,
                args=[response, self._context_json],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=MEMORY_RETRY_POLICY,
            )

            if not is_valid:
                workflow.logger.warning(
                    f"Response validation failed: {validation_error}"
                )
                response = (
                    "I generated a response but it didn't pass validation. "
                    "Let me try to rephrase. Could you please ask your question again?"
                )

            # Step 5: Persist to Memory
            persist_result = await workflow.execute_activity(
                persist_memory_activity,
                MemoryPersistInput(context_json=self._context_json),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=MEMORY_RETRY_POLICY,
            )

            if not persist_result.success:
                workflow.logger.warning(
                    f"Memory persistence failed: {persist_result.error}"
                )

            # Success!
            workflow.logger.info(
                f"Workflow completed: tokens={reasoning_result.tokens_used}"
            )

            return AgentWorkflowOutput(
                response=response,
                agent_id=input.agent_id,
                session_id=input.session_id,
                tokens_used=reasoning_result.tokens_used,
                success=True,
                context_json=self._context_json,
            )

        except Exception as e:
            workflow.logger.error(f"Workflow failed with exception: {e}")
            return AgentWorkflowOutput(
                response="I apologize, but an unexpected error occurred. Please try again.",
                agent_id=input.agent_id,
                session_id=input.session_id,
                tokens_used=0,
                success=False,
                error=str(e),
            )


# =============================================================================
# Long-Running Conversation Workflow
# =============================================================================


@workflow.defn
class ConversationWorkflow:
    """
    Long-running workflow for multi-turn conversations.

    Unlike AgentWorkflow (single turn), this workflow:
    - Maintains conversation state across multiple turns
    - Can wait indefinitely for user input
    - Supports conversation history
    - Can run for days/weeks
    """

    def __init__(self):
        self._context_json: Optional[str] = None
        self._turns: list[ConversationTurn] = []
        self._current_agent: str = "elena"
        self._awaiting_input: bool = False
        self._new_message: Optional[str] = None
        self._should_end: bool = False

    @workflow.signal
    async def send_message(self, message: str):
        """Receive a new message from the user"""
        self._new_message = message
        self._awaiting_input = False

    @workflow.signal
    async def switch_agent(self, agent_id: str):
        """Switch to a different agent"""
        self._current_agent = agent_id

    @workflow.signal
    async def end_conversation(self):
        """End the conversation"""
        self._should_end = True

    @workflow.query
    def get_history(self) -> list[dict]:
        """Get conversation history"""
        return [
            {
                "user": t.user_message,
                "assistant": t.agent_response,
                "agent": t.agent_id,
                "tokens": t.tokens_used,
            }
            for t in self._turns
        ]

    @workflow.query
    def get_turn_count(self) -> int:
        """Get number of turns"""
        return len(self._turns)

    @workflow.run
    async def run(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
        initial_agent: str = "elena",
    ) -> dict:
        """
        Run the conversation workflow.

        This workflow continues until end_conversation signal is received.
        """
        self._current_agent = initial_agent

        # Initialize context
        self._context_json = await workflow.execute_activity(
            initialize_context_activity,
            args=[user_id, tenant_id, session_id, initial_agent],
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info(f"Conversation started: {session_id}")

        # Main conversation loop
        while not self._should_end:
            # Wait for next message (can wait indefinitely)
            self._awaiting_input = True
            await workflow.wait_condition(
                lambda: self._new_message is not None or self._should_end
            )

            if self._should_end:
                break

            # Process the message
            message = self._new_message
            self._new_message = None

            if message:
                # Run single turn as child workflow
                turn_output = await workflow.execute_child_workflow(
                    AgentWorkflow.run,
                    AgentWorkflowInput(
                        user_id=user_id,
                        tenant_id=tenant_id,
                        session_id=session_id,
                        agent_id=self._current_agent,
                        user_message=message,
                    ),
                    id=f"{session_id}-turn-{len(self._turns)}",
                )

                # Record the turn
                self._turns.append(
                    ConversationTurn(
                        user_message=message,
                        agent_response=turn_output.response,
                        agent_id=turn_output.agent_id,
                        tokens_used=turn_output.tokens_used,
                    )
                )

                # Update context
                if turn_output.context_json:
                    self._context_json = turn_output.context_json

        # Conversation ended
        workflow.logger.info(f"Conversation ended: {len(self._turns)} turns")

        return {
            "session_id": session_id,
            "turns": len(self._turns),
            "total_tokens": sum(t.tokens_used for t in self._turns),
        }


# =============================================================================
# Approval Workflow
# =============================================================================


@workflow.defn
class ApprovalWorkflow:
    """
    Workflow for actions requiring human approval.

    Use cases:
    - Approving agent responses before sending
    - Approving tool executions
    - Approving data access
    """

    def __init__(self):
        self._approval: Optional[ApprovalSignal] = None

    @workflow.signal
    async def approve(self, signal: ApprovalSignal):
        """Receive approval decision"""
        self._approval = signal

    @workflow.query
    def is_pending(self) -> bool:
        """Check if still awaiting approval"""
        return self._approval is None

    @workflow.run
    async def run(
        self,
        action_description: str,
        requester_id: str,
        approver_ids: list[str],
        timeout_hours: int = 24,
    ) -> tuple[bool, Optional[str]]:
        """
        Request approval for an action.

        Args:
            action_description: What needs approval
            requester_id: Who requested it
            approver_ids: Who can approve
            timeout_hours: How long to wait

        Returns:
            Tuple of (approved, feedback)
        """
        # Send notification to approvers
        for approver_id in approver_ids:
            await workflow.execute_activity(
                send_notification_activity,
                args=[
                    approver_id,
                    f"Approval needed: {action_description}",
                    "approval_request",
                ],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=NOTIFICATION_RETRY_POLICY,
            )

        workflow.logger.info(f"Waiting for approval: {action_description[:50]}...")

        # Wait for approval (or timeout)
        try:
            await workflow.wait_condition(
                lambda: self._approval is not None,
                timeout=timedelta(hours=timeout_hours),
            )
        except TimeoutError:
            workflow.logger.warning("Approval timed out")
            return False, "Approval request timed out"

        # Return decision
        if self._approval:
            return self._approval.approved, self._approval.feedback

        return False, "No approval received"
