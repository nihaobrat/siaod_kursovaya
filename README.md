# Описание приложения "Регистрация водителей и расписание маршруток"

Это  приложение на Python (с использованием **Tkinter**), которое позволяет:
1. **Регистрировать водителей** двух типов (А и Б).
2. **Устанавливать базовое время прохождения маршрута** (в минутах).
3. **Указывать количество рейсов** на конкретный день недели.
4. **Автоматически формировать расписание** для водителей (как классическими методами, так и генетическим алгоритмом).
5. **Отображать или сохранять** результаты генерируемого расписания, а также выводить уведомления об ошибках (например, если недостаточно водителей).

---

## Основные функции приложения

1. **Добавление нового водителя**  
   - Введите фамилию водителя и выберите его тип (А или Б).  
   - Нажмите кнопку «Добавить водителя», и приложение сохранит нового водителя.

2. **Установка времени маршрута**  
   - Введите длительность одного маршрута (в минутах) в поле «Введите время маршрута в минутах».  
   - Нажмите «Установить время маршрута» — это обновит глобальную переменную, используемую при генерации расписания.

3. **Указание количества рейсов и дня недели**  
   - Укажите день недели (Понедельник—Воскресенье) из выпадающего меню.  
   - Введите требуемое количество рейсов в поле «Введите количество рейсов на день».

4. **Генерация расписания**  
   - **«Сгенерировать расписание из водителей типа А»** и **«Сгенерировать расписание из водителей типа Б»** — для формирования расписания только по водителям типа А или Б.  
   - **«Сгенерировать совместное расписание»** — для формирования расписания сразу для всех водителей (А и Б).  
   - **«Генетическое расписание для типа А / Б»** — альтернативный метод генерации с использованием генетического алгоритма, что иногда позволяет более эффективно распределить рейсы.  
   - **«Генетическое расписание для типа А и Б»** — генетический метод формирования расписания для всех водителей одновременно.

5. **Вывод результата**  
   - После нажатия любой из кнопок генерации расписания результат (таблица с водителями, временем начала, временем окончания и числом маршрутов) выводится в текстовое поле в левой части окна.  
   - При возникновении ошибок (например, «Недостаточно водителей» или «Некорректно введено число рейсов») соответствующие сообщения будут показаны в том же текстовом поле.

6. **Управление водителями**  
   - Кнопка «Управление водителями» открывает отдельное окно, позволяя:
     - Просматривать список водителей типа А и Б.
     - Удалять водителей из списка.
     - Сменять тип (из А в Б и наоборот).

7. **Сброс полей**  
   - Кнопка «Сброс» очищает поля ввода (количество рейсов, время маршрута), а также стирает текущее сформированное расписание из текстового поля.

---

## Инструкция по установке и запуску

1. **Убедитесь, что установлен Python 3.x** и библиотека **Tkinter** (она идёт в составе стандартной библиотеки Python для большинства дистрибутивов).
2. **Установите библиотеку pandas**, если она не установлена:
   ```bash
   pip install pandas
   ```
3. **Сохраните код** (приведённый выше) в файл с расширением `.py` (например, `with_shtafs.py`).
4. **Запустите приложение**:
   ```bash
   python with_shtafs.py
   ```

После этого откроется графическое окно приложения.

---

## Руководство пользователя

1. **Добавление водителя**  
   - Введите фамилию водителя в поле «Введите фамилию водителя».  
   - Выберите тип (A или B) из выпадающего меню.  
   - Нажмите «Добавить водителя». Результат отобразится в нижней части формы.

2. **Выбор дня недели**  
   - Из списка «Выберите день недели» выберите нужный день (Понедельник—Воскресенье).

3. **Указание количества рейсов**  
   - Введите целое число (количество рейсов) в поле «Введите количество рейсов на день».

4. **Указание базового времени маршрута**  
   - Заполните поле «Введите время маршрута в минутах» (целое число).  
   - Нажмите «Установить время маршрута» для применения нового времени маршрута.

5. **Формирование расписания**  
   - Выберите соответствующую кнопку «Сгенерировать расписание …» или «Генетическое расписание …».  
   - По завершении работы алгоритма в текстовом поле появится таблица с расписанием или сообщение об ошибке (например, о нехватке водителей).

6. **Управление водителями**  
   - Нажмите «Управление водителями», чтобы открыть отдельное окно со списками водителей типа А и Б.  
   - В этом окне можно удалять водителя или менять его тип.

7. **Сброс**  
   - Кнопка «Сброс» очищает поля ввода и текстовое поле с результатами.

---

## Возможные сценарии использования

1. **Генерация расписания только для одного типа**  
   - Если вы хотите проверить нагрузку или расписание только для водителей типа А (например, они работают в будние дни), можно сгенерировать расписание отдельно.
2. **Генерация общего расписания (тип A и B)**  
   - Приложение определит оптимальное распределение рейсов с учётом ограничения по времени и наличия водителей.
3. **Выходные дни**  
   - В выходные тип А не работает (при попытке назначить рейс типу А в выходной, приложение пропустит таких водителей).  
   - Если в выходные нет водителей типа Б, будет выведено соответствующее сообщение.
4. **Генетический алгоритм**  
   - Позволяет находить более сбалансированный или разнообразный план, хотя и не всегда самый оптимальный, но более гибкий к изменениям.

---

## Требования и зависимости

- **Python 3.x**
- **Tkinter** (поставляется вместе с Python в большинстве случаев)

---

## Контакты и обратная связь

Если у вас возникли вопросы: Ковалевский Стас, группа БВТ2205
