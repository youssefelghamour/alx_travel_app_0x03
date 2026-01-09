from django.contrib import admin
from .models import Listing, Booking, Review
from django.contrib.auth.models import User

admin.site.register(Listing)
admin.site.register(Booking)
admin.site.register(Review)
