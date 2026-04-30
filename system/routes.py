from starlette.requests import Request
from starlette.responses import JSONResponse

async def post_prompt(request: Request) -> JSONResponse:
    """Send prompt to the agent and return the response."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON format"}, status_code=400)
    user_prompt = data.get("prompt")
    if not user_prompt:
        return JSONResponse({"error": "Missing 'prompt' key"}, status_code=422)
    result = await request.app.state.agent.run(user_prompt)
    return JSONResponse({
        "result": result.output,
    })


async def post_config(request: Request) -> JSONResponse:
    """Get agent configuration"""
    return JSONResponse(request.app.state.config)
