import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from conhecimento.storage.db import DATABASE_URL, engine
from conhecimento.models.document import Document

logging.basicConfig(level=logging.INFO)

print('Connecting to:', DATABASE_URL)
session = Session(engine)
docs = session.query(Document).all()
print(f'\nTotal docs ingeridos no banco: {len(docs)}\n')

for doc in docs:
    print(f'-> ID: {doc.id}')
    print(f'   Source: {doc.source}')
    print(f'   Metadata: {doc.metadata_}')
    print(f'   Text Preview: {doc.content[:100]}...\n')
    print(f'   Embedding: {len(doc.embedding)} dimensoes\n')

session.close()
