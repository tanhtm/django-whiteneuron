"""
Notification API — thông báo của user đang đăng nhập.

Endpoints (mount dưới ``api/notifications/``):

    GET  ""                  Danh sách thông báo (phân trang).
                             Query: page, page_size (≤ 100), unread=1, flag=<info|success|...>
    GET  unread-count/       Số thông báo chưa đọc — nhẹ, dùng cho badge / polling.
    GET  <id>/               Chi tiết một thông báo (kèm changed_data).
    POST <id>/read/          Đánh dấu đã đọc.
    POST <id>/unread/        Đánh dấu chưa đọc.
    POST read-all/           Đánh dấu tất cả đã đọc.

Mọi endpoint yêu cầu đăng nhập (session) và chỉ thấy thông báo của chính user.
POST cần CSRF token (header ``X-CSRFToken``) như các form Django khác.
"""

from __future__ import annotations

from django.core.paginator import EmptyPage, Paginator
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .models import Notification

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
FLAGS = {choice for choice, _ in Notification._meta.get_field("flag").choices}


def _json(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={"ensure_ascii": False})


def _login_required(view):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _json({"detail": "Authentication required."}, status=401)
        return view(request, *args, **kwargs)

    wrapper.__name__ = view.__name__
    wrapper.__doc__ = view.__doc__
    return wrapper


def _int_param(request, name, default, minimum=1, maximum=None):
    try:
        value = int(request.GET.get(name, default))
    except (TypeError, ValueError):
        value = default
    value = max(value, minimum)
    if maximum is not None:
        value = min(value, maximum)
    return value


def _user_qs(request):
    return Notification.objects.filter(user=request.user)


def serialize(n: Notification, detail: bool = False) -> dict:
    data = {
        "id": n.pk,
        "title": n.title,
        "content": n.content,
        "flag": n.flag,
        "action": n.action,
        "obj_link": n.obj_link,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
        "action_by": n.action_by.get_username() if n.action_by_id else None,
    }
    if detail:
        data["changed_data"] = n.changed_data
    return data


def _get_own(request, pk):
    return _user_qs(request).select_related("action_by").filter(pk=pk).first()


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@never_cache
@require_GET
@_login_required
def notification_list(request):
    qs = _user_qs(request).select_related("action_by").order_by("-created_at", "-pk")

    if request.GET.get("unread", "").lower() in ("1", "true", "yes"):
        qs = qs.filter(is_read=False)
    flag = request.GET.get("flag")
    if flag:
        if flag not in FLAGS:
            return _json({"detail": f"Invalid flag. Allowed: {sorted(FLAGS)}"}, status=400)
        qs = qs.filter(flag=flag)

    page_size = _int_param(request, "page_size", DEFAULT_PAGE_SIZE, maximum=MAX_PAGE_SIZE)
    page_number = _int_param(request, "page", 1)
    paginator = Paginator(qs, page_size)
    try:
        page = paginator.page(page_number)
        items = [serialize(n) for n in page.object_list]
    except EmptyPage:
        items = []

    return _json({
        "count": paginator.count,
        "page": page_number,
        "page_size": page_size,
        "num_pages": paginator.num_pages,
        "unread_count": _user_qs(request).filter(is_read=False).count(),
        "results": items,
    })


@never_cache
@require_GET
@_login_required
def unread_count(request):
    return _json({"unread_count": _user_qs(request).filter(is_read=False).count()})


@never_cache
@require_GET
@_login_required
def notification_detail(request, pk):
    n = _get_own(request, pk)
    if n is None:
        return _json({"detail": "Not found."}, status=404)
    return _json(serialize(n, detail=True))


def _set_read(request, pk, value: bool):
    updated = _user_qs(request).filter(pk=pk).update(is_read=value)
    if not updated:
        return _json({"detail": "Not found."}, status=404)
    return _json({
        "id": pk,
        "is_read": value,
        "unread_count": _user_qs(request).filter(is_read=False).count(),
    })


@require_POST
@_login_required
def mark_read(request, pk):
    return _set_read(request, pk, True)


@require_POST
@_login_required
def mark_unread(request, pk):
    return _set_read(request, pk, False)


@require_POST
@_login_required
def mark_all_read(request):
    updated = _user_qs(request).filter(is_read=False).update(is_read=True)
    return _json({"updated": updated, "unread_count": 0})
