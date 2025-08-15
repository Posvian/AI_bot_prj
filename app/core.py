import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import GigaChatEmbeddings
from langchain_community.chat_models import GigaChat

from app.links import LINKS
from app.models import APIResponse, QAResponse
from .utils import get_access_token

from .constants import VECTORSTORE_DIR, VECTORSTORE_PATH, HEADERS


access_token = get_access_token()


class QAService:
    def __init__(self):
        self.embeddings = GigaChatEmbeddings(
            access_token=access_token, verify_ssl_certs=False, model="EmbeddingsGigaR"
        )
        self.retriever = self._initialize_vector_store()
        self.llm = GigaChat(
            access_token=access_token,
            verify_ssl_certs=False,
            temperature=0.3,
            max_tokens=1000,
        )
        self.qa_chain = self._create_chain()

    def _initialize_vector_store(self):
        if VECTORSTORE_PATH.exists():
            db = FAISS.load_local(
                str(VECTORSTORE_PATH),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
        else:
            VECTORSTORE_DIR.mkdir(exist_ok=True)
            loader = WebBaseLoader(LINKS, header_template=HEADERS)
            data = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
            )
            texts = text_splitter.split_documents(data)
            db = FAISS.from_documents(texts, self.embeddings)
            db.save_local(str(VECTORSTORE_PATH))
        return db.as_retriever(search_kwargs={"k": 3})

    def _create_chain(self):

        prompt = ChatPromptTemplate.from_template(
            # """
            #     Ты — ассистент компании EORA, отвечаешь на вопросы о реализованных проектах.
            #     Отвечай ТОЛЬКО на основе предоставленного контекста. Будь конкретным и приводи примеры.
            #
            #     Формат ответа:
            #     1. Если вопрос о конкретном проекте — опиши его кратко и приведи ссылку [N] сразу после упоминания
            #     2. Если вопрос общий (типа "Что вы делали для ритейлеров?") — перечисли 2-3 примера через запятую со ссылками [N]
            #     3. Если информации нет — скажи "Не нашел relevantных проектов в базе"
            #
            #     Контекст:
            #     {context}
            #
            #     Вопрос: {question}
            #
            #     Пример хорошего ответа:
            #     "Для ритейлеров мы делали: бота для HR для Магнита [1], поиск по картинкам для KazanExpress [2]"
            #     """
            """
                Ты — ассистент компании EORA, который знает все о реализованных проектах.
                Отвечай на вопрос максимально конкретно, используя ТОЛЬКО предоставленные данные.
                При приведении примеров пиши названия заказчика.
    
                Обязательный формат ответа:
                1. Сначала краткий ответ на вопрос
                2. Затем "Например, мы делали [проект 1], а ещё [проект 2]"
                
    
                Контекст:
                {context}
    
                Вопрос: {question}
    
                Пример правильного ответа:
                Ответ: Мы разрабатываем AI-решения для автоматизации ритейла.
                Например, мы делали бота для HR для Магнита, а ещё поиск по картинкам для KazanExpress
                """
        )

        def format_docs(docs):
            formatted = []
            for i, doc in enumerate(docs):
                formatted.append(f"[Документ {i+1}]: {doc.page_content}")
                doc.metadata["index"] = i + 1
            return "\n\n".join(formatted), docs

        def format_answer_with_sources(input_dict):
            question = input_dict["question"]
            formatted_context, docs = input_dict["context"]
            answer = self.llm.invoke(
                prompt.format(question=question, context=formatted_context)
            )

            for doc in docs:
                if f"[{doc.metadata['index']}]" in answer:
                    answer = answer.replace(
                        f"[{doc.metadata['index']}]", f"[{doc.metadata['source']}]"
                    )
            return answer

        return (
            {
                "context": self.retriever | format_docs,
                "question": RunnablePassthrough(),
            }
            | RunnablePassthrough.assign(answer=format_answer_with_sources)
            | (
                lambda x: {
                    "answer": x["answer"],
                    "sources": list(set(d.metadata["source"] for d in x["context"][1])),
                }
            )
        )

    def ask_question_api(self, question: str) -> APIResponse:
        try:
            result = self.qa_chain.invoke(question)
            return APIResponse(
                response=QAResponse(
                    answer=(
                        result["answer"].content
                        if hasattr(result["answer"], "content")
                        else str(result["answer"])
                    ),
                    sources=result.get("sources", []),
                )
            )
        except Exception as e:
            return APIResponse(
                response=QAResponse(
                    answer=f"Ошибка при обработке запроса: {str(e)}", sources=[]
                )
            )
