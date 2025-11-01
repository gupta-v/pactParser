# Use a standard, slim Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the *root* requirements file into the container
COPY requirements.txt .

# Install all dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire 'backend' folder's contents into the container's /app/ dir
COPY ./backend /app
