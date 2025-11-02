from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import deals_router, interview_router, interviews 

app = FastAPI(title="AI Startup Analyst API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(deals_router)
app.include_router(interview_router)
app.include_router(interviews.router) 

@app.get("/health")
async def health_check():
    from datetime import datetime
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
