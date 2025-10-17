from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np
from io import BytesIO
import base64
from datetime import datetime
import re
import os

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        # Caminhos para os assets (ajuste conforme necessário)
        self.assets_path = "app/pdf/assets/"
        
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
    
    def desenhar_fundo_interno(self, c, width, height):
        """Adiciona o fundo padrão nas páginas internas"""
        try:
            bg_path = os.path.join(self.assets_path, "background_interno.jpg")
            if os.path.exists(bg_path):
                c.drawImage(bg_path, 0, 0, width=width, height=height, preserveAspectRatio=False, mask='auto')
        except:
            pass
    
    def extrair_dados(self, dados_completos):
        """Extrai dados do sistema e payback do JSON unificado"""
        dados_sistema = {}
        dados_payback = []
        
        for item in dados_completos:
            # Extrair dados de payback
            if "Gráfico Payback" in item and item.get("col_2"):
                # Limpar valores monetários
                if isinstance(item.get("col_2"), str):
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
        anos = []
        amortizacao = []
        
        for item in dados_payback:
            anos.append(item["ano"])
            amortizacao.append(item["amortizacao"])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        cores = ['#FF4444' if valor < 0 else '#FFD700' for valor in amortizacao]
        
        barras = ax.bar(anos, amortizacao, color=cores, width=0.7, edgecolor='none')
        
        ax.set_title('Gráfico Payback', fontsize=14, fontweight='bold', pad=15)
        
        ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        y_min = min(amortizacao) * 1.1 if min(amortizacao) < 0 else 0
        y_max = max(amortizacao) * 1.1
        ax.set_ylim(y_min, y_max)
        
        def format_currency(x, p):
            if x == 0:
                return 'R$ 0,00'
            elif x < 0:
                return f'-R$ {abs(x):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                return f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        
        from matplotlib.ticker import FuncFormatter
        ax.yaxis.set_major_formatter(FuncFormatter(format_currency))
        
        ax.set_xticks(anos)
        ax.set_xticklabels(anos, rotation=45, ha='right', fontsize=8)
        
        ax.axhline(y=0, color='black', linewidth=0.8, alpha=0.5)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
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
        
        # ========== PÁGINA 1: CAPA COM IMAGEM DE FUNDO ==========
        
        # Adicionar imagem de fundo
        try:
            bg_path = os.path.join(self.assets_path, "capa_background.png")
            if os.path.exists(bg_path):
                c.drawImage(bg_path, 0, 0, width=width, height=height, preserveAspectRatio=False)
        except:
            # Se não conseguir carregar a imagem, usar fundo branco
            c.setFillColor(colors.white)
            c.rect(0, 0, width, height, fill=1)
        
        # Nome do cliente e número da proposta centralizados no meio da página
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height/2, dados['cliente']['nome'].upper())
        
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height/2 - 30, f"PROPOSTA {dados['numero_proposta']}")
        
        c.showPage()
        
        # ========== PÁGINA 2: DADOS DO SISTEMA ==========
        # Adicionar fundo
        self.desenhar_fundo_interno(c, width, height)
        
        # Título sem box amarelo
        c.setFillColor(colors.HexColor('#366092'))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height - 80, "Proposta Comercial")
        
        c.setFont("Helvetica", 14)
        c.setFillColor(colors.HexColor('#366092'))
        c.drawCentredString(width/2, height - 105, "Sistema Fotovoltaico On-grid")
        
        # Tabela PROPOSTA COMERCIAL
        y_pos = height - 160
        c.setFillColor(colors.HexColor('#5B9BD5'))
        c.rect(50, y_pos, width - 100, 25, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(60, y_pos + 8, "PROPOSTA COMERCIAL")
        
        y_pos -= 30
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        
        # Dados do cliente
        dados_cliente = [
            ("CLIENTE", dados['cliente']['nome'].upper()),
            ("CPF/CNPJ", dados['cliente']['cpf_cnpj']),
            ("ENDEREÇO", dados['cliente']['endereco']),
            ("CIDADE", dados['cliente']['cidade'])
        ]
        
        for label, valor in dados_cliente:
            c.drawString(60, y_pos, label)
            c.drawString(200, y_pos, valor)
            y_pos -= 20
        
        # DADOS DO PERFIL DE CONSUMO
        y_pos -= 10
        c.setFillColor(colors.HexColor('#5B9BD5'))
        c.rect(50, y_pos, width - 100, 25, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(60, y_pos + 8, "DADOS DO PERFIL DE CONSUMO DO CLIENTE")
        
        y_pos -= 30
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        
        conta_antes = dados_sistema.get('conta_antes', 0)
        dados_consumo = [
            ("CONCESSIONÁRIA", "CPFL"),
            ("TIPO DE FORNECIMENTO", dados_sistema.get('tipo_fornecimento', 'Bifásico')),
            ("TENSÃO", "220V"),
            ("ÍNDICE DE RADIAÇÃO (kWh/m²)", "5.0"),
            ("CONSUMO MÉDIO ATUAL (kWh)", f"{dados_sistema.get('consumo_atual', 0):.0f}"),
            ("GERAÇÃO MÉDIA MENSAL (kWh)", f"{dados_sistema.get('geracao_mensal', 0):.0f}"),
            ("VALOR MÉDIO MENSAL DA CONTA", f"R$ {conta_antes:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        ]
        
        for label, valor in dados_consumo:
            c.drawString(60, y_pos, label)
            c.drawString(300, y_pos, valor)
            y_pos -= 20
        
        # SISTEMA FOTOVOLTAICO PROPOSTO
        y_pos -= 10
        c.setFillColor(colors.HexColor('#5B9BD5'))
        c.rect(50, y_pos, width - 100, 25, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(60, y_pos + 8, "SISTEMA FOTOVOLTAICO PROPOSTO")
        
        y_pos -= 30
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        
        dados_sfv = [
            ("NÚMERO DE MÓDULOS FOTOVOLTAICOS (un.)", f"{dados_sistema.get('num_modulos', 0)}"),
            ("POTÊNCIA TOTAL DO SISTEMA FOTOVOLTAICO (kWp)", f"{dados_sistema.get('potencia_kwp', 0)}"),
            ("ÁREA NECESSÁRIA (m²)", f"{dados_sistema.get('area_total', 0):.0f}")
        ]
        
        for label, valor in dados_sfv:
            c.drawString(60, y_pos, label)
            c.drawString(350, y_pos, valor)
            y_pos -= 20
        
        # Rodapé
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 30, "LEVESOL LTDA CNPJ 44.075.186/0001-11")
        c.drawCentredString(width/2, 20, "www.levesol.com.br")
        
        c.showPage()
        
        # ========== PÁGINA 3: ECONOMIA DE ENERGIA ==========
        # Adicionar fundo
        self.desenhar_fundo_interno(c, width, height)
        
        # Logo LEVESOL no topo
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(colors.HexColor('#366092'))
        c.drawString(50, height - 50, "LEVESOL")
        
        # Título sem box amarelo - usar verde escuro
        c.setFillColor(colors.HexColor('#2E7D32'))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height - 100, "Economia de Energia")
        
        # Tabela de economia
        y_pos = height - 150
        
        # Desenhar tabela com bordas
        c.setStrokeColor(colors.HexColor('#2E7D32'))
        c.setLineWidth(1)
        
        # Cabeçalho da tabela
        c.setFillColor(colors.HexColor('#E8F5E9'))
        c.rect(150, y_pos, 300, 25, fill=1, stroke=1)
        
        # Texto do cabeçalho
        c.setFillColor(colors.HexColor('#2E7D32'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(200, y_pos + 6, "ANO")
        c.drawString(300, y_pos + 11, "ECONOMIA MÉDIA DE")
        c.drawString(310, y_pos + 2, "ENERGIA MENSAL")
        
        y_pos -= 25
        
        # Dados de economia para 21 anos
        for i, item in enumerate(dados_payback[:21]):  # Limitar a 21 anos
            ano = item["ano"]
            economia = item["economia_mensal"]
            
            # Alternar cores de fundo
            if i % 2 == 0:
                c.setFillColor(colors.white)
            else:
                c.setFillColor(colors.HexColor('#F5F5F5'))
            
            c.rect(150, y_pos, 300, 20, fill=1, stroke=1)
            
            # Texto do ano
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 10)
            c.drawString(200, y_pos + 5, str(ano))
            
            # Economia em verde escuro
            c.setFillColor(colors.HexColor('#2E7D32'))
            c.setFont("Helvetica-Bold", 10)
            economia_fmt = f"R$ {economia:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            c.drawString(320, y_pos + 5, economia_fmt)
            
            y_pos -= 20
        
        # Nota no final
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor('#2E7D32'))
        c.drawCentredString(width/2, y_pos - 20, "Considerados reajustes anuais da tarifa de")
        c.drawCentredString(width/2, y_pos - 35, "energia, em média 5% ao ano.")
        
        # Rodapé
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 30, "LEVESOL LTDA CNPJ 44.075.186/0001-11")
        c.drawCentredString(width/2, 20, "Avenida Nossa Senhora de Fátima, 11-15, Jardim América, CEP 17017-337, Bauru")
        
        c.showPage()
        
        # ========== PÁGINA 4: ANÁLISE FINANCEIRA COM GRÁFICO ==========
        # Adicionar fundo
        self.desenhar_fundo_interno(c, width, height)
        
        # Título sem quadro amarelo
        c.setFillColor(colors.HexColor('#366092'))
        c.setFont("Helvetica-Bold", 20)
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
        
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.gray)
        c.drawString(100, height - 195, "*Esse é um orçamento inicial. O preço final é definido após visita técnica.")
        
        # Gerar e inserir gráfico
        if dados_payback:
            grafico_buffer = self.gerar_grafico_payback(dados_payback)
            img = ImageReader(grafico_buffer)
            c.drawImage(img, 60, height - 520, width=480, height=280, preserveAspectRatio=True)
        
        # Rodapé
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 30, "LEVESOL LTDA CNPJ 44.075.186/0001-11")
        c.drawCentredString(width/2, 20, "Avenida Nossa Senhora de Fátima, 11-15, Jardim América, CEP 17017-337, Bauru")
        c.drawCentredString(width/2, 10, "Contato: (14) 99893-7738 contato@levesol.com.br | www.levesol.com.br")
        
        c.showPage()
        
        # ========== PÁGINA 5: RETORNO DO INVESTIMENTO ==========
        # Adicionar fundo
        self.desenhar_fundo_interno(c, width, height)
        
        # Título sem box amarelo - usar verde escuro
        c.setFillColor(colors.HexColor('#2E7D32'))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height - 80, "Retorno do Investimento")
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - 105, "Payback")
        
        # Payback em destaque
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(colors.HexColor('#2E7D32'))
        payback_texto = f"{payback_anos} anos e {payback_meses} meses"
        c.drawCentredString(width/2, height - 140, payback_texto)
        
        # Tabela de retorno
        y_pos = height - 180
        
        # Cabeçalho da tabela
        c.setFillColor(colors.HexColor('#E8F5E9'))
        c.rect(150, y_pos, 300, 25, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#2E7D32'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(200, y_pos + 7, "ANO")
        c.drawString(330, y_pos + 7, "COM REAJUSTE")
        
        y_pos -= 25
        
        # Dados da tabela
        for i, item in enumerate(dados_payback[:21]):  # Limitar a 21 anos
            ano = item["ano"]
            amortizacao = item["amortizacao"]
            
            # Alternar cores de fundo
            if i % 2 == 0:
                c.setFillColor(colors.white)
            else:
                c.setFillColor(colors.HexColor('#F5F5F5'))
            
            c.setStrokeColor(colors.HexColor('#CCCCCC'))
            c.rect(150, y_pos, 300, 20, fill=1, stroke=1)
            
            # Ano
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 10)
            c.drawString(200, y_pos + 5, str(ano))
            
            # Valor com cor baseada em positivo/negativo
            if amortizacao < 0:
                valor_fmt = f"-R$ {abs(amortizacao):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                c.setFillColor(colors.red)
            else:
                valor_fmt = f"R$ {amortizacao:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                c.setFillColor(colors.HexColor('#2E7D32'))
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(330, y_pos + 5, valor_fmt)
            
            y_pos -= 20
            
            # Nova página se necessário
            if y_pos < 150 and i < 20:  # Ainda tem mais dados
                c.showPage()
                self.desenhar_fundo_interno(c, width, height)
                y_pos = height - 100
        
        # Caixa acumulado
        y_pos -= 30
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor('#2E7D32'))
        c.drawCentredString(width/2, y_pos, "CAIXA ACUMULADO EM 21 ANOS:")
        c.setFont("Helvetica-Bold", 20)
        economia_fmt = f"R$ {economia_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        c.drawCentredString(width/2, y_pos - 30, economia_fmt)
        
        # Notas
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.gray)
        c.drawString(100, 60, "*Neste retorno do investimento foram considerados reajustes")
        c.drawString(100, 45, "anuais da tarifa de energia, em média 5% ao ano")
        
        # Rodapé
        c.setFont("Helvetica", 8)
        c.drawCentredString(width/2, 25, "LEVESOL LTDA CNPJ 44.075.186/0001-11")
        c.drawCentredString(width/2, 15, "www.levesol.com.br")
        
        c.showPage()
        
        # ========== PÁGINA 6: LISTA DE SERVIÇOS ==========
        # Adicionar fundo
        self.desenhar_fundo_interno(c, width, height)
        
        # Logo LEVESOL no topo
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(colors.HexColor('#366092'))
        c.drawString(50, height - 50, "LEVESOL")
        
        # Título
        c.setFillColor(colors.HexColor('#366092'))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height - 100, "Lista de Serviços")
        c.setFont("Helvetica", 14)
        c.drawCentredString(width/2, height - 125, "Sistema Solar Fotovoltaico")
        
        # Tabela de serviços
        y_pos = height - 160
        
        # Cabeçalho da tabela
        c.setFillColor(colors.HexColor('#5B9BD5'))
        c.rect(50, y_pos, width - 100, 30, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width/2, y_pos + 10, "DESCRIÇÃO")
        
        y_pos -= 30
        
        # Lista de serviços usando dados reais do sistema
        num_modulos = dados_sistema.get('num_modulos', 20)
        potencia_inversor = dados_sistema.get('potencia_inversor', 10)
        
        servicos = [
            f"{num_modulos} MÓDULOS FOTOVOLTAICOS RISEN SUNX HONOR 700W",
            f"1 INVERSOR SOLAR DEYE {int(potencia_inversor)}KW",
            "ESTRUTURA COMPLETA PARA MONTAGEM",
            "PROTEÇÃO E CABEAMENTO CA/CC",
            "HOMOLOGAÇÃO",
            "INSTALAÇÃO",
            "MONITORAMENTO",
            "FRETE"
        ]
        
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.black)
        
        for servico in servicos:
            # Fundo alternado
            if servicos.index(servico) % 2 == 0:
                c.setFillColor(colors.white)
            else:
                c.setFillColor(colors.HexColor('#F5F5F5'))
            
            c.rect(50, y_pos, width - 100, 25, fill=1, stroke=0)
            
            # Texto
            c.setFillColor(colors.black)
            c.drawCentredString(width/2, y_pos + 8, servico)
            y_pos -= 25
        
        # Garantia de Material - seção com borda amarela
        y_pos -= 30
                
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#366092'))
        c.drawCentredString(width/2, y_pos + 42, "Garantia de Material")
        
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        c.drawString(70, y_pos + 22, "Inversores fotovoltaicos: Garantia de")
        c.drawString(70, y_pos + 8, "10 anos contra defeito de fabricação.")
        
        c.drawString(width/2 + 20, y_pos + 22, "Módulos fotovoltaicos: Garantia de geração")
        c.drawString(width/2 + 20, y_pos + 8, "nominal de 30 anos e 12 anos de garantia")
        c.drawString(width/2 + 20, y_pos - 6, "contra defeito de fabricação.")
        
        # Logos dos fornecedores - movido para baixo e maior
        y_pos -= 120
        try:
            logos_path = os.path.join(self.assets_path, "logos_fornecedores.png")
            if os.path.exists(logos_path):
                # Desenhar maior e centralizado
                c.drawImage(logos_path, 160, y_pos, width=width-320, height=200, 
                           preserveAspectRatio=True, mask='auto')
        except:
            # Se não houver imagem, listar os nomes
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.HexColor('#666666'))
            marcas = ["Growatt", "Solis", "JinKO", "Canadian", "SOFAR", "Deye", 
                     "WEG", "HonorSolar", "HUAWEI", "Risen", "TrinaSolar"]
            x_pos = 60
            for marca in marcas:
                c.drawString(x_pos, y_pos + 50, marca)
                x_pos += 45
                if x_pos > width - 100:
                    x_pos = 60
                    y_pos -= 15
        
        # Garantia de instalação - posição fixa no final
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor('#366092'))
        c.drawCentredString(width/2, 80, "GARANTIA DE 1 ANO DA INSTALAÇÃO ELÉTRICA")
        
        # Rodapé
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 50, "LEVESOL LTDA CNPJ 44.075.186/0001-11")
        c.drawCentredString(width/2, 40, "Avenida Nossa Senhora de Fátima, 11-15, Jardim América, CEP 17017-337, Bauru")
        c.drawCentredString(width/2, 30, f"Contato: (14) 99893-7738 contato@levesol.com.br")
        c.drawCentredString(width/2, 20, "www.levesol.com.br")
        
        c.save()
        
        buffer.seek(0)
        return buffer.getvalue()
