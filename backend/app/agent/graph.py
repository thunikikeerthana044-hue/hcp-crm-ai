"""
The LangGraph agent that powers the conversational "Log Interaction" mode.

Graph shape:

    START -> agent -> (conditional) -> tools -> agent -> ... -> END
                    (no tool call) -> END

`agent` node: the Groq LLM (llama-3.1-8b-instant) decides, given the running chat
history, whether to respond directly or call one of the tools in
app/agent/tools.py (log_interaction, edit_interaction, get_hcp_history,
schedule_follow_up, check_compliance, suggest_next_best_action).

`tools` node: executes whichever tool(s) the model requested and appends the
results back into the message list as ToolMessages, so the agent can use them
to formulate its next reply (e.g. confirm what was logged, or ask a
clarifying question if a required field like hcp_id is missing).

The loop continues until the LLM responds without requesting another tool
call, at which point the graph ends and the reply is returned to the rep.
"""
import json
import warnings
# Suppress LangChainPendingDeprecationWarning from langgraph.checkpoint internals
# (emitted on first import of langgraph; not actionable from our code)
warnings.filterwarnings("ignore", message=".*allowed_objects.*")
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, ToolMessage

from app.agent.llm import get_llm
from app.agent.tools import ALL_TOOLS

AGENT_SYSTEM_PROMPT = """You are Nova, the AI assistant inside a pharma CRM's HCP module. \
You help field reps log and manage interactions with Healthcare Professionals (HCPs) through \
natural conversation, instead of filling out a form.

Rules:
- If the rep describes a visit/call/email with an HCP, and you know the hcp_id (it will be given \
  to you in context, or ask the rep to pick the HCP first if missing), call log_interaction with \
  their raw description as `raw_notes`.
- If the rep wants to change something about an interaction already logged, call edit_interaction.
- Before logging, you may call get_hcp_history if it would help you understand context (e.g. rep \
  says "same as last time").
- If the rep asks "what should I bring up next time" or similar, call suggest_next_best_action.
- If the rep mentions a follow-up date/reminder, call schedule_follow_up.
- After logging an interaction, proactively call check_compliance on it, and mention the result \
  briefly if it was flagged.
- Always confirm back to the rep, in plain conversational language, what was logged/changed.
- Be concise. You are speaking to a busy field rep, not writing a report.
"""

# Build a lookup dict from tool name -> callable for the executor node
_TOOLS_BY_NAME: dict = {t.name: t for t in ALL_TOOLS}


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    hcp_id: str  # currently selected HCP for this chat session, if any


def build_graph():
    llm = get_llm().bind_tools(ALL_TOOLS)

    def agent_node(state: AgentState):
        messages = state["messages"]
        # Inject the system prompt + currently-selected HCP context on every turn
        hcp_context = f"\n\nCurrently selected HCP id: {state.get('hcp_id') or 'NONE - ask the rep which HCP first'}"
        system = SystemMessage(content=AGENT_SYSTEM_PROMPT + hcp_context)
        response = llm.invoke([system] + messages)
        return {"messages": [response]}

    def tool_executor_node(state: AgentState):
        """Execute all tool calls requested by the last AIMessage and return ToolMessages."""
        last_message = state["messages"][-1]
        tool_messages = []
        for tc in getattr(last_message, "tool_calls", []):
            tool_name = tc["name"]
            tool_args = tc["args"]
            tool_call_id = tc["id"]
            tool_fn = _TOOLS_BY_NAME.get(tool_name)
            if tool_fn is None:
                result = json.dumps({"error": f"Unknown tool: {tool_name}"})
            else:
                try:
                    result = tool_fn.invoke(tool_args)
                except Exception as exc:
                    result = json.dumps({"error": str(exc)})
            tool_messages.append(
                ToolMessage(content=str(result), name=tool_name, tool_call_id=tool_call_id)
            )
        return {"messages": tool_messages}

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_executor_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# Compiled once at import time and reused across requests.
compiled_agent_graph = build_graph()
