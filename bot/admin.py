from django.contrib import admin

# Register your models here.

from .models import UserProfile, BusStop, Reminder, DayKeyWord


class BusStopInline(admin.TabularInline):
    model = BusStop

class ReminderInline(admin.TabularInline):
    model = Reminder



class UserProfileAdmin(admin.ModelAdmin):
    inlines = [BusStopInline, ReminderInline]
    list_display = ('user_id', 'user_name')

class BusStopAdmin(admin.ModelAdmin):
    list_display = ('user', 'bus_route', 'stop_name')


class ReminderAdmin(admin.ModelAdmin):
    list_display = ('user', 'event')

class DayKeyWordAdmin(admin.ModelAdmin):
    list_display = ('keyword', )


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(BusStop, BusStopAdmin)
admin.site.register(Reminder, ReminderAdmin)
admin.site.register(DayKeyWord, DayKeyWordAdmin)
