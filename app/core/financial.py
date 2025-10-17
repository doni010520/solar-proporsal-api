import json
from pathlib import Path
from typing import Dict, List


class FinancialAnalyzer:
    def __init__(self):
        # Carregar configurações
        data_dir = Path(__file__).parent.parent / "data"
        with open(data_dir / "config.json", "r") as f:
            self.config = json.load(f)
    
    def calcular_custo_kwh(self, icms: float, pis: float, cofins: float) -> float:
        """
        Calcula custo do kWh
        Fórmula: TUSD + TE (sem impostos)
        """
        tarifas = self.config["tarifas_sp"]
        return tarifas["tusd"] + tarifas["te"]
    
    def calcular_conta_sem_solar(
        self,
        consumo_mensal: float,
        icms: float,
        pis: float,
        cofins: float,
        iluminacao_publica: float,
        ano: int = 1
    ) -> float:
        """
        Calcula valor da conta SEM sistema solar
        Inclui reajuste anual de 5%
        """
        # Custo base do kWh (TUSD + TE)
        custo_kwh = self.calcular_custo_kwh(icms, pis, cofins)
        
        # Aplicar reajuste anual
        reajuste_anual = self.config["sistema"]["correcao_monetaria_anual"]
        fator_reajuste = (1 + reajuste_anual) ** (ano - 1)
        custo_kwh_ajustado = custo_kwh * fator_reajuste
        
        # Valor da energia SEM impostos
        valor_sem_impostos = consumo_mensal * custo_kwh_ajustado
        
        # Aplicar impostos "por dentro" (somados)
        aliquota_total = icms + pis + cofins
        valor_com_impostos = valor_sem_impostos / (1 - aliquota_total)
        
        # Total (energia com impostos + iluminação pública)
        total = valor_com_impostos + iluminacao_publica
        
        return round(total, 2)
    
    def calcular_conta_com_solar(
        self,
        consumo_mensal: float,
        geracao_mensal: float,
        disponibilidade_kwh: int,
        icms: float,
        pis: float,
        cofins: float,
        iluminacao_publica: float,
        ano: int = 1
    ) -> float:
        """
        Calcula valor da conta COM sistema solar
        Considera Lei 14.300 (percentuais de geração nos primeiros anos)
        """
        # Obter percentual de geração conforme Lei 14.300
        percentual_geracao = self.obter_percentual_geracao_lei14300(ano)
        
        # Geração efetiva considerando a lei
        geracao_efetiva = geracao_mensal * percentual_geracao
        
        # Consumo líquido (consumo - geração)
        consumo_liquido = max(consumo_mensal - geracao_efetiva, 0)
        
        # Se consumo líquido for menor que disponibilidade, cobra disponibilidade
        consumo_a_cobrar = max(consumo_liquido, disponibilidade_kwh)
        
        # Custo base do kWh com reajuste
        custo_kwh = self.calcular_custo_kwh(icms, pis, cofins)
        reajuste_anual = self.config["sistema"]["correcao_monetaria_anual"]
        fator_reajuste = (1 + reajuste_anual) ** (ano - 1)
        custo_kwh_ajustado = custo_kwh * fator_reajuste
        
        # Valor da energia SEM impostos
        valor_sem_impostos = consumo_a_cobrar * custo_kwh_ajustado
        
        # Aplicar impostos "por dentro" (somados)
        aliquota_total = icms + pis + cofins
        valor_com_impostos = valor_sem_impostos / (1 - aliquota_total)
        
        # Total (energia com impostos + iluminação pública)
        total = valor_com_impostos + iluminacao_publica
        
        return round(total, 2)
    
    def obter_percentual_geracao_lei14300(self, ano: int) -> float:
        """
        Retorna percentual de geração conforme Lei 14.300
        Anos 1-4 têm percentuais menores, a partir do ano 5 é 100%
        """
        lei = self.config["lei_14300"]
        
        if ano == 1:
            return lei["ano_1"]
        elif ano == 2:
            return lei["ano_2"]
        elif ano == 3:
            return lei["ano_3"]
        elif ano == 4:
            return lei["ano_4"]
        else:
            return lei["ano_5_em_diante"]
    
    def calcular_economia_25_anos(
        self,
        consumo_mensal: float,
        geracao_mensal: float,
        disponibilidade_kwh: int,
        icms: float,
        pis: float,
        cofins: float,
        iluminacao_publica: float
    ) -> List[Dict]:
        """
        Calcula economia para 25 anos
        Retorna lista com dados de cada ano
        """
        economia_por_ano = []
        ano_inicial = 2025
        
        for ano_index in range(1, 26):  # 25 anos
            ano_calendario = ano_inicial + ano_index - 1
            
            conta_sem_solar = self.calcular_conta_sem_solar(
                consumo_mensal, icms, pis, cofins, iluminacao_publica, ano_index
            )
            
            conta_com_solar = self.calcular_conta_com_solar(
                consumo_mensal, geracao_mensal, disponibilidade_kwh,
                icms, pis, cofins, iluminacao_publica, ano_index
            )
            
            economia_mensal = conta_sem_solar - conta_com_solar
            
            economia_por_ano.append({
                "ano": ano_calendario,
                "economia_mensal": round(economia_mensal, 2),
                "conta_sem_solar": conta_sem_solar,
                "conta_com_solar": conta_com_solar
            })
        
        return economia_por_ano
    
    def calcular_economia_total(self, economia_por_ano: List[Dict]) -> float:
        """Calcula economia total acumulada em 25 anos"""
        total = sum(item["economia_mensal"] * 12 for item in economia_por_ano)
        return round(total, 2)
