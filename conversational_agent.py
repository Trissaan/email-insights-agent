"""Conversational email agent using Claude with tool-use for real-time Q&A."""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    CONVERSATIONS_FILE,
    CONVERSATION_MAX_MESSAGES,
    MAX_TOKENS_CONVERSATION,
)
from gmail_client import GmailClient
import storage


class ConversationalEmailAgent:
    """Conversational agent for email Q&A and actions via WhatsApp/SMS."""

    def __init__(self, api_key: str):
        """Initialize the conversational agent."""
        self.client = Anthropic(api_key=api_key)
        self.gmail = GmailClient()
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self._load_conversations()

    def _load_conversations(self) -> None:
        """Load conversation history from disk."""
        if CONVERSATIONS_FILE.exists():
            try:
                with open(CONVERSATIONS_FILE, "r") as f:
                    self.conversations = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load conversations: {e}")
                self.conversations = {}

    def _save_conversations(self) -> None:
        """Save conversation history to disk."""
        try:
            with open(CONVERSATIONS_FILE, "w") as f:
                json.dump(self.conversations, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save conversations: {e}")

    def _get_conversation_history(self, phone: str) -> List[Dict[str, str]]:
        """Get conversation history for a phone number."""
        if phone not in self.conversations:
            self.conversations[phone] = {"messages": [], "last_active": datetime.now().isoformat()}
        return self.conversations[phone]["messages"]

    def _trim_conversation_history(self, phone: str) -> None:
        """Trim conversation history to max messages, preserving tool_use + tool_result pairs."""
        messages = self.conversations[phone]["messages"]
        if len(messages) <= CONVERSATION_MAX_MESSAGES:
            return

        # Find the oldest message that's not part of a tool_use + tool_result pair
        excess = len(messages) - CONVERSATION_MAX_MESSAGES
        i = 0
        removed = 0

        while i < len(messages) and removed < excess:
            if messages[i].get("role") == "assistant" and any(
                block.get("type") == "tool_use" for block in messages[i].get("content", [])
            ):
                # This is a tool_use message - keep it and the next tool_result
                i += 2
            else:
                messages.pop(0)
                removed += 1

    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define the tools available to Claude."""
        return [
            {
                "name": "get_recent_emails",
                "description": "Fetch recent emails from the user's inbox. Returns sender, subject, date, and a preview of the body.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of recent emails to fetch (default: 10, max: 50)",
                            "default": 10,
                        }
                    },
                    "required": [],
                },
            },
            {
                "name": "search_emails",
                "description": "Search emails using Gmail query syntax. Examples: 'from:user@example.com', 'subject:meeting', 'after:2026-03-01'",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Gmail search query (from:, subject:, after:, etc.)",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10, max: 50)",
                            "default": 10,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_email_details",
                "description": "Get the full body of a specific email by its message ID.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "Gmail message ID (returned from other email queries)",
                        }
                    },
                    "required": ["message_id"],
                },
            },
            {
                "name": "send_email",
                "description": "Send a new email. The user must explicitly confirm before this is executed.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient email address",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject",
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body (plain text)",
                        },
                    },
                    "required": ["to", "subject", "body"],
                },
            },
            {
                "name": "get_inbox_insights",
                "description": "Get saved email insights report (summary, categories, sentiment, action items, VIP senders).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Report date in YYYY-MM-DD format (default: most recent)",
                        }
                    },
                    "required": [],
                },
            },
            {
                "name": "get_saved_report",
                "description": "Get a previously saved analysis report by date.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Report date in YYYY-MM-DD format",
                        }
                    },
                    "required": ["date"],
                },
            },
        ]

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool and return the result as JSON string."""
        try:
            if tool_name == "get_recent_emails":
                count = tool_input.get("count", 10)
                count = min(count, 50)
                emails = self.gmail.fetch_emails(count=count)
                result = []
                for email in emails[:count]:
                    body_preview = email["body"][:300] + "..." if len(email["body"]) > 300 else email["body"]
                    result.append({
                        "id": email["id"],
                        "from": email["sender"],
                        "subject": email["subject"],
                        "date": email["date"],
                        "body_preview": body_preview,
                    })
                return json.dumps(result)

            elif tool_name == "search_emails":
                query = tool_input.get("query", "")
                max_results = min(tool_input.get("max_results", 10), 50)
                emails = self.gmail.search_emails(query=query, max_results=max_results)
                result = []
                for email in emails[:max_results]:
                    body_preview = email["body"][:300] + "..." if len(email["body"]) > 300 else email["body"]
                    result.append({
                        "id": email["id"],
                        "from": email["sender"],
                        "subject": email["subject"],
                        "date": email["date"],
                        "body_preview": body_preview,
                    })
                return json.dumps(result)

            elif tool_name == "get_email_details":
                message_id = tool_input.get("message_id", "")
                email_data = self.gmail._parse_message(message_id)
                if email_data:
                    return json.dumps({
                        "id": email_data["id"],
                        "from": email_data["sender"],
                        "subject": email_data["subject"],
                        "date": email_data["date"],
                        "body": email_data["body"],
                    })
                else:
                    return json.dumps({"error": "Email not found"})

            elif tool_name == "send_email":
                to = tool_input.get("to", "")
                subject = tool_input.get("subject", "")
                body = tool_input.get("body", "")
                result = self.gmail.send_email(to=to, subject=subject, body=body)
                return json.dumps({"success": True, "message_id": result.get("id", "")})

            elif tool_name == "get_inbox_insights":
                date_str = tool_input.get("date")
                if date_str:
                    insights = storage.load_insights(date_str)
                else:
                    insights = storage.load_insights()
                if insights:
                    return json.dumps(insights)
                else:
                    return json.dumps({"error": "No insights found for that date"})

            elif tool_name == "get_saved_report":
                date_str = tool_input.get("date", "")
                insights = storage.load_insights(date_str)
                if insights:
                    return json.dumps(insights)
                else:
                    return json.dumps({"error": "No report found for that date"})

            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})

        except Exception as e:
            return json.dumps({"error": str(e)})

    def handle_message(self, phone: str, text: str) -> str:
        """
        Handle an incoming message and return a reply.

        Args:
            phone: Sender phone number
            text: Message text

        Returns:
            Reply text to send back
        """
        with self.lock:
            # Get or create conversation history
            messages = self._get_conversation_history(phone)

            # Add user message
            messages.append({"role": "user", "content": text})

            # Agentic loop (max 5 rounds to prevent infinite loops)
            max_rounds = 5
            round_count = 0

            while round_count < max_rounds:
                round_count += 1

                # Call Claude with current messages
                response = self.client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=MAX_TOKENS_CONVERSATION,
                    system=self._get_system_prompt(),
                    tools=self._define_tools(),
                    messages=messages,
                )

                # Add assistant response to history
                assistant_content = []
                for block in response.content:
                    if block.type == "text":
                        assistant_content.append({"type": "text", "text": block.text})
                    elif block.type == "tool_use":
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })

                messages.append({"role": "assistant", "content": assistant_content})

                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Extract final text response
                    final_text = ""
                    for block in response.content:
                        if block.type == "text":
                            final_text += block.text
                    break

                elif response.stop_reason == "tool_use":
                    # Execute all tools in this response
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            result = self._execute_tool(block.name, block.input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result,
                            })

                    # Add tool results to messages
                    messages.append({"role": "user", "content": tool_results})
                else:
                    # Unexpected stop reason
                    final_text = "I encountered an unexpected error processing your request."
                    break

            # Update last active and trim history
            self.conversations[phone]["last_active"] = datetime.now().isoformat()
            self._trim_conversation_history(phone)

            # Save conversations
            self._save_conversations()

            return final_text if final_text else "I encountered an error processing your request."

    def _get_system_prompt(self) -> str:
        """Return the system prompt for the conversational agent."""
        return """You are a helpful email assistant accessed via WhatsApp or SMS. Keep responses concise since the user is reading on a mobile device.

Your capabilities:
- Read recent emails and search inbox
- View full email content
- Send new emails (you MUST state the recipient, subject, and body before calling send_email, and only proceed if the user explicitly approves)
- Get email insights and summaries

Guidelines:
- Keep responses under 1500 characters
- Be conversational but professional
- Never fabricate email content
- When a user asks to send an email, always show them the recipient, subject, and body preview first, then ask "Should I send this?" before actually sending
- For search queries, use Gmail syntax (from:, subject:, after:, etc.)
- Always check if an email exists before trying to read its full content

Examples of what users might ask:
- "Show me my last 5 emails"
- "Find emails from john@example.com"
- "What are my email insights from today?"
- "Send an email to bob@example.com about the meeting tomorrow"
"""
