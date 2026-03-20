"""Notification agent stub."""


class NotificationAgent:
    def notify(self, message):
        return {"notified": True, "message": message}
