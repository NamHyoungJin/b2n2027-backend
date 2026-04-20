from rest_framework import serializers

from .models import HomepageDocInfo


class HomepageDocReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomepageDocInfo
        fields = ("doc_type", "title", "body_html", "is_published", "updated_at")


class HomepageDocAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomepageDocInfo
        fields = ("title", "body_html", "is_published")

    def validate_title(self, value):
        if value is None:
            return None
        s = value.strip()
        return s or None
