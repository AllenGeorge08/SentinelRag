from typing import List
from typing_extensions import Annotated,TypedDict
from app.evaluation.metrics.llm_client import openrouter_model
from pydantic import BaseModel,Field
import json 


class Correctness(BaseModel):
    #Helps model to reason before filling this schema
    key_points: List[str] = Field(description="The essential points in the ground truth answer")
    explaination: str = Field(description="Explain your reasoning for the score")
    is_correct: bool  =  Field(description="True if the answer is correct, False otherwise")


correctness_instructions ="""

You are grading a student answer against a ground truth answer.

Steps:
1) List the key points of the GROUND TRUTH (the essential facts needed to answer the QUESTION).
2) Check each key point against the STUDENT ANSWER.
3) Check the student answer for statements that contradict the ground truth.

Mark is_correct=True only if:
- every key point is covered (wording and structure may differ),
- there are no contradictions with the ground truth,
- any extra content is relevant and does not conflict with the ground truth.

Mark is_correct=False if:
- a key point is missing or wrong,
- the student says the answer is "not found" but the ground truth gives an answer,
- the student gives a substantive answer but the ground truth says the information is not in the documents.

Rules:
- Judge only against the ground truth. Do not use outside knowledge.
- Ignore "Source Document", "Page", and "Suggestion" lines and formatting.


"""

# Primary model: OpenRouter
openrouter_structured = openrouter_model.with_structured_output(
    Correctness, 
    method="json_schema", 
    strict=True,
).with_retry(
    retry_if_exception_type=(Exception,), 
    wait_exponential_jitter=True, 
    stop_after_attempt=4
)

Correctness_llm = openrouter_structured


def correctness(inputs: dict, outputs: dict,reference_outputs: dict) -> bool:
    """Evaluator for RAG Output Accuracy"""
    actual_answers = f"""\
    Question: {inputs['question']}
    Ground Truth Answer: {reference_outputs['answer']}
    Student Answer: {outputs['answer']}
    """
    result = Correctness_llm.invoke([
        ("system",correctness_instructions),
        ("user",actual_answers)
    ])

    return result.is_correct