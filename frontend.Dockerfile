# Use the same base image for consistency
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the *root* requirements file
COPY requirements.txt .

# Install all dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire 'frontend' folder's contents into the container
COPY ./frontend /app

# Expose the default Streamlit port
EXPOSE 8501

# The command to run when the container starts
CMD ["streamlit", "run", "streamlit-app.py", "--server.port=8501", "--server.address=0.0.0.0"]