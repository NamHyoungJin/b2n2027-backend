from django.contrib import admin
from .models import Participant


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    """참여자 관리자 페이지"""
    
    list_display = [
        'name', 'email', 'phone', 'status',
        'register_type', 'payment_method', 'has_passport_copy', 'created_at'
    ]
    list_filter = ['status', 'register_type', 'payment_method', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['uuid', 'qr_image', 'created_at', 'updated_at']

    @admin.display(description='여권사본', boolean=True)
    def has_passport_copy(self, obj):
        return bool(obj.passport_copy)

    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'phone', 'email')
        }),
        ('여권', {
            'fields': ('passport_copy',),
        }),
        ('행사 정보', {
            'fields': ('church_role', 'age_group', 'gender')
        }),
        ('등록/결제 정보', {
            'fields': ('register_type', 'payment_method', 'status')
        }),
        ('시스템 정보', {
            'fields': ('uuid', 'qr_image', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
