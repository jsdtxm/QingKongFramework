def model_object_to_name(model):
    return f"{model.app.label}.{model.__name__}"
