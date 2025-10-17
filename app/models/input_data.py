from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ClienteInput(BaseModel):
    nome: str = Field(..., description="Nome completo do cliente")
    cpf_cnpj: str = Field(..., description="CPF ou CNPJ do cliente")
    endereco: str = Field(..., description="Endereço completo")
    cidade: str = Field(..., description="Cidade e estado (ex: Bauru-SP)")
    telefone: str = Field(None, description="Telefone de contato")

class PropostaInput(BaseModel):
    # Dados do cliente
    cliente: ClienteInput
    
    # JSON unificado com dados do sistema e payback
    dados_completos: List[Dict[str, Any]] = Field(
        ..., 
        description="Array com todos os dados da planilha (sistema + payback)"
    )
    
    # O investimento será extraído automaticamente de "Preço do Sistema Dimensionado"
