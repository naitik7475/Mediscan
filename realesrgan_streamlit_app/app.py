import streamlit as st
import subprocess
import os
import time

st.title("Medical Image Upscaling Using GAN")

# --- Display Example Images ---
st.subheader("Example Images (DOWNLOAD THESE AND THEN UPLOAD THEM), SCROLL DOWN TO SEE THE OUTPUT!!")
# Example Image Links (Imgur - Direct Links)
example_image_links = [
    "https://i.imgur.com/gvshlGZ.png",
    "https://i.imgur.com/Nw4igau.png",
    "https://i.imgur.com/0maZl8Q.png",
    "https://i.imgur.com/4x36UMB.png"
]

# Initialize session state for selected example
if 'selected_example_path' not in st.session_state:
    st.session_state.selected_example_path = None

cols = st.columns(4)
button_clicked = False
for i, img_link in enumerate(example_image_links):
    with cols[i]:
        st.image(img_link, caption=f"Example {i+1}", use_container_width=True)

st.divider() # Add a visual separator

# --- Main Uploader Section ---
# Use session state to persist uploaded file across reruns caused by button clicks
if 'uploaded_file_state' not in st.session_state:
    st.session_state.uploaded_file_state = None

uploaded_file = st.file_uploader("Choose an image to enhance...", type=["jpg", "jpeg", "png"], key="file_uploader")

# Update session state if a new file is uploaded
if uploaded_file is not None:
    st.session_state.uploaded_file_state = uploaded_file
    # Clear selected example if a file is uploaded
    st.session_state.selected_example_path = None

# Define temp directory names (used later if uploading)
temp_dir = "temp_input"
output_dir = "temp_output"

# Determine the input path for processing
input_path_for_processing = None
is_example = False

if st.session_state.selected_example_path:
    input_path_for_processing = st.session_state.selected_example_path
    is_example = True
elif st.session_state.uploaded_file_state:
    # Process the uploaded file stored in session state
    uploaded_file_data = st.session_state.uploaded_file_state
    temp_dir = "temp_input"
    os.makedirs(temp_dir, exist_ok=True)
    # Use the name from the uploaded file data
    input_path = os.path.join(temp_dir, uploaded_file_data.name)
    input_path_for_processing = input_path

    # Save the uploaded file data
    with open(input_path, "wb") as f:
        f.write(uploaded_file_data.getbuffer())

# --- Processing Section (if input is selected) ---
if input_path_for_processing:
    st.text("Processing, scroll down to see the results!")
    st.subheader("Processing")
    # Create columns for side-by-side display
    col1, col2 = st.columns(2)

    with col1:
        st.image(input_path_for_processing, caption="Original Image", use_container_width=True)

    # Placeholder for the second column until image is processed
    output_placeholder = col2.empty()
    output_placeholder.write("Enhancing image... Please wait.")

    # Define output path (relative to script) using the predefined name
    os.makedirs(output_dir, exist_ok=True)
    # Generate output filename based on input path
    base_filename = os.path.basename(input_path_for_processing)
    output_filename = "enhanced_" + base_filename
    output_path = os.path.join(output_dir, output_filename)

    # Construct the command
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # Use absolute path for the selected input (example or uploaded temp file)
    cmd_input_path = os.path.abspath(input_path_for_processing)
    cmd_output_path = os.path.abspath(output_path)
    executable_path = os.path.join(parent_dir, "realesrgan-ncnn-vulkan")

    command = [
        executable_path,
        "-i", cmd_input_path,
        "-o", cmd_output_path,
        "-n", "realesrgan-x4plus" # Use the specified model
    ]

    try:
        # Execute the command. No cwd needed as we use absolute paths.
        # The executable should find models/DLLs in its own directory (parent).
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        st.text("Command Output:")
        st.text(process.stdout)
        st.text(process.stderr)

        # Check if the output file was created (use original relative path for checking/displaying)
        if os.path.exists(output_path):
            # Display enhanced image in the second column
            with output_placeholder.container(): # Use container to replace the placeholder
                 st.image(output_path, caption="Enhanced Image (x4plus)", use_container_width=True)
                 st.success("Image enhanced successfully!")

            # Provide a download link for the enhanced image (use original relative path) - place below columns
            with open(output_path, "rb") as f:
                st.download_button(
                    label="Download Enhanced Image",
                    data=f,
                    file_name=output_filename,
                    mime="image/png" # realesrgan outputs png by default
                )
        else:
             with output_placeholder.container():
                 st.error("Error: Enhanced image file not found.")
                 st.text("Please check the command output above for details.")

    except subprocess.CalledProcessError as e:
        st.error(f"Error executing Real-ESRGAN: {e}")
        st.text("Command Output:")
        st.text(e.stdout)
        st.text(e.stderr)
    except FileNotFoundError:
        st.error("Error: realesrgan-ncnn-vulkan.exe not found or failed to execute.")
        st.text(f"Attempted to run '{executable_path}'. Ensure it exists and required DLLs are present in the same directory.")
    finally:
        # Clean up temporary files and directories (use original relative paths)
        # Add a small delay to ensure files are not in use before deletion
        time.sleep(0.1)
        # Only clean up if it was an uploaded file (not an example)
        if not is_example and input_path_for_processing and os.path.exists(input_path_for_processing):
             os.remove(input_path_for_processing) # Remove the temp input file
        if os.path.exists(output_path):
             os.remove(output_path) # Always remove the temp output file
        # Clean up temp directories if empty
        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
             os.rmdir(temp_dir)
        if os.path.exists(output_dir) and not os.listdir(output_dir):
             os.rmdir(output_dir)

# Add a clear button maybe?
if st.button("Clear Selection"):
    st.session_state.selected_example_path = None
    st.session_state.uploaded_file_state = None
    # Force rerun to clear the processing section
    st.rerun()
