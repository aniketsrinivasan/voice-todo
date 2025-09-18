# MCP tooling using smolagents for use within agent.py 

from smolagents import Tool


class GenericTool(Tool):
    IS_DISABLED = True
    name: str = "generic_tool"
    description: str = "A tool defining the generic structure of a tool."
    inputs: dict = {
        "name": {
            "type": "The type of the input argument.",
            "description": "What the argument does."
        },
    }
    output_type: str = "object"

    def forward(self, name: str):
        """
        A tool defining the generic structure of a tool.
        """
        if self.IS_DISABLED:
            return f"The {self.name} tool is currently disabled."
        # Make the API call here, and return the response. 
        return f"Hello, {name}!"
