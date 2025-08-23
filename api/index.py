from flask import Flask, request, jsonify
import resend
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Secure way to get API key from environment variables
resend.api_key = os.getenv("RESEND_API_KEY")

@app.route('/')
def home():
    return 'Email API is running!'



@app.route('/send-email', methods=['POST'])
def send_email():
    try:
        # Check if API key is configured
        if not resend.api_key:
            return jsonify({"error": "Email service not configured"}), 500
        
        # Domain-based security check
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
        
        # Validate required fields - now only message and reply_to needed from API
        if not data or not data.get('message'):
            return jsonify({"error": "Missing required field: message"}), 400
        
        # reply_to is required from the API call
        if not data.get('reply_to'):
            return jsonify({"error": "Missing required field: reply_to"}), 400
        
        # Validate reply_to email format
        reply_to = data.get('reply_to')
        if '@' not in reply_to or '.' not in reply_to.split('@')[1]:
            return jsonify({"error": "Invalid reply_to email format"}), 400
        
        # Rate limiting check (basic implementation)
        # In production, use Redis or similar for proper rate limiting
        
        # Prepare email parameters - to and subject from environment
        params = {
            "from": os.getenv("FROM_EMAIL", "noreply@yourdomain.com"),
            "to": [os.getenv("TO_EMAIL", "contact@yourdomain.com")],  # Fixed recipient from env
            "subject": os.getenv("EMAIL_SUBJECT", "New Contact Form Message"),  # Fixed subject from env
            "html": f"""
                <h3>New message from your website</h3>
                <p><strong>From:</strong> {reply_to}</p>
                <p><strong>Message:</strong></p>
                <p>{data['message']}</p>
            """,
            "reply_to": reply_to  # This comes from API call
        }
        
        # Send email
        email = resend.Emails.send(params)
        
        return jsonify({
            "success": True,
            "message": "Email sent successfully",
            "email_id": email.get('id') if hasattr(email, 'get') else str(email)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to send email",
            "details": str(e)
        }), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "email-api"}), 200

if __name__ == '__main__':
    app.run(debug=True)