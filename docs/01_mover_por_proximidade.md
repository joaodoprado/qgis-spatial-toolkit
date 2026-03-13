# Mover por Proximidade
 
Move pontos de uma camada para a geometria mais próxima de outra camada,
dentro de uma distância máxima configurável.
 
## O problema
 
Em cadastros de infraestrutura urbana, é comum ter pontos levantados em campo
que precisam ser associados a estruturas já cadastradas, mas sem nenhum
campo de vínculo disponível — só a proximidade espacial.
 
## Parâmetros
 
| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| Camada origem | Pontos a serem movidos | — |
| Camada destino | Estruturas de referência | — |
| Modo | PONTO (1:1) ou GRUPO (compartilhado) | PONTO |
| Distância máxima | Raio de busca em metros | 10m |
| Máx. destinos testados | Vizinhos avaliados por ponto | 3 |
 
## Lógica
 
- Modo PONTO (1:1): cada destino só recebe um ponto origem.
  O vínculo é confirmado pela verificação reversa: o ponto origem
  deve ser o vizinho mais próximo do destino.
- Modo GRUPO: múltiplos pontos podem ir para o mesmo destino
  se compartilharem o mesmo identificador de grupo.
 
## Saída
 
Edita diretamente a camada origem. As alterações ficam pendentes
até o usuário salvar a camada.
