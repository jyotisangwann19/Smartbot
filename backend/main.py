import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chatbot
import database

# Initialize the database on startup
database.init_db_if_not_exists()

app = FastAPI()

# CORS middleware
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chatbot.router)

# This block is typically for running the script directly, which is not how
# FastAPI is usually run with uvicorn. It's left here but the main way
# to run the app is with `uvicorn main:app --reload`.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 
