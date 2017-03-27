from django.db import models

# Create your models here.

class UserProfile(models.Model):
    user_id = models.CharField(max_length=100, unique=True)
    user_name = models.CharField(max_length=20, blank=True)
    latitude = models.CharField(max_length=50, blank=True)
    longitude = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, blank=True)
    air_pollution = models.CharField(max_length=20, blank=True)
    wake_up_time = models.CharField(max_length=50, blank=True)
    sleep_time = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return str(self.user_id + self.user_name)


class BusStop(models.Model):
    user = models.ForeignKey(UserProfile)
    bus_route = models.CharField(max_length=50)
    stop_name = models.CharField(max_length=50)

    def __str__(self):
        return str(self.user + self.bus_route + self.stop_name)

class Reminder(models.Model):
    user = models.ForeignKey(UserProfile)
    event = models.CharField(max_length=150)
    time = models.DateTimeField()

    def __str__(self):
        return str(self.user + self.name + self.time)

class DayKeyWord(models.Model):
    keyword = models.CharField(max_length=150)

    def __str__(self):
        return self.keyword
