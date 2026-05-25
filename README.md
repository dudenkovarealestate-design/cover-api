# Cover Generator API — Бизнес-Роботикс

API для автоматической генерации обложек постов с шрифтом Russo One.

## Запрос

POST /cover
Content-Type: application/json

{
  "title1": "AI-роботы:",
  "title2": "дайджест недели",
  "date": "18–24 мая 2026",
  "badge": "ЕЖЕНЕДЕЛЬНЫЙ ДАЙДЖЕСТ",
  "brand": "БИЗНЕС-РОБОТИКС"
}

## Ответ

PNG файл готовой обложки 1280x720px

## Проверка работы

GET /health → {"status": "ok"}
