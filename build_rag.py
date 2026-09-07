import pandas as pd
import faiss
import pickle
import os

from sentence_transformers import SentenceTransformer


# =========================================================
# 1. Read Excel Dataset
# =========================================================

dessert_df = pd.read_excel("sugar_desserts.xlsx")


# =========================================================
# 2. Convert Excel Rows into Documents
# =========================================================

documents = []

for _, row in dessert_df.iterrows():

    document = (
        f"Dessert name: {row['Dessert_name']}. "
        f"Sugar per 100g: {row['Sugar_per_100g']} grams."
    )

    documents.append(document)


print("Number of dessert documents:", len(documents))


# =========================================================
# 3. Load Embedding Model
# =========================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# =========================================================
# 4. Create Embeddings
# =========================================================

print("Creating embeddings...")

embeddings = embedding_model.encode(
    documents,
    convert_to_numpy=True
)

embeddings = embeddings.astype("float32")


# =========================================================
# 5. Create FAISS Index
# =========================================================

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(embeddings)


print(
    "Number of vectors stored in FAISS:",
    index.ntotal
)


# =========================================================
# 6. Create FAISS Folder
# =========================================================

os.makedirs(
    "faiss_db",
    exist_ok=True
)


# =========================================================
# 7. Save FAISS Index
# =========================================================

faiss.write_index(
    index,
    "faiss_db/index.faiss"
)


# =========================================================
# 8. Save Dessert Documents
# =========================================================

with open(
    "faiss_db/desserts.pkl",
    "wb"
) as file:

    pickle.dump(
        documents,
        file
    )


print("RAG database created successfully!")