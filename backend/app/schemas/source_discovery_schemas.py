from pydantic import BaseModel, HttpUrl


class RawQueryInput(BaseModel):
    raw_query: str


class MonitoredURLOutput(BaseModel):
    monitorable_urls: list[HttpUrl]
