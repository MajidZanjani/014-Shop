"""Closed service errors, without submitted customer values or secrets."""


class ShbError(ValueError):
    def __init__(self, code, status=409):
        self.code = code
        self.status = status
        super().__init__(code)
