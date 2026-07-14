from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from starlette.concurrency import iterate_in_threadpool
from dotenv import load_dotenv

load_dotenv()

from crewai import LLM
from crewai.utilities.streaming import (
    StreamChunk,
    StreamChunkType
)

import uvicorn

app = FastAPI()


@app.get("/chunk")
async def stream():

    llm = LLM(
        model="gpt-4o-mini",
    )

    response = llm.stream(
        "Explain SSE in simple words",
    )

    def generator():

        for chunk in response:

            if isinstance(chunk, StreamChunk):

                if chunk.chunk_type == StreamChunkType.TEXT:

                    token = chunk.content

                    # terminal output
                    print(token, end="", flush=True)

                    # curl output
                    yield token.encode("utf-8")

        print("\nDONE")

    return StreamingResponse(
        iterate_in_threadpool(generator()),
        media_type="text/plain"
    )


if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )