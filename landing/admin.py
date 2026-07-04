from django.contrib import admin

from .models import ContactSubmission, Review


# BUG FIX: ContactSubmission model pehle admin me register hi nahi tha,
# isliye Django admin panel (/admin/) me contact submissions kabhi dikhti
# hi nahi thi.
@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'submitted_at')
    list_filter = ('submitted_at',)
    search_fields = ('name', 'email', 'phone', 'message')
    readonly_fields = ('submitted_at',)
    ordering = ('-submitted_at',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('name',)