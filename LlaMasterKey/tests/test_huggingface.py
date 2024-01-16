import huggingface_hub

client = huggingface_hub.InferenceClient()
print(client.fill_mask("Hello I'm a <mask> model."))
