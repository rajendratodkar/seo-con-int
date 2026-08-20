"""Pydantic schemas for the monitoring & alerts module."""
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Alert Channels
# ---------------------------------------------------------------------------

class AlertChannelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    channel_type: str = Field(pattern=r"^(email|slack|desktop)$")
    config: dict = Field(default_factory=dict)


class AlertChannelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    enabled: bool | None = None
    config: dict | None = None


class AlertChannelOut(BaseModel):
    id: int
    name: str
    channel_type: str
    enabled: bool
    config: dict
    last_tested_at: str | None = None
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Monitoring Rules
# ---------------------------------------------------------------------------

class MonitoringRuleCreate(BaseModel):
    website_id: int
    name: str = Field(min_length=1, max_length=200)
    rule_type: str = Field(
        pattern=r"^(ranking_drop|traffic_drop|new_seo_issue|crawl_error|position_change|ctr_drop)$"
    )
    config: dict = Field(default_factory=dict)
    channel_ids: list[int] = Field(default_factory=list)
    check_interval: str = Field(default="daily", pattern=r"^(hourly|daily|weekly)$")


class MonitoringRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    enabled: bool | None = None
    config: dict | None = None
    channel_ids: list[int] | None = None
    check_interval: str | None = Field(default=None, pattern=r"^(hourly|daily|weekly)$")


class MonitoringRuleOut(BaseModel):
    id: int
    website_id: int
    name: str
    rule_type: str
    enabled: bool
    config: dict
    channel_ids: list[int]
    check_interval: str
    last_checked_at: str | None = None
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Alert History
# ---------------------------------------------------------------------------

class AlertHistoryOut(BaseModel):
    id: int
    rule_id: int
    channel_id: int
    severity: str
    title: str
    message: str
    data: dict | None = None
    status: str
    error_message: str | None = None
    sent_at: str


# ---------------------------------------------------------------------------
# Test / Run
# ---------------------------------------------------------------------------

class TestChannelRequest(BaseModel):
    channel_id: int


class RunCheckRequest(BaseModel):
    rule_id: int
