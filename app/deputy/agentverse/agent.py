from uagents import Agent

from protocols import chat_protocol

agent = Agent()

agent.include(chat_protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
