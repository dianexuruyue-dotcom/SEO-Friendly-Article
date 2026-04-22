from datetime import datetime

from pydantic import BaseModel, Field

from app.models import ArticleStatus, IndexingCheck, IndexingStatus, QualityIssue, Role


class SiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    domain: str = Field(min_length=4, max_length=255)
    default_language: str = Field(min_length=2, max_length=20)
    supported_languages: list[str] = Field(min_length=1)


class SiteResponse(BaseModel):
    id: int
    name: str
    domain: str
    default_language: str
    supported_languages: list[str]
    created_at: datetime


class SiteListResponse(BaseModel):
    items: list[SiteResponse]
    total: int


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    role: Role


class UserResponse(BaseModel):
    id: int
    name: str
    role: Role
    created_at: datetime


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int


class KeywordCreate(BaseModel):
    site_id: int
    language: str = Field(min_length=2, max_length=20)
    keyword: str = Field(min_length=1, max_length=120)
    intent: str = Field(min_length=1, max_length=120)
    search_volume: int = Field(ge=0)
    difficulty: int = Field(ge=1, le=100)
    priority: int = Field(ge=1, le=10)
    cluster: str | None = Field(default=None, max_length=120)


class KeywordResponse(BaseModel):
    id: int
    site_id: int
    language: str
    keyword: str
    intent: str
    search_volume: int
    difficulty: int
    priority: int
    priority_score: int
    cluster: str | None
    created_at: datetime


class KeywordListResponse(BaseModel):
    items: list[KeywordResponse]
    total: int


class ArticleCreate(BaseModel):
    site_id: int
    language: str = Field(min_length=2, max_length=20)
    title: str = Field(min_length=6, max_length=180)
    slug: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=10)
    author: str = Field(min_length=1, max_length=120)
    author_id: int
    assignee_id: int
    primary_keyword_id: int
    primary_keyword: str = Field(min_length=1, max_length=120)
    secondary_keywords: list[str] = Field(default_factory=list)


class ArticleResponse(BaseModel):
    id: int
    site_id: int
    language: str
    title: str
    slug: str
    content: str
    author: str
    author_id: int
    assignee_id: int
    primary_keyword_id: int
    primary_keyword: str
    secondary_keywords: list[str]
    status: ArticleStatus
    quality_score: int | None
    quality_issues: list[QualityIssue]
    review_records: list[dict]
    indexing_status: IndexingStatus
    indexing_checks: list[IndexingCheck]
    published_url: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int


class QualityCheckResponse(BaseModel):
    article_id: int
    score: int
    status: str
    hard_gate_passed: bool
    issues: list[QualityIssue]
    checked_at: datetime


class StatusChangeResponse(BaseModel):
    article_id: int
    old_status: ArticleStatus
    new_status: ArticleStatus
    updated_at: datetime


class ReviewRequest(BaseModel):
    review_step: str = Field(pattern="^(seo|editorial)$")
    approved: bool


class IndexingCheckRequest(BaseModel):
    day_offset: int = Field(ge=1, le=90)


class IndexingCheckResponse(BaseModel):
    article_id: int
    status: IndexingStatus
    recommendation: str
    checked_at: datetime


class DashboardResponse(BaseModel):
    sites_total: int
    users_total: int
    keywords_total: int
    articles_total: int
    articles_by_status: dict[str, int]
    articles_by_indexing: dict[str, int]
