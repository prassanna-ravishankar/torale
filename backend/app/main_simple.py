from fastapi import FastAPI

app = FastAPI(title="Torale Backend - Simple Test")

@app.get("/")
async def root():
    return {"message": "Torale Backend is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "torale-backend-simple"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main_simple:app", host="0.0.0.0", port=8000) 