from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from datetime import datetime
import base64
import traceback

from app.models.input_data import PropostaInput
from app.pdf.generator import PDFGenerator

app = FastAPI(
    title="Solar Proposal PDF Generator",
    description="API para geração de PDF de propostas de energia solar com gráfico de payback - LEVESOL",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar gerador de PDF
pdf_generator = PDFGenerator()

@app.get("/")
def read_root():
    return {
        "message": "Solar Proposal PDF Generator - LEVESOL",
        "version": "2.0.0",
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

@app.post("/api/proposta")
async def criar_proposta(dados: PropostaInput):
    """
    Gera PDF completo com análise de payback
    
    - **cliente**: Dados do cliente (nome, endereço, etc)
    - **dados_payback**: Array com dados de payback já calculados
    - **investimento**: Valor do investimento inicial
    - Retorna: PDF com gráfico e tabelas
    """
    try:
        # 1. Processar dados de payback
        dados_processados = processar_dados_payback(dados.dados_payback)
        
        # 2. Gerar número da proposta
        numero_proposta = f"{datetime.now().strftime('%d%m%y')}/{datetime.now().year}"
        
        # 3. Preparar dados para PDF
        dados_pdf = {
            "numero_proposta": numero_proposta,
            "cliente": {
                "nome": dados.cliente.nome,
                "cpf_cnpj": dados.cliente.cpf_cnpj,
                "endereco": dados.cliente.endereco,
                "cidade": dados.cliente.cidade,
                "telefone": dados.cliente.telefone
            },
            "investimento": dados.investimento,
            "dados_payback": dados_processados,
            "payback_anos": dados_processados["payback_anos"],
            "payback_meses": dados_processados["payback_meses"],
            "economia_total_21_anos": dados_processados["economia_total_21_anos"]
        }
        
        # 4. Gerar PDF completo
        pdf_bytes = pdf_generator.criar_proposta_completa(dados_pdf)
        
        # 5. Retornar resposta simplificada
        return {
            "status": "success",
            "numero_proposta": numero_proposta,
            "mensagem": "PDF gerado com sucesso",
            "pdf_base64": base64.b64encode(pdf_bytes).decode('utf-8')
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Erro ao criar proposta: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno ao processar proposta: {str(e)}"
        )

@app.post("/api/proposta/pdf", response_class=Response)
async def criar_proposta_pdf_direto(dados: PropostaInput):
    """
    Retorna o PDF diretamente como arquivo (não base64)
    Útil para download direto ou visualização no navegador
    """
    try:
        # Processar dados
        dados_processados = processar_dados_payback(dados.dados_payback)
        numero_proposta = f"{datetime.now().strftime('%d%m%y')}/{datetime.now().year}"
        
        # Preparar dados para PDF
        dados_pdf = {
            "numero_proposta": numero_proposta,
            "cliente": {
                "nome": dados.cliente.nome,
                "cpf_cnpj": dados.cliente.cpf_cnpj,
                "endereco": dados.cliente.endereco,
                "cidade": dados.cliente.cidade,
                "telefone": dados.cliente.telefone
            },
            "investimento": dados.investimento,
            "dados_payback": dados_processados,
            "payback_anos": dados_processados["payback_anos"],
            "payback_meses": dados_processados["payback_meses"],
            "economia_total_21_anos": dados_processados["economia_total_21_anos"]
        }
        
        # Gerar PDF
        pdf_bytes = pdf_generator.criar_proposta_completa(dados_pdf)
        
        # Retornar como arquivo PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=proposta_{numero_proposta.replace('/', '_')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def processar_dados_payback(dados_payback):
    """
    Processa os dados de payback recebidos e calcula métricas
    """
    # Filtrar apenas dados válidos (ignorar linha de cabeçalho)
    dados_validos = [d for d in dados_payback if isinstance(d.get("Gráfico Payback"), int)]
    
    # Encontrar ano de payback (quando amortização fica positiva)
    ano_payback = None
    indice_payback = None
    
    for i, dado in enumerate(dados_validos):
        if dado["col_2"] > 0:
            ano_payback = dado["Gráfico Payback"]
            indice_payback = i
            break
    
    # Calcular anos e meses de payback
    payback_anos = 0
    payback_meses = 0
    
    if ano_payback and indice_payback > 0:
        valor_ano_anterior = dados_validos[indice_payback - 1]["col_2"]
        valor_ano_payback = dados_validos[indice_payback]["col_2"]
        
        # Calcular diferença entre os anos
        economia_ano = valor_ano_payback - valor_ano_anterior
        economia_mensal = economia_ano / 12
        
        # Calcular meses para zerar o déficit anterior
        deficit_anterior = abs(valor_ano_anterior)
        meses_para_zerar = deficit_anterior / economia_mensal if economia_mensal > 0 else 0
        
        # Anos completos antes do payback + meses fracionados
        payback_anos = indice_payback - 1 + int(meses_para_zerar / 12)
        payback_meses = int(meses_para_zerar % 12)
        
        # Ajustar se necessário
        if payback_anos < 0:
            payback_anos = 0
        if payback_meses >= 12:
            payback_anos += 1
            payback_meses -= 12
    
    # Criar tabela de retorno formatada
    tabela_retorno = []
    for dado in dados_validos:
        ano = dado["Gráfico Payback"]
        amortizacao = dado["col_2"]
        economia_mensal = dado["col_3"]
        
        tabela_retorno.append({
            "ano": ano,
            "amortizacao": amortizacao,
            "economia_mensal": economia_mensal,
            "economia_anual": economia_mensal * 12,
            "status": "positivo" if amortizacao > 0 else "negativo"
        })
    
    # Economia total em 21 anos (último valor da amortização)
    economia_total_21_anos = dados_validos[-1]["col_2"] if dados_validos else 0
    
    return {
        "dados_originais": dados_validos,
        "tabela_retorno": tabela_retorno,
        "payback_anos": payback_anos,
        "payback_meses": payback_meses,
        "ano_payback": ano_payback,
        "economia_total_21_anos": economia_total_21_anos
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
