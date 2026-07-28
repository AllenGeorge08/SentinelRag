from typing_extensions import Annotated,TypedDict
from app.evaluation.metrics.llm_client import client
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json 


class Correctness(TypedDict):
    #Helps model to reason before filling this schema
    explaination: Annotated[str,...,"Explain your reasoning for the score"]
    is_correct: Annotated[bool,...,"True if the answer is correct, False otherwise"]


parser = JsonOutputParser(pydantic_object=Correctness)


correctness_instructions ="""

"Role" : You're a teacher grading a quiz.

Context: "You will be given a question , the ground truth(correct) answer, and the student answer.

Here's the grade criteria to follow:

1) Grade the student answers bassed only on their factual accuracy relative to the ground truth answer.
2) Ensure that the student answer does not contain and conflicting statements.
3) A response maybe factually correct but should be marked incorrect if it omits essential information required to fully answer the question.
4) Base your evaluation based on student answer and ground truth. Don't use external knowledge base.
5) Ignore differences in wording,sentence structure,or formatting . Focus only on factual equivalence.
6) If a student answers more than the ground truth answer, and it contains enough relevancy, as it is factually correct to the ground truth answer.

Correctness:
- A correctness value of True means that the student's answer meets all of the criteria.
- A correctness value of False means that the student's answer does not meet all of the criteria.

Expain your reasoning for the sccores in a step by step manner to ensure your reasoning and conclusion are correct.

Avoid simply stating the correct answer at the outset.

"""

correctness_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name":"correctness",
        "schema": {
            "type": "object",
            "properties": {
                "explaination": {"type": "string"},
                "is_correct": {"type": "boolean"}
            },
            "required": ["explaination","is_correct"]
        }
    }
}


structure_llm = client.with_structured_output(Correctness)

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

    return result["is_correct"]


    



    