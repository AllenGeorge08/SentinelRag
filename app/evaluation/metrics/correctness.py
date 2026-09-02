from typing_extensions import Annotated,TypedDict
from app.evaluation.metrics.llm_client import groq_model,nvidia_llm,ollama_model
from pydantic import BaseModel,Field
import json 


class Correctness(BaseModel):
    #Helps model to reason before filling this schema
    explaination: str = Field(description="Explain your reasoning for the score")
    is_correct: bool  =  Field(description="True if the answer is correct, False otherwise")


correctness_instructions ="""

"Role" : You're a teacher grading a quiz.

Context: "You will be given a question , the ground truth(correct) answer, and the student answer.

Here's the grade criteria to follow:

1) Grade the student answers bassed only on their factual accuracy relative to the ground truth answer.
2) Ensure that the student answer does not contain and conflicting statements.
3) A response maybe factually correct but should be marked incorrect if it omits essential information required to fully answer the question.
4) Base your evaluation based on student answer and ground truth. Don't use external knowledge base.
5) Ignore differences in wording,sentence structure,or formatting . Focus only on factual equivalence.
6) If a student answers more than the ground truth answer, and it contains enough relevancy, treat it as factually correct to the ground truth answer.

Correctness:
- A correctness value of True means that the student's answer meets all of the criteria.
- A correctness value of False means that the student's answer does not meet all of the criteria.

Expain your reasoning for the sccores in a step by step manner to ensure your reasoning and conclusion are correct.

Avoid simply stating the correct answer at the outset.

"""



structure_llm = groq_model.with_structured_output(Correctness,method="json_schema",strict=True).with_fallbacks([nvidia_llm.with_structured_output(Correctness,method="json_schema",strict=True),ollama_model.with_structured_output(Correctness,method="json_schema",strict=True)])



def correctness(inputs: dict, outputs: dict,reference_outputs: dict) -> bool:
    """Evaluator for RAG Output Accuracy"""
    actual_answers = f"""\
    Question: {inputs['question']}
    Ground Truth Answer: {reference_outputs['answer']}
    Student Answer: {outputs['answer']}
    """
    result = structure_llm.invoke([
        ("system",correctness_instructions),
        ("user",actual_answers)
    ])

    return result.is_correct


    



    