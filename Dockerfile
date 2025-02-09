# Use official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose port 5000 for Flask
EXPOSE 5000

# Run the Flask app
CMD ["sh", "-c", "python scraper.py && gunicorn -b 0.0.0.0:5000 app:app"]
