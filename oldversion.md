# Porovnání původní verze (ui.py) s novou strukturou

## AI Funkce
- [x] Základní AI poskytovatelé (OpenAI, Cohere, HuggingFace, Ollama)
- [x] Vyhledávání podle nálady/žánru
- [x] Hledání podobných skladeb
- [x] Doporučení na základě historie
- [x] Generování playlistu
- [ ] Konfigurace jednotlivých AI poskytovatelů
  - [ ] OpenAI konfigurace (API klíč, model, teplota)
  - [ ] Cohere konfigurace (API klíč, model)
  - [ ] HuggingFace konfigurace (API klíč, výběr modelu)
  - [ ] Ollama konfigurace (host, port, model)
- [ ] Ukládání historie doporučení
- [ ] Systém promptů pro různé AI modely
- [ ] Cachování AI odpovědí

## Vyhledávání a Stahování
- [x] YouTube vyhledávání
- [x] Filtrování výsledků
- [ ] Pokročilé vyhledávací filtry z původní verze
  - [ ] Filtr podle délky videa
  - [ ] Filtr podle kvality zvuku
  - [ ] Filtr podle jazyka
  - [ ] Filtr podle data nahrání
- [ ] Stahování playlistů
- [ ] Fronta stahování
- [ ] Pozastavení/obnovení stahování
- [ ] QR kód pro sdílení

## Přehrávač
- [ ] Přehrávání skladeb
- [ ] Ovládání přehrávání (play/pause/stop)
- [ ] Playlist funkce
- [ ] Náhodné přehrávání
- [ ] Opakování
- [ ] Ovládání hlasitosti
- [ ] Zobrazení průběhu přehrávání

## Správa Knihovny
- [ ] Organizace podle interpretů
- [ ] Organizace podle žánrů
- [ ] Správa tagů
- [ ] Editace metadat
- [ ] Import/Export playlistů
- [ ] Synchronizace s mobilem
- [ ] Záloha knihovny

## Nastavení
- [x] Základní konfigurace cest
- [ ] Pokročilá nastavení z původní verze
  - [ ] Nastavení kvality zvuku
  - [ ] Nastavení normalizace hlasitosti
  - [ ] Nastavení konverze formátů
  - [ ] Nastavení metadat
  - [ ] Nastavení cache
- [ ] Správa témat
- [ ] Export/Import nastavení

## Webshare Integrace
- [ ] Vyhledávání na Webshare
- [ ] Stahování z Webshare
- [ ] Správa Webshare účtu
- [ ] Filtry pro Webshare

## Další Funkce
- [ ] Systém logování
- [ ] Správa chyb
- [ ] Aktualizace programu
- [ ] Statistiky využití
- [ ] Nápověda/dokumentace

## Vylepšení UI
- [ ] Interaktivní nápověda
- [ ] Klávesové zkratky
- [ ] Stavový řádek
- [ ] Progressbary
- [ ] Notifikace

## Poznámky
- Původní verze měla více integrovaných funkcí v jednom souboru
- Nová verze má lepší strukturu, ale některé funkce ještě chybí
- Prioritně implementovat chybějící funkce z původní verze
- Pak přidat nová vylepšení

## Priority Implementace
1. Dokončit AI funkce (konfigurace poskytovatelů)
2. Implementovat chybějící funkce přehrávače
3. Dokončit správu knihovny
4. Přidat pokročilá nastavení
5. Implementovat Webshare integraci
6. Vylepšit UI a přidat nové funkce 