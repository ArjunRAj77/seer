# Use Python 3.9 base image
FROM python:3.9

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory in the container
WORKDIR /app

# Copy requirements.txt to the working directory
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit app file into the container
COPY seer.py .

# Expose the port your Streamlit app runs on
EXPOSE 8501

# Set the entrypoint and default command for the container
ENTRYPOINT ["streamlit", "run", "seer.py"]