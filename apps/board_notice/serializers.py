from rest_framework import serializers

from .models import BoardNotice


class BoardNoticeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardNotice
        fields = ("id", "title", "subtitle", "is_pinned", "view_count", "created_at")


class BoardNoticeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardNotice
        fields = ("id", "title", "subtitle", "content", "is_pinned", "view_count", "created_at")


class BoardNoticeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardNotice
        fields = ("title", "subtitle", "content", "is_pinned")
