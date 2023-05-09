FROM python:3.9

RUN apt-get update && apt-get -y install libcgal-dev pybind11-dev

# TODO mkdir build
# cmake ..
# make
# what else?

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Expose port 5000 for the Flask API
EXPOSE 5000

# Start the Flask application
CMD ["python", "app.py"]
