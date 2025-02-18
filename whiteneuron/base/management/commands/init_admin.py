# Khởi tạo admin interface theme cho hệ thống sử dụng BaseCommand

from django.core.management.base import BaseCommand
from apps.base.models import User

def init_admin():
    if User.objects.filter(username='admin').count() == 0:
        password = 'wnadmin2024&'
        User.objects.create_superuser('admin', 'ntanhtm@gmail.com', password)

        print('Tạo người dùng admin thành công')
        return True
    else:
        print('Người dùng admin đã tồn tại')
        return False
    
class Command(BaseCommand):
    help = 'Khởi tạo người dùng mặc định cho hệ thống'

    def handle(self, *args, **kwargs):
        fl= init_admin()
        if fl:
            self.stdout.write(self.style.SUCCESS('Khởi tạo người dùng mặc định cho hệ thống thành công'))
        else:
            self.stdout.write(self.style.ERROR('Khởi tạo người dùng mặc định cho hệ thống không thành công vì đã tồn tại'))