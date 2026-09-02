
from app.evaluation.metrics.llm_client import groq_model,nvidia_llm,ollama_model

from pydantic import BaseModel,Field

class Faithfulness(BaseModel):
    explanation: str = Field(description="Explain your reasoning for the score")
    grounded: str = Field(description="Provide the score on if the given answer hallucinates from the documentation")


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

faithfulness_llm = groq_model.with_structured_output(Faithfulness,method="json_schema",strict=True).with_fallbacks([nvidia_llm.with_structured_output(Faithfulness,method="json_schema",strict=True),ollama_model.with_structured_output(Faithfulness,method="json_schema",strict=True)])

def faithfulness(inputs: dict,outputs: dict) ->bool:
    """Evaluator to check RAG's Faithfulness metric"""
    points = outputs["documents"].points
    doc_string = "\n\n".join(p.payload["text"] for p in points if p.payload and p.payload.get("text"))
    answer = f"FACTS: {doc_string}\nSTUDENT ANSWER: {outputs['answer']}"

    grade = faithfulness_llm.invoke([
    {
        "role": "system",
        "content": faithfulness_instructions
    },{
        "role": "user",
        "content": answer
    }])

    return grade.grounded