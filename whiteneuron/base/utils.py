from django.utils import timezone
from .models import User, UserActivity, Notification
from django.contrib.auth.models import Group

# count time run function
def timeit(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} run in {time.time()-start} seconds")
        return result
    return wrapper

def base_badge_callback(request, model):
    # lấy số lượng link từ bảng model từ sáng tạo đến nay
    # Nếu 
    c= model.objects.filter(updated_at__gte= timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)).count()
    if c==0:
        return ''
    return f"+{c}"

def user_badge_callback(request):
    return base_badge_callback(request, User)

def useractivity_badge_callback(request):
    c= UserActivity.objects.filter(timestamp__gte= timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)).count()
    if c==0:
        return ''
    return f"+{c}"

def user_badge_callback(request):
    return base_badge_callback(request, User)

def group_badge_callback(request):
    return ""

def notification_badge_callback(request):
    c= Notification.objects.filter(
        user=request.user,
        is_read=False,
        created_at__gte= timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)).count()
    if c==0:
        return ''
    return f"+{c}"

def permission_callback(request):
    return False

def permission_superuser_callback(request):
    return request.user.is_superuser

def permission_admin_callback(request):
    if request.user.is_superuser:
        return True
    return request.user.groups.filter(name='Quản trị viên').exists()

def permission_non_guest_callback(request):
    return not request.user.groups.filter(name='Khách thăm').exists()


from django.conf import settings
from .models import Mail
def send_email_login(username, password, receiver):
    SUBJECT=  "Thông tin đăng nhập hệ thống"
    SYSTEM_NAME= settings.NAME
    URL= settings.URL
    TEMMPLATE= open('templates/admin/base/email_password.html').read()
    subject= SUBJECT
    template= TEMMPLATE
    system_name= SYSTEM_NAME
    context= template.format(username= username, password= password, url= URL, system_name= system_name)
    mail= Mail.objects.create(subject= subject, content= context, receiver= receiver)
    mail.send()
    return mail.is_sent()

def make_random_password():
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))