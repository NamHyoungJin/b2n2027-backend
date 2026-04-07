from rest_framework import serializers

from apps.admin_accounts.models import AdminMemberShip


class AdminLoginSerializer(serializers.Serializer):
    memberShipId = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=128, write_only=True)


class AdminRegisterSerializer(serializers.Serializer):
    memberShipId = serializers.CharField(max_length=50)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    password_confirm = serializers.CharField(max_length=128, write_only=True)
    memberShipName = serializers.CharField(max_length=100)
    memberShipEmail = serializers.EmailField()
    memberShipPhone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    memberShipLevel = serializers.IntegerField(default=1, min_value=1)
    is_admin = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "비밀번호가 일치하지 않습니다."})
        if AdminMemberShip.objects.filter(memberShipId=attrs["memberShipId"]).exists():
            raise serializers.ValidationError({"memberShipId": "이미 사용 중인 ID입니다."})
        if AdminMemberShip.objects.filter(memberShipEmail=attrs["memberShipEmail"]).exists():
            raise serializers.ValidationError({"memberShipEmail": "이미 사용 중인 이메일입니다."})
        return attrs


class AdminUpdateSerializer(serializers.Serializer):
    memberShipSid = serializers.CharField(max_length=32)
    memberShipName = serializers.CharField(max_length=100, required=False)
    memberShipEmail = serializers.EmailField(required=False)
    memberShipPhone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    memberShipLevel = serializers.IntegerField(required=False, min_value=1)
    is_admin = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    password = serializers.CharField(min_length=8, max_length=128, required=False, allow_blank=True, write_only=True)

    def validate_memberShipSid(self, value):
        if not AdminMemberShip.objects.filter(memberShipSid=value).exists():
            raise serializers.ValidationError("존재하지 않는 관리자입니다.")
        return value

    def validate(self, attrs):
        sid = attrs.get("memberShipSid")
        email = attrs.get("memberShipEmail")
        if email and sid:
            qs = AdminMemberShip.objects.filter(memberShipEmail=email).exclude(memberShipSid=sid)
            if qs.exists():
                raise serializers.ValidationError({"memberShipEmail": "이미 사용 중인 이메일입니다."})
        return attrs
