from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from crewai import Agent, Task, Crew, LLM
from crewai.events import BaseEventListener, LLMStreamChunkEvent
from dotenv import load_dotenv
import asyncio
import uvicorn

app = FastAPI()
load_dotenv()

@app.get("/stream")
async def stream():

    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    class MyStreamListener(BaseEventListener):

        def setup_listeners(self, crewai_event_bus):

            @crewai_event_bus.on(LLMStreamChunkEvent)
            def on_llm_stream_chunk(source, event):

                chunk = event.chunk

                # terminal print
                print(chunk, end="", flush=True)

                # send same chunk to curl response
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    chunk
                )

    listener = MyStreamListener()

    async def run_crew():

        llm = LLM(
            model="gpt-4o-mini",
            stream=True
        )

        agent = Agent(
            role="Assistant",
            goal="Help users",
            backstory="AI Assistant",
            llm=llm
        )

        task = Task(
            description="Explain SSE in simple words",
            expected_output="Simple answer",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task]
        )

        await asyncio.to_thread(crew.kickoff)

        loop.call_soon_threadsafe(
            queue.put_nowait,
            None
        )

    asyncio.create_task(run_crew())

    async def generate():

        while True:

            chunk = await queue.get()

            if chunk is None:
                break

            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


if __name__ == "__main__":

    uvicorn.run(
        "StreaminTest:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )