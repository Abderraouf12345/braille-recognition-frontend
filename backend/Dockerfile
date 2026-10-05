# Use a lightweight python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /code

# Copy the requirements file into the container
COPY ./requirements.txt /code/requirements.txt

# Install dependencies (CPU PyTorch is specified in requirements.txt)
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Create a non-root user (Hugging Face Spaces requirement)
RUN useradd -m -u 1000 user

# Switch to the non-root user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Change the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the rest of the application code
COPY --chown=user . $HOME/app

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Command to run the application
# python -u: unbuffered stdout so logs appear immediately in HF
# app.py uses demo.launch() which is required for ZeroGPU detection
CMD ["python", "-u", "app.py"]

