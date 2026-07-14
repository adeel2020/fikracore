import os
import subprocess
import json
import urllib.request
import urllib.parse
from fastapi import APIRouter, Query, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.config import settings
from backend.database.db import get_db

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp-bot"])

VERIFY_TOKEN = getattr(settings, "whatsapp_verify_token", "sa4dst_verify_token")
PHONE_NUMBER_ID = getattr(settings, "whatsapp_phone_number_id", None)
ACCESS_TOKEN = getattr(settings, "whatsapp_token", None)

def get_workspace_root() -> str:
    """Finds the workspace root dynamically by searching upwards for a signature file/directory."""
    current = os.path.abspath(__file__)
    while True:
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        if os.path.exists(os.path.join(parent, "pyproject.toml")) or os.path.exists(os.path.join(parent, "uv.lock")):
            return parent
        current = parent

def capture_chart_image(element_id: str) -> str:
    """Invokes the Node.js Puppeteer capture script to take a screenshot of a specific chart."""
    root_dir = get_workspace_root()
    frontend_dir = os.path.join(root_dir, "frontend")
    script_path = os.path.join(root_dir, "whatsapp_integration", "frontend", "scripts", "capture_chart.js")
    
    # Save the screenshot inside the workspace's scratch directory
    scratch_dir = os.path.join(root_dir, "scratch")
    os.makedirs(scratch_dir, exist_ok=True)
    temp_path = os.path.join(scratch_dir, f"{element_id}.png")
    
    # Configure environment with NODE_PATH to resolve packages from the active frontend/node_modules
    env = os.environ.copy()
    env["NODE_PATH"] = os.path.join(frontend_dir, "node_modules")
    
    # Run Puppeteer node script
    cmd = ["node", script_path, element_id, temp_path, "3000"]
    print(f"[WhatsApp Bot] Executing capture command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=frontend_dir, env=env)
    
    if result.returncode != 0:
        print(f"[WhatsApp Bot] Capture script error: {result.stderr}")
        raise Exception(f"Failed to capture chart: {result.stderr}")
        
    return temp_path

def send_whatsapp_text(recipient: str, text: str):
    """Sends a text message using the WhatsApp Cloud API (urllib fallback)."""
    if not PHONE_NUMBER_ID or not ACCESS_TOKEN:
        print(f"[WhatsApp Bot MOCK Send] To: {recipient}, Text: {text}")
        return

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {
            "body": text
        }
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"), 
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read().decode("utf-8"))
            print(f"[WhatsApp Bot] Text sent successfully: {response}")
    except Exception as e:
        print(f"[WhatsApp Bot] Error sending WhatsApp text: {e}")

def send_whatsapp_image(recipient: str, image_path: str, caption: str):
    """Uploads the local image to Meta and sends it to the recipient."""
    if not PHONE_NUMBER_ID or not ACCESS_TOKEN:
        print(f"[WhatsApp Bot MOCK Send] To: {recipient}, Image: {image_path}, Caption: {caption}")
        return

    # 1. Upload the media file
    upload_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/media"
    
    # Construct multipart form-data payload manually
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    parts = []
    
    parts.append(f"--{boundary}")
    parts.append('Content-Disposition: form-data; name="messaging_product"')
    parts.append('')
    parts.append('whatsapp')
    
    parts.append(f"--{boundary}")
    filename = os.path.basename(image_path)
    parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"')
    parts.append('Content-Type: image/png')
    parts.append('')
    
    with open(image_path, "rb") as f:
        file_content = f.read()
        
    body = b""
    for p in parts:
        body += p.encode("utf-8") + b"\r\n"
    body += file_content + b"\r\n"
    body += f"--{boundary}--\r\n".encode("utf-8")
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }
    
    try:
        req = urllib.request.Request(upload_url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            media_id = res_data.get("id")
            print(f"[WhatsApp Bot] Media uploaded successfully, ID: {media_id}")
            
            if not media_id:
                raise Exception("Media ID not returned by Meta upload endpoint")
                
            # 2. Send the message containing the media ID
            msg_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
            msg_headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            msg_payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "image",
                "image": {
                    "id": media_id,
                    "caption": caption
                }
            }
            
            msg_req = urllib.request.Request(
                msg_url, 
                data=json.dumps(msg_payload).encode("utf-8"), 
                headers=msg_headers,
                method="POST"
            )
            with urllib.request.urlopen(msg_req) as msg_res:
                response = json.loads(msg_res.read().decode("utf-8"))
                print(f"[WhatsApp Bot] Image message sent successfully: {response}")
                
    except Exception as e:
        print(f"[WhatsApp Bot] Error sending WhatsApp image: {e}")

def send_whatsapp_interactive_list(recipient: str):
    """Sends an interactive list message containing dashboard chart choices."""
    if not PHONE_NUMBER_ID or not ACCESS_TOKEN:
        mock_menu = (
            "[WhatsApp Bot MOCK Send Interactive List] To: {}\n"
            "Options:\n"
            "1. weekly-volume-card (Weekly Complaint Volume)\n"
            "2. avg-queue-times-card (Average Queue Times)\n"
            "3. ticket-distribution-card (Ticket Distribution)\n"
            "4. top-complaint-categories-card (Top Complaint Categories)\n"
            "5. trouble-tickets-card (Trouble Tickets Handled)"
        ).format(recipient)
        print(mock_menu)
        return

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Dashboard Charts"
            },
            "body": {
                "text": "Please select a chart to view the live dashboard data."
            },
            "footer": {
                "text": "Customer Operations Observability"
            },
            "action": {
                "button": "Select Chart",
                "sections": [
                    {
                        "title": "Available Charts",
                        "rows": [
                            {
                                "id": "weekly-volume-card",
                                "title": "Weekly Volume",
                                "description": "Weekly complaint volume trends"
                            },
                            {
                                "id": "avg-queue-times-card",
                                "title": "Queue Times",
                                "description": "Average queue times per category"
                            },
                            {
                                "id": "ticket-distribution-card",
                                "title": "Ticket Distribution",
                                "description": "Total ticket distribution"
                            },
                            {
                                "id": "top-complaint-categories-card",
                                "title": "Top Complaint Categories",
                                "description": "Top complaint categories"
                            },
                            {
                                "id": "trouble-tickets-card",
                                "title": "Trouble Tickets",
                                "description": "Trouble tickets handled in 30 days"
                            }
                        ]
                    }
                ]
            }
        }
    }

    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"), 
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read().decode("utf-8"))
            print(f"[WhatsApp Bot] Interactive list sent successfully: {response}")
    except Exception as e:
        print(f"[WhatsApp Bot] Error sending WhatsApp interactive list: {e}")

@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """Meta Webhook Challenge Verification."""
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print(f"[WhatsApp Webhook] Verification successful. Challenge: {challenge}")
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@router.post("/webhook")
async def receive_event(request: Request, db: Session = Depends(get_db)):
    """Receives inbound messages and interactive button clicks from WhatsApp."""
    try:
        payload = await request.json()
        print(f"[WhatsApp Webhook] Event received: {json.dumps(payload)}")
        
        # Extract messages list
        entry = payload.get("entry", [])
        if not entry:
            return {"status": "no entry found"}
            
        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "no changes found"}
            
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return {"status": "no messages found"}
            
        message = messages[0]
        sender_phone = message.get("from")
        msg_type = message.get("type")
        
        user_choice = ""
        
        if msg_type == "text":
            user_choice = message.get("text", {}).get("body", "").strip().lower()
        elif msg_type == "interactive":
            interactive = message.get("interactive", {})
            int_type = interactive.get("type")
            if int_type == "button_reply":
                user_choice = interactive.get("button_reply", {}).get("id", "").strip().lower()
            elif int_type == "list_reply":
                user_choice = interactive.get("list_reply", {}).get("id", "").strip().lower()
                
        if not user_choice:
            return {"status": "unsupported message type"}
            
        # Map user input options to card DOM element selectors
        chart_map = {
            "1": ("weekly-volume-card", "Weekly Complaint Volume"),
            "weekly volume": ("weekly-volume-card", "Weekly Complaint Volume"),
            "weekly-volume-card": ("weekly-volume-card", "Weekly Complaint Volume"),
            
            "2": ("avg-queue-times-card", "Average Queue Times"),
            "queue times": ("avg-queue-times-card", "Average Queue Times"),
            "avg-queue-times-card": ("avg-queue-times-card", "Average Queue Times"),
            
            "3": ("ticket-distribution-card", "Ticket Distribution"),
            "ticket distribution": ("ticket-distribution-card", "Ticket Distribution"),
            "ticket-distribution-card": ("ticket-distribution-card", "Ticket Distribution"),
            
            "4": ("top-complaint-categories-card", "Top Complaint Categories"),
            "top complaint": ("top-complaint-categories-card", "Top Complaint Categories"),
            "top-complaint-categories-card": ("top-complaint-categories-card", "Top Complaint Categories"),
            
            "5": ("trouble-tickets-card", "Trouble Tickets Handled"),
            "trouble tickets": ("trouble-tickets-card", "Trouble Tickets Handled"),
            "trouble-tickets-card": ("trouble-tickets-card", "Trouble Tickets Handled")
        }
        
        if user_choice in chart_map:
            element_id, title = chart_map[user_choice]
            send_whatsapp_text(sender_phone, f"Generating chart '{title}', please wait...")
            
            try:
                # Capture target chart component
                image_path = capture_chart_image(element_id)
                send_whatsapp_image(sender_phone, image_path, f"Here is the requested '{title}' chart.")
            except Exception as capture_error:
                send_whatsapp_text(sender_phone, f"Failed to generate chart: {str(capture_error)}")
        else:
            # Send the interactive menu
            send_whatsapp_interactive_list(sender_phone)
            
        return {"status": "success"}
    except Exception as e:
        print(f"[WhatsApp Webhook] Exception during event handling: {e}")
        return {"status": "error", "detail": str(e)}
