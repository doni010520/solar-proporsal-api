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

        # --- FONTES ---
        self.FONT_BOLD = 'Helvetica-Bold'
        self.FONT_NORMAL = 'Helvetica'
        
        # --- TAMANHOS DE FONTE ---
        self.FONT_SIZE_TITLE = 26  # era 22 - AUMENTADO
        self.FONT_SIZE_SUBTITLE = 18  # era 16 - AUMENTADO
        self.FONT_SIZE_BODY_LARGE = 13  # era 11 - AUMENTADO
        self.FONT_SIZE_BODY = 12  # era 10 - AUMENTADO
        self.FONT_SIZE_BODY_SMALL = 11  # era 9 - AUMENTADO
        self.FONT_SIZE_FOOTER = 9  # era 8 - AUMENTADO

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
                    "Consumo Total Permitido (mês) kwh:": "consumo_atual",  # MUDADO
                    "Quantidade de módulos": "num_modulos",
                    "Potência do sistema": "potencia_kwp", "Potência do inversor": "potencia_inversor",
                    "Área total instalada": "area_total", "Energia Média Gerada (mês)": "geracao_mensal",
                    "Energia Média Gerada (ano)": "geracao_anual", "Valor da conta antes": "conta_antes",
                    "Valor da conta depois": "conta_depois", "Preço do Sistema": "investimento",
                    "Padrão do Cliente": "tipo_fornecimento"
                }
                
                for key_search, key_final in key_map.items():
                    if key_search in campo:
                        dados_sistema[key_final] = valor
                        break
        
        return dados_sistema, dados_payback

    def gerar_grafico_payback(self, dados_payback):
        """Gera o gráfico de barras do payback."""
        anos = [item['ano'] for item in dados_payback[:21]]
        amortizacao = [item['amortizacao'] for item in dados_payback[:21]]
        
        colors_bars = [self.COLOR_RED_NEGATIVE_HEX if v < 0 else self.COLOR_ACCENT_GOLD_HEX for v in amortizacao]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(anos, amortizacao, color=colors_bars, edgecolor=self.COLOR_TEXT_HEX, linewidth=0.8)
        ax.axhline(0, color='black', linewidth=1.2, linestyle='--')
        ax.set_xlabel('Ano', fontsize=12, color=self.COLOR_TEXT_HEX, weight='bold')
        ax.set_ylabel('Amortização (R$)', fontsize=12, color=self.COLOR_TEXT_HEX, weight='bold')
        ax.set_title('Projeção de Payback do Investimento (21 anos)', fontsize=14, color=self.COLOR_TEXT_HEX, weight='bold')
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.set_xticks(anos)
        ax.set_xticklabels(anos, rotation=45, ha='right')
        
        def format_currency(x, pos):
            return f'R$ {x/1000:.0f}k' if abs(x) >= 1000 else f'R$ {x:.0f}'
        ax.yaxis.set_major_formatter(plt.FuncFormatter(format_currency))
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf

    def gerar_grafico_consumo(self, consumo_atual, geracao_mensal):
        """Gera o gráfico de barras comparando consumo e geração."""
        categorias = ['Consumo Mensal\nAtual', 'Geração Média\nMensal']
        valores = [consumo_atual, geracao_mensal]
        colors_bars = [self.COLOR_RED_NEGATIVE_HEX, self.COLOR_ACCENT_GOLD_HEX]
        
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(categorias, valores, color=colors_bars, edgecolor=self.COLOR_TEXT_HEX, linewidth=1.2, width=0.5)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f} kWh', ha='center', va='bottom', fontsize=12, weight='bold', color=self.COLOR_TEXT_HEX)
        
        ax.set_ylabel('Energia (kWh)', fontsize=12, color=self.COLOR_TEXT_HEX, weight='bold')
        ax.set_title('Comparação: Consumo vs Geração', fontsize=14, color=self.COLOR_TEXT_HEX, weight='bold')
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.set_ylim(0, max(valores) * 1.15)
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf
    
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
        """
        Método principal que chama gerar_pdf com a estrutura de dados correta.
        Este é o método que o sistema externo chama.
        """
        dados_cliente = {
            'nome': dados['cliente']['nome'],
            'endereco': dados['cliente'].get('endereco', 'N/A'),
            'cpf_cnpj': dados['cliente'].get('cpf_cnpj', 'N/A')
        }
        
        return self.gerar_pdf(dados['dados_completos'], dados_cliente)

    def gerar_pdf(self, dados_json, dados_cliente):
        """
        Gera o PDF completo com a NOVA ORDEM:
        1. Capa
        2. Informação (Análise de Consumo)
        3. Material (Equipamentos e Garantias) - MOVIDO
        4. Valor com gráfico (Detalhes do Sistema) - MOVIDO
        5. Payback (21 anos)
        6. Economia (Mensal) - MOVIDO
        7. Prazos
        """
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        dados_sistema, dados_payback = self.extrair_dados(dados_json)
        
        # ========== PÁGINA 1: CAPA ==========
        try:
            capa_path = os.path.join(self.assets_path, "capa.jpg")
            if os.path.exists(capa_path):
                c.drawImage(capa_path, 0, 0, width=width, height=height, preserveAspectRatio=False, mask='auto')
        except:
            pass
        
        c.setFillColor(self.COLOR_WHITE)
        c.setFont(self.FONT_BOLD, 32)
        c.drawCentredString(width/2, height - 500, "PROPOSTA COMERCIAL")
        c.setFont(self.FONT_BOLD, 22)
        c.drawCentredString(width/2, height - 540, "SISTEMA DE ENERGIA SOLAR FOTOVOLTAICA")
        
        y_cliente = height - 610
        c.setFont(self.FONT_BOLD, 18)
        c.drawCentredString(width/2, y_cliente, f"Cliente: {dados_cliente.get('nome', 'N/A')}")
        y_cliente -= 30
        c.setFont(self.FONT_NORMAL, 16)
        endereco = dados_cliente.get('endereco', 'N/A')
        c.drawCentredString(width/2, y_cliente, f"Endereço: {endereco}")
        y_cliente -= 25
        c.drawCentredString(width/2, y_cliente, f"CPF/CNPJ: {dados_cliente.get('cpf_cnpj', 'N/A')}")
        
        c.showPage()
        
        # ========== PÁGINA 2: ANÁLISE DE CONSUMO (INFORMAÇÃO) ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 80, "Análise de Consumo")

        consumo_atual = self._clean_currency(dados_sistema.get('consumo_atual', 0))
        geracao_mensal = self._clean_currency(dados_sistema.get('geracao_mensal', 0))
        
        y_pos = height - 130
        c.setFont(self.FONT_NORMAL, self.FONT_SIZE_BODY_LARGE)
        c.setFillColor(self.COLOR_TEXT)
        c.drawString(70, y_pos, f"Consumo Mensal Atual: {consumo_atual:.0f} kWh")
        y_pos -= self.LINE_SPACING
        c.drawString(70, y_pos, f"Geração Média Mensal do Sistema: {geracao_mensal:.0f} kWh")
        y_pos -= self.SPACE_MEDIUM
        
        grafico_consumo = self.gerar_grafico_consumo(consumo_atual, geracao_mensal)
        img_reader = ImageReader(grafico_consumo)
        c.drawImage(img_reader, 80, y_pos - 300, width=450, height=280, preserveAspectRatio=True, mask='auto')
        y_pos -= 320
        
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_BODY_LARGE)
        c.setFillColor(self.COLOR_SUCCESS_GREEN)
        diferenca = geracao_mensal - consumo_atual
        if diferenca >= 0:
            c.drawString(70, y_pos, f"✓ O sistema gerará {diferenca:.0f} kWh A MAIS que seu consumo mensal!")
        else:
            c.setFillColor(self.COLOR_RED_NEGATIVE)
            c.drawString(70, y_pos, f"⚠ Atenção: O sistema gerará {abs(diferenca):.0f} kWh A MENOS que seu consumo.")
        
        self._draw_footer(c, width)
        c.showPage()
        
        # ========== PÁGINA 3: EQUIPAMENTOS E GARANTIAS (MATERIAL) - MOVIDO PARA FRENTE ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 80, "Equipamentos e Serviços Inclusos")

        y_pos = height - 130
        num_modulos = int(dados_sistema.get('num_modulos', 0))
        potencia_inversor = dados_sistema.get('potencia_inversor', 'N/A')
        
        servicos = [
            (f"{num_modulos} MÓDULOS FOTOVOLTAICOS RISEN / HONOR / SUNX 700W",), 
            (f"1 INVERSOR SOLAR DEYE / GROWATT / SOLIS {potencia_inversor}KW",),
            ("ESTRUTURA COMPLETA PARA MONTAGEM",), ("PROTEÇÃO E CABEAMENTO CA/CC",), ("HOMOLOGAÇÃO",),
            ("INSTALAÇÃO E MÃO DE OBRA",), ("MONITORAMENTO",), ("FRETE",)
        ]

        table = Table(servicos, colWidths=[width - 120])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLOR_WHITE),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [self.COLOR_WHITE, self.COLOR_LIGHT_GRAY_BG]),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.COLOR_TEXT),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.FONT_NORMAL),
            ('FONTSIZE', (0, 0), (-1, -1), self.FONT_SIZE_BODY),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, self.COLOR_BORDER),
            ('BOX', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 20), ('RIGHTPADDING', (0,0), (-1,-1), 20),
            ('TOPPADDING', (0,0), (-1,-1), 12), ('BOTTOMPADDING', (0,0), (-1,-1), 12),
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
        
        # LOGOS AUMENTADAS - de height=170 para height=220
        try:
            logos_path = os.path.join(self.assets_path, "logos_fornecedores.png")
            if os.path.exists(logos_path):
                c.drawImage(logos_path, 60, y_pos - 240, width=width-120, height=220, preserveAspectRatio=True, mask='auto')
        except:
            pass
        
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_BODY_LARGE)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.drawCentredString(width/2, 100, "GARANTIA DE 1 ANO DA INSTALAÇÃO")
        
        self._draw_footer(c, width)
        c.showPage()
        
        # ========== PÁGINA 4: DETALHES DO SISTEMA (VALOR COM GRÁFICO) - MOVIDO ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 80, "Detalhes do Sistema Fotovoltaico")
        
        y_pos = height - 120
        dados_tecnicos = [
            ("Potência do Sistema (kWp)", dados_sistema.get('potencia_kwp', 'N/A')),
            ("Número de Módulos", dados_sistema.get('num_modulos', 'N/A')),
            ("Potência do Inversor (kW)", dados_sistema.get('potencia_inversor', 'N/A')),
            ("Área Total Instalada (m²)", dados_sistema.get('area_total', 'N/A')),
            ("Geração Mensal Estimada (kWh)", dados_sistema.get('geracao_mensal', 'N/A')),
            ("Geração Anual Estimada (kWh)", dados_sistema.get('geracao_anual', 'N/A')),
            ("Tipo de Fornecimento", dados_sistema.get('tipo_fornecimento', 'N/A')),
        ]
        
        table_tech = Table(dados_tecnicos, colWidths=[280, 200])
        table_tech.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.COLOR_LIGHT_GRAY_BG),
            ('BACKGROUND', (1, 0), (1, -1), self.COLOR_WHITE),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.COLOR_TEXT),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (0, -1), self.FONT_BOLD),
            ('FONTNAME', (1, 0), (1, -1), self.FONT_NORMAL),
            ('FONTSIZE', (0, 0), (-1, -1), self.FONT_SIZE_BODY),
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 15), ('RIGHTPADDING', (0,0), (-1,-1), 15),
            ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        
        table_tech.wrapOn(c, width - 100, y_pos)
        table_tech.drawOn(c, (width - 480) / 2, y_pos - table_tech._height)
        y_pos -= table_tech._height + self.SPACE_LARGE
        
        y_pos = self._draw_section_header(c, y_pos, "Investimento", width)
        y_pos -= self.SPACE_SMALL
        
        investimento = self._clean_currency(dados_sistema.get('investimento', 0))
        c.setFont(self.FONT_BOLD, 32)
        c.setFillColor(self.COLOR_ACCENT_GOLD)
        c.drawCentredString(width/2, y_pos - 40, f"R$ {investimento:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        y_pos -= 80
        
        grafico_payback_buf = self.gerar_grafico_payback(dados_payback)
        img_reader = ImageReader(grafico_payback_buf)
        c.drawImage(img_reader, 50, y_pos - 320, width=500, height=300, preserveAspectRatio=True, mask='auto')
        
        self._draw_footer(c, width)
        c.showPage()
        
        # ========== PÁGINA 5: PAYBACK (PROJEÇÃO 21 ANOS) ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 80, "Análise de Retorno do Investimento")
        
        # CENTRALIZAÇÃO VERTICAL MELHORADA - começando mais alto
        y_pos = height - 140
        
        payback_item = next((item for item in dados_payback if item['amortizacao'] >= 0), None)
        payback_anos = payback_item['ano'] if payback_item else 0
        payback_meses = int((payback_item['amortizacao'] / payback_item['economia_mensal']) * 12) if payback_item and payback_item['economia_mensal'] > 0 else 0
        
        economia_total = dados_payback[20]['amortizacao'] if len(dados_payback) >= 21 else 0
        
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_SUBTITLE)
        c.setFillColor(self.COLOR_TEXT)
        c.drawCentredString(width/2, y_pos, "Tempo de Retorno do Investimento (Payback)")
        y_pos -= 30
        c.setFillColor(self.COLOR_SUCCESS_GREEN)
        c.setFont(self.FONT_BOLD, 28)
        c.drawCentredString(width/2, y_pos, f"{payback_anos} anos e {payback_meses} meses")

        y_pos -= self.SPACE_LARGE
        c.setFillColor(self.COLOR_TEXT)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_SUBTITLE)
        c.drawCentredString(width/2, y_pos, "Projeção de Caixa Acumulado (21 anos)")
        y_pos -= 30
        c.setFillColor(self.COLOR_SUCCESS_GREEN)
        c.setFont(self.FONT_BOLD, 28)
        c.drawCentredString(width/2, y_pos, f"R$ {economia_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        y_pos -= self.SPACE_MEDIUM + 10  # Espaço extra antes da tabela

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
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLOR_WHITE, self.COLOR_LIGHT_GRAY_BG]),
        ])
        for s in dynamic_styles:
            style.add(*s)
        table.setStyle(style)
        
        table.wrapOn(c, width - 100, y_pos)
        # Centralizado horizontalmente
        table.drawOn(c, (width-400)/2, y_pos - table._height)
        
        self._draw_footer(c, width)
        c.showPage()
        
        # ========== PÁGINA 6: ECONOMIA MENSAL - MOVIDO ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 80, "Simulação de Economia Mensal")
        
        # CENTRALIZAÇÃO VERTICAL MELHORADA - começando mais alto
        y_pos = height - 150
        
        conta_antes = self._clean_currency(dados_sistema.get('conta_antes', 0))
        conta_depois = self._clean_currency(dados_sistema.get('conta_depois', 0))
        economia_mensal = conta_antes - conta_depois
        economia_anual = economia_mensal * 12
        
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_SUBTITLE)
        c.setFillColor(self.COLOR_TEXT)
        c.drawCentredString(width/2, y_pos, "Economia Estimada")
        y_pos -= self.SPACE_MEDIUM
        
        economia_data = [
            ("Descrição", "Valor Mensal", "Valor Anual"),
            ("Conta de Energia (Antes)", f"R$ {conta_antes:,.2f}", f"R$ {conta_antes * 12:,.2f}"),
            ("Conta de Energia (Depois)", f"R$ {conta_depois:,.2f}", f"R$ {conta_depois * 12:,.2f}"),
            ("Economia", f"R$ {economia_mensal:,.2f}", f"R$ {economia_anual:,.2f}")
        ]
        
        for row in economia_data:
            for i, val in enumerate(row):
                if isinstance(val, str):
                    economia_data[economia_data.index(row)] = tuple(
                        v.replace(',', 'X').replace('.', ',').replace('X', '.') if isinstance(v, str) and 'R$' in v else v 
                        for v in row
                    )
                    break
        
        table_economia = Table(economia_data, colWidths=[200, 150, 150])
        table_economia.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLOR_WHITE),
            ('BACKGROUND', (0, 3), (-1, 3), self.COLOR_LIGHT_GREEN_BG),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.COLOR_TEXT),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), self.FONT_BOLD),
            ('FONTNAME', (0, 3), (-1, 3), self.FONT_BOLD),
            ('FONTNAME', (0, 1), (-1, 2), self.FONT_NORMAL),
            ('FONTSIZE', (0, 0), (-1, -1), self.FONT_SIZE_BODY),
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('ROWBACKGROUNDS', (0, 1), (-1, 2), [self.COLOR_WHITE, self.COLOR_LIGHT_GRAY_BG]),
            ('LEFTPADDING', (0,0), (-1,-1), 12), ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        
        table_economia.wrapOn(c, width - 100, y_pos)
        table_economia.drawOn(c, (width - 500) / 2, y_pos - table_economia._height)
        y_pos -= table_economia._height + self.SPACE_LARGE
        
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_BODY_LARGE)
        c.setFillColor(self.COLOR_SUCCESS_GREEN)
        c.drawCentredString(width/2, y_pos, f"Você economizará aproximadamente R$ {economia_mensal:,.2f} por mês!".replace(',', 'X').replace('.', ',').replace('X', '.'))
        y_pos -= self.LINE_SPACING
        c.drawCentredString(width/2, y_pos, f"Ou seja, R$ {economia_anual:,.2f} por ano!".replace(',', 'X').replace('.', ',').replace('X', '.'))
        y_pos -= self.SPACE_LARGE
        
        c.setFont(self.FONT_NORMAL, self.FONT_SIZE_BODY)
        c.setFillColor(self.COLOR_TEXT)
        texto_info = [
            "* Os valores consideram a tarifa atual de energia e podem variar conforme reajustes da concessionária.",
            "* A economia real dependerá do seu padrão de consumo e da geração efetiva do sistema.",
            "* Valores sujeitos a variações de irradiação solar e condições climáticas."
        ]
        for linha in texto_info:
            c.drawString(70, y_pos, linha)
            y_pos -= self.LINE_SPACING
        
        self._draw_footer(c, width)
        c.showPage()
        
        # ========== PÁGINA 7: PRAZOS E ASSINATURA ==========
        self.desenhar_fundo_interno(c, width, height)
        self._draw_header_logo(c, height)
        c.setFillColor(self.COLOR_PRIMARY_BLUE)
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_TITLE)
        c.drawCentredString(width/2, height - 80, "Prazos e Validade")

        y_pos = height - 140
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_BODY)
        c.setFillColor(self.COLOR_TEXT)
        c.drawString(70, y_pos, "PROPOSTA VÁLIDA POR 10 DIAS OU ENQUANTO DURAREM OS ESTOQUES.")
        y_pos -= self.SPACE_MEDIUM

        text_style = ParagraphStyle(name='Terms', fontName=self.FONT_NORMAL, fontSize=self.FONT_SIZE_BODY,
                                    textColor=self.COLOR_TEXT, leading=self.LINE_SPACING, spaceAfter=self.SPACE_SMALL)
        
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
        c.setFont(self.FONT_BOLD, self.FONT_SIZE_BODY)
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
        
        y_pos -= 60 # Ajuste para descer a assinatura
        try:
            assinatura_path = os.path.join(self.assets_path, "assinatura_gabriel.png")
            if os.path.exists(assinatura_path):
                c.drawImage(assinatura_path, 70, y_pos, width=180, height=70, preserveAspectRatio=True, mask='auto')
        except: pass
        
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
