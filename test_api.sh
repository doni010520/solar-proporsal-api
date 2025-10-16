#!/bin/bash

echo "🚀 Testando Solar Proposal API..."
echo ""

# Verificar se API está rodando
echo "1. Verificando health check..."
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""
echo ""

# Testar criação de proposta
echo "2. Criando proposta de teste..."
curl -X POST http://localhost:8000/api/proposta \
  -H "Content-Type: application/json" \
  -d '{
    "cliente": {
      "nome": "Cliente Teste",
      "cpf_cnpj": "123.456.789-00",
      "endereco": "Rua Teste, 123",
      "cidade": "São Paulo-SP",
      "telefone": "11999999999"
    },
    "consumo": 700,
    "tipo_fornecimento": "bifasico",
    "iluminacao_publica": 14.75
  }' | python3 -m json.tool
echo ""
echo ""

echo "✅ Teste completo!"
echo ""
echo "📖 Acesse a documentação em: http://localhost:8000/docs"
