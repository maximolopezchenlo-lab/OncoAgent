import gradio as gr

def test_fn(x):
    return f"Test: {x}"

with gr.Blocks() as demo:
    btn = gr.Button("↑", variant="primary", size="sm")
    # Checking if gr.Textbox accepts 'buttons'
    try:
        txt = gr.Textbox(placeholder="Testing buttons param...", buttons=[btn])
        print("Success: gr.Textbox accepts 'buttons' parameter.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # We don't launch, just check initialization
    pass
