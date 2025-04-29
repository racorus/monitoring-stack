from fastapi import FastAPI
import httpx
import socket
import datetime
import json
import os

app = FastAPI()

# โหลดไฟล์ config
config_path = os.environ.get('CONFIG_PATH', '/app/config/servers.json')
with open(config_path, 'r') as f:
    config = json.load(f)

@app.get("/")
async def health():
    results = {"status": "healthy", "servers": {}, "services": {}}
    
    # ตรวจสอบทุกเซิร์ฟเวอร์
    for server in config.get('servers', []):
        name = server.get("name")
        ip = server.get("ip")
        port = server.get("port", 9100)
        
        # ตรวจสอบการเชื่อมต่อ TCP
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, port))
            if result == 0:
                results["servers"][name] = "online"
            else:
                results["servers"][name] = "offline"
                results["status"] = "degraded"
            sock.close()
        except Exception as e:
            results["servers"][name] = f"error: {str(e)}"
            results["status"] = "degraded"
    
    # ตรวจสอบบริการต่างๆ
    for service in config.get('services', []):
        name = service.get("name")
        host = service.get("host")
        port = service.get("port")
        health_endpoint = service.get("health_endpoint", "/")
        
        # สร้าง URL
        url = f"http://{host}:{port}{health_endpoint}"
        
        # ตรวจสอบบริการ
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    results["services"][name] = "healthy"
                else:
                    results["services"][name] = f"unhealthy ({response.status_code})"
                    results["status"] = "degraded"
        except Exception as e:
            results["services"][name] = f"error: {str(e)}"
            results["status"] = "degraded"
    
    # เพิ่มเวลาที่ตรวจสอบ
    results["timestamp"] = str(datetime.datetime.now())
    
    return results

@app.get("/simple")
async def simple_health():
    """Simple endpoint ที่ให้ผลลัพธ์แบบง่ายมาก สำหรับการตรวจสอบแบบเร็ว"""
    return {"status": "OK", "timestamp": str(datetime.datetime.now())}
