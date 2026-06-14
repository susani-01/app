from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import DeclarativeBase

SEOUL_TZ = ZoneInfo("Asia/Seoul")


def seoul_now() -> datetime:
    return datetime.now(SEOUL_TZ)


class Base(DeclarativeBase):
    pass
