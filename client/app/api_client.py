"""
HTTP API client - serverga so'rovlar yuborish.
"""
import requests
from typing import Optional, Dict, Any
from .config import Config


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    def __init__(self):
        self._token: Optional[str] = None
        self._user_info: Dict = {}

    @property
    def base_url(self) -> str:
        return Config.server_url()

    @property
    def headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        timeout = kwargs.pop("timeout", Config.get("timeout", 10))
        try:
            resp = requests.request(
                method, url,
                headers=self.headers,
                timeout=timeout,
                **kwargs
            )
            if resp.status_code == 401:
                raise APIError("Session muddati tugadi. Qayta kiring.", 401)
            if resp.status_code == 403:
                raise APIError("Ruxsat yo'q.", 403)
            if not resp.ok:
                try:
                    detail = resp.json().get("detail", resp.text)
                except Exception:
                    detail = resp.text
                raise APIError(str(detail), resp.status_code)
            if resp.content:
                return resp.json()
            return None
        except requests.exceptions.ConnectionError:
            raise APIError("Serverga ulanib bo'lmadi. IP manzilni tekshiring.")
        except requests.exceptions.Timeout:
            raise APIError("Server javob bermadi (timeout).")
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Kutilmagan xato: {e}")

    def check_connection(self) -> bool:
        try:
            result = self._request("GET", "/health", timeout=3)
            return result is not None
        except Exception:
            return False

    # ── Auth ──────────────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> dict:
        result = self._request("POST", "/api/auth/login",
                               json={"username": username, "password": password})
        self._token = result["access_token"]
        self._user_info = result
        return result

    def logout(self):
        self._token = None
        self._user_info = {}

    @property
    def is_logged_in(self) -> bool:
        return bool(self._token)

    @property
    def user_role(self) -> str:
        return self._user_info.get("role", "")

    @property
    def user_name(self) -> str:
        return self._user_info.get("full_name", "")

    @property
    def user_id(self) -> int:
        return self._user_info.get("user_id", 0)

    # ── Users ─────────────────────────────────────────────────────────────────

    def get_users(self) -> list:
        return self._request("GET", "/api/users/")

    def create_user(self, data: dict) -> dict:
        return self._request("POST", "/api/users/", json=data)

    def update_user(self, user_id: int, data: dict) -> dict:
        return self._request("PUT", f"/api/users/{user_id}", json=data)

    def delete_user(self, user_id: int):
        return self._request("DELETE", f"/api/users/{user_id}")

    # ── Questions ─────────────────────────────────────────────────────────────

    def get_questions(self, category_id=None, search=None) -> list:
        params = {}
        if category_id:
            params["category_id"] = category_id
        if search:
            params["search"] = search
        return self._request("GET", "/api/questions/", params=params)

    def create_question(self, data: dict) -> dict:
        return self._request("POST", "/api/questions/", json=data)

    def update_question(self, q_id: int, data: dict) -> dict:
        return self._request("PUT", f"/api/questions/{q_id}", json=data)

    def delete_question(self, q_id: int):
        return self._request("DELETE", f"/api/questions/{q_id}")

    def get_categories(self) -> list:
        return self._request("GET", "/api/questions/categories")

    def create_category(self, name: str) -> dict:
        return self._request("POST", "/api/questions/categories", json={"name": name})

    def delete_category(self, cat_id: int):
        return self._request("DELETE", f"/api/questions/categories/{cat_id}")

    def toggle_question_active(self, q_id: int) -> dict:
        return self._request("PATCH", f"/api/questions/{q_id}/toggle-active")

    def set_category_time_limit(self, cat_id: int, time_limit: int) -> dict:
        return self._request("PUT", f"/api/questions/categories/{cat_id}/time-limit",
                             params={"time_limit": time_limit})

    # ── Class ↔ Fan ───────────────────────────────────────────────────────────

    def get_class_fans(self, class_id: int) -> list:
        return self._request("GET", f"/api/students/classes/{class_id}/fans")

    def assign_fan_to_class(self, class_id: int, fan_id: int) -> dict:
        return self._request("POST", f"/api/students/classes/{class_id}/fans/{fan_id}")

    def unassign_fan_from_class(self, class_id: int, fan_id: int) -> dict:
        return self._request("DELETE", f"/api/students/classes/{class_id}/fans/{fan_id}")

    # ── Tests ─────────────────────────────────────────────────────────────────

    def get_tests(self) -> list:
        return self._request("GET", "/api/tests/")

    def get_public_tests(self) -> list:
        return self._request("GET", "/api/tests/public/list")

    def create_test(self, data: dict) -> dict:
        return self._request("POST", "/api/tests/", json=data)

    def update_test(self, test_id: int, data: dict) -> dict:
        return self._request("PUT", f"/api/tests/{test_id}", json=data)

    def delete_test(self, test_id: int):
        return self._request("DELETE", f"/api/tests/{test_id}")

    def copy_test(self, test_id: int) -> dict:
        return self._request("POST", f"/api/tests/{test_id}/copy")

    def get_test_detail(self, test_id: int) -> dict:
        return self._request("GET", f"/api/tests/{test_id}")

    def add_questions_to_test(self, test_id: int, question_ids: list):
        return self._request("POST", f"/api/tests/{test_id}/questions",
                             json={"question_ids": question_ids})

    def remove_question_from_test(self, test_id: int, question_id: int):
        return self._request("DELETE", f"/api/tests/{test_id}/questions/{question_id}")

    # ── Sessions ──────────────────────────────────────────────────────────────

    def start_exam(self, test_id: int, name: str, lastname: str, student_class: str) -> dict:
        return self._request("POST", "/api/sessions/start", json={
            "test_id": test_id,
            "student_name": name,
            "student_lastname": lastname,
            "student_class": student_class,
        })

    def finish_exam(self, session_id: int, answers: dict) -> dict:
        return self._request("POST", f"/api/sessions/{session_id}/finish",
                             json={"answers": answers})

    def get_results(self) -> list:
        return self._request("GET", "/api/sessions/results")

    # ── Students / Classes ────────────────────────────────────────────────────

    def get_all_students(self, class_id=None, fan_id=None, search=None) -> list:
        params = {}
        if class_id: params["class_id"] = class_id
        if fan_id:   params["fan_id"]   = fan_id
        if search:   params["search"]   = search
        return self._request("GET", "/api/students/all", params=params)

    def get_classes(self) -> list:
        return self._request("GET", "/api/students/classes")

    def get_classes_public(self) -> list:
        return self._request("GET", "/api/students/classes/public")

    def create_class(self, name: str) -> dict:
        return self._request("POST", "/api/students/classes", json={"name": name})

    def update_class(self, class_id: int, name: str) -> dict:
        return self._request("PUT", f"/api/students/classes/{class_id}", json={"name": name})

    def delete_class(self, class_id: int):
        return self._request("DELETE", f"/api/students/classes/{class_id}")

    def get_students(self, class_id: int) -> list:
        return self._request("GET", f"/api/students/classes/{class_id}/students")

    def get_students_public(self, class_id: int) -> list:
        return self._request("GET", f"/api/students/classes/{class_id}/students/public")

    def add_student(self, class_id: int, data: dict) -> dict:
        return self._request("POST", f"/api/students/classes/{class_id}/students", json=data)

    def update_student(self, student_id: int, data: dict) -> dict:
        return self._request("PUT", f"/api/students/{student_id}", json=data)

    def delete_student(self, student_id: int):
        return self._request("DELETE", f"/api/students/{student_id}")

    def toggle_class_active(self, class_id: int) -> dict:
        return self._request("PATCH", f"/api/students/classes/{class_id}/toggle-active")

    def get_class_tests_public(self, class_id: int) -> list:
        return self._request("GET", f"/api/students/classes/{class_id}/tests")

    def assign_test_to_class(self, class_id: int, test_id: int) -> dict:
        return self._request("POST", f"/api/students/classes/{class_id}/tests/{test_id}")

    def unassign_test_from_class(self, class_id: int, test_id: int) -> dict:
        return self._request("DELETE", f"/api/students/classes/{class_id}/tests/{test_id}")

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats_overview(self) -> dict:
        return self._request("GET", "/api/stats/overview")

    def get_top_students(self) -> list:
        return self._request("GET", "/api/stats/top-students")

    def get_stats_by_test(self) -> list:
        return self._request("GET", "/api/stats/by-test")

    def get_grade_distribution(self) -> dict:
        return self._request("GET", "/api/stats/grade-distribution")

    def get_audit_logs(self) -> list:
        return self._request("GET", "/api/stats/audit-logs")

    def clear_audit_logs(self) -> dict:
        return self._request("DELETE", "/api/settings/logs")

    def change_my_password(self, old_password: str, new_password: str) -> dict:
        return self._request("POST", "/api/settings/change-password",
                             params={"old_password": old_password, "new_password": new_password})

    # ── Settings ──────────────────────────────────────────────────────────────

    def get_settings(self) -> dict:
        return self._request("GET", "/api/settings/")

    def save_setting(self, key: str, value: str):
        return self._request("POST", "/api/settings/", json={"key": key, "value": value})

    def export_excel(self) -> bytes:
        url = f"{self.base_url}/api/settings/export/excel"
        resp = requests.get(url, headers=self.headers, timeout=30)
        if not resp.ok:
            raise APIError("Excel eksport xatosi")
        return resp.content


# Global singleton
api = APIClient()
