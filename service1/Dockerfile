# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy all files from the context to the working directory
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir flask requests redis

# Set the default command (optional)
CMD ["python3", "app.py"]
