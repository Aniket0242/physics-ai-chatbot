import os
import json
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Process both NCERT and board papers
PDF_FOLDERS = ["data/ncert_pdfs", "data/board_papers"]
OUTPUT_FOLDER = "data/ncert_index"
CHUNK_SIZE = 500

all_text = ""
for folder in PDF_FOLDERS:
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if filename.endswith(".pdf"):
                path = os.path.join(folder, filename)
                print(f"Processing: {path}")
                reader = PdfReader(path)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        all_text += page_text + "\n"

# Split into chunks
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

print(f"Extracted {len(chunks)} chunks from all PDFs.")

# Create embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(chunks, show_progress_bar=True)

# Build FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings).astype('float32'))

# Save index and chunks
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
faiss.write_index(index, os.path.join(OUTPUT_FOLDER, "ncert.index"))
with open(os.path.join(OUTPUT_FOLDER, "chunks.json"), "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False)

print(f"✅ Saved FAISS index and {len(chunks)} chunks to {OUTPUT_FOLDER}")