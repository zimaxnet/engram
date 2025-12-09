import pytest
from datetime import timedelta
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions

from backend.workflows.activities import (
    MemoryEnrichInput,
    MemoryEnrichOutput,
    MemoryPersistInput,
    MemoryPersistOutput,
    ReasoningInput,
    ReasoningOutput,
    initialize_context_activity,
    enrich_memory_activity,
    agent_reasoning_activity,
    validate_response_activity,
    persist_memory_activity,
    send_notification_activity,
)
from backend.workflows.agent_workflow import (
    AgentWorkflow,
    AgentWorkflowInput,
    ConversationWorkflow,
    ApprovalWorkflow,
    ApprovalSignal,
    UserInputSignal,
)

# =============================================================================
# Mock Activities
# =============================================================================

@activity.defn(name="initialize_context_activity")
async def mock_initialize_context(
    user_id: str, tenant_id: str, session_id: str, agent_id: str
) -> str:
    return '{"mock": "context"}'

@activity.defn(name="enrich_memory_activity")
async def mock_enrich_memory(input: MemoryEnrichInput) -> MemoryEnrichOutput:
    return MemoryEnrichOutput(
        context_json=input.context_json,
        facts_retrieved=1,
        entities_retrieved=1,
        success=True
    )

@activity.defn(name="agent_reasoning_activity")
async def mock_agent_reasoning(input: ReasoningInput) -> ReasoningOutput:
    return ReasoningOutput(
        response=f"Mock response to: {input.user_message}",
        context_json=input.context_json,
        tokens_used=100,
        success=True
    )

@activity.defn(name="validate_response_activity")
async def mock_validate_response(response: str, context_json: str) -> tuple[bool, str]:
    return True, ""

@activity.defn(name="persist_memory_activity")
async def mock_persist_memory(input: MemoryPersistInput) -> MemoryPersistOutput:
    return MemoryPersistOutput(success=True)

@activity.defn(name="send_notification_activity")
async def mock_send_notification(user_id: str, message: str, notification_type: str = "info") -> bool:
    return True

# =============================================================================
# Tests
# =============================================================================

# Configure runner to pass through backend modules to avoid sandbox issues with Pydantic/datetime
runner = SandboxedWorkflowRunner(
    restrictions=SandboxRestrictions.default.with_passthrough_modules(
        "backend", "pydantic"
    )
)

@pytest.mark.asyncio
async def test_agent_workflow_happy_path():
    """Test the single-turn agent workflow happy path."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[AgentWorkflow],
            activities=[
                mock_initialize_context,
                mock_enrich_memory,
                mock_agent_reasoning,
                mock_validate_response,
                mock_persist_memory
            ],
            workflow_runner=runner
        ):
            result = await env.client.execute_workflow(
                AgentWorkflow.run,
                AgentWorkflowInput(
                    user_id="test-user",
                    tenant_id="test-tenant",
                    session_id="test-session",
                    agent_id="elena",
                    user_message="Hello"
                ),
                id="test-agent-workflow",
                task_queue="test-queue",
            )

            assert result.success is True
            assert result.response == "Mock response to: Hello"
            assert result.tokens_used == 100

@pytest.mark.asyncio
async def test_conversation_workflow():
    """Test the long-running conversation workflow."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[ConversationWorkflow, AgentWorkflow],
            activities=[
                mock_initialize_context,
                mock_enrich_memory,
                mock_agent_reasoning,
                mock_validate_response,
                mock_persist_memory
            ],
            workflow_runner=runner
        ):
            # Start conversation
            handle = await env.client.start_workflow(
                ConversationWorkflow.run,
                args=["test-user", "test-tenant", "test-session", "elena"],
                id="test-conversation-workflow",
                task_queue="test-queue",
            )

            # Send first message
            await handle.signal(ConversationWorkflow.send_message, "First message")
            
            # Wait a bit for processing (virtual time)
            await env.sleep(2) 
            
            # Send second message
            await handle.signal(ConversationWorkflow.send_message, "Second message")
            await env.sleep(2)

            # Query history
            history = await handle.query(ConversationWorkflow.get_history)
            assert len(history) == 2
            assert history[0]["user"] == "First message"
            assert history[0]["assistant"] == "Mock response to: First message"
            assert history[1]["user"] == "Second message"

            # End conversation
            await handle.signal(ConversationWorkflow.end_conversation)
            
            # Wait for result
            result = await handle.result()
            assert result["turns"] == 2
            assert result["total_tokens"] == 200

@pytest.mark.asyncio
async def test_approval_workflow():
    """Test the approval workflow signaling."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[ApprovalWorkflow],
            activities=[mock_send_notification],
            workflow_runner=runner
        ):
            handle = await env.client.start_workflow(
                ApprovalWorkflow.run,
                args=["Deploy to prod", "user-1", ["admin-1"], 24],
                id="test-approval-workflow",
                task_queue="test-queue",
            )

            # Verify pending
            is_pending = await handle.query(ApprovalWorkflow.is_pending)
            assert is_pending is True

            # Approve
            await handle.signal(
                ApprovalWorkflow.approve, 
                ApprovalSignal(approved=True, feedback="Looks good", approver_id="admin-1")
            )

            # Get result
            approved, feedback = await handle.result()
            assert approved is True
            assert feedback == "Looks good"
