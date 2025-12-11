import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageRole, FilePurpose, FunctionTool, FileSearchTool, ToolSet
from dotenv import load_dotenv
from tools import calculate_pizza_for_people

load_dotenv(override=True)

project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_CONNECTION_STRING"],
    credential=DefaultAzureCredential()
)

# Create the File Search tool
vector_store_id = "vs_K1rrNSP3GpHefT2u8bXChmYB"
file_search = FileSearchTool(vector_store_ids=[vector_store_id])

# Create a FunctionTool for the calculate_pizza_for_people function
function_tool = FunctionTool(functions={calculate_pizza_for_people})

# Create the toolset
toolset = ToolSet()
toolset.add(file_search)
toolset.add(function_tool)

# Enable automatic function calling for this toolset so the agent can call functions directly
project_client.agents.enable_auto_function_calls(toolset)

agent = project_client.agents.create_agent(
    model="gpt-4o",
    name="my-agent",
    instructions=open("instructions.txt").read(),
    top_p=0.75,
    temperature=0.7,
    toolset=toolset  # Add the toolset to the agentgit
)
print(f"Created agent with system prompt, ID: {agent.id}")

thread = project_client.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

try:
    while True:
        # Get the user input
        user_input = input("You: ")

        # Break out of the loop
        if user_input.lower() in ["exit", "quit"]:
            break

        # Add a message to the thread
        message = project_client.agents.messages.create(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=user_input
        )

        # Process the agent run
        run = project_client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id
        )

        # List messages and print the first text response from the agent
        messages = project_client.agents.messages.list(thread_id=thread.id)
        first_message = next(iter(messages), None)
        if first_message:
            print(next((item["text"]["value"] for item in first_message.content if item.get("type") == "text"), "")) 
finally:
    # Clean up the agent when done
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")