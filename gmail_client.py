"""Gmail API client for fetching and parsing emails."""

import base64
import email
from datetime import datetime
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_FILE, GMAIL_SCOPES, TOKEN_FILE


class GmailClient:
    """Client for interacting with Gmail API."""

    def __init__(self):
        """Initialize Gmail client with OAuth2 authentication."""
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Gmail API using OAuth2."""
        creds = None

        # Load existing token
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {CREDENTIALS_FILE}\n"
                        "Download it from Google Cloud Console (OAuth 2.0 Client ID)"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for future use
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)

    def fetch_emails(self, count: int = 100) -> List[dict]:
        """
        Fetch the last N emails from INBOX.

        Args:
            count: Number of emails to fetch

        Returns:
            List of email dictionaries with sender, subject, date, body
        """
        try:
            results = self.service.users().messages().list(
                userId="me", q="in:inbox", maxResults=count
            ).execute()

            messages = results.get("messages", [])
            emails = []

            for msg in messages:
                email_data = self._parse_message(msg["id"])
                if email_data:
                    emails.append(email_data)

            return emails
        except Exception as e:
            raise RuntimeError(f"Failed to fetch emails: {e}")

    def fetch_emails_since(self, since_date: datetime) -> List[dict]:
        """
        Fetch emails received after a specific date.

        Args:
            since_date: datetime object for cutoff date

        Returns:
            List of email dictionaries
        """
        try:
            # Format date for Gmail API (YYYY/MM/DD)
            date_str = since_date.strftime("%Y/%m/%d")
            query = f"in:inbox after:{date_str}"

            results = self.service.users().messages().list(
                userId="me", q=query, maxResults=100
            ).execute()

            messages = results.get("messages", [])
            emails = []

            for msg in messages:
                email_data = self._parse_message(msg["id"])
                if email_data:
                    emails.append(email_data)

            return emails
        except Exception as e:
            raise RuntimeError(f"Failed to fetch emails since {since_date}: {e}")

    def _parse_message(self, message_id: str) -> Optional[dict]:
        """
        Parse a Gmail message into structured data.

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with sender, subject, date, body, or None if parsing fails
        """
        try:
            message = self.service.users().messages().get(
                userId="me", id=message_id, format="full"
            ).execute()

            headers = message["payload"]["headers"]
            header_dict = {h["name"]: h["value"] for h in headers}

            # Extract fields
            sender = header_dict.get("From", "Unknown")
            subject = header_dict.get("Subject", "(No subject)")
            date_str = header_dict.get("Date", "")

            # Parse body
            body = self._get_body(message["payload"])

            return {
                "id": message_id,
                "sender": sender,
                "subject": subject,
                "date": date_str,
                "body": body,
                "headers": header_dict,
            }
        except Exception as e:
            print(f"Warning: Failed to parse message {message_id}: {e}")
            return None

    def _get_body(self, payload: dict) -> str:
        """
        Extract body text from email payload.

        Args:
            payload: Email payload from Gmail API

        Returns:
            Plain text body
        """
        if "parts" in payload:
            # Multipart message
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        return base64.urlsafe_b64decode(data).decode("utf-8")
        else:
            # Single part message
            data = payload.get("body", {}).get("data", "")
            if data:
                try:
                    return base64.urlsafe_b64decode(data).decode("utf-8")
                except Exception:
                    return ""

        return ""
