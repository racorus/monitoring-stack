from fastapi import FastAPI, Request, HTTPException
import httpx
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
import os
import json

app = FastAPI()

# Load Environment Variables
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
TO = os.getenv("LINE_TARGET_ID")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 25))  # Changed default to 25
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
EMAIL_TO = os.getenv("EMAIL_TO")

@app.post("/sendline")
async def send_line_alert(request: Request):
    try:
        data = await request.json()
        message_text = parse_alert(data)
        await send_line(message_text)
        return {"message": "Sent LINE notification successfully."}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sendemail")
async def send_email_alert(request: Request):
    try:
        data = await request.json()
        message_text = parse_alert(data)
        result = send_email("Prometheus Alert", message_text)
        return {"message": f"Email status: {result}"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alert")
async def alert(request: Request):
    try:
        data = await request.json()
        message_text = parse_alert(data)
        
        # Send Line alert
        line_result = "Failed"
        try:
            await send_line(message_text)
            line_result = "Success"
        except Exception as e:
            line_result = f"Error: {str(e)}"
        
        # Send Email alert
        email_result = "Failed"
        try:
            email_result = send_email("Prometheus Alert", message_text)
        except Exception as e:
            email_result = f"Error: {str(e)}"
            
        return {
            "message": "Alert processing completed", 
            "line_status": line_result, 
            "email_status": email_result
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def parse_alert(data):
    alerts = data.get('alerts', [])
    messages = []
    for alert in alerts:
        status = alert.get('status')
        summary = alert['annotations'].get('summary', 'No summary')
        description = alert['annotations'].get('description', 'No description')
        labels = alert.get('labels', {})
        server_info = f"Server: {labels.get('server_name', labels.get('instance', 'Unknown'))}"
        messages.append(f"[{status}] {summary}\n{description}\n{server_info}")
    return '\n\n'.join(messages)

async def send_line(message_text):
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": TO,
        "messages": [{
            "type": "text",
            "text": message_text
        }]
    }
    async with httpx.AsyncClient() as client:
        await client.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

def send_email(subject, body):
    # Skip email if SMTP settings are not complete
    if not all([SMTP_SERVER, SMTP_USERNAME, EMAIL_TO]):
        return "Email skipped: Missing configuration"
        
    # Follow the example script format
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = formataddr(('Prometheus Alert', SMTP_USERNAME))
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            # No TLS, no login - just like your example
            server.sendmail(SMTP_USERNAME, [EMAIL_TO], msg.as_string())
            return "Success"
    except Exception as e:
        return f"Failed: {str(e)}"

# Add a simple health check endpoint
@app.get("/")
def health_check():
    return {
        "status": "OK", 
        "line_token_configured": bool(LINE_TOKEN), 
        "smtp_configured": bool(SMTP_SERVER)
    }
