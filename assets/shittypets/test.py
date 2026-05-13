import gradio as gr

print("--- Gradio Diagnostic Test ---")
print(f"Reported Gradio Version: {gr.__version__}")

try:
    with gr.Blocks() as demo:
        # This is a minimal test of the feature that causes the error
        def test_function():
            return "Test"
        
        # We are testing if the 'every' keyword is accepted
        demo.load(fn=test_function, outputs=None, every=1)

    print("Modern Syntax Test ('every'): SUCCESSFUL")

except TypeError as e:
    print("Modern Syntax Test ('every'): FAILED")
    print(f"Error Message: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("--- End of Test ---")