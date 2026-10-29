from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import math

app = FastAPI(title="Math API", version="1.0.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors, simplifying only those with non-finite values."""
    import json
    errors = exc.errors()
    try:
        json.dumps({"detail": errors})
        return JSONResponse(status_code=422, content={"detail": errors})
    except ValueError:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid input: check that all numeric values are finite"},
        )


class NumberOperation(BaseModel):
    a: float = Field(allow_inf_nan=False)
    b: float = Field(allow_inf_nan=False)


class Result(BaseModel):
    result: float
    operation: str


def validate_finite_result(result: float, operation: str) -> dict:
    """Validate that the result is a finite float, raise 422 if not."""
    if not math.isfinite(result):
        raise HTTPException(status_code=422, detail=f"Result out of range for {operation}")
    return {"result": result, "operation": operation}


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}


@app.post("/add", response_model=Result, tags=["operations"])
async def add(operation: NumberOperation):
    """Addition: a + b"""
    result = operation.a + operation.b
    return validate_finite_result(result, "addition")


@app.post("/subtract", response_model=Result, tags=["operations"])
async def subtract(operation: NumberOperation):
    """Subtraction: a - b"""
    result = operation.a - operation.b
    return validate_finite_result(result, "subtraction")


@app.post("/multiply", response_model=Result, tags=["operations"])
async def multiply(operation: NumberOperation):
    """Multiplication: a * b"""
    result = operation.a * operation.b
    return validate_finite_result(result, "multiplication")


@app.post("/divide", response_model=Result, tags=["operations"])
async def divide(operation: NumberOperation):
    """Division: a / b"""
    if operation.b == 0:
        raise HTTPException(status_code=400, detail="Division by zero is not allowed")
    result = operation.a / operation.b
    return validate_finite_result(result, "division")


@app.post("/power", response_model=Result, tags=["operations"])
async def power(operation: NumberOperation):
    """Power: a ** b"""
    if operation.a < 0 and not float(operation.b).is_integer():
        raise HTTPException(status_code=400, detail="Cannot raise negative number to fractional power")
    try:
        result = operation.a ** operation.b
    except (ZeroDivisionError, OverflowError):
        raise HTTPException(status_code=400, detail="Power operation resulted in undefined value")
    return validate_finite_result(result, "power")


@app.post("/modulo", response_model=Result, tags=["operations"])
async def modulo(operation: NumberOperation):
    """Modulo: a % b"""
    if operation.b == 0:
        raise HTTPException(status_code=400, detail="Modulo by zero is not allowed")
    result = operation.a % operation.b
    return validate_finite_result(result, "modulo")


class SingleNumber(BaseModel):
    value: float = Field(allow_inf_nan=False)


@app.post("/square-root", response_model=Result, tags=["operations"])
async def square_root(operation: SingleNumber):
    """Square root: sqrt(value)"""
    if operation.value < 0:
        raise HTTPException(status_code=400, detail="Cannot compute square root of negative number")
    result = math.sqrt(operation.value)
    return validate_finite_result(result, "square_root")


@app.post("/absolute", response_model=Result, tags=["operations"])
async def absolute(operation: SingleNumber):
    """Absolute value: abs(value)"""
    result = abs(operation.value)
    return validate_finite_result(result, "absolute")


if __name__ == "__main__":
    import os
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)
