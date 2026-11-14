from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.controllers.appeal_controller import router as appeal_router
from app.controllers.auth_controller import router as auth_router
from app.controllers.case_controller import router as case_router
from app.controllers.dashboard_controller import router as dashboard_router
from app.controllers.reviewer_controller import router as reviewer_router
from app.controllers.similarity_controller import router as similarity_router
from app.controllers.submission_controller import router as submission_router
from app.core.config import settings
from app.db.session import get_db


app = FastAPI(
    title="Academic Integrity Review API",
    version="1.0.0",
    description="Role-aware case review, evidence, decisions and appeals.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(case_router)
app.include_router(appeal_router)
app.include_router(reviewer_router)
app.include_router(similarity_router)
app.include_router(submission_router)


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok"}
