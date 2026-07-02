import pickle
import os
import sys
import json

docs_path = "data/vectorstore/documents.pkl"
if not os.path.exists(docs_path):
    docs_path = "../data/vectorstore/documents.pkl"

if os.path.exists(docs_path):
    with open(docs_path, 'rb') as f:
        documents = pickle.load(f)
    print(f"Total chunks in vector store: {len(documents)}")
    for idx, doc in enumerate(documents, 1):
        print(f"\n--- Chunk {idx} ---")
        print(f"ID: {doc['id']}")
        print(f"Source: {doc['source']}")
        print(f"Text Content:\n{doc['text']}")
        print("-" * 30)
else:
    print("No documents.pkl file found.")
