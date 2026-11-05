import pytest
from pydantic import ValidationError
from app.domain.schemas import RetrievalRequest

def test_question_is_trimmed():
    assert RetrievalRequest(question="  Explain Lambda and S3  ").question == "Explain Lambda and S3"

def test_blank_question_is_rejected():
    with pytest.raises(ValidationError):
        RetrievalRequest(question="   ")
