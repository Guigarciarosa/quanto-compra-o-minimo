"""Servidor MCP (stdio): expõe o warehouse e o RAG para Claude Desktop, Claude Code ou qualquer cliente MCP."""
import os

from mcp.server.mcpserver import MCPServer

from . import tools

mcp = MCPServer("quanto-compra-o-minimo")


@mcp.tool()
def consultar_sql(sql: str) -> str:
    """Roda um SELECT somente leitura no DuckDB com salário mínimo, gasolina (ANP) e Big Mac."""
    return tools.consultar_sql(sql)


@mcp.tool()
def buscar_documentos(pergunta: str, k: int = 5) -> str:
    """Busca semântica nas fichas por ano, normas legais do salário mínimo e notas de metodologia."""
    return tools.buscar_documentos(pergunta, k)


@mcp.resource("qcm://esquema")
def esquema() -> str:
    """Esquema das tabelas disponíveis."""
    return tools.esquema()


def main() -> None:
    # stdio para Claude Desktop/Code; QCM_MCP_TRANSPORT=streamable-http para servir na rede (ex.: ZimaOS)
    mcp.run(transport=os.getenv("QCM_MCP_TRANSPORT", "stdio"))


if __name__ == "__main__":
    main()
