class MockSuperUser:
    pk = 1
    is_active = True
    is_staff = True

    @staticmethod
    def has_perm(perm):
        return True
