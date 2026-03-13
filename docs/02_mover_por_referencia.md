# Mover por Referência
 
Move pontos de uma camada para as coordenadas exatas de pontos
de outra camada, usando um campo-chave como vínculo.
 
## O problema
 
Quando dois cadastros descrevem a mesma entidade mas com coordenadas
divergentes, e há um campo de código ou ID que permite vinculá-los,
esse script corrige a posição usando o cadastro de referência.
 
## Parâmetros
 
| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| De onde mover | Camada com coordenadas a corrigir | — |
| Para onde mover | Camada de referência | — |
| Campo chave origem | Campo de vínculo na camada origem | — |
| Campo chave destino | Campo de vínculo na referência | — |
| Distância mínima | Ignora pontos já coincidentes (metros) | 0.5m |
| Mover diretamente | Edita a camada original | Não |
 
## Lógica de limpeza de chave
 
O script normaliza os códigos antes de comparar:
remove prefixos comuns, zeros à esquerda e espaços.
Isso garante que '0042', '42' e 'COD042' sejam tratados como iguais.
 
## Saída
 
Modo direto: edita a camada original via dataProvider (batch).
Modo sink: gera nova camada com as geometrias corrigidas.
