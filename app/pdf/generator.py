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
        # --- CAMINHOS E ESTILOS ---
        self.assets_path = "app/pdf/assets/"
        self.styles = getSampleStyleSheet()
        self._setup_styles_and_palette()

    def _setup_styles_and_palette(self):
        """Define a paleta de cores, fontes e espaçamentos padrão."""
        # --- PALETA DE CORES ---
        self.COLOR_PRIMARY_BLUE = colors.HexColor('#2c3e50')
        self.COLOR_SECONDARY_BLUE = colors.HexColor('#3498db')
        self.COLOR_SUCCESS_GREEN = colors.HexColor('#27ae60')
        self.COLOR_LIGHT_GREEN_BG = colors.HexColor('#e8f5e9')
        self.COLOR_ACCENT_GOLD = colors.HexColor('#f1c40f')
        self.COLOR_TEXT = colors.HexColor('#34495e')
        self.COLOR_TEXT_LIGHT = colors.HexColor('#7f8c8d')
        self.COLOR_WHITE = colors.white
        self.COLOR_LIGHT_GRAY_BG = colors.HexColor('#ecf0f1')
        self.COLOR_RED_NEGATIVE = colors.HexColor('#e74c3c')
        self.COLOR_BORDER = colors.HexColor('#bdc3c7')

        # Cores em formato de string para Matplotlib
        self.COLOR_RED_NEGATIVE_HEX = '#e74c3c'
        self.COLOR_ACCENT_GOLD_HEX = '#f1c40f'
        self.COLOR_TEXT_HEX = '#34495e'

        # --- FONTES (AUMENTADAS) ---
        self.FONT_BOLD = 'Helvetica-Bold'
        self.FONT_NORMAL = 'Helvetica'
        
        # --- TAMANHOS DE FONTE (AUMENTADOS) ---
        self.FONT_SIZE_TITLE = 26  # era 22
        self.FONT_SIZE_SUBTITLE = 18  # era 16
        self.FONT_SIZE_BODY_LARGE = 13  # era 11
        self.FONT_SIZE_BODY = 12  # era 10
        self.FONT_SIZE_BODY_SMALL = 11  # era 9
        self.FONT_SIZE_FOOTER = 9  # era 8

        # --- ESPAÇAMENTOS ---
        self.SPACE_LARGE = 40
        self.SPACE_MEDIUM = 25
        self.SPACE_SMALL = 15
        self.LINE_SPACING = 18

    def _draw_header_logo(self, c, height):
        """Desenha o logo no canto superior esquerdo."""
        try:
            logo_path = os.path.join(self.assets_path, "levesol_logo.png")
            if os.path.exists(logo_path):
                c.drawImage(logo_path, 40, height - 70, width=150, 
                            preserveAspectRatio=True, mask='auto')
        except:
            pass

    def _draw_footer(self, c, width):
        """Desenha o rodapé padrão em uma página."""
        c.saveState()
        c.setFont(self.FONT_NORMAL, self.FONT_SIZE_FOOTER)
        c.setFillColor(self.COLOR_TEXT_LIGHT)
        c.drawCentredString(width/2, 45, "LEVESOL LTDA CNPJ 44.075.186/0001-11")
        c.drawCentredString(width/2, 33, "Avenida Nossa Senhora de Fátima, 11-15, Jardim América, CEP 17017-337, Bauru")
        c.drawCentredString(width/2, 21, "Contato: (14) 99893-7738 | contato@levesol.com.br | www.levesol.com.br")
        c.restoreState()

    def _draw_section_header(self, c, y_pos, title, width):
        """Desenha um cabeçalho de seção padronizado."""
        c.saveState()
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.rect(50, y_pos, width - 100, 28, fill=1, stroke=0)
        c.setFillColor(self.COLOR_WHITE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_BODY_LARGE)
        c.drawString(65, y_pos + 9, title.upper())
        c.restoreState()
        return y_pos - 28

    def desenhar_fundo_interno(self, c, width, height):
        """Adiciona o fundo padrão nas páginas internas"""
        try:
            bg_path = os.path.join(self.assets_path, "background_interno.jpg")
            if os.path.exists(bg_path):
                c.drawImage(bg_path, 0, 0, width=width, height=height, preserveAspectRatio=False, mask='auto')
        except:
            pass
    
    def _clean_currency(self, value_str):
        """
        Converte uma string de moeda para float de forma segura.
        Trata formatos:
        - R$ 10,416.00 (vírgula = milhar, ponto = decimal) 
        - R$ 10.416,00 (ponto = milhar, vírgula = decimal)
        - R$ 10416.00 (sem separador de milhar)
        """
        if value_str is None:
            return 0.0
        try:
            # Remove R$ e espaços
            s = str(value_str).replace("R$", "").strip()
            
            # Remove espaços internos
            s = s.replace(" ", "")
            
            # Detecta o formato baseado na posição dos separadores
            if ',' in s and '.' in s:
                # Verifica qual vem por último (é o decimal)
                pos_virgula = s.rfind(',')
                pos_ponto = s.rfind('.')
                
                if pos_ponto > pos_virgula:
                    # Formato: 10,416.00 (vírgula = milhar, ponto = decimal)
                    s = s.replace(',', '')  # Remove separador de milhar
                else:
                    # Formato: 10.416,00 (ponto = milhar, vírgula = decimal)
                    s = s.replace('.', '').replace(',', '.')
            elif ',' in s:
                # Apenas vírgula: pode ser decimal brasileiro
                # Se tiver mais de 2 dígitos após vírgula, é milhar
                partes = s.split(',')
                if len(partes[-1]) == 2:  # Formato: 123,45
                    s = s.replace(',', '.')
                else:  # Formato: 1,234 (milhar)
                    s = s.replace(',', '')
            
            return float(s)
        except (ValueError, TypeError) as e:
            print(f"Erro ao converter '{value_str}': {e}")
            return 0.0

    def extrair_dados(self, dados_completos):
        """Extrai dados do sistema e payback do JSON unificado"""
        dados_sistema = {}
        dados_payback = []
        
        for item in dados_completos:
            if "Gráfico Payback" in item and item.get("col_2"):
                try:
                    valor = self._clean_currency(item["col_2"])
                    economia = self._clean_currency(item["col_3"])
                    ano = int(item["Gráfico Payback"])
                    dados_payback.append({"ano": ano, "amortizacao": valor, "economia_mensal": economia})
                except (ValueError, TypeError):
                    continue
            
            if "DADOS DA CONTA DE ENERGIA" in item:
                campo = item["DADOS DA CONTA DE ENERGIA"]
                valor = item.get("col_7")
                
                key_map = {
                    "Consumo Total Permitido (mês) kwh:": "consumo_atual", 
                    "Quantidade de módulos necessários:": "num_modulos",
                    "Potência do sistema (kWp):": "potencia_kwp", 
                    "Potência do inversor:": "potencia_inversor",
                    "Área total instalada (m²):": "area_total", 
                    "Energia Média Gerada (mês) kwh:": "geracao_mensal",
                    "Energia Média Gerada (ano) kwh:": "geracao_anual", 
                    "Valor da conta antes do SFV:": "conta_antes",
                    "Valor da conta depois do SFV:": "conta_depois", 
                    "Preço do Sistema Dimensionado:": "investimento",
                    "Padrão do Cliente:": "tipo_fornecimento"
                }
                for key, mapped_key in key_map.items():
                    if campo == key:
                        if mapped_key == "num_modulos":
                            dados_sistema[mapped_key] = int(float(valor)) if valor else 0
                        elif mapped_key == "consumo_atual":
                            # Consumo Total Permitido mantém as casas decimais
                            dados_sistema[mapped_key] = float(valor) if valor else 0.0
                        elif mapped_key == "tipo_fornecimento":
                            dados_sistema[mapped_key] = str(valor) if valor else "N/A"
                        elif mapped_key in ["potencia_kwp", "potencia_inversor", "area_total", "geracao_mensal", "geracao_anual"]:
                            dados_sistema[mapped_key] = float(valor) if valor else 0.0
                        else:
                            dados_sistema[mapped_key] = self._clean_currency(valor)
        
        return dados_sistema, dados_payback

    def gerar_grafico_payback(self, dados_payback):
        """Gera o gráfico de payback com a nova paleta de cores."""
        anos = [item["ano"] for item in dados_payback]
        amortizacao = [item["amortizacao"] for item in dados_payback]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        cores = [self.COLOR_RED_NEGATIVE_HEX if valor < 0 else self.COLOR_ACCENT_GOLD_HEX for valor in amortizacao]
        
        ax.bar(anos, amortizacao, color=cores, width=0.7, edgecolor='none')
        
        ax.set_title('Análise de Retorno (Payback)', fontsize=16, fontweight='bold', pad=20, color=self.COLOR_TEXT_HEX)
        ax.grid(True, axis='y', alpha=0.4, linestyle='--', linewidth=0.7)
        ax.set_axisbelow(True)
        
        y_min = min(amortizacao) * 1.15 if min(amortizacao) < 0 else 0
        y_max = max(amortizacao) * 1.15
        ax.set_ylim(y_min, y_max)
        
        def format_currency(x, p):
            s = f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            return s
        
        from matplotlib.ticker import FuncFormatter
        ax.yaxis.set_major_formatter(FuncFormatter(format_currency))
        
        ax.set_xticks(anos)
        ax.tick_params(axis='x', labelsize=9)
        ax.tick_params(axis='y', labelsize=9)

        ax.axhline(y=0, color=self.COLOR_TEXT_HEX, linewidth=1, alpha=0.7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#dddddd')
        ax.spines['bottom'].set_color('#dddddd')
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
        buffer.seek(0)
        plt.close()
        return buffer
    
    def calcular_payback(self, dados_payback):
        """Calcula o período de payback"""
        for i, item in enumerate(dados_payback):
            if item["amortizacao"] > 0 and i > 0:
                valor_anterior = dados_payback[i-1]["amortizacao"]
                if valor_anterior < 0:
                    diferenca_anual = item["amortizacao"] - valor_anterior
                    if diferenca_anual > 0:
                        meses_para_zerar = (abs(valor_anterior) / (diferenca_anual / 12))
                        anos = i - 1
                        meses = int(meses_para_zerar)
                        if meses >= 12:
                            anos += meses // 12
                            meses %= 12
                        return anos, meses
        return 0, 0
    
    def criar_proposta_completa(self, dados):
        """Wrapper para manter compatibilidade com a API - chama gerar_pdf()"""
        return self.gerar_pdf(
            dados_entrada=dados["dados_completos"],
            nome_cliente=dados["cliente"]["nome"],
            cpf_cnpj=dados["cliente"].get("cpf_cnpj", "N/A"),
            output_filename="proposta.pdf"
        )

    def gerar_pdf(self, dados_entrada, nome_cliente, cpf_cnpj, output_filename="proposta.pdf"):
        """Gera um PDF de proposta completo."""
        dados_sistema, dados_payback = self.extrair_dados(dados_entrada)
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # ========== PÁGINA 1: CAPA ==========
        try:
            capa_path = os.path.join(self.assets_path, "capa_levesol.jpg")
            if os.path.exists(capa_path):
                c.drawImage(capa_path, 0, 0, width=width, height=height, preserveAspectRatio=False, mask='auto')
        except:
            pass

        c.setFillColor(self.COLOR_WHITE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE + 4)  # Aumentado
        c.drawCentredString(width/2, height - 500, "PROPOSTA COMERCIAL")
        
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_SUBTITLE + 2)  # Aumentado
        c.drawCentredString(width/2, height - 540, f"CLIENTE: {nome_cliente.upper()}")
        c.drawCentredString(width/2, height - 570, f"CPF/CNPJ: {cpf_cnpj}")
        
        c.setFont(self.FONT_NORMAL, self.FONT_SIZE_BODY)
        c.drawCentredString(width/2, height - 610, f"Proposta gerada em {datetime.now().strftime('%d/%m/%Y')}")
        c.showPage()

        # ========== PÁGINA 2: ANÁLISE DE CONSUMO ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 100, "Análise de Consumo")
        
        y_pos = height - 160
        consumo = dados_sistema.get('consumo_atual', 0)
        geracao_mensal = dados_sistema.get('geracao_mensal', 0)
        tipo_fornecimento = dados_sistema.get('tipo_fornecimento', 'N/A')

        info_data = [
            ("Consumo Médio Mensal", f"{consumo:.2f} kWh"),
            ("Geração Média Mensal Estimada", f"{geracao_mensal:.0f} kWh"),
            ("Padrão de Fornecimento", tipo_fornecimento)
        ]
        
        info_table = Table(info_data, colWidths=[250, 200])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.COLOR_PRIMARY_BLUE),
            ('BACKGROUND', (1, 0), (1, -1), self.COLOR_LIGHT_GRAY_BG),
            ('TEXTCOLOR', (0, 0), (0, -1), self.COLOR_WHITE),
            ('TEXTCOLOR', (1, 0), (1, -1), self.COLOR_TEXT),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), self.FONT_SIZE_BODY),
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 12), ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        
        info_table.wrapOn(c, width - 100, y_pos)
        info_table.drawOn(c, (width - 450)/2, y_pos - info_table._height)
        y_pos -= info_table._height + self.SPACE_LARGE

        c.setFont(self.FONT_BOLD, self.FONT_SIZE_SUBTITLE)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.drawCentredString(width/2, y_pos, "Comparativo de Consumo Mensal")
        y_pos -= 40

        # Gráfico de barras
        fig, ax = plt.subplots(figsize=(8, 4))
        categorias = ['Consumo Atual', 'Geração Estimada']
        valores = [consumo, geracao_mensal]
        cores = [self.COLOR_RED_NEGATIVE_HEX, self.COLOR_ACCENT_GOLD_HEX]
        bars = ax.bar(categorias, valores, color=cores, edgecolor=self.COLOR_TEXT_HEX, linewidth=1.5)
        
        for bar in bars:
            height_bar = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height_bar, f'{height_bar:.0f} kWh',
                    ha='center', va='bottom', fontsize=12, fontweight='bold', color=self.COLOR_TEXT_HEX)
        
        ax.set_ylabel('kWh', fontsize=12, fontweight='bold', color=self.COLOR_TEXT_HEX)
        ax.set_title('Análise Comparativa', fontsize=14, fontweight='bold', color=self.COLOR_TEXT_HEX)
        ax.tick_params(axis='both', labelsize=11, colors=self.COLOR_TEXT_HEX)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        c.drawImage(ImageReader(img_buffer), 80, y_pos - 250, width=width-160, height=230, preserveAspectRatio=True, mask='auto')
        
        self._draw_footer(c, width)
        c.showPage()

        # ========== PÁGINA 3: SISTEMA FOTOVOLTAICO ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 100, "Sistema Fotovoltaico Proposto")

        y_pos = height - 160
        num_modulos = dados_sistema.get('num_modulos', 0)
        potencia_kwp = dados_sistema.get('potencia_kwp', 0)
        potencia_inversor = dados_sistema.get('potencia_inversor', 0)
        area_total = dados_sistema.get('area_total', 0)

        system_data = [
            ("Quantidade de Módulos", f"{num_modulos} unidades"),
            ("Potência do Sistema", f"{potencia_kwp:.2f} kWp"),
            ("Potência do Inversor", f"{potencia_inversor:.2f} kW"),
            ("Área Total Estimada", f"{area_total:.2f} m²")
        ]

        system_table = Table(system_data, colWidths=[250, 200])
        system_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.COLOR_PRIMARY_BLUE),
            ('BACKGROUND', (1, 0), (1, -1), self.COLOR_LIGHT_GRAY_BG),
            ('TEXTCOLOR', (0, 0), (0, -1), self.COLOR_WHITE),
            ('TEXTCOLOR', (1, 0), (1, -1), self.COLOR_TEXT),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), self.FONT_SIZE_BODY),
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 12), ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        system_table.wrapOn(c, width - 100, y_pos)
        system_table.drawOn(c, (width - 450)/2, y_pos - system_table._height)
        y_pos -= system_table._height + self.SPACE_LARGE

        try:
            sistema_path = os.path.join(self.assets_path, "sistema_fotovoltaico.jpg")
            if os.path.exists(sistema_path):
                c.drawImage(sistema_path, 60, y_pos - 300, width=width-120, height=280, preserveAspectRatio=True, mask='auto')
        except:
            pass
        
        self._draw_footer(c, width)
        c.showPage()

        # ========== PÁGINA 4: INVESTIMENTO ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 100, "Investimento e Formas de Pagamento")

        y_pos = height - 160
        investimento = dados_sistema.get('investimento', 0)
        
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_SUBTITLE)
        c.setFillColor(self.COLOR_SUCCESS_GREEN)
        c.drawCentredString(width/2, y_pos, "VALOR TOTAL DO INVESTIMENTO")
        y_pos -= 35
        c.setFont(self.FONT_BOLD, 32)  # Aumentado
        c.drawCentredString(width/2, y_pos, f"R$ {investimento:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        y_pos -= self.SPACE_LARGE + 10

        c.setFont(self.FONT_BOLD, self.FONT_SIZE_SUBTITLE)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.drawCentredString(width/2, y_pos, "Formas de Pagamento")
        y_pos -= self.SPACE_MEDIUM

        payment_data = [
            ("À VISTA (PIX)", f"R$ {investimento:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')),
            ("PARCELADO EM ATÉ 12X", "Sujeito à aprovação de crédito")
        ]
        payment_table = Table(payment_data, colWidths=[280, 220])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLOR_LIGHT_GREEN_BG),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.COLOR_TEXT),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), self.FONT_SIZE_BODY),
            ('GRID', (0, 0), (-1, -1), 1.5, self.COLOR_SUCCESS_GREEN),
            ('LEFTPADDING', (0,0), (-1,-1), 15), ('RIGHTPADDING', (0,0), (-1,-1), 15),
            ('TOPPADDING', (0,0), (-1,-1), 12), ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))
        payment_table.wrapOn(c, width - 100, y_pos)
        payment_table.drawOn(c, (width - 500)/2, y_pos - payment_table._height)
        y_pos -= payment_table._height + self.SPACE_LARGE

        c.setFont(self.FONT_BOLD, self.FONT_SIZE_BODY_LARGE)
        c.setFillColor(self.COLOR_TEXT)
        c.drawCentredString(width/2, y_pos, "ECONOMIA MENSAL ESTIMADA")
        y_pos -= 30
        
        conta_antes = dados_sistema.get('conta_antes', 0)
        conta_depois = dados_sistema.get('conta_depois', 0)
        economia_mensal = conta_antes - conta_depois
        
        c.setFillColor(self.COLOR_SUCCESS_GREEN)
        c.setFont(self.FONT_BOLD, 28)  # Aumentado
        c.drawCentredString(width/2, y_pos, f"R$ {economia_mensal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        y_pos -= 30
        c.setFont(self.FONT_NORMAL, self.FONT_SIZE_BODY)
        c.setFillColor(self.COLOR_TEXT)
        c.drawCentredString(width/2, y_pos, f"(De R$ {conta_antes:,.2f} para R$ {conta_depois:,.2f})".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        self._draw_footer(c, width)
        c.showPage()

        # ========== PÁGINA 5: PAYBACK ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 100, "Análise Financeira")

        y_pos = height - 160
        payback_item = next((item for item in dados_payback if item['amortizacao'] >= 0), None)
        payback_anos = payback_item['ano'] if payback_item else 0
        payback_meses = 0
        
        economia_total = sum(item['economia_mensal'] * 12 for item in dados_payback[:21])
        
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_SUBTITLE)
        c.drawCentredString(width/2, y_pos, "Tempo Estimado para Retorno")
        y_pos -= 30
        c.setFillColor(self.COLOR_SUCCESS_GREEN)
        c.setFont(self.FONT_BOLD, 30)  # Aumentado
        c.drawCentredString(width/2, y_pos, f"{payback_anos} anos e {payback_meses} meses")

        y_pos -= self.SPACE_LARGE
        c.setFillColor(self.COLOR_TEXT)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_SUBTITLE)
        c.drawCentredString(width/2, y_pos, "Projeção de Caixa Acumulado (21 anos)")
        y_pos -= 30
        c.setFillColor(self.COLOR_SUCCESS_GREEN)
        c.setFont(self.FONT_BOLD, 30)  # Aumentado
        c.drawCentredString(width/2, y_pos, f"R$ {economia_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        y_pos -= self.SPACE_MEDIUM

        table_data = [("Ano", "Saldo Acumulado")]
        dynamic_styles = []
        for i, item in enumerate(dados_payback[:21]):
            saldo = item['amortizacao']
            table_data.append( (str(item['ano']), f"R$ {saldo:,.2f}") )
            if saldo < 0:
                dynamic_styles.append(('TEXTCOLOR', (1, i + 1), (1, i + 1), self.COLOR_RED_NEGATIVE))

        table = Table(table_data, colWidths=[150, 250])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLOR_WHITE),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), self.FONT_BOLD),
            ('FONTNAME', (0, 1), (-1, -1), self.FONT_NORMAL),
            ('FONTSIZE', (0, 0), (-1, -1), self.FONT_SIZE_BODY),  # Fonte da tabela aumentada
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLOR_WHITE, self.COLOR_LIGHT_GRAY_BG]),
        ])
        for s in dynamic_styles:
            style.add(*s)
        table.setStyle(style)
        
        table.wrapOn(c, width - 100, y_pos)
        table.drawOn(c, (width-400)/2, y_pos - table._height)
        
        self._draw_footer(c, width)
        c.showPage()
        
        # ========== PÁGINA 6: SERVIÇOS E GARANTIAS ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 80, "Equipamentos e Serviços Inclusos")

        y_pos = height - 130
        num_modulos = int(dados_sistema.get('num_modulos', 0))
        potencia_inversor = dados_sistema.get('potencia_inversor', 'N/A')
        
        # MODIFICADO: Adicionadas as 3 marcas de módulos e inversores
        servicos = [
            (f"{num_modulos} MÓDULOS FOTOVOLTAICOS RISEN / HONOR / SUNX 700W",),
            (f"1 INVERSOR SOLAR DEYE / GROWATT / SOLIS {potencia_inversor}KW",),
            ("ESTRUTURA COMPLETA PARA MONTAGEM",),
            ("PROTEÇÃO E CABEAMENTO CA/CC",),
            ("HOMOLOGAÇÃO",),
            ("INSTALAÇÃO E MÃO DE OBRA",),
            ("MONITORAMENTO",),
            ("FRETE",)
        ]

        table = Table(servicos, colWidths=[width - 120])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLOR_WHITE),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [self.COLOR_WHITE, self.COLOR_LIGHT_GRAY_BG]),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.COLOR_TEXT),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.FONT_NORMAL),
            ('FONTSIZE', (0, 0), (-1, -1), self.FONT_SIZE_BODY),  # Fonte aumentada
            ('INNERGRID', (0, 0), (-1, -1), 0.25, self.COLOR_BORDER),
            ('BOX', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 20),
            ('RIGHTPADDING', (0,0), (-1,-1), 20),
            ('TOPPADDING', (0,0), (-1,-1), 14),  # Aumentado
            ('BOTTOMPADDING', (0,0), (-1,-1), 14),  # Aumentado
        ]))
        table.wrapOn(c, width - 100, y_pos)
        table.drawOn(c, 60, y_pos - table._height)
        y_pos -= table._height + self.SPACE_LARGE

        c.setFont(self.FONT_BOLD, self.FONT_SIZE_SUBTITLE)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.drawCentredString(width/2, y_pos, "Garantia dos Equipamentos")
        y_pos -= self.SPACE_MEDIUM

        c.setFont(self.FONT_NORMAL, self.FONT_SIZE_BODY)
        c.setFillColor(self.COLOR_TEXT)
        c.drawCentredString(width/2, y_pos, "Inversores: Garantia de 10 anos contra defeitos de fabricação.")
        y_pos -= self.LINE_SPACING
        c.drawCentredString(width/2, y_pos, "Módulos: Garantia de 12 anos (produto) e 30 anos (eficiência de geração).")
        
        try:
            logos_path = os.path.join(self.assets_path, "logos_fornecedores.png")
            if os.path.exists(logos_path):
                c.drawImage(logos_path, 60, y_pos - 180, width=width-120, height=170, preserveAspectRatio=True, mask='auto')
        except:
            pass
        
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_BODY_LARGE)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.drawCentredString(width/2, 100, "GARANTIA DE 1 ANO DA INSTALAÇÃO")
        
        self._draw_footer(c, width)
        c.showPage()
        
        # ========== PÁGINA 7: PRAZOS E ASSINATURA ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 80, "Prazos e Validade")

        y_pos = height - 140
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_BODY_LARGE)  # Aumentado
        c.setFillColor(self.COLOR_TEXT)
        c.drawString(70, y_pos, "PROPOSTA VÁLIDA POR 10 DIAS OU ENQUANTO DURAREM OS ESTOQUES.")
        y_pos -= self.SPACE_MEDIUM

        text_style = ParagraphStyle(
            name='Terms',
            fontName=self.FONT_NORMAL,
            fontSize=self.FONT_SIZE_BODY,
            textColor=self.COLOR_TEXT,
            leading=self.LINE_SPACING + 2,  # Aumentado
            spaceAfter=self.SPACE_SMALL
        )
        
        text_items = [
            "<b>Entrega dos Equipamentos:</b> 30 a 60 dias após pagamento da entrada ou valor integral.",
            "<b>Instalação:</b> 7 a 15 dias após a entrega dos equipamentos.",
            "<b>Início de Funcionamento:</b> O prazo pode variar de 30 a 60 dias a contar da assinatura, dependendo exclusivamente da liberação da concessionária de energia local, conforme regras da Aneel."
        ]
        
        for item in text_items:
            p = Paragraph(item, text_style)
            p_w, p_h = p.wrapOn(c, width - 140, y_pos)
            p.drawOn(c, 70, y_pos - p_h)
            y_pos -= p_h + self.SPACE_SMALL

        y_pos -= self.SPACE_MEDIUM
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_BODY_LARGE)  # Aumentado
        c.drawString(70, y_pos, "No aceite desta proposta, favor preencher e assinar os campos abaixo:")
        y_pos -= self.SPACE_LARGE
        
        c.setFont(self.FONT_NORMAL, self.FONT_SIZE_BODY_LARGE)
        c.drawString(70, y_pos, f"BAURU-SP, {datetime.now().strftime('%d/%m/%Y')}")
        y_pos -= self.SPACE_LARGE

        fields = ["Nome/Razão Social:", "CPF/CNPJ:", "RG:"]
        field_x_start = [180, 130, 95]
        for i, field in enumerate(fields):
            c.drawString(70, y_pos, field)
            c.line(field_x_start[i], y_pos - 2, width - 70, y_pos - 2)
            y_pos -= self.SPACE_LARGE
        
        y_pos -= 60
        try:
            assinatura_path = os.path.join(self.assets_path, "assinatura_gabriel.png")
            if os.path.exists(assinatura_path):
                c.drawImage(assinatura_path, 70, y_pos, width=180, height=70, preserveAspectRatio=True, mask='auto')
        except:
            pass
        
        c.line(70, y_pos - 2, 350, y_pos - 2)
        y_pos -= self.SPACE_SMALL

        c.setFont(self.FONT_BOLD, self.FONT_SIZE_BODY_LARGE)
        c.drawString(70, y_pos, "GABRIEL SHAYEB")
        y_pos -= 15
        c.setFont(self.FONT_NORMAL, self.FONT_SIZE_BODY)
        details = ["Diretor", "Engenheiro Eletricista", "Engenheiro de Segurança do Trabalho", "CREA 5069575855"]
        for detail in details:
            c.drawString(70, y_pos, detail)
            y_pos -= 14

        self._draw_footer(c, width)
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
