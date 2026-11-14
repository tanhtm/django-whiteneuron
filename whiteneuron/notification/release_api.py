"""
Release note API — "Có gì mới" cho user đang đăng nhập.

Endpoints (mount dưới ``api/release-notes/``):

    GET  ""            Danh sách release note đã publish (phân trang: page, page_size ≤ 100).
    GET  latest/       Release note mới nhất (``null`` nếu chưa có).
    GET  unseen/       Các release note user chưa xem — dùng để hiện popup "Có gì mới".
    GET  <id>/         Chi tiết.
    POST <id>/seen/    Đánh dấu đã xem.
    POST seen-all/     Đánh dấu đã xem tất cả.

Mỗi item có ``content`` (markdown gốc), ``content_html`` (đã render) và ``is_seen``.
"""

from __future__ import annotations

import markdown
from django.core.paginator import EmptyPage, Paginator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .api import _int_param, _json, _login_required, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from .models import ReleaseNote, ReleaseNoteView


def _seen_ids(user, notes) -> set[int]:
    ids = [n.pk for n in notes]
    if not ids:
        return set()
    return set(
        ReleaseNoteView.objects.filter(user=user, release_note_id__in=ids)
        .values_list("release_note_id", flat=True)
    )


def serialize(note: ReleaseNote, seen: bool) -> dict:
    return {
        "id": note.pk,
        "version": note.version,
        "title": note.title,
        "content": note.content,
        "content_html": markdown.markdown(note.content or "", extensions=["extra"]),
        "published_at": note.published_at.isoformat(),
        "is_seen": seen,
    }


def _serialize_many(user, notes) -> list[dict]:
    notes = list(notes)
    seen = _seen_ids(user, notes)
    return [serialize(n, n.pk in seen) for n in notes]


def _mark_seen(user, notes) -> int:
    notes = list(notes)
    already = _seen_ids(user, notes)
    new = [ReleaseNoteView(release_note=n, user=user) for n in notes if n.pk not in already]
    ReleaseNoteView.objects.bulk_create(new, ignore_conflicts=True)
    return len(new)


@never_cache
@require_GET
@_login_required
def release_note_list(request):
    qs = ReleaseNote.objects.visible()
    page_size = _int_param(request, "page_size", DEFAULT_PAGE_SIZE, maximum=MAX_PAGE_SIZE)
    page_number = _int_param(request, "page", 1)
    paginator = Paginator(qs, page_size)
    try:
        items = _serialize_many(request.user, paginator.page(page_number).object_list)
    except EmptyPage:
        items = []
    return _json({
        "count": paginator.count,
        "page": page_number,
        "page_size": page_size,
        "num_pages": paginator.num_pages,
        "unseen_count": ReleaseNote.objects.unseen_by(request.user).count(),
        "results": items,
    })


@never_cache
@require_GET
@_login_required
def release_note_latest(request):
    note = ReleaseNote.objects.visible().first()
    return _json({"result": _serialize_many(request.user, [note])[0] if note else None})


@never_cache
@require_GET
@_login_required
def release_note_unseen(request):
    notes = ReleaseNote.objects.unseen_by(request.user)[:MAX_PAGE_SIZE]
    return _json({"results": [serialize(n, False) for n in notes]})


@never_cache
@require_GET
@_login_required
def release_note_detail(request, pk):
    note = ReleaseNote.objects.visible().filter(pk=pk).first()
    if note is None:
        return _json({"detail": "Not found."}, status=404)
    return _json(_serialize_many(request.user, [note])[0])


@require_POST
@_login_required
def release_note_seen(request, pk):
    note = ReleaseNote.objects.visible().filter(pk=pk).first()
    if note is None:
        return _json({"detail": "Not found."}, status=404)
    _mark_seen(request.user, [note])
    return _json({"id": pk, "is_seen": True,
                  "unseen_count": ReleaseNote.objects.unseen_by(request.user).count()})


@require_POST
@_login_required
def release_note_seen_all(request):
    updated = _mark_seen(request.user, ReleaseNote.objects.unseen_by(request.user))
    return _json({"updated": updated, "unseen_count": 0})
