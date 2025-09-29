import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
from flask import current_app

def send_email_notification(to_email, message, subject="Student Management System Notification"):
    try:
        # Configure your SMTP settings
        smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_username = current_app.config.get('SMTP_USERNAME')
        smtp_password = current_app.config.get('SMTP_PASSWORD')
        
        # Create message
        msg = MimeMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MimeText(message, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def send_sms_notification(phone_number, message):
    try:
        # Configure your SMS gateway settings
        # This is a placeholder - you'll need to integrate with your SMS provider
        api_key = current_app.config.get('SMS_API_KEY')
        api_secret = current_app.config.get('SMS_API_SECRET')
        from_number = current_app.config.get('SMS_FROM_NUMBER')
        
        # Example using Twilio (you would need to install twilio package)
        # from twilio.rest import Client
        # client = Client(api_key, api_secret)
        # message = client.messages.create(
        #     body=message,
        #     from_=from_number,
        #     to=phone_number
        # )
        
        # For now, just log the SMS (implement actual SMS service as needed)
        print(f"SMS to {phone_number}: {message}")
        
        return True, "SMS sent successfully"
    except Exception as e:
        return False, f"Failed to send SMS: {str(e)}"