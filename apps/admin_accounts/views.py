"""관리자 로그인·토큰·CRUD API."""
from __future__ import annotations

from datetime import datetime, timezone as dt_timezone

import jwt
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_accounts.authentication import AdminJWTAuthentication
from apps.admin_accounts.cookies import attach_admin_refresh_cookie, clear_admin_refresh_cookie
from apps.admin_accounts.jwt_utils import create_admin_member_jwt_tokens
from apps.admin_accounts.models import AdminMemberShip
from apps.admin_accounts.serializers import (
    AdminLoginSerializer,
    AdminRegisterSerializer,
    AdminUpdateSerializer,
)


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _user_payload(admin: AdminMemberShip) -> dict:
    return {
        "memberShipSid": str(admin.memberShipSid),
        "memberShipId": admin.memberShipId,
        "memberShipName": admin.memberShipName,
        "memberShipEmail": admin.memberShipEmail,
        "memberShipPhone": admin.memberShipPhone or "",
        "memberShipLevel": admin.memberShipLevel,
        "is_admin": admin.is_admin,
        "last_login": admin.last_login.strftime("%Y-%m-%d %H:%M:%S") if admin.last_login else None,
        "login_count": admin.login_count,
    }


def _admin_from_refresh_string(refresh_token_str: str):
    """Returns (user, error_response)."""
    try:
        payload = jwt.decode(
            refresh_token_str,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        return None, Response({"error": "리프레시 토큰이 만료되었습니다."}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return None, Response({"error": "유효하지 않은 리프레시 토큰입니다."}, status=status.HTTP_401_UNAUTHORIZED)

    if payload.get("token_type") != "refresh" or payload.get("site") != "admin_api":
        return None, Response({"error": "잘못된 리프레시 토큰입니다."}, status=status.HTTP_401_UNAUTHORIZED)

    uid = payload.get("user_id")
    if not uid:
        return None, Response({"error": "토큰에 사용자 ID가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user = AdminMemberShip.objects.get(memberShipSid=uid, is_active=True)
    except AdminMemberShip.DoesNotExist:
        return None, Response({"error": "사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    refresh_iat = payload.get("iat")
    if refresh_iat is not None and user.token_issued_at is not None:
        refresh_dt = datetime.fromtimestamp(int(refresh_iat), tz=dt_timezone.utc)
        if refresh_dt < user.token_issued_at:
            return None, Response({"error": "토큰이 무효화되었습니다."}, status=status.HTTP_401_UNAUTHORIZED)

    return user, None


def _require_settings_admin(user) -> Response | None:
    if not isinstance(user, AdminMemberShip) or not user.is_admin:
        return Response({"error": "설정관리 권한이 필요합니다."}, status=status.HTTP_403_FORBIDDEN)
    return None


@method_decorator(csrf_exempt, name="dispatch")
class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = AdminLoginSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"error": "입력값이 올바르지 않습니다.", "details": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        mid = ser.validated_data["memberShipId"]
        password = ser.validated_data["password"]

        try:
            admin = AdminMemberShip.objects.get(memberShipId=mid, is_active=True)
        except AdminMemberShip.DoesNotExist:
            return Response({"error": "회원 ID 또는 비밀번호가 올바르지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        if not admin.memberShipPassword or not admin.check_password(password):
            return Response({"error": "회원 ID 또는 비밀번호가 올바르지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        admin.last_login = timezone.now()
        admin.login_count += 1
        admin.save(update_fields=["last_login", "login_count"])

        tokens = create_admin_member_jwt_tokens(admin)
        body = {
            "access_token": tokens["access_token"],
            "expires_in": tokens["expires_in"],
            "user": _user_payload(admin),
        }
        resp = Response(body, status=status.HTTP_200_OK)
        attach_admin_refresh_cookie(resp, request, tokens["refresh_token"])
        return resp


@method_decorator(csrf_exempt, name="dispatch")
class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cookie_name = getattr(settings, "ADMIN_JWT_REFRESH_COOKIE_NAME", "adminRefreshToken")
        refresh_str = (request.COOKIES.get(cookie_name) or "").strip()
        data = request.data if isinstance(request.data, dict) else {}
        refresh_str = refresh_str or (data.get("refresh_token") or "").strip()

        if not refresh_str:
            return Response({"error": "리프레시 토큰이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        user, err = _admin_from_refresh_string(refresh_str)
        if err:
            return err

        tokens = create_admin_member_jwt_tokens(user)
        body = {
            "access_token": tokens["access_token"],
            "expires_in": tokens["expires_in"],
            "user": _user_payload(user),
        }
        resp = Response(body, status=status.HTTP_200_OK)
        attach_admin_refresh_cookie(resp, request, tokens["refresh_token"])
        return resp


@method_decorator(csrf_exempt, name="dispatch")
class AdminLogoutView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if isinstance(user, AdminMemberShip):
            user.token_issued_at = timezone.now()
            user.save(update_fields=["token_issued_at"])
        resp = Response({"message": "로그아웃되었습니다."}, status=status.HTTP_200_OK)
        clear_admin_refresh_cookie(resp, request)
        return resp


@method_decorator(csrf_exempt, name="dispatch")
class AdminListView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        err = _require_settings_admin(request.user)
        if err:
            return err

        q = request.query_params.get("search", "").strip()
        status_filter = request.query_params.get("status", "").strip()

        qs = AdminMemberShip.objects.all().order_by("-created_at")
        if status_filter == "active":
            qs = qs.filter(is_active=True)
        elif status_filter == "inactive":
            qs = qs.filter(is_active=False)

        if q:
            qs = qs.filter(
                Q(memberShipId__icontains=q)
                | Q(memberShipName__icontains=q)
                | Q(memberShipEmail__icontains=q)
            )

        admins = []
        for a in qs:
            admins.append(
                {
                    "memberShipSid": str(a.memberShipSid),
                    "memberShipId": a.memberShipId,
                    "memberShipName": a.memberShipName,
                    "memberShipEmail": a.memberShipEmail,
                    "memberShipPhone": a.memberShipPhone or "",
                    "memberShipLevel": a.memberShipLevel,
                    "is_admin": a.is_admin,
                    "is_active": a.is_active,
                    "last_login": a.last_login.strftime("%Y-%m-%d %H:%M:%S") if a.last_login else None,
                    "login_count": a.login_count,
                    "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": a.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        return Response({"admins": admins, "total": len(admins)}, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class AdminRegisterView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        err = _require_settings_admin(request.user)
        if err:
            return err

        ser = AdminRegisterSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"error": "입력값이 올바르지 않습니다.", "details": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data.copy()
        d.pop("password_confirm")
        pwd = d.pop("password")
        d["memberShipPassword"] = make_password(pwd)
        admin = AdminMemberShip.objects.create(**d)
        return Response({"message": "관리자가 등록되었습니다.", "user": _user_payload(admin)}, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class AdminUpdateView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        err = _require_settings_admin(request.user)
        if err:
            return err

        ser = AdminUpdateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"error": "입력값이 올바르지 않습니다.", "details": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        sid = ser.validated_data["memberShipSid"]
        try:
            admin = AdminMemberShip.objects.get(memberShipSid=sid)
        except AdminMemberShip.DoesNotExist:
            return Response({"error": "관리자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        for field in ("memberShipName", "memberShipEmail", "memberShipPhone", "memberShipLevel", "is_admin", "is_active"):
            if field in ser.validated_data and ser.validated_data[field] is not None:
                setattr(admin, field, ser.validated_data[field])

        pwd = ser.validated_data.get("password")
        if pwd:
            admin.memberShipPassword = make_password(pwd)
            admin.token_issued_at = timezone.now()

        admin.save()
        return Response({"message": "수정되었습니다.", "user": _user_payload(admin)}, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class AdminDeactivateView(APIView):
    """비활성화(소프트 삭제). 본인 계정은 비활성화 불가."""

    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        err = _require_settings_admin(request.user)
        if err:
            return err

        sid = (request.data.get("memberShipSid") or "").strip()
        if not sid:
            return Response({"error": "memberShipSid가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        if str(request.user.memberShipSid) == sid:
            return Response({"error": "본인 계정은 비활성화할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            admin = AdminMemberShip.objects.get(memberShipSid=sid)
        except AdminMemberShip.DoesNotExist:
            return Response({"error": "관리자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        admin.is_active = False
        admin.token_issued_at = timezone.now()
        admin.save(update_fields=["is_active", "token_issued_at", "updated_at"])
        return Response({"message": "비활성화되었습니다."}, status=status.HTTP_200_OK)
