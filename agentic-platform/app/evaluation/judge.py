def evaluate_answer(answer, context):

    if context and context not in answer:
        return "low_grounding"

    return "ok"
