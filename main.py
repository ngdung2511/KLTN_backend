from fastapi import FastAPI, Request
from .mvc.controller import question_bank, test_bank, category, answer_sheet, login
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add middleware to print request origins for debugging
@app.middleware("http")
async def log_request_origin(request: Request, call_next):
    origin = request.headers.get("origin", "No origin")
    print(f"Request from origin: {origin}")
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.2.19:3000"],  # Add your frontend URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)
app.include_router(question_bank.router)
app.include_router(test_bank.router)
app.include_router(category.router)
app.include_router(answer_sheet.router)
app.include_router(login.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}