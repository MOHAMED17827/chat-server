# Chat Server (FastAPI)

خادم محادثة بسيط باستخدام FastAPI و WebSocket و SQLite.

## الميزات:
- تسجيل مستخدم جديد
- تسجيل الدخول
- حفظ الرسائل في قاعدة بيانات
- عرض آخر ظهور وحالة الاتصال
- دعم WebSocket للمحادثة المباشرة

## التشغيل المحلي:
```bash
pip install -r requirements.txt
uvicorn server:app --reload
