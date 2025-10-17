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
    description="API para geração de PDF de propostas de energia solar - LEVESOL",
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
    Gera PDF completo com dados do sistema e análise de payback
    
    - **cliente**: Dados do cliente (nome, endereço, etc)
    - **dados_completos**: Array com todos os dados da planilha
    - Retorna: PDF com proposta completa
    """
    try:
        # Gerar número da proposta
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
            "dados_completos": dados.dados_completos
        }
        
        # Gerar PDF completo
        pdf_bytes = pdf_generator.criar_proposta_completa(dados_pdf)
        
        # Retornar resposta
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
    Retorna o PDF diretamente como arquivo
    """
    try:
        numero_proposta = f"{datetime.now().strftime('%d%m%y')}/{datetime.now().year}"
        
        dados_pdf = {
            "numero_proposta": numero_proposta,
            "cliente": {
                "nome": dados.cliente.nome,
                "cpf_cnpj": dados.cliente.cpf_cnpj,
                "endereco": dados.cliente.endereco,
                "cidade": dados.cliente.cidade,
                "telefone": dados.cliente.telefone
            },
            "dados_completos": dados.dados_completos
        }
        
        pdf_bytes = pdf_generator.criar_proposta_completa(dados_pdf)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=proposta_{numero_proposta.replace('/', '_')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
