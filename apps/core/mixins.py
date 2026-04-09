"""DRF 응답을 b2n2027ApiResponse 형식으로 통일."""

from __future__ import annotations

from rest_framework import status

from apps.core.b2n_response import (
    B2N_KEY,
    is_b2n_wrapped,
    legacy_response_to_b2n,
    wrap_success_payload,
)


class B2nResponseMixin:
    """
    성공(2xx): 본문을 Result로 넣어 봉투 처리.
    오류(그 외): legacy dict를 오류 봉투로 변환(Result=null).
    이미 b2n2027ApiResponse 형식이면 그대로 둠.
    """

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if not hasattr(response, "data"):
            return response
        if response.data is None:
            return response
        if getattr(response, "status_code", 200) == status.HTTP_204_NO_CONTENT:
            return response

        data = response.data
        if is_b2n_wrapped(data):
            return response

        sc = response.status_code
        if status.is_success(sc):
            msg = "정상 처리되었습니다."
            if sc == status.HTTP_201_CREATED:
                msg = "생성되었습니다."
            response.data = wrap_success_payload(data, message=msg)
        else:
            response.data = legacy_response_to_b2n(data, sc)

        return response
