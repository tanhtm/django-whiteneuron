# Khởi tạo guest interface theme cho hệ thống sử dụng BaseCommand

from django.core.management.base import BaseCommand
from whiteneuron.base.models import User, Group

def init_admin():
    if User.objects.filter(username='guest').count() == 0:
        password = 'whiteneuron-guest-2024@'
        user= User(username='guest')
        user.set_password(password)
        user.save()
    else:
        user= User.objects.get(username='guest')
        print('Người dùng guest đã tồn tại')

    # group guest
    gr= Group.objects.get(name='Khách thăm')
    user.groups.add(gr)
    user.save()

    print('Tạo người dùng guest thành công')
    return True
    
class Command(BaseCommand):
    help = 'Khởi tạo người dùng mặc định cho hệ thống'

    def handle(self, *args, **kwargs):
        fl= init_admin()
        if fl:
            self.stdout.write(self.style.SUCCESS('Khởi tạo người dùng mặc định cho hệ thống thành công'))
        else:
            self.stdout.write(self.style.ERROR('Khởi tạo người dùng mặc định cho hệ thống không thành công vì đã tồn tại'))