# 1. Start from an official Python image
FROM python:3.11-slim

# 2. Set the working folder
WORKDIR /app

# 3. Copy the requirements file
COPY requirements.txt .

# 4. Install all required Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the project files
COPY . .

# 6. Expose the application's port
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]

# 7. THE SAVED COMMAND FOR WEB BROWSER: http://localhost:8501

# 8.1 Build rag system: python build_database.py
# 8.2 to update the changes in docker:  docker build -t graduated-project .
# 8.2 then run : docker run -p 8501:8501 graduated-project
# 8.3 http://localhost:8501 in web browsers


