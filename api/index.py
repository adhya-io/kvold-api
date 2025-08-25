from flask import Flask, request, jsonify
import resend
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Set API key from environment
resend.api_key = os.getenv("RESEND_API_KEY")

# Hardcoded working values (based on your successful test)
FROM_EMAIL = "system@resend.dev"  # Working sender
TO_EMAIL = "adhya.io@outlook.com"  # Your email where you receive messages

@app.route('/')
def home():
    return jsonify({
        "status": "Healthy!"
    })

@app.route('/send-email', methods=['POST'])
def send_email():
    try:
        # Check if API key is configured
        if not resend.api_key:
            return jsonify({"error": "RESEND_API_KEY environment variable not set"}), 500
        
        # Domain-based security check (optional - you can remove this if not needed)
        origin = request.headers.get('Origin')
        referer = request.headers.get('Referer')
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        
        if allowed_origins and allowed_origins[0]:  # If allowed origins are set
            origin_allowed = any(origin and origin.startswith(domain.strip()) for domain in allowed_origins)
            referer_allowed = any(referer and referer.startswith(domain.strip()) for domain in allowed_origins)
            
            if not (origin_allowed or referer_allowed):
                return jsonify({"error": "Unauthorized domain"}), 403
        
        # Get data from request
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('message'):
            return jsonify({"error": "Missing required field: message"}), 400
        
        if not data.get('reply_to'):
            return jsonify({"error": "Missing required field: reply_to"}), 400
        
        # Validate reply_to email format
        reply_to = data.get('reply_to')
        if '@' not in reply_to or '.' not in reply_to.split('@')[1]:
            return jsonify({"error": "Invalid reply_to email format"}), 400
        
        # Sanitize message content to prevent HTML injection
        message = data['message'].replace('<', '&lt;').replace('>', '&gt;')
        
        # Prepare email parameters (using hardcoded working values)
        params = {
            "from": FROM_EMAIL,  # system@resend.dev (working)
            "to": [TO_EMAIL],    # adhya.io@outlook.com (your email)
            "subject": os.getenv("EMAIL_SUBJECT", "New Contact Form Message"),
            "html": f"""
                <h3>New message from your website</h3>
                <p><strong>From:</strong> {reply_to}</p>
                <p><strong>Message:</strong></p>
                <div style="background: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #007cba;">
                    {message.replace(chr(10), '<br>')}
                </div>
                <hr>
                <p><small>Sent via API at {request.headers.get('Host', 'unknown')}</small></p>
            """,
            "reply_to": reply_to  # This comes from the form - where you can reply to
        }
        
        # Send email using Resend
        email_response = resend.Emails.send(params)
        
        return jsonify({
            "success": True,
            "message": "Email sent successfully",
            "email_id": email_response.get('id') if hasattr(email_response, 'get') else str(email_response)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to send email",
            "details": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/health')
def health():
    api_key_status = "configured" if resend.api_key else "missing"
    return jsonify({
        "status": "healthy",
        "service": "email-api",
        "api_key": api_key_status,
        "config": {
            "from_email": FROM_EMAIL,
            "to_email": TO_EMAIL,
            "subject": os.getenv("EMAIL_SUBJECT", "New Contact Form Message")
        }
    }), 200

@app.route('/test', methods=['GET'])
def test_config():
    """Test endpoint to verify configuration"""
    return jsonify({
        "resend_api_key": "SET" if resend.api_key else "MISSING",
        "from_email": FROM_EMAIL,
        "to_email": TO_EMAIL,
        "ready_to_send": bool(resend.api_key)
    })

if __name__ == '__main__':
    app.run(debug=True)