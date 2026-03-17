"""
WealthLens sub-agent registry.
Sub-agents handle specialized tasks: extraction, enrichment, analytics.
"""

from core.sub_agents.extraction_agent import extraction_agent
from core.sub_agents.enrichment_agent import enrichment_agent
from core.sub_agents.analytics_agent import analytics_agent

SUB_AGENTS = {
    "extraction": extraction_agent,
    "enrichment": enrichment_agent,
    "analytics": analytics_agent,
}
