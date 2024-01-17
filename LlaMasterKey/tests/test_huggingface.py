import huggingface_hub

client = huggingface_hub.InferenceClient()
print(client.fill_mask("Hello I'm a <mask> model."))
print(client.translation("My name is Sarah and I live in London", model="t5-small"))
print(client.text_generation("I am a ", model="NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO"))