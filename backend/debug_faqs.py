# Create: backend/debug_faqs.py
from sqlmodel import Session, select
from data.database import engine
from data.models.faq import Faq
import logging

logging.basicConfig(level=logging.INFO)

def check_faq_embeddings():
    with Session(engine) as session:
        faqs = session.exec(select(Faq)).all()
        
        print(f"Total FAQs in database: {len(faqs)}")
        
        for faq in faqs:
            embedding_length = len(faq.faq_embedding) if faq.faq_embedding else 0
            print(f"FAQ {faq.id}:")
            print(f"  Question: {faq.question}")
            print(f"  Enabled: {faq.is_enabled}")
            print(f"  Embedding length: {embedding_length}")
            print(f"  Expected length: 768")
            print(f"  Valid embedding: {embedding_length == 768}")
            print("---")

if __name__ == "__main__":
    check_faq_embeddings()
