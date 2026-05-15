from fastapi import APIRouter, HTTPException, status

from app.repositories.classification_job_repository import ClassificationJobRepository
from app.schemas.api import ClassificationJobResponse, UserCorrectionRequest, UserCorrectionResponse

router = APIRouter(tags=["classification-jobs"])


@router.get("/classification-jobs/{job_id}", response_model=ClassificationJobResponse)
def get_classification_job(job_id: str) -> ClassificationJobResponse:
    repository = ClassificationJobRepository()
    job = repository.get_job_details(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Classification job not found: {job_id}")
    return ClassificationJobResponse.model_validate(job)


@router.post(
    "/classification-jobs/{job_id}/corrections",
    response_model=UserCorrectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_correction(job_id: str, request: UserCorrectionRequest) -> UserCorrectionResponse:
    repository = ClassificationJobRepository()
    if repository.get_by_job_id(job_id) is None:
        raise HTTPException(status_code=404, detail=f"Classification job not found: {job_id}")

    try:
        correction = repository.create_correction(
            job_id=job_id,
            classification_result_id=request.classification_result_id,
            corrected_movement_type=request.corrected_movement_type,
            corrected_category=request.corrected_category,
            correction_reason=request.correction_reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return UserCorrectionResponse.model_validate(correction)
