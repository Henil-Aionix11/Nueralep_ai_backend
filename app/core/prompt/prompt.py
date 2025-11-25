CONTEXTUAL_PROMPT = """
Given a chat history and the latest follow-up question, determine if the question needs reformulation to be understood without context. If it does, create a standalone version. If not, return it unchanged.

Do not answer the question, just reformulate it if needed otherwise return it as is.

Only reformulate the follow-up question if it does not make sense without the chat history.

Guidelines:
1. Analyze if the follow-up question contains references (e.g., pronouns, demonstratives) that rely on the chat history.
2. Check if the question assumes knowledge from previous exchanges.
3. If reformulation is needed, create a concise standalone question that incorporates necessary context.
4. If it is already standalone, return the question exactly as provided, without adding any extra text.
"""