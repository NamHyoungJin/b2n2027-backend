"""b2n2027ApiResponse 래퍼 — PlanDoc/apiResponseRules.md."""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.response import Response

from apps.core.error_codes import ErrorCode

B2N_KEY = "b2n2027ApiResponse"


def is_b2n_wrapped(data: Any) -> bool:
    return isinstance(data, dict) and B2N_KEY in data and isinstance(data[B2N_KEY], dict)


def api_response(
    code: str,
    message: str,
    result: Any = None,
    *,
    http_status: int | None = None,
) -> Response:
    """표준 봉투로 Response 생성. result는 성공 시 페이로드, 실패 시 None."""
    st = http_status if http_status is not None else (
        status.HTTP_200_OK if code == ErrorCode.SUCCESS else status.HTTP_400_BAD_REQUEST
    )
    return Response(
        {B2N_KEY: {"ErrorCode": code, "Message": message, "Result": result}},
        status=st,
    )


def wrap_success_payload(result: Any, message: str = "정상 처리되었습니다.") -> dict:
    return {B2N_KEY: {"ErrorCode": ErrorCode.SUCCESS, "Message": message, "Result": result}}


def _http_status_to_error_code(status_code: int) -> str:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return ErrorCode.AUTH_REQUIRED
    if status_code == status.HTTP_403_FORBIDDEN:
        return ErrorCode.PERMISSION_DENIED
    if status_code == status.HTTP_404_NOT_FOUND:
        return ErrorCode.RESOURCE_NOT_FOUND
    if status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        return ErrorCode.EXTERNAL_API_ERROR
    if status_code >= 500:
        return ErrorCode.SERVER_ERROR
    return ErrorCode.INVALID_INPUT


def _extract_legacy_error_message(data: Any) -> str:
    if data is None:
        return "요청을 처리할 수 없습니다."
    if isinstance(data, str):
        return data
    if not isinstance(data, dict):
        return str(data)
    if "error" in data and isinstance(data["error"], str):
        return data["error"]
    if "detail" in data:
        d = data["detail"]
        if isinstance(d, str):
            return d
        if isinstance(d, list) and d:
            return str(d[0])
        return str(d)
    if "message" in data and isinstance(data["message"], str):
        return data["message"]
    # DRF 필드 에러
    for _k, v in data.items():
        if isinstance(v, list) and v:
            return f"{v[0]}"
        if isinstance(v, dict) and v:
            first = next(iter(v.values()))
            if isinstance(first, list) and first:
                return str(first[0])
    return "입력값을 확인해 주세요."


def legacy_response_to_b2n(data: Any, status_code: int) -> dict:
    """기존 {error:...} / {detail:...} 응답을 b2n 봉투로 변환."""
    msg = _extract_legacy_error_message(data)
    code = _http_status_to_error_code(status_code)
    return {B2N_KEY: {"ErrorCode": code, "Message": msg, "Result": None}}
