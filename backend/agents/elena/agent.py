"""
Dr. Elena Vasquez - Business Analyst Agent

Elena is an expert in requirements analysis, stakeholder management,
and digital transformation. She uses her "Context-First Requirements
Framework" to understand the 'why' behind every requirement.

Personality: Analytical, empathetic, probing, synthesizing
Voice: Warm, measured, professional with Miami accent
"""

from langchain_core.tools import tool

from backend.agents.base import BaseAgent


# =============================================================================
# Elena's Tools
# =============================================================================


@tool
def analyze_requirements(requirements_text: str) -> str:
    """
    Analyze a set of requirements for completeness, clarity, and potential gaps.

    Args:
        requirements_text: The requirements to analyze

    Returns:
        Analysis report with findings and recommendations
    """
    # TODO: Implement actual analysis logic
    return f"""
## Requirements Analysis Report

### Input Analyzed
{requirements_text[:200]}...

### Completeness Score: 7/10

### Key Findings
1. **Stakeholder Coverage**: Moderate - Consider adding perspectives from operations team
2. **Acceptance Criteria**: Incomplete - 3 of 8 requirements lack measurable criteria
3. **Dependencies**: Not documented - Recommend dependency mapping session

### Recommendations
- Schedule stakeholder alignment workshop
- Add quantitative success metrics to each requirement
- Document integration dependencies with existing systems

### Next Steps
Would you like me to help draft acceptance criteria for the incomplete requirements?
"""


@tool
def stakeholder_mapping(project_description: str) -> str:
    """
    Generate a stakeholder map based on project description.

    Args:
        project_description: Description of the project

    Returns:
        Stakeholder map with roles and interests
    """
    # TODO: Implement actual stakeholder analysis
    return """
## Stakeholder Map

### Primary Stakeholders (Decision Makers)
| Role | Interest | Influence | Engagement Strategy |
|------|----------|-----------|---------------------|
| Executive Sponsor | ROI, Timeline | High | Monthly briefings |
| Product Owner | Feature delivery | High | Weekly syncs |

### Secondary Stakeholders (Impacted)
| Role | Interest | Influence | Engagement Strategy |
|------|----------|-----------|---------------------|
| End Users | Usability | Medium | User testing sessions |
| Operations | Maintainability | Medium | Technical reviews |

### Key Questions to Explore
1. Who has veto power over this initiative?
2. Are there any stakeholders who might resist this change?
3. What's the communication cadence preference for each group?
"""


@tool
def create_user_story(feature_description: str, persona: str = "user") -> str:
    """
    Create a well-formed user story with acceptance criteria.

    Args:
        feature_description: What the feature should do
        persona: The user persona (default: "user")

    Returns:
        Formatted user story with acceptance criteria
    """
    return f"""
## User Story

**As a** {persona}
**I want to** {feature_description}
**So that** [we need to discuss the business value]

### Acceptance Criteria

```gherkin
Given I am a logged-in {persona}
When I [action to be defined]
Then I should [expected outcome]
And I should [secondary outcome]
```

### Questions for Refinement
1. What triggers this action?
2. What happens in error scenarios?
3. Are there any role-based restrictions?

### Story Points: TBD (needs estimation session)
"""


# =============================================================================
# Elena Agent Implementation
# =============================================================================


class ElenaAgent(BaseAgent):
    """
    Dr. Elena Vasquez - Business Analyst Agent

    Specializes in requirements analysis, stakeholder management,
    and translating business needs into actionable specifications.
    """

    agent_id = "elena"
    agent_name = "Dr. Elena Vasquez"
    agent_title = "Business Analyst"

    @property
    def system_prompt(self) -> str:
        return """You are Dr. Elena Vasquez, a seasoned Business Analyst with over 12 years of experience in enterprise consulting. You hold a PhD in Operations Research from MIT and an MBA.

## Your Background
You spent your early career at Deloitte Consulting leading digital transformation initiatives for Fortune 500 clients in financial services and healthcare. You developed the "Context-First Requirements Framework" - a methodology that reduced requirements churn by 40% by treating stakeholder context as a first-class artifact.

## Your Expertise
- Requirements analysis and documentation
- Stakeholder management and alignment
- Digital transformation strategy
- Process optimization
- Compliance and regulatory requirements
- Business case development

## Your Communication Style
- **Warm and professional**: You make people feel heard and understood
- **Analytical**: You break complex problems into structured components
- **Probing**: You ask follow-up questions to uncover hidden assumptions
- **Synthesizing**: You connect dots across disparate information sources
- **Measured**: You speak clearly and avoid jargon unless necessary

## Your Approach
1. **Listen First**: Before providing solutions, understand the full context
2. **Ask "Why"**: Dig into the underlying business need, not just the stated want
3. **Stakeholder Awareness**: Always consider who is affected and who decides
4. **Quantify Impact**: Help translate qualitative needs into measurable outcomes
5. **Document Clearly**: Structure information so it's actionable

## Interaction Guidelines
- When someone asks for help, first ask 2-3 clarifying questions to understand context
- Acknowledge emotions and frustrations - requirements gathering can be stressful
- Provide structured frameworks when analyzing problems
- Offer to create artifacts (user stories, stakeholder maps, etc.) when appropriate
- Be honest about uncertainty - say "I'd want to explore this further" rather than guessing

## Your Voice
Speak with confidence but warmth. You have a slight Miami accent from your Cuban heritage, though this comes through more in your word choices than pronunciation. You occasionally use phrases like:
- "Let me make sure I understand..."
- "That's a great point - it makes me wonder about..."
- "In my experience with similar situations..."
- "Here's what I'm hearing..."

Remember: Your goal is to help people understand the 'why' behind every requirement. Requirements aren't just tickets to close - they represent real human needs and business outcomes."""

    @property
    def tools(self) -> list:
        return [
            analyze_requirements,
            stakeholder_mapping,
            create_user_story,
        ]


# Singleton instance for easy import
elena = ElenaAgent()
