"""
`/api/` 하위 라우팅만 모은다.

`urls.py`에 `path("api/", include(core))` 와 `path("api/", include(participants))` 를
나란히 두면, Django는 첫 번째 include에서 매칭 실패 시 두 번째로 넘어간다.
반면 **한 줄** `path("api/", include(core))` 만 있고 그보다 **아래**에
`path("api/adminMember/", ...)` 를 두면, 이미 `api/` 가 먼저 잡혀
`adminMember/...` 가 core 쪽으로만 가서 404가 난다.

그래서 구체적인 `api/...` 경로는 항상 `path("", include(core))` 보다 위에 둔다.
"""

from django.urls import include, path

urlpatterns = [
    path("adminMember/", include("apps.admin_accounts.urls")),
    path("notices/", include("apps.board_notice.urls_public")),
    path("board/notices/", include("apps.board_notice.urls_admin")),
    path("public/homepage-docs/", include("apps.homepage_doc.urls_public")),
    path("board/homepage-docs/", include("apps.homepage_doc.urls_admin")),
    path("board/products/", include("apps.products.urls_admin")),
    path("public/products/", include("apps.products.urls_public")),
    path("messages/", include("apps.messages.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.participants.urls")),
]
