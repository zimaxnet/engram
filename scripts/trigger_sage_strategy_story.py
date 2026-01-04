
import asyncio
import os

# Override TEMPORAL_HOST for production connection
os.environ["TEMPORAL_HOST"] = "staging-env-temporal-server.gentleriver-dd0de193.eastus2.azurecontainerapps.io:443"

from backend.workflows.client import execute_story

async def main():
    topic = "The Convergence of Memory and Sovereignty: Zep Cloud vs Graphiti"
    context = """
    Engram is transitioning to production. We analyzed Zep Cloud (Free vs Flex) and Graphiti OSS.
    Decision: Start with Zep Cloud Free to leverage metadata and fact extraction without the Neo4j overhead.
    Long-term: Migrate to Graphiti for full data sovereignty once scale and revenue ($380k ARR target) justify the infra management.
    This story should memorialize the decision of 'Memory + Workflows' as the winning architecture.
    """
    
    print(f"Triggering Sage workflow for: {topic}...")
    print(f"Connecting to production Temporal: {os.environ['TEMPORAL_HOST']}")
    
    result = await execute_story(
        user_id="elena-gtm",
        tenant_id="default",
        topic=topic,
        context=context,
        include_diagram=True,
        include_image=True,
        diagram_type="architecture"
    )
    
    if result.success:
        print(f"SUCCESS: Story created with ID: {result.story_id}")
        print(f"Preview: {result.story_content[:200]}...")
    else:
        print(f"FAILED: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())
