👋 Olá, sou @leandr3810
![01_mclaren_senna_black_livery_2_resized](https://github.com/user-attachments/assets/37df449d-7588-4553-8aff-7c73088b3eb6)
![PORCHE](https://github.com/user-attachments/assets/474fd3aa-7bd0-49af-a7da-04201bff8edc)



## Segurança aplicada no projeto

- Cabeçalhos de segurança HTTP no `servidor.js`
- Limite de requisições por IP para reduzir abuso
- Limite de payload em JSON e formulário
- Endpoint de saúde: `GET /health`
- Montagem segura de e-mail no frontend sem `innerHTML`

## Agente de manutenção com IA (n8n + Python)

Foi adicionado:

- Script Python: `automation/ai_maintenance_agent.py`
- Workflow n8n: `n8n/workflows/python25-ai-agent.json`

### Como usar no n8n

1. Importe o arquivo JSON do workflow no n8n.
2. Ajuste o node **Execute Command** para o caminho real do seu repositório.
3. Configure variáveis de ambiente no n8n:
   - `GH_OWNER`
   - `GH_REPO`
   - `GH_TOKEN` (opcional, mas recomendado para API GitHub)
   - `GH_CODE_SCANNING_ENABLED=true` (opcional, usar somente se o repositório tiver acesso ao endpoint de code scanning)
4. Ative o workflow.

### Execução manual do agente

```bash
python3 automation/ai_maintenance_agent.py --json
```

O agente gera um relatório JSON com:
- status local do repositório
- riscos básicos detectados
- recomendação de ação quando houver necessidade de atualização/manutenção

## Ambiente de demonstração da estrutura do projeto

Foi adicionado:

- Script Python: `automation/demo_ambiente_projeto.py`

### Como executar

```bash
python3 automation/demo_ambiente_projeto.py
```

### Saída em JSON

```bash
python3 automation/demo_ambiente_projeto.py --json
```

O ambiente de demonstração mostra:
- estrutura principal do repositório
- esquema de controle de dados
- esquema de sistemas
