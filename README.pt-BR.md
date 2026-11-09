# BAILE by MULÚ

Instrumento de ritmos para o M-VAVE FM-1 com **Tamborzão, Voltmix e Beat Bolha**. Esta reconstrução começa no código oficial limpo do FM1 Open, revisão `4c7496daac04a95ff10d1afdcc8f9ead2dbabc41`, conferida como a mais recente em 08/11/2026. O projeto anterior foi preservado.

## Uso

Após a abertura com a arte do BAILE, aparece o Tamborzão. PLAY inicia ou para o beat. PRESETS troca de kit; ALGORITHM seleciona uma das quatro trilhas; as 16 teclas brancas alternam os passos dessa trilha. OCT −/+ escolhe o primeiro ou o segundo compasso. K1 controla saturação, K2 reverb, K3 BPM e K4 swing.

Os três kits guardam suas edições separadamente durante a sessão. Ao reiniciar, volta o Tamborzão original. Não há Mandelão nesta versão. Os clips de Voltmix e Bolha foram mapeados na ordem KICK, SNARE, HAT, RIM e aproximados à grade de semicolcheias conforme autorizado; cada compasso foi repetido para formar dois.

## O que já foi verificado

- Base oficial limpa compilada e iniciada no teste local.
- Três bancos incorporados conferidos byte a byte; 12 samples originais preparados.
- Patterns conferidos com os eventos extraídos dos projetos.
- Reprodução, edição, troca de kit, reinício e efeitos testados no código C.
- Interface em 240 × 240 e controles da prévia conferidos no navegador.
- SDK íntegro; compilação nativa de diagnóstico e limites de memória verificados separadamente.

## Firmware compilado no Mac

[Baixar BAILE 0.4 — arquivo único .fwsc](https://github.com/arrastao/baile-fm1/raw/refs/heads/main/firmware/BAILE-0.4-MAC.fwsc) · [SHA-256](firmware/SHA256SUMS.txt)

Compilado com JieLi Linux + Blink no Mac, pelo mesmo caminho da primeira versão Tamborzão. O empacotador reproduziu aquela primeira versão byte a byte. O novo pacote contém os três bancos e artes, passou no verificador do SDK, manteve o boot e o OTA loader da versão inicial e iniciou com áudio no emulador de diagnóstico corrigido.

A aplicação ocupa 551.528 bytes; o arquivo completo tem 590.388 bytes. Nenhum banco precisa ser baixado ou importado separadamente.

## O que ainda falta

A instalação deste novo arquivo pelo M-UPGRADE e o teste físico no FM-1 ainda não foram feitos. O resultado no emulador não comprova que o problema de atualização anterior foi resolvido. O emulador comum pode apresentar sua falha conhecida de periférico não implementado; o teste usou a variante local de diagnóstico corrigida.

O BAILE reserva 405.504 bytes para dados do usuário e mantém o boot do SDK. A migração dessa divisão de memória precisa de validação no dispositivo. A compilação com Windows 2.5.3 é uma alternativa ainda não executada, não um requisito para gerar o arquivo no Mac.

Veja [STATUS](STATUS.md), [compilação](docs/BUILDING.md), [arquitetura](docs/ARCHITECTURE.md) e [direitos dos assets](assets/README.md).
