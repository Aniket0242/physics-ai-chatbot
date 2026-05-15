import os
import json
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

PDF_FOLDER = "data/ncert_pdfs"
OUTPUT_FOLDER = "data/ncert_index"
CHUNK_SIZE = 500

all_text = ""
for filename in os.listdir(PDF_FOLDER):
    if filename.endswith(".pdf"):
        path = os.path.join(PDF_FOLDER, filename)
        reader = PdfReader(path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                all_text += page_text + "\n"

chunks = []
current = ""
for line in all_text.split("\n"):
    if len(current) + len(line) < CHUNK_SIZE:
        current += line + " "
    else:
        chunks.append(current.strip())
        current = line + " "
if current:
    chunks.append(current.strip())

print(f"Extracted {len(chunks)} chunks from NCERT PDFs.")

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(chunks, show_progress_bar=True)

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings).astype('float32'))

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
faiss.write_index(index, os.path.join(OUTPUT_FOLDER, "ncert.index"))
with open(os.path.join(OUTPUT_FOLDER, "chunks.json"), "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False)

print(f"Saved FAISS index and {len(chunks)} chunks to {OUTPUT_FOLDER}")