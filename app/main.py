from fastapi import FastAPI,Request,status
from app.api.routers import auth_routers,pdf_routers,rag_routers
from app.database.connection import engine
from app.database.base import Base
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware







app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:5174",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    # "https://your-production-app.render.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Allow these specific origins
    allow_credentials=True,         # Allow cookies and auth headers
    allow_methods=["*"],            # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],            # Allow all headers
)

@app.exception_handler(RequestValidationError)
async def validate_exception_handler(request:Request,exception:RequestValidationError):
    custom_errors=[]

    for errors in exception.errors():
        field = errors['loc'][-1]
        message = errors['msg']

        custom_message = f'The give Input for the {field} has {message}'
        custom_errors.append(custom_message)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "status": "error",
            "message": "Validation failed",
            "errors": custom_errors
        },
    )

app.include_router(auth_routers.router)
app.include_router(pdf_routers.router)
app.include_router(rag_routers.router)



# for auto migration after running the server
Base.metadata.create_all(bind=engine)