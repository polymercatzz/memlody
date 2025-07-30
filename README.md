# 🧠 MEMLODY - โปรแกรมฝึกสมองห่างไกลอัลไซเมอร์

**Memlody** คือเว็บแอปพลิเคชันสำหรับผู้ป่วยอัลไซเมอร์ระยะที่ 1–2  
เพื่อ **ฝึกสมอง**, **กระตุ้นความทรงจำ**, และ **เสริมสุขภาพจิต** ผ่านกิจกรรมเชิงเกม  
โดยมีครอบครัวร่วมเป็นส่วนหนึ่งของการดูแลแบบอบอุ่น

---

## **จุดประสงค์ของโปรเจกต์**

- ✅ ช่วยชะลอการเสื่อมของสมองด้วยกิจกรรมหลายประสาทสัมผัส  
- ✅ เพิ่มปฏิสัมพันธ์ระหว่างผู้ป่วยและครอบครัว (My Voice Mode)  
- ✅ ใช้งานง่ายบนอุปกรณ์ทั่วไป: มือถือ, แท็บเล็ต, คอมพิวเตอร์  
- ✅ เก็บสถิติเพื่อประเมินผลและวิเคราะห์แนวโน้มด้วย Prophet  
- ✅ นำ AI (Whisper + NLP) มาเสริมประสบการณ์ฝึกสมอง

---

## **ฟีเจอร์เด่น**

**เกมนี่เสียงอะไร?**  
- โหมดจับคู่เสียงกับภาพ  
- โหมดพูดตอบคำถาม  
- โหมดเสียงของฉัน (ใช้เสียงจากครอบครัว)

**เกมทายของจากรูปภาพ**  
- โหมดเลือกคำตอบ  
- โหมดพูดตอบภาพ  
- โหมดเรียงลำดับเหตุการณ์

**ระบบสถิติ & กราฟ**  
- วิเคราะห์คะแนนและเวลาที่ใช้  
- ประเมินพัฒนาการรายบุคคล  
- ใช้ Prophet ในการคาดการณ์แนวโน้มพฤติกรรม

---

## **เทคโนโลยีที่ใช้**

**Frontend**  
- HTML5 / CSS (Tailwind) / JavaScript  

**Backend**  
- FastAPI / Uvicorn  

**AI & NLP**  
- Whisper (via Faster-Whisper)  
- PyThaiNLP  

**Data & Security**  
- PostgreSQL / SQLAlchemy / Psycopg2  
- Pandas / Prophet  
- dotenv / Passlib[bcrypt] / Itsdangerous  

**Template & Upload**  
- Jinja2 / python-multipart

---

## 📦 ขั้นตอนติดตั้งโปรเจกต์

**1. Clone โปรเจกต์**

```bash
git clone https://github.com/polymercatzz/memlody.git
cd memlody
```

**2.สร้าง Virtual Environment และติดตั้ง dependencies**
python -m venv env

```bash
python -m venv env
source env/bin/activate       # สำหรับ Mac/Linux
env\Scripts\activate          # สำหรับ Windows
pip install -r requirements.txt
```

**3.สร้างไฟล์ .env**

```bash
# 🔒 ADMIN
ADMIN_ID=admin@example.com

# 🗄️ DATABASE
user=your_postgres_user
password=your_postgres_password
host=localhost
port=5432
dbname=memlody_db

# 🔐 ENCRYPTION KEY
key_middle=your_custom_encryption_key
```
**4.รันเซิร์ฟเวอร์**
```bash
uvicorn main:app --reload --port 8000
```

