from mcp.server import MCPServer

from data.customers import (
    get_customer_annual_spend,
    get_customer_list,
    get_customer_office_locations,
)


CUSTOMER_SCHEMA = """# Customer data

* `id` (integer): the customer's unique ID.
* `name` (string): the customer's name.
* `annual_spend` (integer): the customer's annual spend in GBP.
* `offices_in` (list of strings): ISO 3166-1 alpha-2 country codes for the
  countries where the customer has offices.
"""


# Exercise - Writing an MCP Server
#
# In this exercise, you will provide multiple tools to an LLM through an MCP
# server.
#
# The server currently exposes only one tool: customer office locations. The
# other two data functions are imported above, but are not exposed as tools.
#
# 1. Define `tool_get_customer_annual_spend(customer_id: int) -> int` and expose
#    it as a tool. It should return the annual spend for a customer.
# 2. Define `tool_get_customer_list() -> list[dict]` and expose it as a tool. It
#    should return the list of customers.
# 3. Give both tools a clear description using a docstring.
#
# Once you have reconnected the server in Claude Code, try questions such as:
#
# * How many high-value customers (spending more than 1 million a year) are
#   there?
# * Which customers have offices in Europe?
# * Which customers have offices in the US and spend more than 2 million a year?
# * Which countries do high-value customers (spending more than 1 million a
#   year) have offices in?

mcp = MCPServer("Customer MCP")


@mcp.tool()
def tool_get_customer_office_locations(customer_id: int) -> list[str]:
    """Get the country codes where a customer has an office."""
    return get_customer_office_locations(customer_id)


# Exercise - Resources and Prompts
#
# 1. Expose CUSTOMER_SCHEMA as a text/markdown resource at `customer://schema`.
#    Give the resource a clear description using a docstring.
#
# 2. Define a prompt named `customer_report` with one string parameter,
#    `customer_name`. It should tell the model to:
#
#    * find a unique exact name match using the customer list tool;
#    * stop and ask for clarification if there is no unique match;
#    * retrieve that customer's annual spend and office locations;
#    * use the customer schema resource to interpret those values;
#    * produce a concise Markdown report containing the customer's name, ID,
#      annual spend and office countries; and
#    * avoid claims that are not supported by the customer data.
#
#    Return the prompt as a string. Use the function's docstring to explain what
#    the prompt does.


if __name__ == "__main__":
    mcp.run()
