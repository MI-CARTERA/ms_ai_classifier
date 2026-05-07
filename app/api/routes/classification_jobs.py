from fastapi import APIRouter, HTTPException

from app.repositories.classification_job_repository import ClassificationJobRepository
from app.schemas.api import ClassificationJobResponse

router = APIRouter(tags=["classification-jobs"])


@router.get("/classification-jobs/{job_id}", response_model=ClassificationJobResponse)
def get_classification_job(job_id: str) -> ClassificationJobResponse:
    repository = ClassificationJobRepository()
    job = repository.get_by_job_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Classification job not found: {job_id}")
    return ClassificationJobResponse.model_validate(job)
