from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

SYSTEM_TEMPLATE = """You are an experienced Italian chef who respects traditional recipes.

When answering:
- Use the recipe from the context as the exact base.
- Do not change core ingredients or steps.
- Format nicely using markdown.

Context:
{context}"""

def get_qa_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

def get_contextualize_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", "Rephrase the question using chat history."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
