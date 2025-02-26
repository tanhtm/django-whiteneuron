from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
import os
from django.utils.safestring import mark_safe

from django.utils import timezone

############################################
# ImageModel
############################################
class ImageModel(models.Model):
    image = models.ImageField(upload_to='images/')

    # Tự động tạo thumbnail
    thumbnail = ImageSpecField(source='image',
                               processors=[ResizeToFill(50, 50)],
                               format='JPEG',
                               options={'quality': 90})

    def __str__(self):
        return self.image.name
    
    def display_image(self):
        return mark_safe(f'<img src="{self.image.url}" alt="{self.image}" />')
    
    def display_thumbnail(self):
        if self.image:
            return mark_safe(f'<img src="{self.thumbnail.url}" alt="{self.thumbnail}" />')
        return mark_safe(f'<span class="material-symbols-outlined" style="font-size: 50px;">person</span>')
    
    def clear(self):
        try:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        except:
            pass
        try:
            if os.path.isfile(self.thumbnail.path):
                os.remove(self.thumbnail.path)
        except:
            pass

    def listen(self, image_field: models.ImageField):
        # Nếu tạo mới thêm vào
        if not self.pk:
            self.image = image_field
            self.save()
        # Nếu cập nhật thì xóa cũ và thêm mới
        elif self.image != image_field:
            self.clear()
            self.image = image_field
            self.save()
        else:
            pass
############################################
# User
############################################
class Tag(models.Model):
    title = models.CharField(_("title"), max_length=255)
    slug = models.CharField(_("slug"), max_length=255)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, verbose_name=_("content type")
    )
    object_id = models.PositiveIntegerField(_("object id"))
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return self.tag

    class Meta:
        db_table = "tags"
        verbose_name = _("tag")
        verbose_name_plural = _("tags")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

from django.contrib.auth.models import Group
class User(AbstractUser):
    # avatar_obj= models.OneToOneField(ImageModel, on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='user_avatar')
    avatar = models.ImageField(_("avatar"), upload_to="avatars/", null=True, blank=True, default=None)
    biography = models.TextField(_("biography"), null=True, blank=True, default=None)
    tags = GenericRelation(Tag)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        db_table = "users"
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.last_name}, {self.first_name}"
        return None
    
    def display_avatar(self):
        if self.avatar:
            # print(instance.avatar.url)
            return mark_safe(f'<img src="{self.avatar.url}" style="width: 32px; height: 32px; border-radius: 50%;">')
        return mark_safe(f'<span class="material-symbols-outlined" style="font-size: 32px;">person</span>')
    
    def display_header(self):
        # Hiển thị avatar bên cạnh username 
        return mark_safe(f"""
        <a href="/admin/base/user/{self.id}/change/">
            <div style="display: flex; align-items: center;">
                <div style="border-radius: 50%; overflow: hidden;">
                         {self.display_avatar()}
                </div>
                <div style="margin-left: 10px;">
                    {self.username}
                </div>
            </div>
        </a>
        """)
    
    def save(self, request=None, *args, **kwargs):
        # if not self.pk:
        #     self.avatar_obj = ImageModel.objects.create()
        # self.avatar_obj.listen(self.avatar)
        
        # Nếu tạo mới thi mac dinh is_staff = True
        fl= False
        if not self.pk:
            self.is_staff = True
            fl= True
        super().save(*args, **kwargs)
        if fl:
            try:
                group_staff= Group.objects.get(name='Nhân viên')
                self.groups.add(group_staff)
            except:
                print('Group Nhân viên không tồn tại')
                pass

class UserProfile(User):
    class Meta:
        proxy = True
        verbose_name = _("user profile")
        verbose_name_plural = _("user profiles")

    def __str__(self):
        return self.username

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)
    user_agent = models.TextField(_("User agent"), null=True, blank=True)
    path = models.CharField(_("Path"), max_length=255, null=True, blank=True)
    method = models.CharField(_("Method"), max_length=10, choices=[("GET", "GET"), ("POST", "POST")], null=True, blank=True)
    data = models.JSONField(_("Data"), null=True, blank=True)
    status_code = models.IntegerField(_("Status code"), null=True, blank=True)
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    timelapse = models.DurationField(_("Timelapse"), null=True, blank=True) # Thời gian thực hiện hành động

    class Meta:
        db_table = "user_activities"
        verbose_name = _("user activity")
        verbose_name_plural = _("user activities")
        indexes = [
            models.Index(fields=["user", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.path} at {self.timestamp}"


############################################
# Base Model
############################################
class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, verbose_name= _('Deleted'))
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name= _('Deleted at'))

    class Meta:
        abstract = True  # Đây là một lớp trừu tượng, không tạo bảng trong DB

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self, using=None, keep_parents=False):
        super(SoftDeleteModel, self).delete(using=using, keep_parents=keep_parents)

    def restore(self, request=None):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

class BaseManager(models.Manager):
    def get_queryset(self):
        return super(BaseManager, self).get_queryset().filter(is_hidden=False, is_deleted=False)

class BaseModel(SoftDeleteModel):
    id= models.AutoField(primary_key=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name= _('Date created'))
    created_by = models.ForeignKey(User, null=True, editable=False, verbose_name= _('Created by'),
                                   related_name='%(app_label)s_%(class)s_created', on_delete=models.CASCADE)
    updated_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name= _('Date updated'))
    updated_by = models.ForeignKey(User, null=True, editable=False, verbose_name= _('Updated by'),
                                   related_name='%(app_label)s_%(class)s_updated', on_delete=models.CASCADE)
    is_hidden = models.BooleanField(default=False, verbose_name= _('Hidden'))
    
    objects = BaseManager()
    objects_all = models.Manager()

    class Meta:
        abstract=True

    def path(self):
        return f'/admin/{self._meta.app_label}/{self._meta.model_name}/{self.id}/'

    def delete(self, request=None, *args, **kwargs):
        super(BaseModel, self).delete(*args, **kwargs)

    def save(self, request= None, *args, **kwargs):
        if request:
            if not self.pk:
                self.created_by = request.user
            self.updated_by = request.user
        super(BaseModel, self).save(*args, **kwargs)

############################################
# Notification
############################################

class Notification(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_read = models.BooleanField(default=False, verbose_name=_("Read"))
    flag = models.CharField(max_length=25, choices=[("info", "info"), 
                                                    ("success", "success"), 
                                                    ("warning", "warning"), 
                                                    ("danger", "danger")])
    action = models.CharField(max_length=25, null=True, blank=True, choices=[("update", "update"),
                                                                             ("create", "create"),
                                                                             ('restore', 'restore'),
                                                                             ("delete", "delete")])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")

    def __str__(self):
        return f"[{self.flag}] {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

    def mark_as_unread(self):
        self.is_read = False
        self.save()

    def mark_as_read_all(self):
        self.objects.update(is_read=True)

    def mark_as_unread_all(self):
        self.objects.update(is_read=False)


############################################
# Image Model
############################################

from django.utils.html import format_html
from PIL import Image as PILImage
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from PIL import ExifTags

def handle_orientation(pilimage):
    img= pilimage
    # Xử lý EXIF Orientation nếu có
    try:
        # Lấy metadata EXIF
        exif = img._getexif()
        if exif:
            # Lấy thông tin về Orientation
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif_orientation = exif.get(orientation)

            # Điều chỉnh ảnh theo Orientation
            if exif_orientation == 3:
                img = img.rotate(180, expand=True)
            elif exif_orientation == 6:
                img = img.rotate(270, expand=True)
            elif exif_orientation == 8:
                img = img.rotate(90, expand=True)

    except AttributeError:
        # Nếu ảnh không có EXIF, bỏ qua
        pass
    return img

def save_pilimage_to_imagefield(pilimage, field, quality=100, max_size= None, new_name= None):
    img= pilimage

    img= handle_orientation(img)

    if max_size is not None:
        # max size cho mỗi chiều, giữ nguyên tỷ lệ
        h= img.height
        w= img.width
        if h > w:
            max_h= max_size[1] if h > max_size[1] else h
            max_w= int(max_h / h * w)
        else:
            max_w= max_size[0] if w > max_size[0] else w
            max_h= int(max_w / w * h)
        max_size= (max_w, max_h)
        img= img.resize(max_size, PILImage.LANCZOS)
    if img.mode != 'RGB':
        img= img.convert('RGB')

    if new_name is None:
        filename= field.name.split('/')[-1]
    else:
        filename= new_name

    tempfile= img
    tempfile_io= BytesIO()
    tempfile.save(tempfile_io, format='PNG', quality=quality)
    image_file= InMemoryUploadedFile(tempfile_io, None, filename, 'image/png', tempfile_io.tell(), None)
    field.save(filename, image_file)


MAX_SIZE= (1280, 1280)
THUMBNAIL_SIZE= (256, 256)
import os
class Image(BaseModel):
    image = models.ImageField(upload_to='images', verbose_name= _('Image'))
    thumbnail = models.ImageField(upload_to='images', verbose_name= _('Thumbnail'),
                                  blank=True, null=True)
    preview = models.ImageField(upload_to='images', verbose_name= _('Preview'),
                                blank=True, null=True)
    description = models.TextField(blank=True, null=True, verbose_name= _('Description'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('System image')
        verbose_name_plural = _('System images')

    def __str__(self):
        return self.image.name
    
    # kiểm tra bị mất ảnh
    def lost_data(self):
        return os.path.isfile(self.image.path) == False
    
    def getImage(self):
        if hasattr(self, 'img'):
            return self.img
        img= handle_orientation(PILImage.open(self.image))
        self.img= img
        return img
    
    def width(self):
        return self.getImage().width
    
    def height(self):
        return self.getImage().height
    
    def getImgThumbnailUrl(self):
        fl= True
        try:
            self.thumbnail.url
        except:
            # Nếu không có ảnh thumbnail thì lấy ảnh preview giảm kích thước để làm thumbnail
            fl= False
        try:
            img= PILImage.open(self.thumbnail)
        except:
            fl= False
        if not fl:
            try:
                img= PILImage.open(self.image)
            except:
                return None
            save_pilimage_to_imagefield(img, self.thumbnail, max_size=THUMBNAIL_SIZE, new_name= self.image.name.split('/')[-1][:-4] + '_thumbnail.jpg')
        return self.thumbnail.url
    
    def getImgPreviewUrl(self):
        fl= True
        try:
            self.preview.url
        except:
            fl= False
        try:
            img= PILImage.open(self.preview)
        except:
            fl= False

        if not fl:
            # Nếu không có ảnh preview thì giảm kích thước ảnh gốc để làm preview
            try:
                img= PILImage.open(self.image)
            except:
                return None
            save_pilimage_to_imagefield(img, self.preview, max_size=MAX_SIZE, new_name= self.image.name.split('/')[-1][:-4] + '_preview.jpg')
        return self.preview.url

    def imgThumbnail(self):
        r= self.getImgThumbnailUrl()
        if r is None or self.image is None:
            mes= _('Image not found')
            return format_html(f'<p>{mes}</p>')
        return format_html('<img src="{}" width="100" height="100" style="width: 100px; height: 100px; object-fit: cover;"/>', r)
    imgThumbnail.short_description = _('Thumbnail')

    def imgPreview(self):
        r= self.getImgPreviewUrl()
        img_url= self.image.url
        if r is None or self.image is None:
            mes= _('Image not found')
            return format_html(f'<p>{mes}</p>')
        mes= _('View original image size')
        return format_html(f"""<a href="{img_url}" target="_blank"><img src="{r}" width="512"/>
                            <br><small>{mes}</small>
                           </a>""")
    imgPreview.short_description = _('Preview')

    def url(self):
        return self.getImgPreviewUrl()
    
    def innerHTML(self):
        if self.image is None:
            return ''
        url= self.getImgPreviewUrl()
        html= f"""
<div class="cd-banner-area pb-20">
    <div class="container">
        <div class="row">
            <div class="col-12">
                <div class="cd-banner-img">
                    <img src="{url}" alt="">
                </div>
            </div>
        </div>
    </div>
</div>
""" 
        return html
    
    def hard_delete(self, *args, **kwargs):
        if self.image:
            try:
                self.image.delete(save= False) # Xóa file ảnh khi xóa object
            except Exception as e:
                print(f'Error when delete image: {e}')
        if self.thumbnail:
            try:
                self.thumbnail.delete(save= False) # Xóa file thumbnail khi xóa object
            except Exception as e:
                print(f'Error when delete thumbnail: {e}')
        if self.preview:
            try:
                self.preview.delete(save= False)
            except Exception as e:
                print(f'Error when delete preview: {e}')
        super(Image, self).hard_delete(*args, **kwargs)


    def save(self, *args, **kwargs):

        # Nếu preview thay đổi thì cập nhật thumbnail
        try:
            old= Image.objects.get(id= self.id) if self.id else None
        except:
            old= None
        if old and not old.image is None and not self.image is None and old.image != self.image:
            old.image.delete(save= False) # Xóa file ảnh cũ
            old.thumbnail.delete(save= False)
            old.preview.delete(save= False)

            self.thumbnail= None
            self.preview= None

        super(Image, self).save(*args, **kwargs)

    def set_image_from_pilimage(self, pilimage, fname= None):
        save_pilimage_to_imagefield(pilimage, self.image, max_size=MAX_SIZE, new_name= fname)
        self.save()

############################################
# Mail
############################################

from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import BadHeaderError
import smtplib
import ssl

class Mail(BaseModel):
    subject = models.CharField(max_length=255, verbose_name= _('Subject'))
    content = models.TextField(verbose_name= _('Content'))
    receiver = models.EmailField(verbose_name= _('Receiver'))
    status = models.CharField(max_length=25, choices= [('pending', _('Pending')),
                                                       ('sent', _('Sent')),
                                                       ('failed', _('Failed'))], 
                                                       default='pending', verbose_name= _('Status'))
    note = models.TextField(blank=True, null=True, verbose_name= _('Note'))

    class Meta:
        db_table = 'mail'
        verbose_name = _('Email notification')
        verbose_name_plural = _('Email notifications')

    def __str__(self):
        return self.subject
    
    def save(self, *args, **kwargs):
        super(Mail, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super(Mail, self).delete(*args, **kwargs)

    def send(self):
        if not self.receiver:
            self.status = 'failed'
            self.note = 'No receiver'
            self.save()
            return
        try:
            context = ssl._create_unverified_context()
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                send_mail(
                    self.subject,
                    self.content,
                    settings.EMAIL_HOST_USER,
                    [self.receiver],
                    html_message= self.content,
                    fail_silently=False,
                )
            print("Email sent successfully")
            self.status = 'sent'
            self.note = "Email sent successfully"
        except BadHeaderError:
            print("Invalid header found.")
            self.note = "Invalid header found."
            self.status = 'failed'
        except smtplib.SMTPException as e:
            print(f"SMTP error occurred: {e}")
            self.note = f"SMTP error occurred: {e}"
            self.status = 'failed'
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.note = f"An unexpected error occurred: {e}"
            self.status = 'failed'
        self.save()

    def is_sent(self):
        return self.status == 'sent'