# Jak wnieść wkład w rozwój dockvirt

Cieszymy się, że chcesz pomóc w rozwoju tego projektu! Każdy wkład, niezależnie od jego wielkości, jest mile widziany.

## 💬 Jak zacząć?

Jeśli masz pomysł na nową funkcję, znalazłeś błąd lub chcesz coś ulepszyć, najlepszym sposobem na rozpoczęcie jest założenie nowego **issue** w naszym repozytorium na GitHubie. Pozwoli to na dyskusję i koordynację prac.

## 🚀 Proces wprowadzania zmian

1.  **Sforkuj repozytorium** na swoje konto na GitHubie.

2.  **Sklonuj sforkowane repozytorium** na swój komputer:
    ```bash
    git clone https://github.com/TWOJA_NAZWA_UŻYTKOWNIKA/dockvirt.git
    cd dockvirt
    ```

3.  **Stwórz nową gałąź (branch)** dla swoich zmian:
    ```bash
    git checkout -b feature/twoja-niesamowita-funkcja
    ```

4.  **Wprowadź zmiany** w kodzie. Pamiętaj o zachowaniu czystości i spójności stylu.

5.  **Przetestuj swoje zmiany**. Jeśli dodajesz nową funkcjonalność, rozważ dodanie odpowiednich testów.

6.  **Zacommituj zmiany** z jasnym i opisowym komunikatem:
    ```bash
    git commit -m "feat: Dodaje nową, niesamowitą funkcję"
    ```

7.  **Wypchnij zmiany** do swojego sforkowanego repozytorium:
    ```bash
    git push origin feature/twoja-niesamowita-funkcja
    ```

8.  **Stwórz Pull Request** do głównego repozytorium `dockvirt`. W opisie PR wyjaśnij, co Twoje zmiany wprowadzają i dlaczego są wartościowe.

## 📝 Styl kodu

Projekt używa `flake8` do lintowania kodu. Staraj się pisać kod zgodny ze standardami PEP 8.

## 🙏 Dziękujemy!

Jeszcze raz dziękujemy za Twój wkład. Razem możemy uczynić `dockvirt` jeszcze lepszym narzędziem!
