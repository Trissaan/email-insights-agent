"""Flask webhook server for Twilio WhatsApp/SMS integration."""

from flask import Flask, request, Response
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from werkzeug.middleware.proxy_fix import ProxyFix

from config import (
    ALLOWED_PHONE_NUMBERS,
    ANTHROPIC_API_KEY,
    SKIP_TWILIO_VALIDATION,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
)
from conversational_agent import ConversationalEmailAgent

# Initialize Flask app
app = Flask(__name__)

# Apply ProxyFix for HTTPS handling (needed when behind ngrok)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
validator = RequestValidator(TWILIO_AUTH_TOKEN)

# Initialize conversational agent
agent = ConversationalEmailAgent(api_key=ANTHROPIC_API_KEY)


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Handle incoming WhatsApp/SMS messages from Twilio.

    Validates the request, extracts the message, calls the agent,
    and returns a TwiML response.
    """
    # Validate Twilio signature (skip if SKIP_TWILIO_VALIDATION is true)
    if not SKIP_TWILIO_VALIDATION:
        request_url = request.url
        request_params = request.form.to_dict()

        # Validate using the X-Twilio-Signature header
        twilio_signature = request.headers.get("X-Twilio-Signature", "")

        if not validator.validate(request_url, request_params, twilio_signature):
            return Response("Unauthorized", status=403)

    # Extract message details
    phone = request.form.get("From", "")
    body = request.form.get("Body", "").strip()
    message_sid = request.form.get("MessageSid", "")

    # Check if phone number is allowed (if allowlist is configured)
    if ALLOWED_PHONE_NUMBERS and phone not in ALLOWED_PHONE_NUMBERS:
        # Silently ignore messages from unauthorized numbers
        return _build_twiml_response(""), 200

    # Handle empty body (media-only messages)
    if not body:
        return _build_twiml_response("I can only process text messages."), 200

    try:
        # Process message with conversational agent
        reply = agent.handle_message(phone, body)

        # Build and return TwiML response
        return _build_twiml_response(reply), 200
    except Exception as e:
        # Log error and send fallback response
        print(f"Error processing message {message_sid} from {phone}: {e}")
        return _build_twiml_response("Sorry, I encountered an error. Please try again."), 200


def _build_twiml_response(reply: str) -> Response:
    """
    Build a TwiML response, splitting long messages into chunks.

    Args:
        reply: The reply text to send

    Returns:
        Twilio TwiML response as a Flask Response
    """
    # Split reply into ≤1560 character chunks
    chunks = _split_message(reply, max_length=1560, max_parts=3)

    # Build TwiML message
    twiml_xml = '<?xml version="1.0" encoding="UTF-8"?>'
    twiml_xml += "<Response>"

    for chunk in chunks:
        # Escape XML special characters
        chunk_escaped = chunk.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        twiml_xml += f'<Message>{chunk_escaped}</Message>'

    twiml_xml += "</Response>"

    return Response(twiml_xml, mimetype="application/xml")


def _split_message(text: str, max_length: int = 1560, max_parts: int = 3) -> list[str]:
    """
    Split a message into chunks for Twilio.

    Strategy:
    1. Try to split on paragraph breaks (\\n\\n)
    2. Then try to split on sentence breaks (. )
    3. Finally hard-truncate at max_length

    Args:
        text: Message text to split
        max_length: Maximum characters per chunk
        max_parts: Maximum number of chunks to return

    Returns:
        List of message chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text

    # Try splitting on paragraph breaks first
    if "\n\n" in remaining:
        paragraphs = remaining.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_length:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                if len(para) <= max_length:
                    current_chunk = para
                else:
                    # Para too long, will handle below
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk.rstrip())

        if len(chunks) <= max_parts:
            return chunks

        # Fall through to sentence splitting if too many chunks
        chunks = []
        remaining = text

    # Try splitting on sentence breaks
    if ". " in remaining:
        sentences = remaining.split(". ")
        current_chunk = ""

        for i, sentence in enumerate(sentences):
            sep = ". " if i < len(sentences) - 1 else ""
            if len(current_chunk) + len(sentence) + len(sep) <= max_length:
                current_chunk += sentence + sep
            else:
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                if len(sentence) <= max_length:
                    current_chunk = sentence + sep
                else:
                    # Sentence too long, hard-truncate
                    chunks.append(sentence[:max_length])
                    current_chunk = ""

        if current_chunk:
            chunks.append(current_chunk.rstrip())

        if len(chunks) <= max_parts:
            return chunks

    # Fall back to hard truncation
    chunks = []
    remaining = text

    while remaining and len(chunks) < max_parts:
        chunks.append(remaining[:max_length])
        remaining = remaining[max_length:]

    # If there's still more text and we hit max_parts, append to last chunk
    if remaining and len(chunks) == max_parts:
        chunks[-1] += "..." + remaining[:50]

    return chunks


if __name__ == "__main__":
    # This should not be called directly; use `python main.py serve`
    app.run(host="0.0.0.0", port=5000, debug=False)
