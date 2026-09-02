from typing_extensions import Annotated,TypedDict
from app.evaluation.metrics.llm_client import groq_model,nvidia_llm,ollama_model
from pydantic import BaseModel,Field

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


relevance_llm = groq_model.with_structured_output(RelevanceGrade,method="json_schema",strict=True).with_fallbacks([nvidia_llm.with_structured_output(RelevanceGrade,method="json_schema",strict=True),ollama_model.with_structured_output(RelevanceGrade,method="json_schema",strict=True)])


def relevance(inputs:dict,outputs: dict) -> bool:
    """Relevance Scoring For RAG Pipeline"""
    answer = f"Question: {inputs['question']}\n STUDENT ANSWER: {outputs['answer']}"
    grade = relevance_llm.invoke([
        {"role": "system", "content": relevance_instructions},
        {"role": "user","content": answer}
    ])
    return grade.is_relevant
