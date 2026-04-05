import time
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from langchain_community.document_loaders import JSONLoader
from config import Config

class VectorDB:
    def __init__(self):
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.embeddings = PineconeEmbeddings(model=Config.EMBEDDING_MODEL)
        self._ensure_index()
        
    def _ensure_index(self):
        if Config.INDEX_NAME not in self.pc.list_indexes().names():
            print(f"Creating index: {Config.INDEX_NAME}...")
            self.pc.create_index(
                name=Config.INDEX_NAME,
                dimension=1024,
                metric="cosine",
                spec=ServerlessSpec(cloud=Config.CLOUD, region=Config.REGION)
            )
            while not self.pc.describe_index(Config.INDEX_NAME).status['ready']:
                time.sleep(1)

    def get_store(self):
        return PineconeVectorStore(
            index_name=Config.INDEX_NAME,
            embedding=self.embeddings,
            namespace=Config.NAMESPACE,
            text_key="chunk_text"
        )

    def ingest_if_empty(self):
        index = self.pc.Index(Config.INDEX_NAME)
        if index.describe_index_stats().get('total_vector_count', 0) == 0:
            print("Index empty. Ingesting data...")
            loader = JSONLoader(
                file_path=Config.JSON_DATA_PATH,
                jq_schema='.[]',
                content_key="chunk_text"
            )
            docs = loader.load()
            self.get_store().add_documents(docs, namespace=Config.NAMESPACE)
            print(f"✅ Ingestion complete! {len(docs)} chunks added.")
        else:
            print("✅ Index already populated.")
