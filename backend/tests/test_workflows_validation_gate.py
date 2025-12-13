"""Additional workflow contract tests.

Ensures validation gate behavior is enforced in AgentWorkflow.
"""

import pytest
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
)
from backend.workflows.agent_workflow import AgentWorkflow, AgentWorkflowInput


@activity.defn(name="initialize_context_activity")
async def mock_initialize_context(user_id: str, tenant_id: str, session_id: str, agent_id: str) -> str:
    return '{"mock": "context"}'


@activity.defn(name="enrich_memory_activity")
async def mock_enrich_memory(input: MemoryEnrichInput) -> MemoryEnrichOutput:
    return MemoryEnrichOutput(context_json=input.context_json, facts_retrieved=1, entities_retrieved=0, success=True)


@activity.defn(name="agent_reasoning_activity")
async def mock_agent_reasoning(input: ReasoningInput) -> ReasoningOutput:
    return ReasoningOutput(
        response="Sensitive PII: 123-45-6789",
        context_json=input.context_json,
        tokens_used=10,
        success=True,
    )


@activity.defn(name="validate_response_activity")
async def mock_validate_response(response: str, context_json: str) -> tuple[bool, str]:
    return False, "PII detected"


@activity.defn(name="persist_memory_activity")
async def mock_persist_memory(input: MemoryPersistInput) -> MemoryPersistOutput:
    return MemoryPersistOutput(success=True)


runner = SandboxedWorkflowRunner(restrictions=SandboxRestrictions.default.with_passthrough_modules("backend", "pydantic"))


@pytest.mark.asyncio
async def test_agent_workflow_rewrites_on_validation_fail():
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
                mock_persist_memory,
            ],
            workflow_runner=runner,
        ):
            result = await env.client.execute_workflow(
                AgentWorkflow.run,
                AgentWorkflowInput(
                    user_id="test-user",
                    tenant_id="test-tenant",
                    session_id="test-session",
                    agent_id="elena",
                    user_message="Hello",
                ),
                id="test-agent-workflow-validation-gate",
                task_queue="test-queue",
            )

            assert result.success is True
            assert "didn't pass validation" in result.response
