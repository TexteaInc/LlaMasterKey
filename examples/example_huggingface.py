import huggingface_hub

client = huggingface_hub.InferenceClient()
#print(client.fill_mask("Hello I'm a <mask> model."))
print(client.translation("Llamakey: one master key for many cloud AI APIs.", model="t5-small"))
