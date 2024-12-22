# Proces stahování z YouTube

1. **Formát stahování**:
   - YouTube videa jsou stahována pomocí yt-dlp v nejlepší dostupné kvalitě zvuku
   - Typicky se stahuje ve formátu WEBM nebo M4A (závisí na dostupném formátu)

2. **Konverze do MP3**:
   - Stažený soubor je automaticky konvertován do MP3 pomocí FFmpeg
   - Proces je bezestrátový vzhledem k původnímu staženému formátu
   - Používá se VBR (Variable Bit Rate) pro optimální poměr kvality a velikosti

3. **Nastavení kvality**:
   - 192 kbps je výchozí nastavení (dobrý kompromis mezi kvalitou a velikostí)
   - Vyšší bitrate (256, 320) nemá smysl, pokud zdrojové video nemá odpovídající kvalitu

4. **Normalizace hlasitosti**:
   - Používá se MP3Gain pro bezestrátovou normalizaci
   - Standardní cílová hlasitost je 89 dB (ReplayGain standard)
   - Normalizace je prováděna bez překódování MP3 souboru 