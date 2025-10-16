# 🚀 Guia de Deploy - Easypanel

## Passo a Passo Completo

### 1. Preparar Repositório GitHub

1. Criar novo repositório no GitHub (ex: `solar-proposal-api`)
2. **Não** inicializar com README
3. Copiar a URL do repositório

### 2. Fazer Upload dos Arquivos

Você tem 2 opções:

#### Opção A: Upload via Interface Web do GitHub
1. Acesse seu repositório vazio
2. Clique em "uploading an existing file"
3. Arraste TODOS os arquivos e pastas do projeto
4. Commit

#### Opção B: Via Git (se tiver Git instalado localmente)
```bash
# Na pasta do projeto
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/solar-proposal-api.git
git push -u origin main
```

### 3. Deploy no Easypanel

#### 3.1. Acessar Easypanel
1. Acesse seu Easypanel na VPS
2. Faça login

#### 3.2. Criar Novo Projeto
1. Clique em **"Create Project"** ou **"New Service"**
2. Escolha **"Git Repository"**

#### 3.3. Conectar GitHub
1. Cole a URL do seu repositório
2. Autentique com GitHub se necessário
3. Selecione a branch `main`

#### 3.4. Configurações do Projeto

**Nome do Serviço:** `solar-proposal-api`

**Build Configuration:**
- Easypanel detectará automaticamente o Dockerfile
- Se não detectar, especifique: `Dockerfile` na raiz

**Port Configuration:**
- Port: `8000`
- Protocolo: `HTTP`

**Environment Variables (opcional):**
```
API_HOST=0.0.0.0
API_PORT=8000
API_ENVIRONMENT=production
```

**Domain:**
- Configure um domínio ou use o domínio padrão do Easypanel
- Ex: `solar-api.seudominio.com`

#### 3.5. Deploy
1. Clique em **"Deploy"** ou **"Create"**
2. Aguarde o build (pode levar 2-5 minutos)
3. Easypanel irá:
   - Fazer clone do repositório
   - Build da imagem Docker
   - Iniciar o container
   - Expor na porta configurada

### 4. Verificar Deploy

#### 4.1. Verificar Health
```bash
curl https://solar-api.seudominio.com/health
```

Deve retornar:
```json
{
  "status": "healthy",
  "timestamp": "2025-..."
}
```

#### 4.2. Verificar Documentação
Acesse no navegador:
```
https://solar-api.seudominio.com/docs
```

#### 4.3. Testar API
```bash
curl -X POST https://solar-api.seudominio.com/api/proposta \
  -H "Content-Type: application/json" \
  -d @example_request.json
```

### 5. Configurações Adicionais (Opcional)

#### 5.1. SSL/HTTPS
- Easypanel geralmente configura automaticamente
- Certifique-se de que está habilitado

#### 5.2. Logs
- Acesse logs pelo painel do Easypanel
- Ou via CLI: `docker logs solar-proposal-api`

#### 5.3. Restart Policy
- Certifique-se de que está configurado como: **"Always"** ou **"Unless Stopped"**

### 6. Atualizações Futuras

Quando fizer mudanças no código:

1. **Commit no GitHub:**
```bash
git add .
git commit -m "Descrição da mudança"
git push
```

2. **Redesploy no Easypanel:**
- Easypanel pode ter auto-deploy configurado
- Ou clique manualmente em "Redeploy" no painel

### 7. Troubleshooting

#### Container não inicia
```bash
# Ver logs
docker logs solar-proposal-api

# Verificar se porta 8000 está em uso
netstat -tuln | grep 8000
```

#### Erro 502 Bad Gateway
- Verificar se aplicação está rodando na porta correta (8000)
- Verificar logs do container

#### Dependências faltando
- Verificar se `requirements.txt` está completo
- Rebuild do container

### 8. Monitoramento

#### Health Check Endpoint
```bash
# Adicionar ao seu monitor
GET /health
```

#### Metrics (futuro)
- Considerar adicionar `/metrics` para Prometheus
- Logs estruturados para análise

---

## 🎉 Pronto!

Sua API de propostas solares está no ar!

**URL da API:** `https://solar-api.seudominio.com`
**Documentação:** `https://solar-api.seudominio.com/docs`

## 📞 Suporte

Se tiver problemas:
1. Verificar logs no Easypanel
2. Testar localmente com Docker
3. Verificar configurações de rede/firewall na VPS
