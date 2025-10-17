from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
from typing import Dict, List
from pathlib import Path
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


class PDFGenerator:
    """Gerador de PDF no padrão LEVESOL"""
    
    def __init__(self):
        self.width, self.height = A4
        self.margin = 2 * cm
        
        # Caminhos das imagens
        self.assets_path = Path(__file__).parent / "assets"
        self.capa_background = self.assets_path / "capa_background.png"
        self.logos_fornecedores = self.assets_path / "logos_fornecedores.png"
        self.assinatura_gabriel = self.assets_path / "assinatura_gabriel.png"
        
        # Dados da proposta (será preenchido ao criar)
        self.dados_proposta = {}
        
        # Cores
        self.cor_amarela = colors.HexColor('#FDB913')  # Amarelo LEVESOL
        self.cor_azul_escuro = colors.HexColor('#2C5F7E')  # Azul tabelas
        self.cor_cinza = colors.HexColor('#666666')
        
    def criar_proposta(self, dados: Dict) -> bytes:
        """Cria PDF da proposta completa no padrão LEVESOL"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=2.5*cm  # Mais espaço para rodapé
        )
        
        elements = []
        styles = self._criar_estilos()
        
        # Guardar dados para usar na capa
        self.dados_proposta = dados
        
        # Página 1: Capa (será desenhada via callback)
        # Adicionar apenas um parágrafo vazio para criar a primeira página
        elements.append(Paragraph("", styles['Normal']))
        elements.append(PageBreak())
        
        # Página 2: Informações da Proposta
        elements.extend(self._criar_pagina_informacoes(dados, styles))
        elements.append(PageBreak())
        
        # Página com Gráfico Payback
        elements.extend(self._criar_pagina_payback(dados, styles))
        elements.append(PageBreak())
        
        # Página Lista de Serviços
        elements.extend(self._criar_lista_servicos(dados, styles))
        elements.append(PageBreak())
        
        # Página final: Prazos e Assinatura
        elements.extend(self._criar_pagina_prazos(dados, styles))
        
        # Gerar PDF com capa na primeira página e rodapé nas demais
        doc.build(elements, onFirstPage=self._desenhar_capa, onLaterPages=self._adicionar_rodape)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _criar_estilos(self):
        """Cria estilos personalizados"""
        styles = getSampleStyleSheet()
        
        # Título capa
        styles.add(ParagraphStyle(
            name='TituloCapa',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#333333'),
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        # Título seção com borda amarela
        styles.add(ParagraphStyle(
            name='TituloSecaoAmarela',
            fontSize=18,
            textColor=colors.HexColor('#2C5F7E'),
            alignment=TA_CENTER,
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Texto normal
        styles.add(ParagraphStyle(
            name='TextoNormal',
            fontSize=10,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=5
        ))
        
        return styles
    
    def _criar_pagina_informacoes(self, dados: Dict, styles):
        """Cria página com informações da proposta (logo + tabelas)"""
        elements = []
        
        # Box título - Proposta Comercial
        titulo_data = [[
            Paragraph("<b><font size=18 color=#2C5F7E>Proposta Comercial</font></b><br/>"
                     "<font size=14 color=#2C5F7E>Sistema Fotovoltaico On-grid</font>", 
                     styles['Normal'])
        ]]
        
        table_titulo = Table(titulo_data, colWidths=[16*cm])
        table_titulo.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, self.cor_amarela),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(table_titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Tabela: PROPOSTA COMERCIAL
        proposta_header = [[Paragraph("<b>PROPOSTA COMERCIAL</b>", styles['Normal'])]]
        table_proposta_header = Table(proposta_header, colWidths=[16*cm])
        table_proposta_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.cor_azul_escuro),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table_proposta_header)
        
        proposta_data = [
            ["CLIENTE", dados['cliente']['nome'].upper()],
            ["CPF/CNPJ", dados['cliente'].get('cpf_cnpj', 'N/A')],
            ["ENDEREÇO", dados['cliente'].get('endereco', 'N/A')],
            ["CIDADE", dados['cliente'].get('cidade', 'N/A')]
        ]
        
        table_proposta = Table(proposta_data, colWidths=[8*cm, 8*cm])
        table_proposta.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table_proposta)
        elements.append(Spacer(1, 0.5*cm))
        
        # Tabela: DADOS DO PERFIL DE CONSUMO DO CLIENTE
        consumo_header = [[Paragraph("<b>DADOS DO PERFIL DE CONSUMO DO CLIENTE</b>", styles['Normal'])]]
        table_consumo_header = Table(consumo_header, colWidths=[16*cm])
        table_consumo_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.cor_azul_escuro),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table_consumo_header)
        
        consumo_data = [
            ["CONCESSIONÁRIA", dados.get('concessionaria', 'CPFL')],
            ["TIPO DE FORNECIMENTO", dados.get('tipo_fornecimento', 'Bifásico').capitalize()],
            ["TENSÃO", dados.get('tensao', '220V')],
            ["ÍNDICE DE RADIAÇÃO (KW/m²)", str(dados.get('radiacao_solar', 5))],
            ["CONSUMO MÉDIO ATUAL (KWH)", str(dados['consumo']['consumo_medio_mensal'])],
            ["GERAÇÃO MÉDIA MENSAL (KWH)", f"{dados['sistema']['geracao_media_mensal_kwh']:.0f}"],
            ["VALOR MÉDIO MENSAL DA CONTA", f"R$ {dados['financeiro']['valor_conta_atual_mensal']:.2f}"]
        ]
        
        table_consumo = Table(consumo_data, colWidths=[8*cm, 8*cm])
        table_consumo.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table_consumo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Tabela: SISTEMA FOTOVOLTAICO PROPOSTO
        sistema_header = [[Paragraph("<b>SISTEMA FOTOVOLTAICO PROPOSTO</b>", styles['Normal'])]]
        table_sistema_header = Table(sistema_header, colWidths=[16*cm])
        table_sistema_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.cor_azul_escuro),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table_sistema_header)
        
        sistema_data = [
            ["NÚMERO DE MÓDULOS FOTOVOLTAICOS (un.)", str(dados['sistema']['num_modulos'])],
            ["POTÊNCIA TOTAL DO SISTEMA FOTOVOLTAICO (kWp)", str(dados['sistema']['potencia_kwp'])],
            ["ÁREA NECESSÁRIA (m²)", f"{dados['sistema']['area_necessaria_m2']:.0f}"]
        ]
        
        table_sistema = Table(sistema_data, colWidths=[8*cm, 8*cm])
        table_sistema.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table_sistema)
        
        return elements
    
    def _desenhar_capa(self, canvas_obj, doc):
        """Desenha a capa na primeira página usando canvas"""
        canvas_obj.saveState()
        
        # Desenhar imagem de fundo (tamanho A4 completo)
        if self.capa_background.exists():
            canvas_obj.drawImage(
                str(self.capa_background),
                0, 0,  # Posição (canto inferior esquerdo)
                width=self.width,
                height=self.height,
                preserveAspectRatio=True,
                anchor='c'
            )
        
        # Adicionar textos dinâmicos sobre a imagem (ABAIXO DA LOGO)
        canvas_obj.setFillColor(colors.HexColor('#333333'))
        
        # ANEXO I
        canvas_obj.setFont('Helvetica-Bold', 16)
        canvas_obj.drawCentredString(self.width / 2, 17*cm, "ANEXO I")
        
        # Nome do Cliente
        canvas_obj.setFont('Helvetica-Bold', 16)
        canvas_obj.drawCentredString(self.width / 2, 15.5*cm, self.dados_proposta['cliente']['nome'].upper())
        
        # PROPOSTA COMERCIAL
        canvas_obj.setFont('Helvetica-Bold', 16)
        canvas_obj.drawCentredString(self.width / 2, 14*cm, "PROPOSTA COMERCIAL")
        
        # Número da Proposta
        canvas_obj.setFont('Helvetica-Bold', 14)
        canvas_obj.drawCentredString(self.width / 2, 12.8*cm, self.dados_proposta['numero_proposta'])
        
        canvas_obj.restoreState()
    
    def _criar_capa_com_textos(self, canvas_obj, dados: Dict):
        """Método alternativo para adicionar textos sobre a imagem da capa"""
        # Este método seria chamado via callback no build do PDF
        # Por enquanto, vamos usar a imagem completa como está
        pass
    
    def _criar_grafico_payback(self, dados: Dict) -> io.BytesIO:
        """Cria gráfico de payback (barras amarelas/laranjas)"""
        # Dados de economia acumulada ao longo de 25 anos
        anos = []
        economia_acumulada = []
        economia_acum = 0
        
        ano_inicial = 2025
        for i, item in enumerate(dados['economia_por_ano']):
            anos.append(item['ano'])
            economia_acum += item['economia_mensal'] * 12
            economia_acumulada.append(economia_acum)
        
        # Criar gráfico
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Barras amarelas/laranjas
        bars = ax.bar(anos, economia_acumulada, color='#FDB913', alpha=0.9, width=0.8)
        
        # Configurações do gráfico
        ax.set_xlabel('Ano', fontsize=12, fontweight='bold')
        ax.set_ylabel('Economia Acumulada (R$)', fontsize=12, fontweight='bold')
        ax.set_title('Gráfico Payback', fontsize=14, fontweight='bold', color='#2C5F7E')
        
        # Formato do eixo Y (moeda)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'R$ {x:,.2f}'))
        
        # Grid
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Rotacionar labels do eixo X
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Salvar em buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def _criar_pagina_payback(self, dados: Dict, styles):
        """Cria página com box de investimento e gráfico payback"""
        elements = []
        
        # Box Investimento
        investimento_data = [[
            Paragraph("<b>Investimento</b>", styles['Normal']),
            Paragraph(f"<b>R$ {dados['financeiro']['investimento_total']:,.2f}</b>", styles['Normal'])
        ]]
        
        table_inv = Table(investimento_data, colWidths=[8*cm, 8*cm])
        table_inv.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, self.cor_amarela),
            ('LINEWIDTH', (0, 0), (-1, -1), 2),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(table_inv)
        
        # Nota sobre orçamento
        nota = Paragraph(
            "<i>*Esse é um orçamento inicial. O preço final é definido após visita técnica.</i>",
            styles['Normal']
        )
        elements.append(nota)
        elements.append(Spacer(1, 1*cm))
        
        # Gráfico Payback
        try:
            grafico_buffer = self._criar_grafico_payback(dados)
            img_grafico = Image(grafico_buffer, width=17*cm, height=10*cm)
            elements.append(img_grafico)
        except Exception as e:
            elements.append(Paragraph(f"<i>Erro ao gerar gráfico: {str(e)}</i>", styles['Normal']))
        
        return elements
    
    def _criar_lista_servicos(self, dados: Dict, styles):
        """Cria página Lista de Serviços"""
        elements = []
        
        # Box título
        titulo_data = [[
            Paragraph("<b>Lista de Serviços</b><br/><font size=12>Sistema Solar Fotovoltaico</font>", 
                     styles['TituloSecaoAmarela'])
        ]]
        
        table_titulo = Table(titulo_data, colWidths=[16*cm])
        table_titulo.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, self.cor_amarela),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(table_titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Tabela de Descrição
        descricao_data = [
            [Paragraph("<b>DESCRIÇÃO</b>", styles['Normal'])],
            [f"{dados['sistema']['num_modulos']} MÓDULOS FOTOVOLTAICOS RISEN SUNX HONOR 700W"],
            [f"INVERSOR SOLAR DEYE {dados['sistema']['potencia_inversor']}KW"],
            ["ESTRUTURA COMPLETA PARA MONTAGEM"],
            ["PROTEÇÃO E CABEAMENTO CA/CC"],
            ["HOMOLOGAÇÃO"],
            ["INSTALAÇÃO"],
            ["MONITORAMENTO"],
            ["FRETE"]
        ]
        
        table_desc = Table(descricao_data, colWidths=[16*cm])
        table_desc.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), self.cor_azul_escuro),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table_desc)
        elements.append(Spacer(1, 0.5*cm))
        
        # Box Garantia
        garantia_data = [[
            Paragraph("<b>Garantia de Material</b>", styles['TituloSecaoAmarela'])
        ]]
        
        table_garantia_titulo = Table(garantia_data, colWidths=[16*cm])
        table_garantia_titulo.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, self.cor_amarela),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table_garantia_titulo)
        
        garantia_content = [[
            Paragraph("<b>Inversores fotovoltaicos:</b> Garantia de 10 anos contra defeito de fabricação.", 
                     styles['Normal']),
            Paragraph("<b>Módulos fotovoltaicos:</b> Garantia de geração nominal de 30 anos e 12 anos de garantia contra defeito de fabricação.", 
                     styles['Normal'])
        ]]
        
        table_garantia_content = Table(garantia_content, colWidths=[8*cm, 8*cm])
        table_garantia_content.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, self.cor_amarela),
            ('GRID', (0, 0), (-1, -1), 1, self.cor_amarela),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table_garantia_content)
        elements.append(Spacer(1, 0.5*cm))
        
        # Logos dos fornecedores
        if self.logos_fornecedores.exists():
            img_logos = Image(str(self.logos_fornecedores), width=16*cm, height=4*cm)
            elements.append(img_logos)
        
        return elements
    
    def _criar_pagina_prazos(self, dados: Dict, styles):
        """Cria página de Prazos e Assinatura"""
        elements = []
        
        # Box Prazos
        titulo_prazos = [[Paragraph("<b>Prazos</b>", styles['TituloSecaoAmarela'])]]
        table_titulo_prazos = Table(titulo_prazos, colWidths=[16*cm])
        table_titulo_prazos.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, self.cor_amarela),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table_titulo_prazos)
        
        # Texto dos prazos
        texto_prazos = """
        <b>PROPOSTA VÁLIDA POR 10 DIAS OU ENQUANTO DURAREM OS ESTOQUES.</b><br/>
        <b>Entrega dos Equipamentos:</b> 30 a 60 dias após pagamento da entrada ou valor integral<br/>
        <b>Instalação:</b> 7 a 15 dias após a entrega dos equipamentos<br/>
        <b>Início de Funcionamento do Sistema:</b> o prazo de funcionamento do sistema pode variar em média de 30 a 60 dias a contar da assinatura desta Proposta, a depender única e exclusivamente da concessionária de energia local, conforme regras da Aneel.
        """
        
        prazos_content = [[Paragraph(texto_prazos, styles['Normal'])]]
        table_prazos = Table(prazos_content, colWidths=[16*cm])
        table_prazos.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, self.cor_amarela),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(table_prazos)
        elements.append(Spacer(1, 1*cm))
        
        # Aceite
        aceite_texto = Paragraph(
            "<b>No aceite desta proposta, favor preencher e assinar os campos abaixo:</b>",
            styles['Normal']
        )
        elements.append(aceite_texto)
        elements.append(Spacer(1, 0.3*cm))
        
        # Local e Data
        hoje = datetime.now()
        local_data = Paragraph(
            f"BAURU-SP, {hoje.strftime('%d/%m/%Y')}",
            styles['Normal']
        )
        elements.append(local_data)
        elements.append(Spacer(1, 1*cm))
        
        # Campos para preenchimento
        campos_texto = """
        _____________________________________________<br/>
        Nome/Razão Social:<br/>
        CPF/CNPJ:<br/>
        RG:
        """
        elements.append(Paragraph(campos_texto, styles['Normal']))
        elements.append(Spacer(1, 2*cm))
        
        # Responsável Técnico
        responsavel_data = [[
            Paragraph("_____________________________________________", styles['Normal'])
        ]]
        
        if self.assinatura_gabriel.exists():
            # Adicionar imagem da assinatura
            img_assinatura = Image(str(self.assinatura_gabriel), width=5*cm, height=2*cm)
            elements.append(img_assinatura)
        
        responsavel_texto = """
        <b>GABRIEL SHAYEB</b><br/>
        Diretor<br/>
        Engenheiro Eletricista<br/>
        Engenheiro de Segurança do Trabalho<br/>
        CREA 5069575855
        """
        elements.append(Paragraph(responsavel_texto, styles['Normal']))
        
        return elements
    
    def _adicionar_rodape(self, canvas_obj, doc):
        """Adiciona rodapé em todas as páginas"""
        canvas_obj.saveState()
        
        # Linha separadora (opcional)
        canvas_obj.setStrokeColor(colors.HexColor('#CCCCCC'))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(2*cm, 2*cm, self.width - 2*cm, 2*cm)
        
        # Texto do rodapé
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(self.cor_cinza)
        
        rodape_texto = (
            "LEVESOL LTDA CNPJ 44.075.186/0001-13\n"
            "Avenida Nossa Senhora de Fátima, 11-15, Jardim América, CEP 17017-337, Bauru,\n"
            "Contato: (14) 99893-7738 contato@levesol.com.br\n"
            "www.levesol.com.br"
        )
        
        # Desenhar cada linha do rodapé
        linhas = rodape_texto.split('\n')
        y_pos = 1.5*cm
        for i, linha in enumerate(reversed(linhas)):
            canvas_obj.drawCentredString(self.width / 2, y_pos + (i * 0.35*cm), linha)
        
        canvas_obj.restoreState()


# Teste de geração
if __name__ == "__main__":
    # Dados de exemplo
    dados_teste = {
        "numero_proposta": "251037/2025",
        "cliente": {
            "nome": "HELDER FERNANDES DE AGUIAR",
            "cpf_cnpj": "123.456.789-00",
            "endereco": "Rua Teste, 123",
            "cidade": "Bauru-SP"
        },
        "consumo": {
            "consumo_medio_mensal": 700
        },
        "sistema": {
            "num_modulos": 20,
            "potencia_kwp": 14.0,
            "potencia_inversor": 10,
            "nome_inversor": "Inversor Solar Deye 10kW"
        },
        "financeiro": {
            "investimento_total": 31900.00
        },
        "economia_por_ano": [
            {"ano": 2025, "economia_mensal": 450.00},
            {"ano": 2026, "economia_mensal": 472.50},
            # ... dados dos 25 anos
        ]
    }
    
    generator = PDFGenerator()
    pdf_bytes = generator.criar_proposta(dados_teste)
    
    with open("proposta_teste.pdf", "wb") as f:
        f.write(pdf_bytes)
    
    print("PDF gerado: proposta_teste.pdf")


