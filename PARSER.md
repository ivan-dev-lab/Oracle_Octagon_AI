# Модуль `parser/`

## Подмодуль `parse_fighter.py`
Подмодуль выполняет функцию парсинга бойцов из рейтинга UFC
### **Описание функций:**
- `parse_fighter (url: str)` - функция парсинга статистики об отдельном бойце по ссылке. <br> **Возвращает** словарь с ключами `['Age', 'Height', 'Weight', 'Experience', 'Arm span', 'Leg span', 'Accuracy strikes', 'Accented strikes', 'Missed strikes', 'Number takedowns', 'Strike protection', 'Takedown protection', 'Wins', 'Losses', 'Drafts', 'KO/TKO']` 
- `parse_top_fighters ()` - функция парсинга бойцов из рейтинга UFC ( https://ufc.ru/rankings ) <br> В функции представлено 2 цикла - первый для сбора данных о чемпионах каждого **весового** дивизиона. Второй - для всех остальных спорстменов из рейтинга. <br> **Возвращает** `pd.DataFrame` со всеми данными

## Подмодуль `parse_fights.py`
Подмодуль выполняет функцию парсинга боёв UFC
### **Описание функций:**
- `parse_events ()` - функция собирает данные о прошедших чемпонатах/турнирах на первых 36 страницах сайта <br> **Возвращает** список с полученными чемпионатами
- `check_fighters (fighters_df: pd.DataFrame, names: list[str], urls: list[str])` - функция ищет в `fighters_df` имена из массива `names`. В случае успешного нахождения **возвращает** двумерный массив вида: `[[FighterID, FighterID], []]` ( второй массив предназначен для ссылок из `urls` на тех бойцов, которые не нашлись по имени в `fighters_df`). <br> В случае не нахождения одного/всех из бойцов **возвращает** двумерный массив вида `[[FighterID], [URL]]`, или `[[], [URL, URL]]`
- `get_fighter_bio (url: str)` - функция собирает личные данные бойца ( дивизион, имя, идентификатор `FighterID`, ссылку на бойца) <br> **Возвращает** словарь с личными данными бойца. В случае отсутствия личных данных **возвращает** `{}`
- `parse_fights ()` - главная функция подмодуля. Проходится циклом по всем чемпионатам, полученным из `parse_events()`, где из каждого чемпионата берет бой главного карда ( раздел боев с популярными бойцами ), для которого формирует `fight_card` - cловарь с данными по каждому бою ( ключи словаря: `['FightID', 'URL', 'FighterID_1', 'FighterID_2', 'Result_1', 'Result_2']`) - в котором `Result_1` и `Result_1` - результаты боя для каждого бойца соотвественно. <br> **Возвращает** двумерный массив вида `[[pd.DataFrame], [pd.DataFrame]]`, в котором 1 массив - обновленные данные по бойцам для записи в `data/fighters.csv`, во втором - история боёв для записи в `data/fights.csv`