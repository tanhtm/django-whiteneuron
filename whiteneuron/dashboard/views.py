from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
import random
import json
from django.views.generic import RedirectView

class HomeView(RedirectView):
    pattern_name = "admin:index"


from whiteneuron.base.models import UserActivity
import datetime
# timezones
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDay
import numpy as np

def dashboard_callback(request, context):
    # messages.info(request, render_to_string("CCMS/service.html"))

    time= request.GET.get("time", "week")
    
    MAPTIME = {
        'today': 'today',
        '7days': '7 days',
        'week': 'week',
        'month': 'month',
        'year': 'year',
    }

    WEEKDAYS = [
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun",
    ]

    # Range of time
    if time == "today":
        start= datetime.date.today()
        end= datetime.date.today() + datetime.timedelta(days=1)
        start_last= start - datetime.timedelta(days=1)
        end_last= end - datetime.timedelta(days=1)
    elif time == "7days":
        start= datetime.date.today() - datetime.timedelta(days=7)
        end= datetime.date.today() + datetime.timedelta(days=1)
        start_last= start - datetime.timedelta(days=7)
        end_last= end - datetime.timedelta(days=7)
    elif time == "week":
        start= datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
        end= start + datetime.timedelta(days=7)
        start_last= start - datetime.timedelta(days=7)
        end_last= end - datetime.timedelta(days=7)
    elif time == "month":
        start= datetime.date.today().replace(day=1)
        end= start.replace(month=start.month+1)
        start_last= start.replace(month=start.month-1)
        end_last= end.replace(month=end.month-1)
    elif time == "year":
        start= datetime.date.today().replace(month=1, day=1)
        end= start.replace(year=start.year+1)
        start_last= start.replace(year=start.year-1)
        end_last= end.replace(year=end.year-1)
    else:
        ValueError("Invalid time")

    
    

    # convert to timezone
    start= timezone.make_aware(datetime.datetime.combine(start, datetime.datetime.min.time()))
    end= timezone.make_aware(datetime.datetime.combine(end, datetime.datetime.max.time()))
    start_last= timezone.make_aware(datetime.datetime.combine(start_last, datetime.datetime.min.time()))
    end_last= timezone.make_aware(datetime.datetime.combine(end_last, datetime.datetime.max.time()))


    # start_of_week = timezone.make_aware(datetime.datetime.combine(start_of_week, datetime.datetime.min.time()))
    # end_of_week = timezone.make_aware(datetime.datetime.combine(end_of_week, datetime.datetime.max.time()))
    # start_of_last_week = timezone.make_aware(datetime.datetime.combine(start_of_last_week, datetime.datetime.min.time()))
    # end_of_last_week = timezone.make_aware(datetime.datetime.combine(end_of_last_week, datetime.datetime.max.time()))

    # print(start_of_week, end_of_week)
    # print(start_of_last_week, end_of_last_week)

    # user_activities = UserActivity.objects.filter(timestamp__range=(start_of_week, end_of_week))
    # user_activities_last_week = UserActivity.objects.filter(timestamp__range=(start_of_last_week, end_of_last_week))

    user_activities = UserActivity.objects.filter(timestamp__range=(start, end))
    user_activities_last = UserActivity.objects.filter(timestamp__range=(start_last, end_last))

    # total_activities = user_activities.count()
    # total_activities_last_week = user_activities_last_week.count()

    total_activities = user_activities.count()
    total_activities_last = user_activities_last.count()

    # total_activities_success = user_activities.filter(status_code__lt="400").count()
    # total_activities_last_week_success = user_activities_last_week.filter(status_code="200").count()

    total_activities_success = user_activities.filter(status_code__lt="400").count()
    total_activities_last_success = user_activities_last.filter(status_code__lt="400").count()

    # total_activities_icd10 = user_activities.filter(path__startswith="/admin/icd10").count()
    # total_activities_last_week_icd10 = user_activities_last_week.filter(path__startswith="/admin/icd10").count()

    total_activities_icd10 = user_activities.filter(path__startswith="/admin/icd10").count()
    total_activities_last_icd10 = user_activities_last.filter(path__startswith="/admin/icd10").count()

    # top user TODO: top user
    top_user = user_activities.values("user").annotate(count=Count("id")).order_by("-count")[:5]
    top_user_last = user_activities_last.values("user").annotate(count=Count("id")).order_by("-count")[:5]

    # chart data 28 days for activities success, error
    user_activities_28_days = UserActivity.objects.filter(timestamp__gte=timezone.now()-datetime.timedelta(days=28))
    user_activities_28_days_success = user_activities_28_days.filter(status_code__lt="400").annotate(day= TruncDay("timestamp")).values("day").annotate(count=Count("id")).values("day", "count")
    user_activities_28_days_error = user_activities_28_days.exclude(status_code__lt="400").annotate(day=TruncDay("timestamp")).values("day").annotate(count=Count("id")).values("day", "count") 
    # convert data to fit day of week
    # print(user_activities_28_days_success)
    user_activities_28_days_success = {item["day"].strftime("%Y-%m-%d"): item["count"] for item in user_activities_28_days_success}
    user_activities_28_days_error = {item["day"].strftime("%Y-%m-%d"): item["count"] for item in user_activities_28_days_error}
    # Update data 0 for missing day
    # print(user_activities_28_days_success)
    user_activities_28_days= {
        'success': [],
        'error': []
    }
    for day in range(28): # 28 days
        day = (timezone.now() - datetime.timedelta(days=day)).strftime("%Y-%m-%d")
        user_activities_28_days['success'].append(user_activities_28_days_success.get(day, 0))  
        user_activities_28_days['error'].append(user_activities_28_days_error.get(day, 0))
    
    # Lấy thứ của ngày hiện tại
    last_day = datetime.datetime.now().weekday() 
    # Thứ của 28 ngày trước tính từ ngày hiện tại
    _28_days= [WEEKDAYS[(last_day - i) % 7] for i in range(28)][::-1]
    user_activities_28_days['success'].reverse()
    user_activities_28_days['error'].reverse()
    user_activities_28_days['average'] = ((np.array(user_activities_28_days['success']) + np.array(user_activities_28_days['error'])) / 2).tolist()

    def render_kpi(label, object_name, value, last_value, time):
        is_increase = value > last_value
        diff = value - last_value
        diff_percent = diff / last_value * 100 if last_value else 0
        footer = f'<strong class="text-{"green" if is_increase else "red"}-600 font-medium">{"+" if is_increase else "-"}{abs(diff)} ({diff_percent:.2f}%)</strong>&nbsp;progress from last {MAPTIME[time] if time != "today" else "day"}'
        return {
            "label": label,
            "title": f"{object_name} in this {MAPTIME[time]}",
            "metric": value,
            "footer": mark_safe(footer),
        }


    positive = [[1, random.randrange(8, 28)] for i in range(1, 28)]
    negative = [[-1, -random.randrange(8, 28)] for i in range(1, 28)]
    average = [r[1] - random.randint(3, 5) for r in positive]
    performance_positive = [[1, random.randrange(8, 28)] for i in range(1, 28)]
    performance_negative = [[-1, -random.randrange(8, 28)] for i in range(1, 28)]

    context.update(
        {
            "navigation": [
                {"title": _("Dashboard"), "link": "", "active": True},
                {"title": _("Analytics"), "link": "analytics"},
                {"title": _("Settings"), "link": "settings"},
            ],
            "filters": [
                {
                    "title": _("Today"),
                    "link": "?time=today",
                    "active": False if time != "today" else True,
                },
                {
                    "title": _("7 days"),
                    "link": "?time=7days",
                    "active": False if time != "7days" else True,
                },
                {
                    "title": _("Week"), 
                    "link": "?time=week",
                    "active": False if time != "week" else True,
            },
                {
                    "title": _("Month"),
                    "link": "?time=month",
                    "active": False if time != "month" else True,
                },
                {
                    "title": _("Year"),
                    "link": "?time=year",
                    "active": False if time != "year" else True,
                },
            ],
            "kpi": [
                render_kpi("Activity", "Activities", total_activities, total_activities_last, time),
                render_kpi("Activity", "Success activities", total_activities_success, total_activities_last_success, time),
                # render_kpi("Activity", "ICD-10 activities", total_activities_icd10, total_activities_last_icd10, time),
                # {
                #     "title": "Product A Performance",
                #     "metric": "$1,234.56",
                #     "footer": mark_safe(
                #         '<strong class="text-green-600 font-medium">+3.14%</strong>&nbsp;progress from last week'
                #     ),
                #     "chart": json.dumps(
                #         {
                #             "labels": [WEEKDAYS[day % 7] for day in range(1, 28)],
                #             "datasets": [{"data": average, "borderColor": "#9333ea"}],
                #         }
                #     ),
                # },
            ],
            "progress": [
                {
                    "title": "Social marketing e-book",
                    "description": " $1,234.56",
                    "value": random.randint(10, 90),
                },
                {
                    "title": "Freelancing tasks",
                    "description": " $1,234.56",
                    "value": random.randint(10, 90),
                },
                {
                    "title": "Development coaching",
                    "description": " $1,234.56",
                    "value": random.randint(10, 90),
                },
                {
                    "title": "Product consulting",
                    "description": " $1,234.56",
                    "value": random.randint(10, 90),
                },
                {
                    "title": "Other income",
                    "description": " $1,234.56",
                    "value": random.randint(10, 90),
                },
            ],
            "chart": json.dumps(
                {
                    "labels": _28_days,
                    "datasets": [
                        {
                            "label": "Example 1",
                            "type": "line",
                            "data": user_activities_28_days['average'],
                            "backgroundColor": "#f0abfc",
                            "borderColor": "#f0abfc",
                        },
                        {
                            "label": "Success",
                            "data": user_activities_28_days['success'],
                            "backgroundColor": "#9333ea",
                        },
                        {
                            "label": "Error",
                            "data": user_activities_28_days['error'],
                            "backgroundColor": "#f43f5e",
                        },
                    ],
                }
            ),
            "performance": [
                {
                    "title": _("Last week revenue"),
                    "metric": "$1,234.56",
                    "footer": mark_safe(
                        '<strong class="text-green-600 font-medium">+3.14%</strong>&nbsp;progress from last week'
                    ),
                    "chart": json.dumps(
                        {
                            "labels": [WEEKDAYS[day % 7] for day in range(1, 28)],
                            "datasets": [
                                {"data": performance_positive, "borderColor": "#9333ea"}
                            ],
                        }
                    ),
                },
                {
                    "title": _("Last week expenses"),
                    "metric": "$1,234.56",
                    "footer": mark_safe(
                        '<strong class="text-green-600 font-medium">+3.14%</strong>&nbsp;progress from last week'
                    ),
                    "chart": json.dumps(
                        {
                            "labels": [WEEKDAYS[day % 7] for day in range(1, 28)],
                            "datasets": [
                                {"data": performance_negative, "borderColor": "#f43f5e"}
                            ],
                        }
                    ),
                },
            ],
        },
    )

    return context