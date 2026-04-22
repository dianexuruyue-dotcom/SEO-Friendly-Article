from fastapi import FastAPI


app = FastAPI(title="SEO Friendly Article Workflow")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "SEO-Friendly-Article workflow is running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
