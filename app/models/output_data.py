from pydantic import BaseModel
from typing import List


class ConsumoInfo(BaseModel):
    consumo_medio_mensal: float
    meses_informados: int
    consumo_minimo: float = None
    consumo_maximo: float = None
    variacao_percentual: float = None


class SistemaInfo(BaseModel):
    num_modulos: int
    potencia_kwp: float
    potencia_inversor: float
    nome_inversor: str
    area_necessaria_m2: float
    geracao_media_mensal_kwh: float
    geracao_media_diaria_kwh: float
    geracao_media_anual_kwh: float
    produtividade_anual_kwh_kwp: float


class FinanceiroInfo(BaseModel):
    investimento_total: float
    valor_conta_atual_mensal: float
    valor_conta_com_sistema_mensal: float
    economia_mensal_ano1: float
    economia_25_anos: float
    
class EconomiaAnual(BaseModel):
    ano: int
    economia_mensal: float
    conta_sem_solar: float
    conta_com_solar: float


class PropostaOutput(BaseModel):
    numero_proposta: str
    consumo: ConsumoInfo
    sistema: SistemaInfo
    financeiro: FinanceiroInfo
    economia_por_ano: List[EconomiaAnual]
    pdf_base64: str = None
