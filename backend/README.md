# AgriSense AI — Backend Service

The backend of **AgriSense AI** provides the core RESTful API services that power the farm advisory platform. It is built with **FastAPI**, a modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints.

---

## 🎯 Purpose of the Backend

In subsequent phases, this backend service will:
- Ingest farmer query parameters (location coordinates, acreage, season, soil data).
- Interface with satellite data providers and weather observation APIs.
- Execute machine learning inference pipelines to evaluate crop suitability.
- Compute environmental risk factors and generate actionable advisory reports.
- Serve validated JSON responses to the frontend client.

For **Phase 1**, the backend establishes the foundational application structure, dependency management, and core health monitoring endpoints.

---

## ⚡ Current Endpoints

| Method | Endpoint | Description | Sample Response |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | API Root / Welcome Message | `{"message": "Welcome to AgriSense AI API"}` |
| `GET` | `/health` | Service Health & Readiness Probe | `{"status": "healthy"}` |
| `GET` | `/docs` | Interactive Swagger UI API Docs | Interactive UI |
| `GET` | `/redoc` | Interactive ReDoc API Docs | Interactive UI |

---

## 💻 Getting Started (Windows PowerShell)

Follow these steps in **Windows PowerShell** to set up and run the backend locally.

### 1. Navigate to the Backend Directory
Open PowerShell in the project root and navigate to the `backend/` folder:
```powershell
cd backend
```

### 2. Create a Python Virtual Environment
Create a dedicated virtual environment named `.venv`:
```powershell
python -m venv .venv
```

> **Note on PowerShell Script Execution**: If your system restricts running scripts, allow script execution for the current PowerShell process:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

### 3. Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
*(Your prompt will indicate `(.venv)` when successfully activated).*

### 4. Install Dependencies
Install the required packages from `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### 5. Run the Development Server
Start the FastAPI server using Uvicorn with hot-reload enabled:
```powershell
uvicorn app.main:app --reload
```

The server will initialize on `http://127.0.0.1:8000`.

---

## 🔍 Testing the Endpoints

Once the server is running, open your web browser or use PowerShell to test the endpoints:

1. **Root Endpoint**:
   - URL: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - PowerShell: `curl http://127.0.0.1:8000/` or `Invoke-RestMethod http://127.0.0.1:8000/`
   - Expected Output:
     ```json
     {
       "message": "Welcome to AgriSense AI API"
     }
     ```

2. **Health Check Endpoint**:
   - URL: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
   - PowerShell: `Invoke-RestMethod http://127.0.0.1:8000/health`
   - Expected Output:
     ```json
     {
       "status": "healthy"
     }
     ```

3. **Interactive Swagger Documentation**:
   - URL: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Explore and execute API requests directly from the browser interface.

4. **Alternative ReDoc Documentation**:
   - URL: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
