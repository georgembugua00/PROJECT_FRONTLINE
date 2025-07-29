# Use an official Python runtime as a parent image
# We're using a slim-bullseye image to keep the size down
FROM python:3.10-slim-bullseye
# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by some Python packages
# (e.g., FAISS might have underlying C/C++ dependencies, though faiss-cpu usually bundles them)
# This step is optional but can prevent common installation issues.

ENV PIP_DEFAULT_TIMEOUT=1000

# Copy the requirements.txt file into the working directory
COPY requirements.txt .

RUN pip install --upgrade pip

# Install any specified Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the working directory
# Ensure your main.py and any other necessary files are in the context where you build the Docker image
COPY . .

# Expose the port that Streamlit runs on (default is 8501)
EXPOSE 8501

# Command to run the Streamlit application
# Streamlit usually requires no-watch-dog-thread for Docker environments
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]