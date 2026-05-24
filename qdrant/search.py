from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "bank_support"
VECTOR_SIZE = 384

documents = [
    {
        "id": 1,
        "title": "Ошибка CRM",
        "text": "Система оформления кредитных заявок закрывается после открытия карточки клиента",
        "department": "credit",
        "category": "crm",
    },
    {
        "id": 2,
        "title": "Не печатается документ",
        "text": "После отправки договора на печать устройство не отвечает",
        "department": "operations",
        "category": "printing",
    },
    {
        "id": 3,
        "title": "Ошибка входа",
        "text": "Сотрудник не может войти в систему обработки платежей",
        "department": "finance",
        "category": "authentication",
    },
    {
        "id": 4,
        "title": "Проблема Outlook",
        "text": "Письма остаются в исходящих и не отправляются получателям",
        "department": "office",
        "category": "mail",
    },
    {
        "id": 5,
        "title": "Сбой документооборота",
        "text": "Система электронного согласования зависает при открытии вложений",
        "department": "legal",
        "category": "edms",
    },
    {
        "id": 6,
        "title": "Ошибка клиентского приложения",
        "text": "Приложение для оформления банковских продуктов аварийно завершается после авторизации",
        "department": "credit",
        "category": "crm",
    },
]

queries = [
    ("закрывается программа кредитов", {"crm"}, "обращения CRM"),
    ("не отправляется электронная почта", {"mail"}, "проблемы Outlook"),
    ("невозможно войти в платежную систему", {"authentication"}, "authentication"),
    ("зависает система согласования документов", {"edms"}, "EDMS"),
]


def prepare_text(doc: dict) -> str:
    return doc["text"]


def prepare_query(text: str) -> str:
    return text


def main():
    print("Loading embedding model...")
    model = TextEmbedding(model_name=MODEL_NAME)

    client = QdrantClient(host="localhost", port=6333)

    collections = client.get_collections()
    if any(c.name == COLLECTION_NAME for c in collections.collections):
        print(f"Recreating collection '{COLLECTION_NAME}'...")
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
    )
    print(f"Collection '{COLLECTION_NAME}' created.")

    texts = [prepare_text(doc) for doc in documents]
    print("Generating embeddings for documents...")
    doc_embeddings = list(model.embed(texts))

    print("Indexing documents into Qdrant...")
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=doc["id"],
                vector=emb.tolist(),
                payload=doc,
            )
            for doc, emb in zip(documents, doc_embeddings)
        ],
    )
    print(f"Indexed {len(documents)} documents.")

    print("\n" + "=" * 70)
    print("SEMANTIC SEARCH RESULTS")
    print("=" * 70)

    for query_text, expected_categories, expected_desc in queries:
        print(f"\n{'─' * 70}")
        print(f"Query: «{query_text}»")
        print(f"Expected: {expected_desc} (categories: {expected_categories})")
        print(f"{'─' * 70}")

        query_embedding = list(model.embed([prepare_query(query_text)]))[0]

        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding.tolist(),
            limit=3,
            with_payload=True,
            with_vectors=False,
        )

        for rank, hit in enumerate(results.points, 1):
            p = hit.payload
            category_match = p["category"] in expected_categories
            print(f"  #{rank} score={hit.score:.4f} [{p['category']}] — {p['title']}")
            print(f"      text: {p['text']}")
            if category_match:
                print(f"      ✓ match: semantic search found the correct document in category «{p['category']}»")

        print()


if __name__ == "__main__":
    main()
