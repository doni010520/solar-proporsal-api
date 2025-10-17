from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np
from io import BytesIO
import base64
from datetime import datetime
import re

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Cria estilos customizados para o PDF"""
        self.styles.add(ParagraphStyle(
            name='TitleCustom',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#366092'),
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubtitleCustom',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#366092'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
    
    def extrair_dados(self, dados_completos):
        """Extrai dados do sistema e payback do JSON unificado"""
        dados_sistema = {}
        dados_payback = []
        
        for item in dados_completos:
            # Extrair dados de payback
            if "Gráfico Payback" in item and item.get("col_2"):
                # Limpar valores monetários
                if isinstance(item.get("col_2"), str):
                    # Remove R$, espaços e converte vírgula para ponto
                    valor_str = item["col_2"].replace("R$", "").replace(",", "").replace(" ", "")
                    try:
                        valor = float(valor_str)
                    except:
                        continue
                else:
                    valor = item.get("col_2", 0)
                
                # Processar economia mensal
                if isinstance(item.get("col_3"), str):
                    economia_str = item["col_3"].replace("R$", "").replace(",", "").replace(" ", "")
                    try:
                        economia = float(economia_str)
                    except:
                        economia = 0
                else:
                    economia = item.get("col_3", 0)
                
                # Adicionar aos dados de payback se for ano válido
                try:
                    ano = int(item["Gráfico Payback"])
                    dados_payback.append({
                        "ano": ano,
                        "amortizacao": valor,
                        "economia_mensal": economia
                    })
                except:
                    pass
            
            # Extrair dados do sistema
            if "DADOS DA CONTA DE ENERGIA" in item:
                campo = item["DADOS DA CONTA DE ENERGIA"]
                valor = item.get("col_7")
                
                if "Consumo Atual" in campo:
                    dados_sistema["consumo_atual"] = valor
                elif "Quantidade de módulos" in campo:
                    dados_sistema["num_modulos"] = int(valor) if valor else 0
                elif "Potência do sistema" in campo:
                    dados_sistema["potencia_kwp"] = valor
                elif "Potência do inversor" in campo:
                    dados_sistema["potencia_inversor"] = valor
                elif "Área total instalada" in campo:
                    dados_sistema["area_total"] = valor
                elif "Energia Média Gerada (mês)" in campo:
                    dados_sistema["geracao_mensal"] = valor
                elif "Energia Média Gerada (ano)" in campo:
                    dados_sistema["geracao_anual"] = valor
                elif "Valor da conta antes" in campo:
                    dados_sistema["conta_antes"] = valor
                elif "Valor da conta depois" in campo:
                    dados_sistema["conta_depois"] = valor
                elif "Preço do Sistema" in campo:
                    dados_sistema["investimento"] = valor
                elif "Padrão do Cliente" in campo:
                    dados_sistema["tipo_fornecimento"] = valor
        
        return dados_sistema, dados_payback
    
    def gerar_grafico_payback(self, dados_payback):
        """Gera o gráfico de payback estilo LEVESOL"""
        # Extrair dados
        anos = []
        amortizacao = []
        
        for item in dados_payback:
            anos.append(item["ano"])
            amortizacao.append(item["amortizacao"])
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Definir cores para cada barra
        cores = ['#FF4444' if valor < 0 else '#FFD700' for valor in amortizacao]
        
        # Criar gráfico de barras
        barras = ax.bar(anos, amortizacao, color=cores, width=0.7, edgecolor='none')
        
        # Configurar título
        ax.set_title('Gráfico Payback', fontsize=14, fontweight='bold', pad=15)
        
        # Configurar grid
        ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Configurar eixo Y
        y_min = min(amortizacao) * 1.1 if min(amortizacao) < 0 else 0
        y_max = max(amortizacao) * 1.1
        ax.set_ylim(y_min, y_max)
        
        # Formatar valores do eixo Y
        def format_currency(x, p):
            if x == 0:
                return 'R$ 0,00'
            elif x < 0:
                return f'-R$ {abs(x):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                return f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        
        from matplotlib.ticker import FuncFormatter
        ax.yaxis.set_major_formatter(FuncFormatter(format_currency))
        
        # Configurar eixo X
        ax.set_xticks(anos)
        ax.set_xticklabels(anos, rotation=45, ha='right', fontsize=8)
        
        # Adicionar linha horizontal em y=0
        ax.axhline(y=0, color='black', linewidth=0.8, alpha=0.5)
        
        # Remover bordas superiores e direita
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar em buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def calcular_payback(self, dados_payback):
        """Calcula o período de payback"""
        for i, item in enumerate(dados_payback):
            if item["amortizacao"] > 0:
                # Encontrou o ano de payback
                if i > 0:
                    valor_anterior = dados_payback[i-1]["amortizacao"]
                    valor_atual = item["amortizacao"]
                    diferenca_anual = valor_atual - valor_anterior
                    meses_para_zerar = (abs(valor_anterior) / (diferenca_anual / 12)) if diferenca_anual > 0 else 0
                    
                    anos = i - 1 + int(meses_para_zerar / 12)
                    meses = int(meses_para_zerar % 12)
                    return anos, meses
        return 0, 0
    
    def criar_proposta_completa(self, dados):
        """Cria PDF completo com todos os dados"""
        buffer = BytesIO()
        
        # Extrair dados do JSON unificado
        dados_sistema, dados_payback = self.extrair_dados(dados["dados_completos"])
        
        # Calcular payback
        payback_anos, payback_meses = self.calcular_payback(dados_payback)
        
        # Economia total (último valor de amortização)
        economia_total = dados_payback[-1]["amortizacao"] if dados_payback else 0
        
        # Criar canvas
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # ========== PÁGINA 1: CAPA ==========
        # Logo LEVESOL
        c.setFont("Helvetica-Bold", 36)
        c.setFillColor(colors.HexColor('#366092'))
        c.drawCentredString(width/2, height - 100, "LEVESOL")
        
        # Linha decorativa
        c.setStrokeColor(colors.HexColor('#FFD700'))
        c.setLineWidth(3)
        c.line(100, height - 120, width - 100, height - 120)
        
        # Título
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(colors.black)
        c.drawCentredString(width/2, height/2 + 50, "PROPOSTA COMERCIAL")
        c.drawCentredString(width/2, height/2, "SISTEMA FOTOVOLTAICO")
        
        # Dados do cliente
        c.setFont("Helvetica", 14)
        y_pos = height/2 - 80
        c.drawString(100, y_pos, f"Cliente: {dados['cliente']['nome']}")
        c.drawString(100, y_pos - 25, f"Endereço: {dados['cliente']['endereco']}")
        c.drawString(100, y_pos - 50, f"Cidade: {dados['cliente']['cidade']}")
        if dados['cliente'].get('telefone'):
            c.drawString(100, y_pos - 75, f"Telefone: {dados['cliente']['telefone']}")
        
        # Número da proposta
        c.setFont("Helvetica", 12)
        c.drawString(100, 100, f"Proposta Nº: {dados['numero_proposta']}")
        c.drawString(100, 80, f"Data: {datetime.now().strftime('%d/%m/%Y')}")
        
        # Rodapé
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 40, "LEVESOL LTDA | CNPJ: 44.075.186/0001-11")
        c.drawCentredString(width/2, 25, "Contato: (14) 99893-7738 | contato@levesol.com.br")
        
        c.showPage()
        
        # ========== PÁGINA 2: DADOS DO SISTEMA ==========
        # Título
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(colors.HexColor('#366092'))
        c.setStrokeColor(colors.HexColor('#FFD700'))
        c.setLineWidth(2)
        c.rect(50, height - 100, width - 100, 40, fill=0)
        c.drawCentredString(width/2, height - 80, "Proposta Comercial")
        
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width/2, height - 120, "Sistema Fotovoltaico On-grid")
        
        # Tabela de dados do sistema
        y_pos = height - 160
        
        # Cabeçalho da seção
        c.setFillColor(colors.HexColor('#5B9BD5'))
        c.rect(50, y_pos, width - 100, 25, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(60, y_pos + 8, "SISTEMA FOTOVOLTAICO PROPOSTO")
        
        # Dados do sistema
        y_pos -= 30
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        
        dados_tabela = [
            ("NÚMERO DE MÓDULOS:", f"{dados_sistema.get('num_modulos', 'N/A')} un."),
            ("POTÊNCIA DO SISTEMA:", f"{dados_sistema.get('potencia_kwp', 'N/A')} kWp"),
            ("ÁREA NECESSÁRIA:", f"{round(dados_sistema.get('area_total', 0), 1)} m²"),
            ("GERAÇÃO MÉDIA MENSAL:", f"{round(dados_sistema.get('geracao_mensal', 0), 0)} kWh"),
            ("GERAÇÃO MÉDIA ANUAL:", f"{round(dados_sistema.get('geracao_anual', 0), 0)} kWh"),
        ]
        
        for label, valor in dados_tabela:
            c.drawString(60, y_pos, label)
            c.drawString(300, y_pos, valor)
            y_pos -= 25
        
        # Economia
        y_pos -= 20
        c.setFillColor(colors.HexColor('#5B9BD5'))
        c.rect(50, y_pos, width - 100, 25, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(60, y_pos + 8, "ECONOMIA ESTIMADA")
        
        y_pos -= 30
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        
        conta_antes = dados_sistema.get('conta_antes', 0)
        conta_depois = dados_sistema.get('conta_depois', 0)
        economia_mensal = conta_antes - conta_depois
        
        c.drawString(60, y_pos, "Valor médio da conta ANTES:")
        c.drawString(300, y_pos, f"R$ {conta_antes:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        y_pos -= 25
        
        c.drawString(60, y_pos, "Valor médio da conta DEPOIS:")
        c.drawString(300, y_pos, f"R$ {conta_depois:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        y_pos -= 25
        
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor('#70AD47'))
        c.drawString(60, y_pos, "ECONOMIA MENSAL:")
        c.drawString(300, y_pos, f"R$ {economia_mensal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        # Rodapé
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 30, "LEVESOL LTDA CNPJ 44.075.186/0001-11")
        c.drawCentredString(width/2, 20, "www.levesol.com.br")
        
        c.showPage()
        
        # ========== PÁGINA 3: ANÁLISE FINANCEIRA COM GRÁFICO ==========
        # Título
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(colors.HexColor('#366092'))
        c.setStrokeColor(colors.HexColor('#FFD700'))
        c.setLineWidth(2)
        c.rect(50, height - 100, width - 100, 40, fill=0)
        c.drawCentredString(width/2, height - 80, "Análise Financeira")
        
        # Box com investimento
        c.setStrokeColor(colors.HexColor('#366092'))
        c.setLineWidth(2)
        c.rect(100, height - 180, 150, 50, fill=0)
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.black)
        c.drawString(110, height - 155, "Investimento")
        c.setFont("Helvetica-Bold", 18)
        investimento = dados_sistema.get("investimento", 0)
        investimento_fmt = f"R$ {investimento:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        c.drawString(260, height - 155, investimento_fmt)
        
        c.setFont("Helvetica-Italic", 9)
        c.setFillColor(colors.gray)
        c.drawString(100, height - 195, "*Esse é um orçamento inicial. O preço final é definido após visita técnica.")
        
        # Gerar e inserir gráfico
        if dados_payback:
            grafico_buffer = self.gerar_grafico_payback(dados_payback)
            from reportlab.lib.utils import ImageReader
            img = ImageReader(grafico_buffer)
            c.drawImage(img, 60, height - 520, width=480, height=280, preserveAspectRatio=True)
        
        # Rodapé da página
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 30, "LEVESOL LTDA CNPJ 44.075.186/0001-11")
        c.drawCentredString(width/2, 20, "www.levesol.com.br")
        
        c.showPage()
        
        # ========== PÁGINA 4: RETORNO DO INVESTIMENTO ==========
        # Título
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(colors.HexColor('#366092'))
        c.setStrokeColor(colors.HexColor('#FFD700'))
        c.setLineWidth(2)
        c.rect(50, height - 100, width - 100, 40, fill=0)
        c.drawCentredString(width/2, height - 80, "Retorno do Investimento")
        
        # Subtítulo Payback
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor('#366092'))
        c.drawCentredString(width/2, height - 130, "Payback")
        
        # Payback em destaque
        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(colors.HexColor('#70AD47'))
        payback_texto = f"{payback_anos} anos e {payback_meses} meses"
        c.drawCentredString(width/2, height - 165, payback_texto)
        
        # Cabeçalho da tabela
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor('#366092'))
        c.drawString(200, height - 210, "ANO")
        c.drawString(350, height - 210, "COM REAJUSTE")
        
        # Linha separadora
        c.setStrokeColor(colors.HexColor('#366092'))
        c.setLineWidth(1)
        c.line(190, height - 215, 450, height - 215)
        
        # Tabela de retorno (primeiros 10 anos)
        c.setFont("Helvetica", 10)
        y_pos = height - 235
        
        for i, item in enumerate(dados_payback[:10]):
            ano = item["ano"]
            amortizacao = item["amortizacao"]
            
            # Ano
            c.setFillColor(colors.black)
            c.drawString(200, y_pos, str(ano))
            
            # Valor formatado e colorido
            if amortizacao < 0:
                valor_fmt = f"-R$ {abs(amortizacao):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                c.setFillColor(colors.red)
            else:
                valor_fmt = f"R$ {amortizacao:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                c.setFillColor(colors.HexColor('#70AD47'))
            
            c.drawString(350, y_pos, valor_fmt)
            y_pos -= 20
        
        # Caixa acumulado em 21 anos
        y_pos -= 30
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor('#70AD47'))
        c.drawCentredString(width/2, y_pos, "CAIXA ACUMULADO EM 21 ANOS:")
        c.setFont("Helvetica-Bold", 18)
        economia_fmt = f"R$ {economia_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        c.drawCentredString(width/2, y_pos - 25, economia_fmt)
        
        # Notas
        c.setFont("Helvetica-Italic", 9)
        c.setFillColor(colors.gray)
        c.drawString(100, 100, "*Neste retorno do investimento foram considerados reajustes")
        c.drawString(100, 85, "anuais da tarifa de energia, em média 5% ao ano")
        
        # Rodapé final
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 30, "LEVESOL LTDA CNPJ 44.075.186/0001-11")
        c.drawCentredString(width/2, 20, "Contato: (14) 99893-7738 | contato@levesol.com.br")
        c.drawCentredString(width/2, 10, "www.levesol.com.br")
        
        c.save()
        
        buffer.seek(0)
        return buffer.getvalue()
