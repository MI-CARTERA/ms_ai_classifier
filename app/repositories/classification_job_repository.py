from app.db.session import SessionLocal
from app.models.classification_job import ClassificationJob


class ClassificationJobRepository:
    def create_job(
        self,
        *,
        job_id: str,
        file_id: int,
        user_id: int,
        bank_account_id: int | None,
        file_name: str,
        storage_path: str,
        status: str,
    ) -> ClassificationJob:
        with SessionLocal() as session:
            job = ClassificationJob(
                job_id=job_id,
                file_id=file_id,
                user_id=user_id,
                bank_account_id=bank_account_id,
                file_name=file_name,
                storage_path=storage_path,
                status=status,
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    def mark_processing(self, job_id: str, extracted_text: str) -> None:
        with SessionLocal() as session:
            job = session.query(ClassificationJob).filter_by(job_id=job_id).one()
            job.status = "processing"
            job.extracted_text = extracted_text
            session.commit()

    def mark_succeeded(self, job_id: str, classification_result: dict) -> ClassificationJob:
        with SessionLocal() as session:
            job = session.query(ClassificationJob).filter_by(job_id=job_id).one()
            job.status = "completed"
            job.classification_result = classification_result
            job.error_message = None
            session.commit()
            session.refresh(job)
            return job

    def mark_failed(self, job_id: str, error_message: str) -> ClassificationJob:
        with SessionLocal() as session:
            job = session.query(ClassificationJob).filter_by(job_id=job_id).one()
            job.status = "failed"
            job.error_message = error_message
            session.commit()
            session.refresh(job)
            return job

    def get_by_job_id(self, job_id: str) -> ClassificationJob | None:
        with SessionLocal() as session:
            return session.query(ClassificationJob).filter_by(job_id=job_id).one_or_none()
