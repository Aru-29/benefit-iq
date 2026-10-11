"""Additional live local scenarios; preserves the original HTTP ledger."""

import json
import re
from uuid import uuid4

import httpx

import acceptance as a


def main():
    a.records = json.loads((a.OUT / "http.json").read_text(encoding="utf-8"))
    call = a.call
    email = f"e2e-{uuid4().hex[:10]}@example.com"
    payload = dict(email=email, password=a.password, username=email.split("@")[0],
                   first_name="Synthetic", last_name="Acceptance")
    call("Registration invalid email", "POST", "/api/v1/auth/register", {**payload, "email":"bad"}, (422,))
    call("Registration weak password", "POST", "/api/v1/auth/register", {**payload, "password":"short"}, (422,))
    call("Registration sends Mailpit OTP", "POST", "/api/v1/auth/register", payload, (201,))
    call("Registration wrong OTP", "POST", "/api/v1/auth/verify-registration-otp", dict(email=email, otp="000000"), (400,))
    code = a.otp(email)
    tokens = call("Registration complete", "POST", "/api/v1/auth/verify-registration-otp", dict(email=email, otp=code))
    call("Registration OTP reuse denied", "POST", "/api/v1/auth/verify-registration-otp", dict(email=email, otp=code), (400,))
    call("Duplicate registration", "POST", "/api/v1/auth/register", payload, (409,400))
    a.client.headers["Authorization"] = "Bearer " + tokens["access_token"]
    a.identity = email
    profile = call("New customer profile", "GET", "/api/v1/users/me")
    assert profile["is_email_verified"] and profile["role_name"] == "CUSTOMER"
    call("Profile update", "PUT", "/api/v1/users/me", dict(first_name="Updated",last_name="Acceptance",username=payload["username"]))
    call("Change password wrong current", "POST", "/api/v1/auth/change-password", dict(current_password="wrong",new_password=a.password), (401,))
    call("Change password valid", "POST", "/api/v1/auth/change-password", dict(current_password=a.password,new_password=a.password))
    call("Reset invalid token", "POST", "/api/v1/auth/reset-password", dict(token="invalid",new_password=a.password), (401,400))
    call("Forgot password unknown email", "POST", "/api/v1/auth/forgot-password", dict(email="unknown-e2e@example.com"))
    call("Forgot password delivers reset link", "POST", "/api/v1/auth/forgot-password", dict(email=email))
    messages = httpx.get("http://127.0.0.1:18025/api/v1/messages").json()["messages"]
    item = next(m for m in messages if any(t["Address"] == email for t in m["To"]) and "Reset" in m["Subject"])
    mail = httpx.get("http://127.0.0.1:18025/api/v1/message/" + item["ID"]).json()
    token = re.search(r"token=([A-Za-z0-9_.-]+)", mail["HTML"] or mail["Text"]).group(1)
    call("Reset password valid link", "POST", "/api/v1/auth/reset-password", dict(token=token,new_password=a.password))
    call("Legacy email verification invalid token", "POST", "/api/v1/auth/verify-email", dict(token="invalid"), (401,400))
    call("Unsupported OAuth provider", "POST", "/api/v1/auth/unsupported/callback", {}, (400,))
    call("Google callback missing credentials", "POST", "/api/v1/auth/google/callback", {}, (400,401))
    a.login(email)
    a.login("admin@example.com")
    uid = profile["id"]
    call("Admin reads new user", "GET", "/api/v1/users/"+uid)
    call("Admin updates synthetic user", "PUT", "/api/v1/users/"+uid, dict(first_name="Admin updated",last_name="Acceptance",username=payload["username"]))
    call("User query", "POST", "/api/v1/users/query", dict(search=email))
    call("User query invalid page", "POST", "/api/v1/users/query", dict(page=0), (422,))
    call("Unknown user", "GET", "/api/v1/users/"+str(uuid4()), expected=(404,))
    call("Malformed user ID", "GET", "/api/v1/users/not-a-uuid", expected=(422,))
    call("Secret metadata without configured vault", "GET", "/api/v1/secrets")
    call("Secret rotation unmanaged path", "POST", "/api/v1/secrets/rotate", dict(path="invalid",key="test",value="synthetic"), (422,))
    call("Deactivate synthetic user", "DELETE", "/api/v1/users/"+uid)
    a.client.headers.pop("Authorization", None)
    a.identity = "anonymous"
    call("Inactive user login denied", "POST", "/api/v1/auth/login", dict(email=email,password=a.password), (401,403))
    a.save()


if __name__ == "__main__":
    try:
        main()
    finally:
        a.save()
