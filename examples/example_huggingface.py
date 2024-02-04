import huggingface_hub

client = huggingface_hub.InferenceClient()
print(client.fill_mask("Hello I'm a <mask> model."))
print(client.translation("Translate: My name is Sarah and I live in London", model="t5-small"))