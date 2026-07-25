# Chat App: Flask Server + Rich CLI Client

URL TEST: https://tmqbc-125-27-42-5.run.pinggy-free.link

# Chat App: Flask Server + Python Chat Clients (CLI / GUI)

โปรเจกต์นี้มี 2 ส่วน:

- `server/` — Flask server สำหรับรับ-ส่งข้อความแชท (REST API แบบ polling)
- `client/` — chat client เขียนด้วย Python มี 2 แบบให้เลือก:
  - `chat_client.py` — CLI, ใช้ library Rich
  - `chat_client_tk.py` — GUI, ใช้ Tkinter (มาพร้อม Python อยู่แล้ว)

## 1. รัน Flask server

```bash
cd chat-app/server
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Server จะรันที่ `http://0.0.0.0:5000`

## 2. Tunnel ด้วย pinggy.io

เปิด terminal ใหม่ (ไม่ต้อง sign up, ไม่ต้องติดตั้งอะไรเพิ่ม ใช้ ssh ที่มีอยู่แล้ว):

```bash
ssh -p 443 -R0:localhost:5000 free.pinggy.io
```

ถ้าถูกถาม password ให้กด Enter เฉย ๆ (ไม่ต้องใส่อะไร). คำสั่งนี้จะขึ้น URL แบบ `https://xxxxx.a.free.pinggy.link` มาให้ — คัดลอก URL นี้ไว้ใช้ในขั้นตอนถัดไป (tunnel ฟรีมีอายุ 60 นาทีต่อครั้ง รันคำสั่งใหม่ได้เรื่อย ๆ ถ้าหมดอายุ)

## 3. รัน chat client

เปิด terminal อีกอัน (ทำได้ทั้งบนเครื่องเดียวกันหรือเครื่องอื่น):

```bash
cd chat-app/client
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

จากนั้นเลือกรันแบบใดแบบหนึ่ง:

**แบบ CLI (Rich)**

```bash
python chat_client.py
```

โปรแกรมจะถาม Server URL แล้วตามด้วยชื่อ, พิมพ์ข้อความแล้ว Enter เพื่อส่ง, พิมพ์ `/exit` เพื่อออก

**แบบ GUI (Tkinter)**

```bash
python chat_client_tk.py
```

กรอก Server URL + ชื่อ แล้วกด Connect จะเปิดหน้าต่างแชท มีช่องพิมพ์ + ปุ่ม Send (กด Enter ส่งได้เหมือนกัน)
ถ้าใช้ Linux แล้วเจอ `ModuleNotFoundError: No module named 'tkinter'` ให้ลง `sudo apt install python3-tk` (Windows/Mac มี tkinter มาพร้อม Python อยู่แล้ว ไม่ต้องลงเพิ่ม)

---

ทั้งสองแบบใช้ Server URL เดียวกันจากขั้นตอนที่ 2 และรันได้หลาย instance พร้อมกัน (คนละเครื่อง/คนละ terminal, จะเป็น CLI หรือ GUI ผสมกันก็ได้) ทุกคนจะเห็นข้อความของกันและกันแบบเกือบ real-time (polling ทุก 1 วินาที)

## หมายเหตุ

- ข้อความเก็บอยู่ใน memory ของ server เท่านั้น (ไม่มีฐานข้อมูล) ถ้า restart server ข้อความเก่าจะหาย
- ถ้าต้องการ URL ที่ไม่เปลี่ยนทุก 60 นาที ให้ดูแผน paid ของ pinggy.io หรือ deploy server ขึ้น hosting จริง

## หมายเหตุ

- ข้อความเก็บอยู่ใน memory ของ server เท่านั้น (ไม่มีฐานข้อมูล) ถ้า restart server ข้อความเก่าจะหาย
- ถ้าต้องการ URL ที่ไม่เปลี่ยนทุก 60 นาที ให้ดูแผน paid ของ pinggy.io หรือ deploy server ขึ้น hosting จริง
