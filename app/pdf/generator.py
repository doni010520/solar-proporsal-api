from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
from typing import Dict
import io


class PDFGenerator:
    def __init__(self):
        self.width, self.height = A4
        self.margin = 2 * cm
        
    def criar_proposta(self, dados: Dict) -> bytes:
        """
        Cria PDF da proposta completa
        Retorna bytes do PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Elementos do PDF
        elements = []
        
        # Estilos
        styles = self._criar_estilos()
        
        # Página 1: Capa
        elements.extend(self._criar_capa(dados, styles))
        elements.append(PageBreak())
        
        # Página 2: Dados do cliente e sistema
        elements.extend(self._criar_pagina_dados(dados, styles))
        elements.append(PageBreak())
        
        # Página 3: Economia de energia
        elements.extend(self._criar_pagina_economia(dados, styles))
        elements.append(PageBreak())
        
        # Página 4: Análise financeira
        elements.extend(self._criar_pagina_financeira(dados, styles))
        
        # Gerar PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _criar_estilos(self):
        """Cria estilos personalizados"""
        styles = getSampleStyleSheet()
        
        # Título principal
        styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        
        # Subtítulo
        styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=12
        ))
        
        # Seção
        styles.add(ParagraphStyle(
            name='Secao',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.white,
            backColor=colors.HexColor('#3b82f6'),
            alignment=TA_CENTER,
            spaceAfter=20,
            spaceBefore=10,
            leftIndent=10,
            rightIndent=10
        ))
        
        return styles
    
    def _criar_capa(self, dados: Dict, styles):
        """Cria página de capa"""
        elements = []
        
        # Logo LEVESOL (texto por enquanto)
        titulo = Paragraph("LEVESOL", styles['TituloPrincipal'])
        elements.append(titulo)
        
        subtitulo = Paragraph("ENERGIA SOLAR FOTOVOLTAICA", styles['Subtitulo'])
        elements.append(subtitulo)
        
        elements.append(Spacer(1, 3*cm))
        
        # Informações da proposta
        proposta_texto = f"""
        <para align=center fontSize=16>
        <b>PROPOSTA COMERCIAL</b><br/>
        {dados['numero_proposta']}<br/><br/>
        ANEXO I<br/>
        {dados['cliente']['nome']}<br/><br/>
        (14) 99893-7738
        </para>
        """
        elements.append(Paragraph(proposta_texto, styles['Normal']))
        
        return elements
    
    def _criar_pagina_dados(self, dados: Dict, styles):
        """Cria página com dados do cliente e sistema"""
        elements = []
        
        # Título
        elements.append(Paragraph("Proposta Comercial", styles['Secao']))
        elements.append(Paragraph("Sistema Fotovoltaico On-grid", styles['Subtitulo']))
        elements.append(Spacer(1, 1*cm))
        
        # Tabela de dados do cliente
        elements.append(Paragraph("PROPOSTA COMERCIAL", styles['Subtitulo']))
        
        dados_cliente = [
            ["CLIENTE", dados['cliente']['nome']],
            ["CPF/CNPJ", dados['cliente']['cpf_cnpj']],
            ["ENDEREÇO", dados['cliente']['endereco']],
            ["CIDADE", dados['cliente']['cidade']]
        ]
        
        table_cliente = Table(dados_cliente, colWidths=[6*cm, 10*cm])
        table_cliente.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#e0f2fe')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table_cliente)
        elements.append(Spacer(1, 1*cm))
        
        # Dados do perfil de consumo
        elements.append(Paragraph("DADOS DO PERFIL DE CONSUMO DO CLIENTE", styles['Subtitulo']))
        
        dados_consumo = [
            ["CONCESSIONÁRIA", dados.get('concessionaria', 'CPFL')],
            ["TIPO DE FORNECIMENTO", dados['tipo_fornecimento'].capitalize()],
            ["TENSÃO", dados.get('tensao', '220V')],
            ["ÍNDICE DE RADIAÇÃO (KW/m²)", str(dados.get('radiacao_solar', 5))],
            ["CONSUMO MÉDIO ATUAL (KWH)", str(int(dados['consumo']['consumo_medio_mensal']))],
            ["GERAÇÃO MÉDIA MENSAL (KWH)", str(int(dados['sistema']['geracao_media_mensal_kwh']))],
            ["VALOR MÉDIO MENSAL DA CONTA", f"R$ {dados['financeiro']['valor_conta_atual_mensal']:.2f}"]
        ]
        
        table_consumo = Table(dados_consumo, colWidths=[8*cm, 8*cm])
        table_consumo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#e0f2fe')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table_consumo)
        elements.append(Spacer(1, 1*cm))
        
        # Sistema proposto
        elements.append(Paragraph("SISTEMA FOTOVOLTAICO PROPOSTO", styles['Subtitulo']))
        
        dados_sistema = [
            ["NÚMERO DE MÓDULOS FOTOVOLTAICOS (un.)", str(dados['sistema']['num_modulos'])],
            ["POTÊNCIA TOTAL DO SISTEMA FOTOVOLTAICO (kWp)", str(dados['sistema']['potencia_kwp'])],
            ["ÁREA NECESSÁRIA (m²)", str(int(dados['sistema']['area_necessaria_m2']))]
        ]
        
        table_sistema = Table(dados_sistema, colWidths=[10*cm, 6*cm])
        table_sistema.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#e0f2fe')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table_sistema)
        
        return elements
    
    def _criar_pagina_economia(self, dados: Dict, styles):
        """Cria página de economia de energia"""
        elements = []
        
        elements.append(Paragraph("Economia de Energia", styles['Secao']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Texto explicativo
        texto = Paragraph(
            "Considerados reajustes anuais da tarifa de energia, em média 5% ao ano.",
            styles['Normal']
        )
        elements.append(texto)
        elements.append(Spacer(1, 1*cm))
        
        # Tabela de economia por ano
        tabela_dados = [["ANO", "ECONOMIA MÉDIA DE ENERGIA MENSAL"]]
        
        for economia in dados['economia_por_ano']:
            tabela_dados.append([
                str(economia['ano']),
                f"R$ {economia['economia_mensal']:.2f}"
            ])
        
        table = Table(tabela_dados, colWidths=[4*cm, 8*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')])
        ]))
        elements.append(table)
        
        return elements
    
    def _criar_pagina_financeira(self, dados: Dict, styles):
        """Cria página de análise financeira"""
        elements = []
        
        elements.append(Paragraph("Análise Financeira", styles['Secao']))
        elements.append(Spacer(1, 1*cm))
        
        # Investimento
        investimento_dados = [["Investimento", f"R$ {dados['financeiro']['investimento_total']:,.2f}"]]
        
        table_inv = Table(investimento_dados, colWidths=[8*cm, 8*cm])
        table_inv.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#3b82f6')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#22c55e')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ]))
        elements.append(table_inv)
        elements.append(Spacer(1, 0.5*cm))
        
        nota = Paragraph(
            "*Esse é um orçamento inicial. O preço final é definido após visita técnica.",
            styles['Normal']
        )
        elements.append(nota)
        elements.append(Spacer(1, 2*cm))
        
        # Economia acumulada
        economia_texto = f"""
        <para align=center fontSize=14>
        <b>ECONOMIA ACUMULADA EM 25 ANOS:</b><br/>
        <font size=18 color=#22c55e>
        R$ {dados['financeiro']['economia_25_anos']:,.2f}
        </font>
        </para>
        """
        elements.append(Paragraph(economia_texto, styles['Normal']))
        
        return elements
