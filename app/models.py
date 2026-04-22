from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "admin"
    SEO_MANAGER = "seo_manager"
    AUTHOR = "author"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    PUBLISHER = "publisher"
    VIEWER = "viewer"


class ArticleStatus(str, Enum):
    WRITING = "writing"
    READY_FOR_REVIEW = "ready_for_review"
    READY_FOR_PUBLISH = "ready_for_publish"
    PUBLISHED = "published"
    INDEXING_MONITORING = "indexing_monitoring"


class IndexingStatus(str, Enum):
    NOT_STARTED = "not_started"
    PENDING_CRAWL = "pending_crawl"
    CRAWLED_NOT_INDEXED = "crawled_not_indexed"
    INDEXED = "indexed"
    INDEXING_ISSUE = "indexing_issue"


class Site(BaseModel):
    id: int
    name: str
    domain: str
    default_language: str
    supported_languages: list[str] = Field(default_factory=list)
    created_at: datetime


class User(BaseModel):
    id: int
    name: str
    role: Role
    created_at: datetime


class Keyword(BaseModel):
    id: int
    site_id: int
    language: str
    term: str
    intent: str
    difficulty: int
    priority: int
    created_at: datetime


class QualityIssue(BaseModel):
    code: str
    message: str
    severity: str


class Article(BaseModel):
    id: int
    site_id: int
    keyword_id: int
    language: str
    title: str
    slug: str
    content: str
    status: ArticleStatus
    quality_score: int | None = None
    quality_issues: list[QualityIssue] = Field(default_factory=list)
    owner_user_id: int
    reviewer_user_id: int | None = None
    publisher_user_id: int | None = None
    published_url: str | None = None
    published_at: datetime | None = None
    indexing_status: IndexingStatus = IndexingStatus.NOT_STARTED
    created_at: datetime
    updated_at: datetime


class InMemoryDB(BaseModel):
    site_id_seq: int = 1
    user_id_seq: int = 2
    keyword_id_seq: int = 1
    article_id_seq: int = 1

    sites: dict[int, Site] = Field(default_factory=dict)
    users: dict[int, User] = Field(default_factory=dict)
    keywords: dict[int, Keyword] = Field(default_factory=dict)
    articles: dict[int, Article] = Field(default_factory=dict)

    def reset(self) -> None:
        self.site_id_seq = 1
        self.user_id_seq = 2
        self.keyword_id_seq = 1
        self.article_id_seq = 1
        self.sites.clear()
        self.users.clear()
        self.keywords.clear()
        self.articles.clear()


db = InMemoryDB()
