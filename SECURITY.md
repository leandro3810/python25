# Segurança do projeto python25

## Boas práticas aplicadas

- Uso de cabeçalhos HTTP de segurança no servidor Express
- Rate limit por IP para reduzir abuso
- Limite de tamanho de payload em requisições
- Endpoint de saúde para observabilidade básica
- Redução de risco de XSS no frontend (sem `innerHTML` para conteúdo dinâmico)

## Recomendações operacionais

1. Defina variáveis de ambiente no servidor:
   - `PORT`
   - `RATE_LIMIT_MAX`
   - `RATE_LIMIT_WINDOW_MS`
   - `TRUST_PROXY` (`true` quando rodar atrás de proxy reverso)
2. Nunca commite tokens no repositório.
3. Execute CodeQL e revisão de dependências regularmente.
4. Use o workflow do n8n para monitoramento contínuo e abertura automática de issues.
5. O rate limit atual usa memória local do processo (adequado para uso simples); em produção distribuída, prefira backend compartilhado (ex.: Redis).

## Reporte de vulnerabilidades

Abra uma issue privada (ou canal seguro acordado pelo time) com:

- descrição do problema
- impacto potencial
- passos para reprodução
- sugestão de correção (se houver)
