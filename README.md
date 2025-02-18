# django-whiteneuron 🚀  

**django-whiteneuron** là một gói mở rộng mạnh mẽ giúp nâng cấp Django Admin Site với giao diện hiện đại, tùy chỉnh linh hoạt và tích hợp nhiều tính năng hỗ trợ quản lý dữ liệu chuyên sâu.  

---

## 📥 **Cài đặt**  

### **1️⃣ Cài đặt package**  
Sử dụng pip để cài đặt `django-whiteneuron`:  
```bash
pip install django-whiteneuron
```

---

### **2️⃣ Cấu hình Frontend - TailwindCSS & DaisyUI**  

**Lưu ý:** Package này **chỉ chạy với TailwindCSS phiên bản 3.4.17**.  

#### **Cài đặt TailwindCSS**  
```bash
npm install tailwindcss
```

#### **Tạo file cấu hình `tailwind.config.js`**  
```bash
npx tailwindcss init
```

#### **Thêm DaisyUI vào `package.json`**  
Thêm dòng sau vào `package.json` trong phần `dependencies`:  
```json
"daisyui": "^4.12.10"
```
Sau đó chạy lệnh:  
```bash
npm install
```

#### **Tạo file `styles.css` ở thư mục gốc của project**  
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

### **3️⃣ Cấu hình Django**  

#### **Thêm vào `INSTALLED_APPS` trong `settings.py`**  
```python
INSTALLED_APPS = [
    "whiteneuron.base",         # Base app
    "whiteneuron.feedbacks",    # Feedbacks app
    "whiteneuron.file_management", # File management app
    "whiteneuron.contrib",      # Contrib app
    "whiteneuron.dashboard",    # Dashboard app
]
```

#### **Thêm vào `MIDDLEWARE`**  
```python
MIDDLEWARE = [
    "whiteneuron.base.middleware.ReadonlyExceptionHandlerMiddleware",
    "whiteneuron.base.middleware.UserActivityMiddleware",
]
```

#### **Thiết lập Model User tùy chỉnh**  
```python
AUTH_USER_MODEL = "base.User"
```

---

## ⚙ **Cấu hình giao diện & Admin Panel (Unfold)**  

Thêm vào `settings.py`:  

```python
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_HEADER": _("White Neuron"),
    "SITE_TITLE": _("White Neuron Admin"),
    "SITE_SUBHEADER": _("Admin panel"),
    "SITE_DROPDOWN": [
        {
            "icon": "diamond",
            "title": _("White Neuron Co. Ltd."),
            "link": "https://whiteneuron.com/",
        },
        {
            "icon": "rocket_launch",
            "title": _("Email: anhnt@whiteneuron.com"),
            "link": "mailto:anhnt@whiteneuron.com",
        },
    ],
    "SITE_ICON": {
        "light": lambda request: static("base/images/logo/logo.png"),
        "dark": lambda request: static("base/images/logo/logo.png"),
    },
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("base/images/logo/logo.png"),
        },
    ],
    "SHOW_HISTORY": True,
    "SHOW_LANGUAGES": True,
    "ENVIRONMENT": "CCMS.utils.environment_callback",
    "DASHBOARD_CALLBACK": "apps.dashboard.views.dashboard_callback",
    "LOGIN": {
        "image": lambda request: static("base/images/login_bg.jpg"),
    },
    "STYLES": [
        lambda request: static("base/css/styles.css"),
        lambda request: static("base/css/btn-styles.css"),
        lambda request: static("base/css/loading.css"),
    ],
    "SCRIPTS": [
        lambda request: static("base/js/loading.js"),
    ],
}
```

---

## 📌 **Tích hợp Sidebar & Menu điều hướng**  
Thêm vào `settings.py` để tùy chỉnh Sidebar:  

```python
UNFOLD["SIDEBAR"] = {
    "show_search": True,
    "show_all_applications": False,
    "navigation": [
        {
            "title": _("Navigation"),
            "items": [
                {
                    "title": _("Dashboard"),
                    "icon": "dashboard",
                    "link": reverse_lazy("admin:index"),
                },
                {
                    "title": _("Notifications"),
                    "icon": "notifications",
                    "link": reverse_lazy("admin:base_notification_changelist"),
                    "badge": "whiteneuron.base.utils.notification_badge_callback",
                },
                {
                    "title": _("Feedbacks"),
                    "icon": "feedback",
                    "link": reverse_lazy("admin:feedbacks_feedbackdata_changelist"),
                    "badge": "whiteneuron.feedbacks.utils.feedback_data_badge_callback",
                },
            ],
        },
        {
            "title": _("File Management"),
            "collapsible": True,
            "items": [
                {
                    "title": _("Excel Files"),
                    "icon": "table",
                    "link": reverse_lazy("admin:file_management_excelfile_changelist"),
                    "badge": "whiteneuron.file_management.utils.excelfile_badge_callback",
                },
                {
                    "title": _("PDF Files"),
                    "icon": "picture_as_pdf",
                    "link": reverse_lazy("admin:file_management_pdffile_changelist"),
                    "badge": "whiteneuron.file_management.utils.pdffile_badge_callback",
                },
            ],
        },
        {
            "title": _("Users & Groups"),
            "collapsible": True,
            "items": [
                {
                    "title": _("Users"),
                    "icon": "person",
                    "link": reverse_lazy("admin:base_user_changelist"),
                },
                {
                    "title": _("User Activity"),
                    "icon": "history",
                    "link": reverse_lazy("admin:base_useractivity_changelist"),
                },
                {
                    "title": _("Groups"),
                    "icon": "group",
                    "link": reverse_lazy("admin:auth_group_changelist"),
                },
            ],
        },
    ],
}
```

---

## 🛠 **Chạy dự án**
Sau khi hoàn tất cài đặt, chạy lệnh sau để khởi động Django:

```bash
python manage.py migrate
python manage.py runserver
```

Mở trình duyệt và truy cập:  
🔗 `http://127.0.0.1:8000/admin/`

---

## 📢 **Liên hệ & Hỗ trợ**
Nếu bạn có câu hỏi hoặc cần hỗ trợ, vui lòng liên hệ:  
📧 **Email:** [anhnt@whiteneuron.com](mailto:anhnt@whiteneuron.com)  
🌐 **Website:** [https://whiteneuron.com](https://whiteneuron.com)  
🚀 **GitHub Repo:** [https://github.com/tanhtm/django-whiteneuron](https://github.com/tanhtm/django-whiteneuron)

---

## 📜 **License**
`django-whiteneuron` được phát hành theo giấy phép **MIT License**, bạn có thể sử dụng miễn phí trong các dự án cá nhân và thương mại.

---

🔥 **django-whiteneuron** – Giải pháp tối ưu giúp bạn **nâng cấp Django Admin Site** một cách chuyên nghiệp, mạnh mẽ và hiện đại! 🚀