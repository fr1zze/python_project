-- name: employees
-- 1. Список сотрудников.
SELECT id, name, position
FROM employees
ORDER BY name, id;


-- name: trips
-- 2. Список поездок.
SELECT id, destination, purpose, start_date, end_date
FROM trips
ORDER BY start_date, id;


-- name: approved_requests
-- 3. Отбор согласований по статусу.
SELECT request_id, status
FROM approvals
WHERE status = ?
ORDER BY request_id;


-- name: trips_by_destination
-- 4. Поиск поездок по части названия направления.
SELECT id, destination, purpose, start_date, end_date
FROM trips
WHERE destination LIKE ?
ORDER BY start_date, id;


-- name: requests_details
-- 5. Все заявки со связанными данными.
SELECT
    r.id,
    e.name AS employee_name,
    t.destination,
    t.start_date,
    t.end_date,
    a.status,
    r.budget_limit
FROM travel_requests AS r
JOIN employees AS e ON e.id = r.employee_id
JOIN trips AS t ON t.id = r.trip_id
JOIN approvals AS a ON a.request_id = r.id
ORDER BY t.start_date, r.id;


-- name: employee_requests
-- 6. Связанные данные по заявкам одного сотрудника.
SELECT
    r.id,
    e.name AS employee_name,
    t.destination,
    t.start_date,
    t.end_date,
    a.status,
    r.budget_limit
FROM travel_requests AS r
JOIN employees AS e ON e.id = r.employee_id
JOIN trips AS t ON t.id = r.trip_id
JOIN approvals AS a ON a.request_id = r.id
WHERE r.employee_id = ?
ORDER BY t.start_date, r.id;


-- name: counts
-- 7. Количество записей во всех таблицах.
SELECT
    (SELECT COUNT(*) FROM employees) AS employees_count,
    (SELECT COUNT(*) FROM trips) AS trips_count,
    (SELECT COUNT(*) FROM travel_requests) AS requests_count,
    (SELECT COUNT(*) FROM approvals) AS approvals_count;


-- name: approved_totals
-- 8. Количество и общая стоимость одобренных поездок.
SELECT
    COUNT(*) AS approved_count,
    ROUND(
        COALESCE(
            SUM(
                t.travel_cost
                + t.hotel_cost
                + t.daily_allowance
                * (
                    julianday(t.end_date)
                    - julianday(t.start_date)
                    + 1
                )
            ),
            0
        ),
        2
    ) AS approved_cost
FROM travel_requests AS r
JOIN trips AS t ON t.id = r.trip_id
JOIN approvals AS a ON a.request_id = r.id
WHERE a.status = ?;


-- name: requests_by_employee
-- 9. Количество заявок каждого сотрудника.
SELECT
    e.id,
    e.name,
    COUNT(r.id) AS request_count
FROM employees AS e
LEFT JOIN travel_requests AS r ON r.employee_id = e.id
GROUP BY e.id, e.name
ORDER BY request_count DESC, e.id;


-- name: requests_by_status
-- 10. Количество заявок по статусам.
SELECT
    status,
    COUNT(*) AS request_count
FROM approvals
GROUP BY status
ORDER BY status;


-- name: employees_above_threshold
-- 11. Сотрудники с количеством заявок больше порога.
SELECT
    e.id,
    e.name,
    COUNT(r.id) AS request_count
FROM employees AS e
LEFT JOIN travel_requests AS r ON r.employee_id = e.id
GROUP BY e.id, e.name
HAVING COUNT(r.id) > ?
ORDER BY request_count DESC, e.id;


-- name: available_employees
-- 12. Сотрудники без одобренной поездки на выбранную дату.
SELECT
    e.id,
    e.name,
    e.position
FROM employees AS e
WHERE NOT EXISTS (
    SELECT 1
    FROM travel_requests AS r
    JOIN trips AS t ON t.id = r.trip_id
    JOIN approvals AS a ON a.request_id = r.id
    WHERE r.employee_id = e.id
      AND a.status = 'одобрена'
      AND ? BETWEEN t.start_date AND t.end_date
)
ORDER BY e.name, e.id;