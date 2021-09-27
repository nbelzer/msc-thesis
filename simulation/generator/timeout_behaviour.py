class TimeoutBehaviour:
    current_timeout: int

    def __init__(self):
        self.current_timeout = 0

    def has_timeout(self):
        return self.current_timeout > 0

    def decrement_timeout(self):
        self.current_timeout = max(self.current_timeout - 1, 0)
