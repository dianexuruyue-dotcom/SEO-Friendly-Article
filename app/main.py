from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status

from app.auth import require_role
from app.models import (
    Article,
    ArticleStatus,
    IndexingCheck,
    IndexingStatus,
    Keyword,
    QualityIssue,
    ReviewRecord,
    Role,
    Site,
    User,
    db,
)
from app.schemas import (
    ArticleCreate,
    ArticleListResponse,
    ArticleResponse,
    DashboardResponse,
    IndexingCheckRequest,
    IndexingCheckResponse,
    KeywordCreate,
    KeywordListResponse,
    KeywordResponse,
    QualityCheckResponse,
    ReviewRequest,
    SiteCreate,
    SiteListResponse,
    SiteResponse,
    StatusChangeResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
)


app = FastAPI(title="SEO Friendly Article Workflow")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ensure_site(site_id: int) -> Site:
    site = db.sites.get(site_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Site {site_id} not found")
    return site


def ensure_keyword(keyword_id: int) -> Keyword:
    keyword = db.keywords.get(keyword_id)
    if not keyword:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Keyword {keyword_id} not found")
    return keyword


def ensure_user(user_id: int) -> User:
    user = db.users.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return user


def ensure_article(article_id: int) -> Article:
    article = db.articles.get(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Article {article_id} not found")
    return article


def site_out(site: Site) -> SiteResponse:
    return SiteResponse(**site.model_dump())


def user_out(user: User) -> UserResponse:
    return UserResponse(**user.model_dump())


def keyword_out(keyword: Keyword) -> KeywordResponse:
    return KeywordResponse(**keyword.model_dump())


def article_out(article: Article) -> ArticleResponse:
    return ArticleResponse(**article.model_dump())


def calc_priority(search_volume: int, difficulty: int, priority: int) -> int:
    base = max(1, search_volume // 50)
    return max(1, min(100, int(base * (priority / max(1, difficulty / 20)))))


def run_quality(article: Article) -> QualityCheckResponse:
    issues: list[QualityIssue] = []
    content = article.content

    if len(article.title.strip()) < 30:
        issues.append(
            QualityIssue(
                code="TITLE_TOO_SHORT",
                message="Title should be at least 30 characters for strict mode.",
                severity="error",
            )
        )
    if len(content.split()) < 300:
        issues.append(
            QualityIssue(
                code="CONTENT_TOO_SHORT",
                message="Content should be at least 300 words for strict quality checks.",
                severity="error",
            )
        )
    if "# " not in content:
        issues.append(
            QualityIssue(code="MISSING_H1", message="Missing H1 heading in markdown content.", severity="error")
        )
    if "## " not in content:
        issues.append(
            QualityIssue(code="MISSING_H2", message="Missing at least one H2 heading.", severity="error")
        )
    if "http" not in content:
        issues.append(
            QualityIssue(code="MISSING_LINK", message="Missing at least one reference link.", severity="warning")
        )
    keyword_lower = article.primary_keyword.lower()
    if keyword_lower not in content.lower():
        issues.append(
            QualityIssue(
                code="PRIMARY_KEYWORD_MISSING",
                message="Primary keyword must appear in article content.",
                severity="error",
            )
        )

    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    score = max(0, 100 - len(errors) * 18 - len(warnings) * 5)
    hard_gate_passed = len(errors) == 0 and score >= 85

    article.quality_score = score
    article.hard_gate_passed = hard_gate_passed
    article.quality_issues = issues
    article.updated_at = now_utc()
    if hard_gate_passed:
        article.status = ArticleStatus.PENDING_REVIEW
    else:
        article.status = ArticleStatus.WRITING

    return QualityCheckResponse(
        article_id=article.id,
        score=score,
        status="passed" if hard_gate_passed else "failed",
        hard_gate_passed=hard_gate_passed,
        issues=[issue.model_dump() for issue in issues],
        checked_at=article.updated_at,
    )


def require_article_status(article: Article, expected: ArticleStatus) -> None:
    if article.status != expected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article {article.id} status must be {expected.value}, current is {article.status.value}",
        )


def status_changed(article: Article, old_status: ArticleStatus) -> StatusChangeResponse:
    return StatusChangeResponse(
        article_id=article.id,
        old_status=old_status,
        new_status=article.status,
        updated_at=article.updated_at,
    )


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "SEO-Friendly-Article workflow is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sites", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
def create_site(payload: SiteCreate, _: User = Depends(require_role({Role.ADMIN, Role.SEO_MANAGER}))) -> SiteResponse:
    if any(site.domain == payload.domain for site in db.sites.values()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Domain {payload.domain} already exists")
    site = Site(
        id=db.site_id_seq,
        name=payload.name,
        domain=payload.domain,
        default_language=payload.default_language,
        supported_languages=payload.supported_languages,
        created_at=now_utc(),
    )
    db.site_id_seq += 1
    db.sites[site.id] = site
    return site_out(site)


@app.get("/sites", response_model=SiteListResponse)
def list_sites(
    _: User = Depends(
        require_role({Role.ADMIN, Role.SEO_MANAGER, Role.AUTHOR, Role.EDITOR, Role.REVIEWER, Role.PUBLISHER, Role.VIEWER})
    ),
) -> SiteListResponse:
    items = [site_out(site) for site in db.sites.values()]
    return SiteListResponse(items=items, total=len(items))


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, _: User = Depends(require_role({Role.ADMIN}))) -> UserResponse:
    user = User(id=db.user_id_seq, name=payload.name, role=payload.role, created_at=now_utc())
    db.user_id_seq += 1
    db.users[user.id] = user
    return user_out(user)


@app.get("/users", response_model=UserListResponse)
def list_users(_: User = Depends(require_role({Role.ADMIN, Role.SEO_MANAGER}))) -> UserListResponse:
    items = [user_out(user) for user in db.users.values()]
    return UserListResponse(items=items, total=len(items))


@app.post("/keywords", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
def create_keyword(
    payload: KeywordCreate,
    _: User = Depends(require_role({Role.ADMIN, Role.SEO_MANAGER})),
) -> KeywordResponse:
    ensure_site(payload.site_id)
    priority_score = calc_priority(payload.search_volume, payload.difficulty, payload.priority)
    keyword = Keyword(
        id=db.keyword_id_seq,
        site_id=payload.site_id,
        language=payload.language,
        keyword=payload.keyword,
        intent=payload.intent,
        search_volume=payload.search_volume,
        difficulty=payload.difficulty,
        priority=payload.priority,
        priority_score=priority_score,
        cluster=payload.cluster,
        created_at=now_utc(),
    )
    db.keyword_id_seq += 1
    db.keywords[keyword.id] = keyword
    return keyword_out(keyword)


@app.get("/keywords", response_model=KeywordListResponse)
def list_keywords(
    site_id: int | None = None,
    _: User = Depends(
        require_role({Role.ADMIN, Role.SEO_MANAGER, Role.AUTHOR, Role.EDITOR, Role.REVIEWER, Role.PUBLISHER, Role.VIEWER})
    ),
) -> KeywordListResponse:
    keywords = list(db.keywords.values())
    if site_id is not None:
        keywords = [keyword for keyword in keywords if keyword.site_id == site_id]
    items = [keyword_out(keyword) for keyword in keywords]
    return KeywordListResponse(items=items, total=len(items))


@app.post("/articles", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    payload: ArticleCreate,
    _: User = Depends(require_role({Role.ADMIN, Role.SEO_MANAGER, Role.AUTHOR, Role.EDITOR})),
) -> ArticleResponse:
    ensure_site(payload.site_id)
    ensure_keyword(payload.primary_keyword_id)
    ensure_user(payload.author_id)
    ensure_user(payload.assignee_id)
    article = Article(
        id=db.article_id_seq,
        site_id=payload.site_id,
        language=payload.language,
        title=payload.title,
        slug=payload.slug,
        content=payload.content,
        author=payload.author,
        author_id=payload.author_id,
        assignee_id=payload.assignee_id,
        primary_keyword_id=payload.primary_keyword_id,
        primary_keyword=payload.primary_keyword,
        secondary_keywords=payload.secondary_keywords,
        status=ArticleStatus.WRITING,
        quality_score=None,
        hard_gate_passed=False,
        quality_issues=[],
        review_records=[],
        published_url=None,
        published_at=None,
        indexing_status=IndexingStatus.NOT_STARTED,
        indexing_checks=[],
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    db.article_id_seq += 1
    db.articles[article.id] = article
    return article_out(article)


@app.get("/articles", response_model=ArticleListResponse)
def list_articles(
    status: ArticleStatus | None = None,
    site_id: int | None = None,
    _: User = Depends(
        require_role({Role.ADMIN, Role.SEO_MANAGER, Role.AUTHOR, Role.EDITOR, Role.REVIEWER, Role.PUBLISHER, Role.VIEWER})
    ),
) -> ArticleListResponse:
    articles = list(db.articles.values())
    if status:
        articles = [article for article in articles if article.status == status]
    if site_id:
        articles = [article for article in articles if article.site_id == site_id]
    items = [article_out(article) for article in articles]
    return ArticleListResponse(items=items, total=len(items))


@app.get("/articles/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: int,
    _: User = Depends(
        require_role({Role.ADMIN, Role.SEO_MANAGER, Role.AUTHOR, Role.EDITOR, Role.REVIEWER, Role.PUBLISHER, Role.VIEWER})
    ),
) -> ArticleResponse:
    article = ensure_article(article_id)
    return article_out(article)


@app.post("/articles/{article_id}/quality-check", response_model=QualityCheckResponse)
def quality_check(
    article_id: int,
    _: User = Depends(require_role({Role.ADMIN, Role.SEO_MANAGER, Role.EDITOR, Role.REVIEWER})),
) -> QualityCheckResponse:
    article = ensure_article(article_id)
    return run_quality(article)


@app.post("/articles/{article_id}/submit-review", response_model=StatusChangeResponse)
def submit_review(
    article_id: int,
    _: User = Depends(require_role({Role.ADMIN, Role.SEO_MANAGER, Role.AUTHOR, Role.EDITOR})),
) -> StatusChangeResponse:
    article = ensure_article(article_id)
    if not article.hard_gate_passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article must pass strict quality check before review.",
        )
    old_status = article.status
    if article.status not in {ArticleStatus.WRITING, ArticleStatus.PENDING_REVIEW}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article is not ready to enter review.",
        )
    article.status = ArticleStatus.PENDING_REVIEW
    article.updated_at = now_utc()
    return status_changed(article, old_status)


@app.post("/articles/{article_id}/review", response_model=StatusChangeResponse)
def review_article(
    article_id: int,
    payload: ReviewRequest,
    actor: User = Depends(require_role({Role.ADMIN, Role.SEO_MANAGER, Role.REVIEWER})),
) -> StatusChangeResponse:
    article = ensure_article(article_id)
    require_article_status(article, ArticleStatus.PENDING_REVIEW)
    step = payload.review_step
    approved = payload.approved
    old_status = article.status
    article.review_records.append(
        ReviewRecord(
            review_step=step,
            approved=approved,
            reviewer_role=actor.role,
            reviewed_at=now_utc(),
        )
    )
    if approved and step == "editorial":
        article.status = ArticleStatus.READY_TO_PUBLISH
    elif approved:
        article.status = ArticleStatus.PENDING_REVIEW
    else:
        article.status = ArticleStatus.WRITING
    article.updated_at = now_utc()
    return status_changed(article, old_status)


@app.post("/articles/{article_id}/publish", response_model=ArticleResponse)
def publish_article(
    article_id: int,
    _: User = Depends(require_role({Role.ADMIN, Role.PUBLISHER})),
) -> ArticleResponse:
    article = ensure_article(article_id)
    require_article_status(article, ArticleStatus.READY_TO_PUBLISH)
    site = ensure_site(article.site_id)
    article.status = ArticleStatus.PUBLISHED
    article.published_at = now_utc()
    article.published_url = f"https://{site.domain}/{article.slug}"
    article.indexing_status = IndexingStatus.PENDING_CRAWL
    article.updated_at = now_utc()
    return article_out(article)


@app.post("/articles/{article_id}/indexing-check", response_model=IndexingCheckResponse)
def indexing_check(
    article_id: int,
    payload: IndexingCheckRequest,
    _: User = Depends(require_role({Role.ADMIN, Role.SEO_MANAGER, Role.REVIEWER, Role.PUBLISHER, Role.VIEWER})),
) -> IndexingCheckResponse:
    article = ensure_article(article_id)
    if article.status not in {ArticleStatus.PUBLISHED, ArticleStatus.INDEXING_MONITORING, ArticleStatus.INDEXED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Article must be published first")

    if payload.day_offset <= 1:
        new_status = IndexingStatus.PENDING_CRAWL
        recommendation = "Keep monitoring indexing status."
    elif payload.day_offset <= 7:
        new_status = IndexingStatus.INDEXED
        recommendation = "Indexed successfully."
    elif payload.day_offset <= 14:
        new_status = IndexingStatus.CRAWLED_NOT_INDEXED
        recommendation = "Strengthen internal links and update article depth."
    else:
        new_status = IndexingStatus.INDEXING_ISSUE
        recommendation = "Investigate robots/sitemap/canonical settings and request reindex."

    article.indexing_status = new_status
    article.status = (
        ArticleStatus.INDEXED
        if new_status == IndexingStatus.INDEXED
        else ArticleStatus.INDEXING_MONITORING
    )
    article.updated_at = now_utc()
    article.indexing_checks.append(
        IndexingCheck(
            day_offset=payload.day_offset,
            status=new_status,
            checked_at=article.updated_at,
            recommendation=recommendation,
        )
    )

    return IndexingCheckResponse(
        article_id=article.id,
        status=new_status,
        recommendation=recommendation,
        checked_at=article.updated_at,
    )


@app.get("/dashboard", response_model=DashboardResponse)
def dashboard(_: User = Depends(require_role({Role.ADMIN, Role.SEO_MANAGER, Role.VIEWER}))) -> DashboardResponse:
    by_status: dict[str, int] = {}
    by_indexing: dict[str, int] = {}
    for article in db.articles.values():
        by_status[article.status.value] = by_status.get(article.status.value, 0) + 1
        by_indexing[article.indexing_status.value] = by_indexing.get(article.indexing_status.value, 0) + 1
    return DashboardResponse(
        sites_total=len(db.sites),
        users_total=len(db.users),
        keywords_total=len(db.keywords),
        articles_total=len(db.articles),
        articles_by_status=by_status,
        articles_by_indexing=by_indexing,
    )


@app.post("/_test/reset")
def reset_data() -> dict[str, str]:
    db.reset()
    return {"status": "ok"}
