# Chat App: Flask Server + Rich CLI Client

โปรเจกต์นี้มี 2 ส่วน:

- `server/` — Flask server สำหรับรับ-ส่งข้อความแชท (REST API แบบ polling)
- `client/` — CLI chat client เขียนด้วย Python + Rich

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

## 3. รัน CLI chat client

เปิด terminal อีกอัน (ทำได้ทั้งบนเครื่องเดียวกันหรือเครื่องอื่น):

```bash
cd chat-app/client
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python chat_client.py
```

โปรแกรมจะถาม:

1. **Server URL** — วาง URL จาก pinggy.io ที่ได้จากขั้นตอนที่ 2
2. **Your name** — ชื่อที่จะใช้แชท

จากนั้นพิมพ์ข้อความแล้ว Enter เพื่อส่ง, พิมพ์ `/exit` เพื่อออกจากโปรแกรม

รันโปรแกรมนี้ได้หลาย instance (คนละเครื่อง/คนละ terminal) โดยใช้ URL เดียวกัน ทุกคนจะเห็นข้อความของกันและกันแบบเกือบ real-time (polling ทุก 1 วินาที)

## หมายเหตุ

- ข้อความเก็บอยู่ใน memory ของ server เท่านั้น (ไม่มีฐานข้อมูล) ถ้า restart server ข้อความเก่าจะหาย
- ถ้าต้องการ URL ที่ไม่เปลี่ยนทุก 60 นาที ให้ดูแผน paid ของ pinggy.io หรือ deploy server ขึ้น hosting จริง
