from langchain_groq import ChatGroq
from langchain_classic.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import FileChatMessageHistory

from config import Config
from vector_store import VectorDB
from prompts import get_qa_prompt, get_contextualize_prompt

class ChefBot:
    def __init__(self):
        self.vector_db = VectorDB()
        self.vector_db.ingest_if_empty()
        self.retriever = self.vector_db.get_store().as_retriever(search_kwargs={"k": 4})
        
        self.llm = ChatGroq(
            model_name=Config.LLM_MODEL,
            temperature=0.2,
            api_key=Config.GROQ_API_KEY
        )

        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, get_contextualize_prompt()
        )

        question_answer_chain = create_stuff_documents_chain(self.llm, get_qa_prompt())
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        self.chain = RunnableWithMessageHistory(
            rag_chain,
            self._get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    def _get_session_history(self, session_id: str):
        return FileChatMessageHistory(Config.HISTORY_FILE)

    def ask(self, query: str, session_id: str = "web_session"):
        response = self.chain.invoke(
            {"input": query},
            config={"configurable": {"session_id": session_id}}
        )
        return response.get("answer", "No response.")
