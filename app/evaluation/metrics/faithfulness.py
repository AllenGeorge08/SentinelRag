from typing_extensions import Annotated,TypedDict
from app.evaluation.metrics.llm_client import client 

class Faithfulness(TypedDict):
    explanation: Annotated[str,...,"Explain your reasoning for the score"]
    grounded: Annotated[bool,...,"Provide the score on if the given answer hallucinates from the documentation"]



faithfulness_instructions = """
You're a teacher grading a quiz.

You will be given FACTS and a STUDENT ANSWER.

Here is the grade criteria to follow:

1) Ensure the STUDENT ANSWER is grounded in the FACTS.
2) Ensure the STUDENT ANSWER does not contain "hallucinated" information outside the scope of the FACTS.

Grounded:

- A grounded value of True means that the student's answer meets all of the criteria.
- A grounded value of False means that the student's answer does not meet all of the given criteria.

Explain your reasoning in a step by step manner to ensure your reasoning and conclusion are correct.

Avoid simply stating the correct answer at the outset.

"""

faithfulness_llm = client.with_structured_output(Faithfulness,method="json_schema",strict=True)

def faithfulness(inputs: dict,outputs: dict) ->bool:
    """Evaluator to check RAG's Faithfulness metric"""
    doc_string = "\n\n".join(doc.page_content for doc in outputs["documents"])
    answer = f"FACTS: {doc_string}\nSTUDENT ANSWER: {outputs['answer']}"

    grade = faithfulness_llm.invoke([
    {
        "role": "system",
        "content": faithfulness_instructions
    },{
        "role": "user",
        "content": answer
    }])

    return grade["grounded"]