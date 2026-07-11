# Python UV Starter

This is a simple Python [uv](https://docs.astral.uv) starter in Firebase Studio.

## Running

```
uv run main.py
```

## Add dependencies

```
uv add ruff
```

## Análise de Ativos IA

`public/analyzer/` é uma página onde você digita o código de um ativo (ação
brasileira, FII, ETF BR/US ou stock americana) e obtém:

- Gráfico e fundamentos via widgets do TradingView (gratuitos, sem chave de API).
- Três botões com IA (Claude, via `functions/main.py`): principais notícias,
  avaliação de tendência gráfica (alta/baixa/lateral) e avaliação
  fundamentalista (crescendo/estável/diminuindo). Os dados de mercado usados
  nessas análises vêm do `yfinance`.

### Configuração necessária (uma vez)

As Cloud Functions ficam atrás de login (Firebase Auth) para controlar o
custo de chamadas à API da Anthropic. Para habilitar:

1. No [console do Firebase](https://console.firebase.google.com/project/findash-55202/usage/details),
   faça upgrade do projeto para o plano **Blaze** (pay-as-you-go). O plano
   Spark (gratuito) não permite deploy de Cloud Functions.
2. Instale o [Firebase CLI](https://firebase.google.com/docs/cli) e faça login: `firebase login`.
3. Configure sua chave da API da Anthropic como segredo da função:
   ```
   firebase functions:secrets:set ANTHROPIC_API_KEY
   ```
4. Faça o deploy das funções:
   ```
   firebase deploy --only functions
   ```
5. Habilite Google/E-mail como provedores de login em
   Authentication > Sign-in method no console do Firebase (o app de Wheel
   Strategy já depende disso).

O deploy automático via GitHub Actions (`.github/workflows/main.yml`) só
publica o Hosting; o deploy de `functions/` é feito manualmente com o comando
acima sempre que `functions/main.py` mudar.
