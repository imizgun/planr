# Projekt: Planr (nazwa robocza)

**Opis krótki:** Alternatywny frontend dla planu Wydziału MFI, z funkcjami społecznościowymi.

**Opis szczegółowy:** Platforma mająca na celu prezentację danych z uczelnianego systemu planistycznego w sposób bardziej czytelny, wzbogacając je o informacje przekazywane przez społeczność akademicką za pomocą systemu zmian i ocen.

### Minimalna funkcjonalność:
* Prezentacja planu dla danego kierunku, grupy, fakultetów i grup fakultetów w sposób czytelny i bardziej ekspresywny od obecnego rozwiązania.
* Interpretacja pola „uwagi” i odzwierciedlanie tych danych na planie.

### Rozbudowana funkcjonalność:
* Konta użytkowników zakładane przy pomocy e-maila uczelnianego / logowania przez Microsoft.
* System zgłaszania zmian w planie przez użytkowników z możliwością oceny zgłoszeń przez innych użytkowników i moderacją zgłoszeń.

### Minimalny stack technologiczny:
* **Backend** – Python / FastAPI
* **Frontend** – TS / Angular
* **DB** – PostgreSQL
* **Hosting** – własny

### Rozbudowa stacku technologicznego:
* **Backend** – Python / FastAPI
* **Frontend** – TS / Angular
* **DB** – PostgreSQL
* **Konteneryzacja** – Docker
* **Hosting** – AWS
* **Reverse proxy** – Nginx

### Działanie systemu społecznościowego:
Każdy zalogowany użytkownik ma przyporządkowaną rolę (string) i reputację (number).

* **Rola** – określa możliwości wprowadzania zmian i ich wagę.
  * **Student** przyporządkowany do określonej grupy i fakultetów ma największe przełożenie na zmiany dla zajęć, w których uczestniczy.
  * **Starosta roku** – ma duże przełożenie na zmiany dla całego roku kierunku.
  * **Pracownik akademicki** – ma pełną władzę nad zajęciami prowadzonymi przez siebie.
* **Reputacja** – określa podstawową wagę zmian.
  * Dla nowych kont jest mała i rośnie do bazowej z czasem.
  * Wzrasta wraz z ilością zmian potwierdzonych przez społeczność / moderację.
  * Spada wraz z czasem do poziomu bazowego.
  * Spada wraz z ilością zmian odrzuconych przez społeczność / moderację do poziomu zerowego i powraca do bazowego z czasem.
  * Celowe wprowadzanie błędnych zmian może być automatycznie wykrywane, a odpowiedzialne konta banowane.

Ocena proponowanych zmian odbywa się na dwa sposoby:
* **Ocena społeczności** – zmiany mogą być plusowane bądź minusowane przez użytkowników.
* **Weryfikacja moderacji** – w razie potrzeby możliwa jest manualna interwencja i rozstrzygnięcie.

Zmiany społeczności początkowo wyświetlają się inaczej niż potwierdzone i wraz ze wzrostem oceny zostają utrwalone w planie po przekroczeniu określonego progu.

Zmiany zatwierdzone lub odrzucone przez moderację mają efekt natychmiastowy.

Wszystkie zmiany wygasają wraz z końcem semestru.

---

## BACKEND

### Aktualizacja danych o planach:
1. **Pobranie głównego planu** – z `https://inf.ug.edu.pl/plan/?student=.*&seminarium=.&fakultet=.`
2. **Przypisanie fakultetów do kierunków** – przy pomocy łańcucha URL:
   * `https://inf.ug.edu.pl/plan/?dialog=grupa` i `https://inf.ug.edu.pl/plan/fiz/` – dane o ID kierunków na stronie (z hiperlinków).
   * `https://inf.ug.edu.pl/plan/?grupa=<id>` – dane o FAID przypisanych fakultetów (z hiperlinków).
   * `https://inf.ug.edu.pl/plan/?zajecia=<faid>&format=csv` – dane o przypisanych fakultetach dla kierunku (z pliku CSV).
3. **Aktualizacja danych o przedmiotach o dane z pola uwagi** – za pomocą hierarchicznej analizy:
   * **Analiza regex** – statyczne wyrażenia regularne zwracają zmiany na podstawie znanych templatek.
   * **Analiza LLM** – mały model językowy próbuje zinterpretować podane uwagi i zwrócić je w zrozumiałym dla programu formacie (implementacja funkcji zależna od ilości dostępnego czasu).
   * **Fallback** – uwagi pozostałe po poprzednich etapach zostają niezinterpretowane.
   * **Analiza manualna** – możliwa po fakcie.
4. **Nakładanie zatwierdzonych zmian i propozycji zmian moderacji / społeczności** – wprowadzane, jeśli nie kolidują ze *zmianami* z poprzednich etapów.

### Dokumentacja endpointów:

**1. Endpoint z listą planów, grup i fakultetów do formularza.**

Struktura zapytania:
```http
GET /api/v1/catalog
```

Odpowiedź:
```json
{
  "schema_version": 1,
  "source": { "version": "a3f9c1", "fetched_at": "2026-10-16T08:00:00Z" },
  "programs": [
    {
      "id": "cs-p-3",
      "name": "informatyka (P): III rok",
      "groups": [
        { "id": "grp_1", "label": "gr. 1" },
        { "id": "grp_2", "label": "gr. 2" }
      ],
      "electives": [
        {
          "id": "crs_41",
          "name": "Elective name",
          "groups": [
            {
              "id": "grp_e41_1",
              "label": "gr. 1",
              // Do implementacji później (Wymaga łączenia danych z planów i fetcha ze strony planowej)
              "teachers": ["dr Jan Kowalski"],
              "summary": [
                {
                  "weekday": 3,
                  "start_time": "10:00",
                  "end_time": "11:30",
                  "type": "lab"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

**2. Endpoint z konkretnym planem**

Struktura zapytania:
```http
GET /api/v1/schedule
?program=<programId>
&group=<groupId> (repeatable)
&elective=<courseId>:<groupId> (repeatable)
&from=<YYYY-MM-DD>
&to=<YYYY-MM-DD>
```

Odpowiedź:
```json
{
  "schema_version": 1, // Wersja templatki
  "program": {
    "id": "inf-p-3", // Kierunek
    "name": "informatyka (P): III rok" // Nazwa kierunku
  },
  "source": {
    // Metadane wersji zaktualizowanego planu
    "version": "a3f9c1",
    "fetched_at": "2026-10-16T08:00:00Z",
    "timezone": "Europe/Warsaw"
  },
  "items": [
    // Przedmioty
    {
      "id": "slot_41b7e0", // Id przedmiotu

      // Dane z csv
      "course": { "id": "crs_12", "name": "Aplikacje przemysłowe" },
      "type": "laboratorium",
      "group": { "id": "grp_1", "label": "gr. 1", "program_wide": false },
      "teachers": [{ "id": "t_7", "name": "dr Jakub Neumann, prof. UG" }],
      "room": "1.14",
      "block": { "weekday": 2, "start_hour": 14, "count": 2 },

      // Obowiązujące dane (zaktualizowane o te wyciągnięte z uwag)
      "effective": {
        "weekday": 2,
        "start_time": "14:30",
        "end_time": "16:00",
        "mode": "stationary",
        "date_from": "2026-10-06",
        "date_to": "2027-01-26"
      },

      // Informacja, które pola zostały zaktualizowane
      "patched_fields": ["start_time", "end_time"],

      // Uwagi
      "remark": {
        "raw": "14.30-16.00", // Pełne pole z csv
        "parse_status": "ok", // Czy udało się w pełni sparsować
        "unparsed": null, // Niesparsowany tekst
        "needs_review": false // Flaga, czy potrzebna weryfikacja
      },

      "proposals": [] // Zmiany niezatwierdzone (do rozbudowy w przyszłości)
    }
  ]
}
```

---

## FRONTEND

TBA