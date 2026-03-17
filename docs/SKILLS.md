# Guia de Habilidades do NexusClaw

## Visão Geral

As habilidades (skills) são a forma de expandir as capacidades do NexusClaw. Cada habilidade é uma função que o agente pode chamar para realizar tarefas específicas.

## Habilidades Built-in

### 1. Web Search (`web_search`)

Busca informações na web de forma privada usando SearXNG local.

**Parâmetros:**
- `query` (string, obrigatório): Termo de busca
- `num_results` (number, opcional): Número de resultados (padrão: 5)

**Exemplo de uso:**
```
web_search(query="python async tutorial", num_results=10)
```

**Retorno:**
```json
{
  "success": true,
  "query": "python async tutorial",
  "results": [
    {
      "title": "Async IO in Python",
      "url": "https://example.com/article",
      "content": "Artigo sobre async IO...",
      "engine": "google"
    }
  ]
}
```

---

### 2. File Operations (`file_operations`)

Gerencia arquivos no sistema local.

**Parâmetros:**
- `action` (string, obrigatório): Ação a executar
  - `read`: Ler arquivo
  - `write`: Escrever arquivo
  - `list`: Listar diretório
  - `delete`: Deletar arquivo/diretório
  - `exists`: Verificar existência
- `path` (string, obrigatório): Caminho do arquivo
- `content` (string, opcional): Conteúdo para escrever

**Exemplos:**
```
# Ler arquivo
file_operations(action="read", path="/data/notes.txt")

# Escrever arquivo
file_operations(action="write", path="/data/notes.txt", content="Olá mundo!")

# Listar diretório
file_operations(action="list", path="/data")

# Verificar existência
file_operations(action="exists", path="/data/secret.txt")
```

---

### 3. Code Executor (`code_executor`)

Executa código em ambiente sandbox.

**Parâmetros:**
- `language` (string, obrigatório): Linguagem (`python` ou `bash`)
- `code` (string, obrigatório): Código a executar
- `timeout` (number, opcional): Timeout em segundos (padrão: 30)

**Exemplos:**
```
# Python
code_executor(language="python", code="print(2+2); result = [x**2 for x in range(5)]")

# Bash
code_executor(language="bash", code="ls -la /app")
```

---

### 4. Calculator (`calculator`)

Realiza cálculos matemáticos.

**Parâmetros:**
- `expression` (string, obrigatório): Expressão matemática

**Funções disponíveis:**
- `abs`, `max`, `min`, `pow`, `round`, `sum`
- `sqrt`, `sin`, `cos`, `tan`
- `log`, `log10`, `exp`
- `pi`, `e`

**Exemplos:**
```
calculator(expression="2+2*3")
calculator(expression="sqrt(16) + log(10)")
calculator(expression="sin(pi/2)")
```

---

## Criando Habilidades Personalizadas

### Estrutura Básica

Crie um arquivo em `skills/custom/`:

```python
from skills.base import BaseSkill, SkillMetadata

class MyCustomSkill(BaseSkill):
    metadata = SkillMetadata(
        name="minha_habilidade",
        description="Descrição do que faz",
        parameters={
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "number"}
            },
            "required": ["param1"]
        }
    )
    
    async def execute(self, **params) -> dict:
        # Sua lógica aqui
        return {"success": True, "result": "..."}
```

### Registro

A habilidade será automaticamente carregada na inicialização.

## Melhores Práticas

1. **Valide parâmetros**: Use o método `validate_params`
2. **Tratamento de erros**: Sempre retorne dicionário com `success` e `error`
3. **Documentação**: Use docstrings e metadados
4. **Async**: Use funções async para operações de I/O
5. **Testes**: Escreva testes para suas habilidades
