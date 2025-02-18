from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

GROUP= {
    'admin': 'Quản trị viên',
    'manager': 'Quản lý',
    'staff': 'Nhân viên',
    'customer': 'Khách hàng',
    'guest': 'Khách thăm',
}

PERMISSIONS= {}
PERMISSIONS['admin']= {
    "exclude": [], # Các model không được phép truy cập
    "view": ["*"],
    "add": ["*"],
    "change": ["*"],
    "delete": ["*"],
}
PERMISSIONS['guest']= {
    "exclude": ["user", "useractivity", 
                "group", "permission", 
                "contenttype", "logentry", 
                "session", "token", "authtoken", "excelfile", "pdffile"
                ],
    "view": ["*"],
    "add": [],
    "change": [],
    "delete": [],
}
PERMISSIONS['customer']= {
    "exclude": ["user", "useractivity",
                "group", "permission",
                "contenttype", "logentry",
                "session", "token", "authtoken",
                ],
    "view": ["*"],
    "add": [],
    "change": [],
    "delete": [],
}
PERMISSIONS['staff']= {
    "exclude": ["user", "useractivity",
                "group", "permission",
                "contenttype", "logentry",
                "session", "token", "authtoken",
                ],
    "view": ["*"],
    "add": [],
    "change": [],
    "delete": [],
}
PERMISSIONS['manager']= {
    "exclude": [],
    "view": ["*"],
    "add": ["*"],
    "change": ["*"],
    "delete": [],
}

def init_group():
    for group, name in GROUP.items():
        g, created= Group.objects.get_or_create(name= name)
        print(f"Group {name} {'created' if created else 'existed'}")
        # Xóa tất cả các permission cũ
        g.permissions.clear()
        for perm, models in PERMISSIONS[group].items():
            for model in models:
                if model=='*':
                    for p in Permission.objects.filter(codename__icontains= perm).exclude(content_type__model__in= PERMISSIONS[group]['exclude']):
                        g.permissions.add(p)
                        # print(f"Add permission {p} to group {name}: {p.codename}")
                else:
                    for p in Permission.objects.filter(content_type__model= model, codename__icontains= perm):
                        g.permissions.add(p)

class Command(BaseCommand):
    help = 'Initialize group and permissions'

    def handle(self, *args, **kwargs):
        init_group()
        print('Done')
