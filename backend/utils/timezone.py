import pytz
from datetime import datetime, timezone as datetime_timezone
from backend.core.conf import settings

class TimeZone:
    def __init__(self, tz: str = settings.DATETIME_TIMEZONE):
        self.tz_info = pytz.timezone(tz)

    def now(self) -> datetime:
        """
        Get the current time in the specified timezone

        :return:
        """
        return datetime.now(self.tz_info)

    def f_datetime(self, dt: datetime) -> datetime:
        """
        Convert a datetime object to the specified timezone

        :param dt:
        :return:
        """
        return dt.astimezone(self.tz_info)

    def f_str(self, date_str: str, format_str: str = settings.DATETIME_FORMAT) -> datetime:
        """
        Convert a date string to a datetime object in the specified timezone

        :param date_str:
        :param format_str:
        :return:
        """
        return datetime.strptime(date_str, format_str).replace(tzinfo=self.tz_info)

    @staticmethod
    def f_utc(dt: datetime) -> datetime:
        """
        Convert a datetime object to UTC (GMT) timezone

        :param dt:
        :return:
        """
        return dt.astimezone(datetime_timezone.utc)

timezone = TimeZone()