import vectara

client = vectara.vectara()

corpus_id = client.create_corpus("lmk test corpus")

client.upload(corpus_id, "../../README.md", description="LlaMasterKey README.md")

result = client.query(corpus_id, "What is LlaMasterKey?", top_k=5)
print(result)

client.reset_corpus(corpus_id)
