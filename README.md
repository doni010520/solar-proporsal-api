# ☀️ Solar Proposal API - LEVESOL

API para geração automática de propostas de energia solar fotovoltaica.

## 🚀 Funcionalidades

- ✅ Dimensionamento automático de sistemas solares
- ✅ Cálculo de geração e economia
- ✅ Análise financeira de 25 anos
- ✅ Geração de PDF profissional
- ✅ Suporta consumo único ou histórico de 13 meses
- ✅ Consideração da Lei 14.300
- ✅ Tabela de preços por faixa de potência

## 📋 Requisitos

- Docker e Docker Compose
- Ou Python 3.11+

## 🐳 Deploy com Docker (Easypanel/VPS)

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/solar-proposal-api.git
cd solar-proposal-api
```

### 2. Build e run com Docker Compose
```bash
docker-compose up -d
```

### 3. Verificar se está funcionando
```bash
curl http://localhost:8000/health
```

## 🔧 Instalação Local (sem Docker)

```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Rodar aplicação
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📖 Uso da API

### Endpoint Principal: `POST /api/proposta`

#### Exemplo 1: Consumo único (1 mês)

```bash
curl -X POST http://localhost:8000/api/proposta \
  -H "Content-Type: application/json" \
  -d '{
    "cliente": {
      "nome": "João Silva",
      "cpf_cnpj": "123.456.789-00",
      "endereco": "Rua ABC, 123",
      "cidade": "São Paulo-SP",
      "telefone": "11999999999"
    },
    "consumo": 700,
    "tipo_fornecimento": "bifasico",
    "concessionaria": "CPFL Paulista",
    "iluminacao_publica": 14.75
  }'
```

#### Exemplo 2: Histórico de 13 meses

```bash
curl -X POST http://localhost:8000/api/proposta \
  -H "Content-Type: application/json" \
  -d '{
    "cliente": {
      "nome": "João Silva",
      "cpf_cnpj": "123.456.789-00",
      "endereco": "Rua ABC, 123",
      "cidade": "São Paulo-SP"
    },
    "consumo": [650, 680, 720, 690, 700, 710, 680, 750, 730, 690, 700, 710, 695],
    "tipo_fornecimento": "bifasico",
    "iluminacao_publica": 14.75
  }'
```

### Resposta

```json
{
  "numero_proposta": "161025/2025",
  "consumo": {
    "consumo_medio_mensal": 700,
    "meses_informados": 1,
    "consumo_minimo": 700,
    "consumo_maximo": 700,
    "variacao_percentual": 0
  },
  "sistema": {
    "num_modulos": 9,
    "potencia_kwp": 6.3,
    "potencia_inversor": 5.0,
    "nome_inversor": "Inversor 5kW",
    "area_necessaria_m2": 42.0,
    "geracao_media_mensal_kwh": 650.0,
    "geracao_media_diaria_kwh": 21.67,
    "geracao_media_anual_kwh": 7909.75
  },
  "financeiro": {
    "investimento_total": 18500.00,
    "valor_conta_atual_mensal": 600.00,
    "valor_conta_com_sistema_mensal": 120.00,
    "economia_mensal_ano1": 480.00,
    "economia_25_anos": 245000.00
  },
  "economia_por_ano": [...],
  "pdf_base64": "JVBERi0xLjQKJeLjz9MKMy..."
}
```

## 📝 Parâmetros de Entrada

| Campo | Tipo | Obrigatório | Padrão | Descrição |
|-------|------|-------------|--------|-----------|
| `cliente.nome` | string | ✅ | - | Nome completo do cliente |
| `cliente.cpf_cnpj` | string | ✅ | - | CPF ou CNPJ |
| `cliente.endereco` | string | ✅ | - | Endereço completo |
| `cliente.cidade` | string | ✅ | - | Cidade e estado |
| `cliente.telefone` | string | ❌ | - | Telefone de contato |
| `consumo` | number ou array | ✅ | - | Consumo em kWh (1 mês ou 13 meses) |
| `tipo_fornecimento` | string | ✅ | - | "monofasico", "bifasico" ou "trifasico" |
| `concessionaria` | string | ❌ | "CPFL Paulista" | Nome da concessionária |
| `tensao` | string | ❌ | "220V" | Tensão da rede |
| `iluminacao_publica` | number | ❌ | 14.75 | Taxa de iluminação pública |
| `icms` | number | ❌ | 0.18 | Alíquota de ICMS |
| `pis` | number | ❌ | 0.0099 | Alíquota de PIS |
| `cofins` | number | ❌ | 0.0463 | Alíquota de COFINS |
| `radiacao_solar` | number | ❌ | 5.0 | Radiação solar (kWh/m²/dia) |
| `potencia_modulo` | number | ❌ | 700 | Potência do módulo (Wp) |

## 🔍 Endpoints Adicionais

### Health Check
```bash
GET /health
```

### Configurações
```bash
GET /api/config
```

### Documentação Interativa
```bash
GET /docs
```

## 📊 Como Funciona

### 1. Dimensionamento
- Calcula quantidade de módulos baseado no consumo
- Seleciona inversor apropriado
- Determina área necessária

### 2. Análise Financeira
- Calcula economia mensal e anual
- Projeta 25 anos com reajuste de 5% ao ano
- Considera Lei 14.300 (percentuais de geração)

### 3. Geração de PDF
- Capa profissional
- Dados do cliente e sistema
- Tabela de economia de 25 anos
- Análise financeira completa

## 🛠️ Tecnologias

- **FastAPI** - Framework web
- **Pydantic** - Validação de dados
- **ReportLab** - Geração de PDFs
- **Docker** - Containerização

## 📦 Estrutura do Projeto

```
solar-proposal-api/
├── app/
│   ├── main.py              # API FastAPI
│   ├── models/
│   │   ├── input_data.py    # Schemas de entrada
│   │   └── output_data.py   # Schemas de saída
│   ├── core/
│   │   ├── calculator.py    # Dimensionamento
│   │   └── financial.py     # Análise financeira
│   ├── pdf/
│   │   └── generator.py     # Gerador de PDF
│   └── data/
│       ├── inversores.json  # Tabela de inversores
│       └── config.json      # Configurações
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🚀 Deploy no Easypanel

1. Criar novo projeto no Easypanel
2. Conectar ao repositório GitHub
3. Easypanel detectará automaticamente o Dockerfile
4. Deploy automático!

## 📞 Suporte

Para dúvidas ou sugestões, entre em contato:
- Email: contato@levesol.com.br
- Telefone: (14) 99893-7738

## 📄 Licença

Propriedade da LEVESOL LTDA.
