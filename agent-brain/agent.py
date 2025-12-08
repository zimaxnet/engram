import asyncio
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker
from zep_python import ZepClient

# --- Context Object ---
from pydantic import BaseModel, Field
class EnterpriseContext(BaseModel):
    user_id: str
    task_goal: str
    history: list = []

# --- Activities ---
@activity.defn
async def reason(ctx: EnterpriseContext) -> EnterpriseContext:
    print(f"Reasoning for {ctx.user_id}...")
    # Placeholder for LangGraph execution
    ctx.history.append("Agent reasoned.")
    return ctx

@activity.defn
async def save_memory(ctx: EnterpriseContext) -> str:
    print(f"Saving memory to Zep...")
    # zep = ZepClient("http://zep:8000")
    # await zep.memory.add_memory(...)
    return "Memory Saved"

# --- Workflow ---
@workflow.defn
class AgentWorkflow:
    @workflow.run
    async def run(self, ctx: EnterpriseContext) -> str:
        ctx = await workflow.execute_activity(
            reason, ctx, start_to_close_timeout=timedelta(seconds=60)
        )
        await workflow.execute_activity(
            save_memory, ctx, start_to_close_timeout=timedelta(seconds=10)
        )
        return "Complete"

# --- Main Worker ---
import os
async def main():
    client = await Client.connect(os.getenv("TEMPORAL_HOST", "localhost:7233"))
    worker = Worker(
        client,
        task_queue="agent-queue",
        workflows=[AgentWorkflow],
        activities=[reason, save_memory],
    )
    print("Worker started...")
    await worker.run()

if __name__ == "__main__":
    from datetime import timedelta
    asyncio.run(main())
