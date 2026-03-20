"""Notification service stub."""


class NotificationService:
    def send(self, channel, message):
        return {"sent": True, "channel": channel}
