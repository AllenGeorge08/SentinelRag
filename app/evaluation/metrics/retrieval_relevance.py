from typing_extensions import Annotated,TypedDict
from app.evaluation.metrics.llm_client import groq_model,nvidia_llm,openrouter_model
from pydantic import BaseModel,Field

class RetrievalRelevance(BaseModel):
    explanation: str =  Field(description="Explain your reasoning for the score")
    relevant : bool = Field(description="True if the retrieved documents are relevant to the question")


retrieval_relevance_instructions = """
You're a teacher grading a quiz.

You'll be given a QUESTION and a set of FACTS provided by the student.

Here's the grade criteria to follow:

1) You goal is to identify FACTS that're completely unrelated to the QUESTION.
2) If the facts contain ANY keywords or semantic meaning related to the question, consider them relevant
3) It's OK if the facts have SOME information that is unrelated to the question as long as (2) is met

Relevance:

- A relevance value of True means that the facts contain any keywords or semantic meaning related to the Question and are therefore relevant.
- A relevance value of False means that the Facts are completely unrelated to the Question.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 

Avoid simply stating the correct answer at the outset.

"""
# Primary model: OpenRouter
openrouter_structured = openrouter_model.with_structured_output(
    RetrievalRelevance, 
    method="json_schema", 
    strict=True
)

# Fallback 1: Groq
groq_structured = groq_model.with_structured_output(
    RetrievalRelevance, 
    method="json_schema", 
    strict=True
).with_retry(
    retry_if_exception_type=(Exception,), 
    wait_exponential_jitter=True, 
    stop_after_attempt=4
)

# Fallback 2: NVIDIA
nvidia_structured = nvidia_llm.with_structured_output(
    RetrievalRelevance, 
    method="json_schema", 
    strict=True
).with_retry(
    retry_if_exception_type=(Exception,), 
    wait_exponential_jitter=True, 
    stop_after_attempt=4
)

# Combined runnable: OpenRouter -> Groq -> NVIDIA
retrieval_relevance_llm = openrouter_structured.with_fallbacks(
    [groq_structured, nvidia_structured]
)

def retrieval_relevance(inputs: dict,outputs: dict)-> bool:
    """An evaluator for document relevance"""
    points = outputs["documents"].points
    doc_string = "\n\n".join(p.payload["text"] for p in points if p.payload and p.payload.get("text"))
    answer = f"FACTS: {doc_string}\n QUESTION: {inputs['question']}"

    grade = retrieval_relevance_llm.invoke([
        {"role": "system", "content": retrieval_relevance_instructions},
        {"role":"user","content": answer}
    ])

    return grade.relevant