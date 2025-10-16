from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import base64
import traceback

from app.models.input_data import PropostaInput
from app.models.output_data import (
    PropostaOutput, ConsumoInfo, SistemaInfo, 
    FinanceiroInfo, EconomiaAnual
)
from app.core.calculator import SolarCalculator
from app.core.financial import FinancialAnalyzer
from app.pdf.generator import PDFGenerator


app = FastAPI(
    title="Solar Proposal API",
    description="API para geração de propostas de energia solar - LEVESOL",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar calculadoras
calculator = SolarCalculator()
financial_analyzer = FinancialAnalyzer()
pdf_generator = PDFGenerator()


@app.get("/")
def read_root():
    return {
        "message": "Solar Proposal API - LEVESOL",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "create_proposal": "POST /api/proposta",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/proposta", response_model=PropostaOutput)
async def criar_proposta(dados: PropostaInput):
    """
    Cria uma proposta completa de energia solar
    
    - **consumo**: Consumo mensal em kWh (número único ou array de 13 meses)
    - **tipo_fornecimento**: monofasico, bifasico ou trifasico
    - Retorna proposta completa com PDF em base64
    """
    try:
        # 1. Dimensionar sistema
        dimensionamento = calculator.dimensionar_sistema(
            consumo_input=dados.consumo,
            tipo_fornecimento=dados.tipo_fornecimento,
            radiacao_solar=dados.radiacao_solar,
            potencia_modulo=dados.potencia_modulo
        )
        
        # 2. Calcular economia 25 anos
        economia_25_anos = financial_analyzer.calcular_economia_25_anos(
            consumo_mensal=dimensionamento["consumo"]["consumo_medio_mensal"],
            geracao_mensal=dimensionamento["sistema"]["geracao_media_mensal_kwh"],
            disponibilidade_kwh=dimensionamento["sistema"]["disponibilidade_kwh"],
            icms=dados.icms,
            pis=dados.pis,
            cofins=dados.cofins,
            iluminacao_publica=dados.iluminacao_publica
        )
        
        # 3. Calcular economia total
        economia_total = financial_analyzer.calcular_economia_total(economia_25_anos)
        
        # 4. Gerar número da proposta
        numero_proposta = f"{datetime.now().strftime('%d%m%y')}/{datetime.now().year}"
        
        # 5. Preparar dados para PDF
        dados_pdf = {
            "numero_proposta": numero_proposta,
            "cliente": {
                "nome": dados.cliente.nome,
                "cpf_cnpj": dados.cliente.cpf_cnpj,
                "endereco": dados.cliente.endereco,
                "cidade": dados.cliente.cidade,
                "telefone": dados.cliente.telefone
            },
            "consumo": dimensionamento["consumo"],
            "sistema": dimensionamento["sistema"],
            "financeiro": {
                "investimento_total": dimensionamento["investimento"],
                "valor_conta_atual_mensal": economia_25_anos[0]["conta_sem_solar"],
                "valor_conta_com_sistema_mensal": economia_25_anos[0]["conta_com_solar"],
                "economia_mensal_ano1": economia_25_anos[0]["economia_mensal"],
                "economia_25_anos": economia_total
            },
            "economia_por_ano": economia_25_anos,
            "tipo_fornecimento": dados.tipo_fornecimento,
            "concessionaria": dados.concessionaria,
            "tensao": dados.tensao,
            "radiacao_solar": dados.radiacao_solar
        }
        
        # 6. Gerar PDF
        pdf_bytes = pdf_generator.criar_proposta(dados_pdf)
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # 7. Preparar resposta
        resposta = PropostaOutput(
            numero_proposta=numero_proposta,
            consumo=ConsumoInfo(**dimensionamento["consumo"]),
            sistema=SistemaInfo(**dimensionamento["sistema"]),
            financeiro=FinanceiroInfo(**dados_pdf["financeiro"]),
            economia_por_ano=[EconomiaAnual(**item) for item in economia_25_anos],
            pdf_base64=pdf_base64
        )
        
        return resposta
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Erro ao criar proposta: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno ao processar proposta: {str(e)}"
        )


@app.get("/api/config")
def get_config():
    """Retorna configurações da API (impostos, tarifas, etc)"""
    return calculator.config


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
