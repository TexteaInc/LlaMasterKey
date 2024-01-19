import vectara

client = vectara.vectara()
print(client.query(1, "What is the purpose of the artist?", lang="en"))
