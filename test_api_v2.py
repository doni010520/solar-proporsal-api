#!/usr/bin/env python3
"""
Teste para API v2.0 - JSON unificado
"""
import requests
import json
import base64
from pathlib import Path

API_URL = "http://localhost:8000/api/proposta"

# Dados de teste com formato da planilha
dados_teste = {
    "cliente": {
        "nome": "João da Silva",
        "cpf_cnpj": "123.456.789-00",
        "endereco": "Rua das Flores, 123",
        "cidade": "Bauru-SP",
        "telefone": "14999999999"
    },
    "dados_completos": [
        # Dados de Payback
        {"row_number": 3, "Gráfico Payback": 2025, "col_2": -35750, "col_3": 1288.19},
        {"row_number": 4, "Gráfico Payback": 2026, "col_2": -20291.69, "col_3": 1293.75},
        {"row_number": 5, "Gráfico Payback": 2027, "col_2": -4766.66, "col_3": 1296.65},
        {"row_number": 6, "Gráfico Payback": 2028, "col_2": 10793.11, "col_3": 1296.60},
        {"row_number": 7, "Gráfico Payback": 2029, "col_2": 26352.29, "col_3": 1316.01},
        
        # Dados do Sistema
        {"row_number": 20, "DADOS DA CONTA DE ENERGIA": "Consumo Atual (kWh/mês):", "col_7": 1875},
        {"row_number": 24, "DADOS DA CONTA DE ENERGIA": "Quantidade de módulos necessários:", "col_7": 22},
        {"row_number": 25, "DADOS DA CONTA DE ENERGIA": "Potência do sistema (kWp):", "col_7": 15.4},
        {"row_number": 26, "DADOS DA CONTA DE ENERGIA": "Potência do inversor:", "col_7": 10},
        {"row_number": 27, "DADOS DA CONTA DE ENERGIA": "Área total instalada (m²):", "col_7": 102.5},
        {"row_number": 23, "DADOS DA CONTA DE ENERGIA": "Energia Média Gerada (mês) kwh:", "col_7": 1845},
        {"row_number": 30, "DADOS DA CONTA DE ENERGIA": "Energia Média Gerada (ano) kwh:", "col_7": 22447},
        {"row_number": 31, "DADOS DA CONTA DE ENERGIA": "Valor da conta antes do SFV:", "col_7": 1697.83},
        {"row_number": 32, "DADOS DA CONTA DE ENERGIA": "Valor da conta depois do SFV:", "col_7": 409.64},
        {"row_number": 39, "DADOS DA CONTA DE ENERGIA": "Preço do Sistema Dimensionado:", "col_7": 35750}
    ]
}

response = requests.post(API_URL, json=dados_teste)
if response.status_code == 200:
    print("✅ PDF gerado com sucesso!")
    resultado = response.json()
    pdf_bytes = base64.b64decode(resultado['pdf_base64'])
    Path("proposta_teste.pdf").write_bytes(pdf_bytes)
    print("📄 Salvo como: proposta_teste.pdf")
else:
    print(f"❌ Erro: {response.text}")
