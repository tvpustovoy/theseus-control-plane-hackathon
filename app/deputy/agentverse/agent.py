from uagents import Agent

from protocols import chat_protocol
from http_client import read_memory

agent = Agent()

agent.include(chat_protocol, publish_manifest=True)

@agent.on_event("startup")
async def connection_diagnostic(ctx):
    result = read_memory()
    ctx.logger.info("ATLAS_MEMORY_STATUS connected=" + str(result.get("connected"))
                    + " count=" + str(result.get("record_count"))
                    + " error=" + str(result.get("error"))
                    + " type=" + str(result.get("error_type")))

if __name__ == "__main__":
    agent.run()
