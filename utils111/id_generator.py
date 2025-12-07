import uuid

def generate_uuid():
    """
    إنشاء معرف فريد عشوائي (UUID Version 4).
    يستخدم هذا المعرف كـ Primary Key لجميع الجداول (Users, Sections, Content...)
    لضمان عدم تكرار الأرقام حتى لو قام شخصان بالإضافة في نفس الوقت.
    """
    return str(uuid.uuid4())
