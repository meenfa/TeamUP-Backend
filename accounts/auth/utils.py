def set_auth_cookies(response, access_token, refresh_token):
    response.set_cookie(
        key="access",
        value=access_token,
        httponly=True,
        secure=False,        # keep False for local development (HTTP)
        samesite="Lax",     # REQUIRED for cross-origin (Next.js → Django)
        path="/",
    )

    response.set_cookie(
        key="refresh",
        value=refresh_token,
        httponly=True,
        secure=False,        # keep False for local development
        samesite="Lax",     # REQUIRED for cross-origin
        path="/",
    )

    return response