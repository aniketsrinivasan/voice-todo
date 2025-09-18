# Agentic To-Do List App

## Functionality/Features
- users should be able to add to-do list items with the following information:
    - description: some description of the to-do list entry
    - priority: low/med/high
    - category: users can define categories and categorize their entries accordingly; none by default. multiple categories/tags should be allocatable to each entry
    - transcription: if the to-do entry was created by voice, add a transcription
    - time created 
    - time due 
    - time edited/updated (if applicable)
    - we'll internally generate metadata that is hidden to the user 
- users should be able to create to-do entries using voice commands; the backend should transcribe the user natural language entry and convert it to a to-do entry accordingly. 
- we have agentic workflows within our to-do app:
    - users can voice query for to-do entries (e.g. "what's due this week?" -> agentic AI process the query, queries the database, and returns a meaningful response)
    - users can voice edit (e.g. "edit the to-do task for finishing laundry to tomorrow")
    - users can voice delete 
- users should have the option to also use manual entry/editing/querying for all the above functions, as opposed to using voice 


## Backend Components 
database: Supabase (SQL-like) for storage of to-do entries. 
agent.py: smolagents wrapper of llm.py that integrates the tools in mcp_tools for agentic tool-calling capabilities.
llm.py: LLM wrapper (e.g. OpenAI)
voice.py: voice transcription service (wrapper around OpenAI whisper)


# Backend Architecture for Application:
- FastAPI application/endpoints to wrap the backend functionality and microservices, which the frontend will use to communicate 
- Supabase for database operations 
