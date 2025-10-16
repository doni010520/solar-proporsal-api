import json
import math
from pathlib import Path
from typing import Union, List, Dict


class SolarCalculator:
    def __init__(self):
        # Carregar dados de configuração
        data_dir = Path(__file__).parent.parent / "data"
        
        with open(data_dir / "config.json", "r") as f:
            self.config = json.load(f)
        
        with open(data_dir / "inversores.json", "r") as f:
            self.inversores_data = json.load(f)
            self.inversores = sorted(
                self.inversores_data["inversores"], 
                key=lambda x: x["potencia_kw"], 
                reverse=True
            )
    
    def processar_consumo(self, consumo_input: Union[float, List[float]]) -> Dict:
        """Processa entrada de consumo (único ou múltiplo)"""
        if isinstance(consumo_input, (int, float)):
            return {
                "consumo_medio_mensal": float(consumo_input),
                "meses_informados": 1,
                "historico": [float(consumo_input)],
                "consumo_minimo": float(consumo_input),
                "consumo_maximo": float(consumo_input),
                "variacao_percentual": 0.0
            }
        
        # Lista de consumos
        meses_validos = [x for x in consumo_input if x and x > 0]
        media = sum(meses_validos) / len(meses_validos)
        minimo = min(meses_validos)
        maximo = max(meses_validos)
        variacao = ((maximo - minimo) / minimo * 100) if minimo > 0 else 0
        
        return {
            "consumo_medio_mensal": media,
            "meses_informados": len(meses_validos),
            "historico": consumo_input,
            "consumo_minimo": minimo,
            "consumo_maximo": maximo,
            "variacao_percentual": variacao
        }
    
    def obter_disponibilidade_kwh(self, tipo_fornecimento: str) -> int:
        """Retorna kWh de disponibilidade baseado no tipo de fornecimento"""
        return self.config["disponibilidade_kwh"].get(tipo_fornecimento, 50)
    
    def calcular_numero_modulos(
        self, 
        consumo_medio: float, 
        disponibilidade_kwh: int,
        radiacao_solar: float,
        potencia_modulo: int
    ) -> int:
        """
        Calcula quantidade de módulos necessários
        Fórmula: ROUNDUP((consumo - disponibilidade) / (radiacao * area * eficiencia * (1-perdas) * 30), 0)
        """
        modulo_config = self.config["modulo"]
        sistema_config = self.config["sistema"]
        
        area_modulo = modulo_config["area_m2"]
        eficiencia = modulo_config["eficiencia"]
        perdas = sistema_config["perdas_percentual"]
        
        numerador = consumo_medio - disponibilidade_kwh
        denominador = radiacao_solar * area_modulo * eficiencia * (1 - perdas) * 30
        
        num_modulos = math.ceil(numerador / denominador)
        return max(num_modulos, 1)  # Mínimo 1 módulo
    
    def calcular_potencia_sistema(self, num_modulos: int, potencia_modulo: int) -> float:
        """Calcula potência do sistema em kWp"""
        return (num_modulos * potencia_modulo) / 1000
    
    def selecionar_inversor(self, potencia_sistema_kwp: float) -> Dict:
        """
        Seleciona inversor adequado
        Lógica: potencia_necessaria = potencia_sistema / 1.7
        Retorna o inversor imediatamente superior
        """
        potencia_necessaria = potencia_sistema_kwp / 1.7
        
        # Buscar inversor imediatamente superior
        for inversor in reversed(self.inversores):  # Do menor para o maior
            if inversor["potencia_kw"] >= potencia_necessaria:
                return inversor
        
        # Se não encontrar, retorna o maior
        return self.inversores[0]
    
    def calcular_area_total(self, num_modulos: int) -> float:
        """
        Calcula área total necessária
        Fórmula: num_modulos * area_modulo * 1.5
        """
        area_modulo = self.config["modulo"]["area_m2"]
        return num_modulos * area_modulo * 1.5
    
    def calcular_geracao_diaria(
        self, 
        num_modulos: int, 
        radiacao_solar: float,
        potencia_modulo: int
    ) -> float:
        """
        Calcula geração média diária em kWh
        Fórmula: (radiacao * area * eficiencia * (1-perdas)) * num_modulos
        """
        modulo_config = self.config["modulo"]
        sistema_config = self.config["sistema"]
        
        area_modulo = modulo_config["area_m2"]
        eficiencia = modulo_config["eficiencia"]
        perdas = sistema_config["perdas_percentual"]
        
        return (radiacao_solar * area_modulo * eficiencia * (1 - perdas)) * num_modulos
    
    def calcular_geracao_mensal(self, geracao_diaria: float) -> float:
        """Calcula geração média mensal em kWh"""
        return geracao_diaria * 30
    
    def calcular_geracao_anual(self, geracao_diaria: float) -> float:
        """Calcula geração média anual em kWh"""
        return geracao_diaria * 365
    
    def calcular_preco_sistema(self, potencia_kwp: float) -> float:
        """
        Calcula preço do sistema baseado na tabela de preços por kWp
        """
        for faixa in self.config["precos_por_kwp"]:
            if faixa["kwp_min"] <= potencia_kwp < faixa["kwp_max"]:
                if faixa["preco"] == "fora_da_faixa":
                    raise ValueError(f"Potência {potencia_kwp} kWp fora da faixa de preços")
                return potencia_kwp * faixa["preco"]
        
        raise ValueError(f"Não foi possível calcular preço para {potencia_kwp} kWp")
    
    def dimensionar_sistema(
        self,
        consumo_input: Union[float, List[float]],
        tipo_fornecimento: str,
        radiacao_solar: float = 5.0,
        potencia_modulo: int = 700
    ) -> Dict:
        """
        Dimensiona o sistema solar completo
        Retorna dicionário com todos os dados calculados
        """
        # Processar consumo
        consumo_info = self.processar_consumo(consumo_input)
        consumo_medio = consumo_info["consumo_medio_mensal"]
        
        # Obter disponibilidade
        disponibilidade_kwh = self.obter_disponibilidade_kwh(tipo_fornecimento)
        
        # Calcular módulos
        num_modulos = self.calcular_numero_modulos(
            consumo_medio, 
            disponibilidade_kwh, 
            radiacao_solar,
            potencia_modulo
        )
        
        # Calcular potência do sistema
        potencia_kwp = self.calcular_potencia_sistema(num_modulos, potencia_modulo)
        
        # Selecionar inversor
        inversor = self.selecionar_inversor(potencia_kwp)
        
        # Calcular área
        area_total = self.calcular_area_total(num_modulos)
        
        # Calcular geração
        geracao_diaria = self.calcular_geracao_diaria(num_modulos, radiacao_solar, potencia_modulo)
        geracao_mensal = self.calcular_geracao_mensal(geracao_diaria)
        geracao_anual = self.calcular_geracao_anual(geracao_diaria)
        
        # Calcular preço
        investimento = self.calcular_preco_sistema(potencia_kwp)
        
        # Produtividade
        produtividade = geracao_anual / potencia_kwp if potencia_kwp > 0 else 0
        
        return {
            "consumo": consumo_info,
            "sistema": {
                "num_modulos": num_modulos,
                "potencia_kwp": round(potencia_kwp, 2),
                "potencia_inversor": inversor["potencia_kw"],
                "nome_inversor": inversor["nome"],
                "area_necessaria_m2": round(area_total, 2),
                "geracao_media_mensal_kwh": round(geracao_mensal, 2),
                "geracao_media_diaria_kwh": round(geracao_diaria, 2),
                "geracao_media_anual_kwh": round(geracao_anual, 2),
                "produtividade_anual_kwh_kwp": round(produtividade, 2),
                "disponibilidade_kwh": disponibilidade_kwh
            },
            "investimento": round(investimento, 2)
        }
