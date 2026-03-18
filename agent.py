"""Claude-based email analysis agent."""

import json
from typing import Any, Dict, List

from anthropic import Anthropic

from config import CLAUDE_MODEL, EMAIL_CATEGORIES, MAX_TOKENS_ANALYSIS, SENTIMENTS


class EmailAnalysisAgent:
    """Agent for analyzing emails using Claude."""

    def __init__(self, api_key: str):
        """Initialize the agent with Anthropic client."""
        self.client = Anthropic(api_key=api_key)

    def analyze_emails(self, emails: List[dict]) -> Dict[str, Any]:
        """
        Analyze a batch of emails and return structured insights.

        Args:
            emails: List of email dictionaries from GmailClient

        Returns:
            Dictionary with per-email analysis and aggregate insights
        """
        if not emails:
            return self._empty_analysis()

        # Phase 1: Analyze individual emails
        per_email_analysis = self._analyze_per_email(emails)

        # Phase 2: Generate aggregate insights
        aggregate = self._generate_aggregate_insights(emails, per_email_analysis)

        return {
            "email_count": len(emails),
            "per_email_analysis": per_email_analysis,
            "aggregate_insights": aggregate,
        }

    def _analyze_per_email(self, emails: List[dict]) -> List[dict]:
        """
        Analyze each email for category, sentiment, priority, etc.

        Args:
            emails: List of email dictionaries

        Returns:
            List of analysis results for each email
        """
        email_summaries = []
        for email in emails:
            email_summaries.append(
                f"""
From: {email['sender']}
Subject: {email['subject']}
Date: {email['date']}
Body: {email['body'][:500]}...
"""
            )

        email_dump = "\n---\n".join(email_summaries)

        prompt = f"""You are an expert email analyst. Analyze these {len(emails)} emails and provide structured insights.

For each email, provide:
1. Category (one of: {', '.join(EMAIL_CATEGORIES)})
2. Sentiment (one of: {', '.join(SENTIMENTS)})
3. Priority score (1-10)
4. One-sentence summary
5. Action items (if any, as a list)

Format your response as valid JSON with this structure:
{{
  "emails": [
    {{
      "subject": "...",
      "sender": "...",
      "category": "...",
      "sentiment": "...",
      "priority": 0-10,
      "summary": "...",
      "action_items": ["...", "..."] or []
    }}
  ]
}}

EMAILS TO ANALYZE:
{email_dump}

Respond ONLY with valid JSON, no additional text."""

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS_ANALYSIS,
                thinking={"type": "adaptive"},
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text

            # Try to extract JSON from response
            try:
                result = json.loads(response_text)
                return result.get("emails", [])
            except json.JSONDecodeError:
                # If JSON parsing fails, return simplified analysis
                print("Warning: Could not parse Claude response as JSON")
                return self._fallback_analysis(emails)

        except Exception as e:
            print(f"Error analyzing emails: {e}")
            return self._fallback_analysis(emails)

    def _generate_aggregate_insights(
        self, emails: List[dict], per_email_analysis: List[dict]
    ) -> Dict[str, Any]:
        """
        Generate aggregate insights from individual email analyses.

        Args:
            emails: Original email list
            per_email_analysis: Per-email analysis results

        Returns:
            Dictionary with aggregate insights
        """
        # Calculate basic statistics
        categories = {}
        sentiments = {}
        all_action_items = []
        priority_scores = []
        senders_priority = {}

        for i, analysis in enumerate(per_email_analysis):
            category = analysis.get("category", "OTHER")
            sentiment = analysis.get("sentiment", "NEUTRAL")
            priority = analysis.get("priority", 5)

            categories[category] = categories.get(category, 0) + 1
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            priority_scores.append(priority)

            if analysis.get("action_items"):
                for item in analysis["action_items"]:
                    all_action_items.append(
                        {
                            "item": item,
                            "from": emails[i]["sender"],
                            "subject": emails[i]["subject"],
                            "priority": priority,
                        }
                    )

            sender = emails[i]["sender"]
            if sender not in senders_priority:
                senders_priority[sender] = {"count": 0, "avg_priority": 0}
            senders_priority[sender]["count"] += 1
            senders_priority[sender]["avg_priority"] += priority

        # Calculate averages and identify VIPs
        for sender in senders_priority:
            count = senders_priority[sender]["count"]
            senders_priority[sender]["avg_priority"] /= count

        vips = sorted(
            senders_priority.items(),
            key=lambda x: x[1]["avg_priority"] * x[1]["count"],
            reverse=True,
        )[:5]

        # Calculate inbox health score (0-10)
        avg_priority = sum(priority_scores) / len(priority_scores) if priority_scores else 5
        action_required_count = categories.get("ACTION_REQUIRED", 0)
        health_score = max(1, 10 - (action_required_count / len(emails) * 5))

        # Sort action items by priority
        all_action_items.sort(key=lambda x: x["priority"], reverse=True)
        top_action_items = all_action_items[:5]

        # Create aggregate insights via Claude
        prompt = f"""Based on this email summary, provide strategic insights and recommendations.

Email Statistics:
- Total emails: {len(emails)}
- Categories: {categories}
- Sentiment breakdown: {sentiments}
- Average priority: {avg_priority:.1f}/10
- Action items identified: {len(all_action_items)}

Provide insights as JSON with this structure:
{{
  "inbox_health_score": 0-10,
  "key_trends": ["...", "..."],
  "recommendations": ["...", "..."],
  "email_volume_trend": "...",
  "vip_analysis": "..."
}}"""

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text
            insights_extra = json.loads(response_text)
        except Exception as e:
            insights_extra = {
                "inbox_health_score": health_score,
                "key_trends": [],
                "recommendations": [],
            }

        return {
            "inbox_health_score": insights_extra.get("inbox_health_score", health_score),
            "category_breakdown": categories,
            "sentiment_breakdown": sentiments,
            "average_priority": avg_priority,
            "top_action_items": top_action_items,
            "vip_senders": [
                {"sender": s[0], "email_count": s[1]["count"], "avg_priority": s[1]["avg_priority"]}
                for s in vips
            ],
            "key_trends": insights_extra.get("key_trends", []),
            "recommendations": insights_extra.get("recommendations", []),
        }

    def _fallback_analysis(self, emails: List[dict]) -> List[dict]:
        """Fallback analysis when Claude response parsing fails."""
        return [
            {
                "subject": email["subject"],
                "sender": email["sender"],
                "category": "OTHER",
                "sentiment": "NEUTRAL",
                "priority": 5,
                "summary": email["subject"],
                "action_items": [],
            }
            for email in emails
        ]

    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis when no emails."""
        return {
            "email_count": 0,
            "per_email_analysis": [],
            "aggregate_insights": {
                "inbox_health_score": 10,
                "category_breakdown": {},
                "sentiment_breakdown": {},
                "average_priority": 0,
                "top_action_items": [],
                "vip_senders": [],
                "key_trends": [],
                "recommendations": ["No emails to analyze"],
            },
        }
