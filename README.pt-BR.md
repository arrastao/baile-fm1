# BAILE by MULÚ

Instrumento de ritmos para o M-VAVE FM-1 com **Tamborzão, Voltmix e Beat Bolha**. Esta reconstrução começa no código oficial limpo do FM1 Open, revisão `4c7496daac04a95ff10d1afdcc8f9ead2dbabc41`, conferida como a mais recente em 08/11/2026. O projeto anterior foi preservado.

Na versão 0.7, os 12 samples recebem ajuste de ganho para aproximar o volume dos ataques, com margem nos picos. Os WAVs originais são preservados. [Detalhes](docs/AUDIO.md).

[Testar no navegador](https://arrastao.github.io/baile-fm1/) · [Baixar firmware estável](https://github.com/arrastao/baile-fm1/releases/download/v0.7.0/BAILE-0.7-FM1.fwsc)

## Uso

A arte de abertura do BAILE permanece completa por 3 segundos. Em seguida aparece o Tamborzão e os controles ficam ativos. PLAY inicia ou para o beat. PRESETS troca de kit; ALGORITHM seleciona uma das quatro trilhas; as 16 teclas brancas alternam os passos dessa trilha. Cada preset tem um único compasso de 16 passos; OCT −/+ fica sem função. K1 controla saturação, K2 reverb, K3 BPM e K4 swing.

Os três kits guardam suas edições separadamente durante a sessão. Ao reiniciar, volta o Tamborzão original. Não há Mandelão nesta versão. Os clips de Voltmix e Bolha foram mapeados na ordem KICK, SNARE, HAT, RIM e aproximados à grade de semicolcheias conforme autorizado; é usado um único compasso. A Brilhante do Bolha usa a edição aprovada no navegador: passos 4, 7, 11 e 13.

## O que já foi verificado

- Base oficial limpa compilada e iniciada no teste local.
- Três bancos incorporados conferidos byte a byte; 12 samples originais preparados.
- Patterns conferidos com os eventos extraídos dos projetos.
- Reprodução, edição, troca de kit, reinício e efeitos testados no código C.
- Interface em 240 × 240 e controles da prévia conferidos no navegador.
- SDK íntegro; compilação nativa de diagnóstico e limites de memória verificados separadamente.

## Firmware para FM-1

[Baixar BAILE 0.7 — arquivo único .fwsc](firmware/BAILE-0.7-FM1.fwsc) · [SHA-256](firmware/SHA256SUMS.txt)

Compilado com JieLi Linux + Blink no Mac, pelo mesmo caminho da primeira versão Tamborzão. O empacotador reproduziu aquela primeira versão byte a byte. O novo pacote contém os três bancos e artes, passou no verificador do SDK, manteve o boot e o OTA loader da versão inicial e iniciou com áudio no emulador de diagnóstico corrigido.

A aplicação ocupa 551.528 bytes; o arquivo completo tem 590.388 bytes. Nenhum banco precisa ser baixado ou importado separadamente.

## Versão estável

A versão 0.7 foi promovida a estável após o usuário confirmar funcionamento perfeito no seu FM-1 em 09/11/2026. O arquivo publicado é exatamente o mesmo que foi testado, sem recompilação. Essa confirmação é um relato do usuário sobre seu aparelho. Os testes locais de áudio e de integridade do pacote também passaram.

O emulador comum pode apresentar sua falha conhecida de periférico não implementado; o teste local usou a variante de diagnóstico corrigida.

O BAILE reserva 405.504 bytes para dados do usuário e mantém o boot do SDK. A migração a partir de outros firmwares não foi validada de forma abrangente. A compilação com Windows 2.5.3 é uma alternativa ainda não executada, não um requisito para gerar o arquivo no Mac.

Veja [STATUS](STATUS.md), [compilação](docs/BUILDING.md), [arquitetura](docs/ARCHITECTURE.md) e [direitos dos assets](assets/README.md).
