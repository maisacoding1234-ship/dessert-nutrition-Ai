import faiss
import pickle

from sentence_transformers import SentenceTransformer


# =========================================================
# 1. Load Embedding Model
# =========================================================

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# =========================================================
# 2. Load FAISS Database
# =========================================================

index = faiss.read_index(
    "faiss_db/index.faiss"
)


# =========================================================
# 3. Load Dessert Documents
# =========================================================

with open(
    "faiss_db/desserts.pkl",
    "rb"
) as file:

    documents = pickle.load(file)


# =========================================================
# 4. Search RAG
# =========================================================

def search_rag(dessert_name, k=3):

    query = (
        f"Sugar information for {dessert_name}"
    )

    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True
    )

    query_embedding = query_embedding.astype(
        "float32"
    )

    distances, indices = index.search(
        query_embedding,
        k
    )

    results = []

    for i in indices[0]:

        if i != -1:
            results.append(
                documents[i]
            )

    return results


#====================temporary code==================

results = search_rag("mamoul")

for result in results:
    print(result)


    results = search_rag(
    "Kunafa",
    k=3
)

print("\nRAG RESULTS:")

for result in results:
    print(result)