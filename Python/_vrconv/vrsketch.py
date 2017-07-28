import document
from model import ModelStep


def load(filename):
    return document.VRSketchFile(filename).model


def save(model, filename):
    step = ModelStep(model, "Conversion")
    step.fe_add += model.all_edges()
    step.fe_add += model.all_faces()

    with open(filename, 'wb') as f:
        document.write_header(f)
        document.write_model_step(f, step)
