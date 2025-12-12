"""
Marcus Chen - Project Manager Agent

Marcus is an expert in program management, Agile transformation,
and risk mitigation. Known for his "Calm in the Storm" leadership
style and "Adaptive Governance" framework.

Personality: Pragmatic, direct, risk-aware, timeline-focused, team-oriented
Voice: Confident, energetic, Pacific Northwest professional
"""

from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

from backend.agents.base import BaseAgent, AgentState


# =============================================================================
# Marcus's Tools
# =============================================================================


@tool
def create_project_timeline(project_name: str, start_date: str, end_date: str, milestones: str) -> str:
    """
    Create a project timeline with milestones and risk buffers.

    Args:
        project_name: Name of the project
        start_date: Project start date
        end_date: Target end date
        milestones: Comma-separated list of key milestones

    Returns:
        Project timeline with phases and recommendations
    """
    milestone_list = [m.strip() for m in milestones.split(",")]

    return f"""
## Project Timeline: {project_name}

### Overview
- **Start Date**: {start_date}
- **Target End Date**: {end_date}
- **Duration**: [Calculate based on dates]
- **Risk Buffer**: 15% recommended

### Milestones
{chr(10).join(f"- [ ] **M{i + 1}**: {m}" for i, m in enumerate(milestone_list))}

### Recommended Phase Structure

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| Discovery | 2 weeks | Requirements, stakeholder alignment |
| Design | 3 weeks | Architecture, UX, technical specs |
| Development | 6 weeks | Sprint cycles, iterative delivery |
| Testing | 2 weeks | QA, UAT, performance testing |
| Deployment | 1 week | Staged rollout, monitoring |
| Stabilization | 1 week | Bug fixes, optimization |

### Risk Considerations
1. **Schedule Risk**: Add buffer before hard deadlines
2. **Resource Risk**: Identify critical path dependencies
3. **Scope Risk**: Define MVP vs. nice-to-have clearly

### Next Steps
Want me to help you identify dependencies or create a RACI matrix?
"""


@tool
def assess_project_risks(project_description: str) -> str:
    """
    Assess project risks and provide mitigation strategies.

    Args:
        project_description: Description of the project

    Returns:
        Risk assessment with mitigation strategies
    """
    return f"""
## Risk Assessment Report

### Project Context
{project_description[:200]}...

### Risk Matrix

| Risk | Probability | Impact | Score | Mitigation |
|------|-------------|--------|-------|------------|
| Scope creep | High | High | 🔴 9 | Change control process |
| Resource availability | Medium | High | 🟠 6 | Cross-training, buffer |
| Technical complexity | Medium | Medium | 🟡 4 | Spike early, POC first |
| Stakeholder alignment | Low | High | 🟡 3 | Regular check-ins |
| External dependencies | Medium | Medium | 🟡 4 | Early engagement |

### Top 3 Risks to Watch

1. **Scope Creep** (Score: 9)
   - *Why it matters*: Every unplanned feature adds 1-2 weeks
   - *Mitigation*: Strict change request process, impact assessment required
   - *Owner*: Product Owner + PM

2. **Resource Availability** (Score: 6)
   - *Why it matters*: Key person dependency can halt progress
   - *Mitigation*: Document knowledge, pair programming, buffer time
   - *Owner*: Engineering Lead

3. **External Dependencies** (Score: 4)
   - *Why it matters*: Waiting on others blocks your critical path
   - *Mitigation*: Identify early, escalation path, mock/stub options
   - *Owner*: PM

### Recommended Actions
- [ ] Schedule risk review in sprint planning
- [ ] Create dependency tracker
- [ ] Establish escalation matrix
"""


@tool
def create_status_report(project_name: str, progress_summary: str, blockers: str, next_steps: str) -> str:
    """
    Generate a project status report.

    Args:
        project_name: Name of the project
        progress_summary: Summary of progress this period
        blockers: Current blockers (comma-separated)
        next_steps: Planned next steps

    Returns:
        Formatted status report
    """
    blocker_list = [b.strip() for b in blockers.split(",")] if blockers else ["None"]

    return f"""
## Status Report: {project_name}
**Report Date**: [Current Date]
**Reporting Period**: [Last Week/Sprint]

### Overall Status: 🟡 Yellow

### Progress Summary
{progress_summary}

### Key Metrics
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Sprint Velocity | 40 pts | TBD | ⚪ |
| Scope Completion | 60% | TBD | ⚪ |
| Bug Count | <10 | TBD | ⚪ |
| Team Health | Good | TBD | ⚪ |

### Blockers & Risks
{chr(10).join(f"- 🚧 {b}" for b in blocker_list)}

### Next Period Plan
{next_steps}

### Decisions Needed
- [ ] [List any decisions required from stakeholders]

### Budget Status
- Planned: $[X]
- Actual: $[Y]
- Variance: [Z]%

---
*Report generated by Marcus Chen, Project Manager*
"""


@tool
def estimate_effort(task_description: str, complexity: str = "medium") -> str:
    """
    Provide effort estimation for a task or feature.

    Args:
        task_description: Description of the task
        complexity: low, medium, or high

    Returns:
        Effort estimate with breakdown
    """
    multipliers = {"low": 1, "medium": 2, "high": 3}
    base_days = multipliers.get(complexity.lower(), 2)

    return f"""
## Effort Estimation

### Task
{task_description}

### Complexity Assessment: {complexity.upper()}

### Estimate Breakdown

| Activity | Effort (days) | Notes |
|----------|---------------|-------|
| Analysis/Design | {base_days * 0.5:.1f} | Requirements clarification |
| Development | {base_days * 2:.1f} | Core implementation |
| Testing | {base_days * 1:.1f} | Unit + integration tests |
| Code Review | {base_days * 0.25:.1f} | Peer review, feedback |
| Documentation | {base_days * 0.25:.1f} | Update docs, README |
| **Total** | **{base_days * 4:.1f}** | |

### Confidence Level
- **Point Estimate**: {base_days * 4:.1f} days
- **Best Case** (90%): {base_days * 3:.1f} days
- **Worst Case** (10%): {base_days * 6:.1f} days

### Assumptions
1. Requirements are clear and stable
2. No external blockers
3. Dedicated resource availability

### Caveats
This is a rough estimate. I'd recommend:
- Breaking this into smaller tasks for better accuracy
- Adding 20% buffer for unknowns
- Revisiting after initial spike/POC
"""


# =============================================================================
# Marcus Agent Implementation
# =============================================================================


class MarcusAgent(BaseAgent):
    """
    Marcus Chen - Project Manager Agent

    Specializes in program management, Agile transformation,
    risk mitigation, and helping teams deliver on time.
    """

    agent_id = "marcus"
    agent_name = "Marcus Chen"
    agent_title = "Project Manager"

    @property
    def system_prompt(self) -> str:
        return """You are Marcus Chen, an experienced Project Manager with over 15 years in tech, including 10 years at Microsoft. You hold PMP, CSM, and SAFe SPC certifications.

## Your Background
You spent your first decade at Microsoft as a Program Manager, shipping Windows Azure features and leading the Azure DevOps platform team through three major releases. You're known for your "Calm in the Storm" leadership style, having successfully recovered a $50M enterprise migration that was 18 months behind schedule. You developed the "Adaptive Governance" framework that balances agility with enterprise rigor.

## Your Expertise
- Program and project management
- Agile/Scrum transformation
- Risk identification and mitigation
- Timeline planning and estimation
- Resource allocation and optimization
- Stakeholder communication
- Team leadership and motivation

## Your Communication Style
- **Direct**: You communicate clearly without corporate-speak
- **Pragmatic**: You focus on what will actually work, not theoretical ideals
- **Risk-aware**: You identify potential problems early
- **Timeline-focused**: You always know what's on the critical path
- **Team-oriented**: You celebrate wins and protect teams from blame
- **Quantitative**: You quantify impact when possible

## Your Approach
1. **Assess Reality**: Understand where things actually are, not where people hope
2. **Identify Risks Early**: Surface problems before they become crises
3. **Provide Options**: Give stakeholders choices, not ultimatums
4. **Protect the Team**: Shield developers from unrealistic expectations
5. **Celebrate Progress**: Acknowledge wins, even small ones

## Interaction Guidelines
- When someone describes a problem, first understand the timeline and constraints
- Ask about resources, dependencies, and hard deadlines
- Provide concrete recommendations with trade-offs
- Use real numbers and dates when possible
- Be honest about risks but also offer solutions
- Share relevant war stories when they help illustrate points

## Your Voice
Speak with confidence and energy. You have a Pacific Northwest professional tone with occasional tech industry vernacular. You occasionally use phrases like:
- "Let's figure out where we actually are..."
- "In my experience shipping Azure..."
- "Here's the trade-off..."
- "What's the hard deadline, and what happens if we miss it?"
- "That's a classic [pattern] - I've seen this before..."

## Your Philosophy
Most project failures aren't technical - they're failures of communication, expectation management, and early risk detection. Your job is to help teams see around corners and avoid the pitfalls you've witnessed countless times. A good PM makes the team better, not just busier.

Remember: You're here to help teams succeed, not to create process for its own sake. Every meeting, every report, every status update should serve a clear purpose."""

    @property
    def tools(self) -> list:
        return [
            create_project_timeline,
            assess_project_risks,
            create_status_report,
            estimate_effort,
        ]

    # -------------------------------------------------------------------------
    # LangGraph workflow
    # -------------------------------------------------------------------------
    def build_graph(self) -> StateGraph:
        """
        Marcus' LangGraph:
        - reason: core LLM reasoning
        - maybe_tool: run a PM tool based on the ask
        - respond: craft final response with tool output
        """
        workflow = StateGraph(AgentState)

        workflow.add_node("reason", self._reason_node)
        workflow.add_node("maybe_tool", self._maybe_use_tool)
        workflow.add_node("respond", self._respond_with_context)

        workflow.set_entry_point("reason")
        workflow.add_conditional_edges(
            "reason",
            self._decide_next,
            {
                "tool": "maybe_tool",
                "respond": "respond",
            },
        )
        workflow.add_edge("maybe_tool", "respond")
        workflow.add_edge("respond", END)

        return workflow.compile()

    def _decide_next(self, state: AgentState) -> str:
        """Decide whether to invoke a tool based on the last user message."""
        last_user = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        content = last_user.content if last_user else ""
        tool_name, tool_args = self._select_tool(content)
        if tool_name:
            state["pending_tool"] = tool_name
            state["pending_tool_args"] = tool_args
            return "tool"
        return "respond"

    def _select_tool(self, content: str) -> tuple[str | None, dict]:
        text = content.lower()
        if "timeline" in text or "schedule" in text:
            return "create_project_timeline", {
                "project_name": "Project",
                "start_date": "2025-01-01",
                "end_date": "2025-03-31",
                "milestones": "Planning, Build, Test, Launch",
            }
        if "status" in text or "report" in text:
            return "create_status_report", {
                "project_name": "Project",
                "progress_summary": content,
                "blockers": "",
                "next_steps": "",
            }
        if "risk" in text or "risks" in text:
            return "assess_project_risks", {"project_description": content}
        if "estimate" in text or "effort" in text or "size" in text:
            return "estimate_effort", {
                "task_description": content,
                "complexity": "medium",
            }
        return None, {}

    async def _maybe_use_tool(self, state: AgentState) -> AgentState:
        """Invoke a selected tool and append its result to messages."""
        tool_name: str | None = state.get("pending_tool")
        tool_args: dict = state.get("pending_tool_args", {}) or {}
        if not tool_name:
            return state

        tool_registry = {t.name: t for t in self.tools}
        tool = tool_registry.get(tool_name)
        if not tool:
            state["final_response"] = state.get("final_response") or "I couldn't run the requested analysis."
            return state

        try:
            result = tool.invoke(tool_args)
            state["tool_results"].append({"tool": tool_name, "result": result})
            state["messages"].append(
                type(
                    "ToolMessage",
                    (),
                    {"type": "system", "content": f"[Tool:{tool_name}] {result}"},
                )()
            )
        except Exception as e:
            state["final_response"] = f"I tried to run {tool_name} but hit an error: {e}"
        return state

    async def _respond_with_context(self, state: AgentState) -> AgentState:
        """Compose final response, including any tool outputs."""
        if state["tool_results"]:
            tool_summary = "\n\n".join(f"**{tr['tool']}**\n{tr['result']}" for tr in state["tool_results"])
            base_resp = state.get("final_response") or "Here’s what I can offer:"
            state["final_response"] = f"{base_resp}\n\n{tool_summary}"
        elif not state.get("final_response"):
            state["final_response"] = "Let me summarize that for you in the next turn."

        state["current_step"] = "respond"
        return state


# Singleton instance for easy import
marcus = MarcusAgent()
