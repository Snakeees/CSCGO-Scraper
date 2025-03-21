# Use official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Ensure the logs directory exists
RUN mkdir -p /app/logs

# Expose port 5000 for Flask
EXPOSE 5000

# Run the Flask app
CMD ["sh", "-c", "python -u scheduler.py & gunicorn -b 0.0.0.0:5000 app:app --access-logfile '/app/logs/access.log' --error-logfile '/app/logs/error.log' --log-level 'debug'"]
