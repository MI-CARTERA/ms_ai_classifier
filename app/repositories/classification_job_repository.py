from app.db.session import SessionLocal
from app.models.classification_job import ClassificationJob
from app.models.classification_result import ClassificationResult
from app.models.extracted_transaction import ExtractedTransaction
from app.models.user_correction import UserCorrection
from app.schemas.classification import ClassifiedMovement, NormalizedTransaction


class ClassificationJobRepository:
    def create_job(
        self,
        *,
        job_id: str,
        file_id: int,
        user_id: int,
        bank_account_id: int | None,
        tenant_id: str | None,
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
                tenant_id=tenant_id,
                file_name=file_name,
                storage_path=storage_path,
                status=status,
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    def update_job_status(self, job_id: str, *, status: str, error_message: str | None = None) -> ClassificationJob:
        with SessionLocal() as session:
            job = session.query(ClassificationJob).filter_by(job_id=job_id).one()
            job.status = status
            job.error_message = error_message
            session.commit()
            session.refresh(job)
            return job

    def store_extraction(
        self,
        job_id: str,
        *,
        extracted_text: str,
        extraction_summary: str,
        currency: str | None,
        transactions: list[NormalizedTransaction],
    ) -> list[ExtractedTransaction]:
        with SessionLocal() as session:
            job = session.query(ClassificationJob).filter_by(job_id=job_id).one()
            job.status = "extracting"
            job.extracted_text = extracted_text
            job.extraction_summary = extraction_summary
            job.currency = currency
            job.total_transactions = len(transactions)

            rows: list[ExtractedTransaction] = []
            for transaction in transactions:
                row = ExtractedTransaction(
                    classification_job_id=job.id,
                    sequence=transaction.sequence,
                    transaction_date=transaction.transaction_date,
                    description=transaction.description,
                    amount=transaction.amount,
                    currency=transaction.currency,
                    balance=transaction.balance,
                    raw_text=transaction.raw_text,
                    source=transaction.source,
                )
                session.add(row)
                rows.append(row)

            session.commit()
            for row in rows:
                session.refresh(row)
            return rows

    def store_classifications(
        self,
        job_id: str,
        *,
        classifier_name: str,
        extraction_summary: str | None,
        currency: str | None,
        classifications: list[ClassifiedMovement],
    ) -> list[ClassificationResult]:
        with SessionLocal() as session:
            job = session.query(ClassificationJob).filter_by(job_id=job_id).one()
            extracted_rows = (
                session.query(ExtractedTransaction)
                .filter_by(classification_job_id=job.id)
                .order_by(ExtractedTransaction.sequence.asc())
                .all()
            )
            extracted_by_sequence = {row.sequence: row for row in extracted_rows}

            results: list[ClassificationResult] = []
            review_required_count = 0
            for item in classifications:
                extracted_row = extracted_by_sequence[item.sequence]
                result = ClassificationResult(
                    classification_job_id=job.id,
                    extracted_transaction_id=extracted_row.id,
                    movement_type=item.movement_type,
                    category=item.category,
                    confidence=item.confidence,
                    reason=item.reason,
                    needs_review=item.needs_review,
                )
                if item.needs_review:
                    review_required_count += 1
                session.add(result)
                results.append(result)

            job.status = "classified"
            job.classifier_name = classifier_name
            job.extraction_summary = extraction_summary
            job.currency = currency
            job.total_transactions = len(classifications)
            job.review_required_count = review_required_count
            job.error_message = None

            session.commit()
            for result in results:
                session.refresh(result)
            return results

    def mark_failed(self, job_id: str, error_message: str) -> ClassificationJob:
        return self.update_job_status(job_id, status="failed", error_message=error_message)

    def get_by_job_id(self, job_id: str) -> ClassificationJob | None:
        with SessionLocal() as session:
            return session.query(ClassificationJob).filter_by(job_id=job_id).one_or_none()

    def get_job_details(self, job_id: str) -> dict | None:
        with SessionLocal() as session:
            job = session.query(ClassificationJob).filter_by(job_id=job_id).one_or_none()
            if job is None:
                return None

            extracted_rows = (
                session.query(ExtractedTransaction)
                .filter_by(classification_job_id=job.id)
                .order_by(ExtractedTransaction.sequence.asc())
                .all()
            )
            classification_rows = (
                session.query(ClassificationResult)
                .filter_by(classification_job_id=job.id)
                .order_by(ClassificationResult.id.asc())
                .all()
            )
            corrections = (
                session.query(UserCorrection)
                .join(ClassificationResult, UserCorrection.classification_result_id == ClassificationResult.id)
                .filter(ClassificationResult.classification_job_id == job.id)
                .order_by(UserCorrection.id.asc())
                .all()
            )

            return {
                "job_id": job.job_id,
                "file_id": job.file_id,
                "user_id": job.user_id,
                "bank_account_id": job.bank_account_id,
                "tenant_id": job.tenant_id,
                "status": job.status,
                "file_name": job.file_name,
                "storage_path": job.storage_path,
                "classifier_name": job.classifier_name,
                "currency": job.currency,
                "extraction_summary": job.extraction_summary,
                "total_transactions": job.total_transactions,
                "review_required_count": job.review_required_count,
                "extracted_text": job.extracted_text,
                "error_message": job.error_message,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "extracted_transactions": [
                    {
                        "sequence": row.sequence,
                        "transaction_date": row.transaction_date,
                        "description": row.description,
                        "amount": row.amount,
                        "currency": row.currency,
                        "balance": row.balance,
                        "raw_text": row.raw_text,
                        "source": row.source,
                    }
                    for row in extracted_rows
                ],
                "classifications": [
                    {
                        "id": row.id,
                        "extracted_transaction_id": row.extracted_transaction_id,
                        "sequence": extracted_rows_by_id.sequence,
                        "transaction_date": extracted_rows_by_id.transaction_date,
                        "description": extracted_rows_by_id.description,
                        "amount": extracted_rows_by_id.amount,
                        "currency": extracted_rows_by_id.currency,
                        "balance": extracted_rows_by_id.balance,
                        "movement_type": row.movement_type,
                        "category": row.category,
                        "confidence": row.confidence,
                        "reason": row.reason,
                        "needs_review": row.needs_review,
                        "raw_text": extracted_rows_by_id.raw_text,
                        "source": extracted_rows_by_id.source,
                    }
                    for row in classification_rows
                    for extracted_rows_by_id in [self._get_required_extracted_row(extracted_rows, row.extracted_transaction_id)]
                ],
                "corrections": [
                    {
                        "id": correction.id,
                        "classification_result_id": correction.classification_result_id,
                        "corrected_movement_type": correction.corrected_movement_type,
                        "corrected_category": correction.corrected_category,
                        "correction_reason": correction.correction_reason,
                        "created_at": correction.created_at,
                    }
                    for correction in corrections
                ],
            }

    def create_correction(
        self,
        *,
        job_id: str,
        classification_result_id: int,
        corrected_movement_type: str,
        corrected_category: str,
        correction_reason: str | None,
    ) -> UserCorrection:
        with SessionLocal() as session:
            job = session.query(ClassificationJob).filter_by(job_id=job_id).one()
            result = (
                session.query(ClassificationResult)
                .filter_by(id=classification_result_id, classification_job_id=job.id)
                .one_or_none()
            )
            if result is None:
                raise ValueError(f"Classification result not found: {classification_result_id}")
            correction = UserCorrection(
                classification_result_id=result.id,
                corrected_movement_type=corrected_movement_type,
                corrected_category=corrected_category,
                correction_reason=correction_reason,
            )
            result.movement_type = corrected_movement_type
            result.category = corrected_category
            result.needs_review = False
            session.add(correction)
            job.review_required_count = max(0, job.review_required_count - 1)
            session.commit()
            session.refresh(correction)
            return correction

    @staticmethod
    def _get_required_extracted_row(
        extracted_rows: list[ExtractedTransaction],
        extracted_transaction_id: int,
    ) -> ExtractedTransaction:
        for row in extracted_rows:
            if row.id == extracted_transaction_id:
                return row
        raise ValueError(f"Extracted transaction not found: {extracted_transaction_id}")
