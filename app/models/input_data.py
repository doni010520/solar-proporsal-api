from pydantic import BaseModel, Field, field_validator
from typing import Union, List, Literal


class ClienteInput(BaseModel):
    nome: str = Field(..., description="Nome completo do cliente")
    cpf_cnpj: str = Field(..., description="CPF ou CNPJ do cliente")
    endereco: str = Field(..., description="Endereço completo")
    cidade: str = Field(..., description="Cidade e estado (ex: Bauru-SP)")
    telefone: str = Field(None, description="Telefone de contato")


class PropostaInput(BaseModel):
    # Dados do cliente
    cliente: ClienteInput
    
    # Consumo (flexível: número único ou array de 13 meses)
    consumo: Union[float, List[float]] = Field(
        ..., 
        description="Consumo mensal em kWh (número único) ou histórico de 13 meses (array)"
    )
    
    # Dados da conta de energia
    tipo_fornecimento: Literal["monofasico", "bifasico", "trifasico"] = Field(
        ..., 
        description="Tipo de fornecimento de energia"
    )
    concessionaria: str = Field(default="CPFL Paulista", description="Concessionária de energia")
    tensao: str = Field(default="220V", description="Tensão da rede")
    iluminacao_publica: float = Field(default=14.75, description="Valor da taxa de iluminação pública")
    
    # Impostos (opcional, usa padrão SP se não informado)
    icms: float = Field(default=0.18, description="Alíquota de ICMS")
    pis: float = Field(default=0.0099, description="Alíquota de PIS")
    cofins: float = Field(default=0.0463, description="Alíquota de COFINS")
    
    # Dados técnicos (opcional, usa padrão se não informado)
    radiacao_solar: float = Field(default=5.0, description="Radiação solar em kWh/m²/dia")
    potencia_modulo: int = Field(default=700, description="Potência do módulo em Wp")
    
    @field_validator('consumo')
    @classmethod
    def validar_consumo(cls, v):
        if isinstance(v, (int, float)):
            if v <= 0:
                raise ValueError("Consumo deve ser maior que zero")
            if v > 50000:
                raise ValueError("Consumo muito alto. Verificar dados.")
            return v
        
        if isinstance(v, list):
            if len(v) > 13:
                raise ValueError("Máximo 13 meses de histórico")
            if len(v) < 1:
                raise ValueError("Informar pelo menos 1 mês")
            
            validos = [x for x in v if x and x > 0]
            if len(validos) == 0:
                raise ValueError("Nenhum valor de consumo válido informado")
            
            return v
        
        raise ValueError("Formato inválido. Use número ou lista de números")
    
    @field_validator('tipo_fornecimento')
    @classmethod
    def validar_tipo_fornecimento(cls, v):
        return v.lower()
