# Selecionar Pontos Isolados
 
Seleciona pontos de uma camada que não possuem nenhum vizinho
em uma camada de referência dentro de um raio configurável.
 
## O problema
 
Ao importar um levantamento novo para o cadastro, é preciso identificar
quais registros são realmente novos (não existem na base atual) versus
quais são duplicatas ou atualizações de registros já existentes.
 
## Parâmetros
 
| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| Camada de busca | Pontos a avaliar | — |
| Camada de referência | Base atual de comparação | — |
| Raio de busca | Distância máxima para considerar vizinho (metros) | 1m |
| Campo município | Campo de identificação do município | — |
| Campo mslink | Identificador único do ponto | — |
| Campo barramento | Código de vínculo elétrico | — |
| Criar camada de saída | Gera camada com os isolados em EPSG:4326 | Sim |
 
## Saída
 
- Seleção ativa na camada de busca (pontos isolados destacados)
- Camada opcional com os isolados reprojetados para EPSG:4326,
  incluindo lat/long como campos de atributo
