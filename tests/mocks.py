from dataclasses import dataclass

from django.test import RequestFactory

from uncms.pages.middleware import RequestPageManager


@dataclass
class MockRequestUser:
    is_authenticated: bool
    permission: bool = True
    is_staff: bool = True

    def has_perm(self, perm):
        return self.permission


class MockSuperUser:
    pk = 1
    is_active = True
    is_staff = True

    @staticmethod
    def has_perm(perm):
        return True


def request_with_pages(path="/"):
    request = RequestFactory().get(path)
    request.pages = RequestPageManager(request)
    return request
