# Detector de Alvos
 
Gera polígonos de áreas com alto potencial de cadastro não registrado,
cruzando informações de múltiplas camadas de infraestrutura.
 
## O problema
 
Em redes de infraestrutura urbana, existem pontos que provavelmente
existem fisicamente em campo mas ainda não estão no cadastro.
Identificar essas áreas manualmente é inviável em bases grandes.
 
## Lógica de detecção
 
Um ponto é considerado candidato quando:
1. Não possui iluminação registrada em um raio próximo
2. Possui rede elétrica de baixa tensão próxima (infraestrutura existe)
3. Não é do tipo FlyTap (excluídos da análise)
 
Os candidatos são agrupados em clusters espaciais e cada cluster
gera um polígono de área de interesse, com buracos nas regiões
onde já existe registro de iluminação.
 
## Parâmetros
 
| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| Pontos (origem) | Camada de estruturas a analisar | — |
| Iluminação existente | Camada de referência de IP | — |
| Rede BT | Camada de rede elétrica BT | — |
| Dist. mínima IP | Raio de exclusão por IP existente | 8m |
| Dist. máxima BT | Raio de inclusão por BT próxima | 30m |
| Metade do cluster | Tamanho do quadrado de agrupamento | 30m |
| Buffer externo | Arredondamento do polígono final | 10m |
| Área mínima | Descarta polígonos muito pequenos (m²) | 600 |
 
## Saída
 
Camada de polígonos em EPSG:3857 com as áreas de interesse.
Cada polígono representa um cluster de pontos candidatos.
