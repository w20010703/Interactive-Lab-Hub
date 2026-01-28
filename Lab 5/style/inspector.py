from tflite_runtime.interpreter import Interpreter
import numpy as np

model_path = "style_transform.tflite"
interp = Interpreter(model_path)
interp.allocate_tensors()

print("Input Tensors:")
for i, d in enumerate(interp.get_input_details()):
    print(f"  [{i}] name: {d['name']}, shape: {d['shape']}, dtype: {d['dtype']}")

print("\nOutput Tensors:")
for i, d in enumerate(interp.get_output_details()):
    print(f"  [{i}] name: {d['name']}, shape: {d['shape']}, dtype: {d['dtype']}")
