from typing_extensions import Annotated,TypedDict
from app.evaluation.metrics.llm_client import groq_model,nvidia_llm,openrouter_model
from pydantic import BaseModel,Field
from langchain.rate_limiters import InMemoryRateLimiter

groq_rateLimiter = InMemoryRateLimiter(
    requests_per_second=0.12, #
    check_every_n_seconds=0.1,
    max_bucket_size=1, #tpm is low..8000 tpm, rpm = 30.. 
)


class RelevanceGrade(BaseModel):
    explaination: str=   Field(description="Explain your reasoning for the score")
    is_relevant: bool = Field(description="Provide the score on whether the answer addresses the question correctly or not")


relevance_instructions = """
You're a teacher grading a quiz.

Here's the grade criteria to follow:

1) Ensure the STUDENT ANSWER is relevant to the question i.e: 1) the answer addresses the user's intent 2) It answers the main question 3) It isn't a hallucinated or off topic answer
2) Ensure the STUDENT ANSWER helps to answer the Question
3) Do not evaluate factual accuracy unless it affects whether the answer addresses the question.
4) Evaluate only the relationship between the question and the student answer

Relevance:

- A relevance value of the True means that the student's answer meets all of the criteria.
- A relevance value of False means that the student's answer does not meet all of the criteria

Explain your reasoning in a step by step manner to ensure your reasoning and conclusion are correct.

Avoid simply stating the correct answer at the outset.

"""
# Primary model: OpenRouter
openrouter_structured = openrouter_model.with_structured_output(
    RelevanceGrade, 
    method="json_schema", 
    strict=True
)

# Fallback 1: Groq
groq_structured = groq_model.with_structured_output(
    RelevanceGrade, 
    method="json_schema", 
    strict=True
).with_retry(
    retry_if_exception_type=(Exception,), 
    wait_exponential_jitter=True, 
    stop_after_attempt=4
)

# Fallback 2: NVIDIA
nvidia_structured = nvidia_llm.with_structured_output(
    RelevanceGrade, 
    method="json_schema", 
    strict=True
).with_retry(
    retry_if_exception_type=(Exception,), 
    wait_exponential_jitter=True, 
    stop_after_attempt=4
)

# Combined runnable: OpenRouter -> Groq -> NVIDIA
relevance_llm = openrouter_structured.with_fallbacks(
    [groq_structured, nvidia_structured]
)


def relevance(inputs:dict,outputs: dict) -> bool:
    """Relevance Scoring For RAG Pipeline"""
    answer = f"Question: {inputs['question']}\n STUDENT ANSWER: {outputs['answer']}"
    grade = relevance_llm.invoke([
        {"role": "system", "content": relevance_instructions},
        {"role": "user","content": answer}
    ])
    return grade.is_relevant
